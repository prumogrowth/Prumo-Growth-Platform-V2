#!/usr/bin/env bash
# Offline-only, zero-install TypeScript regression runner for the Meta adapter.
# This script does not start servers, send messages or connect external APIs.
set -euo pipefail
# Block inherited runtime preloads before the first Node invocation.
export NODE_OPTIONS='' NODE_PATH=''
LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:---all}"
if [[ $# -gt 1 ]]; then
  echo 'Usage: run-offline-tests.sh [--unit|--binding|--focus|--all]' >&2
  exit 64
fi
if ! command -v node >/dev/null 2>&1; then
  echo 'Node.js 22+ required; not installing dependencies' >&2
  exit 69
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [[ ! "$NODE_MAJOR" =~ ^[0-9]+$ ]] || (( NODE_MAJOR < 22 )); then
  echo 'Node.js 22+ required for TypeScript strip-types' >&2
  exit 69
fi
case "$MODE" in
  --unit) files=("$LAB_DIR/status-evidence.test.ts") ;;
  --binding) files=("$LAB_DIR/attempt-binding.test.ts") ;;
  --focus) files=("$LAB_DIR/attempt-binding.test.ts"
                   "$LAB_DIR/status-evidence.test.ts"
                   "$LAB_DIR/technical-reconciliation.test.ts"
                   "$LAB_DIR/graph-outbound.test.ts") ;;
  --all)
    files=("$LAB_DIR"/*.test.ts)
    # A partial checkout must not masquerade as a full Meta regression.
    if (( ${#files[@]} < 27 )); then
      echo 'Incomplete Meta test checkout: expected at least 27 suites' >&2
      exit 66
    fi
    for mandatory in attempt-binding status-evidence technical-reconciliation inbound graph-outbound \
        routed-webhook s0-ingress-gateway; do
      if [[ ! -f "$LAB_DIR/$mandatory.test.ts" ]]; then
        echo "Missing mandatory Meta suite: $mandatory.test.ts" >&2
        exit 66
      fi
    done
    ;;
  *) echo 'Usage: run-offline-tests.sh [--unit|--binding|--focus|--all]' >&2; exit 64 ;;
esac
for file in "${files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing offline test: $file" >&2
    exit 66
  fi
done
# The test files are fixtures; no npm install, API calls, secrets or CI run.
cd "$LAB_DIR/../.."
node --experimental-strip-types --test --test-concurrency=1 "${files[@]}"
