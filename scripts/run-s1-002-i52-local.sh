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
# I54: two independent-session races on the canonical queue; disposable DB.
bash scripts/test_s1_002_i54_fila_race.sh
# I56 case reconciliation and real two-session concurrency
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190055_s0_fila_reconciliacao_casos.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_080_fila_reconciliacao_aceite.sql
bash scripts/test_s1_002_i56_reconciliacao_race.sh
# I57: grant after-lock revalidation at canonical S0 assignment boundary
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190056_s0_s1_grant_atribuicao_guard.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_081_atribuicao_grant_i57_aceite.sql
bash scripts/test_s1_002_i57_grant_race.sh
# I58 manager lock and grant revalidation before LIST and claim-CAS
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190057_s0_fila_gestor_revalidacao.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_082_fila_gestor_autorizacao_aceite.sql
bash scripts/test_s1_002_i58_fila_gestor_race.sh
# I59 canonical S0 conversation must reference same case contact/store
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190058_s0_conversa_integridade_contato.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_083_integridade_conversas_i59_aceite.sql
echo "PASS S0+S1 I52-I59 canonical stages after legacy regression"
