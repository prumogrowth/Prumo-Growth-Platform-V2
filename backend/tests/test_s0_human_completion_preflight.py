"""Tests new S0-side preflight without GoTrue network, SQL DB or secrets."""
import sys
import types
import uuid
import unittest
from dataclasses import replace
from unittest.mock import patch

from backend.identity_boundary import Principal, Denied, IdentityUnavailable
from backend.s0_human_completion_preflight import (
    CheckStatus as S, CasePreflightRequest, PsycopgLocalCaseInspection,
    preflight_human_closure,
)

ACTOR = uuid.UUID('11111111-1111-4111-8111-111111111111')
SESSION = uuid.UUID('22222222-2222-4222-8222-222222222222')
CASE = uuid.UUID('33333333-3333-4333-8333-333333333333')
STORE = uuid.UUID('44444444-4444-4444-8444-444444444444')

class Identity:
    def __init__(self, result=None, error=None):
        self.result = Principal(ACTOR,SESSION) if result is None else result
        self.error=error
        self.calls=[]
    def verify(self, bearer):
        self.calls.append(bearer)
        if self.error: raise self.error
        return self.result

class Inspection:
    def __init__(self, status=S.S0_READ_CHECKS_PASSED_S1_REQUIRED, error=None):
        self.status=status
        self.error=error
        self.calls=[]
    def check(self,principal,case,version):
        self.calls.append((principal,case,version))
        if self.error: raise self.error
        return self.status

def call(req=None, identity=None, inspection=None):
    req=req if req is not None else CasePreflightRequest(str(CASE),7)
    identity=identity if identity is not None else Identity()
    inspection=inspection if inspection is not None else Inspection()
    return preflight_human_closure('Bearer MOCK-SANDBOX',req,identity=identity,inspection=inspection)

class FakeCursor:
    def __init__(self,rows):
        self.rows=list(rows)
        self.executed=[]
    def execute(self,query,params):
        self.executed.append((query,params))
    def fetchone(self):
        return self.rows.pop(0)
    def __enter__(self): return self
    def __exit__(self,*_): pass
class FakeCon:
    def __init__(self,cur):self.cur=cur
    def cursor(self):return self.cur
    def __enter__(self):return self
    def __exit__(self,*_):pass

def dbcheck(rows):
    cur=FakeCursor(rows)
    adapter=PsycopgLocalCaseInspection('postgresql://postgres:xxx@localhost/prumo_s0_test_ci')
    with patch.dict(sys.modules,{'psycopg':types.SimpleNamespace(connect=lambda *_a,**_k:FakeCon(cur))}):
        result=adapter.check(Principal(ACTOR,SESSION), CASE, 7)
    return result,cur

