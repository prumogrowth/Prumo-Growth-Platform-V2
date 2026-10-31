"""OPS-03 staging only. No SQL, HTTP client, credentials or administrative act.

Physical tests run only on an exclusive disposable GitHub-hosted runner.
"""
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


def stage():
    from integration.s0s1_ops03.scope import inspect
    root = Path(__file__).absolute().parents[2]
    if (os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'
            or os.environ.get('PRUMO_OPS03_DISPOSABLE') != 'YES'):
        raise RuntimeError('OPS03_EXCLUSIVE_DISPOSABLE_RUNNER_REQUIRED')
    source = root/'integration/i86/.runtime/s1'
    if source.is_symlink() or not source.is_dir():
        raise RuntimeError('OPS03_PINNED_SOURCE_REQUIRED')
    def git(path, *args):
        return subprocess.check_output(['git','-C',str(path),*args]).decode().strip()
    if (git(source,'rev-parse','HEAD') != '0b0930778c29204904c1c1358a9a7ae9e3fff10b'
            or git(source,'rev-parse','HEAD^{tree}') != 'e18d4d1c0b75f6a2ed9fa4d7c904737500fe3e0b'
            or git(source,'status','--porcelain')):
        raise RuntimeError('OPS03_PINNED_SOURCE_DRIFT')
    destination = Path(tempfile.mkdtemp(prefix='prumo-ops03-',dir=os.environ['RUNNER_TEMP']))
    pinned = destination/'s1'
    shutil.move(str(source),str(pinned))
    source.parent.rmdir()
    # The temporary checkout is gone before checking the exact source inventory.
    report = inspect(root)
    if report['status'] != 'PASS':
        raise RuntimeError('OPS03_SCOPE_BLOCKS_ARCHIVE')
    data = subprocess.check_output(['git','-C',str(root),'archive','--format=tar','HEAD'])
    runtime = destination/'source'
    runtime.mkdir(mode=0o700)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(runtime,filter='data')
    with open(os.environ['GITHUB_ENV'],'a') as output:
        output.write('PRUMO_I86_SANDBOX='+str(runtime)+'\n')
        output.write('PRUMO_G1_SOURCE_REPO='+str(pinned)+'\n')
        output.write('PRUMO_I86_SOURCE_HEAD='+report['head']+'\n')
    print('OPS03_EXACT_COMMITTED_ARCHIVE_AND_PINNED_S1_STAGED')
