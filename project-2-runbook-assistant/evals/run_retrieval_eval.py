from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.models import RunbookQuestion
from app.service import RetrievalService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    parser.add_argument("--cases", type=Path, default=Path("evals/cases.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    service = RetrievalService(args.corpus)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        started = time.perf_counter()
        response = service.search(RunbookQuestion(question=case["question"]))
        retrieved = [hit.passage_id for hit in response.hits]
        evidence_correct = response.has_evidence is case["expect_evidence"]
        citation_correct = (
            not case["expect_evidence"]
            or bool(set(retrieved) & set(case["expected_passage_any"]))
        )
        results.append(
            {
                "case_id": case["id"],
                "retrieved_passages": retrieved,
                "has_evidence": response.has_evidence,
                "evidence_correct": evidence_correct,
                "expected_citation_retrieved": citation_correct,
                "all": evidence_correct and citation_correct,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        )

    report = {
        "case_count": len(cases),
        "scores": {
            "evidence": sum(item["evidence_correct"] for item in results),
            "expected_citation": sum(item["expected_citation_retrieved"] for item in results),
            "all": sum(item["all"] for item in results),
        },
        "results": results,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": report["case_count"], "scores": report["scores"]}, indent=2))


if __name__ == "__main__":
    main()
