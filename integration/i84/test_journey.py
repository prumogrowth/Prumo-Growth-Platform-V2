"""Real local CLI journey; fixtures are exclusively here, never in the operator.

No mocked GoTrue/SQL/Edge. One fault replaces only the local env-file write AFTER
actual credential COMMIT; explicit recovery must physically retire that material.
"""
import json
import os
from pathlib import Path
import subprocess
import time
import unittest
from unittest.mock import patch
from urllib import request,error
from uuid import uuid4
import psycopg
from local_admin import boundary as b,environment as e,custody
from local_admin.operation import Operator,resources
from integration.i83 import provision_local as p
from scripts.test_s0_cfi01_auth_rest_local import register

class Journey(unittest.TestCase):
    def cli(self,command,ok=True):
        result=subprocess.run(['python3','-m','local_admin',command],cwd=b.ROOT,capture_output=True)
        body=json.loads(result.stdout)
        self.assertEqual(result.returncode,0 if ok else 2,body)
        self.assertFalse(result.stderr,'operator leaked diagnostics')
        for secret in self.sensitive:self.assertNotIn(secret.encode(),result.stdout+result.stderr)
        return body

    def http(self,payload,token=None):
        data=json.dumps({'version':'prumo.admin.v1','command':payload}).encode()
        h={'apikey':self.env['ANON_KEY'],'Content-Type':'application/json','Authorization':'Bearer '+(token or self.token)}
        q=request.Request(self.env['API_URL']+'/functions/v1/prumo-admin-i82/v1/i79',data=data,headers=h)
        try:r=request.urlopen(q,timeout=25)
        except error.HTTPError as x:r=x
        with r:code=r.status;raw=r.read(262145)
        for secret in self.sensitive:self.assertNotIn(secret.encode(),raw)
        return code,json.loads(raw)

    def remember(self):
        v=custody.read_env(b.DEFAULT)
        from urllib.parse import urlsplit
        self.sensitive.extend([v['PRUMO_I82_HMAC_HEX'],v['PRUMO_I82_DATABASE_URL'],urlsplit(v['PRUMO_I82_DATABASE_URL']).password])
        return v

    def count(self):
        with e.database() as c:return c.execute('select count(*) from prumo_private.s1_i79_requests').fetchone()[0]

    def mark(self,name):self.evidence.append(name);print('I84-PROOF:',name,flush=True)

    def test_real_journey(self):
        self.evidence=[];self.sensitive=[];self.env=e.discover();self.mark('01_cli_init_prepare_without_human_fixture')
        with e.database() as c:
            self.assertEqual(c.execute('select count(*) from auth.users').fetchone()[0],0)
            self.assertEqual(c.execute("select count(*) from pg_roles where rolname like 'prumo_%' and rolcanlogin").fetchone()[0],0)
        self.assertEqual(self.cli('status')['phase'],'PREPARED')
        self.assertEqual(self.cli('serve',False)['code'],'SERVE_REQUIRES_PROVISIONED')
        self.mark('02_absent_credentials_denied')
        self.assertEqual(self.cli('provision')['credential'],'VALID');old=self.remember()
        self.assertTrue(self.cli('serve')['ready']);self.mark('03_dedicated_runtime_ready')
        # Human bootstrap is not an operator feature. Synthetic and installer-only.
        actor,self.token=register(self.env['API_URL'],self.env['ANON_KEY'])
        target,_=register(self.env['API_URL'],self.env['ANON_KEY'])
        with e.database() as c:
            c.execute('insert into public.atores(id) values(%s)',(actor,))
            c.execute('insert into prumo_private.s1_responsaveis_plataforma(ator_id) values(%s)',(actor,))
            c.execute("insert into public.equipe_prumo_s1(ator_id,cargo,estado) values(%s,'diretor','ativo')",(actor,))
        payload={'action':'REGISTER','target_id':str(target),'cargo':'consultor','manager_id':None,'expected_relationship_id':'0','idempotency_key':'i84-'+uuid4().hex}
        code,body=self.http(payload);self.assertEqual((code,body['state']),(200,'APPLIED'));receipt=body['receipt']['request_id'];self.mark('04_gotrue_director_sql_commit')
        before=self.count();self.assertTrue(self.cli('rotate')['ready']);self.remember()
        code,body=self.http(payload);self.assertEqual((code,body['state']),(200,'ALREADY_APPLIED'));self.assertEqual(body['receipt']['request_id'],receipt);self.assertEqual(self.count(),before)
        self.mark('05_rotation_restarts_worker_same_key_reconciles_without_reapply')
        from urllib.parse import urlsplit,urlunsplit
        u=urlsplit(old['PRUMO_I82_DATABASE_URL']);dsn=urlunsplit((u.scheme,u.netloc.replace('supabase_db_prumo-s0-auth-ci:5432','127.0.0.1:54322'),u.path,'',''))
        try:
            with psycopg.connect(dsn,connect_timeout=3):admitted=True
        except psycopg.Error:admitted=False
        self.assertFalse(admitted);self.mark('06_old_sql_password_rejected')
        state=b.load(b.DEFAULT/'state.json');worker_id=state['worker']['container']
        self.assertTrue(self.cli('restart')['ready']);self.assertNotEqual(b.load(b.DEFAULT/'state.json')['worker']['container'],worker_id)
        self.mark('07_explicit_restart_new_container')
        self.assertEqual(self.cli('revoke')['credential'],'REVOKED')
        code,body=self.http(payload);self.assertNotEqual(code,200);self.assertEqual(self.count(),before)
        self.mark('08_old_running_worker_after_revocation_cannot_reapply')
        self.cli('worker-stop');self.assertFalse((b.DEFAULT/'edge.env').exists());self.assertIsNone(b.inspect(b.EDGE));self.mark('09_worker_retired_material_removed')
        self.cli('provision');self.remember();self.cli('serve')
        # Explicit failure after a real successful COMMIT, before custody write.
        self.cli('worker-stop');op=Operator()
        def fail_after_commit(*args,**kwargs):raise OSError('do not expose injected details')
        with patch.object(p,'write_env',fail_after_commit):
            with self.assertRaises(OSError):op.execute('rotate')
        self.assertEqual(self.cli('status')['phase'],'UNCERTAIN')
        self.assertEqual(self.cli('provision',False)['code'],'USE_EXPLICIT_ROTATE')
        self.assertEqual(self.cli('rotate',False)['code'],'CREDENTIAL_OPERATION_REQUIRES_RECOVERY')
        with e.database() as c:self.assertEqual(c.execute('select count(*) from '+p.TABLE+' where enabled and secret is not null').fetchone()[0],1)
        self.cli('recover')
        with e.database() as c:
            self.assertEqual(c.execute('select count(*) from '+p.TABLE+' where enabled or secret is not null').fetchone()[0],0)
            self.assertEqual(c.execute('select rolcanlogin,rolpassword from pg_authid where rolname=%s',(p.LOGIN,)).fetchone(),(False,None))
        self.assertEqual(self.count(),before);self.mark('10_uncertain_commit_recovery_retires_not_retries')
        self.cli('provision');self.remember();self.cli('serve');self.cli('revoke');self.cli('worker-stop')
        op=Operator();op.read();op.verify();final=op.catalog();expected=b.load(b.DEFAULT/'catalog.json');self.assertEqual(final,expected)
        custody.scan(b.DEFAULT,extra=self.sensitive);self.mark('11_exact_catalog_and_log_secrecy')
        # Archive metadata only, before down removes protected local catalog.
        root=Path(os.environ.get('RUNNER_TEMP','/tmp'))
        (root/'prumo_i84_catalog.json').write_text(json.dumps(final,indent=2)+'\n')
        proof=self.cli('down');self.assertTrue(proof['material_removed']);self.assertTrue(proof['resources_absent']);self.assertTrue(proof['retirement_verified'])
        self.assertFalse(any(resources().values()));self.assertEqual(self.cli('down')['phase'],'DISCARDED');self.mark('12_stack_volumes_network_env_log_cleanup_verified')
        proof={'version':'prumo.i84.evidence.v1','checks':self.evidence,'cleanup':proof,'catalog_equal':True,'secret_matches':0}
        data=json.dumps(proof,indent=2)
        for secret in self.sensitive:self.assertNotIn(secret,data)
        (root/'prumo_i84_journey.json').write_text(data+'\n')

if __name__=='__main__':unittest.main(verbosity=2)
