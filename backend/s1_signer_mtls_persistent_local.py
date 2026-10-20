"""S1-002/I28 - signer mTLS rotativo em CI em loopback com TLS mutuo e pin de client cert.

Laboratorio CI somente. Um certificado distinto do gateway eh necessario, e
o assinador valida GoTrue independentemente (I26) ANTES de gerar o HMAC.
Chaves HMAC ficam so no processo-filho; canal de administracao continua pipe
privada do runner. Certificados/CA estao sob a MESMA conta OS no teste.
NAO oferece seguranca operacional multi-host, TLS da borda externa ou KMS.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import multiprocessing
import re
import socket
import ssl
import struct
import threading
import time
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, SupabaseGoTrueVerifier
from backend.s1_signer_process_local import _MATERIAL, _MAX_MATERIAL
from backend.s1_i29_persistent_certificate_store import LocalCertificateState, RevocationStateUnavailable

_MAX_FRAME = 12000


def _send_frame(conn, obj):
    data = json.dumps(obj, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(data) > _MAX_FRAME:
        raise ValueError("I27_FRAME_TOO_LARGE")
    conn.sendall(struct.pack("!I", len(data)) + data)


def _read_exact(conn, count):
    parts = []
    while count:
        data = conn.recv(count)
        if not data:
            raise OSError("I27_TRUNCATED_FRAME")
        parts.append(data)
        count -= len(data)
    return b"".join(parts)


def _read_frame(conn):
    length = struct.unpack("!I", _read_exact(conn, 4))[0]
    if not 2 <= length <= _MAX_FRAME:
        raise ValueError("I27_FRAME_SIZE")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("I27_DUPLICATE_KEY")
            result[key] = value
        return result
    payload = json.loads(_read_exact(conn, length), object_pairs_hook=unique)
    if type(payload) is not dict:
        raise ValueError("I27_OBJECT_REQUIRED")
    return payload


def _sign_with_verified_identity(payload, keys, verifier):
    try:
        if set(payload) != {"action", "key_id", "material", "authorization"}:
            return {"status": "DENIED"}
        if payload["action"] != "SIGN" or not isinstance(payload["key_id"], str):
            return {"status": "DENIED"}
        key_id = uuid.UUID(payload["key_id"])
        if str(key_id) != payload["key_id"] or key_id not in keys:
            return {"status": "DENIED"}
        encoded = payload["material"]
        authorization = payload["authorization"]
        if (not isinstance(encoded, str) or len(encoded) > 900
                or not isinstance(authorization, str)):
            return {"status": "DENIED"}
        material = base64.b64decode(encoded, validate=True)
        if (len(material) > _MAX_MATERIAL or
                not _MATERIAL.fullmatch(material)):
            return {"status": "DENIED"}
        parts = material.decode("ascii").split("|")
        if len(parts) != 12 or parts[0] != "prumo-s1-i20-v1":
            return {"status": "DENIED"}
        for part in (parts[2], parts[3], parts[-1]):
            if str(uuid.UUID(part)) != part:
                return {"status": "DENIED"}
        now = int(time.time())
        issued = int(parts[-2])
        if not now - 30 <= issued <= now + 5:
            return {"status": "DENIED"}
        if parts[1] == "MOVER":
            if (parts[4:8].count("-") or
                    parts[8] != "-" or parts[9] != "-"):
                return {"status": "DENIED"}
            for part in parts[4:8]:
                if str(uuid.UUID(part)) != part:
                    return {"status": "DENIED"}
        elif parts[1] == "PAUSAR":
            if (parts[4:8] != ["-"] * 4
                    or str(uuid.UUID(parts[8])) != parts[8]
                    or parts[9] not in
                    ("AUSENCIA_TEMPORARIA", "INDISPONIBILIDADE_OPERACIONAL")):
                return {"status": "DENIED"}
        elif parts[1] == "REATIVAR":
            if (parts[4:8] != ["-"] * 4
                    or str(uuid.UUID(parts[8])) != parts[8]
                    or parts[9] != "-"):
                return {"status": "DENIED"}
        else:
            return {"status": "DENIED"}
        try:
            principal = verifier.verify(authorization)
        except Denied:
            return {"status": "DENIED"}
        except IdentityUnavailable:
            return {"status": "UNAVAILABLE"}
        if (str(principal.actor_id) != parts[2] or
                str(principal.session_id) != parts[3]):
            return {"status": "DENIED"}
        return {"status": "SIGNED",
                "signature": hmac.new(keys[key_id], material, hashlib.sha256).hexdigest()}
    except (ValueError, TypeError, UnicodeError, KeyError, OverflowError):
        return {"status": "DENIED"}
    except Exception:
        return {"status": "UNAVAILABLE"}


def _mtls_persistent_worker(control, auth_url, publishable_key, ca, server_cert,
                 server_key, state_path):
    keys = {}
    state = LocalCertificateState(state_path)
    revision_watermark = 0
    listener = None
    try:
        verifier = SupabaseGoTrueVerifier(auth_url, publishable_key)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        tls.verify_mode = ssl.CERT_REQUIRED
        tls.load_cert_chain(server_cert, server_key)
        tls.load_verify_locations(cafile=ca)
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(8)
        listener.settimeout(0.08)
        control.send(("READY", listener.getsockname()[1]))
        running = True
        while running:
            if control.poll():
                try:
                    command = control.recv()
                except EOFError:
                    break
                if type(command) is not tuple or not command:
                    control.send(("DENIED", None))
                    continue
                if command[0] == "STOP" and len(command) == 1:
                    control.send(("STOPPED", None))
                    break
                if command[0] == "LOAD" and len(command) == 3:
                    _, key_id, secret = command
                    if (type(key_id) is uuid.UUID and type(secret) is bytes
                            and len(secret) == 32 and key_id not in keys):
                        keys[key_id] = secret
                        control.send(("LOADED", None))
                    else:
                        control.send(("DENIED", None))
                    continue
                if command[0] == "REVOKE" and len(command) == 2:
                    if command[1] in keys:
                        keys.pop(command[1])
                        control.send(("REVOKED", None))
                    else:
                        control.send(("DENIED", None))
                    continue
                control.send(("DENIED", None))
                continue
            try:
                conn, peer = listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            if peer[0] != "127.0.0.1":
                conn.close()
                continue
            try:
                conn.settimeout(8)
                with tls.wrap_socket(conn, server_side=True) as secured:
                    certificate = secured.getpeercert(binary_form=True)
                    # I29: a cada NOVA conexao, consultar a fonte persistente
                    # fora do processo. Snapshot ausente/adulterado ou revisao
                    # inferior a ja vista => nenhuma assinatura.
                    try:
                        snap = state.snapshot()
                    except RevocationStateUnavailable:
                        continue
                    if snap["version"] < revision_watermark:
                        continue
                    revision_watermark = snap["version"]
                    if (not certificate or hashlib.sha256(certificate).hexdigest()
                            not in snap["active"]):
                        continue
                    try:
                        request = _read_frame(secured)
                        response = _sign_with_verified_identity(request, keys, verifier)
                    except (ValueError, TypeError, OSError, UnicodeError):
                        response = {"status": "DENIED"}
                    _send_frame(secured, response)
            except (OSError, ssl.SSLError, TimeoutError, ValueError):
                # Nunca logar body, Bearer, secret, material ou peer.
                continue
    except Exception:
        try:
            control.send(("FAILED", None))
        except (OSError, EOFError):
            pass
    finally:
        keys.clear()
        if listener is not None:
            listener.close()
        control.close()


class LocalMutualTlsSignerClient:
    def __init__(self, *, port, ca, cert, key, process,
                 expected_server_fingerprint):
        self._port = port
        self._ca = ca
        self._cert = cert
        self._key = key
        self._process = process
        self._server_pin = expected_server_fingerprint

    def sign(self, key_id, material, authorization=None):
        if not self._process.is_alive():
            raise IdentityUnavailable("SIGNER_MTLS_DOWN")
        if type(key_id) is not uuid.UUID or type(material) is not bytes:
            raise Denied("I27_BAD_SIGN_REQUEST")
        if not isinstance(authorization, str):
            raise Denied("I27_BEARER_REQUIRED")
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self._ca)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(self._cert, self._key)
        try:
            with socket.create_connection(("127.0.0.1", self._port), timeout=9) as conn:
                conn.settimeout(9)
                with context.wrap_socket(conn, server_hostname="localhost") as tls:
                    cert = tls.getpeercert(binary_form=True)
                    if (not cert or hashlib.sha256(cert).hexdigest() != self._server_pin):
                        raise IdentityUnavailable("I27_SERVER_IDENTITY_DENIED")
                    _send_frame(tls, {
                        "action": "SIGN",
                        "key_id": str(key_id),
                        "material": base64.b64encode(material).decode("ascii"),
                        "authorization": authorization,
                    })
                    response = _read_frame(tls)
        except (OSError, TimeoutError, ssl.SSLError, ValueError, TypeError):
            raise IdentityUnavailable("I27_MTLS_UNAVAILABLE") from None
        if response.get("status") == "UNAVAILABLE":
            raise IdentityUnavailable("I27_GOTRUE_UNAVAILABLE")
        signature = response.get("signature")
        if (response.get("status") != "SIGNED" or
            not isinstance(signature, str) or
            not re.fullmatch(r"[0-9a-f]{64}", signature)):
            raise Denied("I27_SIGN_NOT_AUTHORIZED")
        return signature


class LocalPersistentTlsSignerSupervisor:
    """Runner CI provisiona HMAC via pipe fora do transporte TLS de assinatura."""

    def __init__(self, *, independent_auth_url, publishable_key,
                 ca, server_cert, server_key, gateway_cert, gateway_key,
                 gateway_fingerprint, server_fingerprint, state_path):
        u = urlsplit(independent_auth_url)
        if (u.scheme != "http" or u.hostname not in
            ("127.0.0.1", "localhost", "::1") or u.username or u.password
                or u.query or u.fragment or u.path.rstrip("/")):
            raise ValueError("I27_LOCAL_GOTRUE_REQUIRED")
        if not isinstance(publishable_key, str) or not publishable_key:
            raise ValueError("I27_ANON_KEY_REQUIRED")
        if not (isinstance(gateway_fingerprint, str)
                and re.fullmatch("[a-f0-9]{64}", gateway_fingerprint)
                and isinstance(server_fingerprint, str)
                and re.fullmatch("[a-f0-9]{64}", server_fingerprint)):
            raise ValueError("I27_CERTIFICATE_PIN_REQUIRED")
        self._state = LocalCertificateState(state_path)
        # Sem bootstrap no construtor: reinicio precisa de um ledger
        # preexistente, validado e sem restaurar pin revogado.
        snap = self._state.snapshot()
        if gateway_fingerprint not in snap["active"] | snap["revoked"]:
            raise ValueError("I29_CERT_NOT_IN_PERSISTENT_LEDGER")
        ctx = multiprocessing.get_context("spawn")
        self._control, child = ctx.Pipe(duplex=True)
        self._lock = threading.Lock()
        self._process = ctx.Process(
            target=_mtls_persistent_worker,
            args=(child, independent_auth_url, publishable_key, ca,
                  server_cert, server_key, str(self._state.path)),
            name="prumo_s1_i29_persistent_tls_signer_local", daemon=True)
        self._process.start()
        child.close()
        if not self._control.poll(5):
            self.terminate()
            raise IdentityUnavailable("I27_SIGNER_NOT_READY")
        state, port = self._control.recv()
        if state != "READY" or type(port) is not int:
            self.terminate()
            raise IdentityUnavailable("I27_SIGNER_START_FAILED")
        self.client = LocalMutualTlsSignerClient(
            port=port, ca=ca, cert=gateway_cert, key=gateway_key,
            process=self._process, expected_server_fingerprint=server_fingerprint)

    def _change(self, action, *values):
        if not self._process.is_alive():
            raise IdentityUnavailable("I27_SIGNER_DOWN")
        with self._lock:
            try:
                self._control.send((action, *values))
                if not self._control.poll(5):
                    self.terminate()
                    raise IdentityUnavailable("I27_CONTROL_TIMEOUT")
                state, _ = self._control.recv()
                return state
            except (OSError, EOFError, BrokenPipeError):
                raise IdentityUnavailable("I27_CONTROL_DOWN") from None

    def load(self, key_id, secret):
        return self._change("LOAD", key_id, secret) == "LOADED"

    def revoke(self, key_id):
        return self._change("REVOKE", key_id) == "REVOKED"

    def stage_certificate(self, fingerprint, expected_version):
        # Apenas supervisor administrativo toca o SQLite, nunca gateway TLS.
        return self._state.change("STAGE_CERT", fingerprint, expected_version)

    def revoke_certificate(self, fingerprint, expected_version):
        return self._state.change("REVOKE_CERT", fingerprint, expected_version)

    def rotation_status(self):
        return self._state.status()

    def client_with_certificate(self, cert_path, key_path):
        # Criar cliente NAO autoriza certificado: so controle STAGE_CERT o faz.
        return LocalMutualTlsSignerClient(
            port=self.client._port, ca=self.client._ca,
            cert=cert_path, key=key_path, process=self._process,
            expected_server_fingerprint=self.client._server_pin)

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
        self._control.close()
