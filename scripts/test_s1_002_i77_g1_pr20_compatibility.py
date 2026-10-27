#!/usr/bin/env python3
"""S1-002/I77 — fail-closed reconciliation of PR #20's pinned G1 fixture.

Source G1 is checked out into a disposable folder, NEVER merged into S1.
The only ephemeral write is ref in the copied G1 manifest, after content-hash
verification of all CURRENT S1 source/test files. Ref update is NOT a trust
exception; exact SHA256 equality is required, and missing/extra files fail.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

PR20_CODE="d53c40a6ef55e82d2282c482b299cff1dbf990bd"
S1_BASE="b71ebf4479c9a0a3527519471cca04ec7e178e18"
CONTRACT="s0.g1.manual-queue.v1"

def gitsha(path):
    return subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"],text=True).strip()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def reconcile(g1,s1,current,*,write=False):
    g1,s1=Path(g1).resolve(),Path(s1).resolve()
    if gitsha(g1)!=PR20_CODE:
        raise ValueError("I77_G1_SHA_NOT_CERTIFIED")
    if gitsha(s1)!=current:
        raise ValueError("I77_S1_SHA_NOT_CURRENT")
    if s1==g1 or s1 in g1.parents or (g1 in s1.parents and s1.name!="work-s1-sources"):
        raise ValueError("I77_INVALID_CHECKOUT_LAYOUT")
    mf=g1/"integration/g1/s1_sources.json"
    j=json.loads(mf.read_text(encoding="utf-8"))
    if j["ref"]!=S1_BASE:
        raise ValueError("I77_UNEXPECTED_G1_SOURCE_BASE")
    files=j["files"]+j["test_sources"]
    names=[x["path"] for x in files]
    if len(files)!=34 or len(set(names))!=len(names):
        raise ValueError("I77_INCOMPLETE_OR_DUPLICATED_MANIFEST")
    for entry in files:
        rel=Path(entry["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("I77_UNSAFE_MANIFEST_PATH")
        f=s1/rel
        if not f.is_file() or digest(f)!=entry["sha256"]:
            raise ValueError("I77_S1_SOURCE_DRIFT:"+entry["path"])
    src=(g1/"supabase/tests/s0_g1_manual_queue_local_only.sql").read_text()
    if ("'PENDENTE','ASSUMIDO','DISTRIBUIDO','RECONCILIADO','ENCAMINHADO'" not in src
       or "G1_UNKNOWN_QUEUE_EVENT_CONTRACT" not in src
       or "insert into prumo_private.s0_fila_humana_eventos" not in src
       or "'ENCAMINHADO',p_gestor,p_destino" not in src
       or "g1_manual_requests_local" not in src
       or "s1_prova_excecao_i61" not in src):
        raise ValueError("I77_EVENT_OR_I61_CONTRACT_DRIFT")
    backend=(g1/"backend/s0_g1_manual_queue_local.py").read_text()
    if ("s0-g1-manual-queue-local-v1" not in backend
        or "S0CFI01AtomicCommandsLocal" not in backend
        or "safe_result(rows[0][0],command)" not in backend):
        raise ValueError("I77_G1_AUTH_OR_RESULT_DRIFT")
    result={"mode":"pinned PR20 code; S1-current-content verified",
        "g1_pr20_code":PR20_CODE,"s1_ref":current,"s1_manifest_base":S1_BASE,
        "sha256_verified_files":len(files),
        "event":"ENCAMINHADO","legacy_events_preserved":True,
        "code_imported_to_s1":False,"S0_hosted_changed":False,
        "G1_production_owner_provisioning_approved":False}
    if write:
        j["ref"]=current
        mf.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n")
        dst=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"s1_i77_g1_pinned_compatibility.json"
        dst.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print("PASS I77-01: certified PR20 code, current S1 34/34 SHA256 fixture files and ENCAMINHADO contract")
        print("PASS I77-02: ephemeral manifest rebound to S1 HEAD without source substitutions")
        print("I77 artifact:",dst)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--g1",required=True)
    p.add_argument("--s1",required=True);p.add_argument("--s1-sha",required=True)
    a=p.parse_args()
    if os.environ.get("CI")!="true" or os.environ.get("PRUMO_G1_DISPOSABLE_TEST")!="YES":
        raise SystemExit("I77_ONLY_EPHEMERAL_CI")
    reconcile(a.g1,a.s1,a.s1_sha,write=True)
