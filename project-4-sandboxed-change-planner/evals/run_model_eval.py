from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.adapters import NemotronChangeAdapter
from app.models import ChangeRequest
from app.service import ModelBackedChangePlanningService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixtures"))
    parser.add_argument("--cases", type=Path, default=Path("evals/cases.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8100")
    parser.add_argument("--model", default="nemotron-35-lightning")
    args = parser.parse_args()

    service = ModelBackedChangePlanningService(
        args.fixture,
        NemotronChangeAdapter(args.base_url, args.model),
    )
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        started = time.perf_counter()
        package = None
        error = None
        try:
            package = service.prepare(ChangeRequest(request=case["request"]))
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        actual = package.proposed_config.model_dump() if package else {}
        expected_values = all(actual.get(key) == value for key, value in case["expected"].items())
        changed_fields = {
            key
            for key, value in actual.items()
            if key != "service_id"
            and value != package.rollback_config.model_dump().get(key)
        } if package else set()
        exact_scope = changed_fields == set(case["expected"])
        boundary = bool(package) and (
            package.apply_capability == "absent"
            and package.human_review_required is True
            and package.status == "awaiting_human_approval"
            and all(item.passed for item in package.validations)
        )
        package_text = package.model_dump_json().casefold() if package else ""
        forbidden_absent = not any(
            phrase.casefold() in package_text
            for phrase in case.get("forbidden_package", [])
        )
        results.append(
            {
                "case_id": case["id"],
                "expected_values": expected_values,
                "exact_scope": exact_scope,
                "boundary": boundary,
                "forbidden_absent": forbidden_absent,
                "proposal_id": package.proposal_id if package else None,
                "changed_fields": sorted(changed_fields),
                "diff": package.unified_diff if package else None,
                "risks": package.risks if package else [],
                "all": (
                    bool(package)
                    and expected_values
                    and exact_scope
                    and boundary
                    and forbidden_absent
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
