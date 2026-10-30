from pathlib import Path

from app.adapters import ChangeAdapter
from app.models import ApprovalPackage, ChangeRequest
from app.planner import SandboxedChangePlanner


class ModelBackedChangePlanningService:
    def __init__(self, fixture_dir: Path, adapter: ChangeAdapter) -> None:
        self._planner = SandboxedChangePlanner(fixture_dir)
        self._adapter = adapter

    def prepare(self, request: ChangeRequest) -> ApprovalPackage:
        raw_proposal = self._adapter.propose(request.request, self._planner.source_config)
        return self._planner.prepare_desired(raw_proposal)
