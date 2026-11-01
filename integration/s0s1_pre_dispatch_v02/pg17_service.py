"""PRE_DISPATCH v0.2: durable lab receipt, quota accounting and readback.

NOT an operational lease. Host and M2M principals are test-fixture objects,
not authenticated production identities. No Graph, send, tokens or HTTP.
"""
from __future__ import annotations
import hashlib,json,re
from datetime import datetime,timezone
from integration.s0s1_pre_dispatch.pg17_service import (
 reserve_in_admin_transaction as original,_FIELDS as CORE_FIELDS,
 _REVISIONS as CORE_REV, _id as ident)
from integration.s0s1_m09_registry.port import HostScope,M2MPrincipal,Revisions

VERSION='prumo.s0.pre-dispatch.readback/0.2-lab'
EXTRAS={'intent_ref','nonce','destination_sha256','body_sha256',
        'window_ref','expected_quota_revision','expires_ms','max_age_ms'}
HEX=re.compile(r'^[0-9a-f]{64}$')
FLAGS=dict(lab_only=True,host_authenticated=False,
  consent_source_authenticated=False,m09_host_authenticated=False,
  provider_approval_verified=False,external_lease_issued=False,
  graph_dispatch_authorized=False,send_authorized=False,
  automatic_retry_authorized=False,ack_allowed=False,
  production_authorized=False,commercial_transition_authorized=False)
def out(status,reason,**extras):
 return dict(contract_version=VERSION,status=status,reason=reason,
             **FLAGS,**extras)
