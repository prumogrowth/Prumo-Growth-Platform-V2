#!/usr/bin/env python3
"""Read-only documentary verification. Never connects to a service/database.

Use --sources-root for snapshots downloaded by the connector, organized as
<snapshot>/<repository path>, or --git-repo for a clone already containing the
pinned commits. No fetch, credential lookup, SQL or application import occurs.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def verify(reader):
    evidence = json.loads((ROOT / "EVIDENCIAS.json").read_text())
    matrix = json.loads((ROOT / "MATRIZ_G01_G07.json").read_text())
    checked = {}
    for item in evidence["sources"]:
        path = PurePosixPath(item["path"])
        assert not path.is_absolute() and ".." not in path.parts, path
        data = reader(item)
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        assert blob == item["blob_sha"], f"blob drift: {item['snapshot']}:{path}"
        checked[(item["snapshot"], item["path"])] = data

    pin = checked[("f02", "docs/contracts/upstream/OAI_S0_F02_REVIEW_RESULT_SCHEMA_0_1_PINNED.json")]
    schema_path = "docs/contratos/f02_s0_review/result.schema.json"
    assert pin == checked[("s0", schema_path)] == checked[("i79", schema_path)]
    schema = json.loads(pin)
    assert schema["$id"] == "prumo.s0.f02.review.result/0.1-candidate"
    assert len(schema["properties"]["state"]["enum"]) == 13
    for flag in ("send_authorized", "scheduling_authorized", "commercial_transition_authorized"):
        assert schema["properties"][flag]["const"] is False

    # Blob identity in all three remote trees, not copied source assertions.
    preserved = [
        "backend/f02_reconciled_human_authorization_handoff.py",
        "backend/f02_reconciled_review_lifecycle.py",
        "backend/f02_reconciled_review_recovery.py",
    ]
    for path in preserved:
        # S0/I79 retained blobs are recorded in source_tree_comparison.
        row = next(x for x in evidence["source_tree_comparison"] if x["path"] == path)
        assert row["f02"] == row["s0"] == row["i79"]

    source = checked[("s0", "backend/s0_f02_review_registry_local.py")]
    tree = ast.parse(source)
    enum = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ReviewState")
    values = {ast.literal_eval(n.value) for n in enum.body if isinstance(n, ast.Assign)}
    assert values == set(schema["properties"]["state"]["enum"])
    assert source == checked[("i79", "backend/s0_f02_review_registry_local.py")]

    assert [g["id"] for g in matrix["gates"]] == [f"G{i:02}" for i in range(1, 8)]
    for flag in ("contract_ratified", "operational_homologation", "send_authorized"):
        assert matrix[flag] is False
    for g in matrix["gates"]:
        assert g["levels"]["operational"] == "PENDENTE"
        assert set(g["evidence"]) <= evidence["evidence_ids"].keys()
        assert all(g[k] for k in ("status", "reusable", "evidence", "gaps", "owner", "next_action", "decisions"))
    for checkpoint in evidence["checkpoints"]:
        assert checkpoint["ci_conclusion"] == "success"
        assert all(p.startswith("docs/") for p in checkpoint["post_ci_files"])
    return {
        "result": "PASS_DOCUMENTARY_INTEGRITY_ONLY",
        "sources_verified": len(checked),
        "schema_blob": "61598ba702dc03f9f715673118c88f9359e64113",
        "states_compared": len(values),
        "preserved_f02_modules": len(preserved),
        "gates_traced": len(matrix["gates"]),
        "operational_homologation": False,
        "send_authorized": False,
    }


def main():
    if not __debug__:
        raise ValueError("Run without -O: documentary assertions must remain enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sources-root", type=Path)
    group.add_argument("--git-repo", type=Path)
    args = parser.parse_args()
    if args.sources_root:
        def reader(item):
            return (args.sources_root / item["snapshot"] / item["path"]).read_bytes()
    else:
        def reader(item):
            return subprocess.run(
                ["git", "-C", str(args.git_repo), "show", f"{item['commit']}:{item['path']}"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ).stdout
    print(json.dumps(verify(reader), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
