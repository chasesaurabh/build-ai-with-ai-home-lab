from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ChangeField = Literal[
    "image_tag",
    "replica_count",
    "request_timeout_seconds",
    "maintenance_mode",
]
class ChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request: str = Field(min_length=10, max_length=1000)


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    service_id: Literal["photo-api"]
    image_tag: str = Field(
        pattern=r"^registry\.home\.invalid/photo-api:[0-9]+\.[0-9]+\.[0-9]+$"
    )
    replica_count: int = Field(ge=1, le=4)
    request_timeout_seconds: int = Field(ge=5, le=120)
    maintenance_mode: bool


class ImageTagChange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["image_tag"]
    before: str
    after: str


class ReplicaCountChange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["replica_count"]
    before: int
    after: int


class RequestTimeoutChange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["request_timeout_seconds"]
    before: int
    after: int


class MaintenanceModeChange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["maintenance_mode"]
    before: bool
    after: bool


FieldChange = Annotated[
    ImageTagChange | ReplicaCountChange | RequestTimeoutChange | MaintenanceModeChange,
    Field(discriminator="field"),
]


class ModelChangeProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    changes: list[FieldChange] = Field(min_length=1, max_length=2)

    @field_validator("changes")
    @classmethod
    def unique_changed_fields(cls, value: list[FieldChange]) -> list[FieldChange]:
        fields = [change.field for change in value]
        if len(fields) != len(set(fields)):
            raise ValueError("changed fields must be unique")
        if any(change.before == change.after for change in value):
            raise ValueError("a proposed change must alter its field")
        return value


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check: Literal[
        "source_integrity",
        "field_allowlist",
        "change_budget",
        "full_schema",
        "source_immutability",
    ]
    passed: Literal[True] = True
    detail: str


class DesiredImageTag(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["image_tag"]
    after: str = Field(max_length=150)


class DesiredReplicas(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["replica_count"]
    after: int = Field(ge=1, le=4)


class DesiredTimeout(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["request_timeout_seconds"]
    after: int = Field(ge=5, le=120)


class DesiredMaintenance(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field: Literal["maintenance_mode"]
    after: bool


DesiredChange = Annotated[
    DesiredImageTag | DesiredReplicas | DesiredTimeout | DesiredMaintenance,
    Field(discriminator="field"),
]


class ModelDesiredProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    changes: list[DesiredChange] = Field(min_length=1, max_length=2)

    @field_validator("changes")
    @classmethod
    def unique_fields(cls, changes: list[DesiredChange]) -> list[DesiredChange]:
        if len({change.field for change in changes}) != len(changes):
            raise ValueError("changed fields must be unique")
        return changes


class ApprovalPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: str = Field(pattern=r"^proposal-[a-f0-9]{16}$")
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    service_id: Literal["photo-api"]
    rationale: str
    risks: list[str]
    unified_diff: str
    proposed_config: SourceConfig
    rollback_config: SourceConfig
    validations: list[ValidationResult] = Field(min_length=5, max_length=5)
    status: Literal["awaiting_human_approval"] = "awaiting_human_approval"
    apply_capability: Literal["absent"] = "absent"
    human_review_required: Literal[True] = True
