"""Export two S0 PG17 observations as UNVERIFIED OFF13-compatible fixtures."""
import json
import os
from pathlib import Path
from .test_pg17_service import F01OwnershipPhysical
from .pg17_service import begin_turn,definitive_handoff,VERS

def main():
    if os.environ.get('M09_PG17_DISPOSABLE')!='YES':
        raise SystemExit('disposable only')
    p=Path(os.environ['S0_F01_LAB_EVIDENCE'])
    if p.exists() or not p.parent.is_dir():
        raise SystemExit('exclusive temp path required')
    F01OwnershipPhysical.setUpClass()
    try:
        t=F01OwnershipPhysical('test_01_ai_turn_recorded_no_model_authority')
        t.setUp()
        with t.lab.admin() as c:
            before=c.execute("SELECT * FROM s0_f01_lab.cases "
                 "WHERE case_ref='case_A'").fetchone()
            now=c.execute('SELECT clock_timestamp() AS ts').fetchone()['ts']
        observed=int(now.timestamp()*1000)
        def snapshot(row,ms):
            return {
              'storeRef':row['store_ref'],'caseRef':row['case_ref'],
              'personRef':row['person_ref'],'ownerRoute':row['owner_route'],
              'handoffDefinitive':row['handoff_definitive'],
              'humanized':row['humanized'],'optOut':row['opt_out'],
              'channelEligible':row['channel_eligible'],
              'postRemittance':row['post_remittance'],
              'postSale':row['post_sale'],'observedAtMs':ms,
              'versions':{key:row[key+'_revision'] for key in VERS},
              'snapshotState':'LAB_UNVERIFIED'
            }
        q={'requestRef':'turn_A','storeRef':t.scope['store_ref'],
           'caseRef':t.scope['case_ref'],'personRef':t.scope['person_ref'],
           'startedAtMs':observed-1000,'deadlineMs':observed+120000,
           'expectedVersions':t.expected,'purpose':'F01_DRAFT_LAB'}
        turn=t.start()
        if turn['status']!='LAB_TURN_RECORDED_NO_MODEL':
            raise RuntimeError('PG17 F01 begin denied')
        with t.lab.admin() as c:
            same=c.execute("SELECT * FROM s0_f01_lab.cases "
                "WHERE case_ref='case_A'").fetchone()
        good={'schemaVersion':'prumo.openai.f01-owner-recheck/0.1-lab',
              'request':q,'before':snapshot(before,observed),
              'after':snapshot(same,observed+1000)}
        hand=t.handoff()
        if hand['status']!='LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH':
            raise RuntimeError('PG17 handoff was not committed')
        with t.lab.admin() as c:
            later=c.execute("SELECT * FROM s0_f01_lab.cases "
               "WHERE case_ref='case_A'").fetchone()
        blocked={**good,'after':snapshot(later,observed+2000)}
        result={'lab_only':True,'consistent':good,'handoff':blocked,
                'handoff_status':hand['status'],
                'late_recheck':t.review()['reason']}
        p.write_text(json.dumps(result,sort_keys=True,ensure_ascii=True)+'\n')
        p.chmod(0o600)
    finally:
        F01OwnershipPhysical.tearDownClass()
if __name__=='__main__':
    main()
