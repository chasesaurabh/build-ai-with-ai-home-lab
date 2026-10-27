# Project 1 — Structured Home-Lab Intake Service

Turn one free-text home-lab report into a validated intake decision. The model may extract only category, condition, and explicitly named affected-system text. Application code owns urgency, evidence requests, next step, rationale, validation, and HTTP behavior.

## Boundary

The service cannot run diagnostics, read logs, contact the reported system, execute commands, or apply a change. Instruction-like request text remains data.

## Test

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

Review `compose.yaml`, especially the endpoint, alias, and loopback port, then run:

```text
docker compose up --build
```

See [EVIDENCE.md](EVIDENCE.md), [SPECIFICATION.md](SPECIFICATION.md), and [THREAT_MODEL.md](THREAT_MODEL.md).

