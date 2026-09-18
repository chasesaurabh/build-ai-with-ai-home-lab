from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.adapters import (
    AnswerAdapter,
    AnswerAdapterError,
    AnswerAdapterResponseError,
    AnswerAdapterTimeoutError,
    AnswerAdapterUnavailableError,
    NemotronAnswerAdapter,
)
from app.models import GroundedAnswer, HealthResponse, ReadinessResponse, RunbookQuestion
from app.service import GroundedAnswerService, RetrievalService


def create_app(
    adapter: AnswerAdapter | None = None,
    corpus_dir: Path | None = None,
) -> FastAPI:
    selected_adapter = adapter or NemotronAnswerAdapter(
        base_url=os.getenv("MODEL_BASE_URL", "http://127.0.0.1:8100"),
        model_id=os.getenv("MODEL_ID", "nemotron-35-lightning"),
        timeout_seconds=float(os.getenv("MODEL_TIMEOUT_SECONDS", "30")),
    )
    selected_corpus = corpus_dir or Path(os.getenv("CORPUS_DIR", "/app/corpus"))
    service = GroundedAnswerService(
        RetrievalService(selected_corpus),
        selected_adapter,
    )

    application = FastAPI(title="Project 2 Runbook Assistant", version="0.1.0")

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @application.get("/ready", response_model=ReadinessResponse)
    def ready() -> ReadinessResponse:
        if selected_adapter.ready():
            return ReadinessResponse(status="ready", model=selected_adapter.model_id)
        raise HTTPException(
            status_code=503,
            detail=ReadinessResponse(
                status="not_ready",
                model=selected_adapter.model_id,
            ).model_dump(),
        )

    @application.post("/v1/answer", response_model=GroundedAnswer)
    def answer(request: RunbookQuestion) -> GroundedAnswer:
        try:
            return service.answer(request)
        except AnswerAdapterUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except AnswerAdapterTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except (AnswerAdapterResponseError, AnswerAdapterError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return application


app = create_app()
