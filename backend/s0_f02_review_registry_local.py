"""Authenticated, durable S0 intake of UNVERIFIED F02 review requests.

LOCAL PG17 ONLY. Reuses the exact GoTrue/DSN/CFI implementation. Both HMACs,
CFI recheck, nonce, request and audit execute in one transaction. This is not
a manager ratification API, F03 evidence reader, scheduler or Meta adapter.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
import time
from uuid import UUID, uuid4

from backend.identity_boundary import Denied, Principal
from backend.s0_cfi01_atomic_commands_local import (
    S0CFI01AtomicCommandsLocal, S0InternalReceiptResultLocal,
)
from backend.s0_cfi01_authenticated_commands_local import CommandState
from backend.s0_cfi01_f03_receipt_bridge_local import _valid_binding
from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, HandoffState, prepare_handoff,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow

SCHEMA='prumo.s0.f02.review.request/0.1-candidate'
RESULT_SCHEMA='prumo.s0.f02.review.result/0.1-candidate'
_SQL='''select * from prumo_private.f02_review_signed_local(
 %s::text,%s::text,%s::integer,%s::uuid,%s::uuid,%s::uuid,%s::bigint,
 %s::uuid,%s::text,%s::uuid,%s::bigint,%s::uuid,%s::text,%s::text)'''


class ReviewState(str,Enum):
    RECORDED_REVIEW_ONLY='RECORDED_REVIEW_ONLY'
    REPLAY_REVIEW_ONLY='REPLAY_REVIEW_ONLY'
    CURRENT_REVIEW_ONLY='CURRENT_REVIEW_ONLY'
    WITHDRAWN_REVIEW_ONLY='WITHDRAWN_REVIEW_ONLY'
    EXPIRED_REVIEW_ONLY='EXPIRED_REVIEW_ONLY'
    INPUT_REJECTED='INPUT_REJECTED'
    DENIED='DENIED'
    STALE='STALE'
    IDEMPOTENCY_CONFLICT='IDEMPOTENCY_CONFLICT'
    REQUEST_EXPIRED='REQUEST_EXPIRED'
    REVIEW_REQUEST_NOT_FOUND='REVIEW_REQUEST_NOT_FOUND'
    CLOCK_RECHECK_REQUIRED='CLOCK_RECHECK_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'


@dataclass(frozen=True)
class ReviewResult:
    state: ReviewState
    review_ref: str | None=None
    revision: int | None=None
    observed_at: datetime | None=None
    request_sha256: str | None=None
    expires_at: datetime | None=None

    def projection(self):
        return dict(schema=RESULT_SCHEMA,state=self.state.value,
            review_ref=self.review_ref,revision=None if self.revision is None else str(self.revision),
            observed_at=None if self.observed_at is None else self.observed_at.isoformat(),
            request_sha256=self.request_sha256,
            expires_at=None if self.expires_at is None else self.expires_at.isoformat(),
            evidence_scope='CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING',
            human_ratification='NOT_IMPLEMENTED_CONTRACT_PENDING',
            send_authorized=False,scheduling_authorized=False,
            commercial_transition_authorized=False)


def _utc(value):
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('AWARE_TIME_REQUIRED')
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds')


def _json_value(value):
    if type(value) is UUID:return str(value)
    if type(value) is datetime:return _utc(value)
    raise ValueError('UNSUPPORTED_REVIEW_VALUE')


def prepare_document(binding,evidence,proposal,window):
    """Pure compatibility only; no supplied digest/state becomes S0 proof."""
    if not _valid_binding(binding) or type(window) is not ReviewWindow:
        raise ValueError('INVALID_REVIEW_INPUT')
    handoff=prepare_handoff(evidence,proposal)  # Exact original F02 validator/hash.
    if handoff.status is not HandoffState.HANDOFF_REVIEW_ONLY:
        raise ValueError('F02_HANDOFF_REJECTED')
    r=binding.receipt
    if (str(proposal.shop_id),str(proposal.case_id),str(proposal.closure_id)) != (
            r.store_ref,r.case_ref,r.closure_event_ref):
        raise ValueError('CFI_SCOPE_MISMATCH')
    start,end=_utc(window.requested_at),_utc(window.expires_at)
    if start>=end:raise ValueError('INVALID_REVIEW_WINDOW')
    # Caller expiry is only an immutable voluntary ceiling on THIS request.
    # No 48h / 24h-7d business or ratification policy is adopted here.
    document=dict(schema=SCHEMA,request_sha256=handoff.untrusted_request_sha256,
        evidence=asdict(evidence),proposal=asdict(proposal),requested_at=start,expires_at=end)
    body=json.dumps(document,default=_json_value,sort_keys=True,ensure_ascii=True,separators=(',',':'))
    if len(body.encode())>8192:raise ValueError('REVIEW_INPUT_TOO_LARGE')
    return body


class S0F02ReviewRegistryLocal:
    def __init__(self,gateway:S0CFI01AtomicCommandsLocal):
        if type(gateway) is not S0CFI01AtomicCommandsLocal:
            raise TypeError('Requires existing real CFI gateway')
        self._s0=gateway

    def _parameters(self,operation,body,revision,binding,principal):
        """Internal broker proof only. Never expose these parameters to UI/F02."""
        r=binding.receipt;issued=int(time.time());nonce=uuid4()
        case,event=UUID(r.case_ref),UUID(r.closure_event_ref)
        base=('recheck_human_closure',principal,case,r.expected_cycle_version,
              event,binding.idempotency_key,self._s0._key_id,issued,nonce)
        cfi=hmac.new(self._s0._secret,self._s0._material(*base),hashlib.sha256).hexdigest()
        material='|'.join(['s0-f02-review-local-v1',operation,str(principal.actor_id),
            str(principal.session_id),str(case),str(r.expected_cycle_version),str(event),
            binding.idempotency_key,str(self._s0._key_id),str(issued),str(nonce),
            hashlib.sha256(body.encode()).hexdigest(),str(revision) if revision is not None else '-'])
        review=hmac.new(self._s0._secret,material.encode(),hashlib.sha256).hexdigest()
        return (operation,body,revision,principal.actor_id,principal.session_id,case,
                r.expected_cycle_version,event,binding.idempotency_key,
                self._s0._key_id,issued,nonce,cfi,review)

    def execute(self,authorization,operation,binding,evidence,proposal,window,*,expected_revision=None):
        if (type(operation) is not str or operation not in ('record','read','withdraw')
            or (expected_revision is not None and (type(expected_revision) is not int
                or not 1<=expected_revision<=2147483647))
            or (operation=='withdraw' and expected_revision is None)):
            return ReviewResult(ReviewState.INPUT_REJECTED)
        try:body=prepare_document(binding,evidence,proposal,window)
        except Exception:return ReviewResult(ReviewState.INPUT_REJECTED)
        try:
            principal=self._s0._identity.verify(authorization)
            if (type(principal) is not Principal or type(principal.actor_id) is not UUID
                or type(principal.session_id) is not UUID):raise Denied()
        except Denied:return ReviewResult(ReviewState.DENIED)
        except Exception:return ReviewResult(ReviewState.UNAVAILABLE)
        params=self._parameters(operation,body,expected_revision,binding,principal)
        try:
            import psycopg
            with psycopg.connect(self._s0._dsn,connect_timeout=5) as c:
                rows=c.execute(_SQL,params).fetchall()
                if len(rows)!=1 or len(rows[0])!=14:raise Denied()
                row=rows[0];r=binding.receipt
                decoded=self._s0._decode_result('recheck_human_closure',UUID(r.case_ref),
                    UUID(r.closure_event_ref),r.expected_cycle_version,[row[6:]],True)
                # PR #13 invariant: compare ALL receipt metadata before commit.
                if type(decoded) is not S0InternalReceiptResultLocal or decoded.receipt!=r:
                    raise _StaleReceipt()
                state=ReviewState(row[0])
                if (state not in (ReviewState.RECORDED_REVIEW_ONLY,ReviewState.REPLAY_REVIEW_ONLY,
                        ReviewState.CURRENT_REVIEW_ONLY,ReviewState.WITHDRAWN_REVIEW_ONLY,
                        ReviewState.EXPIRED_REVIEW_ONLY) or type(row[1]) is not UUID
                    or type(row[2]) is not int or row[2]<1
                    or type(row[3]) is not datetime or row[3].tzinfo is None
                    or row[4]!=json.loads(body)['request_sha256']
                    or type(row[5]) is not datetime or _utc(row[5])!=_utc(window.expires_at)):
                    raise Denied()
                result=ReviewResult(state,str(row[1]),row[2],row[3],row[4],row[5])
            return result
        except _StaleReceipt:return ReviewResult(ReviewState.STALE)
        except Denied:return ReviewResult(ReviewState.DENIED)
        except Exception as exc:
            state={'42501':ReviewState.DENIED,'40001':ReviewState.STALE,
                   '23505':ReviewState.IDEMPOTENCY_CONFLICT,'P2001':ReviewState.REQUEST_EXPIRED,
                   'P2002':ReviewState.REVIEW_REQUEST_NOT_FOUND,'P2003':ReviewState.CLOCK_RECHECK_REQUIRED,
                   '22007':ReviewState.INPUT_REJECTED,'22008':ReviewState.INPUT_REJECTED,
                   '22P02':ReviewState.INPUT_REJECTED}.get(getattr(exc,'sqlstate',None),ReviewState.UNAVAILABLE)
            return ReviewResult(state)


class _StaleReceipt(Exception):pass
