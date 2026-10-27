import hashlib
import json
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
import unittest
from uuid import uuid4

from backend.tests.test_f02_reconciled_human_authorization_handoff import fixtures
from backend.f02_reconciled_human_authorization_handoff import prepare_handoff
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.s0_cfi01_atomic_commands_local import S0InternalReceiptLocal
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_f02_review_registry_local import prepare_document,ReviewResult,ReviewState


class ReviewContractTests(unittest.TestCase):
    def setUp(self):
        self.e,self.p=fixtures()
        self.binding=S0F03BoundReceiptLocal(S0InternalReceiptLocal(str(self.p.shop_id),str(self.p.case_id),
            str(self.p.closure_id),1,str(uuid4()),'1'*64,str(uuid4()),1),'capture-request-0001')
        now=datetime(2026,10,26,tzinfo=timezone.utc)
        self.window=ReviewWindow(now,now+timedelta(minutes=10))

    def doc(self,**changes):
        return prepare_document(changes.get('binding',self.binding),changes.get('e',self.e),
                                changes.get('p',self.p),changes.get('window',self.window))

    def test_01_reuses_f02_hash_without_relabeling_as_signed_evidence(self):
        d=json.loads(self.doc())
        self.assertEqual(d['request_sha256'],prepare_handoff(self.e,self.p).untrusted_request_sha256)
        self.assertEqual(d['evidence']['external_disposition'],'EXTERNAL_DISPATCH_UNVERIFIED')

    def test_02_f02_window_not_in_its_hash_is_in_s0_signed_document(self):
        other=replace(self.window,expires_at=self.window.expires_at+timedelta(seconds=1))
        self.assertNotEqual(self.doc(),self.doc(window=other))
        self.assertEqual(json.loads(self.doc())['request_sha256'],json.loads(self.doc(window=other))['request_sha256'])

    def test_03_case_version_or_scope_never_inferred_from_claims(self):
        bad=replace(self.binding,receipt=replace(self.binding.receipt,case_ref=str(uuid4())))
        with self.assertRaises(ValueError):self.doc(binding=bad)

    def test_04_no_client_timeline_clock_or_authorization_added(self):
        self.assertEqual(set(json.loads(self.doc())),{'schema','request_sha256','evidence','proposal','requested_at','expires_at'})
        with self.assertRaises(ValueError):self.doc(e=replace(self.e,human_operational_ratification='APPROVED'))

    def test_05_result_never_grants_any_operation_including_error_and_terminal(self):
        for state in ReviewState:
            p=ReviewResult(state).projection()
            self.assertFalse(p['send_authorized']);self.assertFalse(p['scheduling_authorized'])
            self.assertFalse(p['commercial_transition_authorized'])
            self.assertEqual(p['human_ratification'],'NOT_IMPLEMENTED_CONTRACT_PENDING')

    def test_06_window_is_timezone_aware_and_offsets_canonicalize(self):
        offset=timezone(timedelta(hours=-3))
        w=ReviewWindow(self.window.requested_at.astimezone(offset),self.window.expires_at.astimezone(offset))
        self.assertEqual(self.doc(),self.doc(window=w))
        with self.assertRaises(ValueError):self.doc(window=replace(w,expires_at=datetime(2026,10,27)))

    def test_07_supplied_dictionary_is_not_a_server_binding(self):
        with self.assertRaises(ValueError):self.doc(binding={'receipt':self.binding.receipt})

    def test_08_three_reused_f02_modules_and_four_suites_are_pinned(self):
        root=Path(__file__).resolve().parents[2]
        manifest=json.loads((root/'integration/f02/f02_source_manifest.json').read_text())
        self.assertEqual(len(manifest['files']),7)
        for item in manifest['files']:
            self.assertEqual(hashlib.sha256((root/item['path']).read_bytes()).hexdigest(),item['sha256'],item['path'])
