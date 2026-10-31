"""M09-02: conservative physical read of the PINNED S0 Meta Ingress PG17 fixture.

This is NOT the final registry. The PG17 source has route/binding/principal
revisions but no independent app/grant revision or real Meta ownership proof.
No real M2M verification, hosted changes, HTTP or Graph access occurs here.
"""
import hashlib
import hmac
import json
from typing import Optional

from .port import HostScope, M2MPrincipal, FLAGS


CONTRACT = 'prumo.s0.meta.registry.pg17-binding-lab/0.1-candidate'


def _answer(state, reason, physical=None):
    return {'contract_version': CONTRACT, 'decision': state, 'reason': reason,
            'physical': physical, **FLAGS}


class Pg17BindingReader:
    """Read-only transaction with S0-established locks, no direct S0 writes."""

    def __init__(self, dsn, authenticate, trusted_host, tenant_to_store, *, connect=None):
        self._dsn = dsn
        self._tenant_to_store = dict(tenant_to_store)
        self._authenticate = authenticate
        self._trusted_host = trusted_host
        if connect is None:
            import psycopg
            from psycopg.rows import dict_row
            self._connect = lambda: psycopg.connect(
                self._dsn, row_factory=dict_row, connect_timeout=3,
                options='-c search_path=s0_meta_lab,pg_catalog '
                        '-c statement_timeout=8000 -c lock_timeout=2000')
        else:
            self._connect = connect

    def read(self, proof, host_ref, *, purpose='REGISTRY_READ',
             expected_versions: Optional[dict] = None,
             expected_snapshot_ref: Optional[str] = None):
        if (purpose != 'REGISTRY_READ'
            or expected_versions is not None and (
                type(expected_versions) is not dict or
                set(expected_versions) != {'route', 'binding', 'principal'} or
                any(type(v) is not int or v < 1 for v in expected_versions.values()))
            or expected_snapshot_ref is not None and (
                type(expected_snapshot_ref) is not str or
                len(expected_snapshot_ref) != 64 or
                any(c not in '0123456789abcdef' for c in expected_snapshot_ref))):
            return _answer('DENIED', 'INVALID_INPUT')
        try:
            principal = self._authenticate(proof)
            scope = self._trusted_host(host_ref)
            if (type(principal) is not M2MPrincipal or type(scope) is not HostScope
                or not principal.active or principal.audience != 'LAB_S0_M09'
                or purpose not in principal.allowed_purposes
                or scope.concessionaria_id not in principal.allowed_stores
                or not all(type(x) is str and x for x in (
                    scope.route_ref, scope.app_ref, scope.concessionaria_id,
                    scope.canal_id, scope.waba_id, scope.phone_number_id))):
                return _answer('DENIED', 'NOT_AUTHORIZED')
            # The mapped scope is host-derived. Payload / channel claims cannot
            # create a row or change tenant-to-store ownership.
            with self._connect() as c:
                c.execute("SET LOCAL statement_timeout='8000ms'")
                c.execute("SET LOCAL lock_timeout='2000ms'")
                # Same locking order as the original Ingress implementation.
                route = c.execute(
                    "SELECT id,app,revision,active FROM s0_meta_lab.routes "
                    "WHERE id=%s FOR SHARE", (scope.route_ref,)).fetchone()
                if not route or not route['active'] or route['app'] != scope.app_ref:
                    return _answer('DENIED', 'NOT_AUTHORIZED')
                key = c.execute(
                    "SELECT key_id,issuer,revision,route,app,tenant,scopes,"
                    "channels,active,not_before,not_after FROM "
                    "s0_meta_lab.principals WHERE key_id=%s FOR SHARE",
                    (principal.principal_ref,)).fetchone()
                if (not key or not key['active'] or key['issuer'] != principal.issuer_ref
                    or key['route'] != scope.route_ref or key['app'] != scope.app_ref
                    or key['revision'] != principal.key_revision
                    or purpose not in key['scopes'] or
                    scope.canal_id not in key['channels']):
                    return _answer('DENIED', 'NOT_AUTHORIZED')
                bindings = c.execute(
                    "SELECT route,waba,phone,app,tenant,channel,revision,active "
                    "FROM s0_meta_lab.bindings WHERE route=%s AND waba=%s "
                    "AND phone=%s FOR SHARE",
                    (scope.route_ref,scope.waba_id,scope.phone_number_id)).fetchall()
                if len(bindings) != 1:
                    return _answer('DENIED', 'NOT_AUTHORIZED')
                binding = bindings[0]
                if (not binding['active'] or binding['app'] != scope.app_ref
                    or binding['tenant'] != key['tenant']
                    or self._tenant_to_store.get(key['tenant']) != scope.concessionaria_id
                    or binding['channel'] != scope.canal_id):
                    return _answer('DENIED', 'NOT_AUTHORIZED')
                # The fixture's schema does not enforce global phone/WABA uniqueness.
                # Reject conflicting historical or active bindings rather than
                # inferring exclusivity from the compound primary key.
                phone_matches = c.execute(
                    "SELECT route,channel FROM s0_meta_lab.bindings "
                    "WHERE phone=%s ORDER BY route,channel FOR SHARE",
                    (scope.phone_number_id,)).fetchall()
                waba_matches = c.execute(
                    "SELECT route FROM s0_meta_lab.bindings WHERE waba=%s "
                    "ORDER BY route FOR SHARE",(scope.waba_id,)).fetchall()
                if (len(phone_matches) != 1 or phone_matches[0]['route'] != scope.route_ref
                    or any(x['route'] != scope.route_ref for x in waba_matches)):
                    return _answer('DENIED','AMBIGUOUS_BINDING')
                db_now=c.execute("SELECT clock_timestamp() AS now").fetchone()['now']
                if not key['not_before'] <= db_now < key['not_after']:
                    return _answer('DENIED', 'NOT_AUTHORIZED')
                versions = {'route':route['revision'],
                            'binding':binding['revision'],
                            'principal':key['revision']}
                if expected_versions is not None and versions != expected_versions:
                    return _answer('STALE_OR_REVOKED','STALE_REVISION')
                material = {'route_ref':route['id'], 'app_ref':route['app'],
                            'canal_id':binding['channel'], 'waba_id':binding['waba'],
                            'phone_number_id':binding['phone'],
                            'tenant':binding['tenant'],
                            'concessionaria_id':scope.concessionaria_id,
                            'principal_ref':key['key_id'],
                            'versions':versions,'purpose':purpose}
                digest=hashlib.sha256(json.dumps(material,sort_keys=True,
                                 separators=(',',':')).encode()).hexdigest()
                if (expected_snapshot_ref is not None and
                    not hmac.compare_digest(digest, expected_snapshot_ref)):
                    return _answer('STALE_OR_REVOKED','STALE_SNAPSHOT')
                # No app/grant revision exists in the pinned PG17 schema;
                # do NOT manufacture those versions or claim full M09 readiness.
                return _answer('PG17_BINDING_VERIFIED_LAB_ONLY','LAB_DB_READ', {
                    'concessionaria_id':scope.concessionaria_id,
                    'route_ref':scope.route_ref, 'app_ref':scope.app_ref,
                    'canal_id':scope.canal_id, 'waba_id':scope.waba_id,
                    'phone_number_id':scope.phone_number_id,
                    'versions': versions, 'snapshot_ref':digest,
                    'unproven_revisions':['app','grant'],
                    'ownership_evidence_state':'UNVERIFIED',
                    'delegation_evidence_state':'UNVERIFIED'})
        except Exception:
            return _answer('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
