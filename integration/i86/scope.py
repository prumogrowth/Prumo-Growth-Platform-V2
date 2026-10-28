"""Fail-closed I86 source boundary, including staged/unstaged/ignored files.

The command has no configurable base or allowlist. Reports go to stdout or a
caller-selected file OUTSIDE the checkout, never to a source file.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

BASE = "dbf49ab19b73766d60678c4ce6f7dea56cd66c9b"
BASE_TREE = "9d2f54b8753d4afadf5175ee5b332510890f1772"
BRANCH = "exp/s1-i86-manual-director-20261028"
PREFIXES = ("integration/i86/", "docs/contratos/i86_authority/")
WORKFLOW = ".github/workflows/exp-s1-i86-manual-director.yml"


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args],
                                   stderr=subprocess.DEVNULL)


def permitted(path):
    return (isinstance(path, str) and not any(ord(c) < 32 for c in path)
            and not any(p in (".", "..") for p in PurePosixPath(path).parts)
            and (path == WORKFLOW or any(path.startswith(p) for p in PREFIXES)))


def changes(raw):
    """Git -z includes BOTH names for renames/copies; no line splitting."""
    parts = raw.decode("utf-8", "surrogateescape").split("\0")
    result = []
    i = 0
    while i < len(parts) and parts[i]:
        status = parts[i]
        count = 2 if status[0] in ("R", "C") else 1
        paths = parts[i+1:i+1+count]
        if len(paths) != count or not all(paths):
            raise ValueError("INVALID_DIFF")
        result.append({"status": status, "paths": paths})
        i += count + 1
    return result


def inspect(root, base=BASE, base_tree=BASE_TREE):
    """Parameters support isolated fixture repositories; CLI always fixes BASE."""
    root = Path(root).resolve()
    violations = []
    inventory = []
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if git(root, "rev-parse", base+"^{tree}").decode().strip() != base_tree:
        violations.append("BASE_TREE_CHANGED")
    ancestry = subprocess.run(["git", "-C", str(root), "merge-base",
                               "--is-ancestor", base, head],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ancestry.returncode:
        violations.append("BASE_NOT_ANCESTOR")
    else:
        for line in git(root, "rev-list", "--parents", base+"..HEAD").decode().splitlines():
            if len(line.split()) != 2:
                violations.append("NON_LINEAR_HISTORY:"+line.split()[0])
            else:
                commit, parent = line.split()
                for item in changes(git(root, "diff", "--name-status", "-z",
                                        "--find-renames", parent, commit)):
                    item["source"] = "commit:"+commit
                    inventory.append(item)
    branch = git(root, "branch", "--show-current").decode().strip()
    if branch and branch != BRANCH:
        violations.append("WRONG_BRANCH")
    for source, args in (
        ("committed", ("diff", "--name-status", "-z", "--find-renames", base, "HEAD")),
        ("staged", ("diff", "--cached", "--name-status", "-z", "--find-renames", "HEAD")),
        ("unstaged", ("diff", "--name-status", "-z", "--find-renames")),
    ):
        for item in changes(git(root, *args)):
            item["source"] = source
            inventory.append(item)
    for ignored, args in (
        (False, ("ls-files", "--others", "--exclude-standard", "-z")),
        (True, ("ls-files", "--others", "--ignored", "--exclude-standard", "-z")),
    ):
        for raw in git(root, *args).split(b"\0"):
            if raw:
                inventory.append({"status": "IGNORED" if ignored else "UNTRACKED",
                                  "paths": [os.fsdecode(raw)], "source": "local"})
    # Modes in both Git trees and index detect symlinks/gitlinks even if the
    # worktree happens to look like a regular file.
    all_paths = {p for item in inventory for p in item["paths"]}
    modes = {}
    for raw in git(root, "ls-tree", "-rz", "HEAD").split(b"\0"):
        if raw:
            meta, name = raw.split(b"\t", 1)
            modes[os.fsdecode(name)] = meta.split()[0].decode()
    for raw in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if raw:
            meta, name = raw.split(b"\t", 1)
            mode, _, stage = meta.split()
            path = os.fsdecode(name)
            if path in all_paths and stage != b"0":
                violations.append("UNMERGED:"+path)
            if mode in (b"120000", b"160000") and path in all_paths:
                violations.append("UNSAFE_INDEX_MODE:"+path)
    fingerprints = {}
    for path in sorted(all_paths):
        if not permitted(path):
            violations.append("OUT_OF_SCOPE:"+path)
        if modes.get(path) in ("120000", "160000"):
            violations.append("UNSAFE_TREE_MODE:"+path)
        local = root/path
        if local.is_symlink():
            violations.append("LOCAL_SYMLINK:"+path)
        elif local.is_file():
            fingerprints[path] = hashlib.sha256(local.read_bytes()).hexdigest()
    return {"version": "prumo.i86.scope.v1", "base": base, "base_tree": base_tree,
            "head": head, "branch": branch or "DETACHED", "files": inventory,
            "working_file_sha256": fingerprints, "violations": sorted(set(violations)),
            "status": "FAIL" if violations else "PASS"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        result = inspect(root)
        text = json.dumps(result, indent=2, ensure_ascii=True)+"\n"
        if args.report:
            target = Path(args.report).resolve()
            if target == root or root in target.parents:
                raise ValueError("REPORT_MUST_BE_OUTSIDE_CHECKOUT")
            target.write_text(text)
        print(text, end="")
        return 0 if result["status"] == "PASS" else 1
    except Exception:
        print('{"status":"FAIL","code":"SCOPE_VERIFICATION_UNAVAILABLE"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
