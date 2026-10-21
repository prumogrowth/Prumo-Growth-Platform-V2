#!/usr/bin/env bash
# CFI-01 physical PostgreSQL check. NEVER run against a hosted Supabase DB.
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?Set disposable local test PostgreSQL URL}"
python3 - <<'PY'
import os, urllib.parse
u=urllib.parse.urlsplit(os.environ["PRUMO_TEST_DATABASE_URL"])
assert (u.scheme in ("postgres","postgresql") and
        u.hostname in ("127.0.0.1","localhost","::1") and
        u.path == "/prumo_s0_test_cfi01" and not u.query and not u.fragment), "LOCAL_DB_ONLY"
assert not any(os.environ.get(k) for k in (
    "PGHOSTADDR","PGHOST","PGPORT","PGDATABASE","PGUSER","PGSERVICE",
    "PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY",
    "PGSSLROOTCERT")), "AMBIENT_LIBPQ_OVERRIDE_DENIED"
PY
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/bootstrap_fake_auth.sql
# auth.sessions is a test-only stand-in; actual production sessions are GoTrue-owned.
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c '
 create table auth.sessions(
    id uuid primary key,
    user_id uuid not null references auth.users(id) on delete cascade
 );'
# Minimal existing physical S0 domain with existing S1 normal-team gate.
# Apply in dependency order, never use a fixture as a hosted migration.
for file in \
  supabase/migrations/202610170001_s0_foundation.sql \
  supabase/migrations/202610170002_s0_read_policies.sql \
  supabase/migrations/202610170003_s0_domain.sql \
  supabase/migrations/202610170004_s0_access.sql \
  supabase/migrations/202610170005_s0_scope_integrity.sql \
  supabase/migrations/202610170006_s0_transactional_simulation.sql \
  supabase/migrations/202610170008_s0_lead_operador_caso.sql \
  supabase/tests/s0_cfi01_s1_038_reference_local_only.sql \
  supabase/tests/s0_cfi01_human_closure_table_local_only.sql \
  supabase/tests/s0_cfi01_signed_prerequisite_local_only.sql \
  supabase/tests/s0_cfi01_atomic_owner_local_only.sql
do
    psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f "$file"
done
python3 -m unittest backend.tests.test_s0_cfi01_pg17_integration -v
