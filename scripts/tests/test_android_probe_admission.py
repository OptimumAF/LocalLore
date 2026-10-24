"""Storage/dispatch regressions with synthetic samples and a mocked controller.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_probe_admission as gate


def sample(**changes):
    return {"version": 1, "host_free_bytes": 5 * gate.GIB, "evidence_free_bytes": 10 * gate.GIB,
            "guest_free_bytes": 2 * gate.GIB, "cache_bytes": 0, **changes}


def terminal(**changes):
    return {"clients_cleaned": True, "process_absent": True, "check_passed": True, **changes}


class ProbeAdmissionTest(unittest.TestCase):
    def run_guarded(self, measure, probe):
        with mock.patch.object(gate.play, "run_probe", probe):
            return gate.run_play_probe_with_admission(measure, "device", "apk", "gift", "raw-sink")

    def test_exact_before_thresholds_admit_without_consuming_existing_cache(self):
        self.assertEqual(gate.before_probe(sample(cache_bytes=788412736))["status"], "admitted")

    def test_one_byte_below_each_required_budget_blocks(self):
        for key, limit, reason in (("host_free_bytes", 5 * gate.GIB, "host_headroom"),
                                   ("guest_free_bytes", 2 * gate.GIB, "guest_headroom"),
                                   ("evidence_free_bytes", 10 * gate.GIB, "evidence_headroom")):
            with self.subTest(key=key):
                self.assertEqual(gate.before_probe(sample(**{key: limit - 1}))["reasons"], [reason])

    def test_no_missing_unknown_policy_override_or_bad_version(self):
        values = [None, [], {**sample(), "cache_growth_budget_bytes": 0}, {**sample(), "version": True},
                  {**sample(), "version": 2}]
        value = sample()
        value.pop("cache_bytes")
        values.append(value)
        for value in values:
            with self.subTest(value=value), self.assertRaises(gate.InvalidSample):
                gate.before_probe(value)

    def test_invalid_numeric_samples_rejected(self):
        for key in gate.SAMPLE_KEYS - {"version"}:
            for invalid in (True, False, 0.0, 1.0, -1, gate.MAX_BYTES + 1, "5", None):
                with self.subTest(key=key, invalid=invalid), self.assertRaises(gate.InvalidSample):
                    gate.validate(sample(**{key: invalid}))

    def test_refused_admission_prevents_entire_legacy_controller(self):
        probe = mock.Mock(side_effect=AssertionError("SDK stop must never be reached"))
        measure = mock.Mock(return_value=sample(guest_free_bytes=1800622080))
        value = self.run_guarded(measure, probe)
        self.assertFalse(value.probe_dispatched)
        probe.assert_not_called()
        measure.assert_called_once_with()
        self.assertIsNone(value.post)

    def test_failed_or_invalid_initial_sampler_never_dispatches(self):
        original = OSError("private path and device identifier")
        for measure in (mock.Mock(side_effect=original), mock.Mock(return_value={})):
            probe = mock.Mock()
            value = self.run_guarded(measure, probe)
            self.assertFalse(value.metadata()["storage_checks_passed"])
            self.assertEqual(value.admission["reasons"], ["sample_failed"])
            probe.assert_not_called()
            self.assertNotIn("private path", repr(value))
        self.assertIs(self.run_guarded(mock.Mock(side_effect=original), mock.Mock()).sample_failure, original)

    def test_guarded_entry_calls_exact_controller_once_after_sample(self):
        order = []
        def measure():
            order.append("sample")
            return sample()
        def probe(*args):
            order.append("probe")
            self.assertEqual(args, ("device", "apk", "gift", False, "raw-sink"))
            return terminal()
        result = self.run_guarded(measure, mock.Mock(side_effect=probe))
        self.assertEqual(order, ["sample", "probe", "sample"])
        self.assertTrue(result.probe_dispatched)
        self.assertTrue(result.metadata()["storage_checks_passed"])

    def test_returned_sample_is_copied_before_probe_can_change_it(self):
        shared = sample()
        def probe(*_):
            shared["guest_free_bytes"] = gate.GIB
            shared["cache_bytes"] = gate.GIB
            return terminal()
        result = self.run_guarded(lambda: shared, mock.Mock(side_effect=probe))
        self.assertEqual(result.admission["sample"]["guest_free_bytes"], 2 * gate.GIB)
        self.assertEqual(result.post["observed_deltas"]["guest_net_consumption_bytes"], gate.GIB)
        self.assertTrue(result.metadata()["storage_checks_passed"])

    def test_exact_post_reserves_and_growth_budget_pass(self):
        post = gate.after_probe(sample(), sample(host_free_bytes=4 * gate.GIB, guest_free_bytes=gate.GIB,
                                                cache_bytes=gate.GIB))
        self.assertEqual(post["status"], "admitted")

    def test_each_post_reserve_failure_remains_visible(self):
        for key, limit, reason in (("host_free_bytes", 4 * gate.GIB, "host_reserve"),
                                   ("guest_free_bytes", gate.GIB, "guest_reserve"),
                                   ("evidence_free_bytes", 10 * gate.GIB, "evidence_reserve")):
            with self.subTest(key=key):
                post = gate.after_probe(sample(), sample(**{key: limit - 1}))
                self.assertEqual(post["status"], "blocked")
                self.assertIn(reason, post["reasons"])

    def test_consumption_budget_can_fail_while_reserve_still_passes(self):
        before = sample(host_free_bytes=8 * gate.GIB, guest_free_bytes=5 * gate.GIB)
        for changes, reason in (({"cache_bytes": gate.GIB + 1}, "cache_growth_budget"),
                                ({"host_free_bytes": 7 * gate.GIB - 1}, "host_consumption_budget"),
                                ({"guest_free_bytes": 4 * gate.GIB - 1}, "guest_consumption_budget")):
            with self.subTest(reason=reason):
                self.assertIn(reason, gate.after_probe(before, {**before, **changes})["reasons"])

    def test_cache_decrease_blocks_and_free_space_increase_does_not_assert_cause(self):
        self.assertIn("cache_decreased", gate.after_probe(sample(cache_bytes=10), sample(cache_bytes=9))["reasons"])
        value = gate.after_probe(sample(), sample(host_free_bytes=6 * gate.GIB, guest_free_bytes=3 * gate.GIB))
        self.assertEqual(value["status"], "admitted")
        self.assertEqual(value["observed_deltas"]["host_net_consumption_bytes"], -gate.GIB)

    def test_nonadmitted_before_cannot_be_used_for_post_success(self):
        with self.assertRaisesRegex(gate.InvalidSample, "before_not_admitted"):
            gate.after_probe(sample(guest_free_bytes=0), sample())

    def test_callback_exception_preserved_and_no_dependent_sampler_called(self):
        error = RuntimeError("private model or SQL details")
        measure = mock.Mock(return_value=sample())
        value = self.run_guarded(measure, mock.Mock(side_effect=error))
        self.assertIs(value.failure, error)
        self.assertEqual(value.post["reasons"], ["probe_ownership_unknown"])
        measure.assert_called_once_with()
        self.assertNotIn("private model", repr(value))
        self.assertTrue(value.metadata()["probe_raised"])

    def test_unknown_ownership_or_malformed_result_forbids_after_reads(self):
        for returned in (None, [], {}, terminal(clients_cleaned=False), terminal(process_absent=False),
                         terminal(clients_cleaned=1), terminal(process_absent=1)):
            with self.subTest(returned=returned):
                measure = mock.Mock(return_value=sample())
                value = self.run_guarded(measure, mock.Mock(return_value=returned))
                self.assertIs(value.result, returned)
                self.assertEqual(value.post["reasons"], ["probe_ownership_unknown"])
                measure.assert_called_once_with()

    def test_failed_probe_with_known_clean_owners_keeps_failure_separate_from_storage(self):
        returned = terminal(check_passed=False, status="observed", result={"outcome": "failed", "error": "timeout"})
        value = self.run_guarded(mock.Mock(side_effect=[sample(), sample()]), mock.Mock(return_value=returned))
        self.assertIs(value.result, returned)
        self.assertFalse(value.result["check_passed"])
        self.assertTrue(value.metadata()["storage_checks_passed"])

    def test_post_storage_failure_never_erases_or_rolls_back_an_accepted_receipt(self):
        returned = terminal(result={"revision_after": 1, "receipt": "synthetic accepted receipt"})
        value = self.run_guarded(mock.Mock(side_effect=[sample(), sample(guest_free_bytes=0)]),
                                 mock.Mock(return_value=returned))
        self.assertFalse(value.metadata()["storage_checks_passed"])
        self.assertIs(value.result, returned)
        self.assertEqual(value.result["result"]["revision_after"], 1)
        self.assertTrue(value.result["check_passed"])

    def test_failed_after_sampler_keeps_original_result_and_exception(self):
        returned = terminal(check_passed=False)
        error = OSError("private path")
        value = self.run_guarded(mock.Mock(side_effect=[sample(), error]), mock.Mock(return_value=returned))
        self.assertIs(value.result, returned)
        self.assertIs(value.sample_failure, error)
        self.assertIsNone(value.failure)
        self.assertEqual(value.post["reasons"], ["sample_failed"])

    def test_strict_json_size_duplicates_nonfinite_and_cli_failure_privacy(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-sample.json"
            for raw in (b'{"version":1,"version":1}', b'{"cache_bytes":NaN}', b" " * (16 * 1024 + 1)):
                path.write_bytes(raw)
                with self.assertRaises(gate.InvalidSample):
                    gate.load_sample(path)
            with contextlib.redirect_stdout(output := io.StringIO()):
                code = gate.main(["--sample", str(path.parent / "missing-secret")])
            self.assertEqual(code, 1)
            self.assertNotIn(directory, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["reasons"], ["sample_failed"])

    def test_cli_admission_and_refusal_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            for data, wanted in ((sample(), 0), (sample(guest_free_bytes=1800622080), 2)):
                path.write_text(json.dumps(data), encoding="utf-8")
                with contextlib.redirect_stdout(output := io.StringIO()):
                    self.assertEqual(gate.main(["--sample", str(path)]), wanted)
                self.assertEqual(json.loads(output.getvalue())["status"], "admitted" if wanted == 0 else "blocked")


if __name__ == "__main__":
    unittest.main()
