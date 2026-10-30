from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RunbookQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=10, max_length=1_000)


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passage_id: str
    document_title: str
    document_version: str
    source_file: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    passage_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
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

    answerable: bool = Field(strict=True)
    answer: str = Field(min_length=20, max_length=800)
    citation_ids: list[str] = Field(max_length=3)

    @field_validator("citation_ids")
    @classmethod
    def citation_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("citation identifiers must be unique")
        return value

    @model_validator(mode="after")
    def answerability_matches_citations(self):
        if self.answerable != bool(self.citation_ids):
            raise ValueError("Answerable results need citations; abstentions must have none.")
        return self


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
