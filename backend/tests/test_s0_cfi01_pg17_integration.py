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
from backend.s0_cfi01_authenticated_commands_local import (
    S0CFI01AuthenticatedCommandsLocal, CommandState,
)
from backend.tests.test_s0_cfi01_authenticated_commands_local import (
    token as synthetic_token, Opener as SyntheticGoTrueHTTP,
)
from backend.s0_human_closure_recheck_local import (
    RecheckRequest, RecheckState, S0LocalClosureRecheck,
    recheck_human_closure_local,
)

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

    def recheck(self, closure_event_ref, key="closure-lab-key",
                identity=None, cycle_version=1):
        return recheck_human_closure_local(
            "Bearer synthetic-identity-only",
            RecheckRequest(str(self.case),closure_event_ref,cycle_version,key),
            identity=identity if identity is not None else self.identity,
            store=S0LocalClosureRecheck(DB),s1=self.s1)

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

    def test_11_inbound_commits_before_snapshot_after_parent_lock(self):
        # A concurrent writer first holds the conversation row. Capture
        # must wait, then observe the new inbound after writer commits.
        with self.pg.connect(DB) as con:
            con.execute("""select id from public.conversas
                where id=%s for update""",(self.conversation,))
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(self.capture,"new-inbound-lock-race")
                # Ensure capture has reached the physical blocking point
                # without claiming deterministic scheduler timestamps.
                with self.assertRaises(TimeoutError):
                    future.result(timeout=0.15)
                with con.cursor() as cur:
                    self._add_message(cur,uuid.uuid4())
                con.commit()
                result=future.result(timeout=10)
        self.assertIs(result.state,ClosureState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            count=con.execute("""select quantidade_mensagens from
                prumo_private.cfi01_human_closure_events_local
                where concessionaria_id=%s and caso_id=%s""",
                (self.shop,self.case)).fetchone()[0]
        self.assertEqual(count,2)

    def test_12_team_suspend_transaction_wins_before_case_capture(self):
        with self.pg.connect(DB) as con:
            con.execute("""update public.equipe_prumo_s1
                set estado='suspenso' where ator_id=%s""",(self.actor,))
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(self.capture,"s1-revocation-race")
                with self.assertRaises(TimeoutError):
                    future.result(timeout=0.15)
                con.commit()
                result=future.result(timeout=10)
        self.assertIs(result.state,ClosureState.BLOCKED_S1)
        self.assertEqual(self._count(),0)


    def test_13_recheck_success_only_for_same_s0_receipt(self):
        first=self.capture()
        self.assertIs(first.state,ClosureState.CAPTURED_LOCAL_ONLY)
        review=self.recheck(first.closure_event_ref)
        self.assertIs(review.state,RecheckState.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertFalse(hasattr(review,"applied"))
        self.assertEqual(self._count(),1)

    def test_14_missing_receipt_is_denied(self):
        self.assertIs(self.recheck(str(uuid.uuid4())).state,RecheckState.DENIED)

    def test_15_new_message_after_receipt_is_stale(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._add_message(cur,uuid.uuid4())
        self.assertIs(self.recheck(receipt).state,RecheckState.STALE)

    def test_16_edited_message_after_receipt_is_stale(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("""update public.mensagens
               set conteudo_sintetico='conteudo editado' where id=%s""",
               (self.message,))
        self.assertIs(self.recheck(receipt).state,RecheckState.STALE)

    def test_17_s1_suspension_after_receipt_blocks_recheck(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",
                        (self.actor,))
        self.assertIs(self.recheck(receipt).state,RecheckState.BLOCKED_S1)

    def test_18_session_revoked_after_receipt_denies_recheck(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("delete from auth.sessions where id=%s",(self.session,))
        self.assertIs(self.recheck(receipt).state,RecheckState.DENIED)

    def test_19_reassignment_after_receipt_denies_recheck(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("""update public.atribuicoes_humanas
              set encerrada_em=greatest(atribuida_em,statement_timestamp())
              where id=%s""",(self.assignment,))
        self.assertIs(self.recheck(receipt).state,RecheckState.DENIED)

    def test_20_store_grant_revoked_after_receipt_denies_recheck(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("""delete from public.vinculos_papel_escopo
             where ator_id=%s and concessionaria_id=%s""",(self.actor,self.shop))
        self.assertIs(self.recheck(receipt).state,RecheckState.DENIED)

    def test_21_different_idempotency_key_cannot_reuse_receipt(self):
        receipt=self.capture().closure_event_ref
        self.assertIs(self.recheck(receipt,key="different-key-abc").state,
                      RecheckState.DENIED)

    def test_22_new_session_cannot_reuse_original_receipt(self):
        receipt=self.capture().closure_event_ref
        newer=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute("insert into auth.sessions(id,user_id) values (%s,%s)",
                        (newer,self.actor))
        self.assertIs(self.recheck(receipt,identity=FixtureIdentity(self.actor,newer)).state,
                      RecheckState.DENIED)

    def test_23_cycle_version_changed_after_receipt_is_stale(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("update public.ciclos_comerciais set versao_registro=2 where id=%s",
                        (self.cycle,))
        self.assertIs(self.recheck(receipt).state,RecheckState.STALE)

    def test_24_new_inbound_commit_while_recheck_waits_marks_stale(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("select id from public.conversas where id=%s for update",
                        (self.conversation,))
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(self.recheck,receipt)
                with self.assertRaises(TimeoutError):
                    future.result(timeout=0.15)
                with con.cursor() as cur:
                    self._add_message(cur,uuid.uuid4())
                con.commit()
                review=future.result(timeout=10)
        self.assertIs(review.state,RecheckState.STALE)

    def test_25_status_changed_after_receipt_is_denied(self):
        receipt=self.capture().closure_event_ref
        with self.pg.connect(DB) as con:
            con.execute("""update public.ciclos_comerciais
                set status_comercial='cadastro enviado ao banco'
                where id=%s""",(self.cycle,))
        self.assertIs(self.recheck(receipt).state,RecheckState.DENIED)

    def test_26_wrong_cycle_expectation_is_stale(self):
        receipt=self.capture().closure_event_ref
        self.assertIs(self.recheck(receipt,cycle_version=2).state,RecheckState.STALE)


    def _local_gateway(self):
        # Actual SupabaseGoTrueVerifier network contract with SYNTHETIC HTTP
        # responder; full physical S0/S1 database queries remain real PG17.
        return S0CFI01AuthenticatedCommandsLocal(
            'https://auth.example.invalid','test-publishable-key',DB,
            opener=SyntheticGoTrueHTTP(actor=self.actor))

    def _gateway_payload(self):
        return dict(case_ref=str(self.case), expected_cycle_version=1,
                    idempotency_key='ci-gotrue-wire-key')

    def test_27_gotrue_verifier_code_and_real_pg_capture_recheck(self):
        gateway=self._local_gateway()
        bearer=synthetic_token(self.actor,self.session)
        capture=gateway.execute(bearer,'capture_human_closure',self._gateway_payload())
        self.assertEqual(capture.state,CommandState.CAPTURED_LOCAL_ONLY)
        self.assertEqual(self._count(),1)
        outcome=gateway.execute(bearer,'recheck_human_closure',
            {**self._gateway_payload(),'closure_event_ref':capture.closure_event_ref})
        self.assertEqual(outcome.state,CommandState.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertIsNone(outcome.closure_event_ref)

    def test_28_rogue_browser_actor_rejected_before_physical_writes(self):
        g=self._local_gateway()
        outcome=g.execute(synthetic_token(self.actor,self.session),
            'capture_human_closure',{**self._gateway_payload(),'actor_id':str(uuid.uuid4())})
        self.assertEqual(outcome.state,CommandState.INPUT_REJECTED)
        self.assertEqual(self._count(),0)

    def test_29_expired_local_session_revoked_despite_gotrue_http_success(self):
        g=self._local_gateway()
        with self.pg.connect(DB) as con:
            con.execute('delete from auth.sessions where id=%s',(self.session,))
        x=g.execute(synthetic_token(self.actor,self.session),
            'capture_human_closure',self._gateway_payload())
        self.assertEqual(x.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_30_s1_suspended_blocks_authenticated_command(self):
        g=self._local_gateway()
        with self.pg.connect(DB) as con:
            con.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",
                        (self.actor,))
        x=g.execute(synthetic_token(self.actor,self.session),
                    'capture_human_closure',self._gateway_payload())
        self.assertEqual(x.state,CommandState.BLOCKED_S1)
        self.assertEqual(self._count(),0)

    def test_31_gotrue_sub_mismatch_denied_before_sql(self):
        g=self._local_gateway()
        x=g.execute(synthetic_token(uuid.uuid4(),self.session),
            'capture_human_closure',self._gateway_payload())
        self.assertEqual(x.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_32_gotrue_http_recheck_fails_after_new_inbound(self):
        g=self._local_gateway()
        bearer=synthetic_token(self.actor,self.session)
        capture=g.execute(bearer,'capture_human_closure',self._gateway_payload())
        self.assertEqual(capture.state,CommandState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._add_message(cur,uuid.uuid4())
        out=g.execute(bearer,'recheck_human_closure',
           {**self._gateway_payload(),'closure_event_ref':capture.closure_event_ref})
        self.assertEqual(out.state,CommandState.STALE)
        self.assertEqual(self._count(),1)


if __name__ == "__main__":
    unittest.main()
