"""FV-UI-013: execute acceptance natively from an authorized checkout.

Usage:
    python3 frontend/visual/tests/run_acceptance.py --expected-head <SHA_COMPLETO_DA_BRANCH>
    CHROMIUM_EXECUTABLE=/path/to/chromium python3 frontend/visual/tests/run_acceptance.py
    python3 frontend/visual/tests/run_acceptance.py --skip-browser

--skip-browser is diagnostic only, NEVER full acceptance.
No network, database or production actions are performed by this runner.
"""
import argparse
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
            and actual_branch == "feat/frontend-plataforma-visual"
            and result["clean_frontend_visual"]
        )
        if not result["passed"]:
            result["error"] = "revision, branch or clean working tree mismatch"
        return result
    except (OSError, subprocess.TimeoutExpired) as error:
        result["error"] = str(error)
        return result



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
    # Uma suíte truncada pode passar no Node e não constitui aceite integral.
    expected_tests = {
        "app.dom.test.mjs", "app.mobile.dom.test.mjs", "bank-view.test.mjs",
        "batch-monitor.test.mjs", "cf-op-02.test.mjs", "fixtures.test.mjs",
        "postmark-view.test.mjs", "registration-view.test.mjs", "human-cycle-view.test.mjs",
        "source-contract.test.mjs", "source-module-graph.test.mjs",
        "team-monitor.test.mjs", "team-monitoring.test.mjs",
        "team-operations.test.mjs", "distribution-view.test.mjs", "transport-state-view.test.mjs", "view-model.test.mjs",
        "attention-integration.test.mjs", "conversation-attention.test.mjs",
        "team-pause-preview.test.mjs", "s0-command-result.test.mjs",
        "s0-read-contract.test.mjs", "integration-gate-view.test.mjs", "operation-feedback.test.mjs",
        "acceptance-matrix.test.mjs", "offline-export-manifest.test.mjs",
    }
    required_sources = {
        "index.html", "styles.css", "app.mjs", "fixtures.mjs",
        "view-model.mjs", "cf-op-02.mjs", "registration-view.mjs", "human-cycle-view.mjs",
        "operation-feedback.mjs", "s0-command-result.mjs", "s0-read-contract.mjs", "integration-gate-view.mjs",
        "bank-view.mjs", "postmark-view.mjs", "team-operations.mjs",
        "tests/acceptance-matrix.json", "tests/verify_offline_export.py",
        "tests/test_offline_export.py",
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
    report["steps"].append({
        "name": "FV-UI-013 checkout inventory", "passed": inventory_ok,
        "executed": True, "missing": missing,
        "expected_node_tests": len(expected_tests),
    })
    # Falha fechada: código de interface e Chromium não rodam quando a
    # regressão de segurança do pacote falha, mesmo em checkout válido.
    if not inventory_ok or not revision_ok:
        security_step={"name": "Offline ZIP verifier adversarial regression",
                       "passed": False, "executed": False,
                       "error": "incomplete or unverified checkout"}
    else:
        security_step=run_step(
            "Offline ZIP verifier adversarial regression",
            [sys.executable,"-B","-m","unittest","discover","-s",str(TESTS),
             "-p","test_offline_export.py"],timeout=45)
    report["steps"].append(security_step)
    security_ok=security_step["passed"] and security_step["executed"]
    node = shutil.which("node")
    suite = sorted(str(file) for file in TESTS.glob("*.test.mjs"))
    if not inventory_ok or not node or not revision_ok or not security_ok:
        error = ("incomplete checkout" if not inventory_ok else
                 "unverified checkout revision" if not revision_ok else
                 "ZIP verifier security regression failed" if not security_ok else
                 "node unavailable")
        report["steps"].append({"name": "Node ESM regression", "passed": False,
                                "executed": False, "error": error})
    else:
        report["steps"].append(run_step("Node ESM regression",
                                         [node, "--test", *suite], timeout=180))
    if args.skip_browser:
        report["steps"].append({"name": "Chromium Playwright smoke",
                                "executed": False, "passed": False,
                                "error": "explicitly skipped"})
        print("Chromium SKIPPED — diagnóstico parcial, não homologação.", flush=True)
    elif not inventory_ok or not revision_ok or not security_ok:
        error = ("incomplete checkout" if not inventory_ok else
                 "unverified checkout revision" if not revision_ok else
                 "ZIP verifier security regression failed")
        report["steps"].append({"name": "Chromium Playwright smoke",
                                "executed": False, "passed": False, "error": error})
        print("Chromium BLOCKED — " + error, flush=True)
    else:
        browser_step = run_step("Chromium Playwright smoke",
                                [sys.executable, str(TESTS / "browser.smoke.py")], timeout=180)
        report["steps"].append(browser_step)
        report["browser_executed"] = browser_step["executed"]
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
