"""I85-only profile: same official Runtime/template, no installer credentials.

Docker API is accessed exclusively through the existing local Unix socket.
No Docker API listener, Auth implementation or public bootstrap endpoint.
"""
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import socket
import time
from uuid import uuid4
from local_admin import boundary as b
from local_admin.custody import read_env

FORBIDDEN=frozenset(('SUPABASE_SERVICE_ROLE_KEY','SUPABASE_DB_URL','SUPABASE_INTERNAL_JWT_SECRET','JWT_SECRET','SERVICE_ROLE_KEY'))
IMAGE='supabase/edge-runtime:v1.73.0'

class UnixConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.settimeout(30);self.sock.connect('/var/run/docker.sock')


def engine_api(method,path,body=None,expected=(200,)):
    c=UnixConnection('localhost',timeout=30)
    try:
        encoded=None if body is None else json.dumps(body).encode()
        c.request(method,path,body=encoded,headers={'Content-Type':'application/json'})
        response=c.getresponse();raw=response.read(1048577)
        if response.status not in expected or len(raw)>1048576:raise b.Blocked('I85_DOCKER_API_REFUSED')
        return json.loads(raw) if raw else None
    except b.Blocked:raise
    except Exception:raise b.Blocked('I85_DOCKER_TRANSPORT_UNKNOWN') from None
    finally:c.close()


def verify(state):
    record=state.get('worker') or {};cid=b.inspect(b.EDGE)
    if not cid:return False
    labels=json.loads(b.docker('inspect','--format','{{json .Config.Labels}}',cid))
    if labels.get('prumo.i85.stack')!=state['token'] or labels.get('prumo.i85.attempt')!=record.get('attempt'):raise b.Blocked('I85_EDGE_IDENTITY_UNPROVEN')
    env=json.loads(b.docker('inspect','--format','{{json .Config.Env}}',cid))
    names={line.split('=',1)[0] for line in env}
    if names & FORBIDDEN:raise b.Blocked('I85_EDGE_PRIVILEGED_ENV_PRESENT')
    if json.loads(b.docker('inspect','--format','{{json .HostConfig.Privileged}}',cid)):raise b.Blocked('I85_EDGE_HOST_PRIVILEGED')
    return cid


def reconcile_record(state,checkpoint):
    cid=verify(state)
    if cid and (state.get('worker') or {}).get('container') not in (None,cid):raise b.Blocked('I85_EDGE_IDENTITY_UNPROVEN')
    if cid:state['worker']['container']=cid;checkpoint()
    return cid


def required(state):
    """An I85-born lab cannot fall back to the CLI profile after unset opt-in."""
    from integration.i85.bootstrap import ROOT
    from integration.i85 import storage
    active=(ROOT,ROOT.with_name(ROOT.name+'.disposing'))
    for directory in active:
        if not directory.exists():continue
        storage.checked(directory,True)
        if (directory/'lab.json').exists():binding=storage.read(directory/'lab.json')
        elif (directory/'disposal.json').exists():binding=storage.read(directory/'disposal.json')['binding']
        else:raise b.Blocked('I85_INIT_RECOVERY_REQUIRED')
        if any(binding[k]!=state[v] for k,v in (('stack_token','token'),('db_id','db_id'),('engine','engine'),('network_id','network_id'))):raise b.Blocked('I85_STACK_MISMATCH')
        return True
    directory=ROOT.with_name(ROOT.name+'.disposed')
    if directory.exists():
        binding=storage.read(directory/'proof.json')['binding']
        if all(binding[k]==state[v] for k,v in (('stack_token','token'),('db_id','db_id'),('engine','engine'),('network_id','network_id'))):return True
    return False


def start(state,directory,checkpoint):
    from local_admin import worker
    if b.inspect(b.EDGE):raise b.Blocked('WORKER_ALREADY_PRESENT')
    values=read_env(directory)
    spec=json.loads((b.ROOT/'integration/i85/runtime_main/source.json').read_text())
    template=b.ROOT/'integration/i85/runtime_main/index.ts'
    if hashlib.sha256(template.read_bytes()).hexdigest()!=spec['sha256'] or spec['image']!=IMAGE:raise b.Blocked('I85_RUNTIME_SOURCE_DRIFT')
    b.docker('pull',IMAGE)
    worker.cors(state,True,checkpoint)
    state['worker']={'pid':None,'start':None,'container':None,'generation':state['generation'],
                     'profile':'I85_RESTRICTED','attempt':str(uuid4())};checkpoint()
    config={
      'prumo-admin-i82':{'entrypointPath':'supabase/functions/prumo-admin-i82/index.ts',
                         'importMapPath':'supabase/functions/prumo-admin-i82/deno.json',
                         'staticFiles':[],'verifyJWT':False}}
    values.update({'DENO_DIR':'/tmp/prumo-edge-cache','HOME':'/tmp','SUPABASE_URL':'http://'+b.KONG+':8000','SUPABASE_ANON_KEY':values['PRUMO_I82_ANON_KEY'],
      'SUPABASE_INTERNAL_HOST_PORT':'54321','SUPABASE_INTERNAL_FUNCTIONS_CONFIG':json.dumps(config,separators=(',',':'))})
    if set(values)&FORBIDDEN:raise b.Blocked('I85_EDGE_PRIVILEGED_ENV_PRESENT')
    root=b.ROOT/'integration/i85/runtime_main';function=b.ROOT/'supabase/functions/prumo-admin-i82'
    body={'Image':IMAGE,'Env':[k+'='+v for k,v in values.items()],
      'Entrypoint':['edge-runtime'],'Cmd':['start','--main-service='+str(root),'--port=8081','--policy=per_worker'],
      'WorkingDir':str(b.ROOT),'User':str(os.getuid())+':'+str(os.getgid()),'ExposedPorts':{'8081/tcp':{}},
      'Labels':{'com.supabase.cli.project':b.PROJECT,'com.docker.compose.project':b.PROJECT,
                'prumo.i85.stack':state['token'],'prumo.i85.attempt':state['worker']['attempt']},
      'HostConfig':{'Binds':[str(root)+':'+str(root)+':ro',str(function)+':'+str(function)+':ro'],
                    'NetworkMode':b.NETWORK,'Privileged':False,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges:true']},
      'NetworkingConfig':{'EndpointsConfig':{b.NETWORK:{'Aliases':['edge_runtime',b.EDGE]}}}}
    version=engine_api('GET','/version')['ApiVersion']
    if not re.fullmatch(r'1\.[0-9]{2,3}',version):raise b.Blocked('I85_DOCKER_VERSION_INVALID')
    endpoint='/v'+version
    try:
        record=engine_api('POST',endpoint+'/containers/create?name='+b.EDGE,body,(201,))
        state['worker']['container']=record['Id'];checkpoint()
        engine_api('POST',endpoint+'/containers/'+record['Id']+'/start',expected=(204,))
        until=time.monotonic()+90
        while time.monotonic()<until:
            if verify(state) and worker.available():return
            time.sleep(.25)
        raise b.Blocked('I85_EDGE_READY_TIMEOUT')
    except Exception:
        # A lost creation response can only adopt our pre-journaled attempt.
        reconcile_record(state,checkpoint)
        raise
