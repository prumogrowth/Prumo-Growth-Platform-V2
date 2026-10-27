"""I80 laboratory adapter. Reuses I79/S0 identity, DSN, key and transaction model.

Inventory -> persisted explicit preview -> CAS apply. Not an Edge runtime,
public endpoint, new Auth/permission system or F02 commercial ratification.
"""
from contextlib import closing
from datetime import datetime
import hashlib
import hmac
import re
import time
from uuid import UUID,uuid4
from backend.identity_boundary import Denied,Principal
from backend.s1_professionals_local import S1ProfessionalsLocal,Result,uuid

SQL='select prumo_private.s1_i80_signed('+','.join(['%s']*15)+')'
FIELDS={'action','target_id','cargo','manager_id','expected_sha256','preview_id','cursor','limit','idempotency_key'}
BLOCKERS={'INVENTORY_TOO_LARGE','MISSING_TEAM_USE_I79_REGISTER','AUTH_IDENTITY_MISSING','DIRECTOR_AUTHORITY_CONFLICT',
 'CLASSIFIED_ROLE_CONFLICT','MULTIPLE_ACTIVE_RELATIONS','MANAGER_HAS_PARENT_LINK','CONSULTANT_HAS_SUBORDINATES',
 'INACTIVE_MANAGER_HAS_ACTIVE_CONSULTANTS','MANAGER_REQUIRED','MANAGER_NOT_CLASSIFIED_ACTIVE',
 'PENDING_CHEFIA_USE_I79_ACTIVATION','NOTHING_TO_REGULARIZE','CLASSIFIED_USE_I79_TRANSFER'}


def digest(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}',value,re.ASCII) is None:raise ValueError('I80_SHA256')
    return value


