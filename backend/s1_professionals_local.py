"""I79 internal Director administration on the existing S0 identity/SQL boundary.

Organizational registration of an existing GoTrue UUID, never user creation by
service_role, hosted API, shop grant, case transfer or intake suspension.
"""
from contextlib import closing
from dataclasses import dataclass
import hashlib
import hmac
import re
import time
from uuid import UUID,uuid4
from backend.identity_boundary import Denied,Principal
from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal

SQL='select prumo_private.s1_i79_admin_signed('+','.join(['%s']*12)+')'
FIELDS={'action','target_id','cargo','manager_id','expected_relationship_id','idempotency_key'}


def uuid(value):
    if type(value) is not str or str(UUID(value))!=value or UUID(value).int==0:raise ValueError('I79_UUID')
    return UUID(value)


def command(payload):
    if type(payload) is not dict or set(payload)!=FIELDS:raise ValueError('I79_FIELDS')
    p=payload.copy();p['target_id']=uuid(p['target_id'])
    if p['manager_id'] is not None:p['manager_id']=uuid(p['manager_id'])
    a=p['action'];r=p['expected_relationship_id'];c=p['cargo'];k=p['idempotency_key']
    if (type(a) is not str or a not in ('REGISTER','ACTIVATE','TRANSFER')
        or type(c) is not str or c not in ('gestor','consultor')
        or type(r) is not int or not 0<=r<=9223372036854775807
        or type(k) is not str or re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',k,re.ASCII) is None):raise ValueError('I79_COMMAND')
    if ((a=='REGISTER' and (p['manager_id'] is not None or r!=0))
        or (a=='ACTIVATE' and (r!=0 or (c=='consultor')!=(p['manager_id'] is not None)))
        or (a=='TRANSFER' and (c!='consultor' or p['manager_id'] is None or r==0))):raise ValueError('I79_ACTION_SCOPE')
    return p


def receipt(value,p):
    if type(value) is not dict or set(value)!={'outcome','request_id','action','target_id','cargo','manager_id','previous_relationship_id','relationship_id'}:
        raise ValueError('I79_RECEIPT_FIELDS')
    if value['outcome'] not in ('APPLIED','ALREADY_APPLIED'):raise ValueError('I79_RECEIPT_STATE')
    uuid(value['request_id'])
    if (value['target_id']!=str(p['target_id']) or value['action']!=p['action'] or value['cargo']!=p['cargo']
        or value['manager_id']!=(str(p['manager_id']) if p['manager_id'] else None)
        or value['previous_relationship_id']!=str(p['expected_relationship_id'])):raise ValueError('I79_RECEIPT_SCOPE')
    rel=value['relationship_id']
    needs_relation=p['cargo']=='consultor' and p['action']!='REGISTER'
    if needs_relation:
        if type(rel) is not str or re.fullmatch(r'[1-9][0-9]{0,18}',rel) is None or int(rel)>9223372036854775807 or int(rel)==p['expected_relationship_id']:
            raise ValueError('I79_RECEIPT_RELATION')
    elif rel is not None:raise ValueError('I79_UNEXPECTED_RELATION')
    return value.copy()


@dataclass(frozen=True)
class Result:
    state:str
    receipt:dict|None=None


class S1ProfessionalsLocal:
    def __init__(self,gateway):
        if type(gateway) is not S0CFI01AtomicCommandsLocal:raise TypeError('Real S0 gateway required')
        self.gateway=gateway

    def proof(self,principal,p):
        args=(principal.actor_id,principal.session_id,p['action'],p['target_id'],p['cargo'],p['manager_id'],
              p['expected_relationship_id'],p['idempotency_key'],self.gateway._key_id,int(time.time()),uuid4())
        material='|'.join(['s0-s1-i79-admin-v1',*(str(v) if v is not None else '-' for v in args)])
        return (*args,hmac.new(self.gateway._secret,material.encode(),hashlib.sha256).hexdigest())

    def execute(self,authorization,payload):
        try:p=command(payload)
        except Exception:return Result('INPUT_REJECTED')
        try:
            principal=self.gateway._identity.verify(authorization)
            if type(principal) is not Principal or type(principal.actor_id) is not UUID or type(principal.session_id) is not UUID:raise Denied()
        except Denied:return Result('DENIED')
        except Exception:return Result('UNAVAILABLE')
        try:
            import psycopg
            with closing(psycopg.connect(self.gateway._dsn,connect_timeout=5)) as connection:
                with connection:
                    connection.execute("set local lock_timeout='8s'")
                    connection.execute("set local statement_timeout='15s'")
                    rows=connection.execute(SQL,self.proof(principal,p)).fetchall()
                    if len(rows)!=1 or len(rows[0])!=1:raise ValueError('I79_ROW_COUNT')
                    result=receipt(rows[0][0],p)  # Includes deferred-COMMIT failure handling.
            return Result(result['outcome'],result)
        except Exception as exc:
            return Result({'42501':'DENIED','23514':'DENIED','40001':'STALE','23505':'CONFLICT'}.get(getattr(exc,'sqlstate',None),'UNAVAILABLE'))
