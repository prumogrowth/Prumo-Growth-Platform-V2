"""Unratified UI/CFI01 wire proposal. Pure validation, never a dispatcher.

No identity, SQL, network, receipt lookup or authority is created here. Recheck
references require an approved server binding. Case versions never become cycle
versions. Fingerprints correlate data and are NOT signatures or bearer tokens.
"""
from dataclasses import dataclass
import hashlib
import json
import re

from backend.s0_communication_contract import (
    CAPTURE_PROFILE, MAX_PG_VERSION, PreparedRequest, _uuid, _key,
    prepare_request, completion_review_projection,
)

COMMAND_SCHEMA = 'prumo.s0.cfi01.command/0.1-candidate'
RESULT_SCHEMA = 'prumo.s0.cfi01.result/0.1-candidate'
MAX_COMMAND_BYTES = 4096
CAPTURE = 'capture_human_closure'
RECHECK = 'recheck_human_closure'
COMMON = frozenset(('schema_version','command','request_id','correlation_id',
                    'case_ref','idempotency_key','expected_version'))
_RESULT = frozenset(('schema_version','command','request_id','correlation_id',
                     'case_ref','request_fingerprint','outcome'))
_STATES = frozenset(('CONTRACT_PENDING','REVIEW_REQUIRED','DENIED','STALE',
                     'UNAVAILABLE','INPUT_REJECTED'))
_PHYSICAL = frozenset(('CAPTURED_LOCAL_ONLY','ALREADY_CAPTURED',
    'VERIFIED_REVIEW_ONLY_LOCAL','VERIFIED_CONTRACT_PENDING',
    'CASE_VERSION_BINDING_REQUIRED','DUPLICATE_SNAPSHOT','NO_CONVERSATION',
    'DENIED','BLOCKED_S1','STALE','UNAVAILABLE','INPUT_REJECTED','UNSUPPORTED_COMMAND'))


class InvalidCandidate(ValueError):
    """Fixed diagnostics only; never echo untrusted payload or credentials."""


def _bad():
    raise InvalidCandidate('INVALID_CFI01_CANDIDATE')


@dataclass(frozen=True)
class CommandCandidate:
    command: str
    request_id: str
    correlation_id: str
    case_ref: str
    idempotency_key: str
    version_kind: str
    version_value: str
    capture_request_id: str | None = None

    def to_wire(self):
        result = dict(schema_version=COMMAND_SCHEMA, command=self.command,
            request_id=self.request_id, correlation_id=self.correlation_id,
            case_ref=self.case_ref, idempotency_key=self.idempotency_key,
            expected_version=dict(kind=self.version_kind,value=self.version_value))
        if self.capture_request_id is not None:
            result['capture_request_id'] = self.capture_request_id
        parse_command(result)  # Direct construction is not validation.
        return result


def parse_command(raw):
    if type(raw) is not dict or type(raw.get('command')) is not str:
        _bad()
    command = raw['command']
    if command not in (CAPTURE,RECHECK) or set(raw) != (
            COMMON if command == CAPTURE else COMMON | {'capture_request_id'}):
        _bad()
    if (raw['schema_version'] != COMMAND_SCHEMA
            or not all(_uuid(raw[k]) for k in ('request_id','correlation_id','case_ref'))
            or not _key(raw['idempotency_key'])
            or (command == RECHECK and not _uuid(raw['capture_request_id']))):
        _bad()
    version = raw['expected_version']
    if type(version) is not dict or set(version) != {'kind','value'}:
        _bad()
    kind,value = version['kind'],version['value']
    if type(kind) is not str or type(value) is not str:
        _bad()
    if kind == 'cycle':
        if re.fullmatch(r'[1-9][0-9]{0,18}', value) is None or int(value)>MAX_PG_VERSION:
            _bad()
    elif kind == 'case':
        if re.fullmatch(r'[A-Za-z0-9._:-]{1,128}', value) is None:
            _bad()
    else:
        _bad()
    return CommandCandidate(command,raw['request_id'],raw['correlation_id'],
        raw['case_ref'],raw['idempotency_key'],kind,value,raw.get('capture_request_id'))


