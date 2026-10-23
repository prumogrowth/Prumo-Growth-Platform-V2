"""Lab-only S0-F03 metadata port tests; no network, hosted database or F03 model."""
from __future__ import annotations
import unittest
import sys
import types
from unittest.mock import patch
from uuid import UUID
from datetime import datetime, timezone, timedelta
from dataclasses import replace
from backend.s0_cfi01_atomic_commands_local import S0InternalReceiptLocal
from backend.s0_cfi01_f03_receipt_bridge_local import (
    S0F03BoundReceiptLocal, S0F03BridgeState, S0F03BridgeResultLocal,
    S0CFI01F03ReceiptBridgeLocal,
)
from backend.s0_f03_history_manifest_local import (
    HistoryState, HistoricalRead, HistoricalMessageRef,
    S0F03LocalHistoryManifestBridge, S0F03LocalPostgresHistoryReader,
    _HISTORY_SQL, _CONTEXT_SQL,
)

SHOP='11111111-1111-4111-8111-111111111111'
CASE='22222222-2222-4222-8222-222222222222'
OLD='33333333-3333-4333-8333-333333333333'
PERSON='44444444-4444-4444-8444-444444444444'
EVENT='55555555-5555-4555-8555-555555555555'
WATERMARK='66666666-6666-4666-8666-666666666666'
ASSIGN='77777777-7777-4777-8777-777777777777'
CONVERSATION='88888888-8888-4888-8888-888888888888'
OLDMESSAGE='99999999-9999-4999-8999-999999999999'
DT=datetime(2026,10,23,13,0,tzinfo=timezone.utc)

def selection():
    return HistoricalRead(PERSON,DT,(
        HistoricalMessageRef(OLDMESSAGE,OLD,CONVERSATION,DT-timedelta(hours=1),'entrada','simulado',None),
        HistoricalMessageRef(WATERMARK,CASE,CONVERSATION,DT,'saida','simulado',ASSIGN),
    ))

def target():
    receipt=S0InternalReceiptLocal(SHOP,CASE,EVENT,7,ASSIGN,'a'*64,WATERMARK,2)
    return S0F03BoundReceiptLocal(receipt,'idem-00001')

def new_adapter():
    bridge=object.__new__(S0CFI01F03ReceiptBridgeLocal)
    reader=object.__new__(S0F03LocalPostgresHistoryReader)
    return S0F03LocalHistoryManifestBridge(bridge,reader)

