from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.adapters import NemotronDiagnosticAdapter
from app.agent import BoundedDiagnosticAgent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixtures"))
    parser.add_argument("--cases", type=Path, default=Path("evals/cases.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8100")
    parser.add_argument("--model", default="nemotron-35-lightning")
    args = parser.parse_args()

    adapter = NemotronDiagnosticAdapter(args.base_url, args.model)
    agent = BoundedDiagnosticAgent(args.fixture, adapter, max_calls=4, max_seconds=30)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        started = time.perf_counter()
        run = None
        error = None
        try:
            run = agent.run(case["question"], case["service"])
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        tools = [result.tool for result in run.tool_results] if run else []
        summary = run.report.summary if run else ""
        required_tools = set(case["required_tools"]).issubset(tools)
        summary_terms = any(
            term.casefold() in summary.casefold() for term in case["summary_term_any"]
        )
        forbidden_summary_absent = not any(
            term.casefold() in summary.casefold()
            for term in case.get("forbidden_summary", [])
        )
        evidence_valid = bool(run) and set(run.report.evidence_ids).issubset(
            result.evidence_id for result in run.tool_results
        )
        results.append(
            {
                "case_id": case["id"],
                "service": case["service"],
                "tools": tools,
                "summary": summary or None,
                "evidence_ids": run.report.evidence_ids if run else [],
                "required_tools": required_tools,
                "summary_terms": summary_terms,
                "forbidden_summary_absent": forbidden_summary_absent,
                "evidence_valid": evidence_valid,
                "all": (
                    bool(run)
                    and required_tools
                    and summary_terms
                    and forbidden_summary_absent
                    and evidence_valid
                ),
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
