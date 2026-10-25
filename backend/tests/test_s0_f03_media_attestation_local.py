"""Only synthetic E04 media hash/retention attestation, no STT or API."""
import unittest,uuid
from datetime import datetime,timezone,timedelta
from backend.s0_f03_media_attestation_local import (
    _digest,_proof_hmac,MediaAttestationState,MediaAttestationResult,
    S0F03LocalMediaAttestationBridge,
)
K=b'e04-synthetic-strong-media-test-secret-over-32-bytes'
U=[str(uuid.uuid4()) for _ in range(4)]
EXP=datetime.now(timezone.utc)+timedelta(days=1)
class Tests(unittest.TestCase):
    def test_01_synthetic_bytes_digest_and_unicode_text(self):
        d=_digest(b'fixture-audio','\u00c1udio fict\u00edcio')
        self.assertEqual(len(d[0]),64)
        self.assertEqual(len(d[1]),64)
    def test_02_untrusted_string_not_media_bytes(self):
        self.assertIsNone(_digest('audio', 'texto'))
    def test_03_blank_transcript_rejected(self):
        self.assertIsNone(_digest(b'audio', ' '))
    def test_04_embedded_null_rejected(self):
        self.assertIsNone(_digest(b'audio','abc\x00def'))
    def test_05_mismatched_trailing_space_rejected(self):
        self.assertIsNone(_digest(b'audio','texto '))
    def test_06_too_large_media_rejected(self):
        self.assertIsNone(_digest(b'a'*2097153,'texto'))
    def test_07_hmac_binds_every_uuid_and_expiry(self):
        b='a'*64
        a=_proof_hmac(K,*U,'key-v1-good',b,b,EXP)
        self.assertEqual(len(a),64)
        self.assertNotEqual(a,_proof_hmac(K,*U,'key-v2-good',b,b,EXP))
        self.assertNotEqual(a,_proof_hmac(K,*U,'key-v1-good',b,b,EXP+timedelta(days=1)))
    def test_08_bad_uuid_denied(self):
        self.assertIsNone(_proof_hmac(K,'shop',*U[1:],'key-v1-good','a'*64,'a'*64,EXP))
    def test_09_media_result_returns_only_state(self):
        self.assertEqual(tuple(vars(MediaAttestationResult(
            MediaAttestationState.MEDIA_DIGEST_REVIEW_ONLY))),('state',))
    def test_10_nonphysical_base_rejected(self):
        with self.assertRaises(TypeError):
            S0F03LocalMediaAttestationBridge(object())
if __name__=='__main__':
    unittest.main()
