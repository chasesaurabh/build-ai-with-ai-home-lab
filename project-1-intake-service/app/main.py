from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.adapters import (
    AdapterResponseError,
    AdapterTimeoutError,
    AdapterUnavailableError,
    IntakeAdapter,
    adapter_from_environment,
)
from app.models import HealthResponse, IntakeDecision, IntakeRequest, ReadinessResponse
from app.service import IntakeService


def create_app(adapter: IntakeAdapter | None = None) -> FastAPI:
    service = IntakeService(adapter or adapter_from_environment())
    application = FastAPI(title="Home Lab Intake Service", version="0.1.0")

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @application.get("/ready", response_model=ReadinessResponse)
    def ready() -> ReadinessResponse | JSONResponse:
        is_ready = service.adapter.ready()
        body = ReadinessResponse(
            status="ready" if is_ready else "not_ready",
            adapter=service.adapter.name,
        )
        if not is_ready:
            return JSONResponse(status_code=503, content=body.model_dump())
        return body

    @application.post("/v1/intake", response_model=IntakeDecision)
    def classify(request: IntakeRequest) -> IntakeDecision:
        try:
            return service.classify(request)
        except AdapterUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except AdapterTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except AdapterResponseError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return application


app = create_app()
