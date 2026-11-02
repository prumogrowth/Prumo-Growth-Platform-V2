"""FV-UI-013: execute acceptance natively from an authorized checkout.

Usage:
    python3 frontend/visual/tests/run_acceptance.py --expected-head <SHA_COMPLETO_DA_BRANCH>
    CHROMIUM_EXECUTABLE=/path/to/chromium python3 frontend/visual/tests/run_acceptance.py
    python3 frontend/visual/tests/run_acceptance.py --skip-browser

--skip-browser is diagnostic only, NEVER full acceptance.
No network, database or production actions are performed by this runner.
"""
import argparse
import ast
import hashlib
import json
import re
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def run_step(label, command, timeout):
    print(f"\n=== {label} ===", flush=True)
    try:
        result = subprocess.run(command, cwd=ROOT, timeout=timeout, check=False,
                                capture_output=True, text=True)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return {"name": label, "passed": result.returncode == 0,
                "exit_code": result.returncode, "executed": True}
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {label}", file=sys.stderr)
        return {"name": label, "passed": False, "executed": True,
                "error": "timeout"}
    except OSError as error:
        print(f"NOT EXECUTED: {label} ({error})", file=sys.stderr)
        return {"name": label, "passed": False, "executed": False,
                "error": str(error)}


def check_git_revision(expected_head):
    """Confirma que o checkout é o commit auditado e está na branch autorizada."""
    result = {"name": "Git checkout revision", "passed": False, "executed": False}
    if not expected_head or not re.fullmatch(r"[0-9a-f]{40}", expected_head.lower()):
        result["error"] = "provide full 40-character --expected-head from GitHub"
        return result
    git = shutil.which("git")
    if not git:
        result["error"] = "git unavailable"
        return result
    try:
        def git_cmd(*parts):
            return subprocess.run([git, "-C", str(ROOT), *parts],
                                  check=False, capture_output=True, text=True, timeout=10)
        root_result = git_cmd("rev-parse", "--show-toplevel")
        commit_result = git_cmd("rev-parse", "HEAD")
        branch_result = git_cmd("branch", "--show-current")
        if any(r.returncode != 0 for r in (root_result, commit_result, branch_result)):
            result["error"] = "not an accessible Git checkout"
            return result
        repo_root = Path(root_result.stdout.strip()).resolve()
        changes = subprocess.run(
            [git, "-C", str(repo_root), "status", "--porcelain",
             "--untracked-files=all", "--", "frontend/visual"],
            check=False, capture_output=True, text=True, timeout=10,
        )
        actual_head = commit_result.stdout.strip().lower()
        actual_branch = branch_result.stdout.strip()
        result.update({"executed": True, "commit": actual_head,
                       "branch": actual_branch,
                       "clean_frontend_visual": changes.returncode == 0
                       and not changes.stdout.strip()})
        result["passed"] = (
            actual_head == expected_head.lower()
            and actual_branch in {"feat/frontend-plataforma-visual", "codex/fv-ux-01-comunicacao-20261027", "codex/fv-rev-01-conversas-20261030", "codex/fv-rev-01-modulos-20261030", "codex/fv-cor-07-pos-auditoria-20261031", "fix/fv-cor-08-unicode-20261031", "fix/fv-coe-01-coerencia-20261031", "feat/fv-banco-fila-aptos-20261101", "fix/fv-banco-aud-02-fail-closed-20261101", "feat/fv-modulos-telas-proprias-20261101", "fix/fv-ux-aud-01-functional-minimal-color-20261101"}
            and result["clean_frontend_visual"]
        )
        if not result["passed"]:
            result["error"] = "revision, branch or clean working tree mismatch"
        return result
    except (OSError, subprocess.TimeoutExpired) as error:
        result["error"] = str(error)
        return result




