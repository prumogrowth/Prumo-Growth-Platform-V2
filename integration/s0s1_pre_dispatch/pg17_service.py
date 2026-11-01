"""S0 #10: one-transaction policy recheck + reservation, disposable PG17 only.

Lab fixtures are NOT authenticated consent, template approval or Meta grants.
The entire operation is S0 installer-owned: no runtime ACL, no Graph/vault/send.
The prior M09-08 checkpoint and consent/case/template/reservation all occur in
one PostgreSQL transaction under compatible locks. A successful record is NOT
a lease and MUST NEVER be redeemed as external send authority.
"""
from __future__ import annotations

import re

from integration.s0s1_m09_registry.pg17_use_check import (
    record_control_check_in_admin_transaction as m09_check,
)
from integration.s0s1_m09_registry.port import HostScope, M2MPrincipal, Revisions, FLAGS

_VERSION = 'prumo.s0.pre-dispatch.pg17/0.1-lab-only'
_ID = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
_FIELDS = frozenset((
    'attempt_ref','selection_ref','case_ref','service_ref','template_ref',
    'template_version','template_purpose_ref','consent_purpose_ref',
    'campaign_ref','expected_case_revision','expected_assignment_revision',
    'expected_policy_revision','expected_suppression_revision',
    'expected_consent_revision','expected_template_revision',
    'expected_campaign_revision','expected_grant_revision',
))
_REVISIONS = (
    'expected_case_revision','expected_assignment_revision',
    'expected_policy_revision','expected_suppression_revision',
    'expected_consent_revision','expected_template_revision',
    'expected_campaign_revision','expected_grant_revision'
)


def _id(x):
    return type(x) is str and bool(_ID.fullmatch(x))


def _rev(x):
    return type(x) is int and 1 <= x < 2**63 - 1


def _answer(decision, reason):
    return {
        'contract_version': _VERSION, 'decision': decision, 'reason': reason,
        'lab_reservation_recorded': decision == 'LAB_RESERVATION_RECORDED_NO_DISPATCH',
        'send_authorized': False, 'graph_authorized': False,
        'credential_resolution_authorized': False,
        'pre_dispatch_operationally_authorized': False,
        'provider_approval_verified': False,
        'consent_proven_from_real_source': False,
        'external_http_ack': False, 'production_authorized': False,
        'commercial_transition_authorized': False,
    }


class Reject(Exception):
    def __init__(self, reason):
        self.reason = reason


def _require(condition, reason):
    if not condition:
        raise Reject(reason)


