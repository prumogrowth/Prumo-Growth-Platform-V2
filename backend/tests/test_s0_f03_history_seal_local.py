"""S0 F03 sealing contract, synthetic fixture only; PG driver mocked, no network."""
from __future__ import annotations
import json
import os
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import UUID
from dataclasses import replace
from types import SimpleNamespace
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_f03_history_manifest_local import (
    S0F03LocalHistoryManifestBridge, S0F03LocalPostgresHistoryReader,
    HistoricalRead, HistoricalMessageRef, HistoryResult, HistoryState,
)
from backend.s0_f03_history_seal_local import (
    _snapshot, _INSERT, _SELECT, S0F03LocalHistorySealingBridge,
    S0F03LocalManifestSealStore, SealState,
)
SHOP='11111111-1111-4111-8111-111111111111'
CASE='22222222-2222-4222-8222-222222222222'
OLD='33333333-3333-4333-8333-333333333333'
PERSON='44444444-4444-4444-8444-444444444444'
EVENT='55555555-5555-4555-8555-555555555555'
WATERMARK='66666666-6666-4666-8666-666666666666'
ASSIGN='77777777-7777-4777-8777-777777777777'
CONV='88888888-8888-4888-8888-888888888888'
OLDMSG='99999999-9999-4999-8999-999999999999'
DT=datetime(2026,10,23,13,0,tzinfo=timezone.utc)
DSN='postgresql://postgres:pw@localhost/prumo_s0_test_f03seal'

def fixture():
    return HistoricalRead(PERSON,DT,(
        HistoricalMessageRef(OLDMSG,OLD,CONV,DT-timedelta(hours=1),'entrada','simulado',None),
        HistoricalMessageRef(WATERMARK,CASE,CONV,DT,'saida','simulado',ASSIGN)))

def binding():
    # The actual S0 binding and receipt classes are used in a real repo checkout.
    receipt=SimpleNamespace(store_ref=SHOP,case_ref=CASE,closure_event_ref=EVENT,
        message_watermark=WATERMARK,expected_cycle_version=7,snapshot_sha256='a'*64)
    return S0F03BoundReceiptLocal(receipt,'request-local-01')

def prepared():
    history=object.__new__(S0F03LocalHistoryManifestBridge)
    reader=object.__new__(S0F03LocalPostgresHistoryReader)
    store=object.__new__(S0F03LocalManifestSealStore)
    reader._dsn=store._dsn=DSN
    history._reader=reader
    gateway=S0F03LocalHistorySealingBridge(history,reader,store)
    snap=_snapshot(fixture())
    valid=HistoryResult(HistoryState.REVIEW_ONLY_NOT_FROZEN,snap[1],snap[2],snap[0])
    return gateway,history,reader,store,valid

def persisted_row(data=fixture()):
    s=_snapshot(data)
    return (UUID(data.lead_ref),7,'a'*64,UUID(WATERMARK),data.closure_at,
            s[1],s[2],s[0],json.loads(s[3]))

