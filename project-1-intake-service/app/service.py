from pydantic import ValidationError

from app.adapters import AdapterResponseError, IntakeAdapter
from app.models import IntakeDecision, IntakeRequest, ModelIntakeAssessment


class IntakeService:
    def __init__(self, adapter: IntakeAdapter) -> None:
        self.adapter = adapter

    def classify(self, request: IntakeRequest) -> IntakeDecision:
        raw_result = self.adapter.classify(request)
        try:
            assessment = ModelIntakeAssessment.model_validate(raw_result)
        except ValidationError as exc:
            raise AdapterResponseError("The adapter output violated the application schema.") from exc

        condition = assessment.condition
        # Policy maps validated facts; it must not secretly re-interpret raw
        # description substrings (including negated or historical alerts).
        category = assessment.category
        category_by_condition = {
            "ambiguous": "other",
            "planned_nonimpacting": "change",
            "access_request": "access",
            "security_event": "security",
            "data_loss_risk": "availability",
        }
        category = category_by_condition.get(condition, category)

        if condition == "ambiguous":
            urgency = "low"
            next_step = "request_clarification"
        elif condition in {"outage", "security_event", "data_loss_risk"}:
            urgency = "high"
            next_step = "escalate"
        elif condition in {"access_request", "degraded"}:
            urgency = "normal"
            next_step = "investigate"
        else:
            urgency = "low"
            next_step = "record"

        evidence_by_category = {
            "availability": ["service_status", "recent_logs"],
            "performance": ["resource_usage", "recent_logs"],
            "security": ["identity_audit", "recent_logs"],
            "access": ["identity_audit"],
            "change": ["change_history"],
            "other": ["none"],
        }
        rationale = (
            f"The request names {assessment.affected_system} and was classified as {category} with "
            f"condition {condition}; deterministic policy selected {next_step}."
        )

        return IntakeDecision(
            category=category,
            urgency=urgency,
            affected_system=assessment.affected_system,
            evidence_requests=evidence_by_category[category],
            next_step=next_step,
            rationale=rationale,
            requires_human_review=True,
        )
