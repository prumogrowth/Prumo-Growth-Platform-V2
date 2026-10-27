#!/usr/bin/env bash
# Offline-only tests of PostgreSQL preflight. Synthetic psql, no DB/network.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT
mkdir -p "$temp/mock-bin" "$temp/no-psql-bin"
ln -s "$(command -v bash)" "$temp/no-psql-bin/bash"
ln -s "$(command -v python3)" "$temp/no-psql-bin/python3"
cat > "$temp/mock-bin/psql" <<'MOCK'
#!/usr/bin/env bash
if [[ -n "${PGHOSTADDR:-}" || -n "${PGSERVICE:-}" ]]; then
  echo 'unsafe inherited libpq scope' >&2; exit 77
fi
if [[ "$*" != *server_version_num* || "$*" != *current_database* ]]; then
  echo 'not a read-only server/database preflight' >&2; exit 78
fi
if [[ "${MOCK_ERROR:-0}" == 1 ]]; then exit 22; fi
printf '%s|%s\n' "${MOCK_PG_VERSION:-170006}" "${MOCK_PG_DB:-prumo_s0_test_ci}"
MOCK
chmod 700 "$temp/mock-bin/psql"

readonly base_path='/usr/bin:/bin'
readonly test_path="$temp/mock-bin:$base_path"
readonly target='postgresql://postgres:fixture@127.0.0.1:5432/prumo_s0_test_ci'
readonly helper="$ROOT/scripts/check_s0_pg17.sh"
number=0
expect_exit() {
  local description="$1" wanted="$2" output actual
  shift 2
  actual=0
  output="$("$@" 2>&1)" || actual="$?"
  if [[ "$actual" != "$wanted" ]]; then
    printf 'FAIL %-32s wanted %s got %s: %s\n' "$description" "$wanted" "$actual" "$output" >&2
    exit 1
  fi
  number=$((number + 1))
  printf 'PASS %-32s exit %s\n' "$description" "$actual"
}

expect_exit 'exact PG17 + disposable DB' 0 env -i PATH="$test_path" PRUMO_TEST_DATABASE_URL="$target" bash "$helper"
expect_exit 'reject PG16 server' 65 env -i PATH="$test_path" MOCK_PG_VERSION=160015 PRUMO_TEST_DATABASE_URL="$target" bash "$helper"
expect_exit 'reject other DB' 65 env -i PATH="$test_path" MOCK_PG_DB=prumo_s0_test_other PRUMO_TEST_DATABASE_URL="$target" bash "$helper"
expect_exit 'reject remote host' 1 env -i PATH="$test_path" PRUMO_TEST_DATABASE_URL='postgresql://postgres:fixture@db.example.org:5432/prumo_s0_test_ci' bash "$helper"
expect_exit 'reject URL hostaddr' 1 env -i PATH="$test_path" PRUMO_TEST_DATABASE_URL='postgresql://postgres:fixture@localhost:5432/prumo_s0_test_ci?hostaddr=1.2.3.4' bash "$helper"
expect_exit 'reject production DB' 1 env -i PATH="$test_path" PRUMO_TEST_DATABASE_URL='postgresql://postgres:fixture@localhost:5432/production' bash "$helper"
expect_exit 'strip libpq overrides' 0 env -i PATH="$test_path" PGHOSTADDR=8.8.8.8 PGSERVICE=production PRUMO_TEST_DATABASE_URL="$target" bash "$helper"
expect_exit 'reject server failure' 69 env -i PATH="$test_path" MOCK_ERROR=1 PRUMO_TEST_DATABASE_URL="$target" bash "$helper"
expect_exit 'reject absent psql' 69 env -i PATH="$temp/no-psql-bin" PRUMO_TEST_DATABASE_URL="$target" bash "$helper"
expect_exit 'reject malformed PG version' 65 env -i PATH="$test_path" MOCK_PG_VERSION='17xxx' PRUMO_TEST_DATABASE_URL="$target" bash "$helper"
printf '%s\n' "PASS S0-PG17-PREFLIGHT-TEST: $number/10 synthetic cases (not a real PostgreSQL test)"
