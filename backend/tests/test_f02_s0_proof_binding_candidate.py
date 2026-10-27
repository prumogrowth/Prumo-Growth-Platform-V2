"""F02 claimed proof-source binding, synthetic, strict and non-authorizing."""
import json
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, LAB_SOURCE, LOCAL_RECONCILED,
    LOCAL_ORIGIN, UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN, REQUEST_ONLY,
    prepare_handoff,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_proof_binding_candidate import (
    inspect_claimed_proof_binding, ProofBindingGate, ProofBindingResult,
    _PROOF_SOURCES, SCHEMA, SOURCE_STATE, AUTHORITY_STATE,
)

ROOT=Path(__file__).resolve().parents[2]
MAP=ROOT/"docs/contracts/OAI_E04_F02_S0_MAPA_QUATRO_PROVAS_V1.json"


def sample():
    shop, lead, case, closure = (uuid4() for _ in range(4))
    e=ClaimedS0Evidence(shop,lead,case,closure,LOCAL_RECONCILED,
       LOCAL_ORIGIN,LAB_SOURCE,"a"*64,"b"*64,"c"*64,"d"*64,
       UNVERIFIED_EXTERNAL,UNRATIFIED_HUMAN)
    proposal=ReviewOnlyProposal(shop,lead,case,closure,uuid4(),uuid4(),
       "v1","policy-001",datetime(2026,11,10,18,tzinfo=timezone.utc),
       "proof-binding-0001",REQUEST_ONLY)
    ids={"shop_id":str(shop),"lead_id":str(lead),
         "case_id":str(case),"closure_id":str(closure)}
    closure_time=datetime(2026,11,1,12,tzinfo=timezone.utc)
    proofs={}
    for index, (k,(path,symbol)) in enumerate(_PROOF_SOURCES.items(),1):
        t=closure_time+timedelta(hours=index)
        proofs[k]={
          "producer":path,"symbol":symbol,"source_ref":f"source-{index:04d}",
          "source_revision":"1","canonicalization_version":"draft-01",
          "verifier_version":"pending-01","digest_sha256":getattr(e,k),
          "observed_at":t.isoformat(),
          "cutoff_at":(t+timedelta(minutes=10)).isoformat(),
          "source_event_at":(closure_time-timedelta(days=3)).isoformat()
                               if k=="f03_receipt_sha256" else None,
          "scope":dict(ids),"source_state":SOURCE_STATE}
    window=ReviewWindow(datetime(2026,11,10,19,tzinfo=timezone.utc),
                        datetime(2026,11,13,19,tzinfo=timezone.utc))
    q={"schema":SCHEMA,"scope":ids,"closure_at":closure_time.isoformat(),
       "review_window":{"requested_at":window.requested_at.isoformat(),
                        "expires_at":window.expires_at.isoformat()},
       "handoff_sha256":prepare_handoff(e,proposal).untrusted_request_sha256,
       "proofs":proofs,"source_state":SOURCE_STATE,
       "source_authority":AUTHORITY_STATE,"s1_ratified":False,
       "meta_verified":False,"send_authorized":False}
    return e,proposal,window,q


def alter(q,field,**changes):
    copy=dict(q)
    copy["proofs"]=dict(q["proofs"])
    copy["proofs"][field]=dict(q["proofs"][field],**changes)
    return copy


def result(e,p,w,q):
    return inspect_claimed_proof_binding(e,p,w,q).status


