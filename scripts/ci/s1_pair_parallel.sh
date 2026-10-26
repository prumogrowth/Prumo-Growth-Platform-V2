#!/usr/bin/env bash
set -euo pipefail
umask 077
gate="${1:?I29 or I30 required}"
case "$gate" in
  I29) script=scripts/test_s1_002_i29_persistent_revocation_local.py ;;
  I30) script=scripts/test_s1_002_i30_signed_authority_local.py ;;
  *) exit 2 ;;
esac
: "${RUNNER_TEMP:?}" "${GITHUB_WORKSPACE:?}"
cd "$GITHUB_WORKSPACE"
evidence="$RUNNER_TEMP/ci-pair-$gate"
mkdir -p "$evidence"
workdir="$(mktemp -d)"
printf '%s\n' "$workdir" > "$RUNNER_TEMP/ci-pair-workdir-$gate"
stack_pid=''
cleanup() {
  local status=$?
  trap - EXIT
  if [ -n "$stack_pid" ]; then
    wait "$stack_pid" || true
  fi
  if ! (cd "$workdir" && supabase stop --no-backup); then
    echo "Stack cleanup failed for $gate" >&2
    status=1
  fi
  rm -f "$RUNNER_TEMP/ci-pair-$gate.env"
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
started="$(date +%s)"
(cd "$workdir" && supabase init && supabase start --exclude studio,realtime,storage-api,imgproxy,postgres-meta,edge-runtime,logflare,vector,supavisor) > "$RUNNER_TEMP/$gate-start.log" 2>&1 &
stack_pid=$!
unit_status=0
PYTHONPATH=. python3 scripts/ci/s1_pair_evidence.py unit "$gate" "$evidence" > "$evidence/unit.log" 2>&1 || unit_status=$?
cat "$evidence/unit.log"
stack_status=0
wait "$stack_pid" || stack_status=$?
stack_pid=''
if [ "$unit_status" -ne 0 ] || [ "$stack_status" -ne 0 ]; then
  echo "Failed: $gate units=$unit_status stack=$stack_status (startup log in runner temporary directory)" >&2
  exit 1
fi
ready="$(date +%s)"
(cd "$workdir" && supabase status -o env) > "$RUNNER_TEMP/ci-pair-$gate.env"
test -s "$RUNNER_TEMP/ci-pair-$gate.env"
set -a
source "$RUNNER_TEMP/ci-pair-$gate.env"
set +a
export "PRUMO_S1_${gate}_EPHEMERAL=YES"
PYTHONPATH=. python3 "$script" > "$RUNNER_TEMP/$gate-e2e.log" 2>&1 || {
  echo "E2E $gate failed; displaying last 60 log lines" >&2
  tail -60 "$RUNNER_TEMP/$gate-e2e.log"
  exit 1
}
PYTHONPATH=. python3 scripts/ci/s1_pair_evidence.py e2e "$gate" "$evidence"
finished="$(date +%s)"
printf '%s setup_and_units_seconds=%s e2e_seconds=%s\n' "$gate" "$((ready-started))" "$((finished-ready))" | tee "$evidence/timing.txt"
cat "$evidence/timing.txt" >> "$GITHUB_STEP_SUMMARY"
