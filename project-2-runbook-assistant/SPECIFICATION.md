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
