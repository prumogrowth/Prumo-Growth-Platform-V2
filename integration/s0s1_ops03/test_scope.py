"""Artificial Git attacks only; never mutate other worktrees."""
import ast
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
import io
from integration.s0s1_ops03 import scope as s

class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ops03-git-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_git("init", "-b", s.BRANCH)
        self.run_git("config", "user.name", "Synthetic OPS03")
        self.run_git("config", "user.email", "synthetic@example.invalid")
        (self.root / "protected.txt").write_text("frozen\n")
        (self.root / ".gitignore").write_text("*.ignored\n")
        self.commit()
        self.base = self.run_git("rev-parse", "HEAD").strip()
        self.base_tree = self.run_git("rev-parse", "HEAD^{tree}").strip()
        for path in s.ALLOWED:
            local = self.root / path
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text("synthetic\n")

    def run_git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.DEVNULL).decode()

    def commit(self):
        self.run_git("add", "-A")
        self.run_git("commit", "-m", "synthetic fixture")

    def report(self, candidate=False, **overrides):
        params = {"base": self.base, "base_tree": self.base_tree, "branch": s.BRANCH}
        params.update(overrides)
        return s.inspect(self.root, candidate=candidate, **params)

    def denied(self, candidate=False, **kwargs):
        self.assertEqual(self.report(candidate, **kwargs)["status"], "FAIL")

    def test_authorized_candidate_untracked_and_staged(self):
        self.assertEqual(self.report(True)["status"], "PASS")
        self.run_git("add", "-A")
        self.assertEqual(self.report(True)["status"], "PASS")
        self.denied()

    def test_exact_atomic_commit_pass(self):
        self.commit()
        report = self.report()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(set(report["files"]), s.ALLOWED)
        self.assertIs(report["authorizes_action"], False)

    def test_frozen_wrong_base_tree(self):
        self.denied(True, base_tree="0" * 40)

    def test_base_not_ancestor(self):
        self.commit()
        self.run_git("checkout", "--orphan", "unrelated")
        self.run_git("commit", "-m", "unrelated fixture")
        self.denied()

    def test_wrong_branch_and_detached(self):
        self.commit()
        self.run_git("branch", "-m", "wrong")
        self.denied()
        self.run_git("checkout", "--detach")
        self.denied()

    def test_protected_committed_change(self):
        (self.root / "protected.txt").write_text("changed\n")
        self.commit()
        self.denied()

    def test_protected_pending_staged_unstaged(self):
        (self.root / "protected.txt").write_text("changed\n")
        self.denied(True)
        self.run_git("add", "protected.txt")
        self.denied(True)

    def test_protected_change_reverted_in_history(self):
        (self.root / "protected.txt").write_text("changed\n")
        self.commit()
        (self.root / "protected.txt").write_text("frozen\n")
        self.commit()
        report = self.report()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("HISTORICAL_OUT_OF_SCOPE:protected.txt", report["violations"])

    def test_out_of_scope_untracked_and_ignored(self):
        for name in ("outside.txt", "private.ignored"):
            (self.root / name).write_text("synthetic")
            self.denied(True)
            (self.root / name).unlink()

    def test_symlink_leaf(self):
        path = self.root / sorted(s.ALLOWED)[0]
        path.unlink()
        path.symlink_to(self.root / "protected.txt")
        self.denied(True)
        self.commit()
        self.denied()

    def test_symlink_parent(self):
        self.commit()
        directory = self.root / "ops/s0s1_authority"
        directory.rename(self.root / "saved")
        directory.symlink_to(self.root / "saved", target_is_directory=True)
        self.denied()

    def test_executable_mode(self):
        (self.root / "ops/s0s1_authority/hosted_compat_v1.json").chmod(0o755)
        self.denied(True)
        self.commit()
        self.denied()

    def test_gitlink_index(self):
        path = sorted(s.ALLOWED)[0]
        self.run_git("update-index", "--add", "--cacheinfo", "160000," + self.base + "," + path)
        self.denied(True)

    def test_rename_protected_into_allowlist(self):
        target = "ops/s0s1_authority/hosted_compat_v1.json"
        (self.root / target).unlink()
        self.run_git("mv", "protected.txt", target)
        self.commit()
        self.denied()

    def test_deletion(self):
        (self.root / "protected.txt").unlink()
        self.commit()
        self.denied()

    def test_merge_commit(self):
        self.commit()
        original = self.run_git("rev-parse", "HEAD").strip()
        self.run_git("checkout", "-b", "artificial-side", self.base)
        (self.root / "side.txt").write_text("synthetic")
        self.commit()
        side = self.run_git("rev-parse", "HEAD").strip()
        self.run_git("checkout", s.BRANCH)
        tree_id = self.run_git("rev-parse", "HEAD^{tree}").strip()
        merge = subprocess.check_output(["git", "-C", str(self.root), "commit-tree", tree_id,
                                         "-p", original, "-p", side, "-m", "synthetic merge"]).decode().strip()
        self.run_git("update-ref", "HEAD", merge)
        self.denied()

    def test_pending_authorized_edit_after_commit(self):
        self.commit()
        (self.root / "ops/s0s1_authority/hosted_compat_v1.json").write_text("changed")
        self.denied()
        self.denied(True)

    def test_second_commit_even_within_allowlist_rejected(self):
        self.commit()
        (self.root / "ops/s0s1_authority/hosted_compat_v1.json").write_text("changed")
        self.commit()
        self.denied()

    def test_missing_authorized_file(self):
        (self.root / sorted(s.ALLOWED)[0]).unlink()
        self.denied(True)

    def test_assume_unchanged_does_not_hide_inherited_change(self):
        self.run_git("update-index", "--assume-unchanged", "protected.txt")
        (self.root / "protected.txt").write_text("hidden")
        self.denied(True)

    def test_skip_worktree_does_not_hide_inherited_change(self):
        self.run_git("update-index", "--skip-worktree", "protected.txt")
        (self.root / "protected.txt").write_text("hidden")
        self.denied(True)

    def test_hardlink_and_fifo(self):
        target = self.root / sorted(s.ALLOWED)[0]
        target.unlink()
        os.link(self.root / "protected.txt", target)
        self.denied(True)
        target.unlink()
        os.mkfifo(target)
        self.denied(True)

    def test_replacement_refs(self):
        self.commit()
        self.run_git("replace", self.base, "HEAD")
        self.denied()

    def test_cli_has_no_anchor_override(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(s.main(["--base", "HEAD"]), 1)
        self.assertEqual(json.loads(output.getvalue())["status"], "FAIL")

class ArtifactTests(unittest.TestCase):
    root = Path(__file__).absolute().parents[2]

    def test_contract_never_claims_hosted_or_human_homologation(self):
        doc = json.loads((self.root/'ops/s0s1_authority/hosted_compat_v1.json').read_text())
        self.assertEqual(doc['version'],'prumo.s0s1.ops03.hosted-compat.v1')
        for key in ('hosted_verified','production_homologated','human_presence_certified',
                    'administrative_application_enabled','hosted_supported_revoke_implemented'):
            self.assertIs(doc[key],False)
        self.assertEqual(doc['session_strategy'],'UNCHANGED_I86_ATOMIC_AUTH_DML_LAB_CONTROL_ONLY')

    def test_adapter_preserves_guard_and_cannot_install_a_hosted_variant(self):
        text = (self.root/'integration/s0s1_ops03/hosted_candidate.sql').read_text().lower()
        self.assertIn('select prumo_i86_manual.guard();',text)
        self.assertEqual(text.count('security invoker'),4)
        self.assertEqual(text.count("set search_path=''"),4)
        self.assertIn('return prumo_i86_manual.apply_act(',text)
        self.assertIn('return prumo_i86_manual.reconcile_act(',text)
        for forbidden in ('security definer','create function public.','grant execute',
                          'delete from auth.','update auth.','insert into auth.',
                          'create function auth.','alter function prumo_i86_manual.'):
            self.assertNotIn(forbidden,text)

    def test_diagnostic_only_reads_catalogs_inside_readonly_transaction(self):
        import re
        text = (self.root/'integration/s0s1_ops03/diagnostic.sql').read_text().lower()
        text = re.sub(r'--[^\n]*','',text)
        stripped = re.sub(r"'(?:''|[^'])*'","''",text)
        self.assertIn('begin read only;',text)
        self.assertTrue(text.strip().endswith('commit;'))
        for keyword in ('insert','update','delete','truncate','create','alter','drop','call','do','grant','revoke','copy'):
            self.assertIsNone(re.search(r'\b'+keyword+r'\b',stripped),keyword)
        for forbidden in ('pg_authid','pg_shadow','pg_read_file','dblink','http_get',
                          'from auth.','join auth.','from public.','join public.'):
            self.assertNotIn(forbidden,stripped)

    def test_physical_tests_have_early_and_ownership_guards(self):
        text = (self.root/'integration/s0s1_ops03/test_real.py').read_text()
        self.assertLess(text.index("OPS03_EXCLUSIVE_DISPOSABLE_LAB_REQUIRED"),
                        text.index('from integration.i86.manual'))
        self.assertIn('lab.laboratory()',text)
        self.assertIn('env = e.discover()',text)
        self.assertIn("path not in ('/auth/v1/logout?scope=global','/auth/v1/token?grant_type=refresh_token')",text)
        self.assertIn('COUNTEREXAMPLES_ONLY_NO_EXECUTOR_OR_TWO_PHASE_IMPLEMENTATION',text)
        self.assertNotIn('argparse',text)
        self.assertNotIn('https://',text)

    def test_nonlab_invocation_stops_before_dependencies_or_connections(self):
        env = os.environ.copy()
        for key in ('PRUMO_OPS03_DISPOSABLE','GITHUB_ACTIONS','RUNNER_ENVIRONMENT'):
            env.pop(key,None)
        import sys
        result = subprocess.run([sys.executable,'-B','-m','integration.s0s1_ops03.test_real'],
                                cwd=self.root,env=env,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'OPS03_EXCLUSIVE_DISPOSABLE_LAB_REQUIRED',result.stderr)
        self.assertNotIn(b'ModuleNotFoundError',result.stderr)

    def test_staging_has_no_database_or_http_capability(self):
        tree = ast.parse((self.root/'integration/s0s1_ops03/__init__.py').read_text())
        imports = {n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        imports |= {a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        self.assertEqual(imports,{'io','os','pathlib','shutil','subprocess','tarfile','tempfile','integration.s0s1_ops03.scope'})
        self.assertEqual(len(s.ALLOWED),10)

    def test_workflow_pins_sources_and_excludes_hosted_secrets_or_deployment(self):
        text = (self.root/'.github/workflows/exp-s0-s1-ops03-hosted-parity.yml').read_text()
        for required in ('persist-credentials: false','contents: read','shell: bash',
                         '0b0930778c29204904c1c1358a9a7ae9e3fff10b','PRUMO_OPS03_DISPOSABLE',
                         'integration.i86.cleanup','scope-and-contract','physical-disposable-compatibility'):
            self.assertIn(required,text)
        for forbidden in ('secrets.','supabase link','supabase db push','supabase deploy',
                          '.supabase.co','SUPABASE_ACCESS_TOKEN'):
            self.assertNotIn(forbidden,text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
