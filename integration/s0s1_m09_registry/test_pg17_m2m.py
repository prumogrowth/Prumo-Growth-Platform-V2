"""M09-04 physical Ed25519 signed read tests on exclusive disposable PostgreSQL 17."""
import os
from pathlib import Path
import secrets
from concurrent.futures import ThreadPoolExecutor
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .pg17_m2m import (AuthenticatedM09, DOMAIN, WIRE_VERSION,
                      canonical, parse)
from .port import FLAGS


@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE') == 'YES',
                     'requires pinned disposable PG17 fixture')
class PhysicalM09Signed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse the identical 13-case M09-03 fixture without importing its
        # TestCase into this module's unittest discovery namespace.
        from . import test_pg17_registry as previous
        cls.base = previous.PhysicalRegistryM09
        cls.base.setUpClass.__func__(cls)
        try:
            sql=(cls.origin/'integration/s0s1_m09_registry/pg17_m2m_journal.sql').read_text()
            with cls.lab.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute("SET s0_m09.install='M2M_CANDIDATE_ONLY'")
                c.execute(sql)
        except BaseException:
            cls.base.tearDownClass.__func__(cls)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.base.tearDownClass.__func__(cls)

    def setUp(self):
        self.base.setUp(self)
        self.private=Ed25519PrivateKey.generate()
        with self.lab.admin() as c:
            c.execute('UPDATE s0_meta_lab.principals SET public_key=%s '
                      "WHERE key_id='M09_KEY_A'",
                      (self.private.public_key().public_bytes_raw(),))
        self.service=AuthenticatedM09(
            self.lab.runtime_dsn,lambda ref:self.host.get(ref))

    def request(self, *, nonce=None, host_ref='valid', issued_delta=0,
                expires_delta=60000, **changes):
        with self.lab.admin() as c:
            now=c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
        ms=int(now.timestamp()*1000)
        envelope={'version':WIRE_VERSION,'key_id':'M09_KEY_A',
                  'issuer_ref':'M09_ISSUER','key_revision':1,
                  'audience':'LAB_S0_M09','purpose':'REGISTRY_READ',
                  'nonce':nonce or secrets.token_urlsafe(24),
                  'issued_ms':ms+issued_delta,
                  'expires_ms':ms+expires_delta,
                  'host_ref':host_ref,'route_ref':'route_A','app_ref':'APP_A'}
        envelope.update(changes)
        wire=canonical(envelope)
        return wire,self.private.sign(DOMAIN+wire)

    def deny(self,x):
        self.assertNotEqual(x['decision'],'AUTHENTICATED_READ_LAB_ONLY')
        self.assertIsNone(x['snapshot'])
        self.assertTrue(all(x[k] is False for k in FLAGS))

    def test_signature_and_five_revisions_same_transaction(self):
        wire,sig=self.request()
        x=self.service.read(wire,sig)
        self.assertEqual(x['decision'],'AUTHENTICATED_READ_LAB_ONLY')
        self.assertEqual(x['snapshot']['revisions'],
              {'route':1,'app':1,'binding':1,'grant':1,'principal':1})
        self.assertNotIn('slot_ref',x['snapshot'])
        with self.lab.admin() as c:
            self.assertEqual(c.execute(
                "SELECT count(*) AS n FROM s0_m09_lab.read_nonces").fetchone()['n'],1)

    def test_exact_replay_is_rejected_with_db_unique(self):
        wire,sig=self.request()
        self.assertEqual(self.service.read(wire,sig)['decision'],
                         'AUTHENTICATED_READ_LAB_ONLY')
        self.assertEqual(self.service.read(wire,sig)['reason'],'NONCE_REPLAY')

    def test_two_threads_one_nonce_wins(self):
        wire,sig=self.request()
        with ThreadPoolExecutor(max_workers=2) as pool:
            runs=[pool.submit(self.service.read,wire,sig) for _ in range(2)]
            results=[f.result(timeout=10)['decision'] for f in runs]
        self.assertCountEqual(results,
              ['AUTHENTICATED_READ_LAB_ONLY','DENIED'])

    def test_same_nonce_different_signed_payload_is_denied(self):
        nonce=secrets.token_urlsafe(24)
        a,sa=self.request(nonce=nonce)
        b,sb=self.request(nonce=nonce,expires_delta=65000)
        self.assertEqual(self.service.read(a,sa)['decision'],
                         'AUTHENTICATED_READ_LAB_ONLY')
        self.assertEqual(self.service.read(b,sb)['reason'],'NONCE_REPLAY')

    def test_distinct_nonce_valid_new_request(self):
        a,sa=self.request()
        b,sb=self.request()
        self.assertEqual(self.service.read(a,sa)['decision'],
                         'AUTHENTICATED_READ_LAB_ONLY')
        self.assertEqual(self.service.read(b,sb)['decision'],
                         'AUTHENTICATED_READ_LAB_ONLY')

    def test_changed_wire_or_signature_denied_without_nonce(self):
        wire,sig=self.request()
        x=self.service.read(wire,bytes(64))
        self.assertEqual(x['reason'],'INVALID_SIGNATURE')
        self.assertEqual(self.service.read(wire,sig)['decision'],
                         'AUTHENTICATED_READ_LAB_ONLY')
        different=wire.replace(b'"APP_A"',b'"APP_B"')
        self.deny(self.service.read(different,sig))

    def test_duplicate_json_key_noncanonical_and_extra_field_denied(self):
        wire,sig=self.request()
        self.assertEqual(self.service.read(wire+b' ',sig)['reason'],
                         'INVALID_ENVELOPE')
        malformed=wire[:-1]+b',"nonce":"AAAAAAAAAAAAAAAA"}'
        self.assertEqual(self.service.read(malformed,sig)['reason'],
                         'INVALID_ENVELOPE')
        from json import loads
        value=loads(wire)
        value['admin']=True
        raw=canonical(value)
        self.assertEqual(self.service.read(raw,self.private.sign(DOMAIN+raw))['reason'],
                         'INVALID_ENVELOPE')

    def test_wrong_domain_and_wrong_issuer(self):
        wire,sig=self.request()
        self.assertEqual(self.service.read(wire,self.private.sign(b'OTHER'+wire))['reason'],
                         'INVALID_SIGNATURE')
        w,s=self.request(issuer_ref='OTHER')
        self.deny(self.service.read(w,s))

    def test_missing_host_or_cross_store_does_not_grant(self):
        wire,sig=self.request(host_ref='missing')
        self.deny(self.service.read(wire,sig))
        wire,sig=self.request(host_ref='other',route_ref='route_B',app_ref='APP_B')
        self.deny(self.service.read(wire,sig))

    def test_future_and_expired_windows_denied(self):
        wire,sig=self.request(issued_delta=90000,expires_delta=110000)
        self.assertEqual(self.service.read(wire,sig)['reason'],'EXPIRED')
        wire,sig=self.request(issued_delta=-180000,expires_delta=-120000)
        self.assertEqual(self.service.read(wire,sig)['reason'],'EXPIRED')

    def test_invalid_declared_purpose_and_revision(self):
        for changed in ({'purpose':'GRAPH_ACCESS_TOKEN'},
                        {'key_revision':True},{'audience':'PRODUCTION'}):
            wire,sig=self.request(**changed)
            self.deny(self.service.read(wire,sig))

    def test_revoked_grant_after_signing_never_succeeds(self):
        wire,sig=self.request()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_m09_lab.grants SET active=false,revision=2 "
                      "WHERE canal_id='channel_A'")
        self.deny(self.service.read(wire,sig))

    def test_rotate_public_key_and_revision_invalidates_old_signature(self):
        old_wire,old_sig=self.request()
        new=Ed25519PrivateKey.generate()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.principals SET revision=2,public_key=%s "
                      "WHERE key_id='M09_KEY_A'",
                      (new.public_key().public_bytes_raw(),))
        self.deny(self.service.read(old_wire,old_sig))
        self.private=new
        new_wire,new_sig=self.request(key_revision=2)
        self.assertEqual(self.service.read(new_wire,new_sig)['decision'],
                         'AUTHENTICATED_READ_LAB_ONLY')

    def test_runtime_cannot_select_delete_or_update_nonce_rows(self):
        wire,sig=self.request()
        self.assertEqual(self.service.read(wire,sig)['decision'],
                         'AUTHENTICATED_READ_LAB_ONLY')
        import psycopg
        for command in ('SELECT * FROM s0_m09_lab.read_nonces',
                        'DELETE FROM s0_m09_lab.read_nonces',
                        "UPDATE s0_m09_lab.read_nonces SET nonce='OVERRIDEOVERRIDE01'"):
            with psycopg.connect(self.lab.runtime_dsn) as c:
                with self.assertRaises(psycopg.Error):
                    c.execute(command)

    def test_stale_expected_revision_consumes_nonce_and_denies(self):
        wire,sig=self.request()
        d=self.service.read(wire,sig,expected={
            'route':2,'app':1,'binding':1,'grant':1,'principal':1})
        self.assertEqual(d['decision'],'STALE_OR_REVOKED')
        self.assertEqual(self.service.read(wire,sig)['reason'],'NONCE_REPLAY')

    def test_no_send_ack_or_production_authority(self):
        wire,sig=self.request()
        x=self.service.read(wire,sig)
        self.assertTrue(all(x[k] is False for k in FLAGS))
        self.assertEqual(x['snapshot']['ownership_evidence_state'],'UNVERIFIED')

if __name__ == '__main__':
    unittest.main()
