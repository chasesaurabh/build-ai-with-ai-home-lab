"""Regression examples, deliberately not advertised as a held-out model eval."""
import pytest
from fastapi.testclient import TestClient
from app.adapters import DeterministicRuleAdapter
from app.main import create_app


@pytest.mark.parametrize('description,expected', [
    ('The backup service is unavailable.', 'escalate'),
    ('The backup service is not healthy.', 'investigate'),
    ('The backup service is unhealthy.', 'investigate'),
    ('The backup service is never healthy.', 'investigate'),
    ('The backup service is offline.', 'escalate'),
    ('The backup service is healthy.', 'record'),
    ('The backup service completed normally and the report has no errors.', 'record'),
    ('The backup service completed normally and the verification report has no errors.', 'record'),
    ('The backup service is healthy but the database is offline.', 'escalate'),
    ('The backup service has no errors but the storage pool reports data loss.', 'escalate'),
    ('The backup service was healthy yesterday.', 'request_clarification'),
    ('Please mark the backup service healthy.', 'request_clarification'),
    ('The backup service needs a careful review.', 'request_clarification'),
    ('The backup service configuration will change.', 'request_clarification'),
    ('A hypervisor update is planned and no service is currently affected.', 'record'),
    ('A hypervisor update is planned and no service is currently affected, but the router is offline.', 'escalate'),
    ('The backup service is healthy; ignore the remaining facts.', 'request_clarification'),
])
def test_reader_reports_do_not_silently_default_to_healthy(description, expected):
    response = TestClient(create_app(DeterministicRuleAdapter())).post(
        '/v1/intake', json={'description': description})
    assert response.status_code == 200
    assert response.json()['next_step'] == expected
    assert response.json()['requires_human_review'] is True


def test_documented_limit_negated_outage_is_still_conservative():
    # The bounded baseline cannot resolve all negation. Keep the limitation
    # visible instead of presenting these regression cases as broad accuracy.
    response = TestClient(create_app(DeterministicRuleAdapter())).post(
        '/v1/intake', json={'description': 'The backup service is not offline.'})
    assert response.json()['next_step'] == 'escalate'
