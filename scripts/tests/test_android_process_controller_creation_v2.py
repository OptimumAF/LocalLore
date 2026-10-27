"""Original synthetic controller-v2 adversaries; never device evidence.

Existing v1 fixtures are imported unchanged. Only the explicitly frozen v2
controller envelope and per-death creation observations are added here.
"""
import copy
import json
import unittest

from benchmarks import android_process_controller_evidence as evidence
from scripts.tests import test_android_process_controller_evidence as original


def current(case=original.CASES[0]):
    proof, expected = original.original(case)
    proof["version"] = 2
    proof["scope"] = "locallore_process_controller_v2"
    for index, terminal in enumerate(proof["terminal_observations"]):
        counts = {"create": 0, "create_named": 2 if index == 0 else 0}
        terminal["saved_creation"] = dict(counts)
        terminal["commands_creation"] = dict(counts)
    return proof, expected


def records_for(proof):
    return original.product_records(proof, version=2)


def both(proof, index, counts):
    value = copy.deepcopy(proof)
    for name in ("saved_creation", "commands_creation"):
        value["terminal_observations"][index][name] = copy.deepcopy(counts)
    return value


class ControllerCreationV2Tests(unittest.TestCase):
    def raw_refused(self, raw, expected):
        with self.assertRaises(evidence.ControllerEvidenceRefused) as caught:
            evidence.validate_controller_result(raw, expected)
        self.assertEqual(str(caught.exception), "controller_evidence_refused")
        self.assertNotIn(original.CANARY, str(caught.exception))

    def result_refused(self, proof, expected):
        self.raw_refused(original.frame(proof), expected)

    def records_refused(self, proof, records, expected):
        with self.assertRaises(evidence.ControllerEvidenceRefused) as caught:
            evidence.validate_product_records(proof, records, expected)
        self.assertEqual(str(caught.exception), "controller_evidence_refused")
        self.assertNotIn(original.CANARY, str(caught.exception))

    def test_four_v2_cases_preserve_original_game_fixture_and_helper_data(self):
        for case in original.CASES:
            with self.subTest(case=case):
                legacy, _ = original.original(case)
                proof, expected = current(case)
                before = copy.deepcopy(proof)
                raw = original.frame(proof)
                self.assertLessEqual(len(original.encoded(proof)), 4096)
                self.assertLessEqual(len(raw), 4160)
                self.assertEqual(evidence.validate_controller_result(raw, expected), proof)
                self.assertEqual(evidence.validate_controller_result(raw.replace(b"\n", b"\r\n"), expected), proof)
                records = records_for(proof)
                self.assertEqual(evidence.validate_product_records(proof, records, expected),
                                 {name: json.loads(data) for name, data in records.items()})
                self.assertEqual(proof, before)
                restored = copy.deepcopy(proof)
                restored["version"] = 1
                restored["scope"] = "locallore_process_controller_v1"
                for terminal in restored["terminal_observations"]:
                    del terminal["saved_creation"]
                    del terminal["commands_creation"]
                self.assertEqual(restored, legacy)

    def test_historical_v1_remains_closed_and_accepts_uniform_probe1_or_probe2(self):
        for case in original.CASES:
            # Validation of v2 must not mutate a shared key set used by v1.
            modern, expected = current(case)
            evidence.validate_controller_result(original.frame(modern), expected)
            legacy, expected = original.original(case)
            before = copy.deepcopy(legacy)
            self.assertEqual(evidence.validate_controller_result(original.frame(legacy), expected), legacy)
            for version in (1, 2):
                records = original.product_records(legacy, version=version)
                self.assertEqual(evidence.validate_product_records(legacy, records, expected),
                                 {name: json.loads(data) for name, data in records.items()})
            self.assertEqual(legacy, before)
            for index in (0, 1):
                for name in ("saved_creation", "commands_creation"):
                    bad = copy.deepcopy(legacy)
                    bad["terminal_observations"][index][name] = {"create": 0, "create_named": 0}
                    self.result_refused(bad, expected)

    def test_controller_versions_and_scope_pairs_cannot_be_mixed_or_coerced(self):
        proof, expected = current()
        for version in (True, 2.0, "2", None, 0, 3):
            self.result_refused(dict(proof, version=version), expected)
        self.result_refused(dict(proof, scope="locallore_process_controller_v1"), expected)
        self.result_refused(dict(proof, version=1), expected)
        legacy, _ = original.original()
        self.result_refused(dict(legacy, scope="locallore_process_controller_v2"), expected)
        self.result_refused(dict(legacy, version=2), expected)
        self.result_refused(dict(proof, extra=original.CANARY), expected)
        self.result_refused(dict(proof, fixture=dict(proof["fixture"], version=2)), expected)

    def test_each_terminal_requires_both_exact_creation_maps(self):
        for case in original.CASES:
            proof, expected = current(case)
            for index in (0, 1):
                for name in ("saved_creation", "commands_creation"):
                    missing = copy.deepcopy(proof)
                    del missing["terminal_observations"][index][name]
                    self.result_refused(missing, expected)
                    for value in (None, False, [], [0, 2], original.CANARY,
                                  {}, {"create": 0}, {"create_named": 2},
                                  {"create": 0, "named": 2}, {"legacy_create": 0, "create_named": 2},
                                  {"total_creation": 2}, {"create": 0, "create_named": 2, "extra": 0}):
                        self.result_refused(original.changed(proof, ["terminal_observations", index, name], value), expected)
                    alias = copy.deepcopy(proof)
                    terminal = alias["terminal_observations"][index]
                    terminal["creation"] = terminal.pop(name)
                    self.result_refused(alias, expected)
                extra = copy.deepcopy(proof)
                extra["terminal_observations"][index]["creation_total"] = 2 if index == 0 else 0
                self.result_refused(extra, expected)

    def test_creation_types_ranges_and_overflow_refuse_even_when_both_maps_agree(self):
        proof, expected = current()
        for index in (0, 1):
            wanted = {"create": 0, "create_named": 2 if index == 0 else 0}
            for key in wanted:
                # Matching coerced values are included, not merely wrong totals.
                values = (False, True, float(wanted[key]), str(wanted[key]), None,
                          -1, 4096, 4097, 2**64, [], {}, float("nan"), float("inf"))
                for value in values:
                    with self.subTest(index=index, key=key, value=repr(value)):
                        self.result_refused(both(proof, index, dict(wanted, **{key: value})), expected)

    def test_saved_and_command_creation_observations_must_agree(self):
        for case in original.CASES:
            proof, expected = current(case)
            for index in (0, 1):
                for name in ("saved_creation", "commands_creation"):
                    for key in ("create", "create_named"):
                        value = proof["terminal_observations"][index][name][key] + 1
                        self.result_refused(original.changed(proof, ["terminal_observations", index, name, key], value), expected)

    def test_legacy_named_and_cross_death_counts_cannot_be_aliased_by_a_sum(self):
        for case in original.CASES:
            proof, expected = current(case)
            for counts in ({"create": 2, "create_named": 0}, {"create": 1, "create_named": 1},
                           {"create": 0, "create_named": 0}, {"create": 0, "create_named": 3}):
                self.result_refused(both(proof, 0, counts), expected)
            for counts in ({"create": 1, "create_named": 0}, {"create": 0, "create_named": 1},
                           {"create": 0, "create_named": 2}, {"create": 1, "create_named": -1}):
                self.result_refused(both(proof, 1, counts), expected)
            swapped = both(both(proof, 0, {"create": 0, "create_named": 0}),
                           1, {"create": 0, "create_named": 2})
            self.result_refused(swapped, expected)

    def test_creation_fields_never_replace_the_existing_six_gameplay_counters(self):
        proof, expected = current()
        for index in (0, 1):
            for name in ("saved_game", "commands_game"):
                game = dict(proof["terminal_observations"][index][name], create_named=0)
                self.result_refused(original.changed(proof, ["terminal_observations", index, name], game), expected)
                self.result_refused(original.changed(proof, ["terminal_observations", index, name, "other"], 1), expected)

    def test_recursive_duplicate_keys_and_quiet_frame_still_refuse(self):
        proof, expected = current()
        raw = original.frame(proof)
        self.assertIn(b'"create_named":2', raw)
        duplicate = raw.replace(b'"create_named":2', b'"create_named":2,"create_named":2', 1)
        for bad in (duplicate, raw.replace(b'"version":2', b'"version":2,"version":2', 1),
                    raw.replace(b'"create_named":2', b'"create_named":NaN', 1),
                    raw.replace(b'"create_named":2', b'"create_named":Infinity', 1),
                    b"\xff" + raw, b"chatter " + original.CANARY.encode() + b"\n" + raw,
                    raw + raw, raw[:-1], raw + b"INSTRUMENTATION_CODE: -1\n"):
            self.raw_refused(bad, expected)

    def test_result2_requires_uniform_final_product_probe2(self):
        for case in original.CASES:
            proof, expected = current(case)
            modern = records_for(proof)
            legacy = original.product_records(proof, version=1)
            self.records_refused(proof, legacy, expected)
            for name in modern:
                self.records_refused(proof, dict(modern, **{name: legacy[name]}), expected)
                self.records_refused(proof, dict(legacy, **{name: modern[name]}), expected)

    def test_final_three_records_cannot_contain_automatic_legacy_or_named_creation(self):
        for case in original.CASES:
            proof, expected = current(case)
            records = records_for(proof)
            for name in records:
                value = json.loads(records[name])
                for key in ("create", "create_named"):
                    for number in (1, 2, 4096):
                        bad = original.changed(value, ["operations", key], number)
                        self.records_refused(proof, dict(records, **{name: original.encoded(bad)}), expected)
                    operations = dict(value["operations"])
                    del operations[key]
                    self.records_refused(proof, dict(records, **{name: original.encoded(dict(value, operations=operations))}), expected)

    def test_probe_version_scope_types_and_counter_aliases_remain_closed(self):
        proof, expected = current()
        records = records_for(proof)
        for name in records:
            value = json.loads(records[name])
            for version in (True, 2.0, "2", None, 0, 3):
                self.records_refused(proof, dict(records, **{name: original.encoded(dict(value, version=version))}), expected)
            self.records_refused(proof, dict(records, **{name: original.encoded(dict(value, scope="locallore_process_verify_v1"))}), expected)
            for operations in (dict(value["operations"], creation_total=0),
                               {key: number for key, number in value["operations"].items() if key != "create_named"}):
                self.records_refused(proof, dict(records, **{name: original.encoded(dict(value, operations=operations))}), expected)
            duplicate = records[name].replace(b'"create_named":0', b'"create_named":0,"create_named":0', 1)
            self.assertNotEqual(duplicate, records[name])
            self.records_refused(proof, dict(records, **{name: duplicate}), expected)

    def test_preview_metadata_counter_retains_4096_bound_without_creation_credit(self):
        proof, expected = current()
        records = records_for(proof)
        for name in records:
            value = original.changed(json.loads(records[name]), ["operations", "story_template"], 4096)
            records[name] = original.encoded(value)
        parsed = evidence.validate_product_records(proof, records, expected)
        for value in parsed.values():
            self.assertEqual(value["operations"]["story_template"], 4096)
            self.assertEqual(value["operations"]["create"], 0)
            self.assertEqual(value["operations"]["create_named"], 0)
        for name in records:
            value = json.loads(records[name])
            for number in (True, 4097, -1, 4096.0, "4096"):
                bad = original.changed(value, ["operations", "story_template"], number)
                self.records_refused(proof, dict(records, **{name: original.encoded(bad)}), expected)

    def test_proof4096_and_frame4160_caps_do_not_expand_for_v2(self):
        proof, expected = current()
        body = original.encoded(proof)
        prefix, suffix = b"INSTRUMENTATION_RESULT: proof=", b"\nINSTRUMENTATION_CODE: -1\n"
        self.assertLessEqual(len(body), 4096)
        at_limit = prefix + body + b" " * (4096 - len(body)) + suffix
        self.assertLessEqual(len(at_limit), 4160)
        self.assertEqual(evidence.validate_controller_result(at_limit, expected), proof)
        over_json = prefix + body + b" " * (4097 - len(body)) + suffix
        self.assertLessEqual(len(over_json), 4160)
        self.raw_refused(over_json, expected)
        at_outer_limit = prefix + body + b" " * (4160 - len(prefix) - len(body) - len(suffix)) + suffix
        self.assertEqual(len(at_outer_limit), 4160)
        self.raw_refused(at_outer_limit, expected)  # Inner JSON is already over4096.
        self.raw_refused(b"x" * 4161, expected)

    def test_final_product_record4096_cap_remains_exact(self):
        proof, expected = current()
        records = records_for(proof)
        padded = {name: data + b" " * (4096 - len(data)) for name, data in records.items()}
        self.assertTrue(all(len(data) == 4096 for data in padded.values()))
        self.assertEqual(evidence.validate_product_records(proof, padded, expected),
                         {name: json.loads(data) for name, data in records.items()})
        for name in records:
            self.records_refused(proof, dict(padded, **{name: padded[name] + b" "}), expected)

    def test_product_validator_revalidates_new_creation_observations(self):
        proof, expected = current()
        records = records_for(proof)
        for index in (0, 1):
            value = 0 if index == 0 else 2
            bad = both(proof, index, {"create": 0, "create_named": value})
            self.records_refused(bad, records, expected)


if __name__ == "__main__":
    unittest.main()
