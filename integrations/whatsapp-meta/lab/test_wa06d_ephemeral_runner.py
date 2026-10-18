"""Offline contract/safety tests. Fake postgres tools; never touch a real database."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
RUN = HERE / 'run-wa06d-ephemeral.sh'

class EphemeralRunnerSafetyTests(unittest.TestCase):
    def run_lab(self, argv=(), *, simulate_pg=True, pg_major=17):
        with tempfile.TemporaryDirectory(prefix='wa06d_mock_') as tmp:
            folder=Path(tmp)
            binpath=folder/'bin'
            binpath.mkdir()
            record=folder/'invocations.txt'
            def mk(name, text):
                p=binpath/name
                p.write_text('#!/bin/sh\n'+text+'\n')
                p.chmod(0o700)
            mk('id', 'if [ "$1" = "-u" ]; then echo 1001; else /usr/bin/id "$@"; fi')
            if simulate_pg:
                mk('pg_config', 'if [ "$1" = "--bindir" ]; then echo "$WA06D_FAKE_BIN"; else exit 1; fi')
                mk('postgres', f'echo "PostgreSQL {pg_major}.1"')
                for tool in ('initdb','pg_ctl','createdb','psql'):
                    mk(tool, f'printf "{tool} %s\\n" "$*" >> "$WA06D_FAKE_RECORD"')
            else:
                mk('pg_config','echo /does/not/exist')
            env=dict(os.environ,PATH=str(binpath)+':'+os.environ.get('PATH',''),
                     WA06D_FAKE_BIN=str(binpath), WA06D_FAKE_RECORD=str(record),
                     PGHOSTADDR='203.0.113.77', PGSERVICE='hosted_production',
                     PGOPTIONS='-c search_path=public')
            response=subprocess.run(['/bin/bash', str(RUN),*argv],env=env,
                                    capture_output=True,text=True,timeout=10)
            log=record.read_text() if record.exists() else ''
            return response,log

    def test_01_no_additional_arguments(self):
        response,log=self.run_lab(['postgresql://production.example'])
        self.assertEqual(response.returncode,64)
        self.assertEqual(log,'')

    def test_02_missing_pg_binaries(self):
        response,log=self.run_lab(simulate_pg=False)
        self.assertEqual(response.returncode,69)
        self.assertEqual(log,'')

    def test_03_wrong_major(self):
        response,log=self.run_lab(pg_major=18)
        self.assertEqual(response.returncode,69)
        self.assertEqual(log,'')

    def test_04_three_sql_files_in_separate_sessions_and_cleanup(self):
        response,log=self.run_lab()
        self.assertEqual(response.returncode,0,response.stderr)
        commands=log.splitlines()
        psql=[x for x in commands if x.startswith('psql ')]
        self.assertEqual(len(psql),3)
        names=['wa06d_pg17_atomicity.sql','wa06d_pg17_postcommit_setup.sql',
               'wa06d_pg17_postcommit_verify.sql']
        for line,name in zip(psql,names):
            self.assertIn(name,line)
            self.assertIn('wa06d_test_ephemeral',line)
            self.assertIn(' -h /tmp/wa06d_pg17_',line)
            self.assertNotIn('203.0.113.77',line)
        self.assertTrue(commands[-1].startswith('pg_ctl '))
        self.assertIn('-m fast -w stop',commands[-1])

    def test_05_does_not_use_inherited_service_config(self):
        response,log=self.run_lab()
        self.assertEqual(response.returncode,0,response.stderr)
        self.assertNotIn('hosted_production',log)
        self.assertNotIn('203.0.113.77',log)
        self.assertNotIn('search_path=public',log)
        self.assertIn("listen_addresses=''",log)
        self.assertIn('unix_socket_directories=',log)

if __name__=='__main__':
    unittest.main(verbosity=2)
