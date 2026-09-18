# Project 2 — Citation-Grounded Runbook Assistant

Answer operational questions only from an approved, manifest-verified Markdown corpus. Retrieval, abstention, citation membership, conflict disclosure, and corpus lifecycle remain application responsibilities.

## Boundary

The application has no tools or action path. Retrieved text is untrusted evidence, not an instruction channel. If retrieval finds no eligible evidence, the model is not called.

## Test

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

