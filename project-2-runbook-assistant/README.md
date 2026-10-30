# Project 2 — Citation-Grounded Runbook Assistant

Answer operational questions using an approved, manifest-verified Markdown corpus. The application enforces retrieval bounds, deterministic empty-evidence abstention, response consistency, and citation membership. The model must assess support and describe conflicts; those semantic judgments require evaluation and review.

## Boundary

The application has no tools or action path. Retrieved text is untrusted evidence, not an instruction channel. If retrieval finds no eligible evidence, the model is not called.

## Test

For a complete first run without a model or GPU, use PowerShell 7 from the repository root:

```powershell
pwsh -NoProfile -File ./scripts/runbook-first-run.ps1
```

The exercise builds/tests, starts a disposable loopback-only service, verifies search, abstention, missing-provider errors, input rejection, and restart, then removes its own container. It defaults to port18092; use `-Port 18093` if occupied. Generation readiness503 is intentional in this no-model exercise; `/v1/search` remains available. Existing containers with the exercise name are never removed automatically.

```text
docker build --target test -t build-ai-home-lab-project2-test .
docker run --rm build-ai-home-lab-project2-test
```

## Run retrieval before generation

```text
python -m evals.run_retrieval_eval --output results/project2-retrieval.json
```

## Run grounded-answer evals

```text
python -m evals.run_answer_eval --base-url http://127.0.0.1:8100 --model nemotron-35-lightning --output results/project2-answers.json
python -m evals.run_adversarial_eval --base-url http://127.0.0.1:8100 --model nemotron-35-lightning --output results/project2-adversarial.json
```

Run the holdout corpus only after freezing retrieval, generation, and scoring. See [EVIDENCE.md](EVIDENCE.md), [SPECIFICATION.md](SPECIFICATION.md), and [THREAT_MODEL.md](THREAT_MODEL.md).

Always pass the actual configured model ID and record its reported root/version; the old example alias does not establish which weights are loaded. The revision experiments used `nemotron-super-120b-fp4`, reported as NVIDIA Nemotron3Super120B-A12B-NVFP4 through vLLM0.30.0. The scripts' old defaults remain compatibility values, not model-identity evidence.

Revision checks:43software tests passed; the known ten development retrieval and answerability/citation cases passed. Three related-but-unsupported questions abstained. The first revised adversarial run failed conflict disclosure; after a prompt correction, both existing cases passed. These are development results, not general accuracy or a new holdout. Prior evidence in `EVIDENCE.md` remains historical until separately identified as a revision run.

