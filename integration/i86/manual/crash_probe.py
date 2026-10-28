"""Test-only SIGKILL scheduler; parameters travel through a private stdin pipe."""
import argparse
import json
import os
import signal
import sys
from uuid import UUID
from integration.i86.manual.lab_support import APPLY_SQL, connect, laboratory


def stop(stage):
    os.write(int(os.environ["PRUMO_I86_MANUAL_PROBE_FD"]), stage.encode()+b"\n")
    os.kill(os.getpid(), signal.SIGSTOP)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("before-commit", "after-commit"), required=True)
    args = parser.parse_args()
    try:
        laboratory()
        values = json.loads(sys.stdin.buffer.read(16385))
        values[0] = UUID(values[0])
        with connect() as c:
            c.execute("set application_name='i86-manual-crash-probe'")
            c.execute(APPLY_SQL, values)
            if args.stage == "before-commit":
                stop(args.stage)
        if args.stage == "after-commit":
            stop(args.stage)
        print('{"state":"TEST_OPERATOR_SIMULATION_FINISHED"}')
        return 0
    except Exception:
        print('{"state":"BLOCKED","code":"I86M_TEST_PROBE_FAILED_WITHHELD"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
