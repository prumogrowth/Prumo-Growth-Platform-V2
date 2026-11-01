"""S0 #11 synthetic F01 ownership and irreversible handoff, PG17 lab only.

A 'recheck' records audit evidence, NEVER publishes content or authorizes
model invocation, F02 restart, Graph, assignment, knowledge or production.
All identities and eight revisions are supplied by a disposable test host.
"""
import hashlib
import json
import re
from datetime import timedelta

VERS=('case','cycle','assignment','catalog','knowledge','policy','route','consent')
FIELDS=('case_ref','store_ref','person_ref','service_ref')
ID=re.compile(r'^[A-Za-z0-9_.:-]{1,120}$')
VERSION='prumo.s0.f01-owner/0.1-lab'
NO_AUTH=dict(model_invocation_authorized=False,publish_authorized=False,
             handoff_operationally_authorized=False,
             consultant_assignment_authorized=False,f02_restart_authorized=False,
             commercial_transition_authorized=False,production_authorized=False,
             source_authenticated=False)
def answer(status,reason):
    return dict(contract_version=VERSION,status=status,reason=reason,
                lab_only=True,**NO_AUTH)
def ident(x):
    return type(x) is str and bool(ID.fullmatch(x))
def valid_versions(v):
    return type(v) is dict and set(v)==set(VERS) and all(
        type(v[k]) is int and 0<v[k]<2**63-1 for k in VERS)
def valid_scope(scope):
    return type(scope) is dict and set(scope)==set(FIELDS) and all(
        ident(scope[k]) for k in FIELDS)
def digest(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),
                   ensure_ascii=True,allow_nan=False).encode('ascii')
    return hashlib.sha256(raw).hexdigest()
def versions(k):
    return {p:k[p+'_revision'] for p in VERS}
def current(c,scope):
    return c.execute('SELECT * FROM s0_f01_lab.cases WHERE case_ref=%s FOR UPDATE',
                     (scope['case_ref'],)).fetchone()
def permitted(k,scope,v):
    if not k or any(k[p]!=scope[p] for p in FIELDS):
        return 'SCOPE_DENIED'
    # Ownership/handoff denial MUST precede freshness denial.
    if k['owner_route']!='AI' or k['handoff_definitive'] or k['humanized']:
        return 'HUMAN_ONLY'
    if k['opt_out'] or not k['channel_eligible'] or k['post_remittance'] or k['post_sale']:
        return 'POLICY_DENIED'
    if versions(k)!=v:
        return 'STALE_VERSIONS'
    return None
