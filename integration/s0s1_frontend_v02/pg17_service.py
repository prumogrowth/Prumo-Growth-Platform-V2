"""Issue #14: historical-owner open + post-commit readback in disposable PG17.

No HTTP handler, real actor validation or provider event proof. A staged open
never attests COMMIT. The caller must independently read back with a NEW
transaction after COMMIT before presenting an acknowledged read in the UI.
"""
from __future__ import annotations

from integration.s0s1_frontend_read.pg17_service import (
    scope,valid,REV,case_row,events,cursor,attention
)
V='prumo.s0.frontend.history-readback/0.2-lab'

def result(status,reason,**extra):
    return dict(contract_version=V,status=status,reason=reason,
        lab_only=True,host_principal_authenticated=False,
        inbound_origin_verified=False,production_authorized=False,
        publish_authorized=False,send_authorized=False,**extra)

def request_ok(open_ref,case_ref,store_ref,actor_ref,role,allowed_stores,expected):
    return (valid(open_ref) and valid(case_ref) and
        scope(store_ref,actor_ref,role,allowed_stores) and
        type(expected) is dict and set(expected)==set(REV) and all(
            type(expected[k]) is int and 0<expected[k]<2**63-1 for k in REV))

def _owned(k,case_ref,store_ref,actor_ref,expected,*,allow_inbox_advance=False):
    if not k or k['store_ref']!=store_ref:
        raise ValueError('SCOPE_DENIED')
    if k['owner_ref']!=actor_ref:
        raise ValueError('NOT_CURRENT_OWNER')
    if any(k[x]!=expected[x] for x in REV if
           x!='inbox_revision' or not allow_inbox_advance):
        raise ValueError('STALE_OR_REASSIGNED')
    if k['active'] and not k['actionable']:
        mode='HISTORICAL_READ_ONLY'
    elif not k['active']:
        mode='HISTORICAL_READ_ONLY'
    else:
        mode='ACTIVE_ACTIONABLE'
    return mode

