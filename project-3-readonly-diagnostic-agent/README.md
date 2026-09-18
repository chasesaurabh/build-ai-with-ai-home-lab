# Project 3 — Read-Only Diagnostic Agent

Let the model choose among four typed, read-only observation tools for one approved service, then synthesize only from evidence produced during the current run.

## Boundary

The project contains no shell, arbitrary path, arbitrary URL, write tool, repair action, or deployment socket. Application code binds service scope, validates the complete plan, enforces tool and time budgets, dispatches named handlers, and issues evidence IDs.

## Test

```text
docker build --target test -t build-ai-home-lab-project3-test .
docker run --rm build-ai-home-lab-project3-test
```

## Run the agent eval

```text
python -m evals.run_agent_eval --base-url http://127.0.0.1:8100 --model nemotron-35-lightning --output results/project3-development.json
```

Use `--fixture fixtures-holdout --cases evals/holdout-cases.json` only after freezing the application and scorer.

The verified implementation uses direct typed tools. MCP is intentionally not required; add it only as a separately tested transport over the same capability contract.

See [EVIDENCE.md](EVIDENCE.md), [SPECIFICATION.md](SPECIFICATION.md), and [THREAT_MODEL.md](THREAT_MODEL.md).

