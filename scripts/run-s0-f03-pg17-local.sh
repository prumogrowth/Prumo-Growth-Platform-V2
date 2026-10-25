#!/usr/bin/env bash
# Manual-only extension of the S0 CFI-01 runner. Never hosted Supabase.
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?Use dedicated disposable local PG17 S0 URL}"
python3 - <<'PY'
import os,urllib.parse
u=urllib.parse.urlsplit(os.environ['PRUMO_TEST_DATABASE_URL'])
assert (u.scheme in ('postgres','postgresql')
        and u.hostname in ('127.0.0.1','localhost','::1')
        and u.path == '/prumo_s0_test_cfi01'
        and not u.query and not u.fragment), 'ONLY_DISPOSABLE_S0_PG17'
assert not any(os.environ.get(name) for name in (
  'PGHOSTADDR','PGHOST','PGPORT','PGDATABASE','PGUSER','PGSERVICE',
  'PGSERVICEFILE','PGOPTIONS','PGSSLMODE','PGSSLCERT','PGSSLKEY',
  'PGSSLROOTCERT')), 'AMBIENT_LIBPQ_OVERRIDE_DENIED'
PY
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# The preexisting runner bootstraps the disposable DB and exercises the physical
# S0/S1 closure contract, including GoTrue mock and S0 HMAC/nonce/PG guards.
bash scripts/run-s0-cfi01-pg17-local.sh
server_version="$(psql -X -A -t -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -c 'show server_version_num')"
case "$server_version" in
  17????) ;; # only PostgreSQL 17
  *) echo "F03 REQUIRES LOCAL PG17; got $server_version" >&2; exit 1 ;;
esac
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_alias_lab_roles_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/migrations/202610180028_s0_identidade_aliases_sinteticos.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_history_seal_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_versions_reservation_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_version_source_triggers_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_identity_alias_version_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_identity_human_review_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_identity_ratification_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_identity_resolution_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_identity_scope_serialization_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_operational_contracts_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_field_application_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_message_modalities_local_only.sql
psql -X -v ON_ERROR_STOP=1 "$PRUMO_TEST_DATABASE_URL" -f supabase/tests/s0_f03_media_attestation_local_only.sql
python3 -m unittest backend.tests.test_s0_f03_history_manifest_local \
  backend.tests.test_s0_f03_history_seal_local \
  backend.tests.test_s0_f03_bound_content_seal_local \
  backend.tests.test_s0_f03_version_reservation_local \
  backend.tests.test_s0_f03_operational_contracts_local \
  backend.tests.test_s0_f03_field_application_local \
  backend.tests.test_s0_f03_crossfront_contract_local \
  backend.tests.test_s0_f03_crossfront_evidence_local \
  backend.tests.test_s0_f03_media_attestation_local \
  backend.tests.test_s0_f03_pg17_integration -v
