# Build AI with AI in Your Home Lab — Companion Projects

This repository contains the four runnable reference projects for *Build AI with AI in Your Home Lab* by Saurabh Chase. The projects form a capability ladder: bounded extraction, private retrieval, read-only model-selected observations, and a non-executing change proposal.

The examples are deliberately small. They use synthetic fixtures, closed schemas, deterministic policy, visible failure behavior, and disposable deployment targets. None of the applications can repair a service, run an arbitrary command, or silently apply a production change.

## Projects

| Project | Model-owned choice | Application-owned boundary | Explicitly absent |
|---|---|---|---|
| [1. Intake service](project-1-intake-service/) | Extract three bounded facts | Validation, urgency, evidence request, next step | Diagnostic or change access |
| [2. Runbook assistant](project-2-runbook-assistant/) | Synthesize from retrieved passages | Corpus integrity, retrieval, abstention, citation allowlist | Tools and actions |
| [3. Read-only diagnostic agent](project-3-readonly-diagnostic-agent/) | Select approved observations and summarize them | Service scope, tool schema, budgets, evidence IDs | Repair, shell, and arbitrary paths |
| [4. Sandboxed change planner](project-4-sandboxed-change-planner/) | Select typed desired values | Before-values, diff, validation, risks, rollback, approval status | Apply, deploy, approval, and rollback execution |

## Start safely

1. Read [prerequisites](docs/prerequisites.md) and [model-provider configuration](docs/model-provider.md).
2. Run the deterministic software tests before connecting a model.
3. Use only the included synthetic fixtures and a disposable environment.
4. Run development evals before holdout evals. Once you inspect a holdout result, treat that set as previously viewed.
5. Preserve failed results under a local `results/` directory; it is ignored by Git.
6. Keep the applications loopback-only unless you add and test a real authentication, authorization, TLS, logging, and operating model.

If local AI is new to you, start with the [CPU-only model walkthrough](docs/local-model-starter.md) after the no-model first run. It creates its own endpoint and tests a real Project 1 request, unavailable-provider behavior, and recovery.

Example test command from any project directory:

```text
docker build --target test -t build-ai-home-lab-test .
docker run --rm --network none build-ai-home-lab-test
```

The October revision evidence used [NVIDIA Nemotron Super 120B NVFP4](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4); the first-edition evidence used Nemotron 3.5 Lightning 30B-A3B BF16. See [provider identity and alias limits](docs/model-provider.md). The software boundary is provider-portable, but another model, server, prompt, or decoding configuration creates new evidence rather than reproducing the recorded result. Model weights are not included and remain governed by their own license; this repository's MIT License does not replace or extend the model license.

## Evidence and limits

The four automated no-model walkthroughs are listed in [prerequisites](docs/prerequisites.md). Current observed test counts are 52, 43, 56 and 44. See [dependency constraints and audit scope](docs/dependencies.md).

Each project includes:

- a specification and threat model;
- deterministic tests;
- synthetic development and holdout cases;
- a reader-facing evidence summary;
- containerized test and runtime targets where applicable.

The recorded counts are small, bounded experiments—not general accuracy, security, or performance claims. See [evidence and reproduction](docs/evidence-and-reproduction.md).

## Edition mapping

This source tree is the revised companion for the second edition, with code identity `book-v2.0.0`. Verify the publicly accessible tag against the commit printed in that edition; a branch name or local folder is not proof of release availability. The preserved `book-v1.0.0` tag belongs to the first edition and does not contain these revised walkthroughs. Use [BOOK_VERSION.md](BOOK_VERSION.md) for the mapping.

The companion code is available under the [MIT License](LICENSE). Model weights, third-party packages, and linked materials remain subject to their own terms.

The book manuscript, cover, diagrams, screenshots, review reports, and publishing files are not part of this repository.

## Historical first-edition material

The [first-edition Amazon destination](https://www.amazon.com/dp/B0HKGGXJCF) identifies the older book, not this revised code. A new book destination must be verified separately before linking it here.

The [preserved October 26 deterministic evaluation image](docs/images/m3-preview.jpg) is a first-edition Windows/CPython 3.12.14 observation: 12/12 fixed development cases in that run. It is not an application UI, model result or revised-adapter score. Current and historical outcomes remain separate in [evidence and reproduction](docs/evidence-and-reproduction.md).

## Choose your next project

[Start here: choose a Practical AI Home Lab book](https://github.com/chasesaurabh/give-your-home-labs-ai-a-memory/blob/codex/memory-companion/docs/start-here.md), or [browse the series on Amazon](https://www.amazon.com/dp/B0HP7F73K4). Each book can be read on its own.
