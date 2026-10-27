"""Read-only source provenance + additive-scope gate. Never calls a database."""
import hashlib
import json
import pathlib
import subprocess
import sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
m = json.loads((ROOT / "integration/meta_s0_template_catalog/source-manifest.json").read_text())
for source in m["reused"]:
    content = (ROOT / source["path"]).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    assert blob == source["git_blob"], source["path"]
if "--files-only" not in sys.argv:
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()
    for source in m["reused"]:
        assert git("rev-parse", f'{m["base_sha"]}:{source["path"]}') == source["git_blob"]
    for path in git("diff", "--name-only", m["base_sha"], "HEAD").splitlines():
        assert path.startswith(("integration/meta_s0_template_catalog/",
            "docs/contratos/meta_s0_template_catalog/")) or path == \
            ".github/workflows/aux-meta-s0-template-catalog-05.yml", path
print(f'CATALOG-05 PROVENANCE PASS: {len(m["reused"])} original blobs unchanged')
