"""F02 cycle transitions with signed fixture commands and PG17 CAS, LAB ONLY.

Every cryptographic and identity input is synthetic: HostActor is injected,
not authenticated by a real S0 ingress, KMS, OIDC or Meta authority.
A stage result cannot prove COMMIT, reserve PRE_DISPATCH or enable a send.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from integration.s0s1_f02.pg17_service import (
    prepare_in_admin_transaction as f02_prepare,
    review_in_admin_transaction as f02_review,
)
from integration.s0s1_f02.pg17_service import result as f02_result

DOMAIN=b'PRUMO.S0.F02.CYCLE.COMMAND/0.1-LAB\x00'
K=('version','command_ref','nonce','action','case_ref','flow_ref','store_ref',
   'service_ref','actor_ref','key_revision','purpose_ref','expected_cycle',
   'expected_assignment','expected_policy','expected_suppression',
   'expected_consent','issued_ms','expires_ms')
ID=re.compile(r'^[A-Za-z0-9_.:-]{1,120}$')
ACT={'ADVANCE','PAUSE','RESUME','REVOKE'}
SCHEMA='prumo.s0.f02-cycle-command/0.1-lab'
NO_GRANT=dict(lab_only=True,host_authenticated=False,
    cycle_source_operational=False,consent_source_authenticated=False,
    schedule_authorized=False,send_authorized=False,
    graph_authorized=False,production_authorized=False)
@dataclass(frozen=True)
class HostActor:
    actor_ref:str
    store_ref:str
    service_ref:str
    case_ref:str
    flow_ref:str

class Refused(Exception): pass

def refuse(condition, reason):
    if condition:raise Refused(reason)

def ident(v):
    return type(v) is str and bool(ID.fullmatch(v))

def canonical(request):
    return json.dumps(request,sort_keys=True,separators=(',',':'),
         ensure_ascii=True,allow_nan=False).encode('ascii')

def digest(request):
    return hashlib.sha256(DOMAIN+canonical(request)).hexdigest()

def reply(status,reason,**kwargs):
    return dict(contract_version=SCHEMA,status=status,reason=reason,
                **NO_GRANT,**kwargs)

def valid_request(q,actor,signature):
    return (type(q) is dict and set(q)==set(K)
      and type(actor) is HostActor
      and type(signature) is bytes and len(signature)==64
      and q['version']==SCHEMA and q['action'] in ACT
      and all(ident(q[x]) for x in ('command_ref','nonce','case_ref',
          'flow_ref','store_ref','service_ref','actor_ref','purpose_ref'))
      and len(q['nonce'])>=8
      and type(q['key_revision']) is int and q['key_revision']>0
      and all(type(q[x]) is int and 0<q[x]<2**63-1 for x in (
        'expected_cycle','expected_assignment','expected_policy',
        'expected_suppression','expected_consent','issued_ms','expires_ms'))
      and q['expires_ms']>q['issued_ms']
      and q['expires_ms']-q['issued_ms']<=120000
      and all(getattr(actor,x)==q[x] for x in
           ('actor_ref','store_ref','service_ref','case_ref','flow_ref')))

def now_ms(c):
    return c.execute("SELECT floor(extract(epoch from clock_timestamp())*1000)::bigint AS ms").fetchone()['ms']

def _locked(c,q,*,at_ms,require_policy):
    case=c.execute("SELECT * FROM s0_pre_dispatch_lab.cases "
       "WHERE case_ref=%s FOR UPDATE",(q['case_ref'],)).fetchone()
    refuse(not case or case['concessionaria_id']!=q['store_ref'] or
       case['principal_ref']!=q['service_ref'],'CASE_SCOPE_DENIED')
    auth=c.execute('SELECT * FROM s0_f02_cycle_lab.authorities '
       'WHERE case_ref=%s FOR UPDATE',(q['case_ref'],)).fetchone()
    refuse(not auth or any(auth[k]!=q[k] for k in (
       'flow_ref','store_ref','service_ref','purpose_ref','actor_ref')) or
       not auth['actor_enabled'],'ACTOR_OR_SCOPE_DENIED')
    refuse(auth['actor_key_revision']!=q['key_revision'],'KEY_REVOKED_OR_ROTATED')
    source=c.execute('SELECT * FROM s0_f02_lab.case_cycles '
       'WHERE case_ref=%s FOR UPDATE',(q['case_ref'],)).fetchone()
    refuse(not source or source['flow_ref']!=q['flow_ref'] or
       source['cycle_revision']!=auth['cycle_revision'],
       'CYCLE_SOURCE_DIVERGED')
    # Freshness is checked *after* signature and prior-command lookup.
    # This permits exact idempotent replay without applying any new mutation.
    consent=c.execute('SELECT * FROM s0_pre_dispatch_lab.consents '
       'WHERE case_ref=%s AND purpose_ref=%s FOR UPDATE',
       (q['case_ref'],q['purpose_ref'])).fetchone()
    refuse(not consent,'CONSENT_SOURCE_MISSING_OR_STALE')
    suppression=c.execute('SELECT purpose_ref,active FROM '
       's0_pre_dispatch_lab.suppressions WHERE case_ref=%s '
       'ORDER BY purpose_ref FOR UPDATE',(q['case_ref'],)).fetchall()
    if require_policy:
        refuse(not case['active'] or case['global_opt_out'],
               'POLICY_DENIED')
        refuse(consent['state']!='GRANTED' or
          int(consent['valid_until'].timestamp()*1000)<=at_ms,
          'CONSENT_DENIED')
        refuse(any(x['active'] and x['purpose_ref'] in
            ('*',q['purpose_ref']) for x in suppression),'SUPPRESSED')
    return case,auth,source,consent

def transition(c,*,request,signature,host):
    """Verify fixture actor Ed25519, lock sources, CAS, journal; caller commits."""
    if not valid_request(request,host,signature):
        return reply('DENIED','INVALID_REQUEST')
    sp='f02_cycle_command'
    c.execute('SAVEPOINT '+sp)
    try:
        t=now_ms(c)
        refuse(request['issued_ms']>t+30000 or
            request['expires_ms']<=t,'EXPIRED_OR_FUTURE')
        # Terminal updates must remain possible after opt-out/consent
        # revocation, but stale scope/revisions are always refused.
        case,auth,source,consent=_locked(c,request,at_ms=t,
               require_policy=request['action'] in ('ADVANCE','RESUME'))
        try:
            Ed25519PublicKey.from_public_bytes(
                bytes(auth['ed25519_public_key'])).verify(
                signature,DOMAIN+canonical(request))
        except Exception:
            raise Refused('INVALID_SIGNATURE')
        existing=c.execute('SELECT * FROM s0_f02_cycle_lab.commands '
           'WHERE command_ref=%s OR (case_ref=%s AND nonce=%s) '
           'FOR SHARE',(request['command_ref'],request['case_ref'],
                       request['nonce'])).fetchall()
        if existing:
            exact=len(existing)==1 and (
                 existing[0]['command_ref']==request['command_ref']
                 and existing[0]['request_digest']==digest(request))
            refuse(not exact,'COMMAND_OR_NONCE_COLLISION')
            c.execute('RELEASE SAVEPOINT '+sp)
            return reply('LAB_PREVIOUSLY_RECORDED_NOT_AUTHORITY',
                'IDEMPOTENT_READBACK_REQUIRED',
                recorded_revision=existing[0]['after_revision'])
        refuse(auth['cycle_revision']!=request['expected_cycle'] or
            case['assignment_revision']!=request['expected_assignment'] or
            case['policy_revision']!=request['expected_policy'] or
            case['suppression_revision']!=request['expected_suppression'] or
            consent['revision']!=request['expected_consent'],
            'STALE_VERSIONS')
        refuse(auth['state']=='REVOKED','CYCLE_TERMINAL_REVOKED')
        states={
          ('ACTIVE','ADVANCE'):'ACTIVE',
          ('ACTIVE','PAUSE'):'PAUSED',
          ('PAUSED','RESUME'):'ACTIVE',
          ('ACTIVE','REVOKE'):'REVOKED',
          ('PAUSED','REVOKE'):'REVOKED'
        }
        next_state=states.get((auth['state'],request['action']))
        refuse(next_state is None,'INVALID_TRANSITION')
        next_rev=auth['cycle_revision']+1
        updated_cycle=c.execute('UPDATE s0_f02_lab.case_cycles SET cycle_revision=%s '
            'WHERE case_ref=%s AND cycle_revision=%s',
            (next_rev,request['case_ref'],auth['cycle_revision']))
        refuse(updated_cycle.rowcount!=1,'CYCLE_CAS_FAILED')
        updated_authority=c.execute('UPDATE s0_f02_cycle_lab.authorities '
            'SET cycle_revision=%s,state=%s,generation=generation+1,'
            'last_command_ref=%s WHERE case_ref=%s AND cycle_revision=%s',
            (next_rev,next_state,request['command_ref'],request['case_ref'],
             auth['cycle_revision']))
        refuse(updated_authority.rowcount!=1,'AUTHORITY_CAS_FAILED')
        c.execute('INSERT INTO s0_f02_cycle_lab.commands '
            '(command_ref,case_ref,nonce,request_digest,action,'
            'before_revision,after_revision,after_state,actor_ref,'
            'actor_key_revision,consent_revision,assignment_revision,'
            'policy_revision,suppression_revision) VALUES '
            '(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(
             request['command_ref'],request['case_ref'],request['nonce'],
             digest(request),request['action'],auth['cycle_revision'],next_rev,
             next_state,request['actor_ref'],request['key_revision'],
             request['expected_consent'],request['expected_assignment'],
             request['expected_policy'],request['expected_suppression']))
        c.execute('RELEASE SAVEPOINT '+sp)
        return reply('LAB_CYCLE_STAGED_BEFORE_COMMIT','READBACK_REQUIRED',
            staged_cycle_revision=next_rev,staged_state=next_state,
            commit_verified=False)
    except Refused as ex:
        c.execute('ROLLBACK TO SAVEPOINT '+sp)
        c.execute('RELEASE SAVEPOINT '+sp)
        return reply('DENIED',str(ex))
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT '+sp)
        c.execute('RELEASE SAVEPOINT '+sp)
        return reply('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def readback(c,*,command_ref,host,request_hash):
    """Only independently committed journal/authority observations count."""
    if not ident(command_ref) or type(host) is not HostActor or (
        type(request_hash) is not str or not re.fullmatch('[0-9a-f]{64}',request_hash)):
        return reply('DENIED','INVALID_REQUEST')
    try:
        event=c.execute('SELECT * FROM s0_f02_cycle_lab.commands '
            'WHERE command_ref=%s',(command_ref,)).fetchone()
        if not event:
            return reply('LAB_COMMIT_UNKNOWN','NO_DURABLE_EVENT',
                         commit_verified=False)
        auth=c.execute('SELECT * FROM s0_f02_cycle_lab.authorities '
            'WHERE case_ref=%s',(event['case_ref'],)).fetchone()
        if not auth or auth['actor_ref']!=host.actor_ref or (
           auth['store_ref']!=host.store_ref or
           auth['service_ref']!=host.service_ref or
           auth['case_ref']!=host.case_ref or
           auth['flow_ref']!=host.flow_ref):
            return reply('DENIED','SCOPE_CHANGED')
        if event['request_digest']!=request_hash:
            return reply('DENIED','COMMAND_COLLISION')
        source=c.execute('SELECT * FROM s0_f02_lab.case_cycles '
          'WHERE case_ref=%s',(event['case_ref'],)).fetchone()
        if not source or source['flow_ref']!=host.flow_ref or (
            source['cycle_revision']!=auth['cycle_revision']):
            return reply('DENIED','CYCLE_SOURCE_DIVERGED')
        if auth['cycle_revision']!=event['after_revision'] or (
            auth['last_command_ref']!=command_ref):
            return reply('LAB_COMMAND_SUPERSEDED','NEWER_CYCLE_TRANSITION',
                commit_verified=True,
                original_revision=event['after_revision'],
                latest_revision=auth['cycle_revision'])
        return reply('LAB_COMMITTED_CYCLE_READBACK',
            'DURABLE_PG17_LAB_OBSERVATION',commit_verified=True,
            cycle_revision=event['after_revision'],state=event['after_state'])
    except Exception:
        return reply('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def _authority_gate(c,q,scope,principal,expected):
    if type(q) is not dict or type(expected) is not dict or (
       'cycle' not in expected or 'flow_ref' not in q):
        raise Refused('INVALID_REQUEST')
    auth=c.execute('SELECT * FROM s0_f02_cycle_lab.authorities '
       'WHERE case_ref=%s FOR SHARE',(q['case_ref'],)).fetchone()
    if not auth:
        raise Refused('AUTHORITY_MISSING')
    source=c.execute('SELECT cycle_revision,flow_ref FROM s0_f02_lab.case_cycles '
       'WHERE case_ref=%s FOR SHARE',(q['case_ref'],)).fetchone()
    if not source or (auth['cycle_revision']!=source['cycle_revision'] or
       auth['flow_ref']!=source['flow_ref']):
        raise Refused('CYCLE_SOURCE_DIVERGED')
    if (auth['state']!='ACTIVE' or not auth['actor_enabled'] or
       auth['cycle_revision']!=expected['cycle'] or
       auth['flow_ref']!=q['flow_ref'] or
       auth['store_ref']!=scope.concessionaria_id or
       auth['service_ref']!=principal.principal_ref or
       auth['purpose_ref']!=q['consent_purpose_ref']):
        raise Refused('CYCLE_AUTHORITY_DENIED')

def _guarded(c,fn,*args,request,scope,principal,expected,**kwargs):
    sp='f02_cycle_gate'
    c.execute('SAVEPOINT '+sp)
    try:
        # Original F02 performs M09, case, consent, suppression and template
        # checks under locks. All its journal writes share the outer savepoint.
        out=fn(c,*args,scope=scope,principal=principal,expected=expected,
               **kwargs)
        if out['decision'] not in (
          'LAB_REQUEST_RECORDED_NO_MODEL',
          'LAB_REQUEST_REPLAY_REVIEW_ONLY',
          'LAB_PROPOSAL_RECORDED_REVIEW_ONLY',
          'LAB_ALREADY_REVIEWED_NO_EFFECT'):
            c.execute('RELEASE SAVEPOINT '+sp)
            return out
        _authority_gate(c,request,scope,principal,expected)
        c.execute('RELEASE SAVEPOINT '+sp)
        return dict(out,cycle_authority_lab_consistent=True,
                    source_host_authenticated=False)
    except Refused as ex:
        c.execute('ROLLBACK TO SAVEPOINT '+sp)
        c.execute('RELEASE SAVEPOINT '+sp)
        return f02_result('DENIED',str(ex))
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT '+sp)
        c.execute('RELEASE SAVEPOINT '+sp)
        return f02_result('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def prepare_guarded(c,q,*,scope,principal,m09_versions,expected):
    """Additive candidate: F02 request and cycle gate in one PG17 transaction."""
    return _guarded(c,f02_prepare,q,request=q,scope=scope,
       principal=principal,expected=expected,m09_versions=m09_versions)

def review_guarded(c,proposal,*,q,scope,principal,m09_versions,expected):
    """Additive candidate: review and cycle gate; still NO dispatch."""
    return _guarded(c,f02_review,proposal,request=q,scope=scope,
       principal=principal,expected=expected,m09_versions=m09_versions,q=q)