def load_command(raw):
    """Candidate ingress decoder, no endpoint: reject duplicate decoded names."""
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_COMMAND_BYTES:
        _bad()
    def pairs(items):
        result = {}
        for key,value in items:
            if key in result:
                _bad()
            result[key] = value
        return result
    try:
        return parse_command(json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                              parse_constant=lambda _: _bad()))
    except (ValueError,UnicodeError,RecursionError,TypeError):
        _bad()


def _candidate(value):
    return parse_command(value.to_wire() if type(value) is CommandCandidate else value)


def _tuple(value, *, logical=False):
    c = _candidate(value)
    return [COMMAND_SCHEMA,c.command,*([] if logical else [c.request_id,c.correlation_id]),
            c.case_ref,c.idempotency_key,c.version_kind,c.version_value,c.capture_request_id or '-']


def request_fingerprint(value):
    encoded = json.dumps(_tuple(value),ensure_ascii=True,separators=(',',':')).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()


def compare_retry(previous,current):
    before,after = _candidate(previous),_candidate(current)
    if before.idempotency_key != after.idempotency_key:
        return 'NEW_INTENT_REVIEW_REQUIRED'
    if _tuple(before,logical=True) != _tuple(after,logical=True):
        return 'IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED'
    return 'SAME_INTENT_STRUCTURE_ONLY'


def prepare_physical_capture(value):
    c = _candidate(value)
    if c.command == RECHECK:
        return PreparedRequest('RECHECK_SERVER_BINDING_REQUIRED')
    if c.version_kind == 'case':
        return PreparedRequest('CASE_VERSION_BINDING_REQUIRED')
    # Only an explicitly named physical cycle precondition can roundtrip.
    # This DTO still does not authorize execution or ratify a UI command.
    return prepare_request(CAPTURE_PROFILE,dict(case_ref=c.case_ref,
        expected_cycle_version=int(c.version_value),idempotency_key=c.idempotency_key))


def _valid_state(command,state):
    return type(state) is str and state in _STATES | {
        'RECORDED_REVIEW_ONLY' if command == CAPTURE else 'RECHECKED_REVIEW_ONLY'}


def candidate_response(value, physical_state):
    c = _candidate(value)
    if type(physical_state) is not str or physical_state not in _PHYSICAL:
        _bad()
    state = completion_review_projection(physical_state)['state']
    if not _valid_state(c.command,state):
        _bad()
    return dict(schema_version=RESULT_SCHEMA,command=c.command,request_id=c.request_id,
        correlation_id=c.correlation_id,case_ref=c.case_ref,
        request_fingerprint=request_fingerprint(c),
        outcome=dict(state=state,commercial_effect_confirmed=False))


def stage_response(response,request, *, sent_context,current_context):
    """Structure/display only. Context UUIDs are UI-local and never wire claims."""
    rejected = dict(accepted=False,state='UNTRUSTED_RESPONSE',has_verified_effect=False,may_execute=False)
    try:
        c = _candidate(request)
        if (not _uuid(sent_context) or not _uuid(current_context) or sent_context != current_context
                or type(response) is not dict or set(response) != _RESULT
                or response['schema_version'] != RESULT_SCHEMA
                or any(response[k] != getattr(c,k) for k in ('command','request_id','correlation_id','case_ref'))
                or response['request_fingerprint'] != request_fingerprint(c)):
            return rejected
        outcome = response['outcome']
        if (type(outcome) is not dict or set(outcome) != {'state','commercial_effect_confirmed'}
                or outcome['commercial_effect_confirmed'] is not False
                or not _valid_state(c.command,outcome['state'])):
            return rejected
        return dict(accepted=True,state=outcome['state'],has_verified_effect=False,may_execute=False)
    except (ValueError,TypeError):
        return rejected
