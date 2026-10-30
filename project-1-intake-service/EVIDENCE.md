# Project 1 Evidence Summary

## October 30 revision

- 52 software tests passed with external networking disabled.
- Rules replay: 11/12 known development and 1/12 exposed old holdout.
- Live Nemotron Super 120B NVFP4: development runs 11/12 then 12/12, zero provider errors. Both runs are retained; no new untouched-holdout claim.
- PowerShell first run exercised actual HTTP intake, explicit local-mode failure, input boundaries, restart and cleanup without a model.
- Schema-valid extraction still needs application policy. A single successful run does not establish general classification accuracy.

See [shared evidence scope](../docs/evidence-and-reproduction.md).

## Preserved first-edition observations

- Final software/network suite: 22 passed
- Development set: deterministic 12/12; Nemotron 12/12
- Untouched holdout: deterministic 2/12; Nemotron 9/12
- Provider errors in the two final Nemotron runs: 0
- Deployment evidence: startup, readiness, representative request, restart, controlled provider failure, failed-update detection, and rollback passed

The three holdout misses were affected-system boundary errors. The service remains a limited prototype for synthetic intake, not a diagnostic system or general accuracy claim.


Current-adapter release check: the later known-development replay also passed 12/12 with zero provider errors. The exact output and source identity are in [live-intake-013](../evidence/2026-10-revision/live-intake-013/manifest.json); earlier runs remain historical revision evidence, not final-adapter measurements.
