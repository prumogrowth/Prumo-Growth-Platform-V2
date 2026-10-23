"""I53: canonical S0/S1 intake through real local signed GoTrue gateway.
No new public RPC. HMAC domain is INTAKE53 (not legacy I37 INTAKE).
Only loopback PostgreSQL through the existing separated signer.
"""
from __future__ import annotations
import time
import uuid
from backend.s1_gateway_intake_signed_local import LocalSignedIntakeOnlyGateway
from backend.s1_gateway_signed_local import _proof_material

_SQL_CANONICAL_INTAKE = (
    "select prumo_s1_signed_i20.invocar_intake_v53("
    "%s::uuid,%s::uuid,%s::uuid,%s::boolean,%s::bigint,"
    "%s::uuid,%s::bigint,%s::uuid,%s::text)"
)

class LocalSignedCanonicalIntakeGateway(LocalSignedIntakeOnlyGateway):
    _statement = _SQL_CANONICAL_INTAKE

    def proof(self, principal, operator, paused, version, authorization,
              *, issued=None, nonce=None):
        issued_at=int(time.time()) if issued is None else issued
        unique=uuid.uuid4() if nonce is None else nonce
        action=("P:" if paused else "R:")+str(version)
        material=_proof_material("INTAKE53",principal.actor_id,principal.session_id,
                 (None,None,None,None,operator,action),issued_at,unique)
        signature=self.signer.sign(self.key_id,material,authorization)
        return (principal.actor_id,principal.session_id,operator,paused,version,
                self.key_id,issued_at,unique,signature)
