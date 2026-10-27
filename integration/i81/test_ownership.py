"""Physical PG17 role/ACL/guard proofs on real Director GoTrue I79/I80 ports.

Trusted installer SET ROLE probes are transaction-scoped and always rolled back.
They are not application grants or a substitute for the real authenticated tests.
"""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import unittest
from uuid import uuid4

import psycopg
from psycopg import sql

from backend.s0_cfi01_communication_local import S0CFI01CommunicationLocal
from integration.i80.test_regularization import I80Tests
from scripts.test_s0_cfi01_auth_rest_local import request,register

DOMAIN='prumo_s1_admin_domain_local'
VALIDATOR='prumo_s1_professional_validator_local'
OUTER='prumo_s0_g1_executor_local'
BRIDGES=(
 'prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)',
 'prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)')


class OwnershipTests(I80Tests):
    @contextmanager
    def as_installer_probe(self,role):
        with psycopg.connect(self.db) as c:
            try:
                c.execute(sql.SQL('grant {} to postgres with inherit false,set true').format(sql.Identifier(role)))
                c.execute(sql.SQL('set local role {}').format(sql.Identifier(role)))
                yield c
            finally:c.rollback()  # revoke even successful probes; never COMMIT membership

    def deny_app(self,statement):
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(self.dsn) as c:c.execute(statement)

    def test_i81_01_fixed_owners_no_login_no_executable_membership_no_schema_create(self):
        with psycopg.connect(self.db) as c:
            for signature in BRIDGES:
                owner,definer,config=c.execute('select pg_get_userbyid(proowner),prosecdef,proconfig from pg_proc where oid=to_regprocedure(%s)',(signature,)).fetchone()
                self.assertEqual((owner,definer),(DOMAIN,True));self.assertIn('search_path=""',config)
            self.assertEqual(c.execute("select pg_get_userbyid(proowner),prosecdef from pg_proc where oid='prumo_private.s1_i79_consistencia()'::regprocedure").fetchone(),(VALIDATOR,True))
            for role in (DOMAIN,VALIDATOR):
                self.assertEqual(c.execute('select rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls from pg_roles where rolname=%s',(role,)).fetchone(),(False,)*7)
                self.assertEqual(c.execute('''select count(*) from pg_auth_members
                    where (roleid=(select oid from pg_roles where rolname=%s)
                      and not(member='postgres'::regrole and admin_option and not inherit_option and not set_option))
                    or member=(select oid from pg_roles where rolname=%s)''',(role,role)).fetchone()[0],0)
                for schema in ('public','prumo_private'):
                    self.assertFalse(c.execute("select has_schema_privilege(%s,%s,'CREATE')",(role,schema)).fetchone()[0])
                self.assertEqual(c.execute('select count(*) from pg_class where relowner=(select oid from pg_roles where rolname=%s)',(role,)).fetchone()[0],0)
                self.deny_app('set role '+role)
            self.deny_app('set role '+OUTER)
            self.deny_app('set role postgres')

    def test_i81_02_direct_private_calls_denied_in_real_sql_roles(self):
        signatures=(*BRIDGES,'prumo_private.s1_i81_auth_identity_exists(uuid,boolean)',
                    'prumo_private.s1_i79_consistencia()','prumo_private.s1_i80_snapshot(uuid,uuid)')
        with psycopg.connect(self.db) as c:
            for role in ('anon','authenticated','service_role','prumo_cfi01_pgtest_login'):
                for signature in signatures:
                    self.assertFalse(c.execute("select has_function_privilege(%s,%s,'EXECUTE')",(role,signature)).fetchone()[0])
        statements=[
            'select prumo_private.s1_i79_admin_bridge('+','.join(['null']*9)+')',
            'select prumo_private.s1_i80_bridge('+','.join(['null']*12)+')',
            'select prumo_private.s1_i81_auth_identity_exists(null,false)',
            'select * from prumo_private.s1_i80_previews',
            'select * from prumo_private.s1_i79_requests',
        ]
        for statement in statements:
            self.deny_app(statement)
            for role in ('anon','authenticated','service_role'):
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with self.as_installer_probe(role) as c:c.execute(statement)

    def test_i81_03_i46_still_blocks_accidental_direct_table_grants(self):
        actor,_=self.new_person()
        for role in ('anon','authenticated','service_role','prumo_cfi01_pgtest_login',OUTER,VALIDATOR):
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('grant insert on public.equipe_prumo_s1 to {}').format(sql.Identifier(role)))
                c.execute(sql.SQL('grant {} to postgres with inherit false,set true').format(sql.Identifier(role)))
                c.execute(sql.SQL('set local role {}').format(sql.Identifier(role)))
                try:
                    with self.assertRaisesRegex(psycopg.errors.InsufficientPrivilege,'S1_EQUIPE_ADMIN_NAO_HABILITADO'):
                        c.execute("insert into public.equipe_prumo_s1(ator_id,cargo,estado) values (%s,'gestor','pendente')",(actor,))
                finally:c.rollback()

    def test_i81_04_domain_has_no_keys_nonce_auth_credentials_or_case_command(self):
        for statement in (
            'select secret from prumo_private.cfi01_signing_keys_local',
            'select * from prumo_private.cfi01_consumed_nonces_local',
            'select email from auth.users',
            'select * from auth.sessions',
            'select prumo_private.s0_fila_distribuir(null,null,1)',
            'select prumo_private.s1_mover_excecao_caso_i61(null,null,null,null,null)',
            'select prumo_private.s1_revogar_excecao_i61(null,null)',
            'select prumo_private.g1_manual_bridge_local('+','.join(['null']*8)+')',
        ):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with self.as_installer_probe(DOMAIN) as c:c.execute(statement)

    def test_i81_05_lock_acl_never_authorizes_business_row_mutation(self):
        case=self.assigned(target='c1')
        with self.as_installer_probe(DOMAIN) as c:
            for table,identifier in (('casos_humanos',case['case_id']),('atribuicoes_humanas',case['assignment_id'])):
                row=c.execute('select id,xmin::text from public.'+table+' where id=%s',(identifier,)).fetchone()
                self.assertEqual(str(row[0]),identifier);self.assertTrue(row[1])
        statements=(
            ('update public.casos_humanos set id=id where id=%s',case['case_id']),
            ('update public.atribuicoes_humanas set id=id where id=%s',case['assignment_id']),
            ('update public.vinculos_papel_escopo set id=id where ator_id=%s',self.people['c1'][0]),
        )
        for statement,identifier in statements:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with self.as_installer_probe(DOMAIN) as c:c.execute(statement,(identifier,))
        for statement in (
            'select conteudo_sintetico from public.mensagens',
            'update public.vinculos_papel_escopo set valido_ate=null',
            'update prumo_private.s1_intake_estado set pausado=false',
            'insert into public.casos_humanos default values',
            'insert into public.atribuicoes_humanas default values',
            'update prumo_private.s1_responsaveis_plataforma set ativo=true',
            "update prumo_private.s1_excecoes_caso_i61 set gestor_id=gen_random_uuid()",
        ):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with self.as_installer_probe(DOMAIN) as c:c.execute(statement)

    def test_i81_06_i61_proof_still_requires_case_executor_even_with_accidental_execute(self):
        case=self.assigned()
        with psycopg.connect(self.db) as c:
            self.assertTrue(c.execute('select prumo_private.s1_prova_excecao_i61(%s,%s,%s,%s)',
                (self.shops['A'],case['case_id'],case['assignment_id'],self.people['c2'][0])).fetchone()[0])
        with self.as_installer_probe(DOMAIN) as c:
            c.execute('reset role')
            c.execute('grant execute on function prumo_private.s1_prova_excecao_i61(uuid,uuid,uuid,uuid) to '+DOMAIN)
            # Also make the proof's store row readable in this reverted probe:
            # false must come from executor identity, not a hidden RLS row.
            c.execute('grant select(id,ativo) on public.concessionarias to '+DOMAIN)
            c.execute('create policy i81_probe_store on public.concessionarias for select to '+DOMAIN+' using(true)')
            c.execute('set local role '+DOMAIN)
            self.assertTrue(c.execute('''select exists(select 1 from prumo_private.s1_excecoes_caso_i61 x
                join public.equipe_prumo_s1 e on e.ator_id=x.operador_id and e.estado='ativo'
                join public.equipe_prumo_s1 g on g.ator_id=x.gestor_id and g.estado='ativo'
                join prumo_private.s1_gestor_operadores rel on rel.gestor_id=x.gestor_id and rel.operador_id=x.operador_id and rel.encerrado_em is null
                join public.concessionarias l on l.id=x.concessionaria_id and l.ativo
                where x.id=%s and x.revogada_em is null)''',(case['exception_id'],)).fetchone()[0])
            self.assertFalse(c.execute('select prumo_private.s1_prova_excecao_i61(%s,%s,%s,%s)',
                (self.shops['A'],case['case_id'],case['assignment_id'],self.people['c2'][0])).fetchone()[0])

    def test_i81_07_real_business_and_deferred_work_use_distinct_restricted_owners(self):
        # Test-only observer: original guards remain installed and enforce all
        # invariants. Instrument an INVOKER helper to observe its caller at COMMIT.
        with psycopg.connect(self.db) as c:
            original=c.execute("select pg_get_functiondef('prumo_private.s1_i79_validar_profissional(uuid)'::regprocedure)").fetchone()[0]
            c.execute('create table prumo_private.i81_role_probe(role_name text,source text)')
            c.execute('revoke all on prumo_private.i81_role_probe from public,anon,authenticated,service_role')
            c.execute('grant insert on prumo_private.i81_role_probe to '+DOMAIN+','+VALIDATOR)
            c.execute(original.replace('begin',"begin\n insert into prumo_private.i81_role_probe values(current_user,'validator');",1))
            c.execute("create function prumo_private.i81_role_probe() returns trigger language plpgsql security invoker set search_path='' as $$begin insert into prumo_private.i81_role_probe values(current_user,tg_table_name);return new;end$$")
            for table in ('s1_i79_requests','s1_i80_applications'):
                c.execute('create trigger i81_observe after insert on prumo_private.'+table+' for each row execute function prumo_private.i81_role_probe()')
        try:
            actor,_=self.new_person(activate=True)
            legacy,_,_=self.legacy(pending=True)
            preview,_=self.preview(legacy);self.assertEqual(self.apply(preview).state,'APPLIED')
            with psycopg.connect(self.db) as c:
                observed=set(c.execute('select distinct role_name,source from prumo_private.i81_role_probe').fetchall())
            self.assertIn((DOMAIN,'s1_i79_requests'),observed)
            self.assertIn((DOMAIN,'s1_i80_applications'),observed)
            self.assertIn((VALIDATOR,'validator'),observed)
            self.assertIn((DOMAIN,'validator'),observed)
            self.assertNotIn('postgres',{r for r,_ in observed})
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(original)
                for table in ('s1_i79_requests','s1_i80_applications'):c.execute('drop trigger i81_observe on prumo_private.'+table)
                c.execute('drop function prumo_private.i81_role_probe()')
                c.execute('drop table prumo_private.i81_role_probe')

    def test_i81_08_deferred_constraint_rejects_orphan_even_from_domain_owner(self):
        actor,_=self.new_person()
        with self.assertRaisesRegex(psycopg.errors.CheckViolation,'I79_ACTIVE_CONSULTANT_REQUIRES_ONE_ACTIVE_MANAGER'):
            with psycopg.connect(self.db) as c:
                c.execute('grant '+DOMAIN+' to postgres with inherit false,set true')
                c.execute('set local role '+DOMAIN)
                c.execute("update public.equipe_prumo_s1 set estado='ativo' where ator_id=%s",(actor,))
                # Force deferred validation while original application body has
                # returned; the dedicated validator still has no state DML.
                c.execute('reset role')
                c.commit()
        self.assertEqual(self.preserved(actor)['state'],'pendente')
        self.assertIsNone(self.relation(actor))

    def test_i81_09_validator_cannot_write_state_or_invoke_administration(self):
        for statement in (
            "update public.equipe_prumo_s1 set estado='ativo'",
            'update public.equipe_prumo_s1 set ator_id=ator_id',
            'insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values(null,null)',
            'select prumo_private.s1_i79_admin_bridge('+','.join(['null']*9)+')',
            'select secret from prumo_private.cfi01_signing_keys_local',
        ):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with self.as_installer_probe(VALIDATOR) as c:c.execute(statement)

    def test_i81_10_postgrest_cannot_publish_private_admin_or_auth_shim(self):
        for token in (None,self.tokens['m1'],self.director_token):
            for function in ('s1_i79_admin_bridge','s1_i80_bridge','s1_i81_auth_identity_exists'):
                code,body=request(self.api,self.anon,'POST','/rest/v1/rpc/'+function,{},token=token)
                self.assertIn(code,(401,403,404))
        for token in (self.tokens['m1'],self.director_token):
            code,_=request(self.api,self.anon,'POST','/rest/v1/equipe_prumo_s1',
                 {'ator_id':str(uuid4()),'cargo':'diretor','estado':'ativo'},token=token)
            self.assertIn(code,(401,403))

    def test_i81_11_preserved_i57_i61_bodies_and_all_original_triggers(self):
        before=json.loads((Path(os.environ.get('RUNNER_TEMP','/tmp'))/'prumo_i81_catalog_before.json').read_text())
        with psycopg.connect(self.db) as c:
            for signature,requirement in json.loads(Path('integration/i81/prerequisites.json').read_text()).items():
                if signature in BRIDGES or 's1_exigir_executor' in signature or 's1_i80_snapshot' in signature:continue
                self.assertEqual(c.execute("select encode(sha256(convert_to(prosrc,'UTF8')),'hex') from pg_proc where oid=to_regprocedure(%s)",(signature,)).fetchone()[0],requirement['prosrc_sha256'])
            for trigger in before['triggers']:
                self.assertEqual(c.execute('select pg_get_triggerdef(oid),tgenabled from pg_trigger where tgrelid=to_regclass(%s) and tgname=%s',
                    (trigger['relation'],trigger['tgname'])).fetchone(),(trigger['definition'],trigger['tgenabled']))

    def test_i81_12_no_transitive_postgres_definer_business_escape(self):
        with psycopg.connect(self.db) as c:
            for role in (DOMAIN,VALIDATOR):
                reachable={r[0] for r in c.execute("""select p.oid::regprocedure::text from pg_proc p
                    join pg_namespace n on n.oid=p.pronamespace
                    where n.nspname in('public','prumo_private') and p.prosecdef
                    and pg_get_userbyid(p.proowner)='postgres' and has_function_privilege(%s,p.oid,'EXECUTE')""",(role,))}
                self.assertEqual(reachable,{'prumo_private.cfi01_session_valid_local(uuid,uuid)',
                    'prumo_private.s1_i81_auth_identity_exists(uuid,boolean)'} if role==DOMAIN else set())

    def test_i81_13_auth_identity_row_lock_survives_adapter_and_rechecks_deletion(self):
        target,_=register(self.api,self.anon)
        with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
            c.execute('select id from auth.users where id=%s for update',(target,))
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            pending=pool.submit(self.admin_call,self.dto('REGISTER',target))
            self.wait_blocker(pid)
            c.execute('delete from auth.users where id=%s',(target,));c.commit()
            self.assertEqual(pending.result(timeout=10).state,'DENIED')
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select count(*) from public.equipe_prumo_s1 where ator_id=%s',(target,)).fetchone()[0],0)

    def test_i81_14_cfi_capture_recheck_and_revocation_after_restricted_admission(self):
        # c1 was REGISTERed/ACTIVATEd via real GoTrue under the NEW domain owner
        # during this class bootstrap. G1 supplies its actual canonical case.
        receipt=self.assigned(target='c1')
        with psycopg.connect(self.db) as c:
            channel=c.execute('insert into public.canais_loja(concessionaria_id,identificador_emissor) values (%s,%s) returning id',
                (self.shops['A'],'i81-'+uuid4().hex)).fetchone()[0]
            conversation=c.execute('insert into public.conversas(concessionaria_id,lead_id,canal_id,caso_id) values (%s,%s,%s,%s) returning id',
                (self.shops['A'],self.items['A'][0],channel,receipt['case_id'])).fetchone()[0]
            c.execute("insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo) values (%s,%s,%s,%s,'entrada','I81 disposable context',%s)",
                (self.shops['A'],conversation,channel,receipt['case_id'],'i81-'+uuid4().hex))
            cycle_version,status=c.execute('select versao_registro,status_comercial from public.ciclos_comerciais where id=%s',(self.items['A'][1],)).fetchone()
        adapter=S0CFI01CommunicationLocal(self.gateway)
        capture=adapter.capture('Bearer '+self.tokens['c1'],{'case_ref':receipt['case_id'],'expected_cycle_version':cycle_version,'idempotency_key':'i81-cfi-'+uuid4().hex})
        self.assertEqual(capture.state,'VERIFIED_CONTRACT_PENDING')
        self.assertFalse(capture.public_projection()['confirmed_persisted'])
        self.assertEqual(adapter.recheck('Bearer '+self.tokens['c1'],capture.binding).state,'VERIFIED_CONTRACT_PENDING')
        self.assertEqual(adapter.recheck('Bearer '+self.tokens['c3'],capture.binding).state,'DENIED')
        with psycopg.connect(self.db) as c:
            c.execute('update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s and concessionaria_id=%s',
                (self.people['c1'][0],self.shops['A']))
        self.assertEqual(adapter.recheck('Bearer '+self.tokens['c1'],capture.binding).state,'DENIED')
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select status_comercial from public.ciclos_comerciais where id=%s',(self.items['A'][1],)).fetchone()[0],status)


if __name__=='__main__':
    suite=unittest.TestSuite(OwnershipTests(name) for name in unittest.defaultTestLoader.getTestCaseNames(OwnershipTests) if name.startswith('test_i81_'))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
