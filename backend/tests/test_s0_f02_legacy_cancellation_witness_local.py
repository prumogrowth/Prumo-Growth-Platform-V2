"""E04 cancellation witness: local plans only, never Meta cancellation."""
import unittest,uuid
from datetime import datetime,timezone
from backend.s0_f02_legacy_cancellation_witness_local import (
 _canonical,_verify_chain,_seal,CancelWitnessState,CancelWitnessResult,
 S0F02LocalLegacyCancellationWitness
)
class Tests(unittest.TestCase):
 def test_01_no_legacy_plan_not_certificate(self):
  self.assertIs(_verify_chain([],[],[]),CancelWitnessState.NO_LEGACY_CHAIN)
 def test_02_active_never_certificate(self):
  self.assertIs(_verify_chain([(uuid.uuid4(),uuid.uuid4(),'ativo',1,None,None)],[],[]),
                CancelWitnessState.ACTIVE_LEGACY_CHAIN)
 def test_03_canceled_plan_without_event_not_certificate(self):
  plan,cycle,attempt=uuid.uuid4(),uuid.uuid4(),uuid.uuid4();now=datetime.now(timezone.utc)
  self.assertIs(_verify_chain([(plan,cycle,'cancelado',2,'handoff',now)],
                            [(attempt,plan,'cancelado',None,now)],[]),
                CancelWitnessState.INCOMPLETE_LOCAL_CANCELLATION)
 def test_04_signature_requires_long_s0_secret(self):
  self.assertIsNone(_seal(b'weak','s','e','a','b','key-v1-long','a'*64))
 def test_05_canonical_hash_deterministic(self):
  self.assertEqual(_canonical([(uuid.UUID(int=1),1)],[],[]),
                   _canonical([(uuid.UUID(int=1),1)],[],[]))
 def test_06_return_only_state(self):
  self.assertEqual(tuple(vars(CancelWitnessResult(
     CancelWitnessState.LOCAL_CHAIN_ATTESTED_AUDIT_ONLY))),('state',))
 def test_07_nonphysical_intent_rejected(self):
  with self.assertRaises(TypeError):S0F02LocalLegacyCancellationWitness(object())
 def _chronology(self):
  from datetime import timedelta
  start=datetime.now(timezone.utc)
  created=start-timedelta(hours=2)
  attempt_created=start-timedelta(hours=1)
  canceled=start+timedelta(minutes=1)
  ev=canceled
  plan=uuid.uuid4();attempt=uuid.uuid4()
  plans=[(plan,uuid.uuid4(),'cancelado',2,'handoff',canceled,created)]
  tries=[(attempt,plan,'cancelado',None,canceled,attempt_created,start+timedelta(days=2))]
  events=[(uuid.uuid4(),attempt,'programado','cancelado','handoff',ev)]
  timeline=(start,start,start)
  return plans,tries,events,timeline
 def test_08_valid_pre_handoff_timeline(self):
  from backend.s0_f02_legacy_cancellation_witness_local import _verify_timeline
  from datetime import timedelta
  values=self._chronology()
  self.assertIs(_verify_timeline(*values,now=values[3][0]+timedelta(minutes=5)),
                CancelWitnessState.LOCAL_CHAIN_ATTESTED_AUDIT_ONLY)
 def test_09_post_handoff_plan_blocked(self):
  from backend.s0_f02_legacy_cancellation_witness_local import _verify_timeline
  from datetime import timedelta
  p,a,e,t=self._chronology()
  p=[(*p[0][:6],t[0]+timedelta(seconds=2))]
  self.assertIs(_verify_timeline(p,a,e,t,now=t[0]+timedelta(minutes=5)),
                CancelWitnessState.LEGACY_CHRONOLOGY_REVIEW_REQUIRED)
 def test_10_future_cancellation_blocked(self):
  from backend.s0_f02_legacy_cancellation_witness_local import _verify_timeline
  from datetime import timedelta
  p,a,e,t=self._chronology()
  self.assertIs(_verify_timeline(p,a,e,t,now=t[0]),
                CancelWitnessState.LEGACY_CHRONOLOGY_REVIEW_REQUIRED)
 def test_11_assignment_after_closure_blocked(self):
  from backend.s0_f02_legacy_cancellation_witness_local import _verify_timeline
  from datetime import timedelta
  p,a,e,t=self._chronology()
  later=t[0]+timedelta(minutes=5)
  self.assertIs(_verify_timeline(p,a,e,(t[0],later,t[0]),now=later+timedelta(minutes=5)),
                CancelWitnessState.LEGACY_CHRONOLOGY_REVIEW_REQUIRED)
 def test_12_snapshot_binds_human_timeline(self):
  from datetime import timedelta
  from backend.s0_f02_legacy_cancellation_witness_local import _canonical
  p,a,e,t=self._chronology()
  self.assertNotEqual(_canonical(p,a,e,t),
                      _canonical(p,a,e,(t[0]-timedelta(seconds=1),t[1],t[2])))
if __name__=='__main__':unittest.main()
