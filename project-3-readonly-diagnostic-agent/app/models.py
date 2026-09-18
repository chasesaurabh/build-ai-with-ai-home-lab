from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ServiceName = Literal[
    "media-server",
    "backup-service",
    "reverse-proxy",
    "storage-pool",
]
ToolName = Literal[
    "get_service_status",
    "get_recent_logs",
    "get_resource_metrics",
    "get_config_inventory",
]


class StatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service: ServiceName


class LogsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service: ServiceName
    limit: int = Field(default=5, ge=1, le=20)


class MetricsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service: ServiceName


class ConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service: ServiceName


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: ToolName
    service: ServiceName
    evidence_id: str = Field(pattern=r"^[a-z0-9-]+:[a-z0-9-]+:[a-f0-9]{12}$")
    data: dict[str, Any]


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: ToolName
    arguments: dict[str, Any]


class DiagnosticReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service: ServiceName
    summary: str = Field(min_length=20, max_length=500)
    evidence_ids: list[str] = Field(min_length=1, max_length=4)
    requires_human_review: Literal[True] = True


class PlannedToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: ToolName
    service: ServiceName
    limit: int = Field(default=5, ge=1, le=20)


class ModelToolPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    calls: list[PlannedToolCall] = Field(min_length=1, max_length=4)

    @field_validator("calls")
    @classmethod
    def calls_are_unique(cls, value: list[PlannedToolCall]) -> list[PlannedToolCall]:
        identities = [(call.tool, call.service, call.limit) for call in value]
        if len(identities) != len(set(identities)):
            raise ValueError("planned tool calls must be unique")
        return value


class ModelDiagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    summary: str = Field(min_length=20, max_length=500)
    evidence_ids: list[str] = Field(min_length=1, max_length=4)

    @field_validator("evidence_ids")
    @classmethod
    def evidence_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("diagnosis evidence identifiers must be unique")
        return value


class DiagnosticRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report: DiagnosticReport
    tool_results: list[ToolResult] = Field(min_length=1, max_length=4)
    elapsed_ms: float = Field(ge=0)


class DiagnosticRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    service: ServiceName
    question: str = Field(min_length=10, max_length=1000)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    model: str
