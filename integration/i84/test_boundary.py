"""Physical filesystem/process boundaries, no pretend SQL/Auth integration."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from local_admin import boundary as b
from local_admin.__main__ import main

class BoundaryTests(unittest.TestCase):
    def test_explicit_optin(self):
        with patch.dict(os.environ,{'PRUMO_I84_DISPOSABLE':'NO'}):
            with self.assertRaisesRegex(b.Blocked,'OPT_IN'):
                with b.locked():pass

    def test_private_atomic_journal(self):
        with tempfile.TemporaryDirectory(prefix='prumo-admin-i84-unit-') as d:
            p=Path(d)/'state.json';b.save(p,{'phase':'UNCERTAIN'})
            self.assertEqual(b.load(p),{'phase':'UNCERTAIN'});self.assertFalse(p.with_name('state.json.next').exists())
            p.chmod(0o644)
            with self.assertRaisesRegex(b.Blocked,'PERMISSIONS'):b.load(p)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory(prefix='prumo-admin-i84-unit-') as d:
            p=Path(d)/'state.json';p.symlink_to('/etc/passwd')
            with self.assertRaisesRegex(b.Blocked,'PERMISSIONS'):b.load(p)

    def test_state_outside_temp_child_rejected(self):
        for p in ('/workspace/prumo-admin-i84-x','/tmp/prumo-admin-i84-x/nested','/tmp/else'):
            with self.assertRaises(b.Blocked):b.location(p)

    def test_real_cross_process_lock(self):
        with patch.dict(os.environ,{'PRUMO_I84_DISPOSABLE':'YES'}):
            with b.locked():
                result=subprocess.run(['python3','-m','local_admin','status'],cwd=b.ROOT,capture_output=True)
                self.assertEqual(result.returncode,2);self.assertIn(b'LOCAL_OPERATION_BUSY',result.stdout)

    def test_secret_argument_never_echoed(self):
        out=io.StringIO()
        with patch('sys.argv',['local_admin','--password','sentinel-do-not-echo']),contextlib.redirect_stdout(out):self.assertEqual(main(),2)
        self.assertNotIn('sentinel',out.getvalue());self.assertIn('CLI_ARGUMENTS_INVALID',out.getvalue())

    def test_missing_and_invalid_dedicated_file(self):
        from local_admin.custody import read_env
        with tempfile.TemporaryDirectory(prefix='prumo-admin-i84-unit-') as d:
            with self.assertRaisesRegex(b.Blocked,'MISSING'):read_env(d)
            p=Path(d)/'edge.env';p.write_text('PRUMO_I83_DEDICATED=NO\n');p.chmod(0o600)
            with self.assertRaisesRegex(b.Blocked,'CREDENTIAL_FILE_INVALID'):read_env(d)

    def test_hosted_link_and_unsealed_source_rejected(self):
        from local_admin import environment as e
        import json
        with tempfile.TemporaryDirectory(prefix='prumo-admin-i84-unit-') as d:
            root=Path(d);(root/'local_admin').mkdir();(root/'supabase/.temp').mkdir(parents=True)
            (root/'local_admin/dependencies.json').write_text(json.dumps({'local_sources':{}}))
            (root/'supabase/.temp/project-ref').write_text('hosted-project-ref')
            with patch.object(e,'ROOT',root):
                with self.assertRaisesRegex(b.Blocked,'HOSTED_PROJECT_LINK'):e.checkout()
                (root/'supabase/.temp/project-ref').unlink()
                (root/'supabase/migrations').mkdir();(root/'supabase/migrations/unreviewed.sql').write_text('select 1;')
                with self.assertRaisesRegex(b.Blocked,'UNCERTIFIED_SOURCE_ADDED'):e.checkout()

    def test_material_detection_failure_does_not_echo_value(self):
        from integration.i84.capture import reject_material
        marker='private-diagnostic-sentinel'
        try:reject_material(('unexpected '+marker).encode(),[marker])
        except AssertionError as error:
            self.assertEqual(str(error),'I84_MATERIAL_MATCH_WITHHELD')
            self.assertNotIn(marker,str(error))
        else:self.fail('material detection did not reject')

if __name__=='__main__':unittest.main(verbosity=2)
