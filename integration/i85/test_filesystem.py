"""Real subprocess SIGKILL and private filesystem proofs; no SQL/Auth mocks."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest
from local_admin import boundary as b
from integration.i85 import storage

class FilesystemTests(unittest.TestCase):
    def test_legacy_next_is_reproducible_after_actual_sigkill(self):
        with tempfile.TemporaryDirectory(prefix='prumo-i85-fs-') as folder:
            path=Path(folder)/'state.json';b.save(path,{'phase':'NONE'})
            script="""import os,signal,sys
from unittest.mock import patch
from pathlib import Path
from local_admin import boundary as b
def halt(*a):os.kill(os.getpid(),signal.SIGSTOP)
with patch.object(os,'replace',halt):b.save(Path(sys.argv[1]),{'phase':'COMMIT_UNKNOWN'})
"""
            process=subprocess.Popen(['python3','-c',script,str(path)],cwd=b.ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                until=time.monotonic()+5
                while time.monotonic()<until:
                    if path.with_name('state.json.next').exists():break
                    time.sleep(.01)
                else:self.fail('no actual temporary file')
                process.kill();process.wait(timeout=5)
                with self.assertRaises(FileExistsError):b.save(path,{'phase':'NONE'})
                self.assertEqual(b.load(path),{'phase':'NONE'})
                self.assertEqual(b.load(path.with_name('state.json.next')),{'phase':'COMMIT_UNKNOWN'})
            finally:
                if process.poll() is None:process.kill();process.wait()

    def test_i85_unique_atomic_write_does_not_erase_residual_evidence(self):
        with tempfile.TemporaryDirectory(prefix='prumo-i85-fs-') as folder:
            path=Path(folder)/'state.json';residue=path.with_name('state.json.next')
            b.save(residue,{'phase':'COMMIT_UNKNOWN'})
            before=residue.read_bytes();storage.atomic_save(path,{'phase':'NONE'})
            self.assertEqual(residue.read_bytes(),before)
            self.assertEqual(storage.residues(folder),[residue])

    def test_symlink_and_hardlink_refused(self):
        with tempfile.TemporaryDirectory(prefix='prumo-i85-fs-') as folder:
            target=Path(folder)/'original';storage.atomic_save(target,{'value':'sentinel'})
            link=Path(folder)/'state.json.next';link.symlink_to(target)
            with self.assertRaises(b.Blocked):storage.residues(folder)
            link.unlink();os.link(target,link)
            with self.assertRaises(b.Blocked):storage.residues(folder)

    def test_private_modes_and_durable_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix='prumo-i85-fs-') as folder:
            p=Path(folder)/'state.json';storage.atomic_save(p,{'version':2})
            self.assertEqual(p.stat().st_mode&0o777,0o600)
            self.assertEqual(storage.read(p),{'version':2})
            self.assertFalse(storage.residues(folder))

    def test_cli_never_echoes_unknown_arguments_or_choices(self):
        marker='do-not-echo-sentinel'
        for args in (['--password',marker],[marker],['create','--label',marker]):
            result=subprocess.run(['python3','-m','integration.i85',*args],cwd=b.ROOT,capture_output=True)
            self.assertEqual(result.returncode,2)
            self.assertNotIn(marker.encode(),result.stdout+result.stderr)
            self.assertFalse(result.stderr)
            self.assertEqual(json.loads(result.stdout)['code'],'CLI_ARGUMENTS_INVALID')

    def test_duplicate_and_nonfinite_journals_refused(self):
        for raw in (b'{"phase":"NONE","phase":"ACTIVE"}',b'{"version":NaN}',b'{"version":Infinity}'):
            with self.assertRaises(b.Blocked):storage.decode(raw)

    def test_failed_replace_retains_real_private_staged_bytes(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='prumo-i85-fs-') as folder:
            p=Path(folder)/'state.json'
            with patch.object(os,'replace',side_effect=OSError('synthetic filesystem fault')):
                with self.assertRaises(OSError):storage.atomic_save(p,{'phase':'COMMIT_UNKNOWN'})
            residual=storage.residues(folder)
            self.assertEqual(len(residual),1)
            self.assertEqual(storage.read(residual[0]),{'phase':'COMMIT_UNKNOWN'})
            self.assertFalse(p.exists())

if __name__=='__main__':unittest.main(verbosity=2)
