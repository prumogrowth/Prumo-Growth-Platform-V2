"""S1-002/I25: assinador em processo separado, APENAS no CI loopback.

Sem HTTP no assinador, sem servidor de rede ou compartilhamento de chave com o
objeto gateway. DOIS Pipes diferentes: controle de chaves apenas no runner CI,
solicitacoes de assinatura somente no adaptador validado pelo GoTrue.
Nao e barreira contra outro processo do MESMO usuario do sistema que consiga
capturar descritores, nem substitui KMS/HSM ou credenciais OS segregadas.
"""
from __future__ import annotations

import hashlib
import hmac
import multiprocessing
from multiprocessing.connection import wait
import re
import threading
import time
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand, SupabaseGoTrueVerifier
from backend.s1_gateway_local import _fields
from backend.s1_gateway_signed_local import _COMMAND, _action_args, _proof_material, _SQL_SIGNED

_MATERIAL = re.compile(
    rb"prumo-s1-i20-v1\|(MOVER|PAUSAR|REATIVAR)\|"
    rb"[0-9a-f-]{36}\|[0-9a-f-]{36}\|[A-Z0-9a-f|_-]{5,350}"
)
_MAX_MATERIAL = 600


def _worker(operations, control, independent_auth=None):
    """Child has key bytes, never logs material/signatures; no key in return."""
    keys = {}
    # I26: assinador consulta GoTrue e rejeita forja de identidade/sessao.
    verifier = (SupabaseGoTrueVerifier(*independent_auth)
                if independent_auth is not None else None)
    try:
        while True:
            ready = wait([operations, control], timeout=0.5)
            for conn in ready:
                try:
                    request = conn.recv()
                except (EOFError, BrokenPipeError, OSError):
                    return
                if type(request) is not tuple or not request:
                    conn.send(("DENIED", None))
                    continue
                if conn is control:
                    action = request[0]
                    if action == "STOP" and len(request) == 1:
                        control.send(("STOPPED", None))
                        return
                    if action == "LOAD" and len(request) == 3:
                        _, keyid, secret = request
                        if (type(keyid) is uuid.UUID and type(secret) is bytes
                                and len(secret) == 32 and keyid not in keys):
                            keys[keyid] = secret
                            conn.send(("LOADED", None))
                        else:
                            conn.send(("DENIED", None))
                    elif action == "REVOKE" and len(request) == 2:
                        keyid = request[1]
                        if keyid in keys:
                            keys.pop(keyid)
                            conn.send(("REVOKED", None))
                        else:
                            conn.send(("DENIED", None))
                    else:
                        conn.send(("DENIED", None))
                    continue
                if request[0] != "SIGN":
                    conn.send(("DENIED", None))
                    continue
                if verifier is None and len(request) == 3:
                    _, keyid, material = request
                    authorization = None
                elif verifier is not None and len(request) == 4:
                    _, keyid, material, authorization = request
                    if not isinstance(authorization, str):
                        conn.send(("DENIED", None))
                        continue
                else:
                    conn.send(("DENIED", None))
                    continue
                if (type(keyid) is not uuid.UUID or keyid not in keys
                    or type(material) is not bytes or len(material) > _MAX_MATERIAL
                    or not _MATERIAL.fullmatch(material)):
                    conn.send(("DENIED", None))
                    continue
                parts = material.decode("ascii").split("|")
                # Fixed canonical material from existing _proof_material:
                # domain,op,actor,session,shop,case,assignment,target,operator,
                # reason,unix-epoch,nonce; server does NOT verify GoTrue.
                try:
                    if len(parts) != 12 or parts[0] != "prumo-s1-i20-v1":
                        raise ValueError()
                    for part in (parts[2], parts[3], parts[-1]):
                        if str(uuid.UUID(part)) != part:
                            raise ValueError()
                    issued = int(parts[-2])
                    now = int(time.time())
                    if not now - 30 <= issued <= now + 5:
                        raise ValueError()
                    if parts[1] == "MOVER":
                        if (parts[4:8].count("-") or parts[8] != "-"
                                or parts[9] != "-"):
                            raise ValueError()
                    elif parts[1] == "PAUSAR":
                        if (parts[4:8] != ["-"] * 4 or parts[8] == "-"
                                or parts[9] not in
                                ("AUSENCIA_TEMPORARIA", "INDISPONIBILIDADE_OPERACIONAL")):
                            raise ValueError()
                    elif parts[1] == "REATIVAR":
                        if parts[4:8] != ["-"] * 4 or parts[8] == "-" or parts[9] != "-":
                            raise ValueError()
                    else:
                        raise ValueError()
                except (ValueError, TypeError):
                    conn.send(("DENIED", None))
                    continue
                if verifier is not None:
                    try:
                        principal = verifier.verify(authorization)
                    except Denied:
                        conn.send(("DENIED", None))
                        continue
                    except IdentityUnavailable:
                        conn.send(("UNAVAILABLE", None))
                        continue
                    except Exception:
                        conn.send(("UNAVAILABLE", None))
                        continue
                    if (parts[2] != str(principal.actor_id) or
                            parts[3] != str(principal.session_id)):
                        conn.send(("DENIED", None))
                        continue
                conn.send(("SIGNED", hmac.new(keys[keyid], material, hashlib.sha256).hexdigest()))
    finally:
        keys.clear()
        for conn in (operations, control):
            try:
                conn.close()
            except OSError:
                pass


