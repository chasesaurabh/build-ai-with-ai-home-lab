from __future__ import annotations

import copy
import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models import ApprovalPackage, ModelChangeProposal, ModelDesiredProposal, SourceConfig, ValidationResult


class ChangePlanningError(RuntimeError):
    """A proposal or source failed a deterministic planning boundary."""


class SandboxedChangePlanner:
    _risk_by_field = {
        "image_tag": "The new image may fail readiness checks or change application behavior.",
        "replica_count": "A replica-count change alters compute and memory consumption.",
        "request_timeout_seconds": "A timeout change can increase request occupancy or surface failures sooner.",
        "maintenance_mode": "Maintenance mode intentionally interrupts normal client service.",
    }
    def __init__(self, fixture_dir: Path) -> None:
        fixture_dir = fixture_dir.resolve()
        manifest_path = fixture_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        filename = manifest.get("file")
        if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.json", filename):
            raise ChangePlanningError("The manifest requires a simple JSON filename.")
        source_path = fixture_dir / manifest["file"]
        if source_path.is_symlink() or source_path.resolve().parent != fixture_dir:
            raise ChangePlanningError("The source must not escape through links or paths.")
        unexpected = {
            path.name for path in fixture_dir.glob("*.json")
        } - {"manifest.json", manifest["file"]}
        if unexpected:
            raise ChangePlanningError("Unapproved fixture files are present.")
        with source_path.open("rb") as stream:
            source_bytes = stream.read(65_537)
        if len(source_bytes) > 65_536:
            raise ChangePlanningError("The source exceeds its 64-KiB limit.")
        digest = hashlib.sha256(source_bytes).hexdigest()
        if digest != manifest["sha256"]:
            raise ChangePlanningError("The source configuration hash does not match its manifest.")
        try:
            self._source = SourceConfig.model_validate_json(source_bytes)
        except ValidationError as exc:
            raise ChangePlanningError("The source configuration is invalid.") from exc
        self._source_path = source_path
        self._source_sha256 = digest

    @property
    def source_config(self) -> SourceConfig:
        return self._source.model_copy(deep=True)

    def prepare_desired(self, raw_proposal: dict[str, Any]) -> ApprovalPackage:
        try:
            desired = ModelDesiredProposal.model_validate(raw_proposal)
        except ValidationError as exc:
            raise ChangePlanningError("The desired change violated its closed schema.") from exc
        source = self._source.model_dump()
        return self.prepare({"changes": [
            {"field": change.field, "before": source[change.field], "after": change.after}
            for change in desired.changes
        ]})

    def prepare(self, raw_proposal: dict[str, Any]) -> ApprovalPackage:
        try:
            proposal = ModelChangeProposal.model_validate(raw_proposal)
        except ValidationError as exc:
            raise ChangePlanningError("The proposed change violated its closed schema.") from exc

        source = self._source.model_dump()
        staged = copy.deepcopy(source)
        for change in proposal.changes:
            if source[change.field] != change.before:
                raise ChangePlanningError(
                    f"The stated before value for {change.field} does not match the verified source."
                )
            staged[change.field] = change.after

        try:
            proposed_config = SourceConfig.model_validate(staged)
        except ValidationError as exc:
            raise ChangePlanningError("The staged configuration failed full-schema validation.") from exc

        before_text = json.dumps(source, indent=2, sort_keys=True) + "\n"
        after_text = json.dumps(proposed_config.model_dump(), indent=2, sort_keys=True) + "\n"
        unified_diff = "".join(
            difflib.unified_diff(
                before_text.splitlines(keepends=True),
                after_text.splitlines(keepends=True),
                fromfile="verified/service-config.json",
                tofile="proposed/service-config.json",
            )
        )
        if self._source_path.is_symlink():
            raise ChangePlanningError("The source configuration changed during planning.")
        with self._source_path.open("rb") as stream:
            current_bytes = stream.read(65_537)
        if hashlib.sha256(current_bytes).hexdigest() != self._source_sha256:
            raise ChangePlanningError("The source configuration changed during planning.")

        identity_material = json.dumps(
            {"source": self._source_sha256, "proposal": proposal.model_dump()},
            sort_keys=True,
            separators=(",", ":"),
        )
        proposal_id = "proposal-" + hashlib.sha256(
            identity_material.encode("utf-8")
        ).hexdigest()[:16]
        changed_names = [change.field for change in proposal.changes]
        rationale = "Prepare a review-only change to: " + ", ".join(changed_names) + "."
        risks = [self._risk_by_field[field] for field in changed_names]
        if "maintenance_mode" in changed_names:
            risks[changed_names.index("maintenance_mode")] = (
                "Enabling maintenance mode intentionally interrupts normal client service."
                if proposed_config.maintenance_mode else
                "Disabling maintenance mode resumes client traffic; verify readiness and dependencies first."
            )
        validations = [
            ValidationResult(check="source_integrity", detail="Manifest SHA-256 matched."),
            ValidationResult(check="field_allowlist", detail="Every changed field is explicitly approved."),
            ValidationResult(check="change_budget", detail="The proposal contains no more than two unique changes."),
            ValidationResult(check="full_schema", detail="The complete staged configuration passed validation."),
            ValidationResult(check="source_immutability", detail="The verified source hash remained unchanged."),
        ]
        return ApprovalPackage(
            proposal_id=proposal_id,
            source_sha256=self._source_sha256,
            service_id=self._source.service_id,
            rationale=rationale,
            risks=risks,
            unified_diff=unified_diff,
            proposed_config=proposed_config,
            rollback_config=self._source.model_copy(deep=True),
            validations=validations,
        )