def sha(payload):
 return hashlib.sha256(json.dumps(payload,sort_keys=True,
   separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def scope_material(scope,principal,versions):
 return {'route_ref':scope.route_ref,'store_ref':scope.concessionaria_id,
   'app_ref':scope.app_ref,'channel_ref':scope.canal_id,
   'waba_ref':scope.waba_id,'phone_ref':scope.phone_number_id,
   'principal_ref':principal.principal_ref,'issuer_ref':principal.issuer_ref,
   'key_revision':principal.key_revision,
   'm09_revisions':dict(route=versions.route,app=versions.app,
     binding=versions.binding,grant=versions.grant,principal=versions.principal)}
def validate(req,scope,principal,versions):
 return (type(req) is dict and set(req)==CORE_FIELDS|EXTRAS
  and type(scope) is HostScope and type(principal) is M2MPrincipal
  and type(versions) is Revisions
  and all(ident(req[k]) for k in CORE_FIELDS-set(CORE_REV))
  and all(type(req[k]) is int and 0<req[k]<2**63-1 for k in CORE_REV)
  and all(ident(req[k]) for k in ('intent_ref','window_ref'))
  and type(req['nonce']) is str and 8<=len(req['nonce'])<=120
  and bool(re.fullmatch('[A-Za-z0-9_.:-]+',req['nonce']))
  and all(type(req[k]) is str and HEX.fullmatch(req[k]) for k in
          ('destination_sha256','body_sha256'))
  and all(type(req[k]) is int and req[k]>0 for k in (
       'expected_quota_revision','expires_ms','max_age_ms'))
  and req['max_age_ms']<=120000
  and req['service_ref']==principal.principal_ref
  and all(ident(v) for v in (scope.route_ref,scope.app_ref,
    scope.concessionaria_id,scope.canal_id,scope.waba_id,
    scope.phone_number_id,principal.principal_ref))
  and re.fullmatch(r'\d{5,25}',scope.phone_number_id) is not None)

def reserve(c,request,*,scope,principal,m09_versions):
 """One caller-owned transaction, complete savepoint rollback on any denial."""
 if not validate(request,scope,principal,m09_versions):
  return out('DENIED','INVALID_REQUEST')
 core={k:request[k] for k in CORE_FIELDS}
 identity=scope_material(scope,principal,m09_versions)
 fingerprint=sha({'request':request,'scope':identity})
 scphash=sha(identity)
 sp='pd_v02_reserve'
 c.execute('SAVEPOINT '+sp)
 try:
  # Idempotent replay never consumes quota and NEVER implies COMMIT.
  prior=c.execute('SELECT * FROM s0_pd_v02_lab.receipts '
     'WHERE attempt_ref=%s OR selection_ref=%s OR intent_ref=%s OR nonce=%s '
     'FOR SHARE',(request['attempt_ref'],request['selection_ref'],
       request['intent_ref'],request['nonce'])).fetchall()
  if prior:
   if (len(prior)==1 and prior[0]['attempt_ref']==request['attempt_ref']
       and prior[0]['request_digest']==fingerprint
       and prior[0]['scope_digest']==scphash
       and prior[0]['state']=='LAB_HELD_NO_DISPATCH'):
    c.execute('RELEASE SAVEPOINT '+sp)
    return out('LAB_REPLAY_REQUIRES_READBACK','NO_COMMIT_ASSERTION',
       original_attempt_ref=request['attempt_ref'],commit_verified=False)
   raise ValueError('REPLAY_OR_SCOPE_COLLISION')
  now=c.execute('SELECT clock_timestamp() AS t').fetchone()['t']
  now_ms=int(now.timestamp()*1000)
  if not now_ms<request['expires_ms']<=now_ms+120000:
   raise ValueError('EXPIRED_OR_UNBOUNDED')
  # Original M09+consent/template/grant/campaign/CAS and physical
  # reservation are performed in this SAME transaction.
  first=original(c,core,scope=scope,principal=principal,
       m09_versions=m09_versions)
  if first['decision']!='LAB_RESERVATION_RECORDED_NO_DISPATCH':
   raise ValueError('BASE_'+first['reason'])
  quota=c.execute('SELECT * FROM s0_pd_v02_lab.quotas '
     'WHERE store_ref=%s AND app_ref=%s AND phone_ref=%s AND window_ref=%s '
     'FOR UPDATE',(scope.concessionaria_id,scope.app_ref,
                   scope.phone_number_id,request['window_ref'])).fetchone()
  if not quota or not quota['enabled']:
   raise ValueError('QUOTA_MISSING_OR_DISABLED')
  if quota['revision']!=request['expected_quota_revision']:
   raise ValueError('QUOTA_STALE')
  if not quota['observed_at']<=now<quota['valid_until']:
   raise ValueError('QUOTA_WINDOW_EXPIRED')
  if int((now-quota['observed_at']).total_seconds()*1000)>request['max_age_ms']:
   raise ValueError('QUOTA_OBSERVATION_STALE')
  if quota['consumed']>=quota['capacity']:
   raise ValueError('QUOTA_EXHAUSTED')
  row=c.execute('UPDATE s0_pd_v02_lab.quotas '
     'SET consumed=consumed+1 WHERE store_ref=%s AND app_ref=%s '
     'AND phone_ref=%s AND window_ref=%s AND revision=%s '
     'AND consumed<capacity RETURNING consumed',
     (scope.concessionaria_id,scope.app_ref,scope.phone_number_id,
      request['window_ref'],quota['revision'])).fetchone()
  if not row:raise ValueError('QUOTA_RACE')
  snap={k:request[k] for k in CORE_REV}
  c.execute('INSERT INTO s0_pd_v02_lab.receipts '
    '(attempt_ref,selection_ref,intent_ref,nonce,request_digest,scope_digest,'
    'store_ref,app_ref,route_ref,channel_ref,phone_ref,waba_ref,case_ref,'
    'service_ref,consent_purpose_ref,template_ref,template_version,campaign_ref,'
    'destination_sha256,body_sha256,expected_versions,m09_versions,'
    'window_ref,quota_revision,quota_observed_at,quota_valid_until,quota_slot,expires_at) VALUES '
    '(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'
    'to_timestamp(%s/1000.0))',
    (request['attempt_ref'],request['selection_ref'],request['intent_ref'],
     request['nonce'],fingerprint,scphash,
     scope.concessionaria_id,scope.app_ref,scope.route_ref,scope.canal_id,
     scope.phone_number_id,scope.waba_id,request['case_ref'],
     principal.principal_ref,request['consent_purpose_ref'],
     request['template_ref'],request['template_version'],
     request['campaign_ref'],request['destination_sha256'],
     request['body_sha256'],json.dumps(snap),
     json.dumps(identity['m09_revisions']),request['window_ref'],
     quota['revision'],quota['observed_at'],quota['valid_until'],
     row['consumed'],request['expires_ms']))
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('LAB_RESERVATION_STAGED_BEFORE_COMMIT','READBACK_REQUIRED',
    commit_verified=False,quota_slot_recorded_lab_only=row['consumed'])
 except ValueError as e:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('DENIED',str(e))
 except Exception:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def cancel(c,*,attempt_ref,scope,principal=None,m09_versions=None,
           reason='CANCELLED_BY_S0_LAB'):
 """Full-scoped fixture cancel, not authenticated host authority.

 The original issuer, key revision and five registry revisions are bound
 by the immutable receipt digest. Revoked sources can still be cancelled,
 but a caller missing the ORIGINAL signed scope cannot cancel another.
 """
 if (not ident(attempt_ref) or type(scope) is not HostScope
     or type(principal) is not M2MPrincipal or type(m09_versions) is not Revisions
     or reason not in ('CANCELLED_BY_S0_LAB','REVOKED_BY_S0_LAB')):
  return out('DENIED','INVALID_REQUEST')
 sp='pd_v02_cancel'
 c.execute('SAVEPOINT '+sp)
 try:
  x=c.execute('SELECT * FROM s0_pd_v02_lab.receipts '
    'WHERE attempt_ref=%s FOR UPDATE',(attempt_ref,)).fetchone()
  if not x or any(x[col]!=want for col,want in (
     ('store_ref',scope.concessionaria_id),('app_ref',scope.app_ref),
     ('route_ref',scope.route_ref),('channel_ref',scope.canal_id),
     ('phone_ref',scope.phone_number_id),('waba_ref',scope.waba_id),
     ('service_ref',principal.principal_ref))) or (
     x['scope_digest']!=sha(scope_material(scope,principal,m09_versions))):
   raise ValueError('SCOPE_DENIED')
  if x['state']!='LAB_CANCELLED_NO_DISPATCH':
   c.execute('UPDATE s0_pd_v02_lab.receipts '
     'SET state=%s,cancel_reason=%s WHERE attempt_ref=%s',
     ('LAB_CANCELLED_NO_DISPATCH',reason,attempt_ref))
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('LAB_CANCEL_STAGED_BEFORE_COMMIT','READBACK_REQUIRED',
    commit_verified=False)
 except ValueError as e:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('DENIED',str(e))
 except Exception:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')

def readback(c,request,*,scope,principal,m09_versions):
 """Must be called with a NEW connection after original COMMIT.

 Even when durable: no operational lease, no Graph authority. Recheck
 revisions and redaction only; signatures/consent provenance still fixtures.
 """
 if not validate(request,scope,principal,m09_versions):
  return out('DENIED','INVALID_REQUEST')
 fp=sha({'request':request,'scope':
         scope_material(scope,principal,m09_versions)})
 try:
  receipt=c.execute('SELECT * FROM s0_pd_v02_lab.receipts '
    'WHERE attempt_ref=%s',(request['attempt_ref'],)).fetchone()
  if not receipt:
   return out('LAB_COMMIT_UNKNOWN','NO_DURABLE_RECEIPT',
       commit_verified=False,external_retry_suppressed=True)
  if receipt['request_digest']!=fp or (
      receipt['scope_digest']!=sha(scope_material(scope,principal,m09_versions))):
   return out('DENIED','SCOPE_OR_PAYLOAD_COLLISION',commit_verified=False)
  original=c.execute('SELECT * FROM s0_pre_dispatch_lab.reservations '
     'WHERE attempt_ref=%s',(request['attempt_ref'],)).fetchone()
  if not original or original['selection_ref']!=request['selection_ref'] or (
     original['state']!='LAB_HELD_NO_DISPATCH'):
   return out('LAB_INVALIDATED_NO_DISPATCH','MISSING_OR_REVOKED_BASE',
     commit_verified=True)
  if receipt['state']!='LAB_HELD_NO_DISPATCH':
   return out('LAB_CANCELLED_NO_DISPATCH','CANCELLED_OR_REVOKED',
     commit_verified=True)
  now=c.execute('SELECT clock_timestamp() AS t').fetchone()['t']
  if now>=receipt['expires_at']:
   return out('LAB_EXPIRED_NO_DISPATCH','DEADLINE_PASSED',commit_verified=True)
  case=c.execute('SELECT * FROM s0_pre_dispatch_lab.cases '
     'WHERE case_ref=%s',(receipt['case_ref'],)).fetchone()
  snap=receipt['expected_versions']
  if (not case or not case['active'] or case['global_opt_out'] or
      case['concessionaria_id']!=scope.concessionaria_id or
      case['app_ref']!=scope.app_ref or case['route_ref']!=scope.route_ref or
      case['waba_id']!=scope.waba_id or case['canal_id']!=scope.canal_id or
      case['principal_ref']!=principal.principal_ref or any(
         case[col]!=snap[field] for col,field in (
         ('case_revision','expected_case_revision'),
         ('assignment_revision','expected_assignment_revision'),
         ('policy_revision','expected_policy_revision'),
         ('suppression_revision','expected_suppression_revision')))):
   return out('LAB_STALE_NO_DISPATCH','CASE_POLICY_STALE',commit_verified=True)
  consent=c.execute('SELECT * FROM s0_pre_dispatch_lab.consents '
    'WHERE case_ref=%s AND purpose_ref=%s',
    (receipt['case_ref'],receipt['consent_purpose_ref'])).fetchone()
  if not consent or consent['revision']!=snap['expected_consent_revision'] or (
     consent['state']!='GRANTED' or now>=consent['valid_until']):
   return out('LAB_STALE_NO_DISPATCH','CONSENT_STALE_OR_REVOKED',commit_verified=True)
  sup=c.execute('SELECT * FROM s0_pre_dispatch_lab.suppressions '
     'WHERE case_ref=%s',(receipt['case_ref'],)).fetchall()
  if any(s['active'] and s['purpose_ref'] in (
       '*',receipt['consent_purpose_ref']) for s in sup):
   return out('LAB_STALE_NO_DISPATCH','SUPPRESSED',commit_verified=True)
  tpl=c.execute('SELECT * FROM s0_pre_dispatch_lab.templates '
    'WHERE template_ref=%s AND template_version=%s',
    (receipt['template_ref'],receipt['template_version'])).fetchone()
  campaign=c.execute('SELECT * FROM s0_pre_dispatch_lab.campaigns '
    'WHERE campaign_ref=%s',(receipt['campaign_ref'],)).fetchone()
  grant=c.execute('SELECT * FROM s0_pre_dispatch_lab.grants '
    'WHERE case_ref=%s AND service_ref=%s AND template_ref=%s '
    'AND template_version=%s AND campaign_ref=%s',
    (receipt['case_ref'],receipt['service_ref'],
     receipt['template_ref'],receipt['template_version'],
     receipt['campaign_ref'])).fetchone()
  if (not tpl or not campaign or not grant or
     not tpl['active'] or not tpl['provider_approved'] or
     not tpl['media_verified'] or now>=tpl['valid_until'] or
     tpl['revision']!=snap['expected_template_revision'] or
     tpl['concessionaria_id']!=scope.concessionaria_id or
     tpl['waba_id']!=scope.waba_id or
     tpl['consent_purpose_ref']!=receipt['consent_purpose_ref'] or
     tpl['template_purpose_ref']!=request['template_purpose_ref'] or
     not campaign['active'] or not campaign['eligible'] or
     campaign['case_ref']!=receipt['case_ref'] or
     campaign['template_ref']!=receipt['template_ref'] or
     campaign['template_version']!=receipt['template_version'] or
     campaign['revision']!=snap['expected_campaign_revision'] or
     not grant['active'] or grant['revision']!=snap['expected_grant_revision'] or
     grant['template_purpose_ref']!=request['template_purpose_ref']):
   return out('LAB_STALE_NO_DISPATCH','TEMPLATE_CAMPAIGN_GRANT_STALE',
     commit_verified=True)
  # Exact original technical route/binding/grant check WITHOUT writing
  # another point-of-use record. The source remains unauthenticated LAB.
  v=receipt['m09_versions']
  route=c.execute('SELECT * FROM s0_meta_lab.routes WHERE id=%s',
                  (scope.route_ref,)).fetchone()
  binding=c.execute('SELECT * FROM s0_meta_lab.bindings '
       'WHERE route=%s AND channel=%s',(scope.route_ref,scope.canal_id)).fetchone()
  app=c.execute('SELECT * FROM s0_m09_lab.apps WHERE app_ref=%s',
                (scope.app_ref,)).fetchone()
  mgrant=c.execute('SELECT * FROM s0_m09_lab.grants WHERE canal_id=%s',
                  (scope.canal_id,)).fetchone()
  mprincipal=c.execute('SELECT * FROM s0_meta_lab.principals WHERE key_id=%s',
                   (principal.principal_ref,)).fetchone()
  # Complete scope/tenant/issuer/validity revalidation, mirroring M09
  # point-of-use WITHOUT creating a second point-of-use check record.
  # Still synthetic and read-only: no operational identity assertion.
  phone_rows=c.execute(
    'SELECT route FROM s0_meta_lab.bindings WHERE phone=%s',
    (scope.phone_number_id,)).fetchall()
  waba_rows=c.execute(
    'SELECT route FROM s0_meta_lab.bindings WHERE waba=%s',
    (scope.waba_id,)).fetchall()
  if any(z is None for z in (route,binding,app,mgrant,mprincipal)) or (
    not route['active'] or route['revision']!=v['route'] or
    route['app']!=scope.app_ref or
    not binding['active'] or binding['revision']!=v['binding'] or
    binding['route']!=scope.route_ref or
    binding['channel']!=scope.canal_id or
    binding['app']!=scope.app_ref or
    binding['phone']!=scope.phone_number_id or
    binding['waba']!=scope.waba_id or
    not mprincipal['active'] or mprincipal['revision']!=v['principal'] or
    mprincipal['issuer']!=principal.issuer_ref or
    principal.key_revision!=v['principal'] or
    mprincipal['route']!=scope.route_ref or
    mprincipal['app']!=scope.app_ref or
    scope.canal_id not in mprincipal['channels'] or
    'REGISTRY_READ' not in mprincipal['scopes'] or
    scope.concessionaria_id not in principal.allowed_stores or
    'REGISTRY_READ' not in principal.allowed_purposes or
    principal.audience!='LAB_S0_M09' or
    binding['tenant']!=mprincipal['tenant'] or
    not app['active'] or app['revision']!=v['app'] or
    app['route_ref']!=scope.route_ref or
    app['concessionaria_id']!=scope.concessionaria_id or
    app['tenant']!=mprincipal['tenant'] or
    not mgrant['active'] or mgrant['revision']!=v['grant'] or
    mgrant['app_ref']!=scope.app_ref or
    mgrant['route_ref']!=scope.route_ref or
    mgrant['waba_id']!=scope.waba_id or
    mgrant['phone_number_id']!=scope.phone_number_id or
    not mprincipal['not_before']<=now<mprincipal['not_after'] or
    not app['valid_from']<=now<app['valid_until'] or
    len(phone_rows)!=1 or not waba_rows or
    any(row['route']!=scope.route_ref for row in waba_rows)):
   return out('LAB_STALE_NO_DISPATCH','M09_STALE_OR_REVOKED',
       commit_verified=True)
  quota=c.execute('SELECT * FROM s0_pd_v02_lab.quotas '
     'WHERE store_ref=%s AND app_ref=%s AND phone_ref=%s '
     'AND window_ref=%s',(scope.concessionaria_id,scope.app_ref,
      scope.phone_number_id,receipt['window_ref'])).fetchone()
  if not quota or not quota['enabled'] or (
    quota['revision']!=receipt['quota_revision'] or
    quota['observed_at']!=receipt['quota_observed_at'] or
    quota['valid_until']!=receipt['quota_valid_until'] or
    quota['consumed']<receipt['quota_slot'] or
    quota['capacity']<receipt['quota_slot'] or
    now>=quota['valid_until']):
   return out('LAB_STALE_NO_DISPATCH','QUOTA_REVOKED_OR_EXPIRED',
     commit_verified=True)
  return out('LAB_COMMITTED_RECEIPT_NO_DISPATCH',
     'DURABLE_PG17_LAB_ONLY_NOT_REDEEMABLE',commit_verified=True,
     quota_slot_recorded_lab_only=receipt['quota_slot'])
 except Exception:
  return out('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
