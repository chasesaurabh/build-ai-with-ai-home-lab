from pathlib import Path
import hashlib
import shutil

import pytest
from pydantic import ValidationError

from app.models import LogsRequest, StatusRequest, ToolCall
from app.tools import FixtureError, ReadOnlyLabTools, ToolAuthorizationError
from app.workflow import DeterministicDiagnosticWorkflow


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


def test_fixture_loads_and_status_has_evidence() -> None:
    tools = ReadOnlyLabTools(FIXTURE_DIR)
    result = tools.get_service_status(StatusRequest(service="media-server"))
    assert result.data["state"] == "degraded"
    assert result.evidence_id.startswith("get-service-status:media-server:")


def test_modified_fixture_fails_closed(tmp_path: Path) -> None:
    copied = tmp_path / "fixtures"
    shutil.copytree(FIXTURE_DIR, copied)
    (copied / "lab-state.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FixtureError, match="hash"):
        ReadOnlyLabTools(copied)


def test_unapproved_fixture_file_fails_closed(tmp_path: Path) -> None:
    copied = tmp_path / "fixtures"
    shutil.copytree(FIXTURE_DIR, copied)
    (copied / "extra.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FixtureError, match="Unapproved fixture files"):
        ReadOnlyLabTools(copied)


def test_unknown_service_is_rejected_by_schema() -> None:
    with pytest.raises(ValidationError):
        StatusRequest(service="host-operating-system")


def test_logs_are_newest_first_and_bounded() -> None:
    result = ReadOnlyLabTools(FIXTURE_DIR).get_recent_logs(
        LogsRequest(service="media-server", limit=2)
    )
    assert result.data["returned"] == 2
    assert result.data["entries"][0]["time"] > result.data["entries"][1]["time"]


def test_log_limit_is_bounded() -> None:
    with pytest.raises(ValidationError):
        LogsRequest(service="media-server", limit=100)


def test_caller_supplied_path_is_rejected_before_dispatch() -> None:
    tools = ReadOnlyLabTools(FIXTURE_DIR)
    call = ToolCall(
        tool="get_recent_logs",
        arguments={"service": "media-server", "limit": 5, "path": "C:/secrets"},
    )
    with pytest.raises(ToolAuthorizationError, match="approved schema"):
        tools.dispatch(call)


def test_config_inventory_contains_secret_names_not_values() -> None:
    tools = ReadOnlyLabTools(FIXTURE_DIR)
    result = tools.dispatch(
        ToolCall(tool="get_config_inventory", arguments={"service": "backup-service"})
    )
    assert result.data["secret_names"] == ["BACKUP_ENCRYPTION_KEY"]
    assert "secret_values" not in result.data


@pytest.mark.parametrize(
    ("service", "expected_text"),
    [
        ("media-server", "CPU saturation"),
        ("reverse-proxy", "health checks"),
        ("storage-pool", "degraded redundancy"),
        ("backup-service", "healthy"),
    ],
)
def test_deterministic_workflow_links_diagnosis_to_evidence(
    service: str, expected_text: str
) -> None:
    report = DeterministicDiagnosticWorkflow(FIXTURE_DIR).diagnose(service)
    assert expected_text.casefold() in report.summary.casefold()
    assert len(report.evidence_ids) == 3
    assert len(set(report.evidence_ids)) == 3
    assert report.requires_human_review is True


def test_tool_calls_do_not_modify_fixture() -> None:
    fixture = FIXTURE_DIR / "lab-state.json"
    before = hashlib.sha256(fixture.read_bytes()).hexdigest()
    tools = ReadOnlyLabTools(FIXTURE_DIR)
    tools.dispatch(ToolCall(tool="get_service_status", arguments={"service": "storage-pool"}))
    tools.dispatch(ToolCall(tool="get_resource_metrics", arguments={"service": "storage-pool"}))
    after = hashlib.sha256(fixture.read_bytes()).hexdigest()
    assert after == before
