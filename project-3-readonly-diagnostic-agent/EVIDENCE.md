# Project 3 Evidence Summary

## October 30 revision

- 56 software tests passed in the original revision test container with external networking disabled. That run retained a Starlette/AnyIO deprecation warning. The dependency refresh reran the same suite and first-run script; use the later dependency validation for the current environment.
- Exact PowerShell `scripts/diagnostic-first-run.ps1` passed with real HTTP fixed observations, model-unavailable 503, extra-action 422, restart, stable payload hashes, fresh IDs and cleanup.
- Restricted runtime model diagnosis returned 200 before and after restart. The documented Compose route also returned ready and a real model diagnosis, followed by scoped cleanup.
- Live Nemotron Super 120B NVFP4: 5/5 known-development passes; 3/5 exposed old-holdout replay passes under the unchanged scorer; zero provider/policy errors. Reported model identity checked before/after, not weight-file hashes.
- Replay misses: healthy media vocabulary did not match; TLS diagnosis omitted a required status call. Same-editor support review found the observations supported within the synthetic fixtures, with causal-wording and minimal-access limitations. Scores were not rewritten.
- Fresh IDs fix acceptance of old citations on identical data; duplicate effective observations are rejected; typed fixture bounds reject unexpected configuration fields even with a matching manifest hash; fixed workflow no longer selects a cause by service name.
- Time budgets reject late results and bound provider socket timeouts by remaining time; they do not forcibly cancel running code.

These are limited simulated-project results, not production-security assurance or an unseen holdout. Complete revision records are maintained with the book's private production evidence; the public code release will carry its verified release-specific evidence bundle.

## Preserved first-edition observations

- Final software suite: 24 passed
- Development diagnoses: 5/5 safe, supported, and policy-bounded
- Untouched holdout: 5/5 safe and supported; 4/5 frozen-rubric passes
- Provider/policy errors in the final development and holdout runs: 0
- Adversarial evidence: instruction-like question and poisoned log text did not create execution or unsupported claims
- Deployment evidence: loopback startup, restart, controlled provider failure, recovery, and rollback passed

The rubric miss was conservative tool selection, not unsafe behavior. Fixtures are static and do not establish performance against real monitoring systems, identities, races, or production permissions.


Selected synthetic outputs and run identities are staged in the [revision evidence bundle](../evidence/2026-10-revision/README.md). Local staging is not public release verification.
