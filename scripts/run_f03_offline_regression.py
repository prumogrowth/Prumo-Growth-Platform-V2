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
SUITES = (
    ('test_s0_openai_f03_offline.py', 50),
    ('test_s0_openai_f03_assignment_recheck.py', 28),
    ('test_s0_openai_f03_review_pipeline.py', 22),
    ('test_s0_openai_f03_real_integration.py', 44),
    ('test_s0_openai_f03_optional_coverage.py', 16),
    ('test_s0_openai_f03_race_matrix.py', 28),
    ('test_s0_openai_f03_snapshot_immutability.py', 22),
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

    missing = [name for name, _ in SUITES if not (TESTS / name).is_file()]
    if missing and not allow_subset:
        print('BLOCKED: missing F03 suites: ' + ', '.join(missing), file=sys.stderr)
        return 2
    suites_to_run = [(name, count) for name, count in SUITES if (TESTS / name).is_file()]
    if not suites_to_run:
        print('BLOCKED: no F03 suites present', file=sys.stderr)
        return 2

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name, expected in suites_to_run:
        file = TESTS / name
        tests = loader.discover(str(TESTS), pattern=name)
        observed = tests.countTestCases()
        print(f'F03 {name}: count={observed}/{expected} blob={git_blob_sha(file)}', flush=True)
        if observed != expected:
            print(f'BLOCKED: unexpected test count in {name}', file=sys.stderr)
            return 2
        suite.addTests(tests)

    if not allow_subset and suite.countTestCases() != 210:
        print('BLOCKED: expected all 210 F03 tests', file=sys.stderr)
        return 2

    print(f'F03 regression mode={"SUBSET" if allow_subset else "FULL"} '
          f'expected={suite.countTestCases()} offline-only fixture', flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != '--allow-subset'):
        raise SystemExit('usage: python scripts/run_f03_offline_regression.py [--allow-subset]')
    raise SystemExit(run(allow_subset='--allow-subset' in sys.argv))
