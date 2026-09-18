from __future__ import annotations

import copy
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models import ApprovalPackage, ModelChangeProposal, SourceConfig, ValidationResult


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
        manifest_path = fixture_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_path = fixture_dir / manifest["file"]
        unexpected = {
            path.name for path in fixture_dir.glob("*.json")
        } - {"manifest.json", manifest["file"]}
        if unexpected:
            raise ChangePlanningError("Unapproved fixture files are present.")
        source_bytes = source_path.read_bytes()
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
        if hashlib.sha256(self._source_path.read_bytes()).hexdigest() != self._source_sha256:
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
            rollback_config=self._source,
            validations=validations,
        )
