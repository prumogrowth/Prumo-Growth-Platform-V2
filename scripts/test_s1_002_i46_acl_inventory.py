#!/usr/bin/env python3
"""I46 source-only ACL inventory for all tracked SQL migrations.

No network, Supabase credentials, or customer data. This is lexical discovery:
SQL catalog + real-auth tests remain necessary to establish effective grants.
The script fails when required historical risk surfaces disappear from the scan,
not when it finds still-unresolved legacy risks.
"""
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
MIG=ROOT/"supabase"/"migrations"
files=sorted(MIG.glob("*.sql"))
if not files:
    raise SystemExit("I46: no migrations discovered")

relations=set()
rls=set()
all_policies=[]
defs=[]
grants=[]
views=[]
sources=[]
warnings=[]
def clean(src):
    return "\n".join(line.split("--",1)[0] for line in src.splitlines())

for f in files:
    src=clean(f.read_text(encoding="utf-8"))
    tables=re.findall(r"\bcreate\s+(?:unlogged\s+)?table\s+(?:if\s+not\s+exists\s+)?((?:public|prumo_private)\.[a-z_0-9]+)",src,re.I)
    rels=[x.lower() for x in tables]
    relations.update(rels)
    rls.update(x.lower() for x in re.findall(r"\balter\s+table\s+((?:public|prumo_private)\.[a-z_0-9]+)\s+enable\s+row\s+level\s+security",src,re.I))
    policies=[(a.lower(),b.lower()) for a,b in re.findall(r"\bcreate\s+policy\s+([a-z_0-9]+)\s+on\s+((?:public|prumo_private)\.[a-z_0-9]+)",src,re.I)]
    all_policies.extend((str(f.relative_to(ROOT)),a,b) for a,b in policies)
    views.extend((str(f.relative_to(ROOT)),v.lower()) for v in re.findall(r"\bcreate\s+(?:or\s+replace\s+)?view\s+((?:public|prumo_private)\.[a-z_0-9]+)",src,re.I))
    fn=list(re.finditer(r"\bcreate\s+(?:or\s+replace\s+)?function\s+((?:public|prumo_private)\.[a-z_0-9]+)\s*\(",src,re.I))
    for idx,m in enumerate(fn):
        # The signature/prelude extends up to its dollar-quoted body.
        decl=src[m.end():m.end()+800].split(" as $",1)[0].lower()
        defs.append({"file":f.name,"function":m.group(1).lower(),
                     "security_definer":bool(re.search(r"\bsecurity\s+definer\b",decl)),
                     "search_path_explicit":bool(re.search(r"\bset\s+search_path\b",decl))})
    grant_statements=re.findall(r"\bgrant\b[^;]{0,2000};",src,re.I|re.S)
    for g in grant_statements:
        if re.search(r"\bto\s+(authenticated|anon|public|service_role)\b",g,re.I):
            grants.append({"file":f.name,"sql":re.sub(r"\s+"," ",g).strip()[:250]})
    if re.search(r"\bcreate\s+policy\b",src,re.I) and "vinculos_papel_escopo" in src:
        warnings.append({"file":f.name,"category":"store_grant_in_policy","severity":"manual-review"})
    sources.append({"path":str(f.relative_to(ROOT)),"tables":len(tables),
                    "policies":len(policies),"functions":len(fn),"grants":len(grant_statements)})

policy_names={p[1] for p in all_policies}
expected={"leads_select_gestor_loja","ciclos_select_gestor_loja",
          "lotes_select_gestor","itens_select_gestor",
          "reencontros_select_gestor","eventos_status_select_gestor"}
missing=expected-policy_names
if missing:
    raise SystemExit("I46 inventory assumptions changed: "+",".join(sorted(missing)))
if not {"public.lotes_importacao","public.itens_lote",
        "public.reencontros_lote","public.eventos_status_comercial"}.issubset(relations):
    raise SystemExit("I46 inventory: missing expected S0 D2 relations")
data={"scope":"static tracked migrations only; not effective PostgreSQL privileges",
      "files":len(files),"tables_created":sorted(relations),
      "rls_enabled_in_migrations":sorted(rls),
      "create_policy": [{"file":p[0],"name":p[1],"relation":p[2]} for p in all_policies],
      "views":views,"functions":defs,"grants_to_client_roles":grants,
      "store_grant_policy_candidates":warnings,
      "missing_rls_in_creation_scan":sorted(relations-rls),"per_file":sources}
dest=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"s1_002_i46_acl_inventory.json"
dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"PASS I46-STATIC-01: scanned {len(files)} tracked migrations / "
      f"{len(relations)} created tables / {len(all_policies)} policy declarations")
print(f"PASS I46-STATIC-02: recorded {len(defs)} function declarations, "
      f"{sum(d['security_definer'] for d in defs)} SECURITY DEFINER declarations, "
      f"{len(views)} views and {len(grants)} client-role GRANT statements")
print(f"PASS I46-STATIC-03: known six S0 shop-grant read policies located; "
      "review warnings are not production authorization")
print("I46 inventory JSON: "+str(dest))