def open_owned(c,*,open_ref,case_ref,store_ref,actor_ref,role,allowed_stores,
               expected):
    """Stage a read for titular, even if case is archived/non-actionable.

    NO 'confirmed read' in the response: the caller controls COMMIT. Old
    open_refs never mark newly received inbound messages as read.
    """
    if not request_ok(open_ref,case_ref,store_ref,actor_ref,role,
                      allowed_stores,expected):
        return result('DENIED','INVALID_REQUEST')
    c.execute('SAVEPOINT frontend_v02_open')
    try:
        k=case_row(c,case_ref)
        if not k or k['store_ref']!=store_ref:
            raise ValueError('SCOPE_DENIED')
        if role!='OWNER':
            c.execute('RELEASE SAVEPOINT frontend_v02_open')
            return result('LAB_SUPERVISORY_VIEW_NO_READ',
                          'TITULAR_CURSOR_UNTOUCHED')
        if k['owner_ref']!=actor_ref:
            raise ValueError('NOT_CURRENT_OWNER')
        # Look up old committed attempt before checking the inbox revision,
        # so a timed-out retry cannot acknowledge new inbound implicitly.
        previous=c.execute('SELECT * FROM s0_frontend_lab.open_attempts '
            'WHERE open_ref=%s FOR UPDATE',(open_ref,)).fetchone()
        if previous:
            if (previous['case_ref']!=case_ref or
                previous['store_ref']!=store_ref or
                previous['owner_ref']!=actor_ref or
                any(previous[x]!=expected[x] for x in REV)):
                raise ValueError('OPEN_REF_COLLISION')
            mode=_owned(k,case_ref,store_ref,actor_ref,expected,
                        allow_inbox_advance=True)
            status='LAB_OPEN_REPLAY_STAGED_NOT_COMMIT_PROOF'
            cutoff=previous['read_through_seq']
        else:
            mode=_owned(k,case_ref,store_ref,actor_ref,expected)
            seen=events(c,case_ref)
            cutoff=max((v['event_seq'] for v in seen
                  if v['event_kind']=='INBOUND' and v['inbound_visible']),
                  default=0)
            c.execute('INSERT INTO s0_frontend_lab.read_cursors '
               '(case_ref,owner_ref,read_through_seq) VALUES(%s,%s,%s) '
               'ON CONFLICT(case_ref,owner_ref) DO UPDATE SET '
               'read_through_seq=GREATEST('
               's0_frontend_lab.read_cursors.read_through_seq,'
               'EXCLUDED.read_through_seq)',
               (case_ref,actor_ref,cutoff))
            c.execute('INSERT INTO s0_frontend_lab.open_attempts '
               '(open_ref,case_ref,owner_ref,store_ref,assignment_revision,'
               'case_revision,inbox_revision,read_through_seq) '
               'VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
               (open_ref,case_ref,actor_ref,store_ref,
                expected['assignment_revision'],expected['case_revision'],
                expected['inbox_revision'],cutoff))
            status='LAB_OPEN_STAGED_BEFORE_COMMIT'
        c.execute('RELEASE SAVEPOINT frontend_v02_open')
        return result(status,'READBACK_REQUIRED',open_ref=open_ref,
            read_through_seq=cutoff,conversation_mode=mode,
            read_confirmation_state='NOT_CONFIRMED',
            display_read_confirmed=False,composer_enabled=False if
            mode=='HISTORICAL_READ_ONLY' else bool(k['actionable'] and k['active']))
    except ValueError as e:
        c.execute('ROLLBACK TO SAVEPOINT frontend_v02_open')
        c.execute('RELEASE SAVEPOINT frontend_v02_open')
        return result('DENIED',str(e))
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT frontend_v02_open')
        c.execute('RELEASE SAVEPOINT frontend_v02_open')
        return result('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def readback(c,*,open_ref,case_ref,store_ref,actor_ref,role,allowed_stores,
             expected):
    """Independent transaction must run after caller COMMIT or unknown commit.

    Missing record is UNKNOWN, not proof of rollback. The original cutoff
    remains fixed even if later inbox events become visible.
    """
    if not request_ok(open_ref,case_ref,store_ref,actor_ref,role,
                      allowed_stores,expected):
        return result('DENIED','INVALID_REQUEST')
    if role!='OWNER':
        return result('DENIED','NOT_CURRENT_OWNER')
    try:
        k=case_row(c,case_ref)
        if not k or k['store_ref']!=store_ref:
            return result('DENIED','SCOPE_DENIED')
        if k['owner_ref']!=actor_ref or any(k[x]!=expected[x] for x in
              ('case_revision','assignment_revision')):
            return result('DENIED','STALE_OR_REASSIGNED')
        attempt=c.execute('SELECT * FROM s0_frontend_lab.open_attempts '
            'WHERE open_ref=%s FOR SHARE',(open_ref,)).fetchone()
        if not attempt:
            return result('LAB_COMMIT_UNRESOLVED','NO_READBACK_RECORD',
                read_confirmation_state='UNKNOWN',
                display_read_confirmed=False)
        if (attempt['case_ref']!=case_ref or
            attempt['store_ref']!=store_ref or
            attempt['owner_ref']!=actor_ref or
            any(attempt[x]!=expected[x] for x in REV)):
            return result('DENIED','OPEN_REF_COLLISION')
        checkpoint=attempt['read_through_seq']
        actual=cursor(c,case_ref,actor_ref)
        if actual<checkpoint:
            return result('DENIED','CURSOR_INCONSISTENT')
        snapshot=attention(k,events(c,case_ref),actual)
        # Even if other legitimate opens advanced the cursor, this attempt
        # proves only its own original cutoff, NOT a subsequent message.
        later=any(x['event_kind']=='INBOUND' and x['inbound_visible']
                  and x['event_seq']>checkpoint for x in events(c,case_ref))
        mode='ACTIVE_ACTIONABLE' if k['active'] and k['actionable'] else 'HISTORICAL_READ_ONLY'
        return result('LAB_COMMITTED_READBACK','POST_COMMIT_VISIBLE_IN_PG17',
            open_ref=open_ref,read_confirmation_state='COMMITTED_ORIGINAL_CUTOFF_LAB',
            display_read_confirmed=True,read_through_seq=checkpoint,
            newer_inbound_after_open=later,
            conversation_mode=mode,
            composer_enabled=bool(mode=='ACTIVE_ACTIONABLE'),
            unread_inbound_count=snapshot['unread_inbound_count'],
            human_reply_pending=snapshot['human_reply_pending'],
            last_activity_at=snapshot['last_activity_at'],
            activity_time_state=snapshot['activity_time_state'],
            current_inbox_revision=k['inbox_revision'])
    except Exception:
        return result('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def owner_history(c,*,store_ref,actor_ref,role,allowed_stores):
    """Read-only projection for archived/non-actionable conversations.

    Scopes strictly to current owner in the requested store, never a
    supervisor aggregation or a whole-store history browser.
    """
    if not scope(store_ref,actor_ref,role,allowed_stores) or role!='OWNER':
        return result('DENIED','SCOPE_DENIED')
    try:
        ks=c.execute('SELECT * FROM s0_frontend_lab.cases '
            'WHERE store_ref=%s AND owner_ref=%s '
            'AND (active=false OR actionable=false) '
            'ORDER BY case_ref FOR SHARE',(store_ref,actor_ref)).fetchall()
        rows=[]
        for k in ks:
            a=attention(k,events(c,k['case_ref']),
                        cursor(c,k['case_ref'],actor_ref))
            rows.append(dict(case_ref=k['case_ref'],
                assignment_revision=k['assignment_revision'],
                case_revision=k['case_revision'],
                inbox_revision=k['inbox_revision'],
                **a,historical_read_only=True,composer_enabled=False))
        rows.sort(key=lambda x:x['case_ref'])
        rows.sort(key=lambda x:(x['last_activity_at'] is not None,
                 x['last_activity_at'] or ''),reverse=True)
        return result('LAB_HISTORY_OWNER_PROJECTION','HISTORY_NO_COMPOSER',
            rows=rows,unknown_clock_rows=sum(x['last_activity_at'] is None
                                             for x in rows))
    except Exception:
        return result('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
