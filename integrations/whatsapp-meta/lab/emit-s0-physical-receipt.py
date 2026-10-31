#!/usr/bin/env python3
"""Emit a S0-produced PG17 LAB receipt; consumer/authority live in Meta, not here.

S0 is loaded from an *independent, pinned* checkout and its files are not edited.
This script owns only disposable S0 lab resources and creates a mode-0600
proof artifact. It never serves public HTTP or authorizes a Meta ACK.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys

S0_SHA = "01ffdb093013664b73b18d23f92aac2202578210"
CHANNELS = (("100001", "200001"), ("100002", "200002"))


def git_head(root):
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        text=True, stderr=subprocess.DEVNULL
    ).strip()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("USAGE: emit-s0-physical-receipt.py <pinned-s0-checkout> <new-private-json-file>")
    s0 = Path(sys.argv[1]).resolve(strict=True)
    dest = Path(sys.argv[2]).absolute()
    if git_head(s0) != S0_SHA or dest.exists():
        raise SystemExit("S0_REF_MISMATCH_OR_OUTPUT_EXISTS")
    if s0 == Path(__file__).resolve().parents[3]:
        raise SystemExit("S0_MUST_BE_SEPARATE_CHECKOUT")

    sys.path.insert(0, str(s0))
    old_cwd = Path.cwd()
    lab = None
    cleanup = None
    proof = None
    try:
        os.chdir(s0)  # S0 Laboratory loads its own versioned SQL relatively.
        from integration.s0_meta_ingress import test_ingress as tests
        from integration.s0_meta_ingress.lab import Laboratory
        lab = Laboratory()
        lab.start()
        tests.LAB = lab
        candidate = tests.PhysicalTests("test_09_multichannel_same_app_tenant")
        candidate.setUp()  # Reuse S0's own registered route, M2M key and grants.
        raw = candidate.raw(CHANNELS)
        envelope, signature = candidate.packet(raw=raw)
        result = candidate.s0.call(envelope, signature)
        receipt = candidate.ack(result, 4)  # S0's own readback/signature assertion.
        with lab.admin() as connection:
            rows = connection.execute("SELECT raw,item_count FROM batches").fetchall()
            assert len(rows) == 1, "S0_BATCH_COUNT"
            assert bytes(rows[0]["raw"]) == raw and rows[0]["item_count"] == 4, "S0_COMMIT_READBACK"

        # Trust comes from the *preconfigured S0 lab fixture*, NOT the receipt.
        # All names and binding expectations below are fixed by the independent
        # S0 test fixture above. Never infer them from receipt.body.
        trusted_expected = {
            "app": candidate.app,
            "route": "route_A",
            "route_revision": "1",
            "instance": candidate.s0.instance,
            "receipt_key_id": candidate.s0.receipt_key_id,
            "receipt_key_revision": str(candidate.s0.receipt_revision),
            "m2m_issuer": "LAB_META_INFRA",
            "m2m_key_id": "key_A",
            "m2m_key_revision": "1",
            "expected_item_count": 4,
            "bindings": [
                {"waba": "100001", "phone": "200001", "tenant": "tenant_A",
                 "channel": "channel_A", "revision": "1"},
                {"waba": "100002", "phone": "200002", "tenant": "tenant_A",
                 "channel": "channel_A2", "revision": "1"},
            ],
        }
        proof = {
            "kind": "S0_PG17_DISPOSABLE_RECEIPT_TO_META_UNRATIFIED",
            "source_sha": S0_SHA,
            "raw_base64": base64.b64encode(raw).decode("ascii"),
            "trusted_s0_public_key_base64": base64.b64encode(
                candidate.receipt_key.public_key().public_bytes_raw()
            ).decode("ascii"),
            "trusted_expected": trusted_expected,
            "receipt": receipt,
        }
    finally:
        if lab is not None:
            cleanup = lab.cleanup()
        os.chdir(old_cwd)

    if not cleanup or not all(cleanup.values()) or proof is None:
        raise SystemExit("S0_DISPOSABLE_CLEANUP_FAILED")
    if git_head(s0) != S0_SHA:
        raise SystemExit("S0_HEAD_CHANGED")
    # The artifact has no private key, token or live customer information.
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(proof, handle, separators=(",", ":"), ensure_ascii=False)
        handle.write("\n")
    print("PASS S0 PG17 readback, signed physical receipt, isolated cleanup")


if __name__ == "__main__":
    main()
