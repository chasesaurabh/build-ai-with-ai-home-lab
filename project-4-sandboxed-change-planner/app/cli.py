"""Operator-selected files in; a new review directory out. No apply command."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from app.adapters import NemotronChangeAdapter, ChangeAdapterError
from app.models import ApprovalPackage, ChangeRequest
from app.planner import SandboxedChangePlanner, ChangePlanningError
from app.service import ModelBackedChangePlanningService


def read_json(path: Path) -> object:
    with path.open('rb') as stream:
        raw = stream.read(65_537)
    if len(raw) > 65_536:
        raise ValueError('Input file exceeds 64 KiB.')
    return json.loads(raw)


def write_package(package: ApprovalPackage, output: Path) -> dict[str, object]:
    # Never overwrite a previously reviewed directory, even for the same proposal.
    output.mkdir(parents=True, exist_ok=False)
    payloads = {
        'approval-package.json': package.model_dump(mode='json'),
        'proposed-config.json': package.proposed_config.model_dump(mode='json'),
        'rollback-config.json': package.rollback_config.model_dump(mode='json'),
    }
    hashes = {}
    for filename, payload in payloads.items():
        raw = (json.dumps(payload, sort_keys=True, indent=2) + '\n').encode('utf-8')
        (output / filename).write_bytes(raw)
        hashes[filename] = hashlib.sha256(raw).hexdigest()
    manifest = {'proposal_id': package.proposal_id, 'status': package.status,
                'hash_algorithm': 'sha256', 'files': hashes,
                'meaning': 'Integrity inventory, not an approval record or digital signature.'}
    (output / 'artifact-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=Path('fixtures'))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--proposal-file', type=Path, help='JSON desired values: changes containing field and after only')
    mode.add_argument('--request-file', type=Path, help='JSON request object for the explicitly configured model')
    parser.add_argument('--base-url')
    parser.add_argument('--model')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists; choose a new review directory.')
    if args.request_file and (not args.base_url or not args.model):
        parser.error('Model requests require both --base-url and --model.')
    try:
        if args.proposal_file:
            package = SandboxedChangePlanner(args.fixture).prepare_desired(read_json(args.proposal_file))
        else:
            request = ChangeRequest.model_validate(read_json(args.request_file))
            package = ModelBackedChangePlanningService(
                args.fixture, NemotronChangeAdapter(args.base_url, args.model)
            ).prepare(request)
        manifest = write_package(package, args.output)
    except (ValueError, OSError, ChangePlanningError, ChangeAdapterError) as exc:
        parser.exit(2, f'No approval or application occurred: {exc}\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
