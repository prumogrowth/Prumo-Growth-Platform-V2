#!/usr/bin/env python3
"""Compose pinned Meta fixtures with current S0 in a NEW disposable directory.

No fetch, database access, migration discovery or writes to source checkouts.
The 12 SQL fixtures exist only in the temporary lab, never our migrations path.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def prepare(source_repo, destination):
    assert not destination.is_relative_to(ROOT), 'Destination must be outside S0 checkout'
    assert not destination.is_relative_to(source_repo), 'Destination must be outside Meta checkout'
    manifest = json.loads((HERE / 'source_manifest.json').read_text())
    sha = manifest['meta_head']
    assert git(source_repo, 'rev-parse', sha).decode().strip() == sha
    # All shared migrations must still match. Abort instead of overwriting a
    # changed S0 schema with historical Meta dependencies.
    for name in git(ROOT, 'ls-tree', '-r', '--name-only', 'HEAD',
                    'supabase/migrations').decode().splitlines():
        assert git(ROOT, 'rev-parse', 'HEAD:' + name) == git(source_repo, 'rev-parse', sha + ':' + name), name
    payloads = {}
    for item in manifest['files']:
        content = git(source_repo, 'show', sha + ':' + item['path'])
        assert hashlib.sha256(content).hexdigest() == item['sha256'], item['path']
        assert git(source_repo, 'rev-parse', sha + ':' + item['path']).decode().strip() == item['blob']
        if item['path'] != 'scripts/run-s0-local.sh':
            assert not (ROOT / item['path']).exists(), 'Unexpected S0 overlap: ' + item['path']
        payloads[item['path']] = content
    destination.mkdir(parents=True, exist_ok=False)
    # Trusted, tracked local Git tree. Filter also rejects unsafe tar paths.
    with tarfile.open(fileobj=io.BytesIO(git(ROOT, 'archive', 'HEAD'))) as archive:
        archive.extractall(destination, filter='data')
    for name, content in payloads.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for patch in sorted((HERE / 'patches').glob('*.patch')):
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=destination, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=destination, check=True)
    # Reuse the historical ordering exactly; add a rollback probe immediately
    # before each actual install, when that fixture's dependencies exist.
    for name in ('catalog_fingerprint.py', 'test_install_atomicity.py'):
        target = destination / 'integration/meta' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((HERE / name).read_bytes())
    runner = destination / 'scripts/run-s0-local.sh'
    text = runner.read_text()
    anchor = ' psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/$file"'
    assert text.count(anchor) == 1
    text = text.replace(anchor, ' if [[ "$file" == supabase/migrations/2026102300* ]]; then\n'
        '  python3 "$ROOT/integration/meta/test_install_atomicity.py" "$ROOT/$file"\n fi\n' + anchor)
    late = 'psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/migrations/202610230054_s0_meta_single_entry_seal_fixture.sql"'
    assert text.count(late) == 1
    text = text.replace(late, 'python3 "$ROOT/integration/meta/test_install_atomicity.py" '
        '"$ROOT/supabase/migrations/202610230054_s0_meta_single_entry_seal_fixture.sql"\n' + late)
    runner.write_text(text)
    print('META-COMPOSE: pinned sources verified; current S0 retained; 12 fixtures isolated', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-repo', type=Path, default=ROOT)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.source_repo.resolve(), args.destination.resolve())
