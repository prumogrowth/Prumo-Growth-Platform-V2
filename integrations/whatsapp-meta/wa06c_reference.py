"""WA-06C independent Python wire vectors for the PROPOSED Meta/S0 interface.

No network, database, credentials, cryptographic origin assertion or ACK logic.
Uses only the Python standard library; not a production S0 verifier.
"""
import copy
import hashlib
import struct
import unittest

DOMAIN = b'PRUMO:WA06B:PROOF:V1\0'
CLAIM_FIELDS = ('proof_version', 'canonicalization_version', 'service_ref',
                'request_ref', 'nonce_ref', 'key_epoch', 'purpose', 'audience',
                'issued_at_ms', 'expires_at_ms')
BATCH_FIELDS = ('contract_version', 'batch_ref', 'route_ref', 'route_revision',
                'app_ref', 'protected_payload_ref', 'payload_sha256',
                'scope_sha256', 'event_count', 'ack_allowed', 'production_authorized')
ITEM_FIELDS = ('entry_index', 'change_index', 'array_kind', 'item_index',
               'event_kind', 'app_ref', 'concessionaria_id', 'canal_id', 'waba_id',
               'phone_number_id', 'provider_message_id', 'provider_timestamp',
               'provider_kind')

# Fixed corpus — test strings are fictitious; no telephone numbers or tokens.
EXPECTED = {
    'BASE': (585, 'c94993710cfc4a90d41314c89026385e7cbd446753b2fa7d0ec0cc7f65083209'),
    'NONCE_ROTATED': (585, '219aec893fc30e0f96870d1170643033c8b169515c853085dc58baba6ef3e549'),
    'CALLBACK_REPEAT': (736, '577cad6732765d18b4ee62af0feef71d2c62c86023a8ecd406f8ca3e2977f5e5'),
    'TWO_CHANNELS': (736, '444411a4acf020fb799fd3aeb78b85f77ec0b482f0d10fdf1d91508e1b9cb267'),
    'READ_STATUS': (580, '9dc572689a0ec12fdb45b6b21f8ddddad44aa1f10d1ef6acd32a911f1889eb93'),
}


def base_fixture():
    claims = {
        'proof_version': 'prumo.meta-s0.proof.v1-candidate',
        'canonicalization_version': 'prumo.meta-s0.binlen.v1-candidate',
        'service_ref': 'meta_ingestor', 'request_ref': 'req_1',
        'nonce_ref': 'nonce_1', 'key_epoch': 1,
        'purpose': 'meta_s0.ingest', 'audience': 's0_internal_ingress',
        'issued_at_ms': 1000, 'expires_at_ms': 2000,
    }
    item = {
        'position': {'entry_index': 0, 'change_index': 0,
                     'array_kind': 'statuses', 'item_index': 0},
        'event_kind': 'status_callback', 'app_ref': 'app_a',
        'concessionaria_id': 'loja_a', 'canal_id': 'canal_a',
        'waba_id': 'waba_a', 'phone_number_id': 'phone_a',
        'provider_message_id': 'wamid.ID=',
        'provider_timestamp': '2026-10-18T12:00:00.000Z',
        'provider_kind': 'delivered',
    }
    candidate = {
        'contract_version': 'meta-s0-handoff.v0.1-proposed',
        'batch_ref': 'batch_1', 'route_ref': 'route_1',
        'route_revision': 1, 'app_ref': 'app_a',
        'protected_payload_ref': 'payload_1',
        'payload_sha256': 'a' * 64, 'scope_sha256': 'b' * 64,
        'event_count': 1, 'occurrences': [item],
        'ack_allowed': False, 'production_authorized': False,
    }
    return claims, candidate


def fixture_for(case):
    claims, candidate = base_fixture()
    if case == 'BASE':
        pass
    elif case == 'NONCE_ROTATED':
        claims['nonce_ref'] = 'nonce_2'
    elif case in ('CALLBACK_REPEAT', 'TWO_CHANNELS'):
        second = copy.deepcopy(candidate['occurrences'][0])
        second['position']['item_index'] = 1
        if case == 'TWO_CHANNELS':
            second['canal_id'] = 'canal_b'
            second['phone_number_id'] = 'phone_b'
        candidate['occurrences'].append(second)
        candidate['event_count'] = 2
    elif case == 'READ_STATUS':
        candidate['occurrences'][0]['provider_kind'] = 'read'
    else:
        raise ValueError('UNKNOWN_FIXTURE')
    return claims, candidate


def encode_ref(claims, candidate):
    """Independent reference: fixed fields + BE uint32 UTF-8 lengths.

    This is only a consistency oracle for known synthetic inputs; not an
    authentication, authorization or strict untrusted-input parser.
    """
    values = [claims[k] for k in CLAIM_FIELDS]
    values.extend(candidate[k] for k in BATCH_FIELDS)
    for item in candidate['occurrences']:
        position = item['position']
        values.extend(position[k] if k in position else item[k] for k in ITEM_FIELDS)
    out = bytearray(DOMAIN)
    for value in values:
        if value is False:
            text = 'false'
        elif value is True:
            text = 'true'
        else:
            text = str(value)
        raw = text.encode('utf-8')
        out.extend(struct.pack('>I', len(raw)))
        out.extend(raw)
    return bytes(out)


class CrossRuntimeVectorTests(unittest.TestCase):
    def test_five_vectors(self):
        for case, (length, expected_hash) in EXPECTED.items():
            with self.subTest(case=case):
                claims, candidate = fixture_for(case)
                encoded = encode_ref(claims, candidate)
                self.assertEqual(len(encoded), length)
                self.assertEqual(hashlib.sha256(encoded).hexdigest(), expected_hash)
                self.assertEqual(encoded[:len(DOMAIN)], DOMAIN)

    def test_reference_fields_are_independent(self):
        base = hashlib.sha256(encode_ref(*fixture_for('BASE'))).digest()
        for case in ('NONCE_ROTATED', 'CALLBACK_REPEAT', 'TWO_CHANNELS', 'READ_STATUS'):
            with self.subTest(case=case):
                self.assertNotEqual(hashlib.sha256(encode_ref(*fixture_for(case))).digest(), base)


if __name__ == '__main__':
    unittest.main(verbosity=2)
