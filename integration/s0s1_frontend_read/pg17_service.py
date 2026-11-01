"""Disposable S0 PG17 frontend read projection. Test credentials only."""
import re
from datetime import timezone

V='prumo.s0.frontend.attention/0.1-lab'
ID=re.compile(r'^[A-Za-z0-9_.:-]{1,120}$')
REV=('assignment_revision','case_revision','inbox_revision')
def valid(x): return type(x) is str and bool(ID.fullmatch(x))
def reply(decision,reason,**data):
    return dict(contract_version=V,decision=decision,reason=reason,
        lab_only=True,authenticated_operator=False,
        live_event_proof=False,production_authorized=False,
        send_authorized=False,**data)
def scope(store,actor,role,stores):
    return (valid(store) and valid(actor) and role in ('OWNER','SUPERVISOR')
      and type(stores) in (tuple,frozenset) and len(stores)<=20
      and all(valid(s) for s in stores) and store in stores)
def case_row(c,ref):
    return c.execute('SELECT * FROM s0_frontend_lab.cases WHERE case_ref=%s FOR UPDATE',
                     (ref,)).fetchone()
def events(c,ref):
    return c.execute('SELECT event_seq,event_kind,inbound_visible,occurred_at,'
      'source_verified FROM s0_frontend_lab.events WHERE case_ref=%s '
      'ORDER BY event_seq',(ref,)).fetchall()
def cursor(c,ref,owner):
    r=c.execute('SELECT read_through_seq FROM s0_frontend_lab.read_cursors '
      'WHERE case_ref=%s AND owner_ref=%s',(ref,owner)).fetchone()
    return r['read_through_seq'] if r else 0
def attention(k,ev,read):
    inbound=[e for e in ev if e['event_kind']=='INBOUND' and e['inbound_visible']]
    last_in=max((e['event_seq'] for e in inbound),default=0)
    last_reply=max((e['event_seq'] for e in ev
      if e['event_kind']=='HUMAN_REPLY_PUBLISHED' and e['source_verified']),default=0)
    unread=sum(e['event_seq']>read for e in inbound)
    pending=last_in>last_reply
    conv=[e for e in ev if e['event_kind']=='HUMAN_REPLY_PUBLISHED' or
          (e['event_kind']=='INBOUND' and e['inbound_visible'])]
    latest=conv[-1] if conv else None
    known=bool(latest and latest['source_verified'] and latest['occurred_at'])
    when=(latest['occurred_at'].astimezone(timezone.utc)
         .isoformat(timespec='milliseconds').replace('+00:00','Z') if known else None)
    return dict(unread_inbound_count=unread,
        operator_read_confirmed=bool(inbound and read>=last_in),
        human_reply_pending='COUNT' if pending and unread else 'DOT' if pending else 'NONE',
        historical_read_only=not k['actionable'],
        composer_enabled=bool(k['active'] and k['actionable']),
        last_activity_at=when,
        last_activity_cutoff_seq=latest['event_seq'] if known else None,
        activity_time_state='VERIFIED_LAB_ONLY' if known else 'UNKNOWN')
