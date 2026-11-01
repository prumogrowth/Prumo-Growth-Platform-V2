"""Two signed M09-04 observations + revocation in a disposable PG17.

Signature credentials for these ATTESTATIONS are ephemeral and independent
from the M09 M2M request signing key. Their trust anchor is only a test
fixture. This proves lab integrity, NOT production S0 issuer identity,
slot-redemption rights, hosted trust, or atomicity with an actual dispatch.
"""
import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .pg17_registry import revoke_channel_in_admin_transaction
from .test_pg17_m2m import PhysicalM09Signed

DOMAIN=b'PRUMO.S0.M09.ATTEST.RECHECK/0.1\x00'
VERSION='prumo.s0.meta.origin-recheck/0.1-lab'
SCOPE=('concessionaria_id','app_ref','route_ref','canal_id','waba_id','phone_number_id')


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),
                      ensure_ascii=True,allow_nan=False).encode('ascii')


def b64url(b):
    return base64.urlsafe_b64encode(b).decode('ascii').rstrip('=')


def main():
    if os.environ.get('M09_PG17_DISPOSABLE')!='YES':
        raise SystemExit('disposable S0 PG17 required')
    destination=Path(os.environ['M09_ORIGIN_EVIDENCE'])
    if not destination.parent.is_dir() or destination.exists():
        raise SystemExit('exclusive temporary output required')
    PhysicalM09Signed.setUpClass()
    try:
        case=PhysicalM09Signed('test_signature_and_five_revisions_same_transaction')
        case.setUp()
        def physical():
            wire,sig=case.request()
            outcome=case.service.read(wire,sig)
            if outcome['decision']!='AUTHENTICATED_READ_LAB_ONLY':
                raise RuntimeError('M09-04 physical signature/read unavailable')
            with case.lab.admin() as c:
                names=c.execute(
                    "SELECT slot_ref FROM s0_m09_lab.slots "
                    "WHERE app_ref='APP_A' AND purpose='POST_APP_SECRET'").fetchall()
            if len(names)!=1 or names[0]['slot_ref']!='POST_SLOT_A':
                raise RuntimeError('disposable single-slot fixture inconsistent')
            return outcome['snapshot'],names[0]['slot_ref']
        original,original_slot=physical()
        fresh,fresh_slot=physical()
        if (original['snapshot_ref']!=fresh['snapshot_ref'] or
            original['revisions']!=fresh['revisions'] or original_slot!=fresh_slot):
            raise RuntimeError('concurrent change before signed recheck')
        key=Ed25519PrivateKey.generate()  # only in this disposable process
        with case.lab.admin() as c:
            observed=c.execute("SELECT clock_timestamp() AS now").fetchone()['now']
        now_ms=int(observed.timestamp()*1000)
        origin_nonce='A'*24
        fresh_nonce='B'*24
        def envelope(snapshot,kind,nonce,parent_nonce,issued_ms):
            body={
                'contract_version':VERSION,
                'kind':kind,'issuer_ref':'M09_S0_LAB',
                'audience':'LAB_META_CONSUMER',
                'purpose':'POST_APP_SECRET',
                'scope':{k:snapshot[k] for k in SCOPE},
                'revisions':snapshot['revisions'],
                'source_snapshot_ref':snapshot['snapshot_ref'],
                'slot_ref':original_slot,
                'issued_ms':issued_ms,'expires_ms':now_ms+25000,
                'nonce':nonce,'parent_nonce':parent_nonce
            }
            return {'payload':body,'signature':b64url(key.sign(DOMAIN+canonical(body)))}
        origin=envelope(original,'ORIGIN',origin_nonce,None,now_ms-100)
        rechecked=envelope(fresh,'RECHECK',fresh_nonce,origin_nonce,now_ms)
        expected={'purpose':'POST_APP_SECRET',
                  'scope':origin['payload']['scope'],
                  'revisions':origin['payload']['revisions'],
                  'source_snapshot_ref':original['snapshot_ref']}
        # Demonstrate why *even two valid attestations* never authorize a
        # later use: revoke AFTER them and prove a new signed read denies.
        with case.lab.admin() as c:
            status=revoke_channel_in_admin_transaction(
                c,'route_A','channel_A',1,1,1,1)
        if status!='REVOKED_IN_DISPOSABLE_TRANSACTION':
            raise RuntimeError('physical revoke did not commit')
        third_wire,third_sig=case.request()
        latest=case.service.read(third_wire,third_sig)
        if latest['decision']=='AUTHENTICATED_READ_LAB_ONLY':
            raise RuntimeError('revoked source still accepted by M09-04')
        # This public key is bundled with fixture; it is NOT an independently
        # provisioned trust anchor. Consumers cannot use it operationally.
        public=key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        artifact={
            'lab_only':True,'actual_m2m_reads':2,
            'revoked_after_observations':True,
            'origin':origin,'fresh':rechecked,'expected':expected,
            'fixture_public_key_spki':b64url(public),
            'observed_now_ms':now_ms
        }
        raw=canonical(artifact).decode('ascii')
        if any(s in raw for s in ('private_key','secret_value','access_token_value',
                                   'password','graph_bearer')):
            raise RuntimeError('forbidden evidence data')
        destination.write_text(raw+'\n',encoding='ascii')
        destination.chmod(0o600)
    finally:
        PhysicalM09Signed.tearDownClass()


if __name__=='__main__':
    main()
