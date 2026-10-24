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

if __name__=='__main__':
    unittest.main()
