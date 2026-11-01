"""S0 F02 PG17 disposable planner port. No model, Graph, scheduling or send.

Uses the earlier S0 M09 route lock and PRE_DISPATCH LAB fixture sources only.
Private OFF04 envelope contains protected host identifiers and MUST remain
inside the trusted S0 test process; only f02ProviderView may leave it.
All authenticated/approved fields in OFF04 are explicit LAB assertions.
"""
from __future__ import annotations

from datetime import timedelta, timezone
from hashlib import sha256
import json
import re
import secrets

from integration.s0s1_m09_registry.pg17_use_check import (
    record_control_check_in_admin_transaction as m09_check,
)
from integration.s0s1_m09_registry.port import HostScope,M2MPrincipal,Revisions

VER_KEYS=('case','cycle','catalog','assignment','policy','consent','chain')
REQ_KEYS=frozenset({
 'request_ref','case_ref','service_ref','purpose_ref','consent_purpose_ref',
 'owner_route','instructions_text','instructions_version',
 'start_after_seconds','duration_minutes','max_attempts'
})
ID=re.compile(r'^[A-Za-z0-9_.:-]{1,120}$')
V='prumo.s0.f02.request-persistence/0.1-lab'
P='prumo.openai.f02-plan-private/0.1-candidate'


def enc(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),
                      ensure_ascii=True,allow_nan=False).encode('ascii')


def fingerprint(x):
    return sha256(enc(x)).hexdigest()


def ident(x):
    return type(x) is str and bool(ID.fullmatch(x))


def version(x):
    return type(x) is int and 0<=x<2**63-1


def result(status,reason,private=None):
    return {'contract_version':V,'decision':status,'reason':reason,
            'private':private,'send_authorized':False,
            'schedule_authorized':False,'production_authorized':False,
            'provider_approval_verified':False,
            'consent_source_authenticated':False,
            'm2m_operationally_verified':False}


class Rejected(Exception):
    def __init__(self,why):
        self.why=why


def require(ok,why):
    if not ok:
        raise Rejected(why)


