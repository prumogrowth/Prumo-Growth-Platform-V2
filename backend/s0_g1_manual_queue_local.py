"""Local signed G1 queue handoff; reuse S0 GoTrue/DSN/key infrastructure.

No public endpoint. Never accept actor/session/role from the command. Queue
version is NOT case/cycle version. No send, first-contact or transfer action.
"""
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import re
import time
from uuid import UUID,uuid4

from backend.identity_boundary import Denied,Principal
from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal

_SQL='''select prumo_private.g1_manual_signed_local(
 %s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint,%s::text,
 %s::uuid,%s::bigint,%s::uuid,%s::text)'''
FIELDS={'loja_id','ciclo_id','consultor_id','versao_esperada','chave_idempotencia'}


class State(str,Enum):
    MANUAL_ASSIGNED='MANUAL_ASSIGNED'
    ALREADY_MANUAL_ASSIGNED='ALREADY_MANUAL_ASSIGNED'
    INPUT_REJECTED='INPUT_REJECTED'
    DENIED='DENIED'
    STALE='STALE'
    IDEMPOTENCY_CONFLICT='IDEMPOTENCY_CONFLICT'
    DESTINATION_INELIGIBLE='DESTINATION_INELIGIBLE'
    INTAKE_PAUSED='INTAKE_PAUSED'
    ALREADY_OWNED='ALREADY_OWNED'
    UNAVAILABLE='UNAVAILABLE'


@dataclass(frozen=True)
class Result:
    state:State
    receipt:dict|None=None


def fields(payload):
    if type(payload) is not dict or set(payload)!=FIELDS:raise ValueError('G1_FIELDS')
    values=payload.copy()
    for key in ('loja_id','ciclo_id','consultor_id'):
        value=values[key]
        if type(value) is not str or str(UUID(value))!=value or UUID(value).int==0:
            raise ValueError('G1_UUID')
        values[key]=UUID(value)
    version=values['versao_esperada'];key=values['chave_idempotencia']
    if (type(version) is not int or not 1<=version<9223372036854775807
        or type(key) is not str or re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',key,re.ASCII) is None):
        raise ValueError('G1_VERSION_OR_KEY')
    return values


def safe_result(value,command):
    if type(value) is not dict or set(value)!={
        'outcome','request_id','store_id','cycle_id','consultant_id',
        'case_id','assignment_id','exception_id','version'}:
        raise ValueError('G1_RESULT_FIELDS')
    if value['outcome'] not in ('MANUAL_ASSIGNED','ALREADY_MANUAL_ASSIGNED'):
        raise ValueError('G1_RESULT_STATE')
    for key in ('request_id','store_id','cycle_id','consultant_id','case_id','assignment_id'):
        if type(value[key]) is not str or str(UUID(value[key]))!=value[key] or UUID(value[key]).int==0:
            raise ValueError('G1_RESULT_UUID')
    if value['exception_id'] is not None and (type(value['exception_id']) is not str
        or str(UUID(value['exception_id']))!=value['exception_id'] or UUID(value['exception_id']).int==0):
        raise ValueError('G1_RESULT_EXCEPTION')
    if (value['store_id']!=str(command['loja_id']) or value['cycle_id']!=str(command['ciclo_id'])
        or value['consultant_id']!=str(command['consultor_id'])
        or type(value['version']) is not int or value['version']!=command['versao_esperada']+1):
        raise ValueError('G1_RESULT_SCOPE_OR_VERSION')
    return value.copy()


class S0ManualQueueHandoffLocal:
    def __init__(self,gateway):
        if type(gateway) is not S0CFI01AtomicCommandsLocal:raise TypeError('Requires real S0 gateway')
        self._s0=gateway

    def _proof(self,principal,command):
        issued=int(time.time());nonce=uuid4()
        args=(principal.actor_id,principal.session_id,command['loja_id'],command['ciclo_id'],
            command['consultor_id'],command['versao_esperada'],command['chave_idempotencia'],
            self._s0._key_id,issued,nonce)
        material='|'.join(['s0-g1-manual-queue-local-v1',*(str(x) for x in args)])
        mac=hmac.new(self._s0._secret,material.encode(),hashlib.sha256).hexdigest()
        return (*args,mac)

    def execute(self,authorization,payload):
        try:command=fields(payload)
        except Exception:return Result(State.INPUT_REJECTED)
        try:
            principal=self._s0._identity.verify(authorization)
            if (type(principal) is not Principal or type(principal.actor_id) is not UUID
                or type(principal.session_id) is not UUID):raise Denied()
        except Denied:return Result(State.DENIED)
        except Exception:return Result(State.UNAVAILABLE)
        proof=self._proof(principal,command)
        try:
            import psycopg
            with psycopg.connect(self._s0._dsn,connect_timeout=5) as c:
                c.execute("set local lock_timeout='8s'")
                c.execute("set local statement_timeout='15s'")
                rows=c.execute(_SQL,proof).fetchall()
                if len(rows)!=1 or len(rows[0])!=1:raise ValueError('G1_SQL_RESULT')
                result=safe_result(rows[0][0],command)  # Before COMMIT, as CFI #13.
            return Result(State(result['outcome']),result)
        except ValueError:return Result(State.UNAVAILABLE)
        except Exception as exc:
            state={'42501':State.DENIED,'23514':State.DENIED,'40001':State.STALE,
                   '23505':State.IDEMPOTENCY_CONFLICT,'P3101':State.INTAKE_PAUSED,
                   'P3102':State.DESTINATION_INELIGIBLE,'P3103':State.ALREADY_OWNED}.get(
                       getattr(exc,'sqlstate',None),State.UNAVAILABLE)
            return Result(state)
