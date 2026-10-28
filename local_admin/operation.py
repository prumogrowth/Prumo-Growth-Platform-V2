"""Explicit local lifecycle; no human identities or business operations here."""
import json
import os
from pathlib import Path
import uuid
from local_admin import boundary as b, environment as e, custody, worker


def resources():
    return {
      'containers':b.docker('ps','-a','--no-trunc','--filter','name=_'+b.PROJECT+'$','--format','{{.ID}}').decode().split(),
      'volumes':b.docker('volume','ls','--format','{{.Name}}','--filter','name='+b.PROJECT).decode().split(),
      'networks':b.docker('network','ls','--format','{{.Name}}','--filter','name=^'+b.NETWORK+'$').decode().split()}


class Operator:
    def __init__(self,directory=b.DEFAULT):
        self.directory=b.location(directory);self.file=self.directory/'state.json';self.state=None

    def checkpoint(self):b.save(self.file,self.state)

    def read(self):
        b.private(self.directory,True);self.state=b.load(self.file)
        if self.state.get('version')!=1 or self.state.get('project')!=b.PROJECT or self.state.get('root')!=str(b.ROOT) or self.state.get('engine')!=e.engine():raise b.Blocked('STATE_IDENTITY_INVALID')

    def catalog(self):
        from integration.i83.catalog import snapshot
        with e.database() as c:return snapshot(c)

    def verify(self):
        e.owned(self.state)
        if self.state['phase'] not in ('INITIALIZED','PREPARING','PREPARE_FAILED'):
            expected=b.load(self.directory/'catalog.json');actual=self.catalog()
            # LOGIN is the sole intended catalog difference during a lease.
            for value in (expected,actual):
                for r in value['roles']:
                    if r['rolname']=='prumo_s1_admin_edge_local':r['rolcanlogin']=False
            if actual!=expected:raise b.Blocked('CATALOG_DRIFT')

    def init(self):
        e.checkout()
        if self.directory.exists():raise b.Blocked('STATE_ALREADY_EXISTS')
        if any(resources().values()):raise b.Blocked('EXISTING_STACK_NOT_ADOPTED')
        if b.run(['supabase','--version']).decode().strip()!='2.84.2':raise b.Blocked('CLI_VERSION_UNCERTIFIED')
        for args in (['start'],['stop'],['status'],['functions','serve']):b.run(['supabase',*args,'--help'])
        self.directory.mkdir(mode=0o700)
        self.state={'version':1,'project':b.PROJECT,'root':str(b.ROOT),'engine':e.engine(),'token':str(uuid.uuid4()),'phase':'INITIALIZING','generation':0,'worker':None,'cors':None,'pending':'INIT','db_id':None,'resources':{}}
        self.checkpoint()
        try:
            b.run(['supabase','start','--exclude',b.EXCLUDE])
            self.state['resources']=resources();self.state['db_id']=b.inspect(b.DB);self.checkpoint()
            if not self.state['db_id']:raise b.Blocked('DATABASE_NOT_INITIALIZED')
            with e.database() as c:
                from psycopg import sql
                if c.execute('select count(*) from auth.users').fetchone()[0]:raise b.Blocked('FRESH_AUTH_REQUIRED')
                c.execute(sql.SQL('comment on database postgres is {}').format(sql.Literal('PRUMO_I84_DISPOSABLE:'+self.state['token'])))
            e.owned(self.state)
            self.state.update(phase='INITIALIZED',pending=None);self.checkpoint()
        except Exception:
            self.state['resources']=resources();self.state['db_id']=b.inspect(b.DB)
            self.state['phase']='INIT_FAILED';self.checkpoint();raise
        return self.safe_status()

    def prepare(self,source):
        if self.state['phase']!='INITIALIZED':raise b.Blocked('PREPARE_REQUIRES_FRESH_INITIALIZED_STACK')
        self.verify();self.state.update(phase='PREPARING',pending='PREPARE');self.checkpoint()
        def step(name):self.state['dependency_step']=name;self.checkpoint()
        try:
            from local_admin.bootstrap import install
            catalog=install(source,step);b.save(self.directory/'catalog.json',catalog)
            self.state.update(phase='PREPARED',pending=None);self.checkpoint()
        except Exception:self.state['phase']='PREPARE_FAILED';self.checkpoint();raise
        return self.safe_status()

    def material(self):
        from integration.i83 import provision_local as p
        old=self.state['phase']
        if old not in ('PREPARED','PROVISIONED','SERVING','REVOKED'):raise b.Blocked('CREDENTIAL_OPERATION_REQUIRES_RECOVERY')
        self.verify()
        if self.state.get('worker'):
            worker.stop(self.state,self.directory,self.checkpoint)
        self.state.update(phase='UNCERTAIN',pending='CREDENTIAL_CHANGE');self.checkpoint()
        value=p.rotate(e.discover()['DB_URL'])
        # A failure here after real COMMIT deliberately leaves UNCERTAIN.
        p.write_env(self.directory/'edge.env',e.runtime_env(value))
        with (self.directory/'edge.env').open('rb') as f:os.fsync(f.fileno())
        custody.scan(self.directory,extra=value.sensitive(e.discover()['DB_URL']))
        self.state['generation']+=1
        self.state.update(phase='PROVISIONED',pending=None);self.checkpoint()
        if old=='SERVING':self.serve()
        return self.safe_status()

    def serve(self):
        if self.state['phase']!='PROVISIONED':raise b.Blocked('SERVE_REQUIRES_PROVISIONED')
        self.verify()
        if custody.credential_state(self.directory)!='VALID':raise b.Blocked('CREDENTIAL_NOT_VALID')
        self.state.update(phase='WORKER_STARTING',pending='SERVE');self.checkpoint()
        worker.start(self.state,self.directory,self.checkpoint)
        self.state.update(phase='SERVING',pending=None);self.checkpoint()
        return self.safe_status()

    def retire(self):
        from integration.i83.provision_local import retire
        retire(e.discover()['DB_URL'])
        with e.database() as c:
            if c.execute("select count(*) from pg_stat_activity where usename='prumo_s1_admin_edge_local'").fetchone()[0]:raise b.Blocked('DEDICATED_SESSIONS_REMAIN')

    def revoke(self):
        if self.state['phase'] not in ('PROVISIONED','SERVING','REVOKED'):raise b.Blocked('REVOKE_REQUIRES_PREPARED_CREDENTIAL')
        self.verify();self.state.update(phase='UNCERTAIN',pending='REVOKE');self.checkpoint();self.retire()
        self.state.update(phase='REVOKED',pending=None);self.checkpoint()
        return self.safe_status()

    def worker_stop(self):
        self.verify();worker.stop(self.state,self.directory,self.checkpoint)
        if self.state['phase']=='REVOKED':(self.directory/'edge.env').unlink(missing_ok=True)
        elif self.state['phase']=='SERVING':self.state['phase']='PROVISIONED'
        self.checkpoint();return self.safe_status()

    def recover(self):
        if self.state['phase'] in ('INITIALIZED','PREPARING','PREPARE_FAILED','INIT_FAILED','INITIALIZING'):raise b.Blocked('PARTIAL_INSTALL_REQUIRES_DISCARD')
        self.verify();self.state.update(phase='UNCERTAIN',pending='RECOVER_RETIRE_ONLY');self.checkpoint()
        self.retire();worker.stop(self.state,self.directory,self.checkpoint)
        for n in ('edge.env','edge.env.next'):(self.directory/n).unlink(missing_ok=True)
        self.state.update(phase='REVOKED',pending=None);self.checkpoint();return self.safe_status()

    def down(self):
        current=resources()
        if self.state['phase']=='DISCARDED':
            if any(current.values()):raise b.Blocked('FOREIGN_STACK_PRESENT')
            return self.safe_status()
        partial=self.state['phase'] in ('INIT_FAILED','INITIALIZING')
        if partial:
            if current!=self.state['resources'] or not any(current.values()):raise b.Blocked('PARTIAL_RESOURCE_IDENTITY_UNPROVEN')
        else:e.owned(self.state)
        if not partial:
            if (self.directory/'catalog.json').exists():
                self.retire();worker.stop(self.state,self.directory,self.checkpoint)
                custody.scan(self.directory)
                self.state['retirement_verified']=True
        self.state.update(phase='STOPPING',pending='DOWN');self.checkpoint()
        b.run(['supabase','stop','--no-backup'])
        if any(resources().values()):raise b.Blocked('STACK_RESOURCES_REMAIN')
        for n in ('edge.env','edge.env.next','worker.log','catalog.json','state.json.next'):
            p=self.directory/n
            if p.is_symlink():raise b.Blocked('CUSTODY_SYMLINK')
            p.unlink(missing_ok=True)
        self.state.update(phase='DISCARDED',pending=None,worker=None,cors=None,resources={},material_removed=True);self.checkpoint()
        return self.safe_status()

    def safe_status(self):
        phase=self.state['phase']
        result={'version':'prumo.admin.local.v1','phase':phase,'generation':self.state['generation'],'pending':self.state.get('pending'),'hosted_enabled':False}
        if phase=='DISCARDED':return {**result,'material_removed':not (self.directory/'edge.env').exists(),'resources_absent':not any(resources().values()),'retirement_verified':self.state.get('retirement_verified',False)}
        if phase in ('INIT_FAILED','INITIALIZING','PREPARING','PREPARE_FAILED','INITIALIZED'):return result
        self.verify();result['credential']=custody.credential_state(self.directory)
        result['worker']=worker.container_matches(self.state,self.directory)
        result['ready']=phase=='SERVING' and result['credential']=='VALID' and result['worker']=='CURRENT'
        return result

    def execute(self,command,source=None):
        with b.locked():
            if command=='init':return self.init()
            self.read()
            if command=='prepare':return self.prepare(source)
            if command=='provision':
                if self.state['phase'] not in ('PREPARED','REVOKED'):raise b.Blocked('USE_EXPLICIT_ROTATE')
                return self.material()
            if command=='rotate':return self.material()
            if command=='status':return self.safe_status()
            if command=='restart':
                if self.state['phase']!='SERVING':raise b.Blocked('RESTART_REQUIRES_SERVING')
                self.worker_stop();return self.serve()
            return {'serve':self.serve,'revoke':self.revoke,'worker-stop':self.worker_stop,'recover':self.recover,'down':self.down}[command]()
