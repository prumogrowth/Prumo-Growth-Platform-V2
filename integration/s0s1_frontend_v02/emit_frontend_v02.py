"""Capture only synthetic v0.2 PG17 receipt/history data in runner temporary file."""
import json,os
from pathlib import Path
from .test_pg17_service import FrontendV02Physical
def main():
 if os.getenv('M09_PG17_DISPOSABLE')!='YES':
  raise SystemExit('PG17 disposable only')
 p=Path(os.environ['S0_FRONTEND_V02_EVIDENCE'])
 if p.exists() or not p.parent.is_dir():
  raise RuntimeError('exclusive runner path required')
 FrontendV02Physical.setUpClass()
 try:
  t=FrontendV02Physical('test_01_active_open_staged_not_authority')
  t.setUp()
  history_before=t.history()
  staged=t.stage(ref='archived',case='case_B')
  after_commit=t.proof(ref='archived',case='case_B')
  history_after=t.history()
  t.inbound('case_B')
  after_inbound=t.proof(ref='archived',case='case_B')
  active_staged=t.stage()
  active_after=t.proof()
  data=dict(lab_only=True,history_before=history_before,
   staged=staged,after_commit=after_commit,history_after=history_after,
   after_new_inbound=after_inbound,active_staged=active_staged,
   active_after=active_after)
  p.write_text(json.dumps(data,sort_keys=True,ensure_ascii=True)+'\n')
  p.chmod(0o600)
 finally:
  FrontendV02Physical.tearDownClass()
if __name__=='__main__':main()
