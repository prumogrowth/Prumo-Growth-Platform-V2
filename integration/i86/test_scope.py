"""Adversarial Git repositories; never mutate any project worktree."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
