"""Offline-only unit tests for S0 F03 independent version-vector CAS gate."""
from __future__ import annotations

import unittest
from unittest.mock import patch
from backend.tests.test_s0_f03_history_manifest_local import target
from backend.s0_f03_bound_content_seal_local import (
    S0F03LocalBoundContentBridge,S0F03LocalBoundContentStore,
    BoundContentResult,BoundContentState,
)
from backend.s0_f03_version_reservation_local import (
    S0F03LocalVersionReservationStore,S0F03LocalVersionReservationBridge,
    ReservationState,VersionVector,_validated,
)
DSN='postgresql://postgres:fixture@localhost/prumo_s0_test_f03versions'
KEY=b'local-fixture-version-cas-key-more-than-32-byte'
ID='test-key-v1'
SHA='b'*64
REQUEST='request-cas-0001'
V=VersionVector(1,1,1,1,1)

def setup():
    content=object.__new__(S0F03LocalBoundContentBridge)
    content._store=object.__new__(S0F03LocalBoundContentStore)
    content._store._dsn=DSN
    store=object.__new__(S0F03LocalVersionReservationStore)
    store._dsn=DSN
    return S0F03LocalVersionReservationBridge(content,store)

class Tests(unittest.TestCase):
    def test_01_verified_shape(self):
        self.assertTrue(_validated(target(),V,REQUEST,SHA,ID))
    def test_02_fake_dict_is_denied(self):
        self.assertFalse(_validated({'model':'yes'},V,REQUEST,SHA,ID))
    def test_03_zero_form_version_denied(self):
        self.assertFalse(_validated(target(),VersionVector(0,1,1,1,1),REQUEST,SHA,ID))
    def test_04_boolean_version_denied(self):
        self.assertFalse(_validated(target(),VersionVector(True,1,1,1,1),REQUEST,SHA,ID))
    def test_05_negative_catalogue_version_denied(self):
        self.assertFalse(_validated(target(),VersionVector(1,-1,1,1,1),REQUEST,SHA,ID))
    def test_06_bad_request_denied(self):
        self.assertFalse(_validated(target(),V,'../',SHA,ID))
    def test_07_bad_sha_denied(self):
        self.assertFalse(_validated(target(),V,REQUEST,'not-a-sha',ID))
    def test_08_invalid_version_key_denied(self):
        self.assertFalse(_validated(target(),V,REQUEST,SHA,'with space'))
    def test_09_external_database_denied(self):
        with self.assertRaises(ValueError):
            S0F03LocalVersionReservationStore('postgresql://postgres:x@hosted.example.com/actual')
    def test_10_mismatched_local_databases_rejected(self):
        bridge=setup()
        store=object.__new__(S0F03LocalVersionReservationStore)
        store._dsn='postgresql://postgres:fixture@localhost/prumo_s0_test_different'
        with self.assertRaises(TypeError):
            S0F03LocalVersionReservationBridge(bridge._content,store)
    def test_11_no_authorization_means_no_mutation(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
                          return_value=BoundContentResult(BoundContentState.DENIED)) as auth,\
             patch.object(S0F03LocalVersionReservationStore,'reserve') as store:
            r=bridge.reserve('token',target(),ID,KEY,V,REQUEST,SHA)
        self.assertIs(r.state,ReservationState.STALE_REVIEW_REQUIRED)
        self.assertEqual(auth.call_count,1)
        store.assert_not_called()
    def test_12_rechecks_before_and_after_advisory_reservation(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
                          return_value=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)) as auth,\
             patch.object(S0F03LocalVersionReservationStore,'reserve',
                          return_value=ReservationState.RESERVED_REVIEW_ONLY) as store:
            r=bridge.reserve('token',target(),ID,KEY,V,REQUEST,SHA)
        self.assertIs(r.state,ReservationState.RESERVED_REVIEW_ONLY)
        self.assertEqual(auth.call_count,2)
        self.assertEqual(store.call_count,1)
    def test_13_idempotent_replay_has_same_two_rechecks(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
                          return_value=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)) as auth,\
             patch.object(S0F03LocalVersionReservationStore,'reserve',
                          return_value=ReservationState.ALREADY_HANDLED_REVIEW_ONLY):
            r=bridge.reserve('token',target(),ID,KEY,V,REQUEST,SHA)
        self.assertIs(r.state,ReservationState.ALREADY_HANDLED_REVIEW_ONLY)
        self.assertEqual(auth.call_count,2)
    def test_14_post_authorization_loss_fails_closed(self):
        bridge=setup()
        before=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)
        after=BoundContentResult(BoundContentState.STALE_REVIEW_REQUIRED)
        with patch.object(S0F03LocalBoundContentBridge,'verify',
                          side_effect=[before,after]),\
             patch.object(S0F03LocalVersionReservationStore,'reserve',
                          return_value=ReservationState.RESERVED_REVIEW_ONLY):
            r=bridge.reserve('token',target(),ID,KEY,V,REQUEST,SHA)
        self.assertIs(r.state,ReservationState.STALE_REVIEW_REQUIRED)
    def test_15_stale_vector_stops_without_second_recheck(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
                          return_value=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)) as auth,\
             patch.object(S0F03LocalVersionReservationStore,'reserve',
                          return_value=ReservationState.STALE_REVIEW_REQUIRED):
            r=bridge.reserve('token',target(),ID,KEY,V,REQUEST,SHA)
        self.assertIs(r.state,ReservationState.STALE_REVIEW_REQUIRED)
        self.assertEqual(auth.call_count,1)
    def test_16_store_error_returns_unavailable_without_exception_leak(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
                          return_value=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)),\
             patch.object(S0F03LocalVersionReservationStore,'reserve',
                          side_effect=RuntimeError('private SQL detail')):
            r=bridge.reserve('token',target(),ID,KEY,V,REQUEST,SHA)
        self.assertIs(r.state,ReservationState.UNAVAILABLE)
    def test_17_result_has_no_proposal_or_customer_content(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
                          return_value=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)),\
             patch.object(S0F03LocalVersionReservationStore,'reserve',
                          return_value=ReservationState.RESERVED_REVIEW_ONLY):
            r=bridge.reserve('token',target(),ID,KEY,V,REQUEST,SHA)
        self.assertEqual(tuple(vars(r)),('state',))
        self.assertFalse(hasattr(r,'fields'))
        self.assertFalse(hasattr(r,'secret'))
    def test_18_invalid_secret_rejected_before_authorization(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify') as auth,\
             patch.object(S0F03LocalVersionReservationStore,'reserve') as store:
            r=bridge.reserve('token',target(),ID,b'short',V,REQUEST,SHA)
        self.assertIs(r.state,ReservationState.DENIED)
        auth.assert_not_called();store.assert_not_called()

if __name__=='__main__':
    unittest.main()
