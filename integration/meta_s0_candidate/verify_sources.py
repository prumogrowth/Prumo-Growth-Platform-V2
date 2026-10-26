"""Read-only provenance and branch-scope checks. No network or database."""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
manifest = json.loads((ROOT / "integration/meta_s0_candidate/source-manifest.json").read_text())
def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()
assert git("rev-parse", manifest["base_sha"]) == manifest["base_sha"]
for source in manifest["reused"]:
    path = source["path"]
    assert git("rev-parse", f'{manifest["base_sha"]}:{path}') == source["git_blob"], path
    # Hash actual working-tree bytes too; no modified import can silently pass.
    assert git("hash-object", path) == source["git_blob"], path
for path in git("diff", "--name-only", manifest["base_sha"], "HEAD").splitlines():
    assert (path.startswith("integration/meta_s0_candidate/")
        or path.startswith("docs/contratos/meta_s0/")
        or path == ".github/workflows/aux-meta-s0-contracts.yml"), path
assert not (ROOT / "integration/meta_s0_candidate/node_modules").exists()
print(f"PROVENANCE PASS: {len(manifest['reused'])} unchanged source blobs; additive auxiliary scope")
