"""S1-002/I31. Autoridade de revogacao com witness externo em OUTRO processo, APENAS CI.

Snapshot SQLite I29 com HMAC-SHA256 cuja chave so entra no processo de
autoridade. Servico de assinatura recebe APENAS pipe CHECK, nunca HMAC
da autoridade ou canal admin. Monotonic watermark e retido enquanto a
autoridade continuar viva, mesmo se o assinador reiniciar.
Nao resiste a root/mesmo UID nem rollback de ledger+checkpoint anterior
ao restart DA PROPRIA AUTORIDADE: falta contador externo WORM.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import multiprocessing
from multiprocessing.connection import wait
import os
from pathlib import Path
import re
import stat
import threading

from backend.s1_i29_persistent_certificate_store import (
    LocalCertificateState, RevocationStateUnavailable
)
from backend.identity_boundary import IdentityUnavailable
from backend.s1_i31_monotonic_witness_local import LocalWitnessClient

_FP = re.compile(r"[0-9a-f]{64}\Z")


def _canonical(snapshot):
    # Bytes incluem TODA allowlist/tombstones e historico, mas nao credenciais.
    return json.dumps({
        "domain":"prumo-s1-i30-local-v1",
        "revision":snapshot["version"],
        "active":sorted(snapshot["active"]),
        "revoked":sorted(snapshot["revoked"]),
        "events":[list(x) for x in snapshot["events"]],
    }, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode("ascii")


def _read_checkpoint(path):
    try:
        p=Path(path)
        info=p.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size>4096:
            raise RevocationStateUnavailable("I30_CHECKPOINT_INSECURE")
        obj=json.loads(p.read_text(encoding="ascii"))
        if (type(obj) is not dict or set(obj)!={"revision","mac"} or
            type(obj["revision"]) is not int or obj["revision"]<1 or
            type(obj["mac"]) is not str or _FP.fullmatch(obj["mac"]) is None):
            raise RevocationStateUnavailable("I30_CHECKPOINT_BAD")
        return obj
    except (OSError, UnicodeError, ValueError, TypeError):
        raise RevocationStateUnavailable("I30_CHECKPOINT_UNAVAILABLE") from None


def _write_checkpoint(path, revision, digest, *, create=False):
    target=Path(path)
    # Commit SQLite ocorre ANTES desta escrita; pane intermediaria fecha
    # a autoridade, sem aceitar estados que nao correspondem ao checkpoint.
    payload=json.dumps({"revision":revision,"mac":digest},
                       sort_keys=True,separators=(",",":")).encode("ascii")
    if create:
        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        return
    temp=target.with_name(target.name+".i30-next")
    fd=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,target)
        dir_fd=os.open(str(target.parent),os.O_RDONLY)
        try:os.fsync(dir_fd)
        finally:os.close(dir_fd)
    except Exception:
        try:os.unlink(temp)
        except OSError:pass
        raise


def _witness_authority_worker(admin, requests, db_path, checkpoint_path, secret, witness_connection):
    ledger=LocalCertificateState(db_path)
    witness=LocalWitnessClient(witness_connection)
    watermark=0

    def signed_snapshot():
        nonlocal watermark
        snap=ledger.snapshot()
        checkpoint=_read_checkpoint(checkpoint_path)
        mac=hmac.new(secret,_canonical(snap),hashlib.sha256).hexdigest()
        if (checkpoint["revision"]!=snap["version"] or
            not hmac.compare_digest(checkpoint["mac"],mac) or
            snap["version"]<watermark):
            raise RevocationStateUnavailable("I30_MAC_OR_ROLLBACK")
        if not witness.check(snap["version"],mac):
            raise RevocationStateUnavailable("I31_EXTERNAL_WITNESS_REJECTED")
        watermark=max(watermark,snap["version"])
        return snap

    try:
        if type(secret) is not bytes or len(secret)!=32:
            raise RevocationStateUnavailable("I30_BAD_KEY")
        # I31: bootstrap do checkpoint e witness so no runner confiavel.
        # Reiniciar a authority jamais recria/zera qualquer estado.
        signed_snapshot()
        admin.send(("READY",None))
        while True:
            for channel in wait([admin,requests],timeout=0.2):
                try:
                    msg=channel.recv()
                except (EOFError,OSError):
                    return
                if type(msg) is not tuple or not msg:
                    channel.send(("DENIED",None))
                    continue
                if channel is requests:
                    if len(msg)!=2 or msg[0]!="CHECK" or type(msg[1]) is not str:
                        channel.send(("DENY",None))
                        continue
                    try:
                        snap=signed_snapshot()
                        result="ALLOW" if msg[1] in snap["active"] else "DENY"
                        channel.send((result,snap["version"]))
                    except RevocationStateUnavailable:
                        channel.send(("UNAVAILABLE",None))
                    continue
                action=msg[0]
                if action=="STOP" and len(msg)==1:
                    admin.send(("STOPPED",None))
                    return
                if action=="STATUS" and len(msg)==1:
                    try:
                        snap=signed_snapshot()
                        admin.send(("STATUS",{
                            "version":snap["version"],
                            "active_count":len(snap["active"]),
                            "revoked_count":len(snap["revoked"]),
                            "events":list(snap["events"]),
                        }))
                    except RevocationStateUnavailable:
                        admin.send(("UNAVAILABLE",None))
                    continue
                if action not in ("STAGE_CERT","REVOKE_CERT") or len(msg)!=3:
                    admin.send(("DENIED",None))
                    continue
                fp,expected=msg[1:]
                try:
                    snap=signed_snapshot()
                    if type(expected) is not int or expected!=snap["version"]:
                        admin.send(("STALE",snap["version"]))
                        continue
                    if type(fp) is not str or _FP.fullmatch(fp) is None:
                        admin.send(("DENIED",snap["version"]))
                        continue
                    # Qualquer falha entre commit e MAC causa fail closed.
                    outcome,rev=ledger.change(action,fp,expected)
                    if outcome not in ("STAGED","REVOKED"):
                        admin.send((outcome,rev))
                        continue
                    changed=ledger.snapshot()
                    digest=hmac.new(secret,_canonical(changed),hashlib.sha256).hexdigest()
                    _write_checkpoint(checkpoint_path,rev,digest)
                    if not witness.advance(snap["version"],rev,digest):
                        raise RevocationStateUnavailable("I31_WITNESS_NOT_ADVANCED")
                    watermark=rev
                    admin.send((outcome,rev))
                except (RevocationStateUnavailable,OSError):
                    admin.send(("UNAVAILABLE",None))
    except (RevocationStateUnavailable,OSError,ValueError):
        try:admin.send(("FAILED",None))
        except (EOFError,OSError):pass
    finally:
        admin.close()
        requests.close()
        witness_connection.close()


class LocalAuthorityCheckClient:
    """Objeto UNICO entregue ao signer: nao recebe chave MAC nem admin."""
    def __init__(self,connection):
        self._connection=connection
        self._unusable=False

    def allowed(self,fingerprint):
        if self._unusable or type(fingerprint) is not str or _FP.fullmatch(fingerprint) is None:
            return False
        try:
            self._connection.send(("CHECK",fingerprint))
            if not self._connection.poll(3):
                self._unusable=True
                self._connection.close()
                return False
            outcome,_=self._connection.recv()
            return outcome=="ALLOW"
        except (EOFError,OSError,BrokenPipeError):
            self._unusable=True
            return False


class LocalWitnessBackedRevocationSupervisor:
    """Runner administrativo, nunca entregue ao gateway ou signer."""
    def __init__(self, *, db_path, checkpoint_path, secret, witness_client):
        if not isinstance(witness_client,LocalWitnessClient):
            raise ValueError("I31_WITNESS_REQUIRED")
        ctx=multiprocessing.get_context("spawn")
        self._admin,admin_child=ctx.Pipe(duplex=True)
        client_parent,client_child=ctx.Pipe(duplex=True)
        self._lock=threading.Lock()
        self._process=ctx.Process(
            target=_witness_authority_worker,
            args=(admin_child,client_child,str(db_path),str(checkpoint_path),
                  secret,witness_client._pipe),
            name="prumo_s1_i31_witness_backed_authority_ci",daemon=True)
        self._process.start()
        admin_child.close()
        client_child.close()
        self.client=LocalAuthorityCheckClient(client_parent)
        if not self._admin.poll(5):
            self.close()
            raise IdentityUnavailable("I30_AUTHORITY_START_TIMEOUT")
        state,_=self._admin.recv()
        if state!="READY":
            self.close()
            raise IdentityUnavailable("I31_AUTHORITY_START_DENIED")

    def _request(self,*payload):
        if not self._process.is_alive():
            raise IdentityUnavailable("I30_AUTHORITY_DOWN")
        with self._lock:
            try:
                self._admin.send(payload)
                if not self._admin.poll(5):
                    raise IdentityUnavailable("I30_AUTHORITY_TIMEOUT")
                state,value=self._admin.recv()
                if state=="UNAVAILABLE":
                    raise IdentityUnavailable("I30_LEDGER_UNAVAILABLE")
                return state,value
            except (EOFError,OSError):
                raise IdentityUnavailable("I30_AUTHORITY_UNAVAILABLE") from None

    def stage_certificate(self,fp,version):
        return self._request("STAGE_CERT",fp,version)

    def revoke_certificate(self,fp,version):
        return self._request("REVOKE_CERT",fp,version)

    def status(self):
        outcome,value=self._request("STATUS")
        if outcome!="STATUS":
            raise IdentityUnavailable("I30_BAD_AUTHORITY_STATUS")
        return value

    def terminate(self):
        if self._process.is_alive():
            self._process.terminate()
        self._process.join(timeout=3)

    def close(self):
        if self._process.is_alive():
            try:self._request("STOP")
            except IdentityUnavailable:pass
        self._process.join(timeout=3)
        if self._process.is_alive():
            self.terminate()
        self._admin.close()
        self.client._connection.close()


def bootstrap_i31_authority(db_path, checkpoint_path, witness_path, authority_key, witness_key):
    """Criacao CI unica para conjunto inicialmente rev=1, sem restauro implicito."""
    from backend.s1_i31_monotonic_witness_local import bootstrap_witness
    snap=LocalCertificateState(db_path).snapshot()
    if snap["version"]!=1 or len(snap["active"])!=1 or snap["revoked"] or snap["events"]:
        raise ValueError("I31_INITIAL_STATE_INVALID")
    digest=hmac.new(authority_key,_canonical(snap),hashlib.sha256).hexdigest()
    _write_checkpoint(checkpoint_path,1,digest,create=True)
    bootstrap_witness(witness_path,witness_key,digest)
