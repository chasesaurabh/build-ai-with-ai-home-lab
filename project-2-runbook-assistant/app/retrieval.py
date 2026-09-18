from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


class CorpusError(RuntimeError):
    """The approved corpus could not be verified or parsed safely."""


@dataclass(frozen=True)
class Passage:
    passage_id: str
    document_title: str
    document_version: str
    section_title: str
    text: str


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "can", "do", "for", "from",
    "how", "i", "in", "is", "it", "my", "of", "on", "or", "should", "the", "to",
    "what", "when", "with",
}

_NORMALIZE = {
    "attempts": "attempt",
    "checks": "check",
    "completed": "complete",
    "errors": "error",
    "failed": "fail",
    "failure": "fail",
    "logs": "log",
    "requests": "request",
    "services": "service",
}


def _tokens(value: str) -> list[str]:
    raw = re.findall(r"[a-z0-9]+", value.casefold())
    return [_NORMALIZE.get(token, token) for token in raw if token not in _STOPWORDS]


def _slug(value: str) -> str:
    slug = "-".join(_tokens(value))
    if not slug:
        raise CorpusError("A section heading produced an empty passage identifier.")
    return slug


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_document(path: Path, document_id: str, version: str) -> list[Passage]:
    title: str | None = None
    current_section: str | None = None
    body: list[str] = []
    passages: list[Passage] = []

    def flush() -> None:
        nonlocal body
        if current_section is None:
            body = []
            return
        text = " ".join(line.strip() for line in body if line.strip())
        if text:
            passages.append(
                Passage(
                    passage_id=f"{document_id}#{_slug(current_section)}",
                    document_title=title or document_id,
                    document_version=version,
                    section_title=current_section,
                    text=text,
                )
            )
        body = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# ") and title is None:
            title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            current_section = line[3:].strip()
        elif current_section is not None:
            body.append(line)
    flush()
    if title is None or not passages:
        raise CorpusError(f"Document {path.name} lacks a title or usable sections.")
    return passages


def load_corpus(corpus_dir: Path) -> list[Passage]:
    manifest_path = corpus_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise CorpusError("The corpus manifest contains no documents.")

    allowed_files = {entry["file"] for entry in documents}
    actual_files = {path.name for path in corpus_dir.glob("*.md")}
    unexpected = actual_files - allowed_files
    if unexpected:
        raise CorpusError(f"Unapproved corpus files found: {', '.join(sorted(unexpected))}")

    passages: list[Passage] = []
    seen_ids: set[str] = set()
    for entry in documents:
        path = corpus_dir / entry["file"]
        if not path.is_file():
            raise CorpusError(f"Approved corpus file is missing: {entry['file']}")
        if _sha256(path) != entry["sha256"]:
            raise CorpusError(f"Hash mismatch for approved corpus file: {entry['file']}")
        for passage in _parse_document(path, entry["id"], entry["version"]):
            if passage.passage_id in seen_ids:
                raise CorpusError(f"Duplicate passage identifier: {passage.passage_id}")
            seen_ids.add(passage.passage_id)
            passages.append(passage)
    return passages


def retrieve(question: str, passages: list[Passage], top_k: int = 3) -> list[tuple[Passage, float]]:
    if top_k < 1 or top_k > 3:
        raise ValueError("top_k must be between 1 and 3")
    query_terms = _tokens(question)
    if not query_terms:
        return []

    document_terms = [
        _tokens(f"{passage.document_title} {passage.section_title} {passage.text}")
        for passage in passages
    ]
    document_frequency = Counter(
        term for terms in document_terms for term in set(terms)
    )
    average_length = sum(len(terms) for terms in document_terms) / len(document_terms)
    query_counts = Counter(query_terms)
    results: list[tuple[Passage, float]] = []

    for passage, terms in zip(passages, document_terms, strict=True):
        frequencies = Counter(terms)
        score = 0.0
        for term, query_weight in query_counts.items():
            frequency = frequencies[term]
            if frequency == 0:
                continue
            inverse_document_frequency = math.log(
                1 + (len(passages) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5)
            )
            length_normalization = frequency + 1.5 * (
                0.25 + 0.75 * len(terms) / average_length
            )
            score += query_weight * inverse_document_frequency * (frequency * 2.5 / length_normalization)
        if score > 0:
            results.append((passage, round(score, 6)))

    return sorted(results, key=lambda item: (-item[1], item[0].passage_id))[:top_k]
