from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.adapters import (
    DiagnosticAdapter,
    DiagnosticAdapterError,
    DiagnosticAdapterResponseError,
    DiagnosticAdapterTimeoutError,
    DiagnosticAdapterUnavailableError,
    NemotronDiagnosticAdapter,
)
from app.agent import BoundedDiagnosticAgent, DiagnosticPolicyError
from app.models import DiagnosticRequest, DiagnosticRun, HealthResponse, ReadinessResponse


def create_app(
    adapter: DiagnosticAdapter | None = None,
    fixture_dir: Path | None = None,
) -> FastAPI:
    selected_adapter = adapter or NemotronDiagnosticAdapter(
        base_url=os.getenv("MODEL_BASE_URL", "http://127.0.0.1:8100"),
        model_id=os.getenv("MODEL_ID", "nemotron-35-lightning"),
        timeout_seconds=float(os.getenv("MODEL_TIMEOUT_SECONDS", "30")),
    )
    selected_fixture = fixture_dir or Path(os.getenv("FIXTURE_DIR", "/app/fixtures"))
    agent = BoundedDiagnosticAgent(
        selected_fixture,
        selected_adapter,
        max_calls=int(os.getenv("MAX_TOOL_CALLS", "4")),
        max_seconds=float(os.getenv("MAX_RUN_SECONDS", "30")),
    )
    application = FastAPI(title="Project 3 Read-Only Diagnostic Agent", version="0.1.0")

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

    @application.post("/v1/diagnose", response_model=DiagnosticRun)
    def diagnose(request: DiagnosticRequest) -> DiagnosticRun:
        try:
            return agent.run(request.question, request.service)
        except DiagnosticAdapterUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except DiagnosticAdapterTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except DiagnosticAdapterResponseError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except (DiagnosticPolicyError, DiagnosticAdapterError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return application


app = create_app()
