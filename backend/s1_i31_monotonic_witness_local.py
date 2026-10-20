"""S1-002/I31: testemunha monotônica em processo/arquivo proprio, SOMENTE CI.

Diferente da authority I30: o witness guarda revisao+digest autenticados
sob uma segunda chave HMAC. Sobrevive ao restart da authority. Nunca
compartilha a chave witness com signer ou authority; authority usa somente
pipe client que suporta CHECK e ADVANCE CAS.

NAO E anti-rollback completo: mesmo usuario do runner controla witness key,
arquivo e processos. Quem restaurar TODOS os snapshots e segredos antes
do restart de TODOS os processos pode contornar este prototipo.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import multiprocessing
from pathlib import Path
import os
import re
import stat
import threading


_HASH = re.compile(r"[0-9a-f]{64}\Z")


def _payload(revision, digest):
    return json.dumps(
        {"domain":"prumo-s1-i31-witness-ci-v1","revision":revision,"digest":digest},
        sort_keys=True,separators=(",",":"),ensure_ascii=True
    ).encode("ascii")


def _seal(secret, revision, digest):
    return hmac.new(secret,_payload(revision,digest),hashlib.sha256).hexdigest()


def _validate_record(path, secret):
    try:
        p=Path(path)
        st=p.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_mode&0o077 or st.st_size>1024:
            return None
        value=json.loads(p.read_text(encoding="ascii"))
        if (type(value) is not dict or set(value)!={"revision","digest","mac"} or
            type(value["revision"]) is not int or value["revision"]<1 or
            any(type(value[k]) is not str or _HASH.fullmatch(value[k]) is None
                for k in ("digest","mac"))):
            return None
        if not hmac.compare_digest(_seal(secret,value["revision"],value["digest"]),value["mac"]):
            return None
        return value
    except (OSError,UnicodeError,ValueError,TypeError):
        return None


def _create_file(path, secret, revision, digest):
    if type(secret) is not bytes or len(secret)!=32 or type(revision) is not int or revision!=1 or not isinstance(digest,str) or not _HASH.fullmatch(digest):
        raise ValueError("I31_INVALID_BOOTSTRAP")
    p=Path(path)
    data=json.dumps({"revision":revision,"digest":digest,"mac":_seal(secret,revision,digest)},
                    sort_keys=True,separators=(",",":")).encode("ascii")
    fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,"wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    dir_fd=os.open(str(p.parent),os.O_RDONLY)
    try:os.fsync(dir_fd)
    finally:os.close(dir_fd)


def _replace_file(path, secret, revision, digest):
    p=Path(path)
    data=json.dumps({"revision":revision,"digest":digest,"mac":_seal(secret,revision,digest)},
                    sort_keys=True,separators=(",",":")).encode("ascii")
    tmp=p.with_name(p.name+".i31-next")
    fd=os.open(tmp,os.O_EXCL|os.O_CREAT|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,p)
        dir_fd=os.open(str(p.parent),os.O_RDONLY)
        try:os.fsync(dir_fd)
        finally:os.close(dir_fd)
    except Exception:
        try:os.unlink(tmp)
        except OSError:pass
        raise


def bootstrap_witness(path, secret, digest):
    """ONE TIME somente no CI. Não reconstituir a partir de arquivo revertido."""
    _create_file(path,secret,1,digest)


def _worker(requests, control, path, secret):
    try:
        if type(secret) is not bytes or len(secret)!=32 or _validate_record(path,secret) is None:
            control.send(("FAILED",None))
            return
        control.send(("READY",None))
        while True:
            from multiprocessing.connection import wait
            for conn in wait([requests,control],timeout=0.2):
                try:cmd=conn.recv()
                except (EOFError,OSError):return
                if conn is control:
                    if cmd==("STOP",):
                        control.send(("STOPPED",None))
                        return
                    if cmd==("STATUS",):
                        record=_validate_record(path,secret)
                        control.send(("STATUS",None if record is None else record["revision"]))
                    else:
                        control.send(("DENIED",None))
                    continue
                if type(cmd) is not tuple or not cmd:
                    requests.send(("DENIED",None))
                    continue
                record=_validate_record(path,secret)
                if record is None:
                    requests.send(("UNAVAILABLE",None))
                    continue
                revision,digest=record["revision"],record["digest"]
                if cmd[0]=="CHECK" and len(cmd)==3:
                    _,r,d=cmd
                    valid=type(r) is int and r==revision and type(d) is str and hmac.compare_digest(d,digest)
                    requests.send(("OK" if valid else "DENIED",revision))
                elif cmd[0]=="ADVANCE" and len(cmd)==4:
                    _,prior,next_revision,new_digest=cmd
                    if (type(prior) is not int or prior!=revision or
                        type(next_revision) is not int or next_revision!=revision+1 or
                        type(new_digest) is not str or _HASH.fullmatch(new_digest) is None):
                        requests.send(("STALE",revision))
                        continue
                    try:
                        _replace_file(path,secret,next_revision,new_digest)
                        requests.send(("ADVANCED",next_revision))
                    except OSError:
                        requests.send(("UNAVAILABLE",None))
                else:
                    requests.send(("DENIED",None))
    finally:
        requests.close()
        control.close()


class LocalWitnessClient:
    """Somente authority recebe isto; signer nao pode avancar revisao."""
    def __init__(self,pipe):
        self._pipe=pipe
        self._lock=threading.Lock()
        self._failed=False

    def _rpc(self,*params):
        if self._failed:return "UNAVAILABLE",None
        with self._lock:
            try:
                self._pipe.send(params)
                if not self._pipe.poll(4):
                    self._failed=True
                    self._pipe.close()
                    return "UNAVAILABLE",None
                return self._pipe.recv()
            except (EOFError,OSError,BrokenPipeError):
                self._failed=True
                return "UNAVAILABLE",None

    def check(self,revision,digest):
        return self._rpc("CHECK",revision,digest)[0]=="OK"

    def advance(self,prior,revision,digest):
        return self._rpc("ADVANCE",prior,revision,digest)==("ADVANCED",revision)


class LocalMonotonicWitnessSupervisor:
    def __init__(self,*,path,secret):
        ctx=multiprocessing.get_context("spawn")
        self._control,ctl_child=ctx.Pipe()
        client_parent,client_child=ctx.Pipe()
        self._process=ctx.Process(target=_worker,args=(client_child,ctl_child,str(path),secret),
            name="prumo_s1_i31_rollback_witness_ci",daemon=True)
        self._process.start()
        ctl_child.close()
        client_child.close()
        self.client=LocalWitnessClient(client_parent)
        if not self._control.poll(5):
            self.terminate()
            raise RuntimeError("I31_WITNESS_NOT_READY")
        status,_=self._control.recv()
        if status!="READY":
            self.terminate()
            raise RuntimeError("I31_WITNESS_STATE_INVALID")

    def status(self):
        if not self._process.is_alive():return None
        self._control.send(("STATUS",))
        if not self._control.poll(4):return None
        status,revision=self._control.recv()
        return revision if status=="STATUS" else None

    def terminate(self):
        if self._process.is_alive():self._process.terminate()
        self._process.join(timeout=3)

    def close(self):
        if self._process.is_alive():
            try:
                self._control.send(("STOP",))
                self._control.poll(2)
            except (EOFError,OSError):pass
            self._process.join(timeout=3)
        if self._process.is_alive():self.terminate()
        self.client._pipe.close()
        self._control.close()
