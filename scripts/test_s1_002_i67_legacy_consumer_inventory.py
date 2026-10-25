"""I67 static consumer inventory, fail-closed on new legacy SQL facade users.

Check the actual checked-out branch in disposable CI; no network/deploy.
This cannot prove dynamic SQL/text generated outside repository.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=("prumo_s1_interface","s1_mover_atendimento_sessao",
       "s1_pausar_operador_sessao","s1_reativar_operador_sessao")
SUFFIX={".py",".sql",".sh",".ts",".tsx",".js",".jsx"}
HISTORY={
 "supabase/migrations/202610190051_s1_sessao_autorizacao_privada.sql",
 "supabase/migrations/202610190052_s1_verificacao_sessao_gotrue.sql",
}
allowed=[]
consumer=[]
for f in ROOT.rglob("*"):
 if not f.is_file() or f.suffix not in SUFFIX or ".git" in f.parts:
  continue
 rel=f.relative_to(ROOT).as_posix()
 if rel==Path(__file__).relative_to(ROOT).as_posix(): continue
 data=f.read_text(encoding="utf-8",errors="replace")
 names=[name for name in NAMES if name in data]
 if not names: continue
 if rel in HISTORY or rel.startswith("supabase/tests/") or rel.startswith("tests/") or (
   rel.startswith("scripts/test_") and rel.endswith(".py")):
  allowed.append((rel,",".join(names)))
 else:consumer.append((rel,",".join(names)))
for path,names in sorted(allowed):
 print("I67-HISTORICAL_REFERENCE",path,names)
for path,names in sorted(consumer):
 print("I67-UNREVIEWED_RUNTIME_CONSUMER",path,names)
if consumer:raise SystemExit("I67_RUNTIME_LEGACY_FACADE_REFERENCE_DENIED")
print(f"PASS I67-SCAN-01: zero runtime source references; {len(allowed)} archived/test references inventoried")
