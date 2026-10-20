#!/usr/bin/env python3
"""Run only the seven synthetic F03 suites in a single verifiable process.

This deliberately never invokes PostgreSQL, OpenAI, Meta, Supabase, or any
commercial backend. It does not provide an OS-level network sandbox.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / 'backend' / 'tests'
# Git blob IDs for exact source files checked on the PR #8 branch. This
# manifest is intentionally explicit and reviewed; a changed test requires
# deliberately updating its pin, not only preserving the same test count.
SUITES = (
    ('test_s0_openai_f03_offline.py', 50, '34d72534f26e0c950105a473a7586769756f70ca'),
    ('test_s0_openai_f03_assignment_recheck.py', 28, '753e384115ae6b27bfa0ca17811c3ee1bf8832bd'),
    ('test_s0_openai_f03_review_pipeline.py', 22, '1865e953ec7c7aadef0da218a594d282a018b762'),
    ('test_s0_openai_f03_real_integration.py', 44, '8ff655b88223c326c65ccc2515b54a2a086d8661'),
    ('test_s0_openai_f03_optional_coverage.py', 16, '3969aa5c379ca14726399bdb8021ad4564173a7a'),
    ('test_s0_openai_f03_race_matrix.py', 28, '43668487df0372ba1be4595fd21ff4924f40eb88'),
    ('test_s0_openai_f03_snapshot_immutability.py', 22, '5ccc16028d47e9a86a26c8008ad37b54fde25a32'),
)
EXPECTED_FULL_CASES = 210
# Verify the three real F03 validators too: a full pass against a locally
# modified validator is NOT a regression of the reviewed GitHub branch.
MODULES = (
    ('f03_offline_gate.py', '01dfce772b66b30dac505ed80ecca81054dbf75b'),
    ('f03_assignment_recheck.py', 'd2e7f6a6ed4308186eac4b2c5801837c800ce5ab'),
    ('f03_review_pipeline.py', '11e39080b2713db3a00f90fd08e57c29e5305b75'),
)


# Clear commonly used credentials/endpoints in this process before importing
# backend tests. This is defense in depth, NOT a full network or OS sandbox.
SENSITIVE_ENV = (
    'DATABASE_URL', 'PRUMO_TEST_DATABASE_URL', 'SUPABASE_URL',
    'SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_ANON_KEY', 'OPENAI_API_KEY',
    'META_ACCESS_TOKEN', 'WHATSAPP_ACCESS_TOKEN', 'META_APP_SECRET',
)


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(content)).encode('ascii')
                        + b'\0' + content).hexdigest()


def run(*, allow_subset: bool = False) -> int:
    for key in SENSITIVE_ENV:
        os.environ.pop(key, None)
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)

    missing = [name for name, _, _ in SUITES if not (TESTS / name).is_file()]
    if missing and not allow_subset:
        print('BLOCKED: missing F03 suites: ' + ', '.join(missing), file=sys.stderr)
        return 2
    suites_to_run = [(name, count, sha) for name, count, sha in SUITES
                     if (TESTS / name).is_file()]
    if not suites_to_run:
        print('BLOCKED: no F03 suites present', file=sys.stderr)
        return 2

    # Verify implementations before importing tests (or their dependencies).
    for name, trusted_sha in MODULES:
        path = ROOT / 'backend' / 's0_openai_bridge' / name
        if not path.is_file():
            print(f'BLOCKED: missing F03 validator: {name}', file=sys.stderr)
            return 2
        actual_sha = git_blob_sha(path)
        print(f'F03 module {name}: pinned_blob={trusted_sha} actual_blob={actual_sha}', flush=True)
        if actual_sha != trusted_sha:
            print(f'BLOCKED: unapproved F03 validator: {name}', file=sys.stderr)
            return 2

    # Validate ALL pinned files before importing ANY suite. A bad file must
    # not execute top-level module code merely because its test count matches.
    for name, expected, trusted_sha in suites_to_run:
        actual_sha = git_blob_sha(TESTS / name)
        print(f'F03 {name}: pinned_blob={trusted_sha} actual_blob={actual_sha}', flush=True)
        if actual_sha != trusted_sha:
            print(f'BLOCKED: unapproved F03 test file: {name}', file=sys.stderr)
            return 2

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name, expected, _ in suites_to_run:
        tests = loader.discover(str(TESTS), pattern=name)
        observed = tests.countTestCases()
        print(f'F03 {name}: count={observed}/{expected}', flush=True)
        if observed != expected:
            print(f'BLOCKED: unexpected test count in {name}', file=sys.stderr)
            return 2
        suite.addTests(tests)

    if not allow_subset and suite.countTestCases() != EXPECTED_FULL_CASES:
        print(f'BLOCKED: expected all {EXPECTED_FULL_CASES} F03 tests', file=sys.stderr)
        return 2

    print(f'F03 regression mode={"SUBSET" if allow_subset else "FULL"} '
          f'expected={suite.countTestCases()} offline-only fixture', flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != '--allow-subset'):
        raise SystemExit('usage: python scripts/run_f03_offline_regression.py [--allow-subset]')
    raise SystemExit(run(allow_subset='--allow-subset' in sys.argv))
