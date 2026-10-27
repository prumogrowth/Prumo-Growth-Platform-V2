"""S0 security-denial events with strict low-sensitivity fields.

No actor UUID, session ID, Bearer token, SQL, exception message, payload or PII.
The receiving logger must be separately configured with retention and access
controls before any real deployment. This module does NOT persist denials to SQL.
"""
from __future__ import annotations

import logging
from typing import Protocol


_CATEGORIES = frozenset(("INPUT_REJECTED", "AUTH_DENIED", "IDENTITY_UNAVAILABLE"))
_COMMANDS = frozenset(("cancelar_plano", "conciliar_c07"))


class SecurityEventSink(Protocol):
    def emit(self, category: str, command: str) -> None: ...


class SanitizedDenialLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def emit(self, category: str, command: str) -> None:
        if category not in _CATEGORIES:
            raise ValueError("INVALID_EVENT_CATEGORY")
        safe_command = command if command in _COMMANDS else "desconhecido"
        # Never interpolate caller content (or exception text). The logger
        # can be forwarded to a separate protected sink in a future phase.
        self._logger.warning(
            "prumo_s0_security_denial category=%s command=%s",
            category, safe_command
        )
