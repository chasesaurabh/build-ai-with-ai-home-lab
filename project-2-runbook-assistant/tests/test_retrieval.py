from pathlib import Path
import shutil

import pytest

from app.models import RunbookQuestion
from app.retrieval import CorpusError, load_corpus, retrieve
from app.service import RetrievalService


CORPUS_DIR = Path(__file__).parents[1] / "corpus"


def test_manifest_corpus_loads_with_stable_unique_passages() -> None:
    passages = load_corpus(CORPUS_DIR)
    assert len(passages) == 12
    assert len({passage.passage_id for passage in passages}) == 12
    assert "storage-pool#degraded-redundancy" in {
        passage.passage_id for passage in passages
    }


def test_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS_DIR, copied)
    (copied / "storage-pool.md").write_text("modified", encoding="utf-8")
    with pytest.raises(CorpusError, match="Hash mismatch"):
        load_corpus(copied)


def test_unapproved_document_fails_closed(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS_DIR, copied)
    (copied / "unapproved.md").write_text("# Unapproved\n\n## Text\n\nNo.", encoding="utf-8")
    with pytest.raises(CorpusError, match="Unapproved corpus files"):
        load_corpus(copied)


@pytest.mark.parametrize(
    ("question", "expected_id"),
    [
        ("What evidence should I collect for degraded storage redundancy?", "storage-pool#evidence-collect"),
        ("How should I investigate intermittent TLS handshake errors?", "reverse-proxy#tls-handshake-error"),
        ("When is a completed backup considered verified?", "backup-service#healthy-verification"),
        ("What should be recorded after suspicious blocked login attempts?", "identity-provider#suspicious-login-attempt"),
    ],
)
def test_relevant_question_retrieves_expected_passage(question: str, expected_id: str) -> None:
    passages = load_corpus(CORPUS_DIR)
    ids = [passage.passage_id for passage, _ in retrieve(question, passages)]
    assert expected_id in ids


def test_out_of_scope_question_returns_no_evidence() -> None:
    response = RetrievalService(CORPUS_DIR).search(
        RunbookQuestion(question="How can I calibrate a resin printer exposure profile?")
    )
    assert response.has_evidence is False
    assert response.hits == []


def test_retrieval_response_is_bounded() -> None:
    response = RetrievalService(CORPUS_DIR).search(
        RunbookQuestion(question="Which logs and status evidence should I collect for an error?")
    )
    assert 1 <= len(response.hits) <= 3
    assert all(hit.score > 0 for hit in response.hits)


def test_invalid_top_k_is_rejected() -> None:
    passages = load_corpus(CORPUS_DIR)
    with pytest.raises(ValueError, match="between 1 and 3"):
        retrieve("storage pool", passages, top_k=4)


def test_deleted_document_requires_restore_before_rebuild(tmp_path: Path) -> None:
    working = tmp_path / "working"
    backup = tmp_path / "backup"
    shutil.copytree(CORPUS_DIR, working)
    shutil.copytree(CORPUS_DIR, backup)
    original_ids = [passage.passage_id for passage in load_corpus(working)]

    (working / "backup-service.md").unlink()
    with pytest.raises(CorpusError, match="missing"):
        load_corpus(working)

    shutil.copy2(backup / "backup-service.md", working / "backup-service.md")
    restored_ids = [passage.passage_id for passage in load_corpus(working)]
    assert restored_ids == original_ids
