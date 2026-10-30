# Project 3 — Read-Only Diagnostic Agent

Let the model choose among four typed, read-only observation tools for one approved service, then synthesize only from evidence produced during the current run.

## Boundary

The project contains no shell, arbitrary path, arbitrary URL, write tool, repair action, or deployment socket. Application code binds service scope, validates the complete plan, enforces a call limit, checks elapsed time, passes remaining time to provider requests, dispatches named handlers, and issues fresh observation IDs. Time checks reject late results; they do not forcibly cancel a blocking adapter.

## Start without a model

From the repository root in PowerShell 7, with Docker running Linux containers:

```powershell
./scripts/diagnostic-first-run.ps1
```

This builds and tests the service, demonstrates `/v1/diagnose-fixed`, checks an unavailable model and an invalid action field, restarts, compares data hashes and fresh IDs, then removes its own container. Use `-Port 18095` if the default 18093 is occupied. Synthetic fixtures never query your real lab. The fixed endpoint is explicitly selected, not automatic failover.

## Test

```text
docker build --target test -t build-ai-home-lab-project3-test .
docker run --rm --network none build-ai-home-lab-project3-test
```

## Run the agent eval

From this project directory, build the test image above. In PowerShell 7, inspect your provider listing and set its actual model ID:

```powershell
(Invoke-RestMethod 'http://127.0.0.1:8100/v1/models').data | Select-Object id, root
$env:MODEL_ID = 'replace-with-an-id-from-your-listing'
docker run --rm --add-host host.docker.internal:host-gateway `
  build-ai-home-lab-project3-test python -m evals.run_agent_eval `
  --base-url http://host.docker.internal:8100 --model $env:MODEL_ID `
  --output /tmp/project3-development.json
```

The evaluator prints counts; the temporary output above disappears with the container. To retain full JSON, create a local `results` directory and mount it at `/results`, then use `--output /results/project3-development.json`. Full traces include tool data and should stay synthetic.

Use `--fixture fixtures-holdout --cases evals/holdout-cases.json` to replay the published holdout. It is now exposed regression material. Create a separate unseen set before claiming a new holdout evaluation. The compatibility default alias is historical; always pass your actual ID and record its underlying model identity. An alias alone does not establish which weights ran.

## Run model diagnosis over HTTP

With `MODEL_ID` set as above, run from this project directory in PowerShell 7:

```powershell
docker compose -p build-ai-diagnostic-reader up -d --build
Invoke-RestMethod 'http://127.0.0.1:18083/ready'
$body = @{service='media-server'; question='Why is the media server slow?'} | ConvertTo-Json
Invoke-RestMethod 'http://127.0.0.1:18083/v1/diagnose' `
  -Method Post -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 8
docker compose -p build-ai-diagnostic-reader down
```

If the service is still starting, wait briefly and repeat readiness. The published port is loopback-only. The default provider route is `host.docker.internal:8100`; set `MODEL_BASE_URL` to a container-reachable base URL when yours differs. An unavailable provider returns 503; a provider timeout returns 504; malformed output, invalid citations, rejected plans or provider-rejected requests return 502. `/health` remains independent of the model. This prototype provides no request authentication or production deployment guarantee.

The verified implementation uses direct typed tools. MCP is intentionally not required; add it only as a separately tested transport over the same capability contract.

See [EVIDENCE.md](EVIDENCE.md), [SPECIFICATION.md](SPECIFICATION.md), and [THREAT_MODEL.md](THREAT_MODEL.md).

