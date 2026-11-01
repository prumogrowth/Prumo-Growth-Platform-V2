"""Produce a SINGLE synthetic purpose-slot witness from disposable PG17.

The privilege of the fixture owner NEVER becomes runtime privilege.
No token, secret value, Ed25519 private key or vault access is exported.
The output is only for the WA04A/WA09 offline laboratory.
"""
import json
import os
from pathlib import Path

from .test_pg17_m2m import PhysicalM09Signed


def main():
    if os.environ.get('M09_PG17_DISPOSABLE') != 'YES':
        raise SystemExit('disposable PG17 required')
    destination=Path(os.environ['M09_PURPOSE_EVIDENCE'])
    if not destination.parent.is_dir() or destination.exists():
        raise SystemExit('exclusive empty destination required')
    PhysicalM09Signed.setUpClass()
    try:
        case=PhysicalM09Signed('test_signature_and_five_revisions_same_transaction')
        case.setUp()
        wire,signature=case.request()
        response=case.service.read(wire,signature)
        if response.get('decision') != 'AUTHENTICATED_READ_LAB_ONLY':
            raise RuntimeError('signed physical read denied')
        snapshot=response['snapshot']
        purpose='POST_APP_SECRET'
        with case.lab.admin() as c:
            names=c.execute(
                'SELECT slot_ref FROM s0_m09_lab.slots '
                'WHERE app_ref=%s AND purpose=%s',
                (snapshot['app_ref'],purpose)).fetchall()
        if len(names)!=1 or names[0]['slot_ref']!='POST_SLOT_A':
            raise RuntimeError('isolated PG17 slot inventory mismatch')
        witness={
            'contract_version':'prumo.s0.meta.purpose-slot-witness/0.1-lab',
            'app_ref':snapshot['app_ref'],
            'purpose':purpose,
            'slot_ref':names[0]['slot_ref'],
            'source_snapshot_ref':snapshot['snapshot_ref'],
            'source_role':'DISPOSABLE_PG17_INSTALLER_UNVERIFIED',
            'production_authorized':False,
            'send_authorized':False
        }
        keys=('concessionaria_id','app_ref','route_ref','canal_id',
              'waba_id','phone_number_id')
        artifact={
            'source':response,
            'witness':witness,
            'request':{
                'purpose':purpose,
                'scope':{key:snapshot[key] for key in keys},
                'expected_revisions':snapshot['revisions']
            }
        }
        encoded=json.dumps(artifact,sort_keys=True,separators=(',',':'))
        if any(x in encoded for x in ('private_key','public_key','password',
                                      'secret_value','access_token','signature')):
            raise RuntimeError('confidential evidence field')
        destination.write_text(encoded+'\n',encoding='utf-8')
        destination.chmod(0o600)
    finally:
        PhysicalM09Signed.tearDownClass()


if __name__=='__main__':
    main()
