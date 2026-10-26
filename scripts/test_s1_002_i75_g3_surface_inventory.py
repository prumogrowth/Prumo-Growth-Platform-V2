#!/usr/bin/env python3
"""I75B: lexical S0/S1 G3 inventory; no database/network/client data.
Static evidence NEVER certifies effective RLS, production or media URLs.
"""
from pathlib import Path
import json
import os
import re

CORE={
 "public.leads_loja":("concessionaria_id","telefone_cliente_normalizado"),
 "public.ciclos_comerciais":("concessionaria_id","lead_id"),
 "public.casos_humanos":("concessionaria_id","lead_id","ciclo_id"),
 "public.atribuicoes_humanas":("concessionaria_id","caso_id","operador_id"),
 "public.conversas":("concessionaria_id","lead_id","canal_id","caso_id"),
 "public.mensagens":("concessionaria_id","conversa_id","canal_id","caso_id"),
 "public.itens_lote":("concessionaria_id","lote_id","lead_id"),
 "public.reencontros_lote":("concessionaria_id","lote_id","lead_id"),
 "public.eventos_status_comercial":("concessionaria_id","ciclo_id"),
 "public.lotes_importacao":("concessionaria_id",),
 "public.canais_loja":("concessionaria_id",),
}
HISTORY={"public.casos_humanos","public.atribuicoes_humanas",
         "public.conversas","public.mensagens"}
ROWS={"public.itens_lote","public.reencontros_lote","public.eventos_status_comercial"}
HEADERS={"public.lotes_importacao","public.canais_loja"}
DDL=re.compile(r"\bcreate\s+(?:unlogged\s+)?table\s+(?:if\s+not\s+exists\s+)?((?:public|prumo_private|storage)\.[a-z_][\w]*)\s*\(",re.I)
POLICY=re.compile(r"\bcreate\s+policy\s+([a-z_][\w]*)\s+on\s+((?:public|prumo_private|storage)\.[a-z_][\w]*)",re.I)
MEDIA=re.compile(r"\b(?:storage\.objects|storage\.buckets|createSignedUrl|signed_url|presigned|media_url|m[ií]dia(?:s)?|anexo(?:s)?|attachment(?:s)?|bucket(?:s)?)\b",re.I)
SENSITIVE=re.compile(r"telefone|conteudo|documento|cpf|banco|segredo|secret|token|payload|fingerprint|id_externo",re.I)

def strip_comments(src):
    result=[]
    for line in src.splitlines():
        quote=False; out=[];i=0
        while i<len(line):
            if line[i]=="'":
                if quote and i+1<len(line) and line[i+1]=="'":
                    out.extend(("'","'"));i+=2;continue
                quote=not quote
            if not quote and line[i:i+2]=="--": break
            out.append(line[i]);i+=1
        result.append("".join(out))
    return "\n".join(result)

def ddl_columns(source):
    cleaned=strip_comments(source);out={}
    for m in DDL.finditer(cleaned):
        key=m.group(1).lower();i=m.end();level=1;quoted=False;chunk=[]
        while i<len(cleaned) and level:
            c=cleaned[i]
            if c=="'":
                if quoted and i+1<len(cleaned) and cleaned[i+1]=="'":
                    chunk.extend(("'","'"));i+=2;continue
                quoted=not quoted
            if not quoted:
                if c=="(": level+=1
                elif c==")": level-=1
            if level:chunk.append(c)
            i+=1
        if level:raise ValueError("I75_UNBALANCED_DDL:"+key)
        parts=[];word=[];nesting=0;quoted=False
        for c in "".join(chunk):
            if c=="'":quoted=not quoted
            if not quoted:
                if c=="(":nesting+=1
                elif c==")":nesting-=1
                elif c=="," and nesting==0:
                    parts.append("".join(word));word=[];continue
            word.append(c)
        parts.append("".join(word))
        cols=[]
        for part in parts:
            token=re.match(r"\s*([a-z_][\w]*)\s+",part,re.I)
            if token and token.group(1).lower() not in (
                "primary","foreign","constraint","unique","check","exclude"):
                cols.append(token.group(1).lower())
        if key in out:raise ValueError("I75_DUPLICATE_DDL:"+key)
        out[key]=cols
    return out

def discover(root):
    migrations=sorted((root/"supabase/migrations").glob("*.sql"))
    candidates=sorted((root/"supabase/tests").glob("*.sql"))
    runtime=[]
    for folder in ("backend","app","src","web","frontend","supabase/functions"):
        target=root/folder
        if target.is_dir():
            runtime.extend(p for p in target.rglob("*")
                           if p.is_file() and p.suffix in (".py",".js",".jsx",".ts",".tsx")
                           and "tests" not in p.parts)
    return migrations,candidates,sorted(set(runtime))

