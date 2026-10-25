"""I67 static consumer inventory, fail-closed on new legacy SQL facade users.

Check the actual checked-out branch in disposable CI; no network/deploy.
This cannot prove dynamic SQL/text generated outside repository.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=("prumo_s1_interface","s1_mover_atendimento_sessao",
       "s1_pausar_operador_sessao","s1_reativar_operador_sessao")
SUFFIX={".py",".sql",".sh",".ts",".tsx",".js",".jsx"}
# Known retired I19 adapter remains importable in the test branch.
# Explicitly inventory it rather than misreporting zero legacy source code.
RETIRED_ADAPTER="backend/s1_gateway_local.py"
ADAPTER_IMPORTS=("backend.s1_gateway_local","LocalTeamGateway")
HISTORY={
 "supabase/migrations/202610190051_s1_sessao_autorizacao_privada.sql",
 "supabase/migrations/202610190052_s1_verificacao_sessao_gotrue.sql",
}
allowed=[]
consumer=[]
retired=[]
for f in ROOT.rglob("*"):
 if not f.is_file() or f.suffix not in SUFFIX or ".git" in f.parts:
  continue
 rel=f.relative_to(ROOT).as_posix()
 if rel==Path(__file__).relative_to(ROOT).as_posix(): continue
 data=f.read_text(encoding="utf-8",errors="replace")
 names=[name for name in NAMES+ADAPTER_IMPORTS if name in data]
 if not names: continue
 if rel==RETIRED_ADAPTER:
  # This is a historical loopback-only implementation, NOT a cleared
  # runtime consumer. Removing its SQL ACL in I66 makes calls fail closed.
  if not ('SOMENTE LOCAL' in data and
          'parsed.username != "prumo_s1_gateway_ci"' in data and
          'ThreadingHTTPServer(("127.0.0.1", 0), Handler)' in data):
   consumer.append((rel,"RETIRED_ADAPTER_CHANGED_SECURITY_CONTRACT"))
  else:retired.append((rel,",".join(names)))
 elif rel in HISTORY or rel.startswith("supabase/tests/") or rel.startswith("tests/") or (
   rel.startswith("scripts/test_") and rel.endswith(".py")):
  allowed.append((rel,",".join(names)))
 else:consumer.append((rel,",".join(names)))
for path,names in sorted(allowed):
 print("I67-HISTORICAL_REFERENCE",path,names)
for path,names in sorted(retired):
 print("I67-RETIRED_LOCAL_ADAPTER",path,names)
for path,names in sorted(consumer):
 print("I67-UNREVIEWED_RUNTIME_CONSUMER",path,names)
if consumer or len(retired)!=1:
 raise SystemExit("I67_UNREVIEWED_RUNTIME_DEPENDENCY_OR_RETIRED_ADAPTER_DRIFT")
print(f"PASS I67-SCAN-01: zero unreviewed runtime consumers; one explicit retired loopback adapter; {len(allowed)} archived/test references inventoried")
