"""Disposable PG17-only S0 attention evidence."""
import json
import os
from pathlib import Path
from .test_pg17_service import FrontendReadPhysical

def main():
    assert os.getenv('M09_PG17_DISPOSABLE')=='YES'
    p=Path(os.environ['S0_FRONTEND_EVIDENCE'])
    if p.exists() or not p.parent.is_dir():
        raise RuntimeError('exclusive temp artifact required')
    FrontendReadPhysical.setUpClass()
    try:
        t=FrontendReadPhysical('test_01_titular_open_immediate_without_dwell')
        t.setUp()
        before=t.queue()['rows'][0]
        supervisor=t.open(ref='manager_open',actor='manager_A',role='SUPERVISOR')
        recorded=t.open()
        after=t.queue()['rows'][0]
        historical=t.open(ref='historical',case='case_B')
        result={'lab_only':True,'before':before,'supervisor':supervisor,
                'recorded':recorded,'after':after,'historical':historical,
                'manager':t.manager(),'queue':t.queue()['rows']}
        p.write_text(json.dumps(result,sort_keys=True,ensure_ascii=True)+'\n')
        p.chmod(0o600)
    finally:
        FrontendReadPhysical.tearDownClass()

if __name__=='__main__':
    main()
