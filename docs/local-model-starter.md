# First local model: a bounded CPU-only exercise

This path starts its own model server, downloads a small model, and sends one
synthetic report through Project 1. It does not require an existing model
installation, GPU, API key, or the 120B model used for the other recorded evals.
First complete `scripts/first-run.ps1` to separate application setup problems
from model-server problems. Run walkthroughs one at a time.

## Before starting

Use PowerShell 7 and a running Linux-container Docker engine. The measured
platform is Windows 11, Docker Desktop 4.91.0 / Engine 29.8.0, Linux x86_64.
Other platforms have not been measured by this exercise. Docker must be able to
download the official Ollama image, model blobs, and the Python application
dependencies. This is not an offline installation procedure.

The script caps the **model container** at eight CPUs and 6 GiB RAM with no
additional swap allowance. It passes no GPU devices. Docker and the application
need memory outside that cap. Start with at least 8 GiB available to Docker and
free space for the server image, approximately 2.5 GB of model files, Python
images, and build cache. This is planning headroom, not a measured minimum PC
specification. Check actual free Docker storage before downloading; image size
is additional to model size. Do not prune unrelated images or volumes.

The tested host had an i9-12900K and approximately 128 GiB RAM, with about
62.7 GiB visible to Docker. A container cap does not recreate a smaller host's
CPU, storage, memory pressure, or performance. On a slower system, the same
request may exceed the deliberately bounded 180-second model deadline.

## Run from the companion repository root

```powershell
pwsh -NoProfile -File ./scripts/model-first-run.ps1
```

The script uses Ollama **0.40.12**, pinned to an image manifest digest, and
`qwen3:4b-instruct-2507-q4_K_M`. It verifies the downloaded model's reported
manifest digest before using it. The full expected digests are in the script
and evidence. It refuses to replace existing containers or the exercise network.
Its model Docker volume is retained for reuse; an existing volume is recorded
as a cached run rather than a fresh download.

If a port or evidence directory is occupied, choose new values:

```powershell
pwsh -NoProfile -File ./scripts/model-first-run.ps1 `
  -ModelPort 18135 -AppPort 18098 `
  -OutputDirectory ./results/model-first-run-02
```

Read the script before running it. Its stages are:

1. Check Docker and refuse conflicting container/network names.
2. Download the pinned Ollama image and create a named model-storage volume.
3. Start a CPU-only server with cloud features disabled, one parallel request,
   and a 4,096-token context limit. Publish its port on host loopback only.
4. Pull the named model, inspect `/v1/models`, and check its manifest digest.
5. Build Project 1 and start it on the same dedicated Docker network, using
   the exact model ID and an explicit provider deadline.
6. Submit `The backup service is offline.` through `/v1/intake`. Check the
   validated application's escalation decision and human-review requirement.
7. Stop the model server. Check that application liveness stays HTTP 200,
   readiness becomes 503, and a model-backed request returns a controlled 503.
8. Restart the server, repeat the request, save evidence, and remove only the
   two created containers and the created network. Keep the model volume.

## Understand the three addresses

| Caller and destination | Default address | Purpose |
|---|---|---|
| Host to model | `http://127.0.0.1:18134` | Version/model listing during the exercise |
| Application container to model | `http://build-ai-starter-model:11434` | Name resolved on the dedicated Docker network |
| Host to application | `http://127.0.0.1:18097` | `/health`, `/ready`, and `/v1/intake` |

The application base URL is the **origin without `/v1`**. Its adapter appends
the API paths. Container loopback refers to that container, so pointing the
application at `127.0.0.1:18134` would not reach the separate model container.
No host-gateway mapping is needed for this shared-network route. The model
server has no application authentication; loopback publication is for this
single-machine exercise, not a multiuser deployment security design.

The default exercise cleans up automatically. These addresses stop responding
when it finishes. To keep the two services after a successful test, add
`-KeepRunning` and use a new evidence directory. Failed runs still clean up.
The retained services continue consuming resources until you stop them.

While retained, inspect the host route and send another synthetic request:

