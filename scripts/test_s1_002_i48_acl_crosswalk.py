#!/usr/bin/env python3
"""I48 source-only crosswalk of S0/013-037; never infer effective ACL from regex."""
import json
import os
from pathlib import Path
import re

root=Path(__file__).resolve().parent.parent
files=[]
for p in sorted((root/"supabase/migrations").glob("*.sql")):
    m=re.match(r"20\d{6}(\d{4})_",p.name)
    if m and 13<=int(m.group(1))<=37 and "_s1_" not in p.name:
        files.append(p)
if len(files)<20:
    raise AssertionError("I48 missing S0 source migrations")
matrix=[]
for p in files:
    source="\n".join(x.split("--",1)[0] for x in p.read_text(encoding="utf-8").splitlines())
    funcs=re.findall(r"\bcreate\s+(?:or\s+replace\s+)?function\s+([\w.]+)",source,re.I)
    tables=re.findall(r"\bcreate\s+table\s+([\w.]+)",source,re.I)
    policies=re.findall(r"\bcreate\s+policy\s+([\w]+)\s+on\s+([\w.]+)",source,re.I)
    matrix.append({"migration":p.name,"functions":funcs,"tables":tables,
        "policies":[{"name":a,"relation":b} for a,b in policies],
        "security_definer_declarations":len(re.findall(r"\bsecurity\s+definer\b",source,re.I)),
        "contains_store_grant_context":bool(re.search(r"\bvinculos_papel_escopo\b",source,re.I))})
pol={row['name'] for x in matrix for row in x['policies']}
if not {"elegibilidade_select_gestor","supressoes_select_gestor"}.issubset(pol):
    raise AssertionError("I48 S0/016 legacy shop-grant policies changed")
if sum(x['security_definer_declarations'] for x in matrix)<4:
    raise AssertionError("I48 gateway SECURITY DEFINER declarations missing")
dest=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"s1_002_i48_crosswalk.json"
dest.write_text(json.dumps({"scope":"lexical S0/013-037 source; not effective privileges",
                            "files":len(files),"matrix":matrix},indent=2,ensure_ascii=False)+"\n",
                encoding="utf-8")
print(f"PASS I48-SOURCE: {len(files)} migration files, "
      f"{sum(len(x['functions']) for x in matrix)} function declarations, "
      f"{sum(len(x['tables']) for x in matrix)} table declarations, "
      f"{sum(x['security_definer_declarations'] for x in matrix)} definer declarations")
print("I48 crosswalk:",dest)
