# CFI-01 integration fixture

The workflow `s0-cfi01-transactional.yml` checks out the original S0 CFI-01
runtime at `948891714f632adb6179cf3a11f362a6eb914f91` into a separate directory.
It overlays only the two communication modules and the new test. There is no
merge, cherry-pick, runtime replacement or change to the source branch.

It starts a fresh, unlinked Supabase CLI 2.84.2 PostgreSQL17/GoTrue/PostgREST
stack from that source's existing config. The original Auth/REST suite prepares
its existing schema; the original ten-scenario CFI-01 GoTrue suite installs the
original four SQL fixtures and exercises its existing capture/recheck. The new
tests then reuse the same real gateway and helpers, with their own synthetic
users, UUIDs, case and shop per test. No mock identity/opener is used.

`PRUMO_CFI01_TRANSACTIONAL_TEST=YES` is mandatory. The original local-env and
restricted-DSN checks reject remote origins; libpq ambient overrides are rejected
by the pinned runtime. No remote project is linked, no external API is called.
The workflow always stops its own disposable stack with `--no-backup`.

The code uses the source's fixed lab-only SQL password/key. They are test
fixtures, not live credentials, and must not be used outside disposable tests.
Admin SQL seeds/mutates test conditions; the adapter itself uses only the
existing restricted login and NOLOGIN fixture owner. The source's narrow
privileged session helper remains a lab dependency, not a production credential
architecture. S1 team/grants are physical reference fixtures, not the whole
latest S1 service. The UI contract and commercial changes remain out of scope.

To reproduce, use the same two checkouts/overlay steps as the workflow, install
the pinned original test requirements, and run these from the runtime directory:

```bash
supabase start --exclude realtime,storage-api,imgproxy,mailpit,postgres-meta,studio,edge-runtime,logflare,vector,supavisor
PYTHONPATH=. python3 scripts/test_s0_auth_rest_local.py
PYTHONPATH=. python3 scripts/test_s0_cfi01_auth_rest_local.py
PRUMO_CFI01_TRANSACTIONAL_TEST=YES PYTHONPATH=. python3 scripts/test_transactional_communication.py
supabase stop --no-backup
```

Only run in a fresh local throwaway environment. No production migrations are
created or applied by this delivery. Test 12 installs and removes a case-scoped
failure trigger exclusively inside that throwaway database to prove rollback.
