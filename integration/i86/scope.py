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

BASE = "ae4bb16ac12086ad64509eff1c200b282fbd2f9f"
BASE_TREE = "3385f06bb477007c7d682f621227da422cf6fc5c"
BRANCH = "exp/s1-i86-manual-director-20261028"
PREFIXES = ("integration/i86/", "docs/contratos/i86_authority/")
WORKFLOW = ".github/workflows/exp-s1-i86-manual-director.yml"

# CM-01 is an approved public trust decision, not historical equivalence.
# These paths remain OUTSIDE permitted(). Only one exact, committed, paired
# transition immediately after CM01_PARENT can receive the exception.
CM01_PARENT = "89513a82c7fe00fd22ffb71384aef3636a143e42"
CM01_FILES = {
    "integration/g1/s1_sources.json": {
        "before_blob": "bbbc3159621103049f6884261f96f99ffcb2bc26",
        "after_blob": "03e539790fed10dbe91afe2b9f16176ae6d8337f",
        "before_sha256": "66f9ee4a7aeed7892d314582078b077d8a49486b919a51e17832183982f83cf2",
        "after_sha256": "087a654faaf99e5c2f59129850599995e16b6253079e3c700e544ad1b17322be",
    },
    "local_admin/dependencies.json": {
        "before_blob": "ad49091f46bdf4b7291924b7dfe43ecff24824f8",
        "after_blob": "994db2ebb6f2ece9d12b6b8b6ca4c51afa6720f3",
        "before_sha256": "8dc6eeba070d4b4234123e9723344821ccf7234510acb3330d460b79c6f35685",
        "after_sha256": "33333c6fd89425afb8e408d43d71da6380f44bcb8515fb878f8c02759362bae7",
    },
}


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


def cm01_transition(root, base, head, inventory, parent, expected):
    """Verify the frozen exception; explicit arguments serve synthetic tests.

    Production inspect() supplies only the constants above. No CLI, environment
    or mutable document can authorize a different path, parent or content.
    """
    violations = []
    paths = set(expected)
    touched = {}
    aggregate = []
    for item in inventory:
        if not paths.intersection(item["paths"]):
            continue
        if item["status"] != "M" or len(item["paths"]) != 1:
            violations.append("CM01_PROTECTED_CHANGE_SHAPE")
        if item["source"].startswith("commit:"):
            touched.setdefault(item["source"][7:], []).extend(item["paths"])
        elif item["source"] == "committed":
            aggregate.extend(item["paths"])
        else:
            violations.append("CM01_PROTECTED_PENDING")
    migration = next(iter(touched)) if len(touched) == 1 else None
    if migration is None:
        violations.append("CM01_MIGRATION_COUNT")
    elif sorted(touched[migration]) != sorted(paths):
        violations.append("CM01_PAIRED_TRANSITION_REQUIRED")
    if sorted(aggregate) != sorted(paths):
        violations.append("CM01_AGGREGATE_CHANGED")
    if migration:
        parents = git(root, "rev-list", "--parents", "-n", "1", migration).decode().split()
        if parents != [migration, parent]:
            violations.append("CM01_MIGRATION_PARENT")

    def fixed_tree(ref, path, spec, state):
        entries = [r for r in git(root, "ls-tree", "-z", ref, "--", path).split(b"\0") if r]
        if len(entries) != 1:
            return False
        meta, name = entries[0].split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        return (os.fsdecode(name) == path and mode == "100644" and kind == "blob"
                and blob == spec[state+"_blob"]
                and hashlib.sha256(git(root, "cat-file", "blob", blob)).hexdigest()
                == spec[state+"_sha256"])

    for path, spec in expected.items():
        for ref, state in ((base, "before"), (parent, "before"), (head, "after")):
            if not fixed_tree(ref, path, spec, state):
                violations.append("CM01_PROTECTED_TREE:"+path)
        if migration and not fixed_tree(migration, path, spec, "after"):
            violations.append("CM01_PROTECTED_TRANSITION:"+path)
        index = git(root, "ls-files", "--stage", "-z", "--", path).split(b"\0")
        records = [r for r in index if r]
        wanted = ("100644 "+spec["after_blob"]+" 0\t"+path).encode()
        if records != [wanted]:
            violations.append("CM01_PROTECTED_INDEX:"+path)
        local = root/path
        chain = [root.joinpath(*PurePosixPath(path).parts[:i])
                 for i in range(1, len(PurePosixPath(path).parts)+1)]
        if (any(p.is_symlink() for p in chain) or not local.is_file()
                or local.stat().st_mode & 0o111
                or hashlib.sha256(local.read_bytes()).hexdigest() != spec["after_sha256"]):
            violations.append("CM01_PROTECTED_WORKTREE:"+path)
    return {"decision": "CM-01", "parent": parent, "commit": migration,
            "protected_files": expected, "violations": sorted(set(violations)),
            "status": "FAIL" if violations else "PASS"}


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
    cm01 = None
    exceptions = set()
    if base == BASE and base_tree == BASE_TREE:
        cm01 = cm01_transition(root, base, head, inventory, CM01_PARENT, CM01_FILES)
        violations.extend(cm01["violations"])
        if cm01["status"] == "PASS":
            exceptions = set(CM01_FILES)
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
        if not permitted(path) and path not in exceptions:
            violations.append("OUT_OF_SCOPE:"+path)
        if modes.get(path) in ("120000", "160000"):
            violations.append("UNSAFE_TREE_MODE:"+path)
        local = root/path
        if local.is_symlink():
            violations.append("LOCAL_SYMLINK:"+path)
        elif local.is_file():
            fingerprints[path] = hashlib.sha256(local.read_bytes()).hexdigest()
    return {"version": "prumo.i86.scope.v1", "base": base, "base_tree": base_tree,
            "head": head, "head_tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
            "branch": branch or "DETACHED", "files": inventory, "cm01": cm01,
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
