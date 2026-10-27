"""Real I80 on the SAME disposable PG17/GoTrue stack after all 62 I79 tests.

Fixture-only postgres quarantines fresh synthetic professionals as legacy by
setting cargo NULL, preserving existing guards, assignments and history. All
administrative previews/applies use real Director GoTrue sessions and SQL login.
"""
from concurrent.futures import ThreadPoolExecutor
import os
import unittest
from unittest.mock import patch
from uuid import UUID,uuid4
import psycopg
from psycopg import sql
from backend import s1_legacy_regularization_local as regularization
from integration.i79.test_professionals import I79Tests as FoundationTests
from scripts.test_s0_cfi01_auth_rest_local import request,register


class I80Tests(FoundationTests):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_I80_DISPOSABLE_TEST')!='YES':raise RuntimeError('I80 opt-in required')
        super().setUpClass();cls.regularizer=regularization.S1LegacyRegularizationLocal(cls.gateway)

    @staticmethod
    def wire(action,target=None,cargo=None,manager=None,expected=None,preview=None,cursor=None,limit=0,key=None):
        return dict(action=action,target_id=str(target) if target else None,cargo=cargo,manager_id=str(manager) if manager else None,
         expected_sha256=expected,preview_id=str(preview) if preview else None,cursor=str(cursor) if cursor else None,
         limit=limit,idempotency_key=key or 'i80-'+uuid4().hex)
    def run_command(self,p,token=None):return self.regularizer.execute('Bearer '+(token or self.director_token),p)
    def inventory_item(self,target,token=None):
        cursor=None
        for _ in range(100):
            r=self.run_command(self.wire('INVENTORY',cursor=cursor,limit=50),token)
            self.assertEqual(r.state,'INVENTORY')
            for item in r.receipt['items']:
                if item['target_id']==str(target):return item
            if not r.receipt['has_more']:break
            cursor=r.receipt['next_cursor']
        self.fail('fixture target absent from authorized legacy inventory')
    def preview(self,target,cargo='consultor',manager=None,token=None,key=None):
        item=self.inventory_item(target,token)
        p=self.wire('PREVIEW',target,cargo,manager,item['inventory_sha256'],key=key)
        r=self.run_command(p,token);self.assertIn(r.state,('READY','BLOCKED'));return r.receipt,p
    def apply_wire(self,preview,key=None):
        return self.wire('APPLY',preview['target_id'],preview['cargo'],preview['manager_id'],preview['snapshot_sha256'],preview['preview_id'],key=key)
    def apply(self,preview,token=None,key=None):return self.run_command(self.apply_wire(preview,key),token)
    def legacy(self,pending=False,orphan=False,exception=False,case=True):
        actor,token=self.new_person(activate=not pending)
        receipt=None
        if not pending:
            with psycopg.connect(self.db) as c:
                for shop in ('B',) if exception else ('A','B'):
                    c.execute("insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel,valido_ate) values (%s,%s,'operador',clock_timestamp()+interval '1 day')",(actor,self.shops[shop]))
            if case:
                r=self.call(payload={**self.payload(key='i80-case-'+uuid4().hex),'consultor_id':str(actor)})
                self.assertEqual(r.state.value,'MANUAL_ASSIGNED');receipt=r.receipt
                with psycopg.connect(self.db) as c:
                    channel=c.execute('insert into public.canais_loja(concessionaria_id,identificador_emissor) values (%s,%s) returning id',(self.shops['A'],'i80-'+uuid4().hex)).fetchone()[0]
                    conv=c.execute('insert into public.conversas(concessionaria_id,lead_id,canal_id,caso_id) values (%s,%s,%s,%s) returning id',
                        (self.shops['A'],self.items['A'][0],channel,receipt['case_id'])).fetchone()[0]
                    c.execute("insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo) values (%s,%s,%s,%s,'entrada','I80 synthetic history',%s)",
                        (self.shops['A'],conv,channel,receipt['case_id'],'i80-'+uuid4().hex))
        # Import/quarantine fixture, not an application or production command.
        # It does not disable any FK, RLS, trigger or I79 assignment guard.
        with psycopg.connect(self.db) as c:
            c.execute('update public.equipe_prumo_s1 set cargo=null where ator_id=%s',(actor,))
            if orphan:c.execute('update prumo_private.s1_gestor_operadores set encerrado_em=greatest(atribuido_em,clock_timestamp()) where operador_id=%s and encerrado_em is null',(actor,))
        return actor,token,receipt
    def preserved(self,actor):
        with psycopg.connect(self.db) as c:
            result={'state':c.execute('select estado from public.equipe_prumo_s1 where ator_id=%s',(actor,)).fetchone()[0]}
            for table,where in (
                ('public.vinculos_papel_escopo','ator_id=%s'),('prumo_private.s1_intake_estado','operador_id=%s'),
                ('public.atribuicoes_humanas','operador_id=%s'),
                ('public.casos_humanos','id in(select caso_id from public.atribuicoes_humanas where operador_id=%s)'),
                ('public.conversas','caso_id in(select caso_id from public.atribuicoes_humanas where operador_id=%s)'),
                ('public.mensagens','caso_id in(select caso_id from public.atribuicoes_humanas where operador_id=%s)')):
                result[table]=c.execute('select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text),\'[]\') from '+table+' t where '+where,(actor,)).fetchone()[0]
            return result
    def cargo(self,actor):
        with psycopg.connect(self.db) as c:return c.execute('select cargo from public.equipe_prumo_s1 where ator_id=%s',(actor,)).fetchone()[0]

    def test_i80_01_director_inventory_minimized_paginated_and_manager_denied(self):
        actor,_,_=self.legacy(pending=True)
        item=self.inventory_item(actor);self.assertIsNone(item['cargo']);self.assertEqual(item['estado'],'pendente')
        p=self.wire('INVENTORY',limit=1);a=self.run_command(p);self.assertEqual(a.state,'INVENTORY')
        if a.receipt['has_more']:
            b=self.run_command(self.wire('INVENTORY',limit=1,cursor=a.receipt['next_cursor']))
            self.assertGreater(b.receipt['items'][0]['target_id'],a.receipt['items'][0]['target_id'])
        self.assertEqual(self.run_command(p,self.tokens['m1']).state,'DENIED')

    def test_i80_02_preview_is_not_classification_or_activation(self):
        actor,_,_=self.legacy(orphan=True);before=self.preserved(actor)
        p,_=self.preview(actor,manager=self.people['m1'][0]);self.assertEqual(p['outcome'],'READY')
        self.assertIsNone(self.cargo(actor));self.assertIsNone(self.relation(actor));self.assertEqual(self.preserved(actor),before)

    def test_i80_03_apply_preserves_both_stores_case_history_intake_and_grants(self):
        actor,token,case=self.legacy(orphan=True);before=self.preserved(actor)
        p,_=self.preview(actor,manager=self.people['m1'][0]);r=self.apply(p)
        self.assertEqual(r.state,'APPLIED');self.assertEqual(self.cargo(actor),'consultor')
        self.assertEqual(self.relation(actor)[1],self.people['m1'][0]);self.assertEqual(self.preserved(actor),before)
        code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=eq.'+case['case_id'],token=token)
        self.assertEqual((code,len(rows)),(200,1))

    def test_i80_04_preserve_same_relation_and_valid_i61_without_new_grant(self):
        actor,_,case=self.legacy(exception=True);old=self.relation(actor);before=self.preserved(actor)
        p,_=self.preview(actor,manager=self.people['m1'][0]);self.assertFalse(p['impact']['change_relationship'])
        self.assertEqual(p['impact']['revoke_exception_ids'],[]);self.assertEqual(self.apply(p).state,'APPLIED')
        self.assertEqual(self.relation(actor),old);self.assertEqual(self.preserved(actor),before)
        with psycopg.connect(self.db) as c:self.assertIsNone(c.execute('select revogada_em from prumo_private.s1_excecoes_caso_i61 where id=%s',(case['exception_id'],)).fetchone()[0])

    def test_i80_05_explicit_new_manager_revokes_i61_and_never_revives(self):
        actor,token,case=self.legacy(exception=True);before=self.preserved(actor)
        p,_=self.preview(actor,manager=self.people['m2'][0]);self.assertEqual(p['impact']['revoke_exception_ids'],[case['exception_id']])
        result=self.apply(p);self.assertEqual(result.state,'APPLIED');self.assertEqual(result.receipt['revoked_exception_count'],1)
        self.assertEqual(self.preserved(actor),before)
        r=self.admin_call(self.dto('TRANSFER',actor,manager=self.people['m1'][0],previous=self.relation(actor)[0]));self.assertEqual(r.state,'APPLIED')
        code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=eq.'+case['case_id'],token=token)
        self.assertEqual((code,rows),(200,[]))

    def test_i80_06_no_manager_choice_blocks_active_orphan(self):
        actor,_,_=self.legacy(orphan=True)
        p,_=self.preview(actor);self.assertIn('MANAGER_REQUIRED',p['blockers'])
        self.assertEqual(self.apply(p).state,'BLOCKED');self.assertIsNone(self.cargo(actor))

    def test_i80_07_manager_request_does_not_silently_close_parent(self):
        actor,_,_=self.legacy(case=False);old=self.relation(actor)
        p,_=self.preview(actor,'gestor');self.assertIn('MANAGER_HAS_PARENT_LINK',p['blockers'])
        self.assertEqual(self.apply(p).state,'BLOCKED');self.assertEqual(self.relation(actor),old)

    def test_i80_08_pending_stays_pending_then_existing_i79_activates(self):
        actor,_,_=self.legacy(pending=True);p,_=self.preview(actor);self.assertEqual(self.apply(p).state,'APPLIED')
        self.assertIsNone(self.relation(actor));self.assertEqual(self.preserved(actor)['state'],'pendente')
        result=self.admin_call(self.dto('ACTIVATE',actor,manager=self.people['m1'][0]));self.assertEqual(result.state,'APPLIED')

    def test_i80_09_pending_manager_link_is_not_invented_before_activation(self):
        actor,_,_=self.legacy(pending=True);p,_=self.preview(actor,manager=self.people['m1'][0])
        self.assertIn('PENDING_CHEFIA_USE_I79_ACTIVATION',p['blockers']);self.assertEqual(self.apply(p).state,'BLOCKED')

    def test_i80_10_explicit_manager_then_consultant_order_without_inference(self):
        boss,_=self.new_person('gestor',True);child,child_token=register(self.api,self.anon)
        self.assertEqual(self.admin_call(self.dto('REGISTER',child)).state,'APPLIED')
        self.assertEqual(self.admin_call(self.dto('ACTIVATE',child,manager=boss)).state,'APPLIED')
        with psycopg.connect(self.db) as c:c.execute('update public.equipe_prumo_s1 set cargo=null where ator_id=any(%s)',([boss,child],))
        blocked,_=self.preview(boss,'consultor',self.people['m1'][0]);self.assertIn('CONSULTANT_HAS_SUBORDINATES',blocked['blockers'])
        p,_=self.preview(child,manager=boss);self.assertIn('MANAGER_NOT_CLASSIFIED_ACTIVE',p['blockers'])
        p,_=self.preview(boss,'gestor');self.assertEqual(self.apply(p).state,'APPLIED')
        p,_=self.preview(child,manager=boss);self.assertEqual(self.apply(p).state,'APPLIED')

    def test_i80_11_inventory_to_preview_stale(self):
        actor,_,_=self.legacy(pending=True);item=self.inventory_item(actor)
        with psycopg.connect(self.db) as c:c.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",(actor,))
        result=self.run_command(self.wire('PREVIEW',actor,'consultor',expected=item['inventory_sha256']))
        self.assertEqual(result.state,'STALE');self.assertIsNone(self.cargo(actor))

    def test_i80_12_preview_detects_aba_same_visible_state(self):
        actor,_,_=self.legacy(pending=True);p,_=self.preview(actor)
        with psycopg.connect(self.db) as c:c.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",(actor,))
        with psycopg.connect(self.db) as c:c.execute("update public.equipe_prumo_s1 set estado='pendente' where ator_id=%s",(actor,))
        self.assertEqual(self.apply(p).state,'STALE');self.assertIsNone(self.cargo(actor))

    def test_i80_13_grant_change_even_same_count_invalidates_preview(self):
        actor,_,_=self.legacy();p,_=self.preview(actor,manager=self.people['m1'][0])
        with psycopg.connect(self.db) as c:c.execute("update public.vinculos_papel_escopo set valido_ate=clock_timestamp()+interval '2 days' where ator_id=%s",(actor,))
        self.assertEqual(self.apply(p).state,'STALE')

    def test_i80_14_paused_intake_is_preserved_not_account_suspension(self):
        actor,_,_=self.legacy()
        with psycopg.connect(self.db) as c:c.execute('select prumo_private.s1_definir_intake(%s,%s,true,1)',(self.people['m1'][0],actor))
        p,_=self.preview(actor,manager=self.people['m1'][0]);before=self.preserved(actor)
        self.assertTrue(p['impact']['intake_paused']);self.assertEqual(self.apply(p).state,'APPLIED');self.assertEqual(self.preserved(actor),before)
        denied=self.call(payload={**self.payload(item=self.queue(),key='i80-paused-new-lead'),'consultor_id':str(actor)})
        self.assertEqual(denied.state.value,'INTAKE_PAUSED')

    def test_i80_15_intake_change_after_preview_is_stale(self):
        actor,_,_=self.legacy();p,_=self.preview(actor,manager=self.people['m1'][0])
        with psycopg.connect(self.db) as c:c.execute('select prumo_private.s1_definir_intake(%s,%s,true,1)',(self.people['m1'][0],actor))
        self.assertEqual(self.apply(p).state,'STALE')

    def test_i80_16_assignment_closure_after_preview_is_stale(self):
        actor,_,case=self.legacy();p,_=self.preview(actor,manager=self.people['m1'][0])
        with psycopg.connect(self.db) as c:c.execute('update public.atribuicoes_humanas set encerrada_em=clock_timestamp() where id=%s',(case['assignment_id'],))
        self.assertEqual(self.apply(p).state,'STALE')

    def test_i80_17_i62_revocation_after_preview_is_stale(self):
        actor,_,case=self.legacy(exception=True);p,_=self.preview(actor,manager=self.people['m1'][0])
        exc=UUID(case['exception_id']);principal,issued,nonce,mac=self.s1_proof('EXC62R',(exc,None,None,None,None,'R'),'m1')
        with psycopg.connect(self.s1_dsn) as c:c.execute('select prumo_s1_signed_i20.invocar_excecao_i62(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (principal.actor_id,principal.session_id,'REVOKE',exc,None,None,None,self.s1_key,issued,nonce,mac))
        self.assertEqual(self.apply(p).state,'STALE')

    def test_i80_18_preview_bound_to_live_director_session(self):
        actor,_,_=self.legacy(pending=True);token=self.fresh_director_token();p,_=self.preview(actor,token=token)
        self.assertIn(request(self.api,self.anon,'POST','/auth/v1/logout?scope=local',token=token)[0],(200,204))
        self.assertEqual(self.apply(p,token).state,'DENIED')
        self.assertEqual(self.apply(p,self.director_token).state,'DENIED')

    def test_i80_19_director_competence_revocation_denies_application(self):
        actor,_,_=self.legacy(pending=True);p,_=self.preview(actor);self.set_director(False)
        try:self.assertEqual(self.apply(p).state,'DENIED');self.assertIsNone(self.cargo(actor))
        finally:self.set_director(True)

    def test_i80_20_same_key_concurrent_one_application_and_exact_retry(self):
        actor,_,_=self.legacy(orphan=True);p,_=self.preview(actor,manager=self.people['m1'][0]);wire=self.apply_wire(p)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=[f.result(timeout=15) for f in [pool.submit(self.run_command,wire),pool.submit(self.run_command,wire)]]
        self.assertEqual({r.state for r in results},{'APPLIED','ALREADY_APPLIED'})
        self.assertEqual(results[0].receipt['request_id'],results[1].receipt['request_id'])

    def test_i80_21_different_keys_cannot_consume_preview_twice(self):
        actor,_,_=self.legacy(orphan=True);p,_=self.preview(actor,manager=self.people['m1'][0])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=[f.result(timeout=15) for f in [pool.submit(self.apply,p),pool.submit(self.apply,p)]]
        self.assertEqual(sum(r.state=='APPLIED' for r in results),1)
        self.assertTrue(all(r.state in ('APPLIED','CONCURRENT_CHANGE','CONFLICT') for r in results))
        self.assertEqual(self.apply(p).state,'CONFLICT')

    def test_i80_22_preview_idempotency_payload_conflict(self):
        actor,_,_=self.legacy(orphan=True);p,wire=self.preview(actor,manager=self.people['m1'][0])
        self.assertEqual(self.run_command(wire).receipt['preview_id'],p['preview_id'])
        self.assertEqual(self.run_command({**wire,'manager_id':str(self.people['m2'][0])}).state,'CONFLICT')

    def test_i80_23_busy_assignment_fails_fast_then_same_preview_retry(self):
        actor,_,case=self.legacy();p,_=self.preview(actor,manager=self.people['m1'][0]);wire=self.apply_wire(p)
        with psycopg.connect(self.db) as c:
            c.execute('select id from public.atribuicoes_humanas where id=%s for update',(case['assignment_id'],))
            self.assertEqual(self.run_command(wire).state,'CONCURRENT_CHANGE');c.rollback()
        self.assertEqual(self.run_command(wire).state,'APPLIED')

    def fault(self,deferred=False):
        actor,_,_=self.legacy(exception=True);p,_=self.preview(actor,manager=self.people['m2'][0]);wire=self.apply_wire(p)
        before=self.preserved(actor);old=self.relation(actor);name='i80_fault_'+uuid4().hex
        with psycopg.connect(self.db) as c:
            nonce_before=c.execute('select count(*) from prumo_private.cfi01_consumed_nonces_local').fetchone()[0]
            exception_before=c.execute('select jsonb_agg(to_jsonb(x) order by x.id) from prumo_private.s1_excecoes_caso_i61 x where operador_id=%s',(actor,)).fetchone()[0]
        with psycopg.connect(self.db) as c:
            c.execute(sql.SQL("create function prumo_private.{}() returns trigger language plpgsql as $$begin raise exception 'I80_DISPOSABLE_FAULT';end$$").format(sql.Identifier(name)))
            trigger='create constraint trigger {} after insert on prumo_private.s1_i80_audit deferrable initially deferred for each row execute function prumo_private.{}()' if deferred else 'create trigger {} before insert on prumo_private.s1_i80_audit for each row execute function prumo_private.{}()'
            c.execute(sql.SQL(trigger).format(sql.Identifier(name),sql.Identifier(name)))
        try:
            self.assertEqual(self.run_command(wire).state,'UNAVAILABLE');self.assertIsNone(self.cargo(actor));self.assertEqual(self.relation(actor),old);self.assertEqual(self.preserved(actor),before)
            with psycopg.connect(self.db) as c:self.assertEqual(c.execute("select count(*) from pg_stat_activity where usename='prumo_cfi01_pgtest_login'").fetchone()[0],0)
            with psycopg.connect(self.db) as c:
                self.assertEqual(c.execute('select count(*) from prumo_private.cfi01_consumed_nonces_local').fetchone()[0],nonce_before)
                self.assertEqual(c.execute('select jsonb_agg(to_jsonb(x) order by x.id) from prumo_private.s1_excecoes_caso_i61 x where operador_id=%s',(actor,)).fetchone()[0],exception_before)
                self.assertEqual(c.execute('select count(*) from prumo_private.s1_i80_applications where preview_id=%s',(p['preview_id'],)).fetchone()[0],0)
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on prumo_private.s1_i80_audit').format(sql.Identifier(name)))
                c.execute(sql.SQL('drop function prumo_private.{}()').format(sql.Identifier(name)))
        self.assertEqual(self.run_command(wire).state,'APPLIED')

    def test_i80_24_partial_failure_rolls_back_role_relation_i61_and_nonce(self):self.fault()
    def test_i80_25_deferred_failure_no_success_or_open_connection(self):self.fault(True)

    def test_i80_26_malformed_result_rolls_back_before_commit(self):
        actor,_,_=self.legacy(orphan=True);p,_=self.preview(actor,manager=self.people['m1'][0]);wire=self.apply_wire(p)
        bad="select t.r || jsonb_build_object('target_id','00000000-0000-4000-8000-000000000001') from ("+regularization.SQL+") t(r)"
        with patch.object(regularization,'SQL',bad):self.assertEqual(self.run_command(wire).state,'UNAVAILABLE')
        self.assertIsNone(self.cargo(actor));self.assertEqual(self.run_command(wire).state,'APPLIED')

    def test_i80_27_mac_nonce_and_direct_sql_access(self):
        actor,_,_=self.legacy(pending=True);item=self.inventory_item(actor)
        p=regularization.command(self.wire('PREVIEW',actor,'consultor',expected=item['inventory_sha256']))
        principal=self.gateway._identity.verify('Bearer '+self.director_token);proof=self.regularizer.proof(principal,p)
        with psycopg.connect(self.dsn) as c:c.execute(regularization.SQL,proof)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(self.dsn) as c:c.execute(regularization.SQL,proof)
        changed=list(self.regularizer.proof(principal,p));changed[4]='gestor'
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(self.dsn) as c:c.execute(regularization.SQL,changed)
        for query in ('select * from prumo_private.s1_i80_previews','set role prumo_s0_g1_executor_local'):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(self.dsn) as c:c.execute(query)

    def test_i80_28_expired_persisted_preview_is_not_applied(self):
        actor,_,_=self.legacy(pending=True);p,_=self.preview(actor);expired=uuid4()
        with psycopg.connect(self.db) as c:
            # Old persisted fixture simulates elapsed server time, no clock
            # monkeypatch and no UPDATE of the immutable original preview.
            c.execute("insert into prumo_private.s1_i80_previews(id,diretor_id,session_id,request_key,target_id,cargo,manager_id,inventory_sha256,snapshot,snapshot_sha256,blockers,impact,created_at,expires_at) select %s,diretor_id,session_id,%s,target_id,cargo,manager_id,inventory_sha256,snapshot,snapshot_sha256,blockers,impact,clock_timestamp()-interval '6 minutes',clock_timestamp()-interval '1 minute' from prumo_private.s1_i80_previews where id=%s",(expired,'expired-'+uuid4().hex,p['preview_id']))
        p={**p,'preview_id':str(expired)};self.assertEqual(self.apply(p).state,'EXPIRED');self.assertIsNone(self.cargo(actor))

    def test_i80_29_g1_waits_for_regularization_commit_then_rechecks(self):
        actor,_,_=self.legacy(case=False);p,_=self.preview(actor,manager=self.people['m1'][0]);wire=regularization.command(self.apply_wire(p))
        principal=self.gateway._identity.verify('Bearer '+self.director_token)
        with psycopg.connect(self.dsn) as c,ThreadPoolExecutor(max_workers=1) as pool:
            result=c.execute(regularization.SQL,self.regularizer.proof(principal,wire)).fetchone()[0];self.assertEqual(result['outcome'],'APPLIED')
            pending=pool.submit(self.call,payload={**self.payload(key='i80-g1-after-commit'),'consultor_id':str(actor)})
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            try:self.wait_blocker(pid)
            finally:c.commit()
            self.assertEqual(pending.result(timeout=15).state.value,'MANUAL_ASSIGNED')

    def test_i80_30_candidate_manager_revoked_between_preview_and_apply(self):
        boss,_=self.new_person('gestor',True);actor,_,_=self.legacy(orphan=True);p,_=self.preview(actor,manager=boss)
        with psycopg.connect(self.db) as c:c.execute("update public.equipe_prumo_s1 set estado='suspenso' where ator_id=%s",(boss,))
        self.assertEqual(self.apply(p).state,'STALE');self.assertIsNone(self.cargo(actor))

    def test_i80_31_missing_team_record_is_inventory_only_not_silent_registration(self):
        actor,_=register(self.api,self.anon)
        with psycopg.connect(self.db) as c:c.execute('insert into public.atores(id) values (%s)',(actor,))
        p,_=self.preview(actor,'gestor');self.assertIn('MISSING_TEAM_USE_I79_REGISTER',p['blockers'])
        self.assertEqual(self.apply(p).state,'BLOCKED')

    def test_i80_32_private_functions_and_immutable_preview_are_not_client_authority(self):
        actor,_,_=self.legacy(pending=True);p,_=self.preview(actor)
        signature='prumo_private.s1_i80_signed(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid,bigint,uuid,text)'
        with psycopg.connect(self.db) as c:
            for role in ('anon','authenticated','service_role'):
                self.assertFalse(c.execute("select has_function_privilege(%s,%s,'EXECUTE')",(role,signature)).fetchone()[0])
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(self.dsn) as c:c.execute('update prumo_private.s1_i80_previews set cargo=\'gestor\' where id=%s',(p['preview_id'],))
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(self.db) as c:c.execute('update prumo_private.s1_i80_previews set cargo=\'gestor\' where id=%s',(p['preview_id'],))


if __name__=='__main__':
    suite=unittest.TestSuite(I80Tests(name) for name in unittest.defaultTestLoader.getTestCaseNames(I80Tests) if name.startswith('test_i80_'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
