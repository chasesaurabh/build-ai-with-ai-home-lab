from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.adapters import (
    DiagnosticAdapterResponseError,
    DiagnosticAdapterTimeoutError,
    DiagnosticAdapterUnavailableError,
)
from app.main import create_app


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


class StubAdapter:
    model_id = "stub-model"

    def __init__(self, ready: bool = True) -> None:
        self.is_ready = ready

    def ready(self) -> bool:
        return self.is_ready

    def plan(self, question: str, service: str) -> dict[str, Any]:
        return {"calls": [{"tool": "get_service_status", "service": service, "limit": 5}]}

    def diagnose(self, question: str, service: str, results: list[Any]) -> dict[str, Any]:
        return {
            "summary": "The simulated service status provides evidence for a human-reviewed diagnosis.",
            "evidence_ids": [results[0].evidence_id],
        }


class RaisingAdapter(StubAdapter):
    def __init__(self, error: Exception) -> None:
        super().__init__(ready=False)
        self.error = error

    def plan(self, question: str, service: str) -> dict[str, Any]:
        raise self.error


def test_health_is_independent_of_model() -> None:
    response = TestClient(create_app(StubAdapter(ready=False), FIXTURE_DIR)).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_model_state() -> None:
    ready = TestClient(create_app(StubAdapter(ready=True), FIXTURE_DIR)).get("/ready")
    unavailable = TestClient(create_app(StubAdapter(ready=False), FIXTURE_DIR)).get("/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "model": "stub-model"}
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"] == {"status": "not_ready", "model": "stub-model"}


def test_diagnosis_returns_trace_over_http() -> None:
    response = TestClient(create_app(StubAdapter(), FIXTURE_DIR)).post(
        "/v1/diagnose",
        json={"service": "media-server", "question": "Why is the media service degraded?"},
    )
    assert response.status_code == 200
    assert response.json()["report"]["requires_human_review"] is True
    assert len(response.json()["tool_results"]) == 1


def test_invalid_input_is_rejected_before_model_call() -> None:
    response = TestClient(create_app(StubAdapter(), FIXTURE_DIR)).post(
        "/v1/diagnose",
        json={"service": "host", "question": "short", "command": "whoami"},
    )
    assert response.status_code == 422


def test_provider_errors_are_controlled() -> None:
    errors = [
        (DiagnosticAdapterUnavailableError("unavailable"), 503),
        (DiagnosticAdapterTimeoutError("timeout"), 504),
        (DiagnosticAdapterResponseError("bad response"), 502),
    ]
    for error, status in errors:
        response = TestClient(create_app(RaisingAdapter(error), FIXTURE_DIR)).post(
            "/v1/diagnose",
            json={"service": "media-server", "question": "Why is the media service degraded?"},
        )
        assert response.status_code == status
