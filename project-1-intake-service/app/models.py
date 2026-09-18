from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Category = Literal["availability", "performance", "security", "access", "change", "other"]
Urgency = Literal["low", "normal", "high"]
Condition = Literal[
    "healthy",
    "planned_nonimpacting",
    "access_request",
    "degraded",
    "outage",
    "security_event",
    "data_loss_risk",
    "ambiguous",
]
EvidenceRequest = Literal[
    "service_status",
    "recent_logs",
    "resource_usage",
    "change_history",
    "network_reachability",
    "identity_audit",
    "none",
]
NextStep = Literal["record", "investigate", "escalate", "request_clarification"]


class IntakeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    description: str = Field(min_length=20, max_length=2_000)


class ModelIntakeAssessment(BaseModel):
    """Bounded facts extracted by an adapter before application policy is applied."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: Category
    condition: Condition
    affected_system: str = Field(min_length=1, max_length=100)


class IntakeDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: Category
    urgency: Urgency
    affected_system: str = Field(min_length=1, max_length=100)
    evidence_requests: list[EvidenceRequest] = Field(
        min_length=1,
        max_length=3,
        json_schema_extra={"uniqueItems": True},
    )
    next_step: NextStep
    rationale: str = Field(min_length=20, max_length=240)
    requires_human_review: Literal[True]

    @field_validator("evidence_requests")
    @classmethod
    def evidence_requests_are_unique_and_coherent(
        cls,
        value: list[EvidenceRequest],
    ) -> list[EvidenceRequest]:
        if len(value) != len(set(value)):
            raise ValueError("evidence requests must be unique")
        if "none" in value and len(value) != 1:
            raise ValueError("none cannot be combined with another evidence request")
        return value


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    adapter: str
