"""Offline contract/safety tests. Fake postgres tools; never touch a real database."""
import os
import re
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
RUN = HERE / 'run-wa06d-ephemeral.sh'

class EphemeralRunnerSafetyTests(unittest.TestCase):
    def run_lab(self, argv=(), *, simulate_pg=True, pg_major=17, fail_start=False, still_running=False):
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
                for tool in ('initdb','createdb','psql'):
                    mk(tool, f'printf "{tool} %s\\n" "$*" >> "$WA06D_FAKE_RECORD"')
                mk('pg_ctl', """case "$3" in
status) if [ "$WA06D_STILL_RUNNING" = 1 ]; then exit 0; else exit 1; fi;;
esac
printf "pg_ctl %s\\n" "$*" >> "$WA06D_FAKE_RECORD"
case "$*" in
*" -w start") [ "$WA06D_FAIL_START" != 1 ] || exit 9;;
*" -w stop") [ "$WA06D_STILL_RUNNING" != 1 ] || exit 9;;
esac
""")
            else:
                mk('pg_config','echo /does/not/exist')
            env=dict(os.environ,PATH=str(binpath)+':'+os.environ.get('PATH',''),
                     WA06D_FAKE_BIN=str(binpath), WA06D_FAKE_RECORD=str(record),
                     PGHOSTADDR='203.0.113.77', PGSERVICE='hosted_production',
                     PGOPTIONS='-c search_path=public',
                     WA06D_FAIL_START='1' if fail_start else '0',
                     WA06D_STILL_RUNNING='1' if still_running else '0')
            response=subprocess.run(['/bin/bash', str(RUN),*argv],env=env,
                                    capture_output=True,text=True,timeout=10)
            log=record.read_text() if record.exists() else ''
            # Only simulated tool executions: remove deliberately preserved fixture dirs.
            if still_running and 'WA06D CRITICAL:' in response.stderr:
                match=re.search(r'/tmp/wa06d_pg17_[A-Za-z0-9_]+', response.stderr)
                if match:
                    shutil.rmtree(match.group(0),ignore_errors=True)
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

    def test_06_failed_start_still_attempts_shutdown(self):
        response,log=self.run_lab(fail_start=True)
        self.assertNotEqual(response.returncode,0)
        self.assertIn(' -w start',log)
        self.assertIn('-m fast -w stop',log)
        self.assertNotIn('psql ',log)

    def test_07_unverified_shutdown_preserves_cluster(self):
        response,log=self.run_lab(still_running=True)
        self.assertEqual(response.returncode,70,response.stderr)
        self.assertIn('WA06D CRITICAL:',response.stderr)
        self.assertIn('-m fast -w stop',log)

if __name__=='__main__':
    unittest.main(verbosity=2)
