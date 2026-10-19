#!/usr/bin/env bash
# Starts and DESTROYS its own PostgreSQL 17 cluster. No existing cluster, no TCP.
set -euo pipefail
if [[ $# -ne 0 ]]; then echo 'WA06D: no connection arguments accepted' >&2; exit 64; fi
if [[ "$(id -u)" -eq 0 ]]; then echo 'WA06D: run as an unprivileged user, never root' >&2; exit 77; fi
if ! command -v pg_config >/dev/null 2>&1; then echo 'WA06D: PostgreSQL 17 unavailable' >&2; exit 69; fi
pg_bin="$(pg_config --bindir)"
for tool in initdb pg_ctl postgres createdb psql; do
  if [[ ! -x "$pg_bin/$tool" ]]; then echo "WA06D: missing $tool" >&2; exit 69; fi
done
if [[ "$("$pg_bin/postgres" --version)" != PostgreSQL\ 17.* ]]; then
  echo 'WA06D: only PostgreSQL 17 supported' >&2; exit 69
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for file in wa06d_pg17_atomicity.sql wa06d_pg17_postcommit_setup.sql wa06d_pg17_postcommit_verify.sql; do
  if [[ ! -f "$script_dir/$file" ]]; then echo "WA06D: missing $file" >&2; exit 66; fi
done
# PGHOSTADDR overrides PGHOST even with explicit -h. No inherited remote connection setup.
unset PGHOSTADDR PGHOST PGPORT PGDATABASE PGUSER PGSERVICE PGSERVICEFILE PGOPTIONS PGSSLMODE PGSSLCERT PGSSLKEY PGSSLROOTCERT
sandbox="$(mktemp -d /tmp/wa06d_pg17_XXXXXXXX)"
cluster="$sandbox/cluster"
sock="$sandbox/socket"
mkdir -m 700 "$sock"
start_attempted=false
cleanup() {
  original_status=$?
  trap - EXIT
  if [[ "$start_attempted" == true ]]; then
    # A failed pg_ctl start may still have spawned postgres: ALWAYS attempt stop.
    "$pg_bin/pg_ctl" -D "$cluster" -m fast -w stop >/dev/null 2>&1 || :
    if "$pg_bin/pg_ctl" -D "$cluster" status >/dev/null 2>&1; then
      echo "WA06D CRITICAL: cluster may still be running; preserving $sandbox for safe manual inspection" >&2
      exit 70
    fi
  fi
  if [[ -n "${sandbox:-}" && "$sandbox" == /tmp/wa06d_pg17_* && -d "$sandbox" ]]; then
    rm -rf -- "$sandbox"
  fi
  exit "$original_status"
}
trap cleanup EXIT
"$pg_bin/initdb" -D "$cluster" -A trust -U wa06d_owner --no-instructions >"$sandbox/initdb.log" 2>&1
start_attempted=true
"$pg_bin/pg_ctl" -D "$cluster" -o "-c listen_addresses='' -c unix_socket_directories='$sock' -c port=54339" \
  -l "$sandbox/postgres.log" -w start >/dev/null
"$pg_bin/createdb" -h "$sock" -p 54339 -U wa06d_owner wa06d_test_ephemeral
for file in wa06d_pg17_atomicity.sql wa06d_pg17_postcommit_setup.sql wa06d_pg17_postcommit_verify.sql; do
  "$pg_bin/psql" -X -v ON_ERROR_STOP=1 -h "$sock" -p 54339 -U wa06d_owner -d wa06d_test_ephemeral -f "$script_dir/$file"
done
printf '%s\n' 'WA06D: all PostgreSQL 17 scripts returned exit code 0; ephemeral cluster will be deleted'
