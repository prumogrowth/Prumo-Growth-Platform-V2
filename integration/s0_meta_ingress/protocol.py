"""Strict laboratory wire formats. No human identity or commercial operation."""
import base64
import hashlib
import hmac
import json
import re
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

VERSION = 'prumo.s0-meta-ingress.lab/1-candidate'
M2M_DOMAIN = b'PRUMO/S0-META-INGRESS/M2M/LAB/v1\x00'
RECEIPT_DOMAIN = b'PRUMO/S0-META-INGRESS/RECEIPT/LAB/v1\x00'
MAX_RAW = 262144
MAX_ITEMS = 100
FIELDS = {'version', 'issuer', 'key_id', 'key_revision', 'audience', 'scope',
          'app', 'route', 'route_revision', 'batch_ref', 'nonce', 'issued_ms',
          'expires_ms', 'raw_base64', 'meta_signature'}

class Reject(Exception):
    def __init__(self, reason):
        self.reason = reason

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')

def digest(value):
    return hashlib.sha256(value).hexdigest()

def b64(value):
    return base64.b64encode(value).decode('ascii')

def unb64(value):
    try:
        decoded = base64.b64decode(value, validate=True)
        if b64(decoded) != value:
            raise ValueError()
        return decoded
    except (ValueError, TypeError):
        raise Reject('INVALID_BASE64') from None

def strict_json(raw):
    def pairs(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise Reject('DUPLICATE_JSON_KEY')
            obj[k] = v
        return obj
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise Reject('INVALID_JSON') from None

def decode_envelope(wire):
    if not isinstance(wire, bytes) or len(wire) > 360000:
        raise Reject('ENVELOPE_LIMIT')
    e = strict_json(wire)
    if not isinstance(e, dict) or set(e) != FIELDS or canonical(e) != wire:
        raise Reject('INVALID_ENVELOPE')
    if e['version'] != VERSION or e['audience'] != 'LAB_S0_META_INGRESS' or e['scope'] not in ('append', 'recover'):
        raise Reject('DOMAIN_OR_SCOPE')
    for f in ('issuer', 'key_id', 'app', 'route', 'batch_ref', 'nonce'):
        if not isinstance(e[f], str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', e[f]):
            raise Reject('INVALID_IDENTIFIER')
    for f in ('key_revision', 'route_revision'):
        if not isinstance(e[f], str) or not re.fullmatch(r'[1-9][0-9]{0,17}', e[f]):
            raise Reject('INVALID_REVISION')
    if any(type(e[f]) is not int for f in ('issued_ms', 'expires_ms')) or not 0 < e['expires_ms'] - e['issued_ms'] <= 30000:
        raise Reject('INVALID_TIME')
    raw = unb64(e['raw_base64'])
    if not raw or len(raw) > MAX_RAW:
        raise Reject('BODY_LIMIT')
    if not isinstance(e['meta_signature'], str) or not re.fullmatch(r'sha256=[0-9a-f]{64}', e['meta_signature']):
        raise Reject('INVALID_META_PROOF')
    return e, raw

def verify_m2m(public, wire, signature):
    try:
        Ed25519PublicKey.from_public_bytes(bytes(public)).verify(unb64(signature), M2M_DOMAIN + wire)
    except Exception:
        raise Reject('M2M_SIGNATURE') from None

def verify_meta(raw, signature, secret):
    expected = 'sha256=' + hmac.new(secret, raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise Reject('META_SIGNATURE')

def normalize(raw):
    """Preserve array provenance and JSON member encounter order; no item dedupe."""
    p = strict_json(raw)
    out = []
    def ident(x, limit=256):
        return isinstance(x, str) and 0 < len(x) <= limit
    try:
        if not isinstance(p, dict) or p.get('object') != 'whatsapp_business_account' or not isinstance(p['entry'], list) or not p['entry']:
            raise ValueError()
        for ei, entry in enumerate(p['entry']):
            if not ident(entry['id']) or not isinstance(entry['changes'], list) or not entry['changes']:
                raise ValueError()
            for ci, change in enumerate(entry['changes']):
                v = change['value']
                if change['field'] != 'messages' or not ident(v['metadata']['phone_number_id']):
                    raise ValueError()
                if set(v) - {'metadata','contacts','messaging_product','messages','statuses'}:
                    raise ValueError()
                before = len(out)
                for kind, values in v.items():
                    if kind not in ('messages', 'statuses'):
                        continue  # Full change context retained below, plus original bytes.
                    if not isinstance(values, list):
                        raise ValueError()
                    for ii, item in enumerate(values):
                        status = kind == 'statuses'
                        provider_kind = item['status' if status else 'type']
                        participant = item['recipient_id' if status else 'from']
                        if not ident(item['id']) or not ident(participant, 64) or not ident(provider_kind, 64):
                            raise ValueError()
                        if not isinstance(item['timestamp'], str) or not re.fullmatch(r'[0-9]{1,13}', item['timestamp']):
                            raise ValueError()
                        if status and provider_kind not in ('sent', 'delivered', 'read', 'failed'):
                            raise ValueError()
                        out.append({'ordinal': len(out), 'entry_index': ei, 'change_index': ci,
                                    'array_kind': kind, 'item_index': ii, 'waba': entry['id'],
                                    'phone': v['metadata']['phone_number_id'],
                                    'kind': 'status_callback' if status else 'inbound_message',
                                    'provider_message_id': item['id'], 'item': item,
                                    'change_context': v, 'resolution': 'ARCHIVED_UNRESOLVED'})
                if len(out) == before:
                    raise ValueError()
        if not 0 < len(out) <= MAX_ITEMS:
            raise ValueError()
        return out
    except (KeyError, TypeError, ValueError, IndexError):
        raise Reject('INVALID_OR_UNSUPPORTED_OCCURRENCE') from None

def verify_receipt(receipt, public, expected):
    """Consumer must pin trusted S0 key AND expected request context."""
    try:
        if not {'app','route','route_revision','raw_sha256'} <= set(expected):
            return False
        body = receipt['body']
        if body['version'] != 'prumo.s0-meta-ingress.receipt.lab/1-candidate':
            return False
        Ed25519PublicKey.from_public_bytes(public).verify(unb64(receipt['signature']),
                                                        RECEIPT_DOMAIN + canonical(body))
        return body['state'] == 'DURABLY_COMMITTED' and all(body[k] == v for k, v in expected.items())
    except Exception:
        return False
