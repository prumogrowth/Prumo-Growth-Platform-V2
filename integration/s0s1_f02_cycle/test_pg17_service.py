"""Physical lab checks: F02 signed cycle/consent and original F02 gate."""
import os,unittest,threading
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import psycopg
from integration.s0s1_f02 import test_pg17_service as base
from .pg17_service import (
  SCHEMA,DOMAIN,HostActor,canonical,digest,transition,readback,
  prepare_guarded,review_guarded,now_ms)
@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE')=='YES',
                     'disposable PG17 only')
class F02CyclePhysical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  base.F02Physical.setUpClass.__func__(cls)
  try:
   with cls.lab.admin() as c:
    c.execute("SET s0_meta.disposable='YES'")
    c.execute("SET s0_f02.install='CYCLE_AUTHORITY_LAB_ONLY'")
    c.execute((cls.origin/'integration/s0s1_f02_cycle/pg17_schema.sql').read_text())
  except BaseException:
   base.F02Physical.tearDownClass.__func__(cls)
   raise
 @classmethod
 def tearDownClass(cls):
  try:
   with cls.lab.admin() as c:
    c.execute('DROP SCHEMA IF EXISTS s0_f02_cycle_lab CASCADE')
  finally:
   base.F02Physical.tearDownClass.__func__(cls)
 def setUp(self):
  base.F02Physical.setUp(self)
  self.private=Ed25519PrivateKey.generate()
  self.host=HostActor('ACTOR_A','store-A','M09_KEY_A','case_A','flow_A')
  with self.lab.admin() as c:
   c.execute('TRUNCATE s0_f02_cycle_lab.commands,'
             's0_f02_cycle_lab.authorities CASCADE')
   c.execute('INSERT INTO s0_f02_cycle_lab.authorities '
    '(case_ref,flow_ref,store_ref,service_ref,purpose_ref,actor_ref,'
    'actor_key_revision,ed25519_public_key,cycle_revision,state) '
    'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(
     'case_A','flow_A','store-A','M09_KEY_A','lead_followup','ACTOR_A',
     1,self.private.public_key().public_bytes(
       serialization.Encoding.Raw,serialization.PublicFormat.Raw),1,'ACTIVE'))
   self.now=now_ms(c)
  self.seq=0
 def versions7(self):
  return dict(self.versions)
 def cmd(self,action='ADVANCE',**edits):
  self.seq+=1
  q=dict(version=SCHEMA,command_ref=f'cmd_{self.seq}',
   nonce=f'nonce_{self.seq:08d}',action=action,case_ref='case_A',
   flow_ref='flow_A',store_ref='store-A',service_ref='M09_KEY_A',
   actor_ref='ACTOR_A',key_revision=1,purpose_ref='lead_followup',
   expected_cycle=1,expected_assignment=1,expected_policy=1,
   expected_suppression=1,expected_consent=1,issued_ms=self.now-1000,
   expires_ms=self.now+60000)
  q.update(edits)
  return q,self.private.sign(DOMAIN+canonical(q))
 def apply(self,q,s,rollback=False,host=None):
  with self.lab.admin() as c:
   x=transition(c,request=q,signature=s,host=host or self.host)
   if rollback:c.rollback()
   return x
 def rb(self,q,hashval=None):
  with self.lab.admin() as c:
   return readback(c,command_ref=q['command_ref'],host=self.host,
      request_hash=hashval or digest(q))
 def change(self,sql):
  with self.lab.admin() as c:c.execute(sql)
 def prepare(self):
  with self.lab.admin() as c:
   return prepare_guarded(c,self.q,scope=self.scope,principal=self.principal,
       m09_versions=self.m09_versions,expected=self.versions7())
 def review(self,p):
  with self.lab.admin() as c:
   return review_guarded(c,p,q=self.q,scope=self.scope,
      principal=self.principal,m09_versions=self.m09_versions,
      expected=self.versions7())
 def proposal(self,raw):
  t=raw['request']['templates'][0]
  return dict(status='S0_RECHECK_ONLY',
    schemaVersion='prumo.openai.f02-plan-candidate/0.1',
    requestId=self.q['request_ref'],chainRef='synthetic_chain',
    expectedVersions=self.versions7(),
    attempts=[dict(templateId=t['id'],templateVersion=t['version'],
       purpose=self.q['purpose_ref'],at=raw['request']['windowStart'])],
    finalTemplate=None,sendAuthorized=False,schedulingAuthorized=False,
    commercialTransitionAuthorized=False)
 def count(self):
  with self.lab.admin() as c:
   return c.execute('SELECT count(*) AS n FROM s0_f02_cycle_lab.commands').fetchone()['n']
 def test_01_signed_transition_and_independent_readback(self):
  q,s=self.cmd()
  a=self.apply(q,s)
  self.assertEqual(a['status'],'LAB_CYCLE_STAGED_BEFORE_COMMIT')
  self.assertFalse(a['commit_verified']);self.assertFalse(a['send_authorized'])
  self.assertEqual(self.rb(q)['status'],'LAB_COMMITTED_CYCLE_READBACK')
 def test_02_exact_replay_no_new_command(self):
  q,s=self.cmd();self.apply(q,s)
  self.assertEqual(self.apply(q,s)['status'],
                  'LAB_PREVIOUSLY_RECORDED_NOT_AUTHORITY')
  self.assertEqual(self.count(),1)
 def test_03_duplicate_nonce_different_command_denied(self):
  q,s=self.cmd();self.apply(q,s)
  bad={**q,'command_ref':'different'}
  self.assertEqual(self.apply(bad,self.private.sign(
     DOMAIN+canonical(bad)))['reason'],'COMMAND_OR_NONCE_COLLISION')
 def test_04_tamper_signature_denied(self):
  q,s=self.cmd();q['action']='REVOKE'
  self.assertEqual(self.apply(q,s)['reason'],'INVALID_SIGNATURE')
 def test_05_wrong_host_denied(self):
  q,s=self.cmd()
  host=HostActor('ACTOR_A','store-B','M09_KEY_A','case_A','flow_A')
  self.assertEqual(self.apply(q,s,host=host)['reason'],'INVALID_REQUEST')
 def test_06_mismatched_cycle_source_denied(self):
  self.change("UPDATE s0_f02_lab.case_cycles SET cycle_revision=3 "
              "WHERE case_ref='case_A'")
  q,s=self.cmd()
  self.assertEqual(self.apply(q,s)['reason'],'CYCLE_SOURCE_DIVERGED')
  # The original F02 boundary can deny stale before the additive gate.
  self.assertEqual(self.prepare()['reason'],'STALE_OR_CHANGED')
 def test_07_revoked_consent_does_not_resume_or_advance(self):
  self.change("UPDATE s0_pre_dispatch_lab.consents "
              "SET state='REVOKED' WHERE case_ref='case_A'")
  q,s=self.cmd()
  self.assertEqual(self.apply(q,s)['reason'],'CONSENT_DENIED')
  self.assertEqual(self.prepare()['reason'],'CONSENT_DENIED')
 def test_08_suppression_denies_advance(self):
  self.change("UPDATE s0_pre_dispatch_lab.suppressions SET active=true "
              "WHERE purpose_ref='lead_followup'")
  q,s=self.cmd()
  self.assertEqual(self.apply(q,s)['reason'],'SUPPRESSED')
 def test_09_pause_denies_guarded_plan(self):
  q,s=self.cmd('PAUSE')
  self.assertEqual(self.apply(q,s)['status'],'LAB_CYCLE_STAGED_BEFORE_COMMIT')
  self.versions['cycle']=2
  self.assertEqual(self.prepare()['reason'],'CYCLE_AUTHORITY_DENIED')
 def test_10_pause_resume_reopens_only_lab_planning(self):
  q,s=self.cmd('PAUSE');self.apply(q,s)
  r,rs=self.cmd('RESUME',expected_cycle=2);self.apply(r,rs)
  self.versions['cycle']=3
  x=self.prepare()
  self.assertEqual(x['decision'],'LAB_REQUEST_RECORDED_NO_MODEL')
  self.assertTrue(x['cycle_authority_lab_consistent'])
  self.assertFalse(x['send_authorized'])
 def test_11_f02_review_blocked_by_intervening_pause(self):
  prepared=self.prepare();p=self.proposal(prepared['private'])
  q,s=self.cmd('PAUSE');self.apply(q,s)
  self.assertNotEqual(self.review(p)['decision'],
                      'LAB_PROPOSAL_RECORDED_REVIEW_ONLY')
 def test_12_f02_review_ok_while_source_active(self):
  prepared=self.prepare()
  out=self.review(self.proposal(prepared['private']))
  self.assertEqual(out['decision'],'LAB_PROPOSAL_RECORDED_REVIEW_ONLY')
  self.assertFalse(out['schedule_authorized'])
 def test_13_rollback_never_proves_commit(self):
  q,s=self.cmd()
  self.apply(q,s,rollback=True)
  self.assertEqual(self.rb(q)['status'],'LAB_COMMIT_UNKNOWN')
 def test_14_revoke_terminal_after_optout(self):
  self.change("UPDATE s0_pre_dispatch_lab.cases "
              "SET global_opt_out=true WHERE case_ref='case_A'")
  q,s=self.cmd('REVOKE')
  self.assertEqual(self.apply(q,s)['status'],'LAB_CYCLE_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.rb(q)['state'],'REVOKED')
 def test_15_key_revoked_or_rotated_denies_signature(self):
  q,s=self.cmd()
  self.change("UPDATE s0_f02_cycle_lab.authorities "
              "SET actor_key_revision=2 WHERE case_ref='case_A'")
  self.assertEqual(self.apply(q,s)['reason'],'KEY_REVOKED_OR_ROTATED')
 def test_16_source_stale_assignment_independent(self):
  self.change("UPDATE s0_pre_dispatch_lab.cases "
              "SET assignment_revision=2 WHERE case_ref='case_A'")
  q,s=self.cmd()
  self.assertEqual(self.apply(q,s)['reason'],'STALE_VERSIONS')
 def test_17_concurrent_same_revision_only_one_wins(self):
  gate=threading.Barrier(2)
  q,s=self.cmd();a,asig=self.cmd('PAUSE')
  def worker(payload,sig):
   with self.lab.admin() as c:
    gate.wait(timeout=7)
    return transition(c,request=payload,signature=sig,host=self.host)
  with ThreadPoolExecutor(max_workers=2) as pool:
   fs=[pool.submit(worker,q,s),pool.submit(worker,a,asig)]
   outcomes=[f.result(timeout=17) for f in fs]
  self.assertEqual(sum(x['status']=='LAB_CYCLE_STAGED_BEFORE_COMMIT'
                       for x in outcomes),1)
  self.assertEqual(self.count(),1)
 def test_18_runtime_acl_denies_cycle_private_tables(self):
  for name in ('authorities','commands'):
   with psycopg.connect(self.lab.runtime_dsn) as c:
    with self.assertRaises(psycopg.Error):
     c.execute('SELECT * FROM s0_f02_cycle_lab.'+name)
 def test_19_invalid_array_action_denied_without_exception(self):
  q,s=self.cmd()
  q['action']=['REVOKE']
  with self.lab.admin() as c:
   out=transition(c,request=q,signature=s,host=self.host)
  self.assertEqual(out['status'],'DENIED')
 def test_20_expired_and_future_signed_command_denied(self):
  for attrs in ({'issued_ms':self.now-60000,'expires_ms':self.now-1},
                {'issued_ms':self.now+50000,'expires_ms':self.now+70000}):
   q,s=self.cmd(**attrs)
   self.assertEqual(self.apply(q,s)['reason'],'EXPIRED_OR_FUTURE')
  self.assertEqual(self.count(),0)
 def test_21_disabled_actor_cannot_advance(self):
  q,s=self.cmd()
  self.change("UPDATE s0_f02_cycle_lab.authorities "
              "SET actor_enabled=false WHERE case_ref='case_A'")
  self.assertEqual(self.apply(q,s)['reason'],'ACTOR_OR_SCOPE_DENIED')
 def test_22_consent_revision_changed_requires_new_command(self):
  q,s=self.cmd()
  self.change("UPDATE s0_pre_dispatch_lab.consents "
              "SET revision=2 WHERE case_ref='case_A'")
  self.assertEqual(self.apply(q,s)['reason'],'STALE_VERSIONS')
 def test_23_old_command_readback_cannot_authorize_new_cycle(self):
  old,so=self.cmd('ADVANCE');self.apply(old,so)
  new,sn=self.cmd('PAUSE',expected_cycle=2);self.apply(new,sn)
  self.assertEqual(self.rb(old)['status'],'LAB_COMMAND_SUPERSEDED')
  self.assertEqual(self.rb(new)['state'],'PAUSED')
 def test_24_pause_allowed_after_consent_revocation(self):
  self.change("UPDATE s0_pre_dispatch_lab.consents "
              "SET state='REVOKED' WHERE case_ref='case_A'")
  q,s=self.cmd('PAUSE')
  self.assertEqual(self.apply(q,s)['status'],'LAB_CYCLE_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.rb(q)['state'],'PAUSED')
if __name__=='__main__':unittest.main()
