"""PG17 snapshots for OFF14; synthetic and runner-local only."""
import json,os
from pathlib import Path
from .test_pg17_service import F01CommercialPhysical

def main():
 p=Path(os.environ['S0_F01_SOURCE_EVIDENCE'])
 if os.environ.get('M09_PG17_DISPOSABLE')!='YES' or p.exists():
  raise RuntimeError('disposable exclusive runner required')
 F01CommercialPhysical.setUpClass()
 try:
  t=F01CommercialPhysical('test_01_selected_only_opaque_alias_no_offer')
  t.setUp()
  selected=t.select()
  assert selected['status']=='LAB_SELECTION_RECORDED_NO_MODEL'
  def snap():
   with t.lab.admin() as c:
    ctx=c.execute("SELECT * FROM s0_f01_sources_lab.contexts WHERE case_ref='case_A'").fetchone()
    rows=c.execute("SELECT * FROM s0_f01_sources_lab.sources WHERE case_ref='case_A' ORDER BY source_ref").fetchall()
    now=c.execute('SELECT clock_timestamp() AS ts').fetchone()['ts']
   ms=lambda x:int(x.timestamp()*1000) if x else None
   return dict(storeRef=ctx['store_ref'],caseRef=ctx['case_ref'],
    personRef=ctx['person_ref'],purposeRef=ctx['purpose_ref'],
    observedAtMs=ms(now),versions={k:ctx[k+'_revision'] for k in
     ('catalog','knowledge','policy','consent','grant')},
    contentPolicy=ctx['content_policy'],snapshotState='LAB_UNVERIFIED',
    sources=[dict(sourceRef=s['source_ref'],storeRef=s['store_ref'],
      kind=s['kind'],approvalState=s['approval_state'],
      sourceVersion=s['source_version'],validUntilMs=ms(s['valid_until']),
      correctedByRef=s['corrected_by_ref'],claimCodes=s['claim_codes'])
      for s in rows])
  before=snap()
  req=dict(requestRef='turn_A',storeRef='store-A',caseRef='case_A',
    personRef='person_A',purposeRef='offer_info',
    startedAtMs=before['observedAtMs']-1000,
    deadlineMs=before['observedAtMs']+120000,
    versions=before['versions'],claims=[
      dict(sourceRef='src_current_A',claimCode='PRODUCT_FEATURE',usage='commercial')])
  stable=dict(schemaVersion='prumo.openai.f01-source-review/0.1-lab',
              request=req,before=before,after=snap())
  assert t.assess()['status']=='LAB_REVIEW_RECORDED_NO_PUBLISH'
  t.mutate("UPDATE s0_f01_sources_lab.sources SET source_version=2 WHERE source_ref='src_history_A'")
  changed=dict(stable,after=snap())
  assert t.assess()['reason']=='SOURCES_CHANGED'
  p.write_text(json.dumps(dict(lab_only=True,stable=stable,changed=changed,
   aliases=selected['aliases']),sort_keys=True)+'\n')
  p.chmod(0o600)
 finally:
  F01CommercialPhysical.tearDownClass()
if __name__=='__main__':main()
