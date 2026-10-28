"""Materialize pinned S1/I63 sources ONLY in the new local disposable stack.

No merge, branch mutation, candidate adoption or rewritten S1 DDL. Must run
after the existing CFI suite has installed its exact S1/038 reference.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from scripts.test_s0_cfi01_auth_rest_local import local_env

ROOT=Path(__file__).resolve().parents[2]


def verify_sources(source_repo,manifest):
    ref=manifest['ref']
    def git(*parts):return subprocess.check_output(['git','-C',str(source_repo),*parts])
    assert git('rev-parse','HEAD').decode().strip()==ref
    # The baseline and the previously installed team gate must be byte-equal
    # to S1. Abort rather than layering incompatible historical migrations.
    s1=set(git('ls-tree','-r','--name-only',ref,'supabase/migrations').decode().splitlines())
    for path in s1:
        if (ROOT/path).exists():
            assert (ROOT/path).read_bytes()==git('show',ref+':'+path),path
    reference='supabase/migrations/202610180038_s1_equipe_prumo_gate.sql'
    assert (ROOT/'supabase/tests/s0_cfi01_s1_038_reference_local_only.sql').read_bytes()==git('show',ref+':'+reference)
    sources=[]
    for item in manifest['files']:
        data=git('show',ref+':'+item['path'])
        assert hashlib.sha256(data).hexdigest()==item['sha256'],item['path']
        sources.append(data)
    return sources


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-repo',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=ROOT/'integration/history/s1_sources.json')
    args=parser.parse_args()
    if os.environ.get('PRUMO_HISTORY_DISPOSABLE_TEST')!='YES':
        raise RuntimeError('Disposable opt-in required')
    env=local_env()
    manifest_path=args.manifest.resolve()
    if not manifest_path.is_relative_to(ROOT/'integration'):
        raise RuntimeError('Manifest must be a local integration artifact')
    manifest=json.loads(manifest_path.read_text())
    sources=verify_sources(args.source_repo,manifest)
    for data in sources:
        subprocess.run(['psql','-X','-q','-v','ON_ERROR_STOP=1',env['DB_URL']],input=data,check=True,stdout=subprocess.DEVNULL)
    print(f'HISTORY-I63-SOURCES: {len(sources)} pinned original files verified and installed in loopback disposable DB',flush=True)


if __name__=='__main__':main()
