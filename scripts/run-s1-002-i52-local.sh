#!/usr/bin/env bash
# S0+S1 canonical I52/053 stage, applied after legacy migrations/tests.
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?Local disposable database required}"
python3 - <<'PY'
import os,sys
from urllib.parse import urlparse,unquote
u=urlparse(os.environ["PRUMO_TEST_DATABASE_URL"])
if u.scheme not in ("postgres","postgresql") or u.hostname not in ("localhost","127.0.0.1","::1") or not unquote(u.path.strip("/")).startswith("prumo_s0_test_"):
    sys.exit("I52 canonical runner refuses remote or non-ephemeral SQL")
PY
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190053_s0_s1_intake_atribuicao_guard.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_076_integracao_intake_canonico_aceite.sql
bash scripts/test_s1_002_i52_intake_race.sh
# I54: real S0 lead/cycle signal, queue CAS and canonical assignment.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190054_s0_fila_humana_canonica.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_078_fila_s0_canonica_aceite.sql
echo "PASS S0+S1 I52-I54 canonical stages after legacy regression"