def check_native_blob_manifest(expected_head, revision_ok):
    """FV-UI-045: bloqueia testes se blobs do checkout divergirem da árvore Git.

    Lê o json.loads(...) literal do verificador usando AST, SEM executá-lo.
    source_head é o commit de conteúdo ancestral do HEAD; o repin altera
    somente o verificador e a documentação. Não autoriza outro repositório.
    """
    step = {"name": "FV-UI-045 native Git blob preflight", "passed": False,
            "executed": False, "files_checked": 0}
    if not revision_ok:
        step["error"] = "unverified Git checkout"
        return step
    try:
        verifier = TESTS / "verify_offline_export.py"
        syntax = ast.parse(verifier.read_text(encoding="utf-8"), str(verifier))
        assignment = next((node for node in syntax.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "MANIFEST"
                    for target in node.targets)), None)
        if assignment is None or not isinstance(assignment.value, ast.Call):
            raise ValueError("manifest assignment unavailable")
        call = assignment.value
        if (not isinstance(call.func, ast.Attribute) or call.func.attr != "loads"
                or not isinstance(call.func.value, ast.Name)
                or call.func.value.id != "json" or len(call.args) != 1
                or not isinstance(call.args[0], ast.Constant)
                or not isinstance(call.args[0].value, str)):
            raise ValueError("manifest is not a literal json.loads call")
        manifest = json.loads(call.args[0].value)
        source = manifest.get("source_head", "")
        if (manifest.get("source_branch") not in {"feat/frontend-plataforma-visual", "codex/fv-ux-01-comunicacao-20261027", "codex/fv-rev-01-conversas-20261030", "codex/fv-rev-01-modulos-20261030", "codex/fv-cor-07-pos-auditoria-20261031", "fix/fv-cor-08-unicode-20261031", "fix/fv-coe-01-coerencia-20261031", "feat/fv-banco-fila-aptos-20261101", "fix/fv-banco-aud-02-fail-closed-20261101", "feat/fv-modulos-telas-proprias-20261101", "fix/fv-ux-aud-01-functional-minimal-color-20261101"}
                or not isinstance(source, str)
                or not re.fullmatch(r"[0-9a-f]{40}", source)):
            raise ValueError("manifest provenance invalid")
        files = manifest.get("files", {})
        if not isinstance(files, dict) or not files:
            raise ValueError("manifest has no files")
        git = shutil.which("git")
        root = Path(subprocess.run([git, "-C", str(ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=10).stdout.strip())
        ancestor = subprocess.run([git, "-C", str(root), "merge-base", "--is-ancestor",
            source, expected_head], capture_output=True, timeout=10, check=False)
        if ancestor.returncode != 0:
            raise ValueError("manifest source_head is not an ancestor of expected HEAD")
        tree = subprocess.run([git, "-C", str(root), "ls-tree", "-r", "--long",
            expected_head, "--", "frontend/visual"],
            capture_output=True, text=True, check=True, timeout=10)
        actual = {}
        for line in tree.stdout.splitlines():
            entry = re.fullmatch(r"(100644|100755) blob ([0-9a-f]{40})\s+(\d+)\t(.+)", line)
            if not entry:
                raise ValueError("unexpected Git tree entry: " + line[:80])
            mode, sha, size, path = entry.groups()
            actual[path] = {"sha": sha, "size": int(size)}
        verifier_path = "frontend/visual/tests/verify_offline_export.py"
        if verifier_path not in actual:
            raise ValueError("self verifier absent from Git tree")
        if set(actual) != set(files) | {verifier_path}:
            raise ValueError("Git tree inventory differs from pinned manifest")
        if any(actual[name] != details for name, details in files.items()):
            raise ValueError("Git tree blob hash/size mismatch")
        for name, details in actual.items():
            path = root / name
            if not path.is_file() or path.is_symlink():
                raise ValueError("missing or unsafe checkout file: " + name)
            data = path.read_bytes()
            digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if digest != details["sha"] or len(data) != details["size"]:
                raise ValueError("working-tree blob mismatch: " + name)
            step["files_checked"] += 1
        step.update({"executed": True, "passed": True,
                     "source_head": source, "expected_head": expected_head})
        return step
    except (OSError, ValueError, StopIteration, KeyError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, SyntaxError, TypeError) as exc:
        step.update({"executed": True, "error": str(exc)})
        return step

def main():
    parser = argparse.ArgumentParser(description="Validação local Node + Chromium")
    parser.add_argument("--skip-browser", action="store_true",
                        help="Apenas diagnóstico; nunca equivale a homologação Chromium")
    parser.add_argument("--json-report", type=Path,
                        help="Escrever resultado local JSON (nenhum dado de cliente)")
    parser.add_argument("--expected-head",
                        help="SHA completo do HEAD autorizado (obrigatório para aceite integral)")
    args = parser.parse_args()
    report = {"kind": "FV-UI-013-local-validation",
              "generated_utc": datetime.now(timezone.utc).isoformat(),
              "checkout_root": str(ROOT), "steps": [],
              "browser_executed": False, "full_acceptance": False}
    revision_step = check_git_revision(args.expected_head)
    report["steps"].append(revision_step)
    revision_ok = revision_step["passed"]
    blob_step = check_native_blob_manifest(args.expected_head, revision_ok)
    report["steps"].append(blob_step)
    blob_ok = blob_step["passed"] and blob_step["executed"]
    # Uma suíte truncada pode passar no Node e não constitui aceite integral.
    expected_tests = {
        "modules.dom.test.mjs", "relationship-view.test.mjs",
        "revision-conversations.test.mjs",
        "local-audio.test.mjs", "communication-composer.test.mjs",
        "app.dom.test.mjs", "app.mobile.dom.test.mjs", "app.tablet.dom.test.mjs", "bank-view.test.mjs", "bank-ready-list.test.mjs",
        "batch-monitor.test.mjs", "cf-op-02.test.mjs", "fixtures.test.mjs",
        "postmark-view.test.mjs", "registration-view.test.mjs", "human-cycle-view.test.mjs",
        "source-contract.test.mjs", "source-module-graph.test.mjs",
        "team-monitor.test.mjs", "team-monitoring.test.mjs",
        "team-operations.test.mjs", "distribution-view.test.mjs", "transport-state-view.test.mjs", "view-model.test.mjs",
        "attention-integration.test.mjs", "conversation-attention.test.mjs",
        "team-pause-preview.test.mjs", "s0-command-result.test.mjs",
        "s0-read-contract.test.mjs", "integration-gate-view.test.mjs", "operation-feedback.test.mjs",
        "acceptance-matrix.test.mjs", "offline-export-manifest.test.mjs",
        "validation-layers.test.mjs",
    }
    required_sources = {
        "relationship-view.mjs", "revision-fixtures.mjs", "tests/browser.modules.py", "tests/browser.corrections.py",
        "local-audio.mjs", "communication-composer.mjs", "tests/browser.communication.py", "tests/browser.revision.py",
        "index.html", "styles.css", "app.mjs", "fixtures.mjs",
        "view-model.mjs", "cf-op-02.mjs", "registration-view.mjs", "human-cycle-view.mjs",
        "operation-feedback.mjs", "s0-command-result.mjs", "s0-read-contract.mjs", "integration-gate-view.mjs",
        "bank-view.mjs", "postmark-view.mjs", "team-operations.mjs",
        "tests/acceptance-matrix.json", "tests/verify_offline_export.py",
        "tests/test_offline_export.py", "tests/validation-layers.json",
        "tests/run_validation_layers.mjs",
        "team-monitor.mjs", "team-monitoring.mjs", "batch-monitor.mjs", "distribution-view.mjs", "transport-state-view.mjs",
    }
    missing = sorted(
        [f"tests/{name}" for name in expected_tests if not (TESTS / name).is_file()]
        + [name for name in required_sources if not (ROOT / name).is_file()]
        + (["tests/browser.smoke.py"] if not (TESTS / "browser.smoke.py").is_file() else [])
        + (["tests/dom-fixture.mjs"] if not (TESTS / "dom-fixture.mjs").is_file() else [])
    )
    # Não aceitar regressão apenas parcial: todo *.test.mjs deve estar registrado.
    unknown = sorted(file.name for file in TESTS.glob("*.test.mjs")
                     if file.name not in expected_tests)
    missing += [f"NOT_REGISTERED:{name}" for name in unknown]
    inventory_ok = not missing
    # Verificação de sintaxe ANTES dos ensaios Chromium longos: erros de
    # indentação nos roteiros não devem consumir toda a matriz visual.
    syntax_errors = []
    for script_path in sorted(TESTS.glob("browser*.py")):
        try:
            ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))
        except (SyntaxError, UnicodeError, OSError) as error:
            syntax_errors.append(f"{script_path.name}: {error}")
    browser_syntax_ok = not syntax_errors
    report["steps"].append({
        "name": "Chromium Python source syntax",
        "passed": browser_syntax_ok,
        "executed": True,
        "errors": syntax_errors,
    })
    inventory_ok = inventory_ok and browser_syntax_ok
    report["steps"].append({
        "name": "FV-UI-013 checkout inventory", "passed": inventory_ok,
        "executed": True, "missing": missing,
        "expected_node_tests": len(expected_tests),
    })
    # Falha fechada: código de interface e Chromium não rodam quando a
    # regressão de segurança do pacote falha, mesmo em checkout válido.
    if not inventory_ok or not revision_ok or not blob_ok:
        security_step={"name": "Offline ZIP verifier adversarial regression",
                       "passed": False, "executed": False,
                       "error": "incomplete, unverified or blob-mismatched checkout"}
    else:
        security_step=run_step(
            "Offline ZIP verifier adversarial regression",
            [sys.executable,"-B","-m","unittest","discover","-s",str(TESTS),
             "-p","test_offline_export.py"],timeout=45)
    report["steps"].append(security_step)
    security_ok=security_step["passed"] and security_step["executed"]
    node = shutil.which("node")
    suite = sorted(str(file) for file in TESTS.glob("*.test.mjs"))
    if not inventory_ok or not node or not revision_ok or not blob_ok or not security_ok:
        error = ("incomplete checkout" if not inventory_ok else
                 "unverified checkout revision" if not revision_ok else
                 "native blob preflight failed" if not blob_ok else
                 "ZIP verifier security regression failed" if not security_ok else
                 "node unavailable")
        node_step={"name": "Node ESM regression", "passed": False,
                   "executed": False, "error": error}
    else:
        node_step=run_step("Node ESM regression",
                           [node, "--test", "--test-concurrency=1", *suite], timeout=180)
    report["steps"].append(node_step)
    node_ok=node_step["passed"] and node_step["executed"]
    if args.skip_browser:
        report["steps"].append({"name": "Chromium Playwright smoke",
                                "executed": False, "passed": False,
                                "error": "explicitly skipped"})
        print("Chromium SKIPPED — diagnóstico parcial, não homologação.", flush=True)
    elif not inventory_ok or not revision_ok or not blob_ok or not security_ok or not node_ok:
        error = ("incomplete checkout" if not inventory_ok else
                 "unverified checkout revision" if not revision_ok else
                 "native blob preflight failed" if not blob_ok else
                 "ZIP verifier security regression failed" if not security_ok else
                 "Node ESM regression failed")
        report["steps"].append({"name": "Chromium Playwright smoke",
                                "executed": False, "passed": False, "error": error})
        print("Chromium BLOCKED — " + error, flush=True)
    else:
        browser_step = run_step("Chromium Playwright smoke",
                                [sys.executable, str(TESTS / "browser.smoke.py")], timeout=600)
        report["steps"].append(browser_step)
        report["browser_executed"] = browser_step["executed"]
        # Additional bounded gate; the original Chromium 600s budget is unchanged.
        # A failed/skipped old suite cannot be replaced by the new reproductions.
        if browser_step["passed"] and browser_step["executed"]:
            corrections = run_step("FV-COR-07 Chromium regression",
                [sys.executable, str(TESTS / "browser.corrections.py")], timeout=360)
        else:
            corrections = {"name": "FV-COR-07 Chromium regression", "executed": False,
                           "passed": False, "error": "previous Chromium gate failed"}
        report["steps"].append(corrections)
    report["full_acceptance"] = all(s["passed"] and s["executed"]
                                    for s in report["steps"]) and report["browser_executed"]
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
    print("\nFULL LOCAL ACCEPTANCE: " + ("PASS" if report["full_acceptance"] else "NOT PASSED"))
    return 0 if report["full_acceptance"] else 1


if __name__ == "__main__":
    sys.exit(main())
