"""No secret/URL/identity arguments; all errors use a fixed public code."""
import argparse
import json
import os
from local_admin.boundary import Blocked,DEFAULT,ROOT
from local_admin.operation import Operator

class Parser(argparse.ArgumentParser):
    def error(self,message):raise Blocked('CLI_ARGUMENTS_INVALID')


def main():
    try:
        p=Parser(description='I84: fixed, unlinked, disposable local stack only')
        p.add_argument('--state-dir',default=str(DEFAULT))
        sub=p.add_subparsers(dest='command',required=True)
        for name in ('init','provision','serve','status','rotate','revoke','restart','worker-stop','recover','down'):sub.add_parser(name)
        sub.add_parser('prepare').add_argument('--s1-source',required=True)
        a=p.parse_args();os.chdir(ROOT);result=Operator(a.state_dir).execute(a.command,getattr(a,'s1_source',None))
        print(json.dumps(result,sort_keys=True));return 0
    except Blocked as error:print(json.dumps({'state':'BLOCKED','code':error.code}));return 2
    except Exception as error:
        code=getattr(error,'sqlstate',None)
        code=code if isinstance(code,str) and len(code)==5 and code.isascii() and code.isalnum() else 'WITHHELD'
        print(json.dumps({'state':'BLOCKED','code':'LOCAL_OPERATION_FAILED_RECOVERY_REQUIRED','sqlstate':code}));return 2

if __name__=='__main__':raise SystemExit(main())
