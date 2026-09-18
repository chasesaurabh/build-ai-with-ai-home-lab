# Project 2 Threat Model

## Assets

- Integrity and provenance of the approved corpus
- Accuracy of citations and abstention
- Separation between document text and application instructions
- Availability of the retrieval and answer service

## Trust boundaries

1. Corpus file to manifest/hash verification
2. Question to input validation
3. Retrieved passage to later model context
4. Model answer to application citation validation

## Primary threats and planned controls

| Threat | Phase A control | Later control |
|---|---|---|
| Unapproved or modified document enters the index | Closed manifest and SHA-256 verification | Signed/versioned release manifest |
| A document contains instructions for the model | Retrieval treats all passage text as inert content | Delimited context, explicit instruction hierarchy, adversarial cases |
| Retrieval returns a plausible but irrelevant passage | Labeled query set and top-k scoring | Citation-support review independent of answer fluency |
| The system invents a source | Stable IDs come only from parsed manifest documents | Reject citations outside the retrieved-ID set |
| Evidence is missing | Zero-match behavior | Explicit no-answer response; no parametric fallback |
| Sources conflict | Not present in the initial baseline corpus | Conflict fixtures and answer policy before release |
| Deleted material remains searchable | Rebuild tests planned | Deletion, backup, restore, and stale-index checks |

## Stop conditions

- A hash mismatch is ignored.
- A non-manifest file is indexed automatically.
- A generated answer can cite a passage that retrieval did not supply.
- Missing evidence produces an unsupported operational recommendation.
- Retrieved document instructions can alter application policy or tools.
