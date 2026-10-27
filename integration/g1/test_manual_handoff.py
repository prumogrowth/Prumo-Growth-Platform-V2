"""Real GoTrue + canonical I54/I55/I61/I62 + S0 G1 in new loopback PG17.

No identity stub, mock queue or provider calls. Legacy SQL fixtures are tested
separately and are not counted as GoTrue scenarios.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import UUID,uuid4

import psycopg
from psycopg import sql
import backend
from backend.identity_boundary import SupabaseGoTrueVerifier
from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal
from backend import s0_g1_manual_queue_local as g1
from scripts.test_s0_cfi01_auth_rest_local import local_env,register,request


class G1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_G1_DISPOSABLE_TEST')!='YES':raise RuntimeError('G1 opt-in required')
        cls.env=local_env();cls.db,cls.api,cls.anon=(cls.env[k] for k in ('DB_URL','API_URL','ANON_KEY'))
        os.environ['PRUMO_CFI01_SUPABASE_LOCAL_AUTH_TEST']='1'
        src=Path(os.environ['PRUMO_G1_SOURCE_REPO']).resolve()
        manifest=json.loads(Path('integration/g1/s1_sources.json').read_text())
        assert subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip()==manifest['ref']
        for item in manifest['test_sources']:
            assert hashlib.sha256((src/item['path']).read_bytes()).hexdigest()==item['sha256']
        # Test-only import of the ORIGINAL S1 proof codec; no source overwrite.
        backend.__path__.append(str(src/'backend'))
        from backend.s1_gateway_signed_local import _proof_material
        cls.s1_material=staticmethod(_proof_material)
        cls.key_id=uuid4();cls.secret=secrets.token_bytes(48);password=secrets.token_urlsafe(40)
        cls.s1_key=uuid4();cls.s1_secret=secrets.token_bytes(48);s1_password=secrets.token_urlsafe(40)
        with psycopg.connect(cls.db,autocommit=True) as c:
            assert c.execute("select current_setting('server_version_num')::int/10000").fetchone()[0]==17
            c.execute('update prumo_private.cfi01_signing_keys_local set active=false')
            c.execute('insert into prumo_private.cfi01_signing_keys_local(key_id,secret) values (%s,%s)',(cls.key_id,cls.secret))
            c.execute(sql.SQL('alter role prumo_cfi01_pgtest_login password {}').format(sql.Literal(password)))
            c.execute(sql.SQL('alter role prumo_s1_signed_login_ci password {}').format(sql.Literal(s1_password)))
            # I22 deliberately removes installer's implicit key-table access.
            # Use its existing explicit custodian membership, never new grants.
            c.execute('set role prumo_s1_i22_custodio')
            c.execute("insert into prumo_s1_signed_i20.chaves(id,segredo,valido_desde,valido_ate) values (%s,%s,clock_timestamp()-interval '1 hour',clock_timestamp()+interval '1 hour')",(cls.s1_key,cls.s1_secret))
            c.execute('reset role')
            assert c.execute("select to_regprocedure('prumo_private.g1_manual_signed_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)') is not null").fetchone()[0], 'Run integration/g1/install_local.py first'
        u=urlsplit(cls.db)
        cls.dsn=f'postgresql://prumo_cfi01_pgtest_login:{password}@{u.hostname}:{u.port}/postgres'
        cls.s1_dsn=f'postgresql://prumo_s1_signed_login_ci:{s1_password}@{u.hostname}:{u.port}/postgres'
        cls.gateway=S0CFI01AtomicCommandsLocal(cls.api,cls.anon,cls.dsn,key_id=cls.key_id,signing_key=cls.secret)
        cls.command=g1.S0ManualQueueHandoffLocal(cls.gateway)
        cls.people={name:register(cls.api,cls.anon) for name in ('m1','m2','c1','c2','c3')}
        with psycopg.connect(cls.db) as c:
            for actor,_ in cls.people.values():
                c.execute('insert into public.atores(id) values (%s)',(actor,))
                c.execute("insert into public.equipe_prumo_s1(ator_id,estado) values (%s,'ativo')",(actor,))
            for manager,target in [('m1','c1'),('m1','c2'),('m2','c3')]:
                c.execute('insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values (%s,%s)',(cls.people[manager][0],cls.people[target][0]))

    def setUp(self):
        self.tokens={n:t for n,(_,t) in self.people.items()};self.shops={s:uuid4() for s in ('A','B')}
        with psycopg.connect(self.db) as c:
            for shop in self.shops.values():c.execute("insert into public.concessionarias(id,nome_operacional) values (%s,'G1 DISPOSABLE')",(shop,))
            for who,shop,role in [('m1','A','gestor'),('m1','B','gestor'),('m2','A','gestor'),('c1','A','operador'),('c3','A','operador')]:
                c.execute('insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values (%s,%s,%s)',(self.people[who][0],self.shops[shop],role))
        self.items={s:self.queue(s) for s in ('A','B')}

    def queue(self,shop='A',signal=True):
        lead,cycle=uuid4(),uuid4()
        with psycopg.connect(self.db) as c:
            c.execute('insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values (%s,%s,%s)',(lead,self.shops[shop],'+55'+str(int(lead)%10**11).zfill(11)))
            c.execute("insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial) values (%s,%s,%s,'aguardando primeiro disparo')",(cycle,self.shops[shop],lead))
            if signal:c.execute("update public.ciclos_comerciais set status_comercial='em atendimento pelo operador' where id=%s",(cycle,))
        return lead,cycle

    def payload(self,shop='A',target='c2',version=1,key='g1-request-0001',item=None):
        return dict(loja_id=str(self.shops[shop]),ciclo_id=str((item or self.items[shop])[1]),
            consultor_id=str(self.people[target][0]),versao_esperada=version,chave_idempotencia=key)

    def call(self,who='m1',payload=None,**kwargs):
        return self.command.execute('Bearer '+self.tokens[who],payload or self.payload(**kwargs))

    def proof(self,who='m1',payload=None):
        principal=self.gateway._identity.verify('Bearer '+self.tokens[who])
        return self.command._proof(principal,g1.fields(payload or self.payload()))

    def facts(self):
        with psycopg.connect(self.db) as c:
            shops=list(self.shops.values())
            return tuple(c.execute(q,(shops,)).fetchone()[0] for q in (
                'select count(*) from public.casos_humanos where concessionaria_id=any(%s)',
                'select count(*) from public.atribuicoes_humanas where concessionaria_id=any(%s)',
                'select count(*) from prumo_private.s1_excecoes_caso_i61 where concessionaria_id=any(%s)',
                'select count(*) from prumo_private.s0_fila_humana_eventos where concessionaria_id=any(%s)',
                'select count(*) from prumo_private.g1_manual_requests_local where concessionaria_id=any(%s)',
                'select count(*) from prumo_private.g1_manual_audit_local a join prumo_private.g1_manual_requests_local r on r.id=a.request_id where r.concessionaria_id=any(%s)'))+(c.execute('select count(*) from prumo_private.cfi01_consumed_nonces_local').fetchone()[0],)

    def reject(self,state,**kwargs):
        before=self.facts();result=self.call(**kwargs)
        self.assertEqual(result.state.value,state);self.assertIsNone(result.receipt)
        self.assertEqual(self.facts(),before);return result

    def assigned(self,**kwargs):
        result=self.call(**kwargs);self.assertEqual(result.state,g1.State.MANUAL_ASSIGNED);return result.receipt

    def wait_blocker(self,pid):
        end=time.monotonic()+6
        while time.monotonic()<end:
            with psycopg.connect(self.db) as c:
                if c.execute("select 1 from pg_stat_activity where wait_event_type='Lock' and %s=any(pg_blocking_pids(pid))",(pid,)).fetchone():return
            time.sleep(.025)
        self.fail('actual PostgreSQL blocker not observed')

    def pause(self,paused):
        with psycopg.connect(self.db) as c:
            version=c.execute('select versao from prumo_private.s1_intake_estado where operador_id=%s',(self.people['c2'][0],)).fetchone()
            c.execute('select prumo_private.s1_definir_intake(%s,%s,%s,%s)',(self.people['m1'][0],self.people['c2'][0],paused,version[0] if version else 1))

    def s1_proof(self,op,args,who):
        principal=SupabaseGoTrueVerifier(self.api,self.anon).verify('Bearer '+self.tokens[who])
        issued=int(time.time());nonce=uuid4()
        mac=hmac.new(self.s1_secret,self.s1_material(op,principal.actor_id,principal.session_id,args,issued,nonce),hashlib.sha256).hexdigest()
        return principal,issued,nonce,mac

    def claim(self,c,who='m2'):
        principal,issued,nonce,mac=self.s1_proof('FILA55C',(self.shops['A'],self.items['A'][1],None,None,None,'C:1'),who)
        return c.execute('select prumo_s1_signed_i20.invocar_fila_v55(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(principal.actor_id,principal.session_id,self.shops['A'],self.items['A'][1],1,self.s1_key,issued,nonce,mac)).fetchone()[0]

    def fresh_manager_session(self):
        with psycopg.connect(self.db) as c:email=c.execute('select email from auth.users where id=%s',(self.people['m1'][0],)).fetchone()[0]
        code,body=request(self.api,self.anon,'POST','/auth/v1/token?grant_type=password',{'email':email,'password':'Only-Local-CFI01-Test!X8b2'})
        self.assertEqual(code,200);self.tokens['m1']=body['access_token']
        return self.gateway._identity.verify('Bearer '+self.tokens['m1']).session_id

    def test_01_normal_store_grant_needs_no_exception(self):
        result=self.assigned(target='c1');self.assertIsNone(result['exception_id'])
        self.assertEqual(result['consultant_id'],str(self.people['c1'][0]))
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute("select count(*) from prumo_private.s0_fila_humana_eventos where ciclo_id=%s and resultado='ENCAMINHADO'",(self.items['A'][1],)).fetchone()[0],1)

    def test_02_case_only_exception_and_real_rls_two_teams(self):
        first=self.assigned();other=self.assigned(who='m2',target='c3',item=self.queue(),key='g1-other-request')
        self.assertIsNotNone(first['exception_id'])
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select count(*) from public.vinculos_papel_escopo where ator_id=%s and concessionaria_id=%s',(self.people['c2'][0],self.shops['A'])).fetchone()[0],0)
        path='/rest/v1/casos_humanos?select=id&id=in.('+first['case_id']+','+other['case_id']+')'
        for who,wanted in [('c2',first['case_id']),('m1',first['case_id']),('m2',other['case_id'])]:
            code,rows=request(self.api,self.anon,'GET',path,token=self.tokens[who])
            self.assertEqual(code,200);self.assertEqual({r['id'] for r in rows},{wanted})

    def test_03_other_team_consultant_denied_even_same_store(self):self.reject('DESTINATION_INELIGIBLE',target='c3')
    def test_04_self_claim_is_a_different_operation(self):self.reject('DESTINATION_INELIGIBLE',target='m1')

    def test_05_a2_paused_consultant_with_existing_exception_cannot_get_new_case(self):
        first=self.assigned();self.pause(True)
        try:
            self.reject('INTAKE_PAUSED',item=self.queue(),key='g1-paused-new-request')
            code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=eq.'+first['case_id'],token=self.tokens['c2'])
            self.assertEqual((code,len(rows)),(200,1))
        finally:self.pause(False)

    def test_06_invalid_real_bearer_signature_denied(self):
        token=self.tokens['m1'];parts=token.split('.');parts[2]=('a' if parts[2][0]!='a' else 'b')+parts[2][1:]
        self.tokens['m1']='.'.join(parts);self.reject('DENIED')

    def test_07_expired_live_session_denied(self):
        sid=self.fresh_manager_session()
        with psycopg.connect(self.db) as c:c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(sid,))
        self.reject('DENIED')

    def test_08_revoked_a_does_not_grant_or_revoke_b(self):
        with psycopg.connect(self.db) as c:c.execute('update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s and concessionaria_id=%s',(self.people['m1'][0],self.shops['A']))
        self.reject('DENIED');self.assigned(shop='B')

    def after_lead_wait(self,change,state,restore=None):
        with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute('select id from public.leads_loja where id=%s for update',(self.items['A'][0],))
            pid=c.execute('select pg_backend_pid()').fetchone()[0];future=pool.submit(self.call)
            try:self.wait_blocker(pid);change()
            finally:c.commit()
            try:self.assertEqual(future.result(timeout=15).state.value,state)
            finally:
                if restore:restore()

    def test_09_team_change_while_waiting_is_rechecked(self):
        def change(end):
            with psycopg.connect(self.db) as c:c.execute('update prumo_private.s1_gestor_operadores set encerrado_em='+('clock_timestamp()' if end else 'null')+' where operador_id=%s',(self.people['c2'][0],))
        self.after_lead_wait(lambda:change(True),'DESTINATION_INELIGIBLE',lambda:change(False))
        self.assertEqual(self.facts()[0:3],(0,0,0))

    def test_10_pause_wins_during_lead_wait(self):
        self.after_lead_wait(lambda:self.pause(True),'INTAKE_PAUSED',lambda:self.pause(False))
        self.assertEqual(self.facts()[0:3],(0,0,0))

    def test_11_manager_grant_revoked_during_lead_wait(self):
        def revoke():
            with psycopg.connect(self.db) as c:c.execute('update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s and concessionaria_id=%s',(self.people['m1'][0],self.shops['A']))
        self.after_lead_wait(revoke,'DENIED');self.assertEqual(self.facts()[0:3],(0,0,0))

    def test_12_session_delete_commits_before_command_gets_session_lock(self):
        sid=self.fresh_manager_session()
        with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute('delete from auth.sessions where id=%s',(sid,));pid=c.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(self.call)
            try:self.wait_blocker(pid)
            finally:c.commit()
            self.assertEqual(future.result(timeout=15).state,g1.State.DENIED)

    def compete(self,kind,manual_first):
        def old(c):
            if kind=='claim':return self.claim(c)
            return c.execute('select prumo_private.s0_fila_distribuir(%s,%s,1)',(self.shops['A'],self.items['A'][1])).fetchone()[0]
        first_dsn=self.dsn if manual_first else (self.s1_dsn if kind=='claim' else self.db)
        with psycopg.connect(first_dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
            if manual_first:
                value=c.execute(g1._SQL,self.proof()).fetchone()[0];self.assertEqual(value['outcome'],'MANUAL_ASSIGNED')
                def other():
                    with psycopg.connect(self.s1_dsn if kind=='claim' else self.db) as x:return old(x)
                future=pool.submit(other)
            else:
                value=old(c);self.assertIn(value['outcome'],('CLAIMED_BY_MANAGER','ASSIGNED_NEW'))
                future=pool.submit(self.call)
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            try:self.wait_blocker(pid)
            finally:c.commit()
            result=future.result(timeout=15)
        if manual_first:self.assertEqual(result['outcome'],'CONFLICT')
        else:self.assertEqual(result.state,g1.State.STALE)
        self.assertEqual(self.facts()[0:2],(1,1))

    def test_13_signed_i55_claim_wins(self):self.compete('claim',False)
    def test_14_manual_wins_over_signed_i55_claim(self):self.compete('claim',True)
    def test_15_original_automatic_distribution_wins(self):self.compete('auto',False)
    def test_16_manual_wins_over_original_distribution(self):self.compete('auto',True)

    def test_17_two_managers_each_with_own_team_one_winner(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(self.call);b=pool.submit(self.call,'m2',target='c3')
            results=[a.result(timeout=15),b.result(timeout=15)]
        self.assertEqual({r.state for r in results},{g1.State.MANUAL_ASSIGNED,g1.State.STALE})
        self.assertEqual(self.facts()[0:2],(1,1))

    def test_18_exact_retry_returns_same_receipt_without_new_assignment(self):
        first=self.assigned();second=self.call()
        self.assertEqual(second.state,g1.State.ALREADY_MANUAL_ASSIGNED);self.assertEqual(second.receipt,{**first,'outcome':'ALREADY_MANUAL_ASSIGNED'})
        self.assertEqual(self.facts()[0:3],(1,1,1))

    def test_19_key_reused_with_another_destination_conflicts(self):
        self.assigned();self.reject('IDEMPOTENCY_CONFLICT',target='c1')

    def test_20_key_reused_on_another_cycle_conflicts(self):
        self.assigned();self.reject('IDEMPOTENCY_CONFLICT',item=self.queue())

    def test_21_nonce_replay_and_tampered_destination_denied(self):
        proof=self.proof()
        with psycopg.connect(self.dsn) as c:c.execute(g1._SQL,proof).fetchone()
        before=self.facts()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(self.dsn) as c:c.execute(g1._SQL,proof)
        self.assertEqual(self.facts(),before)
        changed=list(self.proof());changed[4]=self.people['c1'][0]
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(self.dsn) as c:c.execute(g1._SQL,changed)
        self.assertEqual(self.facts(),before)

    def test_22_original_i62_signed_revocation_removes_access_and_blocks_replay(self):
        result=self.assigned();exc=UUID(result['exception_id'])
        principal,issued,nonce,mac=self.s1_proof('EXC62R',(exc,None,None,None,None,'R'),'m1')
        with psycopg.connect(self.s1_dsn) as c:
            value=c.execute('select prumo_s1_signed_i20.invocar_excecao_i62(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (principal.actor_id,principal.session_id,'REVOKE',exc,None,None,None,self.s1_key,issued,nonce,mac)).fetchone()[0]
        self.assertEqual(value['outcome'],'REVOKED_CASE_ACCESS');self.reject('DENIED')
        code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=eq.'+result['case_id'],token=self.tokens['c2'])
        self.assertEqual((code,rows),(200,[]))

    def fault(self,table,deferred=False):
        name='g1_fault_'+uuid4().hex
        with psycopg.connect(self.db) as c:
            open_before=c.execute("select count(*) from pg_stat_activity where usename='prumo_cfi01_pgtest_login'").fetchone()[0]
            c.execute(sql.SQL("create function prumo_private.{}() returns trigger language plpgsql as $$ begin raise exception 'G1_DISPOSABLE_FAULT'; end $$").format(sql.Identifier(name)))
            trigger=('create constraint trigger {} after insert on {} deferrable initially deferred for each row execute function prumo_private.{}()' if deferred else 'create trigger {} before insert on {} for each row execute function prumo_private.{}()')
            c.execute(sql.SQL(trigger).format(sql.Identifier(name),sql.Identifier('prumo_private' if table!='atribuicoes_humanas' else 'public',table),sql.Identifier(name)))
        try:
            self.reject('UNAVAILABLE')
            with psycopg.connect(self.db) as c:
                self.assertLessEqual(c.execute("select count(*) from pg_stat_activity where usename='prumo_cfi01_pgtest_login'").fetchone()[0],open_before)
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on {}').format(sql.Identifier(name),sql.Identifier('prumo_private' if table!='atribuicoes_humanas' else 'public',table)))
                c.execute(sql.SQL('drop function prumo_private.{}()').format(sql.Identifier(name)))
        self.assigned()

    def test_23_exception_creation_failure_rolls_back_case(self):self.fault('s1_excecoes_caso_i61')
    def test_24_assignment_failure_rolls_back_exception(self):self.fault('atribuicoes_humanas')
    def test_25_late_audit_failure_rolls_back_queue_case_nonce_and_request(self):self.fault('g1_manual_audit_local')
    def test_26_deferred_commit_failure_never_returns_success(self):self.fault('g1_manual_audit_local',True)

    def test_27_response_validation_is_before_commit(self):
        corrupt="select x.result || jsonb_build_object('version',0) from ("+g1._SQL+") x(result)"
        with patch.object(g1,'_SQL',corrupt):self.reject('UNAVAILABLE')
        self.assigned()

    def test_28_grant_expiry_is_checked_after_lock_wait(self):
        with psycopg.connect(self.db) as c:c.execute("update public.vinculos_papel_escopo set valido_ate=clock_timestamp()+interval '1 second' where ator_id=%s and concessionaria_id=%s",(self.people['m1'][0],self.shops['A']))
        self.after_lead_wait(lambda:time.sleep(1.2),'DENIED')

    def test_29_real_logout_revokes_same_jwt(self):
        self.fresh_manager_session()
        self.assertIn(request(self.api,self.anon,'POST','/auth/v1/logout?scope=local',token=self.tokens['m1'])[0],(200,204))
        self.reject('DENIED')

    def test_30_intake_pause_waits_for_committing_assignment(self):
        with psycopg.connect(self.dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute(g1._SQL,self.proof()).fetchone();pid=c.execute('select pg_backend_pid()').fetchone()[0]
            pending=pool.submit(self.pause,True)
            try:self.wait_blocker(pid)
            finally:c.commit()
            pending.result(timeout=15)
        try:
            self.assertEqual(self.facts()[0:3],(1,1,1));self.reject('INTAKE_PAUSED')
        finally:self.pause(False)

    def test_31_no_queue_signal_and_no_self_transfer(self):
        item=self.queue(signal=False);self.reject('DENIED',item=item)
        self.assigned();self.reject('STALE',target='c1',key='g1-new-key-no-transfer',version=2)

    def test_32_private_acl_no_global_grant_or_owner_role(self):
        signatures=['prumo_private.g1_manual_signed_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid,bigint,uuid,text)',
                    'prumo_private.g1_manual_bridge_local(uuid,uuid,uuid,uuid,uuid,bigint,text,uuid)']
        with psycopg.connect(self.db) as c:
            for role in ('anon','authenticated','service_role'):
                for fn in signatures:self.assertFalse(c.execute('select has_function_privilege(%s,%s,\'EXECUTE\')',(role,fn)).fetchone()[0])
            self.assertFalse(c.execute('select has_function_privilege(%s,%s,\'EXECUTE\')',('prumo_cfi01_pgtest_login',signatures[1])).fetchone()[0])
            self.assertEqual(c.execute("select rolcanlogin,rolsuper,rolbypassrls from pg_roles where rolname='prumo_s0_g1_executor_local'").fetchone(),(False,False,False))
            self.assertFalse(c.execute("select has_schema_privilege('prumo_s0_g1_executor_local','prumo_private','CREATE')").fetchone()[0])
            self.assertFalse(c.execute("select pg_has_role('prumo_cfi01_pgtest_login','prumo_s0_g1_executor_local','MEMBER')").fetchone()[0])
        for query in ('set role prumo_s0_g1_executor_local','select * from prumo_private.s0_fila_humana','select * from prumo_private.g1_manual_requests_local'):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(self.dsn) as c:c.execute(query)

    def test_33_external_i56_case_creation_wins_without_duplicate(self):
        with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute('insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id) values (%s,%s,%s)',(self.shops['A'],*self.items['A']))
            pid=c.execute('select pg_backend_pid()').fetchone()[0];pending=pool.submit(self.call)
            try:self.wait_blocker(pid)
            finally:c.commit()
            self.assertEqual(pending.result(timeout=15).state,g1.State.STALE)
        self.assertEqual(self.facts()[0:3],(1,0,0))

    def test_34_second_manager_without_b_grant_cannot_forward_b(self):
        self.reject('DENIED',who='m2',shop='B',target='c3')
        self.assigned(shop='B')

    def test_35_case_exception_does_not_expose_other_store_or_team_cases(self):
        own=self.assigned()
        other_store=self.assigned(shop='B',target='c1')
        other_team=self.assigned(who='m2',target='c3',item=self.queue(),key='g1-other-team-visibility')
        ids=','.join(x['case_id'] for x in (own,other_store,other_team))
        code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=in.('+ids+')',token=self.tokens['c2'])
        self.assertEqual(code,200);self.assertEqual({r['id'] for r in rows},{own['case_id']})

    def test_36_concurrent_same_key_creates_one_assignment_and_one_request(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(self.call) for _ in range(2)]
            results=[f.result(timeout=15) for f in futures]
        self.assertEqual({r.state for r in results},{g1.State.MANUAL_ASSIGNED,g1.State.ALREADY_MANUAL_ASSIGNED})
        self.assertEqual(results[0].receipt['request_id'],results[1].receipt['request_id'])
        self.assertEqual(self.facts()[0:3],(1,1,1));self.assertEqual(self.facts()[4:6],(1,2))


if __name__=='__main__':unittest.main(verbosity=2)
