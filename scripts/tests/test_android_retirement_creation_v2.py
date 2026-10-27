"""Original synthetic controller-v2 compatibility controls, not actual retirement execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
Author source-only; tests UNRUN until coordinator qualification.
"""
import copy
import json
import unittest

from benchmarks import android_retirement_evidence as evidence
from scripts.tests import test_android_retirement_evidence as historical


def fixture(retained):
    """Reuse the untouched complete historical native-helper/sidecar fixtures."""
    data = historical.fixture(retained)
    proof = data[0]
    proof["version"] = 2
    proof["scope"] = "locallore_process_controller_v2"
    for index, row in enumerate(proof["terminal_observations"]):
        row["saved_creation"] = {"create": 0, "create_named": 2 if index == 0 else 0}
        row["commands_creation"] = row["saved_creation"].copy()
    return data


class AndroidRetirementCreationV2Tests(unittest.TestCase):
    def refused(self, data):
        with self.assertRaises(evidence.RetirementEvidenceRefused) as caught:
            evidence.validate_retirement(*data)
        self.assertLess(len(str(caught.exception)), 32)
        self.assertNotIn("SYNTHETIC", str(caught.exception))

    def test_v2_both_cases_keep_full_helpers_and_sidecars_without_mutating_input(self):
        for retained in (False, True):
            with self.subTest(retained=retained):
                data = fixture(retained)
                before = copy.deepcopy(data)
                result = evidence.validate_retirement(*data)
                self.assertEqual({"case": data[3]["case"], "helper_count": 3,
                                  "sidecar_count": 4 if retained else 0,
                                  "preserved_sha256": historical.digest(next(iter(data[2].values()))) if retained else None,
                                  "passed": True}, result)
                self.assertEqual(before, data)

    def test_historical_v1_both_cases_remain_exact_without_fabricated_creation_metadata(self):
        for retained in (False, True):
            data = historical.fixture(retained)
            before = copy.deepcopy(data)
            self.assertTrue(evidence.validate_retirement(*data)["passed"])
            self.assertEqual(before, data)
            for row in data[0]["terminal_observations"]:
                self.assertNotIn("saved_creation", row)
                self.assertNotIn("commands_creation", row)

    def test_version_and_scope_are_an_exact_closed_typed_pair(self):
        bad = ((1, "locallore_process_controller_v2"), (2, "locallore_process_controller_v1"),
               (0, "locallore_process_controller_v0"), (3, "locallore_process_controller_v3"),
               (True, "locallore_process_controller_v1"), (False, "locallore_process_controller_v2"),
               (2.0, "locallore_process_controller_v2"), ("2", "locallore_process_controller_v2"),
               (None, "locallore_process_controller_v2"), (2, "locallore_process_controller_v02"),
               (2, "locallore_process_controller_v2 "), (2, None))
        for retained in (False, True):
            for version, scope in bad:
                with self.subTest(retained=retained, version=version, scope=scope):
                    data = fixture(retained)
                    data[0].update(version=version, scope=scope)
                    self.refused(data)

    def test_v2_requires_each_creation_map_in_each_terminal(self):
        for retained in (False, True):
            for index in range(2):
                for key in ("saved_creation", "commands_creation"):
                    with self.subTest(retained=retained, index=index, key=key):
                        data = fixture(retained)
                        data[0]["terminal_observations"][index].pop(key)
                        self.refused(data)

    def test_maps_cannot_be_missing_extra_aliased_or_replaced_by_totals(self):
        bad = ({"create_named": 2}, {"create": 0}, {"create": 0, "create_named": 2, "other": 0},
               {"create": 0, "named_create": 2}, {"create": 0, "createNamed": 2},
               {"total": 2}, {"create": 2}, [], None, "SYNTHETIC private metadata")
        for retained in (False, True):
            for index in range(2):
                for key in ("saved_creation", "commands_creation"):
                    for value in bad:
                        with self.subTest(retained=retained, index=index, key=key, value=value):
                            data = fixture(retained)
                            data[0]["terminal_observations"][index][key] = copy.deepcopy(value)
                            self.refused(data)

    def test_creation_counts_refuse_bool_float_nonfinite_string_and_out_of_bounds(self):
        bad = (False, True, 0.0, 2.0, float("nan"), float("inf"), "0", "2", None, -1, 4097, 2**63)
        for retained in (False, True):
            for index in range(2):
                for key in ("saved_creation", "commands_creation"):
                    for field in ("create", "create_named"):
                        for value in bad:
                            with self.subTest(retained=retained, index=index, key=key, field=field, value=value):
                                data = fixture(retained)
                                data[0]["terminal_observations"][index][key][field] = value
                                self.refused(data)

    def test_first_terminal_requires_named_two_and_legacy_zero_separately(self):
        for retained in (False, True):
            for value in ({"create": 2, "create_named": 0}, {"create": 1, "create_named": 1},
                          {"create": 0, "create_named": 0}, {"create": 0, "create_named": 1},
                          {"create": 0, "create_named": 3}, {"create": 4096, "create_named": 4096}):
                for key in ("saved_creation", "commands_creation"):
                    data = fixture(retained)
                    data[0]["terminal_observations"][0][key] = value.copy()
                    self.refused(data)

    def test_second_terminal_refuses_any_automatic_legacy_or_named_creation(self):
        for retained in (False, True):
            for value in ({"create": 1, "create_named": 0}, {"create": 0, "create_named": 1},
                          {"create": 0, "create_named": 2}, {"create": 4096, "create_named": 0}):
                for key in ("saved_creation", "commands_creation"):
                    data = fixture(retained)
                    data[0]["terminal_observations"][1][key] = value.copy()
                    self.refused(data)

    def test_historical_v1_refuses_new_terminal_fields_even_when_all_zero(self):
        for retained in (False, True):
            for index in range(2):
                for key in ("saved_creation", "commands_creation"):
                    data = historical.fixture(retained)
                    data[0]["terminal_observations"][index][key] = {"create": 0, "create_named": 0}
                    self.refused(data)

    def test_v2_terminal_fields_order_identity_and_original_game_remain_bound(self):
        for retained in (False, True):
            for mutation in (lambda rows: rows[0].update(creation=2),
                             lambda rows: rows[0].pop("saved_game"),
                             lambda rows: rows[1].update(pid=rows[0]["pid"]),
                             lambda rows: rows.reverse(),
                             lambda rows: rows[0]["saved_game"].update(other=0)):
                data = fixture(retained)
                mutation(data[0]["terminal_observations"])
                self.refused(data)

    def test_v2_cannot_omit_or_replace_original_helper_bodies(self):
        for retained in (False, True):
            for mode in ("load", "probe", "retire"):
                data = fixture(retained)
                data[1].pop(mode)
                self.refused(data)
                data = fixture(retained)
                data[1][mode] = b'{}\n'
                self.refused(data)

    def test_v2_does_not_bypass_helper_ownership_provenance_or_retirement_state(self):
        for retained in (False, True):
            for change in (lambda value: value.update(archive_closed=False),
                           lambda value: value.update(workspace_closed=1),
                           lambda value: value.update(product_sha256="e" * 64),
                           lambda value: value.update(commit_attempts=0),
                           lambda value: value["after"].update(target_active=True)):
                data = fixture(retained)
                historical.replace_helper(data, "retire", change)
                self.refused(data)

    def test_v2_retained_parent_requires_all_four_unchanged_original_sidecars(self):
        for name in evidence.SIDECARS:
            data = fixture(True)
            data[2].pop(name)
            self.refused(data)
            data = fixture(True)
            data[2][name] += b' '
            self.refused(data)
        data = fixture(False)
        data[2][evidence.SIDECARS[0]] = b'{}'
        self.refused(data)

    def test_v2_rebound_sidecars_still_require_original_receipt_scope_and_prefix(self):
        for change in (lambda value: value["receipts"][0]["request"]["scope"].update(branch="grandchild_g"),
                       lambda value: value["receipts"][1]["request"]["intent"]["value"].update(text="SYNTHETIC altered prefix"),
                       lambda value: value["player"].update(observer="omniscient")):
            data = fixture(True)
            value = json.loads(next(iter(data[2].values())))
            change(value["views"]["retained"])
            historical.replace_sidecars(data, historical.canonical(value))
            self.refused(data)


if __name__ == "__main__":
    unittest.main()
