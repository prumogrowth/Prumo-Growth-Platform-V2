import hashlib
import json
from pathlib import Path
m=json.loads(Path('integration/s0_meta_ingress/source-manifest.json').read_text())
for item in m['files']:
    data=Path(item['path']).read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if actual != item['git_blob']:
        raise SystemExit('SOURCE FAIL: '+item['path'])
print('SOURCE PASS:',len(m['files']),'original Git blobs, PR14',m['source_head'])
