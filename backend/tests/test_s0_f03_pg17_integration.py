"""Physical F03 metadata seal tests. ONLY disposable S0 PostgreSQL 17.

No hosted Supabase, business write, AI call, or claim of complete history.
S0's existing authenticated/signed bridge has its separate PG17 tests.
"""
from __future__ import annotations

import os
import unittest
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Principal
from backend.s0_human_closure_event_local import (
    ClosureRequest, ClosureState, S0LocalClosureStore,
    capture_human_closure_local,
)
from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority
from backend.s0_cfi01_atomic_commands_local import S0InternalReceiptLocal
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_f03_history_manifest_local import S0F03LocalPostgresHistoryReader
from backend.s0_f03_history_seal_local import (
    S0F03LocalManifestSealStore, SealState, _snapshot, _INSERT,
)

DB = os.environ.get('PRUMO_TEST_DATABASE_URL', '')
URI = urlsplit(DB)
DISPOSABLE = (URI.scheme in ('postgresql', 'postgres')
              and URI.hostname in ('127.0.0.1', 'localhost', '::1')
              and URI.path == '/prumo_s0_test_cfi01'
              and not URI.query and not URI.fragment)


class LocalIdentity:
    def __init__(self, actor, session):
        self.identity = Principal(actor, session)

    def verify(self, _authorization):
        return self.identity


