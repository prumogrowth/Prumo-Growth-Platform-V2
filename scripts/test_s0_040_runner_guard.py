"""Offline checks of S0 runner's actual embedded URL guard. No SQL connection."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

RUNNER = Path(os.environ.get('S0_RUNNER_TEST_PATH', str(Path(__file__).resolve().parents[1] / 'scripts/run-s0-local.sh')))

class S0RunnerUrlGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = RUNNER.read_text(encoding='utf-8')
        cls.validator = source.split("python3 - <<'PY'\n", 1)[1].split('\nPY\n', 1)[0]
        cls.env_scrub = source.split('\nPY\n', 1)[1]

    def check(self, url):
        env = dict(os.environ, PRUMO_TEST_DATABASE_URL=url, PGHOSTADDR='203.0.113.52', PGSERVICE='remote')
        return subprocess.run([sys.executable, '-c', self.validator], capture_output=True, text=True, env=env)

    def test_valid_local_pg17_ci_format(self):
        r = self.check('postgresql://postgres:postgres@127.0.0.1:5432/prumo_s0_test_ci')
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_remote_hostname_denied(self):
        self.assertNotEqual(self.check('postgresql://u:p@db.example/prumo_s0_test_ci').returncode, 0)

    def test_hostaddr_url_override_denied(self):
        self.assertNotEqual(self.check('postgresql://u:p@localhost/prumo_s0_test_ci?hostaddr=203.0.113.55').returncode, 0)

    def test_service_url_override_denied(self):
        self.assertNotEqual(self.check('postgresql://u:p@localhost/prumo_s0_test_ci?service=remote').returncode, 0)

    def test_encoded_non_test_path_denied(self):
        self.assertNotEqual(self.check('postgresql://u:p@localhost/prumo_s0_test_ci%2fproduction').returncode, 0)

    def test_non_test_db_denied(self):
        self.assertNotEqual(self.check('postgresql://u:p@localhost/postgres').returncode, 0)

    def test_fragment_denied(self):
        self.assertNotEqual(self.check('postgresql://u:p@localhost/prumo_s0_test_ci#remote').returncode, 0)

    def test_libpq_remote_environment_is_unset_before_calls(self):
        self.assertIn('unset PGHOSTADDR PGHOST PGPORT PGDATABASE PGUSER PGSERVICE PGSERVICEFILE PGOPTIONS', self.env_scrub)
        self.assertLess(self.env_scrub.index('unset PGHOSTADDR'), self.env_scrub.index('for file in supabase/tests/'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
