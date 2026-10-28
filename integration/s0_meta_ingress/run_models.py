"""Run unchanged source suites separately from SQL/HTTP proofs, check actual TAP counts."""
import os
from pathlib import Path
import subprocess
import sys

base=Path('integration/s0_meta_ingress/vendor')
tests=[base/'integration/meta_s0_candidate'/n for n in ('candidate.test.mjs','durable.test.mjs')]
tests += [base/'integrations/whatsapp-meta'/(n+'.test.ts') for n in (
    'cloud-webhook-handoff','cloud-wire-observation','inbound','routed-webhook',
    'graph-outbound','graph-template','wa36-ratification-gate','wa37-acceptance-handoff')]
r=subprocess.run(['node','--experimental-strip-types','--test','--test-reporter=tap','--test-concurrency=1',*map(str,tests)],
                 env={**os.environ,'NODE_OPTIONS':'','NODE_PATH':''},stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
output=r.stdout.decode()
path=Path(os.environ.get('S0_META_MODEL_REPORT','/tmp/s0-meta-models.tap'))
path.write_text(output)
for line in output.splitlines():
    if line.startswith(('# tests ','# pass ','# fail ','# skipped ','# cancelled ')):
        print(line)
if r.returncode or not all(line in output.splitlines() for line in ('# tests 213','# pass 213','# fail 0','# skipped 0','# cancelled 0')):
    print('MODEL/REGRESSION FAIL; inspect TAP artifact',file=sys.stderr)
    sys.exit(1)
