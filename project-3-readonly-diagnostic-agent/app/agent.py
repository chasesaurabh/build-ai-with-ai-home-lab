from __future__ import annotations

import time
import math
from pathlib import Path

from pydantic import ValidationError

from app.adapters import DiagnosticAdapter, DiagnosticAdapterError
from app.models import (
    DiagnosticReport,
    DiagnosticRun,
    ModelDiagnosis,
    ModelToolPlan,
    ServiceName,
    ToolCall,
)
from app.tools import ReadOnlyLabTools, ToolAuthorizationError


class DiagnosticPolicyError(RuntimeError):
    """A model plan or diagnosis violated application-owned policy."""


class BoundedDiagnosticAgent:
    def __init__(
        self,
        fixture_dir: Path,
        adapter: DiagnosticAdapter,
        max_calls: int = 4,
        max_seconds: float = 30,
    ) -> None:
        if type(max_calls) is not int or not 1 <= max_calls <= 4:
            raise ValueError("max_calls must be an integer from 1 to 4.")
        if not math.isfinite(max_seconds) or max_seconds <= 0:
            raise ValueError("max_seconds must be finite and positive.")
        self._tools = ReadOnlyLabTools(fixture_dir)
        self._adapter = adapter
        self._max_calls = max_calls
        self._max_seconds = max_seconds

    def run(self, question: str, service: ServiceName) -> DiagnosticRun:
        started = time.perf_counter()

        def remaining() -> float:
            value = self._max_seconds - (time.perf_counter() - started)
            if value <= 0:
                raise DiagnosticPolicyError("The diagnostic run exceeded its time budget.")
            return value

        try:
            plan = ModelToolPlan.model_validate(
                self._adapter.plan(question, service, timeout_seconds=remaining())
            )
        except ValidationError as exc:
            raise DiagnosticPolicyError("The diagnostic tool plan was unusable.") from exc
        except DiagnosticAdapterError:
            raise
        if len(plan.calls) > self._max_calls:
            raise DiagnosticPolicyError("The diagnostic plan exceeded the tool-call budget.")
        if any(call.service != service for call in plan.calls):
            raise DiagnosticPolicyError("The diagnostic plan targeted an unapproved service.")

        results = []
        for planned in plan.calls:
            remaining()
            arguments: dict[str, object] = {"service": planned.service}
            if planned.tool == "get_recent_logs":
                arguments["limit"] = planned.limit
            try:
                results.append(
                    self._tools.dispatch(ToolCall(tool=planned.tool, arguments=arguments))
                )
            except ToolAuthorizationError as exc:
                raise DiagnosticPolicyError("The planned tool call was not authorized.") from exc

        try:
            diagnosis = ModelDiagnosis.model_validate(
                self._adapter.diagnose(question, service, results, timeout_seconds=remaining())
            )
        except ValidationError as exc:
            raise DiagnosticPolicyError("The diagnostic report was unusable.") from exc
        except DiagnosticAdapterError:
            raise

        allowed_evidence = {result.evidence_id for result in results}
        if not set(diagnosis.evidence_ids).issubset(allowed_evidence):
            raise DiagnosticPolicyError("The diagnosis cited evidence not produced by this run.")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        remaining()
        return DiagnosticRun(
            report=DiagnosticReport(
                service=service,
                summary=diagnosis.summary,
                evidence_ids=diagnosis.evidence_ids,
            ),
            tool_results=results,
            elapsed_ms=elapsed_ms,
        )
