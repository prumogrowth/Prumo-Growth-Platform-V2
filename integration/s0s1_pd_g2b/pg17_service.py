"""S0 G2-B: cooperative lab transaction/epoch gate, NOT an operational lease.

All functions use a caller-owned PG17 transaction. Writers that bypass this
lab gate (including original PRE_DISPATCH and hosted future writers) are NOT
serialized. Return values never claim COMMIT, real actor, or Graph permission.
"""
from __future__ import annotations
from integration.s0s1_pre_dispatch_v02.pg17_service import (
 reserve as original_reserve,readback as original_readback,
 cancel as original_cancel,validate,ident, out as old_out)
from integration.s0s1_m09_registry.port import HostScope,M2MPrincipal,Revisions

VERSION='prumo.s0.pd.g2b.cooperative/0.1-lab'
def result(status,reason,**extra):
 return {'contract_version':VERSION,'status':status,'reason':reason,
    'lab_only':True,'cooperative_gate_only':True,
    'host_authenticated':False,'source_operational':False,
    'source_coherent_only_if_writers_cooperate':True,
    'commit_verified':False,'current_authority_verified':False,
    'authenticated_attempt_binding':False,
    'outbox_authorized':False,'lease_issued':False,
    'send_authorized':False,'graph_dispatch_authorized':False,
    'automatic_retry_authorized':False,'production_authorized':False,
    **extra}
class Refused(Exception):pass
def _check(c,case_ref,store_ref,expected_generation):
 if not ident(case_ref) or not ident(store_ref) or (
    type(expected_generation) is not int or expected_generation<1):
  raise Refused('INVALID_REQUEST')
 gate=c.execute('SELECT * FROM s0_pd_g2b_lab.case_gates '
    'WHERE case_ref=%s FOR UPDATE',(case_ref,)).fetchone()
 if not gate or gate['store_ref']!=store_ref:
  raise Refused('GATE_SCOPE_DENIED')
 if gate['generation']!=expected_generation:
  raise Refused('GENERATION_STALE')
 return gate
def _bump(c,case_ref,old):
 newer=c.execute('UPDATE s0_pd_g2b_lab.case_gates '
    'SET generation=generation+1,changed_at=clock_timestamp() '
    'WHERE case_ref=%s AND generation=%s RETURNING generation',
    (case_ref,old)).fetchone()
 if not newer:raise Refused('GENERATION_CAS_FAILED')
 return newer['generation']
