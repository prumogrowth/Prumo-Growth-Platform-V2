"""S0/S1 M09: isolated, synthetic registry snapshot/recheck contract port.

No endpoint, DB access, Meta Graph, commercial authority or real M2M authenticator.
The injection boundary must be replaced by an independently authenticated host
before considering any operational use. All decisions are lab-only.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from hmac import compare_digest
from threading import RLock
from typing import Callable, FrozenSet, Optional, Tuple
import json
import re

SCHEMA = 'prumo.s0.meta.registry.snapshot/0.1-candidate'
PURPOSES = frozenset({'GET_VERIFY_TOKEN', 'POST_APP_SECRET', 'GRAPH_ACCESS_TOKEN', 'REGISTRY_READ'})
SLOTS = frozenset({'GET_VERIFY_TOKEN', 'POST_APP_SECRET', 'GRAPH_ACCESS_TOKEN'})
FLAGS = {'production_authorized': False, 'send_authorized': False,
         'external_http_ack': False, 'commercial_transition_authorized': False}
_ID = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
_SLOT = re.compile(r'^[A-Z][A-Z0-9_]{2,127}$')
_PHONE = re.compile(r'^\d{5,25}$')


def _ident(v: object) -> bool:
    return type(v) is str and bool(_ID.fullmatch(v))


def _revision(v: object) -> bool:
    return type(v) is int and 1 <= v <= 2**63 - 1


@dataclass(frozen=True)
class Channel:
    canal_id: str
    waba_id: str
    phone_number_id: str
    binding_revision: int
    grant_revision: int
    active: bool = True
    grant_active: bool = True


@dataclass(frozen=True)
class App:
    app_ref: str
    route_ref: str
    concessionaria_id: str
    tenant: str
    route_revision: int
    app_revision: int
    principal_revision: int
    valid_from_ms: int
    valid_until_ms: int
    slots: Tuple[Tuple[str, str], ...]
    channels: Tuple[Channel, ...]
    active: bool = True
    ownership_evidence_state: str = 'UNVERIFIED'
    delegation_evidence_state: str = 'UNVERIFIED'


@dataclass(frozen=True)
class M2MPrincipal:
    """Resolved by an injected verifier; never derived from client claims."""
    principal_ref: str
    issuer_ref: str
    audience: str
    key_revision: int
    allowed_stores: FrozenSet[str]
    allowed_purposes: FrozenSet[str]
    privileged_slot_reader: bool
    active: bool = True


@dataclass(frozen=True)
class HostScope:
    """Resolved independently by an injected host router."""
    route_ref: str
    concessionaria_id: str
    app_ref: str
    canal_id: Optional[str] = None
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None


@dataclass(frozen=True)
class Revisions:
    route: int
    app: int
    binding: int
    grant: int
    principal: int


class RegistryLab:
    """Lock-protected synthetic authority; no SQL, storage or external writes."""
    def __init__(self, apps: Tuple[App, ...], tenant_to_store: dict[str, str]):
        self._lock = RLock()
        self._apps = tuple(apps)
        self._tenant_to_store = dict(tenant_to_store)

    def _valid(self) -> bool:
        if not 0 < len(self._apps) <= 100 or not self._tenant_to_store:
            return False
        routes, app_ids, channels, phones, waba_owners, slots = set(), set(), set(), set(), {}, set()
        for a in self._apps:
            if (not all(_ident(x) for x in (a.app_ref, a.route_ref, a.concessionaria_id, a.tenant))
                or a.route_ref in routes or a.app_ref in app_ids
                or self._tenant_to_store.get(a.tenant) != a.concessionaria_id
                or not all(_revision(x) for x in (a.route_revision, a.app_revision, a.principal_revision))
                or type(a.active) is not bool
                or not (type(a.valid_from_ms) is int and type(a.valid_until_ms) is int
                        and 0 <= a.valid_from_ms < a.valid_until_ms)
                or a.ownership_evidence_state != 'UNVERIFIED'
                or a.delegation_evidence_state != 'UNVERIFIED'):
                return False
            routes.add(a.route_ref)
            app_ids.add(a.app_ref)
            if set(k for k, _ in a.slots) != SLOTS or len(a.slots) != 3:
                return False
            for _, slot in a.slots:
                if (type(slot) is not str or not _SLOT.fullmatch(slot) or slot.startswith('SUPABASE_')
                    or slot in slots):
                    return False
                slots.add(slot)
            if not 0 < len(a.channels) <= 1000:
                return False
            for c in a.channels:
                if (not all(_ident(x) for x in (c.canal_id, c.waba_id))
                    or type(c.phone_number_id) is not str or not _PHONE.fullmatch(c.phone_number_id)
                    or not _revision(c.binding_revision) or not _revision(c.grant_revision)
                    or type(c.active) is not bool or type(c.grant_active) is not bool
                    or c.canal_id in channels or c.phone_number_id in phones
                    or (c.waba_id in waba_owners and waba_owners[c.waba_id] != a.app_ref)):
                    return False
                channels.add(c.canal_id)
                phones.add(c.phone_number_id)
                waba_owners[c.waba_id] = a.app_ref
        return len(channels) <= 1000

    def revoke_channel(self, route_ref: str, canal_id: str, expected: Revisions) -> str:
        """Synthetic CAS. Never used as a production or privileged S0 mutation."""
        with self._lock:
            if not self._valid() or not isinstance(expected, Revisions):
                return 'DENIED'
            for n, app in enumerate(self._apps):
                if app.route_ref != route_ref:
                    continue
                for i, channel in enumerate(app.channels):
                    if channel.canal_id != canal_id:
                        continue
                    actual = Revisions(app.route_revision, app.app_revision,
                                       channel.binding_revision, channel.grant_revision,
                                       app.principal_revision)
                    if actual != expected:
                        return 'CONFLICT'
                    if not channel.active or not channel.grant_active:
                        return 'DENIED'
                    if app.route_revision == 2**63 - 1 or channel.grant_revision == 2**63 - 1:
                        return 'DENIED'
                    changed = replace(channel, grant_revision=channel.grant_revision + 1,
                                      grant_active=False)
                    chans = list(app.channels)
                    chans[i] = changed
                    apps = list(self._apps)
                    apps[n] = replace(app, channels=tuple(chans), route_revision=app.route_revision + 1)
                    self._apps = tuple(apps)
                    return 'REVOKED_LAB_ONLY'
            return 'DENIED'


class RegistryPort:
    def __init__(self, lab: RegistryLab,
                 verify_m2m: Callable[[object], Optional[M2MPrincipal]],
                 resolve_host: Callable[[object], Optional[HostScope]],
                 clock_ms: Callable[[], int]):
        self._lab = lab
        self._verify_m2m = verify_m2m
        self._resolve_host = resolve_host
        self._clock_ms = clock_ms

    @staticmethod
    def _answer(state: str, reason: str, snapshot: Optional[dict] = None) -> dict:
        return {'schema': SCHEMA, 'decision': state, 'reason': reason,
                'snapshot': snapshot, **FLAGS}

    def read(self, *, proof: object, host_ref: object, purpose: str,
             expected: Optional[Revisions] = None,
             previous_snapshot_ref: Optional[str] = None) -> dict:
        """Read or point-of-use recheck. All ports are synthetic injections.

        `previous_snapshot_ref` is a non-bearer integrity correlation. A mismatch
        is stale even when expected versions were omitted.
        """
        if (type(purpose) is not str or purpose not in PURPOSES
            or (expected is not None and not isinstance(expected, Revisions))
            or (previous_snapshot_ref is not None and
                (type(previous_snapshot_ref) is not str or
                 not re.fullmatch(r'[0-9a-f]{64}', previous_snapshot_ref)))):
            return self._answer('DENIED', 'INVALID_REQUEST')
        try:
            with self._lab._lock:
                if not self._lab._valid():
                    return self._answer('UNAVAILABLE', 'REGISTRY_UNAVAILABLE')
                # All authorization checks precede any metadata exposure.
                principal = self._verify_m2m(proof)
                scope = self._resolve_host(host_ref)
                now = self._clock_ms()
                if (type(principal) is not M2MPrincipal or type(scope) is not HostScope
                    or type(now) is not int or now < 0
                    or not principal.active or not _ident(principal.principal_ref)
                    or not _ident(principal.issuer_ref) or not _ident(principal.audience)
                    or principal.audience != 'LAB_S0_M09' or not _revision(principal.key_revision)
                    or purpose not in principal.allowed_purposes
                    or scope.concessionaria_id not in principal.allowed_stores
                    or not all(_ident(x) for x in (scope.concessionaria_id, scope.route_ref, scope.app_ref))):
                    return self._answer('DENIED', 'NOT_AUTHORIZED')
                # GET/POST routing must be anchored in the trusted host, not webhook bytes.
                if purpose in ('GRAPH_ACCESS_TOKEN', 'REGISTRY_READ') and not all(
                    _ident(x) for x in (scope.canal_id, scope.waba_id, scope.phone_number_id)
                ):
                    return self._answer('DENIED', 'NOT_AUTHORIZED')
                app = next((a for a in self._lab._apps if a.route_ref == scope.route_ref), None)
                if (app is None or not app.active or not app.valid_from_ms <= now < app.valid_until_ms
                    or app.concessionaria_id != scope.concessionaria_id or app.app_ref != scope.app_ref
                    or self._lab._tenant_to_store.get(app.tenant) != app.concessionaria_id):
                    return self._answer('DENIED', 'NOT_AUTHORIZED')
                channel = None
                if scope.canal_id is not None:
                    channel = next((c for c in app.channels if c.canal_id == scope.canal_id), None)
                    if (channel is None or not channel.active or not channel.grant_active
                        or channel.waba_id != scope.waba_id
                        or channel.phone_number_id != scope.phone_number_id):
                        return self._answer('DENIED', 'NOT_AUTHORIZED')
                # Route-only snapshots cannot imply authorization over any channel.
                if purpose in ('GRAPH_ACCESS_TOKEN', 'REGISTRY_READ') and channel is None:
                    return self._answer('DENIED', 'NOT_AUTHORIZED')
                versions = Revisions(app.route_revision, app.app_revision,
                                     channel.binding_revision if channel else 0,
                                     channel.grant_revision if channel else 0,
                                     app.principal_revision)
                if principal.key_revision != app.principal_revision:
                    return self._answer('DENIED', 'NOT_AUTHORIZED')
                if expected is not None and expected != versions:
                    return self._answer('STALE_OR_REVOKED', 'STALE_REVISION')
                slot = dict(app.slots).get(purpose)
                payload = {'concessionaria_id': app.concessionaria_id,
                           'app_ref': app.app_ref, 'route_ref': app.route_ref,
                           'canal_id': channel.canal_id if channel else None,
                           'waba_id': channel.waba_id if channel else None,
                           'phone_number_id': channel.phone_number_id if channel else None,
                           'observed_at_ms': now,
                           'revisions': {'route': versions.route, 'app': versions.app,
                                         'binding': versions.binding, 'grant': versions.grant,
                                         'principal': versions.principal},
                           'ownership_evidence_state': 'UNVERIFIED',
                           'delegation_evidence_state': 'UNVERIFIED'}
                # Hash is an integrity check, NOT signature, authentication or bearer.
                digest_data = {k: v for k, v in payload.items() if k != 'observed_at_ms'}
                digest_data['purpose'] = purpose
                digest_data['principal_ref'] = principal.principal_ref
                digest_data['principal_key_revision'] = principal.key_revision
                snapshot_ref = sha256(json.dumps(digest_data, sort_keys=True,
                                 separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
                if (previous_snapshot_ref is not None and
                    not compare_digest(previous_snapshot_ref, snapshot_ref)):
                    return self._answer('STALE_OR_REVOKED', 'STALE_SNAPSHOT')
                payload['snapshot_ref'] = snapshot_ref
                payload['source_revision'] = snapshot_ref
                if slot is not None and principal.privileged_slot_reader:
                    payload['slot_ref'] = slot  # exactly one purpose-specific slot name
                return self._answer('SNAPSHOT_CANDIDATE_ONLY', 'LAB_READ_ONLY', payload)
        except Exception:
            # No provider error text, secrets or metadata leak through the port.
            return self._answer('UNAVAILABLE', 'DEPENDENCY_UNAVAILABLE')
