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
echo 'S1-002/I1+I2+I3 e concorrencia sintética; apenas PostgreSQL local descartável.'
