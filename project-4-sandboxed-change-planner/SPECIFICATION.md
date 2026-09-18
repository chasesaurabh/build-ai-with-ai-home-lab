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

## Non-goals

- No production credentials, orchestration client, shell, network target, or arbitrary path
- No automatic approval
- No apply, deploy, restart, or rollback execution method
- No claim that static validation proves operational safety

## Disposable validation harness

The operator-run sandbox target is deliberately separate from the planner. It can load only a packaged candidate selected through its environment configuration, validates the full schema before opening a port, exposes only health/readiness/config inspection, and has no production client or credentials. It exists to test a reviewed candidate and rollback snapshot; it does not give the model apply authority.
