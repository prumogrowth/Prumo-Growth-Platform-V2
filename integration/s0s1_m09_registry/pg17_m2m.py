"""M09-04 signed read boundary, disposable PostgreSQL 17 laboratory only.

Ed25519 authenticates canonical request bytes under a domain distinct from
the Meta ingress and receipt domains. A nonce is journaled atomically in the
SAME transaction as the full M09-03 App/grant read. No HTTP, Graph, secret
disclosure, operational principal/host credentials, send or ACK authorization.
"""
from __future__ import annotations

from contextlib import nullcontext
from hashlib import sha256
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from psycopg import errors

from .pg17_registry import RegistryPhysical
from .port import M2MPrincipal, HostScope, FLAGS

VERSION = 'prumo.s0.meta.registry.m2m-pg17/0.1-candidate'
DOMAIN = b'PRUMO.S0.M09.REGISTRY.READ/0.1\x00'
WIRE_VERSION = 'prumo.s0.m09.signed-read/0.1-candidate'
AUDIENCE = 'LAB_S0_M09'
FIELDS = frozenset({
    'version', 'key_id', 'issuer_ref', 'key_revision', 'audience', 'purpose',
    'nonce', 'issued_ms', 'expires_ms', 'host_ref', 'route_ref', 'app_ref'
})
ID = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
NONCE = re.compile(r'^[A-Za-z0-9_-]{16,128}$')
MAX_WIRE_BYTES = 2048


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def parse(wire):
    if type(wire) is not bytes or not (10 <= len(wire) <= MAX_WIRE_BYTES):
        raise ValueError('wire size')
    def distinct(items):
        d = {}
        for key, value in items:
            if key in d:
                raise ValueError('duplicate JSON key')
            d[key] = value
        return d
    e = json.loads(wire.decode('utf-8'), object_pairs_hook=distinct,
                   parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
    if (type(e) is not dict or set(e) != FIELDS or wire != canonical(e)
        or e['version'] != WIRE_VERSION or e['audience'] != AUDIENCE
        or e['purpose'] != 'REGISTRY_READ'
        or not all(type(e[k]) is str and ID.fullmatch(e[k]) for k in
                   ('key_id','issuer_ref','host_ref','route_ref','app_ref'))
        or type(e['nonce']) is not str or not NONCE.fullmatch(e['nonce'])
        or type(e['key_revision']) is not int or not 1 <= e['key_revision'] < 2**63-1
        or any(type(e[k]) is not int or e[k] < 0 for k in ('issued_ms','expires_ms'))
        or not 0 < e['expires_ms'] - e['issued_ms'] <= 120000):
        raise ValueError('invalid signed fields')
    return e


def result(state, reason, snapshot=None):
    return {'contract_version': VERSION, 'decision': state, 'reason': reason,
            'snapshot': snapshot, **FLAGS}


class AuthenticatedM09:
    """The host resolver is injected and must NOT trust arbitrary payload claims.

    The caller's signed host_ref is only a lookup key for an independently
    trusted host scope. Production identity/host provisioning is NOT present.
    """

    def __init__(self, dsn, resolve_trusted_host):
        self.dsn = dsn
        self.resolve_host = resolve_trusted_host

    def read(self, wire, signature, *, expected=None,
             previous_snapshot_ref=None):
        try:
            e = parse(wire)
        except (ValueError, UnicodeError, TypeError, RecursionError, OverflowError):
            return result('DENIED','INVALID_ENVELOPE')
        if type(signature) is not bytes or len(signature) != 64:
            return result('DENIED','INVALID_SIGNATURE')
        try:
            scope = self.resolve_host(e['host_ref'])
            if (type(scope) is not HostScope
                or scope.route_ref != e['route_ref'] or scope.app_ref != e['app_ref']
                or not all(type(v) is str and ID.fullmatch(v)
                           for v in (scope.route_ref,scope.app_ref,
                                     scope.concessionaria_id,scope.canal_id,
                                     scope.waba_id,scope.phone_number_id))):
                return result('DENIED','NOT_AUTHORIZED')
            # One connection/transaction protects replay reservation + read.
            reader = RegistryPhysical(self.dsn, lambda _: None, lambda _: None)
            decision = None
            with reader.connect() as c:
                # Lock order matches the historical S0 ingress: route then principal.
                route = c.execute(
                    'SELECT id,app,revision,active FROM s0_meta_lab.routes '
                    'WHERE id=%s FOR SHARE',(scope.route_ref,)).fetchone()
                key = c.execute(
                    'SELECT key_id,issuer,revision,route,app,tenant,scopes,channels,'
                    'active,public_key,not_before,not_after FROM s0_meta_lab.principals '
                    'WHERE key_id=%s FOR SHARE',(e['key_id'],)).fetchone()
                if (not route or not route['active'] or route['app'] != scope.app_ref
                    or not key or not key['active']
                    or key['issuer'] != e['issuer_ref']
                    or key['revision'] != e['key_revision']
                    or key['route'] != scope.route_ref or key['app'] != scope.app_ref
                    or 'REGISTRY_READ' not in key['scopes']
                    or scope.canal_id not in key['channels']
                    or len(bytes(key['public_key'])) != 32):
                    return result('DENIED','NOT_AUTHORIZED')
                now = c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
                now_ms = int(now.timestamp()*1000)
                if (not key['not_before'] <= now < key['not_after']
                    or not e['issued_ms'] - 30000 <= now_ms < e['expires_ms']
                    or e['expires_ms'] > e['issued_ms'] + 120000):
                    return result('DENIED','EXPIRED')
                try:
                    Ed25519PublicKey.from_public_bytes(bytes(key['public_key'])).verify(
                        signature, DOMAIN + wire)
                except (InvalidSignature,ValueError,TypeError):
                    return result('DENIED','INVALID_SIGNATURE')
                # UNIQUE(key_id,nonce) enforces single use across processes.
                # Failed read outcomes consume verified nonces too, unless SQL
                # itself aborts the transaction, in which case success is denied.
                c.execute('INSERT INTO s0_m09_lab.read_nonces '
                          '(key_id,nonce,envelope_sha256) VALUES(%s,%s,%s)',
                          (e['key_id'],e['nonce'],sha256(wire).hexdigest()))
                verified_principal = M2MPrincipal(
                    principal_ref=key['key_id'],issuer_ref=key['issuer'],
                    audience=AUDIENCE,key_revision=key['revision'],
                    allowed_stores=frozenset({scope.concessionaria_id}),
                    allowed_purposes=frozenset({'REGISTRY_READ'}),
                    privileged_slot_reader=False)
                # Use M09-03's full source+App/grant checks in the SAME
                # transaction/connection, without overriding shared objects.
                scoped = RegistryPhysical(
                    self.dsn,
                    lambda proof: verified_principal if proof is wire else None,
                    lambda ref: scope if ref == e['host_ref'] else None)
                scoped.connect = lambda: nullcontext(c)
                decision = scoped.read(wire,e['host_ref'],purpose='REGISTRY_READ',
                                       expected=expected,
                                       previous_snapshot_ref=previous_snapshot_ref)
            # Returns only after successful commit of nonce + versioned read.
            if decision is None or decision['decision'] != 'PHYSICAL_REGISTRY_LAB_ONLY':
                return result(decision['decision'], decision['reason']) if decision else (
                    result('UNAVAILABLE','RESULT_UNPROVEN'))
            return result('AUTHENTICATED_READ_LAB_ONLY','SIGNED_READ_COMMITTED',
                          decision['snapshot'])
        except errors.UniqueViolation:
            return result('DENIED','NONCE_REPLAY')
        except Exception:
            # No SQL, signature bytes, public key or principal metadata leak.
            return result('UNAVAILABLE','RESULT_UNPROVEN')