def _check(c, request, scope, principal, versions):
    # Source M09 is examined first with compatible route lock order. This
    # appends a technical CHECK only on lab success, in the SAME transaction.
    technical = m09_check(c, scope=scope, principal=principal,
                          expected=versions, attempt_ref='pd.'+request['attempt_ref'])
    _require(technical['decision'] == 'LAB_CHECK_RECORDED_NO_USE',
             'STALE_OR_CHANGED' if technical['reason'] != 'DUPLICATE_ATTEMPT'
             else 'DUPLICATE_ATTEMPT')

    _require(request['service_ref'] == principal.principal_ref, 'SCOPE_CHANGED')

    case = c.execute(
        'SELECT * FROM s0_pre_dispatch_lab.cases WHERE case_ref=%s FOR UPDATE',
        (request['case_ref'],)
    ).fetchone()
    _require(case is not None and case['active'] and not case['global_opt_out'],
             'POLICY_DENIED')
    _require(case['concessionaria_id'] == scope.concessionaria_id
             and case['app_ref'] == scope.app_ref
             and case['route_ref'] == scope.route_ref
             and case['canal_id'] == scope.canal_id
             and case['waba_id'] == scope.waba_id
             and case['principal_ref'] == principal.principal_ref,
             'SCOPE_CHANGED')
    for column,field in (
        ('case_revision','expected_case_revision'),
        ('assignment_revision','expected_assignment_revision'),
        ('policy_revision','expected_policy_revision'),
        ('suppression_revision','expected_suppression_revision')
    ):
        _require(case[column] == request[field], 'STALE_OR_CHANGED')

    consent = c.execute(
        'SELECT * FROM s0_pre_dispatch_lab.consents '
        'WHERE case_ref=%s AND purpose_ref=%s FOR UPDATE',
        (request['case_ref'],request['consent_purpose_ref'])
    ).fetchone()
    _require(consent is not None and consent['state'] == 'GRANTED',
             'CONSENT_DENIED')
    _require(consent['revision'] == request['expected_consent_revision'],
             'STALE_OR_CHANGED')

    # Select all active suppressions, not just the chosen purpose; explicit
    # "*" means store-level global opt-out. Case UPDATE lock also blocks
    # transactional FK-checked new suppression/consent rows.
    suppressions = c.execute(
        'SELECT purpose_ref,active FROM s0_pre_dispatch_lab.suppressions '
        'WHERE case_ref=%s ORDER BY purpose_ref FOR UPDATE',
        (request['case_ref'],)
    ).fetchall()
    _require(not any(s['active'] and s['purpose_ref'] in (
        '*', request['consent_purpose_ref']) for s in suppressions),
             'SUPPRESSED')

    template = c.execute(
        'SELECT * FROM s0_pre_dispatch_lab.templates '
        'WHERE template_ref=%s AND template_version=%s FOR UPDATE',
        (request['template_ref'],request['template_version'])
    ).fetchone()
    _require(template is not None and template['active']
             and template['provider_approved'] and template['media_verified'],
             'TEMPLATE_UNVERIFIED')
    _require(template['concessionaria_id'] == scope.concessionaria_id
             and template['waba_id'] == scope.waba_id
             and template['template_purpose_ref'] == request['template_purpose_ref']
             and template['consent_purpose_ref'] == request['consent_purpose_ref'],
             'SCOPE_CHANGED')
    _require(template['revision'] == request['expected_template_revision'],
             'STALE_OR_CHANGED')

    campaign = c.execute(
        'SELECT * FROM s0_pre_dispatch_lab.campaigns '
        'WHERE campaign_ref=%s FOR UPDATE', (request['campaign_ref'],)
    ).fetchone()
    _require(campaign is not None and campaign['active'] and campaign['eligible'],
             'CAMPAIGN_DENIED')
    _require(campaign['case_ref'] == request['case_ref']
             and campaign['template_ref'] == request['template_ref']
             and campaign['template_version'] == request['template_version'],
             'SCOPE_CHANGED')
    _require(campaign['revision'] == request['expected_campaign_revision'],
             'STALE_OR_CHANGED')

    grant = c.execute(
        'SELECT * FROM s0_pre_dispatch_lab.grants '
        'WHERE case_ref=%s AND service_ref=%s AND template_ref=%s '
        'AND template_version=%s AND campaign_ref=%s FOR UPDATE',
        (request['case_ref'],request['service_ref'],request['template_ref'],
         request['template_version'],request['campaign_ref'])
    ).fetchone()
    _require(grant is not None and grant['active'], 'GRANT_DENIED')
    _require(grant['template_purpose_ref'] == request['template_purpose_ref'],
             'SCOPE_CHANGED')
    _require(grant['revision'] == request['expected_grant_revision'],
             'STALE_OR_CHANGED')

    now = c.execute('SELECT clock_timestamp() AS now').fetchone()['now']
    _require(now < consent['valid_until'] and now < template['valid_until'],
             'EXPIRED')

    inserted = c.execute(
        'INSERT INTO s0_pre_dispatch_lab.reservations '
        '(attempt_ref,selection_ref,case_ref,concessionaria_id,'
        'template_ref,template_version,template_purpose_ref) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s) '
        'ON CONFLICT DO NOTHING RETURNING attempt_ref',
        (request['attempt_ref'],request['selection_ref'],request['case_ref'],
         scope.concessionaria_id,request['template_ref'],
         request['template_version'],request['template_purpose_ref'])
    ).fetchone()
    _require(inserted is not None, 'DUPLICATE_ATTEMPT')
    readback = c.execute(
        'SELECT attempt_ref,state,selection_ref FROM '
        's0_pre_dispatch_lab.reservations WHERE attempt_ref=%s FOR SHARE',
        (request['attempt_ref'],)
    ).fetchone()
    _require(readback is not None
             and readback['state'] == 'LAB_HELD_NO_DISPATCH'
             and readback['selection_ref'] == request['selection_ref'],
             'READBACK_UNAVAILABLE')


def reserve_in_admin_transaction(c, request, *, scope, principal, m09_versions):
    """Caller owns commit/rollback. Requires disposable admin connection.

    All denial paths roll back the SAVEPOINT: no ghost M09 check or attempted
    reservation is left. A successful response is returned before caller commit:
    caller MUST NOT use it externally, even if COMMIT later succeeds.
    """
    if (type(request) is not dict or set(request) != _FIELDS
        or any(not _id(request[k]) for k in _FIELDS.difference(_REVISIONS))
        or any(not _rev(request[k]) for k in _REVISIONS)
        or type(scope) is not HostScope or type(principal) is not M2MPrincipal
        or type(m09_versions) is not Revisions):
        return _answer('DENIED','INVALID_REQUEST')
    c.execute('SAVEPOINT s0_pre_dispatch_v01')
    try:
        _check(c, request, scope, principal, m09_versions)
    except Reject as rejected:
        c.execute('ROLLBACK TO SAVEPOINT s0_pre_dispatch_v01')
        c.execute('RELEASE SAVEPOINT s0_pre_dispatch_v01')
        return _answer('DENIED',rejected.reason)
    except Exception:
        c.execute('ROLLBACK TO SAVEPOINT s0_pre_dispatch_v01')
        c.execute('RELEASE SAVEPOINT s0_pre_dispatch_v01')
        return _answer('UNAVAILABLE','DEPENDENCY_UNAVAILABLE')
    c.execute('RELEASE SAVEPOINT s0_pre_dispatch_v01')
    return _answer('LAB_RESERVATION_RECORDED_NO_DISPATCH','LAB_READBACK_ONLY')
