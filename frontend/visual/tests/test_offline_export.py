"""FV-UI-024 — testes locais, sem rede, do verificador de ZIP privado.
Executar: python3 -m unittest discover -s frontend/visual/tests -p test_offline_export.py
Fixtures são bytes inventados; não são dados de clientes ou arquivos reais.
"""
import importlib.util
import json
import contextlib
import io
import sys
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, BadZipFile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fv_ui_offline_verifier", HERE / "verify_offline_export.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

PREFIX = "Prumo-Growth---Platform-feat-frontend-plataforma-visual/"
DATA_PATH = "frontend/visual/index.html"
VERIFY_PATH = "frontend/visual/tests/verify_offline_export.py"


class OfflineExportIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fv-ui-024-")
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "synthetic.zip"
        self.payload = b"<html>offline synthetic fixture</html>\n"
        self.verifier_bytes = (HERE / "verify_offline_export.py").read_bytes()
        self.fake_manifest = {
            "source_head": "a" * 40,
            "source_branch": "feat/frontend-plataforma-visual",
            "files": {DATA_PATH: {
                "size": len(self.payload),
                "sha": verifier.blob_sha(self.payload),
            }},
        }
        self.patch_manifest = patch.object(verifier, "MANIFEST", self.fake_manifest)
        self.patch_manifest.start()
        self.addCleanup(self.patch_manifest.stop)

    def make_zip(self, *, data=None, extras=(), verifier_data=None):
        if data is None:
            data = self.payload
        if verifier_data is None:
            verifier_data = self.verifier_bytes
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as z:
            z.writestr(PREFIX + DATA_PATH, data)
            z.writestr(PREFIX + VERIFY_PATH, verifier_data)
            for name, value in extras:
                z.writestr(name, value)
        return self.archive

    def test_happy_path_only_explicitly_pinned_data_and_verifier(self):
        result = verifier.load_verified(self.make_zip())
        self.assertEqual(result[DATA_PATH], self.payload)
        self.assertEqual(result[VERIFY_PATH], self.verifier_bytes)
        self.assertEqual(set(result), {DATA_PATH, VERIFY_PATH})

    def test_modified_blob_rejected(self):
        with self.assertRaisesRegex(ValueError, "Git blob hash mismatch"):
            verifier.load_verified(self.make_zip(data=b"corrupt data"))

    def test_same_size_tampered_blob_rejected(self):
        tampered = b"X" + self.payload[1:]
        self.assertEqual(len(tampered), len(self.payload))
        with self.assertRaisesRegex(ValueError, "Git blob hash mismatch"):
            verifier.load_verified(self.make_zip(data=tampered))

    def test_extra_frontend_file_rejected_even_if_not_extracted(self):
        extra = PREFIX + "frontend/visual/unsafe-extra.mjs"
        with self.assertRaisesRegex(ValueError, "Unpinned or missing"):
            verifier.load_verified(self.make_zip(extras=[(extra, b"alert(1)")]))
    
    def test_total_uncompressed_frontend_budget_is_bounded(self):
        # Dados altamente compressíveis: verifica tamanho declarado descompactado.
        big = b"Z" * 13_000_000
        with self.assertRaisesRegex(ValueError, "uncompressed budget exceeded"):
            verifier.load_verified(self.make_zip(extras=[
                (PREFIX + "frontend/visual/large-1.bin", big),
                (PREFIX + "frontend/visual/large-2.bin", big),
            ]))

    def test_missing_required_member_rejected(self):
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as z:
            z.writestr(PREFIX + VERIFY_PATH, self.verifier_bytes)
        with self.assertRaisesRegex(ValueError, "Unpinned or missing"):
            verifier.load_verified(self.archive)

    def test_duplicate_archive_member_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate file entries"):
            verifier.load_verified(self.make_zip(extras=[(PREFIX + DATA_PATH, self.payload)]))

    def test_changed_verifier_rejected(self):
        with self.assertRaisesRegex(ValueError, "Offline verifier differs"):
            verifier.load_verified(self.make_zip(verifier_data=b"# malicious verifier"))

    def test_path_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsafe path"):
            verifier.load_verified(self.make_zip(extras=[(PREFIX + "../escape.txt", b"x")]))

    def test_absolute_path_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsafe path"):
            verifier.load_verified(self.make_zip(extras=[("/tmp/bad.txt", b"x")]))

    def test_symlink_rejected(self):
        link = ZipInfo(PREFIX + "other-link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as z:
            z.writestr(PREFIX + DATA_PATH, self.payload)
            z.writestr(PREFIX + VERIFY_PATH, self.verifier_bytes)
            z.writestr(link, "another-file")
        with self.assertRaisesRegex(ValueError, "Symbolic links"):
            verifier.load_verified(self.archive)

    def test_multiple_frontend_roots_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one frontend/visual root"):
            verifier.load_verified(self.make_zip(extras=[
                ("other-branch/" + DATA_PATH, self.payload)]))

    def test_absent_root_rejected(self):
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as z:
            z.writestr("anything.txt", b"no frontend")
        with self.assertRaisesRegex(ValueError, "exactly one frontend/visual root"):
            verifier.load_verified(self.archive)

    def test_invalid_zip_rejected_by_archive_reader(self):
        self.archive.write_bytes(b"not zip")
        with self.assertRaises(BadZipFile):
            verifier.load_verified(self.archive)

    def _run_main_with_fake_verified_snapshot(self, security_result):
        # Isola somente a sequência dos gates, sem executar Node/Chromium.
        fake_files = {DATA_PATH: self.payload, VERIFY_PATH: self.verifier_bytes}
        args = ["verify_offline_export.py", "--archive", str(self.archive),
                "--run-native"]
        with patch.object(verifier, "load_verified", return_value=fake_files), \
             patch.object(verifier, "execute",
                          return_value=security_result if not isinstance(security_result, list) else None,
                          side_effect=security_result if isinstance(security_result, list) else None) as run, \
             patch.object(sys, "argv", args), \
             contextlib.redirect_stdout(io.StringIO()):
            result = verifier.main()
        return result, run

    def test_native_gates_block_after_security_failure(self):
        result, run = self._run_main_with_fake_verified_snapshot(
            {"executed": True, "passed": False, "exit_code": 1})
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 1, "Node/Chromium must not start")
        self.assertIn("test_offline_export.py", str(run.call_args_list[0]))

    def test_native_gates_block_if_python_security_not_executed(self):
        result, run = self._run_main_with_fake_verified_snapshot(
            {"executed": False, "passed": False, "error": "unavailable"})
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 1, "Node/Chromium must not start")

    def test_native_gates_block_chromium_after_node_failure(self):
        result, run = self._run_main_with_fake_verified_snapshot([
            {"executed": True, "passed": True, "exit_code": 0},
            {"executed": True, "passed": False, "exit_code": 1},
        ])
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 2, "Chromium must not start")
        self.assertIn("--test", run.call_args_list[1].args[0])

    def test_native_gates_block_chromium_if_node_not_executed(self):
        result, run = self._run_main_with_fake_verified_snapshot([
            {"executed": True, "passed": True, "exit_code": 0},
            {"executed": False, "passed": False, "error": "no node"},
        ])
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 2)

    def test_native_gates_run_only_after_python_security_passes(self):
        result, run = self._run_main_with_fake_verified_snapshot(
            {"executed": True, "passed": True, "exit_code": 0})
        self.assertEqual(result, 0, "Mocked gates all passed")
        self.assertEqual(run.call_count, 3,
                         "security, Node, Chromium execute in that order")
        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn("unittest", commands[0])
        self.assertIn("-B", commands[0], "Do not write __pycache__ in verified tree")
        self.assertIn("--test", commands[1])
        self.assertTrue(str(commands[2][-1]).endswith("browser.smoke.py"))

    def test_manifest_pinning_is_git_blob_hash_not_plain_sha(self):
        self.assertEqual(len(verifier.blob_sha(self.payload)), 40)
        import hashlib
        self.assertNotEqual(verifier.blob_sha(self.payload),
                            hashlib.sha1(self.payload).hexdigest())




