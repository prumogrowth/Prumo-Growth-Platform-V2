# Pinned source for offline cross-front compatibility tests

These files are byte-for-byte snapshots, not alternative implementations or
runtime dependencies. `manifest.json` records commit, original path, Git blob
SHA and SHA-256. No branch is merged, imported into production or overwritten.
No browser, network, model or database is invoked by these fixtures.

Tests execute the real Frontend/S2 modules with Node, the real S0 closure
validator and S1 export parser with Python. For PR #1, tests compile only the
original `FieldKind`, `ProposedField`, `proposal_digest` and `_candidate` AST
nodes, omitting imports of database adapters; their source code is unchanged.
The atomic receipt DTO/command fields are checked directly from the pinned AST.
Hash validation covers every original file, including unused parts.

Changing a pin requires explicit manifest/source updates and reviewing drift.
Tests demonstrate compatibility of these SHAs, not future branch heads or
an authenticated production integration. Fixtures contain synthetic metadata.

`s0_atomic_checkpoint_1b4.py` preserves the exact PR #9 atomic runtime at
`1b4f2841d513fb971c93379636414bf686784beb` for the PR #11 provenance check.
It is test data, never imported as a runtime. The active backend now has the
audited precommit expected-receipt check; source_manifest.json explicitly
points the historical checkpoint entry at this immutable reference.
