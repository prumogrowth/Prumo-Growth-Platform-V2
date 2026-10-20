"""S1-002/I29: autoridade DURAVEL de identidade TLS, somente CI efemero.

SQLite pertence ao runner administrador e NAO ao processo assinador.
Leitura do child via URI read-only a CADA nova conexao TLS. Ausencia,
corrupcao, schema adulterado, revisao regressiva: falha fechada.
Nao protege contra root/mesmo UID, rollback ANTES do restart, adulteracao
do SQLite por quem possui acesso de escrita ou perda de disco.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import sqlite3
import stat


_FP = re.compile(r"[0-9a-f]{64}\Z")


class RevocationStateUnavailable(Exception):
    pass


class LocalCertificateState:
    def __init__(self, path):
        self.path = Path(path).resolve()

    def initialize(self, gateway_fp):
        if type(gateway_fp) is not str or not _FP.fullmatch(gateway_fp):
            raise ValueError("I29_BOOTSTRAP_FP_INVALID")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # NUNCA sobrescrever state/tombstones em reinicio.
        fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        os.close(fd)
        try:
            with self._connection(read_only=False) as db:
                db.execute("PRAGMA synchronous=FULL")
                db.execute("CREATE TABLE meta (singleton integer PRIMARY KEY CHECK(singleton=1), revision integer NOT NULL CHECK(revision>=1))")
                db.execute("CREATE TABLE certificates (fingerprint text PRIMARY KEY, state text NOT NULL CHECK(state IN ('ACTIVE','REVOKED')))")
                db.execute("CREATE TABLE events (revision integer PRIMARY KEY, event_code text NOT NULL CHECK(event_code IN ('CERT_STAGED','CERT_REVOKED')))")
                db.execute("INSERT INTO meta VALUES(1,1)")
                db.execute("INSERT INTO certificates VALUES (?, 'ACTIVE')", (gateway_fp,))
                db.commit()
        except Exception:
            # Nenhuma recriacao silenciosa em caminho ja existente.
            raise

    def _connection(self, *, read_only):
        try:
            st = self.path.lstat()
            if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077:
                raise RevocationStateUnavailable("I29_INSECURE_STATE_FILE")
            if read_only:
                db = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=2)
                db.execute("PRAGMA query_only=ON")
            else:
                db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=2)
            db.execute("PRAGMA busy_timeout=2000")
            return db
        except (OSError, sqlite3.Error) as error:
            raise RevocationStateUnavailable("I29_STATE_UNAVAILABLE") from None

    def snapshot(self):
        try:
            with self._connection(read_only=True) as db:
                ok = db.execute("PRAGMA integrity_check").fetchone()
                if ok != ("ok",):
                    raise RevocationStateUnavailable("I29_INTEGRITY_CHECK_FAIL")
                tables = {
                    row[0] for row in db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")}
                if tables != {"meta","certificates","events"}:
                    raise RevocationStateUnavailable("I29_SCHEMA_MISMATCH")
                revision_row = db.execute(
                    "SELECT revision FROM meta WHERE singleton=1").fetchall()
                if len(revision_row) != 1 or type(revision_row[0][0]) is not int:
                    raise RevocationStateUnavailable("I29_INVALID_REVISION")
                revision = revision_row[0][0]
                rows = db.execute(
                    "SELECT fingerprint,state FROM certificates").fetchall()
                events = db.execute(
                    "SELECT revision,event_code FROM events ORDER BY revision").fetchall()
            active = set()
            revoked = set()
            for fp,state in rows:
                if type(fp) is not str or not _FP.fullmatch(fp) or fp in active or fp in revoked:
                    raise RevocationStateUnavailable("I29_INVALID_FP")
                if state == "ACTIVE":
                    active.add(fp)
                elif state == "REVOKED":
                    revoked.add(fp)
                else:
                    raise RevocationStateUnavailable("I29_INVALID_CERT_STATE")
            if (revision < 1 or len(active) > 2 or not rows or
                len(events) != revision-1 or
                any(event_revision != index+2 or event_code not in
                    ("CERT_STAGED","CERT_REVOKED")
                    for index,(event_revision,event_code) in enumerate(events))):
                raise RevocationStateUnavailable("I29_INVALID_LEDGER")
            # Nunca expor fingerprint no STATUS usado por runner.
            return {"version":revision,"active":frozenset(active),
                    "revoked":frozenset(revoked),"events":tuple(events)}
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise RevocationStateUnavailable("I29_STATE_CORRUPT") from None

    def status(self):
        s=self.snapshot()
        return {"version":s["version"],"active_count":len(s["active"]),
                "revoked_count":len(s["revoked"]),
                "events":list(s["events"])}

    def change(self, operation, fp, expected_version):
        if operation not in ("STAGE_CERT","REVOKE_CERT"):
            raise ValueError("I29_OPERATION_DENIED")
        if type(fp) is not str or _FP.fullmatch(fp) is None or type(expected_version) is not int or expected_version<1:
            return ("DENIED", self.snapshot()["version"])
        try:
            with self._connection(read_only=False) as db:
                db.execute("PRAGMA synchronous=FULL")
                db.execute("BEGIN IMMEDIATE")
                # Intencionalmente reler o snapshot sob transacao: snapshot()
                # usa conexao read-only separada, mas BEGIN IMMEDIATE garante
                # que nenhum outro escritor administrativo execute em paralelo.
                snapshot=self.snapshot()
                version=snapshot["version"]
                if expected_version != version:
                    return ("STALE",version)
                if operation == "STAGE_CERT":
                    if fp in snapshot["active"] or fp in snapshot["revoked"] or len(snapshot["active"])>=2:
                        return ("DENIED",version)
                    db.execute("INSERT INTO certificates (fingerprint,state) VALUES (?, 'ACTIVE')",(fp,))
                    code="CERT_STAGED"; outcome="STAGED"
                else:
                    if fp not in snapshot["active"]:
                        return ("DENIED",version)
                    db.execute("UPDATE certificates SET state='REVOKED' WHERE fingerprint=? AND state='ACTIVE'",(fp,))
                    code="CERT_REVOKED";outcome="REVOKED"
                db.execute("UPDATE meta SET revision=? WHERE singleton=1",(version+1,))
                db.execute("INSERT INTO events (revision,event_code) VALUES (?,?)",(version+1,code))
                db.commit()
                return (outcome,version+1)
        except (sqlite3.Error, OSError, RevocationStateUnavailable):
            raise RevocationStateUnavailable("I29_WRITE_FAILED") from None
