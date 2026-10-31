"""Physical disposable compatibility experiments; no operational executor.

31 unchanged inherited I86 scenarios plus explicit OPS03 boundary experiments.
Auth logout calls below are synthetic fixtures/counterexamples, NEVER a proposed
automatic Director administration path or a two-phase implementation.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch
from urllib import request, error

if (os.environ.get('GITHUB_ACTIONS') != 'true'
        or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'
        or os.environ.get('PRUMO_OPS03_DISPOSABLE') != 'YES'):
    raise RuntimeError('OPS03_EXCLUSIVE_DISPOSABLE_LAB_REQUIRED')

from integration.i86.manual import test_real as inherited
from integration.i86.manual import lab_support as lab
from integration.i85 import bootstrap as i85
from integration.i84.capture import reject_material
from local_admin import boundary as b, environment as e

HERE = Path(__file__).parent
OBSERVATIONS = {}


def fixture_guard():
    # Environment flags alone never suffice: laboratory() verifies physical
    # ownership, source digests, loopback ports and the real DB marker/principal.
    if (os.environ.get('PRUMO_OPS03_DISPOSABLE') != 'YES'
            or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'):
        raise b.Blocked('OPS03_DISPOSABLE_FIXTURES_ONLY')
    lab.laboratory()


class OPS03Tests(inherited.ManualTests):
    @classmethod
    def setUpClass(cls):
        if (os.environ.get('PRUMO_OPS03_DISPOSABLE') != 'YES'
                or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'):
            raise b.Blocked('OPS03_DISPOSABLE_FIXTURES_ONLY')
        super().setUpClass()  # exact certified setup; no bootstrap grant
        fixture_guard()
        OBSERVATIONS['lab_images'] = {}
        for name in (b.DB, 'supabase_auth_'+b.PROJECT, b.KONG, b.EDGE):
            OBSERVATIONS['lab_images'][name] = json.loads(b.docker('inspect','--format',
                '{{json .Config.Image}}',name))
        with lab.connect() as c:
            cls.core_fingerprint = c.execute("""select p.proname,md5(p.prosrc),p.proacl::text,p.prosecdef,
                p.proowner::regrole::text,p.proconfig
                from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                where n.nspname='prumo_i86_manual' order by p.proname""").fetchall()
        with lab.connect() as c:
            c.autocommit = True
            c.execute((HERE/'hosted_candidate.sql').read_text())
        cls.adapter_patch = patch.object(lab, 'APPLY_SQL',
            'select prumo_ops03_manual.apply_act('+','.join(['%s']*7)+')')
        cls.adapter_patch.start()
        # All inherited lab.apply_for_test paths now use the guarded adapter.
        # Explicit original SQL/SIGKILL probes remain unchanged baseline probes.

    @classmethod
    def finish(cls):
        try:
            if hasattr(cls, 'core_fingerprint'):
                with lab.connect() as c:
                    current = c.execute("""select p.proname,md5(p.prosrc),p.proacl::text,p.prosecdef,
                        p.proowner::regrole::text,p.proconfig
                        from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                        where n.nspname='prumo_i86_manual' order by p.proname""").fetchall()
                if current != cls.core_fingerprint:
                    raise AssertionError('OPS03_CERTIFIED_SQL_OBJECT_CHANGED')
                OBSERVATIONS['certified_sql_objects_unchanged'] = True
        finally:
            try:
                super().finish()  # inherited catalog equality, secret scan, full teardown
            finally:
                if hasattr(cls, 'adapter_patch'):
                    cls.adapter_patch.stop()

    def login_pair(self, person):
        fixture_guard()
        value = i85._api('POST','/auth/v1/token?grant_type=password',
            {'email':person['email'],'password':self.passwords[person['id']]},
            admin=False,token=e.discover()['ANON_KEY'])
        self.technical.extend([value['access_token'],value['refresh_token']])
        return value

    def auth_fixture(self, path, token, data=None):
        fixture_guard()
        if path not in ('/auth/v1/logout?scope=global','/auth/v1/token?grant_type=refresh_token'):
            raise b.Blocked('OPS03_FIXED_AUTH_FIXTURE_PATH_ONLY')
        env = e.discover()  # certified fixed loopback URL, never an argument
        req = request.Request(env['API_URL']+path,
            data=None if data is None else json.dumps(data).encode(), method='POST',
            headers={'apikey':env['ANON_KEY'],'Authorization':'Bearer '+token,
                     'Content-Type':'application/json'})
        try:
            response = request.build_opener(i85.NoRedirect()).open(req,timeout=10)
        except error.HTTPError as exc:
            response = exc
        with response:
            body,status = response.read(65537),response.status
        self.assertLessEqual(len(body),65536)
        reject_material(body,self.technical+list(self.passwords.values()))
        return status

    def test_40_adapter_acl_invoker_owners_and_role_inheritance(self):
        roles = ('anon','authenticated','service_role','prumo_s1_admin_edge_local',
                 'prumo_cfi01_pgtest_login','prumo_s1_signed_login_ci',
                 'prumo_s0_g1_executor_local','prumo_cfi01_atomic_owner_local',
                 'prumo_s1_admin_domain_local','prumo_s1_professional_validator_local')
        signature = 'prumo_ops03_manual.apply_act(uuid,text,uuid,text,text,text,text)'
        with lab.connect() as c:
            self.assertEqual(c.execute("""select count(*),bool_and(not prosecdef),bool_and(proowner='postgres'::regrole)
                from pg_proc where pronamespace='prumo_ops03_manual'::regnamespace""").fetchone(),(4,True,True))
            for role in roles:
                self.assertEqual(c.execute('select has_schema_privilege(%s,%s,%s),has_function_privilege(%s,%s,%s)',
                    (role,'prumo_ops03_manual','USAGE',role,signature,'EXECUTE')).fetchone(),(False,False))
            self.assertEqual(c.execute("""select count(*) from pg_proc p,
                lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
                where p.pronamespace='prumo_ops03_manual'::regnamespace and a.grantee=0
                and a.privilege_type='EXECUTE'""").fetchone()[0],0)
        OBSERVATIONS['adapter_no_client_or_ordinary_owner_privilege'] = True

    def test_41_all_actions_denied_to_common_sql_roles_despite_claims(self):
        import psycopg
        values = lab.act(self.primary['id'],'REVOKE')
        for role in ('anon','authenticated','service_role','prumo_s1_admin_edge_local',
                     'prumo_cfi01_pgtest_login','prumo_s1_admin_domain_local'):
            for action in ('APPOINT','REVOKE','REACTIVATE'):
                with self.subTest(role=role,action=action),self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with lab.connect() as c:
                        c.execute('set local role "'+role+'"')
                        c.execute("select set_config('request.jwt.claims',%s,true)",
                            (json.dumps({'role':'postgres','cargo':'diretor','human_authorized':True}),))
                        c.execute(lab.APPLY_SQL,(values[0],action,*values[2:]))

    def test_42_application_director_manager_consultant_and_service_rpc_denied(self):
        consultant = self.person('consultant')
        self.success('i79',self.prof('REGISTER',consultant['id'],'consultor'),self.primary_token)
        self.success('i79',self.prof('ACTIVATE',consultant['id'],'consultor',
            manager=self.manager['id']),self.primary_token)
        tokens = [self.primary_token,self.manager_token,
                  lab.token(consultant,self.passwords,self.technical),i85._key()]
        for token in tokens:
            for profile in (None,'prumo_ops03_manual'):
                status = self.direct_http('/rest/v1/rpc/apply_act',
                    {'p_action':'APPOINT','p_target':consultant['id']},token,profile)
                self.assertIn(status,(400,401,403,404,406))

    def test_43_readonly_metadata_diagnostic_collects_no_identity_rows(self):
        with lab.connect() as c:
            c.autocommit = True
            cursor = c.execute((HERE/'diagnostic.sql').read_text())
            reports = []
            while True:
                if cursor.description:
                    reports.extend(row[0] for row in cursor.fetchall())
                if not cursor.nextset():
                    break
        self.assertEqual(len(reports),1)
        report = reports[0]
        self.assertIs(report['authorizes_action'],False)
        self.assertIs(report['hosted_homologated'],False)
        self.assertEqual(report['transaction_read_only'],'on')
        self.assertTrue(all(r['exists'] and r['required_columns_present'] for r in report['objects']))
        self.assertTrue(report['essential_professional_constraint'])
        for secret in self.technical+list(self.passwords.values()):
            self.assertNotIn(secret,json.dumps(report))
        for forbidden in ('email','password','access_token','refresh_token'):
            self.assertNotIn('"'+forbidden+'"',json.dumps(report))
        OBSERVATIONS['metadata_diagnostic'] = report

    def test_44_adapter_rejects_unmarked_database_and_wrong_isolation(self):
        import psycopg
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with lab.connect() as c:
                c.execute("comment on database postgres is 'OPS03_UNMARKED_SYNTHETIC_TEST'")
                c.execute('select prumo_ops03_manual.inspect_subject(%s)',(self.primary['id'],))
        # Database comment rolls back, never spoofing a hosted installation.
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with lab.connect() as c:
                c.execute('set transaction isolation level repeatable read')
                c.execute('select prumo_ops03_manual.inspect_subject(%s)',(self.primary['id'],))

    def test_45_adapter_reconciliation_is_after_commit_only(self):
        person = self.person('candidate-reconcile')
        values = lab.act(person['id'])
        with lab.connect() as c:
            c.execute(lab.APPLY_SQL,values)
            self.assertEqual(c.execute('select prumo_ops03_manual.reconcile_act(%s,%s)',
                (values[0],values[6])).fetchone()[0]['state'],'COMMIT_NOT_PROVEN')
        with lab.connect() as c:
            self.assertEqual(c.execute('select prumo_ops03_manual.reconcile_act(%s,%s)',
                (values[0],values[6])).fetchone()[0]['state'],'COMMITTED_CURRENT_STATE_VERIFIED')

    def test_46_auth_global_logout_real_refresh_denial_and_unexpired_jwt(self):
        person,_ = self.appoint()
        first,second = self.login_pair(person),self.login_pair(person)
        claims = json.loads(base64.urlsafe_b64decode(first['access_token'].split('.')[1]+'=='))
        self.assertGreater(claims['exp'],time.time())
        self.assertIn(self.auth_fixture('/auth/v1/logout?scope=global',first['access_token']),(200,204))
        with lab.connect() as c:
            self.assertEqual(c.execute('select count(*) from auth.sessions where user_id=%s',
                (person['id'],)).fetchone()[0],0)
        for pair in (first,second):
            self.assertIn(self.auth_fixture('/auth/v1/token?grant_type=refresh_token',
                e.discover()['ANON_KEY'],{'refresh_token':pair['refresh_token']}),(400,401,403))
            self.assertIn(self.http('i80',self.reg('INVENTORY',limit=1),pair['access_token'])[0],(401,403))
        self.assertGreater(claims['exp'],time.time())
        OBSERVATIONS['auth_global_logout_refresh_denied_before_jwt_expiry'] = True

    def test_47_auth_commit_does_not_rollback_with_separate_domain_transaction(self):
        # Counterexample to a hypothetical two-phase design. NOT an authority
        # implementation: direct fixture update is rolled back and never audited
        # as an I86 act; Auth has its own transaction and cannot join this one.
        person,_ = self.appoint()
        pair = self.login_pair(person)
        with lab.connect() as c:
            c.execute('update prumo_private.s1_responsaveis_plataforma set ativo=false where ator_id=%s',
                (person['id'],))
            self.assertIn(self.auth_fixture('/auth/v1/logout?scope=global',pair['access_token']),(200,204))
            c.rollback()
        with lab.connect() as c:
            self.assertTrue(c.execute('select ativo from prumo_private.s1_responsaveis_plataforma where ator_id=%s',
                (person['id'],)).fetchone()[0])
            self.assertEqual(c.execute('select count(*) from auth.sessions where user_id=%s',
                (person['id'],)).fetchone()[0],0)
        OBSERVATIONS['separate_auth_call_survives_domain_rollback'] = True
        OBSERVATIONS['cross_service_atomicity'] = 'NOT_PROVEN_COUNTEREXAMPLE_OBSERVED'

    def test_48_supported_logout_is_not_a_ban_and_live_competence_still_denies(self):
        # Synthetic probe of the other ordering, not a proposed two-phase REVOKE.
        person,_ = self.appoint()
        pair = self.login_pair(person)
        with lab.connect() as c:
            c.execute('update prumo_private.s1_responsaveis_plataforma set ativo=false where ator_id=%s',
                (person['id'],))
        self.assertEqual(self.http('i80',self.reg('INVENTORY',limit=1),pair['access_token'])[0],403)
        with lab.connect() as c:
            self.assertGreater(c.execute('select count(*) from auth.sessions where user_id=%s',
                (person['id'],)).fetchone()[0],0)
        self.assertIn(self.auth_fixture('/auth/v1/logout?scope=global',pair['access_token']),(200,204))
        fresh = self.login_pair(person)  # new authentication after the logout cut
        self.assertEqual(self.http('i80',self.reg('INVENTORY',limit=1),fresh['access_token'])[0],403)
        OBSERVATIONS['fresh_login_after_logout_not_authority'] = True
        OBSERVATIONS['domain_commit_before_auth_call_leaves_session_gap'] = True

    def test_49_session_api_failure_is_not_success_or_reactivation(self):
        person,_ = self.appoint()
        pair = self.login_pair(person)
        values = lab.act(person['id'],'REVOKE')
        lab.apply_for_test(values)  # guarded atomic baseline, not an Auth API replacement
        self.assertIn(self.auth_fixture('/auth/v1/logout?scope=global','OPS03_INVALID_SYNTHETIC_TOKEN'),(401,403))
        with lab.connect() as c:
            self.assertFalse(c.execute('select ativo from prumo_private.s1_responsaveis_plataforma where ator_id=%s',
                (person['id'],)).fetchone()[0])
        self.assertIn(self.http('i80',self.reg('INVENTORY',limit=1),pair['access_token'])[0],(401,403))
        self.assertEqual(lab.reconcile(values)['state'],'COMMITTED_CURRENT_STATE_VERIFIED')


if __name__ == '__main__':
    # Hard stop before even starting a fixture, also when manually invoked.
    if (os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'
            or os.environ.get('PRUMO_OPS03_DISPOSABLE') != 'YES'):
        raise SystemExit('OPS03_EXCLUSIVE_DISPOSABLE_LAB_REQUIRED')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OPS03Tests)
    planned = [test._testMethodName for test in suite]
    result = unittest.TextTestRunner(verbosity=2,resultclass=inherited.ProofResult,failfast=True).run(suite)
    proof = {'version':'prumo.s0s1.ops03.physical.v1',
        'status':'PASS' if result.wasSuccessful() and not result.skipped and result.testsRun==len(planned) else 'FAIL',
        'source_head':os.environ['PRUMO_I86_SOURCE_HEAD'],'planned_tests':len(planned),
        'tests_run':result.testsRun,'skipped':len(result.skipped),'results':inherited.RESULTS,
        'not_tested':[name for name in planned if name not in {r['test'] for r in inherited.RESULTS}],
        'observations':OBSERVATIONS,'final':inherited.FINAL,
        'hosted_verified':False,'human_presence_certified':False,
        'hosted_supported_revoke_implemented':False,
        'session_strategy':'UNCHANGED_I86_ATOMIC_AUTH_DML_LAB_CONTROL_ONLY',
        'auth_api_experiments':'COUNTEREXAMPLES_ONLY_NO_EXECUTOR_OR_TWO_PHASE_IMPLEMENTATION'}
    (Path(os.environ['RUNNER_TEMP'])/'ops03-physical.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'status':proof['status'],'planned':len(planned),'run':result.testsRun,
                      'hosted_verified':False,'hosted_supported_revoke_implemented':False}))
    raise SystemExit(0 if proof['status']=='PASS' else 1)
