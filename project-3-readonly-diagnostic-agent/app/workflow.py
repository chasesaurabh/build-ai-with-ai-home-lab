from pathlib import Path

from app.models import DiagnosticReport, LogsRequest, MetricsRequest, ServiceName, StatusRequest
from app.tools import ReadOnlyLabTools


class DeterministicDiagnosticWorkflow:
    def __init__(self, fixture_dir: Path) -> None:
        self._tools = ReadOnlyLabTools(fixture_dir)

    def diagnose(self, service: ServiceName) -> DiagnosticReport:
        status = self._tools.get_service_status(StatusRequest(service=service))
        logs = self._tools.get_recent_logs(LogsRequest(service=service, limit=5))
        metrics = self._tools.get_resource_metrics(MetricsRequest(service=service))

        state = status.data["state"]
        if state == "healthy":
            summary = (
                f"{service} is healthy in the simulated fixture; the latest logs report successful "
                "completion and no active error condition."
            )
        elif service == "media-server" and metrics.data.get("cpu_percent", 0) >= 90:
            summary = (
                "The simulated media-server degradation is consistent with CPU saturation and a growing "
                "worker queue during slow transcode requests."
            )
        elif service == "reverse-proxy":
            summary = (
                "The simulated reverse-proxy is down because all health checks to its configured media-server "
                "upstream are failing with connection refused."
            )
        elif service == "storage-pool":
            summary = (
                "The simulated storage pool remains online but has degraded redundancy after repeated read "
                "errors from disk-03; human review is required."
            )
        else:
            summary = f"{service} is {state}; the bounded fixture requires human review."

        return DiagnosticReport(
            service=service,
            summary=summary,
            evidence_ids=[status.evidence_id, logs.evidence_id, metrics.evidence_id],
        )
