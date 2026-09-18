from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.adapters import (
    AnswerAdapterResponseError,
    AnswerAdapterTimeoutError,
    AnswerAdapterUnavailableError,
)
from app.main import create_app


CORPUS_DIR = Path(__file__).parents[1] / "corpus"


class StubAdapter:
    model_id = "stub-model"

    def __init__(self, ready: bool = True) -> None:
        self.is_ready = ready
        self.calls = 0

    def ready(self) -> bool:
        return self.is_ready

    def answer(self, question: str, hits: list[Any]) -> dict[str, Any]:
        self.calls += 1
        return {
            "answer": "Collect the storage status, pool summary, device identifier, and recent logs.",
            "citation_ids": ["storage-pool#evidence-collect"],
        }


class RaisingAdapter(StubAdapter):
    def __init__(self, error: Exception) -> None:
        super().__init__(ready=False)
        self.error = error

    def answer(self, question: str, hits: list[Any]) -> dict[str, Any]:
        raise self.error


def test_health_is_independent_of_model() -> None:
    response = TestClient(create_app(StubAdapter(ready=False), CORPUS_DIR)).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_model_state() -> None:
    ready = TestClient(create_app(StubAdapter(ready=True), CORPUS_DIR)).get("/ready")
    unavailable = TestClient(create_app(StubAdapter(ready=False), CORPUS_DIR)).get("/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "model": "stub-model"}
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"] == {
        "status": "not_ready",
        "model": "stub-model",
    }


def test_supported_answer_returns_inspectable_citation() -> None:
    response = TestClient(create_app(StubAdapter(), CORPUS_DIR)).post(
        "/v1/answer",
        json={"question": "What evidence should I collect for degraded storage redundancy?"},
    )
    assert response.status_code == 200
    assert response.json()["answerable"] is True
    assert response.json()["citations"][0]["passage_id"] == "storage-pool#evidence-collect"
    assert response.json()["requires_human_review"] is True


def test_no_evidence_bypasses_model_over_http() -> None:
    adapter = StubAdapter()
    response = TestClient(create_app(adapter, CORPUS_DIR)).post(
        "/v1/answer",
        json={"question": "How can I calibrate a resin printer exposure profile?"},
    )
    assert response.status_code == 200
    assert response.json()["answerable"] is False
    assert response.json()["citations"] == []
    assert adapter.calls == 0


def test_unavailable_model_returns_503() -> None:
    response = TestClient(
        create_app(
            RaisingAdapter(AnswerAdapterUnavailableError("provider unavailable")),
            CORPUS_DIR,
        )
    ).post(
        "/v1/answer",
        json={"question": "What evidence should I collect for degraded storage redundancy?"},
    )
    assert response.status_code == 503


def test_model_timeout_returns_504() -> None:
    response = TestClient(
        create_app(RaisingAdapter(AnswerAdapterTimeoutError("provider timed out")), CORPUS_DIR)
    ).post(
        "/v1/answer",
        json={"question": "What evidence should I collect for degraded storage redundancy?"},
    )
    assert response.status_code == 504


def test_bad_model_response_returns_502() -> None:
    response = TestClient(
        create_app(RaisingAdapter(AnswerAdapterResponseError("bad response")), CORPUS_DIR)
    ).post(
        "/v1/answer",
        json={"question": "What evidence should I collect for degraded storage redundancy?"},
    )
    assert response.status_code == 502


def test_invalid_input_is_rejected_before_adapter_call() -> None:
    adapter = StubAdapter()
    response = TestClient(create_app(adapter, CORPUS_DIR)).post(
        "/v1/answer",
        json={"question": "short", "unexpected": True},
    )
    assert response.status_code == 422
    assert adapter.calls == 0
