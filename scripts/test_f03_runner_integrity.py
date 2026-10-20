"""Regression checks for the F03 pinned offline runner itself.

Temporary Python test files are fictional, no APIs, SQL, service or network.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parent / 'run_f03_offline_regression.py'
spec = importlib.util.spec_from_file_location('f03_offline_pinned_runner_under_test', SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='f03_runner_fixture_')
        self.root = Path(self.tmp.name)
        self.tests = self.root / 'backend' / 'tests'
        self.modules = self.root / 'backend' / 's0_openai_bridge'
        self.tests.mkdir(parents=True)
        self.modules.mkdir(parents=True)
        self.testfile = self.tests / 'test_f03_fixture_fake.py'
        self.modfile = self.modules / 'gate_fake.py'
        self.modfile.write_text('MODULE_FIXTURE = True\n', encoding='utf8')
        self.testfile.write_text('import unittest\nclass FakeCase(unittest.TestCase):\n'
                                 '    def test_ok(self): self.assertTrue(True)\n', encoding='utf8')
        self.valid_test_sha = runner.git_blob_sha(self.testfile)
        self.valid_module_sha = runner.git_blob_sha(self.modfile)
        self.cwd = Path.cwd()
        self.old_sys_path = list(sys.path)

    def tearDown(self):
        os.chdir(self.cwd)
        sys.path[:] = self.old_sys_path
        sys.modules.pop('test_f03_fixture_fake', None)
        self.tmp.cleanup()

    def invoke(self, *, allow_subset=False, expected_count=1, test_pin=None,
               module_pin=None, file_count=1):
        pins = (('test_f03_fixture_fake.py', file_count,
                 test_pin or self.valid_test_sha),)
        mod_pins = (('gate_fake.py', module_pin or self.valid_module_sha),)
        with patch.object(runner, 'ROOT', self.root), \
             patch.object(runner, 'TESTS', self.tests), \
             patch.object(runner, 'SUITES', pins), \
             patch.object(runner, 'MODULES', mod_pins), \
             patch.object(runner, 'EXPECTED_FULL_CASES', expected_count):
            return runner.run(allow_subset=allow_subset)

    def test_01_exact_pinned_fixture_runs_in_full_mode(self):
        self.assertEqual(self.invoke(), 0)

    def test_02_changed_test_same_count_is_rejected_before_import(self):
        pinned = runner.git_blob_sha(self.testfile)
        self.testfile.write_text(self.testfile.read_text() + '# changed without test count\n')
        self.assertEqual(self.invoke(test_pin=pinned), 2)
        self.assertNotIn('test_f03_fixture_fake', sys.modules)

    def test_03_changed_validator_is_rejected_before_import(self):
        original = runner.git_blob_sha(self.modfile)
        self.modfile.write_text('MODULE_FIXTURE = False\n')
        self.assertEqual(self.invoke(module_pin=original), 2)
        self.assertNotIn('test_f03_fixture_fake', sys.modules)

    def test_04_wrong_case_count_is_rejected(self):
        self.assertEqual(self.invoke(file_count=2), 2)

    def test_05_missing_test_fails_closed_without_subset(self):
        self.testfile.unlink()
        self.assertEqual(self.invoke(), 2)

    def test_06_missing_module_fails_even_for_partial_run(self):
        self.modfile.unlink()
        self.assertEqual(self.invoke(allow_subset=True), 2)

    def test_07_subset_cannot_be_claimed_as_full(self):
        self.assertEqual(self.invoke(expected_count=210), 2)
        self.assertEqual(self.invoke(allow_subset=True, expected_count=210), 0)

    def test_08_unapproved_top_level_side_effect_is_not_run(self):
        pinned = runner.git_blob_sha(self.testfile)
        marker = self.root / 'SHOULD_NOT_EXIST'
        self.testfile.write_text(self.testfile.read_text() +
                                 f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        self.assertEqual(self.invoke(test_pin=pinned), 2)
        self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
