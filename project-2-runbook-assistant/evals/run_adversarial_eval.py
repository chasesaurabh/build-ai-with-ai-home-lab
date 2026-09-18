from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.adapters import NemotronAnswerAdapter
from app.models import RunbookQuestion
from app.service import GroundedAnswerService, RetrievalService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("fixtures/adversarial-corpus"))
    parser.add_argument("--cases", type=Path, default=Path("evals/adversarial-cases.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8100")
    parser.add_argument("--model", default="nemotron-35-lightning")
    args = parser.parse_args()

    service = GroundedAnswerService(
        RetrievalService(args.corpus),
        NemotronAnswerAdapter(args.base_url, args.model),
    )
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        started = time.perf_counter()
        response = None
        error = None
        try:
            response = service.answer(RunbookQuestion(question=case["question"]))
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        answer = response.answer.casefold() if response else ""
        citations = [item.passage_id for item in response.citations] if response else []
        required_citations = set(case["required_citations"])
        citation_pass = required_citations.issubset(citations)
        required_text_pass = any(
            phrase.casefold() in answer for phrase in case["required_answer_any"]
        )
        forbidden_text_pass = not any(
            phrase.casefold() in answer for phrase in case["forbidden_answer"]
        )
        results.append(
            {
                "case_id": case["id"],
                "answer": response.answer if response else None,
                "citation_ids": citations,
                "required_citations": citation_pass,
                "required_answer": required_text_pass,
                "forbidden_answer_absent": forbidden_text_pass,
                "all": bool(response) and citation_pass and required_text_pass and forbidden_text_pass,
                "error": error,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )

    report = {
        "model": args.model,
        "case_count": len(cases),
        "error_count": sum(item["error"] is not None for item in results),
        "passed": sum(item["all"] for item in results),
        "results": results,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("case_count", "error_count", "passed")}, indent=2))


if __name__ == "__main__":
    main()
