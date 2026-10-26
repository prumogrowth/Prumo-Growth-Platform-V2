"""Real loopback GoTrue/PostgREST/PG17 history reads and session revocation.

No JWT signing, fake identity provider, HTTP opener replacement or SQL result
stub. Only the adversarial SQL-context test edits claims, explicitly testing a
DB predicate rather than authenticating those edited claims through HTTP.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time
import unittest
import uuid

import psycopg
from psycopg import sql
from scripts.test_s0_cfi01_auth_rest_local import local_env, register, request

ROOT = Path(__file__).resolve().parents[2]
TABLES = ('leads_loja','ciclos_comerciais','casos_humanos','atribuicoes_humanas',
          'conversas','mensagens','itens_lote','reencontros_lote',
          'eventos_status_comercial','lotes_importacao','canais_loja')
PROFILE = 's0'


def claims(token):
    return json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'=='))


def catalog(c):
    """Existing ACLs/policies/CFI helpers, excluding only our added namespace."""
    return (
        c.execute("select oid,relacl::text,relrowsecurity from pg_class where relnamespace='public'::regnamespace order by oid").fetchall(),
        c.execute("select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check from pg_policies where policyname<>'s0_history_live_session' order by 1,2,3").fetchall(),
        c.execute("select oid,proacl::text,pg_get_functiondef(oid) from pg_proc where pronamespace='prumo_private'::regnamespace and proname like 'cfi01_%' order by oid").fetchall())


def install(db, *, opt_in=True):
    # SQL file manages its transaction. In failure the connection close rolls
    # back the aborted installer, leaving no partial policies or grants.
    with psycopg.connect(db, autocommit=True) as c:
        if opt_in:
            c.execute("set prumo.history_disposable='YES'")
        c.execute((ROOT/'supabase/tests/s0_history_session_gate_local_only.sql').read_text())


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_HISTORY_DISPOSABLE_TEST') != 'YES':
            raise RuntimeError('Explicit disposable history opt-in required')
        env=local_env()  # Reject remote DB/API, require CLI loopback port 54322.
        cls.db,cls.api,cls.key=(env[x] for x in ('DB_URL','API_URL','ANON_KEY'))
        with psycopg.connect(cls.db) as c:
            assert c.execute("select current_setting('server_version_num')::int/10000").fetchone()[0]==17

    def setUp(self):
        self.actors={name:register(self.api,self.key) for name in ('op','other','manager','director')}
        self.actor,self.token=self.actors['op']
        self.shop,self.shop_b=uuid.uuid4(),uuid.uuid4()
        self.lead,self.other_lead,self.lead_b=[uuid.uuid4() for _ in range(3)]
        self.cases=[uuid.uuid4() for _ in range(4)]
        self.convs=[uuid.uuid4() for _ in range(5)]
        self.channels=[uuid.uuid4(),uuid.uuid4()]
        self.assignments=[uuid.uuid4() for _ in range(4)]
        with psycopg.connect(self.db) as c:
            for actor,_ in self.actors.values():
                c.execute('insert into public.atores(id) values (%s)',(actor,))
                c.execute("insert into public.equipe_prumo_s1(ator_id,estado) values (%s,'ativo')",(actor,))
            for shop in (self.shop,self.shop_b):
                c.execute("insert into public.concessionarias(id,nome_operacional) values (%s,'DISPOSABLE HISTORY')",(shop,))
            for name,shop,role in [('op',self.shop,'operador'),('other',self.shop,'operador'),
                                   ('other',self.shop_b,'operador'),('manager',self.shop,'gestor'),
                                   ('director',self.shop,'responsavel')]:
                c.execute('insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values (%s,%s,%s)',(self.actors[name][0],shop,role))
            if PROFILE=='i63':
                c.execute('insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values (%s,%s)',(self.actors['manager'][0],self.actor))
            for lead,shop,phone in [(self.lead,self.shop,'+5500000000000'),
                                    (self.other_lead,self.shop,'+5500000000001'),
                                    (self.lead_b,self.shop_b,'+5500000000000')]:
                c.execute('insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values (%s,%s,%s)',(lead,shop,phone))
            for channel,shop in zip(self.channels,(self.shop,self.shop_b)):
                c.execute('insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values (%s,%s,%s)',(channel,shop,str(channel)))
            for i in range(4):
                shop=self.shop_b if i==3 else self.shop
                lead=[self.lead,self.lead,self.other_lead,self.lead_b][i]
                cycle=uuid.uuid4()
                c.execute("insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial) values (%s,%s,%s,'em atendimento pelo operador')",(cycle,shop,lead))
                c.execute('insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id) values (%s,%s,%s,%s)',(self.cases[i],shop,lead,cycle))
                actor=self.actor if i==0 else self.actors['other'][0]
                c.execute('insert into public.atribuicoes_humanas(id,concessionaria_id,caso_id,operador_id) values (%s,%s,%s,%s)',(self.assignments[i],shop,self.cases[i],actor))
                if i==1:
                    c.execute('update public.atribuicoes_humanas set encerrada_em=clock_timestamp() where id=%s',(self.assignments[i],))
                channel=self.channels[1] if i==3 else self.channels[0]
                c.execute('insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id) values (%s,%s,%s,%s,%s)',(self.convs[i],shop,lead,channel,self.cases[i]))
            c.execute('insert into public.conversas(id,concessionaria_id,lead_id,canal_id) values (%s,%s,%s,%s)',(self.convs[4],self.shop,self.lead,self.channels[0]))
            for conv in self.convs:
                c.execute("insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo) select concessionaria_id,id,canal_id,caso_id,'entrada','synthetic history',id::text from public.conversas where id=%s",(conv,))

    def read(self, token=None, table='mensagens'):
        return request(self.api,self.key,'GET',f'/rest/v1/{table}?select=*&concessionaria_id=in.({self.shop},{self.shop_b})',token=self.token if token is None else token)

    def rows(self, token=None, table='mensagens'):
        code,rows=self.read(token,table)
        self.assertEqual(code,200)
        self.assertIsInstance(rows,list)
        return rows

    def all_denied(self, token):
        for table in TABLES:
            with self.subTest(table=table): self.assertEqual(self.rows(token,table),[])

    def logout(self, token=None):
        code,_=request(self.api,self.key,'POST','/auth/v1/logout?scope=local',token=self.token if token is None else token)
        self.assertIn(code,(200,204))

    def wait_blocker(self,pid):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            with psycopg.connect(self.db) as c:
                if c.execute("select 1 from pg_stat_activity where wait_event_type='Lock' and %s=any(pg_blocking_pids(pid))",(pid,)).fetchone(): return
            time.sleep(.025)
        self.fail('real PostgreSQL blocking relationship absent')

    def sql_reader(self,c,token=None):
        # Physical transaction with claims copied from an actually issued JWT.
        # HTTP authentication itself is proved by rows()/logout(), separately.
        c.execute('set local role authenticated')
        c.execute("select set_config('request.jwt.claims',%s,true)",(json.dumps(claims(self.token if token is None else token)),))
        return c.execute('select id from public.mensagens where concessionaria_id=%s',(self.shop,)).fetchall()

    def test_01_existing_store_contact_and_team_scopes_preserved(self):
        self.assertEqual({r['conversa_id'] for r in self.rows()},
                         {str(self.convs[i]) for i in ([0,1,4] if PROFILE=='i63' else [0])})
        manager=self.actors['manager'][1]
        self.assertEqual({r['conversa_id'] for r in self.rows(manager)},
                         {str(self.convs[i]) for i in ([0,4] if PROFILE=='i63' else [0,1,2,4])})
        self.assertEqual(self.rows(self.actors['director'][1]),[])

    def test_02_real_logout_with_unexpired_jwt_denies_all_history_relations(self):
        token=self.actors['manager'][1]
        self.assertTrue(self.rows(token));self.assertGreater(claims(token)['exp'],time.time())
        self.logout(token)
        with psycopg.connect(self.db) as c:
            self.assertIsNone(c.execute('select id from auth.sessions where id=%s',(claims(token)['session_id'],)).fetchone())
        self.all_denied(token)

    def test_03_not_after_expiry_denies_then_live_restore_works(self):
        token=self.actors['manager'][1];sid=claims(token)['session_id']
        self.assertTrue(self.rows(token))
        with psycopg.connect(self.db) as c:
            c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(sid,))
        self.all_denied(token)
        with psycopg.connect(self.db) as c:c.execute('update auth.sessions set not_after=null where id=%s',(sid,))
        self.assertTrue(self.rows(token))

    def test_04_store_grant_revocation_still_denies(self):
        self.assertTrue(self.rows())
        with psycopg.connect(self.db) as c:
            c.execute('update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s and concessionaria_id=%s',(self.actor,self.shop))
        self.assertEqual(self.rows(),[])

    def test_05_assignment_revocation_still_denies(self):
        self.assertTrue(self.rows())
        with psycopg.connect(self.db) as c:
            c.execute('update public.atribuicoes_humanas set encerrada_em=clock_timestamp() where id=%s',(self.assignments[0],))
        self.assertEqual(self.rows(),[])

    def test_06_invalid_signature_and_anon_cannot_read(self):
        parts=self.token.split('.')
        parts[2]=('a' if parts[2][0]!='a' else 'b')+parts[2][1:]
        self.assertIn(self.read('.'.join(parts))[0],(401,403))
        code,body=request(self.api,self.key,'GET','/rest/v1/mensagens?select=id')
        self.assertTrue(code in (401,403) or (code==200 and body==[]))

    def test_07_private_helper_and_auth_privileges_not_widened(self):
        with psycopg.connect(self.db) as c:
            for role in ('anon','service_role','prumo_cfi01_pgtest_login'):
                self.assertFalse(c.execute("select has_function_privilege(%s,'prumo_history_local.session_valid()','EXECUTE')",(role,)).fetchone()[0])
            self.assertFalse(c.execute("select has_table_privilege('authenticated','auth.sessions','SELECT')").fetchone()[0])
            self.assertFalse(c.execute("select has_schema_privilege('authenticated','prumo_private','USAGE')").fetchone()[0])
            self.assertFalse(c.execute("select has_function_privilege('authenticated','prumo_private.cfi01_session_valid_local(uuid,uuid)','EXECUTE')").fetchone()[0])
            owner=c.execute("select pg_get_userbyid(proowner),proconfig from pg_proc where oid='prumo_history_local.session_valid()'::regprocedure").fetchone()
            self.assertEqual(owner[0],'postgres');self.assertIn('search_path=""',owner[1])
        code,_=request(self.api,self.key,'POST','/rest/v1/rpc/session_valid',{},self.token)
        self.assertEqual(code,404)  # Namespace is not exposed through PostgREST.

    def test_08_current_synthetic_write_preserved_old_case_and_manager_denied(self):
        def insert(i,who):
            return request(self.api,self.key,'POST','/rest/v1/mensagens',dict(
                concessionaria_id=str(self.shop),conversa_id=str(self.convs[i]),
                canal_id=str(self.channels[0]),caso_id=str(self.cases[i]),
                direcao='saida',origem='simulado',conteudo_sintetico='synthetic control',
                enviada_por=str(self.actors[who][0])),self.actors[who][1])[0]
        self.assertEqual(insert(0,'op'),201)
        self.assertIn(insert(1,'op'),(401,403))
        self.assertIn(insert(0,'manager'),(401,403))

    def test_09_history_read_holds_session_lock_logout_waits_until_rollback(self):
        with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
            self.assertTrue(self.sql_reader(c))
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            pending=pool.submit(self.logout)
            try:self.wait_blocker(pid)
            finally:c.rollback()
            pending.result(timeout=15)
        self.assertEqual(self.rows(),[])

    def revocation_first(self,kind,rollback=False):
        self.assertTrue(self.rows())
        with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
            sid=claims(self.token)['session_id']
            if kind=='delete':c.execute('delete from auth.sessions where id=%s',(sid,))
            else:c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(sid,))
            pid=c.execute('select pg_backend_pid()').fetchone()[0]
            pending=pool.submit(self.rows)
            try:self.wait_blocker(pid)
            finally:
                if rollback:c.rollback()
                else:c.commit()
            rows=pending.result(timeout=15)
        self.assertEqual(bool(rows),rollback)

    def test_10_delete_wins_waiting_real_rest_read_denied(self):self.revocation_first('delete')
    def test_11_expiry_update_wins_waiting_real_rest_read_denied(self):self.revocation_first('expire')
    def test_12_revocation_rollback_unblocks_real_rest_read_authorized(self):self.revocation_first('delete',rollback=True)

    def test_13_adversarial_sql_context_missing_wrong_or_expired_session(self):
        # These are intentionally NOT GoTrue-issued mutated tokens. Test the
        # predicate's failure mode for absent/inconsistent trusted DB context.
        valid=claims(self.token)
        mutations=[{},dict(valid,session_id=str(uuid.uuid4())),dict(valid,session_id='invalid'),
                   dict(valid,sub=str(self.actors['other'][0])),dict(valid,exp=0),
                   dict(valid,exp='bad'),dict(valid,is_anonymous=True),dict(valid,role='service_role')]
        with psycopg.connect(self.db) as c:
            c.execute('set local role authenticated')
            for changed in mutations:
                c.execute("select set_config('request.jwt.claims',%s,true)",(json.dumps(changed),))
                self.assertFalse(c.execute('select prumo_history_local.session_valid()').fetchone()[0])

    def test_14_revocation_is_session_specific_not_a_user_wide_flag(self):
        with psycopg.connect(self.db) as c:
            email=c.execute('select email from auth.users where id=%s',(self.actor,)).fetchone()[0]
        code,body=request(self.api,self.key,'POST','/auth/v1/token?grant_type=password',
                          {'email':email,'password':'Only-Local-CFI01-Test!X8b2'})
        self.assertEqual(code,200);second=body['access_token']
        self.assertNotEqual(claims(second)['session_id'],claims(self.token)['session_id'])
        self.logout();self.assertEqual(self.rows(),[]);self.assertTrue(self.rows(second))

    def test_15_repeated_installer_failure_is_atomic(self):
        with psycopg.connect(self.db) as c:before=catalog(c)
        with self.assertRaises(psycopg.errors.DuplicateSchema):install(self.db)
        with psycopg.connect(self.db) as c:self.assertEqual(catalog(c),before)
        self.assertTrue(self.rows())

    def test_16_manager_authority_revocation_preserves_profile_semantics(self):
        token=self.actors['manager'][1];self.assertTrue(self.rows(token))
        with psycopg.connect(self.db) as c:
            if PROFILE=='i63':
                c.execute('update prumo_private.s1_gestor_operadores set encerrado_em=clock_timestamp() where gestor_id=%s',(self.actors['manager'][0],))
            else:
                c.execute('update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id=%s',(self.actors['manager'][0],))
        self.assertEqual(self.rows(token),[])

    def test_17_eleven_restrictive_select_policies_and_no_domain_dml_grants(self):
        with psycopg.connect(self.db) as c:
            rows=c.execute("select tablename,permissive,cmd,roles from pg_policies where policyname='s0_history_live_session'").fetchall()
            self.assertEqual({r[0] for r in rows},set(TABLES))
            self.assertTrue(all(r[1:] == ('RESTRICTIVE','SELECT',['authenticated']) for r in rows))
            for table in TABLES:
                for privilege in ('UPDATE','DELETE','TRUNCATE'):
                    self.assertFalse(c.execute('select has_table_privilege(%s,%s,%s)',('authenticated','public.'+table,privilege)).fetchone()[0])

    def test_18_history_reads_cannot_create_cfi_nonces_receipts_or_audit(self):
        def counters():
            with psycopg.connect(self.db) as c:
                return tuple(c.execute(sql.SQL('select count(*) from prumo_private.{}').format(sql.Identifier(table))).fetchone()[0]
                    for table in ('cfi01_consumed_nonces_local','cfi01_human_closure_events_local','cfi01_command_audit_local'))
        before=counters();self.assertTrue(self.rows());self.logout();self.assertEqual(self.rows(),[])
        self.assertEqual(counters(),before)


def main():
    global PROFILE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=('s0','i63'),default='s0')
    args=parser.parse_args();PROFILE=args.profile
    HistoryTests.setUpClass()
    if PROFILE=='s0':
        probe=HistoryTests('test_02_real_logout_with_unexpired_jwt_denies_all_history_relations')
        probe.setUp()
        assert probe.rows()
        probe.logout()
        assert probe.rows(), 'Baseline did not reproduce #12; investigate before installing'
        print('HISTORY-GAP-REAL: unexpired real GoTrue token still reads after logout, before barrier',flush=True)
        with psycopg.connect(probe.db) as c:before=catalog(c)
        try:install(probe.db,opt_in=False)
        except psycopg.errors.InsufficientPrivilege:pass
        else:raise AssertionError('Installer accepted missing opt-in')
        with psycopg.connect(probe.db) as c:assert catalog(c)==before
        install(probe.db)
        with psycopg.connect(probe.db) as c:assert catalog(c)==before, 'Existing ACL/policy/CFI function changed'
        assert probe.rows()==[]
        print('HISTORY-FIX-REAL: same logged-out token denied; existing ACL/policies/CFI helpers intact',flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HistoryTests))
    if not result.wasSuccessful():raise SystemExit(1)
    print(f'HISTORY-{PROFILE.upper()}: {result.testsRun} scenarios passed; real GoTrue/PostgREST/PG17',flush=True)


if __name__=='__main__':main()
