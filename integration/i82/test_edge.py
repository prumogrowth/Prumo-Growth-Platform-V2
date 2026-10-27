"""Actual Supabase Edge Runtime -> GoTrue -> signed PG17 I79/I80 under I81.

Python is test orchestration/fixtures only. All asserted administrative HTTP
operations run TypeScript inside supabase functions serve, never a Python API.
"""
from concurrent.futures import ThreadPoolExecutor
import http.client as http_client
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from urllib import request as http, error as httperror
from urllib.parse import urlsplit,urlunsplit
from uuid import uuid4

import psycopg
from psycopg import sql
from integration.i80.test_regularization import I80Tests
from integration.i82.gateway_local import configure as configure_gateway
from scripts.test_s0_cfi01_auth_rest_local import register,request


class EdgeTests(I80Tests):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_I82_DISPOSABLE_TEST')!='YES':raise RuntimeError('I82 opt-in required')
        super().setUpClass()
        cls.addClassCleanup(configure_gateway())
        cls.http_base=cls.api+'/functions/v1/prumo-admin-i82/v1/'
        cls.temporary=tempfile.TemporaryDirectory(prefix='prumo-i82-')
        cls.addClassCleanup(cls.temporary.cleanup)
        u=urlsplit(cls.dsn)
        internal=urlunsplit((u.scheme,u.netloc.replace(u.hostname+':'+str(u.port),'supabase_db_prumo-s0-auth-ci:5432'),u.path,'',''))
        networks=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .NetworkSettings.Networks}}','supabase_db_prumo-s0-auth-ci']))
        addresses=[v['IPAddress'] for k,v in networks.items() if k=='supabase_network_prumo-s0-auth-ci' and v.get('IPAddress')]
        if len(addresses)!=1:raise RuntimeError('I82 own disposable DB network address required')
        env=dict(PRUMO_I82_DISPOSABLE='YES',PRUMO_I82_AUTH_URL='http://supabase_kong_prumo-s0-auth-ci:8000',
            PRUMO_I82_DATABASE_URL=internal,PRUMO_I82_DATABASE_IPV4=addresses[0],PRUMO_I82_ANON_KEY=cls.anon,PRUMO_I82_KEY_ID=str(cls.key_id),
            PRUMO_I82_HMAC_HEX=cls.secret.hex(),PRUMO_I82_ALLOW_ORIGIN='http://localhost:3000')
        file=Path(cls.temporary.name)/'edge.env'
        file.write_text('\n'.join(k+'='+v for k,v in env.items())+'\n');file.chmod(0o600)
        cls.runtime_log=Path(os.environ.get('RUNNER_TEMP',cls.temporary.name))/'prumo_i82_runtime.log'
        log=cls.runtime_log.open('w');cls.addClassCleanup(log.close)
        # CLI help is executed by workflow before reaching this command.
        cls.process=subprocess.Popen(['supabase','functions','serve','prumo-admin-i82','--env-file',str(file),'--no-verify-jwt'],stdout=log,stderr=subprocess.STDOUT)
        def cleanup():
            cls.process.terminate()
            try:cls.process.wait(timeout=10)
            except subprocess.TimeoutExpired:cls.process.kill();cls.process.wait(timeout=5)
        cls.addClassCleanup(cleanup)
        until=time.monotonic()+60
        while time.monotonic()<until:
            try:
                code,body,_=cls.raw('i79',method='GET')
                if code==405 and body.get('version')=='prumo.admin.v1':break
                if code==503 and body.get('version')=='prumo.admin.v1':raise RuntimeError('I82 runtime config rejected')
            except (httperror.URLError,ConnectionError,TimeoutError,ValueError):pass
            if cls.process.poll() is not None:raise RuntimeError('I82 serve exited; inspect sanitized local runtime log')
            time.sleep(.25)
        else:raise RuntimeError('I82 actual Edge runtime did not become ready within 60 seconds')
        code,body,_=cls.raw('i80',cls.wire('INVENTORY',limit=1),cls.director_token)
        if code!=200 or body.get('state')!='INVENTORY':raise RuntimeError('I82 authenticated SQL startup probe failed; inspect bounded I82_CORE_FAILURE diagnostics')

    @classmethod
    def raw(cls,family,p=None,token=None,method='POST',body=None,headers=None,base=None):
        data=body if body is not None else (json.dumps({'version':'prumo.admin.v1','command':p}).encode() if p is not None else None)
        h={'apikey':cls.anon,'Content-Type':'application/json'}
        if token:h['Authorization']='Bearer '+token
        h.update(headers or {})
        req=http.Request((base or cls.http_base)+family,data=data,headers=h,method=method)
        try:
            with http.urlopen(req,timeout=25) as response:status=response.status;wire=response.read(262145);rh=dict(response.headers)
        except httperror.HTTPError as response:status=response.code;wire=response.read(262145);rh=dict(response.headers)
        assert len(wire)<=262144
        return status,json.loads(wire) if wire else {},{k.lower():v for k,v in rh.items()}

    def edge(self,family,p,token=None):
        status,body,_=self.raw(family,p,token or self.director_token)
        self.assertEqual(set(body),{'version','correlation_id','state','commit','scope','receipt'})
        self.assertEqual(body['version'],'prumo.admin.v1');self.assertEqual(body['scope'],'ADMINISTRATIVE_ONLY')
        self.assertEqual(body['receipt'] is None,body['commit']!='CONFIRMED')
        return status,body
    def professional(self,action,target,cargo='consultor',manager=None,previous=0,key=None):
        p=self.dto(action,target,cargo,manager,previous,key);p['expected_relationship_id']=str(previous);return p
    def http_inventory_item(self,actor):
        cursor=None
        for _ in range(100):
            status,b=self.edge('i80',self.wire('INVENTORY',cursor=cursor,limit=50));self.assertEqual((status,b['state']),(200,'INVENTORY'))
            for r in b['receipt']['items']:
                if r['target_id']==str(actor):return r
            if not b['receipt']['has_more']:break
            cursor=b['receipt']['next_cursor']
        self.fail('legacy target absent')
    def http_preview(self,actor,manager=None):
        item=self.http_inventory_item(actor)
        status,b=self.edge('i80',self.wire('PREVIEW',actor,'consultor',manager,item['inventory_sha256']))
        self.assertEqual(status,200);return b['receipt']

    def test_edge_01_real_director_registers_and_activates_consultant(self):
        actor,_=register(self.api,self.anon)
        for action in ('REGISTER','ACTIVATE'):
            status,b=self.edge('i79',self.professional(action,actor,manager=self.people['m1'][0] if action=='ACTIVATE' else None))
            self.assertEqual((status,b['state'],b['commit']),(200,'APPLIED','CONFIRMED'))
        self.assertEqual(self.relation(actor)[1],self.people['m1'][0])
        with psycopg.connect(self.db) as c:
            self.assertEqual(c.execute('select cargo,estado from public.equipe_prumo_s1 where ator_id=%s',(actor,)).fetchone(),('consultor','ativo'))
            self.assertEqual(c.execute('select count(*) from public.vinculos_papel_escopo where ator_id=%s',(actor,)).fetchone()[0],0)

    def test_edge_02_manager_has_no_director_competence_even_with_shop_grant(self):
        actor,_=register(self.api,self.anon);before=self.counters()
        status,b=self.edge('i79',self.professional('REGISTER',actor),self.tokens['m1'])
        self.assertEqual((status,b['state'],b['commit']),(403,'DENIED','REJECTED'));self.assertEqual(self.counters(),before)

    def test_edge_03_expired_real_session_rechecked_by_sql(self):
        token=self.fresh_director_token();principal=self.gateway._identity.verify('Bearer '+token)
        with psycopg.connect(self.db) as c:c.execute("update auth.sessions set not_after=clock_timestamp()-interval '1 second' where id=%s",(principal.session_id,))
        status,b=self.edge('i80',self.wire('INVENTORY',limit=1),token)
        self.assertIn(status,(401,403));self.assertEqual(b['state'],'DENIED')

    def test_edge_04_actual_logout_and_invalid_signature_denied(self):
        token=self.fresh_director_token()
        self.assertIn(request(self.api,self.anon,'POST','/auth/v1/logout?scope=local',token=token)[0],(200,204))
        for bearer in (token,token[:-8]+'xxxxxxxx'):
            status,b=self.edge('i80',self.wire('INVENTORY',limit=1),bearer)
            self.assertIn(status,(401,403));self.assertEqual(b['state'],'DENIED')
        status,b,_=self.raw('i80',self.wire('INVENTORY',limit=1));self.assertEqual((status,b['state']),(401,'DENIED'))

    def test_edge_05_payload_identity_duplicates_utf8_and_limits_rejected(self):
        p=self.professional('REGISTER',uuid4());before=self.counters()
        for payload in ({**p,'actor_id':str(self.director)},{**p,'cargo':'diretor'},{**p,'expected_relationship_id':0}):
            status,b=self.edge('i79',payload);self.assertEqual((status,b['state'],b['commit']),(400,'INPUT_REJECTED','NOT_ATTEMPTED'))
        for body in (b'{"version":"a","version":"prumo.admin.v1","command":{}}',b'\xff'):
            self.assertEqual(self.raw('i79',token=self.director_token,body=body)[0],400)
        self.assertEqual(self.raw('i79',token=self.director_token,body=b'x'*8193)[0],413)
        self.assertEqual(self.raw('i79',p,self.director_token,headers={'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.counters(),before)

    def test_edge_06_chefia_transfer_cas_and_durable_idempotency(self):
        actor,_=self.new_person(activate=True);old=self.relation(actor)[0]
        p=self.professional('TRANSFER',actor,manager=self.people['m2'][0],previous=old)
        _,a=self.edge('i79',p);self.assertEqual(a['state'],'APPLIED')
        _,b=self.edge('i79',p);self.assertEqual(b['state'],'ALREADY_APPLIED');self.assertEqual(a['receipt']['request_id'],b['receipt']['request_id'])
        status,b=self.edge('i79',{**p,'idempotency_key':'i82-stale-'+uuid4().hex});self.assertEqual((status,b['state']),(409,'STALE'))

    def test_edge_07_inventory_preview_does_not_apply_then_explicit_apply_preserves_cases(self):
        actor,_,_=self.legacy(orphan=True);before=self.preserved(actor)
        preview=self.http_preview(actor,self.people['m1'][0]);self.assertEqual(preview['outcome'],'READY')
        self.assertIsNone(self.cargo(actor));self.assertIsNone(self.relation(actor))
        status,b=self.edge('i80',self.apply_wire(preview));self.assertEqual((status,b['state']),(200,'APPLIED'))
        self.assertEqual(self.preserved(actor),before)

    def test_edge_08_stale_preview_refused_after_context_change(self):
        actor,_,_=self.legacy();p=self.http_preview(actor,self.people['m1'][0])
        with psycopg.connect(self.db) as c:c.execute("update public.vinculos_papel_escopo set valido_ate=clock_timestamp()+interval '2 days' where ator_id=%s",(actor,))
        status,b=self.edge('i80',self.apply_wire(p));self.assertEqual((status,b['state'],b['commit']),(409,'STALE','REJECTED'))
        self.assertIsNone(self.cargo(actor))

    def test_edge_09_concurrent_identical_apply_has_one_commit_and_one_replay(self):
        actor,_,_=self.legacy(orphan=True);p=self.http_preview(actor,self.people['m1'][0]);wire=self.apply_wire(p)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:self.edge('i80',wire),range(2)))
        self.assertEqual({b['state'] for _,b in results},{'APPLIED','ALREADY_APPLIED'})
        self.assertEqual(results[0][1]['receipt']['request_id'],results[1][1]['receipt']['request_id'])

    def test_edge_10_preview_session_and_director_binding_cannot_be_reassigned(self):
        actor,_,_=self.legacy(pending=True);p=self.http_preview(actor)
        other,_=register(self.api,self.anon)
        with psycopg.connect(self.db) as c:
            c.execute('insert into public.atores(id) values(%s)',(other,))
            c.execute('insert into prumo_private.s1_responsaveis_plataforma(ator_id) values(%s)',(other,))
            c.execute("insert into public.equipe_prumo_s1(ator_id,cargo,estado) values(%s,'diretor','ativo')",(other,))
        _,other_token=request(self.api,self.anon,'POST','/auth/v1/token?grant_type=password',{'email':self._email(other),'password':'Only-Local-CFI01-Test!X8b2'})
        for token in (self.fresh_director_token(),other_token['access_token']):
            status,b=self.edge('i80',self.apply_wire(p),token);self.assertEqual((status,b['state']),(403,'DENIED'))

    def _email(self,actor):
        with psycopg.connect(self.db) as c:return c.execute('select email from auth.users where id=%s',(actor,)).fetchone()[0]

    def test_edge_11_director_revocation_while_waiting_rechecked_under_locks(self):
        actor,_=self.new_person(activate=True);p=self.professional('TRANSFER',actor,manager=self.people['m2'][0],previous=self.relation(actor)[0])
        try:
            with psycopg.connect(self.db) as c,ThreadPoolExecutor(max_workers=1) as pool:
                c.execute('select ator_id from public.equipe_prumo_s1 where ator_id=%s for update',(self.director,));pid=c.execute('select pg_backend_pid()').fetchone()[0]
                future=pool.submit(self.edge,'i79',p);self.wait_blocker(pid)
                c.execute('update prumo_private.s1_responsaveis_plataforma set ativo=false where ator_id=%s',(self.director,));c.commit()
                status,b=future.result(timeout=15);self.assertEqual((status,b['state']),(403,'DENIED'))
        finally:self.set_director(True)

    def http_fault(self,deferred):
        actor,_,case=self.legacy(exception=True);p=self.http_preview(actor,self.people['m2'][0]);wire=self.apply_wire(p);before=self.counters();old=self.relation(actor)
        name='i82_fault_'+uuid4().hex
        with psycopg.connect(self.db) as c:
            c.execute(sql.SQL("create function prumo_private.{}() returns trigger language plpgsql security invoker set search_path='' as $$begin raise exception 'I82_FAULT' using errcode='23514';end$$").format(sql.Identifier(name)))
            c.execute(sql.SQL('create '+('constraint ' if deferred else '')+'trigger {} after insert on prumo_private.s1_i80_audit '+('deferrable initially deferred ' if deferred else '')+'for each row execute function prumo_private.{}()').format(sql.Identifier(name),sql.Identifier(name)))
        try:
            status,b=self.edge('i80',wire);self.assertEqual((status,b['state'],b['commit']),(403,'DENIED','REJECTED'))
            self.assertIsNone(self.cargo(actor));self.assertEqual(self.relation(actor),old);self.assertEqual(self.counters(),before)
            with psycopg.connect(self.db) as c:self.assertIsNone(c.execute('select revogada_em from prumo_private.s1_excecoes_caso_i61 where id=%s',(case['exception_id'],)).fetchone()[0])
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on prumo_private.s1_i80_audit').format(sql.Identifier(name)))
                c.execute(sql.SQL('drop function prumo_private.{}()').format(sql.Identifier(name)))
        self.assertEqual(self.edge('i80',wire)[1]['state'],'APPLIED')
    def test_edge_12_partial_failure_rolls_back_i61_role_relation_nonce(self):self.http_fault(False)
    def test_edge_13_deferred_commit_failure_never_returns_success(self):self.http_fault(True)

    def test_edge_14_response_lost_after_actual_commit_reconciles_same_key(self):
        actor,_=register(self.api,self.anon);p=self.professional('REGISTER',actor)
        owner=self;observed={}
        class Loss(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                wire=self.rfile.read(int(self.headers['Content-Length']))
                code,body,_=owner.raw('i79',token=owner.director_token,body=wire)
                observed.update(code=code,state=body.get('state'),receipt=body.get('receipt'))
                self.close_connection=True;self.connection.shutdown(2);self.connection.close()
        server=ThreadingHTTPServer(('127.0.0.1',0),Loss);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with self.assertRaises((http_client.RemoteDisconnected,httperror.URLError,ConnectionError)):
                self.raw('i79',p,self.director_token,base='http://127.0.0.1:'+str(server.server_port)+'/')
        finally:server.shutdown();server.server_close();thread.join(timeout=5)
        self.assertEqual((observed['code'],observed['state']),(200,'APPLIED'))
        _,retry=self.edge('i79',p);self.assertEqual(retry['state'],'ALREADY_APPLIED')
        self.assertEqual(retry['receipt']['request_id'],observed['receipt']['request_id'])

    def test_edge_15_unreviewed_ddl_quarantines_both_ports_without_mutation(self):
        with psycopg.connect(self.db) as c:c.execute('alter table public.casos_humanos add column i82_unreviewed_content text')
        actor,_=register(self.api,self.anon)
        try:
            for family,p in [('i79',self.professional('REGISTER',actor)),('i80',self.wire('INVENTORY',limit=1))]:
                status,b=self.edge(family,p);self.assertEqual((status,b['state'],b['commit']),(403,'DENIED','REJECTED'))
        finally:
            with psycopg.connect(self.db) as c:c.execute('alter table public.casos_humanos drop column i82_unreviewed_content')
        self.assertEqual(self.edge('i79',self.professional('REGISTER',actor))[1]['state'],'APPLIED')

    def test_edge_16_metadata_lock_fences_ddl_until_real_http_transaction_commits(self):
        actor,_,_=self.legacy(pending=True);p=self.http_preview(actor);wire=self.apply_wire(p);name='i82_wait_'+uuid4().hex
        with psycopg.connect(self.db) as c:
            c.execute(sql.SQL('create function prumo_private.{}() returns trigger language plpgsql security invoker set search_path=\'\' as $$begin perform pg_advisory_xact_lock(8227,1);return new;end$$').format(sql.Identifier(name)))
            c.execute(sql.SQL('create trigger {} before insert on prumo_private.s1_i80_audit for each row execute function prumo_private.{}()').format(sql.Identifier(name),sql.Identifier(name)))
        try:
            with psycopg.connect(self.db) as holder,ThreadPoolExecutor(max_workers=1) as pool:
                holder.execute('select pg_advisory_xact_lock(8227,1)');pid=holder.execute('select pg_backend_pid()').fetchone()[0]
                future=pool.submit(self.edge,'i80',wire);self.wait_blocker(pid)
                with self.assertRaises(psycopg.errors.LockNotAvailable):
                    with psycopg.connect(self.db) as ddl:
                        ddl.execute("set local lock_timeout='500ms'");ddl.execute('alter table public.casos_humanos add column i82_forbidden_race text')
                holder.commit();self.assertEqual(future.result(timeout=15)[1]['state'],'APPLIED')
        finally:
            with psycopg.connect(self.db) as c:
                c.execute(sql.SQL('drop trigger {} on prumo_private.s1_i80_audit').format(sql.Identifier(name)))
                c.execute(sql.SQL('drop function prumo_private.{}()').format(sql.Identifier(name)))

    def test_edge_17_private_sql_roles_and_public_rest_do_not_bypass_edge(self):
        for query in ('set role prumo_s1_admin_domain_local','set role prumo_s1_professional_validator_local','select * from prumo_private.s1_i80_previews','select prumo_private.s1_i82_metadata_fence()'):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(self.dsn) as c:c.execute(query)
        for name in ('s1_i79_admin_signed','s1_i80_signed','s1_i82_metadata_fence'):
            self.assertIn(request(self.api,self.anon,'POST','/rest/v1/rpc/'+name,{},token=self.director_token)[0],(401,403,404))

    def test_edge_18_two_teams_and_stores_history_visibility_preserved(self):
        actor,token,case=self.legacy(orphan=True);before=self.preserved(actor);p=self.http_preview(actor,self.people['m1'][0])
        self.assertEqual(self.edge('i80',self.apply_wire(p))[1]['state'],'APPLIED');self.assertEqual(self.preserved(actor),before)
        for bearer,expected in ((token,1),(self.tokens['c3'],0)):
            code,rows=request(self.api,self.anon,'GET','/rest/v1/casos_humanos?select=id&id=eq.'+case['case_id'],token=bearer)
            self.assertEqual((code,len(rows)),(200,expected))
        self.assertEqual(self.edge('i80',self.wire('INVENTORY',limit=1),self.tokens['m2'])[1]['state'],'DENIED')

    def test_edge_19_blocked_preview_never_promotes_active_orphan_without_manager(self):
        actor,_,_=self.legacy(orphan=True);p=self.http_preview(actor)
        self.assertEqual(p['outcome'],'BLOCKED');self.assertIn('MANAGER_REQUIRED',p['blockers'])
        status,b=self.edge('i80',self.apply_wire(p));self.assertEqual((status,b['state']),(409,'BLOCKED'));self.assertIsNone(self.cargo(actor))

    def test_edge_20_transport_headers_local_cors_no_secrets_or_private_auth(self):
        code,b,h=self.raw('i80',self.wire('INVENTORY',limit=1),self.director_token,headers={'Origin':'http://localhost:3000','X-Request-ID':str(self.director)})
        self.assertEqual(code,200);self.assertEqual(h.get('access-control-allow-origin'),'http://localhost:3000')
        code,_,h=self.raw('i80',method='OPTIONS',headers={'Origin':'http://localhost:3000','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'})
        self.assertEqual(code,204);self.assertEqual(h.get('access-control-allow-origin'),'http://localhost:3000')
        self.assertEqual(self.raw('i80',method='OPTIONS',headers={'Origin':'http://localhost:3000','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'x-actor-id'})[0],403)
        text=json.dumps(b)
        for forbidden in (self.secret.hex(),self.dsn,self.director_token,'session_id','email','secret'):self.assertNotIn(forbidden,text)
        self.assertNotEqual(b['correlation_id'],str(self.director))
        self.assertEqual(self.raw('i80',self.wire('INVENTORY',limit=1),self.director_token,headers={'Origin':'https://outside.example'})[0],403)


if __name__=='__main__':
    suite=unittest.TestSuite(EdgeTests(name) for name in unittest.defaultTestLoader.getTestCaseNames(EdgeTests) if name.startswith('test_edge_'))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
