from typing import Any, Literal, Annotated

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
    limit: int = Field(default=5, ge=1, le=20, strict=True)


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
    evidence_id: str = Field(pattern=r"^[a-z0-9-]+:[a-z0-9-]+:[a-f0-9]{32}$")
    payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
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
    limit: int = Field(default=5, ge=1, le=20, strict=True)


class ModelToolPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    calls: list[PlannedToolCall] = Field(min_length=1, max_length=4)

    @field_validator("calls")
    @classmethod
    def calls_are_unique(cls, value: list[PlannedToolCall]) -> list[PlannedToolCall]:
        # One observation per tool/target. Changing an ignored field or taking
        # overlapping log slices must not bypass the observation budget.
        identities = [(call.tool, call.service) for call in value]
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


class BoundedData(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StatusData(BoundedData):
    state: Literal["healthy", "degraded", "down"]
    since: str = Field(min_length=1, max_length=50)
    detail: str = Field(min_length=1, max_length=500)


class LogEntry(BoundedData):
    time: str = Field(min_length=1, max_length=50)
    level: Literal["debug", "info", "warning", "error", "critical"]
    message: str = Field(min_length=1, max_length=2000)


class LogsData(BoundedData):
    entries: list[LogEntry] = Field(max_length=20)
    returned: int = Field(ge=0, le=20, strict=True)


class ResourceData(BoundedData):
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    queue_depth: int = Field(ge=0, le=1_000_000, strict=True)
    request_error_percent: float = Field(ge=0, le=100)


class StorageData(BoundedData):
    capacity_percent: float = Field(ge=0, le=100)
    read_error_count: int = Field(ge=0, strict=True)
    degraded_devices: int = Field(ge=0, le=1000, strict=True)


class ConfigData(BoundedData):
    secret_names: list[Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{0,99}$")]] = Field(max_length=20)


class MediaConfig(ConfigData):
    release: str = Field(min_length=1, max_length=50)
    worker_count: int = Field(ge=1, le=1000, strict=True)
    timeout_seconds: int = Field(ge=1, le=3600, strict=True)


class BackupConfig(ConfigData):
    release: str = Field(min_length=1, max_length=50)
    retention_days: int = Field(ge=1, le=3650, strict=True)
    verification_enabled: bool = Field(strict=True)


class ProxyConfig(ConfigData):
    release: str = Field(min_length=1, max_length=50)
    upstream: str = Field(min_length=1, max_length=200)
    tls_enabled: bool = Field(strict=True)


class StorageConfig(ConfigData):
    layout: str = Field(min_length=1, max_length=50)
    device_count: int = Field(ge=1, le=1000, strict=True)
    scrub_schedule: str = Field(min_length=1, max_length=100)


def validate_tool_data(tool: str, service: str, data: dict[str, Any]) -> dict[str, Any]:
    config_types = {"media-server": MediaConfig, "backup-service": BackupConfig,
                    "reverse-proxy": ProxyConfig, "storage-pool": StorageConfig}
    model = {
        "get_service_status": StatusData,
        "get_recent_logs": LogsData,
        "get_resource_metrics": StorageData if service == "storage-pool" else ResourceData,
        "get_config_inventory": config_types[service],
    }[tool]
    result = model.model_validate(data).model_dump(mode="json")
    if tool == "get_recent_logs" and result["returned"] != len(result["entries"]):
        raise ValueError("Returned log count does not match its entries.")
    return result