def begin_turn(c,*,turn_ref,scope,expected,deadline_seconds=30):
    """Starts a LAB turn, not a model invocation; caller commits transaction."""
    if not (ident(turn_ref) and valid_scope(scope) and valid_versions(expected)
            and type(deadline_seconds) is int and 1<=deadline_seconds<=120):
        return answer('DENIED','INVALID_REQUEST')
    c.execute('SAVEPOINT f01_start')
    try:
        k=current(c,scope)
        denial=permitted(k,scope,expected)
        if denial: raise ValueError(denial)
        now=c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
        binding=digest(dict(scope=scope,versions=expected))
        before=c.execute('SELECT * FROM s0_f01_lab.turns WHERE turn_ref=%s FOR UPDATE',
                         (turn_ref,)).fetchone()
        if before:
            if before['scope_digest']!=binding or before['expected_versions']!=expected:
                raise ValueError('TURN_COLLISION')
            if before['deadline_at']<=now: raise ValueError('TURN_EXPIRED')
            status='LAB_TURN_REPLAY_ONLY'
        else:
            c.execute('INSERT INTO s0_f01_lab.turns '
              '(turn_ref,case_ref,service_ref,scope_digest,expected_versions,'
              'started_at,deadline_at) VALUES(%s,%s,%s,%s,%s,%s,%s)',
              (turn_ref,scope['case_ref'],scope['service_ref'],binding,
               json.dumps(expected,sort_keys=True),now,
               now+timedelta(seconds=deadline_seconds)))
            status='LAB_TURN_RECORDED_NO_MODEL'
        c.execute('RELEASE SAVEPOINT f01_start')
        return answer(status,'LAB_ONLY_NO_EXTERNAL_AUTHORITY')
    except ValueError as e:
        c.execute('ROLLBACK TO SAVEPOINT f01_start')
        c.execute('RELEASE SAVEPOINT f01_start')
        return answer('DENIED',str(e))
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT f01_start')
        c.execute('RELEASE SAVEPOINT f01_start')
        return answer('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def definitive_handoff(c,*,event_ref,scope,expected):
    """A HUMAN transfer, once committed, is irreversible even on direct UPDATE."""
    if not ident(event_ref) or not valid_scope(scope) or not valid_versions(expected):
        return answer('DENIED','INVALID_REQUEST')
    c.execute('SAVEPOINT f01_handoff')
    try:
        k=current(c,scope)
        if not k or any(k[p]!=scope[p] for p in FIELDS):
            raise ValueError('SCOPE_DENIED')
        if k['handoff_definitive']:
            prior=c.execute('SELECT * FROM s0_f01_lab.handoff_events '
               'WHERE case_ref=%s FOR SHARE',(scope['case_ref'],)).fetchone()
            if prior and prior['event_ref']==event_ref and prior['service_ref']==scope['service_ref']:
                status='LAB_HANDOFF_REPLAY_HUMAN_ONLY'
                reason='IRREVERSIBLE'
            else:
                raise ValueError('HUMAN_ONLY')
        else:
            if versions(k)!=expected: raise ValueError('STALE_VERSIONS')
            c.execute('UPDATE s0_f01_lab.cases SET '
              "owner_route='HUMAN',handoff_definitive=true,humanized=true,"
              'handoff_sequence=handoff_sequence+1,'
              'assignment_revision=assignment_revision+1,'
              'case_revision=case_revision+1 '
              'WHERE case_ref=%s',(scope['case_ref'],))
            c.execute('INSERT INTO s0_f01_lab.handoff_events '
              '(event_ref,case_ref,service_ref,event_sequence) '
              'VALUES(%s,%s,%s,%s)',
              (event_ref,scope['case_ref'],scope['service_ref'],
               k['handoff_sequence']+1))
            status='LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH'
            reason='HUMAN_ONLY'
        c.execute('RELEASE SAVEPOINT f01_handoff')
        return answer(status,reason)
    except ValueError as e:
        c.execute('ROLLBACK TO SAVEPOINT f01_handoff')
        c.execute('RELEASE SAVEPOINT f01_handoff')
        return answer('DENIED',str(e))
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT f01_handoff')
        c.execute('RELEASE SAVEPOINT f01_handoff')
        return answer('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def recheck_proposal(c,*,turn_ref,scope,expected,candidate_digest):
    """After a draft: recheck ownership and write ONLY a no-publish audit fact."""
    if (not ident(turn_ref) or not valid_scope(scope)
        or not valid_versions(expected) or type(candidate_digest) is not str
        or not re.fullmatch('[0-9a-f]{64}',candidate_digest)):
        return answer('DENIED','INVALID_REQUEST')
    c.execute('SAVEPOINT f01_review')
    try:
        k=current(c,scope)
        denial=permitted(k,scope,expected)
        if denial: raise ValueError(denial)
        now=c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
        turn=c.execute('SELECT * FROM s0_f01_lab.turns WHERE turn_ref=%s FOR UPDATE',
                       (turn_ref,)).fetchone()
        if not turn or turn['case_ref']!=scope['case_ref'] or \
           turn['service_ref']!=scope['service_ref'] or \
           turn['scope_digest']!=digest(dict(scope=scope,versions=expected)) or \
           turn['expected_versions']!=expected:
            raise ValueError('MISSING_OR_CHANGED_TURN')
        if now>=turn['deadline_at']: raise ValueError('TURN_EXPIRED')
        prior=c.execute('SELECT * FROM s0_f01_lab.publication_checks '
                        'WHERE turn_ref=%s FOR UPDATE',(turn_ref,)).fetchone()
        if prior:
            if prior['candidate_digest']!=candidate_digest:
                raise ValueError('PROPOSAL_CONFLICT')
            state='LAB_RECHECK_REPLAY_NO_PUBLISH'
        else:
            c.execute('INSERT INTO s0_f01_lab.publication_checks '
              '(turn_ref,case_ref,candidate_digest) VALUES(%s,%s,%s)',
              (turn_ref,scope['case_ref'],candidate_digest))
            state='LAB_RECHECK_RECORDED_NO_PUBLISH'
        c.execute('RELEASE SAVEPOINT f01_review')
        return answer(state,'FURTHER_S0_SEMANTIC_AND_META_GATES_REQUIRED')
    except ValueError as e:
        c.execute('ROLLBACK TO SAVEPOINT f01_review')
        c.execute('RELEASE SAVEPOINT f01_review')
        return answer('DENIED',str(e))
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT f01_review')
        c.execute('RELEASE SAVEPOINT f01_review')
        return answer('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
