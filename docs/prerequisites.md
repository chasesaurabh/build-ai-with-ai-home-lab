# Prerequisites

## Required for deterministic tests

- Docker with Linux-container support, or Python 3.12 with an isolated environment
- Git for retrieving an immutable release tag
- Enough disk space to build the small Python images

Run tests from inside one project directory:

```text
docker build --target test -t build-ai-home-lab-test .
docker run --rm build-ai-home-lab-test
```

To run without Docker, create an isolated Python 3.12 environment, install `requirements-dev.txt`, and run `python -m pytest -q`.

## Required for behavioral evals

- An OpenAI-compatible chat-completions endpoint
- A model capable of the project's structured-output contract
- A loopback or otherwise approved network path
- A local `results/` directory for raw outputs

The recorded path used NVIDIA Nemotron 3.5 Lightning 30B-A3B BF16. A different checkpoint or serving stack is a valid experiment, but its results must be labeled as new evidence.

## Not included

- Model weights or model-serving software
- Production credentials or real logs
- A hosted-provider account
- Public-ingress, authentication, or TLS configuration
- The book manuscript or publishing assets