def open_case(c,*,open_ref,case_ref,store_ref,actor_ref,role,allowed_stores,expected):
    if not (scope(store_ref,actor_ref,role,allowed_stores) and
       valid(open_ref) and valid(case_ref) and type(expected) is dict and
       set(expected)==set(REV) and all(type(expected[k]) is int and
       0<expected[k]<2**63-1 for k in REV)):
        return reply('DENIED','INVALID_REQUEST')
    c.execute('SAVEPOINT s0_read')
    try:
        k=case_row(c,case_ref)
        if not k or not k['active'] or k['store_ref']!=store_ref:
            raise ValueError('SCOPE_DENIED')
        if any(k[col]!=expected[col] for col in REV):
            raise ValueError('STALE_OR_REASSIGNED')
        if role=='SUPERVISOR':
            c.execute('RELEASE SAVEPOINT s0_read')
            return reply('SUPERVISORY_VIEW_NO_READ','NO_OWNER_MUTATION')
        if actor_ref!=k['owner_ref']:
            raise ValueError('NOT_CURRENT_OWNER')
        ev=events(c,case_ref)
        seen=c.execute('SELECT * FROM s0_frontend_lab.open_attempts '
            'WHERE open_ref=%s FOR UPDATE',(open_ref,)).fetchone()
        if seen:
            if seen['case_ref']!=case_ref or seen['owner_ref']!=actor_ref or \
               seen['store_ref']!=store_ref or \
               any(seen[col]!=expected[col] for col in REV):
                raise ValueError('OPEN_REF_COLLISION')
            decision='LAB_OPEN_REPLAY_NO_ADDITIONAL_READ'
        else:
            read=max((e['event_seq'] for e in ev if
                e['event_kind']=='INBOUND' and e['inbound_visible']),default=0)
            c.execute('INSERT INTO s0_frontend_lab.read_cursors '
              '(case_ref,owner_ref,read_through_seq) VALUES(%s,%s,%s) '
              'ON CONFLICT(case_ref,owner_ref) DO UPDATE SET '
              'read_through_seq=GREATEST('
              's0_frontend_lab.read_cursors.read_through_seq,EXCLUDED.read_through_seq)',
              (case_ref,actor_ref,read))
            c.execute('INSERT INTO s0_frontend_lab.open_attempts '
              '(open_ref,case_ref,owner_ref,store_ref,assignment_revision,'
              'case_revision,inbox_revision,read_through_seq) '
              'VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
              (open_ref,case_ref,actor_ref,store_ref,*[expected[x] for x in REV],read))
            decision='LAB_READ_RECORDED_BEFORE_COMMIT'
        out=attention(k,ev,cursor(c,case_ref,actor_ref))
        c.execute('RELEASE SAVEPOINT s0_read')
        return reply(decision,'OPEN_TITULAR_ONLY',**out)
    except ValueError as e:
        c.execute('ROLLBACK TO SAVEPOINT s0_read')
        c.execute('RELEASE SAVEPOINT s0_read')
        return reply('DENIED',str(e))
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT s0_read')
        c.execute('RELEASE SAVEPOINT s0_read')
        return reply('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
def owner_queue(c,*,store_ref,actor_ref,role,allowed_stores):
    if not scope(store_ref,actor_ref,role,allowed_stores) or role!='OWNER':
        return reply('DENIED','SCOPE_DENIED')
    try:
        ks=c.execute('SELECT * FROM s0_frontend_lab.cases '
          'WHERE store_ref=%s AND owner_ref=%s AND active=true '
          'ORDER BY case_ref FOR SHARE',(store_ref,actor_ref)).fetchall()
        rows=[]
        for k in ks:
            a=attention(k,events(c,k['case_ref']),cursor(c,k['case_ref'],actor_ref))
            rows.append(dict(case_ref=k['case_ref'],
              assignment_revision=k['assignment_revision'],
              case_revision=k['case_revision'],inbox_revision=k['inbox_revision'],**a))
        rows.sort(key=lambda a:a['case_ref'])
        rows.sort(key=lambda a:(a['last_activity_at'] is not None,
                  a['last_activity_at'] or ''),reverse=True)
        return reply('LAB_OWNER_QUEUE','NO_LIVE_ORIGIN',rows=rows,
            unknown_clock_rows=sum(a['last_activity_at'] is None for a in rows))
    except Exception:
        return reply('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
def manager_summary(c,*,store_ref,actor_ref,role,allowed_stores):
    if not scope(store_ref,actor_ref,role,allowed_stores) or role!='SUPERVISOR':
        return reply('DENIED','SCOPE_DENIED')
    try:
        ks=c.execute('SELECT * FROM s0_frontend_lab.cases '
          'WHERE store_ref=%s AND active=true ORDER BY case_ref FOR SHARE',
          (store_ref,)).fetchall()
        summaries=[attention(k,events(c,k['case_ref']),
                    cursor(c,k['case_ref'],k['owner_ref'])) for k in ks]
        return reply('LAB_MANAGER_MINIMIZED','AGGREGATE_ONLY',
          cases_total=len(ks),
          cases_reply_pending=sum(x['human_reply_pending']!='NONE' for x in summaries),
          cases_unread=sum(x['human_reply_pending']=='COUNT' for x in summaries),
          cases_read_without_reply=sum(x['human_reply_pending']=='DOT' for x in summaries))
    except Exception:
        return reply('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