def inventory(root):
    migrations,candidates,runtime=discover(root)
    if not migrations:raise ValueError("I75_NO_MIGRATIONS")
    created={};migrated={}
    for file in migrations:
        raw=file.read_text(encoding="utf-8");src=strip_comments(raw)
        for name,cols in ddl_columns(raw).items():
            if name in created:raise ValueError("I75_TABLE_REDECLARED:"+name)
            created[name]={"file":file.relative_to(root).as_posix(),"columns":cols}
        for match in POLICY.finditer(src):
            migrated.setdefault(match.group(2).lower(),[]).append(
                {"file":file.relative_to(root).as_posix(),"name":match.group(1).lower()})
    missing=sorted(set(CORE)-set(created))
    if missing:raise ValueError("I75_REQUIRED_OBJECT_MISSING:"+",".join(missing))
    drift={name:sorted(set(cols)-set(created[name]["columns"])) for name,cols in CORE.items()
           if set(cols)-set(created[name]["columns"])}
    if drift:raise ValueError("I75_SCOPE_KEY_DRIFT:"+str(drift))
    candidate={};media=[]
    for file in candidates+migrations+runtime:
        raw=file.read_text(encoding="utf-8",errors="replace")
        rel=file.relative_to(root).as_posix()
        src=strip_comments(raw) if file.suffix==".sql" else raw
        if file in candidates:
            for match in POLICY.finditer(src):
                candidate.setdefault(match.group(2).lower(),[]).append(
                    {"file":rel,"name":match.group(1).lower()})
        if file in migrations or file in runtime:
            for number,line in enumerate(src.splitlines(),1):
                if MEDIA.search(line):
                    media.append({"file":rel,"line":number,"excerpt":line.strip()[:150]})
    counts={name:len([p for p in candidate.get(name,[])
                       if p["file"].endswith("s1_087_rls_excecao_canonica_local_only.sql")])
            for name in HISTORY}
    if sorted(counts.values())!=[2,2,2,2]:
        raise ValueError("I75_I63_POLICY_BASELINE_DRIFT:"+str(counts))
    consumers=[]
    for file in runtime:
        src=file.read_text(encoding="utf-8",errors="replace")
        refs=sorted(name for name in CORE if re.search(
            r"\b"+re.escape(name.split(".")[1])+r"\b",src,re.I))
        if refs:consumers.append({"file":file.relative_to(root).as_posix(),
            "references":refs,"note":"lexical candidate; not proven database access"})
    surfaces=[]
    for name in sorted(CORE):
        cols=created[name]["columns"]
        scope=("history" if name in HISTORY else
               "administrative-row" if name in ROWS else
               "shared-header" if name in HEADERS else "contact-or-cycle")
        surfaces.append({"table":name,"scope":scope,"source":created[name]["file"],
            "columns":cols,"sensitive_column_candidates":[c for c in cols if SENSITIVE.search(c)],
            "migrated_policies":migrated.get(name,[]),
            "candidate_test_policies":candidate.get(name,[]),
            "approved_operational_access":False})
    return {"scope":"static tracked checkout only; NOT effective grants or hosted Supabase",
        "scanned":{"migrations":len(migrations),"test_sql":len(candidates),"runtime_files":len(runtime)},
        "surfaces":surfaces,
        "other_declared_tables":[{"table":name,"source":val["file"]}
                                 for name,val in sorted(created.items()) if name not in CORE],
        "runtime_consumer_candidates":consumers,"media_lexical_matches":media,
        "media_storage_contract_verified":False,
        "d3_d4_object_column_contract_verified":False,
        "operational_gate":"BLOCKED_PENDING_S0_MEDIA_AND_COLUMN_CATALOG"}

def main():
    root=Path(__file__).resolve().parents[1]
    data=inventory(root)
    target=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"s1_002_i75b_g3_inventory.json"
    target.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PASS I75B-01: 11 canonical G3 tables found with required shop/case keys")
    print("PASS I75B-02: 8 I63 history RLS candidates verified as test-only")
    print("PASS I75B-03: inventoried %s migrations, %s additional tables, %s runtime files"%
          (data["scanned"]["migrations"],len(data["other_declared_tables"]),data["scanned"]["runtime_files"]))
    print("I75B-G3 MEDIA/D3/D4 ACCESS UNVERIFIED; no production authorization")
    print("I75B artifact:",target)

if __name__=="__main__":main()
