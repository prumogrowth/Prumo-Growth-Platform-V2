"""F01 commercial metadata selection; disposable PG17 only, no real prices or publish."""
import hashlib,json,re
from datetime import timezone
from integration.s0s1_f01_ownership.pg17_service import (
 current,permitted,digest as f01_digest,recheck_proposal as f01_review,
 valid_scope,valid_versions)
V='prumo.s0.f01-commercial-sources/0.1-lab'
FLAGS=dict(source_authenticated=False,content_grant_verified=False,
 semantic_support_verified=False,commercial_offer_authorized=False,
 model_content_authorized=False,publish_authorized=False,
 send_authorized=False,production_authorized=False)
ID=re.compile(r'^[A-Za-z0-9_.:-]{1,120}$')
CODE=re.compile(r'^[A-Za-z][A-Za-z0-9_.:-]{0,79}$')
def out(status,reason,**more):
 return dict(contract_version=V,status=status,reason=reason,lab_only=True,
             **FLAGS,**more)
def hashx(x):
 return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),
       ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()
def valid(x):
 return isinstance(x,str) and bool(ID.fullmatch(x))
def valid_claims(xs):
 return type(xs) is list and 1<=len(xs)<=24 and all(
   type(v) is dict and set(v)=={'source_ref','claim_code','usage'}
   and valid(v['source_ref']) and type(v['claim_code']) is str
   and CODE.fullmatch(v['claim_code'])
   and v['usage'] in ('commercial','interpretive') for v in xs) and len({
   (v['source_ref'],v['claim_code'],v['usage']) for v in xs})==len(xs)
def request_ok(ref,scope,versions,grant,claims):
 return (valid(ref) and valid_scope(scope) and valid_versions(versions)
    and type(grant) is int and 0<grant<2**63-1 and valid_claims(claims))
def binding(scope,versions,grant,claims):
 return hashx(dict(scope=scope,versions=versions,grant=grant,
    claims=sorted(claims,key=lambda c:(c['source_ref'],c['claim_code'],c['usage']))))
def fail_if(x,reason):
 if x: raise ValueError(reason)
def read(c,ref,scope,versions,grant,claims):
 k=current(c,scope)
 reason=permitted(k,scope,versions)
 fail_if(reason is not None,reason or 'DENIED')
 ctx=c.execute('SELECT * FROM s0_f01_sources_lab.contexts '
   'WHERE case_ref=%s FOR UPDATE',(scope['case_ref'],)).fetchone()
 fail_if(not ctx or not ctx['active'] or
   ctx['store_ref']!=scope['store_ref'] or
   ctx['person_ref']!=scope['person_ref'],'SCOPE_DENIED')
 for col in ('catalog','knowledge','policy','consent'):
  fail_if(ctx[col+'_revision']!=versions[col],'STALE_VERSIONS')
 fail_if(ctx['grant_revision']!=grant,'STALE_VERSIONS')
 fail_if(ctx['content_policy']!='LAB_ALLOWED' or
         ctx['consent_state']!='LAB_ALLOWED','CONTENT_POLICY_DENIED')
 turn=c.execute('SELECT * FROM s0_f01_lab.turns WHERE turn_ref=%s FOR UPDATE',
                (ref,)).fetchone()
 fail_if(not turn or turn['case_ref']!=scope['case_ref'] or
   turn['service_ref']!=scope['service_ref'] or
   turn['scope_digest']!=f01_digest(dict(scope=scope,versions=versions)) or
   turn['expected_versions']!=versions,'TURN_MISSING_OR_CHANGED')
 now=c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
 fail_if(now>=turn['deadline_at'],'TURN_EXPIRED')
 sources=c.execute('SELECT * FROM s0_f01_sources_lab.sources WHERE case_ref=%s '
    'ORDER BY source_ref FOR SHARE',(scope['case_ref'],)).fetchall()
 fail_if(len(sources)>32,'CATALOG_TOO_LARGE')
 material=[]
 for s in sources:
  fail_if(s['store_ref']!=scope['store_ref'] or
          s['purpose_ref']!=ctx['purpose_ref'],'SCOPE_DENIED')
  codes=s['claim_codes']
  fail_if(type(codes) is not list or len(codes)>30 or
     len(codes)!=len(set(map(str,codes))) or
     any(type(z) is not str or not CODE.fullmatch(z) for z in codes),
     'CATALOG_INVALID')
  material.append(dict(source=s['source_ref'],store=s['store_ref'],
    purpose=s['purpose_ref'],kind=s['kind'],state=s['approval_state'],
    version=s['source_version'],expires=s['valid_until'].isoformat()
       if s['valid_until'] else None,corrected=s['corrected_by_ref'],
    codes=codes,grant=s['content_grant_active'],
    provenance=s['provenance_lab_asserted'],
    minimized=s['minimized_lab_asserted']))
 byref={s['source_ref']:s for s in sources}
 for x in claims:
  s=byref.get(x['source_ref'])
  fail_if(s is None,'SOURCE_NOT_IN_SCOPE')
  fail_if(x['claim_code'] not in s['claim_codes'],'CLAIM_UNSUPPORTED')
  fail_if(s['corrected_by_ref'] is not None,'SOURCE_CORRECTED')
  fail_if(not s['content_grant_active'] or
      not s['provenance_lab_asserted'] or
      not s['minimized_lab_asserted'],'GRANT_OR_PROVENANCE_MISSING')
  if x['usage']=='commercial':
   fail_if(s['kind']!='current','HISTORICAL_CANNOT_OFFER')
   fail_if(s['approval_state']!='APPROVED_ACTIVE','SOURCE_INACTIVE')
   fail_if(s['valid_until'] is None or s['valid_until']<=now,
           'EXPIRED_OR_UNBOUNDED')
  else:
   fail_if(s['approval_state'] not in ('APPROVED_ACTIVE','EXPIRED'),
           'HISTORY_INELIGIBLE')
 return sources,hashx(material)