class Tests(unittest.TestCase):
    def test_01_canonical_hash_matches_prior_bridge_format(self):
        s=_snapshot(fixture())
        self.assertEqual(s[1:3],(2,2))
        self.assertEqual(len(s[0]),64)
        self.assertEqual(json.loads(s[3])[0][1],OLD)
    def test_02_empty_history_cannot_be_sealed(self):
        self.assertIsNone(_snapshot(HistoricalRead(PERSON,DT,())))
    def test_03_future_message_fails(self):
        a=fixture(); b=replace(a.rows[1],created_at=DT+timedelta(seconds=1))
        self.assertIsNone(_snapshot(replace(a,rows=(a.rows[0],b))))
    def test_04_duplicate_message_id_fails(self):
        a=fixture();b=replace(a.rows[1],message_ref=OLDMSG)
        self.assertIsNone(_snapshot(replace(a,rows=(a.rows[0],b))))
    def test_05_out_of_order_history_fails(self):
        a=fixture();self.assertIsNone(_snapshot(replace(a,rows=a.rows[::-1])))
    def test_06_metadata_never_contains_text(self):
        self.assertNotIn('conteudo_sintetico',_snapshot(fixture())[3])
        self.assertNotIn('cliente',_snapshot(fixture())[3])
    def test_07_only_local_disposable_pg_dsn(self):
        with self.assertRaises(ValueError):
            S0F03LocalManifestSealStore('postgresql://postgres:pw@prod.invalid/customer')
    def test_08_no_fake_adapter_injection(self):
        g,h,r,s,v=prepared()
        with self.assertRaises(TypeError):S0F03LocalHistorySealingBridge(object(),r,s)
        with self.assertRaises(TypeError):S0F03LocalHistorySealingBridge(h,object(),s)
        other=object.__new__(S0F03LocalPostgresHistoryReader);other._dsn=DSN
        with self.assertRaises(TypeError):S0F03LocalHistorySealingBridge(h,other,s)
    def test_09_mismatched_db_rejected(self):
        g,h,r,s,v=prepared();s._dsn=DSN+'_other'
        with self.assertRaises(TypeError):S0F03LocalHistorySealingBridge(h,r,s)
    def test_10_binding_input_is_required(self):
        g,h,r,s,v=prepared()
        self.assertEqual(g.seal('token',{'id':EVENT}).state,SealState.DENIED)
        self.assertEqual(g.verify('token',{'id':EVENT}).state,SealState.DENIED)
    def test_11_seal_checks_history_three_times_and_captures_once(self):
        g,h,r,s,v=prepared()
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v) as chk,\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()) as load,\
             patch.object(S0F03LocalManifestSealStore,'capture',return_value=SealState.SEALED_REVIEW_ONLY) as save:
            state=g.seal('Bearer FAKE',binding()).state
        self.assertEqual(state,SealState.SEALED_REVIEW_ONLY)
        self.assertEqual((chk.call_count,load.call_count,save.call_count),(3,1,1))
    def test_12_explicit_recheck_denial_does_not_read(self):
        g,h,r,s,v=prepared()
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=HistoryResult(HistoryState.DENIED)) as chk,\
             patch.object(S0F03LocalPostgresHistoryReader,'load') as load:
            self.assertEqual(g.seal('x',binding()).state,SealState.DENIED)
        self.assertEqual(chk.call_count,1);load.assert_not_called()
    def test_13_unchanged_request_is_idempotent(self):
        g,h,r,s,v=prepared()
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'capture',return_value=SealState.ALREADY_SEALED_REVIEW_ONLY):
            self.assertEqual(g.seal('x',binding()).state,SealState.ALREADY_SEALED_REVIEW_ONLY)
    def test_14_selection_drift_between_read_and_capture(self):
        g,h,r,s,v=prepared(); wrong=replace(fixture(),rows=(fixture().rows[1],))
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=wrong),\
             patch.object(S0F03LocalManifestSealStore,'capture') as write:
            self.assertEqual(g.seal('x',binding()).state,SealState.STALE)
        write.assert_not_called()
    def test_15_recheck_drift_before_insert_blocks(self):
        g,h,r,s,v=prepared();other=HistoryResult(HistoryState.REVIEW_ONLY_NOT_FROZEN,99,3,'b'*64)
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',side_effect=[v,other]),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'capture') as write:
            self.assertEqual(g.seal('x',binding()).state,SealState.STALE)
        write.assert_not_called()
    def test_16_revocation_after_insert_stays_closed(self):
        g,h,r,s,v=prepared()
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',side_effect=[v,v,HistoryResult(HistoryState.DENIED)]),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'capture',return_value=SealState.SEALED_REVIEW_ONLY):
            self.assertEqual(g.seal('x',binding()).state,SealState.STALE)
    def test_17_reader_exception_is_not_leaked(self):
        g,h,r,s,v=prepared()
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',side_effect=RuntimeError('private SQL')):
            self.assertEqual(g.seal('x',binding()).state,SealState.UNAVAILABLE)
    def test_18_watermark_not_selected_rejects(self):
        g,h,r,s,v=prepared()
        case=replace(fixture(),rows=(fixture().rows[0],))
        vs=_snapshot(case);status=HistoryResult(HistoryState.REVIEW_ONLY_NOT_FROZEN,vs[1],vs[2],vs[0])
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=status),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=case),\
             patch.object(S0F03LocalManifestSealStore,'capture') as write:
            self.assertEqual(g.seal('x',binding()).state,SealState.HISTORY_INCOMPLETE)
        write.assert_not_called()
    def test_19_verify_matching_ledger_still_review_only(self):
        g,h,r,s,v=prepared()
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v) as chk,\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'lookup',return_value=persisted_row()):
            self.assertEqual(g.verify('x',binding()).state,SealState.MATCHES_LIVE_REVIEW_ONLY)
        self.assertEqual(chk.call_count,2)
    def test_20_verify_late_insertion_requires_new_review(self):
        g,h,r,s,v=prepared();more=HistoryResult(HistoryState.REVIEW_ONLY_NOT_FROZEN,3,2,'b'*64)
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=more),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'lookup',return_value=persisted_row()):
            self.assertEqual(g.verify('x',binding()).state,SealState.STALE)
    def test_21_verify_mismatched_person_rejects(self):
        g,h,r,s,v=prepared();row=list(persisted_row());row[0]=UUID(OLD)
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'lookup',return_value=tuple(row)):
            self.assertEqual(g.verify('x',binding()).state,SealState.STALE)
    def test_22_verify_mismatched_metadata_json_rejects(self):
        g,h,r,s,v=prepared();row=list(persisted_row());row[-1]=[]
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'lookup',return_value=tuple(row)):
            self.assertEqual(g.verify('x',binding()).state,SealState.STALE)
    def test_23_verify_missing_seal(self):
        g,h,r,s,v=prepared()
        with patch.object(S0F03LocalHistoryManifestBridge,'inspect',return_value=v),\
             patch.object(S0F03LocalPostgresHistoryReader,'load',return_value=fixture()),\
             patch.object(S0F03LocalManifestSealStore,'lookup',return_value=None):
            self.assertEqual(g.verify('x',binding()).state,SealState.HISTORY_INCOMPLETE)
    def test_24_no_public_F03_or_model_grant_states(self):
        self.assertNotIn('F03_READY',SealState.__members__)
        self.assertNotIn('APPLIED',SealState.__members__)
        self.assertNotIn('BANK_SENT',SealState.__members__)
    def test_25_reject_history_over_cap(self):
        r=fixture().rows[0]
        giant=HistoricalRead(PERSON,DT,(r,)*10001)
        self.assertIsNone(_snapshot(giant))
    def test_26_insert_is_idempotent_and_parameterized(self):
        self.assertIn('on conflict (concessionaria_id,evento_fechamento_id) do nothing',_INSERT)
        self.assertIn('%s::uuid',_INSERT)
        self.assertNotIn('conteudo_sintetico',_INSERT)
    def test_27_select_scoped_to_store_closure_and_case(self):
        self.assertIn('concessionaria_id=%s::uuid',_SELECT)
        self.assertIn('evento_fechamento_id=%s::uuid',_SELECT)
        self.assertIn('caso_id=%s::uuid',_SELECT)
    def test_28_store_capture_uses_mocked_local_pg_and_retains_metadata_only(self):
        b=binding();data=fixture();snap=_snapshot(data);seen=[]
        class Cur:
            rowcount=1
            def execute(self,sql,args):seen.append((sql,args))
            def fetchone(self):return persisted_row()
            def __enter__(self):return self
            def __exit__(self,*a):return False
        class Conn:
            def cursor(self):return Cur()
            def __enter__(self):return self
            def __exit__(self,*a):return False
        store=object.__new__(S0F03LocalManifestSealStore);store._dsn=DSN
        with patch.dict(sys.modules,{'psycopg':types.SimpleNamespace(connect=lambda *a,**k:Conn())}):
            outcome=store.capture(b,data,snap)
        self.assertEqual(outcome,SealState.SEALED_REVIEW_ONLY)
        self.assertEqual(len(seen),2)
        self.assertEqual(seen[0][1][0:4],(SHOP,EVENT,CASE,PERSON))
        self.assertEqual(seen[1][1],(SHOP,EVENT,CASE))
        self.assertNotIn('customer_text',json.dumps(seen,default=str))
    def test_29_store_capture_conflicting_previous_digest_rejects(self):
        b=binding();data=fixture();snap=_snapshot(data)
        bad=list(persisted_row());bad[-2]='b'*64
        class Cur:
            rowcount=0
            def execute(self,*a):pass
            def fetchone(self):return tuple(bad)
            def __enter__(self):return self
            def __exit__(self,*a):return False
        class Conn:
            def cursor(self):return Cur()
            def __enter__(self):return self
            def __exit__(self,*a):return False
        store=object.__new__(S0F03LocalManifestSealStore);store._dsn=DSN
        with patch.dict(sys.modules,{'psycopg':types.SimpleNamespace(connect=lambda *a,**k:Conn())}):
            self.assertEqual(store.capture(b,data,snap),SealState.STALE)
    def test_30_store_capture_idempotent_same_digest(self):
        b=binding();data=fixture();snap=_snapshot(data)
        class Cur:
            rowcount=0
            def execute(self,*a):pass
            def fetchone(self):return persisted_row()
            def __enter__(self):return self
            def __exit__(self,*a):return False
        class Conn:
            def cursor(self):return Cur()
            def __enter__(self):return self
            def __exit__(self,*a):return False
        store=object.__new__(S0F03LocalManifestSealStore);store._dsn=DSN
        with patch.dict(sys.modules,{'psycopg':types.SimpleNamespace(connect=lambda *a,**k:Conn())}):
            self.assertEqual(store.capture(b,data,snap),SealState.ALREADY_SEALED_REVIEW_ONLY)
    def test_31_commit_requires_no_external_API_or_secret(self):
        source=__import__('inspect').getsource(S0F03LocalHistorySealingBridge)
        self.assertNotIn('openai',source.lower())
        self.assertNotIn('requests.post',source)
        self.assertNotIn('subprocess',source)

if __name__=='__main__':unittest.main()
