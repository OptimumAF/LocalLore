"""Independent hostile ownership/checkpoint cases; no device, SDK or model calls.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_preservation as preservation

ORDER = ("model_metadata", "cache_metadata", "prior_canonical", "guarded_canonical",
         "traced_canonical", "phase_journal", "storage", "inventory")
KEYS = {"version", "scope", "status", "checks", "clients_cleaned", "boundary_verified",
        "retention_complete", "collection_complete", "preservation_verified", "stop_reason"}


class Fixture:
    def __init__(self):
        self.known = True
        self.events = []
        self.saved = []
        self.checks = {name: self.check(name) for name in ORDER}

    def check(self, name, result="matched"):
        def callback():
            self.events.append(name)
            return result
        return callback

    def boundary(self):
        self.events.append("boundary")
        return True

    def retain(self, report):
        self.events.append("retain")
        self.saved.append(copy.deepcopy(report))

    def clients(self):
        return self.known

    def collect(self, **overrides):
        args = {"checks": self.checks, "verify_boundary": self.boundary,
                "clients_known": self.clients, "retain": self.retain}
        args.update(overrides)
        return preservation.collect(**args)


class PreservationTests(unittest.TestCase):
    def shape(self, result):
        self.assertEqual(set(result), KEYS)
        self.assertIs(type(result["version"]), int)
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["scope"], "android_preservation_collection")
        self.assertIn(result["status"], {"input_refused", "observed", "stopped"})
        self.assertIn(result["stop_reason"], {"none", "input", "ownership_unknown", "boundary_failed",
                                             "check_failed", "invalid_check", "retention_failed"})
        self.assertIs(type(result["checks"]), list)
        self.assertEqual([row["check"] for row in result["checks"]], list(ORDER))
        for row in result["checks"]:
            self.assertEqual(set(row), {"check", "status", "boundary_verified"})
            self.assertIn(row["status"], {"not_run", "matched", "mismatched", "unavailable", "error"})
            self.assertIs(type(row["boundary_verified"]), bool)
        for key in ("clients_cleaned", "boundary_verified", "retention_complete",
                    "collection_complete", "preservation_verified"):
            self.assertIs(type(result[key]), bool)

    def test_success_exact_checkpoint_sequence_and_before_after_boundaries(self):
        f = Fixture()
        result = f.collect()
        self.shape(result)
        self.assertEqual(f.events, ["retain"] + [event for name in ORDER
                         for event in ("boundary", name, "boundary", "retain")])
        self.assertEqual(len(f.saved), 9)
        self.assertTrue(all(checkpoint["preservation_verified"] is False for checkpoint in f.saved))
        self.assertTrue(all(row["status"] == "not_run" for row in f.saved[0]["checks"]))
        self.assertFalse(f.saved[0]["collection_complete"])
        self.assertTrue(result["collection_complete"])
        self.assertTrue(result["preservation_verified"])
        self.assertTrue(result["retention_complete"])
        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["stop_reason"], "none")
        for finished, checkpoint in enumerate(f.saved[1:], 1):
            self.assertEqual([row["status"] for row in checkpoint["checks"]],
                             ["matched"] * finished + ["not_run"] * (8 - finished))

    def test_mismatch_and_unavailable_continue_to_later_canonical_and_final_checks(self):
        f = Fixture()
        f.checks["cache_metadata"] = f.check("cache_metadata", "mismatched")
        f.checks["prior_canonical"] = f.check("prior_canonical", "unavailable")
        result = f.collect()
        self.shape(result)
        self.assertEqual([event for event in f.events if event in ORDER], list(ORDER))
        self.assertEqual(result["status"], "observed")
        self.assertTrue(result["collection_complete"])
        self.assertTrue(result["retention_complete"])
        self.assertTrue(result["boundary_verified"])
        self.assertFalse(result["preservation_verified"])
        self.assertEqual(result["stop_reason"], "none")
        self.assertEqual(result["checks"][1]["status"], "mismatched")
        self.assertEqual(result["checks"][2]["status"], "unavailable")

    def test_every_valid_nonmatch_position_completes_collection_without_promoting_pass(self):
        for name in ORDER:
            for status in ("mismatched", "unavailable"):
                with self.subTest(name=name, status=status):
                    f = Fixture(); f.checks[name] = f.check(name, status)
                    result = f.collect()
                    self.assertTrue(result["collection_complete"])
                    self.assertFalse(result["preservation_verified"])
                    self.assertEqual(len(f.saved), 9)

    def test_invalid_input_is_refused_before_any_callback(self):
        for name in ORDER:
            for mutation in ("missing", "noncallable"):
                with self.subTest(name=name, mutation=mutation):
                    f = Fixture()
                    if mutation == "missing":
                        del f.checks[name]
                    else:
                        f.checks[name] = "matched"
                    result = f.collect()
                    self.shape(result)
                    self.assertEqual(result["status"], "input_refused")
                    self.assertEqual(result["stop_reason"], "input")
                    self.assertEqual(f.events, [])
        class DictSubclass(dict):
            pass
        for bad in (None, [], DictSubclass(Fixture().checks),
                    {**Fixture().checks, "private_extra": lambda: "matched"}):
            f = Fixture(); result = f.collect(checks=bad)
            self.assertEqual(result["status"], "input_refused")
            self.assertEqual(f.events, [])
        for key in ("verify_boundary", "clients_known", "retain"):
            f = Fixture(); result = f.collect(**{key: None})
            self.assertEqual(result["status"], "input_refused")
            self.assertEqual(f.events, [])

    def test_input_dictionary_insertion_order_cannot_change_dispatch_order(self):
        f = Fixture()
        result = f.collect(checks=dict(reversed(list(f.checks.items()))))
        self.assertTrue(result["preservation_verified"])
        self.assertEqual([event for event in f.events if event in ORDER], list(ORDER))

    def test_validated_callback_references_survive_original_dictionary_mutation(self):
        for stage in ("initial_sink", "first_check"):
            with self.subTest(stage=stage):
                f = Fixture()
                def retain(report):
                    f.retain(report)
                    if stage == "initial_sink":
                        f.checks.clear()
                def first_check():
                    f.events.append(ORDER[0])
                    if stage == "first_check":
                        f.checks.clear()
                    return "matched"
                f.checks[ORDER[0]] = first_check
                result = f.collect(retain=retain)
                self.assertEqual([e for e in f.events if e in ORDER], list(ORDER))
                self.assertTrue(result["preservation_verified"])

    def test_initial_unknown_or_truthy_owner_refuses_every_observation_dispatch(self):
        for value in (False, 1, "true", None, []):
            with self.subTest(value=value):
                f = Fixture(); result = f.collect(clients_known=lambda: value)
                self.shape(result)
                self.assertTrue(all(event == "retain" for event in f.events))
                self.assertLessEqual(len(f.saved), 1)
                self.assertEqual(result["stop_reason"], "ownership_unknown")
                self.assertFalse(result["clients_cleaned"])

    def test_owner_predicate_exception_is_private_and_stops_without_io(self):
        f = Fixture()
        def broken():
            raise RuntimeError("private-owner-diagnostic")
        result = f.collect(clients_known=broken)
        self.assertTrue(all(event == "retain" for event in f.events))
        self.assertLessEqual(len(f.saved), 1)
        self.assertEqual(result["stop_reason"], "ownership_unknown")
        self.assertNotIn("private-owner-diagnostic", json.dumps(result))

    def test_pre_boundary_false_truthy_or_exception_never_calls_first_check(self):
        for value in (False, 1, "yes", None, RuntimeError("private-boundary")):
            with self.subTest(value=value):
                f = Fixture()
                def boundary():
                    f.events.append("boundary")
                    if isinstance(value, Exception):
                        raise value
                    return value
                result = f.collect(verify_boundary=boundary)
                self.shape(result)
                self.assertEqual(result["stop_reason"], "boundary_failed")
                self.assertTrue(all(row["status"] == "not_run" for row in result["checks"]))
                self.assertEqual([e for e in f.events if e in ORDER], [])
                self.assertNotIn("private-boundary", json.dumps(result))

    def test_post_boundary_failure_retains_observation_but_not_verified_claim(self):
        f = Fixture(); calls = 0
        def boundary():
            nonlocal calls
            calls += 1; f.events.append("boundary")
            return calls == 1
        result = f.collect(verify_boundary=boundary)
        self.shape(result)
        self.assertEqual(result["checks"][0], {"check": "model_metadata", "status": "matched",
                                               "boundary_verified": False})
        self.assertTrue(all(row["status"] == "not_run" for row in result["checks"][1:]))
        self.assertEqual(result["stop_reason"], "boundary_failed")
        self.assertFalse(result["preservation_verified"])
        self.assertFalse(result["collection_complete"])
        self.assertFalse(result["boundary_verified"])
        self.assertEqual(calls, 2)

    def test_each_check_exception_stops_without_post_boundary_and_keeps_prior_rows(self):
        for index, name in enumerate(ORDER):
            with self.subTest(name=name):
                f = Fixture()
                def broken():
                    f.events.append(name)
                    raise OSError("private-path/secret")
                f.checks[name] = broken
                result = f.collect()
                self.shape(result)
                self.assertEqual(result["stop_reason"], "check_failed")
                self.assertEqual(result["checks"][index]["status"], "error")
                self.assertFalse(result["checks"][index]["boundary_verified"])
                self.assertEqual(f.events.count("boundary"), index * 2 + 1)
                self.assertEqual([e for e in f.events if e in ORDER], list(ORDER[:index + 1]))
                self.assertNotIn("private-path", json.dumps(result))

    def test_invalid_check_values_are_not_truthy_or_synthesized_matches(self):
        class EqualityTrap:
            def __eq__(self, other):
                raise AssertionError("private-equality-trap")
        class StringSubclass(str):
            pass
        for value in (True, 1, None, {}, EqualityTrap(), StringSubclass("matched"), "MATCHED",
                      "matched\n", "error", "not_run", "private-secret"):
            with self.subTest(value=value):
                f = Fixture(); f.checks[ORDER[0]] = f.check(ORDER[0], value)
                result = f.collect()
                self.assertEqual(result["stop_reason"], "invalid_check")
                self.assertEqual(result["checks"][0]["status"], "error")
                self.assertEqual(f.events.count("boundary"), 1)
                self.assertFalse(result["preservation_verified"])
                self.assertNotIn("private-secret", json.dumps(result))

    def test_ownership_loss_after_successful_post_boundary_invalidates_observation_fence(self):
        f = Fixture(); calls = 0
        def boundary():
            nonlocal calls
            calls += 1; f.events.append("boundary")
            if calls == 2:
                f.known = False
            return True
        result = f.collect(verify_boundary=boundary)
        self.assertEqual([e for e in f.events if e != "retain"], ["boundary", ORDER[0], "boundary"])
        self.assertEqual(result["checks"][0]["status"], "matched")
        self.assertFalse(result["checks"][0]["boundary_verified"])
        self.assertFalse(result["clients_cleaned"])
        self.assertFalse(result["collection_complete"])
        self.assertFalse(result["preservation_verified"])
        self.assertEqual(result["stop_reason"], "ownership_unknown")

    def test_original_failure_survives_failed_stopped_checkpoint(self):
        f = Fixture(); calls = 0
        def broken_check():
            f.events.append(ORDER[0])
            raise OSError("private-primary")
        def retain(report):
            nonlocal calls
            calls += 1; f.retain(report)
            if calls == 2:
                raise OSError("private-secondary")
        f.checks[ORDER[0]] = broken_check
        result = f.collect(retain=retain)
        self.assertEqual(result["stop_reason"], "check_failed")
        self.assertFalse(result["retention_complete"])
        self.assertFalse(result["preservation_verified"])
        self.assertEqual(calls, 2)
        self.assertNotIn("private-", json.dumps(result))

    def test_ownership_loss_during_boundary_never_reaches_check_or_fresh_boundary(self):
        f = Fixture()
        def boundary():
            f.events.append("boundary"); f.known = False
            return True
        result = f.collect(verify_boundary=boundary)
        self.assertEqual([event for event in f.events if event != "retain"], ["boundary"])
        self.assertLessEqual(len(f.saved), 2)
        self.assertEqual(result["stop_reason"], "ownership_unknown")
        self.assertFalse(result["clients_cleaned"])

    def test_ownership_loss_during_check_prevents_post_boundary_and_further_reads(self):
        f = Fixture()
        def check():
            f.events.append(ORDER[0]); f.known = False
            return "matched"
        f.checks[ORDER[0]] = check
        result = f.collect()
        self.assertEqual([event for event in f.events if event != "retain"], ["boundary", ORDER[0]])
        self.assertLessEqual(len(f.saved), 2)
        self.assertEqual(result["stop_reason"], "ownership_unknown")
        self.assertFalse(result["preservation_verified"])

    def test_false_owner_observation_is_sticky_even_if_predicate_would_recover(self):
        f = Fixture(); seen_false = False; calls = 0
        def clients():
            nonlocal calls, seen_false
            calls += 1
            if calls == 2:
                seen_false = True
                return False
            return True
        result = f.collect(clients_known=clients)
        self.assertTrue(seen_false)
        self.assertEqual(result["stop_reason"], "ownership_unknown")
        self.assertFalse(result["clients_cleaned"])
        self.assertFalse(result["preservation_verified"])
        self.assertFalse(any(event in ORDER or event == "boundary" for event in f.events))

    def test_loss_at_checkpoint_entry_writes_one_fenced_checkpoint_without_next_iteration(self):
        f = Fixture(); post_boundary_seen = False
        def clients():
            nonlocal post_boundary_seen
            if f.events.count("boundary") == 2:
                if post_boundary_seen:
                    return False
                post_boundary_seen = True
            return True
        result = f.collect(clients_known=clients)
        self.assertTrue(post_boundary_seen)
        self.assertEqual([event for event in f.events if event != "retain"],
                         ["boundary", ORDER[0], "boundary"])
        self.assertEqual(len(f.saved), 2)
        self.assertEqual(f.saved[-1]["status"], "stopped")
        self.assertFalse(f.saved[-1]["clients_cleaned"])
        self.assertEqual(result["stop_reason"], "ownership_unknown")
        self.assertFalse(result["preservation_verified"])

    def test_sink_mutation_cannot_promote_mismatch_or_change_dispatch_order(self):
        f = Fixture(); f.checks["cache_metadata"] = f.check("cache_metadata", "mismatched")
        references = []
        def retain(report):
            f.retain(report); references.append(report)
            report["checks"].reverse()
            report["checks"][0]["status"] = "matched"
            report["preservation_verified"] = True
            report["stop_reason"] = "private-forgery"
        result = f.collect(retain=retain)
        self.shape(result)
        self.assertEqual(result["checks"][1]["status"], "mismatched")
        self.assertFalse(result["preservation_verified"])
        self.assertEqual(result["stop_reason"], "none")
        self.assertEqual([e for e in f.events if e in ORDER], list(ORDER))
        references[0].clear()
        self.assertEqual(len(result["checks"]), 8)

    def test_sink_failure_at_initial_intermediate_and_final_checkpoint_never_retries(self):
        for fail_at in (1, 4, 9):
            with self.subTest(fail_at=fail_at):
                f = Fixture(); calls = 0
                def retain(report):
                    nonlocal calls
                    calls += 1; f.retain(report)
                    if calls == fail_at:
                        raise OSError("private-retention-path")
                result = f.collect(retain=retain)
                self.assertEqual(calls, fail_at)
                self.assertEqual(result["stop_reason"], "retention_failed")
                self.assertFalse(result["retention_complete"])
                self.assertFalse(result["preservation_verified"])
                self.assertEqual([e for e in f.events if e in ORDER], list(ORDER[:fail_at - 1]))
                self.assertNotIn("private-retention-path", json.dumps(result))

    def test_sink_poison_initial_or_final_revokes_pass_without_any_later_callback(self):
        for poison_at in (1, 9):
            with self.subTest(poison_at=poison_at):
                f = Fixture(); calls = 0
                def retain(report):
                    nonlocal calls
                    calls += 1; f.retain(report)
                    if calls == poison_at:
                        f.known = False
                result = f.collect(retain=retain)
                self.assertEqual(calls, poison_at)
                self.assertEqual(result["stop_reason"], "ownership_unknown")
                self.assertFalse(result["clients_cleaned"])
                self.assertFalse(result["retention_complete"])
                self.assertFalse(result["preservation_verified"])
                self.assertEqual(f.events[-1], "retain")

    def test_owner_loss_and_primary_check_error_still_prevent_further_dispatch(self):
        f = Fixture()
        def broken():
            f.events.append(ORDER[0]); f.known = False
            raise RuntimeError("private-original")
        f.checks[ORDER[0]] = broken
        result = f.collect()
        self.assertFalse(result["clients_cleaned"])
        self.assertFalse(result["preservation_verified"])
        self.assertEqual([event for event in f.events if event != "retain"], ["boundary", ORDER[0]])
        self.assertLessEqual(len(f.saved), 2)
        self.assertNotIn("private-original", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
