"""Real GoTrue/PG17/PostgREST I79 plus ALL 36 inherited G1 regressions.

Original G1 assertions retained; two setup hooks now use Director admission and
an actual CAS transfer instead of creating/reopening an orphan management row.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import unittest
from unittest.mock import patch
from uuid import UUID,uuid4
import psycopg
from psycopg import sql
from backend import s1_professionals_local as admin_module
from integration.g1.test_manual_handoff import G1Tests as OriginalG1
from scripts.test_s0_cfi01_auth_rest_local import register,request


class I79Tests(OriginalG1):
    @classmethod
    def seed_professionals(cls):
        if os.environ.get('PRUMO_I79_DISPOSABLE_TEST')!='YES':raise RuntimeError('I79 opt-in required')
        cls.director,cls.director_token=register(cls.api,cls.anon)
        # Bootstrap existing Director authority, ONLY by disposable installer.
        # No client/admin command can appoint itself or another Director.
        with psycopg.connect(cls.db) as c:
            c.execute('insert into public.atores(id) values (%s)',(cls.director,))
            c.execute('insert into prumo_private.s1_responsaveis_plataforma(ator_id) values (%s)',(cls.director,))
            c.execute("insert into public.equipe_prumo_s1(ator_id,cargo,estado) values (%s,'diretor','ativo')",(cls.director,))
        cls.admin=admin_module.S1ProfessionalsLocal(cls.gateway)
        for name in ('m1','m2','c1','c2','c3'):
            target=cls.people[name][0];cargo='gestor' if name.startswith('m') else 'consultor'
            manager=None if cargo=='gestor' else cls.people['m2' if name=='c3' else 'm1'][0]
            for action in ('REGISTER','ACTIVATE'):
                result=cls.admin.execute('Bearer '+cls.director_token,cls.dto(action,target,cargo,manager if action=='ACTIVATE' else None))
                if result.state!='APPLIED':
                    # Fixed SQL diagnostic only; never log proof/DSN/JWT/keys.
                    p=cls.dto(action,target,cargo,manager if action=='ACTIVATE' else None)
                    principal=cls.gateway._identity.verify('Bearer '+cls.director_token)
                    try:
                        with psycopg.connect(cls.dsn) as c:c.execute(admin_module.SQL,cls.admin.proof(principal,admin_module.command(p)))
                    except psycopg.Error as error:
                        raise RuntimeError('I79 bootstrap SQL '+str(error.sqlstate)+' '+str(error.diag.message_primary)) from None
                assert result.state=='APPLIED',(name,action,result.state)

    @staticmethod
    def dto(action,target,cargo='consultor',manager=None,previous=0,key=None):
        return dict(action=action,target_id=str(target),cargo=cargo,manager_id=str(manager) if manager else None,
                    expected_relationship_id=previous,idempotency_key=key or 'i79-'+uuid4().hex)

    def admin_call(self,payload,token=None):return self.admin.execute('Bearer '+(token or self.director_token),payload)
    def relation(self,name='c2'):
        actor=self.people[name][0] if isinstance(name,str) else name
        with psycopg.connect(self.db) as c:return c.execute('select id,gestor_id from prumo_private.s1_gestor_operadores where operador_id=%s and encerrado_em is null',(actor,)).fetchone()
    def transfer(self,name='c2',manager='m2',**kwargs):
        actor=self.people[name][0] if isinstance(name,str) else name
        destination=self.people[manager][0] if isinstance(manager,str) else manager
        return self.admin_call(self.dto('TRANSFER',actor,manager=destination,previous=self.relation(actor)[0],**kwargs))
    def change_team_for_test(self,end):
        result=self.transfer(manager='m2' if end else 'm1')
        self.assertEqual(result.state,'APPLIED')
    def counters(self):
        with psycopg.connect(self.db) as c:return tuple(c.execute('select count(*) from '+table).fetchone()[0] for table in (
            'prumo_private.s1_i79_requests','prumo_private.s1_i79_audit','prumo_private.cfi01_consumed_nonces_local','prumo_private.s1_gestor_operadores'))
    def new_person(self,cargo='consultor',activate=False):
        actor,token=register(self.api,self.anon)
        self.assertEqual(self.admin_call(self.dto('REGISTER',actor,cargo)).state,'APPLIED')
        if activate:self.assertEqual(self.admin_call(self.dto('ACTIVATE',actor,cargo,self.people['m1'][0] if cargo=='consultor' else None)).state,'APPLIED')
        return actor,token
    def transfer_payload(self,**kwargs):return self.dto('TRANSFER',self.people['c2'][0],manager=self.people['m2'][0],previous=self.relation()[0],**kwargs)

    def test_40_director_registers_pending_and_atomically_activates_consultant(self):
        actor,_=self.new_person()
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select cargo,estado from public.equipe_prumo_s1 where ator_id=%s',(actor,)).fetchone(),('consultor','pendente'))
        result=self.admin_call(self.dto('ACTIVATE',actor,manager=self.people['m1'][0]))
        self.assertEqual(result.state,'APPLIED');self.assertEqual(self.relation(actor)[1],self.people['m1'][0])
        with psycopg.connect(self.db) as c:self.assertEqual(c.execute('select count(*) from public.vinculos_papel_escopo where ator_id=%s',(actor,)).fetchone()[0],0)

    def test_41_active_consultant_without_manager_cannot_commit(self):
        actor,_=self.new_person()
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(self.db) as c:c.execute("update public.equipe_prumo_s1 set estado='ativo' where ator_id=%s",(actor,))
        with psycopg.connect(self.db) as c:self.assertEqual(c.execute('select estado from public.equipe_prumo_s1 where ator_id=%s',(actor,)).fetchone()[0],'pendente')

    def test_42_manager_without_children_has_authoritative_role_and_accepts_transfer(self):
        actor,_=self.new_person('gestor',True)
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select prumo_private.s1_i79_cargo(%s)',(actor,)).fetchone()[0],'gestor')
            self.assertEqual(c.execute('select count(*) from prumo_private.s1_gestor_operadores where gestor_id=%s',(actor,)).fetchone()[0],0)
        try:self.assertEqual(self.transfer(manager=actor).state,'APPLIED')
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def test_43_manager_cannot_register_or_transfer_as_director(self):
        before=self.counters()
        for p in (self.dto('REGISTER',uuid4()),self.transfer_payload()):
            self.assertEqual(self.admin_call(p,self.tokens['m1']).state,'DENIED')
        self.assertEqual(self.counters(),before)

    def test_44_duplicate_active_manager_rejected_physically(self):
        before=self.relation()
        with self.assertRaises(psycopg.errors.UniqueViolation):
            with psycopg.connect(self.db) as c:c.execute('insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values (%s,%s)',(self.people['m2'][0],self.people['c2'][0]))
        self.assertEqual(self.relation(),before)

    def test_45_two_director_commands_one_cas_winner(self):
        a=self.transfer_payload();b={**a,'idempotency_key':'i79-other-'+uuid4().hex}
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=[f.result(timeout=15) for f in [pool.submit(self.admin_call,a),pool.submit(self.admin_call,b)]]
            self.assertEqual({r.state for r in results},{'APPLIED','STALE'})
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def test_46_old_relation_cas_stale_even_if_destination_still_manager(self):
        p=self.transfer_payload()
        try:
            self.assertEqual(self.admin_call(p).state,'APPLIED');before=self.counters()
            self.assertEqual(self.admin_call({**p,'idempotency_key':'i79-stale-'+uuid4().hex}).state,'STALE')
            self.assertEqual(self.counters(),before)
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def test_47_concurrent_identical_key_one_durable_request(self):
        p=self.transfer_payload();before=self.counters()
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=[f.result(timeout=15) for f in [pool.submit(self.admin_call,p),pool.submit(self.admin_call,p)]]
            self.assertEqual({r.state for r in results},{'APPLIED','ALREADY_APPLIED'})
            self.assertEqual(results[0].receipt['relationship_id'],results[1].receipt['relationship_id'])
            after=self.counters();self.assertEqual(after[0]-before[0],1);self.assertEqual(after[3]-before[3],1)
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def test_48_key_reuse_payload_conflict(self):
        p=self.transfer_payload()
        try:
            self.assertEqual(self.admin_call(p).state,'APPLIED');before=self.counters()
            self.assertEqual(self.admin_call({**p,'target_id':str(self.people['c1'][0])}).state,'CONFLICT')
            self.assertEqual(self.counters(),before)
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def fresh_director_token(self):
        with psycopg.connect(self.db) as c:email=c.execute('select email from auth.users where id=%s',(self.director,)).fetchone()[0]
        code,body=request(self.api,self.anon,'POST','/auth/v1/token?grant_type=password',{'email':email,'password':'Only-Local-CFI01-Test!X8b2'})
        self.assertEqual(code,200);return body['access_token']

    def test_49_real_logout_revokes_same_director_jwt(self):
        token=self.fresh_director_token()
        self.assertIn(request(self.api,self.anon,'POST','/auth/v1/logout?scope=local',token=token)[0],(200,204))
        before=self.counters();self.assertEqual(self.admin_call(self.transfer_payload(),token).state,'DENIED');self.assertEqual(self.counters(),before)

    def set_director(self,active):
        with psycopg.connect(self.db) as c:c.execute('update prumo_private.s1_responsaveis_plataforma set ativo=%s where ator_id=%s',(active,self.director))

    def test_50_global_director_competence_revoked_no_shop_grant_fallback(self):
        self.set_director(False)
        try:
            before=self.counters();self.assertEqual(self.admin_call(self.transfer_payload()).state,'DENIED');self.assertEqual(self.counters(),before)
        finally:self.set_director(True)

    def test_51_revocation_commits_while_command_waits_then_rechecks(self):
        p=self.transfer_payload()
        try:
            with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
                c.execute('select id from public.atores where id=%s for update',(self.people['c2'][0],));pid=c.execute('select pg_backend_pid()').fetchone()[0]
                pending=pool.submit(self.admin_call,p)
                try:self.wait_blocker(pid);self.set_director(False)
                finally:c.commit()
                self.assertEqual(pending.result(timeout=15).state,'DENIED')
        finally:self.set_director(True)

    def test_52_director_revocation_waits_for_inflight_commit(self):
        p=self.transfer_payload();principal=self.gateway._identity.verify('Bearer '+self.director_token)
        try:
            with psycopg.connect(self.dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
                c.execute(admin_module.SQL,self.admin.proof(principal,admin_module.command(p))).fetchone()
                pid=c.execute('select pg_backend_pid()').fetchone()[0];pending=pool.submit(self.set_director,False)
                try:self.wait_blocker(pid)
                finally:c.commit()
                pending.result(timeout=15)
            self.assertEqual(self.admin_call(p).state,'DENIED')
        finally:
            self.set_director(True);self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def test_53_session_expiry_denied_with_unexpired_jwt(self):
        token=self.fresh_director_token();principal=self.gateway._identity.verify('Bearer '+token)
        with psycopg.connect(self.db) as c:c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(principal.session_id,))
        before=self.counters();self.assertEqual(self.admin_call(self.transfer_payload(),token).state,'DENIED');self.assertEqual(self.counters(),before)

    def test_54_transfer_changes_supervision_not_cases_grants_or_paused_intake(self):
        case=self.assigned(target='c1');actor=self.people['c1'][0]
        def pause(manager,flag,version):
            with psycopg.connect(self.db) as c:c.execute('select prumo_private.s1_definir_intake(%s,%s,%s,%s)',(self.people[manager][0],actor,flag,version))
        pause('m1',True,1)
        try:
            self.assertEqual(self.transfer(name='c1').state,'APPLIED')
            with psycopg.connect(self.db) as c:
                self.assertEqual(c.execute('select pausado from prumo_private.s1_intake_estado where operador_id=%s',(actor,)).fetchone()[0],True)
                self.assertEqual(c.execute('select operador_id,encerrada_em from public.atribuicoes_humanas where id=%s',(case['assignment_id'],)).fetchone(),(actor,None))
                self.assertEqual(c.execute('select count(*) from public.vinculos_papel_escopo where ator_id=%s and concessionaria_id=%s',(actor,self.shops['A'])).fetchone()[0],1)
            for who,count in [('c1',1),('m1',0),('m2',1)]:
                code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=eq.'+case['case_id'],token=self.tokens[who])
                self.assertEqual((code,len(rows)),(200,count))
        finally:
            self.assertEqual(self.transfer(name='c1',manager='m1').state,'APPLIED');pause('m1',False,2)

    def test_55_manager_cannot_deactivate_leaving_active_consultant_orphan(self):
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(self.db) as c:c.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",(self.people['m1'][0],))
        self.assertEqual(self.relation()[1],self.people['m1'][0])

    def admin_fault(self,deferred=False):
        name='i79_fault_'+uuid4().hex;p=self.transfer_payload();old=self.relation();before=self.counters()
        with psycopg.connect(self.db) as c:
            c.execute(sql.SQL("create function prumo_private.{}() returns trigger language plpgsql as $$ begin raise exception 'I79_DISPOSABLE_FAULT';end $$").format(sql.Identifier(name)))
            trigger='create constraint trigger {} after insert on prumo_private.s1_i79_audit deferrable initially deferred for each row execute function prumo_private.{}()' if deferred else 'create trigger {} before insert on prumo_private.s1_i79_audit for each row execute function prumo_private.{}()'
            c.execute(sql.SQL(trigger).format(sql.Identifier(name),sql.Identifier(name)))
        try:
            self.assertEqual(self.admin_call(p).state,'UNAVAILABLE');self.assertEqual(self.relation(),old);self.assertEqual(self.counters(),before)
            with psycopg.connect(self.db) as c:self.assertEqual(c.execute("select count(*) from pg_stat_activity where usename='prumo_cfi01_pgtest_login'").fetchone()[0],0)
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on prumo_private.s1_i79_audit').format(sql.Identifier(name)))
                c.execute(sql.SQL('drop function prumo_private.{}()').format(sql.Identifier(name)))
        try:self.assertEqual(self.admin_call(p).state,'APPLIED')
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def test_56_partial_failure_restores_previous_relation_and_audit(self):self.admin_fault()
    def test_57_deferred_commit_failure_rolls_back_and_closes_connection(self):self.admin_fault(True)

    def test_58_nonce_replay_and_payload_tamper_denied(self):
        p=self.transfer_payload();principal=self.gateway._identity.verify('Bearer '+self.director_token)
        proof=self.admin.proof(principal,admin_module.command(p))
        try:
            with psycopg.connect(self.dsn) as c:c.execute(admin_module.SQL,proof)
            before=self.counters()
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(self.dsn) as c:c.execute(admin_module.SQL,proof)
            changed=list(proof);changed[3]=self.people['c1'][0]
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(self.dsn) as c:c.execute(admin_module.SQL,changed)
            self.assertEqual(self.counters(),before)
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')

    def test_59_malformed_return_rolls_back_before_commit(self):
        p=self.transfer_payload();before=self.counters();old=self.relation()
        corrupt="select v.r || jsonb_build_object('relationship_id','0') from ("+admin_module.SQL+") v(r)"
        with patch.object(admin_module,'SQL',corrupt):self.assertEqual(self.admin_call(p).state,'UNAVAILABLE')
        self.assertEqual(self.counters(),before);self.assertEqual(self.relation(),old)

    def test_60_legacy_unclassified_account_cannot_receive_new_assignment(self):
        actor,_=register(self.api,self.anon)
        with psycopg.connect(self.db) as c:
            c.execute('insert into public.atores(id) values (%s)',(actor,))
            c.execute("insert into public.equipe_prumo_s1(ator_id,estado) values (%s,'ativo')",(actor,))
            c.execute("insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values (%s,%s,'operador')",(actor,self.shops['A']))
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(self.db) as c:
                case=c.execute('insert into public.casos_humanos(concessionaria_id,lead_id,ciclo_id) values (%s,%s,%s) returning id',(self.shops['A'],*self.items['A'])).fetchone()[0]
                c.execute('insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id) values (%s,%s,%s)',(self.shops['A'],case,actor))

    def test_61_private_acl_does_not_grant_director_to_sql_login(self):
        with psycopg.connect(self.db) as c:
            for role in ('anon','authenticated','service_role','prumo_cfi01_pgtest_login'):
                self.assertFalse(c.execute("select has_function_privilege(%s,'prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)','EXECUTE')",(role,)).fetchone()[0])
            for role in ('anon','authenticated','service_role'):
                self.assertFalse(c.execute("select has_function_privilege(%s,'prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text)','EXECUTE')",(role,)).fetchone()[0])

    def test_62_auto_distribution_skips_unclassified_and_uses_canonical_classifier(self):
        # Both classified candidates have one open case; the legacy candidate
        # has zero. Without the selector adaptation it would win and fail late.
        self.assigned(target='c1',item=self.queue(),key='i79-auto-load-c1')
        self.assigned(who='m2',target='c3',item=self.queue(),key='i79-auto-load-c3')
        actor,_=register(self.api,self.anon)
        with psycopg.connect(self.db) as c:
            c.execute('insert into public.atores(id) values (%s)',(actor,))
            c.execute("insert into public.equipe_prumo_s1(ator_id,estado) values (%s,'ativo')",(actor,))
            c.execute('insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values (%s,%s)',(self.people['m1'][0],actor))
            c.execute("insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values (%s,%s,'operador')",(actor,self.shops['A']))
        with psycopg.connect(self.db) as c:
            result=c.execute('select prumo_private.s0_fila_distribuir(%s,%s,1)',(self.shops['A'],self.items['A'][1])).fetchone()[0]
            self.assertEqual(result['outcome'],'ASSIGNED_NEW')
            self.assertEqual(c.execute('select cargo from public.equipe_prumo_s1 where ator_id=%s',(result['operator_id'],)).fetchone()[0],'consultor')

    def test_63_empty_manager_can_self_claim_but_is_not_a_consultant_destination(self):
        actor,token=self.new_person('gestor',True);self.tokens['empty_manager']=token
        with psycopg.connect(self.db) as c:c.execute("insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values (%s,%s,'gestor')",(actor,self.shops['A']))
        principal,issued,nonce,mac=self.s1_proof('FILA55C',(self.shops['A'],self.items['A'][1],None,None,None,'C:1'),'empty_manager')
        with psycopg.connect(self.s1_dsn) as c:
            result=c.execute('select prumo_s1_signed_i20.invocar_fila_v55(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (principal.actor_id,principal.session_id,self.shops['A'],self.items['A'][1],1,self.s1_key,issued,nonce,mac)).fetchone()[0]
        self.assertEqual(result['outcome'],'CLAIMED_BY_MANAGER')
        # No B grant and no subordinate: the former inference would mistake it
        # for a consultant, so the new G1 role guard must roll back that attempt.
        before=self.facts();p={**self.payload(shop='B'),'consultor_id':str(actor)}
        self.assertEqual(self.call(payload=p).state.value,'DESTINATION_INELIGIBLE');self.assertEqual(self.facts(),before)

    def test_64_old_case_exception_never_revives_after_return_to_original_manager(self):
        case=self.assigned();exception=UUID(case['exception_id'])
        try:self.assertEqual(self.transfer().state,'APPLIED')
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')
        with psycopg.connect(self.db) as c:
            self.assertIsNotNone(c.execute('select revogada_em from prumo_private.s1_excecoes_caso_i61 where id=%s',(exception,)).fetchone()[0])
            self.assertEqual(c.execute("select count(*) from prumo_private.s1_excecoes_caso_eventos_i61 where excecao_id=%s and evento='REVOGADA' and solicitante_id=%s",(exception,self.director)).fetchone()[0],1)
        code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=eq.'+case['case_id'],token=self.tokens['c2'])
        self.assertEqual((code,rows),(200,[]));self.reject('DENIED')

    def test_65_busy_i61_exception_aborts_chefia_transfer_without_lock_inversion(self):
        case=self.assigned();before=self.relation();p=self.transfer_payload()
        with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute('select id from prumo_private.s1_excecoes_caso_i61 where id=%s for update',(case['exception_id'],))
            pending=pool.submit(self.admin_call,p)
            result=pending.result(timeout=5)  # Must not wait on the exception while holding team.
            self.assertEqual(result.state,'UNAVAILABLE');self.assertEqual(self.relation(),before)
            c.commit()
        try:self.assertEqual(self.admin_call(p).state,'APPLIED')
        finally:self.assertEqual(self.transfer(manager='m1').state,'APPLIED')


if __name__=='__main__':
    # Do not collect OriginalG1 as an extra unclassified test class.
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(I79Tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
