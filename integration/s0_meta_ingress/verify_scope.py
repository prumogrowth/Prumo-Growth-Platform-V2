"""Fail closed against frozen base, complete history, index, worktree and untracked files."""
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = '3cab3d57619cc1157698a08ac26f34e0c363f6dd'
PREFIXES = ('integration/s0_meta_ingress/', 'docs/contratos/s0_meta_ingress/')
WORKFLOW = '.github/workflows/exp-s0-meta-ingress-01.yml'

def git(*args):
    return subprocess.check_output(['git', *args])

def allowed(path):
    return path.startswith(PREFIXES) or path == WORKFLOW

def verify():
    if os.environ.get('S0_META_EXPECTED_BASE', BASE) != BASE:
        raise ValueError('unexpected base')
    if git('rev-parse', BASE).decode().strip() != BASE:
        raise ValueError('frozen object missing')
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    for line in git('rev-list','--parents', BASE+'..HEAD').decode().splitlines():
        if len(line.split()) != 2:
            raise ValueError('merge or foreign ancestry')
    inherited = set(git('ls-tree','-rz','--name-only',BASE).decode().split('\0')) - {''}
    changes = set()
    def inspect(diff, history=False):
        parts = diff.decode().split('\0')
        for i in range(0,len(parts)-1,2):
            status,path = parts[i:i+2]
            if status not in (('A','M') if history else ('A',)) or not allowed(path) or path in inherited:
                raise ValueError('unexpected change: '+status+' '+path)
            changes.add(path)
    inspect(git('diff','--no-renames','--name-status','-z',BASE))
    inspect(git('diff','--cached','--no-renames','--name-status','-z',BASE))
    # Also reject temporary mutations/deletions hidden by an inverse pending change.
    for commit in git('rev-list', BASE+'..HEAD').decode().splitlines():
        inspect(git('diff-tree','--no-commit-id','-r','--no-renames','--name-status','-z',commit),history=True)
    # Pending modifications of newly owned files are allowed; deletion is never implicit.
    for line in git('diff','--no-renames','--name-status').decode().splitlines():
        status,path = line.split('\t')
        if status not in ('A','M') or not allowed(path) or path in inherited:
            raise ValueError('unexpected worktree modification: '+path)
    for path in git('ls-files','--others','-z').decode().split('\0'):
        if path:
            if not allowed(path):
                raise ValueError('untracked out of scope: '+path)
            changes.add(path)
    for path in changes:
        if Path(path).is_symlink():
            raise ValueError('symlink not permitted: '+path)
    manifest = json.loads(Path('integration/s0_meta_ingress/file-manifest.json').read_text())
    if manifest['base_sha'] != BASE or set(manifest['files']) != changes:
        raise ValueError('file manifest differs from full diff')
    print(json.dumps({'scope':'PASS','base_sha':BASE,'inherited_files_checked':len(inherited),
                      'changed_files':sorted(changes),'pending_included':True}))

if __name__ == '__main__':
    try:
        verify()
    except Exception as ex:
        print('SCOPE FAIL: '+str(ex), file=sys.stderr)
        sys.exit(1)
