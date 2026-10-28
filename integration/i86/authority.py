"""Installer-only I86 observation, NOT an operational authorization service.

Reuses GoTrue verification and the existing transactional session barrier.
Only private I86 evidence is written. No appointment/revocation function exists.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import re
from uuid import UUID, uuid4

from backend.identity_boundary import Denied, Principal, SupabaseGoTrueVerifier
from integration.i85.bootstrap import Bootstrap
from local_admin import boundary as b, environment as e

VERSION = "prumo.i86.observation.v1"
FIELDS = {"version", "idempotency_key", "expected_sha256"}
GOVERNANCE = {
    "APPOINT_DIRECTOR": ("D01_APPOINTING_AUTHORITY", "D02_APPROVAL_EVIDENCE"),
    "REPLACE_DIRECTOR": ("D01_APPOINTING_AUTHORITY", "D02_APPROVAL_EVIDENCE",
                         "D03_CONTINUITY_AND_HANDOVER"),
    "REACTIVATE_AUTHORITY": ("D01_APPOINTING_AUTHORITY", "D02_APPROVAL_EVIDENCE",
                            "D04_RECOVERY_AUTHORITY"),
    "REVOKE_ORGANIZATIONAL_AUTHORITY": ("D05_ORDINARY_REVOCATION_AUTHORITY",),
}


def governance_gate(action):
    """Capability diagnostic only. Even an existing Director cannot ratify it."""
    if type(action) is not str or action not in GOVERNANCE:
        raise ValueError("I86_UNKNOWN_GOVERNANCE_ACTION")
    return {"state": "PENDING_DECISION", "operationally_enabled": False,
            "missing_decisions": list(GOVERNANCE[action])}


def command(payload):
    if type(payload) is not dict or set(payload) != FIELDS:
        raise ValueError("I86_INPUT_FIELDS")
    p = payload.copy()
    if p["version"] != VERSION or type(p["version"]) is not str:
        raise ValueError("I86_INPUT_VERSION")
    if type(p["idempotency_key"]) is not str or re.fullmatch(
            r"[A-Za-z0-9._:-]{8,128}", p["idempotency_key"], re.ASCII) is None:
        raise ValueError("I86_INPUT_KEY")
    if p["expected_sha256"] is not None and (
            type(p["expected_sha256"]) is not str or re.fullmatch(
                "[0-9a-f]{64}", p["expected_sha256"], re.ASCII) is None):
        raise ValueError("I86_INPUT_CAS")
    return p


@dataclass(frozen=True)
class Result:
    state: str
    observation: dict | None = None


class Refusal(Exception):
    def __init__(self, state):
        self.state = state


SNAPSHOT = """
with observed as (
 select jsonb_build_object(
   'actor_id',u.id::text,'session_id',s.id::text,'auth_present',true,
   'actor_present',a.id is not null,'cargo',t.cargo,'estado',t.estado,
   'competence_active',coalesce(d.ativo,false),
   'ordinary_admin',coalesce(a.id is not null and t.cargo='diretor'
                            and t.estado='ativo' and d.ativo,false),
   'actor_revision',a.xmin::text,'team_revision',t.xmin::text,
   'competence_revision',d.xmin::text,'session_revision',s.xmin::text,
   'session_not_after',s.not_after) as state
 from auth.users u join auth.sessions s on s.user_id=u.id and s.id=%s
 left join public.atores a on a.id=u.id
 left join public.equipe_prumo_s1 t on t.ator_id=u.id
 left join prumo_private.s1_responsaveis_plataforma d on d.ator_id=u.id
 where u.id=%s
)
select state,encode(pg_catalog.sha256(convert_to(state::text,'UTF8')),'hex'),
 clock_timestamp() from observed
