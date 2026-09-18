from pathlib import Path
import time
from typing import Any

import pytest

from app.agent import BoundedDiagnosticAgent, DiagnosticPolicyError


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


class StubDiagnosticAdapter:
    def __init__(
        self,
        plan: dict[str, Any],
        summary: str = "The simulated service evidence supports a bounded diagnosis requiring human review.",
        evidence_override: list[str] | None = None,
        delay_seconds: float = 0,
    ) -> None:
        self.plan_result = plan
        self.summary = summary
        self.evidence_override = evidence_override
        self.delay_seconds = delay_seconds

    def plan(self, question: str, service: str) -> dict[str, Any]:
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        return self.plan_result

    def diagnose(self, question: str, service: str, results: list[Any]) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "evidence_ids": self.evidence_override
            if self.evidence_override is not None
            else [result.evidence_id for result in results],
        }


def valid_plan(service: str = "media-server") -> dict[str, Any]:
    return {
        "calls": [
            {"tool": "get_service_status", "service": service, "limit": 5},
            {"tool": "get_recent_logs", "service": service, "limit": 3},
            {"tool": "get_resource_metrics", "service": service, "limit": 5},
        ]
    }


def test_bounded_agent_executes_authorized_plan_and_returns_trace() -> None:
    run = BoundedDiagnosticAgent(
        FIXTURE_DIR,
        StubDiagnosticAdapter(
            valid_plan(),
            summary=(
                "The simulated media server is degraded by CPU saturation and a growing transcode queue."
            ),
        ),
    ).run("Why is the media server slow?", "media-server")
    assert len(run.tool_results) == 3
    assert set(run.report.evidence_ids) == {
        result.evidence_id for result in run.tool_results
    }
    assert run.report.requires_human_review is True


def test_plan_cannot_target_another_service() -> None:
    agent = BoundedDiagnosticAgent(
        FIXTURE_DIR,
        StubDiagnosticAdapter(valid_plan("storage-pool")),
    )
    with pytest.raises(DiagnosticPolicyError, match="unapproved service"):
        agent.run("Why is the media server slow?", "media-server")


def test_duplicate_tool_call_is_rejected() -> None:
    plan = {
        "calls": [
            {"tool": "get_service_status", "service": "media-server", "limit": 5},
            {"tool": "get_service_status", "service": "media-server", "limit": 5},
        ]
    }
    with pytest.raises(DiagnosticPolicyError, match="plan was unusable"):
        BoundedDiagnosticAgent(FIXTURE_DIR, StubDiagnosticAdapter(plan)).run(
            "Why is the media server slow?", "media-server"
        )


def test_unknown_tool_is_rejected_before_dispatch() -> None:
    plan = {
        "calls": [
            {"tool": "run_shell", "service": "media-server", "limit": 5},
        ]
    }
    with pytest.raises(DiagnosticPolicyError, match="plan was unusable"):
        BoundedDiagnosticAgent(FIXTURE_DIR, StubDiagnosticAdapter(plan)).run(
            "Run a command to diagnose the media server.", "media-server"
        )


def test_invented_evidence_identifier_is_rejected() -> None:
    adapter = StubDiagnosticAdapter(
        valid_plan(),
        evidence_override=["get-service-status:media-server:000000000000"],
    )
    with pytest.raises(DiagnosticPolicyError, match="not produced"):
        BoundedDiagnosticAgent(FIXTURE_DIR, adapter).run(
            "Why is the media server slow?", "media-server"
        )


def test_time_budget_is_application_owned() -> None:
    adapter = StubDiagnosticAdapter(valid_plan(), delay_seconds=0.02)
    with pytest.raises(DiagnosticPolicyError, match="time budget"):
        BoundedDiagnosticAgent(
            FIXTURE_DIR,
            adapter,
            max_seconds=0.001,
        ).run("Why is the media server slow?", "media-server")
