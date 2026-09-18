from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunbookQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=10, max_length=1_000)


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passage_id: str
    document_title: str
    document_version: str
    section_title: str
    excerpt: str
    score: float = Field(gt=0)


class RetrievalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    has_evidence: bool
    hits: list[RetrievalHit] = Field(max_length=3)


class ModelGroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    answer: str = Field(min_length=20, max_length=800)
    citation_ids: list[str] = Field(min_length=1, max_length=3)

    @field_validator("citation_ids")
    @classmethod
    def citation_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("citation identifiers must be unique")
        return value


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    answerable: bool
    answer: str = Field(min_length=20, max_length=800)
    citations: list[RetrievalHit] = Field(max_length=3)
    requires_human_review: Literal[True] = True


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    model: str
