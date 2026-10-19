"""FV-UI-013: execute acceptance natively from an authorized checkout.

Usage:
    python3 frontend/visual/tests/run_acceptance.py
    CHROMIUM_EXECUTABLE=/path/to/chromium python3 frontend/visual/tests/run_acceptance.py
    python3 frontend/visual/tests/run_acceptance.py --skip-browser

--skip-browser is diagnostic only, NEVER full acceptance.
No network, database or production actions are performed by this runner.
"""
import argparse
import json
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


def main():
    parser = argparse.ArgumentParser(description="Validação local Node + Chromium")
    parser.add_argument("--skip-browser", action="store_true",
                        help="Apenas diagnóstico; nunca equivale a homologação Chromium")
    parser.add_argument("--json-report", type=Path,
                        help="Escrever resultado local JSON (nenhum dado de cliente)")
    args = parser.parse_args()
    report = {"kind": "FV-UI-013-local-validation",
              "generated_utc": datetime.now(timezone.utc).isoformat(),
              "checkout_root": str(ROOT), "steps": [],
              "browser_executed": False, "full_acceptance": False}
    node = shutil.which("node")
    suite = sorted(str(file) for file in TESTS.glob("*.test.mjs"))
    if not node or not suite:
        report["steps"].append({"name": "Node ESM regression", "passed": False,
                                "executed": False, "error": "node or *.test.mjs unavailable"})
    else:
        report["steps"].append(run_step("Node ESM regression",
                                         [node, "--test", *suite], timeout=180))
    if args.skip_browser:
        report["steps"].append({"name": "Chromium Playwright smoke",
                                "executed": False, "passed": False,
                                "error": "explicitly skipped"})
        print("Chromium SKIPPED — diagnóstico parcial, não homologação.", flush=True)
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
