# Project 4 — Sandboxed Change Planner

Convert a free-text request into typed desired values, then build a deterministic diff, validation report, risk summary, rollback snapshot, and human-review package.

## Boundary

The AI application has no apply, deploy, approve, rollback, credential, shell, or production-client capability. A separate operator-run sandbox can consume an already packaged candidate for disposable validation.

## Test

```text
docker build --target test -t build-ai-home-lab-project4-test .
docker run --rm build-ai-home-lab-project4-test
```

## Run the model eval

```text
python -m evals.run_model_eval --base-url http://127.0.0.1:8100 --model nemotron-35-lightning --output results/project4-development.json
```

Use the adversarial and holdout case files only according to the documented freeze procedure.

## Run a disposable candidate

Review the candidate JSON and Compose file first. The supplied default starts only the synthetic good candidate on a loopback port:

```text
docker compose up --build
```

The bad-candidate and baseline files exist to test rejection and restoration. They are operator-run fixtures, not model-callable tools.

See [EVIDENCE.md](EVIDENCE.md), [SPECIFICATION.md](SPECIFICATION.md), and [THREAT_MODEL.md](THREAT_MODEL.md).

