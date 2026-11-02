"""OFF-23 F02 controlled PG17 mutation tests for current-event readback."""
import os,unittest
import psycopg
from integration.s0s1_f02_cycle import test_pg17_service as inherited

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES','PG17 disposable only')
class F02Off23Physical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  inherited.F02CyclePhysical.setUpClass()
 @classmethod
 def tearDownClass(cls):
  inherited.F02CyclePhysical.tearDownClass()
 def setUp(self):
  self.t=inherited.F02CyclePhysical('test_01_signed_transition_and_independent_readback')
  self.t.setUp()
 def stage(self,action='ADVANCE'):
  q,s=self.t.cmd(action)
  res=self.t.apply(q,s)
  self.assertEqual(res['status'],'LAB_CYCLE_STAGED_BEFORE_COMMIT',res)
  self.assertEqual(self.t.rb(q)['status'],'LAB_COMMITTED_CYCLE_READBACK')
  return q
 def deny(self,q,reason):
  out=self.t.rb(q)
  self.assertEqual(out['status'],'DENIED',out)
  self.assertEqual(out['reason'],reason,out)
  self.assertIs(out['send_authorized'],False)
  self.assertIs(out['schedule_authorized'],False)
 def test_off23_01_current_authority_paused_without_revision_denied(self):
  q=self.stage()
  self.t.change("UPDATE s0_f02_cycle_lab.authorities SET state='PAUSED' "
     "WHERE case_ref='case_A'")
  self.deny(q,'EVENT_STATE_DIVERGED')
 def test_off23_02_current_authority_revoked_without_revision_denied(self):
  q=self.stage()
  self.t.change("UPDATE s0_f02_cycle_lab.authorities SET state='REVOKED' "
     "WHERE case_ref='case_A'")
  self.deny(q,'EVENT_STATE_DIVERGED')
 def test_off23_03_event_after_state_tamper_denied(self):
  q=self.stage('PAUSE')
  self.t.change("UPDATE s0_f02_cycle_lab.commands SET after_state='ACTIVE' "
     "WHERE command_ref='cmd_1'")
  self.deny(q,'EVENT_STATE_DIVERGED')
 def test_off23_04_event_actor_mismatch_denied(self):
  q=self.stage()
  self.t.change("UPDATE s0_f02_cycle_lab.commands SET actor_ref='OTHER_ACTOR' "
     "WHERE command_ref='cmd_1'")
  self.deny(q,'EVENT_ACTOR_DIVERGED')
 def test_off23_05_event_actor_key_revision_mismatch_denied(self):
  q=self.stage()
  self.t.change("UPDATE s0_f02_cycle_lab.commands SET actor_key_revision=2 "
     "WHERE command_ref='cmd_1'")
  self.deny(q,'EVENT_ACTOR_KEY_REVISION_CHANGED')
 def test_off23_06_authority_actor_key_rotated_without_cycle_denied(self):
  q=self.stage()
  self.t.change("UPDATE s0_f02_cycle_lab.authorities SET actor_key_revision=2 "
     "WHERE case_ref='case_A'")
  self.deny(q,'EVENT_ACTOR_KEY_REVISION_CHANGED')
 def test_off23_07_nonadjacent_journal_revision_denied_by_pg_constraint(self):
  q=self.stage()
  # PostgreSQL itself prohibits a broken before/after sequence; it cannot
  # be used as an artificial counterexample in the readback layer.
  with self.assertRaises(psycopg.errors.CheckViolation):
   self.t.change("UPDATE s0_f02_cycle_lab.commands SET before_revision=5 "
      "WHERE command_ref='cmd_1'")
  self.assertEqual(self.t.rb(q)['status'],'LAB_COMMITTED_CYCLE_READBACK')
 def test_off23_08_valid_pause_readback_unchanged(self):
  q=self.stage('PAUSE')
  self.assertEqual(self.t.rb(q)['state'],'PAUSED')
 def test_off23_09_valid_revoke_readback_unchanged(self):
  q=self.stage('REVOKE')
  self.assertEqual(self.t.rb(q)['state'],'REVOKED')
 def test_off23_10_old_event_superseded_not_newly_authorized(self):
  old=self.stage()
  new,s=self.t.cmd('PAUSE',expected_cycle=2)
  self.assertEqual(self.t.apply(new,s)['status'],'LAB_CYCLE_STAGED_BEFORE_COMMIT')
  result=self.t.rb(old)
  self.assertEqual(result['status'],'LAB_COMMAND_SUPERSEDED',result)
  self.assertIs(result['send_authorized'],False)
  self.assertEqual(self.t.rb(new)['state'],'PAUSED')
 def test_off23_11_readback_postcommit_only(self):
  q,s=self.t.cmd('ADVANCE')
  self.t.apply(q,s,rollback=True)
  self.assertEqual(self.t.rb(q)['status'],'LAB_COMMIT_UNKNOWN')
 def test_off23_12_event_wrong_digest_fails_closed(self):
  q=self.stage()
  self.t.change("UPDATE s0_f02_cycle_lab.commands SET request_digest="
                "repeat('0',64) WHERE command_ref='cmd_1'")
  self.deny(q,'COMMAND_COLLISION')
if __name__=='__main__':unittest.main()
