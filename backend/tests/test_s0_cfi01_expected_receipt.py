"""Server-only expectation validation, not authentication evidence.

No database or provider calls in these tests; real identity/rollback are checked
by the disposable GoTrue suite. A receipt DTO is not a grant.
"""
from dataclasses import asdict,replace
import unittest
import uuid

from backend.identity_boundary import Denied
from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal,S0InternalReceiptLocal
from backend.s0_cfi01_authenticated_commands_local import CommandState

U='00000000-0000-4000-8000-000000000001'


class DenyIdentity:
    def __init__(self):self.calls=0
    def verify(self,authorization):
        self.calls+=1
        raise Denied('TEST_ONLY_NO_NETWORK')


class ExpectedReceiptValidationTests(unittest.TestCase):
    def setUp(self):
        self.gateway=S0CFI01AtomicCommandsLocal('http://127.0.0.1:54321','test-public-key',
            'postgresql://prumo_cfi01_pgtest_login@127.0.0.1:5432/prumo_s0_test_cfi01',
            key_id=uuid.UUID(U),signing_key=b'test-only-not-a-production-secret')
        self.identity=DenyIdentity();self.gateway._identity=self.identity
        self.receipt=S0InternalReceiptLocal(U,U,U,1,U,'a'*64,U,1)
        self.payload=dict(case_ref=U,closure_event_ref=U,expected_cycle_version=1,idempotency_key='capture-001')

    def test_dictionary_and_malformed_expectations_refused_before_io(self):
        values=[asdict(self.receipt),replace(self.receipt,snapshot_sha256='secret invalid'),
                replace(self.receipt,message_count=True),replace(self.receipt,expected_cycle_version=0),
                replace(self.receipt,store_ref='not-a-uuid')]
        for value in values:
            with self.subTest(value=type(value).__name__):
                r=self.gateway.recheck_internal_receipt('Bearer never-used',self.payload,expected_receipt=value)
                self.assertEqual(r.state,CommandState.INPUT_REJECTED);self.assertIsNone(r.receipt)
        self.assertEqual(self.identity.calls,0)

    def test_valid_expectation_and_legacy_call_both_still_require_identity(self):
        for kw in ({'expected_receipt':self.receipt},{}):
            r=self.gateway.recheck_internal_receipt('Bearer denied',self.payload,**kw)
            self.assertEqual(r.state,CommandState.DENIED);self.assertIsNone(r.receipt)
        self.assertEqual(self.identity.calls,2)
