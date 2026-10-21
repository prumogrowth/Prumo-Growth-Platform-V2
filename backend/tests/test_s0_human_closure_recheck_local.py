"""Offline guards for S0 post-F03 closure recheck; no database or token traffic."""
import unittest
import uuid
from unittest.mock import MagicMock

from backend.identity_boundary import Principal, Denied
from backend.s0_human_closure_recheck_local import (
    RecheckRequest, RecheckState as State, RecheckResult,
    S0LocalClosureRecheck, recheck_human_closure_local,
)

A=uuid.UUID('11111111-1111-4111-8111-111111111111')
S=uuid.UUID('22222222-2222-4222-8222-222222222222')
C=uuid.UUID('33333333-3333-4333-8333-333333333333')
E=uuid.UUID('44444444-4444-4444-8444-444444444444')

class ID:
    def __init__(self, principal=None, error=None):
        self.value=principal if principal is not None else Principal(A,S)
        self.error=error;self.calls=[]
    def verify(self, auth):
        self.calls.append(auth)
        if self.error: raise self.error
        return self.value

class Store:
    def __init__(self, state=State.VERIFIED_REVIEW_ONLY_LOCAL):
        self.state=state;self.calls=[]
    def recheck(self, p, req, s1):
        self.calls.append((p,req,s1))
        return RecheckResult(self.state)

def request():
    return RecheckRequest(str(C),str(E),7,'completion-key-001')

def run(req=None, identity=None, store=None, s1=Ellipsis):
    identity=identity if identity is not None else ID()
    store=store if store is not None else Store()
    s1=object() if s1 is Ellipsis else s1
    return recheck_human_closure_local("Bearer sandbox-only",req if req is not None else request(),
                                       identity=identity,store=store,s1=s1)

class Tests(unittest.TestCase):
    def test_01_only_review_state_no_apply(self):
        x=run()
        self.assertIs(x.state,State.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertEqual(set(RecheckResult.__dataclass_fields__),{'state'})
    def test_02_missing_s1_denies_before_identity(self):
        ident=ID();store=Store()
        self.assertIs(run(identity=ident,store=store,s1=None).state,State.BLOCKED_S1)
        self.assertEqual(ident.calls,[]);self.assertEqual(store.calls,[])
    def test_03_browser_actor_or_shop_not_in_request(self):
        self.assertEqual(set(RecheckRequest.__dataclass_fields__),
                         {'case_ref','closure_event_ref','expected_cycle_version','idempotency_key'})
    def test_04_invalid_case_ref_denied(self):
        ident=ID();self.assertIs(run(RecheckRequest('bad',str(E),7,'completion-key-001'),identity=ident).state,State.DENIED)
        self.assertEqual(ident.calls,[])
    def test_05_invalid_event_ref_denied(self):
        ident=ID();self.assertIs(run(RecheckRequest(str(C),'not-uuid',7,'completion-key-001'),identity=ident).state,State.DENIED)
        self.assertEqual(ident.calls,[])
    def test_06_invalid_bool_version_denied(self):
        self.assertIs(run(RecheckRequest(str(C),str(E),True,'completion-key-001')).state,State.DENIED)
    def test_07_invalid_key_denied(self):
        self.assertIs(run(RecheckRequest(str(C),str(E),7,'x')).state,State.DENIED)
        self.assertIs(run(RecheckRequest(str(C),str(E),7,' leading-key')).state,State.DENIED)
    def test_08_identity_unavailable_fails_closed(self):
        self.assertIs(run(identity=ID(error=OSError('unavailable'))).state,State.UNAVAILABLE)
    def test_09_rejected_identity_denies(self):
        self.assertIs(run(identity=ID(error=Denied('denied'))).state,State.DENIED)
    def test_10_bad_identity_type_denies(self):
        self.assertIs(run(identity=ID(principal="fabricated")).state,State.DENIED)
    def test_11_exact_principal_used_for_store(self):
        s=Store();req=request()
        self.assertIs(run(req,store=s).state,State.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertEqual(s.calls[0][0],Principal(A,S))
        self.assertEqual(s.calls[0][1],req)
    def test_12_storage_exception_fails_closed(self):
        store=Store()
        store.recheck=MagicMock(side_effect=RuntimeError('DB down'))
        self.assertIs(run(store=store).state,State.UNAVAILABLE)
    def test_13_denied_storage_state_not_upgraded(self):
        self.assertIs(run(store=Store(State.DENIED)).state,State.DENIED)
    def test_14_stale_storage_state_not_upgraded(self):
        self.assertIs(run(store=Store(State.STALE)).state,State.STALE)
    def test_15_remote_dsn_rejected_by_parent_policy(self):
        with self.assertRaises(ValueError):
            S0LocalClosureRecheck('postgresql://postgres:pw@prod.example.com/prumo_s0_test_foo')
    def test_16_public_model_has_no_grant_or_message_access(self):
        self.assertFalse(hasattr(RecheckResult(State.VERIFIED_REVIEW_ONLY_LOCAL),'messages'))
        self.assertFalse(hasattr(RecheckResult(State.VERIFIED_REVIEW_ONLY_LOCAL),'authorized'))

if __name__=='__main__':
    unittest.main()
