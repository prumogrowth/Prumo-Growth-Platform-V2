#!/usr/bin/env python3
"""I75C: effective PG17 G3 relation/column privilege snapshot, lab-only.

Never examines customer rows, external services or hosted databases. This does NOT
certify history, media, D3/D4 or PostgREST end-to-end permissions.
"""
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlparse, unquote

EXPECTED={
 "leads_loja":("concessionaria_id","telefone_cliente_normalizado"),
 "ciclos_comerciais":("concessionaria_id","lead_id"),
 "casos_humanos":("concessionaria_id","lead_id"),
 "atribuicoes_humanas":("concessionaria_id","caso_id","operador_id"),
 "conversas":("concessionaria_id","lead_id","canal_id","caso_id"),
 "mensagens":("concessionaria_id","conversa_id","canal_id","caso_id","conteudo_sintetico"),
 "itens_lote":("concessionaria_id","lote_id","lead_id"),
 "reencontros_lote":("concessionaria_id","lote_id","lead_id"),
 "eventos_status_comercial":("concessionaria_id","ciclo_id"),
 "lotes_importacao":("concessionaria_id",),
 "canais_loja":("concessionaria_id",),
}
SENSITIVE={"leads_loja":{"telefone_cliente_normalizado"},
           "mensagens":{"conteudo_sintetico"}}
QUERY=r"""
with requested(name) as (
 values ('leads_loja'),('ciclos_comerciais'),('casos_humanos'),
 ('atribuicoes_humanas'),('conversas'),('mensagens'),('itens_lote'),
 ('reencontros_lote'),('eventos_status_comercial'),('lotes_importacao'),
 ('canais_loja')
),
objects as (
 select r.name, c.oid, c.relrowsecurity, c.relforcerowsecurity
 from requested r
 left join pg_catalog.pg_namespace n on n.nspname='public'
 left join pg_catalog.pg_class c on c.relnamespace=n.oid
 and c.relname=r.name and c.relkind in ('r','p')
),
cells as (
 select o.name, coalesce(jsonb_agg(jsonb_build_object(
  'name',a.attname,
  'anon_select',pg_catalog.has_column_privilege('anon',o.oid,a.attname,'SELECT'),
  'authenticated_select',pg_catalog.has_column_privilege('authenticated',o.oid,a.attname,'SELECT')
 ) order by a.attnum) filter (where a.attname is not null),'[]'::jsonb) as cols
 from objects o
 left join pg_catalog.pg_attribute a on a.attrelid=o.oid
 and a.attnum>0 and not a.attisdropped
 group by o.name
),
policies as (
 select o.name,coalesce(jsonb_agg(jsonb_build_object(
   'name',p.polname,'command',p.polcmd,'permissive',p.polpermissive)
   order by p.polname) filter(where p.oid is not null),'[]'::jsonb) as policies
 from objects o left join pg_catalog.pg_policy p on p.polrelid=o.oid
 group by o.name
)
select jsonb_build_object(
 'tables', (select jsonb_agg(jsonb_build_object(
 'name',o.name,'exists',o.oid is not null,
 'rls_enabled',coalesce(o.relrowsecurity,false),
 'rls_forced',coalesce(o.relforcerowsecurity,false),
 'anon_select',case when o.oid is not null then
   pg_catalog.has_table_privilege('anon',o.oid,'SELECT') else false end,
 'authenticated_select',case when o.oid is not null then
   pg_catalog.has_table_privilege('authenticated',o.oid,'SELECT') else false end,
 'columns',ce.cols,'policies',po.policies
 ) order by o.name) from objects o
 join cells ce using(name) join policies po using(name)),
 'storage_objects_declared',to_regclass('storage.objects') is not null,
 'storage_buckets_declared',to_regclass('storage.buckets') is not null,
 'scope','PG17 ephemeral effective catalog after S0/S1 canonical regressions'
)::text
"""

def check_url(url):
    p=urlparse(url)
    db=unquote(p.path.lstrip("/"))
    if p.scheme not in ("postgres","postgresql") or p.hostname not in (
            "localhost","127.0.0.1","::1") or not db.startswith("prumo_s0_test_") \
       or p.fragment or p.query:
        raise ValueError("I75C_REFUSES_REMOTE_OR_NON_EPHEMERAL_DB")
    return url

def validate(report):
    tables=report.get("tables")
    if not isinstance(tables,list) or {x.get("name") for x in tables}!=set(EXPECTED):
        raise ValueError("I75C_UNEXPECTED_RELATION_SET")
    for table in tables:
        name=table["name"]
        if not table.get("exists") or not table.get("rls_enabled"):
            raise ValueError("I75C_MISSING_RLS:"+name)
        if table.get("anon_select"):
            raise ValueError("I75C_ANON_TABLE_READ:"+name)
        cols=table.get("columns",[])
        indexed={c["name"]:c for c in cols}
        if not set(EXPECTED[name]).issubset(indexed):
            raise ValueError("I75C_REQUIRED_COLUMN_DRIFT:"+name)
        if any(c.get("anon_select") for c in cols):
            raise ValueError("I75C_ANON_COLUMN_LEAK:"+name)
        if any(p["name"].startswith("s1_63_canon_") for p in table.get("policies",[])):
            raise ValueError("I75C_TEST_POLICY_PERSISTED:"+name)
    # Probe the exact two sensitive synthetic columns, never sample their values.
    for table,cols in SENSITIVE.items():
        found={x["name"] for x in next(x for x in tables if x["name"]==table)["columns"]}
        if not cols.issubset(found):
            raise ValueError("I75C_SENSITIVE_COLUMN_DRIFT:"+table)
    return {
      "tables":len(tables),
      "rls_enabled":sum(bool(t["rls_enabled"]) for t in tables),
      "anon_selectable":sum(bool(t["anon_select"]) for t in tables),
      "authenticated_selectable":sum(bool(t["authenticated_select"]) for t in tables),
      "sensitive_columns_tested":sum(len(x) for x in SENSITIVE.values()),
      "media_contract_verified":False,"d3_d4_column_contract_verified":False,
      "runtime_authorization_verified":False,
    }

def main():
    if os.environ.get("CI")!="true" or not os.getenv("PRUMO_TEST_DATABASE_URL"):
        raise SystemExit("I75C_REQUIRES_DISPOSABLE_CI_DB")
    url=check_url(os.environ["PRUMO_TEST_DATABASE_URL"])
    res=subprocess.run(["psql","-X","-A","-t","-v","ON_ERROR_STOP=1",url,
                        "-c",QUERY],check=True,capture_output=True,text=True,timeout=30)
    data=json.loads(res.stdout.strip())
    metrics=validate(data)
    data["verification"]=metrics
    data["warning"]="STATIC ACCESS CATALOG ONLY: no media/download or D3/D4 authorization"
    dest=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"s1_002_i75c_pg17_g3_effective_catalog.json"
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PASS I75C-01: {metrics['tables']}/11 canonical tables present with RLS enabled")
    print("PASS I75C-02: anon denied SELECT at relation and column level across G3")
    print("PASS I75C-03: test-only I63 RLS policies absent from persisted candidate baseline")
    print("PASS I75C-04: protected synthetic contact and message columns catalogued")
    print("I75C MEDIA/D3/D4 UNVERIFIED: actual object/column contracts require S0 review")
    print("I75C artifact:",dest)

if __name__=="__main__":
    main()
