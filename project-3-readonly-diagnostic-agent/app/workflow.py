from pathlib import Path
import time

from app.models import DiagnosticReport, DiagnosticRun, LogsRequest, MetricsRequest, ServiceName, StatusRequest
from app.tools import ReadOnlyLabTools


class DeterministicDiagnosticWorkflow:
    def __init__(self, fixture_dir: Path) -> None:
        self._tools = ReadOnlyLabTools(fixture_dir)

    def diagnose(self, service: ServiceName) -> DiagnosticReport:
        return self.run(service).report

    def run(self, service: ServiceName) -> DiagnosticRun:
        started = time.perf_counter()
        status = self._tools.get_service_status(StatusRequest(service=service))
        logs = self._tools.get_recent_logs(LogsRequest(service=service, limit=5))
        metrics = self._tools.get_resource_metrics(MetricsRequest(service=service))

        state = status.data["state"]
        # Report observations, never a cause selected merely by service name.
        detail = status.data['detail'][:200]
        summary = f'{service} is {state} in the simulated fixture. Status detail: "{detail}" '
        if metrics.data.get("cpu_percent", 0) >= 90:
            summary += f"CPU saturation is plausible: CPU {metrics.data['cpu_percent']}%, queue {metrics.data['queue_depth']}. "
        if metrics.data.get("degraded_devices", 0) > 0:
            summary += "Metrics indicate degraded redundancy; they do not identify the failed device. "
        summary += "This is an observation summary, not a verified root cause; human review is required."

        return DiagnosticRun(
            report=DiagnosticReport(
                service=service,
                summary=summary,
                evidence_ids=[status.evidence_id, logs.evidence_id, metrics.evidence_id],
            ),
            tool_results=[status, logs, metrics],
            elapsed_ms=round((time.perf_counter() - started) * 1000, 1),
        )
