"""Offline regression for selective lead pause. No DB, RLS or real users."""
import unittest
from dataclasses import replace

from backend.operator_distribution_policy import (
    CaseSnapshot, CandidateSnapshot, propose_selective_pause_case,
    classify_manual_transfer_target,
)


def case(started=False, shop="aurora"):
    return CaseSnapshot("case-1", shop, "rafael", "marina", "v7", started, True)


def person(operator, manager="marina", shops=("aurora",), active=True, intake=True):
    return CandidateSnapshot(operator, manager, active, intake, shops)


class SelectivePauseContractTests(unittest.TestCase):
    def test_started_contact_is_preserved(self):
        result = propose_selective_pause_case(
            case(True), "rafael", "marina", (person("lia"),)
        )
        self.assertEqual(result.disposition, "RETAIN_STARTED")
        self.assertFalse(result.mutates_case)
        self.assertIsNone(result.proposed_operator)

    def test_unstarted_lead_proposes_authorized_same_team_recipient(self):
        result = propose_selective_pause_case(
            case(False), "rafael", "marina",
            (person("daniel-op", "daniel"), person("lia"),
             person("otavio", "marina", ("horizonte",))),
        )
        self.assertEqual(result.disposition, "PROPOSE_SAME_TEAM_REASSIGNMENT")
        self.assertEqual(result.proposed_operator, "lia")
        self.assertFalse(result.mutates_case)

    def test_without_same_team_shop_grant_lead_stays_with_paused_operator(self):
        for candidates in (
            (),
            (person("b", manager="daniel"),),
            (person("b", shops=("horizonte",)),),
            (person("b", active=False),),
            (person("b", intake=False),),
            (person("rafael"),),
        ):
            result = propose_selective_pause_case(
                case(False), "rafael", "marina", candidates
            )
            self.assertEqual(result.disposition, "RETAIN_NO_SAME_TEAM_RECIPIENT")
            self.assertIsNone(result.proposed_operator)

    def test_completed_case_is_never_moved_automatically(self):
        closed=CaseSnapshot("case-1", "aurora", "rafael", "marina", "v7", False, False)
        result=propose_selective_pause_case(closed,"rafael","marina",(person("lia"),))
        self.assertEqual(result.disposition,"RETAIN_NOT_ACTIVE_OR_UNVERIFIED")

    def test_unknown_human_contact_is_not_reassigned(self):
        result = propose_selective_pause_case(
            case(None), "rafael", "marina", (person("lia"),)
        )
        self.assertEqual(result.disposition, "RETAIN_CONTACT_UNVERIFIED")

    def test_unauthorized_or_stale_case_snapshot_fails_closed(self):
        self.assertEqual(
            propose_selective_pause_case(
                case(False), "outro", "marina", (person("lia"),)
            ).disposition, "DENIED_OR_UNVERIFIED"
        )
        self.assertEqual(
            propose_selective_pause_case(
                case(False), "rafael", "daniel", (person("lia"),)
            ).disposition, "DENIED_OR_UNVERIFIED"
        )
        self.assertEqual(
            propose_selective_pause_case(
                CaseSnapshot("case-1","aurora","rafael","marina","",False,True),
                "rafael", "marina", (person("lia"),)
            ).disposition, "DENIED_OR_UNVERIFIED"
        )
        self.assertEqual(
            propose_selective_pause_case(
                case(False), "rafael", "marina", (None,)
            ).disposition, "DENIED_OR_UNVERIFIED"
        )

    def test_manual_transfer_with_valid_shop_grant_is_not_automatic_authorization(self):
        self.assertEqual(
            classify_manual_transfer_target(case(True),"marina",person("lia")),
            "S1_STANDARD_AUTH_REQUIRED"
        )

    def test_manual_transfer_without_shop_grant_requires_case_specific_exception(self):
        self.assertEqual(
            classify_manual_transfer_target(
                case(True), "marina", person("lia",shops=("horizonte",))
            ),
            "S1_CASE_SCOPED_EXCEPTION_REQUIRED"
        )
        self.assertEqual(
            classify_manual_transfer_target(
                case(True), "marina", person("bianca",manager="daniel")
            ),
            "DENIED"
        )

    def test_manual_transfer_of_closed_case_is_denied(self):
        archived=CaseSnapshot("case-1", "aurora", "rafael", "marina", "v7", True, False)
        self.assertEqual(classify_manual_transfer_target(archived,"marina",person("lia")),"DENIED")

    def test_no_grant_provision_and_no_input_mutation(self):
        original_case=case(False)
        source=(person("lia"), person("bianca",manager="daniel"))
        before=repr((original_case,source))
        propose_selective_pause_case(original_case,"rafael","marina",source)
        self.assertEqual(repr((original_case,source)),before)
        self.assertFalse(hasattr(original_case,"account_state"))


class MalformedSnapshotTests(unittest.TestCase):
    def test_mixed_candidate_ids_are_denied_without_sort_failure(self):
        candidates = (person("lia"), person(123))
        result = propose_selective_pause_case(case(), "rafael", "marina", candidates)
        self.assertEqual(result.disposition, "DENIED_OR_UNVERIFIED")
        self.assertIsNone(result.proposed_operator)
        self.assertFalse(result.mutates_case)

    def test_malformed_case_identity_is_denied_on_both_paths(self):
        for field in ("case_ref", "shop_ref", "owner_operator", "manager_ref", "assignment_version"):
            for value in (None, 7, [], "", "   "):
                with self.subTest(field=field, value=value):
                    malformed = replace(case(), **{field: value})
                    self.assertEqual(propose_selective_pause_case(
                        malformed, "rafael", "marina", (person("lia"),)
                    ).disposition, "DENIED_OR_UNVERIFIED")
                    self.assertEqual(classify_manual_transfer_target(
                        malformed, "marina", person("lia")
                    ), "DENIED")

    def test_malformed_candidate_cannot_request_exception_or_standard_path(self):
        invalid = [replace(person("lia"), **{field: value})
                   for field, values in {
                       "operator_ref": (None, [], 123, "", " "),
                       "manager_ref": (None, [], 123, "", " "),
                       "active_account": (1, "true", None),
                       "intake_receiving": (1, "true", None),
                       "granted_shops": (["aurora"], "aurora", None, (7,), ("",), (" ",)),
                   }.items() for value in values]
        for target in invalid:
            with self.subTest(target=target):
                self.assertEqual(propose_selective_pause_case(
                    case(), "rafael", "marina", (person("valid"), target)
                ).disposition, "DENIED_OR_UNVERIFIED")
                self.assertEqual(classify_manual_transfer_target(
                    case(), "marina", target
                ), "DENIED")

    def test_empty_valid_grants_still_require_case_scoped_authority(self):
        self.assertEqual(classify_manual_transfer_target(
            case(), "marina", person("lia", shops=())
        ), "S1_CASE_SCOPED_EXCEPTION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
