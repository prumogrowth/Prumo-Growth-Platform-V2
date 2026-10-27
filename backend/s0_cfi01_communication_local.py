"""Local integration with the existing signed CFI-01 capture/recheck runtime.

Runtime is supplied by the pinned S0 checkout in integration/cfi01. No gateway
reimplementation, HTTP route, UI command, model call or commercial effect.
Bindings are server-internal and must never be deserialized from browser JSON.
"""
from dataclasses import asdict, dataclass
from backend.s0_communication_contract import (
    CAPTURE_PROFILE, prepare_request, parse_receipt_metadata,
    completion_review_projection,
)


@dataclass(frozen=True)
class CommunicationResultLocal:
    state: str
    binding: object | None = None

    def public_projection(self):
        return completion_review_projection(self.state)


class S0CFI01CommunicationLocal:
    def __init__(self, gateway):
        # No fake port or browser-supplied authority. Imports are deferred because
        # this lab runtime is staged from its source SHA, not merged into S0.
        from backend.s0_cfi01_atomic_commands_local import S0CFI01AtomicCommandsLocal
        from backend.s0_cfi01_f03_receipt_bridge_local import S0CFI01F03ReceiptBridgeLocal
        if type(gateway) is not S0CFI01AtomicCommandsLocal:
            raise TypeError('requires existing S0 atomic local gateway')
        self._bridge = S0CFI01F03ReceiptBridgeLocal(gateway)

    @staticmethod
    def _result(outcome):
        from backend.s0_cfi01_f03_receipt_bridge_local import (
            S0F03BridgeResultLocal, S0F03BridgeState,
        )
        if type(outcome) is not S0F03BridgeResultLocal:
            return CommunicationResultLocal('DENIED')
        if outcome.state is not S0F03BridgeState.VERIFIED_CONTRACT_PENDING:
            return CommunicationResultLocal(outcome.state.value)
        if outcome.binding is None:
            return CommunicationResultLocal('DENIED')
        # Structural validation supplements the real gateway's transaction;
        # it never replaces live GoTrue/session/S1/HMAC verification.
        parse_receipt_metadata(asdict(outcome.binding.receipt))
        return CommunicationResultLocal(outcome.state.value, outcome.binding)

    def capture(self, authorization, payload, *, profile=CAPTURE_PROFILE):
        prepared = prepare_request(profile, payload)
        if prepared.state != 'STRUCTURE_ONLY':
            state = 'CASE_VERSION_BINDING_REQUIRED' if prepared.state == 'CASE_VERSION_BINDING_REQUIRED' else 'INPUT_REJECTED'
            # This pending result deliberately has NO verified binding.
            return CommunicationResultLocal(state)
        try:
            return self._result(self._bridge.capture(
                authorization, prepared.request.to_physical_payload()))
        except Exception:
            return CommunicationResultLocal('UNAVAILABLE')

    def recheck(self, authorization, binding):
        try:
            # The existing bridge checks concrete type, signs a NEW command and
            # revalidates live permissions, receipt, versions and messages in DB.
            return self._result(self._bridge.recheck(authorization, binding))
        except Exception:
            return CommunicationResultLocal('UNAVAILABLE')
