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
        # Synthetic, ephemeral ASCII HMAC secret: also consumable by Meta JS
        # independently, unlike S0's default arbitrary binary fixture secret.
        candidate.meta = base64.urlsafe_b64encode(os.urandom(32))
        candidate.s0.app_secrets[candidate.app] = candidate.meta

        def empty_ingress():
            with lab.admin() as c:
                return (c.execute("SELECT count(*) AS n FROM batches").fetchone()["n"] == 0
                    and c.execute("SELECT count(*) AS n FROM occurrences").fetchone()["n"] == 0
                    and c.execute("SELECT count(*) AS n FROM nonces").fetchone()["n"] == 0)

        # Each is a fully signed, physical POST with one good channel plus
        # one bad sibling. A rejection must persist neither sibling.
        invalid = (
            ("FOREIGN_TENANT", candidate.raw((("100001", "200001"), ("100003", "200003")))),
            ("FOREIGN_APP", candidate.raw((("100001", "200001"), ("100004", "200004")))),
            ("UNKNOWN_CHANNEL", candidate.raw((("100001", "200001"), ("999999", "999999")))),
        )
        assert empty_ingress(), "S0_LAB_NOT_EMPTY"
        for name, untrusted_raw in invalid:
            wire, sig = candidate.packet(raw=untrusted_raw, ref="m08_" + name)
            rejected = candidate.s0.call(wire, sig)
            assert rejected["decision"] == "REJECTED", name + "_NOT_DENIED"
            assert rejected["receipt"] is None and empty_ingress(), name + "_PARTIAL_COMMIT"

        malformed = json.loads(candidate.raw(CHANNELS))
        del malformed["entry"][1]["changes"][0]["value"]["statuses"][0]["id"]
        malformed_raw = json.dumps(malformed, separators=(",", ":")).encode()
        wire, sig = candidate.packet(raw=malformed_raw, ref="m08_BAD_LATE_ITEM")
        malformed_result = candidate.s0.call(wire, sig)
        assert malformed_result["decision"] == "REJECTED", "M08_LATE_ITEM_NOT_DENIED"
        assert malformed_result["receipt"] is None and empty_ingress(), "M08_LATE_ITEM_PARTIAL"

        with lab.admin() as c:
            c.execute(
                "INSERT INTO bindings VALUES('route_A','100006','200006',%s,'tenant_A','channel_A3',1,true)",
                (candidate.app,)
            )
        wire, sig = candidate.packet(
            raw=candidate.raw((("100001", "200001"), ("100006", "200006"))),
            ref="m08_NO_GRANT"
        )
        ungranted = candidate.s0.call(wire, sig)
        assert ungranted["decision"] == "REJECTED", "M08_UNGRANTED_NOT_DENIED"
        assert ungranted["receipt"] is None and empty_ingress(), "M08_UNGRANTED_PARTIAL"

        raw = candidate.raw(CHANNELS)
        envelope, signature = candidate.packet(raw=raw)
        result = candidate.s0.call(envelope, signature)
        receipt = candidate.ack(result, 4)  # S0's own readback/signature assertion.
        replay = candidate.s0.call(envelope, signature)
        assert replay["decision"] == "REJECTED" and replay["receipt"] is None, "M08_NONCE_REPLAY"
        recovery_envelope, recovery_signature = candidate.packet(raw=raw, scope="recover")
        recovered = candidate.s0.call(recovery_envelope, recovery_signature)
        assert recovered["decision"] == "ACK_ELIGIBLE", "M08_RECOVERY_NOT_ELIGIBLE"
        assert recovered["receipt"] == receipt, "M08_RECOVERY_RECEIPT_CHANGED"
        conflicting_raw = raw + b" "
        conflicting_envelope, conflicting_signature = candidate.packet(raw=conflicting_raw)
        conflict = candidate.s0.call(conflicting_envelope, conflicting_signature)
        assert conflict["decision"] == "CONFLICT", "M08_MUTATED_POST_NOT_CONFLICT"
        assert conflict["receipt"] is None, "M08_CONFLICT_RETURNED_RECEIPT"
        with lab.admin() as connection:
            rows = connection.execute("SELECT raw,item_count FROM batches").fetchall()
            assert len(rows) == 1, "S0_BATCH_COUNT"
            assert bytes(rows[0]["raw"]) == raw and rows[0]["item_count"] == 4, "S0_COMMIT_READBACK"
            assert connection.execute("SELECT count(*) AS n FROM occurrences").fetchone()["n"] == 4, "M08_DUPLICATE_OCCURRENCES"
            assert connection.execute("SELECT count(*) AS n FROM batches").fetchone()["n"] == 1, "M08_DUPLICATE_BATCH"

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
            "trusted_meta_app_secret": candidate.meta.decode("ascii"),
            "trusted_meta_signature_header": json.loads(envelope)["meta_signature"],
            "m08_lab_evidence": {
                "rejected_sibling_batches_without_partial_storage": 5,
                "fresh_nonce_recovery_same_signed_receipt": True,
                "nonce_replay_rejected": True,
                "mutated_same_batch_conflict_without_second_batch": True
            },
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
    print("PASS M08: five invalid multi-item POSTs rejected without partial commit")
    print("PASS M08: same signed receipt on fresh-nonce recovery; replay and conflict denied")
    print("PASS S0 PG17 readback, signed physical receipt, isolated cleanup")


if __name__ == "__main__":
    main()
