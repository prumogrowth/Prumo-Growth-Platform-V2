"""Local-only paths, subprocesses, durable journal and exclusive project lock."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parents[1]
PROJECT='prumo-s0-auth-ci'
DB='supabase_db_'+PROJECT
EDGE='supabase_edge_runtime_'+PROJECT
KONG='supabase_kong_'+PROJECT
NETWORK='supabase_network_'+PROJECT
DEFAULT=Path(tempfile.gettempdir())/('prumo-admin-i84-'+str(os.getuid()))
EXCLUDE='realtime,storage-api,imgproxy,mailpit,postgres-meta,studio,edge-runtime,logflare,vector,supavisor'

class Blocked(RuntimeError):
    def __init__(self,code):self.code=code;super().__init__(code)


def private(path,directory=False):
    try:s=Path(path).lstat()
    except FileNotFoundError:raise Blocked('STATE_MISSING') from None
    if stat.S_ISLNK(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=(0o700 if directory else 0o600):raise Blocked('CUSTODY_PERMISSIONS')
    if directory and not stat.S_ISDIR(s.st_mode):raise Blocked('CUSTODY_PERMISSIONS')
    if not directory and not stat.S_ISREG(s.st_mode):raise Blocked('CUSTODY_PERMISSIONS')


def location(path):
    p=Path(path).absolute()
    if p.parent!=Path(tempfile.gettempdir()).resolve() or not p.name.startswith('prumo-admin-i84-') or p.is_symlink():raise Blocked('STATE_PATH_FORBIDDEN')
    return p


def save(path,value):
    private(Path(path).parent,True)
    data=json.dumps(value,sort_keys=True).encode()+b'\n';next_path=Path(path).with_name(Path(path).name+'.next')
    fd=os.open(next_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(next_path,path)
        fd=os.open(Path(path).parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:next_path.unlink(missing_ok=True)


def load(path):
    private(path)
    try:return json.loads(Path(path).read_text())
    except Exception:raise Blocked('STATE_INVALID') from None


def child_env():
    e=os.environ.copy()
    for k in ('DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):e.pop(k,None)
    e['DOCKER_HOST']='unix:///var/run/docker.sock'
    e['SUPABASE_DISABLE_TELEMETRY']='1'
    return e


def run(argv,*,data=None,combined=False):
    try:p=subprocess.run(argv,cwd=ROOT,env=child_env(),input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=240)
    except Exception:raise Blocked('LOCAL_COMMAND_UNAVAILABLE') from None
    if p.returncode:raise Blocked('LOCAL_COMMAND_FAILED')
    return p.stdout+p.stderr if combined else p.stdout


def docker(*args):return run(['docker','--host=unix:///var/run/docker.sock',*args])


def inspect(name):
    # No full env/config inspection here. Only selected nonsecret metadata.
    data=docker('container','ls','-a','--no-trunc','--filter','name=^/'+name+'$','--format','{{.ID}}').strip()
    if not data:return None
    return json.loads(docker('inspect','--format','{{json .Id}}',data.decode()))


@contextmanager
def locked():
    if os.environ.get('PRUMO_I84_DISPOSABLE')!='YES':raise Blocked('DISPOSABLE_OPT_IN_REQUIRED')
    path=Path(tempfile.gettempdir())/('prumo-admin-i84-project-'+str(os.getuid())+'.lock')
    fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        private(path)
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise Blocked('LOCAL_OPERATION_BUSY') from None
        yield
    finally:os.close(fd)


def digest(data):return hashlib.sha256(data).hexdigest()
