"""M09-08: transactional point-of-use CONTROL-only check, disposable PG17.

This is deliberately NOT an authorization to send, redeem a vault slot, run
Graph, emit HTTP ACK, or exercise PRE_DISPATCH (#10). It writes only a LAB
check record after revalidating the technical route/channel/grant/principal
within a single admin-controlled transaction. The external use boundary is
absent. A successful old check MUST NOT be redeemed after the transaction.
"""
from __future__ import annotations

import re

from .port import HostScope, M2MPrincipal, Revisions, FLAGS

_ID = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
_MAX = 2**63 - 1


def _id(value):
    return type(value) is str and bool(_ID.fullmatch(value))


def _rev(value):
    return type(value) is int and 1 <= value < _MAX


def _response(decision, reason):
    return {
        'contract_version': 'prumo.s0.meta.point-of-use-check/0.1-lab',
        'decision': decision, 'reason': reason,
        'check_recorded_lab_only': decision == 'LAB_CHECK_RECORDED_NO_USE',
        'credential_resolution_authorized': False,
        'external_use_authorized': False,
        'pre_dispatch_authorized': False,
        **FLAGS,
    }


def record_control_check_in_admin_transaction(
    connection, *, scope, principal, expected, attempt_ref
):
    """Admin-only lab fixture. Transaction COMMIT belongs to the caller.

    Lock ordering mirrors M09-03: source route -> source principal ->
    source binding -> candidate App -> candidate grant. Concurrent revoke
    takes source route first, so the check and revoke cannot be committed
    with the same revisions in opposite orders.

    A recorded check is a *historical audit fact*, not a lease, a bearer,
    an allow decision for outbound, or a real privileged operation.
    """
    if (type(scope) is not HostScope or type(principal) is not M2MPrincipal
        or type(expected) is not Revisions
        or not _id(attempt_ref)
        or not all(_id(v) for v in (
            scope.route_ref,scope.app_ref,scope.concessionaria_id,
            scope.canal_id,scope.waba_id,scope.phone_number_id,
            principal.principal_ref,principal.issuer_ref))
        or not all(_rev(v) for v in (
            expected.route,expected.app,expected.binding,
            expected.grant,expected.principal))
        or not principal.active or principal.audience != 'LAB_S0_M09'
        or scope.concessionaria_id not in principal.allowed_stores
        or 'REGISTRY_READ' not in principal.allowed_purposes
        or not re.fullmatch(r'\d{5,25}',scope.phone_number_id)):
        return _response('DENIED','INVALID_SCOPE_OR_PRINCIPAL')

    # Must be called with a single existing transaction on a throwaway lab DB.
    # SQL exceptions are allowed to abort the entire caller transaction.
    route = connection.execute(
        'SELECT id,app,revision,active FROM s0_meta_lab.routes '
        'WHERE id=%s FOR UPDATE', (scope.route_ref,)
    ).fetchone()
    if (not route or not route['active'] or route['app'] != scope.app_ref
        or route['revision'] != expected.route):
        return _response('DENIED','STALE_OR_REVOKED')

    principal_row = connection.execute(
        'SELECT key_id,issuer,revision,route,app,tenant,scopes,channels,'
        'active,not_before,not_after FROM s0_meta_lab.principals '
        'WHERE key_id=%s FOR SHARE', (principal.principal_ref,)
    ).fetchone()
    if (not principal_row or not principal_row['active']
        or principal_row['issuer'] != principal.issuer_ref
        or principal_row['revision'] != expected.principal
        or principal.key_revision != expected.principal
        or principal_row['route'] != scope.route_ref
        or principal_row['app'] != scope.app_ref
        or scope.canal_id not in principal_row['channels']
        or 'REGISTRY_READ' not in principal_row['scopes']):
        return _response('DENIED','STALE_OR_REVOKED')

    binding = connection.execute(
        'SELECT route,waba,phone,app,tenant,channel,revision,active '
        'FROM s0_meta_lab.bindings '
        'WHERE route=%s AND channel=%s FOR UPDATE',
        (scope.route_ref,scope.canal_id)
    ).fetchone()
    if (not binding or not binding['active']
        or binding['revision'] != expected.binding
        or binding['waba'] != scope.waba_id
        or binding['phone'] != scope.phone_number_id
        or binding['app'] != scope.app_ref
        or binding['tenant'] != principal_row['tenant']):
        return _response('DENIED','STALE_OR_REVOKED')

    app = connection.execute(
        'SELECT app_ref,route_ref,concessionaria_id,tenant,revision,active,'
        'valid_from,valid_until FROM s0_m09_lab.apps '
        'WHERE app_ref=%s FOR UPDATE',
        (scope.app_ref,)
    ).fetchone()
    grant = connection.execute(
        'SELECT canal_id,app_ref,route_ref,waba_id,phone_number_id,'
        'revision,active FROM s0_m09_lab.grants '
        'WHERE canal_id=%s FOR UPDATE',(scope.canal_id,)
    ).fetchone()
    if (not app or not app['active'] or app['revision'] != expected.app
        or app['route_ref'] != scope.route_ref
        or app['concessionaria_id'] != scope.concessionaria_id
        or app['tenant'] != principal_row['tenant']
        or not grant or not grant['active'] or grant['revision'] != expected.grant
        or grant['app_ref'] != scope.app_ref
        or grant['route_ref'] != scope.route_ref
        or grant['waba_id'] != scope.waba_id
        or grant['phone_number_id'] != scope.phone_number_id):
        return _response('DENIED','STALE_OR_REVOKED')

    now = connection.execute(
        'SELECT clock_timestamp() AS now'
    ).fetchone()['now']
    if (not principal_row['not_before'] <= now < principal_row['not_after']
        or not app['valid_from'] <= now < app['valid_until']):
        return _response('DENIED','EXPIRED')

    # This does NOT grant permission or check Meta template/consent.
    # The UNIQUE attempt_ref is only a lab idempotency check.
    inserted = connection.execute(
        'INSERT INTO s0_m09_lab.point_of_use_checks '
        '(attempt_ref,route_ref,app_ref,canal_id,principal_ref,'
        'expected_route_revision,expected_app_revision,'
        'expected_binding_revision,expected_grant_revision,'
        'expected_principal_revision) '
        'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT(attempt_ref) DO NOTHING RETURNING attempt_ref',
        (attempt_ref,scope.route_ref,scope.app_ref,scope.canal_id,
         principal.principal_ref,expected.route,expected.app,
         expected.binding,expected.grant,expected.principal)
    ).fetchone()
    if not inserted:
        return _response('DENIED','DUPLICATE_ATTEMPT')
    return _response('LAB_CHECK_RECORDED_NO_USE','AUDIT_ONLY_NO_EXTERNAL_USE')
