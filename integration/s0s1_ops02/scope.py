"""OPS-02 Git boundary. Default certifies one clean atomic commit.

--candidate permits only the eight new files pending at the exact checkpoint.
This checker is reviewable code, not an independent trust anchor. Its JSON
inventory must also be compared using external Git/object hashing by a reviewer.
Only this gate (never the offline document validator) invokes local Git.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

BASE = "a0c4eaf2720bd6cf2bd756544498f8f185f005fc"
BASE_TREE = "977c4ed302b9dd14e459575abbbc718eaa8ca920"
BRANCH = "exp/s0-s1-ops02-evidence-contract-20261030"
ALLOWED = frozenset({
    "ops/s0s1_authority/contract_v1.json",
    "ops/s0s1_authority/validate.py",
    "integration/s0s1_ops02/test_contract.py",
    "integration/s0s1_ops02/scope.py",
    "docs/contratos/s0s1_ops02/CONTRATO_CANDIDATO.md",
    "docs/contratos/s0s1_ops02/RUNBOOK_CANDIDATO.md",
    "docs/contratos/s0s1_ops02/DECISOES_E_TESTES.json",
    ".github/workflows/exp-s0-s1-ops02-evidence-contract.yml",
})


def git(root, *args):
    return subprocess.check_output(
        ["git", "--no-replace-objects", "--literal-pathspecs", "-C", str(root),
         "-c", "core.fsmonitor=false", *args], stderr=subprocess.DEVNULL)


def tree(root, ref):
    result = {}
    for entry in git(root, "ls-tree", "-rz", ref).split(b"\0"):
        if entry:
            meta, name = entry.split(b"\t", 1)
            mode, kind, blob = meta.decode("ascii").split()
            result[os.fsdecode(name)] = (mode, kind, blob)
    return result


def inspect(root, candidate=False, *, base=BASE, base_tree=BASE_TREE, branch=BRANCH):
    """Explicit keyword anchors support ONLY artificial-repository unit tests.

    The CLI cannot change anchors, allowlist or branch via flags/environment.
    """
    root = Path(root).absolute()
    failures, inventory = [], {}
    head = git(root, "rev-parse", "HEAD").decode().strip()
    head_tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    if git(root, "branch", "--show-current").decode().strip() != branch:
        failures.append("WRONG_OR_DETACHED_BRANCH")
    if git(root, "rev-parse", base + "^{tree}").decode().strip() != base_tree:
        failures.append("BASE_TREE_MISMATCH")
    if git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
        failures.append("SHALLOW_REPOSITORY")
    if git(root, "for-each-ref", "refs/replace").strip():
        failures.append("REPLACEMENT_OBJECTS")
    graft = Path(os.fsdecode(git(root, "rev-parse", "--git-path", "info/grafts")).strip())
    if not graft.is_absolute():
        graft = root / graft
    if graft.exists():
        failures.append("GRAFTED_HISTORY")
    ancestry = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(root), "merge-base",
         "--is-ancestor", base, head], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ancestry.returncode:
        failures.append("BASE_NOT_ANCESTOR")
        history = []
    else:
        history = git(root, "rev-list", "--reverse", "--parents", base + "..HEAD").decode().splitlines()
    expected_count = 0 if candidate else 1
    if len(history) != expected_count or (candidate and head != base):
        failures.append("ATOMIC_HISTORY_REQUIRED")
    previous = base
    base_entries, head_entries = tree(root, base), tree(root, head)
    if ALLOWED.intersection(base_entries):
        failures.append("AUTHORIZED_PATH_ALREADY_IN_BASE")
    for line in history:
        parts = line.split()
        if len(parts) != 2 or parts[1] != previous:
            failures.append("NON_LINEAR_HISTORY")
        current = parts[0]
        current_entries = tree(root, current)
        parent_entries = tree(root, parts[1]) if len(parts) == 2 else {}
        # Each intermediate tree is inspected, so edit-then-revert is rejected.
        for path in set(current_entries) | set(parent_entries):
            if current_entries.get(path) != parent_entries.get(path):
                if path not in ALLOWED:
                    failures.append("HISTORICAL_OUT_OF_SCOPE:" + path)
                if current_entries.get(path, ())[:2] != ("100644", "blob"):
                    failures.append("UNSAFE_HISTORICAL_MODE_OR_REMOVAL:" + path)
        previous = current
    index = {}
    for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if entry:
            meta, name = entry.split(b"\t", 1)
            mode, blob, stage = meta.decode().split()
            path = os.fsdecode(name)
            if stage != "0":
                failures.append("UNMERGED_INDEX:" + path)
            index[path] = (mode, "blob" if mode != "160000" else "commit", blob)
    extras = set()
    for args in (("ls-files", "--others", "--exclude-standard", "-z"),
                 ("ls-files", "--others", "--ignored", "--exclude-standard", "-z")):
        extras.update(os.fsdecode(p) for p in git(root, *args).split(b"\0") if p)
    pending = bool(git(root, "status", "--porcelain=v1", "--untracked-files=all", "--ignored"))
    if pending and not candidate:
        failures.append("PENDING_FILES")
    for path in set(base_entries) | set(head_entries) | set(index) | extras:
        base_item, head_item, index_item = (base_entries.get(path), head_entries.get(path), index.get(path))
        local = root / path
        components = Path(path).parts
        unsafe = any(root.joinpath(*components[:i]).is_symlink()
                     for i in range(1, len(components) + 1))
        raw, local_item = None, None
        if unsafe:
            failures.append("SYMLINK_PATH:" + path)
        else:
            try:
                info = local.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o111 or info.st_nlink != 1:
                    failures.append("UNSAFE_LOCAL_TYPE_OR_MODE:" + path)
                else:
                    raw = local.read_bytes()
                    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                    local_item = ("100644", "blob", blob)
            except FileNotFoundError:
                pass
        if path not in ALLOWED:
            if not base_item or head_item != base_item or index_item != base_item or local_item != base_item:
                failures.append("OUT_OF_SCOPE_OR_INHERITED_CHANGED:" + path)
        else:
            if head_item and head_item[:2] != ("100644", "blob"):
                failures.append("UNSAFE_TREE_MODE:" + path)
            if index_item and index_item[:2] != ("100644", "blob"):
                failures.append("UNSAFE_INDEX_MODE:" + path)
            if local_item is None:
                failures.append("AUTHORIZED_FILE_MISSING_OR_UNSAFE:" + path)
            elif not candidate and (head_item != local_item or index_item != head_item):
                failures.append("CONTENT_NOT_COMMITTED:" + path)
            if local_item:
                inventory[path] = {"mode": local_item[0], "git_blob": local_item[2],
                                   "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    if set(inventory) != set(ALLOWED):
        failures.append("EXACT_EIGHT_FILES_REQUIRED")
    delta = {p for p in set(base_entries) | set(head_entries) if base_entries.get(p) != head_entries.get(p)}
    if not candidate and delta != set(ALLOWED):
        failures.append("EXACT_COMMITTED_DELTA_REQUIRED")
    return {"version": "prumo.s0s1.ops02.scope.v1", "mode": "CANDIDATE" if candidate else "CERTIFY",
            "status": "FAIL" if failures else "PASS", "base": base, "base_tree": base_tree,
            "head": head, "head_tree": head_tree, "branch": branch,
            "commits_after_base": len(history), "files": inventory,
            "violations": sorted(set(failures)), "authorizes_action": False}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).absolute().parents[2]
    try:
        if args not in ([], ["--candidate"]):
            raise ValueError("USAGE: scope.py [--candidate]")
        report = inspect(root, candidate=bool(args))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report = {"status": "FAIL", "authorizes_action": False,
                  "violations": ["GIT_OR_INSPECTION_FAILURE:" + type(exc).__name__]}
    print(json.dumps(report, sort_keys=True, ensure_ascii=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
