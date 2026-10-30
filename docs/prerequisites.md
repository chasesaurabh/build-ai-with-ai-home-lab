# Prerequisites

You should be comfortable opening a terminal, changing directories and editing a
configuration file. Prior local-AI experience is not required for the first run.

## First run without a model

- Git, for obtaining and identifying a release checkout.
- A running Docker engine in Linux-container mode. Image builds need network
  access; the software-test runs explicitly disable external networking.
- PowerShell 7 (`pwsh`) for the supplied automated walkthroughs. Windows
  PowerShell 5.1 does not support all their HTTP options. The project READMEs
  also explain the individual Docker and Python commands.
- Disk space for the Python images and a free loopback port. No GPU, model
  download or hosted-provider account is required for these four first runs.

From the companion repository root, run one walkthrough at a time:

```powershell
pwsh -NoProfile -File scripts/first-run.ps1
pwsh -NoProfile -File scripts/runbook-first-run.ps1
pwsh -NoProfile -File scripts/diagnostic-first-run.ps1
pwsh -NoProfile -File scripts/planner-first-run.ps1
```

The default ports are 18088, 18092, 18093 and 18096, respectively; each script
accepts `-Port`. Scripts build images, test synthetic cases, exercise actual HTTP
or generated-package behavior and remove only the containers they created.
Planner output stays under `results/` for inspection. Images are retained.

To run only a project's tests, change into that project directory:

```text
docker build --target test -t build-ai-home-lab-test .
docker run --rm --network none build-ai-home-lab-test
```

The recorded container platform is Linux x86_64, Python 3.12.16. For a direct
Python installation, create an isolated Python 3.12 environment, then run:

```text
python -m pip install --only-binary=:all: pip==26.2.1
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The direct installation is an alternative to the measured container path; do not
assume its platform-specific dependencies match. Read [dependency scope](dependencies.md).

## Adding a model

If you do not yet have an endpoint, follow the complete
[CPU-only local-model starter](local-model-starter.md). It downloads a pinned
Ollama runtime and small Qwen model, runs a real Project 1 request, tests server
failure/recovery, and saves the result. This path is separate from the four
no-model first runs and needs additional downloads, memory and storage.

You need an OpenAI-compatible chat-completions endpoint, an exact served model
identifier, the project's structured-output behavior and an approved network
path. Endpoint compatibility alone does not prove that a model follows the
contract. Start with [model-provider configuration](model-provider.md), then
the project's explicit readiness and evaluation commands.

Weights, serving software, real logs, credentials, public-ingress configuration,
book text and publishing assets are not included. GPU and memory requirements
depend on the model and server you choose; the recorded 120B checkpoint is an
experiment identity, not a minimum requirement for learning these applications.
