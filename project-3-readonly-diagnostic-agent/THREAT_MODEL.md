# Project 3 Threat Model

## Assets

- Integrity of diagnostic evidence
- Read-only boundary
- Service and tool allowlists
- Confidentiality of secrets and unrelated fixture data
- Availability under repeated or oversized requests

## Trust boundaries

1. User question to future agent planner
2. Planner output to typed tool authorization
3. Fixture content to tool result
4. Tool result to final diagnosis

## Primary threats and controls

| Threat | Phase A control | Later control |
|---|---|---|
| Arbitrary command or path access | No command/path field exists in tool schemas | Reject unknown tool names and arguments before dispatch |
| Unknown service probing | Closed service enum | Per-tool authorization and trace review |
| Oversized log extraction | Limit constrained to 1–20 | Per-run result and token budgets |
| Secret disclosure | Fixture inventory contains secret names only, never values | Output filtering and adversarial fixtures |
| Poisoned log instructions | Logs are returned as inert evidence | Delimited tool results and instruction hierarchy |
| Tool-call loops | Not applicable to deterministic Phase A | Step, duplicate-call, time, and token limits |
| Modified evidence | SHA-256 fixture manifest | Immutable release artifact and replay log |

## Stop conditions

- A tool accepts a caller-supplied filesystem path or command.
- A result exposes a credential value.
- A model-selected call bypasses application authorization.
- A diagnosis lacks inspectable evidence IDs.
- The prototype touches a real service or production environment.