class LocalSignerSupervisor:
    """Runner CI owns control channel; gateway receives ONLY separate client."""

    def __init__(self, *, independent_auth_url=None, publishable_key=None):
        if (independent_auth_url is None) != (publishable_key is None):
            raise ValueError("I26_INDEPENDENT_GOTRUE_REQUIRED")
        if independent_auth_url is not None:
            u = urlsplit(independent_auth_url)
            if (u.scheme != "http" or u.hostname not in
                ("localhost", "127.0.0.1", "::1") or u.username or u.password
                or u.query or u.fragment or u.path.rstrip("/") != ""):
                raise ValueError("I26_ONLY_LOCAL_GOTRUE")
            if not isinstance(publishable_key, str) or not publishable_key:
                raise ValueError("I26_PUBLISHABLE_KEY_REQUIRED")
        independent_auth = ((independent_auth_url, publishable_key)
                            if independent_auth_url is not None else None)
        ctx = multiprocessing.get_context("spawn")
        work_parent, work_child = ctx.Pipe(duplex=True)
        control_parent, control_child = ctx.Pipe(duplex=True)
        self._ops = work_parent
        self._control = control_parent
        self._lock = threading.Lock()
        self._ctl_lock = threading.Lock()
        self._process = ctx.Process(target=_worker, args=(work_child, control_child, independent_auth),
                                    name="s1_i25_local_signer", daemon=True)
        self._process.start()
        work_child.close()
        control_child.close()
        self.client = LocalSignerClient(self._ops, self._lock, self._process,
                                        independent_auth=independent_auth is not None)

    def _change(self, operation, *values):
        if not self._process.is_alive():
            raise IdentityUnavailable("ASSINADOR_INDISPONIVEL")
        with self._ctl_lock:
            try:
                self._control.send((operation, *values))
                if not self._control.poll(3):
                    raise IdentityUnavailable("ASSINADOR_INDISPONIVEL")
                answer, _ = self._control.recv()
                return answer
            except (OSError, EOFError, BrokenPipeError):
                raise IdentityUnavailable("ASSINADOR_INDISPONIVEL") from None

    def load(self, key_id, secret):
        return self._change("LOAD", key_id, secret) == "LOADED"

    def revoke(self, key_id):
        return self._change("REVOKE", key_id) == "REVOKED"

    def terminate(self):
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=3)

    def close(self):
        if self._process.is_alive():
            try:
                self._change("STOP")
            except IdentityUnavailable:
                pass
            self._process.join(timeout=3)
        if self._process.is_alive():
            self.terminate()
        self._ops.close()
        self._control.close()


