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
from backend.s0_cfi01_signed_prerequisite_local import (
    S0CFI01RestrictedSignedPrerequisiteLocal, SignedState,
)
from backend.s0_cfi01_signed_commands_local import S0CFI01SignedCommandsLocal
from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal, _ATOMIC_SQL
from backend.s0_cfi01_f03_receipt_bridge_local import (
    S0CFI01F03ReceiptBridgeLocal, S0F03BridgeState,
    S0F03BoundReceiptLocal, UNRATIFIED_F03_INPUTS,
)
import hmac
import hashlib
from backend.tests.test_s0_cfi01_authenticated_commands_local import (
    token as synthetic_token, Opener as SyntheticGoTrueHTTP,
)
from backend.tests.cfi01_signed_http_auth_fixture import (
    mock_signed_auth_server, make_signed_token,
)
import time
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


    def test_33_signed_loopback_http_auth_real_pg_capture_and_recheck(self):
        with mock_signed_auth_server() as url:
            g=S0CFI01AuthenticatedCommandsLocal(url,'test-public-key',DB)
            auth=make_signed_token(self.actor,self.session)
            cap=g.execute(auth,'capture_human_closure',self._gateway_payload())
            self.assertIs(cap.state,CommandState.CAPTURED_LOCAL_ONLY)
            check=g.execute(auth,'recheck_human_closure',
                {**self._gateway_payload(),'closure_event_ref':cap.closure_event_ref})
        self.assertIs(check.state,CommandState.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertEqual(self._count(),1)

    def test_34_tampered_signed_payload_is_denied_before_pg_insert(self):
        with mock_signed_auth_server() as url:
            g=S0CFI01AuthenticatedCommandsLocal(url,'test-public-key',DB)
            good=make_signed_token(self.actor,self.session)
            parts=good.split('.')
            # Keep original signature, change the user payload.
            tampered=parts[0]+'.'+parts[1][:-1]+('A' if parts[1][-1]!='A' else 'B')+'.'+parts[2]
            x=g.execute(tampered,'capture_human_closure',self._gateway_payload())
        self.assertIs(x.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_35_expired_signed_token_is_denied_before_pg_insert(self):
        with mock_signed_auth_server() as url:
            g=S0CFI01AuthenticatedCommandsLocal(url,'test-public-key',DB)
            expired=make_signed_token(self.actor,self.session,
                                      expires_at=int(time.time())-5)
            x=g.execute(expired,'capture_human_closure',self._gateway_payload())
        self.assertIs(x.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_36_wrong_signature_denied(self):
        with mock_signed_auth_server() as url:
            g=S0CFI01AuthenticatedCommandsLocal(url,'test-public-key',DB)
            auth=make_signed_token(self.actor,self.session,signing_key=b'another-test-key')
            x=g.execute(auth,'capture_human_closure',self._gateway_payload())
        self.assertIs(x.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_37_valid_signed_http_but_session_deleted_revokes_recheck(self):
        with mock_signed_auth_server() as url:
            g=S0CFI01AuthenticatedCommandsLocal(url,'test-public-key',DB)
            auth=make_signed_token(self.actor,self.session)
            cap=g.execute(auth,'capture_human_closure',self._gateway_payload())
            self.assertIs(cap.state,CommandState.CAPTURED_LOCAL_ONLY)
            with self.pg.connect(DB) as con:
                con.execute('delete from auth.sessions where id=%s',(self.session,))
            check=g.execute(auth,'recheck_human_closure',
                {**self._gateway_payload(),'closure_event_ref':cap.closure_event_ref})
        self.assertIs(check.state,CommandState.DENIED)
        self.assertEqual(self._count(),1)


    # CFI-01 signed SQL gate, separate restricted database user. This is
    # proof-of-prerequisites only: no F03 data access or model writes.
    _SIGNED_KEY_ID=uuid.UUID('cfeed000-0000-4000-8000-000000000001')
    _SIGNED_SECRET=bytes.fromhex(
        '1160b59cd3466f55112233445566778899aabbccddeeff001122334455667788')
    _RESTRICTED_DSN=('postgresql://prumo_cfi01_pgtest_login:'
        'cf-i01-disposable-test-only-not-production@127.0.0.1:5432/prumo_s0_test_cfi01')

    def _signed_gate(self):
        return S0CFI01RestrictedSignedPrerequisiteLocal(
            self._RESTRICTED_DSN,key_id=self._SIGNED_KEY_ID,
            signing_key=self._SIGNED_SECRET)

    def _restricted_call_raw(self, *, operation='capture_human_closure',
                             actor=None,case=None,session=None,version=1,
                             event=None,key=None,issued=None,nonce=None,
                             signature=None):
        import time
        from backend.s0_cfi01_signed_prerequisite_local import _QUERY
        actor=actor or self.actor
        case=case or self.case
        session=session or self.session
        key=key or self._SIGNED_KEY_ID
        issued=issued if issued is not None else int(time.time())
        nonce=nonce or uuid.uuid4()
        material=self._signed_gate()._material(
            operation,Principal(actor,session),case,version,event,issued,nonce)
        signature=signature if signature is not None else hmac.new(
            self._SIGNED_SECRET,material,hashlib.sha256).hexdigest()
        conn=self.pg.connect(self._RESTRICTED_DSN,connect_timeout=5)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(_QUERY,(operation,actor,session,case,version,event,
                                        key,issued,nonce,signature))
                    return cur.fetchone()
        finally:
            conn.close()

    def test_38_signed_gate_valid_physical_restricted_login(self):
        result=self._signed_gate().prove('capture_human_closure',
           Principal(self.actor,self.session),self.case,1)
        self.assertIs(result.state,SignedState.SIGNED_PREREQUISITES_ONLY_LOCAL)
        self.assertEqual(self._count(),0)

    def test_39_nonce_replay_is_physically_rejected(self):
        nonce=uuid.uuid4()
        self.assertEqual(self._restricted_call_raw(nonce=nonce),
                         ('SIGNED_PREREQUISITES_ONLY_LOCAL',))
        with self.assertRaises(self.pg.Error):
            self._restricted_call_raw(nonce=nonce)
        self.assertEqual(self._count(),0)

    def test_40_signed_proof_changed_case_is_rejected(self):
        false_case=uuid.uuid4()
        out=self._signed_gate().prove('capture_human_closure',
             Principal(self.actor,self.session),false_case,1)
        self.assertIs(out.state,SignedState.DENIED)

    def test_41_signed_proof_wrong_session_is_rejected(self):
        out=self._signed_gate().prove('capture_human_closure',
            Principal(self.actor,uuid.uuid4()),self.case,1)
        self.assertIs(out.state,SignedState.DENIED)

    def test_42_signed_proof_stale_cycle_is_rejected(self):
        out=self._signed_gate().prove('capture_human_closure',
            Principal(self.actor,self.session),self.case,2)
        self.assertIs(out.state,SignedState.DENIED)

    def test_43_expired_proof_is_rejected(self):
        import time
        with self.assertRaises(self.pg.Error):
            self._restricted_call_raw(issued=int(time.time())-90)

    def test_44_forged_hmac_is_rejected(self):
        with self.assertRaises(self.pg.Error):
            self._restricted_call_raw(signature='a'*64)

    def test_45_wrong_key_id_is_rejected(self):
        with self.assertRaises(self.pg.Error):
            self._restricted_call_raw(key=uuid.uuid4())

    def test_46_restricted_login_cannot_directly_read_private_receipts(self):
        with self.pg.connect(self._RESTRICTED_DSN) as conn:
            with self.assertRaises(self.pg.Error):
                conn.execute("select * from prumo_private.cfi01_human_closure_events_local")

    def test_47_restricted_login_cannot_directly_read_messages(self):
        with self.pg.connect(self._RESTRICTED_DSN) as conn:
            with self.assertRaises(self.pg.Error):
                conn.execute("select * from public.mensagens")

    def test_48_restricted_login_cannot_directly_read_signing_keys(self):
        with self.pg.connect(self._RESTRICTED_DSN) as conn:
            with self.assertRaises(self.pg.Error):
                conn.execute("select * from prumo_private.cfi01_signing_keys_local")

    def test_49_recheck_requires_matching_existing_receipt(self):
        missing=self._signed_gate().prove('recheck_human_closure',
            Principal(self.actor,self.session),self.case,1,event=uuid.uuid4())
        self.assertIs(missing.state,SignedState.DENIED)
        captured=self.capture()
        self.assertIs(captured.state,ClosureState.CAPTURED_LOCAL_ONLY)
        good=self._signed_gate().prove('recheck_human_closure',
            Principal(self.actor,self.session),self.case,1,
            event=uuid.UUID(captured.closure_event_ref))
        self.assertIs(good.state,SignedState.SIGNED_PREREQUISITES_ONLY_LOCAL)

    def test_50_s1_suspension_revokes_signed_gate(self):
        with self.pg.connect(DB) as conn:
            conn.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",
                         (self.actor,))
        out=self._signed_gate().prove('capture_human_closure',
            Principal(self.actor,self.session),self.case,1)
        self.assertIs(out.state,SignedState.DENIED)
        self.assertEqual(self._count(),0)

    def test_51_restricted_login_cannot_insert_technical_receipt(self):
        with self.pg.connect(self._RESTRICTED_DSN) as conn:
            with self.assertRaises(self.pg.Error):
                conn.execute("""insert into prumo_private.cfi01_human_closure_events_local
                    (id) values (%s)""",(uuid.uuid4(),))



    def _signed_commands(self):
        return S0CFI01SignedCommandsLocal(
            'https://auth.example.invalid','test-public-key',
            DB,self._RESTRICTED_DSN,
            key_id=self._SIGNED_KEY_ID,signing_key=self._SIGNED_SECRET,
            opener=SyntheticGoTrueHTTP(actor=self.actor))

    def test_52_signed_sql_gate_then_real_pg_capture(self):
        gate=self._signed_commands()
        result=gate.execute(synthetic_token(self.actor,self.session),
             'capture_human_closure',self._gateway_payload())
        self.assertIs(result.state,CommandState.CAPTURED_LOCAL_ONLY)
        self.assertEqual(self._count(),1)

    def test_53_signed_sql_gate_then_real_pg_recheck(self):
        gate=self._signed_commands()
        auth=synthetic_token(self.actor,self.session)
        receipt=gate.execute(auth,'capture_human_closure',self._gateway_payload())
        self.assertIs(receipt.state,CommandState.CAPTURED_LOCAL_ONLY)
        check=gate.execute(auth,'recheck_human_closure',
             {**self._gateway_payload(),'closure_event_ref':receipt.closure_event_ref})
        self.assertIs(check.state,CommandState.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertEqual(self._count(),1)

    def test_54_wrong_signed_key_blocks_before_privileged_capture(self):
        gate=S0CFI01SignedCommandsLocal(
            'https://auth.example.invalid','test-public-key',
            DB,self._RESTRICTED_DSN,key_id=self._SIGNED_KEY_ID,
            signing_key=b'x'*32,opener=SyntheticGoTrueHTTP(actor=self.actor))
        result=gate.execute(synthetic_token(self.actor,self.session),
             'capture_human_closure',self._gateway_payload())
        self.assertIs(result.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_55_team_suspension_blocks_signed_capture(self):
        gate=self._signed_commands()
        with self.pg.connect(DB) as con:
            con.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",
                        (self.actor,))
        result=gate.execute(synthetic_token(self.actor,self.session),
            'capture_human_closure',self._gateway_payload())
        self.assertIs(result.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_56_signed_entry_rejects_claimed_browser_role(self):
        gate=self._signed_commands()
        result=gate.execute(synthetic_token(self.actor,self.session),
            'capture_human_closure',{**self._gateway_payload(),
                                      'actor_id':str(self.actor)})
        self.assertIs(result.state,CommandState.INPUT_REJECTED)
        self.assertEqual(self._count(),0)


    def _atomic_gateway(self,signing_key=None):
        return S0CFI01AtomicCommandsLocal(
            'https://auth.example.invalid','test-public-key',
            self._RESTRICTED_DSN,
            key_id=self._SIGNED_KEY_ID,
            signing_key=signing_key if signing_key is not None
              else self._SIGNED_SECRET,
            opener=SyntheticGoTrueHTTP(actor=self.actor))

    def test_57_atomic_capture_only_restricted_login(self):
        gate=self._atomic_gateway()
        result=gate.execute(synthetic_token(self.actor,self.session),
            'capture_human_closure',self._gateway_payload())
        self.assertIs(result.state,CommandState.CAPTURED_LOCAL_ONLY)
        self.assertTrue(uuid.UUID(result.closure_event_ref))
        self.assertEqual(self._count(),1)

    def test_58_atomic_recheck_and_idempotency(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        first=gate.execute(auth,'capture_human_closure',self._gateway_payload())
        self.assertIs(first.state,CommandState.CAPTURED_LOCAL_ONLY)
        repeat=gate.execute(auth,'capture_human_closure',self._gateway_payload())
        self.assertIs(repeat.state,CommandState.ALREADY_CAPTURED)
        self.assertEqual(repeat.closure_event_ref,first.closure_event_ref)
        result=gate.execute(auth,'recheck_human_closure',
           {**self._gateway_payload(),'closure_event_ref':first.closure_event_ref})
        self.assertIs(result.state,CommandState.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertEqual(self._count(),1)

    def test_59_atomic_recheck_rejects_inbound_change(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        cap=gate.execute(auth,'capture_human_closure',self._gateway_payload())
        self.assertIs(cap.state,CommandState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._add_message(cur,uuid.uuid4())
        out=gate.execute(auth,'recheck_human_closure',
            {**self._gateway_payload(),'closure_event_ref':cap.closure_event_ref})
        self.assertIs(out.state,CommandState.STALE)

    def test_60_atomic_wrong_signing_key_never_mutates(self):
        gate=self._atomic_gateway(signing_key=b'wrong-lab-test-key-must-be-32bytes-at-least')
        result=gate.execute(synthetic_token(self.actor,self.session),
             'capture_human_closure',self._gateway_payload())
        self.assertIs(result.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_61_atomic_s1_suspension_denied(self):
        with self.pg.connect(DB) as con:
            con.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",
                        (self.actor,))
        out=self._atomic_gateway().execute(
             synthetic_token(self.actor,self.session),'capture_human_closure',
             self._gateway_payload())
        self.assertIs(out.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)

    def test_62_atomic_recheck_new_session_denied(self):
        gate=self._atomic_gateway()
        cap=gate.execute(synthetic_token(self.actor,self.session),
          'capture_human_closure',self._gateway_payload())
        newer=uuid.uuid4()
        with self.pg.connect(DB) as con:
            con.execute('insert into auth.sessions(id,user_id) values (%s,%s)',
                        (newer,self.actor))
        out=gate.execute(synthetic_token(self.actor,newer),
          'recheck_human_closure',
          {**self._gateway_payload(),'closure_event_ref':cap.closure_event_ref})
        self.assertIs(out.state,CommandState.DENIED)

    def test_63_atomic_owner_is_nonlogin_nonbypassrls_nonsuperuser(self):
        with self.pg.connect(DB) as con:
            row=con.execute("""select rolcanlogin,rolsuper,rolbypassrls,rolinherit
              from pg_roles where rolname='prumo_cfi01_atomic_owner_local'""").fetchone()
            self.assertEqual(row,(False,False,False,False))
            owner=con.execute("""select pg_get_userbyid(proowner)
                from pg_proc where oid='prumo_private.cfi01_atomic_signed_closure_local(
                  text,uuid,uuid,uuid,bigint,uuid,text,uuid,bigint,uuid,text)'::regprocedure""").fetchone()[0]
            self.assertEqual(owner,'prumo_cfi01_atomic_owner_local')

    def test_64_atomic_restricted_login_still_cannot_read_or_update_messages(self):
        with self.pg.connect(self._RESTRICTED_DSN) as con:
            with self.assertRaises(self.pg.Error):
                con.execute("select * from public.mensagens")
        with self.pg.connect(self._RESTRICTED_DSN) as con:
            with self.assertRaises(self.pg.Error):
                con.execute("update public.mensagens set conteudo_sintetico='forged'")

    def test_65_atomic_restricted_login_cannot_insert_receipt(self):
        with self.pg.connect(self._RESTRICTED_DSN) as con:
            with self.assertRaises(self.pg.Error):
                con.execute("insert into prumo_private.cfi01_human_closure_events_local(id) values (%s)",
                            (uuid.uuid4(),))

    def test_66_atomic_never_changes_eight_commercial_statuses(self):
        self.assertIs(self._atomic_gateway().execute(
            synthetic_token(self.actor,self.session),'capture_human_closure',
            self._gateway_payload()).state,CommandState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            x=con.execute("select status_comercial from public.ciclos_comerciais where id=%s",
                (self.cycle,)).fetchone()[0]
        self.assertEqual(x,'em atendimento pelo operador')

    def test_67_atomic_request_binds_idempotency_key_before_sql(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        cap=gate.execute(auth,'capture_human_closure',self._gateway_payload())
        self.assertIs(cap.state,CommandState.CAPTURED_LOCAL_ONLY)
        wrong=gate.execute(auth,'recheck_human_closure',
            {**self._gateway_payload(),'idempotency_key':'different-safe-key',
             'closure_event_ref':cap.closure_event_ref})
        self.assertIs(wrong.state,CommandState.DENIED)

    def test_68_atomic_denies_f03_fields_in_public_command(self):
        out=self._atomic_gateway().execute(
            synthetic_token(self.actor,self.session),'capture_human_closure',
            {**self._gateway_payload(),'fields_proposed':{'bank_status':'approved'}})
        self.assertIs(out.state,CommandState.INPUT_REJECTED)
        self.assertEqual(self._count(),0)


    def test_69_atomic_two_concurrent_sessions_same_key_single_receipt(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        barrier=threading.Barrier(2)
        def runner():
            barrier.wait(timeout=7)
            return gate.execute(auth,'capture_human_closure',
                                self._gateway_payload()).state
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(runner) for _ in range(2)]
            results={f.result(timeout=15) for f in futures}
        self.assertEqual(results,{CommandState.CAPTURED_LOCAL_ONLY,
                                  CommandState.ALREADY_CAPTURED})
        self.assertEqual(self._count(),1)

    def test_70_atomic_inbound_arrives_before_conversation_lock(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        with self.pg.connect(DB) as con:
            con.execute('select id from public.conversas where id=%s for update',
                        (self.conversation,))
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(gate.execute,auth,'capture_human_closure',
                                   self._gateway_payload())
                with self.assertRaises(TimeoutError):
                    future.result(timeout=0.15)
                with con.cursor() as cur:
                    self._add_message(cur,uuid.uuid4())
                con.commit()
                cap=future.result(timeout=10)
        self.assertIs(cap.state,CommandState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            count=con.execute("""select quantidade_mensagens from
                prumo_private.cfi01_human_closure_events_local where caso_id=%s""",
                (self.case,)).fetchone()[0]
        self.assertEqual(count,2)
        check=gate.execute(auth,'recheck_human_closure',
             {**self._gateway_payload(),'closure_event_ref':cap.closure_event_ref})
        self.assertIs(check.state,CommandState.VERIFIED_REVIEW_ONLY_LOCAL)


    def test_71_atomic_owner_cannot_directly_read_auth_sessions(self):
        # Session verification remains a privileged tiny helper, NOT
        # blanket access by the NOLOGIN atomic function owner.
        with self.pg.connect(DB) as con:
            direct=con.execute("""select has_schema_privilege(
                  'prumo_cfi01_atomic_owner_local','auth','USAGE'),
                  has_table_privilege('prumo_cfi01_atomic_owner_local',
                  'auth.sessions','SELECT')""").fetchone()
            self.assertEqual(direct,(False,False))
            ownership=con.execute("""select pg_get_userbyid(p.proowner)
             from pg_proc p where p.oid=
             'prumo_private.cfi01_session_valid_local(uuid,uuid)'::regprocedure
             """).fetchone()[0]
            self.assertEqual(ownership,'postgres')

    def test_72_session_helper_not_callable_by_browser_or_sql_login(self):
        with self.pg.connect(DB) as con:
            direct=con.execute("""select has_function_privilege(
                  'prumo_cfi01_pgtest_login',
                  'prumo_private.cfi01_session_valid_local(uuid,uuid)',
                  'EXECUTE'),
                  has_function_privilege('authenticated',
                  'prumo_private.cfi01_session_valid_local(uuid,uuid)',
                  'EXECUTE'),
                  has_function_privilege('prumo_cfi01_atomic_owner_local',
                  'prumo_private.cfi01_session_valid_local(uuid,uuid)',
                  'EXECUTE')""").fetchone()
            self.assertEqual(direct,(False,False,True))

    def test_73_atomic_missing_session_denied_by_private_helper(self):
        with self.pg.connect(DB) as con:
            con.execute("delete from auth.sessions where id=%s",(self.session,))
        result=self._atomic_gateway().execute(
            synthetic_token(self.actor,self.session),
            'capture_human_closure',self._gateway_payload())
        self.assertIs(result.state,CommandState.DENIED)
        self.assertEqual(self._count(),0)


    def test_74_atomic_internal_receipt_matches_persisted_event(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        outcome=gate.capture_internal_receipt(auth,self._gateway_payload())
        self.assertIs(outcome.state,CommandState.CAPTURED_LOCAL_ONLY)
        receipt=outcome.receipt
        self.assertIsNotNone(receipt)
        with self.pg.connect(DB) as con:
            row=con.execute("""select concessionaria_id,caso_id,id,atribuicao_id,
                versao_ciclo,snapshot_sha256,ultima_mensagem_id,quantidade_mensagens
                from prumo_private.cfi01_human_closure_events_local
                where caso_id=%s""",(self.case,)).fetchone()
        self.assertEqual((receipt.store_ref,receipt.case_ref,receipt.closure_event_ref,
                          receipt.assignment_ref,receipt.expected_cycle_version,
                          receipt.snapshot_sha256,receipt.message_watermark,receipt.message_count),
                         (str(row[0]),str(row[1]),str(row[2]),str(row[3]),row[4],
                          row[5],str(row[6]),row[7]))
        self.assertFalse(hasattr(receipt,"content"))
        self.assertFalse(hasattr(receipt,"form_version"))
        self.assertFalse(hasattr(receipt,"bank_submission_proved"))
        same=gate.recheck_internal_receipt(auth,{
           **self._gateway_payload(),"closure_event_ref":receipt.closure_event_ref})
        self.assertIs(same.state,CommandState.VERIFIED_REVIEW_ONLY_LOCAL)
        self.assertEqual(same.receipt,receipt)

    def test_75_atomic_internal_receipt_no_leak_when_stale(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        first=gate.capture_internal_receipt(auth,self._gateway_payload())
        self.assertIs(first.state,CommandState.CAPTURED_LOCAL_ONLY)
        with self.pg.connect(DB) as con:
            with con.cursor() as cur: self._add_message(cur,uuid.uuid4())
        later=gate.recheck_internal_receipt(auth,{
           **self._gateway_payload(),"closure_event_ref":first.receipt.closure_event_ref})
        self.assertIs(later.state,CommandState.STALE)
        self.assertIsNone(later.receipt)

    def test_76_atomic_internal_receipt_denies_fake_grant_and_revoked_session(self):
        gate=self._atomic_gateway()
        auth=synthetic_token(self.actor,self.session)
        injected=gate.capture_internal_receipt(auth,{
           **self._gateway_payload(),"store_grant":True})
        self.assertIs(injected.state,CommandState.INPUT_REJECTED)
        self.assertIsNone(injected.receipt)
        with self.pg.connect(DB) as con:
            con.execute('delete from auth.sessions where id=%s',(self.session,))
        revoked=gate.capture_internal_receipt(auth,self._gateway_payload())
        self.assertIs(revoked.state,CommandState.DENIED)
        self.assertIsNone(revoked.receipt)
        self.assertEqual(self._count(),0)

    def test_77_bridge_real_capture_and_recheck_remain_contract_pending(self):
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        result=bridge.capture(auth,self._gateway_payload())
        self.assertIs(result.state,S0F03BridgeState.VERIFIED_CONTRACT_PENDING)
        self.assertEqual(result.binding.receipt.case_ref,str(self.case))
        self.assertEqual(result.binding.receipt.assignment_ref,str(self.assignment))
        self.assertEqual(result.binding.receipt.message_count,1)
        self.assertFalse(hasattr(result.binding.receipt,'case_version'))
        self.assertFalse(hasattr(result.binding.receipt,'form_version'))
        self.assertFalse(hasattr(result.binding.receipt,'catalogue_version'))
        self.assertTrue(any('expected_case_version' in g for g in UNRATIFIED_F03_INPUTS))
        again=bridge.recheck(auth,result.binding)
        self.assertIs(again.state,S0F03BridgeState.VERIFIED_CONTRACT_PENDING)
        self.assertEqual(again.binding,result.binding)
        self.assertEqual(self._count(),1)

    def test_78_bridge_new_message_blocks_without_receipt_leak(self):
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        cap=bridge.capture(auth,self._gateway_payload())
        with self.pg.connect(DB) as con:
            with con.cursor() as cur:
                self._add_message(cur,uuid.uuid4())
        later=bridge.recheck(auth,cap.binding)
        self.assertIs(later.state,S0F03BridgeState.STALE)
        self.assertIsNone(later.binding)

    def test_79_bridge_reassignment_invalidates_old_binding(self):
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        cap=bridge.capture(auth,self._gateway_payload())
        self.assertIs(cap.state,S0F03BridgeState.VERIFIED_CONTRACT_PENDING)
        with self.pg.connect(DB) as con:
            con.execute('delete from public.atribuicoes_humanas where id=%s',
                        (self.assignment,))
            con.execute('''insert into public.atribuicoes_humanas
                        (id,concessionaria_id,caso_id,operador_id)
                        values (%s,%s,%s,%s)''',
                        (uuid.uuid4(),self.shop,self.case,self.actor))
        after=bridge.recheck(auth,cap.binding)
        self.assertIn(after.state,(S0F03BridgeState.DENIED,S0F03BridgeState.STALE))
        self.assertIsNone(after.binding)

    def test_80_bridge_rejects_ui_catalog_and_case_version_injection(self):
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        for fake in ('expected_case_version','form_version','catalogue_version',
                     'actor_id','assignment_ref','fields_proposed'):
            with self.subTest(fake=fake):
                outcome=bridge.capture(auth,{**self._gateway_payload(),fake:1})
                self.assertIs(outcome.state,S0F03BridgeState.INPUT_REJECTED)
                self.assertIsNone(outcome.binding)
        self.assertEqual(self._count(),0)

    def test_81_bridge_cycle_version_change_is_stale(self):
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        cap=bridge.capture(auth,self._gateway_payload())
        with self.pg.connect(DB) as con:
            con.execute('update public.ciclos_comerciais set versao_registro=2 where id=%s',
                        (self.cycle,))
        after=bridge.recheck(auth,cap.binding)
        self.assertIs(after.state,S0F03BridgeState.STALE)
        self.assertIsNone(after.binding)

    def test_82_bridge_revoked_session_denies_recheck(self):
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        cap=bridge.capture(auth,self._gateway_payload())
        with self.pg.connect(DB) as con:
            con.execute('delete from auth.sessions where id=%s',(self.session,))
        denied=bridge.recheck(auth,cap.binding)
        self.assertIs(denied.state,S0F03BridgeState.DENIED)
        self.assertIsNone(denied.binding)

    def test_83_bridge_tampered_receipt_cannot_skip_s0_recheck(self):
        from dataclasses import replace
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        cap=bridge.capture(auth,self._gateway_payload())
        modified=replace(cap.binding,receipt=replace(
            cap.binding.receipt,closure_event_ref=str(uuid.uuid4())))
        denied=bridge.recheck(auth,modified)
        self.assertIs(denied.state,S0F03BridgeState.DENIED)
        self.assertIsNone(denied.binding)

    def test_84_bridge_rejects_fake_source_and_malformed_binding(self):
        from dataclasses import replace
        with self.assertRaises(TypeError):
            S0CFI01F03ReceiptBridgeLocal(object())
        bridge=S0CFI01F03ReceiptBridgeLocal(self._atomic_gateway())
        auth=synthetic_token(self.actor,self.session)
        self.assertIs(bridge.recheck(auth,{'case_ref':str(self.case)}).state,
                      S0F03BridgeState.INPUT_REJECTED)
        cap=bridge.capture(auth,self._gateway_payload())
        bad=replace(cap.binding,receipt=replace(
            cap.binding.receipt,expected_cycle_version=True))
        self.assertIs(bridge.recheck(auth,bad).state,S0F03BridgeState.INPUT_REJECTED)

if __name__ == "__main__":
    unittest.main()
