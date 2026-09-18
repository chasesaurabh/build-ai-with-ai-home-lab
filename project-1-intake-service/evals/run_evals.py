from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from app.adapters import DeterministicRuleAdapter, OpenAICompatibleAdapter
from app.models import IntakeDecision, IntakeRequest
from app.service import IntakeService


def score(case: dict[str, Any], decision: IntakeDecision) -> dict[str, bool]:
    fields = {
        "category": decision.category in case["expected_categories"],
        "urgency": decision.urgency == case["expected_urgency"],
        "affected_system": decision.affected_system.casefold() == case["expected_system"].casefold(),
        "next_step": decision.next_step in case["expected_next_steps"],
        "evidence": bool(set(decision.evidence_requests) & set(case["expected_evidence_any"])),
        "human_review": decision.requires_human_review is True,
    }
    fields["all"] = all(fields.values())
    return fields


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", choices=("deterministic", "local"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).with_name("cases.json"),
        help="Evaluation case file (defaults to the original frozen cases).",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8100")
    parser.add_argument("--model", default="nemotron-35-lightning")
    parser.add_argument("--case", action="append", dest="case_ids")
    args = parser.parse_args()

    adapter = (
        DeterministicRuleAdapter()
        if args.adapter == "deterministic"
        else OpenAICompatibleAdapter(args.base_url, args.model, timeout_seconds=30)
    )
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if args.case_ids:
        selected = set(args.case_ids)
        cases = [case for case in cases if case["id"] in selected]
        missing = selected - {case["id"] for case in cases}
        if missing:
            parser.error(f"unknown case id(s): {', '.join(sorted(missing))}")
    results = []
    for case in cases:
        started = time.perf_counter()
        error = None
        decision = None
        field_scores = None
        try:
            decision = IntakeService(adapter).classify(
                IntakeRequest(description=case["description"])
            )
            field_scores = score(case, decision)
        except Exception as exc:  # The raw failure is evidence for this bounded experiment.
            error = f"{type(exc).__name__}: {exc}"
        results.append(
            {
                "case_id": case["id"],
                "decision": decision.model_dump() if decision else None,
                "scores": field_scores,
                "error": error,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )

    successful = [item for item in results if item["scores"]]
    field_names = ("category", "urgency", "affected_system", "next_step", "evidence", "human_review", "all")
    report = {
        "adapter": args.adapter,
        "model": args.model if args.adapter == "local" else None,
        "cases_file": args.cases.name,
        "case_count": len(cases),
        "error_count": sum(item["error"] is not None for item in results),
        "scores": {name: sum(item["scores"][name] for item in successful) for name in field_names},
        "results": results,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("adapter", "case_count", "error_count", "scores")}, indent=2))


if __name__ == "__main__":
    main()
