"""Lab-only real S0 closure receipt -> pending F03 contract preflight.

This adapter consumes ONLY a GoTrue-authenticated, HMAC-signed, transactionally
verified S0 internal receipt. It intentionally does not coerce the physical
cycle version into the proposed case/form version or invent a field catalogue.
No message content, model call, HTTP endpoint, form mutation or bank action.
A positive outcome is a technical S0 recheck, NOT F03 processing authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from backend.s0_cfi01_atomic_commands_local import (
    S0CFI01AtomicCommandsLocal, S0InternalReceiptLocal,
    S0InternalReceiptResultLocal,
)
from backend.s0_cfi01_authenticated_commands_local import CommandState

# Not negotiable aliases: these are unfulfilled F03 inputs, NOT default values.
UNRATIFIED_F03_INPUTS = (
    'expected_case_version (distinct from ciclos_comerciais.versao_registro)',
    'form_version and authority for form edits',
    'allowed_fields_catalog_version and field classifications',
    'assignment_version (S0 currently proves only assignment UUID)',
    'authorized/minimized customer messages and purpose/LGPD',
    'OAI-05/OAI-07 output schema, provenance and write rules',
)


class S0F03BridgeState(str, Enum):
    VERIFIED_CONTRACT_PENDING = 'VERIFIED_CONTRACT_PENDING'
    INPUT_REJECTED = 'INPUT_REJECTED'
    DENIED = 'DENIED'
    STALE = 'STALE'
    UNAVAILABLE = 'UNAVAILABLE'


@dataclass(frozen=True)
class S0F03BoundReceiptLocal:
    """Internal server-only correlation, NOT a token or model payload.

    The receipt is minted by S0; never instantiate this from a browser or F03.
    The request key is retained only on the S0 server for signed recheck.
    """
    receipt: S0InternalReceiptLocal
    idempotency_key: str


@dataclass(frozen=True)
class S0F03BridgeResultLocal:
    state: S0F03BridgeState
    binding: S0F03BoundReceiptLocal | None = None


def _uuid(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        return str(UUID(value)) == value
    except (ValueError, AttributeError, TypeError):
        return False


def _valid_binding(binding: object) -> bool:
    if type(binding) is not S0F03BoundReceiptLocal:
        return False
    r = binding.receipt
    return (
        type(r) is S0InternalReceiptLocal
        and all(_uuid(v) for v in (
            r.store_ref, r.case_ref, r.closure_event_ref,
            r.assignment_ref, r.message_watermark,
        ))
        and type(r.expected_cycle_version) is int
        and 1 <= r.expected_cycle_version <= 9223372036854775807
        and type(r.message_count) is int and 1 <= r.message_count <= 2500
        and type(r.snapshot_sha256) is str
        and len(r.snapshot_sha256) == 64
        and all(c in '0123456789abcdef' for c in r.snapshot_sha256)
        and type(binding.idempotency_key) is str
        and 8 <= len(binding.idempotency_key) <= 128
        and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-'
                for c in binding.idempotency_key)
    )


def _blocked(state: CommandState) -> S0F03BridgeResultLocal:
    if state is CommandState.STALE:
        out = S0F03BridgeState.STALE
    elif state in (CommandState.INPUT_REJECTED, CommandState.UNSUPPORTED_COMMAND):
        out = S0F03BridgeState.INPUT_REJECTED
    elif state is CommandState.UNAVAILABLE:
        out = S0F03BridgeState.UNAVAILABLE
    else:
        out = S0F03BridgeState.DENIED
    return S0F03BridgeResultLocal(out)


class S0CFI01F03ReceiptBridgeLocal:
    """Only wraps an actual S0 atomic gateway; never accepts fake authority."""

    def __init__(self, s0: S0CFI01AtomicCommandsLocal):
        if type(s0) is not S0CFI01AtomicCommandsLocal:
            raise TypeError('requires real S0 atomic gateway object')
        self._s0 = s0

    def capture(self, authorization: str, payload: object) -> S0F03BridgeResultLocal:
        if type(payload) is not dict or set(payload) != {
            'case_ref', 'expected_cycle_version', 'idempotency_key',
        }:
            return S0F03BridgeResultLocal(S0F03BridgeState.INPUT_REJECTED)
        outcome = self._s0.capture_internal_receipt(authorization, payload)
        if type(outcome) is not S0InternalReceiptResultLocal:
            return S0F03BridgeResultLocal(S0F03BridgeState.DENIED)
        if outcome.state not in (
            CommandState.CAPTURED_LOCAL_ONLY, CommandState.ALREADY_CAPTURED,
        ):
            return _blocked(outcome.state)
        binding = S0F03BoundReceiptLocal(outcome.receipt, payload['idempotency_key'])
        if not _valid_binding(binding):
            return S0F03BridgeResultLocal(S0F03BridgeState.DENIED)
        # Binding must be the same scoped and versioned request that S0 signed.
        if (binding.receipt.case_ref != payload['case_ref']
                or binding.receipt.expected_cycle_version !=
                payload['expected_cycle_version']):
            return S0F03BridgeResultLocal(S0F03BridgeState.DENIED)
        return S0F03BridgeResultLocal(
            S0F03BridgeState.VERIFIED_CONTRACT_PENDING, binding)

    def recheck(self, authorization: str,
                binding: object) -> S0F03BridgeResultLocal:
        if not _valid_binding(binding):
            return S0F03BridgeResultLocal(S0F03BridgeState.INPUT_REJECTED)
        receipt = binding.receipt
        outcome = self._s0.recheck_internal_receipt(authorization, {
            'case_ref': receipt.case_ref,
            'expected_cycle_version': receipt.expected_cycle_version,
            'idempotency_key': binding.idempotency_key,
            'closure_event_ref': receipt.closure_event_ref,
        })
        if type(outcome) is not S0InternalReceiptResultLocal:
            return S0F03BridgeResultLocal(S0F03BridgeState.DENIED)
        if outcome.state is not CommandState.VERIFIED_REVIEW_ONLY_LOCAL:
            return _blocked(outcome.state)
        if outcome.receipt != receipt:
            return S0F03BridgeResultLocal(S0F03BridgeState.STALE)
        return S0F03BridgeResultLocal(
            S0F03BridgeState.VERIFIED_CONTRACT_PENDING, binding)
