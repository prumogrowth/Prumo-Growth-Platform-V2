"""Emit one internal F02 PRIVATE envelope from disposable PG17 for OFF-04 interop.

This is not an HTTP/provider request and must never be presented to a model.
The Node interop invokes the original OFF-04 f02ProviderView, which strips
store/person/case, request and original template identities.
"""
import json
import os
from pathlib import Path

from . import test_pg17_service as physical


def main():
    if os.environ.get('M09_PG17_DISPOSABLE')!='YES':
        raise SystemExit('PG17 disposable only')
    target=Path(os.environ['S0_F02_PRIVATE_EVIDENCE'])
    if not target.parent.is_dir() or target.exists():
        raise SystemExit('exclusive runner temp path required')
    physical.F02Physical.setUpClass()
    try:
        case=physical.F02Physical('test_01_private_envelope_and_persistent_alias')
        case.setUp()
        out=case.create()
        if out['decision']!='LAB_REQUEST_RECORDED_NO_MODEL':
            raise RuntimeError('source read denied')
        with case.lab.admin() as c:
            rows=c.execute('SELECT alias,template_ref,version_ref '
                'FROM s0_f02_lab.aliases ORDER BY alias').fetchall()
            request=c.execute('SELECT request_ref,provider_tag '
                'FROM s0_f02_lab.requests').fetchone()
        if (len(rows)!=1 or rows[0]['alias']!='tpl_001'
            or rows[0]['template_ref']!='tpl_A'
            or request['provider_tag']!=out['private']['providerTag']):
            raise RuntimeError('S0 readback mismatch')
        obj={'lab_only':True,'private':out['private'],
             'expected_aliases':[{
                'alias':r['alias'],'template_ref':r['template_ref'],
                'version_ref':r['version_ref']} for r in rows]}
        contents=json.dumps(obj,ensure_ascii=True,separators=(',',':'))
        if any(s in contents for s in ('private_key','secret_value',
                 'access_token','password','bearer')):
            raise RuntimeError('leak in fixture')
        target.write_text(contents+'\n',encoding='ascii')
        target.chmod(0o600)
    finally:
        physical.F02Physical.tearDownClass()


if __name__=='__main__':
    main()