class LocalSignerClient:
    def __init__(self, pipe, lock, process, *, independent_auth=False):
        self._independent_auth = independent_auth
        self._pipe = pipe
        self._lock = lock
        self._process = process

    def sign(self, key_id, material, authorization=None):
        if not self._process.is_alive():
            raise IdentityUnavailable("ASSINADOR_INDISPONIVEL")
        if self._independent_auth and not isinstance(authorization, str):
            raise Denied("BEARER_ASSINADOR_OBRIGATORIO")
        if not self._independent_auth and authorization is not None:
            raise Denied("PROTOCOLO_NAO_PERMITIDO")
        with self._lock:
            try:
                request = (("SIGN", key_id, material, authorization)
                           if self._independent_auth
                           else ("SIGN", key_id, material))
                self._pipe.send(request)
                # GoTrue usa timeout 5s. Em timeout IPC, matar processo
                # para jamais consumir resposta antiga numa nova assinatura.
                if not self._pipe.poll(8 if self._independent_auth else 3):
                    self._process.terminate()
                    self._process.join(timeout=2)
                    raise IdentityUnavailable("ASSINADOR_TIMEOUT")
                status, signature = self._pipe.recv()
            except (OSError, EOFError, BrokenPipeError):
                raise IdentityUnavailable("ASSINADOR_INDISPONIVEL") from None
        if status == "UNAVAILABLE":
            raise IdentityUnavailable("GOTRUE_ASSINADOR_INDISPONIVEL")
        if status != "SIGNED" or not isinstance(signature, str) or not re.fullmatch(
            r"[0-9a-f]{64}", signature
        ):
            raise Denied("ASSINATURA_NAO_AUTORIZADA")
        return signature


class LocalSeparatedSignerGateway:
    """Gateway CI: GoTrue first, IPC signer second, SQL restricted third.

    Does not have signing_key attribute; supervisor and its control pipe must
    never be stored here or passed to HTTP layer.
    """

    def __init__(self, dsn, gotrue, *, signer, key_id):
        u = urlsplit(dsn)
        if (u.scheme not in ("postgres", "postgresql")
            or u.hostname not in ("127.0.0.1", "localhost", "::1")
            or u.username != "prumo_s1_signed_login_ci"
            or u.path != "/postgres" or u.query or u.fragment):
            raise ValueError("I25_DSN_LOCAL_REQUIRED")
        if type(key_id) is not uuid.UUID or not hasattr(signer, "sign"):
            raise ValueError("I25_SIGNER_REQUIRED")
        self.dsn = dsn
        self.gotrue = gotrue
        self.signer = signer
        self.key_id = key_id

    def proof(self, principal, command, values, *, issued=None, nonce=None):
        op = _COMMAND.get(command)
        if op is None:
            raise InvalidCommand("COMANDO_NAO_PERMITIDO")
        args = _action_args(command, values)
        timestamp = int(time.time()) if issued is None else issued
        unique = uuid.uuid4() if nonce is None else nonce
        material = _proof_material(op, principal.actor_id, principal.session_id,
                                   args, timestamp, unique)
        signature = self.signer.sign(self.key_id, material)
        return (op, principal.actor_id, principal.session_id, *args,
                self.key_id, timestamp, unique, signature)

    def invoke(self, authorization, command, payload):
        import psycopg
        values = _fields(command, payload)
        principal = self.gotrue.verify(authorization)
        proof = self.proof(principal, command, values)
        with psycopg.connect(self.dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(_SQL_SIGNED, proof)
                except psycopg.Error as e:
                    if e.sqlstate in ("42501", "22023", "23514", "23505"):
                        raise Denied("OPERACAO_S1_NAO_AUTORIZADA") from None
                    raise IdentityUnavailable("BANCO_INDISPONIVEL") from None
                row = cursor.fetchone()
                if row is None or not isinstance(row[0], dict):
                    raise IdentityUnavailable("RETORNO_S1_INVALIDO")
                return row[0]
