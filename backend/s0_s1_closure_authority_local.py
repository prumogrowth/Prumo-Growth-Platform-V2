"""CFI-01 S0/S1 authorization bridge for LOCAL PostgreSQL testing only.

Uses the actual S1-002 `public.equipe_prumo_s1` table from migration 038.
S0 baseline alone lacks that table: absence must FAIL CLOSED; no S1 fixture
is fabricated or silently treated as a production authorization.

Only normal per-store operator/grant is supported here. Special case
exceptions (S1 fixture 055) are deliberately NOT accepted by this adapter.
Both methods must run on the exact same S0 transaction cursor.
"""
from __future__ import annotations

import uuid
from typing import Any

from backend.identity_boundary import Principal
from backend.s0_human_closure_event_local import S1Proof

# S1 I13 contract: lock the team member BEFORE the case/assignment to
# preserve order against a concurrent S1 transfer, pause or deactivation.
_TEAM_FIRST = """select e.ator_id from public.equipe_prumo_s1 e
where e.ator_id=%s::uuid and e.estado='ativo'
for share of e"""

# The public assignment and normal store grant have already been checked and
# locked by S0's closure transaction, but verify their *joint* scope again.
_SCOPE = """select 1 from public.atribuicoes_humanas a
join public.casos_humanos h
 on h.id=a.caso_id and h.concessionaria_id=a.concessionaria_id
join public.vinculos_papel_escopo v
 on v.concessionaria_id=a.concessionaria_id and v.ator_id=a.operador_id
where a.id=%s::uuid and a.operador_id=%s::uuid
 and a.concessionaria_id=%s::uuid and a.caso_id=%s::uuid
 and a.encerrada_em is null and v.papel in ('operador','gestor')
 and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())"""


class S0S1LocalTeamAuthority:
    """Local-only normal S1 authorization. Not a production grant broker."""
    def lock_team(self, cursor: Any, principal: Principal) -> S1Proof:
        if type(principal) is not Principal or type(principal.actor_id) is not uuid.UUID:
            return S1Proof.DENY
        cursor.execute(_TEAM_FIRST, (principal.actor_id,))
        row = cursor.fetchone()
        return S1Proof.ALLOW if row is not None else S1Proof.DENY

    def check(self, cursor: Any, principal: Principal, store: uuid.UUID,
              case: uuid.UUID, assignment: uuid.UUID) -> S1Proof:
        if (type(principal) is not Principal
                or any(type(x) is not uuid.UUID for x in
                       (principal.actor_id, store, case, assignment))):
            return S1Proof.DENY
        cursor.execute(_SCOPE, (assignment, principal.actor_id, store, case))
        return S1Proof.ALLOW if cursor.fetchone() is not None else S1Proof.DENY
