import os
import sys
import types
import uuid
import unittest
from dataclasses import replace
from unittest.mock import patch

from backend.identity_boundary import Principal, Denied, IdentityUnavailable
from backend.s0_human_closure_event_local import (
    ClosureRequest, ClosureState as Status, S1Proof, S0LocalClosureStore,
    capture_human_closure_local, _SESSION, _CASE, _GRANT,
    _LOCK_CONVERSATIONS, _MESSAGES, _EXISTING, _INSERT, _fingerprint,
)
A=uuid.UUID('11111111-1111-4111-8111-111111111111')
S=uuid.UUID('22222222-2222-4222-8222-222222222222')
C=uuid.UUID('33333333-3333-4333-8333-333333333333')
SHOP=uuid.UUID('44444444-4444-4444-8444-444444444444')
ASSIGN=uuid.UUID('55555555-5555-4555-8555-555555555555')
CONV=uuid.UUID('66666666-6666-4666-8666-666666666666')
MSG=uuid.UUID('77777777-7777-4777-8777-777777777777')
EV=uuid.UUID('88888888-8888-4888-8888-888888888888')
ROWS=[(MSG,'2026-10-20T10:00:00Z','entrada','simulado','Oi',None)]
DSN='postgresql://postgres:pass@localhost/prumo_s0_test_lab'

class Identity:
    def __init__(self, error=None): self.calls=[];self.error=error
    def verify(self,auth):
        self.calls.append(auth)
        if self.error: raise self.error
        return Principal(A,S)

class S1:
    def __init__(self,result=S1Proof.ALLOW):
        self.result=result;self.calls=[];self.lock_calls=[]
    def lock_team(self,cur,principal):
        self.lock_calls.append((cur,principal))
        return self.result
    def check(self,cur,principal,store,case,assignment):
        self.calls.append((cur,principal,store,case,assignment))
        return self.result

class Cursor:
    def __init__(self):
        self.calls=[];self.next=None;self.case=(SHOP,4,'em atendimento pelo operador',ASSIGN)
        self.session=True;self.grant=True;self.conversations=[(CONV,)];self.messages=list(ROWS)
        self.prior=None;self.inserted=EV;self.inject=None
    def execute(self,sql,args):
        self.calls.append((sql,args))
        if self.inject is not None and self.inject in sql: raise RuntimeError('DB TEST FAILURE')
        if sql==_SESSION:self.next=(1,) if self.session else None
        elif sql==_CASE:self.next=self.case
        elif sql==_GRANT:self.next=(1,) if self.grant else None
        elif sql==_LOCK_CONVERSATIONS:self.next=self.conversations
        elif sql==_MESSAGES:self.next=self.messages
        elif sql==_EXISTING:self.next=self.prior
        elif sql==_INSERT:self.next=(self.inserted,) if self.inserted else None
        else:raise AssertionError('Unknown query')
    def fetchone(self):return self.next
    def fetchall(self):return list(self.next)
    def __enter__(self):return self
    def __exit__(self,*args):return False

class Conn:
    def __init__(self,cursor):self.cur=cursor
    def cursor(self):return self.cur
    def __enter__(self):return self
    def __exit__(self,*args):return False

def execute(cursor=None, s1=Ellipsis, request=None, identity=None):
    cursor=cursor if cursor is not None else Cursor()
    s1=S1() if s1 is Ellipsis else s1
    request=request or ClosureRequest(str(C),4,'key-A-12345')
    identity=identity or Identity()
    store=S0LocalClosureStore(DSN)
    with patch.dict(sys.modules,{'psycopg':types.SimpleNamespace(connect=lambda *_args,**_kwargs:Conn(cursor))}):
        result=capture_human_closure_local('Bearer TEST',request,identity=identity,store=store,s1=s1)
    return result,cursor,s1,identity

