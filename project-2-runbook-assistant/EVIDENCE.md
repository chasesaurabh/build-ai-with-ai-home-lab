# Project 2 Evidence Summary

## October 30 revision

- 43 software tests passed with external networking disabled.
- Final live Nemotron Super 120B NVFP4 run: 10/10 development retrieval and answerability/citation checks, 2/2 known adversarial cases, 3/3 related-but-insufficient abstentions; zero provider errors.
- Earlier conflict case failed before prompt clarification. That failure is preserved; the later pass is development evidence, not an unseen holdout.
- The same AI editor checked passage support for ten development and two adversarial outputs. This was not independent human review.
- PowerShell first run exercised HTTP search, zero-hit abstention, model-unavailable 503, extra-field 422, restart and cleanup. Synthetic Markdown corpora do not establish production parsing or universal injection resistance.

See [shared evidence scope](../docs/evidence-and-reproduction.md).

## Preserved first-edition observations

- Final software suite: 23 passed
- Development retrieval: 10/10 expected evidence and citation checks
- Untouched-holdout retrieval: 10/10
- Development and holdout Nemotron answerability/citation checks: 10/10 each
- Recorded passage-support review: 20/20 answers supported by cited passages
- Adversarial cases: document injection and equal-authority conflict behavior passed
- Deployment evidence: startup, restart, controlled provider failure, and rollback passed

The corpora are small, clean, synthetic Markdown sets. Results do not establish broad document parsing, universal prompt-injection resistance, or independent correctness.

