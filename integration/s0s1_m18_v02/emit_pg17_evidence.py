"""Emit one-time evidence from REAL disposable PG17 PRE_DISPATCH v0.2.

Writes ONLY lab status/flags to temporary CI artifact; never copy IDs,
database URI, messages, customer data or credentials to the repository.
"""
import json,os
from pathlib import Path
from integration.s0s1_pre_dispatch_v02.test_pg17_service import PDReadbackPhysical
def run():
 if os.getenv('M09_PG17_DISPOSABLE')!='YES':
  raise RuntimeError('PG17_DISPOSABLE_REQUIRED')
 target=os.getenv('M18_V02_PG17_FIXTURE')
 if not target or not str(Path(target).resolve()).startswith('/tmp/'):
  raise RuntimeError('TEMP_OUTPUT_REQUIRED')
 cls=PDReadbackPhysical
 cls.setUpClass.__func__(cls)
 try:
  t=cls('test_01_stage_does_not_attest_commit')
  t.setUp()
  stage=t.act()
  committed=t.rb()
  assert stage['status']=='LAB_RESERVATION_STAGED_BEFORE_COMMIT'
  assert committed['status']=='LAB_COMMITTED_RECEIPT_NO_DISPATCH'
  replay=t.act()
  assert replay['status']=='LAB_REPLAY_REQUIRES_READBACK'
  positive={'stage':stage,'readback':committed,'replay':replay}
  t.setUp()
  rolled=t.act(rollback=True)
  unknown=t.rb()
  assert unknown['status']=='LAB_COMMIT_UNKNOWN'
  t.setUp()
  stale_stage=t.act()
  t.sql("UPDATE s0_pre_dispatch_lab.consents SET state='REVOKED',revision=2 "
        "WHERE case_ref='case_A'")
  stale=t.rb()
  assert stale['status']=='LAB_STALE_NO_DISPATCH'
  t.setUp()
  cancel_stage=t.act()
  cancel=t.stop()
  cancelled=t.rb()
  assert cancel['status']=='LAB_CANCEL_STAGED_BEFORE_COMMIT'
  assert cancelled['status']=='LAB_CANCELLED_NO_DISPATCH'
  t.setUp()
  exp_stage=t.act()
  t.sql("UPDATE s0_pd_v02_lab.receipts SET expires_at="
        "clock_timestamp()-interval '1 millisecond' WHERE attempt_ref='attempt_A'")
  expired=t.rb()
  assert expired['status']=='LAB_EXPIRED_NO_DISPATCH'
  # Prove S0 v0.2 itself cannot pretend to be an external lease.
  data={'positive':positive,'rollback':{'stage':rolled,'readback':unknown},
   'stale':{'stage':stale_stage,'readback':stale},
   'cancelled':{'stage':cancel_stage,'cancel_stage':cancel,'readback':cancelled},
   'expired':{'stage':exp_stage,'readback':expired}}
  for sample in data.values():
   for val in sample.values():
    assert val['send_authorized'] is False
    assert val['graph_dispatch_authorized'] is False
    assert val['external_lease_issued'] is False
    assert val['production_authorized'] is False
  dest=Path(target)
  dest.write_text(json.dumps(data,sort_keys=True,separators=(',',':')))
  dest.chmod(0o600)
  print('M18 physical PRE_DISPATCH v0.2 evidence emitted:',','.join(data))
 finally:
  cls.tearDownClass.__func__(cls)
if __name__=='__main__':
 run()
