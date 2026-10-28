"""Negative-only cleanup through existing I84/I85 interfaces."""
import json
import os
from pathlib import Path
from integration.i85 import bootstrap as i85
from local_admin import boundary as b
from local_admin.operation import Operator, resources


def cleanup():
    if not (b.DEFAULT/"state.json").exists():
        if any(resources().values()):
            raise b.Blocked("I86_UNOWNED_RESOURCES_PRESERVED")
        return {"resources_absent": True, "no_owned_stack_created": True}
    if i85.ROOT.exists():
        try:
            op = i85.Bootstrap()
            op.load()
            if op.state["authority"]["phase"] == "COMMIT_UNKNOWN":
                op.reconcile_authority()
                op.load()
            if op.state["authority"]["phase"] in ("ACTIVE", "REVOKE_UNKNOWN", "REVOKED"):
                op.revoke_director()
            op.dispose()
        except b.Blocked:
            pass  # never infer rollback or erase uncertain evidence
    proof = Operator().execute("down")
    if not proof["resources_absent"] or not proof["material_removed"] or any(resources().values()):
        raise b.Blocked("I86_LAB_DISCARD_UNPROVEN")
    retained = False
    if i85.ROOT.exists() or i85.ROOT.with_name(i85.ROOT.name+".disposing").exists():
        os.environ["PRUMO_I85_ABANDON"] = "PRESERVE_EVIDENCE_AFTER_VERIFIED_LAB_DISCARD"
        try:
            retired = i85.Bootstrap().abandon_after_stack_down()
            if not retired["password_material_removed"]:
                raise b.Blocked("I86_PASSWORD_RETIREMENT_UNPROVEN")
            retained = retired["uncertain_evidence_retained"]
        finally:
            os.environ.pop("PRUMO_I85_ABANDON", None)
    return {"resources_absent": True, "private_material_removed": True,
            "uncertain_nonsecret_evidence_retained": retained,
            "hosted_enabled": False}


if __name__ == "__main__":
    result = cleanup()
    (Path(os.environ["RUNNER_TEMP"])/"prumo_i86_cleanup.json").write_text(
        json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True))
