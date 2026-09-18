# Evidence and Reproduction

The four projects preserve the distinction between software tests, behavioral evals, human review, and deployment evidence.

## Recorded results

| Project | Software tests | Development behavior | Untouched holdout | Important limitation |
|---|---:|---|---|---|
| 1 | 22 passed | Nemotron 12/12; deterministic 12/12 | Nemotron 9/12; deterministic 2/12 | Three affected-system boundary misses |
| 2 | 23 passed | Retrieval 10/10; answerability/citation 10/10 | Same recorded counts on ten holdout cases | Small clean Markdown corpora; blind review pending |
| 3 | 24 passed | Five safe supported diagnoses | Five safe results; 4/5 frozen-rubric passes | Static fixtures and no real monitoring identity |
| 4 | 20 passed | Five normal and five adversarial cases | 5/5 first-run holdout | Independent approval-package usability review pending |

These numbers describe the frozen synthetic sets only. They are not accuracy percentages for other users, models, hardware, corpora, or environments.

## Reproduction sequence

1. Record the source commit and dirty-state result.
2. Run the project test image without a model.
3. Run development cases and preserve raw output under `results/`.
4. Freeze code, prompt, model, provider, cases, and scorer.
5. Run holdout once.
6. Inspect individual misses and provider errors.
7. Exercise the documented dependency-failure and restoration path.
8. Record the result as a new manifest rather than overwriting the historical claim.

If you change a prompt, model, provider, schema, corpus, scorer, or environment after viewing holdout, start a new development/holdout cycle.

