# Project 1 — Structured Home-Lab Intake Service

Turn one free-text home-lab report into a validated intake decision. The model may extract only category, condition, and explicitly named affected-system text. Application code owns urgency, evidence requests, next step, rationale, validation, and HTTP behavior.

## Boundary

The service cannot run diagnostics, read logs, contact the reported system, execute commands, or apply a change. Instruction-like request text remains data.

## Test

For the complete no-model first-run exercise, use PowerShell 7 from the repository root:

```powershell
pwsh -NoProfile -File ./scripts/first-run.ps1
```

It tests and starts a disposable loopback-only service, verifies a request and input rejection, restarts it, verifies the response, and removes its own container. It requires a running Linux-container Docker engine and package/image downloads during builds. No GPU or API key is needed. The default port is 18088; use `-Port 18089` if occupied. Existing containers with the exercise name are never removed automatically.

The deterministic adapter is a deliberately limited teaching baseline. Unsupported conditions request clarification; healthy decisions require supported whole statements. It still mishandles some negations (for example, "not offline" escalates), quotations, historical reports, and multi-system descriptions. It is not a production incident interpreter. The service does not automatically fail over to it on model errors.

```text
docker build --target test -t build-ai-home-lab-project1-test .
docker run --rm build-ai-home-lab-project1-test
```

## Run the deterministic eval

From an environment with `requirements-dev.txt` installed, create the ignored `results` directory first (`mkdir results` if it does not exist):

```text
python -m evals.run_evals --adapter deterministic --output results/project1-deterministic.json
```

## Run the model eval

```text
python -m evals.run_evals --adapter local --base-url http://127.0.0.1:8100 --model nemotron-35-lightning --output results/project1-development.json
```

Use `--cases evals/holdout-cases.json` only after freezing the application, prompt, model, provider, and scorer.

## Start the service

Review `compose.yaml`, especially the endpoint, alias, and loopback port. It now defaults to the deterministic adapter, which needs no model. From this project directory:

```text
docker compose up --build
```

To select a locally hosted compatible model, use a separate terminal session and set `APP_ADAPTER=local`, `MODEL_BASE_URL`, and `MODEL_ID` explicitly before starting Compose. `MODEL_BASE_URL` is the origin without `/v1`; the adapter appends API paths. From Docker Desktop, a host service commonly uses `http://host.docker.internal:8100`; verify your own port and connectivity. The model ID must exactly match `/v1/models`. An alias does not establish the underlying model weights.

Readiness checks the bounded model listing and exact configured ID. It does not prove that structured generation works; verify a representative request. The adapter currently targets a local endpoint without API-key authentication and sends a provider-specific thinking control. Hosted providers require separate compatibility work. Stop only this Compose project with `docker compose down` when finished.

Revision evidence: the expanded Project 1 suite passed 52 tests. Replayed known development cases scored 11/12 for the revised rules; replayed old holdout cases scored 1/12. Two live runs on the existing development cases with Nemotron Super 120B NVFP4 through vLLM 0.30.0 scored 11/12 and 12/12, with no provider errors. These are bounded, already-known cases, not new holdout accuracy. Preserve the first-edition evidence below as historical; it describes a different release/model configuration.

See [EVIDENCE.md](EVIDENCE.md), [SPECIFICATION.md](SPECIFICATION.md), and [THREAT_MODEL.md](THREAT_MODEL.md).


Current-adapter release check: the later known-development replay also passed 12/12 with zero provider errors. The exact output and source identity are in [live-intake-013](../evidence/2026-10-revision/live-intake-013/manifest.json); earlier runs remain historical revision evidence, not final-adapter measurements.
