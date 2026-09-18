from pathlib import Path
import hashlib
import shutil

import pytest

from app.planner import ChangePlanningError, SandboxedChangePlanner


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


def valid_proposal() -> dict[str, object]:
    return {
        "changes": [
            {
                "field": "image_tag",
                "before": "registry.home.invalid/photo-api:1.4.2",
                "after": "registry.home.invalid/photo-api:1.4.3",
            }
        ],
    }


def test_valid_proposal_produces_exact_approval_package() -> None:
    package = SandboxedChangePlanner(FIXTURE_DIR).prepare(valid_proposal())
    assert package.status == "awaiting_human_approval"
    assert package.apply_capability == "absent"
    assert package.human_review_required is True
    assert package.proposed_config.image_tag.endswith(":1.4.3")
    assert package.rollback_config.image_tag.endswith(":1.4.2")
    assert "-  \"image_tag\": \"registry.home.invalid/photo-api:1.4.2\"" in package.unified_diff
    assert "+  \"image_tag\": \"registry.home.invalid/photo-api:1.4.3\"" in package.unified_diff
    assert len(package.validations) == 5


def test_source_fixture_is_not_modified() -> None:
    source = FIXTURE_DIR / "service-config.json"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    SandboxedChangePlanner(FIXTURE_DIR).prepare(valid_proposal())
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    assert before == after


def test_planner_has_no_apply_interface() -> None:
    assert not hasattr(SandboxedChangePlanner, "apply")
    assert not hasattr(SandboxedChangePlanner, "deploy")
    assert not hasattr(SandboxedChangePlanner, "rollback")


def test_wrong_before_value_fails_closed() -> None:
    proposal = valid_proposal()
    proposal["changes"][0]["before"] = "registry.home.invalid/photo-api:9.9.9"
    with pytest.raises(ChangePlanningError, match="does not match"):
        SandboxedChangePlanner(FIXTURE_DIR).prepare(proposal)


@pytest.mark.parametrize("field", ["command", "path", "production_target", "service_id"])
def test_unapproved_change_fields_fail_closed(field: str) -> None:
    proposal = valid_proposal()
    proposal["changes"] = [{"field": field, "before": "x", "after": "y"}]
    with pytest.raises(ChangePlanningError, match="closed schema"):
        SandboxedChangePlanner(FIXTURE_DIR).prepare(proposal)


def test_extra_command_data_fails_closed() -> None:
    proposal = valid_proposal()
    proposal["command"] = "docker compose up -d"
    with pytest.raises(ChangePlanningError, match="closed schema"):
        SandboxedChangePlanner(FIXTURE_DIR).prepare(proposal)


def test_invalid_registry_or_tag_fails_full_schema() -> None:
    proposal = valid_proposal()
    proposal["changes"][0]["after"] = "public.invalid/photo-api:latest"
    with pytest.raises(ChangePlanningError, match="full-schema"):
        SandboxedChangePlanner(FIXTURE_DIR).prepare(proposal)


def test_more_than_two_changes_fails_closed() -> None:
    proposal = valid_proposal()
    proposal["changes"] = [
        {"field": "replica_count", "before": 2, "after": 3},
        {"field": "request_timeout_seconds", "before": 30, "after": 45},
        {"field": "maintenance_mode", "before": False, "after": True},
    ]
    with pytest.raises(ChangePlanningError, match="closed schema"):
        SandboxedChangePlanner(FIXTURE_DIR).prepare(proposal)


def test_duplicate_or_noop_change_fails_closed() -> None:
    proposal = valid_proposal()
    proposal["changes"] = [
        {"field": "replica_count", "before": 2, "after": 3},
        {"field": "replica_count", "before": 2, "after": 4},
    ]
    with pytest.raises(ChangePlanningError, match="closed schema"):
        SandboxedChangePlanner(FIXTURE_DIR).prepare(proposal)

    proposal = valid_proposal()
    proposal["changes"][0]["after"] = proposal["changes"][0]["before"]
    with pytest.raises(ChangePlanningError, match="closed schema"):
        SandboxedChangePlanner(FIXTURE_DIR).prepare(proposal)


def test_tampered_or_unapproved_fixture_fails_closed(tmp_path: Path) -> None:
    copied = tmp_path / "fixtures"
    shutil.copytree(FIXTURE_DIR, copied)
    (copied / "service-config.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ChangePlanningError, match="hash"):
        SandboxedChangePlanner(copied)

    copied = tmp_path / "fixtures-extra"
    shutil.copytree(FIXTURE_DIR, copied)
    (copied / "production.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ChangePlanningError, match="Unapproved"):
        SandboxedChangePlanner(copied)


def test_package_contains_no_secret_or_execution_fields() -> None:
    serialized = SandboxedChangePlanner(FIXTURE_DIR).prepare(valid_proposal()).model_dump_json()
    for forbidden in ("password", "secret", "token", "command", "production_target"):
        assert forbidden not in serialized.casefold()
