"""Independent real tests. Each test owns an entirely fresh disposable stack.

No deleting organizational history, disabling triggers or sharing a Director
fixture between tests. Only fault scheduling is injected; all effects are real.
"""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time
import unittest
from uuid import uuid4
from local_admin import boundary as b,environment as e
from local_admin.operation import Operator,resources
from local_admin.custody import read_env
from integration.i85 import bootstrap as m,storage
from integration.i84.capture import reject_material

RESULTS=[]

class Resistance(unittest.TestCase):
    def setUp(self):
        if os.environ.get('PRUMO_I85_DISPOSABLE')!='YES':raise RuntimeError('I85 resistance opt-in required')
        self.children=[];self.sensitive=[];self.cleanup_proof=None;self.observations={}
        self.addCleanup(self.emergency_cleanup)
        self.ops=Operator();self.ops.execute('init');self.ops.execute('prepare',os.environ.get('PRUMO_G1_SOURCE_REPO','work-s1-sources'))
        self.parent=b.load(b.DEFAULT/'state.json');self.op=m.Bootstrap()
        if not self._testMethodName.startswith(('test_00','test_052')):self.op.init()
        self.source_catalog=b.load(b.DEFAULT/'catalog.json')

    def emergency_cleanup(self):
        if self.cleanup_proof is not None:return
        # A setup failure still attempts only the owned I84 teardown. Failure
        # remains an ERROR; cleanup never turns a partially executed test PASS.
        state_file=b.DEFAULT/'state.json'
        if state_file.exists():
            Operator().execute('down')
            if m.ROOT.exists() or m.ROOT.with_name(m.ROOT.name+'.disposing').exists():
                os.environ['PRUMO_I85_ABANDON']='PRESERVE_EVIDENCE_AFTER_VERIFIED_LAB_DISCARD'
                try:m.Bootstrap().abandon_after_stack_down()
                finally:os.environ.pop('PRUMO_I85_ABANDON',None)

    def cli(self,action,*args,ok=True):
        result=subprocess.run(['python3','-m','integration.i85',action,*args],cwd=b.ROOT,capture_output=True,timeout=30)
        reject_material(result.stdout+result.stderr,self.sensitive)
        if result.stderr or result.returncode!=(0 if ok else 2):raise AssertionError('I85_CLI_RESULT_WITHHELD')
        return json.loads(result.stdout)

    def identity(self,label='director'):
        self.op.create(label);self.op.load();self.sensitive.extend(self.op.secrets().values())
        return self.op.state['identities'][label]['uuid']

    def approval(self):
        os.environ['PRUMO_I85_DIRECTOR_APPROVAL']=m.APPROVAL
        try:self.op.authorize_director()
        finally:os.environ.pop('PRUMO_I85_DIRECTOR_APPROVAL',None)

    def active(self):
        self.identity();self.approval();self.op.grant_director();self.op.load()
        return self.op.state['authority']['uuid']

    def start_edge(self):
        self.ops.execute('provision');values=read_env(b.DEFAULT)
        from urllib.parse import urlsplit
        self.sensitive.extend([values['PRUMO_I82_HMAC_HEX'],values['PRUMO_I82_DATABASE_URL'],urlsplit(values['PRUMO_I82_DATABASE_URL']).password,m._key()])
        self.ops.execute('serve')

    def inventory(self,token):
        from urllib import request,error
        env=e.discover();payload={'version':'prumo.admin.v1','command':{'action':'INVENTORY','target_id':None,'cargo':None,'manager_id':None,'expected_sha256':None,'preview_id':None,'cursor':None,'limit':1,'idempotency_key':'i85-audit-'+uuid4().hex}}
        q=request.Request(env['API_URL']+'/functions/v1/prumo-admin-i82/v1/i80',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','apikey':env['ANON_KEY'],'Authorization':'Bearer '+token})
        try:response=request.urlopen(q,timeout=20)
        except error.HTTPError as x:response=x
        with response:status=response.status;raw=response.read(262145)
        reject_material(raw,self.sensitive)
        return status,json.loads(raw)

    def stopped(self,action,stage,label='director'):
        read_fd,write_fd=os.pipe();env=os.environ.copy();env['PRUMO_I85_PROBE_FD']=str(write_fd)
        process=subprocess.Popen(['python3','-m','integration.i85.fault_driver',action,'--stage',stage,'--label',label],cwd=b.ROOT,env=env,pass_fds=(write_fd,),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        os.close(write_fd);self.children.append(process)
        try:
            ready,_,_=select.select([read_fd],[],[],30)
            if not ready or os.read(read_fd,256).strip()!=stage.encode():raise AssertionError('I85_FAULT_POINT_NOT_REACHED')
        finally:os.close(read_fd)
        return process

    def kill(self,process):
        process.kill();stdout,stderr=process.communicate(timeout=10)
        reject_material(stdout+stderr,self.sensitive)
        self.assertEqual(process.returncode,-signal.SIGKILL)
        # Server-side rollback after a dead client must settle before assertions.
        until=time.monotonic()+10
        while time.monotonic()<until:
            with e.database() as c:
                waiting=c.execute("select count(*) from pg_stat_activity where application_name='i85-crash-probe'").fetchone()[0]
            if not waiting:break
            time.sleep(.05)

    def assert_authority_count(self,count):
        with e.database() as c:
            actual=c.execute('select count(*) from prumo_private.s1_responsaveis_plataforma where ativo').fetchone()[0]
        self.assertEqual(actual,count)

    def test_000_init_after_directory_sigkill_recovers_without_identity(self):
        self.kill(self.stopped('init','init-dir'))
        self.assertTrue(m.ROOT.exists())
        self.assertEqual(self.op.recover_journal()['authority'],'NONE')
        self.assertEqual(self.op.status()['identities'],{})

    def test_001_init_after_initial_state_sigkill_recovers(self):
        self.kill(self.stopped('init','init-state'))
        self.assertEqual(self.cli('status',ok=False)['state'],'BLOCKED')
        self.assertEqual(self.op.recover_journal()['authority'],'NONE')

    def test_010_orphan_secret_before_identity_intent_blocks(self):
        self.kill(self.stopped('create','create-before-intent'))
        self.assertEqual(self.cli('create','--label','director',ok=False)['code'],'I85_SECRET_STATE_DIVERGENCE')
        with self.assertRaises(b.Blocked):self.op.recover_journal()
        with e.database() as c:self.assertEqual(c.execute('select count(*) from auth.users').fetchone()[0],0)

    def test_011_identity_intent_without_post_remains_conservatively_blocked(self):
        self.kill(self.stopped('create','create-after-intent'))
        with self.assertRaises(b.Blocked):self.op.reconcile_identity('director')
        with self.assertRaises(b.Blocked):self.op.create('director')
        with e.database() as c:self.assertEqual(c.execute('select count(*) from auth.users').fetchone()[0],0)

    def test_012_post_committed_before_ack_reconciles_same_uuid(self):
        self.kill(self.stopped('create','create-post-ack'))
        self.op.reconcile_identity('director');self.op.load();identifier=self.op.state['identities']['director']['uuid']
        self.op.reconcile_identity('director');self.op.load()
        self.assertEqual(self.op.state['identities']['director']['uuid'],identifier)
        with e.database() as c:self.assertEqual(c.execute('select count(*) from auth.users').fetchone()[0],1)

    def test_013_reconciliation_sigkill_does_not_repeat_creation(self):
        self.identity();self.op.state['identities']['director']['phase']='CREATE_UNKNOWN';self.op.save('TEST_UNCERTAIN_FIXTURE')
        self.kill(self.stopped('reconcile-identity','identity-reconcile'))
        self.op.reconcile_identity('director')
        with e.database() as c:self.assertEqual(c.execute('select count(*) from auth.users').fetchone()[0],1)

    def test_014_two_direct_python_processes_create_one_identity(self):
        commands=[]
        for _ in range(2):
            child=subprocess.Popen(['python3','-m','integration.i85.fault_driver','create','--label','director'],cwd=b.ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.children.append(child);commands.append(child)
        codes=[]
        for child in commands:
            stdout,stderr=child.communicate(timeout=30);reject_material(stdout+stderr,self.sensitive);codes.append(child.returncode)
        self.assertEqual(sorted(codes),[0,2]);self.op.load()
        with e.database() as c:self.assertEqual(c.execute('select count(*) from auth.users').fetchone()[0],1)

    def test_020_grant_before_intent_has_no_mutation(self):
        self.identity();self.approval();self.kill(self.stopped('grant-director','grant-before-intent'))
        self.assert_authority_count(0);self.op.grant_director();self.assert_authority_count(1)

    def test_021_grant_precommit_kill_rolls_back_and_blocks_reissue(self):
        self.identity();self.approval();process=self.stopped('grant-director','grant-pre-commit')
        self.assertEqual(self.cli('grant-director',ok=False)['code'],'LOCAL_OPERATION_BUSY')
        self.kill(process);self.assert_authority_count(0)
        with self.assertRaises(b.Blocked):self.op.reconcile_authority()
        with self.assertRaises(b.Blocked):self.op.grant_director()
        with self.assertRaises(b.Blocked):self.op.dispose()

    def test_022_grant_postcommit_kill_reconciles_without_second_authority(self):
        self.identity();self.approval();self.kill(self.stopped('grant-director','grant-post-commit'))
        self.assert_authority_count(1);self.op.reconcile_authority();self.assert_authority_count(1)
        with self.assertRaises(b.Blocked):self.op.grant_director()

    def test_023_confirmation_kill_reconciles(self):
        self.identity();self.approval();self.kill(self.stopped('grant-director','grant-confirmation'))
        self.assertEqual(self.op.reconcile_authority()['authority'],'ACTIVE')

    def test_024_staged_active_journal_is_not_silently_promoted(self):
        self.identity();self.approval();self.kill(self.stopped('grant-director','grant-journal-replace'))
        self.assertTrue(storage.residues(m.ROOT))
        self.assertEqual(self.cli('status',ok=False)['code'],'I85_JOURNAL_RECOVERY_REQUIRED')
        self.assertEqual(self.op.recover_journal()['authority'],'COMMIT_UNKNOWN')
        self.assertTrue((m.ROOT/'evidence').exists());self.op.reconcile_authority();self.assert_authority_count(1)

    def test_030_two_process_approvals_cannot_overwrite_custody(self):
        self.identity();self.identity('outsider')
        env=os.environ.copy();env['PRUMO_I85_DIRECTOR_APPROVAL']=m.APPROVAL
        def approve():return subprocess.run(['python3','-m','integration.i85','authorize-director'],cwd=b.ROOT,env=env,capture_output=True,timeout=30)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:approve(),range(2)))
        self.assertEqual(sorted(r.returncode for r in results),[0,2]);self.op.load()
        self.assertEqual(self.op.state['approval']['uuid'],self.op.state['identities']['director']['uuid'])
        with self.assertRaises(b.Blocked):m.Bootstrap(m.ROOT.with_name('other-custody'))

    def test_031_distinct_canonical_candidate_sql_transactions_have_one_winner(self):
        self.identity();self.identity('outsider')
        first=self.stopped('sql-candidate','sql-ready','director');second=self.stopped('sql-candidate','sql-ready','outsider')
        for process in (first,second):os.kill(process.pid,signal.SIGCONT)
        codes=[]
        for process in (first,second):
            stdout,stderr=process.communicate(timeout=20);reject_material(stdout+stderr,self.sensitive);codes.append(process.returncode)
        self.assertEqual(sorted(codes),[0,2]);self.assert_authority_count(1)
        with e.database() as c:self.assertEqual(c.execute("select count(*) from public.equipe_prumo_s1 where cargo='diretor'").fetchone()[0],1)
        with self.assertRaises(b.Blocked):self.op.dispose() # journal NONE is not authority proof

    def test_032_staged_approval_requires_explicit_ratification(self):
        self.identity();os.environ['PRUMO_I85_DIRECTOR_APPROVAL']=m.APPROVAL
        try:self.kill(self.stopped('authorize-director','approval-journal-replace'))
        finally:os.environ.pop('PRUMO_I85_DIRECTOR_APPROVAL',None)
        result=self.op.recover_journal();self.assertTrue(result['approval_pending'])
        with self.assertRaises(b.Blocked):self.op.grant_director()
        self.op.load();old=self.op.state['approval']['approval_id']
        self.approval();self.op.load();self.assertEqual(self.op.state['approval']['approval_id'],old)
        self.op.grant_director();self.assert_authority_count(1)

    def test_040_revocation_precommit_can_resume_only_negative_mutation(self):
        self.active();self.sensitive.append(self.op.token('director'))
        self.kill(self.stopped('revoke-director','revoke-pre-commit'));self.assert_authority_count(1)
        with self.assertRaises(b.Blocked):self.op.reconcile_authority()
        self.assertEqual(self.op.revoke_director()['authority'],'REVOKED');self.assert_authority_count(0)

    def test_041_revocation_postcommit_reconciles(self):
        self.active();self.sensitive.append(self.op.token('director'))
        self.kill(self.stopped('revoke-director','revoke-post-commit'));self.assert_authority_count(0)
        self.assertEqual(self.op.reconcile_authority()['authority'],'REVOKED')

    def test_042_session_retirement_rolls_back_together_with_authority(self):
        self.active();self.sensitive.append(self.op.token('director'))
        self.kill(self.stopped('revoke-director','session-retirement'));self.assert_authority_count(1)
        with e.database() as c:self.assertGreater(c.execute('select count(*) from auth.sessions').fetchone()[0],0)
        self.op.revoke_director()
        with e.database() as c:self.assertEqual(c.execute('select count(*) from auth.sessions').fetchone()[0],0)

    def test_043_refresh_and_fresh_login_do_not_recover_revoked_authority(self):
        self.start_edge();identifier=self.active();self.op.load()
        result=m._api('POST','/auth/v1/token?grant_type=password',{'email':self.op.state['identities']['director']['email'],'password':self.op.secrets()['director']},admin=False,token=e.discover()['ANON_KEY'])
        access=result['access_token'];refresh=result['refresh_token'];self.sensitive.extend([access,refresh])
        self.assertEqual(self.inventory(access)[0],200);self.op.revoke_director()
        self.assertIn(self.inventory(access)[0],(401,403))
        try:
            refreshed=m._api('POST','/auth/v1/token?grant_type=refresh_token',{'refresh_token':refresh},admin=False,token=e.discover()['ANON_KEY'])
        except b.Blocked:refreshed=None
        self.observations['refresh']='REFRESHED_BUT_NO_AUTHORITY' if refreshed and refreshed.get('access_token') else 'REJECTED'
        if refreshed and refreshed.get('access_token'):
            self.sensitive.append(refreshed['access_token']);self.assertIn(self.inventory(refreshed['access_token'])[0],(401,403))
        fresh=self.op.token('director');self.sensitive.append(fresh)
        self.assertEqual(self.inventory(fresh)[0],403)
        self.observations['fresh_password_login']='AUTHENTICATED_ADMIN_DENIED'
        with e.database() as c:
            self.assertEqual(c.execute('select cargo,estado from public.equipe_prumo_s1 where ator_id=%s',(identifier,)).fetchone(),('diretor','ativo'))
        self.op.revoke_director() # explicitly retire sessions created by fresh Auth login

    def test_044_original_inverse_lock_order_has_physical_deadlock(self):
        self.active();self.sensitive.append(self.op.token('director'));self.op.load()
        identifier=self.op.state['authority']['uuid']
        import threading
        ready=threading.Event()
        def inverse():
            with e.database() as c:
                try:
                    c.execute("set local lock_timeout='5s'")
                    c.execute('select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for update',(identifier,));ready.set()
                    c.execute('delete from auth.sessions where user_id=%s',(identifier,))
                    return 'COMPLETED'
                except Exception as error:return getattr(error,'sqlstate','WITHHELD')
                finally:c.rollback()
        with e.database() as first,ThreadPoolExecutor(max_workers=1) as pool:
            first.execute('select id from auth.sessions where user_id=%s for share',(identifier,))
            future=pool.submit(inverse);self.assertTrue(ready.wait(10))
            try:
                first.execute('select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for share',(identifier,));own='COMPLETED'
            except Exception as error:own=getattr(error,'sqlstate','WITHHELD')
            finally:first.rollback()
            other=future.result(timeout=10)
        self.assertIn('40P01',(own,other));self.assert_authority_count(1)
        self.observations['original_lock_order']='40P01_REPRODUCED_WITH_ROLLBACK'

    def test_045_fixed_revocation_drains_real_signed_http_before_withdrawing_authority(self):
        self.start_edge();identifier=self.active();token=self.op.token('director');self.sensitive.append(token)
        with e.database() as blocker,ThreadPoolExecutor(max_workers=1) as pool:
            blocker.execute('select ator_id from public.equipe_prumo_s1 where ator_id=%s for update',(identifier,))
            pid=blocker.execute('select pg_backend_pid()').fetchone()[0]
            request=pool.submit(self.inventory,token)
            until=time.monotonic()+10
            while time.monotonic()<until:
                with e.database() as monitor:waiting=monitor.execute('select count(*) from pg_stat_activity where %s=any(pg_blocking_pids(pid))',(pid,)).fetchone()[0]
                if waiting:break
                time.sleep(.05)
            else:self.fail('signed HTTP did not reach the real row lock')
            child=subprocess.Popen(['python3','-m','integration.i85.fault_driver','revoke-director'],cwd=b.ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.children.append(child)
            until=time.monotonic()+4
            while time.monotonic()<until:
                with e.database() as monitor:waiting=monitor.execute("select count(*) from pg_stat_activity where application_name='i85-crash-probe' and wait_event_type='Lock'").fetchone()[0]
                if waiting:break
                time.sleep(.05)
            else:self.fail('revocation did not wait on the live command')
            # Unlike the old order, competence is not already locked by revoke.
            with e.database() as monitor:monitor.execute('select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for share nowait',(identifier,))
            blocker.commit();self.assertEqual(request.result(timeout=15)[0],200)
            stdout,stderr=child.communicate(timeout=15);reject_material(stdout+stderr,self.sensitive)
            self.assertEqual(child.returncode,0)
        self.assert_authority_count(0);self.assertIn(self.inventory(token)[0],(401,403))

    def test_050_private_profile_has_no_installer_credentials_or_bootstrap_endpoint(self):
        self.start_edge()
        from integration.i85.edge_profile import verify,FORBIDDEN
        state=b.load(b.DEFAULT/'state.json');self.assertTrue(verify(state))
        actual=json.loads(b.docker('inspect','--format','{{json .Config.Env}}',b.EDGE));names={v.split('=',1)[0] for v in actual}
        self.assertFalse(names&FORBIDDEN)
        identifier=self.identity();token=self.op.token('director');self.sensitive.append(token)
        self.assertEqual(self.inventory(token)[0],403)
        m._api('PUT','/auth/v1/user',{'data':{'cargo':'diretor','role':'service_role','authority':True}},admin=False,token=token)
        self.assertEqual(self.inventory(token)[0],403);self.assert_authority_count(0)
        env=e.discover()
        from urllib import request,error
        q=request.Request(env['API_URL']+'/functions/v1/prumo-admin-i82/v1/bootstrap',data=b'{}',headers={'apikey':env['ANON_KEY'],'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        try:r=request.urlopen(q,timeout=10)
        except error.HTTPError as x:r=x
        with r:self.assertEqual(r.status,404)

    def test_052_late_optin_rejects_legacy_worker_and_no_fallback_after_bootstrap(self):
        self.ops.execute('provision');os.environ.pop('PRUMO_I85_DISPOSABLE')
        try:self.ops.execute('serve')
        finally:os.environ['PRUMO_I85_DISPOSABLE']='YES'
        actual=json.loads(b.docker('inspect','--format','{{json .Config.Env}}',b.EDGE));names={v.split('=',1)[0] for v in actual}
        self.assertTrue({'SUPABASE_SERVICE_ROLE_KEY','SUPABASE_DB_URL','SUPABASE_INTERNAL_JWT_SECRET'}<=names)
        with self.assertRaises(b.Blocked):self.op.init()
        with e.database() as c:self.assertEqual(c.execute('select count(*) from auth.users').fetchone()[0],0)
        self.ops.execute('worker-stop');self.ops.execute('serve');self.op.init()
        self.ops.execute('worker-stop');os.environ.pop('PRUMO_I85_DISPOSABLE')
        try:self.ops.execute('serve')
        finally:os.environ['PRUMO_I85_DISPOSABLE']='YES'
        from integration.i85.edge_profile import verify
        self.assertTrue(verify(b.load(b.DEFAULT/'state.json')))
        self.observations['legacy_runtime_env']='PRIVILEGED_VARIABLE_NAMES_PRESENT'
        self.observations['i85_runtime_env']='PRIVILEGED_VARIABLES_ABSENT_NO_FALLBACK'

    def test_060_disposal_after_intent_is_resumable(self):
        self.identity();self.kill(self.stopped('dispose','disposal-intent'))
        self.assertTrue(self.op.dispose()['private_material_removed']);self.assertFalse(m.ROOT.exists())

    def test_061_disposal_after_directory_rename_is_resumable(self):
        self.identity();self.kill(self.stopped('dispose','disposal-rename'))
        self.assertTrue(self.op.dispose()['private_material_removed']);self.assertFalse(m.ROOT.exists())

    def test_062_disposal_after_password_unlink_is_resumable(self):
        self.identity();self.kill(self.stopped('dispose','disposal-material'))
        self.assertTrue(self.op.dispose()['private_material_removed']);self.assertFalse(m.ROOT.exists())

    def test_070_corrupt_journal_does_not_delete_live_authority(self):
        self.active();self.op.load();self.op.state['authority']={'phase':'NONE','uuid':None};self.op.save('TEST_DIVERGENCE')
        with self.assertRaises(b.Blocked):self.op.dispose()
        with self.assertRaises(b.Blocked):self.op.status()
        with self.assertRaises(b.Blocked):self.op.recover_journal()
        self.assert_authority_count(1)

    def test_071_torn_next_requires_retention_not_guessing(self):
        self.identity();path=m.ROOT/'state.json.next'
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(b'{"authority":');stream.flush();os.fsync(stream.fileno())
        with self.assertRaises(b.Blocked):self.op.recover_journal()
        self.assertTrue(path.exists());self.assertEqual(self.cli('grant-director',ok=False)['state'],'BLOCKED')

    def test_080_old_identity_token_and_operator_cannot_cross_stack(self):
        self.start_edge();old_uuid=self.active();old_token=self.op.token('director');self.sensitive.append(old_token);old=self.op
        self.op.revoke_director();self.op.dispose();self.ops.execute('down')
        self.ops=Operator();self.ops.execute('init');self.ops.execute('prepare',os.environ.get('PRUMO_G1_SOURCE_REPO','work-s1-sources'))
        self.parent=b.load(b.DEFAULT/'state.json');self.source_catalog=b.load(b.DEFAULT/'catalog.json')
        self.op=m.Bootstrap();self.op.init();new_uuid=self.identity();self.start_edge()
        self.assertNotEqual(new_uuid,old_uuid)
        with self.assertRaises(b.Blocked):old.token('director')
        self.assertIn(self.inventory(old_token)[0],(401,403))
        with e.database() as c:self.assertFalse(c.execute('select exists(select 1 from auth.users where id=%s)',(old_uuid,)).fetchone()[0])
        self.assert_authority_count(0)

    def tearDown(self):
        for process in getattr(self,'children',[]):
            if process.poll() is None:process.kill();process.communicate(timeout=10)
        if not hasattr(self,'parent'):return
        try:
            files=[]
            if m.ROOT.exists():
                files.extend(m.ROOT.iterdir())
                if (m.ROOT/'evidence').exists():files.extend((m.ROOT/'evidence').iterdir())
            for path in files:
                if 'secrets.json' in path.name and path.is_file():
                    storage.checked(path)
                    import re
                    self.sensitive.extend(v.decode() for v in re.findall(rb'[A-Za-z0-9_-]{40,128}',path.read_bytes()))
            if (b.DEFAULT/'edge.env').exists():
                from urllib.parse import urlsplit
                values=read_env(b.DEFAULT)
                self.sensitive.extend([values['PRUMO_I82_HMAC_HEX'],values['PRUMO_I82_DATABASE_URL'],urlsplit(values['PRUMO_I82_DATABASE_URL']).password,m._key()])
            # No fixture-history deletion or disabled triggers: each test's
            # database is discarded in full. First try only safe negative cleanup.
            if m.ROOT.exists():
                try:
                    op=m.Bootstrap();op.load()
                    if op.state['authority']['phase']=='COMMIT_UNKNOWN':op.reconcile_authority();op.load()
                    if op.state['authority']['phase'] in ('ACTIVE','REVOKE_UNKNOWN','REVOKED'):op.revoke_director()
                    op.dispose()
                except b.Blocked:pass
            with e.database() as c:
                from integration.i83.catalog import snapshot
                actual=snapshot(c)
                for row in actual['roles']:
                    if row['rolname']=='prumo_s1_admin_edge_local':row['rolcanlogin']=False
                self.assertEqual(actual,self.source_catalog)
            # Scan only in memory; errors never contain values.
            for name in (b.DB,b.KONG,'supabase_auth_'+b.PROJECT):
                reject_material(b.run(['docker','--host=unix:///var/run/docker.sock','logs',name],combined=True),self.sensitive)
            if b.inspect(b.EDGE):reject_material(b.run(['docker','--host=unix:///var/run/docker.sock','logs',b.EDGE],combined=True),self.sensitive)
            proof=self.ops.execute('down');self.assertTrue(proof['resources_absent']);self.assertTrue(proof['material_removed']);self.assertFalse(any(resources().values()))
            if m.ROOT.exists() or m.ROOT.with_name(m.ROOT.name+'.disposing').exists():
                os.environ['PRUMO_I85_ABANDON']='PRESERVE_EVIDENCE_AFTER_VERIFIED_LAB_DISCARD'
                try:retired=m.Bootstrap().abandon_after_stack_down();self.assertTrue(retired['password_material_removed'])
                finally:os.environ.pop('PRUMO_I85_ABANDON',None)
            self.cleanup_proof={'resources_absent':True,'private_password_material_removed':True,'catalog_equal':True}
        finally:
            RESULTS.append({'test':self._testMethodName,'cleanup':self.cleanup_proof or {'status':'FAIL'}})

class ProofResult(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.outcomes=[]
    def addSuccess(self,test):super().addSuccess(test);self.outcomes.append({'test':test._testMethodName,'status':'PASS','observations':test.observations})
    def addFailure(self,test,err):super().addFailure(test,err);self.outcomes.append({'test':test._testMethodName,'status':'FAIL'})
    def addError(self,test,err):super().addError(test,err);self.outcomes.append({'test':test._testMethodName,'status':'FAIL'})

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Resistance)
    planned=[test._testMethodName for test in suite]
    result=unittest.TextTestRunner(verbosity=2,resultclass=ProofResult,failfast=True).run(suite)
    proof={'version':'prumo.i85.resistance.v1','status':'PASS' if result.wasSuccessful() and not result.skipped and result.testsRun==len(planned) else 'FAIL',
           'planned_tests':len(planned),'not_tested':[name for name in planned if name not in {item['test'] for item in result.outcomes}],'tests_run':result.testsRun,'skipped':len(result.skipped),'results':result.outcomes,'cleanup':RESULTS,'faults':'real SIGKILL, real Auth/PG/Edge; wrappers schedule only'}
    (Path(os.environ.get('RUNNER_TEMP','/tmp'))/'prumo_i85_resistance.json').write_text(json.dumps(proof,indent=2)+'\n')
    raise SystemExit(0 if proof['status']=='PASS' else 1)
