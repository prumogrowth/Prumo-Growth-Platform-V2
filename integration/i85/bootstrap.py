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
import functools
import re
from urllib import request, error
from uuid import UUID, uuid4
from local_admin import boundary as b, environment as e
from integration.i85 import storage

ROOT = b.DEFAULT.parent / ("prumo-i85-" + str(os.getuid()))
LABELS = frozenset(("director", "manager", "manager2", "consultant", "legacy", "outsider"))
APPROVAL = "AUTHORIZE_SYNTHETIC_DIRECTOR_ONLY_IN_OWNED_DISPOSABLE_LAB"
MAX_HTTP = 65536

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None



def serialized(method):
    @functools.wraps(method)
    def call(self,*args,**kwargs):
        with b.locked():
            if method.__name__ not in ('init','recover_journal','dispose','abandon_after_stack_down'):
                self.load()
            return method(self,*args,**kwargs)
    return call


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
        with request.build_opener(NoRedirect()).open(req, timeout=8) as res:
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
        storage.checked(path)
        remaining=memoryview(data)
        while remaining:
            size=os.write(fd,remaining)
            if size<=0:_blocked("I85_AUDIT_SHORT_WRITE")
            remaining=remaining[size:]
        os.fsync(fd)
    finally:
        os.close(fd)
    storage.sync_dir(directory)