def aliases(claims):
 names={z:f'src_{i:03d}' for i,z in enumerate(
   sorted({c['source_ref'] for c in claims}),1)}
 return sorted([(names[x['source_ref']],x['source_ref'],
   x['claim_code'],x['usage']) for x in claims])
def provider_rows(claims):
 return [dict(alias=a,claimCode=c,usage=u) for a,s,c,u in aliases(claims)]
def deny(c,savepoint,why):
 c.execute('ROLLBACK TO SAVEPOINT '+savepoint)
 c.execute('RELEASE SAVEPOINT '+savepoint)
 return out('DENIED',why)
def prepare(c,*,request_ref,scope,expected,grant_revision,claims):
 if not request_ok(request_ref,scope,expected,grant_revision,claims):
  return out('DENIED','INVALID_REQUEST')
 sp='f01_sources_prepare'
 c.execute('SAVEPOINT '+sp)
 try:
  sources,digest=read(c,request_ref,scope,expected,grant_revision,claims)
  fp=binding(scope,expected,grant_revision,claims)
  old=c.execute('SELECT * FROM s0_f01_sources_lab.selections '
      'WHERE request_ref=%s FOR UPDATE',(request_ref,)).fetchone()
  if old:
   fail_if(old['request_fingerprint']!=fp,'REQUEST_COLLISION')
   fail_if(old['snapshot_fingerprint']!=digest,'SOURCES_CHANGED')
   saved=c.execute('SELECT alias_ref,source_ref,claim_code,usage FROM '
     's0_f01_sources_lab.aliases WHERE request_ref=%s ORDER BY alias_ref '
     'FOR SHARE',(request_ref,)).fetchall()
   fail_if(sorted((x['alias_ref'],x['source_ref'],x['claim_code'],x['usage'])
     for x in saved)!=aliases(claims),'ALIAS_CHANGED')
   status='LAB_SELECTION_REPLAY_NO_MODEL'
  else:
   c.execute('INSERT INTO s0_f01_sources_lab.selections '
      '(request_ref,case_ref,request_fingerprint,snapshot_fingerprint,'
      'expected_versions) VALUES(%s,%s,%s,%s,%s)',
      (request_ref,scope['case_ref'],fp,digest,json.dumps(expected)))
   versions={x['source_ref']:x['source_version'] for x in sources}
   for a,s,code,usage in aliases(claims):
    c.execute('INSERT INTO s0_f01_sources_lab.aliases '
      '(request_ref,alias_ref,source_ref,source_version,claim_code,usage) '
      'VALUES(%s,%s,%s,%s,%s,%s)',
      (request_ref,a,s,versions[s],code,usage))
   status='LAB_SELECTION_RECORDED_NO_MODEL'
  c.execute('RELEASE SAVEPOINT '+sp)
  return out(status,'METADATA_ONLY_NO_SEMANTIC_PROOF',
             aliases=provider_rows(claims))
 except ValueError as e:
  return deny(c,sp,str(e))
 except Exception:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')


