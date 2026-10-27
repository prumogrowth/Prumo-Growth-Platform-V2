#!/usr/bin/env bash
# Fail-closed preflight for disposable S0 PostgreSQL regression only.
# Does NOT create schemas, issue Graph requests, or connect to hosted Supabase.
set -euo pipefail
: "${PRUMO_TEST_DATABASE_URL:?Defina uma URL LOCAL descartavel prumo_s0_test_*}"

expected_db="$(python3 - <<'PY'
import os, re, sys
from urllib.parse import urlparse, unquote
u = urlparse(os.environ['PRUMO_TEST_DATABASE_URL'])
name = unquote(u.path[1:]) if u.path.startswith('/') else ''
if (u.scheme not in ('postgres', 'postgresql')
    or u.hostname not in ('localhost', '127.0.0.1', '::1')
    or not re.fullmatch(r'prumo_s0_test_[a-z0-9_]{1,40}', name)
    or u.query or u.fragment or u.params):
    sys.exit('RECUSADO: exige PostgreSQL local descartavel prumo_s0_test_*')
print(name)
PY
)"

# libpq can override an otherwise safe URL via environmental settings.
unset PGHOSTADDR PGHOST PGPORT PGDATABASE PGUSER PGSERVICE PGSERVICEFILE PGOPTIONS PGSSLMODE PGSSLCERT PGSSLKEY PGSSLROOTCERT
if ! command -v psql >/dev/null 2>&1; then
  echo 'BLOQUEADO: psql ausente; instale PostgreSQL 17 apenas em ambiente isolado.' >&2
  exit 69
fi

# Read-only server introspection, before the first S0 migration is applied.
# Never print credentials/DSNs or the raw psql response in diagnostics.
if ! identity="$(psql -X -qAt -v ON_ERROR_STOP=1 \
  "$PRUMO_TEST_DATABASE_URL" \
  -c "select current_setting('server_version_num') || '|' || current_database()")"; then
  echo 'BLOQUEADO: nao foi possivel consultar o PostgreSQL local de testes.' >&2
  exit 69
fi
IFS='|' read -r version observed_db <<< "$identity"
if [[ ! "$version" =~ ^17[0-9]{4}$ || "$observed_db" != "$expected_db" ]]; then
  echo 'RECUSADO: servidor PostgreSQL diferente de 17 ou banco diferente do alvo descartavel.' >&2
  exit 65
fi
echo 'PASS S0-PG17-PREFLIGHT: PostgreSQL 17 e banco descartavel confirmados (somente leitura).'
