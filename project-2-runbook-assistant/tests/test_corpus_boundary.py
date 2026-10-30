import json
import hashlib
import shutil
from pathlib import Path
import pytest
from app.retrieval import CorpusError, load_corpus

CORPUS = Path(__file__).parents[1] / 'corpus'

@pytest.mark.parametrize('filename', ['../outside.md', '/tmp/outside.md', r'..\outside.md', 'C:outside.md', 'nested/runbook.md'])
def test_manifest_cannot_select_paths_outside_flat_corpus(tmp_path, filename):
    copied = tmp_path / 'corpus'
    shutil.copytree(CORPUS, copied)
    manifest = json.loads((copied/'manifest.json').read_text())
    manifest['documents'][0]['file'] = filename
    (copied/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(CorpusError, match='simple Markdown filenames'):
        load_corpus(copied)


def test_symlink_cannot_import_external_document(tmp_path):
    copied = tmp_path / 'corpus'
    shutil.copytree(CORPUS, copied)
    source = copied/'backup-service.md'
    external = tmp_path/'outside.md'
    external.write_bytes(source.read_bytes())
    source.unlink()
    source.symlink_to(external)
    with pytest.raises(CorpusError, match='links or paths'):
        load_corpus(copied)


def test_duplicate_manifest_entry_is_rejected(tmp_path):
    copied = tmp_path/'corpus'
    shutil.copytree(CORPUS, copied)
    manifest = json.loads((copied/'manifest.json').read_text())
    manifest['documents'].append(dict(manifest['documents'][0], id='different-id'))
    (copied/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(CorpusError, match='Duplicate manifest'):
        load_corpus(copied)


def test_parser_uses_the_bytes_that_passed_hash_verification(tmp_path, monkeypatch):
    copied = tmp_path/'corpus'
    shutil.copytree(CORPUS, copied)
    original = Path.read_bytes
    def read_then_change(path):
        data = original(path)
        if path == copied/'backup-service.md':
            path.write_text('# Changed after verification\n\n## Unapproved\n\nChanged content.\n')
        return data
    monkeypatch.setattr(Path, 'read_bytes', read_then_change)
    passages = load_corpus(copied)
    assert any(p.passage_id == 'backup-service#healthy-verification' for p in passages)
    assert not any(p.section_title == 'Unapproved' for p in passages)


def test_citation_provenance_matches_actual_source_and_excerpt():
    from app.models import RunbookQuestion
    from app.service import RetrievalService
    response = RetrievalService(CORPUS).search(RunbookQuestion(question='What evidence should I collect for degraded storage redundancy?'))
    assert response.hits
    for hit in response.hits:
        assert hit.source_sha256 == hashlib.sha256((CORPUS/hit.source_file).read_bytes()).hexdigest()
        assert hit.passage_sha256 == hashlib.sha256(hit.excerpt.encode('utf-8')).hexdigest()


def test_reviewed_deletion_removes_source_from_rebuilt_index(tmp_path):
    from app.models import RunbookQuestion
    from app.service import RetrievalService
    copied=tmp_path/'corpus'
    shutil.copytree(CORPUS,copied)
    question=RunbookQuestion(question='When is a completed backup considered verified?')
    prior=RetrievalService(copied)
    assert any(h.passage_id.startswith('backup-service#') for h in prior.search(question).hits)
    manifest=json.loads((copied/'manifest.json').read_text())
    manifest['documents']=[e for e in manifest['documents'] if e['id']!='backup-service']
    (copied/'manifest.json').write_text(json.dumps(manifest))
    (copied/'backup-service.md').unlink()
    rebuilt=RetrievalService(copied)
    assert not any(h.passage_id.startswith('backup-service#') for h in rebuilt.search(question).hits)
    # Existing processes retain their old in-memory snapshot until replaced.
    assert any(h.passage_id.startswith('backup-service#') for h in prior.search(question).hits)
