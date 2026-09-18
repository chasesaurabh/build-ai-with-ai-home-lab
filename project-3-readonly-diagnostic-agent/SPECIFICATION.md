# Project 3 Specification

## User outcome

A home-lab operator asks why an approved simulated service is unhealthy and receives a bounded diagnosis whose observations can be traced to read-only tool results.

## Core contract

- Approved services: `media-server`, `backup-service`, `reverse-proxy`, and `storage-pool`
- Approved tools: service status, recent logs, resource metrics, and configuration inventory
- Log limit: 1–20 entries
- No caller-supplied paths, commands, URLs, credentials, or arbitrary query language
- Every result includes a stable evidence identifier
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
2. Application code validates and dispatches every call and owns the time and call budgets.
3. A diagnosis may cite only evidence identifiers produced by its own run.
4. The HTTP process runs as a non-root user with a read-only root filesystem, all capabilities dropped, no-new-privileges, and a loopback-only published port.
5. Model unavailability produces an unhealthy readiness result and a controlled diagnostic error while liveness remains independent.
6. Restart and rollback restore a working diagnosis path without changing the read-only tool boundary.

## Non-goals

- No host commands or Docker control
- No filesystem browsing
- No access to the real home lab
- No remediation or configuration changes
- No MCP server in the core path
- No claim of safe autonomous remediation
- No production-infrastructure access or general safety claim