@unittest.skipUnless(DISPOSABLE, 'requires disposable local PG17 S0 database')
class PostgresF03ManifestIntegration(unittest.TestCase):
    def setUp(self):
        import psycopg
        self.pg = psycopg
        self.actor, self.session = uuid.uuid4(), uuid.uuid4()
        self.shop, self.lead, self.cycle = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        self.case, self.old_case = uuid.uuid4(), uuid.uuid4()
        self.assignment = uuid.uuid4()
        self.channel = uuid.uuid4()
        self.conversation, self.old_conversation = uuid.uuid4(), uuid.uuid4()
        self.message, self.old_message = uuid.uuid4(), uuid.uuid4()
        with psycopg.connect(DB) as con:
            with con.cursor() as cur:
                cur.execute('select current_setting(\'server_version_num\')::integer')
                major = cur.fetchone()[0]
                if not 170000 <= major < 180000:
                    self.fail('physical F03 tests require PostgreSQL 17')
                cur.execute('insert into auth.users(id) values (%s)', (self.actor,))
                cur.execute('insert into public.atores(id) values (%s)', (self.actor,))
                cur.execute('insert into auth.sessions(id,user_id) values (%s,%s)',
                            (self.session, self.actor))
                cur.execute('insert into public.concessionarias(id,nome_operacional) '
                            "values (%s,'F03 LOCAL FIXTURE')", (self.shop,))
                cur.execute('insert into public.vinculos_papel_escopo('
                            'ator_id,concessionaria_id,papel) '
                            "values (%s,%s,'operador')", (self.actor,self.shop))
                cur.execute('insert into public.leads_loja('
                            'id,concessionaria_id,telefone_cliente_normalizado) '
                            "values (%s,%s,'+5511988887777')", (self.lead,self.shop))
                cur.execute('insert into public.ciclos_comerciais('
                            'id,concessionaria_id,lead_id,status_comercial,versao_registro) '
                            "values (%s,%s,%s,'em atendimento pelo operador',1)",
                            (self.cycle,self.shop,self.lead))
                for case in (self.case, self.old_case):
                    cur.execute('insert into public.casos_humanos('
                                'id,concessionaria_id,lead_id,ciclo_id) '
                                'values (%s,%s,%s,%s)',
                                (case,self.shop,self.lead,self.cycle))
                cur.execute('insert into public.atribuicoes_humanas('
                            'id,concessionaria_id,caso_id,operador_id) '
                            'values (%s,%s,%s,%s)',
                            (self.assignment,self.shop,self.case,self.actor))
                cur.execute('insert into public.equipe_prumo_s1(ator_id,estado) '
                            "values (%s,'ativo')", (self.actor,))
                cur.execute('insert into public.canais_loja('
                            'id,concessionaria_id,identificador_emissor) '
                            'values (%s,%s,%s)',
                            (self.channel,self.shop,str(self.channel)))
                for conversation, case in ((self.conversation,self.case),
                                           (self.old_conversation,self.old_case)):
                    cur.execute('insert into public.conversas('
                                'id,concessionaria_id,lead_id,canal_id,caso_id) '
                                'values (%s,%s,%s,%s,%s)',
                                (conversation,self.shop,self.lead,self.channel,case))
                self._message(cur,self.old_message,self.old_conversation,self.old_case,
                              older=True)
                self._message(cur,self.message,self.conversation,self.case)
        self.s0=S0LocalClosureStore(DB)
        self.reader=S0F03LocalPostgresHistoryReader(DB)
        self.seal=S0F03LocalManifestSealStore(DB)
        closed=capture_human_closure_local(
            'Bearer FIXTURE', ClosureRequest(str(self.case),1,'f03-pg17-closure'),
            identity=LocalIdentity(self.actor,self.session),
            store=self.s0,s1=S0S1LocalTeamAuthority())
        self.assertIs(closed.state,ClosureState.CAPTURED_LOCAL_ONLY)
        self.event=uuid.UUID(closed.closure_event_ref)
        with psycopg.connect(DB) as con:
            rec=con.execute('select snapshot_sha256, ultima_mensagem_id, quantidade_mensagens '
                            'from prumo_private.cfi01_human_closure_events_local '
                            'where id=%s', (self.event,)).fetchone()
        self.assertEqual(rec[2],1)
        self.receipt=S0InternalReceiptLocal(
            str(self.shop),str(self.case),str(self.event),1,str(self.assignment),
            rec[0],str(rec[1]),rec[2])
        self.binding=S0F03BoundReceiptLocal(self.receipt,'f03-pg17-closure')

    def _message(self, cur, ident, conversation, case, *, older=False):
        cur.execute('insert into public.mensagens('
                    'id,concessionaria_id,conversa_id,canal_id,caso_id,'
                    'direcao,origem,conteudo_sintetico,id_externo,criada_em) '
                    "values (%s,%s,%s,%s,%s,'entrada','simulado','somente fixture',%s,"
                    "case when %s then statement_timestamp()-interval '1 day' "
                    'else statement_timestamp() end)',
                    (ident,self.shop,conversation,self.channel,case,str(ident),older))

    def _read(self):
        value=self.reader.load(self.receipt)
        self.assertIsNotNone(value)
        return value

    def _save(self):
        data=self._read()
        fingerprint=_snapshot(data)
        self.assertIsNotNone(fingerprint)
        return self.seal.capture(self.binding,data,fingerprint)

    def test_01_physical_reader_selects_same_lead_two_cases(self):
        data=self._read()
        self.assertEqual(data.lead_ref,str(self.lead))
        self.assertEqual(len(data.rows),2)
        self.assertEqual(set(row.case_ref for row in data.rows),
                         {str(self.old_case),str(self.case)})
        self.assertNotIn('customer_text',data.__dataclass_fields__)

    def test_02_store_persists_metadata_only(self):
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        row=self.seal.lookup(self.binding)
        self.assertIsNotNone(row)
        self.assertEqual((row[5],row[6]),(2,2))
        self.assertEqual(len(row[7]),64)
        self.assertEqual(len(row[8]),2)
        self.assertFalse(any('somente fixture' in str(x) for x in row[8]))

    def test_03_idempotent_replay_preserves_one_row(self):
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        self.assertIs(self._save(),SealState.ALREADY_SEALED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from prumo_private.cfi01_f03_history_seals_local '
                              'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(count,1)

    def test_04_retrodated_message_in_old_case_detected(self):
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._message(cur,uuid.uuid4(),self.old_conversation,self.old_case,older=True)
        altered=self._read()
        self.assertEqual(len(altered.rows),3)
        self.assertIs(self.seal.capture(self.binding,altered,_snapshot(altered)),SealState.STALE)
        self.assertEqual(self.seal.lookup(self.binding)[5],2)

    def test_05_sql_scope_trigger_rejects_wrong_lead(self):
        real=self._read()
        finger=_snapshot(real)
        other=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.leads_loja('
                        'id,concessionaria_id,telefone_cliente_normalizado) '
                        "values (%s,%s,'+5511977776666')", (other,self.shop))
        args=(str(self.shop),str(self.event),str(self.case),str(other),1,
              self.receipt.snapshot_sha256,str(self.message),real.closure_at,
              finger[1],finger[2],finger[0],finger[3])
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute(_INSERT,args)
        self.assertEqual(cm.exception.sqlstate,'42501')

    def test_06_immutable_update_and_delete(self):
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        for query in ('update prumo_private.cfi01_f03_history_seals_local '
                      'set quantidade_mensagens=500 where evento_fechamento_id=%s',
                      'delete from prumo_private.cfi01_f03_history_seals_local '
                      'where evento_fechamento_id=%s'):
            with self.subTest(query=query):
                with self.assertRaises(self.pg.Error) as cm:
                    with self.pg.connect(DB) as con:
                        con.execute(query,(self.event,))
                self.assertEqual(cm.exception.sqlstate,'42501')

    def test_07_authenticated_role_has_no_direct_manifest_access(self):
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from prumo_private.cfi01_f03_history_seals_local')

    def test_08_scope_cannot_be_changed_on_replay(self):
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        data=self._read()
        digest,count,cases,payload=_snapshot(data)
        args=(str(self.shop),str(self.event),str(self.old_case),data.lead_ref,1,
              self.receipt.snapshot_sha256,str(self.message),data.closure_at,
              count,cases,digest,payload)
        with self.assertRaises(self.pg.Error):
            with self.pg.connect(DB) as con:
                con.execute(_INSERT,args)
        # Existing valid row remains untouched.
        self.assertEqual(self.seal.lookup(self.binding)[5],2)

    def test_09_other_store_message_not_in_history(self):
        other_shop, other_lead, other_channel = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        other_conversation, other_message = uuid.uuid4(), uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute("insert into public.concessionarias(id,nome_operacional) "
                        "values (%s,'OTHER LAB SHOP')",(other_shop,))
            con.execute('insert into public.leads_loja('
                        'id,concessionaria_id,telefone_cliente_normalizado) '
                        "values (%s,%s,'+5511966665555')",(other_lead,other_shop))
            con.execute('insert into public.canais_loja('
                        'id,concessionaria_id,identificador_emissor) '
                        'values (%s,%s,%s)',(other_channel,other_shop,str(other_channel)))
            con.execute('insert into public.conversas('
                        'id,concessionaria_id,lead_id,canal_id) values (%s,%s,%s,%s)',
                        (other_conversation,other_shop,other_lead,other_channel))
            con.execute('insert into public.mensagens('
                        'id,concessionaria_id,conversa_id,canal_id,'
                        'direcao,origem,conteudo_sintetico,id_externo,criada_em) '
                        "values (%s,%s,%s,%s,'entrada','simulado','separado',%s,"
                        "statement_timestamp()-interval '2 days')",
                        (other_message,other_shop,other_conversation,other_channel,str(other_message)))
        data=self._read()
        self.assertEqual(len(data.rows),2)
        self.assertNotIn(str(other_message),[m.message_ref for m in data.rows])

    def test_10_other_person_same_shop_not_in_history(self):
        other_lead,other_conversation,other_message=uuid.uuid4(),uuid.uuid4(),uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.leads_loja('
                        'id,concessionaria_id,telefone_cliente_normalizado) '
                        "values (%s,%s,'+5511955554444')",(other_lead,self.shop))
            con.execute('insert into public.conversas('
                        'id,concessionaria_id,lead_id,canal_id) values (%s,%s,%s,%s)',
                        (other_conversation,self.shop,other_lead,self.channel))
            con.execute('insert into public.mensagens('
                        'id,concessionaria_id,conversa_id,canal_id,'
                        'direcao,origem,conteudo_sintetico,id_externo,criada_em) '
                        "values (%s,%s,%s,%s,'entrada','simulado','outra pessoa',%s,"
                        "statement_timestamp()-interval '2 days')",
                        (other_message,self.shop,other_conversation,self.channel,str(other_message)))
        data=self._read()
        self.assertEqual(len(data.rows),2)
        self.assertNotIn(str(other_message),[m.message_ref for m in data.rows])

    def test_11_content_edit_is_not_detected_by_membership_only_seal(self):
        # Deliberately shows an OPEN GAP, not evidence of content integrity.
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        original=_snapshot(self._read())[0]
        with self.pg.connect(DB) as con:
            con.execute('update public.mensagens set conteudo_sintetico=%s where id=%s',
                        ('texto alterado apos encerramento',self.old_message))
        self.assertEqual(_snapshot(self._read())[0],original)
        self.assertIs(self._save(),SealState.ALREADY_SEALED_REVIEW_ONLY)
        # F03 remains blocked from consuming content by contract.

    def test_12_content_hmac_detects_changed_old_case_text(self):
        from backend.s0_f03_content_integrity_local import (
            S0F03LocalContentIntegrityReader, _equal_proof, ContentState,
        )
        # Fixture key only, NEVER a hosted credential or production signing key.
        key=b'f03-test-only-32-bytes-local-not-for-production!'
        reader=S0F03LocalContentIntegrityReader(DB)
        original=reader.compute(self.receipt,key)
        self.assertIsNotNone(original)
        with self.pg.connect(DB) as con:
            con.execute('update public.mensagens set conteudo_sintetico=%s where id=%s',
                        ('renda manipulada no caso anterior',self.old_message))
        updated=reader.compute(self.receipt,key)
        self.assertIsNotNone(updated)
        self.assertEqual(original.metadata_sha256,updated.metadata_sha256)
        self.assertNotEqual(original.content_mac_sha256,updated.content_mac_sha256)
        self.assertIs(_equal_proof(original,updated),ContentState.CHANGED_REVIEW_REQUIRED)

    def test_13_hmac_same_content_matches_and_different_key_rejects(self):
        from backend.s0_f03_content_integrity_local import (
            S0F03LocalContentIntegrityReader, _equal_proof, ContentState,
        )
        reader=S0F03LocalContentIntegrityReader(DB)
        first=reader.compute(self.receipt,b'f03-test-only-32-bytes-local-not-for-production!')
        second=reader.compute(self.receipt,b'f03-test-only-32-bytes-local-not-for-production!')
        other=reader.compute(self.receipt,b'completely-different-local-test-only-key!')
        self.assertIsNotNone(first)
        self.assertIs(_equal_proof(first,second),ContentState.MATCHES_REVIEW_ONLY)
        self.assertIs(_equal_proof(first,other),ContentState.CHANGED_REVIEW_REQUIRED)
        self.assertEqual(first.count,2)
        self.assertEqual(first.case_count,2)

    def test_14_content_hmac_rejects_short_key_without_database_read(self):
        from backend.s0_f03_content_integrity_local import S0F03LocalContentIntegrityReader
        reader=S0F03LocalContentIntegrityReader(DB)
        self.assertIsNone(reader.compute(self.receipt,b'weak'))

if __name__=='__main__':
    unittest.main()
