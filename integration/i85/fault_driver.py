"""Test-only subprocess controller. Faults wrap real I/O; no Auth/SQL stubs."""
import json
import os
from pathlib import Path
import signal
from unittest.mock import patch
from local_admin import boundary as b,environment as e
from integration.i85 import bootstrap as module,storage
from local_admin.__main__ import Parser


def halt(stage):
    os.write(int(os.environ['PRUMO_I85_PROBE_FD']),stage.encode()+b'\n')
    os.kill(os.getpid(),signal.SIGSTOP)


def main():
    parser=Parser();parser.add_argument('action');parser.add_argument('--stage',default='')
    parser.add_argument('--label',default='director');args=parser.parse_args()
    op=module.Bootstrap();stage=args.stage
    old_save=module.Bootstrap.save;old_api=module._api;old_verify=module.Bootstrap.verify_auth
    old_confirm=module.Bootstrap._confirm_grant;old_revoke=module.Bootstrap._confirm_revocation
    old_atomic=storage.atomic_save;old_replace=os.replace;old_rename=os.rename;old_mkdir=Path.mkdir;old_unlink=Path.unlink
    old_db=e.database
    def save(self,event,label=None):
        if (stage,event) in (('create-before-intent','AUTH_CREATE_ATTEMPT'),('grant-before-intent','DIRECTOR_COMMIT_ATTEMPT')):halt(stage)
        result=old_save(self,event,label)
        if (stage,event)==('create-after-intent','AUTH_CREATE_ATTEMPT'):halt(stage)
        return result
    def api(method,path,*a,**kw):
        result=old_api(method,path,*a,**kw)
        if stage=='create-post-ack' and method=='POST' and path=='/auth/v1/admin/users':halt(stage)
        return result
    def verify(self,*a,**kw):
        result=old_verify(self,*a,**kw)
        if stage=='identity-reconcile':halt(stage)
        return result
    def confirm(self,*a,**kw):
        if stage=='grant-post-commit':halt(stage)
        result=old_confirm(self,*a,**kw)
        if stage=='grant-confirmation':halt(stage)
        return result
    def revoke(self,*a,**kw):
        if stage=='revoke-post-commit':halt(stage)
        return old_revoke(self,*a,**kw)
    def atomic(path,value):
        result=old_atomic(path,value)
        if stage=='init-state' and Path(path).name=='state.json' and args.action=='init':halt(stage)
        if stage=='disposal-intent' and Path(path).name=='disposal.json':halt(stage)
        return result
    def replace(source,destination):
        if stage in ('grant-journal-replace','approval-journal-replace') and Path(destination)==op.state_file:
            candidate=json.loads(Path(source).read_bytes())
            if stage=='grant-journal-replace' and candidate['authority']['phase']=='ACTIVE':halt(stage)
            if stage=='approval-journal-replace' and candidate['approval'] is not None and candidate['authority']['phase']=='NONE':halt(stage)
        return old_replace(source,destination)
    def mkdir(path,*a,**kw):
        result=old_mkdir(path,*a,**kw)
        if stage=='init-dir' and path==module.ROOT:halt(stage)
        return result
    def rename(source,destination):
        result=old_rename(source,destination)
        if stage=='disposal-rename' and Path(destination)==op.disposing:halt(stage)
        return result
    def unlink(path,*a,**kw):
        result=old_unlink(path,*a,**kw)
        if stage=='disposal-material' and path.parent==op.disposing and path.name=='secrets.json':halt(stage)
        return result
    class Connection:
        def __init__(self,real):self.real=real
        def __enter__(self):self.real.__enter__();return self
        def __exit__(self,*a):return self.real.__exit__(*a)
        def execute(self,query,*a,**kw):
            result=self.real.execute(query,*a,**kw)
            sql=str(query).strip().lower()
            if stage=='grant-pre-commit' and sql.startswith('insert into public.equipe_prumo_s1'):halt(stage)
            if stage=='revoke-pre-commit' and sql.startswith('update prumo_private.s1_responsaveis_plataforma'):halt(stage)
            if stage=='session-retirement' and sql.startswith('delete from auth.sessions'):halt(stage)
            return result
    def database():
        conn=old_db();conn.execute("set application_name='i85-crash-probe'");return Connection(conn)
    try:
        with patch.object(module.Bootstrap,'save',save),patch.object(module,'_api',api),patch.object(module.Bootstrap,'verify_auth',verify),patch.object(module.Bootstrap,'_confirm_grant',confirm),patch.object(module.Bootstrap,'_confirm_revocation',revoke),patch.object(storage,'atomic_save',atomic),patch.object(os,'replace',replace),patch.object(os,'rename',rename),patch.object(Path,'mkdir',mkdir),patch.object(Path,'unlink',unlink),patch.object(e,'database',database):
            if args.action=='sql-candidate':
                op.load()
                if stage=='sql-ready':halt(stage)
                item=op.state['identities'][args.label]
                op._grant_transaction(item['uuid'],item['email']);result={'state':'COMMITTED'}
            elif args.action=='create':result=op.create(args.label)
            elif args.action=='reconcile-identity':result=op.reconcile_identity(args.label)
            else:result=getattr(op,args.action.replace('-','_'))()
        print(json.dumps(result));return 0
    except b.Blocked as error:print(json.dumps({'state':'BLOCKED','code':error.code}));return 2
    except Exception:print(json.dumps({'state':'BLOCKED','code':'I85_TEST_DRIVER_FAILURE_WITHHELD'}));return 3

if __name__=='__main__':raise SystemExit(main())