class ProofBindingTests(unittest.TestCase):
    def test_01_valid_shape_still_explicitly_not_attested(self):
        self.assertIs(result(*sample()),ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_02_map_and_runtime_sources_agree(self):
        source=json.loads(MAP.read_text(encoding="utf-8"))
        self.assertEqual({v["field"]:(v["producer"],v["symbol"])
                          for v in source["fields"]},_PROOF_SOURCES)
        self.assertTrue(all(v["operationally_verified"] is False
                            for v in source["fields"]))

    def test_03_cross_store_scope_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,dict(q,scope=dict(q["scope"],shop_id=str(uuid4())))),
                      ProofBindingGate.SCOPE_RECHECK_REQUIRED)

    def test_04_cross_lead_proof_rejected(self):
        e,p,w,q=sample();k="f03_receipt_sha256"
        b=alter(q,k,scope=dict(q["scope"],lead_id=str(uuid4())))
        self.assertIs(result(e,p,w,b),ProofBindingGate.SCOPE_RECHECK_REQUIRED)

    def test_05_cross_case_and_closure_rejected(self):
        e,p,w,q=sample();k="human_intent_sha256"
        for part in ("case_id","closure_id"):
            with self.subTest(part=part):
                b=alter(q,k,scope=dict(q["scope"],**{part:str(uuid4())}))
                self.assertIs(result(e,p,w,b),ProofBindingGate.SCOPE_RECHECK_REQUIRED)

    def test_06_changed_claimed_digest_rejected(self):
        e,p,w,q=sample()
        k="c08_local_witness_sha256"
        self.assertIs(result(e,p,w,alter(q,k,digest_sha256="e"*64)),
                      ProofBindingGate.DIGEST_RECHECK_REQUIRED)

    def test_07_changed_evidence_after_handoff_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(replace(e,origin_ledger_sha256="e"*64),p,w,q),
                      ProofBindingGate.HANDOFF_RECHECK_REQUIRED)

    def test_08_swapped_proposal_or_template_rejected(self):
        e,p,w,q=sample()
        for updated in (replace(p,template_version="v2"),
                        replace(p,policy_version="policy-002"),
                        replace(p,idempotency_key="new-binding-0001")):
            self.assertIs(result(e,updated,w,q),
                          ProofBindingGate.HANDOFF_RECHECK_REQUIRED)

    def test_09_forged_source_symbol_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,alter(q,"f03_receipt_sha256",
                                      symbol="FakeSource.load")),
                      ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_10_wrong_source_path_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,alter(q,"origin_ledger_sha256",
                                      producer="backend/another.py")),
                      ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_11_missing_or_extra_proof_fails_closed(self):
        e,p,w,q=sample()
        for proofs in ({k:v for k,v in q["proofs"].items()
                        if k!="human_intent_sha256"},
                       dict(q["proofs"],rogue={})):
            self.assertIs(result(e,p,w,dict(q,proofs=proofs)),
                          ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_12_incomplete_or_extra_field_fails_closed(self):
        e,p,w,q=sample();k="origin_ledger_sha256"
        bad=dict(q["proofs"][k]);bad.pop("source_revision")
        self.assertIs(result(e,p,w,alter(q,k,**{}).copy() if False else
                          dict(q,proofs=dict(q["proofs"],**{k:bad}))),
                      ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)
        self.assertIs(result(e,p,w,alter(q,k,approved=True)),
                      ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_13_bad_version_or_source_ref_rejected(self):
        e,p,w,q=sample();k="f03_receipt_sha256"
        for field,value in (("source_revision","0"),
                            ("source_revision","01"),
                            ("source_revision","-1"),
                            ("source_ref","x"),
                            ("canonicalization_version"," "),
                            ("verifier_version","invalid value")):
            with self.subTest(field=field,value=value):
                self.assertIs(result(e,p,w,alter(q,k,**{field:value})),
                              ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_14_source_observed_after_cutoff_rejected(self):
        e,p,w,q=sample();k="origin_ledger_sha256"
        self.assertIs(result(e,p,w,alter(q,k,observed_at="2026-11-11T12:00:00+00:00")),
                      ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    def test_15_evidence_cutoff_after_proposal_rejected(self):
        e,p,w,q=sample();k="f03_receipt_sha256"
        self.assertIs(result(e,p,w,alter(q,k,cutoff_at="2026-12-01T12:00:00+00:00")),
                      ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    def test_16_evidence_before_closure_rejected(self):
        e,p,w,q=sample();k="human_intent_sha256"
        self.assertIs(result(e,p,w,alter(q,k,observed_at="2026-10-31T12:00:00+00:00")),
                      ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    def test_17_new_closure_after_proposal_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,dict(q,closure_at="2026-11-15T12:00:00+00:00")),
                      ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    def test_18_timezone_equivalent_input_accepted_without_grant(self):
        e,p,w,q=sample()
        e2=replace(p,proposed_at=p.proposed_at.astimezone(timezone(timedelta(hours=-3))))
        self.assertIs(result(e,e2,w,q),ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_19_non_authorized_flags_never_accepted(self):
        e,p,w,q=sample()
        for flag in ("s1_ratified","meta_verified","send_authorized"):
            self.assertIs(result(e,p,w,dict(q,**{flag:True})),
                          ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_20_fake_source_authority_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,dict(q,source_authority="S0_SIGNED")),
                      ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_21_negative_missing_data_fails_closed(self):
        e,p,w,q=sample()
        for bad in (None,[],{},dict(q,proofs=None),
                    dict(q,handoff_sha256=None),dict(q,closure_at=None)):
            self.assertNotEqual(result(e,p,w,bad),
                                ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_22_output_has_only_status(self):
        e,p,w,q=sample()
        out=inspect_claimed_proof_binding(e,p,w,q)
        self.assertEqual([f.name for f in fields(ProofBindingResult)],["status"])
        for forbidden in ("token","signature","approve","send","schedule",
                          "dispatch","persist","retry","receipt","source_ref"):
            self.assertFalse(hasattr(out,forbidden))

    def test_23_disjoint_scope_cannot_be_repaired_by_change_digest(self):
        e,p,w,q=sample()
        k="c08_local_witness_sha256"
        self.assertIs(result(e,p,w,alter(q,k,scope=dict(q["scope"],case_id=str(uuid4())),
                                      digest_sha256=getattr(e,k))),
                      ProofBindingGate.SCOPE_RECHECK_REQUIRED)

    def test_24_no_s0_authentication_claim_in_result(self):
        self.assertTrue(all("AUTHORIZED" not in s.value and
                            "VERIFIED" not in s.value
                            for s in ProofBindingGate))
        self.assertTrue(all("APPROVED" not in s.value and
                            "SEND" not in s.value
                            for s in ProofBindingGate))

    def test_25_swapped_original_window_rejected_even_with_same_handoff(self):
        e,p,w,q=sample()
        changed=ReviewWindow(w.requested_at+timedelta(minutes=1),w.expires_at)
        self.assertEqual(prepare_handoff(e,p).untrusted_request_sha256,
                         q["handoff_sha256"])
        self.assertIs(result(e,p,w=changed,q=q),ProofBindingGate.WINDOW_RECHECK_REQUIRED)

    def test_26_tampered_packet_expiry_refused(self):
        e,p,w,q=sample()
        candidate=dict(q,review_window=dict(q["review_window"],
            expires_at=(w.expires_at+timedelta(hours=1)).isoformat()))
        self.assertIs(result(e,p,w,candidate),ProofBindingGate.WINDOW_RECHECK_REQUIRED)

    def test_27_packet_window_missing_extra_or_naive_refused(self):
        e,p,w,q=sample()
        options=[None,{},dict(q["review_window"],unknown="x"),
                 dict(q["review_window"],requested_at="2026-11-10T19:00:00")]
        for option in options:
            self.assertIs(result(e,p,w,dict(q,review_window=option)),
                          ProofBindingGate.WINDOW_RECHECK_REQUIRED)

    def test_28_window_reversal_refused(self):
        e,p,w,q=sample()
        wrong=ReviewWindow(w.expires_at,w.requested_at)
        self.assertIs(result(e,p,wrong,q),ProofBindingGate.WINDOW_RECHECK_REQUIRED)

    def test_29_window_equivalent_offset_stays_candidate_only(self):
        e,p,w,q=sample()
        offset=timezone(timedelta(hours=-3))
        other=ReviewWindow(w.requested_at.astimezone(offset),
                           w.expires_at.astimezone(offset))
        self.assertIs(result(e,p,other,q),
                      ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_30_voluntary_window_longer_than_48h_is_not_capped(self):
        e,p,w,q=sample()
        self.assertGreater(w.expires_at-w.requested_at,timedelta(hours=48))
        self.assertIs(result(e,p,w,q),
                      ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_31_DST_fold_reversed_absolute_order_refused(self):
        e,p,w,q=sample()
        ny=ZoneInfo("America/New_York")
        start=datetime(2026,11,1,1,45,tzinfo=ny,fold=1)
        end=datetime(2026,11,1,1,50,tzinfo=ny,fold=0)
        wrong=ReviewWindow(start,end)
        packet=dict(q,review_window={"requested_at":start.isoformat(),
                                     "expires_at":end.isoformat()})
        self.assertIs(result(e,p,wrong,packet),
                      ProofBindingGate.WINDOW_RECHECK_REQUIRED)

    def test_32_DST_fold_forward_absolute_order_candidate_only(self):
        e,p,w,q=sample()
        ny=ZoneInfo("America/New_York")
        start=datetime(2026,11,1,1,45,tzinfo=ny,fold=0)
        end=datetime(2026,11,1,1,15,tzinfo=ny,fold=1)
        valid=ReviewWindow(start,end)
        packet=dict(q,review_window={"requested_at":start.isoformat(),
                                     "expires_at":end.isoformat()})
        self.assertIs(result(e,p,valid,packet),
                      ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_33_extra_authority_flag_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,dict(q,approved=True)),
                      ProofBindingGate.DENIED_MALFORMED)

    def test_34_invalid_window_object_or_naive_datetime(self):
        e,p,w,q=sample()
        for invalid in (None,{},ReviewWindow(datetime(2026,11,10,19),w.expires_at),
                        ReviewWindow(w.requested_at,datetime(2026,11,13,19))):
            expected=(ProofBindingGate.DENIED_MALFORMED
                      if not isinstance(invalid,ReviewWindow)
                      else ProofBindingGate.WINDOW_RECHECK_REQUIRED)
            self.assertIs(result(e,p,invalid,q),expected)

    def test_35_historical_F03_event_before_closure_allowed_only_as_claim(self):
        e,p,w,q=sample()
        f=q["proofs"]["f03_receipt_sha256"]
        self.assertLess(datetime.fromisoformat(f["source_event_at"]),
                        datetime.fromisoformat(q["closure_at"]))
        self.assertIs(result(e,p,w,q),ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_36_source_event_later_than_inspection_denied(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,alter(q,"f03_receipt_sha256",
                      source_event_at="2026-11-08T12:00:00+00:00")),
                      ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    def test_37_naive_or_invalid_source_event_denied(self):
        e,p,w,q=sample()
        for bad in ("2026-10-31T10:00:00","2026-10-31",True,{},17):
            self.assertIs(result(e,p,w,alter(q,"f03_receipt_sha256",
                          source_event_at=bad)),ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    def test_38_null_unknown_event_does_not_assert_attestation(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,alter(q,"f03_receipt_sha256",
                      source_event_at=None)),ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_39_source_event_field_cannot_be_removed(self):
        e,p,w,q=sample()
        f="f03_receipt_sha256";src=dict(q["proofs"][f]);src.pop("source_event_at")
        self.assertIs(result(e,p,w,dict(q,proofs=dict(q["proofs"],**{f:src}))),
                      ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    def test_40_offset_equivalent_history_event_keeps_review_only(self):
        e,p,w,q=sample()
        value=datetime.fromisoformat(q["proofs"]["f03_receipt_sha256"]["source_event_at"])
        other=value.astimezone(timezone(timedelta(hours=-3))).isoformat()
        self.assertIs(result(e,p,w,alter(q,"f03_receipt_sha256",
                      source_event_at=other)),ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_41_original_event_time_not_in_unsigned_handoff_digest(self):
        e,p,w,q=sample()
        value=prepare_handoff(e,p).untrusted_request_sha256
        changed=alter(q,"f03_receipt_sha256",
                      source_event_at="2026-10-01T00:00:00+00:00")
        self.assertEqual(changed["handoff_sha256"],value)
        self.assertIs(result(e,p,w,changed),ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)

    def test_42_event_self_approval_extra_flag_rejected(self):
        e,p,w,q=sample()
        self.assertIs(result(e,p,w,alter(q,"human_intent_sha256",
                      event_authorized=True)),ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

if __name__=="__main__":
    unittest.main()
