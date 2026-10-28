"""Adversarial scope checks in fresh local clones, never in the user's working tree."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from .verify_scope import BASE

ROOT=Path.cwd()
class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='s0-meta-scope-',dir=os.environ.get('S0_META_WORK','/tmp'))
        self.repo=Path(self.tmp.name)/'repo'
        self.git('clone','--shared','--no-checkout',str(ROOT),str(self.repo),cwd=ROOT)
        self.git('checkout','--detach',BASE)
        for folder in ('integration/s0_meta_ingress','docs/contratos/s0_meta_ingress'):
            shutil.copytree(ROOT/folder,self.repo/folder)
        path=Path('.github/workflows/exp-s0-meta-ingress-01.yml')
        shutil.copyfile(ROOT/path,self.repo/path)
    def tearDown(self):self.tmp.cleanup()
    def git(self,*args,cwd=None):
        return subprocess.run(['git',*args],cwd=cwd or self.repo,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def verify(self,expected=1,extra=None):
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**(extra or {})}
        r=subprocess.run(['python3','integration/s0_meta_ingress/verify_scope.py'],cwd=self.repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertEqual(r.returncode,expected,r.stderr.decode())
    def test_clean(self):self.verify(0)
    def test_i85_pending(self):
        with (self.repo/'integration/i85/__init__.py').open('a') as f:f.write('\n# unauthorized\n')
        self.verify()
    def test_i86_new(self):
        p=self.repo/'integration/i86/forbidden.py';p.parent.mkdir(exist_ok=True);p.write_text('forbidden\n');self.verify()
    def test_official_migration_staged(self):
        p=next((self.repo/'supabase/migrations').glob('*.sql'));p.write_text('-- unauthorized\n');self.git('add',str(p));self.verify()
    def test_inherited_deleted(self):
        (self.repo/'integration/i85/__init__.py').unlink();self.verify()
    def test_inherited_rename(self):
        self.git('mv','integration/i85/__init__.py','integration/i85/renamed.py');self.verify()
    def test_unrelated_workflow(self):
        p=self.repo/'.github/workflows/forbidden.yml';p.write_text('name: forbidden\n');self.verify()
    def test_base_environment_override(self):self.verify(extra={'S0_META_EXPECTED_BASE':'0'*40})
    def test_manifest_missing_file(self):
        (self.repo/'integration/s0_meta_ingress/unlisted.txt').write_text('not listed');self.verify()
    def test_inherited_ignored_untracked(self):
        p=self.repo/'backend/.env';p.write_text('SYNTHETIC=only');self.verify()
    def test_symlink(self):
        p=self.repo/'integration/s0_meta_ingress/protocol.py';p.unlink();p.symlink_to(self.repo/'backend/__init__.py');self.verify()
    def test_committed_owned_edit_allowed(self):
        self.git('add','integration/s0_meta_ingress','docs/contratos/s0_meta_ingress','.github/workflows/exp-s0-meta-ingress-01.yml')
        self.git('-c','user.name=Scope Test','-c','user.email=scope@invalid.test','commit','-m','owned additions')
        p=self.repo/'integration/s0_meta_ingress/protocol.py';p.write_text(p.read_text()+'\n# owned edit\n')
        self.git('add',str(p));self.git('-c','user.name=Scope Test','-c','user.email=scope@invalid.test','commit','-m','owned edit')
        self.verify(0)

if __name__=='__main__':unittest.main(verbosity=2)