def _wrap(c,fn):
 # This is a savepoint INSIDE the caller's transaction; a successful result
 # CANNOT assert COMMIT. The caller is responsible for commit/rollback.
 sp='s0_g2b_gate'
 c.execute('SAVEPOINT '+sp)
 try:
  x=fn()
  c.execute('RELEASE SAVEPOINT '+sp)
  return x
 except Refused as e:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return result('DENIED',str(e))
 except Exception:
  c.execute('ROLLBACK TO SAVEPOINT '+sp)
  c.execute('RELEASE SAVEPOINT '+sp)
  return result('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
def reserve(c,request,*,scope,principal,m09_versions,expected_generation):
 if not validate(request,scope,principal,m09_versions):
  return result('DENIED','INVALID_REQUEST')
 def operation():
  gate=_check(c,request['case_ref'],scope.concessionaria_id,expected_generation)
  original=original_reserve(c,request,scope=scope,principal=principal,
                           m09_versions=m09_versions)
  if original['status']!='LAB_RESERVATION_STAGED_BEFORE_COMMIT':
   return result('DENIED' if original['status']=='DENIED' else 'UNAVAILABLE',
     'V02_'+original['reason'])
  newer=_bump(c,request['case_ref'],gate['generation'])
  return result('LAB_G2B_RESERVATION_STAGED_BEFORE_COMMIT',
     'READBACK_REQUIRED',generation_after_stage=newer)
 return _wrap(c,operation)
def revoke_consent(c,*,case_ref,store_ref,purpose_ref,
                   expected_generation,expected_consent_revision):
 if not ident(purpose_ref) or type(expected_consent_revision) is not int or (
    expected_consent_revision<1):
  return result('DENIED','INVALID_REQUEST')
 def operation():
  gate=_check(c,case_ref,store_ref,expected_generation)
  case=c.execute('SELECT * FROM s0_pre_dispatch_lab.cases '
     'WHERE case_ref=%s FOR UPDATE',(case_ref,)).fetchone()
  if not case or case['concessionaria_id']!=store_ref:
   raise Refused('CASE_SCOPE_DENIED')
  consent=c.execute('SELECT * FROM s0_pre_dispatch_lab.consents '
     'WHERE case_ref=%s AND purpose_ref=%s FOR UPDATE',
     (case_ref,purpose_ref)).fetchone()
  if not consent or consent['revision']!=expected_consent_revision:
   raise Refused('CONSENT_REVISION_STALE')
  if consent['state']!='GRANTED':
   raise Refused('CONSENT_ALREADY_REVOKED')
  changed=c.execute('UPDATE s0_pre_dispatch_lab.consents '
     "SET state='REVOKED',revision=revision+1 "
     'WHERE case_ref=%s AND purpose_ref=%s AND revision=%s '
     "AND state='GRANTED' RETURNING revision",
     (case_ref,purpose_ref,expected_consent_revision)).fetchone()
  if not changed:raise Refused('CONSENT_CAS_FAILED')
  newer=_bump(c,case_ref,gate['generation'])
  return result('LAB_G2B_REVOCATION_STAGED_BEFORE_COMMIT',
     'READBACK_REQUIRED',generation_after_stage=newer)
 return _wrap(c,operation)
def cancel(c,*,attempt_ref,case_ref,scope,principal,m09_versions,
           expected_generation):
 if not ident(attempt_ref) or not ident(case_ref) or (
    type(scope) is not HostScope or type(principal) is not M2MPrincipal or
    type(m09_versions) is not Revisions):
  return result('DENIED','INVALID_REQUEST')
 def operation():
  gate=_check(c,case_ref,scope.concessionaria_id,expected_generation)
  receipt=c.execute('SELECT case_ref FROM s0_pd_v02_lab.receipts '
    'WHERE attempt_ref=%s FOR UPDATE',(attempt_ref,)).fetchone()
  if not receipt or receipt['case_ref']!=case_ref:
   raise Refused('RECEIPT_CASE_SCOPE_DENIED')
  original=original_cancel(c,attempt_ref=attempt_ref,scope=scope,
    principal=principal,m09_versions=m09_versions)
  if original['status']!='LAB_CANCEL_STAGED_BEFORE_COMMIT':
   raise Refused('CANCEL_'+original['reason'])
  newer=_bump(c,case_ref,gate['generation'])
  return result('LAB_G2B_CANCEL_STAGED_BEFORE_COMMIT',
    'READBACK_REQUIRED',generation_after_stage=newer)
 return _wrap(c,operation)
def observe(c,request,*,scope,principal,m09_versions,expected_generation):
 """Locked observation relative to cooperative writers only, NOT a grant."""
 if not validate(request,scope,principal,m09_versions):
  return result('DENIED','INVALID_REQUEST')
 def operation():
  gate=_check(c,request['case_ref'],scope.concessionaria_id,expected_generation)
  historical=original_readback(c,request,scope=scope,principal=principal,
                              m09_versions=m09_versions)
  if historical['status'] in ('UNAVAILABLE','DENIED'):
   return result('UNAVAILABLE','SOURCE_UNAVAILABLE')
  # Returning commit_verified=false is deliberate even if a historical
  # v0.2 readback saw a committed receipt. Caller's txn may still rollback
  # and any noncooperative writer may immediately supersede the sources.
  return result('LAB_G2B_OBSERVATION_STAGED_NO_DISPATCH',
     'COOPERATIVE_ONLY_NOT_REDEEMABLE',
     historical_classification=historical['status'],
     historical_reason=historical['reason'],
     observed_generation=gate['generation'])
 return _wrap(c,operation)
