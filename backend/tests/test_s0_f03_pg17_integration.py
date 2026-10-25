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

    def test_15_persist_hmac_binds_existing_manifest(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        store=Store(DB)
        key=b'fixture-only-content-seal-key-more-than-32-bytes'
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.SEALED_REVIEW_ONLY)
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=False),
                      State.MATCHES_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            row=con.execute('select chave_versao,metadados_sha256,mac_sha256 '
                'from prumo_private.cfi01_f03_content_proofs_local '
                'where concessionaria_id=%s and evento_fechamento_id=%s',
                (self.shop,self.event)).fetchone()
        self.assertEqual(row[0],'test-key-v1')
        self.assertEqual(len(row[1]),64)
        self.assertEqual(len(row[2]),64)
        self.assertNotEqual(row[1],row[2])

    def test_16_replay_hmac_same_key_is_idempotent(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        self._save()
        store=Store(DB)
        key=b'fixture-only-content-seal-key-more-than-32-bytes'
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.SEALED_REVIEW_ONLY)
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.ALREADY_SEALED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from prumo_private.cfi01_f03_content_proofs_local '
                              'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(count,1)

    def test_17_old_text_mutation_invalidates_persisted_hmac(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        self._save()
        store=Store(DB)
        key=b'fixture-only-content-seal-key-more-than-32-bytes'
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.SEALED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            con.execute('update public.mensagens set conteudo_sintetico=%s where id=%s',
                        ('texto alterado após selação',self.old_message))
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=False),
                      State.STALE_REVIEW_REQUIRED)
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.STALE_REVIEW_REQUIRED)

    def test_18_different_key_or_version_cannot_rebind_original_proof(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        self._save()
        store=Store(DB)
        key=b'fixture-only-content-seal-key-more-than-32-bytes'
        other=b'another-distinct-fixture-key-longer-than-32-bytes'
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.SEALED_REVIEW_ONLY)
        self.assertIs(store.check(self.binding,'test-key-v1',other,create=False),
                      State.STALE_REVIEW_REQUIRED)
        self.assertIs(store.check(self.binding,'test-key-v2',key,create=False),
                      State.STALE_REVIEW_REQUIRED)
        self.assertIs(store.check(self.binding,'test-key-v2',key,create=True),
                      State.STALE_REVIEW_REQUIRED)

    def test_19_source_insert_retrodated_invalidates_hmac(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        self._save()
        store=Store(DB)
        key=b'fixture-only-content-seal-key-more-than-32-bytes'
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.SEALED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._message(cur,uuid.uuid4(),self.old_conversation,self.old_case,older=True)
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=False),
                      State.STALE_REVIEW_REQUIRED)

    def test_20_proof_cannot_exist_without_metadata_manifest(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        key=b'fixture-only-content-seal-key-more-than-32-bytes'
        store=Store(DB)
        self.assertIs(store.check(self.binding,'test-key-v1',key,create=True),
                      State.MISSING_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            num=con.execute('select count(*) from prumo_private.cfi01_f03_content_proofs_local '
                            'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(num,0)

    def test_21_content_proof_immutable_update_delete(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        self._save()
        self.assertIs(Store(DB).check(self.binding,'test-key-v1',
            b'fixture-only-content-seal-key-more-than-32-bytes',create=True),
            State.SEALED_REVIEW_ONLY)
        for sql in ('update prumo_private.cfi01_f03_content_proofs_local '
                    'set chave_versao=%s where evento_fechamento_id=%s',
                    'delete from prumo_private.cfi01_f03_content_proofs_local '
                    'where evento_fechamento_id=%s'):
            params=('other-test-v1',self.event) if 'update' in sql else (self.event,)
            with self.subTest(sql=sql):
                with self.assertRaises(self.pg.Error) as cm:
                    with self.pg.connect(DB) as con:
                        con.execute(sql,params)
                self.assertEqual(cm.exception.sqlstate,'42501')

    def test_22_authenticated_role_cannot_read_content_proof(self):
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from prumo_private.cfi01_f03_content_proofs_local')

    def test_23_two_simultaneous_proof_writers_one_persisted_receipt(self):
        from concurrent.futures import ThreadPoolExecutor
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore as Store, BoundContentState as State,
        )
        self._save()
        key=b'fixture-only-content-seal-key-more-than-32-bytes'
        def attempt(_):
            return Store(DB).check(self.binding,'test-key-v1',key,create=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            states=list(pool.map(attempt,range(2)))
        self.assertCountEqual(states,[State.SEALED_REVIEW_ONLY,
                                       State.ALREADY_SEALED_REVIEW_ONLY])
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from prumo_private.cfi01_f03_content_proofs_local '
                              'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(count,1)

    def _seed_versions(self):
        from backend.s0_f03_version_reservation_local import VersionVector
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_catalog_versions_local '
                        '(concessionaria_id) values (%s)',(self.shop,))
            con.execute('insert into prumo_private.cfi01_f03_lead_versions_local '
                        '(concessionaria_id,lead_id) values (%s,%s)',(self.shop,self.lead))
            con.execute('insert into prumo_private.cfi01_f03_case_versions_local '
                        '(concessionaria_id,caso_id,lead_id) values (%s,%s,%s)',
                        (self.shop,self.case,self.lead))
        return VersionVector(1,1,1,1,1)

    def _prepare_cas(self):
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentStore,BoundContentState,
        )
        from backend.s0_f03_version_reservation_local import S0F03LocalVersionReservationStore
        vector=self._seed_versions()
        self.assertIs(self._save(),SealState.SEALED_REVIEW_ONLY)
        secret=b'fixture-only-content-seal-key-more-than-32-bytes'
        state=S0F03LocalBoundContentStore(DB).check(
            self.binding,'test-key-v1',secret,create=True)
        self.assertIs(state,BoundContentState.SEALED_REVIEW_ONLY)
        return S0F03LocalVersionReservationStore(DB),vector

    def _reserve(self,store,vector,request='request-cas-0001',sha=None,key='test-key-v1'):
        return store.reserve(self.binding,vector,request,sha or 'b'*64,key)

    def test_24_cas_reservation_does_not_modify_customer_or_cycle(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            c=con.execute('select count(*) from prumo_private.cfi01_f03_reservations_local '
                          'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
            form=con.execute('select versao_ficha from prumo_private.cfi01_f03_lead_versions_local '
                             'where lead_id=%s',(self.lead,)).fetchone()[0]
            cycle=con.execute('select versao_registro,status_comercial from public.ciclos_comerciais '
                              'where id=%s',(self.cycle,)).fetchone()
        self.assertEqual(c,1)
        self.assertEqual(form,1)
        self.assertEqual(cycle,(1,'em atendimento pelo operador'))

    def test_25_cas_same_request_is_idempotent(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)
        self.assertIs(self._reserve(store,v),State.ALREADY_HANDLED_REVIEW_ONLY)

    def test_26_cas_different_proposal_same_closure_is_conflict(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)
        self.assertIs(self._reserve(store,v,'request-cas-0002','c'*64),
                      State.CONFLICT_REVIEW_REQUIRED)
        self.assertIs(self._reserve(store,v,'request-cas-0001','c'*64),
                      State.CONFLICT_REVIEW_REQUIRED)

    def test_27_form_version_drift_is_stale(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.cfi01_f03_lead_versions_local '
                        'set versao_ficha=2 where lead_id=%s',(self.lead,))
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_28_catalogue_version_drift_is_stale(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.cfi01_f03_catalog_versions_local '
                        'set versao_catalogo=2 where concessionaria_id=%s',(self.shop,))
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_29_case_version_drift_is_stale(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.cfi01_f03_case_versions_local '
                        'set versao_caso=2 where caso_id=%s',(self.case,))
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_30_assignment_version_drift_is_stale(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.cfi01_f03_case_versions_local '
                        'set versao_atribuicao=2 where caso_id=%s',(self.case,))
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_31_identity_version_drift_is_stale(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.cfi01_f03_lead_versions_local '
                        'set versao_identidade=2 where lead_id=%s',(self.lead,))
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_32_missing_version_source_is_not_fabricated(self):
        from backend.s0_f03_version_reservation_local import (
            S0F03LocalVersionReservationStore,VersionVector,ReservationState as State,
        )
        self._save()
        self.assertIs(self._reserve(S0F03LocalVersionReservationStore(DB),
                                    VersionVector(1,1,1,1,1)),
                      State.MISSING_VERSION_REVIEW_REQUIRED)

    def test_33_missing_content_seal_blocks_reservation(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        v=self._seed_versions()
        from backend.s0_f03_version_reservation_local import S0F03LocalVersionReservationStore
        self.assertIs(self._reserve(S0F03LocalVersionReservationStore(DB),v),
                      State.STALE_REVIEW_REQUIRED)

    def test_34_closed_assignment_blocks_reservation(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update public.atribuicoes_humanas '
                        'set encerrada_em=greatest(atribuida_em,statement_timestamp()) '
                        'where id=%s',(self.assignment,))
        self.assertIs(self._reserve(store,v),State.MISSING_VERSION_REVIEW_REQUIRED)

    def test_35_concurrent_idempotent_reservations_create_one_record(self):
        from concurrent.futures import ThreadPoolExecutor
        from backend.s0_f03_version_reservation_local import (
            ReservationState as State,S0F03LocalVersionReservationStore as Store,
        )
        store,v=self._prepare_cas()
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(lambda _:self._reserve(Store(DB),v),range(2)))
        self.assertCountEqual(statuses,[State.RESERVED_REVIEW_ONLY,
                                        State.ALREADY_HANDLED_REVIEW_ONLY])
        with self.pg.connect(DB) as con:
            n=con.execute('select count(*) from prumo_private.cfi01_f03_reservations_local '
                          'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(n,1)

    def test_36_concurrent_competing_proposals_only_one_reservation(self):
        from concurrent.futures import ThreadPoolExecutor
        from backend.s0_f03_version_reservation_local import (
            ReservationState as State,S0F03LocalVersionReservationStore as Store,
        )
        store,v=self._prepare_cas()
        def contender(i):
            return self._reserve(Store(DB),v,'request-cas-000'+str(i),str(i)*64)
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(contender,[1,2]))
        self.assertCountEqual(statuses,[State.RESERVED_REVIEW_ONLY,
                                        State.CONFLICT_REVIEW_REQUIRED])
        with self.pg.connect(DB) as con:
            n=con.execute('select count(*) from prumo_private.cfi01_f03_reservations_local '
                          'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(n,1)

    def test_37_reservation_audit_is_immutable(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)
        for sql,args in (
            ('update prumo_private.cfi01_f03_reservations_local '
             'set proposta_sha256=%s where evento_fechamento_id=%s',
             ('c'*64,self.event)),
            ('delete from prumo_private.cfi01_f03_reservations_local '
             'where evento_fechamento_id=%s',(self.event,))
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(self.pg.Error) as err:
                    with self.pg.connect(DB) as con:con.execute(sql,args)
                self.assertEqual(err.exception.sqlstate,'42501')

    def test_38_authenticated_role_cannot_read_or_write_reservation(self):
        self._prepare_cas()
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from prumo_private.cfi01_f03_reservations_local')

    def test_39_invalid_digest_or_request_is_denied(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self.assertIs(self._reserve(store,v,'bad','not-a-hash'),State.DENIED)
        self.assertIs(self._reserve(store,v,'request-cas-0001','g'*64),State.DENIED)

    def test_40_cycle_version_drift_prevents_reservation(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update public.ciclos_comerciais set versao_registro=2 '
                        'where id=%s',(self.cycle,))
        self.assertIs(self._reserve(store,v),State.MISSING_VERSION_REVIEW_REQUIRED)

    def test_41_replay_after_form_version_change_is_stale(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.cfi01_f03_lead_versions_local '
                        'set versao_ficha=2 where lead_id=%s',(self.lead,))
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)


    def test_42_real_lead_phone_edit_bumps_identity_and_stales_CAS(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,vector=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('update public.leads_loja set telefone_cliente_normalizado=%s '
                        'where concessionaria_id=%s and id=%s',
                        ('+5511998765432',self.shop,self.lead))
            version=con.execute('select versao_identidade from '
                'prumo_private.cfi01_f03_lead_versions_local where '
                'concessionaria_id=%s and lead_id=%s',(self.shop,self.lead)).fetchone()[0]
        self.assertEqual(version,2)
        self.assertIs(self._reserve(store,vector),State.STALE_REVIEW_REQUIRED)

    def test_43_noop_phone_update_does_not_bump(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('update public.leads_loja set telefone_cliente_normalizado='
                        'telefone_cliente_normalizado where id=%s',(self.lead,))
            ver=con.execute('select versao_identidade from '
                'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
                (self.lead,)).fetchone()[0]
        self.assertEqual(ver,1)

    def test_44_real_case_edit_bumps_case_and_stales_CAS(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute("update public.casos_humanos set criado_em=criado_em + interval '1 second' "
                        'where concessionaria_id=%s and id=%s',(self.shop,self.case))
            ver=con.execute('select versao_caso from '
                'prumo_private.cfi01_f03_case_versions_local where caso_id=%s',
                (self.case,)).fetchone()[0]
        self.assertEqual(ver,2)
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_45_noop_case_update_does_not_bump(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('update public.casos_humanos set criado_em=criado_em '
                        'where id=%s',(self.case,))
            ver=con.execute('select versao_caso from '
                'prumo_private.cfi01_f03_case_versions_local where caso_id=%s',
                (self.case,)).fetchone()[0]
        self.assertEqual(ver,1)

    def test_46_real_assignment_closure_bumps_assignment(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('update public.atribuicoes_humanas '
                        'set encerrada_em=greatest(atribuida_em,statement_timestamp()) '
                        'where id=%s',(self.assignment,))
            ver=con.execute('select versao_atribuicao from '
                'prumo_private.cfi01_f03_case_versions_local where caso_id=%s',
                (self.case,)).fetchone()[0]
        self.assertEqual(ver,2)

    def test_47_noop_assignment_update_does_not_bump(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('update public.atribuicoes_humanas set operador_id=operador_id '
                        'where id=%s',(self.assignment,))
            ver=con.execute('select versao_atribuicao from '
                'prumo_private.cfi01_f03_case_versions_local where caso_id=%s',
                (self.case,)).fetchone()[0]
        self.assertEqual(ver,1)

    def test_48_synthetic_form_insert_bumps_form_and_stales_CAS(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_form_fields_local '
                        '(concessionaria_id,lead_id,campo_sintetico,valor_sintetico) '
                        'values (%s,%s,%s,%s)',
                        (self.shop,self.lead,'renda_sintetica','TEST_ONLY_1000'))
            ver=con.execute('select versao_ficha from '
                'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
                (self.lead,)).fetchone()[0]
        self.assertEqual(ver,2)
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_49_synthetic_form_noop_update_does_not_bump(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_form_fields_local '
                        '(concessionaria_id,lead_id,campo_sintetico,valor_sintetico) '
                        'values (%s,%s,%s,%s)',
                        (self.shop,self.lead,'renda_sintetica','TEST_ONLY_1000'))
            con.execute('update prumo_private.cfi01_f03_form_fields_local '
                        'set valor_sintetico=valor_sintetico where lead_id=%s',
                        (self.lead,))
            ver=con.execute('select versao_ficha from '
                'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
                (self.lead,)).fetchone()[0]
        self.assertEqual(ver,2)

    def test_50_synthetic_catalogue_insert_bumps_and_stales_CAS(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_catalog_entries_local '
                        '(concessionaria_id,codigo_sintetico,descricao_sintetica) '
                        'values (%s,%s,%s)',(self.shop,'VEICULO_TESTE','Modelo ficticio'))
            ver=con.execute('select versao_catalogo from '
                'prumo_private.cfi01_f03_catalog_versions_local where concessionaria_id=%s',
                (self.shop,)).fetchone()[0]
        self.assertEqual(ver,2)
        self.assertIs(self._reserve(store,v),State.STALE_REVIEW_REQUIRED)

    def test_51_catalogue_edit_and_delete_each_bump_once(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_catalog_entries_local '
                        '(concessionaria_id,codigo_sintetico,descricao_sintetica) '
                        'values (%s,%s,%s)',(self.shop,'VEICULO_TESTE','Modelo ficticio'))
            con.execute('update prumo_private.cfi01_f03_catalog_entries_local '
                        'set descricao_sintetica=%s where concessionaria_id=%s',
                        ('Modelo alterado',self.shop))
            con.execute('delete from prumo_private.cfi01_f03_catalog_entries_local '
                        'where concessionaria_id=%s',(self.shop,))
            ver=con.execute('select versao_catalogo from '
                'prumo_private.cfi01_f03_catalog_versions_local where concessionaria_id=%s',
                (self.shop,)).fetchone()[0]
        self.assertEqual(ver,4)

    def test_52_form_source_key_rebind_denied(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_form_fields_local '
                        '(concessionaria_id,lead_id,campo_sintetico,valor_sintetico) '
                        'values (%s,%s,%s,%s)',
                        (self.shop,self.lead,'renda_sintetica','TEST_ONLY_1000'))
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute('update prumo_private.cfi01_f03_form_fields_local '
                            'set campo_sintetico=%s where lead_id=%s',
                            ('telefone_sintetico',self.lead))
        self.assertEqual(cm.exception.sqlstate,'42501')

    def test_53_catalogue_source_key_rebind_denied(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_catalog_entries_local '
                        '(concessionaria_id,codigo_sintetico,descricao_sintetica) '
                        'values (%s,%s,%s)',(self.shop,'VEICULO_TESTE','Modelo ficticio'))
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute('update prumo_private.cfi01_f03_catalog_entries_local '
                            'set codigo_sintetico=%s where concessionaria_id=%s',
                            ('TROCA_NAO_AUTORIZADA',self.shop))
        self.assertEqual(cm.exception.sqlstate,'42501')

    def test_54_uninitialized_form_source_denied(self):
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute('insert into prumo_private.cfi01_f03_form_fields_local '
                            '(concessionaria_id,lead_id,campo_sintetico,valor_sintetico) '
                            'values (%s,%s,%s,%s)',
                            (self.shop,self.lead,'renda_sintetica','TEST_ONLY_1000'))
        self.assertEqual(cm.exception.sqlstate,'42501')

    def test_55_uninitialized_catalogue_source_denied(self):
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute('insert into prumo_private.cfi01_f03_catalog_entries_local '
                            '(concessionaria_id,codigo_sintetico,descricao_sintetica) '
                            'values (%s,%s,%s)',(self.shop,'VEICULO_TESTE','Modelo ficticio'))
        self.assertEqual(cm.exception.sqlstate,'42501')

    def test_56_untouched_S0_lead_without_F03_vector_still_writable(self):
        with self.pg.connect(DB) as con:
            con.execute('update public.leads_loja set telefone_cliente_normalizado=%s '
                        'where concessionaria_id=%s and id=%s',
                        ('+5511998765432',self.shop,self.lead))
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
                (self.lead,)).fetchone()[0]
        self.assertEqual(count,0)

    def test_57_version_sources_tenant_isolated(self):
        self._seed_versions()
        another_shop=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.concessionarias(id,nome_operacional) '
                        "values (%s,'OTHER VERSION TEST SHOP')",(another_shop,))
            con.execute('insert into prumo_private.cfi01_f03_catalog_versions_local '
                        '(concessionaria_id) values (%s)',(another_shop,))
            con.execute('insert into prumo_private.cfi01_f03_catalog_entries_local '
                        '(concessionaria_id,codigo_sintetico,descricao_sintetica) '
                        'values (%s,%s,%s)',(another_shop,'OUTRA_LOJA','Outro modelo'))
            ver=con.execute('select versao_catalogo from '
                'prumo_private.cfi01_f03_catalog_versions_local where concessionaria_id=%s',
                (self.shop,)).fetchone()[0]
            foreign=con.execute('select versao_catalogo from '
                'prumo_private.cfi01_f03_catalog_versions_local where concessionaria_id=%s',
                (another_shop,)).fetchone()[0]
        self.assertEqual((ver,foreign),(1,2))


    def _insert_alias(self,number='+5511999981111',confirmed=True):
        with self.pg.connect(DB) as con:
            return con.execute('insert into prumo_private.aliases_identidade_s0 '
                '(concessionaria_id,lead_id,numero_sintetico,origem,'
                'mobile_confirmado_sintetico) values (%s,%s,%s,%s,%s) returning id',
                (self.shop,self.lead,number,'CANAL_SINTETICO',confirmed)).fetchone()[0]

    def _identity_version(self,lead=None,shop=None):
        with self.pg.connect(DB) as con:
            return con.execute('select versao_identidade from '
                'prumo_private.cfi01_f03_lead_versions_local '
                'where concessionaria_id=%s and lead_id=%s',
                (shop or self.shop,lead or self.lead)).fetchone()[0]

    def test_58_new_alias_invalidates_existing_CAS(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,vector=self._prepare_cas()
        self._insert_alias()
        self.assertEqual(self._identity_version(),2)
        self.assertIs(self._reserve(store,vector),State.STALE_REVIEW_REQUIRED)

    def test_59_unconfirmed_alias_still_invalidates_identity(self):
        self._seed_versions()
        self._insert_alias(confirmed=False)
        self.assertEqual(self._identity_version(),2)

    def test_60_duplicate_alias_insert_does_not_bump(self):
        self._seed_versions()
        self._insert_alias()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.aliases_identidade_s0 '
                '(concessionaria_id,lead_id,numero_sintetico,origem,'
                'mobile_confirmado_sintetico) values (%s,%s,%s,%s,%s) '
                'on conflict(concessionaria_id,numero_sintetico) do nothing',
                (self.shop,self.lead,'+5511999981111','CANAL_SINTETICO',True))
        self.assertEqual(self._identity_version(),2)

    def test_61_alias_evidence_change_invalidates_identity(self):
        self._seed_versions()
        alias=self._insert_alias(confirmed=False)
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.aliases_identidade_s0 '
                'set mobile_confirmado_sintetico=true where id=%s',(alias,))
        self.assertEqual(self._identity_version(),3)

    def test_62_alias_noop_update_does_not_bump(self):
        self._seed_versions()
        alias=self._insert_alias()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.aliases_identidade_s0 '
                'set origem=origem where id=%s',(alias,))
        self.assertEqual(self._identity_version(),2)

    def test_63_alias_deletion_invalidates_identity(self):
        self._seed_versions()
        alias=self._insert_alias()
        with self.pg.connect(DB) as con:
            con.execute('delete from prumo_private.aliases_identidade_s0 '
                'where id=%s',(alias,))
        self.assertEqual(self._identity_version(),3)

    def test_64_alias_cannot_be_rebound_to_different_lead(self):
        self._seed_versions()
        alias=self._insert_alias()
        other=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.leads_loja '
                '(id,concessionaria_id,telefone_cliente_normalizado) '
                "values (%s,%s,'+5511999912222')",(other,self.shop))
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute('update prumo_private.aliases_identidade_s0 '
                    'set lead_id=%s where id=%s',(other,alias))
        self.assertEqual(cm.exception.sqlstate,'42501')
        self.assertEqual(self._identity_version(),2)

    def test_65_identity_event_append_bumps_version(self):
        self._seed_versions()
        alias=self._insert_alias()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.eventos_identidade_s0 '
                '(concessionaria_id,lead_id,alias_id,decisao) '
                'values (%s,%s,%s,%s)',
                (self.shop,self.lead,alias,'MATCH_EXACT'))
        self.assertEqual(self._identity_version(),3)

    def test_66_identity_event_must_match_alias_lead(self):
        self._seed_versions()
        alias=self._insert_alias()
        other=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.leads_loja '
                '(id,concessionaria_id,telefone_cliente_normalizado) '
                "values (%s,%s,'+5511999912222')",(other,self.shop))
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute('insert into prumo_private.eventos_identidade_s0 '
                    '(concessionaria_id,lead_id,alias_id,decisao) '
                    'values (%s,%s,%s,%s)',
                    (self.shop,other,alias,'MATCH_EXACT'))
        self.assertEqual(cm.exception.sqlstate,'42501')

    def test_67_identity_event_decision_change_bumps_version(self):
        self._seed_versions()
        alias=self._insert_alias()
        with self.pg.connect(DB) as con:
            event=con.execute('insert into prumo_private.eventos_identidade_s0 '
                '(concessionaria_id,lead_id,alias_id,decisao) '
                'values (%s,%s,%s,%s) returning id',
                (self.shop,self.lead,alias,'MATCH_EXACT')).fetchone()[0]
            con.execute('update prumo_private.eventos_identidade_s0 '
                'set decisao=%s where id=%s',('MATCH_CANONICAL_VARIANT',event))
        self.assertEqual(self._identity_version(),4)

    def test_68_real_S0_028_resolver_increments_alias_and_event_version(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,vector=self._prepare_cas()
        with self.pg.connect(DB) as con:
            out=con.execute('select prumo_private.resolver_contato_s0(%s,%s,%s,%s)',
                (self.shop,'+5511988887777','CANAL_SINTETICO',True)).fetchone()[0]
        self.assertEqual(out['outcome'],'MATCH_EXACT')
        self.assertEqual(str(out['lead_id']),str(self.lead))
        self.assertEqual(self._identity_version(),3)
        self.assertIs(self._reserve(store,vector),State.STALE_REVIEW_REQUIRED)

    def test_69_alias_change_in_other_store_does_not_invalidate_customer(self):
        self._seed_versions()
        other_shop,other_lead=uuid.uuid4(),uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.concessionarias(id,nome_operacional) '
                "values (%s,'F03 OTHER ALIAS SHOP')",(other_shop,))
            con.execute('insert into public.leads_loja '
                '(id,concessionaria_id,telefone_cliente_normalizado) '
                "values (%s,%s,'+5511977776666')",(other_lead,other_shop))
            con.execute('insert into prumo_private.cfi01_f03_lead_versions_local '
                '(concessionaria_id,lead_id) values (%s,%s)',
                (other_shop,other_lead))
            con.execute('insert into prumo_private.aliases_identidade_s0 '
                '(concessionaria_id,lead_id,numero_sintetico,origem,'
                'mobile_confirmado_sintetico) values (%s,%s,%s,%s,%s)',
                (other_shop,other_lead,'+5511977770000','CANAL_SINTETICO',False))
        self.assertEqual(self._identity_version(),1)
        self.assertEqual(self._identity_version(other_lead,other_shop),2)

    def test_70_alias_without_F03_version_does_not_break_S0(self):
        alias=self._insert_alias()
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
                (self.lead,)).fetchone()[0]
        self.assertEqual(count,0)
        self.assertIsInstance(alias,uuid.UUID)

    def test_71_identity_event_noop_update_does_not_bump(self):
        self._seed_versions()
        alias=self._insert_alias()
        with self.pg.connect(DB) as con:
            event=con.execute('insert into prumo_private.eventos_identidade_s0 '
                '(concessionaria_id,lead_id,alias_id,decisao) '
                'values (%s,%s,%s,%s) returning id',
                (self.shop,self.lead,alias,'MATCH_EXACT')).fetchone()[0]
            con.execute('update prumo_private.eventos_identidade_s0 '
                'set decisao=decisao where id=%s',(event,))
        self.assertEqual(self._identity_version(),3)

    def test_72_event_deletion_invalidates_identity(self):
        self._seed_versions()
        alias=self._insert_alias()
        with self.pg.connect(DB) as con:
            event=con.execute('insert into prumo_private.eventos_identidade_s0 '
                '(concessionaria_id,lead_id,alias_id,decisao) '
                'values (%s,%s,%s,%s) returning id',
                (self.shop,self.lead,alias,'MATCH_EXACT')).fetchone()[0]
            con.execute('delete from prumo_private.eventos_identidade_s0 '
                'where id=%s',(event,))
        self.assertEqual(self._identity_version(),4)

    def test_73_identity_event_cannot_switch_alias_ref(self):
        self._seed_versions()
        first=self._insert_alias()
        second=self._insert_alias(number='+5511999982222')
        with self.pg.connect(DB) as con:
            event=con.execute('insert into prumo_private.eventos_identidade_s0 '
                '(concessionaria_id,lead_id,alias_id,decisao) '
                'values (%s,%s,%s,%s) returning id',
                (self.shop,self.lead,first,'MATCH_EXACT')).fetchone()[0]
        with self.assertRaises(self.pg.Error) as cm:
            with self.pg.connect(DB) as con:
                con.execute('update prumo_private.eventos_identidade_s0 '
                    'set alias_id=%s where id=%s',(second,event))
        self.assertEqual(cm.exception.sqlstate,'42501')


    def _pending_identity(self,phone,shop=None,channel=None):
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.pendencias_identidade_s0 '
                '(concessionaria_id,canal_id,id_externo,telefone_sintetico,'
                'texto_sintetico,motivo) values (%s,%s,%s,%s,%s,%s)',
                (shop or self.shop,channel or self.channel,str(uuid.uuid4()),
                 phone,'fixture: identidade ambigua','IDENTITY_CONFLICT'))

    def test_74_unresolved_exact_phone_blocks_CAS_without_receipt(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self._pending_identity('+5511988887777')
        self.assertIs(self._reserve(store,v),State.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            amount=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_reservations_local '
                'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(amount,0)

    def test_75_unresolved_mobile_variant_blocks_CAS(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        # The source's own Brazilian +55 9-digit/8-digit variant key.
        self._pending_identity('+551188887777')
        self.assertIs(self._reserve(store,v),State.CONFLICT_REVIEW_REQUIRED)

    def test_76_unresolved_alias_phone_blocks_CAS(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        self._insert_alias(number='+5511999981111')
        store,v=self._prepare_cas()
        self._pending_identity('+5511999981111')
        self.assertIs(self._reserve(store,v),State.CONFLICT_REVIEW_REQUIRED)

    def test_77_unrelated_pending_phone_is_not_arbitrary_global_block(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self._pending_identity('+5581999965555')
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)

    def test_78_other_store_pending_phone_is_isolated(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        other_shop,other_channel=uuid.uuid4(),uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.concessionarias(id,nome_operacional) '
                "values (%s,'OTHER PENDING F03 SHOP')",(other_shop,))
            con.execute('insert into public.canais_loja '
                '(id,concessionaria_id,identificador_emissor) '
                'values (%s,%s,%s)',
                (other_channel,other_shop,str(other_channel)))
        self._pending_identity('+5511988887777',other_shop,other_channel)
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)

    def test_79_pending_identity_blocks_idempotent_replay(self):
        from backend.s0_f03_version_reservation_local import ReservationState as State
        store,v=self._prepare_cas()
        self.assertIs(self._reserve(store,v),State.RESERVED_REVIEW_ONLY)
        self._pending_identity('+5511988887777')
        self.assertIs(self._reserve(store,v),State.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            amount=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_reservations_local '
                'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(amount,1)


    def _review_pending(self, pending=None, *, decision=None, expected_version=1,
                        evidence=None, idem='f03-human-review-01', identity=None,
                        s1=True):
        from backend.s0_f03_identity_human_review_local import (
            S0F03LocalHumanReviewStore, HumanReviewRequest,
            HumanReviewDecision, record_human_identity_review_local,
        )
        from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority
        if pending is None:
            with self.pg.connect(DB) as con:
                pending=con.execute(
                    'select id from prumo_private.pendencias_identidade_s0 '
                    'where concessionaria_id=%s order by registrado_em desc,id desc limit 1',
                    (self.shop,)).fetchone()[0]
        req=HumanReviewRequest(
            str(self.case),str(pending),1,expected_version,
            decision or HumanReviewDecision.ESCALATE_REVIEW,
            evidence or 'a'*64,idem)
        return record_human_identity_review_local(
            'Bearer FIXTURE',req,
            identity=identity or LocalIdentity(self.actor,self.session),
            store=S0F03LocalHumanReviewStore(DB),
            s1=S0S1LocalTeamAuthority() if s1 else None)

    def test_80_human_review_is_append_only_and_no_text(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending().state,State.RECORDED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            rows=con.execute('select decisao,evidencia_sha256,ator_id,sessao_id,'
                'versao_identidade from prumo_private.cfi01_f03_identity_human_reviews_local '
                'where concessionaria_id=%s and caso_id=%s',(self.shop,self.case)).fetchall()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][0],'ESCALATE_REVIEW')
        self.assertEqual(rows[0][1],'a'*64)
        self.assertEqual(rows[0][2],self.actor)
        self.assertEqual(rows[0][3],self.session)
        self.assertEqual(rows[0][4],1)

    def test_81_human_review_exact_idempotent_replay(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending().state,State.RECORDED_REVIEW_ONLY)
        self.assertIs(self._review_pending().state,State.ALREADY_RECORDED_REVIEW_ONLY)

    def test_82_human_review_different_decision_conflicts(self):
        from backend.s0_f03_identity_human_review_local import (
            HumanReviewState as State,HumanReviewDecision as Decision,
        )
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending().state,State.RECORDED_REVIEW_ONLY)
        self.assertIs(self._review_pending(
            decision=Decision.CANDIDATE_NOT_RELATED).state,
            State.CONFLICT_REVIEW_REQUIRED)

    def test_83_human_review_missing_pending_is_denied(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self.assertIs(self._review_pending(pending=uuid.uuid4()).state,State.DENIED)

    def test_84_human_review_cannot_attach_unrelated_number(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5581999965555')
        self.assertIs(self._review_pending().state,State.NOT_RELATED_REVIEW_REQUIRED)

    def test_85_human_review_cannot_attach_other_shop_pending(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        shop,channel=uuid.uuid4(),uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.concessionarias(id,nome_operacional) '
                        "values (%s,'OTHER REVIEW LAB SHOP')",(shop,))
            con.execute('insert into public.canais_loja(id,concessionaria_id,'
                        'identificador_emissor) values (%s,%s,%s)',
                        (channel,shop,str(channel)))
            pending=con.execute('insert into prumo_private.pendencias_identidade_s0 '
                '(concessionaria_id,canal_id,id_externo,telefone_sintetico,'
                'texto_sintetico,motivo) values (%s,%s,%s,%s,%s,%s) returning id',
                (shop,channel,str(uuid.uuid4()),'+5511988887777',
                 'fixture outro escopo','NEEDS_REVIEW')).fetchone()[0]
        self.assertIs(self._review_pending(pending=pending).state,State.DENIED)

    def test_86_human_review_stale_identity_version_refused(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending(expected_version=2).state,
                      State.STALE_REVIEW_REQUIRED)

    def test_87_human_review_after_alias_change_requires_fresh_version(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self._insert_alias()
        self.assertIs(self._review_pending(expected_version=1).state,
                      State.STALE_REVIEW_REQUIRED)
        self.assertIs(self._review_pending(expected_version=2).state,
                      State.RECORDED_REVIEW_ONLY)

    def test_88_human_review_absent_S1_cannot_record(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending(s1=False).state,State.BLOCKED_S1)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_identity_human_reviews_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        self.assertEqual(count,0)

    def test_89_human_review_missing_session_is_denied(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        bad_identity=LocalIdentity(uuid.uuid4(),uuid.uuid4())
        self.assertIs(self._review_pending(identity=bad_identity).state,State.DENIED)

    def test_90_human_review_expired_role_is_denied(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        with self.pg.connect(DB) as con:
            con.execute('update public.vinculos_papel_escopo set '
                "valido_desde=statement_timestamp()-interval '2 days', "
                "valido_ate=statement_timestamp()-interval '1 day' "
                'where ator_id=%s and concessionaria_id=%s',
                (self.actor,self.shop))
        self.assertIs(self._review_pending().state,State.DENIED)

    def test_91_human_review_record_is_immutable(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending().state,State.RECORDED_REVIEW_ONLY)
        for query,params in [
            ('update prumo_private.cfi01_f03_identity_human_reviews_local '
             'set decisao=%s where caso_id=%s',('CANDIDATE_NOT_RELATED',self.case)),
            ('delete from prumo_private.cfi01_f03_identity_human_reviews_local '
             'where caso_id=%s',(self.case,))]:
            with self.subTest(query=query):
                with self.assertRaises(self.pg.Error) as cm:
                    with self.pg.connect(DB) as con:con.execute(query,params)
                self.assertEqual(cm.exception.sqlstate,'42501')

    def test_92_authenticated_role_cannot_read_human_reviews(self):
        self._seed_versions()
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from prumo_private.cfi01_f03_identity_human_reviews_local')

    def test_93_simultaneous_different_human_decisions_only_one_receipt(self):
        from concurrent.futures import ThreadPoolExecutor
        from backend.s0_f03_identity_human_review_local import (
            HumanReviewState as State,HumanReviewDecision as Decision,
        )
        self._seed_versions()
        self._pending_identity('+5511988887777')
        def attempt(d):
            return self._review_pending(decision=d).state
        with ThreadPoolExecutor(max_workers=2) as pool:
            got=list(pool.map(attempt,(
                Decision.ESCALATE_REVIEW,Decision.CANDIDATE_NOT_RELATED)))
        self.assertCountEqual(got,[
            State.RECORDED_REVIEW_ONLY,State.CONFLICT_REVIEW_REQUIRED])
        with self.pg.connect(DB) as con:
            amount=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_identity_human_reviews_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        self.assertEqual(amount,1)

    def test_94_human_review_does_not_unblock_F03_reservation(self):
        from backend.s0_f03_identity_human_review_local import (
            HumanReviewState as State,HumanReviewDecision as Decision,
        )
        from backend.s0_f03_version_reservation_local import ReservationState
        store,v=self._prepare_cas()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending(
            decision=Decision.CANDIDATE_NOT_RELATED).state,
            State.RECORDED_REVIEW_ONLY)
        self.assertIs(self._reserve(store,v),ReservationState.CONFLICT_REVIEW_REQUIRED)

    def test_95_human_review_invalid_evidence_digest_denied(self):
        from backend.s0_f03_identity_human_review_local import HumanReviewState as State
        self._seed_versions()
        self._pending_identity('+5511988887777')
        self.assertIs(self._review_pending(evidence='NOT_A_SHA').state,State.DENIED)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_identity_human_reviews_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        self.assertEqual(count,0)


    def _new_ratifiable_review(self, *, seed=True, decision=None):
        from backend.s0_f03_identity_human_review_local import (
            HumanReviewDecision,HumanReviewState,
        )
        if seed:
            self._seed_versions()
        self._pending_identity('+5511988887777')
        state=self._review_pending(decision=(
            decision or HumanReviewDecision.CANDIDATE_NOT_RELATED)).state
        self.assertIs(state,HumanReviewState.RECORDED_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            record=con.execute(
                'select id,pendencia_id from '
                'prumo_private.cfi01_f03_identity_human_reviews_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()
        self.assertIsNotNone(record)
        return record

    def _new_ratification_manager(self, *, scoped=True,team=True,session=True):
        actor,session_id=uuid.uuid4(),uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into auth.users(id) values (%s)',(actor,))
            con.execute('insert into public.atores(id) values (%s)',(actor,))
            if session:
                con.execute('insert into auth.sessions(id,user_id) values (%s,%s)',
                            (session_id,actor))
            if scoped:
                con.execute('insert into public.vinculos_papel_escopo '
                            '(ator_id,concessionaria_id,papel) '
                            "values (%s,%s,'gestor')",(actor,self.shop))
            if team:
                con.execute('insert into public.equipe_prumo_s1(ator_id,estado) '
                            "values (%s,'ativo')",(actor,))
        return actor,session_id

    def _ratify_review(self, review, pending, manager, *, version=1,
                       cycle=1, evidence=None, key='f03-ratification-01',
                       s1=True):
        from backend.s0_f03_identity_ratification_local import (
            S0F03LocalRatificationStore,RatificationRequest,
            ratify_human_identity_review_local,
        )
        from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority
        actor,session=manager
        return ratify_human_identity_review_local(
            'Bearer FIXTURE',
            RatificationRequest(str(review),str(self.case),str(pending),
                                cycle,version,evidence or 'b'*64,key),
            identity=LocalIdentity(actor,session),
            store=S0F03LocalRatificationStore(DB),
            s1=S0S1LocalTeamAuthority() if s1 else None)

    def test_96_second_manager_ratifies_negative_review_as_audit_only(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        manager=self._new_ratification_manager()
        self.assertIs(self._ratify_review(review,pending,manager).state,
                      State.RATIFIED_AUDIT_ONLY)
        with self.pg.connect(DB) as con:
            rows=con.execute('select ratificador_id,revisao_id,decisao,'
                'evidencia_sha256,versao_identidade from '
                'prumo_private.cfi01_f03_identity_ratifications_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchall()
        self.assertEqual(rows,[(manager[0],review,'RATIFY_CANDIDATE_NOT_RELATED',
                                'b'*64,1)])

    def test_97_same_manager_ratification_replay_idempotent(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        manager=self._new_ratification_manager()
        self.assertIs(self._ratify_review(review,pending,manager).state,
                      State.RATIFIED_AUDIT_ONLY)
        self.assertIs(self._ratify_review(review,pending,manager).state,
                      State.ALREADY_RATIFIED_AUDIT_ONLY)

    def test_98_escalation_cannot_be_ratified_as_negative(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        from backend.s0_f03_identity_human_review_local import HumanReviewDecision
        review,pending=self._new_ratifiable_review(
            decision=HumanReviewDecision.ESCALATE_REVIEW)
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager()).state,State.DENIED)

    def test_99_reviewing_operator_cannot_ratify_own_decision(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            review,pending,(self.actor,self.session)).state,State.DENIED)

    def test_100_manager_without_store_role_cannot_ratify(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager(scoped=False)).state,
            State.DENIED)

    def test_101_missing_S1_team_adapter_blocks_ratification(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager(),s1=False).state,
            State.BLOCKED_S1)

    def test_102_manager_not_active_in_S1_cannot_ratify(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager(team=False)).state,
            State.BLOCKED_S1)

    def test_103_identity_change_makes_review_stale_for_ratification(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self._insert_alias()
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager(),version=1).state,
            State.STALE_REVIEW_REQUIRED)
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager(),version=2).state,
            State.STALE_REVIEW_REQUIRED)

    def test_104_cycle_change_makes_review_stale_for_ratification(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        with self.pg.connect(DB) as con:
            con.execute('update public.ciclos_comerciais set versao_registro=2 '
                        'where id=%s',(self.cycle,))
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager()).state,
            State.STALE_REVIEW_REQUIRED)

    def test_105_pending_phone_changed_cannot_be_ratified(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.pendencias_identidade_s0 '
                        'set telefone_sintetico=%s where id=%s',
                        ('+5581999965555',pending))
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager()).state,
            State.STALE_REVIEW_REQUIRED)

    def test_106_wrong_review_reference_is_denied(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            uuid.uuid4(),pending,self._new_ratification_manager()).state,
            State.DENIED)

    def test_107_wrong_pending_reference_is_denied(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            review,uuid.uuid4(),self._new_ratification_manager()).state,
            State.DENIED)

    def test_108_manager_without_live_session_is_denied(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager(session=False)).state,
            State.DENIED)

    def test_109_ratification_record_is_immutable(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        manager=self._new_ratification_manager()
        self.assertIs(self._ratify_review(review,pending,manager).state,
                      State.RATIFIED_AUDIT_ONLY)
        for query,params in (
            ('update prumo_private.cfi01_f03_identity_ratifications_local '
             'set evidencia_sha256=%s where caso_id=%s',('c'*64,self.case)),
            ('delete from prumo_private.cfi01_f03_identity_ratifications_local '
             'where caso_id=%s',(self.case,))):
            with self.subTest(query=query):
                with self.assertRaises(self.pg.Error) as exc:
                    with self.pg.connect(DB) as con: con.execute(query,params)
                self.assertEqual(exc.exception.sqlstate,'42501')

    def test_110_authenticated_cannot_read_ratification_ledger(self):
        self._new_ratifiable_review()
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from '
                            'prumo_private.cfi01_f03_identity_ratifications_local')

    def test_111_concurrent_competing_manager_receipts_one_wins(self):
        from concurrent.futures import ThreadPoolExecutor
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        managers=[self._new_ratification_manager() for _ in range(2)]
        def attempt(item):
            i,manager=item
            return self._ratify_review(
                review,pending,manager,evidence=str(i+1)*64,
                key='f03-ratification-'+str(i+1)).state
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,enumerate(managers)))
        self.assertCountEqual(results,[
            State.RATIFIED_AUDIT_ONLY,State.CONFLICT_REVIEW_REQUIRED])
        with self.pg.connect(DB) as con:
            amount=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_identity_ratifications_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        self.assertEqual(amount,1)

    def test_112_ratification_does_not_unblock_F03_CAS(self):
        from backend.s0_f03_identity_ratification_local import RatificationState
        from backend.s0_f03_version_reservation_local import ReservationState
        store,vector=self._prepare_cas()
        review,pending=self._new_ratifiable_review(seed=False)
        manager=self._new_ratification_manager()
        self.assertIs(self._ratify_review(review,pending,manager).state,
                      RatificationState.RATIFIED_AUDIT_ONLY)
        self.assertIs(self._reserve(store,vector),
                      ReservationState.CONFLICT_REVIEW_REQUIRED)

    def test_113_direct_same_actor_insert_blocked_by_SQL_trigger(self):
        review,pending=self._new_ratifiable_review()
        query=('insert into prumo_private.cfi01_f03_identity_ratifications_local '
               '(concessionaria_id,pendencia_id,caso_id,revisao_id,'
               'lead_candidato_id,ratificador_id,sessao_id,versao_ciclo,'
               'versao_identidade,decisao,evidencia_sha256,chave_idempotencia) '
               'values (%s,%s,%s,%s,%s,%s,%s,1,1,%s,%s,%s)')
        with self.assertRaises(self.pg.Error) as exc:
            with self.pg.connect(DB) as con:
                con.execute(query,(self.shop,pending,self.case,review,self.lead,
                                   self.actor,self.session,'RATIFY_CANDIDATE_NOT_RELATED',
                                   'a'*64,'ratify-direct-invalid-01'))
        self.assertEqual(exc.exception.sqlstate,'42501')

    def test_114_malformed_ratification_hash_is_denied(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        self.assertIs(self._ratify_review(
            review,pending,self._new_ratification_manager(),
            evidence='not-a-digest').state,State.DENIED)

    def test_115_expired_gestor_role_is_denied(self):
        from backend.s0_f03_identity_ratification_local import RatificationState as State
        review,pending=self._new_ratifiable_review()
        manager=self._new_ratification_manager()
        with self.pg.connect(DB) as con:
            con.execute('update public.vinculos_papel_escopo set '
                        "valido_desde=statement_timestamp()-interval '2 days',"
                        "valido_ate=statement_timestamp()-interval '1 day' "
                        'where ator_id=%s and concessionaria_id=%s',
                        (manager[0],self.shop))
        self.assertIs(self._ratify_review(
            review,pending,manager).state,State.DENIED)


    def _resolution_chain(self):
        from backend.s0_f03_identity_ratification_local import RatificationState
        review,pending=self._new_ratifiable_review()
        manager=self._new_ratification_manager()
        self.assertIs(self._ratify_review(review,pending,manager).state,
                      RatificationState.RATIFIED_AUDIT_ONLY)
        with self.pg.connect(DB) as con:
            ratification=con.execute('select id from '
                'prumo_private.cfi01_f03_identity_ratifications_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        closer=self._new_ratification_manager()
        return review,pending,ratification,manager,closer

    def _close_resolution(self,chain,*,closer=None,version=1,cycle=1,
                          secret=None,key_version='resolution-key-v1',
                          evidence=None,idem='resolution-local-0001',s1=True):
        from backend.s0_f03_identity_resolution_local import (
            S0F03LocalResolutionStore,ResolutionRequest,
            close_human_identity_resolution_local,
        )
        from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority
        review,pending,ratification,_ratifier,default_closer=chain
        actor,session=closer or default_closer
        return close_human_identity_resolution_local(
            'Bearer FIXTURE',
            ResolutionRequest(str(review),str(ratification),str(pending),
                str(self.case),cycle,version,key_version,
                evidence or 'c'*64,idem),
            identity=LocalIdentity(actor,session),
            store=S0F03LocalResolutionStore(DB),
            s1=S0S1LocalTeamAuthority() if s1 else None,
            key=secret if secret is not None else
              b'S0-E04-fixture-only-resolution-secret-minimum-32-bytes')

    def test_116_third_independent_manager_closes_hold_only(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        with self.pg.connect(DB) as con:
            rows=con.execute('select resultado,chave_hmac_versao,'
                'pendencia_mac_sha256,evidencia_sha256,gestor_resolvedor_id '
                'from prumo_private.cfi01_f03_identity_resolution_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchall()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][0],'NOT_RELATED_HOLD_ONLY')
        self.assertEqual(rows[0][1],'resolution-key-v1')
        self.assertEqual(len(rows[0][2]),64)
        self.assertEqual(rows[0][3],'c'*64)
        self.assertEqual(rows[0][4],chain[4][0])

    def test_117_exact_replay_is_idempotent(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.ALREADY_CLOSED_HOLD_ONLY)

    def test_118_source_mutation_invalidates_old_proof_replay(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.pendencias_identidade_s0 '
                        'set texto_sintetico=%s where id=%s',
                        ('outra narrativa ficticia',chain[1]))
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CONFLICT_REVIEW_REQUIRED)

    def test_119_different_runtime_key_cannot_replay(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        self.assertIs(self._close_resolution(
            chain,secret=b'different-fixture-S0-hmac-secret-32-bytes-or-more').state,
            ResolutionState.CONFLICT_REVIEW_REQUIRED)

    def test_120_new_hmac_key_version_cannot_override_receipt(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        self.assertIs(self._close_resolution(
            chain,key_version='resolution-key-v2').state,
            ResolutionState.CONFLICT_REVIEW_REQUIRED)

    def test_121_reviewer_cannot_close_own_case(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(
            chain,closer=(self.actor,self.session)).state,ResolutionState.DENIED)

    def test_122_ratifier_cannot_close_own_ratification(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(
            chain,closer=chain[3]).state,ResolutionState.DENIED)

    def test_123_unscoped_manager_cannot_close(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        outsider=self._new_ratification_manager(scoped=False)
        self.assertIs(self._close_resolution(
            chain,closer=outsider).state,ResolutionState.DENIED)

    def test_124_missing_S1_adapter_fails_closed(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain,s1=False).state,
                      ResolutionState.BLOCKED_S1)

    def test_125_changed_identity_version_fails_closed(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self._insert_alias()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.STALE_REVIEW_REQUIRED)
        self.assertIs(self._close_resolution(chain,version=2).state,
                      ResolutionState.STALE_REVIEW_REQUIRED)

    def test_126_changed_cycle_version_fails_closed(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        with self.pg.connect(DB) as con:
            con.execute('update public.ciclos_comerciais '
                        'set versao_registro=2 where id=%s',(self.cycle,))
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.STALE_REVIEW_REQUIRED)

    def test_127_change_phone_in_pending_fails_closed(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.pendencias_identidade_s0 '
                        'set telefone_sintetico=%s where id=%s',
                        ('+5581999965555',chain[1]))
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.STALE_REVIEW_REQUIRED)

    def test_128_wrong_ratification_reference_fails_closed(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=list(self._resolution_chain())
        chain[2]=uuid.uuid4()
        self.assertIs(self._close_resolution(chain).state,ResolutionState.DENIED)

    def test_129_missing_session_fails_closed(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        actor=self._new_ratification_manager(session=False)
        self.assertIs(self._close_resolution(chain,closer=actor).state,
                      ResolutionState.DENIED)

    def test_130_competing_closers_one_receipt_only(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        from concurrent.futures import ThreadPoolExecutor
        chain=self._resolution_chain()
        managers=[chain[4],self._new_ratification_manager()]
        def attempt(i):
            return self._close_resolution(
                chain,closer=managers[i],evidence=str(i+1)*64,
                idem='resolution-local-competing-'+str(i)).state
        with ThreadPoolExecutor(max_workers=2) as pool:
            got=list(pool.map(attempt,[0,1]))
        self.assertCountEqual(got,[ResolutionState.CLOSED_HOLD_ONLY,
                                   ResolutionState.CONFLICT_REVIEW_REQUIRED])
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_identity_resolution_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        self.assertEqual(count,1)

    def test_131_resolution_does_not_unblock_F03_CAS(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        from backend.s0_f03_version_reservation_local import ReservationState
        store,v=self._prepare_cas()
        chain=self._resolution_chain_from_existing_version()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        self.assertIs(self._reserve(store,v),ReservationState.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            remaining=con.execute('select count(*) from '
                'prumo_private.pendencias_identidade_s0 '
                'where id=%s',(chain[1],)).fetchone()[0]
        self.assertEqual(remaining,1)

    def _resolution_chain_from_existing_version(self):
        from backend.s0_f03_identity_ratification_local import RatificationState
        review,pending=self._new_ratifiable_review(seed=False)
        manager=self._new_ratification_manager()
        self.assertIs(self._ratify_review(review,pending,manager).state,
                      RatificationState.RATIFIED_AUDIT_ONLY)
        with self.pg.connect(DB) as con:
            ratification=con.execute('select id from '
                'prumo_private.cfi01_f03_identity_ratifications_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        return review,pending,ratification,manager,self._new_ratification_manager()

    def test_132_resolution_update_delete_are_forbidden(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        for sql,params in (
            ('update prumo_private.cfi01_f03_identity_resolution_local '
             'set evidencia_sha256=%s where caso_id=%s',('f'*64,self.case)),
            ('delete from prumo_private.cfi01_f03_identity_resolution_local '
             'where caso_id=%s',(self.case,))
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(self.pg.Error) as err:
                    with self.pg.connect(DB) as con:con.execute(sql,params)
                self.assertEqual(err.exception.sqlstate,'42501')

    def test_133_authenticated_cannot_read_resolution(self):
        self._resolution_chain()
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from '
                            'prumo_private.cfi01_f03_identity_resolution_local')

    def test_134_malformed_hmac_input_is_denied(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain,secret=b'short').state,
                      ResolutionState.DENIED)
        self.assertIs(self._close_resolution(chain,key_version='bad key').state,
                      ResolutionState.DENIED)

    def test_135_expired_manager_role_is_denied(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        with self.pg.connect(DB) as con:
            con.execute('update public.vinculos_papel_escopo set '
                        "valido_desde=statement_timestamp()-interval '2 days',"
                        "valido_ate=statement_timestamp()-interval '1 day' "
                        'where ator_id=%s and concessionaria_id=%s',
                        (chain[4][0],self.shop))
        self.assertIs(self._close_resolution(chain).state,ResolutionState.DENIED)


    def _closed_resolution_for_verify(self):
        from backend.s0_f03_identity_resolution_local import ResolutionState
        chain=self._resolution_chain()
        self.assertIs(self._close_resolution(chain).state,
                      ResolutionState.CLOSED_HOLD_ONLY)
        with self.pg.connect(DB) as con:
            resolution=con.execute(
                'select id from prumo_private.cfi01_f03_identity_resolution_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        return chain,resolution

    def _verify_resolution_hold(self,chain,resolution,*,principal=None,
                                key=None,key_id='resolution-key-v1',s1=True,
                                pending=None,case=None):
        from backend.s0_f03_identity_resolution_verify_local import (
            S0F03LocalResolutionValidityStore,ValidityRequest,
            verify_human_identity_resolution_local,
        )
        from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority
        actor,session=principal or chain[4]
        return verify_human_identity_resolution_local(
            'Bearer FIXTURE',
            ValidityRequest(str(resolution),str(pending or chain[1]),
                            str(case or self.case),key_id),
            identity=LocalIdentity(actor,session),
            store=S0F03LocalResolutionValidityStore(DB),
            s1=S0S1LocalTeamAuthority() if s1 else None,
            key=key if key is not None else
                 b'S0-E04-fixture-only-resolution-secret-minimum-32-bytes')

    def test_136_live_close_hmac_matches_only_as_hold(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        check=self._verify_resolution_hold(chain,rid)
        self.assertIs(check.state,ValidityState.CURRENT_HOLD_ONLY)
        self.assertEqual(tuple(vars(check)),('state',))
        self.assertFalse(hasattr(check,'content'))

    def test_137_verification_is_read_only_and_does_not_grant_F03(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        from backend.s0_f03_version_reservation_local import ReservationState
        store,v=self._prepare_cas()
        chain=self._resolution_chain_from_existing_version()
        self.assertIs(self._close_resolution(chain).state,
                      __import__('backend.s0_f03_identity_resolution_local',
                                 fromlist=['ResolutionState']).ResolutionState.CLOSED_HOLD_ONLY)
        with self.pg.connect(DB) as con:
            rid=con.execute('select id from '
                'prumo_private.cfi01_f03_identity_resolution_local '
                'where concessionaria_id=%s and caso_id=%s',
                (self.shop,self.case)).fetchone()[0]
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CURRENT_HOLD_ONLY)
        self.assertIs(self._reserve(store,v),ReservationState.CONFLICT_REVIEW_REQUIRED)

    def test_138_pending_text_change_invalidates_hmac(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.pendencias_identidade_s0 '
                        'set texto_sintetico=%s where id=%s',
                        ('texto alterado posteriormente',chain[1]))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_139_pending_reason_change_invalidates_hmac(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.pendencias_identidade_s0 '
                        'set motivo=%s where id=%s',
                        ('NEEDS_REVIEW',chain[1]))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_140_pending_phone_change_is_stale(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.pendencias_identidade_s0 '
                        'set telefone_sintetico=%s where id=%s',
                        ('+5581999965555',chain[1]))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_141_alias_insert_invalidates_identity_version(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        self._insert_alias()
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_142_main_phone_change_invalidates_version(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('update public.leads_loja '
                        'set telefone_cliente_normalizado=%s where id=%s',
                        ('+5511999933333',self.lead))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_143_cycle_changed_is_stale(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('update public.ciclos_comerciais '
                        'set versao_registro=versao_registro+1 where id=%s',
                        (self.cycle,))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_144_assignment_closed_is_stale(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('update public.atribuicoes_humanas '
                        'set encerrada_em=greatest(atribuida_em,statement_timestamp()) '
                        'where id=%s',(self.assignment,))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_145_new_matching_pending_is_conflict_even_with_valid_hmac(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        self._pending_identity('+5511988887777')
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CONFLICT_REVIEW_REQUIRED)

    def test_146_unrelated_pending_same_shop_not_global_block(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        self._pending_identity('+5581999965555')
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CURRENT_HOLD_ONLY)

    def test_147_pending_other_shop_not_global_block(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        other_shop,other_channel=uuid.uuid4(),uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.concessionarias(id,nome_operacional) '
                        "values (%s,'OTHER VERIFY HOLD SHOP')",(other_shop,))
            con.execute('insert into public.canais_loja '
                        '(id,concessionaria_id,identificador_emissor) '
                        'values (%s,%s,%s)',
                        (other_channel,other_shop,str(other_channel)))
        self._pending_identity('+5511988887777',other_shop,other_channel)
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CURRENT_HOLD_ONLY)

    def test_148_other_manager_cannot_verify_owner_hold(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        other=self._new_ratification_manager()
        self.assertIs(self._verify_resolution_hold(
            chain,rid,principal=other).state,ValidityState.DENIED)

    def test_149_old_or_missing_session_cannot_verify(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        other=(chain[4][0],uuid.uuid4())
        self.assertIs(self._verify_resolution_hold(
            chain,rid,principal=other).state,ValidityState.DENIED)

    def test_150_wrong_HMAC_key_or_version_is_stale(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        self.assertIs(self._verify_resolution_hold(
            chain,rid,key=b'another-S0-disposable-secret-longer-than-32-bytes'
            ).state,ValidityState.STALE_REVIEW_REQUIRED)
        self.assertIs(self._verify_resolution_hold(
            chain,rid,key_id='resolution-key-v2'
            ).state,ValidityState.STALE_REVIEW_REQUIRED)

    def test_151_expired_manager_role_denied_live(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('update public.vinculos_papel_escopo set '
                        "valido_desde=statement_timestamp()-interval '2 days',"
                        "valido_ate=statement_timestamp()-interval '1 day' "
                        'where ator_id=%s and concessionaria_id=%s',
                        (chain[4][0],self.shop))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.DENIED)

    def test_152_no_S1_authority_fails_closed(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        self.assertIs(self._verify_resolution_hold(
            chain,rid,s1=False).state,ValidityState.BLOCKED_S1)

    def test_153_invalid_scope_and_short_key_denied(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        self.assertIs(self._verify_resolution_hold(
            chain,rid,case=uuid.uuid4()).state,ValidityState.DENIED)
        self.assertIs(self._verify_resolution_hold(
            chain,rid,key=b'short').state,ValidityState.DENIED)


    def test_154_competing_second_primary_lead_blocks_hold(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.leads_loja '
                        '(id,concessionaria_id,telefone_cliente_normalizado) '
                        'values (%s,%s,%s)',
                        (uuid.uuid4(),self.shop,'+551188887777'))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CONFLICT_REVIEW_REQUIRED)

    def test_155_competing_alias_lead_blocks_hold_without_merging(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        other=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.leads_loja '
                        '(id,concessionaria_id,telefone_cliente_normalizado) '
                        'values (%s,%s,%s)',
                        (other,self.shop,'+5581999989999'))
            con.execute('insert into prumo_private.aliases_identidade_s0 '
                        '(concessionaria_id,lead_id,numero_sintetico,'
                        'origem,mobile_confirmado_sintetico) '
                        'values (%s,%s,%s,%s,%s)',
                        (self.shop,other,'+551188887777',
                         'CANAL_SINTETICO',True))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CONFLICT_REVIEW_REQUIRED)

    def test_156_concurrent_pending_writer_cannot_pass_shop_lock(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as keeper:
            keeper.execute('select prumo_private.s0_f03_lock_shop_local(%s)',
                           (self.shop,))
            with self.assertRaises(self.pg.Error) as e:
                with self.pg.connect(DB) as writer:
                    writer.execute("set local lock_timeout='150ms'")
                    writer.execute('insert into prumo_private.pendencias_identidade_s0 '
                        '(concessionaria_id,canal_id,id_externo,telefone_sintetico,'
                        'texto_sintetico,motivo) values (%s,%s,%s,%s,%s,%s)',
                        (self.shop,self.channel,str(uuid.uuid4()),
                         '+5511988887777','concorrente','IDENTITY_CONFLICT'))
            self.assertEqual(e.exception.sqlstate,'55P03')
        self._pending_identity('+5511988887777')
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CONFLICT_REVIEW_REQUIRED)

    def test_157_concurrent_alias_writer_cannot_pass_shop_lock(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        with self.pg.connect(DB) as keeper:
            keeper.execute('select prumo_private.s0_f03_lock_shop_local(%s)',
                           (self.shop,))
            with self.assertRaises(self.pg.Error) as e:
                with self.pg.connect(DB) as writer:
                    writer.execute("set local lock_timeout='150ms'")
                    writer.execute('insert into prumo_private.aliases_identidade_s0 '
                        '(concessionaria_id,lead_id,numero_sintetico,'
                        'origem,mobile_confirmado_sintetico) '
                        'values (%s,%s,%s,%s,%s)',
                        (self.shop,self.lead,'+5511999974444',
                         'CANAL_SINTETICO',False))
            self.assertEqual(e.exception.sqlstate,'55P03')
        self._insert_alias('+5511999974444',confirmed=False)
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.STALE_REVIEW_REQUIRED)

    def test_158_cross_shop_writer_is_not_blocked(self):
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        shop,channel=uuid.uuid4(),uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.concessionarias(id,nome_operacional) '
                        "values (%s,'TEST OTHER SHOP')",(shop,))
            con.execute('insert into public.canais_loja '
                        '(id,concessionaria_id,identificador_emissor) '
                        'values (%s,%s,%s)',(channel,shop,str(channel)))
        with self.pg.connect(DB) as keeper:
            keeper.execute('select prumo_private.s0_f03_lock_shop_local(%s)',
                           (self.shop,))
            with self.pg.connect(DB) as writer:
                writer.execute("set local lock_timeout='150ms'")
                writer.execute('insert into prumo_private.pendencias_identidade_s0 '
                    '(concessionaria_id,canal_id,id_externo,telefone_sintetico,'
                    'texto_sintetico,motivo) values (%s,%s,%s,%s,%s,%s)',
                    (shop,channel,str(uuid.uuid4()),
                     '+5511988887777','outra loja','NEEDS_REVIEW'))
        self.assertIs(self._verify_resolution_hold(chain,rid).state,
                      ValidityState.CURRENT_HOLD_ONLY)

    def test_159_reader_waits_for_committed_pending_writer(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        from backend.s0_f03_identity_resolution_verify_local import ValidityState
        chain,rid=self._closed_resolution_for_verify()
        started=Event()
        with self.pg.connect(DB) as writer:
            writer.execute('insert into prumo_private.pendencias_identidade_s0 '
                '(concessionaria_id,canal_id,id_externo,telefone_sintetico,'
                'texto_sintetico,motivo) values (%s,%s,%s,%s,%s,%s)',
                (self.shop,self.channel,str(uuid.uuid4()),
                 '+5511988887777','commit pendente','IDENTITY_CONFLICT'))
            with ThreadPoolExecutor(max_workers=1) as pool:
                def reader():
                    started.set()
                    return self._verify_resolution_hold(chain,rid).state
                result=pool.submit(reader)
                self.assertTrue(started.wait(2))
                writer.commit()
                self.assertIs(result.result(timeout=6),
                              ValidityState.CONFLICT_REVIEW_REQUIRED)



    def _operational_fixture(self,fields,*,definitions=None,products=()):
        from backend.s0_f03_operational_contracts_local import proposal_digest
        from backend.s0_f03_version_reservation_local import (
            VersionVector,ReservationState,
        )
        reservation,vector=self._prepare_cas()
        definitions=definitions if definitions is not None else (
            ('observacao_sintetica','TEXT_ONLY',48,True),
        )
        with self.pg.connect(DB) as con:
            for key,kind,max_chars,active in definitions:
                con.execute('insert into '
                    'prumo_private.cfi01_f03_operational_field_contracts_local '
                    '(concessionaria_id,campo_sintetico,tipo_sintetico,'
                    'max_chars,ativo_sintetico) values (%s,%s,%s,%s,%s)',
                    (self.shop,key,kind,max_chars,active))
            for key,active in products:
                con.execute('insert into prumo_private.cfi01_f03_catalog_entries_local '
                    '(concessionaria_id,codigo_sintetico,descricao_sintetica,'
                    'ativo_sintetico) values (%s,%s,%s,%s)',
                    (self.shop,key,'Produto ficticio da loja',active))
            cat=con.execute('select versao_catalogo from '
                'prumo_private.cfi01_f03_catalog_versions_local '
                'where concessionaria_id=%s',(self.shop,)).fetchone()[0]
        vector=VersionVector(vector.form,cat,vector.case,vector.assignment,
                             vector.identity)
        digest=proposal_digest(fields)
        self.assertIsNotNone(digest)
        self.assertIs(self._reserve(reservation,vector,sha=digest),
                      ReservationState.RESERVED_REVIEW_ONLY)
        return vector,digest

    def _operational_check(self,fields,vector,digest):
        from backend.s0_f03_operational_contracts_local import (
            S0F03LocalOperationalContractsStore,
        )
        return S0F03LocalOperationalContractsStore(DB).check(
            self.binding,vector,'request-cas-0001',digest,
            'test-key-v1',fields)

    def test_160_operational_text_review_is_read_only(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,
                              'Preferencia ficticia'),)
        v,d=self._operational_fixture(fields)
        with self.pg.connect(DB) as con:
            before=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_form_fields_local '
                'where concessionaria_id=%s',(self.shop,)).fetchone()[0]
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.CONTRACT_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            after=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_form_fields_local '
                'where concessionaria_id=%s',(self.shop,)).fetchone()[0]
        self.assertEqual((before,after),(0,0))

    def test_161_active_catalog_code_review_only(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('produto_sintetico',FieldKind.CATALOG_CODE,
                              'MODELO_TESTE'),)
        v,d=self._operational_fixture(fields,definitions=(
            ('produto_sintetico','CATALOG_CODE',48,True),),
            products=(('MODELO_TESTE',True),))
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.CONTRACT_REVIEW_ONLY)

    def test_162_unregistered_field_is_denied_by_contract(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('identidade_sintetica',FieldKind.TEXT_ONLY,'x'),)
        v,d=self._operational_fixture(fields)
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.FIELD_REVIEW_REQUIRED)

    def test_163_wrong_field_kind_is_denied(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('observacao_sintetica',FieldKind.CATALOG_CODE,
                              'MODELO_TESTE'),)
        v,d=self._operational_fixture(fields)
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.FIELD_REVIEW_REQUIRED)

    def test_164_field_length_above_contract_is_denied(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,
                              'x'*50),)
        v,d=self._operational_fixture(fields)
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.FIELD_REVIEW_REQUIRED)

    def test_165_nonexistent_catalog_item_denied(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('produto_sintetico',FieldKind.CATALOG_CODE,
                              'INEXISTENTE'),)
        v,d=self._operational_fixture(fields,definitions=(
            ('produto_sintetico','CATALOG_CODE',48,True),))
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.CATALOG_REVIEW_REQUIRED)

    def test_166_inactive_catalog_item_denied(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('produto_sintetico',FieldKind.CATALOG_CODE,
                              'MODELO_TESTE'),)
        v,d=self._operational_fixture(fields,definitions=(
            ('produto_sintetico','CATALOG_CODE',48,True),),
            products=(('MODELO_TESTE',False),))
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.CATALOG_REVIEW_REQUIRED)

    def test_167_catalog_version_drift_invalidates_contract(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,
                              'Texto ficticio'),)
        v,d=self._operational_fixture(fields)
        with self.pg.connect(DB) as con:
            con.execute('update prumo_private.cfi01_f03_operational_field_contracts_local '
                'set max_chars=%s where concessionaria_id=%s and campo_sintetico=%s',
                (64,self.shop,'observacao_sintetica'))
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.STALE_REVIEW_REQUIRED)

    def test_168_form_version_drift_invalidates_contract(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'x'),)
        v,d=self._operational_fixture(fields)
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_form_fields_local '
                '(concessionaria_id,lead_id,campo_sintetico,valor_sintetico) '
                'values (%s,%s,%s,%s)',
                (self.shop,self.lead,'observacao_sintetica','valor existente'))
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.STALE_REVIEW_REQUIRED)

    def test_169_new_identity_pending_invalidates_contract(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        fields=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'x'),)
        v,d=self._operational_fixture(fields)
        self._pending_identity('+5511988887777')
        self.assertIs(self._operational_check(fields,v,d),
                      OperationalState.CONFLICT_REVIEW_REQUIRED)

    def test_170_contract_rekey_is_forbidden(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,
        )
        fields=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'x'),)
        self._operational_fixture(fields)
        with self.assertRaises(self.pg.Error) as err:
            with self.pg.connect(DB) as con:
                con.execute('update prumo_private.cfi01_f03_operational_field_contracts_local '
                  'set tipo_sintetico=%s where concessionaria_id=%s '
                  'and campo_sintetico=%s',
                  ('CATALOG_CODE',self.shop,'observacao_sintetica'))
        self.assertEqual(err.exception.sqlstate,'42501')

    def test_171_authenticated_cannot_query_field_registry(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,
        )
        self._operational_fixture((
            ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'x'),))
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from '
                    'prumo_private.cfi01_f03_operational_field_contracts_local')


    def _application_fixture(self,*,multiple=False,existing=False):
        from backend.s0_f03_operational_contracts_local import ProposedField,FieldKind
        from backend.s0_f03_field_application_local import (
            FieldCAS,HumanFieldRequest,HumanDecision,_sha,
        )
        fields=[ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,
                              'preferencia ficticia aprovada')]
        defs=[('observacao_sintetica','TEXT_ONLY',48,True)]
        products=()
        if multiple:
            fields.append(ProposedField('produto_sintetico',
                                        FieldKind.CATALOG_CODE,'MODELO_TESTE'))
            defs.append(('produto_sintetico','CATALOG_CODE',48,True))
            products=(('MODELO_TESTE',True),)
        vector,digest=self._operational_fixture(tuple(fields),
                               definitions=tuple(defs),products=products)
        if existing:
            with self.pg.connect(DB) as con:
                con.execute('insert into prumo_private.cfi01_f03_form_fields_local '
                    '(concessionaria_id,lead_id,campo_sintetico,valor_sintetico) '
                    'values (%s,%s,%s,%s)',
                    (self.shop,self.lead,'observacao_sintetica','texto anterior'))
            # The reservation became stale; this is intentional for stale tests.
        cas=tuple(FieldCAS(field,None) for field in fields)
        req=HumanFieldRequest(self.binding,vector,'request-cas-0001',
                    'test-key-v1',cas,HumanDecision.EXPLICIT_APPROVE_SYNTHETIC_FIELDS,
                    'a'*64,'human-apply-fixture-001')
        manager=self._new_ratification_manager()
        return req,manager

    def _human_apply(self,req,manager,*,secret=None,s1=True):
        from backend.s0_f03_field_application_local import (
            S0F03LocalHumanFieldApplicationStore,apply_human_s0_synthetic_fields,
        )
        from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority
        return apply_human_s0_synthetic_fields('Bearer FIXTURE',req,
            identity=LocalIdentity(*manager),
            store=S0F03LocalHumanFieldApplicationStore(DB),
            s1=S0S1LocalTeamAuthority() if s1 else None,
            key=secret if secret is not None else
                b'fixture-only-content-seal-key-more-than-32-bytes')

    def test_172_human_s0_applies_one_synthetic_field_and_audits(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        response=self._human_apply(req,manager)
        self.assertIs(response.state,ApplicationState.APPLIED_SYNTHETIC_ONLY)
        self.assertEqual(tuple(vars(response)),('state',))
        with self.pg.connect(DB) as con:
            field=con.execute('select valor_sintetico from '
              'prumo_private.cfi01_f03_form_fields_local '
              'where concessionaria_id=%s and lead_id=%s '
              'and campo_sintetico=%s',
              (self.shop,self.lead,'observacao_sintetica')).fetchone()[0]
            ver=con.execute('select versao_ficha from '
              'prumo_private.cfi01_f03_lead_versions_local '
              'where concessionaria_id=%s and lead_id=%s',
              (self.shop,self.lead)).fetchone()[0]
            count=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_application_items_local').fetchone()[0]
        self.assertEqual((field,ver,count),('preferencia ficticia aprovada',2,1))

    def test_173_two_fields_atomic_with_incrementing_form_version(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture(multiple=True)
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.APPLIED_SYNTHETIC_ONLY)
        with self.pg.connect(DB) as con:
            rows=con.execute('select campo_sintetico,valor_sintetico from '
              'prumo_private.cfi01_f03_form_fields_local where '
              'concessionaria_id=%s and lead_id=%s order by campo_sintetico',
              (self.shop,self.lead)).fetchall()
            ver=con.execute('select versao_ficha from '
              'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
              (self.lead,)).fetchone()[0]
        self.assertEqual(len(rows),2)
        self.assertEqual(ver,3)

    def test_174_human_replay_is_audit_only(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.APPLIED_SYNTHETIC_ONLY)
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.ALREADY_APPLIED_AUDIT_ONLY)
        with self.pg.connect(DB) as con:
            versions=con.execute('select versao_ficha from '
              'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
              (self.lead,)).fetchone()[0]
        self.assertEqual(versions,2)

    def test_175_other_manager_cannot_claim_existing_application(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.APPLIED_SYNTHETIC_ONLY)
        stranger=self._new_ratification_manager()
        self.assertIs(self._human_apply(req,stranger).state,
                      ApplicationState.CONFLICT_REVIEW_REQUIRED)

    def test_176_unscoped_manager_denied(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,_=self._application_fixture()
        manager=self._new_ratification_manager(scoped=False)
        self.assertIs(self._human_apply(req,manager).state,ApplicationState.DENIED)

    def test_177_without_s1_authority_blocked(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        self.assertIs(self._human_apply(req,manager,s1=False).state,
                      ApplicationState.BLOCKED_S1)

    def test_178_pending_identity_blocks_all_fields(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture(multiple=True)
        self._pending_identity('+5511988887777')
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            total=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_fields_local '
              'where lead_id=%s',(self.lead,)).fetchone()[0]
        self.assertEqual(total,0)

    def test_179_stale_catalog_contract_no_form_write(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        with self.pg.connect(DB) as con:
            con.execute('update '
              'prumo_private.cfi01_f03_operational_field_contracts_local '
              'set max_chars=40 where concessionaria_id=%s',
              (self.shop,))
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.STALE_REVIEW_REQUIRED)

    def test_180_wrong_runtime_hmac_refused(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        self.assertIs(self._human_apply(req,manager,
            secret=b'wrong-S0-disposable-key-has-more-than-32-bytes').state,
            ApplicationState.STALE_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            total=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_fields_local '
              'where lead_id=%s',(self.lead,)).fetchone()[0]
        self.assertEqual(total,0)

    def test_181_existing_old_value_without_expected_hash_conflicts(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture(existing=True)
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.STALE_REVIEW_REQUIRED)

    def test_182_audit_ledgers_immutable(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.APPLIED_SYNTHETIC_ONLY)
        for statement in (
            'update prumo_private.cfi01_f03_form_application_local '
            'set evidencia_aprovacao_sha256=%s',
            'delete from prumo_private.cfi01_f03_form_application_items_local '
            'where campo_sintetico=%s'
        ):
            param=('b'*64,) if statement.startswith('update') else (
                'observacao_sintetica',)
            with self.assertRaises(self.pg.Error) as err:
                with self.pg.connect(DB) as con: con.execute(statement,param)
            self.assertEqual(err.exception.sqlstate,'42501')

    def test_183_authenticated_role_cannot_access_applications(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        self.assertIs(self._human_apply(req,manager).state,
                      ApplicationState.APPLIED_SYNTHETIC_ONLY)
        with self.pg.connect(DB) as con:
            with self.assertRaises(self.pg.Error):
                con.execute('set local role authenticated')
                con.execute('select * from '
                  'prumo_private.cfi01_f03_form_application_local')

    def test_184_same_human_competing_application_single_write(self):
        from concurrent.futures import ThreadPoolExecutor
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(lambda _:self._human_apply(req,manager).state,
                                   range(2)))
        self.assertCountEqual(outcomes,[
            ApplicationState.APPLIED_SYNTHETIC_ONLY,
            ApplicationState.ALREADY_APPLIED_AUDIT_ONLY])
        with self.pg.connect(DB) as con:
            ver=con.execute('select versao_ficha from '
              'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
              (self.lead,)).fetchone()[0]
        self.assertEqual(ver,2)

    def test_185_second_field_invalid_rolls_back_entire_batch(self):
        from backend.s0_f03_field_application_local import (
            ApplicationState,FieldCAS,HumanFieldRequest,
        )
        req,manager=self._application_fixture(multiple=True)
        # Retain original, valid, reserved proposal; make its second CAS
        # precondition impossible. The first field must not be inserted.
        first,second=req.fields
        bad=HumanFieldRequest(req.binding,req.version,req.request_ref,
            req.key_version,(first,FieldCAS(second.proposed,'f'*64)),
            req.decision,req.approval_evidence_sha256,req.idempotency_key)
        self.assertIs(self._human_apply(bad,manager).state,
                      ApplicationState.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_fields_local where lead_id=%s',
              (self.lead,)).fetchone()[0]
            audit=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_application_local where caso_id=%s',
              (self.case,)).fetchone()[0]
        self.assertEqual((count,audit),(0,0))


    def test_186_existing_field_updates_only_if_old_hash_matches(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,proposal_digest,
        )
        from backend.s0_f03_field_application_local import (
            FieldCAS,HumanDecision,HumanFieldRequest,_sha,ApplicationState,
        )
        from backend.s0_f03_version_reservation_local import (
            VersionVector,ReservationState,
        )
        store,_=self._prepare_cas()
        with self.pg.connect(DB) as con:
            con.execute('insert into prumo_private.cfi01_f03_form_fields_local '
                '(concessionaria_id,lead_id,campo_sintetico,valor_sintetico) '
                'values (%s,%s,%s,%s)',
                (self.shop,self.lead,'observacao_sintetica','antes'))
            con.execute('insert into '
                'prumo_private.cfi01_f03_operational_field_contracts_local '
                '(concessionaria_id,campo_sintetico,tipo_sintetico,max_chars) '
                'values (%s,%s,%s,%s)',
                (self.shop,'observacao_sintetica','TEXT_ONLY',48))
        proposed=ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'depois')
        digest=proposal_digest((proposed,))
        version=VersionVector(2,2,1,1,1)
        self.assertIs(self._reserve(store,version,sha=digest),
                      ReservationState.RESERVED_REVIEW_ONLY)
        approval=HumanFieldRequest(self.binding,version,'request-cas-0001',
                'test-key-v1',(FieldCAS(proposed,_sha('antes')),),
                HumanDecision.EXPLICIT_APPROVE_SYNTHETIC_FIELDS,
                'a'*64,'human-existing-cas-001')
        manager=self._new_ratification_manager()
        self.assertIs(self._human_apply(approval,manager).state,
                      ApplicationState.APPLIED_SYNTHETIC_ONLY)
        with self.pg.connect(DB) as con:
            row=con.execute('select valor_sintetico from '
                'prumo_private.cfi01_f03_form_fields_local '
                'where lead_id=%s and campo_sintetico=%s',
                (self.lead,'observacao_sintetica')).fetchone()[0]
            ver=con.execute('select versao_ficha from '
                'prumo_private.cfi01_f03_lead_versions_local where lead_id=%s',
                (self.lead,)).fetchone()[0]
            item=con.execute('select i.antigo_sha256,i.novo_sha256 from '
                'prumo_private.cfi01_f03_form_application_items_local i '
                'join prumo_private.cfi01_f03_form_application_local a '
                'on a.id=i.aplicacao_id '
                'where a.concessionaria_id=%s and a.lead_id=%s '
                'and i.campo_sintetico=%s',
                (self.shop,self.lead,'observacao_sintetica')).fetchone()
        self.assertEqual((row,ver),('depois',3))
        self.assertEqual(item,(_sha('antes'),_sha('depois')))

    def test_187_late_audit_sql_failure_rolls_back_all_field_changes(self):
        from backend.s0_f03_field_application_local import ApplicationState
        req,manager=self._application_fixture(multiple=True)
        # Deliberately fail AFTER both field writes and their version bumps.
        # A successful rollback must leave zero fields/audit and old version.
        with self.pg.connect(DB) as con:
            con.execute("""
              create function prumo_private.f03_fail_audit_test_local()
              returns trigger language plpgsql set search_path='' as $boom$
              begin
                raise exception 'E04_FORCED_AUDIT_FAILURE'
                  using errcode='23514';
              end $boom$;
              create trigger f03_fail_audit_test
              before insert on prumo_private.cfi01_f03_form_application_local
              for each row execute function prumo_private.f03_fail_audit_test_local();
            """)
        try:
            self.assertIs(self._human_apply(req,manager).state,
                          ApplicationState.UNAVAILABLE)
        finally:
            with self.pg.connect(DB) as con:
                con.execute('drop trigger if exists f03_fail_audit_test on '
                    'prumo_private.cfi01_f03_form_application_local')
                con.execute('drop function if exists '
                    'prumo_private.f03_fail_audit_test_local()')
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_fields_local where '
              'concessionaria_id=%s and lead_id=%s',
              (self.shop,self.lead)).fetchone()[0]
            ver=con.execute('select versao_ficha from '
              'prumo_private.cfi01_f03_lead_versions_local where '
              'concessionaria_id=%s and lead_id=%s',
              (self.shop,self.lead)).fetchone()[0]
            receipts=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_application_local '
              'where concessionaria_id=%s',(self.shop,)).fetchone()[0]
        self.assertEqual((count,ver,receipts),(0,1,0))


    def _second_identity_candidate(self,*,phone='+551188887777',
                                   alias=None,shop=None):
        other=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.leads_loja '
                        '(id,concessionaria_id,telefone_cliente_normalizado) '
                        'values (%s,%s,%s)',
                        (other,shop or self.shop,phone))
            if alias is not None:
                con.execute('insert into prumo_private.aliases_identidade_s0 '
                            '(concessionaria_id,lead_id,numero_sintetico,origem,'
                            'mobile_confirmado_sintetico) '
                            "values (%s,%s,%s,'CANAL_SINTETICO',true)",
                            (shop or self.shop,other,alias))
        return other

    def test_188_reservation_refuses_second_lead_br_variant_without_pending(self):
        from backend.s0_f03_version_reservation_local import ReservationState
        store,vector=self._prepare_cas()
        self._second_identity_candidate()
        self.assertIs(self._reserve(store,vector),
                      ReservationState.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_reservations_local '
                'where evento_fechamento_id=%s',(self.event,)).fetchone()[0]
        self.assertEqual(count,0)

    def test_189_reservation_refuses_other_lead_alias_variant_without_pending(self):
        from backend.s0_f03_version_reservation_local import ReservationState
        store,vector=self._prepare_cas()
        self._second_identity_candidate(phone='+5581999989999',
                                        alias='+551188887777')
        self.assertIs(self._reserve(store,vector),
                      ReservationState.CONFLICT_REVIEW_REQUIRED)

    def test_190_operational_contract_detects_new_candidate_after_reservation(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,OperationalState,
        )
        proposals=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'x'),)
        vector,digest=self._operational_fixture(proposals)
        self._second_identity_candidate()
        self.assertIs(self._operational_check(proposals,vector,digest),
                      OperationalState.CONFLICT_REVIEW_REQUIRED)

    def test_191_application_cannot_write_with_second_candidate_phone(self):
        from backend.s0_f03_field_application_local import ApplicationState
        request,manager=self._application_fixture()
        self._second_identity_candidate()
        self.assertIs(self._human_apply(request,manager).state,
                      ApplicationState.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_form_fields_local '
                'where lead_id=%s',(self.lead,)).fetchone()[0]
        self.assertEqual(count,0)

    def test_192_other_shop_matching_phone_does_not_block_local_human(self):
        from backend.s0_f03_field_application_local import ApplicationState
        request,manager=self._application_fixture()
        other_shop=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into public.concessionarias(id,nome_operacional) '
                        "values (%s,'UNRELATED TEST SHOP')",(other_shop,))
        self._second_identity_candidate(phone='+5511988887777',shop=other_shop)
        self.assertIs(self._human_apply(request,manager).state,
                      ApplicationState.APPLIED_SYNTHETIC_ONLY)

    def test_193_own_alias_matching_other_lead_primary_blocks_reservation(self):
        from backend.s0_f03_version_reservation_local import ReservationState
        self._insert_alias(number='+5511999981111')
        store,vector=self._prepare_cas()
        self._second_identity_candidate(phone='+5511999981111')
        self.assertIs(self._reserve(store,vector),
                      ReservationState.CONFLICT_REVIEW_REQUIRED)

    def test_194_candidate_writer_waits_behind_scope_lock_before_cas(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        from backend.s0_f03_field_application_local import ApplicationState
        request,manager=self._application_fixture()
        started=Event()
        with self.pg.connect(DB) as writer:
            writer.execute('insert into public.leads_loja '
                '(id,concessionaria_id,telefone_cliente_normalizado) '
                'values (%s,%s,%s)',
                (uuid.uuid4(),self.shop,'+551188887777'))
            with ThreadPoolExecutor(max_workers=1) as pool:
                def verify():
                    started.set()
                    return self._human_apply(request,manager).state
                result=pool.submit(verify)
                self.assertTrue(started.wait(2))
                writer.commit()
                self.assertIs(result.result(timeout=7),
                              ApplicationState.CONFLICT_REVIEW_REQUIRED)
        with self.pg.connect(DB) as con:
            count=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_form_fields_local '
                'where lead_id=%s',(self.lead,)).fetchone()[0]
        self.assertEqual(count,0)

    def test_195_own_alias_without_second_lead_remains_eligible(self):
        from backend.s0_f03_version_reservation_local import ReservationState
        self._insert_alias(number='+551188887777')
        store,vector=self._prepare_cas()
        self.assertIs(self._reserve(store,vector),
                      ReservationState.RESERVED_REVIEW_ONLY)


    def _s2_recheck_fixture(self):
        from backend.s0_f03_operational_contracts_local import (
            ProposedField,FieldKind,S0F03LocalOperationalContractsStore,
            S0F03LocalOperationalContractsBridge,
        )
        from backend.s0_f03_crossfront_contract_local import (
            S0F03CrossFrontLocalBridge,
        )
        from backend.s0_f03_bound_content_seal_local import (
            S0F03LocalBoundContentBridge,S0F03LocalBoundContentStore,
        )
        from backend.s0_f03_history_seal_local import SealState,SealResult
        fields=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,
                              'preferencia ficticia'),)
        vector,digest=self._operational_fixture(fields)
        with self.pg.connect(DB) as con:
            sha=con.execute('select metadados_sha256 from '
                'prumo_private.cfi01_f03_content_proofs_local where '
                'concessionaria_id=%s and evento_fechamento_id=%s',
                (self.shop,self.event)).fetchone()[0]
        # E04 synthetic S0 authority fixture only. Actual *physical* HMAC
        # recomputation, SQL receipt, versions and scope remain unmocked.
        class S0TestHistoryAuthority:
            def verify(self,authorization,binding):
                if authorization!='Bearer PINNED_S2_LOCAL_E04':
                    return SealResult(SealState.DENIED)
                return SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)
        content=object.__new__(S0F03LocalBoundContentBridge)
        content._store=S0F03LocalBoundContentStore(DB)
        content._history=S0TestHistoryAuthority()
        contract=S0F03LocalOperationalContractsBridge(
            content,S0F03LocalOperationalContractsStore(DB))
        gate=S0F03CrossFrontLocalBridge(contract)
        versions=dict(case=vector.case,cycle=1,form=vector.form,
                      catalog=vector.catalog,assignment=vector.assignment,
                      identity=vector.identity)
        scope=dict(authenticated=True,authorized=True,tenantAllowed=True,
                   storeId=str(self.shop),personId=str(self.lead),
                   caseId=str(self.case),closureId=str(self.event),
                   requestId='request-cas-0001')
        item=fields[0]
        js=dict(
          scope=scope,
          cutoff=dict(storeId=str(self.shop),personId=str(self.lead),
            closureId=str(self.event),s0ClosureVerified=True,
            historyComplete=True,snapshotRef=sha,watermark=2,
            expectedVersions=versions,
            sources=[dict(id=str(self.message),storeId=str(self.shop),
              personId=str(self.lead),caseId=str(self.case),
              sequence=1,available=True,s0Verified=True,
              claims=[dict(code=item.field_key,value=item.value,explicit=True)])]),
          proposal=dict(proposalRef='synthetic-proposal-01',
            fields=[dict(code=item.field_key,value=item.value,
                         sourceId=str(self.message))],
            conflicts=[],advisory=None),
          catalog=[dict(code=item.field_key,essential=True)],
          current=dict(versions=versions.copy(),
            closureStillAuthorized=True,assignmentAuthorized=True,
            personScopeVerified=True),
          prior=None)
        return gate,fields,vector,js

    def _s2_evaluate_real_js(self,payload):
        import subprocess,json
        path=os.environ['PRUMO_S2_F03_GATE_PATH']
        node_script=("import {pathToFileURL} from 'node:url'; "
                     "import {readFileSync} from 'node:fs'; "
                     "const m=await import(pathToFileURL(process.argv[1]).href); "
                     "const f=JSON.parse(readFileSync(0,'utf8')); "
                     "console.log(JSON.stringify(m.evaluateF03CommitCandidate(f)))")
        result=subprocess.run(['node','--input-type=module','-e',
                               node_script,path],
                   input=json.dumps(payload,ensure_ascii=False),
                   text=True,capture_output=True,timeout=12,check=True)
        return json.loads(result.stdout)

    def _s2_review(self,gate,fields,vector,output,authorization='Bearer PINNED_S2_LOCAL_E04'):
        return gate.inspect(authorization,self.binding,'test-key-v1',
                            b'fixture-only-content-seal-key-more-than-32-bytes',
                            vector,'request-cas-0001',fields,output).state

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_196_real_js_gate_s0_review_does_not_write(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,input_js=self._s2_recheck_fixture()
        output=self._s2_evaluate_real_js(input_js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            form=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_fields_local where lead_id=%s',
              (self.lead,)).fetchone()[0]
            applied=con.execute('select count(*) from '
              'prumo_private.cfi01_f03_form_application_local where lead_id=%s',
              (self.lead,)).fetchone()[0]
        self.assertEqual((form,applied),(0,0))

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_197_stale_js_response_cannot_enter_physical_review(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,js=self._s2_recheck_fixture()
        js['current']['versions']['form']+=1
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output,{'status':'STALE'})
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.DENIED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_198_forged_field_codes_cannot_bypass_s0(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,js=self._s2_recheck_fixture()
        output=self._s2_evaluate_real_js(js)
        output['fieldCodes']=['identidade_sintetica']
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.DENIED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_199_forged_snapshot_digest_rejected_by_s0(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,js=self._s2_recheck_fixture()
        output=self._s2_evaluate_real_js(js)
        output['snapshotRef']='f'*64
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.STALE_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_200_s0_catalog_version_stale_after_js_proposal(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,js=self._s2_recheck_fixture()
        output=self._s2_evaluate_real_js(js)
        with self.pg.connect(DB) as con:
            con.execute('update '
              'prumo_private.cfi01_f03_operational_field_contracts_local '
              'set max_chars=64 where concessionaria_id=%s',
              (self.shop,))
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.STALE_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_201_s0_hmac_fails_when_old_history_changes_after_js(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,js=self._s2_recheck_fixture()
        output=self._s2_evaluate_real_js(js)
        with self.pg.connect(DB) as con:
            con.execute('update public.mensagens set conteudo_sintetico=%s '
                        'where id=%s',
                        ('mudanca no caso antigo sem prova',self.old_message))
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.STALE_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_202_new_s0_duplicate_lead_after_js_forces_review(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,js=self._s2_recheck_fixture()
        output=self._s2_evaluate_real_js(js)
        self._second_identity_candidate()
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.CONFLICT_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'needs pinned S2 JS gate checked out in the CI')
    def test_203_s2_gate_false_authorization_never_enters_s0(self):
        from backend.s0_f03_crossfront_contract_local import CrossFrontState
        gate,fields,vector,js=self._s2_recheck_fixture()
        js['scope']['authenticated']=False
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output,{'status':'DENIED'})
        self.assertIs(self._s2_review(gate,fields,vector,output),
                      CrossFrontState.DENIED)


    def _s2_provenance_fixture(self,*,text='observacao_sintetica=preferencia ficticia',
                               older_text=None):
        from backend.s0_f03_crossfront_evidence_local import S0F03LocalEvidenceReviewBridge
        with self.pg.connect(DB) as con:
            con.execute('update public.mensagens set conteudo_sintetico=%s '
                        'where id=%s',(text,self.message))
            if older_text is not None:
                con.execute('update public.mensagens set conteudo_sintetico=%s '
                            'where id=%s',(older_text,self.old_message))
        base,fields,vector,js=self._s2_recheck_fixture()
        return S0F03LocalEvidenceReviewBridge(base),fields,vector,js

    def _s2_evidence_review(self,gate,fields,vector,output,proposal):
        return gate.inspect('Bearer PINNED_S2_LOCAL_E04',self.binding,'test-key-v1',
             b'fixture-only-content-seal-key-more-than-32-bytes',
             vector,'request-cas-0001',fields,output,proposal).state

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_204_s2_verified_literal_from_same_case_yields_s0_review_only(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture()
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(
            gate,fields,vector,output,js['proposal']),
            EvidenceState.S0_EVIDENCE_REVIEW_ONLY)
        with self.pg.connect(DB) as con:
            changed=con.execute('select count(*) from '
                'prumo_private.cfi01_f03_form_fields_local '
                'where lead_id=%s',(self.lead,)).fetchone()[0]
        self.assertEqual(changed,0)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_205_js_claims_value_s0_does_not_contain(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture(text='somente fixture')
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.SOURCE_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_206_s2_hidden_earlier_conflict_detected_physically(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture(
            older_text='observacao_sintetica=outra preferencia')
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.CONFLICT_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_207_fake_source_id_rejected_even_if_js_accepts(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture()
        alien=str(uuid.uuid4())
        js['cutoff']['sources'][0]['id']=alien
        js['proposal']['fields'][0]['sourceId']=alien
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.SOURCE_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_208_value_in_historical_case_authorized_with_same_lead(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture(
            text='registro de outro campo',
            older_text='observacao_sintetica=preferencia ficticia')
        js['cutoff']['sources'][0]['id']=str(self.old_message)
        js['cutoff']['sources'][0]['caseId']=str(self.old_case)
        js['proposal']['fields'][0]['sourceId']=str(self.old_message)
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.S0_EVIDENCE_REVIEW_ONLY)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_209_s2_forged_claim_with_matching_s2_source_rejected_by_s0(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture()
        js['proposal']['fields'][0]['value']='alegacao inventada'
        js['cutoff']['sources'][0]['claims'][0]['value']='alegacao inventada'
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.DENIED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_210_source_changed_after_s2_response_fails_live_hmac(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture()
        output=self._s2_evaluate_real_js(js)
        with self.pg.connect(DB) as con:
            con.execute('update public.mensagens set conteudo_sintetico=%s '
                        'where id=%s',
                        ('observacao_sintetica=preferencia alterada',self.message))
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.STALE_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_211_s2_foreign_code_and_extra_authority_rejected(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture()
        output=self._s2_evaluate_real_js(js)
        forged={**js['proposal'],'approvedByAI':True}
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,forged),
                      EvidenceState.DENIED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_212_natural_language_unstructured_text_not_accepted_as_fact(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture(
            text='O cliente quer preferencia ficticia na observacao_sintetica')
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.SOURCE_REVIEW_REQUIRED)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_213_two_identical_claims_across_cases_are_not_conflict(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture(
            older_text='observacao_sintetica=preferencia ficticia')
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.S0_EVIDENCE_REVIEW_ONLY)


    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_214_old_case_source_preserves_original_human_closure_receipt(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState,S0F03LocalEvidenceReviewBridge
        from backend.s0_human_closure_event_local import _MESSAGES,_fingerprint
        # Modify ONLY a prior case. The current closed human conversation is
        # byte-for-byte identical to the moment of S0 closure certification.
        with self.pg.connect(DB) as con:
            con.execute('update public.mensagens set conteudo_sintetico=%s '
                        'where id=%s',
                        ('observacao_sintetica=preferencia ficticia',self.old_message))
            current=con.execute(_MESSAGES,(self.shop,self.case)).fetchall()
            self.assertEqual(_fingerprint(current),self.receipt.snapshot_sha256)
        base,fields,vector,js=self._s2_recheck_fixture()
        js['cutoff']['sources'][0]['id']=str(self.old_message)
        js['cutoff']['sources'][0]['caseId']=str(self.old_case)
        js['proposal']['fields'][0]['sourceId']=str(self.old_message)
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        state=self._s2_evidence_review(
            S0F03LocalEvidenceReviewBridge(base),fields,vector,
            output,js['proposal'])
        self.assertIs(state,EvidenceState.S0_EVIDENCE_REVIEW_ONLY)

    @unittest.skipUnless(os.environ.get('PRUMO_S2_F03_GATE_PATH'),
                         'requires pinned S2 JS in CI')
    def test_215_s2_references_after_cutoff_message_refused(self):
        from backend.s0_f03_crossfront_evidence_local import EvidenceState
        gate,fields,vector,js=self._s2_provenance_fixture()
        after=uuid.uuid4()
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._message(cur,after,self.old_conversation,self.old_case)
                cur.execute('update public.mensagens set conteudo_sintetico=%s '
                            'where id=%s',
                            ('observacao_sintetica=preferencia ficticia',after))
                created=cur.execute('select criada_em from public.mensagens '
                                    'where id=%s',(after,)).fetchone()[0]
                cutoff=cur.execute('select registrado_em from '
                                   'prumo_private.cfi01_human_closure_events_local '
                                   'where id=%s',(self.event,)).fetchone()[0]
                self.assertGreater(created,cutoff)
        js['cutoff']['sources'][0]['id']=str(after)
        js['cutoff']['sources'][0]['caseId']=str(self.old_case)
        js['proposal']['fields'][0]['sourceId']=str(after)
        # S2 can falsely label a post-cutoff message with an old sequence;
        # S0 derives cutoff and source membership from its own PostgreSQL.
        output=self._s2_evaluate_real_js(js)
        self.assertEqual(output['status'],'S0_RECHECK_ONLY')
        self.assertIs(self._s2_evidence_review(gate,fields,vector,output,js['proposal']),
                      EvidenceState.SOURCE_REVIEW_REQUIRED)

if __name__=='__main__':
    unittest.main()
