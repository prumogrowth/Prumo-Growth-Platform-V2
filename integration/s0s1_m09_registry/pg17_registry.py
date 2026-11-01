"""M09-03 disposable PG17 transactional App/grant candidate only.

Uses the pinned S0 Meta Ingress schema as physical provenance. Additional
tables exist only in a freshly isolated PG17 container. The external M2M and
host resolvers remain fixtures; this is NOT operational source of truth.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re

from .port import HostScope, M2MPrincipal, FLAGS

VERSION = 'prumo.s0.meta.registry.pg17-candidate/0.1'
_ID = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
_MAX_REV = 9223372036854775807


def answer(decision, reason, snapshot=None):
    return {'contract_version': VERSION, 'decision': decision,
            'reason': reason, 'snapshot': snapshot, **FLAGS}


def valid_id(v):
    return type(v) is str and bool(_ID.fullmatch(v))


def valid_revision(v):
    return type(v) is int and 1 <= v < _MAX_REV


class RegistryPhysical:
    """No public listener, transport secrets, caller-controlled host or Graph."""

    def __init__(self, dsn, m2m_authenticator, trusted_host_resolver):
        self.dsn = dsn
        self.authenticate = m2m_authenticator
        self.resolve_host = trusted_host_resolver

    def connect(self):
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(
            self.dsn, row_factory=dict_row, connect_timeout=3,
            options='-c search_path=pg_catalog -c statement_timeout=8000 -c lock_timeout=2000')

    def read(self, proof, host_ref, *, purpose='REGISTRY_READ', expected=None,
             previous_snapshot_ref=None):
        if (purpose != 'REGISTRY_READ'
            or expected is not None and (
                type(expected) is not dict
                or set(expected) != {'route','app','binding','grant','principal'}
                or not all(valid_revision(v) for v in expected.values()))
            or previous_snapshot_ref is not None and (
                type(previous_snapshot_ref) is not str
                or not re.fullmatch('[0-9a-f]{64}', previous_snapshot_ref))):
            return answer('DENIED','INVALID_REQUEST')
        try:
            principal = self.authenticate(proof)
            scope = self.resolve_host(host_ref)
            if (type(principal) is not M2MPrincipal or type(scope) is not HostScope
                or not principal.active or principal.audience != 'LAB_S0_M09'
                or purpose not in principal.allowed_purposes
                or scope.concessionaria_id not in principal.allowed_stores
                or not all(valid_id(v) for v in (
                    principal.principal_ref, principal.issuer_ref, scope.route_ref,
                    scope.concessionaria_id, scope.app_ref, scope.canal_id,
                    scope.waba_id, scope.phone_number_id))
                or not valid_revision(principal.key_revision)):
                return answer('DENIED','NOT_AUTHORIZED')
            with self.connect() as c:
                # Preserve original ingress lock order before M09 candidates.
                route = c.execute(
                    'SELECT id,app,revision,active FROM s0_meta_lab.routes '
                    'WHERE id=%s FOR SHARE',(scope.route_ref,)).fetchone()
                key = c.execute(
                    'SELECT key_id,issuer,revision,route,app,tenant,scopes,'
                    'channels,active,not_before,not_after FROM s0_meta_lab.principals '
                    'WHERE key_id=%s FOR SHARE',(principal.principal_ref,)).fetchone()
                binding = c.execute(
                    'SELECT route,waba,phone,app,tenant,channel,revision,active '
                    'FROM s0_meta_lab.bindings WHERE route=%s AND waba=%s '
                    'AND phone=%s FOR SHARE',
                    (scope.route_ref,scope.waba_id,scope.phone_number_id)).fetchone()
                if (not route or not key or not binding or not route['active']
                    or route['app'] != scope.app_ref or not key['active']
                    or key['issuer'] != principal.issuer_ref
                    or key['revision'] != principal.key_revision
                    or key['route'] != scope.route_ref or key['app'] != scope.app_ref
                    or purpose not in key['scopes'] or scope.canal_id not in key['channels']
                    or not binding['active'] or binding['app'] != scope.app_ref
                    or binding['channel'] != scope.canal_id
                    or binding['tenant'] != key['tenant']):
                    return answer('DENIED','NOT_AUTHORIZED')
                app = c.execute(
                    'SELECT * FROM s0_m09_lab.apps WHERE app_ref=%s FOR SHARE',
                    (scope.app_ref,)).fetchone()
                grant = c.execute(
                    'SELECT * FROM s0_m09_lab.grants WHERE canal_id=%s FOR SHARE',
                    (scope.canal_id,)).fetchone()
                if (not app or not grant or not app['active'] or not grant['active']
                    or app['route_ref'] != scope.route_ref
                    or app['concessionaria_id'] != scope.concessionaria_id
                    or app['tenant'] != key['tenant']
                    or grant['app_ref'] != scope.app_ref
                    or grant['route_ref'] != scope.route_ref
                    or grant['waba_id'] != scope.waba_id
                    or grant['phone_number_id'] != scope.phone_number_id):
                    return answer('DENIED','NOT_AUTHORIZED')
                # Original fixture is not globally UNIQUE. Recheck negatives,
                # but do not claim strong uniqueness for independently mutating
                # unmodified source outside our controlled transactions.
                phones=c.execute(
                    'SELECT route FROM s0_meta_lab.bindings WHERE phone=%s '
                    'ORDER BY route FOR SHARE',(scope.phone_number_id,)).fetchall()
                wabas=c.execute(
                    'SELECT route FROM s0_meta_lab.bindings WHERE waba=%s '
                    'ORDER BY route FOR SHARE',(scope.waba_id,)).fetchall()
                if (len(phones)!=1 or any(x['route']!=scope.route_ref for x in wabas)
                    or not wabas):
                    return answer('DENIED','AMBIGUOUS_BINDING')
                now=c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
                if (not key['not_before'] <= now < key['not_after']
                    or not app['valid_from'] <= now < app['valid_until']):
                    return answer('DENIED','NOT_AUTHORIZED')
                versions={'route':route['revision'],'app':app['revision'],
                          'binding':binding['revision'],'grant':grant['revision'],
                          'principal':key['revision']}
                if expected is not None and expected != versions:
                    return answer('STALE_OR_REVOKED','STALE_REVISION')
                material={
                    'concessionaria_id':scope.concessionaria_id,
                    'app_ref':scope.app_ref,'route_ref':scope.route_ref,
                    'canal_id':scope.canal_id,'waba_id':scope.waba_id,
                    'phone_number_id':scope.phone_number_id,
                    'versions':versions, 'principal_ref':key['key_id'],
                    'tenant_ref':app['tenant'], 'purpose':purpose}
                digest=hashlib.sha256(json.dumps(material,sort_keys=True,
                        separators=(',',':')).encode()).hexdigest()
                if (previous_snapshot_ref is not None and
                    not hmac.compare_digest(previous_snapshot_ref,digest)):
                    return answer('STALE_OR_REVOKED','STALE_SNAPSHOT')
                return answer('PHYSICAL_REGISTRY_LAB_ONLY','PG17_CANDIDATE_READ',{
                    'concessionaria_id':scope.concessionaria_id,
                    'app_ref':scope.app_ref,'route_ref':scope.route_ref,
                    'canal_id':scope.canal_id,'waba_id':scope.waba_id,
                    'phone_number_id':scope.phone_number_id,
                    'revisions':versions,'source_revision':digest,
                    'snapshot_ref':digest,
                    'ownership_evidence_state':'UNVERIFIED',
                    'delegation_evidence_state':'UNVERIFIED'
                })
        except Exception:
            return answer('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')


def revoke_channel_in_admin_transaction(c, route_ref, channel_id,
                                        expected_route, expected_app,
                                        expected_binding, expected_grant):
    """Installer-control ONLY; caller must commit or rollback the entire transaction.

    Ordering: original route -> original binding -> M09 App -> M09 grant.
    The original Ingress also denies the channel after commit, preventing a
    contradictory M09-only revocation in this isolated PG17 source.
    """
    if (not valid_id(route_ref) or not valid_id(channel_id)
        or not all(valid_revision(x) for x in
                   (expected_route,expected_app,expected_binding,expected_grant))):
        return 'DENIED'
    route=c.execute('SELECT id,revision FROM s0_meta_lab.routes '
                    'WHERE id=%s FOR UPDATE',(route_ref,)).fetchone()
    binding=c.execute('SELECT route,channel,revision,active '
                      'FROM s0_meta_lab.bindings '
                      'WHERE route=%s AND channel=%s FOR UPDATE',
                      (route_ref,channel_id)).fetchone()
    app=c.execute('SELECT app_ref,revision,active FROM s0_m09_lab.apps '
                  'WHERE route_ref=%s FOR UPDATE',(route_ref,)).fetchone()
    grant=c.execute('SELECT canal_id,route_ref,revision,active FROM s0_m09_lab.grants '
                    'WHERE canal_id=%s FOR UPDATE',(channel_id,)).fetchone()
    if (not route or not binding or not app or not grant
        or grant['route_ref'] != route_ref
        or not binding['active'] or not app['active'] or not grant['active']
        or (route['revision'],app['revision'],binding['revision'],grant['revision'])
           != (expected_route,expected_app,expected_binding,expected_grant)):
        return 'CONFLICT'
    c.execute('UPDATE s0_m09_lab.grants SET active=false,revision=revision+1 '
              'WHERE canal_id=%s',(channel_id,))
    c.execute('UPDATE s0_m09_lab.apps SET revision=revision+1 '
              'WHERE app_ref=%s',(app['app_ref'],))
    c.execute('UPDATE s0_meta_lab.bindings SET active=false,revision=revision+1 '
              'WHERE route=%s AND channel=%s',(route_ref,channel_id))
    c.execute('UPDATE s0_meta_lab.routes SET revision=revision+1 '
              'WHERE id=%s',(route_ref,))
    return 'REVOKED_IN_DISPOSABLE_TRANSACTION'
