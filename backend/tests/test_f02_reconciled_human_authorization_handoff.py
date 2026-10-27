"""Pure F02 handoff contract; S0 assertions are never operational authority."""
import unittest
from dataclasses import replace, fields
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, HandoffState, HandoffResult,
    LAB_SOURCE, LOCAL_RECONCILED, LOCAL_ORIGIN,
    UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN, REQUEST_ONLY, prepare_handoff,
)


def fixtures():
    shop, lead, case, closure = (uuid4() for _ in range(4))
    evidence = ClaimedS0Evidence(
        shop, lead, case, closure, LOCAL_RECONCILED, LOCAL_ORIGIN,
        LAB_SOURCE, "a" * 64, "b" * 64, "c" * 64, "d" * 64,
        UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN,
    )
    proposal = ReviewOnlyProposal(
        shop, lead, case, closure, uuid4(), uuid4(),
        "v1", "policy-001",
        datetime(2026, 11, 1, 16, 0, tzinfo=timezone.utc),
        "reconciled-case-0001", REQUEST_ONLY,
    )
    return evidence, proposal


class Tests(unittest.TestCase):
    def test_01_valid_claim_yields_only_non_authorizing_handoff(self):
        e, p = fixtures()
        result = prepare_handoff(e, p)
        self.assertIs(result.status, HandoffState.HANDOFF_REVIEW_ONLY)
        self.assertEqual(len(result.untrusted_request_sha256), 64)
        self.assertEqual(tuple(x.name for x in fields(HandoffResult)),
                         ("status", "untrusted_request_sha256", "contract_version"))

    def test_02_deterministic_fingerprint_same_scope(self):
        e, p = fixtures()
        self.assertEqual(prepare_handoff(e, p), prepare_handoff(e, p))

    def test_03_scope_tenant_crossing_denied(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(e, replace(p, shop_id=uuid4())).status,
                      HandoffState.SCOPE_MISMATCH)

    def test_04_scope_lead_crossing_denied(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(e, replace(p, lead_id=uuid4())).status,
                      HandoffState.SCOPE_MISMATCH)

    def test_05_case_and_closure_binding(self):
        e, p = fixtures()
        for field in ("case_id", "closure_id"):
            with self.subTest(field=field):
                self.assertIs(prepare_handoff(e, replace(p, **{field: uuid4()})).status,
                              HandoffState.SCOPE_MISMATCH)

    def test_06_source_must_be_known_lab_only(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(replace(e, source="META_CONFIRMED"), p).status,
                      HandoffState.S0_RECONCILIATION_REQUIRED)

    def test_07_no_converting_reserved_to_safe(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(
            replace(e, reconciliation_state="EXTERNAL_DISPATCH_UNKNOWN"), p).status,
            HandoffState.S0_RECONCILIATION_REQUIRED)

    def test_08_fake_s0_reconciliation_boolean_not_allowed(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(replace(e, reconciliation_state=True), p).status,
                      HandoffState.S0_RECONCILIATION_REQUIRED)

    def test_09_origin_must_be_explicit(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(replace(e, origin_state="MISSING_ORIGIN"), p).status,
                      HandoffState.S0_RECONCILIATION_REQUIRED)

    def test_10_hmac_and_evidence_digest_format(self):
        e, p = fixtures()
        for key in ("f03_receipt_sha256", "c08_local_witness_sha256",
                    "origin_ledger_sha256", "human_intent_sha256"):
            with self.subTest(key=key):
                self.assertIs(prepare_handoff(replace(e, **{key: "a" * 63}), p).status,
                              HandoffState.DENIED_MALFORMED)

    def test_11_human_ratification_cannot_be_user_declared(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(
            replace(e, human_operational_ratification="APPROVED"), p).status,
            HandoffState.OPERATIONAL_RATIFICATION_NOT_ATTESTED)

    def test_12_external_cancel_cannot_be_user_declared(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(
            replace(e, external_disposition="META_CANCELLED"), p).status,
            HandoffState.EXTERNAL_DISPOSITION_NOT_ATTESTED)

    def test_13_send_command_rejected(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(replace(e, source=LAB_SOURCE),
                    replace(p, action="SEND_NOW")).status,
                      HandoffState.DENIED_MALFORMED)

    def test_14_timezone_is_required(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(
            e, replace(p, proposed_at=datetime(2026, 11, 1, 16))).status,
            HandoffState.DENIED_MALFORMED)

    def test_15_utc_normalization_retains_digest(self):
        e, p = fixtures()
        offset = timezone(timedelta(hours=-3))
        same = p.proposed_at.astimezone(offset)
        self.assertEqual(prepare_handoff(e, p).untrusted_request_sha256,
                         prepare_handoff(e, replace(p, proposed_at=same)
                                        ).untrusted_request_sha256)

    def test_16_changes_to_template_or_time_change_digest(self):
        e, p = fixtures()
        h = prepare_handoff(e, p).untrusted_request_sha256
        for modified in (
            replace(p, template_id=uuid4()),
            replace(p, proposed_at=p.proposed_at + timedelta(minutes=1)),
            replace(p, policy_version="policy-002"),
        ):
            self.assertNotEqual(h, prepare_handoff(e, modified).untrusted_request_sha256)

    def test_17_changed_evidence_does_not_reuse_digest(self):
        e, p = fixtures()
        original = prepare_handoff(e, p).untrusted_request_sha256
        self.assertNotEqual(original, prepare_handoff(
            replace(e, origin_ledger_sha256="e" * 64), p).untrusted_request_sha256)

    def test_18_fake_type_and_null_denied(self):
        e, p = fixtures()
        for a, b in (({}, p), (e, None), (e, {}), (None, None)):
            with self.subTest(a=type(a).__name__, b=type(b).__name__):
                self.assertIs(prepare_handoff(a, b).status,
                              HandoffState.DENIED_MALFORMED)

    def test_19_nil_uuid_and_short_idempotency_denied(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(
            e, replace(p, template_id=UUID(int=0))).status,
            HandoffState.DENIED_MALFORMED)
        self.assertIs(prepare_handoff(
            e, replace(p, idempotency_key="x")).status,
            HandoffState.DENIED_MALFORMED)

    def test_20_no_execution_methods(self):
        from backend.f02_reconciled_human_authorization_handoff import (
            HandoffResult, prepare_handoff,
        )
        self.assertFalse(any(hasattr(HandoffResult, name) for name in (
            "approve", "schedule", "send", "execute", "persist")))
        self.assertFalse(any(hasattr(prepare_handoff, name) for name in (
            "approve", "schedule", "send", "execute", "persist")))

    def test_21_template_version_strict_format(self):
        e, p = fixtures()
        self.assertIs(prepare_handoff(e, p).status,
                      HandoffState.HANDOFF_REVIEW_ONLY)
        for bad in ("v", "VERSION_1", "v-1", "v1.0", "v" + "1" * 20):
            with self.subTest(template_version=bad):
                self.assertIs(prepare_handoff(
                    e, replace(p, template_version=bad)).status,
                    HandoffState.DENIED_MALFORMED)


if __name__ == "__main__":
    unittest.main()
