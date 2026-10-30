"""Synthetic OPS-02 contracts, capability boundary and artificial Git attacks."""
import ast
from contextlib import redirect_stdout
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ops.s0s1_authority import validate as v
from integration.s0s1_ops02 import scope as s

ROOT = Path(__file__).absolute().parents[2]
ACT = "10000000-0000-4000-8000-000000000001"
TARGET = "20000000-0000-4000-8000-000000000001"
ATTEMPT = "30000000-0000-4000-8000-000000000001"


def seal(document):
    document["digest"] = v.document_digest(document)
    return document


def intention(action="APPOINT"):
    return seal({"version": v.VERSION, "kind": "INTENTION",
                 "data_classification": "SYNTHETIC", "authorizes_action": False,
                 "act_id": ACT, "action": action, "target_id": TARGET,
                 "environment": {"kind": "SYNTHETIC_OFFLINE", "id": "synthetic:lab-01"},
                 "cas": {"scheme": "i86.snapshot.sha256", "observed_sha256": "a" * 64},
                 "operator_ref": "synthetic:operator-01", "authorization_ref": "synthetic:record-01",
                 "evidence": {"ref": "synthetic:intent-01", "sha256": "b" * 64}})


def receipt(intent=None, state="RECONCILED_DECLARED"):
    intent = intention() if intent is None else intent
    document = {k: copy.deepcopy(intent[k]) for k in v.COMMON if k != "digest"}
    document.update(kind="RECEIPT", intention_digest=intent["digest"], attempt_id=ATTEMPT,
                    state=state, commit_claim=v.STATES[state][0],
                    posterior_evidence={"ref": "synthetic:receipt-01", "sha256": "c" * 64})
    return seal(document)


def raw(document):
    return json.dumps(document, ensure_ascii=True).encode()


