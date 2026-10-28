"""Stage an exact Git source archive on an exclusive GitHub-hosted runner.

CLI caches, disposable SQL installation and private runtime state never dirty the
reviewed source checkout. No Docker operation occurs in this staging tool.
"""
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from integration.i86.scope import inspect


def main():
    root = Path(__file__).resolve().parents[2]
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("PRUMO_I86_RUNNER_ISOLATION") != "github-hosted"):
        raise RuntimeError("I86_EXCLUSIVE_HOSTED_RUNNER_REQUIRED")
    report = inspect(root)
    if report["status"] != "PASS":
        raise RuntimeError("I86_SCOPE_BLOCKS_STAGING")
    temporary = Path(os.environ["RUNNER_TEMP"]).resolve()
    directory = Path(tempfile.mkdtemp(prefix="prumo-i86-", dir=temporary))
    source = root/"integration/i86/.runtime/s1"
    if not source.is_dir() or source.is_symlink():
        raise RuntimeError("I86_PINNED_SOURCE_MISSING")
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"]).decode().strip()
    if revision != "8780b576aa18bd3983c063339e2e42d2452af22c":
        raise RuntimeError("I86_PINNED_SOURCE_DRIFT")
    if subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"]):
        raise RuntimeError("I86_PINNED_SOURCE_DIRTY")
    for item in report["files"]:
        if item["source"] in ("staged", "unstaged", "local") and any(
                not p.startswith("integration/i86/.runtime/") for p in item["paths"]):
            raise RuntimeError("I86_UNCOMMITTED_CODE_CANNOT_BE_STAGED_AS_TESTED")
    pinned = directory/"s1"
    shutil.move(str(source), str(pinned))
    source.parent.rmdir()
    runtime = directory/"source"
    runtime.mkdir(mode=0o700)
    archive = subprocess.check_output(["git", "-C", str(root), "archive", "--format=tar", "HEAD"])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        tree.extractall(runtime, filter="data")
    with open(os.environ["GITHUB_ENV"], "a") as output:
        output.write("PRUMO_I86_SANDBOX="+str(runtime)+"\n")
        output.write("PRUMO_G1_SOURCE_REPO="+str(pinned)+"\n")
        output.write("PRUMO_I86_SOURCE_HEAD="+report["head"]+"\n")
    print("I86_EXACT_SOURCE_STAGED_ON_EXCLUSIVE_RUNNER")


if __name__ == "__main__":
    main()
