#!/usr/bin/env bash
# WA-06D/A: explicitly local, disposable PG17 only; no hosted / remote connections.
set -euo pipefail
if [[ $# -ne 1 || ! "$1" =~ ^wa06d_test_[a-z0-9_]{1,40}$ ]]; then
  echo 'DENIED: provide one disposable DB named wa06d_test_<suffix>' >&2
  exit 64
fi
if ! command -v psql >/dev/null 2>&1; then
  echo 'DENIED: PostgreSQL psql is unavailable; no SQL was executed' >&2
  exit 69
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Pin TCP to loopback and override any ambient PG service/URI selectors.
export PGSERVICE='' PGHOST='127.0.0.1' PGPORT='5432' PGDATABASE="$1"
exec psql -X -v ON_ERROR_STOP=1 -h 127.0.0.1 -p 5432 -d "$1" \
  -f "$script_dir/wa06d_pg17_atomicity.sql"
