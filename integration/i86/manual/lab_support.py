"""TEST SUPPORT ONLY. No operational CLI, endpoint, MCP or hosted SQL client.

Automated positive calls below simulate an operator exclusively in the owned
GitHub-hosted throwaway laboratory authorized by the test mission. They do not
prove human presence or supply an organizational authorization channel.
"""
import hashlib
import os
from pathlib import Path
import secrets
from uuid import uuid4

from integration.i85 import bootstrap as i85
from local_admin import boundary as b, environment as e

APPLY_SQL = "select prumo_i86_manual.apply_act("+",".join(["%s"]*7)+")"


def laboratory():
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("PRUMO_I86_RUNNER_ISOLATION") != "github-hosted"
            or os.environ.get("PRUMO_I86_MANUAL_LAB") != "YES"):
        raise b.Blocked("I86M_TEST_SIMULATION_ONLY")
    i85.Bootstrap().owned()


def connect():
    laboratory()
    return e.database()


def install():
    with connect() as c:
        c.autocommit = True
        c.execute(Path(__file__).with_name("procedure.sql").read_text())


def subject(label, passwords):
    """Only Auth fixtures; no I85 bootstrap grant or authority journal."""
    laboratory()
    email = "i86-manual-"+uuid4().hex+"@example.invalid"
    password = secrets.token_urlsafe(42)
    raw = i85._api("POST", "/auth/v1/admin/users",
                  {"email": email, "password": password, "email_confirm": True})
    value = raw.get("user", raw)
    identifier = i85._ident(value["id"])
    with connect() as c:
        row = c.execute("select id::text,email from auth.users where id=%s", (identifier,)).fetchone()
    canonical = i85._api("GET", "/auth/v1/admin/users/"+identifier)
    canonical = canonical.get("user", canonical)
    if row != (identifier, email) or canonical.get("id") != identifier or canonical.get("email") != email:
        raise b.Blocked("I86M_FIXTURE_UUID_UNPROVEN")
    passwords[identifier] = password
    return {"id": identifier, "email": email, "label": label}


def token(person, passwords, technical):
    laboratory()
    value = i85._api("POST", "/auth/v1/token?grant_type=password",
                    {"email": person["email"], "password": passwords[person["id"]]},
                    admin=False, token=e.discover()["ANON_KEY"])
    technical.extend([value["access_token"], value.get("refresh_token", "")])
    who = i85._api("GET", "/auth/v1/user", admin=False, token=value["access_token"])
    if who.get("id") != person["id"]:
        raise b.Blocked("I86M_FIXTURE_LOGIN_UNPROVEN")
    return value["access_token"]


def inspect(target):
    with connect() as c:
        return c.execute("select prumo_i86_manual.inspect_subject(%s)", (target,)).fetchone()[0]


def act(target, action="APPOINT", expected=None):
    digest = inspect(target)["expected_sha256"] if expected is None else expected
    identifier = uuid4()
    # Synthetic references/evidence are explicitly NOT proof of a human act.
    return (identifier, action, target, digest, "I86M_SYNTHETIC_OPERATOR_ONLY",
            "I86M-SYNTHETIC-ACT-"+identifier.hex,
            hashlib.sha256(("I86M SYNTHETIC TEST "+identifier.hex).encode()).hexdigest())


def apply_for_test(values):
    with connect() as c:
        result = c.execute(APPLY_SQL, values).fetchone()[0]
    return result  # no success escapes if the caller's COMMIT failed


def reconcile(values):
    with connect() as c:
        return c.execute("select prumo_i86_manual.reconcile_act(%s,%s)",
                         (values[0], values[6])).fetchone()[0]
