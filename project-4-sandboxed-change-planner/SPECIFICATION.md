# Project 4 Specification

## User outcome

A home-lab operator receives a reviewable configuration diff, validation record, risk summary, and exact rollback snapshot. Nothing is applied to a live system.

## Core contract

- The only target is the manifest-listed disposable `photo-api` configuration.
- A proposal may change at most two fields from `image_tag`, `replica_count`, `request_timeout_seconds`, and `maintenance_mode`.
- `service_id` is immutable.
- Every proposed value must pass the complete configuration schema after staging.
- Validation checks are fixed by application code; the model cannot supply commands or validators.
- The approval package always says `apply_capability: absent` and `human_review_required: true`.
- Rollback is the exact verified pre-change configuration, not generated prose.
- Model-facing proposals contain only field and strict typed after values. The application supplies before-values; the internal explicit-before interface also checks them.
- Returned source/rollback objects do not share mutable state with the planner.
- The fixture manifest names a flat JSON source; path and symlink escapes are rejected, and source bytes are limited to 64 KiB.
- CLI export creates a new review directory and hashes the complete package, candidate and rollback files. Hashes are an integrity inventory, not an approval or signature.

## Non-goals

- No production credentials, orchestration client, shell, network target, or arbitrary path
- No automatic approval
- No apply, deploy, restart, or rollback execution method
- No claim that static validation proves operational safety

## Disposable validation harness

The operator-run sandbox target is deliberately separate from the planner. It loads a JSON file at the operator-selected CONFIG_PATH, validates the full schema before opening a port, exposes only health/readiness/config inspection, and has no production client or credentials. The supplied script mounts only its synthetic review directory read-only into the target. The harness is not an approval verifier: it does not require a signed manifest or check that a human approved the file. It does not pull images or scale containers; image_tag and replica_count are synthetic state. Maintenance mode controls readiness. It exists to test configuration flow and restoration, not operational deployment safety.
