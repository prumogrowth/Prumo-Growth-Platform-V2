"""Isolated real-transaction crash probe; bearer supplied only through stdin."""
import argparse
import json
import os
import signal
from integration.i86.authority import AuthorityLab, command


def stop(stage):
    os.write(int(os.environ["PRUMO_I86_PROBE_FD"]), stage.encode()+b"\n")
    os.kill(os.getpid(), signal.SIGSTOP)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("before-commit", "after-commit"), required=True)
    args = parser.parse_args()
    try:
        import sys
        request = json.loads(sys.stdin.buffer.read(16385))
        lab = AuthorityLab()
        principal = lab._identity.verify(request["authorization"])
        payload = command(request["payload"])
        with lab.connect() as conn:
            conn.execute("set application_name='i86-crash-probe'")
            lab.record(conn, principal, payload)
            if args.stage == "before-commit":
                stop(args.stage)
        if args.stage == "after-commit":
            stop(args.stage)
        print('{"status":"RECORDED_TECHNICAL_EVIDENCE_ONLY"}')
        return 0
    except Exception:
        print('{"status":"BLOCKED","code":"I86_PROBE_FAILURE_WITHHELD"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
