"""I85: private, disposable GoTrue identity bootstrap and Director authority.

Not an Edge endpoint, not a frontend API, and not a hosted migration.
The local Docker/Postgres operator is the trusted installation principal.
Nothing in Auth metadata, JWT claims or a browser approves Director authority.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
from urllib import request, error
from uuid import UUID, uuid4
from local_admin import boundary as b, environment as e

ROOT = b.DEFAULT.parent / ("prumo-i85-" + str(os.getuid()))
LABELS = frozenset(("director", "manager", "manager2", "consultant", "legacy", "outsider"))
APPROVAL = "AUTHORIZE_SYNTHETIC_DIRECTOR_ONLY_IN_OWNED_DISPOSABLE_LAB"
MAX_HTTP = 65536


def _blocked(code):
    raise b.Blocked(code)


def _ident(value):
    try:
        parsed = UUID(str(value))
        if parsed.version != 4 or str(parsed) != value:
            _blocked("AUTH_UUID_INVALID")
        return str(parsed)
    except (TypeError, ValueError, AttributeError):
        _blocked("AUTH_UUID_INVALID")


def _key():
    # The service_role key belongs ONLY to the trusted technical host.
    # Neither the restricted I83 login nor the Edge worker receives it.
    data = b.run(["supabase", "status", "--output", "env"]).decode()
    items = {}
    for line in data.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            items[k.strip()] = v.strip().strip('"').strip("'")
    if not items.get("SERVICE_ROLE_KEY"):
        _blocked("LOCAL_GOTRUE_ADMIN_KEY_UNAVAILABLE")
    return items["SERVICE_ROLE_KEY"]


def _api(method, path, data=None, admin=True, token=None):
    env = e.discover()
    if not path.startswith("/auth/v1/") or "://" in path or ".." in path:
        _blocked("AUTH_PATH_INVALID")
    key = _key() if admin else env["ANON_KEY"]
    headers = {"apikey": key, "Content-Type": "application/json",
               "Authorization": "Bearer " + (key if admin else token or "")}
    body = None if data is None else json.dumps(data, separators=(",", ":")).encode()
    url = env["API_URL"] + path
    try:
        req = request.Request(url, data=body, headers=headers, method=method)
        with request.urlopen(req, timeout=8) as res:
            raw = res.read(MAX_HTTP + 1)
            if res.status not in (200, 201) or len(raw) > MAX_HTTP:
                _blocked("GOTRUE_RESPONSE_INVALID")
            return json.loads(raw)
    except (error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        _blocked("GOTRUE_RESULT_UNKNOWN")


def _record(directory, action, label=None, phase=None):
    # Local installer-only audit, append-only by this program, no tokens,
    # passwords, service keys, HTTP bodies, emails or SQL parameters.
    path = directory / "audit.log"
    data = json.dumps({"event": action, "label": label, "phase": phase},
                      sort_keys=True, separators=(",", ":")).encode() + b"\n"
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(path, flags, 0o600)
    try:
        b.private(path)
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


class Bootstrap:
    def __init__(self, directory=ROOT):
        self.dir = Path(directory)
        if self.dir != ROOT or self.dir.is_symlink():
            _blocked("I85_PATH_INVALID")
        self.state_file = self.dir / "state.json"
        self.secret_file = self.dir / "secrets.json"
        self.state = None

    def owned(self):
        if os.environ.get("PRUMO_I84_DISPOSABLE") != "YES" or os.environ.get("PRUMO_I85_DISPOSABLE") != "YES":
            _blocked("I85_OPT_IN_REQUIRED")
        b.private(b.DEFAULT, True)
        state = b.load(b.DEFAULT / "state.json")
        if state["phase"] not in ("PREPARED", "PROVISIONED", "SERVING", "REVOKED"):
            _blocked("I84_STATE_UNSAFE_FOR_BOOTSTRAP")
        e.owned(state)
        if self.state:
            if self.state["stack_token"] != state["token"] or self.state["db_id"] != state["db_id"]:
                _blocked("I85_STACK_MISMATCH")
        return state

    def init(self):
        parent = self.owned()
        if self.dir.exists():
            _blocked("I85_JOURNAL_ALREADY_EXISTS")
        self.dir.mkdir(mode=0o700)
        self.state = {"version": 1, "stack_token": parent["token"], "db_id": parent["db_id"],
                      "identities": {}, "approval": None, "authority": {"phase": "NONE", "uuid": None}}
        b.save(self.state_file, self.state)
        b.save(self.secret_file, {})
        _record(self.dir, "INIT")
        return self.status()

    def load(self):
        b.private(self.dir, True)
        self.state = b.load(self.state_file)
        if self.state.get("version") != 1 or not isinstance(self.state.get("identities"), dict):
            _blocked("I85_STATE_INVALID")
        b.private(self.secret_file)
        self.owned()
        return self

    def save(self, event, label=None):
        b.save(self.state_file, self.state)
        _record(self.dir, event, label)

    def secrets(self):
        return b.load(self.secret_file)

    def status(self):
        return {"version": "prumo.i85.local.v1",
                "identities": {label: item["phase"] for label, item in self.state["identities"].items()},
                "authority": self.state["authority"]["phase"], "approval": self.state["approval"] is not None,
                "hosted_enabled": False}

    def auth_row(self, email):
        with e.database() as conn:
            rows = conn.execute("select id::text,email from auth.users where lower(email)=lower(%s)",
                                (email,)).fetchall()
        if len(rows) > 1:
            _blocked("AUTH_EMAIL_DIVERGENCE")
        return rows[0] if rows else None

    def verify_auth(self, label, allow_unknown=False):
        item = self.state["identities"].get(label)
        if not item:
            _blocked("IDENTITY_NOT_PREPARED")
        row = self.auth_row(item["email"])
        if not row or row[1] != item["email"]:
            _blocked("AUTH_EXISTENCE_UNPROVEN")
        identifier = _ident(row[0])
        if item.get("uuid") and item["uuid"] != identifier:
            _blocked("AUTH_UUID_DIVERGENCE")
        if not allow_unknown and item["phase"] != "CONFIRMED":
            _blocked("AUTH_RECONCILIATION_REQUIRED")
        result = _api("GET", "/auth/v1/admin/users/" + identifier)
        user = result.get("user", result) if isinstance(result, dict) else {}
        if user.get("id") != identifier or user.get("email") != item["email"]:
            _blocked("AUTH_ADMIN_VIEW_DIVERGENCE")
        return identifier

    def create(self, label):
        if label not in LABELS:
            _blocked("IDENTITY_LABEL_INVALID")
        if label in self.state["identities"]:
            _blocked("IDENTITY_CREATION_NOT_REPEATABLE")
        if self.state["authority"]["phase"] != "NONE":
            _blocked("IDENTITY_BATCH_CLOSED")
        email = "prumo-i85-" + label + "-" + uuid4().hex + "@example.invalid"
        password = secrets.token_urlsafe(42)
        values = self.secrets()
        values[label] = password
        b.save(self.secret_file, values)
        self.state["identities"][label] = {"email": email, "uuid": None, "phase": "CREATE_UNKNOWN"}
        self.save("AUTH_CREATE_ATTEMPT", label)
        # A lost response MUST NOT generate a second request. Only reconcile().
        try:
            result = _api("POST", "/auth/v1/admin/users",
                          {"email": email, "password": password, "email_confirm": True})
            user = result.get("user", result)
            identifier = _ident(user["id"])
            if user.get("email") != email:
                _blocked("AUTH_ADMIN_VIEW_DIVERGENCE")
            self.state["identities"][label]["uuid"] = identifier
            self.verify_auth(label, allow_unknown=True)
        except Exception:
            self.save("AUTH_CREATE_UNKNOWN", label)
            raise
        self.state["identities"][label]["phase"] = "CONFIRMED"
        self.save("AUTH_CREATE_CONFIRMED", label)
        return self.status()

    def reconcile_identity(self, label):
        if label not in self.state["identities"]:
            _blocked("IDENTITY_NOT_PREPARED")
        # Never POST again, even when lookup currently returns 404/zero rows.
        identifier = self.verify_auth(label, allow_unknown=True)
        self.state["identities"][label]["uuid"] = identifier
        self.state["identities"][label]["phase"] = "CONFIRMED"
        self.save("AUTH_RECONCILED", label)
        return self.status()

    def token(self, label):
        identifier = self.verify_auth(label)
        item = self.state["identities"][label]
        response = _api("POST", "/auth/v1/token?grant_type=password",
                        {"email": item["email"], "password": self.secrets()[label]},
                        admin=False, token=e.discover()["ANON_KEY"])
        token = response.get("access_token")
        if not isinstance(token, str) or len(token) < 30:
            _blocked("AUTH_LOGIN_FAILED")
        who = _api("GET", "/auth/v1/user", admin=False, token=token)
        if who.get("id") != identifier:
            _blocked("AUTH_LOGIN_SUB_MISMATCH")
        return token

    def authorize_director(self):
        if os.environ.get("PRUMO_I85_DIRECTOR_APPROVAL") != APPROVAL:
            _blocked("TRUSTED_INSTALLER_APPROVAL_REQUIRED")
        identifier = self.verify_auth("director")
        if self.state["approval"] is not None or self.state["authority"]["phase"] != "NONE":
            _blocked("BOOTSTRAP_APPROVAL_ALREADY_ISSUED")
        # Approval is bound to this owned physical disposable stack and one
        # verified UUID; neither JWT nor client metadata can issue it.
        self.state["approval"] = {"uuid": identifier, "stack_token": self.state["stack_token"],
                                   "approval_id": str(uuid4())}
        self.save("TECHNICAL_APPROVAL_RECORDED", "director")
        return self.status()

    def authority_view(self, identifier):
        with e.database() as conn:
            all_rows = conn.execute("select ator_id::text,ativo from prumo_private.s1_responsaveis_plataforma").fetchall()
            team = conn.execute("select cargo,estado from public.equipe_prumo_s1 where ator_id=%s",
                                (identifier,)).fetchall()
            actor = conn.execute("select 1 from public.atores where id=%s", (identifier,)).fetchall()
            sessions = conn.execute("select count(*) from auth.sessions where user_id=%s",
                                    (identifier,)).fetchone()[0]
        return all_rows, team, len(actor), sessions

    def grant_director(self):
        identifier = self.verify_auth("director")
        approval = self.state["approval"]
        if not approval or approval["uuid"] != identifier or approval["stack_token"] != self.state["stack_token"]:
            _blocked("BOOTSTRAP_AUTHORIZATION_MISSING")
        if self.state["authority"]["phase"] != "NONE":
            _blocked("BOOTSTRAP_MUST_RECONCILE_OR_IS_FINAL")
        self.state["authority"] = {"phase": "COMMIT_UNKNOWN", "uuid": identifier}
        self.save("DIRECTOR_COMMIT_ATTEMPT", "director")
        try:
            with e.database() as conn:
                conn.execute("set local lock_timeout = '5s'")
                conn.execute("lock table public.atores, public.equipe_prumo_s1, prumo_private.s1_responsaveis_plataforma in share row exclusive mode")
                if not conn.execute("select 1 from auth.users where id=%s and email=%s for share",
                                    (identifier, self.state["identities"]["director"]["email"])).fetchone():
                    _blocked("BOOTSTRAP_AUTH_DIVERGENCE")
                if conn.execute("select count(*) from prumo_private.s1_responsaveis_plataforma").fetchone()[0]:
                    _blocked("EXISTING_DIRECTOR_AUTHORITY_REQUIRES_REVIEW")
                if conn.execute("select count(*) from public.equipe_prumo_s1 where cargo='diretor'").fetchone()[0]:
                    _blocked("EXISTING_DIRECTOR_CLASSIFICATION")
                if conn.execute("select 1 from public.atores where id=%s", (identifier,)).fetchone():
                    _blocked("BOOTSTRAP_ACTOR_ALREADY_BOUND")
                if conn.execute("select 1 from public.equipe_prumo_s1 where ator_id=%s", (identifier,)).fetchone():
                    _blocked("BOOTSTRAP_TEAM_ALREADY_BOUND")
                conn.execute("insert into public.atores(id) values(%s)", (identifier,))
                conn.execute("insert into prumo_private.s1_responsaveis_plataforma(ator_id) values(%s)", (identifier,))
                conn.execute("insert into public.equipe_prumo_s1(ator_id,cargo,estado) values(%s,'diretor','ativo')", (identifier,))
            self._confirm_grant(identifier)
        except Exception:
            self.save("DIRECTOR_RESULT_UNCERTAIN", "director")
            raise
        self.state["authority"]["phase"] = "ACTIVE"
        self.save("DIRECTOR_BOOTSTRAP_CONFIRMED", "director")
        return self.status()

    def _confirm_grant(self, identifier):
        rows, team, actor, _ = self.authority_view(identifier)
        if rows != [(identifier, True)] or team != [("diretor", "ativo")] or actor != 1:
            _blocked("DIRECTOR_AUTHORITY_NOT_PROVEN")

    def revoke_director(self):
        auth = self.state["authority"]
        if auth["phase"] != "ACTIVE":
            _blocked("DIRECTOR_REVOCATION_REQUIRES_ACTIVE_PROOF")
        identifier = self.verify_auth("director")
        if auth["uuid"] != identifier:
            _blocked("DIRECTOR_REVOKE_IDENTITY_DIVERGENCE")
        auth["phase"] = "REVOKE_UNKNOWN"
        self.save("DIRECTOR_REVOCATION_ATTEMPT", "director")
        try:
            with e.database() as conn:
                conn.execute("set local lock_timeout = '5s'")
                conn.execute("select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for update", (identifier,))
                conn.execute("update prumo_private.s1_responsaveis_plataforma set ativo=false where ator_id=%s and ativo", (identifier,))
                conn.execute("delete from auth.sessions where user_id=%s", (identifier,))
            self._confirm_revocation(identifier)
        except Exception:
            self.save("DIRECTOR_REVOCATION_UNKNOWN", "director")
            raise
        auth["phase"] = "REVOKED"
        self.save("DIRECTOR_REVOCATION_CONFIRMED", "director")
        return self.status()

    def _confirm_revocation(self, identifier):
        rows, team, actor, sessions = self.authority_view(identifier)
        if rows != [(identifier, False)] or team != [("diretor", "ativo")] or actor != 1 or sessions:
            _blocked("DIRECTOR_REVOCATION_NOT_PROVEN")

    def reconcile_authority(self):
        phase = self.state["authority"]["phase"]
        identifier = self.verify_auth("director")
        if self.state["authority"]["uuid"] != identifier:
            _blocked("DIRECTOR_RECONCILE_UUID_DIVERGENCE")
        if phase == "COMMIT_UNKNOWN":
            self._confirm_grant(identifier)
            self.state["authority"]["phase"] = "ACTIVE"
            self.save("DIRECTOR_COMMIT_RECONCILED", "director")
        elif phase == "REVOKE_UNKNOWN":
            self._confirm_revocation(identifier)
            self.state["authority"]["phase"] = "REVOKED"
            self.save("DIRECTOR_REVOKE_RECONCILED", "director")
        else:
            _blocked("DIRECTOR_NO_UNCERTAIN_ACTION")
        return self.status()

    def dispose(self):
        # Do not delete uncertain proof: retain state for explicit intervention.
        if self.state["authority"]["phase"] not in ("NONE", "REVOKED"):
            _blocked("I85_AUTHORITY_MUST_BE_REVOKED_BEFORE_DISCARD")
        if any(i["phase"] == "CREATE_UNKNOWN" for i in self.state["identities"].values()):
            _blocked("I85_UNCERTAIN_AUTH_RETAIN_FOR_REVIEW")
        _record(self.dir, "DISPOSE")
        for name in ("secrets.json", "state.json", "audit.log"):
            path = self.dir / name
            b.private(path)
            path.unlink()
        self.dir.rmdir()
        return {"version": "prumo.i85.local.v1", "private_material_removed": True,
                "audit_archived": False, "forensic_erasure_claimed": False}
