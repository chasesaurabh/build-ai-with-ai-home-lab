from pathlib import Path
from typing import Any

import pytest

from app.adapters import AnswerAdapterError
from app.models import RunbookQuestion
from app.service import GroundedAnswerService, RetrievalService


CORPUS_DIR = Path(__file__).parents[1] / "corpus"


class StubAnswerAdapter:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.calls = 0

    def answer(self, question: str, hits: list[Any]) -> dict[str, Any]:
        self.calls += 1
        return self.result


def test_no_evidence_abstains_without_calling_model() -> None:
    adapter = StubAnswerAdapter({})
    service = GroundedAnswerService(RetrievalService(CORPUS_DIR), adapter)
    response = service.answer(
        RunbookQuestion(question="How can I calibrate a resin printer exposure profile?")
    )
    assert response.answerable is False
    assert response.citations == []
    assert "does not contain enough evidence" in response.answer
    assert adapter.calls == 0


def test_supplied_citation_is_returned_as_inspectable_passage() -> None:
    adapter = StubAnswerAdapter(
        {
            "answerable": True,
            "answer": "Collect the pool health summary and recent storage logs before human review.",
            "citation_ids": ["storage-pool#evidence-collect"],
        }
    )
    service = GroundedAnswerService(RetrievalService(CORPUS_DIR), adapter)
    response = service.answer(
        RunbookQuestion(question="What evidence should I collect for degraded storage redundancy?")
    )
    assert response.answerable is True
    assert response.citations[0].passage_id == "storage-pool#evidence-collect"
    assert response.requires_human_review is True


def test_citation_outside_retrieved_set_fails_closed() -> None:
    adapter = StubAnswerAdapter(
        {
            "answerable": True,
            "answer": "This answer cites a passage that was not supplied by retrieval.",
            "citation_ids": ["invented#passage"],
        }
    )
    service = GroundedAnswerService(RetrievalService(CORPUS_DIR), adapter)
    with pytest.raises(AnswerAdapterError, match="retrieval did not supply"):
        service.answer(
            RunbookQuestion(question="What evidence should I collect for degraded storage redundancy?")
        )


def test_malformed_model_answer_fails_closed() -> None:
    adapter = StubAnswerAdapter({"answer": "Too short", "citation_ids": []})
    service = GroundedAnswerService(RetrievalService(CORPUS_DIR), adapter)
    with pytest.raises(AnswerAdapterError, match="application schema"):
        service.answer(
            RunbookQuestion(question="What evidence should I collect for degraded storage redundancy?")
        )


def test_related_but_insufficient_evidence_can_abstain() -> None:
    adapter = StubAnswerAdapter({
        'answerable': False,
        'answer': 'The supplied passages do not state any administrator password.',
        'citation_ids': [],
    })
    service = GroundedAnswerService(RetrievalService(CORPUS_DIR), adapter)
    result = service.answer(RunbookQuestion(question='What is the backup service administrator password?'))
    assert adapter.calls == 1  # Lexical overlap did produce passages.
    assert result.answerable is False
    assert result.citations == []
    assert result.answer == GroundedAnswerService._NO_EVIDENCE_ANSWER


@pytest.mark.parametrize('answerable,citations', [(True, []), (False, ['storage-pool#evidence-collect']), ('false', [])])
def test_incoherent_answerability_fails_closed(answerable, citations):
    adapter = StubAnswerAdapter({'answerable': answerable, 'answer': 'A sufficiently long synthetic answer for validation.', 'citation_ids': citations})
    service = GroundedAnswerService(RetrievalService(CORPUS_DIR), adapter)
    with pytest.raises(AnswerAdapterError, match='application schema'):
        service.answer(RunbookQuestion(question='What evidence should I collect for degraded storage redundancy?'))