class NativeCheckoutPreflightTests(unittest.TestCase):
    """FV-UI-045 — regressões isoladas de um repositório Git sintético, sem rede."""

    def setUp(self):
        import json
        import subprocess
        self.temp = tempfile.TemporaryDirectory(prefix="fv-ui-045-git-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.visual = self.root / "frontend" / "visual"
        self.tests = self.visual / "tests"
        self.tests.mkdir(parents=True)
        spec = importlib.util.spec_from_file_location("fv_ui_native_acceptance",
                                                     HERE / "run_acceptance.py")
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)
        self.patch_root = patch.object(self.runner, "ROOT", self.visual)
        self.patch_tests = patch.object(self.runner, "TESTS", self.tests)
        self.patch_root.start(); self.patch_tests.start()
        self.addCleanup(self.patch_root.stop); self.addCleanup(self.patch_tests.stop)

        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), *args],
                                  capture_output=True, text=True, check=True).stdout.strip()
        self.git = git
        subprocess.run(["git", "init", "-q", "-b", "feat/frontend-plataforma-visual",
                        str(self.root)], check=True, capture_output=True)
        git("config", "user.name", "Local Fixture")
        git("config", "user.email", "fixture@invalid.local")
        git("commit", "-q", "--allow-empty", "-m", "synthetic root")
        source = git("rev-parse", "HEAD")
        self.data_path = "frontend/visual/index.html"
        body = b"<main>only synthetic evidence</main>\n"
        (self.visual / "index.html").write_bytes(body)
        pinned = {
            "source_head": source,
            "source_branch": "feat/frontend-plataforma-visual",
            "files": {self.data_path: {"sha": verifier.blob_sha(body), "size": len(body)}},
        }
        (self.tests / "verify_offline_export.py").write_text(
            "import json\nMANIFEST = json.loads(" + json.dumps(json.dumps(pinned)) + ")\n",
            encoding="utf-8")
        git("add", ".")
        git("commit", "-q", "-m", "pinned synthetic visual tree")
        self.head = git("rev-parse", "HEAD")

    def test_native_manifest_accepts_complete_unchanged_git_tree(self):
        result = self.runner.check_native_blob_manifest(self.head, True)
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["executed"])
        self.assertEqual(result["files_checked"], 2)

    def test_native_manifest_rejects_modified_worktree_blob(self):
        (self.visual / "index.html").write_text("tampered content", encoding="utf-8")
        result = self.runner.check_native_blob_manifest(self.head, True)
        self.assertFalse(result["passed"])
        self.assertIn("working-tree blob mismatch", result["error"])

    def test_native_manifest_rejects_unpinned_committed_blob(self):
        (self.visual / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "unlisted synthetic blob")
        actual = self.git("rev-parse", "HEAD")
        result = self.runner.check_native_blob_manifest(actual, True)
        self.assertFalse(result["passed"])
        self.assertIn("Git tree inventory differs", result["error"])

    def test_native_manifest_rejects_unverified_checkout(self):
        result = self.runner.check_native_blob_manifest(self.head, False)
        self.assertFalse(result["passed"])
        self.assertFalse(result["executed"])

class AcceptanceInventoryGuardTests(unittest.TestCase):
    """FV-UI-046: impede que o runner deixe um *.test.mjs sem registro."""

    def test_every_node_test_is_registered_by_acceptance(self):
        import ast
        source = (HERE / "run_acceptance.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        registrations = [node for node in ast.walk(tree)
                         if isinstance(node, ast.Assign)
                         and any(isinstance(target, ast.Name)
                                 and target.id == "expected_tests"
                                 for target in node.targets)]
        self.assertEqual(len(registrations), 1)
        expected = ast.literal_eval(registrations[0].value)
        actual = {path.name for path in HERE.glob("*.test.mjs")}
        self.assertEqual(expected, actual)
        self.assertIn("app.tablet.dom.test.mjs", expected)


if __name__ == "__main__":
    unittest.main()
