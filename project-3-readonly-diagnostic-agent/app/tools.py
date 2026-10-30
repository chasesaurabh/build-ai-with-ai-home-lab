from __future__ import annotations

import hashlib
import json
import re
from uuid import uuid4
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models import (
    ConfigRequest,
    LogsRequest,
    MetricsRequest,
    ServiceName,
    StatusRequest,
    ToolCall,
    ToolResult,
    LogEntry,
    validate_tool_data,
)


class FixtureError(RuntimeError):
    """The simulated lab fixture failed integrity or shape validation."""


class ToolAuthorizationError(RuntimeError):
    """A requested tool call is outside the approved typed interface."""


class ReadOnlyLabTools:
    _EXPECTED_SERVICES = {
        "media-server",
        "backup-service",
        "reverse-proxy",
        "storage-pool",
    }

    def __init__(self, fixture_dir: Path) -> None:
        fixture_dir = fixture_dir.resolve()
        manifest_path = fixture_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        filename = manifest.get("file")
        if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.json", filename):
            raise FixtureError("The fixture manifest requires a simple JSON filename.")
        fixture_path = fixture_dir / manifest["file"]
        if fixture_path.is_symlink() or fixture_path.resolve().parent != fixture_dir:
            raise FixtureError("The fixture must not escape through links or paths.")
        if not fixture_path.is_file():
            raise FixtureError("The approved lab-state fixture is missing.")
        with fixture_path.open("rb") as stream:
            verified_bytes = stream.read(1_048_577)
        if len(verified_bytes) > 1_048_576:
            raise FixtureError("The simulated fixture exceeds its one-MiB bound.")
        digest = hashlib.sha256(verified_bytes).hexdigest()
        if digest != manifest["sha256"]:
            raise FixtureError("The lab-state fixture hash does not match its manifest.")
        unexpected = {
            path.name for path in fixture_dir.glob("*.json")
        } - {"manifest.json", manifest["file"]}
        if unexpected:
            raise FixtureError(
                f"Unapproved fixture files found: {', '.join(sorted(unexpected))}"
            )
        state = json.loads(verified_bytes)
        services = state.get("services")
        if not isinstance(services, dict) or set(services) != self._EXPECTED_SERVICES:
            raise FixtureError("The simulated service inventory is incomplete or unapproved.")
        try:
            for name, service in services.items():
                if not isinstance(service, dict) or set(service) != {"status", "logs", "metrics", "config"}:
                    raise ValueError("Unexpected service fields")
                if not isinstance(service["logs"], list) or len(service["logs"]) > 100:
                    raise ValueError("Fixture logs exceed their bound")
                service["logs"] = [LogEntry.model_validate(e).model_dump() for e in service["logs"]]
                for key, tool in [("status", "get_service_status"), ("metrics", "get_resource_metrics"), ("config", "get_config_inventory")]:
                    service[key] = validate_tool_data(tool, name, service[key])
        except (ValidationError, ValueError, TypeError, KeyError) as exc:
            raise FixtureError("The fixture violated its bounded data schema.") from exc
        self._state = state

    @staticmethod
    def _result(tool: str, service: ServiceName, data: dict[str, Any]) -> ToolResult:
        data = validate_tool_data(tool, service, data)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        evidence_tool = tool.replace("_", "-")
        return ToolResult(
            tool=tool,
            service=service,
            evidence_id=f"{evidence_tool}:{service}:{uuid4().hex}",
            payload_sha256=digest,
            data=data,
        )

    def get_service_status(self, request: StatusRequest) -> ToolResult:
        data = dict(self._state["services"][request.service]["status"])
        return self._result("get_service_status", request.service, data)

    def get_recent_logs(self, request: LogsRequest) -> ToolResult:
        logs = sorted(
            self._state["services"][request.service]["logs"],
            key=lambda entry: entry["time"],
            reverse=True,
        )[: request.limit]
        data = {"entries": [dict(entry) for entry in logs], "returned": len(logs)}
        return self._result("get_recent_logs", request.service, data)

    def get_resource_metrics(self, request: MetricsRequest) -> ToolResult:
        data = dict(self._state["services"][request.service]["metrics"])
        return self._result("get_resource_metrics", request.service, data)

    def get_config_inventory(self, request: ConfigRequest) -> ToolResult:
        data = dict(self._state["services"][request.service]["config"])
        return self._result("get_config_inventory", request.service, data)

    def dispatch(self, call: ToolCall) -> ToolResult:
        request_types = {
            "get_service_status": StatusRequest,
            "get_recent_logs": LogsRequest,
            "get_resource_metrics": MetricsRequest,
            "get_config_inventory": ConfigRequest,
        }
        methods = {
            "get_service_status": self.get_service_status,
            "get_recent_logs": self.get_recent_logs,
            "get_resource_metrics": self.get_resource_metrics,
            "get_config_inventory": self.get_config_inventory,
        }
        try:
            request = request_types[call.tool].model_validate(call.arguments)
        except (KeyError, ValidationError) as exc:
            raise ToolAuthorizationError("The tool call violated its approved schema.") from exc
        return methods[call.tool](request)