def _ms(dt):
    # OFF04 accepts at most millisecond precision; persist exactly that unit.
    return dt.replace(microsecond=(dt.microsecond//1000)*1000)


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat(
        timespec='milliseconds').replace('+00:00','Z')


def _validate_input(q,s,p,m,expected):
    if (type(q) is not dict or set(q)!=REQ_KEYS or
        type(s) is not HostScope or type(p) is not M2MPrincipal or
        type(m) is not Revisions or type(expected) is not dict or
        set(expected)!=set(VER_KEYS)):
        return False
    return (all(ident(q[k]) for k in REQ_KEYS-{
                'start_after_seconds','duration_minutes','max_attempts',
                'instructions_text'})
        and type(q['instructions_text']) is str
        and 1<=len(q['instructions_text'])<=1800
        and not any(v in q['instructions_text'] for v in (
            s.concessionaria_id,s.app_ref,s.canal_id,
            q['case_ref'],s.phone_number_id))
        and type(q['start_after_seconds']) is int
        and 1<=q['start_after_seconds']<=3600
        and type(q['duration_minutes']) is int
        and 1<=q['duration_minutes']<=1440
        and type(q['max_attempts']) is int
        and 0<=q['max_attempts']<=16
        and q['owner_route'] in ('human','seller_ai')
        and q['service_ref']==p.principal_ref
        and all(version(expected[k]) for k in VER_KEYS))


def _sources(c,q,s,p,expected):
    # Must be called AFTER M09 route lock under one transaction. The case
    # UPDATE lock serializes compliant consent/suppression policy changes.
    case=c.execute('SELECT * FROM s0_pre_dispatch_lab.cases '
                   'WHERE case_ref=%s FOR UPDATE',(q['case_ref'],)).fetchone()
    require(case and case['active'] and not case['global_opt_out'],
            'POLICY_DENIED')
    require(case['concessionaria_id']==s.concessionaria_id
            and case['app_ref']==s.app_ref and case['route_ref']==s.route_ref
            and case['canal_id']==s.canal_id and case['waba_id']==s.waba_id
            and case['principal_ref']==p.principal_ref,'SCOPE_CHANGED')
    # F02 cycle and assignment are independent, separately persisted
    # revision sources. Do not alias one to the other's physical column.
    cycle=c.execute(
        'SELECT cycle_revision,flow_ref FROM s0_f02_lab.case_cycles '
        'WHERE case_ref=%s FOR UPDATE',(q['case_ref'],)).fetchone()
    require(cycle is not None and cycle['flow_ref']=='flow_A',
            'CYCLE_SOURCE_MISSING_OR_CHANGED')
    require(case['case_revision']==expected['case']
            and cycle['cycle_revision']==expected['cycle']
            and case['assignment_revision']==expected['assignment']
            and case['policy_revision']==expected['policy'],
            'STALE_OR_CHANGED')

    consent=c.execute(
        'SELECT * FROM s0_pre_dispatch_lab.consents '
        'WHERE case_ref=%s AND purpose_ref=%s FOR UPDATE',
        (q['case_ref'],q['consent_purpose_ref'])).fetchone()
    require(consent and consent['state']=='GRANTED','CONSENT_DENIED')
    require(consent['revision']==expected['consent'],'STALE_OR_CHANGED')
    suppression=c.execute(
        'SELECT purpose_ref,active FROM s0_pre_dispatch_lab.suppressions '
        'WHERE case_ref=%s ORDER BY purpose_ref FOR UPDATE',
        (q['case_ref'],)).fetchall()
    require(not any(x['active'] and x['purpose_ref'] in (
        '*',q['consent_purpose_ref']) for x in suppression),'SUPPRESSED')

    # Deterministic order for alias generation, explicit proof of campaign
    # and grant for EACH candidate; never use an M15 preview as a grant.
    candidates=c.execute("""
        SELECT t.template_ref,t.template_version,t.template_purpose_ref,
          t.consent_purpose_ref,t.revision,t.valid_until,t.active,
          t.provider_approved,t.media_verified,t.concessionaria_id,t.waba_id,
          g.service_ref,g.revision AS grant_revision,g.active AS grant_active,
          cp.active AS campaign_active,cp.eligible AS campaign_eligible
        FROM s0_pre_dispatch_lab.templates t
        JOIN s0_pre_dispatch_lab.campaigns cp
          ON cp.template_ref=t.template_ref
         AND cp.template_version=t.template_version
         AND cp.case_ref=%s
        JOIN s0_pre_dispatch_lab.grants g
          ON g.case_ref=%s
         AND g.campaign_ref=cp.campaign_ref
         AND g.template_ref=t.template_ref
         AND g.template_version=t.template_version
        WHERE t.concessionaria_id=%s AND t.waba_id=%s
          AND t.template_purpose_ref=%s
          AND t.consent_purpose_ref=%s
          AND g.service_ref=%s
        ORDER BY t.template_ref,t.template_version,cp.campaign_ref
        FOR SHARE OF t,cp,g
    """,(q['case_ref'],q['case_ref'],s.concessionaria_id,s.waba_id,
         q['purpose_ref'],q['consent_purpose_ref'],p.principal_ref)).fetchall()
    require(0<len(candidates)<=32,'NO_ELIGIBLE_CATALOG')
    now=c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
    require(consent['valid_until']>now,'EXPIRED')
    filtered=[]
    seen=set()
    for t in candidates:
        key=(t['template_ref'],t['template_version'])
        require(key not in seen,'AMBIGUOUS_CATALOG')
        seen.add(key)
        require(t['active'] and t['provider_approved']
                and t['media_verified'] and t['grant_active']
                and t['campaign_active'] and t['campaign_eligible'],
                'CATALOG_NOT_VERIFIED')
        require(t['valid_until']>now,'EXPIRED')
        require(t['revision']==expected['catalog'] and
                t['grant_revision']==expected['chain'],'STALE_OR_CHANGED')
        filtered.append(t)
    return case,consent,filtered,now


def _private(q,s,expected,templates,provider_tag,now,deadline):
    # Private refs are deliberately synthetic opaque references; this
    # function does NOT create a signed S0 authorization for OpenAI.
    return {
        'schemaVersion':P,
        'requestId':q['request_ref'],'providerTag':provider_tag,
        'nowMs':int(now.timestamp()*1000),
        'deadlineMs':int(deadline.timestamp()*1000),
        'scope':{
            'authenticated':True,'authorized':True,'tenantAllowed':True,
            'storeId':s.concessionaria_id,'caseId':q['case_ref'],
            'personId':'synthetic_person_01',
            'expectedVersions':expected,'currentVersions':dict(expected)
        },
        'request':{
            'explicitS0Request':True,'optOut':False,
            'ownerRoute':q['owner_route'],'purpose':q['purpose_ref'],
            'handoffDefinitive':False,'priorAiPlanCancelled':False,
            'windowStart':_iso(now+timedelta(seconds=q['start_after_seconds'])),
            'windowEnd':_iso(now+timedelta(seconds=q['start_after_seconds'],
                                          minutes=q['duration_minutes'])),
            'maxAttempts':q['max_attempts'],
            'templates':[
              {'id':t['template_ref'],'version':t['template_version'],
               'storeId':s.concessionaria_id,'purpose':q['purpose_ref'],
               'category':'UTILITY','active':True,'approved':True,
               'eligible':True}
              for t in templates
            ],
            'instructions':{'text':q['instructions_text'],
                            'version':q['instructions_version']},
            'privateRefs':{
                'consentRef':'synthetic_consent',
                'authorizationRef':'synthetic_authorization',
                'sessionRef':'synthetic_session',
                's0EvidenceRef':'synthetic_evidence'
            },
            'continuity':{
                'chainRef':'synthetic_chain',
                'chainVersion':expected['chain'],
                'previousPlanRef':None,'revision':1
            }
        }
    }


def prepare_in_admin_transaction(c,q,*,scope,principal,m09_versions,expected):
    """Returns a *private laboratory* OFF-04 envelope. Caller owns COMMIT."""
    if not _validate_input(q,scope,principal,m09_versions,expected):
        return result('DENIED','INVALID_REQUEST')
    c.execute('SAVEPOINT s0_f02_create')
    try:
        attempt=m09_check(c,scope=scope,principal=principal,
                          expected=m09_versions,
                          attempt_ref='f02.'+q['request_ref'])
        require(attempt['decision']=='LAB_CHECK_RECORDED_NO_USE' or
                attempt['reason']=='DUPLICATE_ATTEMPT','M09_STALE_OR_REVOKED')
        case,consent,templates,now=_sources(c,q,scope,principal,expected)
        # Enforce caller-supplied intent rather than deriving a Meta 24h rule.
        deadline=now+timedelta(seconds=30)
        binding={
            'request':q,'versions':expected,
            'scope':{
                'store':scope.concessionaria_id,'app':scope.app_ref,
                'route':scope.route_ref,'channel':scope.canal_id,
                'phone':scope.phone_number_id,'waba':scope.waba_id
            },
            'catalog':[(t['template_ref'],t['template_version'],
                        t['revision'],t['grant_revision']) for t in templates],
        }
        digest=fingerprint(binding)
        prior=c.execute('SELECT * FROM s0_f02_lab.requests '
                        'WHERE request_ref=%s FOR UPDATE',
                        (q['request_ref'],)).fetchone()
        if prior:
            require(prior['fingerprint']==digest,'REQUEST_COLLISION')
            require(prior['deadline_at']>now,'EXPIRED')
            # Exact retry preserves provider tag AND original plan window.
            private=_private(q,scope,dict(expected),templates,
                             prior['provider_tag'],
                             prior['window_start']-timedelta(
                                seconds=q['start_after_seconds']),
                             prior['deadline_at'])
            c.execute('RELEASE SAVEPOINT s0_f02_create')
            return result('LAB_REQUEST_REPLAY_REVIEW_ONLY','EXACT_REPLAY',private)
        tag='opaque_'+secrets.token_urlsafe(20)
        source_hash=fingerprint(binding['catalog'])
        c.execute("""
          INSERT INTO s0_f02_lab.requests
            (request_ref,provider_tag,fingerprint,case_ref,concessionaria_id,
             app_ref,principal_ref,purpose_ref,consent_purpose_ref,
             owner_route,plan_revision,case_revision,cycle_revision,
             assignment_revision,policy_revision,consent_revision,
             template_revision,grant_revision,
             source_sha256,window_start,window_end,deadline_at,max_attempts)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                   %s,%s,%s,%s,%s,%s,%s)
        """,(q['request_ref'],tag,digest,q['case_ref'],
             scope.concessionaria_id,scope.app_ref,principal.principal_ref,
             q['purpose_ref'],q['consent_purpose_ref'],q['owner_route'],
             1,expected['case'],expected['cycle'],expected['assignment'],
             expected['policy'],expected['consent'],expected['catalog'],expected['chain'],
             source_hash,
             _ms(now+timedelta(seconds=q['start_after_seconds'])),
             _ms(now+timedelta(seconds=q['start_after_seconds'],
                            minutes=q['duration_minutes'])),
             deadline,q['max_attempts']))
        for i,t in enumerate(templates,1):
            c.execute("""
              INSERT INTO s0_f02_lab.aliases
               (request_ref,alias,template_ref,version_ref,template_revision)
              VALUES(%s,%s,%s,%s,%s)
            """,(q['request_ref'],f'tpl_{i:03d}',t['template_ref'],
                 t['template_version'],t['revision']))
        saved=c.execute(
            'SELECT request_ref,provider_tag FROM s0_f02_lab.requests '
            'WHERE request_ref=%s FOR SHARE',(q['request_ref'],)).fetchone()
        require(saved and saved['provider_tag']==tag,'READBACK_UNAVAILABLE')
        private=_private(q,scope,dict(expected),templates,tag,now,deadline)
        c.execute('RELEASE SAVEPOINT s0_f02_create')
        return result('LAB_REQUEST_RECORDED_NO_MODEL', 'PRIVATE_ONLY',private)
    except Rejected as e:
        c.execute('ROLLBACK TO SAVEPOINT s0_f02_create')
        c.execute('RELEASE SAVEPOINT s0_f02_create')
        return result('DENIED',e.why)
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT s0_f02_create')
        c.execute('RELEASE SAVEPOINT s0_f02_create')
        return result('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')


def review_in_admin_transaction(c,proposal,*,q,scope,principal,m09_versions,
                                expected):
    """Internal S0 only: require old original model result + NEW source check.
    Return only REVIEW_ONLY; no send, timer, reservation or business effect.
    """
    if (type(proposal) is not dict or
        set(proposal)!={'status','schemaVersion','requestId','chainRef',
                        'expectedVersions','attempts','finalTemplate',
                        'sendAuthorized','schedulingAuthorized',
                        'commercialTransitionAuthorized'}
        or proposal['status']!='S0_RECHECK_ONLY'
        or proposal['schemaVersion']!='prumo.openai.f02-plan-candidate/0.1'
        or proposal['requestId']!=q.get('request_ref')
        or type(proposal['expectedVersions']) is not dict
        or proposal['expectedVersions']!=expected
        or any(proposal[k] is not False for k in (
            'sendAuthorized','schedulingAuthorized',
            'commercialTransitionAuthorized'))
        or type(proposal['attempts']) is not list or
        not 0<=len(proposal['attempts'])<=16
        or not _validate_input(q,scope,principal,m09_versions,expected)):
        return result('DENIED','INVALID_PROPOSAL')
    c.execute('SAVEPOINT s0_f02_review')
    try:
        technical=m09_check(c,scope=scope,principal=principal,
                          expected=m09_versions,
                          attempt_ref='f02.review.'+q['request_ref'])
        require(technical['decision']=='LAB_CHECK_RECORDED_NO_USE' or
                technical['reason']=='DUPLICATE_ATTEMPT','M09_STALE_OR_REVOKED')
        case,consent,templates,now=_sources(c,q,scope,principal,expected)
        saved=c.execute('SELECT * FROM s0_f02_lab.requests '
            'WHERE request_ref=%s FOR UPDATE',(q['request_ref'],)).fetchone()
        require(saved and saved['deadline_at']>now
                and saved['case_ref']==q['case_ref']
                and saved['purpose_ref']==q['purpose_ref']
                and saved['consent_purpose_ref']==q['consent_purpose_ref']
                and saved['principal_ref']==principal.principal_ref,
                'STALE_OR_CHANGED')
        # Durable readback must preserve the independently resolved revision.
        require(saved['case_revision']==expected['case']
                and saved['cycle_revision']==expected['cycle']
                and saved['assignment_revision']==expected['assignment']
                and saved['policy_revision']==expected['policy']
                and saved['consent_revision']==expected['consent']
                and saved['template_revision']==expected['catalog']
                and saved['grant_revision']==expected['chain'],
                'STALE_OR_CHANGED')
        require(saved['fingerprint']==fingerprint({
            'request':q,'versions':expected,
            'scope':{'store':scope.concessionaria_id,'app':scope.app_ref,
                     'route':scope.route_ref,'channel':scope.canal_id,
                     'phone':scope.phone_number_id,'waba':scope.waba_id},
            'catalog':[(t['template_ref'],t['template_version'],
                        t['revision'],t['grant_revision']) for t in templates]
        }), 'STALE_OR_CHANGED')
        # Durable aliases are the authority for translating OFF04 proposals.
        # A changed or incomplete map is NOT silently rebuilt or accepted.
        stored_aliases=c.execute(
            'SELECT alias,template_ref,version_ref,template_revision '
            'FROM s0_f02_lab.aliases WHERE request_ref=%s '
            'ORDER BY alias FOR SHARE',(q['request_ref'],)).fetchall()
        expected_aliases=[(
            f'tpl_{i:03d}',t['template_ref'],t['template_version'],
            t['revision']) for i,t in enumerate(templates,1)]
        require([
            (a['alias'],a['template_ref'],a['version_ref'],
             a['template_revision']) for a in stored_aliases
        ]==expected_aliases,'ALIAS_CHANGED')
        require(proposal['chainRef']=='synthetic_chain',
                'INVALID_PROPOSAL')
        require(len(proposal['attempts'])<=saved['max_attempts'],
                'INVALID_PROPOSAL')
        tuples={(t['template_ref'],t['template_version']) for t in templates}
        rows=proposal['attempts']+(
            [] if proposal['finalTemplate'] is None
            else [proposal['finalTemplate']])
        prev_ms=int(saved['window_start'].timestamp()*1000)-1
        for a in rows:
            require(type(a) is dict and
              set(a)=={'templateId','templateVersion','purpose','at'}
              and (a['templateId'],a['templateVersion']) in tuples
              and a['purpose']==q['purpose_ref']
              and type(a['at']) is str,'INVALID_PROPOSAL')
            from datetime import datetime
            try:
                at=datetime.fromisoformat(a['at'].replace('Z','+00:00'))
                ms=int(at.timestamp()*1000)
            except (ValueError,TypeError,OverflowError):
                raise Rejected('INVALID_PROPOSAL')
            require(prev_ms<ms and
                saved['window_start']<=at<=saved['window_end'],
                'INVALID_PROPOSAL')
            prev_ms=ms
        digest=fingerprint(proposal)
        prior=c.execute('SELECT * FROM s0_f02_lab.reviews '
                        'WHERE request_ref=%s FOR UPDATE',
                        (q['request_ref'],)).fetchone()
        if prior:
            require(prior['plan_fingerprint']==digest,'PROPOSAL_CONFLICT')
            decision='LAB_ALREADY_REVIEWED_NO_EFFECT'
            reason='EXACT_REPLAY'
        else:
            c.execute(
              'INSERT INTO s0_f02_lab.reviews(request_ref,plan_fingerprint) '
              'VALUES(%s,%s)',(q['request_ref'],digest))
            decision='LAB_PROPOSAL_RECORDED_REVIEW_ONLY'
            reason='S0_RECHECK_FOR_FUTURE_ONLY'
        c.execute('RELEASE SAVEPOINT s0_f02_review')
        return result(decision,reason)
    except Rejected as e:
        c.execute('ROLLBACK TO SAVEPOINT s0_f02_review')
        c.execute('RELEASE SAVEPOINT s0_f02_review')
        return result('DENIED',e.why)
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT s0_f02_review')
        c.execute('RELEASE SAVEPOINT s0_f02_review')
        return result('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
