# Project 4 Threat Model

| Threat | Control | Evidence target |
|---|---|---|
| Request asks the model to apply a change | Application exposes proposal preparation only; no apply method or infrastructure client exists | Interface and negative tests |
| Model invents a field, command, path, or URL | Closed proposal schema and extra-field rejection | Adversarial schema tests |
| Proposal silently targets another service | Immutable literal `service_id` loaded from a checksum-locked fixture | Validation tests |
| Model lies about the old value | Application compares every `before` value with the verified source | Mismatch test |
| Proposed values escape safe bounds | Full staged configuration is independently validated | Boundary tests |
| Too many changes obscure review | Two-field maximum and unique-field rule | Budget tests |
| Rollback prose is incomplete | Package embeds the exact verified source object | Equality test |
| Planner mutates source state while staging | Work occurs on an in-memory copy and fixture hash is rechecked | Immutability test |
| Secrets leak into review output | Fixture contains no secret fields and proposal fields are an allowlist | Output scan test |

Residual risk: a valid-looking configuration can still be operationally wrong. Later gates must use a disposable deployment and a human usability review; this experiment does not grant apply authority.