def review(c,*,request_ref,scope,expected,grant_revision,claims,proposal_aliases):
 """Checks unchanged full catalog, alias map and F01 owner. NO publish."""
 if not request_ok(request_ref,scope,expected,grant_revision,claims) or (
    type(proposal_aliases) is not list or not 0<len(proposal_aliases)<=24
    or not all(type(v) is dict and
      set(v)=={'alias','claimCode','usage'} and
      valid(v['alias']) and type(v['claimCode']) is str and
      CODE.fullmatch(v['claimCode']) and v['usage'] in
      ('commercial','interpretive') for v in proposal_aliases)):
  return out('DENIED','INVALID_REQUEST')
 sp='f01_sources_review'
 c.execute('SAVEPOINT '+sp)
 try:
  sources,full_hash=read(c,request_ref,scope,expected,grant_revision,claims)
  selection=c.execute('SELECT * FROM s0_f01_sources_lab.selections '
     'WHERE request_ref=%s FOR UPDATE',(request_ref,)).fetchone()
  fail_if(not selection,'SELECTION_MISSING')
  fail_if(selection['request_fingerprint']!=binding(
       scope,expected,grant_revision,claims),'REQUEST_COLLISION')
  fail_if(selection['snapshot_fingerprint']!=full_hash,'SOURCES_CHANGED')
  got=c.execute('SELECT alias_ref,source_ref,source_version,claim_code,usage '
     'FROM s0_f01_sources_lab.aliases WHERE request_ref=%s '
     'ORDER BY alias_ref,claim_code,usage FOR SHARE',
     (request_ref,)).fetchall()
  versions={v['source_ref']:v['source_version'] for v in sources}
  expected_rows=sorted((a,s,versions[s],code,usage)
      for a,s,code,usage in aliases(claims))
  fail_if(sorted((x['alias_ref'],x['source_ref'],x['source_version'],
      x['claim_code'],x['usage']) for x in got)!=expected_rows,
      'ALIAS_CHANGED')
  received=sorted((v['alias'],v['claimCode'],v['usage'])
                  for v in proposal_aliases)
  intended=sorted((x['alias'],x['claimCode'],x['usage'])
                  for x in provider_rows(claims))
  fail_if(received!=intended,'CLAIMS_NOT_EXACT')
  candidate=hashx(dict(request=request_ref,sources=full_hash,claims=received))
  owner=f01_review(c,turn_ref=request_ref,scope=scope,expected=expected,
                   candidate_digest=candidate)
  fail_if(owner['status'] not in (
      'LAB_RECHECK_RECORDED_NO_PUBLISH','LAB_RECHECK_REPLAY_NO_PUBLISH'),
      'F01_OWNER_CHANGED')
  prior=c.execute('SELECT * FROM s0_f01_sources_lab.reviews '
        'WHERE request_ref=%s FOR UPDATE',(request_ref,)).fetchone()
  if prior:
   fail_if(prior['proposal_fingerprint']!=candidate,'REVIEW_COLLISION')
   decision='LAB_REVIEW_REPLAY_NO_PUBLISH'
  else:
   c.execute('INSERT INTO s0_f01_sources_lab.reviews '
      '(request_ref,proposal_fingerprint) VALUES(%s,%s)',
      (request_ref,candidate))
   decision='LAB_REVIEW_RECORDED_NO_PUBLISH'
  c.execute('RELEASE SAVEPOINT '+sp)
  return out(decision,'SEMANTIC_AND_OPERATIONAL_GATES_MISSING')
 except ValueError as e:
  return deny(c,sp,str(e))
 except Exception:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return out('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