class Tests(unittest.TestCase):
    def execute(self, data=None, first=None, second=None, exc=None):
        binding=target()
        ok=S0F03BridgeResultLocal(S0F03BridgeState.VERIFIED_CONTRACT_PENDING,binding)
        with patch.object(S0CFI01F03ReceiptBridgeLocal,'recheck',side_effect=[first or ok,second or ok]) as check,\
             patch.object(S0F03LocalPostgresHistoryReader,'load',side_effect=exc if exc else None,return_value=selection() if data is None else data) as load:
            value=new_adapter().inspect('Bearer SYNTHETIC',binding)
        return value,check.call_count,load.call_count

    def test_01_multicase_source_metadata_only(self):
        result,checks,reads=self.execute()
        self.assertEqual(result.state,HistoryState.REVIEW_ONLY_NOT_FROZEN)
        self.assertEqual((result.count,result.case_count),(2,2))
        self.assertEqual((checks,reads),(2,1))
        self.assertEqual(len(result.metadata_sha256),64)
        self.assertFalse(hasattr(result,'customer_text'))
        self.assertFalse(hasattr(result,'authorized_for_model'))

    def test_02_first_recheck_denied_no_db_read(self):
        bad=S0F03BridgeResultLocal(S0F03BridgeState.DENIED)
        result,checks,reads=self.execute(first=bad)
        self.assertEqual(result.state,HistoryState.DENIED)
        self.assertEqual((checks,reads),(1,0))

    def test_03_first_recheck_stale(self):
        result,checks,reads=self.execute(first=S0F03BridgeResultLocal(S0F03BridgeState.STALE))
        self.assertEqual(result.state,HistoryState.STALE)
        self.assertEqual(reads,0)

    def test_04_second_recheck_revoked(self):
        result,checks,reads=self.execute(second=S0F03BridgeResultLocal(S0F03BridgeState.DENIED))
        self.assertEqual(result.state,HistoryState.DENIED)
        self.assertEqual((checks,reads),(2,1))

    def test_05_second_recheck_stale(self):
        result,_,_=self.execute(second=S0F03BridgeResultLocal(S0F03BridgeState.STALE))
        self.assertEqual(result.state,HistoryState.STALE)

    def test_06_reader_error_fails_closed(self):
        result,_,_=self.execute(exc=RuntimeError('offline unavailable'))
        self.assertEqual(result.state,HistoryState.UNAVAILABLE)

    def test_07_unavailable_reader_result(self):
        result,_,_=self.execute(data=False)
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_08_no_rows_refuses_complete(self):
        result,_,_=self.execute(data=HistoricalRead(PERSON,DT,()))
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_09_wrong_lead_type(self):
        result,_,_=self.execute(data=HistoricalRead('browser-claimed-person',DT,selection().rows))
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_10_future_row_refuses(self):
        rows=selection().rows
        result,_,_=self.execute(data=HistoricalRead(PERSON,DT,(rows[0],replace(rows[1],created_at=DT+timedelta(seconds=1)))))
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_11_other_shop_not_in_sql(self):
        self.assertIn('m.concessionaria_id=%s::uuid',_HISTORY_SQL)
        self.assertIn('v.lead_id=%s::uuid',_HISTORY_SQL)
        self.assertIn('e.concessionaria_id=%s::uuid',_CONTEXT_SQL)
        self.assertNotIn('telefone_cliente_normalizado',_HISTORY_SQL)

    def test_12_cutoff_from_recorded_event_not_ui(self):
        self.assertIn('e.registrado_em',_CONTEXT_SQL)
        self.assertIn('m.criada_em<=%s::timestamptz',_HISTORY_SQL)

    def test_13_watermark_not_present(self):
        data=HistoricalRead(PERSON,DT,selection().rows[:1])
        result,_,_=self.execute(data=data)
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_14_watermark_from_other_case_invalid(self):
        rows=list(selection().rows)
        rows[1]=replace(rows[1],case_ref=OLD)
        result,_,_=self.execute(data=HistoricalRead(PERSON,DT,tuple(rows)))
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_15_duplicate_message_ref_rejected(self):
        rows=list(selection().rows)
        rows[0]=replace(rows[0],message_ref=WATERMARK)
        result,_,_=self.execute(data=HistoricalRead(PERSON,DT,tuple(rows)))
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_16_out_of_order_rows_rejected(self):
        data=selection()
        result,_,_=self.execute(data=replace(data,rows=tuple(reversed(data.rows))))
        self.assertEqual(result.state,HistoryState.HISTORY_INCOMPLETE)

    def test_17_reader_strict_local_only(self):
        with self.assertRaises(ValueError):
            S0F03LocalPostgresHistoryReader('postgresql://postgres:pw@prod.invalid/customers')

    def test_18_no_unauthorized_reader_injection(self):
        with self.assertRaises(TypeError):
            S0F03LocalHistoryManifestBridge(object(),object())

    def test_19_no_untrusted_reader_injection(self):
        with self.assertRaises(TypeError):
            S0F03LocalHistoryManifestBridge(object.__new__(S0CFI01F03ReceiptBridgeLocal),object())

    def test_20_scope_immutable_hash_deterministic(self):
        a,_,_=self.execute()
        b,_,_=self.execute()
        self.assertEqual(a.metadata_sha256,b.metadata_sha256)


    def test_21_reader_queries_authorized_local_context_and_history(self):
        receipt=target().receipt
        queries=[]
        class Cursor:
            def __init__(self):self.n=0
            def execute(self,sql,args=None):queries.append((sql,args))
            def fetchall(self):return [(UUID(PERSON),DT)]
            def fetchmany(self,count):
                self.n=count
                return [
                    (UUID(OLDMESSAGE),UUID(OLD),UUID(CONVERSATION),DT-timedelta(hours=1),'entrada','simulado',None),
                    (UUID(WATERMARK),UUID(CASE),UUID(CONVERSATION),DT,'saida','simulado',UUID(ASSIGN)),
                ]
            def __enter__(self):return self
            def __exit__(self,*args):return False
        class Connection:
            def cursor(self):return Cursor()
            def __enter__(self):return self
            def __exit__(self,*args):return False
        fake=types.SimpleNamespace(connect=lambda _dsn,**_kwargs:Connection())
        with patch.dict(sys.modules,{'psycopg':fake}):
            reader=S0F03LocalPostgresHistoryReader('postgresql://postgres:pw@localhost/prumo_s0_test_history')
            answer=reader.load(receipt)
        self.assertEqual(answer.lead_ref,PERSON)
        self.assertEqual(len(answer.rows),2)
        self.assertEqual(answer.rows[0].case_ref,OLD)
        self.assertEqual(queries[1][1][0],EVENT)
        self.assertEqual(queries[1][1][1],SHOP)
        self.assertEqual(queries[2][1],(SHOP,UUID(PERSON),DT))
        self.assertIn('repeatable read read only',queries[0][0])
        self.assertNotIn('conteudo_sintetico',queries[2][0])

    def test_22_reader_cannot_inherit_s0_capture_writer(self):
        reader=S0F03LocalPostgresHistoryReader('postgresql://postgres:pw@localhost/prumo_s0_test_history')
        self.assertFalse(hasattr(reader,'capture'))

    def test_23_reader_missing_closure_returns_none(self):
        class Cursor:
            def execute(self,*args):pass
            def fetchall(self):return []
            def __enter__(self):return self
            def __exit__(self,*args):return False
        class Connection:
            def cursor(self):return Cursor()
            def __enter__(self):return self
            def __exit__(self,*args):return False
        with patch.dict(sys.modules,{'psycopg':types.SimpleNamespace(connect=lambda *a,**k:Connection())}):
            reader=S0F03LocalPostgresHistoryReader('postgresql://postgres:pw@localhost/prumo_s0_test_history')
            self.assertIsNone(reader.load(target().receipt))

    def test_24_only_read_statements_in_history_reader(self):
        self.assertIn('select m.id',_HISTORY_SQL)
        self.assertIn('select h.lead_id',_CONTEXT_SQL)
        self.assertNotIn('insert into',_HISTORY_SQL.lower())
        self.assertNotIn('update public',_HISTORY_SQL.lower())

if __name__=='__main__': unittest.main()
