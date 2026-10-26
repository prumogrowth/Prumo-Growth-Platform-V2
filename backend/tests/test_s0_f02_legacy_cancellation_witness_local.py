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
if __name__=='__main__':unittest.main()
