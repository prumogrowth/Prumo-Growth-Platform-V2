#!/usr/bin/env bash
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?Defina URL LOCAL prumo_s0_test_*}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$ROOT/scripts/run-s0-local.sh"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/migrations/202610180038_s1_equipe_prumo_gate.sql"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/tests/s1_002_equipe_prumo_gate.sql"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/migrations/202610180039_s1_remanejamento_transacional.sql"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/tests/s1_002_remanejamento_transacional.sql"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/migrations/202610180040_s1_concessoes_expiradas_reconciliacao.sql"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/tests/s1_003_concessoes_expiradas.sql"
bash "$ROOT/scripts/test_s1_002_concurrency.sh"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/migrations/202610180041_s1_prevenir_deadlock_remanejamento.sql"
# Reexecutar suites transacionais apos a substituicao da funcao I2, para provar regressao.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/tests/s1_002_remanejamento_transacional.sql"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$ROOT/supabase/tests/s1_003_concessoes_expiradas.sql"
bash "$ROOT/scripts/test_s1_002_simultaneous_suspensions.sh"
echo 'S1-002/I1–I5 sintético e concorrência; apenas PostgreSQL local descartável.'
