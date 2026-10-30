# Project 3 Specification

## User outcome

A home-lab operator asks why an approved simulated service is unhealthy and receives a bounded diagnosis whose observations can be traced to read-only tool results.

## Core contract

- Approved services: `media-server`, `backup-service`, `reverse-proxy`, and `storage-pool`
- Approved tools: service status, recent logs, resource metrics, and configuration inventory
- Log limit: 1–20 entries
- No caller-supplied paths, commands, URLs, credentials, or arbitrary query language
- Every observation receives a fresh evidence identifier; payload_sha256 separately identifies normalized data
- Fixture integrity is verified before any tool runs

## Acceptance criteria

1. Unknown services and tools are rejected before fixture access.
2. Tool arguments use closed types and bounded numeric values.
3. Tool results contain only fixture data approved for that tool.
4. Logs are capped and newest-first.
5. Configuration inventory excludes secret values.
6. The deterministic workflow links every diagnosis to evidence IDs.
7. Modified or unmanifested fixture files fail closed.

## Agent and deployment criteria

1. The model may propose only one to four unique typed calls for the requested service.
2. Application code validates and dispatches every call, rejects repeated tool/service pairs, and owns call and acceptance-time budgets. Remaining time is passed to the provider. This is not hard cancellation of running code.
3. A diagnosis may cite only evidence identifiers produced by its own run.
4. The HTTP process runs as a non-root user with a read-only root filesystem, all capabilities dropped, no-new-privileges, and a loopback-only published port.
5. Model unavailability produces an unhealthy readiness result and a controlled diagnostic error while liveness remains independent.
6. Restart and rollback restore a working diagnosis path without changing the read-only tool boundary.

## Revised bounded data and fixed workflow

- The manifest names a flat JSON file; parent paths and symlink escapes are rejected. The same captured bytes are hashed and parsed, bounded to one MiB.
- Service-specific status, metric, log and configuration schemas reject extra fields and out-of-range values. Fixture logs are limited to 100 entries per service; returned logs to 20, with messages at most 2,000 characters.
- Configuration exposes ordinary approved settings and secret names, not secret values or presence flags. Schema validation does not detect a secret accidentally placed in an allowed text field.
- POST /v1/diagnose-fixed accepts only service and returns a three-observation DiagnosticRun without a model. It is explicitly selected, never an automatic provider fallback.
- The fixed workflow reports fixture observations, not a cause hard-coded by service name. Current-run citations do not establish semantic correctness or causality.

## Non-goals

- No host commands or Docker control
- No filesystem browsing
- No access to the real home lab
- No remediation or configuration changes
- No MCP server in the core path
- No claim of safe autonomous remediation
- No production-infrastructure access or general safety claim
