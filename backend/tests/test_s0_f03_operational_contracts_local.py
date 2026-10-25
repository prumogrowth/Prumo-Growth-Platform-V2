"""E04 S0/F03 operational contracts: input shape and auth bridge guards."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from backend.tests.test_s0_f03_history_manifest_local import target
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_f03_bound_content_seal_local import (
    S0F03LocalBoundContentBridge,S0F03LocalBoundContentStore,
    BoundContentResult,BoundContentState,
)
from backend.s0_f03_operational_contracts_local import (
    FieldKind,ProposedField,proposal_digest,OperationalState,
    S0F03LocalOperationalContractsStore,S0F03LocalOperationalContractsBridge,
)
DSN='postgresql://postgres:fixture@localhost/prumo_s0_test_f03versions'
KEY=b'local-fixture-version-cas-key-more-than-32-byte'
FIELDS=(ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'texto ficticio'),)
V=VersionVector(1,1,1,1,1)
SHA=proposal_digest(FIELDS)

def setup():
    content=object.__new__(S0F03LocalBoundContentBridge)
    content._store=object.__new__(S0F03LocalBoundContentStore)
    content._store._dsn=DSN
    store=object.__new__(S0F03LocalOperationalContractsStore)
    store._dsn=DSN
    return S0F03LocalOperationalContractsBridge(content,store)

class Tests(unittest.TestCase):
    def test_01_stable_order_digest(self):
        second=ProposedField('produto_sintetico',FieldKind.CATALOG_CODE,'TESTE')
        self.assertEqual(proposal_digest(FIELDS+(second,)),
                         proposal_digest((second,)+FIELDS))

    def test_02_duplicate_fields_denied(self):
        self.assertIsNone(proposal_digest(FIELDS+FIELDS))

    def test_03_empty_fields_denied(self):
        self.assertIsNone(proposal_digest(()))

    def test_04_control_chars_denied(self):
        self.assertIsNone(proposal_digest((
            ProposedField('observacao_sintetica',FieldKind.TEXT_ONLY,'a\nb'),)))

    def test_05_no_s0_auth_no_contract_probe(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
             return_value=BoundContentResult(BoundContentState.DENIED)) as auth,\
             patch.object(S0F03LocalOperationalContractsStore,'check') as check:
            result=bridge.validate('fixture',target(),'test-key-v1',KEY,V,
                                   'request-cas-0001',SHA,FIELDS)
        self.assertIs(result.state,OperationalState.STALE_REVIEW_REQUIRED)
        check.assert_not_called()
        self.assertEqual(auth.call_count,1)

    def test_06_both_s0_auth_checks_for_positive_result(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify',
             return_value=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)) as auth,\
             patch.object(S0F03LocalOperationalContractsStore,'check',
             return_value=OperationalState.CONTRACT_REVIEW_ONLY) as check:
            result=bridge.validate('fixture',target(),'test-key-v1',KEY,V,
                                   'request-cas-0001',SHA,FIELDS)
        self.assertIs(result.state,OperationalState.CONTRACT_REVIEW_ONLY)
        self.assertEqual(auth.call_count,2)
        self.assertEqual(check.call_count,1)
        self.assertEqual(tuple(vars(result)),('state',))

    def test_07_revoked_after_contract_check_returns_stale(self):
        bridge=setup()
        yes=BoundContentResult(BoundContentState.MATCHES_REVIEW_ONLY)
        no=BoundContentResult(BoundContentState.STALE_REVIEW_REQUIRED)
        with patch.object(S0F03LocalBoundContentBridge,'verify',
             side_effect=[yes,no]),\
             patch.object(S0F03LocalOperationalContractsStore,'check',
             return_value=OperationalState.CONTRACT_REVIEW_ONLY):
            result=bridge.validate('fixture',target(),'test-key-v1',KEY,V,
                                   'request-cas-0001',SHA,FIELDS)
        self.assertIs(result.state,OperationalState.STALE_REVIEW_REQUIRED)

    def test_08_invalid_secret_denied_before_auth(self):
        bridge=setup()
        with patch.object(S0F03LocalBoundContentBridge,'verify') as auth,\
             patch.object(S0F03LocalOperationalContractsStore,'check') as check:
            result=bridge.validate('fixture',target(),'test-key-v1',b'short',V,
                                   'request-cas-0001',SHA,FIELDS)
        self.assertIs(result.state,OperationalState.DENIED)
        auth.assert_not_called()
        check.assert_not_called()

if __name__=='__main__':
    unittest.main()
