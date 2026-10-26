"""Real GoTrue + restricted signed SQL integration. Only disposable loopback.

Run from the pinned S0 runtime AFTER its original Auth/REST and CFI-01 suites.
No identity mock, opener replacement, SQL gateway stub or production service.
"""
import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
import time
import unittest
import uuid
from urllib.parse import urlsplit

import psycopg
from psycopg import sql
from scripts.test_s0_cfi01_auth_rest_local import local_env, register, request
from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal
from backend.s0_cfi01_communication_local import S0CFI01CommunicationLocal
from backend.s0_communication_contract import FV_INTENT_PROFILE


class TransactionalCommunicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_CFI01_TRANSACTIONAL_TEST') != 'YES':
            raise RuntimeError('Explicit disposable integration opt-in required')
        cls.env = local_env()  # Original helper rejects remote API/DB.
        cls.db, cls.api, cls.key = (cls.env[k] for k in ('DB_URL','API_URL','ANON_KEY'))
        os.environ['PRUMO_CFI01_SUPABASE_LOCAL_AUTH_TEST'] = '1'
        with psycopg.connect(cls.db) as c:
            version = c.execute("select current_setting('server_version_num')::int").fetchone()[0]
            if not 170000 <= version < 180000:
                raise RuntimeError('PostgreSQL 17 required')
        u = urlsplit(cls.db)
        dsn = (f'postgresql://prumo_cfi01_pgtest_login:'
               f'cf-i01-disposable-test-only-not-production@{u.hostname}:{u.port}/postgres')
        cls.gateway = S0CFI01AtomicCommandsLocal(cls.api,cls.key,dsn,
            key_id=uuid.UUID('cfeed000-0000-4000-8000-000000000001'),
            signing_key=bytes.fromhex('1160b59cd3466f55112233445566778899aabbccddeeff001122334455667788'))
        cls.adapter = S0CFI01CommunicationLocal(cls.gateway)

    def setUp(self):
        self.actor,self.token = register(self.api,self.key)
        for name in ('shop','lead','cycle','case','assignment','channel','conversation','message'):
            setattr(self,name,uuid.uuid4())
        with psycopg.connect(self.db) as c:
            c.execute('insert into public.atores(id) values (%s)',(self.actor,))
            c.execute("insert into public.equipe_prumo_s1(ator_id,estado) values (%s,'ativo')",(self.actor,))
            c.execute("insert into public.concessionarias(id,nome_operacional) values (%s,'CFI TRANSACTION LAB')",(self.shop,))
            c.execute("insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values (%s,%s,'operador')",(self.actor,self.shop))
            c.execute("insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values (%s,%s,'+5581999888877')",(self.lead,self.shop))
            c.execute("""insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial,versao_registro)
                values (%s,%s,%s,'em atendimento pelo operador',1)""",(self.cycle,self.shop,self.lead))
            c.execute('insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values (%s,%s,%s,%s)',(self.case,self.shop,self.lead,self.cycle))
            c.execute('insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id) values (%s,%s,%s,%s)',(self.assignment,self.shop,self.case,self.actor))
            c.execute('insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values (%s,%s,%s)',(self.channel,self.shop,str(self.channel)))
            c.execute('insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id) values (%s,%s,%s,%s,%s)',(self.conversation,self.shop,self.lead,self.channel,self.case))
            self.add_message(c,self.message)
        self.payload = dict(case_ref=str(self.case),expected_cycle_version=1,idempotency_key='transactional-capture-001')
        self.auth = 'Bearer '+self.token

    def tearDown(self):
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select status_comercial from public.ciclos_comerciais where id=%s',(self.cycle,)).fetchone()[0], 'em atendimento pelo operador')
            self.assertEqual(c.execute('select operador_id from public.atribuicoes_humanas where id=%s',(self.assignment,)).fetchone()[0],self.actor)

    def add_message(self,c,ref):
        c.execute("""insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,caso_id,
            direcao,origem,conteudo_sintetico,id_externo) values (%s,%s,%s,%s,%s,'entrada','simulado','synthetic transactional test',%s)""",
            (ref,self.shop,self.conversation,self.channel,self.case,str(ref)))

    def counters(self):
        with psycopg.connect(self.db) as c:
            return (c.execute('select count(*) from prumo_private.cfi01_human_closure_events_local where caso_id=%s',(self.case,)).fetchone()[0],
                    c.execute('select count(*) from prumo_private.cfi01_consumed_nonces_local').fetchone()[0])

    def capture(self):
        result = self.adapter.capture(self.auth,self.payload)
        self.assertEqual(result.state,'VERIFIED_CONTRACT_PENDING')
        self.assertIsNotNone(result.binding)
        self.assertFalse(result.public_projection()['confirmed_persisted'])
        return result.binding

    def refused(self,call,state):
        before = self.counters()
        result = call()
        self.assertEqual(result.state,state)
        self.assertIsNone(result.binding)
        projection = result.public_projection()
        self.assertEqual(set(projection),{'schema_version','state','confirmed_persisted'})
        self.assertFalse(projection['confirmed_persisted'])
        self.assertEqual(self.counters(),before,'denied/stale transaction persisted nonce or receipt')
        return result

    def wait_for_blocker(self,pid):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            with psycopg.connect(self.db) as c:
                found=c.execute("""select 1 from pg_stat_activity a where a.usename='prumo_cfi01_pgtest_login'
                    and a.wait_event_type='Lock' and %s=any(pg_blocking_pids(a.pid))""",(pid,)).fetchone()
                if found: return
            time.sleep(.05)
        self.fail('restricted CFI command did not reach the asserted physical row lock')

    def test_01_authorized_capture_recheck_and_no_commercial_effect(self):
        before=self.counters();binding=self.capture()
        result=self.adapter.recheck(self.auth,binding)
        self.assertEqual(result.state,'VERIFIED_CONTRACT_PENDING');self.assertEqual(result.binding,binding)
        self.assertEqual(self.counters(),(1,before[1]+2))
        with psycopg.connect(self.db) as c:
            row=c.execute('select id,snapshot_sha256,ultima_mensagem_id,quantidade_mensagens from prumo_private.cfi01_human_closure_events_local where caso_id=%s',(self.case,)).fetchone()
        self.assertEqual(str(row[0]),binding.receipt.closure_event_ref)
        self.assertEqual(row[1],binding.receipt.snapshot_sha256)
        self.assertEqual((str(row[2]),row[3]),(str(self.message),1))

    def test_02_concurrent_same_key_one_technical_receipt(self):
        before=self.counters()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.adapter.capture(self.auth,self.payload),range(2)))
        self.assertTrue(all(r.state=='VERIFIED_CONTRACT_PENDING' for r in results))
        self.assertEqual(results[0].binding,results[1].binding)
        self.assertEqual(self.counters(),(1,before[1]+2))

    def test_03_invalid_jwt_signature_rejected_by_real_gotrue(self):
        parts=self.token.split('.');claims=json.loads(base64.urlsafe_b64decode(parts[1]+'='*((-len(parts[1]))%4)))
        claims['sub']=str(uuid.uuid4());parts[1]=base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip('=')
        self.refused(lambda:self.adapter.capture('Bearer '+'.'.join(parts),self.payload),'DENIED')

    def test_04_real_logout_revokes_session_before_recheck(self):
        binding=self.capture()
        status,_=request(self.api,self.key,'POST','/auth/v1/logout',token=self.token)
        self.assertIn(status,(200,204))
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select count(*) from auth.sessions where user_id=%s',(self.actor,)).fetchone()[0],0)
        self.refused(lambda:self.adapter.recheck(self.auth,binding),'DENIED')

    def test_05_live_shop_grant_revocation_denies_same_jwt(self):
        binding=self.capture()
        with psycopg.connect(self.db) as c:
            c.execute("update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s and concessionaria_id=%s",(self.actor,self.shop))
        self.refused(lambda:self.adapter.recheck(self.auth,binding),'DENIED')

    def test_06_s1_team_suspension_denies_same_jwt(self):
        binding=self.capture()
        with psycopg.connect(self.db) as c:
            c.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",(self.actor,))
        self.refused(lambda:self.adapter.recheck(self.auth,binding),'DENIED')

    def test_07_stale_cycle_blocks_capture_and_later_recheck(self):
        self.refused(lambda:self.adapter.capture(self.auth,{**self.payload,'expected_cycle_version':2}),'STALE')
        binding=self.capture()
        with psycopg.connect(self.db) as c:
            c.execute('update public.ciclos_comerciais set versao_registro=versao_registro+1 where id=%s',(self.cycle,))
        self.refused(lambda:self.adapter.recheck(self.auth,binding),'STALE')

    def test_08_new_committed_message_invalidates_bound_snapshot(self):
        binding=self.capture()
        with psycopg.connect(self.db) as c:self.add_message(c,uuid.uuid4())
        self.refused(lambda:self.adapter.recheck(self.auth,binding),'STALE')

    def test_09_revoked_authority_takes_precedence_over_staleness(self):
        binding=self.capture()
        with psycopg.connect(self.db) as c:
            c.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",(self.actor,))
            self.add_message(c,uuid.uuid4())
        self.refused(lambda:self.adapter.recheck(self.auth,binding),'DENIED')

    def test_10_recheck_waits_for_grant_revocation_commit(self):
        binding=self.capture();before=self.counters()
        with psycopg.connect(self.db) as writer,ThreadPoolExecutor(max_workers=1) as pool:
            writer.execute("update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s and concessionaria_id=%s",(self.actor,self.shop))
            pid=writer.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(self.adapter.recheck,self.auth,binding)
            try:self.wait_for_blocker(pid)
            finally:writer.commit()
            result=future.result(timeout=15)
        self.assertEqual(result.state,'DENIED');self.assertIsNone(result.binding);self.assertEqual(self.counters(),before)

    def test_11_recheck_waits_for_inbound_commit_and_returns_stale(self):
        binding=self.capture();before=self.counters()
        with psycopg.connect(self.db) as writer,ThreadPoolExecutor(max_workers=1) as pool:
            self.add_message(writer,uuid.uuid4())
            pid=writer.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(self.adapter.recheck,self.auth,binding)
            try:self.wait_for_blocker(pid)
            finally:writer.commit()
            result=future.result(timeout=15)
        self.assertEqual(result.state,'STALE');self.assertIsNone(result.binding);self.assertEqual(self.counters(),before)

    def test_12_failed_receipt_insert_rolls_back_nonce_and_retry_is_safe(self):
        before=self.counters();name='cfi_fault_'+uuid.uuid4().hex
        fn=sql.Identifier('prumo_private',name);trigger=sql.Identifier(name)
        with psycopg.connect(self.db) as c:
            c.execute(sql.SQL("create function {}() returns trigger language plpgsql as $$ begin if new.caso_id='{}'::uuid then raise exception 'LAB_FORCED_RECEIPT_FAILURE'; end if; return new; end $$").format(fn,sql.SQL(str(self.case))))
            c.execute(sql.SQL('create trigger {} before insert on prumo_private.cfi01_human_closure_events_local for each row execute function {}()').format(trigger,fn))
        try:self.refused(lambda:self.adapter.capture(self.auth,self.payload),'UNAVAILABLE')
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on prumo_private.cfi01_human_closure_events_local').format(trigger))
                c.execute(sql.SQL('drop function {}()').format(fn))
        self.capture();self.assertEqual(self.counters(),(1,before[1]+1))

    def test_13_authenticated_other_user_cannot_capture_case(self):
        _,other=register(self.api,self.key)
        self.refused(lambda:self.adapter.capture('Bearer '+other,self.payload),'DENIED')

    def test_14_forged_binding_and_pending_ui_intent_never_gain_authority(self):
        binding=self.capture()
        forged=replace(binding,receipt=replace(binding.receipt,store_ref=str(uuid.uuid4())))
        # Complete expected metadata is now compared before COMMIT. A stale
        # server binding must not leave nonce/audit from an accepted recheck.
        before=self.counters()
        result=self.adapter.recheck(self.auth,forged)
        self.assertEqual(result.state,'STALE');self.assertIsNone(result.binding)
        self.assertEqual(self.counters(),before)
        pending=self.adapter.capture(self.auth,dict(case_ref=str(self.case),expected_case_version='v1',idempotency_key='pending-only-001'),profile=FV_INTENT_PROFILE)
        self.assertIsNone(pending.binding);self.assertEqual(pending.public_projection()['state'],'CONTRACT_PENDING')
        self.assertEqual(self.counters(),before)


if __name__=='__main__':
    unittest.main(verbosity=2)