def command(payload):
    if type(payload) is not dict or set(payload)!=FIELDS:raise ValueError('I80_FIELDS')
    p=payload.copy()
    for key in ('target_id','manager_id','preview_id','cursor'):
        if p[key] is not None:p[key]=uuid(p[key])
    a=p['action'];limit=p['limit'];key=p['idempotency_key']
    if (type(a) is not str or a not in ('INVENTORY','PREVIEW','APPLY') or type(limit) is not int
        or type(key) is not str or re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',key,re.ASCII) is None):raise ValueError('I80_COMMAND')
    if a=='INVENTORY':
        if not 1<=limit<=50 or any(p[k] is not None for k in ('target_id','cargo','manager_id','expected_sha256','preview_id')):
            raise ValueError('I80_INVENTORY_SCOPE')
    else:
        if (p['target_id'] is None or type(p['cargo']) is not str or p['cargo'] not in ('gestor','consultor')
            or (p['cargo']=='gestor' and p['manager_id'] is not None) or limit!=0 or p['cursor'] is not None
            or (a=='PREVIEW' and p['preview_id'] is not None) or (a=='APPLY' and p['preview_id'] is None)):
            raise ValueError('I80_PROPOSAL_SCOPE')
        digest(p['expected_sha256'])
    return p


def relation(value):
    if value is not None and (type(value) is not str or re.fullmatch(r'[1-9][0-9]{0,18}',value,re.ASCII) is None or int(value)>9223372036854775807):
        raise ValueError('I80_RELATION_ID')


def receipt(value,p):
    if type(value) is not dict:raise ValueError('I80_RECEIPT')
    if p['action']=='INVENTORY':
        if set(value)!={'outcome','items','has_more','next_cursor'} or value['outcome']!='INVENTORY' or type(value['items']) is not list or len(value['items'])>p['limit'] or type(value['has_more']) is not bool:
            raise ValueError('I80_INVENTORY_RESULT')
        previous=p['cursor']
        for item in value['items']:
            if type(item) is not dict or set(item)!={'target_id','cargo','estado','bounded','inventory_sha256'}:raise ValueError('I80_INVENTORY_ITEM')
            actor=uuid(item['target_id']);digest(item['inventory_sha256'])
            if previous is not None and actor.int<=previous.int:raise ValueError('I80_INVENTORY_ORDER')
            if item['cargo'] not in (None,'diretor','gestor','consultor') or item['estado'] not in (None,'pendente','ativo','suspenso','desligado') or type(item['bounded']) is not bool:
                raise ValueError('I80_INVENTORY_STATE')
            previous=actor
        if value['has_more']:
            if not value['items'] or uuid(value['next_cursor'])!=previous:raise ValueError('I80_CURSOR')
        elif value['next_cursor'] is not None:raise ValueError('I80_TERMINAL_CURSOR')
        return value.copy()
    if value.get('target_id')!=str(p['target_id']) or value.get('cargo')!=p['cargo'] or value.get('manager_id')!=(str(p['manager_id']) if p['manager_id'] else None):
        raise ValueError('I80_RECEIPT_BINDING')
    uuid(value['preview_id'])
    if p['action']=='PREVIEW':
        if set(value)!={'outcome','preview_id','target_id','cargo','manager_id','inventory_sha256','snapshot_sha256','blockers','impact','expires_at'}:
            raise ValueError('I80_PREVIEW_FIELDS')
        if value['inventory_sha256']!=p['expected_sha256']:raise ValueError('I80_INVENTORY_BINDING')
        digest(value['snapshot_sha256'])
        if type(value['blockers']) is not list or any(type(b) is not str or b not in BLOCKERS for b in value['blockers']):raise ValueError('I80_BLOCKERS')
        if value['outcome']!=('BLOCKED' if value['blockers'] else 'READY'):raise ValueError('I80_PREVIEW_STATUS')
        i=value['impact']
        if type(i) is not dict or set(i)!={'state_preserved','current_relationship_id','complete','consultant_intake_gate_after','must_recheck_assignment_authority','change_relationship','revoke_exception_ids','grant_count','assignment_count','case_count','intake_paused'}:
            raise ValueError('I80_IMPACT_FIELDS')
        if (i['state_preserved'] not in (None,'pendente','ativo','suspenso','desligado') or type(i['complete']) is not bool
            or type(i['change_relationship']) is not bool or type(i['consultant_intake_gate_after']) is not bool
            or i['must_recheck_assignment_authority'] is not True
            or (i['intake_paused'] is not None and type(i['intake_paused']) is not bool)):
            raise ValueError('I80_IMPACT_STATE')
        relation(i['current_relationship_id'])
        if type(i['revoke_exception_ids']) is not list or len(set(i['revoke_exception_ids']))!=len(i['revoke_exception_ids']):raise ValueError('I80_IMPACT_EXCEPTIONS')
        for v in i['revoke_exception_ids']:uuid(v)
        for k in ('grant_count','assignment_count','case_count'):
            if i['complete']:
                if type(i[k]) is not int or not 0<=i[k]<=2000:raise ValueError('I80_IMPACT_COUNT')
            elif i[k] is not None:raise ValueError('I80_INCOMPLETE_COUNT')
        if datetime.fromisoformat(value['expires_at']).tzinfo is None:raise ValueError('I80_EXPIRY_TYPE')
    else:
        if set(value)!={'outcome','request_id','preview_id','target_id','cargo','estado','manager_id','relationship_id','revoked_exception_count','before_sha256','after_sha256'}:
            raise ValueError('I80_APPLICATION_FIELDS')
        if value['outcome'] not in ('APPLIED','ALREADY_APPLIED') or value['preview_id']!=str(p['preview_id']) or value['before_sha256']!=p['expected_sha256']:
            raise ValueError('I80_APPLICATION_BINDING')
        uuid(value['request_id']);digest(value['after_sha256']);relation(value['relationship_id'])
        if value['estado'] not in ('pendente','ativo','suspenso','desligado') or type(value['revoked_exception_count']) is not int or not 0<=value['revoked_exception_count']<=2000:
            raise ValueError('I80_APPLICATION_STATE')
        if (p['manager_id'] is None)!=(value['relationship_id'] is None):raise ValueError('I80_APPLICATION_RELATION')
    return value.copy()


class S1LegacyRegularizationLocal(S1ProfessionalsLocal):
    def proof(self,principal,p):
        args=(principal.actor_id,principal.session_id,p['action'],p['target_id'],p['cargo'],p['manager_id'],p['expected_sha256'],p['preview_id'],p['cursor'],p['limit'],p['idempotency_key'],self.gateway._key_id,int(time.time()),uuid4())
        material='|'.join(['s0-s1-i80-regularization-v1',*(str(v) if v is not None else '-' for v in args)])
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
            with closing(psycopg.connect(self.gateway._dsn,connect_timeout=5)) as c:
                with c:
                    c.execute("set local lock_timeout='8s'");c.execute("set local statement_timeout='15s'")
                    rows=c.execute(SQL,self.proof(principal,p)).fetchall()
                    if len(rows)!=1 or len(rows[0])!=1:raise ValueError('I80_ROW_COUNT')
                    result=receipt(rows[0][0],p)
            return Result(result['outcome'],result)
        except Exception as exc:
            return Result({'42501':'DENIED','23514':'DENIED','40001':'STALE','23505':'CONFLICT',
                           '55P03':'CONCURRENT_CHANGE','P3180':'EXPIRED','P3181':'BLOCKED'}.get(getattr(exc,'sqlstate',None),'UNAVAILABLE'))
