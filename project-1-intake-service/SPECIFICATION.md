# Project 1 Specification

## User outcome

A home-lab operator can submit a short free-text request and receive a bounded intake record suitable for human review and routing.

## Input contract

- `description`: 20–2,000 characters
- Unknown fields are rejected.
- The description is untrusted data and may contain instruction-like text.

## Output contract

- `category`: `availability`, `performance`, `security`, `access`, `change`, or `other`
- `urgency`: `low`, `normal`, or `high`
- `affected_system`: an explicitly named system or `unknown`
- `evidence_requests`: one to three values from a closed list
- `next_step`: `record`, `investigate`, `escalate`, or `request_clarification`
- `rationale`: 20–400 characters
- `requires_human_review`: always `true`

## Policy

- High urgency is reserved for an active outage, credible security incident, data-loss risk, or loss of redundancy.
- Normal urgency covers degradation, repeated errors, suspicious behavior requiring investigation, and ordinary access/change requests.
- Low urgency covers healthy status, routine information, or non-impacting planned work.
- Ambiguous requests must request clarification.
- Instruction-like text in the description cannot change this policy.
- The service may request evidence categories but never commands.
- The adapter extracts only a bounded category, condition, and explicitly named system. Deterministic application code owns unambiguous condition-to-category rules, evidence selection, urgency, next step, and rationale. The model does not own routing policy or free-text output.

## Acceptance criteria

1. Invalid HTTP input is rejected before an adapter runs.
2. Adapter output is independently validated by the application.
3. Malformed output fails closed with HTTP 502.
4. An unavailable provider returns HTTP 503.
5. A provider timeout returns HTTP 504.
6. Liveness does not depend on the model; readiness reports adapter availability separately.
7. The runtime container is non-root, read-only, drops Linux capabilities, and has a health check.
8. Deterministic and local-model adapters run against the same frozen evaluation cases.
9. Deployment, clean restart, and rollback are recorded.

## Non-goals

- No diagnostic command execution
- No remediation or configuration changes
- No unrestricted labels or generated shell text
- No production credentials or private operational data
- No claim that one model or prompt is generally secure