"""


class AuthorityLab:
    def __init__(self):
        if os.environ.get("PRUMO_I86_DISPOSABLE") != "YES":
            raise b.Blocked("I86_DISPOSABLE_OPT_IN_REQUIRED")
        self._owner = Bootstrap()
        self._owner.owned()  # immutable per-instance physical binding from I85
        env = e.discover()
        self._identity = SupabaseGoTrueVerifier(env["API_URL"], env["ANON_KEY"])

    def connect(self):
        self._owner.owned()
        return e.database()

    def install(self):
        with self.connect() as conn:
            conn.execute(Path(__file__).with_name("observation.sql").read_text())

    def capture(self, conn, principal):
        # Same direction as I79/I80; no authority is derived from JWT metadata.
        if not conn.execute("select prumo_private.cfi01_session_valid_local(%s,%s)",
                            (principal.actor_id, principal.session_id)).fetchone()[0]:
            raise Refusal("DENIED")
        conn.execute("select id from public.atores where id=%s for no key update",
                     (principal.actor_id,))
        conn.execute("select ator_id from public.equipe_prumo_s1 where ator_id=%s for update",
                     (principal.actor_id,))
        conn.execute("select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for share",
                     (principal.actor_id,))
        if not conn.execute("select prumo_private.cfi01_session_valid_local(%s,%s)",
                            (principal.actor_id, principal.session_id)).fetchone()[0]:
            raise Refusal("DENIED")
        row = conn.execute(SNAPSHOT, (principal.session_id, principal.actor_id)).fetchone()
        if row is None:
            raise Refusal("DENIED")
        return row

    def record(self, conn, principal, payload):
        from psycopg.types.json import Jsonb
        conn.execute("set local lock_timeout='8s'")
        conn.execute("set local statement_timeout='15s'")
        conn.execute("set local timezone='UTC'")
        key = "i86-observation|"+str(principal.actor_id)+"|"+str(principal.session_id)+"|"+payload["idempotency_key"]
        conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (key,))
        state, digest, now = self.capture(conn, principal)
        existing = conn.execute(
            "select id,request,state_sha256,observed_at from prumo_i86_lab.observations "
            "where actor_id=%s and session_id=%s and request_key=%s",
            (principal.actor_id, principal.session_id, payload["idempotency_key"])).fetchone()
        if existing and existing[1] != payload:
            raise Refusal("CONFLICT")
        if payload["expected_sha256"] is not None and payload["expected_sha256"] != digest:
            raise Refusal("STALE")
        if existing:
            if existing[2] != digest:
                raise Refusal("STALE")  # never replay a formerly true permission
            identifier, _, _, observed = existing
            outcome, event = "ALREADY_RECORDED", "OBSERVATION_REPLAYED"
        else:
            identifier, observed = uuid4(), now
            conn.execute(
                "insert into prumo_i86_lab.observations"
                "(id,actor_id,session_id,request_key,request,state,state_sha256,observed_at,governance_state)"
                " values(%s,%s,%s,%s,%s,%s,%s,%s,'PENDING_DECISION')",
                (identifier, principal.actor_id, principal.session_id,
                 payload["idempotency_key"], Jsonb(payload), Jsonb(state), digest, observed))
            outcome, event = "OBSERVED", "OBSERVED"
        conn.execute("insert into prumo_i86_lab.audit(observation_id,event) values(%s,%s)",
                     (identifier, event))
        return Result(outcome, {"version": VERSION, "observation_id": str(identifier),
                      "state_sha256": digest, "observed_at": observed.isoformat(),
                      "state": state, "governance_state": "PENDING_DECISION",
                      "authority_scope": "ORDINARY_ADMIN_OBSERVED_ONLY",
                      "authorization_token": False})

    def assess(self, authorization, payload):
        try:
            p = command(payload)
        except Exception:
            return Result("INPUT_REJECTED")
        try:
            principal = self._identity.verify(authorization)
            if type(principal) is not Principal or type(principal.actor_id) is not UUID or type(principal.session_id) is not UUID:
                raise Denied()
        except Denied:
            return Result("DENIED")
        except Exception:
            return Result("UNAVAILABLE")
        try:
            with self.connect() as conn:
                result = self.record(conn, principal, p)
            return result
        except Refusal as error:
            return Result(error.state)
        except Exception as error:
            return Result({"55P03": "CONCURRENT_CHANGE", "40001": "STALE",
                           "42501": "DENIED"}.get(getattr(error, "sqlstate", None),
                                                 "UNAVAILABLE"))
