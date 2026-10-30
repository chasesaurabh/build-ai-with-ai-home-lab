import hashlib
import io
import json
import shutil
import socket
import time
import urllib.error
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters import (NemotronDiagnosticAdapter, DiagnosticAdapterResponseError,
                          DiagnosticAdapterTimeoutError)
from app.agent import BoundedDiagnosticAgent, DiagnosticPolicyError
from app.main import create_app
from app.models import StatusRequest
from app.tools import ReadOnlyLabTools, FixtureError
from app.workflow import DeterministicDiagnosticWorkflow
from test_agent import StubDiagnosticAdapter, valid_plan

FIXTURES = Path(__file__).parents[1] / 'fixtures'


def test_observation_ids_are_fresh_but_payload_hashes_are_stable():
    tools = ReadOnlyLabTools(FIXTURES)
    a = tools.get_service_status(StatusRequest(service='media-server'))
    b = tools.get_service_status(StatusRequest(service='media-server'))
    assert a.evidence_id != b.evidence_id
    assert a.payload_sha256 == b.payload_sha256
    assert a.payload_sha256 == hashlib.sha256(json.dumps(a.data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def test_replaying_prior_run_evidence_is_rejected():
    adapter = StubDiagnosticAdapter(valid_plan())
    agent = BoundedDiagnosticAgent(FIXTURES, adapter)
    first = agent.run('Why is the service slow?', 'media-server')
    adapter.evidence_override = first.report.evidence_ids
    with pytest.raises(DiagnosticPolicyError, match='not produced'):
        agent.run('Why is the service slow?', 'media-server')


@pytest.mark.parametrize('tool', ['get_service_status', 'get_recent_logs'])
def test_limit_change_does_not_allow_duplicate_observation(tool):
    plan = {'calls': [{'tool': tool, 'service': 'media-server', 'limit': n} for n in [5, 7]]}
    with pytest.raises(DiagnosticPolicyError, match='plan was unusable'):
        BoundedDiagnosticAgent(FIXTURES, StubDiagnosticAdapter(plan)).run('Check the service status.', 'media-server')


def copy_fixture(tmp_path):
    destination = tmp_path / 'fixtures'
    shutil.copytree(FIXTURES, destination)
    return destination


def write_fixture(destination, state):
    raw = json.dumps(state).encode()
    (destination / 'lab-state.json').write_bytes(raw)
    manifest = json.loads((destination / 'manifest.json').read_text())
    manifest['sha256'] = hashlib.sha256(raw).hexdigest()
    (destination / 'manifest.json').write_text(json.dumps(manifest))


@pytest.mark.parametrize('mutation', ['extra_secret', 'oversize_log', 'invalid_metric'])
def test_hash_match_does_not_bypass_data_bounds(tmp_path, mutation):
    directory = copy_fixture(tmp_path)
    state = json.loads((directory / 'lab-state.json').read_text())
    service = state['services']['media-server']
    if mutation == 'extra_secret':
        service['config']['secret_values'] = {'TEST_FAKE_SECRET': 'synthetic-test-only'}
    elif mutation == 'oversize_log':
        service['logs'][0]['message'] = 'x' * 2001
    else:
        service['metrics']['cpu_percent'] = float('nan')
    write_fixture(directory, state)
    with pytest.raises(FixtureError, match='bounded data schema'):
        ReadOnlyLabTools(directory)


@pytest.mark.parametrize('filename', ['../outside.json', '/outside.json', 'nested/data.json', 'C:\\outside.json'])
def test_manifest_cannot_supply_a_path(tmp_path, filename):
    directory = copy_fixture(tmp_path)
    (directory / 'manifest.json').write_text(json.dumps({'file': filename, 'sha256': '0' * 64}))
    with pytest.raises(FixtureError, match='simple JSON filename'):
        ReadOnlyLabTools(directory)


def test_fixture_symlink_rejected(tmp_path):
    directory = copy_fixture(tmp_path)
    source = directory / 'lab-state.json'
    outside = tmp_path / 'outside.json'
    source.rename(outside)
    source.symlink_to(outside)
    with pytest.raises(FixtureError, match='links or paths'):
        ReadOnlyLabTools(directory)


def test_fixed_workflow_uses_changed_fixture_not_hardcoded_cause():
    report = DeterministicDiagnosticWorkflow(FIXTURES.parent / 'fixtures-holdout').diagnose('reverse-proxy')
    assert 'degraded' in report.summary
    assert 'TLS handshakes' in report.summary
    assert 'connection refused' not in report.summary
    assert 'is down' not in report.summary


@pytest.mark.parametrize('seconds', [0, -1, float('nan'), float('inf')])
def test_invalid_time_budget_fails_at_construction(seconds):
    with pytest.raises(ValueError, match='finite and positive'):
        BoundedDiagnosticAgent(FIXTURES, StubDiagnosticAdapter(valid_plan()), max_seconds=seconds)


@pytest.mark.parametrize('calls', [0, 5, True, 1.5])
def test_invalid_call_budget_fails_at_construction(calls):
    with pytest.raises(ValueError, match='integer from 1 to 4'):
        BoundedDiagnosticAgent(FIXTURES, StubDiagnosticAdapter(valid_plan()), max_calls=calls)


def test_remaining_budget_is_passed_to_both_model_calls():
    class Capture(StubDiagnosticAdapter):
        def plan(self, question, service, *, timeout_seconds=None):
            self.plan_budget = timeout_seconds
            time.sleep(.01)
            return super().plan(question, service, timeout_seconds=timeout_seconds)

        def diagnose(self, question, service, results, *, timeout_seconds=None):
            self.diagnosis_budget = timeout_seconds
            return super().diagnose(question, service, results, timeout_seconds=timeout_seconds)

    adapter = Capture(valid_plan())
    BoundedDiagnosticAgent(FIXTURES, adapter, max_seconds=2).run('Why is the service slow?', 'media-server')
    assert 0 < adapter.diagnosis_budget < adapter.plan_budget <= 2


def test_fixed_http_path_needs_no_model_and_rejects_extra_actions():
    class Unavailable(StubDiagnosticAdapter):
        model_id = 'unavailable'
        def ready(self):
            return False
        def plan(self, *args, **kwargs):
            pytest.fail('The fixed workflow must not call the model.')
    client = TestClient(create_app(Unavailable(valid_plan()), FIXTURES))
    assert client.get('/ready').status_code == 503
    response = client.post('/v1/diagnose-fixed', json={'service': 'reverse-proxy'})
    assert response.status_code == 200
    assert len(response.json()['tool_results']) == 3
    assert client.post('/v1/diagnose-fixed', json={'service': 'reverse-proxy', 'command': 'restart'}).status_code == 422


@pytest.mark.parametrize('envelope', [[], {'data': None}, {'data': [{'id': 'other'}]}, {'data': 'wrong'}, None])
def test_readiness_rejects_malformed_or_wrong_model(monkeypatch, envelope):
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: io.BytesIO(json.dumps(envelope).encode()))
    assert NemotronDiagnosticAdapter(model_id='expected').ready() is False


def test_readiness_size_limit_and_valid_model(monkeypatch):
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: io.BytesIO(b' ' * 65537))
    assert not NemotronDiagnosticAdapter().ready()
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: io.BytesIO(b'{"data":[{"id":"expected"}]}'))
    assert NemotronDiagnosticAdapter(model_id='expected').ready()


@pytest.mark.parametrize('error, expected', [
    (urllib.error.HTTPError('http://fixture', 400, 'rejected', {}, None), DiagnosticAdapterResponseError),
    (urllib.error.URLError(socket.timeout()), DiagnosticAdapterTimeoutError),
])
def test_provider_errors_keep_their_meaning(monkeypatch, error, expected):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr('urllib.request.urlopen', fail)
    with pytest.raises(expected):
        NemotronDiagnosticAdapter().plan('Check this service.', 'media-server', timeout_seconds=1)


def test_adapter_uses_remaining_timeout(monkeypatch):
    observed = []
    def respond(*args, **kwargs):
        observed.append(kwargs['timeout'])
        return io.BytesIO(b'{"choices":[{"message":{"content":"{}"}}]}')
    monkeypatch.setattr('urllib.request.urlopen', respond)
    NemotronDiagnosticAdapter(timeout_seconds=30).plan('Check this service.', 'media-server', timeout_seconds=.25)
    assert observed == [.25]
