"""Run an unchanged S1 SQL acceptance file only in CLI loopback PG17."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from scripts.test_s0_cfi01_auth_rest_local import local_env

if os.environ.get('PRUMO_G1_DISPOSABLE_TEST')!='YES':raise RuntimeError('G1 opt-in required')
path=Path(sys.argv[1]).resolve()
source=Path(os.environ['PRUMO_G1_SOURCE_REPO']).resolve()
relative=str(path.relative_to(source))
manifest=json.loads(Path('integration/g1/s1_sources.json').read_text())
entry=next(x for x in manifest['test_sources'] if x['path']==relative)
assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
subprocess.run(['psql','-X','-q','-v','ON_ERROR_STOP=1',local_env()['DB_URL'],'-f',str(path)],check=True)
