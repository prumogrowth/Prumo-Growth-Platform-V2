"""Physical S0/S1 SQL tests. Only disposable local PostgreSQL 17 in CI.

GoTrue identity is a trusted fake Principal here, not a live GoTrue token.
Do not run this module against hosted Supabase. No business status mutation.
"""
from __future__ import annotations

import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from backend.identity_boundary import Principal
from backend.s0_human_closure_event_local import (
    ClosureRequest, ClosureState, S0LocalClosureStore, capture_human_closure_local)
from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority

DB = os.environ.get("PRUMO_TEST_DATABASE_URL", "")
URI = urlsplit(DB)
DISPOSABLE = (URI.scheme in ("postgresql", "postgres")
              and URI.hostname in ("127.0.0.1","localhost","::1")
              and URI.path == "/prumo_s0_test_cfi01"
              and not URI.query and not URI.fragment)


class FixtureIdentity:
    def __init__(self, actor, session):
        self.principal = Principal(actor, session)

    def verify(self, _authorization):
        return self.principal


@unittest.skipUnless(DISPOSABLE, "requires LOCAL prumo_s0_test_cfi01 PostgreSQL database")
class PostgresPhysicalIntegration(unittest.TestCase):
    def setUp(self):
        import psycopg
        self.pg = psycopg
        self.actor = uuid.uuid4()
        self.session = uuid.uuid4()
        self.shop = uuid.uuid4()
        self.lead = uuid.uuid4()
        self.cycle = uuid.uuid4()
        self.case = uuid.uuid4()
        self.assignment = uuid.uuid4()
        self.channel = uuid.uuid4()
        self.conversation = uuid.uuid4()
        self.message = uuid.uuid4()
        self.identity = FixtureIdentity(self.actor, self.session)
        self.s1 = S0S1LocalTeamAuthority()
        self.store = S0LocalClosureStore(DB)
        with psycopg.connect(DB) as con:
            with con.cursor() as cur:
                cur.execute("insert into auth.users(id) values (%s)", (self.actor,))
                cur.execute("insert into public.atores(id) values (%s)", (self.actor,))
                cur.execute("insert into auth.sessions(id,user_id) values (%s,%s)",
                            (self.session, self.actor))
                cur.execute("insert into public.concessionarias(id,nome_operacional) values (%s,'LAB ONLY')",
                            (self.shop,))
                cur.execute("""insert into public.vinculos_papel_escopo(
                    ator_id,concessionaria_id,papel) values (%s,%s,'operador')""",
                            (self.actor,self.shop))
                cur.execute("""insert into public.leads_loja(
                    id,concessionaria_id,telefone_cliente_normalizado)
                    values (%s,%s,'+5511999999999')""",(self.lead,self.shop))
                cur.execute("""insert into public.ciclos_comerciais(
                    id,concessionaria_id,lead_id,status_comercial,versao_registro)
                    values (%s,%s,%s,'em atendimento pelo operador',1)""",
                            (self.cycle,self.shop,self.lead))
                cur.execute("""insert into public.casos_humanos(
                    id,concessionaria_id,lead_id,ciclo_id) values (%s,%s,%s,%s)""",
                            (self.case,self.shop,self.lead,self.cycle))
                cur.execute("""insert into public.atribuicoes_humanas(
                    id,concessionaria_id,caso_id,operador_id) values (%s,%s,%s,%s)""",
                            (self.assignment,self.shop,self.case,self.actor))
                cur.execute("""insert into public.equipe_prumo_s1(ator_id,estado)
                               values (%s,'ativo')""",(self.actor,))
                cur.execute("""insert into public.canais_loja(
                    id,concessionaria_id,identificador_emissor)
                    values (%s,%s,%s)""",(self.channel,self.shop,str(self.channel)))
                cur.execute("""insert into public.conversas(
                    id,concessionaria_id,lead_id,canal_id,caso_id)
                    values (%s,%s,%s,%s,%s)""",
                            (self.conversation,self.shop,self.lead,self.channel,self.case))
                self._add_message(cur, self.message)

    def _add_message(self, cursor, msg_id):
        cursor.execute("""insert into public.mensagens(
          id,concessionaria_id,conversa_id,canal_id,caso_id,
          direcao,origem,conteudo_sintetico,id_externo)
          values (%s,%s,%s,%s,%s,'entrada','simulado','mensagem sintetica',%s)""",
          (msg_id,self.shop,self.conversation,self.channel,self.case,str(msg_id)))

    def capture(self, key="closure-lab-key"):
        return capture_human_closure_local(
            "Bearer synthetic-identity-only",
            ClosureRequest(str(self.case),1,key),
            identity=self.identity,store=self.store,s1=self.s1)

    def _count(self):
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                cur.execute("""select count(*) from prumo_private.cfi01_human_closure_events_local
                    where concessionaria_id=%s and caso_id=%s""",(self.shop,self.case))
                return cur.fetchone()[0]

    def test_01_record_is_real_private_sql_and_idempotent(self):
        first=self.capture()
        self.assertIs(first.state,ClosureState.CAPTURED_LOCAL_ONLY)
        self.assertTrue(uuid.UUID(first.closure_event_ref))
        second=self.capture()
        self.assertIs(second.state,ClosureState.ALREADY_CAPTURED)
        self.assertEqual(second.closure_event_ref,first.closure_event_ref)
        self.assertEqual(self._count(),1)

    def test_02_new_inbound_replay_is_stale(self):
        self.assertIs(self.capture().state,ClosureState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._add_message(cur,uuid.uuid4())
        self.assertIs(self.capture().state,ClosureState.STALE)
        self.assertEqual(self._count(),1)

    def test_03_s1_account_suspended_blocks_capture(self):
        with self.pg.connect(DB) as con:
            con.execute("""update public.equipe_prumo_s1 set estado='suspenso'
                           where ator_id=%s""",(self.actor,))
        self.assertIs(self.capture().state,ClosureState.BLOCKED_S1)
        self.assertEqual(self._count(),0)

    def test_04_session_revoked_blocks_capture(self):
        with self.pg.connect(DB) as con:
            con.execute("delete from auth.sessions where id=%s",(self.session,))
        self.assertIs(self.capture().state,ClosureState.DENIED)
        self.assertEqual(self._count(),0)

    def test_05_store_grant_revoked_blocks_capture(self):
        with self.pg.connect(DB) as con:
            con.execute("""delete from public.vinculos_papel_escopo
                where ator_id=%s and concessionaria_id=%s""",(self.actor,self.shop))
        self.assertIs(self.capture().state,ClosureState.DENIED)
        self.assertEqual(self._count(),0)

    def test_06_reassignment_invalidates_request(self):
        with self.pg.connect(DB) as con:
            con.execute("""update public.atribuicoes_humanas
              set encerrada_em=greatest(atribuida_em,statement_timestamp())
              where id=%s""",(self.assignment,))
        self.assertIs(self.capture().state,ClosureState.DENIED)
        self.assertEqual(self._count(),0)

    def test_07_second_different_key_same_snapshot_not_duplicated(self):
        self.assertIs(self.capture('first-key-001').state,ClosureState.CAPTURED_LOCAL_ONLY)
        self.assertIs(self.capture('second-key-001').state,ClosureState.DUPLICATE_SNAPSHOT)
        self.assertEqual(self._count(),1)

    def test_08_two_real_sessions_same_key_exactly_one_event(self):
        barrier=threading.Barrier(2)
        def concurrent():
            barrier.wait(timeout=5)
            return self.capture('same-key-concurrent').state
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(concurrent) for _ in range(2)]
            outcomes={f.result(timeout=15) for f in futures}
        self.assertEqual(outcomes,{
            ClosureState.CAPTURED_LOCAL_ONLY,
            ClosureState.ALREADY_CAPTURED})
        self.assertEqual(self._count(),1)

    def test_09_cycle_version_stale_without_mutation(self):
        with self.pg.connect(DB) as con:
            con.execute("update public.ciclos_comerciais set versao_registro=2 where id=%s",
                        (self.cycle,))
        self.assertIs(self.capture().state,ClosureState.STALE)
        self.assertEqual(self._count(),0)

    def test_10_no_accidental_business_status_change(self):
        self.assertIs(self.capture().state,ClosureState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            value=con.execute("select status_comercial from public.ciclos_comerciais where id=%s",
                              (self.cycle,)).fetchone()[0]
        self.assertEqual(value,"em atendimento pelo operador")


if __name__ == "__main__":
    unittest.main()
