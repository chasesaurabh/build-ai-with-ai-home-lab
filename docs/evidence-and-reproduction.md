# Evidence and Reproduction

Software tests, model behavior, reviewer judgments and runtime demonstrations
answer different questions. None alone certifies production suitability.

## October 30 revision observations

| Project | Software tests | Recorded model behavior | Important limitation |
|---|---:|---|---|
| 1 | 52 passed | Earlier 11/12 then 12/12; current-adapter replay 12/12; zero provider errors | Rules replay: 11/12 development, 1/12 old holdout; no new unseen model holdout |
| 2 | 43 passed | Final run: 10/10 development, 2/2 known adversarial, 3/3 related-but-insufficient abstentions | Earlier conflict-abstention failure preserved; answer support checked by the same AI editor |
| 3 | 56 passed | 5/5 development, 3/5 old-holdout replay; zero provider/policy errors | Healthy-summary vocabulary and missing required TLS status call remain scorer misses |
| 4 | 44 passed | 5/5 development, 5/5 adversarial, 5/5 old-holdout replay; zero errors | Synthetic configuration harness does not pull images or scale real replicas |

These 195 tests verify application properties on the checked source. The four
PowerShell first-run scripts also exercised actual local requests, failure
responses, restart or candidate restoration and scoped cleanup. Dependency
refresh validation reran all four scripts; see [dependency scope](dependencies.md).
The model scores above came from the earlier recorded application experiments,
not from that dependency-only validation.

The revision model was Nemotron Super 120B NVFP4; see [provider identity](model-provider.md).
Small synthetic sets and already-viewed cases cannot establish general accuracy,
speed, privacy, robustness or a fresh holdout estimate. Qualitative support and
risk reviews so far are AI-editor assessments, not independent human reviews.
The [local release evidence bundle](../evidence/2026-10-revision/README.md) retains seven exact model-output files and selected run identities. It is still a locally prepared candidate, not a published or independently reviewed release.

## Preserved first-edition observations

| Project | Software tests | Development behavior | Original holdout observation |
|---|---:|---|---|
| 1 | 22 | Model 12/12; rules 12/12 | Model 9/12; rules 2/12 |
| 2 | 23 | Retrieval and answerability/citation 10/10 | Ten original holdout cases; historical support review recorded separately |
| 3 | 24 | Five safe supported diagnoses | Five safe results; 4/5 frozen-rubric passes |
| 4 | 20 | Five normal and five adversarial cases | 5/5 first-run holdout |

Those September results used the first-edition code and provider. Project
`EVIDENCE.md` files retain their details. They do not establish present behavior.
Once viewed or used to tune a revision, the same holdout cases become known
regression material; renaming a replay does not make it unseen.

## Reproduction sequence

1. Record the source commit and dirty-state result, dependency inventory and
   image identity.
2. Run the project's software tests without a model.
3. Run development cases and retain raw outputs under the ignored `results/`.
4. Freeze code, prompt, model, provider, cases and scorer before a new holdout.
5. Run genuinely unseen holdout cases once; preserve misses and provider errors.
6. Inspect each result and distinguish structural checks from semantic review.
7. Exercise dependency failure and restoration, not only a successful request.
8. Save a new run manifest. Never overwrite an earlier failed run or claim.

If you change the system after seeing a holdout, begin a new development/holdout
cycle for an unbiased estimate. Previously exposed sets remain useful regression
checks when labeled honestly.