class Tests(unittest.TestCase):
    def test_01_event_insert_is_local_only(self):
        result,cur,s1,identity=execute()
        self.assertIs(result.state,Status.CAPTURED_LOCAL_ONLY)
        self.assertEqual(result.closure_event_ref,str(EV))
        self.assertEqual(identity.calls,['Bearer TEST'])
        self.assertEqual(len(s1.calls),1)
    def test_02_s1_absent_does_not_even_open_db(self):
        result,cur,_,_=execute(s1=None)
        self.assertIs(result.state,Status.BLOCKED_S1)
        self.assertEqual(cur.calls,[])
    def test_03_s1_denies_before_message_access(self):
        result,cur,*_=execute(s1=S1(S1Proof.DENY))
        self.assertIs(result.state,Status.BLOCKED_S1)
        self.assertNotIn(_MESSAGES,[x[0] for x in cur.calls])
    def test_04_s1_string_result_is_not_authorization(self):
        self.assertIs(execute(s1=S1('ALLOW'))[0].state,Status.BLOCKED_S1)
    def test_05_session_absent_denied(self):
        cur=Cursor();cur.session=False
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
        self.assertEqual(len(cur.calls),1)
    def test_06_case_not_owned_denied(self):
        cur=Cursor();cur.case=None
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
    def test_07_store_grant_revoked_denied(self):
        cur=Cursor();cur.grant=False
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
    def test_08_version_stale(self):
        cur=Cursor();cur.case=(SHOP,5,'em atendimento pelo operador',ASSIGN)
        self.assertIs(execute(cursor=cur)[0].state,Status.STALE)
    def test_09_bank_submission_not_closable(self):
        cur=Cursor();cur.case=(SHOP,4,'cadastro enviado ao banco',ASSIGN)
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
    def test_10_sold_not_closable(self):
        cur=Cursor();cur.case=(SHOP,4,'vendido',ASSIGN)
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
    def test_11_no_conversation_not_captured(self):
        cur=Cursor();cur.conversations=[]
        self.assertIs(execute(cursor=cur)[0].state,Status.NO_CONVERSATION)
    def test_12_no_messages_not_captured(self):
        cur=Cursor();cur.messages=[]
        self.assertIs(execute(cursor=cur)[0].state,Status.NO_CONVERSATION)
    def test_13_too_many_messages_fail_closed(self):
        cur=Cursor();cur.messages=list(ROWS)*2501
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
    def test_14_idempotent_retry_same_snapshot(self):
        cur=Cursor();cur.prior=(EV,A,ASSIGN,4,_fingerprint(ROWS))
        res,cur,*_=execute(cursor=cur)
        self.assertIs(res.state,Status.ALREADY_CAPTURED)
        self.assertEqual(res.closure_event_ref,str(EV))
        self.assertNotIn(_INSERT,[q for q,p in cur.calls])
    def test_15_idempotency_key_after_new_inbound_stale(self):
        cur=Cursor();cur.prior=(EV,A,ASSIGN,4,'a'*64)
        self.assertIs(execute(cursor=cur)[0].state,Status.STALE)
    def test_16_other_actor_cannot_replay(self):
        cur=Cursor();cur.prior=(EV,uuid.uuid4(),ASSIGN,4,_fingerprint(ROWS))
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
    def test_17_reassignment_revokes_prior(self):
        cur=Cursor();cur.prior=(EV,A,uuid.uuid4(),4,_fingerprint(ROWS))
        self.assertIs(execute(cursor=cur)[0].state,Status.DENIED)
    def test_18_second_key_same_snapshot_unique_conflict(self):
        cur=Cursor();cur.inserted=None
        self.assertIs(execute(cursor=cur)[0].state,Status.DUPLICATE_SNAPSHOT)
    def test_19_browser_cannot_send_store_actor(self):
        self.assertEqual(set(ClosureRequest.__dataclass_fields__),{'case_ref','expected_cycle_version','idempotency_key'})
    def test_20_invalid_case_before_identity(self):
        ident=Identity();res,cur,*_=execute(request=ClosureRequest('bad',4,'key-A-12345'),identity=ident)
        self.assertIs(res.state,Status.DENIED)
        self.assertEqual(ident.calls,[])
    def test_21_bool_version_denied(self):
        self.assertIs(execute(request=ClosureRequest(str(C),True,'key-A-12345'))[0].state,Status.DENIED)
    def test_22_short_key_denied(self):
        self.assertIs(execute(request=ClosureRequest(str(C),4,'x'))[0].state,Status.DENIED)
    def test_23_whitespace_key_denied(self):
        self.assertIs(execute(request=ClosureRequest(str(C),4,' key-long '))[0].state,Status.DENIED)
    def test_24_invalid_identity_denied(self):
        self.assertIs(execute(identity=Identity(error=Denied('revoked')))[0].state,Status.DENIED)
    def test_25_unavailable_identity_fail_closed(self):
        self.assertIs(execute(identity=Identity(error=IdentityUnavailable('unavailable')))[0].state,Status.UNAVAILABLE)
    def test_26_database_failure_fail_closed(self):
        cur=Cursor();cur.inject='insert into'
        self.assertIs(execute(cursor=cur)[0].state,Status.UNAVAILABLE)
    def test_27_remote_db_rejected(self):
        with self.assertRaises(ValueError):S0LocalClosureStore('postgresql://postgres:pw@outside.test/prumo_s0_test_x')
    def test_28_nonprivileged_user_rejected(self):
        with self.assertRaises(ValueError):S0LocalClosureStore('postgresql://service:pw@localhost/prumo_s0_test_x')
    def test_29_unsafe_db_name_rejected(self):
        with self.assertRaises(ValueError):S0LocalClosureStore('postgresql://postgres:pw@localhost/customers')
    def test_30_no_commercial_update_sql(self):
        from backend import s0_human_closure_event_local as mod
        queries=[mod._SESSION,mod._CASE,mod._GRANT,mod._LOCK_CONVERSATIONS,mod._MESSAGES,mod._EXISTING,mod._INSERT]
        self.assertTrue(all(q.lower().lstrip().startswith(('select','insert into prumo_private.cfi01_')) for q in queries))
        self.assertFalse(any('update public.ciclos_comerciais' in q.lower() for q in queries))
    def test_31_snapshot_uses_content_without_returning_it(self):
        res,cur,*_=execute()
        self.assertFalse(hasattr(res,'messages'))
        self.assertNotIn('Oi',repr(res))
    def test_32_snapshot_hash_is_stable_and_changes_with_new_message(self):
        self.assertEqual(_fingerprint(ROWS),_fingerprint(list(ROWS)))
        self.assertNotEqual(_fingerprint(ROWS),_fingerprint(ROWS+[(uuid.uuid4(),'2026-10-21','entrada','simulado','outro',None)]))
    def test_33_lock_order_before_read_messages_and_insert(self):
        _,cur,*_=execute()
        statements=[q for q,_ in cur.calls]
        self.assertLess(statements.index(_SESSION),statements.index(_CASE))
        self.assertLess(statements.index(_CASE),statements.index(_GRANT))
        self.assertLess(statements.index(_LOCK_CONVERSATIONS),statements.index(_MESSAGES))
        self.assertLess(statements.index(_MESSAGES),statements.index(_INSERT))
    def test_34_s1_receives_same_transaction_cursor(self):
        _,cur,s1,*_=execute()
        self.assertIs(s1.calls[0][0],cur)
        self.assertEqual(s1.calls[0][1],Principal(A,S))
        self.assertEqual(s1.calls[0][2:],(SHOP,C,ASSIGN))
    def test_35_insert_contains_only_metadata(self):
        _,cur,*_=execute()
        params=[p for q,p in cur.calls if q==_INSERT][0]
        self.assertEqual(params[0:6],(SHOP,C,A,S,ASSIGN,4))
        self.assertEqual(params[7],_fingerprint(ROWS))
        self.assertEqual(params[8],MSG)
        self.assertEqual(params[9],1)
        self.assertEqual(len(params),10)

    def test_36_s1_team_checked_before_case_lock(self):
        cur=Cursor()
        s1=S1()
        execute(cur,s1=s1)
        self.assertEqual(s1.lock_calls[0][1],Principal(A,S))
        self.assertEqual(len(s1.calls),1)
        self.assertIs(s1.lock_calls[0][0],cur)

    def test_37_missing_s1_lock_method_fails_closed(self):
        class OldS1:
            def check(self,*args):
                return S1Proof.ALLOW
        result,cur,*_=execute(s1=OldS1())
        self.assertIs(result.state,Status.UNAVAILABLE)
        self.assertNotIn(_CASE,[q for q,_ in cur.calls])

    def test_38_s1_lock_denied_before_case(self):
        cur=Cursor()
        result,cur,*_=execute(cursor=cur,s1=S1(S1Proof.DENY))
        self.assertIs(result.state,Status.BLOCKED_S1)
        self.assertNotIn(_CASE,[q for q,_ in cur.calls])

    def test_39_s1_string_lock_unauthorized(self):
        cur=Cursor()
        result,cur,*_=execute(cursor=cur,s1=S1('ALLOW'))
        self.assertIs(result.state,Status.BLOCKED_S1)
        self.assertNotIn(_CASE,[q for q,_ in cur.calls])

    def test_40_messages_locked_during_snapshot_fingerprint(self):
        self.assertIn('for share of m',_MESSAGES.lower())
        self.assertIn('order by m.criada_em,m.id',_MESSAGES.lower())

    def test_41_pghostaddr_cannot_redirect_local_closure(self):
        with patch.dict('os.environ',{'PGHOSTADDR':'203.0.113.3'}):
            with self.assertRaisesRegex(ValueError,'LIBPQ'):
                S0LocalClosureStore(DSN)

    def test_42_pgservicefile_cannot_redirect_local_closure(self):
        with patch.dict('os.environ',{'PGSERVICEFILE':'/tmp/evil'}):
            with self.assertRaisesRegex(ValueError,'LIBPQ'):
                S0LocalClosureStore(DSN)

if __name__ == '__main__':unittest.main()
