#!/bin/bash
set -euo pipefail
bash scripts/run-s1-002-local.sh
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610190049_s1_movimento_manual_por_equipe.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s1_012_movimento_manual_equipe.sql
