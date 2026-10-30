# Project 4 Evidence Summary

## October 30 revision

- 44 software tests passed with external networking disabled.
- Baseline probes reproduced mutable rollback sharing, acceptance of a parent-path source, and directionally incorrect maintenance risk text; fixes are covered by regression tests.
- Model-facing changes now contain field and after only; application code supplies verified before-values.
- Exact PowerShell `scripts/planner-first-run.ps1` passed: generated review package, file hashes, candidate startup/restart, invalid-candidate exit1, restoration of all baseline values/readiness, scoped cleanup.
- Live Nemotron Super 120B NVFP4: 5/5 known development, 5/5 known adversarial, 5/5 exposed old-holdout replay; zero provider/policy errors under the unchanged scorer. Reported model identity checked before/after, not weight-file hashes.
- Actual model CLI export produced replicas2to3 and awaiting-human-approval; deliberately unavailable provider exited2 without creating a package directory.
- Full packages are retained for review. These are synthetic regression results; the harness does not pull images or scale replicas. Independent review remains pending.

## Preserved first-edition observations

- Final software suite: 20 passed
- Normal development cases: 5/5
- Adversarial development cases: 5/5
- First-run untouched holdout: 5/5
- Provider/policy errors in the final development and holdout runs: 0
- Sandboxed deployment: good candidate started; bad candidate failed before readiness; exact baseline restored
- Structural invariant: apply capability absent from the planner

The evidence supports a proposal-and-disposable-validation pattern only. It does not establish that a schema-valid change is safe for a real service. Independent approval-package usability review remains required.


Selected synthetic outputs and run identities are staged in the [revision evidence bundle](../evidence/2026-10-revision/README.md). Local staging is not public release verification.