class Cases(unittest.TestCase):
    def test_01_authorized_s0_tables_do_not_grant_closure(self):
        self.assertIs(call().status,S.S0_READ_CHECKS_PASSED_S1_REQUIRED)
    def test_02_no_browser_actor_or_store(self):
        self.assertEqual(set(CasePreflightRequest.__dataclass_fields__),{'case_ref','expected_cycle_version'})
    def test_03_invalid_case_denies_before_identity(self):
        i=Identity();db=Inspection()
        self.assertIs(call(CasePreflightRequest('bad',7),i,db).status,S.DENIED)
        self.assertEqual(i.calls,[]);self.assertEqual(db.calls,[])
    def test_04_boolean_version_denied(self):
        self.assertIs(call(CasePreflightRequest(str(CASE),True)).status,S.DENIED)
    def test_05_zero_version_denied(self):
        self.assertIs(call(CasePreflightRequest(str(CASE),0)).status,S.DENIED)
    def test_06_oversized_version_denied(self):
        self.assertIs(call(CasePreflightRequest(str(CASE),2**63)).status,S.DENIED)
    def test_07_extra_uuid_whitespace_denied(self):
        self.assertIs(call(CasePreflightRequest(' '+str(CASE),7)).status,S.DENIED)
    def test_08_identity_called_with_bearer(self):
        i=Identity(); call(identity=i);self.assertEqual(i.calls,['Bearer MOCK-SANDBOX'])
    def test_09_actor_never_from_browser(self):
        db=Inspection();call(inspection=db);self.assertEqual(db.calls[0][0],Principal(ACTOR,SESSION))
    def test_10_denied_identity_blocks_storage(self):
        db=Inspection(); r=call(identity=Identity(error=Denied()),inspection=db)
        self.assertIs(r.status,S.DENIED);self.assertEqual(db.calls,[])
    def test_11_unavailable_identity_blocks_storage(self):
        db=Inspection();r=call(identity=Identity(error=IdentityUnavailable()),inspection=db)
        self.assertIs(r.status,S.UNAVAILABLE);self.assertEqual(db.calls,[])
    def test_12_bad_identity_shape_denies(self):
        self.assertIs(call(identity=Identity(result='spoof')).status,S.DENIED)
    def test_13_expired_case_version(self):
        self.assertIs(call(inspection=Inspection(status=S.STALE)).status,S.STALE)
    def test_14_denied_assignment(self):
        self.assertIs(call(inspection=Inspection(status=S.DENIED)).status,S.DENIED)
    def test_15_arbitrary_storage_reply_fails_closed(self):
        self.assertIs(call(inspection=Inspection(status='AUTHORIZED')).status,S.DENIED)
    def test_16a_string_impersonating_enum_is_denied(self):
        self.assertIs(call(inspection=Inspection(status="S0_READ_CHECKS_PASSED_S1_REQUIRED")).status,S.DENIED)
    def test_16_storage_error_unavailable(self):
        self.assertIs(call(inspection=Inspection(error=RuntimeError('db down'))).status,S.UNAVAILABLE)
    def test_17_pg_remote_dsn_rejected(self):
        with self.assertRaises(ValueError):PsycopgLocalCaseInspection('postgres://postgres:pass@production.example.com/prod')
    def test_18_pg_nonpostgres_user_rejected(self):
        with self.assertRaises(ValueError):PsycopgLocalCaseInspection('postgresql://api:secret@localhost/prumo_s0_test_ci')
    def test_19_pg_arbitrary_db_rejected(self):
        with self.assertRaises(ValueError):PsycopgLocalCaseInspection('postgresql://postgres:secret@localhost/customerdb')
    def test_20_pg_session_missing_denied(self):
        result,cur=dbcheck([None]);self.assertIs(result,S.DENIED);self.assertEqual(len(cur.executed),1)
    def test_21_pg_case_missing_denied(self):
        result,cur=dbcheck([(1,),None]);self.assertIs(result,S.DENIED);self.assertEqual(len(cur.executed),2)
    def test_22_pg_grant_missing_denied(self):
        result,_=dbcheck([(1,),(STORE,7,'em atendimento pelo operador'),None]);self.assertIs(result,S.DENIED)
    def test_23_pg_cross_case_or_unauthorized_denied(self):
        result,cur=dbcheck([(1,),None]);self.assertIs(result,S.DENIED)
        self.assertEqual(cur.executed[1][1],(ACTOR,CASE))
    def test_24_pg_stale_cycle_denied_as_stale(self):
        result,_=dbcheck([(1,),(STORE,8,'em atendimento pelo operador'),(1,)])
        self.assertIs(result,S.STALE)
    def test_25_pg_sold_rejected(self):
        result,_=dbcheck([(1,),(STORE,7,'vendido'),(1,)])
        self.assertIs(result,S.DENIED)
    def test_26_pg_sent_to_bank_not_auto_reopen(self):
        result,_=dbcheck([(1,),(STORE,7,'cadastro enviado ao banco'),(1,)])
        self.assertIs(result,S.DENIED)
    def test_27_pg_current_human_case_prelim_only(self):
        result,_=dbcheck([(1,),(STORE,7,'em atendimento pelo operador'),(1,)])
        self.assertIs(result,S.S0_READ_CHECKS_PASSED_S1_REQUIRED)
    def test_28_pg_sent_to_operator_prelim_only(self):
        result,_=dbcheck([(1,),(STORE,7,'cadastro enviado ao operador'),(1,)])
        self.assertIs(result,S.S0_READ_CHECKS_PASSED_S1_REQUIRED)
    def test_29_pg_queries_join_real_case_store_and_assignment(self):
        result,cur=dbcheck([(1,),(STORE,7,'em atendimento pelo operador'),(1,)])
        self.assertIn('a.operador_id=%s::uuid',cur.executed[1][0])
        self.assertIn('a.encerrada_em is null',cur.executed[1][0])
        self.assertIn('h.concessionaria_id',cur.executed[1][0])
    def test_30_pg_grant_is_store_scoped(self):
        result,cur=dbcheck([(1,),(STORE,7,'em atendimento pelo operador'),(1,)])
        self.assertEqual(cur.executed[2][1],(ACTOR,STORE))
        self.assertIn('v.valido_ate',cur.executed[2][0])
    def test_31_pg_session_bound_to_identity(self):
        result,cur=dbcheck([(1,),(STORE,7,'em atendimento pelo operador'),(1,)])
        self.assertEqual(cur.executed[0][1],(SESSION,ACTOR))
        self.assertIn('for key share',cur.executed[0][0].lower())
    def test_32_no_write_statements_in_inspection(self):
        for query in (PsycopgLocalCaseInspection._CASE,PsycopgLocalCaseInspection._GRANT,PsycopgLocalCaseInspection._SESSION):
            self.assertTrue(query.strip().lower().startswith('select '))
            self.assertNotIn('update ',query.lower())
            self.assertNotIn('insert ',query.lower())

if __name__=='__main__': unittest.main()
