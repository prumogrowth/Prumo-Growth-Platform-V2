"""Offline gate: mock psql executable, never open a database connection."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

RUNNER = Path(__file__).with_name('run-wa06d-local.sh')

class RunnerGuardTests(unittest.TestCase):
    def run_case(self, args, use_mock=True):
        with tempfile.TemporaryDirectory(prefix='wa06d_runner_') as tmp:
            t = Path(tmp)
            if use_mock:
                fake = t / 'psql'
                fake.write_text('#!/bin/sh\nif [ "${PGHOSTADDR-unset}" != "unset" ]; then exit 42; fi\nprintf "%s\\n" "$@" > "$WA06D_CAPTURE"\n')
                fake.chmod(0o700)
            capture = t / 'args.txt'
            env = dict(os.environ, PATH=(str(t) + ':' + os.environ.get('PATH','')) if use_mock else str(t), WA06D_CAPTURE=str(capture), PGHOSTADDR='192.0.2.88')
            result = subprocess.run(['/bin/bash', str(RUNNER), *args], env=env, capture_output=True, text=True)
            return result, capture.read_text() if capture.exists() else None

    def test_denies_no_argument(self):
        result, args = self.run_case([])
        self.assertEqual(result.returncode, 64)
        self.assertIsNone(args)

    def test_denies_url_and_real_db_name(self):
        for name in ['postgres', 'production', 'https://remote.example/db', 'wa06d_test_x;rm -rf /', 'wa06d_test_']:
            with self.subTest(name=name):
                result, args = self.run_case([name])
                self.assertEqual(result.returncode, 64)
                self.assertIsNone(args)

    def test_denies_extra_arguments(self):
        result, args = self.run_case(['wa06d_test_lab', '--host=remote'])
        self.assertEqual(result.returncode, 64)
        self.assertIsNone(args)

    def test_denies_missing_psql_without_execution(self):
        result, args = self.run_case(['wa06d_test_lab'], False)
        self.assertEqual(result.returncode, 69)
        self.assertIn('no SQL was executed', result.stderr)
        self.assertIsNone(args)

    def test_valid_invocation_is_loopback_only(self):
        result, data = self.run_case(['wa06d_test_scratch1'])
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = data.splitlines()
        self.assertEqual(arguments[:9], ['-X', '-v', 'ON_ERROR_STOP=1', '-h', '127.0.0.1', '-p', '5432', '-d', 'wa06d_test_scratch1'])
        self.assertEqual(arguments[9], '-f')
        self.assertTrue(arguments[10].endswith('/wa06d_pg17_atomicity.sql'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
