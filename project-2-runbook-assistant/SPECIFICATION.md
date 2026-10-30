# Project 2 Specification

## User outcome

A home-lab operator asks an operational question and receives either a source-supported answer with inspectable citations or a clear statement that the approved corpus does not contain enough evidence.

## Phase A input and output

- Input: one question, 10–1,000 characters
- Output: zero to three ranked passages from the approved corpus
- Every passage includes a stable passage ID, document title, version, and excerpt
- Zero evidence is a successful, explicit outcome rather than a forced match

## Policy

- Only manifest-listed documents may be indexed.
- Every document hash must match before ingestion.
- Retrieved text is untrusted data, never system instruction.
- Retrieval quality and answer quality must be scored separately.
- Later model answers may cite only passage IDs supplied by retrieval.
- The system must abstain when evidence is absent or insufficient.

## Phase A acceptance criteria

1. Corpus hashes are verified before parsing.
2. Stable passage IDs are derived from document and section identities.
3. Relevant synthetic questions retrieve an expected passage in the top three.
4. An out-of-scope question returns no evidence.
5. Duplicate passage IDs or unexpected documents fail closed.
6. The baseline uses no model, embedding service, or network dependency.

## Non-goals

- No command execution or remediation
- No production/private documents
- No claim that lexical retrieval is sufficient for the final assistant
- No model-generated answer in Phase A
- No hidden or unverifiable citations

## Revised HTTP and answer contract

- `POST /v1/search` accepts the same question and returns bounded ranked passages without calling the model. `has_evidence` means lexical matches exist, not that they answer the question.
- `POST /v1/answer` returns `question`, `answerable`, `answer`, full `citations`, and `requires_human_review=true`.
- Model output contains strict Boolean `answerable`, answer text, and zero to three unique `citation_ids`. True requires citations; false forbids them. Unknown fields and incoherent combinations fail closed.
- Empty retrieval returns fixed abstention without a model call. With retrieved but insufficient support, validated model abstention also returns fixed application text and no citations.
- A supported description of a conflict is answerable and should cite all competing passages. Conflict detection is prompted and evaluated, not guaranteed by citation membership checks.
- Each returned passage includes a relative source filename, source SHA-256, and normalized-excerpt SHA-256. Passage IDs remain document-plus-heading identities, not content hashes.
- The flat corpus rejects path traversal, absolute paths, links, duplicate file/document entries, and invalid metadata. Parsing uses the bytes that passed digest verification.
- Readiness checks an exact configured model ID in a bounded `/v1/models` listing. Liveness and search remain independent of model readiness.

## Revision acceptance cases and limits

The updated software suite covers related-but-insufficient evidence, inconsistent answerability/citations, no-model search, corpus containment, verified-byte parsing, citation provenance, and reviewed deletion followed by index rebuild. An existing process retains its prior in-memory corpus until it is replaced. Source deletion does not erase old images, backups, or another system's caches.

The model must abstain when asked for facts absent from the synthetic corpus even if system names overlap: administrator password, installation date, or operating-system version. Retain the observed conflict-versus-abstention failure and its correction as development evidence. These cases are not a fresh holdout. Citation membership and hashes do not prove semantic support or document authenticity; support review remains required.
