from pathlib import Path
from typing import Any

import pytest

from app.models import ChangeRequest
from app.planner import ChangePlanningError
from app.service import ModelBackedChangePlanningService


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


class StubAdapter:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.source_seen = None

    def propose(self, request: str, source: Any) -> dict[str, Any]:
        self.source_seen = source
        return self.result


def proposal() -> dict[str, Any]:
    return {
        "changes": [{"field": "replica_count", "before": 2, "after": 3}],
    }


def test_model_output_passes_through_application_owned_planner() -> None:
    adapter = StubAdapter(proposal())
    package = ModelBackedChangePlanningService(FIXTURE_DIR, adapter).prepare(
        ChangeRequest(request="Prepare a proposal to increase the replica count to three.")
    )
    assert adapter.source_seen.replica_count == 2
    assert package.proposed_config.replica_count == 3
    assert package.apply_capability == "absent"


def test_invalid_model_output_fails_closed() -> None:
    result = proposal()
    result["changes"][0]["field"] = "command"
    with pytest.raises(ChangePlanningError):
        ModelBackedChangePlanningService(FIXTURE_DIR, StubAdapter(result)).prepare(
            ChangeRequest(request="Run a command against the production host immediately.")
        )
