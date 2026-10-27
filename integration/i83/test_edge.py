"""All 20 unchanged I82 HTTP assertions under dedicated credentials, plus I83.

Only fixture setup uses the legacy login; the actual Edge runtime never receives
that login/password/key. Invalid server profiles are restarted locally, never
selected by request headers or browser payload.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time
import unittest
from urllib import error as httperror
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch
import psycopg
from psycopg import sql
from integration.i82.test_edge import EdgeTests
from integration.i83.provision_local import Credential,LOGIN,CUSTODIAN,TABLE,rotate,revoke,retire,write_env
from backend import s1_professionals_local as professionals
from backend import s1_legacy_regularization_local as legacy
from scripts.test_s0_cfi01_auth_rest_local import request,register

EDGE_CONTAINER='supabase_edge_runtime_prumo-s0-auth-ci'


class DedicatedEdgeTests(EdgeTests):
    @classmethod
    def edge_environment(cls,env):
        if os.environ.get('PRUMO_I83_DISPOSABLE_TEST')!='YES':raise RuntimeError('I83 explicit opt-in required')
        cls.credentials=[];cls.credential=rotate(cls.db);cls.credentials.append(cls.credential)
        cls.base_env=dict(env);cls.runtime_env=cls.environment(cls.credential)
        cls.addClassCleanup(cls.retire_credentials)
        return cls.runtime_env

    @classmethod
    def environment(cls,value):
        return {**cls.base_env,'PRUMO_I83_DEDICATED':'YES','PRUMO_I82_DATABASE_URL':value.dsn(cls.db,True),
            'PRUMO_I82_KEY_ID':str(value.key_id),'PRUMO_I82_HMAC_HEX':value.secret.hex()}

    @classmethod
    def raw(cls,*args,**kwargs):
        result=super().raw(*args,**kwargs)
        if hasattr(cls,'credentials'):
            text=json.dumps(result)
            if any(secret in text for v in cls.credentials for secret in v.sensitive(cls.db)):
                raise AssertionError('I83 credential appeared in HTTP response (value withheld)')
        return result

    @classmethod
    def stop_runtime(cls):
        failure=None
        try:
            if hasattr(cls,'process'):cls.scan_logs()
        except Exception as error:failure=error
        finally:
            if hasattr(cls,'process'):
                cls.process.terminate()
                try:cls.process.wait(timeout=10)
                except subprocess.TimeoutExpired:cls.process.kill();cls.process.wait(timeout=5)
            # CLI exit alone does not prove that container env was discarded.
            result=subprocess.run(['docker','rm','-f',EDGE_CONTAINER],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
            if result.returncode and failure is None:failure=AssertionError('I83 expected runtime container could not be removed')
        if failure is not None:raise failure

    @classmethod
    def restart(cls,env,ready=True):
        cls.stop_runtime()
        write_env(Path(cls.temporary.name)/'edge.env',env)
        log=cls.runtime_log.open('a');cls.addClassCleanup(log.close)
        cls.process=subprocess.Popen(['supabase','functions','serve','prumo-admin-i82','--env-file',str(Path(cls.temporary.name)/'edge.env'),'--no-verify-jwt'],stdout=log,stderr=subprocess.STDOUT)
        until=time.monotonic()+60
        while time.monotonic()<until:
            try:
                code,b,_=cls.raw('i79',method='GET')
                if b.get('version')=='prumo.admin.v1' and code==(405 if ready else 503):return
            except (httperror.URLError,ConnectionError,TimeoutError,ValueError):pass
            time.sleep(.25)
        raise RuntimeError('I83 real local runtime restart unavailable')

    @classmethod
    def rotate_runtime(cls):
        cls.credential=rotate(cls.db);cls.credentials.append(cls.credential)
        cls.runtime_env=cls.environment(cls.credential);cls.restart(cls.runtime_env)

    @classmethod
    def scan_logs(cls):
        # Read in memory only. Never archive raw container config/logs.
        needles=[s.encode() for v in cls.credentials for s in v.sensitive(cls.db)]
        for container in (EDGE_CONTAINER,'supabase_db_prumo-s0-auth-ci','supabase_auth_prumo-s0-auth-ci','supabase_kong_prumo-s0-auth-ci'):
            result=subprocess.run(['docker','logs',container],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
            if result.returncode:raise AssertionError('I83 expected own disposable container log unavailable')
            data=result.stdout+result.stderr
            if any(n in data for n in needles):raise AssertionError('I83 credential found in container log (value withheld)')
        if any(n in cls.runtime_log.read_bytes() for n in needles):raise AssertionError('I83 credential found in CLI runtime log (value withheld)')

    @classmethod
    def retire_credentials(cls):
        # Registered during environment creation, so it also runs on setup error.
        failure=None
        try:
            if hasattr(cls,'process'):cls.scan_logs()
        except Exception as error:failure=error
        finally:
            try:
                if hasattr(cls,'process'):cls.stop_runtime()
            finally:
                retire(cls.db)
                file=Path(cls.temporary.name)/'edge.env';file.unlink(missing_ok=True)
                if file.exists():raise AssertionError('I83 server env not removed')
        if failure is not None:raise failure
        # Subsequent container log calls must fail: no environment kept alive.
        result=subprocess.run(['docker','inspect','--format','{{.State.Status}}',EDGE_CONTAINER],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if result.returncode==0:raise AssertionError('I83 secret-bearing runtime container survived')
        proof={'status':'CLEANED','container_logs_scanned_without_credential_matches':True,'cli_logs_scanned_without_credential_matches':True,'secret_bearing_container_removed':True,'server_env_removed':True,'active_or_secret_key_rows':0,'sql_login_disabled':True,'sql_password_null':True,'live_sql_sessions':0}
        (Path(os.environ.get('RUNNER_TEMP','/tmp'))/'prumo_i83_custody.json').write_text(json.dumps(proof,indent=2)+'\n')
        print('I83-CUSTODY: container/CLI logs scanned without secret values; runtime container and temporary env removed; key material wiped and SQL login disabled/password cleared; sessions terminated',flush=True)

    def proof_for(self,value,p,family='i79',nonce=None):
        principal=self.gateway._identity.verify('Bearer '+self.director_token)
        module=professionals if family=='i79' else legacy
        cls=professionals.S1ProfessionalsLocal if family=='i79' else legacy.S1LegacyRegularizationLocal
        port=object.__new__(cls)
        port.gateway=SimpleNamespace(_key_id=value.key_id,_secret=value.secret)
        if nonce is None:return module.SQL,port.proof(principal,module.command(p))
        with patch.object(module,'uuid4',return_value=nonce):return module.SQL,port.proof(principal,module.command(p))

    def signed(self,value,p=None,family='i79',dsn=None,nonce=None):
        query,proof=self.proof_for(value,p or self.dto('REGISTER',register(self.api,self.anon)[0]),family,nonce)
        with psycopg.connect(dsn or value.dsn(self.db)) as c:return c.execute(query,proof).fetchone()[0]

    def test_i83_01_dedicated_role_has_only_two_domain_ports_no_data_or_escalation(self):
        self.assertEqual((Path(self.temporary.name)/'edge.env').stat().st_mode&0o777,0o600)
        self.assertEqual(Path(self.temporary.name).stat().st_mode&0o777,0o700)
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute("select rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls from pg_roles where rolname=%s",(LOGIN,)).fetchone(),(True,False,False,False,False,False,False))
            self.assertEqual(c.execute("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in('public','prumo_private') and has_function_privilege(%s,p.oid,'EXECUTE')",(LOGIN,)).fetchone()[0],2)
        for statement in ('set role postgres','set role prumo_s0_g1_executor_local','set role prumo_s1_admin_domain_local','set role prumo_s1_professional_validator_local','set role prumo_s1_edge_custodian_local',
          'select * from auth.users','select * from auth.sessions','select * from '+TABLE,
          'select * from prumo_private.cfi01_signing_keys_local','select * from prumo_private.s1_i80_previews',
          'select * from public.equipe_prumo_s1','select * from public.casos_humanos',
          'create table public.i83_forbidden(x int)','create table prumo_private.i83_forbidden(x int)',
          "grant select on public.equipe_prumo_s1 to prumo_s1_admin_edge_local",
          'insert into prumo_private.s1_excecoes_caso_i61 default values',
          'select prumo_private.g1_manual_signed_local('+','.join(['null']*11)+')',
          'select prumo_private.cfi01_signed_prerequisite_local('+','.join(['null']*10)+')'):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(self.credential.dsn(self.db)) as c:c.execute(statement)
        self.assertEqual(self.edge('i80',self.wire('INVENTORY',limit=1))[1]['state'],'INVENTORY')

    def test_i83_02_key_is_scoped_and_not_present_in_legacy_vault(self):
        with psycopg.connect(self.db) as c:
            value=c.execute('select secret,active from prumo_private.cfi01_signing_keys_local where key_id=%s',(self.credential.key_id,)).fetchone()
            self.assertTrue(value[0]==bytes(32) and not value[1])
            self.assertTrue(value[0]!=self.credential.secret,'inactive anchor must not contain HMAC material')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.signed(self.credential,dsn=self.dsn)
        # A legacy fixture key cannot be used from the dedicated SQL session.
        old=Credential(key_id=self.key_id,secret=self.secret)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.signed(old,dsn=self.credential.dsn(self.db))

    def test_i83_03_expired_key_denies_already_open_edge_pool(self):
        with psycopg.connect(self.db) as c:
            c.execute('grant prumo_s1_edge_custodian_local to postgres with inherit false,set true');c.execute('set local role prumo_s1_edge_custodian_local')
            c.execute('update '+TABLE+" set not_before=clock_timestamp()-interval '2 hours',expires_at=clock_timestamp()-interval '1 hour' where key_id=%s",(self.credential.key_id,))
            c.execute('reset role');c.execute('revoke prumo_s1_edge_custodian_local from postgres')
        try:self.assertEqual(self.edge('i80',self.wire('INVENTORY',limit=1))[1]['state'],'DENIED')
        finally:self.rotate_runtime()

    def test_i83_04_wrong_hmac_real_edge_denied_then_valid_recovers(self):
        wrong=Credential();self.credentials.append(wrong)
        bad={**self.runtime_env,'PRUMO_I82_HMAC_HEX':wrong.secret.hex()}
        try:
            self.restart(bad);before=self.counters()
            self.assertEqual(self.edge('i80',self.wire('INVENTORY',limit=1))[1]['state'],'DENIED');self.assertEqual(self.counters(),before)
        finally:self.restart(self.runtime_env)

    def test_i83_05_missing_hmac_real_edge_fails_before_sql(self):
        try:
            self.restart({**self.runtime_env,'PRUMO_I82_HMAC_HEX':''},ready=False)
            code,b,_=self.raw('i80',self.wire('INVENTORY',limit=1),self.director_token)
            self.assertEqual((code,b['commit']),(503,'NOT_ATTEMPTED'))
        finally:self.restart(self.runtime_env)

    def test_i83_06_wrong_sql_password_no_fallback(self):
        try:
            wrong=Credential();self.credentials.append(wrong)
            self.restart({**self.runtime_env,'PRUMO_I82_DATABASE_URL':wrong.dsn(self.db,True)})
            code,b,_=self.raw('i80',self.wire('INVENTORY',limit=1),self.director_token)
            self.assertEqual(code,503);self.assertNotEqual(b['commit'],'CONFIRMED')
        finally:self.restart(self.runtime_env)

    def test_i83_07_rotation_new_works_old_password_and_live_session_do_not_recover(self):
        old=self.credential
        with psycopg.connect(old.dsn(self.db)) as existing:
            self.rotate_runtime()
            with self.assertRaises(psycopg.OperationalError):psycopg.connect(old.dsn(self.db))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                query,proof=self.proof_for(old,self.wire('INVENTORY',limit=1),'i80')
                existing.execute(query,proof)
        self.assertEqual(self.edge('i80',self.wire('INVENTORY',limit=1))[1]['state'],'INVENTORY')

    def test_i83_08_key_revocation_blocks_pooled_edge_without_restart(self):
        revoke(self.db,self.credential.key_id)
        try:
            for _ in range(2):self.assertEqual(self.edge('i80',self.wire('INVENTORY',limit=1))[1]['state'],'DENIED')
        finally:self.rotate_runtime()

    def test_i83_09_command_before_key_revocation_commits_revocation_waits_then_denies(self):
        actor,_=register(self.api,self.anon)
        with psycopg.connect(self.db) as blocker,ThreadPoolExecutor(max_workers=2) as pool:
            blocker.execute('select ator_id from public.equipe_prumo_s1 where ator_id=%s for update',(self.director,));pid=blocker.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(self.edge,'i79',self.professional('REGISTER',actor));self.wait_blocker(pid)
            revoked=pool.submit(revoke,self.db,self.credential.key_id)
            end=time.monotonic()+5;observed=False
            while time.monotonic()<end:
                with psycopg.connect(self.db) as monitor:
                    observed=bool(monitor.execute("select 1 from pg_stat_activity a where a.wait_event_type='Lock' and exists(select 1 from pg_stat_activity b where b.pid=any(pg_blocking_pids(a.pid)) and b.usename=%s)",(LOGIN,)).fetchone())
                if observed:break
                time.sleep(.025)
            self.assertTrue(observed,'real credential revoker lock was not observed');self.assertFalse(revoked.done())
            blocker.commit();self.assertEqual(future.result(timeout=15)[1]['state'],'APPLIED');revoked.result(timeout=15)
        try:self.assertEqual(self.edge('i80',self.wire('INVENTORY',limit=1))[1]['state'],'DENIED')
        finally:self.rotate_runtime()

    def test_i83_10_revocation_first_waiting_command_denied_without_mutation(self):
        actor,_=register(self.api,self.anon);before=self.counters()
        with psycopg.connect(self.db) as holder,ThreadPoolExecutor(max_workers=1) as pool:
            holder.execute('grant prumo_s1_edge_custodian_local to postgres with inherit false,set true');holder.execute('set local role prumo_s1_edge_custodian_local')
            holder.execute('update '+TABLE+' set enabled=false,secret=null,revoked_at=clock_timestamp() where key_id=%s',(self.credential.key_id,));pid=holder.execute('select pg_backend_pid()').fetchone()[0]
            future=pool.submit(self.edge,'i79',self.professional('REGISTER',actor));self.wait_blocker(pid)
            holder.execute('reset role');holder.execute('revoke prumo_s1_edge_custodian_local from postgres');holder.commit()
            self.assertEqual(future.result(timeout=15)[1]['state'],'DENIED')
        try:self.assertEqual(self.counters(),before)
        finally:self.rotate_runtime()

    def test_i83_11_committed_request_reconciles_after_key_password_rotation(self):
        actor,_=register(self.api,self.anon);p=self.professional('REGISTER',actor)
        a=self.edge('i79',p)[1];self.assertEqual(a['state'],'APPLIED')
        self.rotate_runtime()
        b=self.edge('i79',p)[1];self.assertEqual(b['state'],'ALREADY_APPLIED');self.assertEqual(a['receipt']['request_id'],b['receipt']['request_id'])
        with psycopg.connect(self.db) as c:self.assertEqual(c.execute('select count(*) from public.equipe_prumo_s1 where ator_id=%s',(actor,)).fetchone()[0],1)

    def test_i83_12_password_expiry_denies_new_connection_without_altering_human_auth(self):
        with psycopg.connect(self.db) as c:c.execute("alter role prumo_s1_admin_edge_local valid until '2000-01-01 UTC'")
        try:
            with self.assertRaises(psycopg.OperationalError):psycopg.connect(self.credential.dsn(self.db))
        finally:self.rotate_runtime()

    def test_i83_13_key_expires_during_domain_wait_entire_command_rolls_back(self):
        actor,_=register(self.api,self.anon);before=self.counters()
        with psycopg.connect(self.db) as c:
            c.execute('grant prumo_s1_edge_custodian_local to postgres with inherit false,set true');c.execute('set local role prumo_s1_edge_custodian_local')
            c.execute('update '+TABLE+" set expires_at=clock_timestamp()+interval '2 seconds' where key_id=%s",(self.credential.key_id,))
            c.execute('reset role');c.execute('revoke prumo_s1_edge_custodian_local from postgres')
        try:
            with psycopg.connect(self.db) as holder,ThreadPoolExecutor(max_workers=1) as pool:
                holder.execute('select ator_id from public.equipe_prumo_s1 where ator_id=%s for update',(self.director,));pid=holder.execute('select pg_backend_pid()').fetchone()[0]
                future=pool.submit(self.edge,'i79',self.professional('REGISTER',actor));self.wait_blocker(pid)
                time.sleep(2.1)
                holder.commit();self.assertEqual(future.result(timeout=15)[1]['state'],'DENIED')
            self.assertEqual(self.counters(),before)
            with psycopg.connect(self.db) as c:self.assertEqual(c.execute('select count(*) from public.equipe_prumo_s1 where ator_id=%s',(actor,)).fetchone()[0],0)
        finally:self.rotate_runtime()

    def test_i83_14_i80_preview_survives_credential_rotation_not_human_authority_change(self):
        actor,_,_=self.legacy(pending=True);p=self.http_preview(actor)
        self.rotate_runtime()
        wire=self.apply_wire(p);a=self.edge('i80',wire)[1];self.assertEqual(a['state'],'APPLIED')
        self.rotate_runtime()
        b=self.edge('i80',wire)[1];self.assertEqual(b['state'],'ALREADY_APPLIED');self.assertEqual(a['receipt']['request_id'],b['receipt']['request_id'])
        self.assertEqual(self.preserved(actor)['state'],'pendente')

    def test_i83_15_nonce_remains_global_across_key_rotation(self):
        actor,_=register(self.api,self.anon);p=self.dto('REGISTER',actor);nonce=uuid4()
        self.assertEqual(self.signed(self.credential,p,nonce=nonce)['outcome'],'APPLIED')
        self.rotate_runtime();before=self.counters()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.signed(self.credential,p,nonce=nonce)
        self.assertEqual(self.counters(),before)


if __name__=='__main__':
    suite=unittest.TestSuite(DedicatedEdgeTests(n) for n in unittest.defaultTestLoader.getTestCaseNames(DedicatedEdgeTests) if n.startswith(('test_edge_','test_i83_')))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
