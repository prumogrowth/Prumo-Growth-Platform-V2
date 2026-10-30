"""Adversarial Git repositories; never mutate any project worktree."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from integration.i86 import scope
from integration.i86.scope import BRANCH, WORKFLOW, changes, git, inspect


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="i86-git-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run_git("init", "-q", "-b", BRANCH)
        self.run_git("config", "user.name", "I86 Synthetic")
        self.run_git("config", "user.email", "i86@example.invalid")
        self.write("backend/inherited.py", "immutable\n")
        self.write(".gitignore", "*.cache\n")
        self.commit()
        self.base = git(self.root, "rev-parse", "HEAD").decode().strip()
        self.tree = git(self.root, "rev-parse", "HEAD^{tree}").decode().strip()

    def run_git(self, *args):
        return git(self.root, *args)

    def write(self, path, value):
        p = self.root/path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value)

    def commit(self):
        self.run_git("add", "-A")
        self.run_git("commit", "-qm", "synthetic scope fixture")

    def result(self):
        return inspect(self.root, self.base, self.tree)

    def test_allowed_committed_and_pending_inventory(self):
        self.write("integration/i86/new.py", "pass\n")
        self.commit()
        self.write("docs/contratos/i86_authority/new.md", "candidate\n")
        result = self.result()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual({p for r in result["files"] for p in r["paths"]},
                         {"integration/i86/new.py", "docs/contratos/i86_authority/new.md"})

    def test_inherited_committed_edit_blocks(self):
        self.write("backend/inherited.py", "changed\n")
        self.commit()
        self.assertIn("OUT_OF_SCOPE:backend/inherited.py", self.result()["violations"])

    def test_staged_violation_hidden_by_unstaged_revert_still_blocks(self):
        self.write("backend/inherited.py", "changed\n")
        self.run_git("add", "-A")
        self.write("backend/inherited.py", "immutable\n")
        result = self.result()
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(r["source"] == "staged" for r in result["files"]))

    def test_deleted_inherited_file_blocks(self):
        (self.root/"backend/inherited.py").unlink()
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_protected_edit_then_committed_revert_is_not_hidden(self):
        self.write("backend/inherited.py", "changed\n")
        self.commit()
        self.write("backend/inherited.py", "immutable\n")
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_rename_from_protected_into_allowlist_checks_both_names(self):
        self.run_git("mv", "backend/inherited.py", "backend/temp.py")
        (self.root/"integration/i86").mkdir(parents=True)
        self.run_git("mv", "backend/temp.py", "integration/i86/moved.py")
        self.commit()
        result = self.result()
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(len(r["paths"]) == 2 for r in result["files"]))

    def test_untracked_and_ignored_protected_files_block(self):
        self.write("frontend/untracked.txt", "not authorized\n")
        self.write("backend/hidden.cache", "not authorized\n")
        result = self.result()
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(r["status"] == "IGNORED" for r in result["files"]))

    def test_symlink_inside_allowlist_blocks(self):
        (self.root/"integration/i86").mkdir(parents=True)
        (self.root/"integration/i86/link").symlink_to("../../backend/inherited.py")
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_wrong_anchor_tree_blocks(self):
        self.assertEqual(inspect(self.root, self.base, "0"*40)["status"], "FAIL")

    def test_old_i86_workflow_is_protected_even_after_a_revert(self):
        path = ".github/workflows/exp-s1-i86-governanca.yml"
        self.write(path, "unauthorized edit\n")
        self.commit()
        self.run_git("rm", path)
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_only_new_manual_workflow_is_allowed(self):
        self.write(WORKFLOW, "name: synthetic scope fixture\n")
        self.commit()
        self.assertEqual(self.result()["status"], "PASS")

    def test_merge_of_other_front_blocks_even_with_allowed_final_diff(self):
        self.run_git("switch", "-qc", "other-front")
        self.write("integration/i86/other.py", "pass\n")
        self.commit()
        self.run_git("switch", "-q", BRANCH)
        self.write("integration/i86/ours.py", "pass\n")
        self.commit()
        self.run_git("merge", "--no-ff", "-qm", "unapproved merge", "other-front")
        self.assertTrue(any(v.startswith("NON_LINEAR_HISTORY") for v in self.result()["violations"]))

    def test_diff_parser_handles_newlines_and_two_rename_paths(self):
        self.assertEqual(changes(b"R100\0old\nname\0new\0"),
                         [{"status": "R100", "paths": ["old\nname", "new"]}])


class CM01Tests(unittest.TestCase):
    """Synthetic Git histories exercise the production exception algorithm."""
    run_git = ScopeTests.run_git
    write = ScopeTests.write
    commit = ScopeTests.commit

    def setUp(self):
        ScopeTests.setUp(self)
        self.old = {p: ('old:'+p+'\n').encode() for p in scope.CM01_FILES}
        self.new = {p: ('approved:'+p+'\n').encode() for p in scope.CM01_FILES}
        self.expected = {}
        for p in self.old:
            self.write(p, self.old[p].decode())
            self.expected[p] = {}
            for state, data in (("before", self.old[p]), ("after", self.new[p])):
                self.expected[p][state+"_sha256"] = hashlib.sha256(data).hexdigest()
                self.expected[p][state+"_blob"] = subprocess.check_output(
                    ["git", "hash-object", "--stdin"], input=data).decode().strip()
        self.commit()
        self.base = self.run_git("rev-parse", "HEAD").decode().strip()
        self.tree = self.run_git("rev-parse", "HEAD^{tree}").decode().strip()
        self.parent = self.base

    def result(self, base=None, tree=None):
        base, tree = base or self.base, tree or self.tree
        with patch.object(scope, "BASE", base), patch.object(scope, "BASE_TREE", tree), \
                patch.object(scope, "CM01_PARENT", self.parent), \
                patch.object(scope, "CM01_FILES", self.expected):
            return inspect(self.root, base, tree)

    def migrate(self):
        for p, data in self.new.items():
            self.write(p, data.decode())
        self.commit()

    def test_exact_paired_transition_passes_and_is_reported(self):
        self.migrate()
        r = self.result()
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["cm01"]["parent"], self.parent)
        self.assertEqual(r["cm01"]["commit"], r["head"])
        self.assertEqual(r["head_tree"], self.run_git("rev-parse", "HEAD^{tree}").decode().strip())

    def test_exception_does_not_expand_permitted(self):
        self.assertTrue(all(not scope.permitted(p) for p in self.expected))

    def test_missing_transition_blocks(self):
        self.assertEqual(self.result()["status"], "FAIL")

    def test_different_parent_blocks(self):
        self.write("integration/i86/intermediate.py", "pass\n")
        self.commit()
        self.migrate()
        self.assertIn("CM01_MIGRATION_PARENT", self.result()["violations"])

    def test_only_one_protected_file_blocks(self):
        p = next(iter(self.new))
        self.write(p, self.new[p].decode())
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_wrong_bytes_block(self):
        self.migrate()
        p = next(iter(self.new))
        self.write(p, "not approved\n")
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_wrong_bytes_in_migration_block(self):
        p = next(iter(self.new))
        self.new[p] += b"\n"
        self.migrate()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_mode_change_in_migration_blocks(self):
        for p, data in self.new.items():
            self.write(p, data.decode())
        (self.root/next(iter(self.new))).chmod(0o755)
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_protected_delete_blocks(self):
        self.migrate()
        (self.root/next(iter(self.new))).unlink()
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_protected_rename_blocks(self):
        self.migrate()
        (self.root/"integration/i86").mkdir(parents=True, exist_ok=True)
        self.run_git("mv", next(iter(self.new)), "integration/i86/renamed.json")
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_protected_symlink_blocks(self):
        self.migrate()
        p = self.root/next(iter(self.new))
        p.unlink()
        p.symlink_to("../../backend/inherited.py")
        self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_protected_gitlink_blocks(self):
        self.migrate()
        self.run_git("update-index", "--cacheinfo", "160000,"+self.parent+","+next(iter(self.new)))
        self.run_git("commit", "-qm", "synthetic unsafe gitlink")
        self.assertEqual(self.result()["status"], "FAIL")

    def test_staged_change_blocks(self):
        self.migrate()
        self.write(next(iter(self.new)), "staged divergence\n")
        self.run_git("add", "-A")
        self.assertIn("CM01_PROTECTED_PENDING", self.result()["violations"])

    def test_staged_change_hidden_by_worktree_revert_blocks(self):
        self.migrate()
        p = next(iter(self.new))
        self.write(p, "staged divergence\n")
        self.run_git("add", "-A")
        self.write(p, self.new[p].decode())
        self.assertEqual(self.result()["status"], "FAIL")

    def test_unstaged_change_blocks(self):
        self.migrate()
        self.write(next(iter(self.new)), "unstaged divergence\n")
        self.assertIn("CM01_PROTECTED_PENDING", self.result()["violations"])

    def test_assume_unchanged_cannot_hide_wrong_protected_bytes(self):
        self.migrate()
        p = next(iter(self.new))
        self.run_git("update-index", "--assume-unchanged", p)
        self.write(p, "hidden divergence\n")
        self.assertEqual(self.result()["status"], "FAIL")

    def test_third_protected_path_blocks(self):
        for p, data in self.new.items():
            self.write(p, data.decode())
        self.write("backend/inherited.py", "unauthorized\n")
        self.commit()
        self.assertIn("OUT_OF_SCOPE:backend/inherited.py", self.result()["violations"])

    def test_later_edit_and_revert_blocks(self):
        self.migrate()
        p = next(iter(self.new))
        self.write(p, "temporary divergence\n")
        self.commit()
        self.write(p, self.new[p].decode())
        self.commit()
        self.assertIn("CM01_MIGRATION_COUNT", self.result()["violations"])

    def test_split_transition_blocks(self):
        for p, data in self.new.items():
            self.write(p, data.decode())
            self.commit()
        self.assertEqual(self.result()["status"], "FAIL")

    def test_later_allowed_commit_passes(self):
        self.migrate()
        self.write("integration/i86/later.py", "pass\n")
        self.commit()
        self.assertEqual(self.result()["status"], "PASS")

    def test_wrong_tree_blocks(self):
        self.migrate()
        self.assertIn("BASE_TREE_CHANGED", self.result(tree="0"*40)["violations"])

    def test_non_ancestor_blocks(self):
        self.migrate()
        unrelated = self.run_git("commit-tree", self.tree, "-m", "synthetic unrelated root").decode().strip()
        self.assertIn("BASE_NOT_ANCESTOR", self.result(base=unrelated)["violations"])

    def test_merge_still_blocks(self):
        self.migrate()
        self.run_git("switch", "-qc", "other")
        self.write("integration/i86/theirs.py", "pass\n")
        self.commit()
        self.run_git("switch", "-q", BRANCH)
        self.write("integration/i86/ours.py", "pass\n")
        self.commit()
        self.run_git("merge", "--no-ff", "-qm", "synthetic merge", "other")
        self.assertTrue(any(v.startswith("NON_LINEAR_HISTORY") for v in self.result()["violations"]))


class SourceIntegrityTests(unittest.TestCase):
    """Only Git/filesystem operations; no database, CLI, Docker or HTTP."""
    S1 = "0b0930778c29204904c1c1358a9a7ae9e3fff10b"

    @classmethod
    def setUpClass(cls):
        cls.project = Path(__file__).resolve().parents[2]
        cls.tmp = tempfile.TemporaryDirectory(prefix="cm01-sources-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.source = Path(cls.tmp.name)/"s1"
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout",
                        str(cls.project), str(cls.source)], check=True, capture_output=True)
        git(cls.source, "checkout", "--quiet", "--detach", cls.S1)

    def setUp(self):
        from integration.history import prepare_s1_profile
        from local_admin import environment
        self.prepare, self.environment = prepare_s1_profile, environment
        self.manifest = json.loads((self.project/"integration/g1/s1_sources.json").read_text())
        self.tmp_root = tempfile.TemporaryDirectory(prefix="cm01-checkout-")
        self.addCleanup(self.tmp_root.cleanup)
        self.root = Path(self.tmp_root.name)
        deps = self.project/"local_admin/dependencies.json"
        self.dependencies = json.loads(deps.read_text())
        for path in [*self.dependencies["local_sources"], "local_admin/dependencies.json"]:
            target = self.root/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.project/path).read_bytes())
        self.addCleanup(lambda: git(self.source, "checkout", "--quiet", "--detach", self.S1))

    def checkout(self):
        with patch.object(self.environment, "ROOT", self.root):
            return self.environment.checkout()

    def verify(self, manifest=None):
        with patch.object(self.prepare, "ROOT", self.root):
            return self.prepare.verify_sources(self.source, manifest or self.manifest)

    def test_approved_values_and_current_manifest(self):
        active = json.loads((self.project/"docs/contratos/i86_authority/manual/CM01_MANIFESTO_PUBLICO.json").read_text())
        self.assertEqual(scope.BASE, "ae4bb16ac12086ad64509eff1c200b282fbd2f9f")
        self.assertEqual(scope.BASE_TREE, "3385f06bb477007c7d682f621227da422cf6fc5c")
        self.assertEqual(scope.CM01_PARENT, "89513a82c7fe00fd22ffb71384aef3636a143e42")
        self.assertEqual(active["protected_transition"], scope.CM01_FILES)
        self.assertEqual(self.manifest["ref"], self.S1)
        self.assertEqual(self.dependencies["s1_ref"], self.S1)
        for path, spec in scope.CM01_FILES.items():
            self.assertFalse(scope.permitted(path))
            self.assertEqual(hashlib.sha256((self.project/path).read_bytes()).hexdigest(), spec["after_sha256"])
        for path, digest in active["code_files"].items():
            self.assertEqual(hashlib.sha256((self.project/path).read_bytes()).hexdigest(), digest, path)

    def test_all_34_s1_digests_and_exact_tree(self):
        self.assertEqual(git(self.source, "rev-parse", "HEAD^{tree}").decode().strip(),
                         "e18d4d1c0b75f6a2ed9fa4d7c904737500fe3e0b")
        entries = self.manifest["files"]+self.manifest["test_sources"]
        self.assertEqual(len(entries), 34)
        for item in entries:
            self.assertEqual(hashlib.sha256(git(self.source, "show", self.S1+":"+item["path"])).hexdigest(), item["sha256"])

    def test_unchanged_verifier_accepts_27_sources(self):
        self.assertEqual(len(self.verify()), 27)

    def test_old_ref_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["ref"] = "8780b576aa18bd3983c063339e2e42d2452af22c"
        with self.assertRaisesRegex(RuntimeError, "PINNED_S1_HEAD_MISMATCH"):
            self.verify(manifest)

    def test_other_real_commit_rejected(self):
        git(self.source, "checkout", "--quiet", "--detach", self.S1+"^")
        with self.assertRaisesRegex(RuntimeError, "PINNED_S1_HEAD_MISMATCH"):
            self.verify()

    def test_wrong_source_digest_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["files"][0]["sha256"] = "0"*64
        with self.assertRaisesRegex(RuntimeError, "PINNED_S1_HASH_MISMATCH"):
            self.verify(manifest)

    def test_overlap_drift_rejected(self):
        (self.root/"supabase/migrations/202610170001_s0_foundation.sql").write_text("-- divergent\n")
        with self.assertRaisesRegex(RuntimeError, "PINNED_S1_OVERLAP_MISMATCH"):
            self.verify()

    def test_reference_038_drift_rejected(self):
        (self.root/"supabase/tests/s0_cfi01_s1_038_reference_local_only.sql").write_text("-- divergent\n")
        with self.assertRaisesRegex(RuntimeError, "PINNED_S1_REFERENCE_MISMATCH"):
            self.verify()

    def test_exact_62_dependencies_pass(self):
        self.assertEqual(len(self.checkout()["local_sources"]), 62)

    def test_stale_dependent_digest_rejected(self):
        self.dependencies["local_sources"]["integration/g1/s1_sources.json"] = scope.CM01_FILES["integration/g1/s1_sources.json"]["before_sha256"]
        (self.root/"local_admin/dependencies.json").write_text(json.dumps(self.dependencies))
        with self.assertRaisesRegex(RuntimeError, "CERTIFIED_SOURCE_DRIFT"):
            self.checkout()

    def test_one_byte_drift_rejected(self):
        p = self.root/"integration/g1/s1_sources.json"
        p.write_bytes(p.read_bytes()+b"\n")
        with self.assertRaisesRegex(RuntimeError, "CERTIFIED_SOURCE_DRIFT"):
            self.checkout()

    def test_extra_migration_rejected(self):
        (self.root/"supabase/migrations/999999999999_synthetic.sql").write_text("-- synthetic\n")
        with self.assertRaisesRegex(RuntimeError, "UNCERTIFIED_SOURCE_ADDED"):
            self.checkout()

    def test_seed_rejected(self):
        (self.root/"supabase/seed.sql").write_text("-- synthetic\n")
        with self.assertRaisesRegex(RuntimeError, "UNCERTIFIED_SEED_FORBIDDEN"):
            self.checkout()

    def test_hosted_link_rejected(self):
        p = self.root/"supabase/.temp/project-ref"
        p.parent.mkdir(exist_ok=True)
        p.write_text("synthetic")
        with self.assertRaisesRegex(RuntimeError, "HOSTED_PROJECT_LINK_FORBIDDEN"):
            self.checkout()

    def test_sandbox_rejects_dirty_pinned_source(self):
        from integration.i86 import sandbox
        # Pure unit fixture: only the pre-staging guards are reached. The
        # mocked runner claims never authorize a database or container action.
        root = self.source.parent/"stage"
        path = root/"integration/i86/.runtime/s1"
        path.parent.mkdir(parents=True)
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout",
                        str(self.project), str(path)], check=True, capture_output=True)
        git(path, "checkout", "--quiet", "--detach", self.S1)
        (path/"synthetic-untracked.txt").write_text("synthetic\n")
        with patch.object(sandbox, "__file__", str(root/"integration/i86/sandbox.py")), \
                patch.object(sandbox, "inspect", return_value={"status": "PASS"}), \
                patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "PRUMO_I86_RUNNER_ISOLATION": "github-hosted",
                                        "RUNNER_TEMP": self.tmp.name}):
            with self.assertRaisesRegex(RuntimeError, "I86_PINNED_SOURCE_DIRTY"):
                sandbox.main()


if __name__ == "__main__":
    unittest.main(verbosity=2)
