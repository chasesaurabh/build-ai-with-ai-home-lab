# Model Provider Configuration

The applications use a narrow provider adapter. Keep model-server administration
separate from application policy, and use only synthetic inputs while learning.

No endpoint yet? The [CPU-only starter](local-model-starter.md) walks from a
running Docker engine to a real, validated Project 1 request using Ollama
0.40.12 and Qwen 4B Instruct. It includes failure, recovery and cleanup. Its
small-model compatibility result does not replace the separately recorded
Nemotron evaluations below.

## Recorded identities

The October 30, 2026 revision runs reported model root
`nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4` through vLLM 0.30.0. The endpoint
exposed both `nemotron-super-120b-fp4` and a historical alias,
`nemotron-35-lightning`, for that same root. The latter name did **not** mean the
30B model was loaded. Identity responses were checked around the runs; weight
file hashes were not verified. Do not identify a model from a friendly alias.

The preserved first-edition experiments used NVIDIA Nemotron 3.5 Lightning
30B-A3B BF16. Their results and settings do not describe the revision runs.

Model cards and weight-license terms:

- https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4
- https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16

This repository distributes no weights. Its MIT license does not replace model
or server terms.

## Configure your endpoint explicitly

The measured host endpoint was `http://127.0.0.1:8100`; containers reached it
through `http://host.docker.internal:8100`. These are examples for the recorded
Docker Desktop setup. A remote machine's loopback refers to that machine, and
the container's loopback refers to the container. Native Linux Docker may need
an explicit host-gateway mapping; do not expose a server publicly to fix routing.

Inspect `/v1/models`, confirm the intended root in your server configuration,
then pass that server's exact ID using the project's `--model` option or
`MODEL_ID` environment variable. Pass `--base-url` or `MODEL_BASE_URL` as shown
in its README. Some legacy eval defaults still say `nemotron-35-lightning`;
override them explicitly. Never infer a new checkpoint from that default.

## Compatibility checks

1. The requested model resolves to the intended checkpoint.
2. The provider accepts the project's structured-output request.
3. Output parses and passes the complete application schema and policy checks.
4. Timeouts, unavailable providers and malformed responses produce controlled
   failures; they do not silently switch to another model or grant more access.
5. Extra fields, tools, targets and authority remain rejected.
6. Comparisons use identified cases, prompts and scorers, with failures retained.

Record model root, alias, server version, decoding settings, request limits,
source commit, date, raw results and limitations. A different model, provider or
prompt creates new evidence. Deterministic application validation is still
required after every model response.
