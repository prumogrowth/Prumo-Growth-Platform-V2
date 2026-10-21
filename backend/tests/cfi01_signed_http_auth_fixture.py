"""SYNTHETIC JWT-signature-checking HTTP test server, NOT Supabase GoTrue.

Only for CI's loopback PG17 integration. Secret is disposable/test-only;
no real GoTrue database, users or production authentication is exercised.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
import uuid
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = b"synthetic-local-auth-fixture-secret-never-use-in-production"
def _url64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

def _decode(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * ((-len(seg)) % 4))

def make_signed_token(actor: uuid.UUID, session: uuid.UUID,
                      *, expires_at: int | None = None,
                      signing_key: bytes = KEY) -> str:
    header = _url64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _url64(json.dumps({
        "sub": str(actor), "session_id": str(session),
        "role": "authenticated",
        "exp": expires_at if expires_at is not None else int(time.time()) + 120,
    }, separators=(',', ':')).encode())
    body = (header + "." + payload).encode("ascii")
    signature = _url64(hmac.new(signing_key, body, hashlib.sha256).digest())
    return "Bearer " + body.decode("ascii") + "." + signature


@contextmanager
def mock_signed_auth_server():
    """Local server that checks JWT HS256 + expiration before returning /user."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/auth/v1/user":
                self.send_error(404)
                return
            bearer = self.headers.get("Authorization", "")
            parts = bearer.removeprefix("Bearer ").split(".")
            if (not bearer.startswith("Bearer ") or len(parts) != 3
                    or not all(parts)):
                self.send_error(401)
                return
            try:
                header, payload, sig = parts
                obj = json.loads(_decode(header))
                user = json.loads(_decode(payload))
                body = (header + "." + payload).encode("ascii")
                expected = hmac.new(KEY, body, hashlib.sha256).digest()
                signed = _decode(sig)
                valid = (obj.get("alg") == "HS256"
                         and hmac.compare_digest(expected, signed)
                         and user.get("role") == "authenticated"
                         and isinstance(user.get("exp"), int)
                         and user["exp"] > time.time())
                actor = uuid.UUID(user["sub"])
                session = uuid.UUID(user["session_id"])
                valid = valid and actor.int != 0 and session.int != 0
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                valid = False
            if not valid:
                self.send_error(401)
                return
            data = json.dumps({"id": str(actor), "role": "authenticated"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args):
            # Never log auth bearer even in ephemeral tests.
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