```powershell
Invoke-RestMethod http://127.0.0.1:18134/v1/models
$body = @{ description = 'The backup service is offline.' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:18097/v1/intake `
  -Method Post -ContentType application/json -Body $body -TimeoutSec 190
```

Use your selected ports if you changed the defaults. A separately launched
application container can join `build-ai-starter-network` and use
`http://build-ai-starter-model:11434`; it must still pass its own compatibility
checks. This starter validates only Project 1. For later projects, follow the
project README and record a new model evaluation rather than inheriting this
one-case result.

When finished, inspect the two names with `docker ps -a`, confirm they belong
to this exercise, then remove them and their dedicated network:

```powershell
docker rm -f build-ai-starter-intake build-ai-starter-model
docker network rm build-ai-starter-network
```

These commands discard the exercise containers, not their named model volume.
Do not run them against unrelated names or use a broad prune command.

## Inspect the result, including failure

Read `results/model-first-run/result.json`, `request-before.json`,
`request-after.json`, `provider-stopped.json`, `request-provider-stopped.json`,
`model-tags.json`, and `model-loaded.json`. Container logs and image identities
are saved alongside them. Failed runs remain failures; do not edit their files
to pass. Choose a new evidence directory for a rerun.

The October 30 initial run used a new empty model volume and passed the
representative request before and after restart in 11.49 and 11.04 seconds.
The server reported zero VRAM use, a 4,096-token loaded context and about
3.19 GB loaded-model allocation. A Docker snapshot after the first request
showed 5.458 GiB model-container usage, which includes more than model weights
and is neither a peak measurement nor a minimum requirement. These are two
requests for one synthetic case, not a model-quality benchmark. This does not
establish Qwen performance on Projects 2–4 or equivalence to the 120B evals.

The adapter sends a vLLM-specific `chat_template_kwargs` field. This Ollama
request was accepted; that does not establish that Ollama honors that field.
The selected Instruct model produced usable content through this exact path.
Changing the model, runtime, context, prompt or adapter requires a new
compatibility check. The application continues to validate the full schema and
enforce policy after generation.

## Troubleshoot without hiding the problem

- **Download failure:** check connectivity, registry access and Docker free
  space. Preserve the log; rerun with a new evidence directory. The model
  volume remains so the server can reuse completed data.
- **Port/name conflict:** inspect the existing resource; do not delete another
  project's container. Choose alternate ports or stop your earlier exercise.
- **Model-digest mismatch:** the remote tag changed. Preserve the new identity
  and review it; do not silently remove the comparison.
- **Exit 137 / out-of-memory:** inspect the saved server log and Docker memory
  allocation. Free resources you own or revise the explicit cap and retest.
  A smaller model needs separate schema/quality evidence.
- **HTTP 504:** the model deadline expired. Investigate load and CPU speed;
  the client timeout is longer than the provider deadline. Do not add unlimited
  retries or silently switch to the deterministic adapter.
- **HTTP 502:** inspect the saved response and provider log. The server may be
  reachable while output is invalid or incompatible.
- **Interrupted cleanup:** inspect only `build-ai-starter-model`,
  `build-ai-starter-intake`, and `build-ai-starter-network`. Remove an owned
  exercise resource explicitly only after confirming its identity. The normal
  script cleanup does not delete the model volume or images.

To discard downloaded model files later, first confirm the exact volume name
in `result.json` and that no container uses it. `docker volume rm` for that
specific volume is a separate, destructive choice; it is not part of the test.

## Official sources and licenses

Reviewed October 30, 2026:

- [Ollama 0.40.12 release](https://github.com/ollama/ollama/releases/tag/v0.40.12)
- [CPU Docker setup](https://docs.ollama.com/docker)
- [OpenAI-compatible interface](https://docs.ollama.com/api/openai-compatibility)
- [Exact Qwen artifact and license](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M)

The model artifact page identifies Q4_K_M quantization and Apache 2.0 terms.
The companion's MIT license does not replace model or runtime licenses. Model
weights and serving images are downloaded from their upstream sources and are
not distributed in this repository.
