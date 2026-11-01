"""Emit a real M09-04 PG17 signed-read LAB response for Node WA04A bridge tests.

Only runnable inside a dedicated disposable PG17 fixture. Never print an
Ed25519 private key, signature or SQL credentials. The fixture is terminated
and the inherited catalog compared by the original cleanup harness.
"""
import json
import os
from pathlib import Path

from .test_pg17_m2m import PhysicalM09Signed


def main():
    if os.environ.get('M09_PG17_DISPOSABLE') != 'YES':
        raise SystemExit('disposable PG17 required')
    target = Path(os.environ['M09_BRIDGE_EVIDENCE'])
    if not target.parent.is_dir():
        raise SystemExit('evidence destination must already exist')
    PhysicalM09Signed.setUpClass()
    try:
        case = PhysicalM09Signed('test_signature_and_five_revisions_same_transaction')
        case.setUp()
        wire, signature = case.request()
        response = case.service.read(wire, signature)
        if response.get('decision') != 'AUTHENTICATED_READ_LAB_ONLY':
            raise RuntimeError('signed PG17 read did not commit')
        snap = response['snapshot']
        if snap.get('revisions') != {
            'route':1, 'app':1, 'binding':1, 'grant':1, 'principal':1
        }:
            raise RuntimeError('PG17 independent revisions unavailable')
        serialized=json.dumps(response,sort_keys=True,separators=(',',':'))
        if any(secret in serialized for secret in ('private_key','public_key','signature',
                                                   'slot_ref','password')):
            raise RuntimeError('forbidden evidence field')
        target.write_text(serialized+'\n',encoding='utf-8')
        target.chmod(0o600)
    finally:
        PhysicalM09Signed.tearDownClass()


if __name__ == '__main__':
    main()