class ContractTests(unittest.TestCase):
    def check_result(self, documents, code=None):
        report = v.validate_bytes([raw(d) for d in documents])
        self.assertIs(report["authorizes_action"], False)
        for key in ("human_identity_verified", "organizational_authorization_verified",
                    "origin_authenticated", "referenced_evidence_bytes_verified", "commit_proven"):
            self.assertIs(report[key], False)
        self.assertEqual(report["status"], "INVALID_UNTRUSTED" if code else "FORMALLY_VALID_UNTRUSTED")
        if code:
            self.assertEqual(report["errors"][0]["code"], code)
        return report

    def test_appoint(self):
        self.check_result([intention("APPOINT")])

    def test_revoke(self):
        self.check_result([intention("REVOKE")])

    def test_reactivate(self):
        self.check_result([intention("REACTIVATE")])

    def test_receipt_each_state_remains_untrusted(self):
        for state in v.STATES:
            with self.subTest(state=state):
                self.check_result([intention(), receipt(state=state)])

    def test_receipt_all_actions(self):
        for action in v.ACTIONS:
            document = intention(action)
            self.check_result([document, receipt(document)])

    def test_determinism_and_input_order(self):
        docs = [raw(intention()), raw(receipt())]
        expected = v.validate_bytes(docs)
        for _ in range(3):
            self.assertEqual(v.validate_bytes(docs), expected)
        self.assertEqual(v.validate_bytes(list(reversed(docs))), expected)

    def test_canonical_bytes_independent_vector(self):
        doc = intention()
        independent = json.dumps({k: val for k, val in doc.items() if k != "digest"},
                                 ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected = hashlib.sha256(b"prumo.s0s1.authority.evidence.v1\0INTENTION\0" + independent).hexdigest()
        self.assertEqual(doc["digest"], expected)
        self.assertEqual(v.canonical_bytes(doc), independent)

    def test_digest_excludes_only_itself(self):
        doc = intention()
        first = doc["digest"]
        doc["digest"] = "f" * 64
        self.assertEqual(v.document_digest(doc), first)
        doc["declared_at"] = "2026-10-30T16:00:00Z"
        self.assertNotEqual(v.document_digest(doc), first)
        self.check_result([seal(doc)])

    def test_formatted_json_same_semantics(self):
        report = v.validate_bytes([json.dumps(intention(), indent=2).encode()])
        self.assertEqual(report["status"], "FORMALLY_VALID_UNTRUSTED")
        self.assertIs(report["authorizes_action"], False)

    def test_uuid_invalid_and_noncanonical(self):
        for value in ("bad", "00000000-0000-0000-0000-000000000000", TARGET.upper().replace("2", "A", 1), TARGET.replace("-", "")):
            doc = intention()
            doc["target_id"] = value
            self.check_result([seal(doc)], "INVALID_UUID")

    def test_hash_invalid(self):
        for value in ("a" * 63, "A" * 64, "g" * 64):
            doc = intention()
            doc["evidence"]["sha256"] = value
            self.check_result([seal(doc)], "INVALID_SHA256")

    def test_missing_required_fields(self):
        for field in v.INTENTION_FIELDS - {"version", "kind"}:
            doc = intention()
            del doc[field]
            self.check_result([doc], "MISSING_FIELD")

    def test_missing_receipt_fields(self):
        for field in v.RECEIPT_FIELDS - {"version", "kind"}:
            doc = receipt()
            del doc[field]
            self.check_result([intention(), doc], "MISSING_FIELD")

    def test_unknown_fields_at_all_levels(self):
        for location in (None, "environment", "cas", "evidence"):
            doc = intention()
            (doc if location is None else doc[location])["unexpected"] = "synthetic:extra"
            self.check_result([seal(doc)], "UNKNOWN_FIELD")

    def test_unknown_version(self):
        doc = intention()
        doc["version"] = "v999"
        self.check_result([seal(doc)], "UNSUPPORTED_VERSION")

    def test_unknown_kind(self):
        doc = intention()
        doc["kind"] = "EXECUTE"
        self.check_result([seal(doc)], "UNKNOWN_KIND")

    def test_unknown_action(self):
        doc = intention()
        doc["action"] = "BOOTSTRAP"
        self.check_result([seal(doc)], "UNKNOWN_ACTION")

    def test_environment_target_action_and_cas_binding(self):
        for key, value in (("environment", {"kind": "SYNTHETIC_OFFLINE", "id": "synthetic:other"}),
                           ("target_id", "20000000-0000-4000-8000-000000000002"),
                           ("action", "REVOKE"),
                           ("cas", {"scheme": "i86.snapshot.sha256", "observed_sha256": "d" * 64})):
            with self.subTest(key=key):
                doc = receipt()
                doc[key] = value
                self.check_result([intention(), seal(doc)], "BINDING_MISMATCH")

    def test_cas_scheme_incompatible(self):
        doc = intention()
        doc["cas"]["scheme"] = "jwt-role"
        self.check_result([seal(doc)], "UNKNOWN_CAS")

    def test_digest_tampered(self):
        doc = intention()
        doc["operator_ref"] = "synthetic:different"
        self.check_result([doc], "DIGEST_MISMATCH")

    def test_receipt_wrong_intention_digest(self):
        doc = receipt()
        doc["intention_digest"] = "e" * 64
        self.check_result([intention(), seal(doc)], "INTENTION_DIGEST_MISMATCH")

    def test_receipt_wrong_act_id(self):
        doc = receipt()
        doc["act_id"] = "10000000-0000-4000-8000-000000000002"
        self.check_result([intention(), seal(doc)], "INTENTION_NOT_FOUND")

    def test_receipt_alone_rejected(self):
        self.check_result([receipt()], "INTENTION_REQUIRED")

    def test_receipt_contradictory(self):
        doc = receipt(state="COMMIT_NOT_PROVEN")
        doc["commit_claim"] = "DECLARED_COMMITTED"
        self.check_result([intention(), seal(doc)], "CONTRADICTORY_RECEIPT")

    def test_unknown_receipt_state(self):
        doc = receipt()
        doc["state"] = "COMMIT_PROVEN"
        self.check_result([intention(), seal(doc)], "UNKNOWN_RECEIPT_STATE")

    def test_duplicate_act_id_different_content(self):
        self.check_result([intention(), intention("REVOKE")], "ACT_ID_CONTENT_CONFLICT")

    def test_duplicate_attempt_id_different_content(self):
        self.check_result([intention(), receipt(), receipt(state="COMMIT_NOT_PROVEN")], "ATTEMPT_CONTENT_CONFLICT")

    def test_identical_duplicates_do_not_authorize(self):
        self.check_result([intention(), intention(), receipt(), receipt()])

    def test_human_authentication_claim_rejected(self):
        for key in ("human_verified", "human_authorized", "signature", "sql_principal", "approved"):
            doc = intention()
            doc[key] = True
            self.check_result([seal(doc)], "UNKNOWN_FIELD")

    def test_commit_confirmed_payload_rejected(self):
        doc = receipt()
        doc["commit_confirmed"] = True
        self.check_result([intention(), seal(doc)], "UNKNOWN_FIELD")
        del doc["commit_confirmed"]
        doc["commit_claim"] = "CONFIRMED"
        self.check_result([intention(), seal(doc)], "CONTRADICTORY_RECEIPT")

    def test_credentials_and_personal_fields_rejected(self):
        for key in ("token", "password", "service_role", "jwt", "full_name", "cpf", "sql", "execute"):
            doc = intention()
            doc[key] = "synthetic:forbidden"
            self.check_result([seal(doc)], "UNKNOWN_FIELD")

    def test_operational_permission_claim_rejected(self):
        doc = intention()
        doc["authorizes_action"] = True
        self.check_result([seal(doc)], "AUTHORIZATION_CLAIM_FORBIDDEN")
        doc["authorizes_action"] = "false"
        self.check_result([seal(doc)], "AUTHORIZATION_CLAIM_FORBIDDEN")

    def test_real_environment_rejected(self):
        doc = intention()
        doc["environment"]["kind"] = "PRODUCTION"
        self.check_result([seal(doc)], "SYNTHETIC_ONLY")

    def test_non_synthetic_classification_rejected(self):
        doc = intention()
        doc["data_classification"] = "REAL"
        self.check_result([seal(doc)], "SYNTHETIC_ONLY")

    def test_reference_not_a_url_or_email(self):
        for value in ("https://example.invalid", "fictitious@example.invalid", "synthetic:../escape", "synthetic:a\n"):
            doc = intention()
            doc["operator_ref"] = value
            self.check_result([seal(doc)], "INVALID_SYNTHETIC_REFERENCE")

    def test_optional_time_and_no_null_default(self):
        for value in ("2026-02-30T16:00:00Z", "2026-10-30T16:00:00-03:00", "2026-10-30T16:00:00Z\n"):
            doc = intention()
            doc["declared_at"] = value
            self.check_result([seal(doc)], "INVALID_DECLARED_TIME")
        doc["declared_at"] = None
        self.check_result([seal(doc)], "UNSUPPORTED_JSON_VALUE")

    def test_malformed_and_duplicate_json(self):
        for data, code in ((b"{", "MALFORMED_JSON"), (b"\xff", "MALFORMED_JSON"),
                           (b'{"a":true,"a":false}', "DUPLICATE_JSON_KEY"),
                           (b'{"a":NaN}', "NONFINITE_JSON_NUMBER"),
                           (b'[]', "ARRAY_NOT_SUPPORTED"), (b'{"a":1}', "UNSUPPORTED_JSON_VALUE"),
                           (b'{"a":1.1}', "UNSUPPORTED_JSON_VALUE")):
            report = v.validate_bytes([data])
            self.assertEqual(report["errors"][0]["code"], code)
            self.assertIs(report["authorizes_action"], False)

    def test_size_count_and_depth_limits(self):
        for docs, code in (([], "DOCUMENT_COUNT_LIMIT"), ([raw(intention())] * 33, "DOCUMENT_COUNT_LIMIT"),
                           ([b" " * 65537], "DOCUMENT_SIZE_LIMIT"),
                           ([b" " * 65536] * 17, "TOTAL_SIZE_LIMIT"),
                           ([b'{"a":' * 10 + b'true' + b'}' * 10], "MAX_DEPTH_EXCEEDED"),
                           (["text"], "BYTES_REQUIRED")):
            report = v.validate_bytes(docs)
            self.assertEqual(report["errors"][0]["code"], code)
            self.assertIs(report["authorizes_action"], False)

    def test_contract_machine_readable_matches_implementation(self):
        contract = json.loads((ROOT / "ops/s0s1_authority/contract_v1.json").read_text())
        self.assertEqual(contract["version"], v.VERSION)
        self.assertEqual(set(contract["intention_required"]), v.INTENTION_FIELDS)
        self.assertEqual(set(contract["receipt_required"]), v.RECEIPT_FIELDS)
        self.assertEqual(contract["receipt_states"], {k: list(val) for k, val in v.STATES.items()})
        self.assertEqual(contract["actions"], list(v.ACTIONS))
        self.assertEqual(contract["limits"]["documents"], v.MAX_DOCUMENTS)
        self.assertEqual(contract["limits"]["bytes_per_document"], v.MAX_BYTES)
        self.assertEqual(contract["limits"]["total_bytes"], v.MAX_TOTAL_BYTES)
        self.assertEqual(contract["limits"]["depth"], v.MAX_DEPTH)
        self.assertIs(contract["authorizes_action"], False)

    def test_documented_synthetic_models(self):
        document = (ROOT / "docs/contratos/s0s1_ops02/CONTRATO_CANDIDATO.md").read_text()
        blocks = re.findall(r"```json\n(.*?)\n```", document, re.DOTALL)
        self.assertEqual(len(blocks), 2)
        report = v.validate_bytes([block.encode() for block in blocks])
        self.assertEqual(report["status"], "FORMALLY_VALID_UNTRUSTED")
        self.assertIs(report["authorizes_action"], False)


class PathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ops02-input-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "intent.json").write_bytes(raw(intention()))

    def cli(self, args):
        out = io.StringIO()
        with redirect_stdout(out):
            status = v.main(args)
        report = json.loads(out.getvalue())
        self.assertIs(report["authorizes_action"], False)
        return status, report

    def test_explicit_files_only(self):
        (self.root / "unmentioned.json").write_text("not json")
        code, report = self.cli(["--input-root", str(self.root), "intent.json"])
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "FORMALLY_VALID_UNTRUSTED")

    def test_nested_regular_file(self):
        (self.root / "nested").mkdir()
        (self.root / "nested/copy.json").write_bytes(raw(intention()))
        self.assertEqual(self.cli(["--input-root", str(self.root), "nested/copy.json"])[0], 0)

    def test_path_traversal_absolute_and_globs(self):
        for name in ("../intent.json", "/intent.json", "./intent.json", "a/../intent.json", "*.json", "a//x.json", "a\\x.json", "a\nx.json", "a.txt", "--execute", "a/" * 8 + "x.json", "a" * 257 + ".json"):
            code, report = self.cli(["--input-root", str(self.root), name])
            self.assertEqual(code, 2)
            self.assertEqual(report["errors"][0]["code"], "UNSAFE_PATH")

    def test_symlink_leaf_and_directory(self):
        (self.root / "link.json").symlink_to(self.root / "intent.json")
        (self.root / "linkdir").symlink_to(self.root, target_is_directory=True)
        for name in ("link.json", "linkdir/intent.json"):
            code, report = self.cli(["--input-root", str(self.root), name])
            self.assertEqual(code, 2)
            self.assertEqual(report["errors"][0]["code"], "UNSAFE_OR_UNREADABLE_PATH")

    def test_symlink_root_and_parent(self):
        (self.root / "linkdir").symlink_to(self.root, target_is_directory=True)
        for root in (str(self.root / "linkdir"), str(self.root / "linkdir/sub")):
            self.assertEqual(self.cli(["--input-root", root, "intent.json"])[0], 2)

    def test_root_path_boundaries(self):
        for root in ("/", ".", "relative", str(self.root) + "/../x", str(self.root) + "/"):
            self.assertEqual(self.cli(["--input-root", root, "intent.json"])[1]["errors"][0]["code"], "UNSAFE_ROOT")

    def test_fifo_hardlink_directory(self):
        os.mkfifo(self.root / "fifo.json")
        os.link(self.root / "intent.json", self.root / "hard.json")
        (self.root / "dir.json").mkdir()
        for name in ("fifo.json", "hard.json", "dir.json"):
            self.assertEqual(self.cli(["--input-root", str(self.root), name])[1]["errors"][0]["code"], "UNSAFE_FILE_TYPE")

    def test_missing_and_oversized_file(self):
        self.assertEqual(self.cli(["--input-root", str(self.root), "absent.json"])[0], 2)
        (self.root / "large.json").write_bytes(b" " * 65537)
        self.assertEqual(self.cli(["--input-root", str(self.root), "large.json"])[1]["errors"][0]["code"], "DOCUMENT_SIZE_LIMIT")

    def test_usage_and_dangerous_commands(self):
        for args in ([], ["--execute"], ["--sql", "SELECT 1"], ["--input-root", str(self.root)],
                     ["--network", "https://example.invalid"], ["--authorize", "true"]):
            code, report = self.cli(args)
            self.assertEqual(code, 2)
            self.assertEqual(report["errors"][0]["code"], "USAGE")

    def test_read_only_open_flags(self):
        original, seen = os.open, []
        def opened(path, flags, *args, **kwargs):
            seen.append(flags)
            return original(path, flags, *args, **kwargs)
        with patch.object(v.os, "open", side_effect=opened):
            self.assertEqual(self.cli(["--input-root", str(self.root), "intent.json"])[0], 0)
        self.assertTrue(seen)
        for flags in seen:
            self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            self.assertTrue(flags & os.O_NOFOLLOW)


