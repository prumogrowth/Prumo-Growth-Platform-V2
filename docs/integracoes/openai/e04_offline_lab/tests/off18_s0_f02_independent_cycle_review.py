"""OFF-18 independent verification of S0's OFF17-F02-VERSIONS-01 repair.

Loads the published S0 F02 _sources AST unchanged at an exact pinned Git
commit. Exercises synthetic cursor responses; no PostgreSQL, API or secrets.
An ACCEPTED mapping here is only a source-level contract recommendation,
not authentication, production grant, or a live end-to-end test.
"""
from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

PINNED_SHA = "31e88ec2632e861d55c2e0ae4766f8a0a4362e22"
NOW = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)


class Blocked(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Blocked(reason)


def load_exact_function():
    path = Path(os.environ["S0_F02_PINNED_SOURCE"])
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    targets = [n for n in tree.body
               if isinstance(n, ast.FunctionDef) and n.name == "_sources"]
    if len(targets) != 1:
        raise AssertionError("Expected exactly one pinned S0 F02 _sources")
    fn = targets[0]
    # Keep source function intact; compile only this source AST node, no
    # unrelated side effects or imports from PG-dependent modules.
    namespace = {"require": require}
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["_sources"]


S0_SOURCES = load_exact_function()


class FakeCursor:
    """Minimal deterministic SELECT fixture; not a database emulator."""
    def __init__(self):
        self.scope = SimpleNamespace(
            concessionaria_id="shop-A", app_ref="app-A", route_ref="route-A",
            canal_id="channel-A", waba_id="waba-A")
        self.principal = SimpleNamespace(principal_ref="service-A")
        self.q = {"case_ref": "case-A", "flow_ref": "flow-A", "purpose_ref": "followup",
                  "consent_purpose_ref": "consent-followup"}
        self.expected = dict(case=1, cycle=3, catalog=1, assignment=7,
                             policy=1, consent=1, chain=1)
        self.case = dict(active=True, global_opt_out=False,
                         concessionaria_id="shop-A", app_ref="app-A",
                         route_ref="route-A", canal_id="channel-A",
                         waba_id="waba-A", principal_ref="service-A",
                         case_revision=1, assignment_revision=7,
                         policy_revision=1)
        self.cycle = dict(cycle_revision=3, flow_ref="flow-A")
        self.consent = dict(state="GRANTED", revision=1,
                            valid_until=NOW + timedelta(days=1))
        self.suppressions = []
        self.templates = [dict(
            template_ref="template-A", template_version="v1",
            concessionaria_id="shop-A", waba_id="waba-A",
            active=True, provider_approved=True, media_verified=True,
            grant_active=True, campaign_active=True, campaign_eligible=True,
            revision=1, grant_revision=1,
            valid_until=NOW + timedelta(days=1))]
        self.last = None

    def execute(self, sql, args=None):
        if "FROM s0_pre_dispatch_lab.cases " in sql:
            self.last = self.case
        elif "FROM s0_f02_lab.case_cycles " in sql:
            self.last = self.cycle
        elif "FROM s0_pre_dispatch_lab.consents " in sql:
            self.last = self.consent
        elif "FROM s0_pre_dispatch_lab.suppressions " in sql:
            self.last = self.suppressions
        elif "FROM s0_pre_dispatch_lab.templates " in sql:
            self.last = self.templates
        elif "clock_timestamp() AS now" in sql:
            self.last = {"now": NOW}
        else:
            raise AssertionError("Unexpected S0 source SELECT: " + sql[:120])
        return self

    def fetchone(self):
        return self.last

    def fetchall(self):
        return self.last

    def check(self):
        return S0_SOURCES(self, self.q, self.scope, self.principal,
                          self.expected)


class F02PinnedSourceReview(unittest.TestCase):
    def good(self):
        c = FakeCursor()
        _case, _consent, rows, at = c.check()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["template_ref"], "template-A")
        self.assertEqual(at, NOW)
        return c

    def denied(self, action, reason):
        c = FakeCursor()
        action(c)
        with self.assertRaises(Blocked) as trap:
            c.check()
        self.assertEqual(str(trap.exception), reason)
        return c

    def test_01_distinct_cycle_3_assignment_7_accepted(self):
        c = self.good()
        self.assertNotEqual(c.expected["cycle"], c.expected["assignment"])

    def test_02_distinct_cycle_5_assignment_1_accepted(self):
        c = FakeCursor()
        c.cycle["cycle_revision"] = c.expected["cycle"] = 5
        c.case["assignment_revision"] = c.expected["assignment"] = 1
        self.assertEqual(len(c.check()[2]), 1)

    def test_03_distinct_cycle_1_assignment_9_accepted(self):
        c = FakeCursor()
        c.cycle["cycle_revision"] = c.expected["cycle"] = 1
        c.case["assignment_revision"] = c.expected["assignment"] = 9
        self.assertEqual(len(c.check()[2]), 1)

    def test_04_stale_cycle_detected_without_changing_assignment(self):
        self.denied(lambda c: c.expected.__setitem__("cycle", 2),
                    "STALE_OR_CHANGED")

    def test_05_wrong_case_revision_denied(self):
        self.denied(lambda c: c.expected.__setitem__("case", 2),
                    "STALE_OR_CHANGED")

    def test_06_wrong_policy_revision_denied(self):
        self.denied(lambda c: c.expected.__setitem__("policy", 2),
                    "STALE_OR_CHANGED")

    def test_07_wrong_catalog_revision_denied(self):
        self.denied(lambda c: c.expected.__setitem__("catalog", 2),
                    "STALE_OR_CHANGED")

    def test_08_wrong_grant_chain_revision_denied(self):
        self.denied(lambda c: c.expected.__setitem__("chain", 2),
                    "STALE_OR_CHANGED")

    def test_09_wrong_consent_revision_denied(self):
        self.denied(lambda c: c.expected.__setitem__("consent", 2),
                    "STALE_OR_CHANGED")

    def test_10_revoked_consent_denied(self):
        self.denied(lambda c: c.consent.__setitem__("state", "REVOKED"),
                    "CONSENT_DENIED")

    def test_11_global_opt_out_denied(self):
        self.denied(lambda c: c.case.__setitem__("global_opt_out", True),
                    "POLICY_DENIED")

    def test_12_cross_store_denied(self):
        self.denied(lambda c: c.case.__setitem__("concessionaria_id", "shop-B"),
                    "SCOPE_CHANGED")

    def test_13_suppressed_purpose_denied(self):
        self.denied(lambda c: c.suppressions.append(
            {"purpose_ref": "consent-followup", "active": True}),
            "SUPPRESSED")

    def test_14_expired_consent_denied(self):
        self.denied(lambda c: c.consent.__setitem__(
            "valid_until", NOW - timedelta(seconds=1)), "EXPIRED")

    def test_15_unapproved_template_denied(self):
        self.denied(lambda c: c.templates[0].__setitem__(
            "provider_approved", False), "CATALOG_NOT_VERIFIED")

    def test_16_unverified_template_media_denied(self):
        self.denied(lambda c: c.templates[0].__setitem__(
            "media_verified", False), "CATALOG_NOT_VERIFIED")

    def test_17_revoked_grant_denied(self):
        self.denied(lambda c: c.templates[0].__setitem__(
            "grant_active", False), "CATALOG_NOT_VERIFIED")

    def test_18_duplicate_catalog_template_denied(self):
        self.denied(lambda c: c.templates.append(dict(c.templates[0])),
                    "AMBIGUOUS_CATALOG")

    def test_19_inactive_campaign_denied(self):
        self.denied(lambda c: c.templates[0].__setitem__(
            "campaign_active", False), "CATALOG_NOT_VERIFIED")

    def test_20_template_expired_denied(self):
        self.denied(lambda c: c.templates[0].__setitem__(
            "valid_until", NOW - timedelta(seconds=1)), "EXPIRED")

    def test_21_stale_assignment_detected_without_changing_cycle(self):
        self.denied(lambda c: c.expected.__setitem__("assignment", 2),
                    "STALE_OR_CHANGED")

    def test_22_wrong_flow_ref_denied_even_versions_identical(self):
        self.denied(lambda c: c.q.__setitem__("flow_ref", "flow-B"),
                    "CYCLE_SOURCE_MISSING_OR_CHANGED")

    def test_23_missing_cycle_source_denied(self):
        self.denied(lambda c: setattr(c, "cycle", None),
                    "CYCLE_SOURCE_MISSING_OR_CHANGED")

    def test_24_updated_cycle_source_denied_after_snapshot(self):
        self.denied(lambda c: c.cycle.__setitem__("cycle_revision", 4),
                    "STALE_OR_CHANGED")



if __name__ == "__main__":
    unittest.main(verbosity=2)
