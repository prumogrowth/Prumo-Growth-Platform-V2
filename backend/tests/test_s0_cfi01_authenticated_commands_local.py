"""Contract tests: actual GoTrue-verifier parsing with a synthetic HTTP opener.

The HTTP fixture is NOT a real GoTrue server or a cryptographic JWT validator.
Storage ports are fakes here; separate PG17 integration tests exercise real SQL.
"""
import base64
import io
import json
import unittest
import uuid
import urllib.error

from backend.identity_boundary import Principal
from backend.s0_cfi01_authenticated_commands_local import (
    S0CFI01AuthenticatedCommandsLocal as Gateway, CommandState as State)
from backend.s0_human_closure_event_local import ClosureResult, ClosureState
from backend.s0_human_closure_recheck_local import RecheckResult, RecheckState

ACTOR=uuid.UUID('11111111-1111-4111-8111-111111111111')
SESSION=uuid.UUID('22222222-2222-4222-8222-222222222222')
CASE=str(uuid.UUID('33333333-3333-4333-8333-333333333333'))
EVENT=str(uuid.UUID('44444444-4444-4444-8444-444444444444'))
DSN='postgresql://postgres:secret@localhost/prumo_s0_test_auth'
def token(sub=ACTOR, session=SESSION, role='authenticated'):
    def encoded(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip('=')
    return 'Bearer '+'.'.join([
        encoded({'alg':'HS256','typ':'JWT'}),
        encoded({'sub':str(sub),'session_id':str(session),'role':role}),
        'fixture_signature_not_cryptographically_verified'
    ])

class Response:
    def __init__(self,data):self.status=200;self.buffer=io.BytesIO(json.dumps(data).encode())
    def read(self,size):return self.buffer.read(size)
    def __enter__(self):return self
    def __exit__(self,*args):return False

class Opener:
    def __init__(self,actor=ACTOR,role='authenticated',error=None):
        self.actor=actor;self.role=role;self.error=error;self.calls=[]
    def open(self,request,timeout):
        self.calls.append((request,timeout))
        if self.error:raise self.error
        return Response({'id':str(self.actor),'role':self.role})

class Store:
    def __init__(self,capture=None,recheck=None):
        self.calls=[]
        self.capture_result=capture if capture is not None else ClosureResult(
            ClosureState.CAPTURED_LOCAL_ONLY,EVENT)
        self.recheck_result=recheck if recheck is not None else RecheckResult(
            RecheckState.VERIFIED_REVIEW_ONLY_LOCAL)
    def capture(self,p,req,s1):
        self.calls.append(('capture',p,req))
        return self.capture_result
    def recheck(self,p,req,s1):
        self.calls.append(('recheck',p,req))
        return self.recheck_result

def gateway(openr=None,store=None):
    o=openr or Opener()
    st=store or Store()
    g=Gateway('https://auth.example.invalid','public-key-test',DSN,opener=o)
    g._capture_store=st
    g._recheck_store=st
    return g,o,st
CAP={'case_ref':CASE,'expected_cycle_version':7,'idempotency_key':'test-request-key-01'}
REV={**CAP,'closure_event_ref':EVENT}

class Tests(unittest.TestCase):
    def test_01_capture_uses_auth_endpoint_and_actual_verifier(self):
        g,o,s=gateway()
        x=g.execute(token(),'capture_human_closure',CAP)
        self.assertEqual(x.state,State.CAPTURED_LOCAL_ONLY)
        self.assertEqual(x.closure_event_ref,EVENT)
        self.assertEqual(s.calls[0][1],Principal(ACTOR,SESSION))
        req,timeout=o.calls[0]
        self.assertEqual(req.full_url,'https://auth.example.invalid/auth/v1/user')
        self.assertEqual(req.get_method(),'GET')
        self.assertEqual(timeout,5)
    def test_02_recheck_reverifies_with_gotrue_code(self):
        g,o,s=gateway()
        x=g.execute(token(),'recheck_human_closure',REV)
        self.assertEqual(x.state,State.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertIsNone(x.closure_event_ref)
        self.assertEqual(len(o.calls),1)
        self.assertEqual(s.calls[0][0],'recheck')
    def test_03_capture_and_recheck_verify_twice(self):
        g,o,s=gateway()
        g.execute(token(),'capture_human_closure',CAP)
        g.execute(token(),'recheck_human_closure',REV)
        self.assertEqual(len(o.calls),2)
    def test_04_unsupported_command_refused_without_http(self):
        g,o,s=gateway()
        x=g.execute(token(),'grant_admin',CAP)
        self.assertEqual(x.state,State.UNSUPPORTED_COMMAND)
        self.assertEqual(o.calls,[])
    def test_05_browser_actor_is_rejected(self):
        g,o,s=gateway()
        x=g.execute(token(),'capture_human_closure',{**CAP,'actor_id':str(ACTOR)})
        self.assertEqual(x.state,State.INPUT_REJECTED)
        self.assertEqual(o.calls,[])
    def test_06_browser_store_is_rejected(self):
        g,o,s=gateway()
        self.assertEqual(g.execute(token(),'capture_human_closure',{**CAP,'store_ref':'any'}).state,
                         State.INPUT_REJECTED)
        self.assertEqual(o.calls,[])
    def test_07_model_permission_flag_is_rejected(self):
        g,o,s=gateway()
        self.assertEqual(g.execute(token(),'recheck_human_closure',{**REV,'model_authorized':True}).state,
                         State.INPUT_REJECTED)
    def test_08_no_extra_sensitive_model_payload(self):
        g,o,s=gateway()
        self.assertEqual(g.execute(token(),'recheck_human_closure',{**REV,'fields_proposed':[]}).state,
                         State.INPUT_REJECTED)
    def test_09_bad_payload_type_rejected(self):
        g,o,s=gateway()
        self.assertEqual(g.execute(token(),'capture_human_closure',[]).state,State.INPUT_REJECTED)
    def test_10_missing_payload_field_rejected(self):
        g,o,s=gateway()
        self.assertEqual(g.execute(token(),'capture_human_closure',{'case_ref':CASE}).state,
                         State.INPUT_REJECTED)
    def test_11_wrong_gotrue_sub_denied(self):
        g,o,s=gateway()
        x=g.execute(token(sub=uuid.uuid4()),'capture_human_closure',CAP)
        self.assertEqual(x.state,State.DENIED)
        self.assertEqual(s.calls,[])
    def test_12_wrong_role_in_user_response_denied(self):
        g,o,s=gateway(openr=Opener(role='anon'))
        self.assertEqual(g.execute(token(),'capture_human_closure',CAP).state,State.DENIED)
    def test_13_invalid_jwt_role_denied(self):
        g,o,s=gateway()
        self.assertEqual(g.execute(token(role='service_role'),'capture_human_closure',CAP).state,
                         State.DENIED)
        self.assertEqual(s.calls,[])
    def test_14_http_401_denied(self):
        err=urllib.error.HTTPError('https://auth.example.invalid',401,'unauthorized',{},None)
        g,o,s=gateway(openr=Opener(error=err))
        self.assertEqual(g.execute(token(),'capture_human_closure',CAP).state,State.DENIED)
    def test_15_network_failure_unavailable(self):
        g,o,s=gateway(openr=Opener(error=OSError('auth down')))
        self.assertEqual(g.execute(token(),'capture_human_closure',CAP).state,State.UNAVAILABLE)
    def test_16_invalid_bearer_denied(self):
        g,o,s=gateway()
        self.assertEqual(g.execute('Bearer short','capture_human_closure',CAP).state,State.DENIED)
    def test_17_session_from_jwt_used_only_after_verified_identity(self):
        new_session=uuid.uuid4()
        g,o,s=gateway()
        self.assertEqual(g.execute(token(session=new_session),'capture_human_closure',CAP).state,
                         State.CAPTURED_LOCAL_ONLY)
        self.assertEqual(s.calls[0][1].session_id,new_session)
    def test_18_capture_denied_no_receipt_leak(self):
        st=Store(capture=ClosureResult(ClosureState.DENIED))
        g,o,s=gateway(store=st)
        x=g.execute(token(),'capture_human_closure',CAP)
        self.assertEqual(x.state,State.DENIED)
        self.assertIsNone(x.closure_event_ref)
    def test_19_recheck_stale_not_promoted_to_applied(self):
        st=Store(recheck=RecheckResult(RecheckState.STALE))
        g,o,s=gateway(store=st)
        x=g.execute(token(),'recheck_human_closure',REV)
        self.assertEqual(x.state,State.STALE)
        self.assertFalse(hasattr(x,'applied'))
    def test_20_cannot_initialize_with_remote_postgres(self):
        with self.assertRaises(ValueError):
            Gateway('https://auth.example.invalid','key',
                    'postgresql://postgres:pw@prod.example.invalid/customers',
                    opener=Opener())

if __name__=='__main__':
    unittest.main()
