"""Unit tests of S0-authenticated content-proof bridge, without external providers."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.tests.test_s0_f03_history_manifest_local import target
from backend.s0_f03_history_seal_local import (
    S0F03LocalHistorySealingBridge, S0F03LocalManifestSealStore,
    SealResult, SealState,
)
from backend.s0_f03_history_manifest_local import S0F03LocalPostgresHistoryReader
from backend.s0_f03_bound_content_seal_local import (
    S0F03LocalBoundContentBridge, S0F03LocalBoundContentStore,
    BoundContentState, _valid,
)

DSN='postgresql://postgres:fixture@localhost/prumo_s0_test_f03bound'
KEY_ID='f03-content-v1'
KEY=b'only-for-synthetic-F03-content-integrity-tests-123'

def sut():
    history=object.__new__(S0F03LocalHistorySealingBridge)
    reader=object.__new__(S0F03LocalPostgresHistoryReader)
    manifest=object.__new__(S0F03LocalManifestSealStore)
    content=object.__new__(S0F03LocalBoundContentStore)
    reader._dsn=manifest._dsn=content._dsn=DSN
    history._reader=reader
    history._store=manifest
    return S0F03LocalBoundContentBridge(history,content),history,content

class Tests(unittest.TestCase):
    def test_01_valid_binding_and_test_key(self):
        self.assertTrue(_valid(target(),KEY_ID,KEY))
    def test_02_model_supplied_dict_is_not_binding(self):
        self.assertFalse(_valid({'store_ref':'fake'},KEY_ID,KEY))
    def test_03_short_key_blocks_before_db_and_auth(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify') as gate,\
             patch.object(S0F03LocalBoundContentStore,'check') as db:
            result=bridge.seal('token',target(),KEY_ID,b'short')
        self.assertIs(result.state,BoundContentState.DENIED)
        gate.assert_not_called();db.assert_not_called()
    def test_04_invalid_key_version_blocks(self):
        bridge,h,s=sut()
        self.assertIs(bridge.seal('token',target(),'../../../x',KEY).state,
                      BoundContentState.DENIED)
    def test_05_unratified_history_blocks_without_storage(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          return_value=SealResult(SealState.HISTORY_INCOMPLETE)) as auth,\
             patch.object(S0F03LocalBoundContentStore,'check') as db:
            result=bridge.seal('token',target(),KEY_ID,KEY)
        self.assertIs(result.state,BoundContentState.STALE_REVIEW_REQUIRED)
        self.assertEqual(auth.call_count,1);db.assert_not_called()
    def test_06_recheck_before_and_after_success(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          return_value=SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)) as auth,\
             patch.object(S0F03LocalBoundContentStore,'check',
                          return_value=BoundContentState.SEALED_REVIEW_ONLY) as db:
            result=bridge.seal('token',target(),KEY_ID,KEY)
        self.assertIs(result.state,BoundContentState.SEALED_REVIEW_ONLY)
        self.assertEqual(auth.call_count,2)
        self.assertEqual(db.call_count,1)
        self.assertTrue(db.call_args.kwargs['create'])
    def test_07_read_only_verification_uses_existing_proof(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          return_value=SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)),\
             patch.object(S0F03LocalBoundContentStore,'check',
                          return_value=BoundContentState.MATCHES_REVIEW_ONLY) as db:
            result=bridge.verify('token',target(),KEY_ID,KEY)
        self.assertIs(result.state,BoundContentState.MATCHES_REVIEW_ONLY)
        self.assertFalse(db.call_args.kwargs['create'])
    def test_08_authorization_revoked_after_commit_is_not_success(self):
        bridge,h,s=sut()
        statuses=[SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY),
                  SealResult(SealState.DENIED)]
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          side_effect=statuses),\
             patch.object(S0F03LocalBoundContentStore,'check',
                          return_value=BoundContentState.SEALED_REVIEW_ONLY):
            result=bridge.seal('token',target(),KEY_ID,KEY)
        self.assertIs(result.state,BoundContentState.STALE_REVIEW_REQUIRED)
    def test_09_persisted_content_mismatch_fails_closed(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          return_value=SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)),\
             patch.object(S0F03LocalBoundContentStore,'check',
                          return_value=BoundContentState.STALE_REVIEW_REQUIRED):
            self.assertIs(bridge.verify('token',target(),KEY_ID,KEY).state,
                          BoundContentState.STALE_REVIEW_REQUIRED)
    def test_10_local_dsn_required_for_store(self):
        with self.assertRaises(ValueError):
            S0F03LocalBoundContentStore('postgresql://postgres:x@hosted.invalid/bank')
    def test_11_database_mismatch_rejected_before_any_io(self):
        bridge,h,s=sut()
        s._dsn='postgresql://postgres:fixture@localhost/prumo_s0_test_other'
        with self.assertRaises(TypeError):
            S0F03LocalBoundContentBridge(h,s)
    def test_12_only_state_visible_in_result(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          return_value=SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)),\
             patch.object(S0F03LocalBoundContentStore,'check',
                          return_value=BoundContentState.MATCHES_REVIEW_ONLY):
            result=bridge.verify('token',target(),KEY_ID,KEY)
        self.assertEqual(tuple(vars(result)),('state',))
        self.assertFalse(hasattr(result,'content_mac_sha256'))
        self.assertFalse(hasattr(result,'content'))
        self.assertFalse(hasattr(result,'key'))
    def test_13_history_verification_exception_fails_closed(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          side_effect=RuntimeError('private details')):
            self.assertIs(bridge.seal('token',target(),KEY_ID,KEY).state,
                          BoundContentState.UNAVAILABLE)
    def test_14_store_error_fails_closed(self):
        bridge,h,s=sut()
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          return_value=SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)),\
             patch.object(S0F03LocalBoundContentStore,'check',
                          side_effect=RuntimeError('unavailable')):
            self.assertIs(bridge.seal('token',target(),KEY_ID,KEY).state,
                          BoundContentState.UNAVAILABLE)
    def test_15_multiple_key_rotation_versions_are_not_accepted_as_same_receipt(self):
        bridge,h,s=sut()
        self.assertTrue(_valid(target(),'f03-content-v2',KEY))
        # Key version can be syntactically valid, but an existing append-only
        # record rejects it physically; see PG17 test_18.
        with patch.object(S0F03LocalHistorySealingBridge,'verify',
                          return_value=SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)),\
             patch.object(S0F03LocalBoundContentStore,'check',
                          return_value=BoundContentState.STALE_REVIEW_REQUIRED):
            self.assertIs(bridge.seal('token',target(),'f03-content-v2',KEY).state,
                          BoundContentState.STALE_REVIEW_REQUIRED)

if __name__=='__main__':
    unittest.main()