class Bootstrap:
    def __init__(self, directory=ROOT):
        self.dir = Path(directory)
        if self.dir != ROOT or self.dir.is_symlink():
            _blocked("I85_PATH_INVALID")
        self.state_file = self.dir / "state.json"
        self.secret_file = self.dir / "secrets.json"
        self.disposing = self.dir.with_name(self.dir.name+".disposing")
        self.disposed = self.dir.with_name(self.dir.name+".disposed")
        self.state = None
        self._bound = None

    def owned(self):
        if os.environ.get("PRUMO_I84_DISPOSABLE") != "YES" or os.environ.get("PRUMO_I85_DISPOSABLE") != "YES":
            _blocked("I85_OPT_IN_REQUIRED")
        b.private(b.DEFAULT, True)
        state = b.load(b.DEFAULT / "state.json")
        if state["phase"] not in ("PREPARED", "PROVISIONED", "SERVING", "REVOKED"):
            _blocked("I84_STATE_UNSAFE_FOR_BOOTSTRAP")
        e.owned(state)
        if b.inspect(b.EDGE):
            if (state.get('worker') or {}).get('profile')!='I85_RESTRICTED':_blocked('I85_RESTRICTED_RUNTIME_REQUIRED')
            from integration.i85.edge_profile import verify
            verify(state)
        physical=self.binding(state)
        if self._bound is not None and self._bound!=physical:_blocked('I85_STACK_MISMATCH')
        if self.state:
            if any(self.state[k] != state[v] for k,v in (("stack_token","token"),("db_id","db_id"),("engine","engine"),("network_id","network_id"))):
                _blocked("I85_STACK_MISMATCH")
        if self.dir.exists() and (self.dir/'lab.json').exists():
            if storage.read(self.dir/'lab.json')!=self.binding(state):_blocked('I85_BIRTH_BINDING_DIVERGENCE')
        self._bound=physical
        return state

    @staticmethod
    def binding(parent):
        return {'version':2,'stack_token':parent['token'],'db_id':parent['db_id'],
                'engine':parent['engine'],'network_id':parent['network_id'],'project':b.PROJECT,'root':str(b.ROOT)}

    @staticmethod
    def fresh(parent):
        with e.database() as conn:
            if conn.execute('select count(*) from auth.users').fetchone()[0] or conn.execute('select count(*) from prumo_private.s1_responsaveis_plataforma').fetchone()[0]:
                _blocked('I85_REQUIRES_FRESH_SYNTHETIC_LAB')

    @staticmethod
    def validate_state(value):
        try:
            if set(value)!={'version','stack_token','db_id','engine','network_id','identities','approval','approval_pending','authority'}:raise ValueError
            if type(value['version']) is not int or value['version']!=2 or not isinstance(value['identities'],dict):raise ValueError
            for k in ('stack_token','db_id','engine','network_id'):
                if not isinstance(value[k],str) or not value[k]:raise ValueError
            if type(value['approval_pending']) is not bool:raise ValueError
            ids=[]
            for label,item in value['identities'].items():
                if label not in LABELS or set(item)!={'email','uuid','phase'}:raise ValueError
                if not re.fullmatch('prumo-i85-'+label+r'-[a-f0-9]{32}@example\.invalid',item['email']):raise ValueError
                if item['phase'] not in ('CREATE_UNKNOWN','CONFIRMED'):raise ValueError
                if item['uuid'] is not None:ids.append(_ident(item['uuid']))
                if item['phase']=='CONFIRMED' and not item['uuid']:raise ValueError
            if len(ids)!=len(set(ids)):raise ValueError
            authority=value['authority']
            if set(authority)!={'phase','uuid'} or authority['phase'] not in ('NONE','COMMIT_UNKNOWN','ACTIVE','REVOKE_UNKNOWN','REVOKED'):raise ValueError
            approval=value['approval']
            if approval is not None:
                if set(approval)!={'uuid','stack_token','approval_id'}:raise ValueError
                if approval['uuid']!=value['identities']['director']['uuid'] or approval['stack_token']!=value['stack_token']:raise ValueError
                _ident(approval['approval_id'])
            if value['approval_pending'] and (approval is None or authority['phase']!='NONE'):raise ValueError
            if authority['phase']!='NONE':
                if approval is None or authority['uuid']!=approval['uuid']:raise ValueError
            elif authority['uuid'] is not None:raise ValueError
        except (KeyError,TypeError,ValueError):_blocked('I85_STATE_INVALID')

    @staticmethod
    def validate_secrets(values,state):
        if not isinstance(values,dict) or set(values)!=set(state['identities']):_blocked('I85_SECRET_STATE_DIVERGENCE')
        if any(not isinstance(v,str) or not re.fullmatch('[A-Za-z0-9_-]{40,128}',v) for v in values.values()):_blocked('I85_SECRET_STATE_DIVERGENCE')

    def validate_audit(self):
        path=self.dir/'audit.log'
        if not path.exists():_blocked('I85_AUDIT_INCOMPLETE')
        storage.checked(path)
        raw=path.read_bytes()
        if raw and not raw.endswith(b'\n'):_blocked('I85_AUDIT_TORN')
        try:
            for line in raw.splitlines():
                value=json.loads(line)
                if set(value)!={'event','label','phase'} or not re.fullmatch('[A-Z_]{1,64}',value['event']):raise ValueError
                if value['label'] is not None and value['label'] not in LABELS:raise ValueError
        except (ValueError,TypeError):_blocked('I85_AUDIT_INVALID')

    def _checked_status(self):
        phase=self.state['authority']['phase']
        if phase=='ACTIVE':self._confirm_grant(self.state['authority']['uuid'])
        elif phase=='REVOKED':
            rows,team,actor,_=self.authority_view(self.state['authority']['uuid'])
            if rows!=[(self.state['authority']['uuid'],False)] or team!=[('diretor','ativo')] or actor!=1:_blocked('I85_CANONICAL_AUTHORITY_DIVERGENCE')
        elif phase=='NONE':
            with e.database() as conn:
                if conn.execute('select count(*) from prumo_private.s1_responsaveis_plataforma').fetchone()[0]:_blocked('I85_CANONICAL_AUTHORITY_DIVERGENCE')
        return self._status()

    @serialized
    def status(self):return self._checked_status()

    @serialized
    def init(self):
        parent = self.owned()
        if self.dir.exists():
            _blocked("I85_JOURNAL_ALREADY_EXISTS")
        self.fresh(parent)
        if self.disposing.exists():_blocked('I85_DISPOSAL_IN_PROGRESS')
        self.dir.mkdir(mode=0o700)
        storage.sync_dir(self.dir.parent)
        storage.atomic_save(self.dir/'lab.json',self.binding(parent))
        self.state = {"version": 2, "stack_token": parent["token"], "db_id": parent["db_id"],
                      "engine": parent["engine"], "network_id": parent["network_id"],
                      "identities": {}, "approval": None, "approval_pending": False, "authority": {"phase": "NONE", "uuid": None}}
        storage.atomic_save(self.state_file, self.state)
        storage.atomic_save(self.secret_file, {})
        _record(self.dir, "INIT")
        return self._status()

    def load(self):
        b.private(self.dir, True)
        if self.disposing.exists():_blocked('I85_DISPOSAL_IN_PROGRESS')
        if (self.dir/'recovery.json').exists() or (self.dir/'disposal.json').exists() or storage.residues(self.dir):
            _blocked('I85_JOURNAL_RECOVERY_REQUIRED')
        self.state = storage.read(self.state_file)
        self.validate_state(self.state)
        self.validate_secrets(storage.read(self.secret_file),self.state)
        self.validate_audit()
        if (self.dir/'evidence').exists():
            storage.checked(self.dir/'evidence',True)
            for path in (self.dir/'evidence').iterdir():storage.checked(path)
        if any(path.name not in ('state.json','secrets.json','lab.json','audit.log','evidence') for path in self.dir.iterdir()):_blocked('I85_UNKNOWN_CUSTODY_FILE')
        self.owned()
        return self

    def save(self, event, label=None):
        storage.atomic_save(self.state_file, self.state)
        _record(self.dir, event, label, self.state["authority"]["phase"])

    def secrets(self):
        return storage.read(self.secret_file)

    def _status(self):
        return {"version": "prumo.i85.local.v1",
                "identities": {label: item["phase"] for label, item in self.state["identities"].items()},
                "authority": self.state["authority"]["phase"], "approval": self.state["approval"] is not None,
                "approval_pending":self.state["approval_pending"],
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

    @serialized
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
        storage.atomic_save(self.secret_file, values)
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
        return self._status()

    @serialized
    def reconcile_identity(self, label):
        if label not in self.state["identities"]:
            _blocked("IDENTITY_NOT_PREPARED")
        # Never POST again, even when lookup currently returns 404/zero rows.
        identifier = self.verify_auth(label, allow_unknown=True)
        self.state["identities"][label]["uuid"] = identifier
        self.state["identities"][label]["phase"] = "CONFIRMED"
        self.save("AUTH_RECONCILED", label)
        return self._status()

    @serialized
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

    @serialized
    def authorize_director(self):
        if os.environ.get("PRUMO_I85_DIRECTOR_APPROVAL") != APPROVAL:
            _blocked("TRUSTED_INSTALLER_APPROVAL_REQUIRED")
        identifier = self.verify_auth("director")
        if (self.state["approval"] is not None and not self.state["approval_pending"]) or self.state["authority"]["phase"] != "NONE":
            _blocked("BOOTSTRAP_APPROVAL_ALREADY_ISSUED")
        # Approval is bound to this owned physical disposable stack and one
        # verified UUID; neither JWT nor client metadata can issue it.
        self.state["approval"] = {"uuid": identifier, "stack_token": self.state["stack_token"],
                                   "approval_id": (self.state["approval"] or {}).get("approval_id",str(uuid4()))}
        self.state["approval_pending"]=False
        self.save("TECHNICAL_APPROVAL_RECORDED", "director")
        return self._status()

    def authority_view(self, identifier):
        with e.database() as conn:
            all_rows = conn.execute("select ator_id::text,ativo from prumo_private.s1_responsaveis_plataforma").fetchall()
            team = conn.execute("select cargo,estado from public.equipe_prumo_s1 where ator_id=%s",
                                (identifier,)).fetchall()
            actor = conn.execute("select 1 from public.atores where id=%s", (identifier,)).fetchall()
            sessions = conn.execute("select count(*) from auth.sessions where user_id=%s",
                                    (identifier,)).fetchone()[0]
        return all_rows, team, len(actor), sessions

    @serialized
    def grant_director(self):
        identifier = self.verify_auth("director")
        approval = self.state["approval"]
        if self.state["approval_pending"] or not approval or approval["uuid"] != identifier or approval["stack_token"] != self.state["stack_token"]:
            _blocked("BOOTSTRAP_AUTHORIZATION_MISSING")
        if self.state["authority"]["phase"] != "NONE":
            _blocked("BOOTSTRAP_MUST_RECONCILE_OR_IS_FINAL")
        self.state["authority"] = {"phase": "COMMIT_UNKNOWN", "uuid": identifier}
        self.save("DIRECTOR_COMMIT_ATTEMPT", "director")
        try:
            self._grant_transaction(identifier,self.state["identities"]["director"]["email"])
            self._confirm_grant(identifier)
        except Exception:
            self.save("DIRECTOR_RESULT_UNCERTAIN", "director")
            raise
        self.state["authority"]["phase"] = "ACTIVE"
        self.save("DIRECTOR_BOOTSTRAP_CONFIRMED", "director")
        return self._status()

    def _grant_transaction(self,identifier,email):
        with e.database() as conn:
            conn.execute("set local lock_timeout = '5s'")
            conn.execute("lock table public.atores, public.equipe_prumo_s1, prumo_private.s1_responsaveis_plataforma in share row exclusive mode")
            if not conn.execute("select 1 from auth.users where id=%s and email=%s for share",
                                (identifier, email)).fetchone():
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

    def _confirm_grant(self, identifier):
        rows, team, actor, _ = self.authority_view(identifier)
        if rows != [(identifier, True)] or team != [("diretor", "ativo")] or actor != 1:
            _blocked("DIRECTOR_AUTHORITY_NOT_PROVEN")

    @serialized
    def revoke_director(self):
        auth = self.state["authority"]
        if auth["phase"] not in ("ACTIVE","REVOKE_UNKNOWN","REVOKED"):
            _blocked("DIRECTOR_REVOCATION_REQUIRES_ACTIVE_PROOF")
        identifier = self.verify_auth("director")
        if auth["uuid"] != identifier:
            _blocked("DIRECTOR_REVOKE_IDENTITY_DIVERGENCE")
        auth["phase"] = "REVOKE_UNKNOWN"
        self.save("DIRECTOR_REVOCATION_ATTEMPT", "director")
        try:
            with e.database() as conn:
                conn.execute("set local lock_timeout = '5s'")
                conn.execute("lock table auth.sessions in share row exclusive mode")
                conn.execute("select id from auth.sessions where user_id=%s order by id for update",(identifier,))
                conn.execute("select id from public.atores where id=%s for no key update",(identifier,))
                conn.execute("select ator_id from public.equipe_prumo_s1 where ator_id=%s for update",(identifier,))
                conn.execute("select ator_id from prumo_private.s1_responsaveis_plataforma where ator_id=%s for update", (identifier,))
                conn.execute("update prumo_private.s1_responsaveis_plataforma set ativo=false where ator_id=%s and ativo", (identifier,))
                conn.execute("delete from auth.sessions where user_id=%s", (identifier,))
            self._confirm_revocation(identifier)
        except Exception:
            self.save("DIRECTOR_REVOCATION_UNKNOWN", "director")
            raise
        auth["phase"] = "REVOKED"
        self.save("DIRECTOR_REVOCATION_CONFIRMED", "director")
        return self._status()

    def _confirm_revocation(self, identifier):
        rows, team, actor, sessions = self.authority_view(identifier)
        if rows != [(identifier, False)] or team != [("diretor", "ativo")] or actor != 1 or sessions:
            _blocked("DIRECTOR_REVOCATION_NOT_PROVEN")

    @serialized
    def reconcile_authority(self):
        phase = self.state["authority"]["phase"]
        if self.state["approval_pending"] or self.state["approval"] is None:_blocked("BOOTSTRAP_AUTHORIZATION_MISSING")
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
        return self._status()


    @serialized
    def recover_journal(self):
        """Explicit recovery retains exact evidence and never repeats Auth/SQL."""
        storage.checked(self.dir,True)
        parent=self.owned();binding=self.binding(parent)
        marker=self.dir/'recovery.json'
        if marker.exists():
            plan=storage.read(marker)
            if plan.get('binding')!=binding:_blocked('I85_RECOVERY_BINDING_INVALID')
        else:
            paths=[p for p in self.dir.iterdir() if p.is_file() or p.is_symlink()]
            if any(p.name not in ('state.json','secrets.json','lab.json','audit.log') and not p.name.endswith('.next') for p in paths):_blocked('I85_RECOVERY_UNKNOWN_FILE')
            snapshots=storage.archive(self.dir,paths)
            plan={'binding':binding,'snapshots':snapshots}
            storage.atomic_save(marker,plan)
        images={}
        for name,item in plan['snapshots'].items():
            path=self.dir/'evidence'/item['file'];storage.checked(path)
            raw=path.read_bytes()
            if b.digest(raw)!=item['sha256']:_blocked('I85_RECOVERY_EVIDENCE_CHANGED')
            images[name]=raw
        def decode(raw):
            try:return storage.decode(raw)
            except b.Blocked:_blocked('I85_TORN_JOURNAL_REQUIRES_LAB_DISCARD')
        state=decode(images['state.json']) if 'state.json' in images else None
        if state is None:
            # Interrupted init has no Auth/authority operation before completion.
            self.fresh(parent)
            state={'version':2,'stack_token':parent['token'],'db_id':parent['db_id'],
              'engine':parent['engine'],'network_id':parent['network_id'],'identities':{},
              'approval':None,'approval_pending':False,'authority':{'phase':'NONE','uuid':None}}
        self.validate_state(state)
        if any(state[k]!=binding[k] for k in ('stack_token','db_id','engine','network_id')):_blocked('I85_STACK_MISMATCH')
        candidates={kind:[] for kind in ('state.json','secrets.json','lab.json')}
        for name,raw in images.items():
            if name.endswith('.next'):
                kind=next((k for k in candidates if name==k+'.next' or name.startswith('.'+k+'.')),None)
                if not kind:_blocked('I85_RECOVERY_PLAN_TORN_REQUIRES_REVIEW')
                candidates[kind].append(decode(raw))
        if any(len(v)>1 for v in candidates.values()):_blocked('I85_MULTIPLE_WRITES_REQUIRE_REVIEW')
        for lab in ([decode(images['lab.json'])] if 'lab.json' in images else [])+candidates['lab.json']:
            if lab!=binding:_blocked('I85_BIRTH_BINDING_DIVERGENCE')
        for pending in candidates['state.json']:
            self.validate_state(pending)
            if any(pending[k]!=state[k] for k in ('stack_token','db_id','engine','network_id')):_blocked('I85_STACK_MISMATCH')
            if not set(state['identities'])<=set(pending['identities']):_blocked('I85_NON_MONOTONIC_JOURNAL')
            for label,item in pending['identities'].items():
                previous=state['identities'].get(label)
                if previous:
                    if previous['email']!=item['email'] or (previous['uuid'] and previous['uuid']!=item['uuid']):_blocked('AUTH_UUID_DIVERGENCE')
                    if previous['phase']=='CONFIRMED' and item!=previous:_blocked('I85_NON_MONOTONIC_JOURNAL')
                    # Confirmations are not silently promoted from staged bytes.
                else:
                    if item['phase']!='CREATE_UNKNOWN':_blocked('I85_NON_MONOTONIC_JOURNAL')
                    state['identities'][label]=item
            if state['approval'] is None and pending['approval'] is not None:
                state['approval']=pending['approval'];state['approval_pending']=True
            elif state['approval']!=pending['approval']:_blocked('I85_APPROVAL_DIVERGENCE')
            old=state['authority']['phase'];new=pending['authority']['phase']
            if (old,new) in (('NONE','COMMIT_UNKNOWN'),('ACTIVE','REVOKE_UNKNOWN')):
                state['authority']=pending['authority']
            elif old==new or (old,new) in (('COMMIT_UNKNOWN','ACTIVE'),('REVOKE_UNKNOWN','REVOKED')):pass
            else:_blocked('I85_NON_MONOTONIC_JOURNAL')
        values=decode(images.get('secrets.json',b'{}'))
        for pending in candidates['secrets.json']:
            if any(pending.get(k)!=v for k,v in values.items()):_blocked('I85_SECRET_STATE_DIVERGENCE')
            values=pending
        self.validate_state(state);self.validate_secrets(values,state)
        # No residual is removed before the exact source bytes are retained.
        extra=storage.residues(self.dir)
        if extra:storage.archive(self.dir,extra)
        for path in extra:path.unlink()
        storage.atomic_save(self.dir/'lab.json',binding)
        storage.atomic_save(self.secret_file,values)
        storage.atomic_save(self.state_file,state)
        raw=images.get('audit.log',b'')
        complete=raw if raw.endswith(b'\n') else raw[:raw.rfind(b'\n')+1]
        storage.atomic_bytes(self.dir/'audit.log',complete)
        self.state=state
        _record(self.dir,'JOURNAL_RECOVERY_RECORDED',phase=state['authority']['phase'])
        self.validate_audit();self.owned();self._checked_status()
        destination=self.dir/'evidence'/(uuid4().hex+'-recovery-complete.json')
        os.replace(marker,destination);storage.sync_dir(self.dir);storage.sync_dir(destination.parent)
        return self._status()

    def _disposal_proof(self,state):
        phase=state['authority']['phase']
        if phase not in ('NONE','REVOKED'):_blocked('I85_AUTHORITY_MUST_BE_REVOKED_BEFORE_DISCARD')
        if any(i['phase']!='CONFIRMED' for i in state['identities'].values()):_blocked('I85_UNCERTAIN_AUTH_RETAIN_FOR_REVIEW')
        with e.database() as conn:
            rows=conn.execute('select ator_id::text,ativo from prumo_private.s1_responsaveis_plataforma').fetchall()
        if phase=='NONE':
            if rows:_blocked('I85_CANONICAL_AUTHORITY_DIVERGENCE')
        else:
            self._confirm_revocation(state['authority']['uuid'])
        return {'version':2,'binding':{k:state[k] for k in ('stack_token','db_id','engine','network_id')},
                'authority':state['authority'],'identities':state['identities']}

    @serialized
    def dispose(self):
        if self.disposing.exists():
            storage.checked(self.disposing,True)
            proof=storage.read(self.disposing/'disposal.json')
            self.state={**proof['binding'],'authority':proof['authority'],'identities':proof['identities']}
            self.owned();self._disposal_proof(self.state)
        elif (self.dir/'disposal.json').exists():
            storage.checked(self.dir,True);proof=storage.read(self.dir/'disposal.json')
            self.state={**proof['binding'],'authority':proof['authority'],'identities':proof['identities']}
            self.owned();self._disposal_proof(self.state)
            os.rename(self.dir,self.disposing);storage.sync_dir(self.dir.parent)
        elif self.disposed.exists() and not self.dir.exists():
            storage.checked(self.disposed,True)
            proof=storage.read(self.disposed/'proof.json')
            if not proof.get('private_material_removed'):_blocked('I85_DISPOSAL_UNPROVEN')
            if any(p.name not in ('proof.json','disposal.json') for p in self.disposed.iterdir()):_blocked('I85_DISPOSAL_UNPROVEN')
            (self.disposed/'disposal.json').unlink(missing_ok=True);storage.sync_dir(self.disposed)
            return {'version':'prumo.i85.local.v1','private_material_removed':True,'audit_archived':False,'forensic_erasure_claimed':False}
        else:
            # A durable intent allows safe continuation even after some files
            # were unlinked. Unknown journals are never erased by ordinary dispose.
            self.load();proof=self._disposal_proof(self.state)
            storage.atomic_save(self.dir/'disposal.json',proof)
            _record(self.dir,'DISPOSE_INTENT',phase=self.state['authority']['phase'])
            os.rename(self.dir,self.disposing);storage.sync_dir(self.dir.parent)
        for path in list(self.disposing.iterdir()):
            if path.name=='disposal.json':continue
            if path.is_dir() and path.name=='evidence':storage.remove_private_tree(path)
            else:
                if path.name not in ('secrets.json','state.json','lab.json','audit.log','recovery.json','proof.json') and not path.name.endswith('.next'):_blocked('I85_UNKNOWN_CUSTODY_FILE')
                storage.checked(path);path.unlink();storage.sync_dir(self.disposing)
        # A nonsecret tombstone is retained; no secret/current journal remains.
        storage.atomic_save(self.disposing/'proof.json',{'version':2,'binding':proof['binding'],
          'private_material_removed':True,'authority_inactive_verified':True})
        if self.disposed.exists():storage.remove_private_tree(self.disposed)
        os.rename(self.disposing,self.disposed);storage.sync_dir(self.dir.parent)
        (self.disposed/'disposal.json').unlink();storage.sync_dir(self.disposed)
        return {'version':'prumo.i85.local.v1','private_material_removed':True,
                'audit_archived':False,'forensic_erasure_claimed':False}

    @serialized
    def abandon_after_stack_down(self):
        """Explicit lab retirement only; retains uncertain nonsecret evidence."""
        if os.environ.get('PRUMO_I85_ABANDON')!='PRESERVE_EVIDENCE_AFTER_VERIFIED_LAB_DISCARD':_blocked('I85_ABANDON_EXPLICIT_OPT_IN_REQUIRED')
        from local_admin.operation import resources
        parent=b.load(b.DEFAULT/'state.json')
        if parent.get('phase')!='DISCARDED' or parent.get('engine')!=e.engine() or any(resources().values()):_blocked('I85_LAB_DISCARD_UNPROVEN')
        directory=self.disposing if self.disposing.exists() else self.dir
        storage.checked(directory,True)
        binding=storage.read(directory/'lab.json') if (directory/'lab.json').exists() else storage.read(directory/'disposal.json')['binding']
        if any(binding[k]!=parent[v] for k,v in (('stack_token','token'),('db_id','db_id'),('engine','engine'),('network_id','network_id'))):_blocked('I85_STACK_MISMATCH')
        # Private evidence remains intentionally. Password snapshots are removed
        # by filename class only; no export or interpretation of their values.
        files=list(directory.iterdir())
        evidence=directory/'evidence'
        if evidence.exists():
            storage.checked(evidence,True);files+=list(evidence.iterdir())
        for path in files:
            if path.is_file() or path.is_symlink():
                storage.checked(path)
                if 'secrets.json' in path.name:path.unlink()
        storage.atomic_save(directory/'abandoned.json',{'version':2,'binding':binding,
          'lab_resources_absent':True,'password_material_removed':True,'uncertain_evidence_retained':True})
        destination=self.dir.with_name(self.dir.name+'.abandoned-'+uuid4().hex)
        os.rename(directory,destination);storage.sync_dir(destination.parent)
        return {'version':'prumo.i85.local.v1','password_material_removed':True,
                'uncertain_evidence_retained':True,'lab_resources_absent':True}
