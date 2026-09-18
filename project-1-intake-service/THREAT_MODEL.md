# Project 1 Threat Model

## Assets

- Integrity of the intake record
- Availability of the service
- Provider endpoint configuration
- Logs and synthetic evaluation data

## Trust boundaries

1. User description to application input validation
2. Validated request to model adapter
3. Provider response to application-owned output validation
4. Container to host-local model endpoint

## Primary threats and controls

| Threat | Control in this prototype | Residual risk |
|---|---|---|
| Instruction-like request text changes policy | Untrusted-data instruction, closed output schema, behavioral cases | A model can still misclassify novel attacks |
| Model invents a system | Prompt requires explicit evidence; `unknown` is available; eval cases score invention | Semantic validation is incomplete |
| Model emits commands | The model emits only two closed enums and a bounded system name; the application creates evidence, next step, and rationale | A malicious system-name string remains display-only and is length-bounded |
| Model changes routing policy | Adapter emits a bounded condition; application code owns unambiguous category rules, evidence selection, urgency, and next step | A wrong extracted condition can still lead to wrong routing |
| Malformed or partial provider output | JSON parsing plus independent Pydantic validation | Repeated failures can reduce availability |
| Provider is slow or unavailable | Explicit timeout and separate 503/504 responses | No retry is enabled in this prototype |
| Container compromise | Non-root user, read-only root filesystem, no added capabilities | Host networking still exposes the configured model endpoint |
| Sensitive text leaves the lab | Default adapter points to a host-local endpoint | A future hosted adapter requires a separate data-exposure decision |

## Stop conditions

- The adapter bypasses application validation.
- The model directly controls urgency or the operational next step.
- A request causes command execution or infrastructure mutation.
- Secrets or private production data appear in fixtures, logs, or images.
- The runtime requires privileged container access.
