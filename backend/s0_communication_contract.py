"""Candidate compatibility profiles, not an approved operational API.

No authentication, I/O, domain writes, model calls or permission minting.
Positive parsing proves structure only. S0/S1 must authenticate and recheck
inside their existing transaction before using a prepared physical payload.
"""
from dataclasses import dataclass
import re
from uuid import UUID

CONTRACT = 's0.communication.compatibility/0.1-candidate'
CAPTURE_PROFILE = 's0.cfi01.capture.local'
FV_INTENT_PROFILE = 'fv.cfi01.intent.candidate'
MAX_PG_VERSION = 9223372036854775807
MAX_JS_INTEGER = 9007199254740991
_CAPTURE = frozenset(('case_ref', 'expected_cycle_version', 'idempotency_key'))
_RECEIPT = frozenset(('store_ref', 'case_ref', 'closure_event_ref',
    'expected_cycle_version', 'assignment_ref', 'snapshot_sha256',
    'message_watermark', 'message_count'))


class InvalidCompatibilityInput(ValueError):
    """Fixed diagnostics only: never echo caller values or credentials."""


def _uuid(value):
    if type(value) is not str:
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def _digest(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _version(value):
    return type(value) is int and 1 <= value <= MAX_PG_VERSION


def _key(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9._:-]{8,128}', value) is not None


def _exact(raw, keys):
    return type(raw) is dict and set(raw) == keys


@dataclass(frozen=True)
class CaptureRequest:
    case_ref: str
    expected_cycle_version: int
    idempotency_key: str

    def to_physical_payload(self):
        # Revalidate even a directly constructed instance; dataclasses are not proof.
        raw = dict(case_ref=self.case_ref, expected_cycle_version=self.expected_cycle_version,
                   idempotency_key=self.idempotency_key)
        _capture(raw)
        return raw

    def to_js_payload(self):
        raw = self.to_physical_payload()
        if self.expected_cycle_version > MAX_JS_INTEGER:
            raise InvalidCompatibilityInput('UNSAFE_JS_VERSION_REQUIRES_CONTRACT_DECISION')
        return raw


def _capture(raw):
    if (not _exact(raw, _CAPTURE) or not _uuid(raw['case_ref'])
            or not _version(raw['expected_cycle_version']) or not _key(raw['idempotency_key'])):
        raise InvalidCompatibilityInput('INVALID_CAPTURE_SHAPE')
    return CaptureRequest(**raw)


@dataclass(frozen=True)
class PreparedRequest:
    state: str
    request: CaptureRequest | None = None


def prepare_request(profile, raw):
    if type(profile) is not str:
        return PreparedRequest('INPUT_REJECTED')
    if profile == CAPTURE_PROFILE:
        try:
            return PreparedRequest('STRUCTURE_ONLY', _capture(raw))
        except InvalidCompatibilityInput:
            return PreparedRequest('INPUT_REJECTED')
    if profile == FV_INTENT_PROFILE:
        # Preserve the unresolved case/cycle version distinction. No aliasing.
        required = {'case_ref', 'expected_case_version', 'idempotency_key'}
        if (type(raw) is dict and required <= set(raw)
                and set(raw) <= required | {'request_id', 'correlation_id'}
                and _uuid(raw['case_ref']) and _key(raw['idempotency_key'])
                and (_version(raw['expected_case_version']) or (
                    type(raw['expected_case_version']) is str
                    and 1 <= len(raw['expected_case_version']) <= 128
                    and raw['expected_case_version'].strip() == raw['expected_case_version']))
                and all(type(raw[k]) is str and raw[k].strip() for k in
                        ('request_id', 'correlation_id') if k in raw)):
            return PreparedRequest('CASE_VERSION_BINDING_REQUIRED')
        return PreparedRequest('INPUT_REJECTED')
    return PreparedRequest('UNSUPPORTED_PROFILE')


@dataclass(frozen=True)
class ReceiptMetadata:
    store_ref: str
    case_ref: str
    closure_event_ref: str
    expected_cycle_version: int
    assignment_ref: str
    snapshot_sha256: str
    message_watermark: str
    message_count: int


def parse_receipt_metadata(raw):
    """Server-only structural metadata; never a verified/transferable receipt."""
    if (not _exact(raw, _RECEIPT)
            or not all(_uuid(raw[k]) for k in ('store_ref', 'case_ref',
                'closure_event_ref', 'assignment_ref', 'message_watermark'))
            or not _version(raw['expected_cycle_version'])
            or not _digest(raw['snapshot_sha256'])
            or type(raw['message_count']) is not int or not 1 <= raw['message_count'] <= 2500):
        raise InvalidCompatibilityInput('INVALID_RECEIPT_METADATA')
    return ReceiptMetadata(**raw)


def compare_receipt_metadata(captured, current):
    # Compare all facts, not only hash or cycle version. Does not authenticate.
    before = parse_receipt_metadata(captured)
    after = parse_receipt_metadata(current)
    return 'UNCHANGED_STRUCTURE_ONLY' if before == after else 'STALE_REVIEW_REQUIRED'


@dataclass(frozen=True)
class F03ReviewCandidate:
    field_codes: tuple[str, ...]
    metadata_snapshot_sha256: str


def parse_f03_review_candidate(raw):
    """Matches the existing S2 output accepted by the PR #1 S0 bridge.

    snapshotRef binds the SEALED METADATA digest, not receipt.snapshot_sha256.
    Values/evidence remain in the separate S0-owned field proposal validator.
    """
    if not _exact(raw, {'status', 'fieldCodes', 'snapshotRef'}) or raw['status'] != 'S0_RECHECK_ONLY':
        raise InvalidCompatibilityInput('INVALID_F03_REVIEW_SHAPE')
    codes = raw['fieldCodes']
    if (type(codes) is not list or not 1 <= len(codes) <= 12
            or any(type(k) is not str or re.fullmatch(r'[a-z_]{2,48}', k) is None for k in codes)
            or codes != sorted(set(codes)) or not _digest(raw['snapshotRef'])):
        raise InvalidCompatibilityInput('INVALID_F03_REVIEW_SHAPE')
    return F03ReviewCandidate(tuple(codes), raw['snapshotRef'])


def match_f03_review(raw, *, sealed_metadata_sha256, proposed_field_codes):
    """Structural correlation only. No bearer, authority or grant accepted here."""
    candidate = parse_f03_review_candidate(raw)
    if (not _digest(sealed_metadata_sha256) or type(proposed_field_codes) is not tuple
            or not 1 <= len(proposed_field_codes) <= 12
            or any(type(k) is not str or re.fullmatch(r'[a-z_]{2,48}', k) is None for k in proposed_field_codes)
            or len(set(proposed_field_codes)) != len(proposed_field_codes)):
        raise InvalidCompatibilityInput('INVALID_SERVER_CORRELATION_SHAPE')
    if candidate.metadata_snapshot_sha256 != sealed_metadata_sha256:
        return 'STALE_REVIEW_REQUIRED'
    if candidate.field_codes != tuple(sorted(proposed_field_codes)):
        return 'FIELD_REVIEW_REQUIRED'
    return 'MATCHED_STRUCTURE_ONLY'


def completion_review_projection(physical_state):
    """Candidate UI projection, deliberately incompatible with C11/C13 results.

    CAPTURED and ALREADY_CAPTURED do not mean extracted/applied. No actor, tenant,
    snapshot, receipt, field values or opaque internal correlators leave here.
    """
    states = {
        'CAPTURED_LOCAL_ONLY': 'RECORDED_REVIEW_ONLY',
        'ALREADY_CAPTURED': 'RECORDED_REVIEW_ONLY',
        'VERIFIED_REVIEW_ONLY_LOCAL': 'RECHECKED_REVIEW_ONLY',
        'VERIFIED_CONTRACT_PENDING': 'CONTRACT_PENDING',
        'DUPLICATE_SNAPSHOT': 'REVIEW_REQUIRED',
        'NO_CONVERSATION': 'REVIEW_REQUIRED',
        'DENIED': 'DENIED', 'BLOCKED_S1': 'DENIED',
        'STALE': 'STALE', 'UNAVAILABLE': 'UNAVAILABLE',
        'INPUT_REJECTED': 'INPUT_REJECTED',
        'UNSUPPORTED_COMMAND': 'INPUT_REJECTED',
    }
    state = states.get(physical_state, 'INPUT_REJECTED') if type(physical_state) is str else 'INPUT_REJECTED'
    return {'schema_version': CONTRACT, 'state': state, 'confirmed_persisted': False}