class CapabilityTests(unittest.TestCase):
    def test_validator_import_and_call_surface(self):
        syntax = ast.parse((ROOT / "ops/s0s1_authority/validate.py").read_text())
        imports = set()
        forbidden_calls = {"eval", "exec", "compile", "__import__", "getattr", "setattr", "open", "input", "breakpoint"}
        allowed_os = {"open", "read", "close", "fstat", "O_RDONLY", "O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK"}
        for node in ast.walk(syntax):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, forbidden_calls)
            elif isinstance(node, ast.Attribute):
                self.assertFalse(node.attr.startswith("__"))
                if isinstance(node.value, ast.Name) and node.value.id == "os":
                    self.assertIn(node.attr, allowed_os)
                if isinstance(node.value, ast.Name) and node.value.id == "sys":
                    self.assertIn(node.attr, {"argv", "exit"})
            elif isinstance(node, ast.Assert):
                self.fail("Security validation cannot depend on assert / Python optimization")
        self.assertEqual(imports, {"hashlib", "json", "os", "re", "stat", "sys", "uuid", "datetime"})

    def test_document_validation_has_no_external_effect(self):
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("process forbidden")), \
             patch.object(os, "system", side_effect=AssertionError("shell forbidden")), \
             patch.object(os, "open", side_effect=AssertionError("implicit reads forbidden")):
            report = v.validate_bytes([raw(intention()), raw(receipt())])
        self.assertEqual(report["status"], "FORMALLY_VALID_UNTRUSTED")
        self.assertIs(report["authorizes_action"], False)

    def test_no_privileged_cli_or_external_workflow_services(self):
        source = (ROOT / "ops/s0s1_authority/validate.py").read_text()
        self.assertNotIn("subprocess", {a.name for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Import) for a in n.names})
        workflow = (ROOT / ".github/workflows/exp-s0-s1-ops02-evidence-contract.yml").read_text()
        for forbidden in ("services:", "supabase/", "psql ", "docker ", "secrets.", "pip install", "npm ", "curl "):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("shell: bash", workflow)  # GitHub's explicit bash enables pipefail.


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ops02-git-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_git("init", "-b", s.BRANCH)
        self.run_git("config", "user.name", "Synthetic OPS02")
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
        (self.root / "ops/s0s1_authority/validate.py").chmod(0o755)
        self.denied(True)
        self.commit()
        self.denied()

    def test_gitlink_index(self):
        path = sorted(s.ALLOWED)[0]
        self.run_git("update-index", "--add", "--cacheinfo", "160000," + self.base + "," + path)
        self.denied(True)

    def test_rename_protected_into_allowlist(self):
        target = "ops/s0s1_authority/validate.py"
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
        (self.root / "ops/s0s1_authority/validate.py").write_text("changed")
        self.denied()
        self.denied(True)

    def test_second_commit_even_within_allowlist_rejected(self):
        self.commit()
        (self.root / "ops/s0s1_authority/validate.py").write_text("changed")
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
