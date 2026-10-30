from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
import sys

import pytest

from app.adapters import NemotronChangeAdapter, ChangeAdapterError
from app.cli import write_package
from app.models import ModelDesiredProposal
from app.planner import SandboxedChangePlanner, ChangePlanningError

FIXTURES = Path(__file__).parents[1] / 'fixtures'
DESIRED = {'changes': [{'field': 'replica_count', 'after': 3}]}


def test_returned_rollback_cannot_mutate_planner_source():
    planner = SandboxedChangePlanner(FIXTURES)
    package = planner.prepare_desired(DESIRED)
    package.rollback_config.replica_count = 4
    assert planner.source_config.replica_count == 2
    assert planner.prepare_desired(DESIRED).rollback_config.replica_count == 2


def test_source_property_is_also_a_copy():
    planner = SandboxedChangePlanner(FIXTURES)
    source = planner.source_config
    source.replica_count = 4
    assert planner.source_config.replica_count == 2


def test_application_supplies_before_and_rejects_model_before():
    planner = SandboxedChangePlanner(FIXTURES)
    package = planner.prepare_desired(DESIRED)
    assert package.rollback_config.replica_count == 2
    assert package.proposed_config.replica_count == 3
    with pytest.raises(ChangePlanningError, match='closed schema'):
        planner.prepare_desired({'changes': [{'field':'replica_count','before':2,'after':3}]})
    assert '"before"' not in json.dumps(ModelDesiredProposal.model_json_schema())


@pytest.mark.parametrize('after', ['3', True, 0, 5, 3.5])
def test_desired_replica_value_is_strict_and_bounded(after):
    with pytest.raises(ChangePlanningError):
        SandboxedChangePlanner(FIXTURES).prepare_desired({'changes':[{'field':'replica_count','after':after}]})


def test_unchanged_desired_value_is_rejected():
    with pytest.raises(ChangePlanningError, match='closed schema'):
        SandboxedChangePlanner(FIXTURES).prepare_desired({'changes':[{'field':'replica_count','after':2}]})


@pytest.mark.parametrize('filename', ['../outside.json','/outside.json','nested/source.json','C:\\outside.json'])
def test_manifest_path_cannot_escape_fixture(tmp_path, filename):
    copied=tmp_path/'fixtures';shutil.copytree(FIXTURES,copied)
    manifest=json.loads((copied/'manifest.json').read_text())
    manifest['file']=filename
    (copied/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ChangePlanningError,match='simple JSON filename'):
        SandboxedChangePlanner(copied)


def test_source_symlink_is_rejected(tmp_path):
    copied=tmp_path/'fixtures';shutil.copytree(FIXTURES,copied)
    source=copied/'service-config.json';outside=tmp_path/'outside.json'
    source.rename(outside);source.symlink_to(outside)
    with pytest.raises(ChangePlanningError,match='links or paths'):
        SandboxedChangePlanner(copied)


def test_stale_source_cannot_produce_a_package(tmp_path):
    copied=tmp_path/'fixtures';shutil.copytree(FIXTURES,copied)
    planner=SandboxedChangePlanner(copied)
    source=copied/'service-config.json';source.write_bytes(source.read_bytes()+b'\n')
    with pytest.raises(ChangePlanningError,match='changed during planning'):
        planner.prepare_desired(DESIRED)


def test_oversized_source_is_rejected_even_with_matching_hash(tmp_path):
    copied=tmp_path/'fixtures';shutil.copytree(FIXTURES,copied)
    raw=(copied/'service-config.json').read_bytes()+b' '*65536
    (copied/'service-config.json').write_bytes(raw)
    manifest=json.loads((copied/'manifest.json').read_text());manifest['sha256']=hashlib.sha256(raw).hexdigest()
    (copied/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ChangePlanningError,match='64-KiB'):
        SandboxedChangePlanner(copied)


def test_maintenance_risk_matches_change_direction():
    enabled=SandboxedChangePlanner(FIXTURES).prepare_desired({'changes':[{'field':'maintenance_mode','after':True}]})
    disabled=SandboxedChangePlanner(FIXTURES.parent/'fixtures-holdout').prepare_desired({'changes':[{'field':'maintenance_mode','after':False}]})
    assert 'interrupts' in enabled.risks[0]
    assert 'resumes client traffic' in disabled.risks[0]


def test_artifact_inventory_covers_entire_review_package_and_no_overwrite(tmp_path):
    package=SandboxedChangePlanner(FIXTURES).prepare_desired(DESIRED)
    out=tmp_path/'review'
    manifest=write_package(package,out)
    for filename,digest in manifest['files'].items():
        assert hashlib.sha256((out/filename).read_bytes()).hexdigest()==digest
    before=(out/'approval-package.json').read_bytes()
    with pytest.raises(FileExistsError):
        write_package(package,out)
    assert (out/'approval-package.json').read_bytes()==before
    changed=json.loads(before);changed['risks']=['An altered risk statement.']
    assert hashlib.sha256(json.dumps(changed).encode()).hexdigest()!=manifest['files']['approval-package.json']


def test_cli_produces_review_only_artifacts_and_failure_writes_nothing(tmp_path):
    input_path=tmp_path/'desired.json';input_path.write_text(json.dumps(DESIRED))
    out=tmp_path/'review'
    cmd=[sys.executable,'-m','app.cli','--fixture',str(FIXTURES),'--proposal-file',str(input_path),'--output',str(out)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads((out/'approval-package.json').read_text())['status']=='awaiting_human_approval'
    assert subprocess.run(cmd,capture_output=True).returncode==2
    input_path.write_text('{"changes":[{"field":"command","after":"restart"}]}')
    cmd[-1]=str(tmp_path/'invalid-output')
    assert subprocess.run(cmd,capture_output=True).returncode==2
    assert not (tmp_path/'invalid-output').exists()


@pytest.mark.parametrize('timeout', [0,-1,float('inf'),float('nan')])
def test_provider_timeout_is_validated(timeout):
    with pytest.raises(ValueError,match='finite and positive'):
        NemotronChangeAdapter(timeout_seconds=timeout)


def test_provider_response_is_bounded(monkeypatch):
    monkeypatch.setattr('urllib.request.urlopen',lambda *a,**k:io.BytesIO(b' '*1_048_577))
    with pytest.raises(ChangeAdapterError,match='size limit'):
        NemotronChangeAdapter().propose('Scale to three replicas.',SandboxedChangePlanner(FIXTURES).source_config)
