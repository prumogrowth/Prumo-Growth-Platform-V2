"""CLI for the trusted local installer only; NOT callable by Edge/frontend."""
import argparse
import json
from local_admin import boundary as b
from integration.i85.bootstrap import Bootstrap, LABELS
from local_admin.__main__ import Parser
import os


def main():
    try:
        parser = Parser(description="I85 isolated disposable installer")
        parser.add_argument("action", choices=("init", "create", "reconcile-identity", "authorize-director",
                                                "grant-director", "revoke-director", "reconcile-authority",
                                                "status", "dispose", "recover-journal", "abandon-after-stack-down"))
        parser.add_argument("--label", choices=sorted(LABELS))
        args = parser.parse_args()
        if (args.action in ("create", "reconcile-identity")) != bool(args.label):
            raise b.Blocked("I85_LABEL_SCOPE_INVALID")
        os.chdir(b.ROOT)
        bootstrap = Bootstrap()
        if args.action == "init":
            result = bootstrap.init()
        else:
            methods = {
                "create": lambda: bootstrap.create(args.label),
                "reconcile-identity": lambda: bootstrap.reconcile_identity(args.label),
                "authorize-director": bootstrap.authorize_director,
                "grant-director": bootstrap.grant_director,
                "revoke-director": bootstrap.revoke_director,
                "reconcile-authority": bootstrap.reconcile_authority,
                "status": bootstrap.status,
                "dispose": bootstrap.dispose,
                "recover-journal": bootstrap.recover_journal,
                "abandon-after-stack-down": bootstrap.abandon_after_stack_down,
            }
            result = methods[args.action]()
        print(json.dumps(result, sort_keys=True))
        return 0
    except b.Blocked as exc:
        print(json.dumps({"state": "BLOCKED", "code": exc.code}))
        return 2
    except Exception:
        print(json.dumps({"state": "BLOCKED", "code": "I85_UNKNOWN_REQUIRES_EXPLICIT_RECONCILIATION"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
