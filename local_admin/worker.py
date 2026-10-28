"""Detached local Supabase CLI worker with PID-reuse and container ownership checks."""
import json
import os
from pathlib import Path
import signal
import time
from urllib import request,error
from local_admin.boundary import EDGE,Blocked,docker,inspect,child_env,private,digest
from local_admin.custody import read_env,scan


def cors(state,enabled,checkpoint):
    from integration.i82 import gateway_local as gateway
    before=gateway._read(env=child_env())
    start=before.index(b'\n  - name: functions-v1\n');end=before.index(b'\n  - name: ',start+10)
    block=before[start:end];corsline=b'      - name: cors\n';transform=b'      - name: request-transformer\n'
    if enabled:
        if state.get('cors'):
            if digest(before)!=state['cors']['patched']:raise Blocked('GATEWAY_DRIFT')
            return
        if block.count(corsline)!=1:raise Blocked('GATEWAY_TEMPLATE_CHANGED')
        after=before[:start]+block.replace(corsline,b'',1)+before[end:]
        state['cors']={'original':digest(before),'patched':digest(after)};checkpoint()
    else:
        if not state.get('cors'):return
        if digest(before)==state['cors']['original']:
            state['cors']=None;checkpoint();return
        if digest(before)!=state['cors']['patched'] or corsline in block or block.count(transform)!=1:raise Blocked('GATEWAY_DRIFT')
        after=before[:start]+block.replace(transform,corsline+transform,1)+before[end:]
        if digest(after)!=state['cors']['original']:raise Blocked('GATEWAY_RESTORE_UNPROVEN')
    gateway._load(after,env=child_env())
    if gateway._read(env=child_env())!=after:raise Blocked('GATEWAY_READBACK_MISMATCH')
    if not enabled:state['cors']=None
    checkpoint()


def proc_identity(pid):
    try:
        p=Path('/proc')/str(pid)
        if p.stat().st_uid!=os.getuid():return None
        parts=(p/'stat').read_text().rsplit(')',1)[1].split()
        return None if parts[0]=='Z' else parts[19]
    except (FileNotFoundError,ProcessLookupError):return None


def container_matches(state,directory):
    cid=inspect(EDGE)
    if not cid:return 'ABSENT'
    if cid!=(state.get('worker') or {}).get('container'):return 'FOREIGN'
    try:
        if docker('inspect','--format','{{.State.Running}}',cid).strip()!=b'true':return 'STOPPED'
        expected=read_env(directory)
        actual=json.loads(docker('inspect','--format','{{json .Config.Env}}',cid))
        actual=dict(line.split('=',1) for line in actual if '=' in line)
        return 'CURRENT' if all(actual.get(k)==v for k,v in expected.items()) else 'STALE'
    except Blocked:return 'STALE'


def stop(state,directory,checkpoint):
    record=state.get('worker') or {};cid=inspect(EDGE)
    if cid and cid!=record.get('container'):raise Blocked('UNOWNED_WORKER')
    failure=None
    try:scan(directory,(cid,) if cid else ())
    except Blocked as error:failure=error
    pid=record.get('pid');start=record.get('start')
    if pid and proc_identity(pid):
        if proc_identity(pid)!=start:raise Blocked('WORKER_PID_CHANGED')
        os.killpg(pid,signal.SIGTERM);until=time.monotonic()+5
        while proc_identity(pid) and time.monotonic()<until:time.sleep(.05)
        if proc_identity(pid)==start:os.killpg(pid,signal.SIGKILL)
    if cid:docker('rm','-f',cid)
    if inspect(EDGE):raise Blocked('WORKER_NOT_REMOVED')
    state['worker']=None;checkpoint();cors(state,False,checkpoint)
    if failure:raise failure


def start(state,directory,checkpoint):
    if inspect(EDGE):raise Blocked('WORKER_ALREADY_PRESENT')
    env=read_env(directory);cors(state,True,checkpoint)
    file=Path(directory)/'worker.log'
    fd=os.open(file,os.O_CREAT|os.O_APPEND|os.O_WRONLY|os.O_NOFOLLOW,0o600);private(file)
    null=os.open(os.devnull,os.O_RDONLY)
    try:
        pid=os.posix_spawnp('supabase',['supabase','functions','serve','prumo-admin-i82','--env-file',str(Path(directory)/'edge.env'),'--no-verify-jwt'],
          child_env(),setsid=True,file_actions=[(os.POSIX_SPAWN_DUP2,fd,1),(os.POSIX_SPAWN_DUP2,fd,2),(os.POSIX_SPAWN_DUP2,null,0),(os.POSIX_SPAWN_CLOSE,fd),(os.POSIX_SPAWN_CLOSE,null)])
    finally:os.close(fd);os.close(null)
    state['worker']={'pid':pid,'start':proc_identity(pid),'container':None,'generation':state['generation']};checkpoint()
    until=time.monotonic()+60
    while time.monotonic()<until:
        cid=inspect(EDGE)
        if cid and not state['worker']['container']:
            state['worker']['container']=cid;checkpoint()
        try:
            r=request.Request('http://127.0.0.1:54321/functions/v1/prumo-admin-i82/v1/i79',method='GET')
            try:response=request.urlopen(r,timeout=2)
            except error.HTTPError as e:response=e
            with response:
                body=json.loads(response.read(8192));ready=response.status==405 and body.get('version')=='prumo.admin.v1'
            if ready and container_matches(state,directory)=='CURRENT':return
        except (error.URLError,TimeoutError,ValueError,ConnectionError):pass
        if not proc_identity(pid):raise Blocked('WORKER_START_FAILED')
        time.sleep(.2)
    raise Blocked('WORKER_READY_TIMEOUT')


def available():
    try:
        r=request.Request('http://127.0.0.1:54321/functions/v1/prumo-admin-i82/v1/i79',method='GET')
        try:response=request.urlopen(r,timeout=2)
        except error.HTTPError as x:response=x
        with response:return response.status==405 and json.loads(response.read(8192)).get('version')=='prumo.admin.v1'
    except (error.URLError,TimeoutError,ValueError,ConnectionError):return False
