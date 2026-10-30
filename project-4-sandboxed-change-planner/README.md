# Project 4 — Sandboxed Change Planner

Convert a free-text request into typed desired values, then build a deterministic diff, validation report, risk summary, rollback snapshot, and human-review package.

## Boundary

The AI application has no apply, deploy, approve, rollback, credential, shell, or production-client capability. A separate operator-run sandbox can consume an already packaged candidate for disposable validation.

## Test

```text
docker build --target test -t build-ai-home-lab-project4-test .
docker run --rm --network none build-ai-home-lab-project4-test
```

## First complete exercise, without a model

From the repository root in PowerShell 7, with Docker running Linux containers:

```powershell
./scripts/planner-first-run.ps1
```

This tests the code, generates a review-only package, verifies artifact hashes, runs the generated candidate in a disposable target, restarts, rejects an invalid configuration, restores all baseline values, and removes its own container. Review artifacts remain in the printed results directory. Optional `-Port 18097` and `-OutputDirectory ./results/my-planner-review` select an unused port and new output directory. Existing output directories/containers are not overwritten.

The script is an explicit operator-run test. The planner cannot start it. The sandbox displays synthetic settings: it does not pull the `image_tag`, scale replicas, or deploy a photo application. Maintenance mode changes `/ready`; other fields are inspected through `/config`.

## Generate a package from a model request

From this project directory, build the test image above. In PowerShell 7, inspect your provider and set its actual ID; the example host endpoint may need adjustment:

```powershell
(Invoke-RestMethod 'http://127.0.0.1:8100/v1/models').data | Select-Object id, root
$modelId = 'replace-with-an-id-from-your-listing'
New-Item -ItemType Directory -Path './results/request-review' -ErrorAction Stop
$reviewPath = (Resolve-Path './results/request-review').Path
@{request='Prepare a proposal to increase the replica count to three.'} |
  ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $reviewPath 'request.json')
docker run --rm --add-host host.docker.internal:host-gateway `
  --mount "type=bind,source=$reviewPath,target=/review" `
  build-ai-home-lab-project4-test python -m app.cli `
  --request-file /review/request.json --base-url http://host.docker.internal:8100 `
  --model $modelId --output /review/package
```

The generated package proposes replicas 2 to 3 and remains awaiting human approval. The CLI writes no approval record and starts no target. For manual input, replace `--request-file` with `--proposal-file` whose JSON is `{"changes":[{"field":"replica_count","after":3}]}`; no provider settings are needed. The application supplies before-values and rejects any model-supplied `before` field. Use a new directory for every review package.

`artifact-manifest.json` hashes the complete package, candidate and rollback files. This inventory is not a signature or approval. The short `proposal_id` identifies source plus changes; it does not bind every explanation string. A real external approval system must bind the reviewed complete artifact and recheck source state.

## Run the model eval

```text
python -m evals.run_model_eval --base-url http://127.0.0.1:8100 --model nemotron-35-lightning --output results/project4-development.json
```

Always pass the actual model ID, record the provider-reported underlying model separately, and create the output parent directory first. The compatibility default alias is historical. Use the existing adversarial and published holdout cases as regression material; an unseen evaluation needs a newly frozen set. The evaluator's full package traces should remain synthetic.

## Run a disposable candidate

Review the candidate JSON and Compose file first. The supplied default starts only the synthetic good candidate on a loopback port:

```text
docker compose up --build
```

The bad-candidate and baseline files exist to test rejection and restoration. They are operator-run fixtures, not model-callable tools.

See [EVIDENCE.md](EVIDENCE.md), [SPECIFICATION.md](SPECIFICATION.md), and [THREAT_MODEL.md](THREAT_MODEL.md).

