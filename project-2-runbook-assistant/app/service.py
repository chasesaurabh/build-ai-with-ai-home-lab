from pathlib import Path

from pydantic import ValidationError

from app.adapters import AnswerAdapter, AnswerAdapterError
from app.models import (
    GroundedAnswer,
    ModelGroundedAnswer,
    RetrievalHit,
    RetrievalResponse,
    RunbookQuestion,
)
from app.retrieval import load_corpus, retrieve


class RetrievalService:
    def __init__(self, corpus_dir: Path) -> None:
        self._passages = load_corpus(corpus_dir)

    def search(self, request: RunbookQuestion) -> RetrievalResponse:
        ranked = retrieve(request.question, self._passages)
        hits = [
            RetrievalHit(
                passage_id=passage.passage_id,
                document_title=passage.document_title,
                document_version=passage.document_version,
                section_title=passage.section_title,
                excerpt=passage.text,
                score=score,
            )
            for passage, score in ranked
        ]
        return RetrievalResponse(
            question=request.question,
            has_evidence=bool(hits),
            hits=hits,
        )


class GroundedAnswerService:
    _NO_EVIDENCE_ANSWER = (
        "The approved runbook corpus does not contain enough evidence to answer this question."
    )

    def __init__(self, retrieval: RetrievalService, adapter: AnswerAdapter) -> None:
        self._retrieval = retrieval
        self._adapter = adapter

    def answer(self, request: RunbookQuestion) -> GroundedAnswer:
        retrieval = self._retrieval.search(request)
        if not retrieval.has_evidence:
            return GroundedAnswer(
                question=request.question,
                answerable=False,
                answer=self._NO_EVIDENCE_ANSWER,
                citations=[],
            )

        raw = self._adapter.answer(request.question, retrieval.hits)
        try:
            model_answer = ModelGroundedAnswer.model_validate(raw)
        except ValidationError as exc:
            raise AnswerAdapterError("The answer provider violated the application schema.") from exc

        hits_by_id = {hit.passage_id: hit for hit in retrieval.hits}
        unexpected = set(model_answer.citation_ids) - set(hits_by_id)
        if unexpected:
            raise AnswerAdapterError(
                "The answer provider cited a passage that retrieval did not supply."
            )
        citations = [hits_by_id[passage_id] for passage_id in model_answer.citation_ids]
        return GroundedAnswer(
            question=request.question,
            answerable=True,
            answer=model_answer.answer,
            citations=citations,
        )
