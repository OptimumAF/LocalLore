"""Original adversarial volume/callback cases; no devices, models or SDK calls.

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
import android_cache_volume as gate

UUID = "ABCD-1234"


def sample(**changes):
    return {"version": 1, "volume_uuid": UUID, "userdata_device": 10, "cache_device": 20,
            "mounted": True, "primary": False, "emulated": False, "writable": True, "backing_verified": True,
            "userdata_free_bytes": gate.GIB + gate.USERDATA_ALLOWANCE, "cache_free_bytes": 2 * gate.GIB,
            "cache_bytes": 0, "userdata_host_volume": "system", "cache_host_volume": "secondary",
            "evidence_host_volume": "secondary", "userdata_host_free_bytes": 4 * gate.GIB + gate.USERDATA_ALLOWANCE,
            "cache_host_free_bytes": 11 * gate.GIB, "evidence_free_bytes": 11 * gate.GIB, **changes}


def clean(**changes):
    return {"clients_cleaned": True, "process_absent": True, "check_passed": True, **changes}


class CacheVolumeTests(unittest.TestCase):
    def test_exact_budgets_accept_independent_cache_not_old_userdata_policy(self):
        self.assertEqual(gate.before_probe(sample(), UUID)["status"], "admitted")
        self.assertLess(sample()["userdata_free_bytes"], 2 * gate.GIB)

    def test_same_host_reserve_max_plus_distinct_growth_not_double_free(self):
        value = sample(userdata_host_volume="secondary", userdata_host_free_bytes=11 * gate.GIB,
                       cache_host_free_bytes=11 * gate.GIB, evidence_free_bytes=11 * gate.GIB)
        self.assertEqual(gate.before_probe(value, UUID)["reasons"], ["host_headroom"])
        for k in ("userdata_host_free_bytes", "cache_host_free_bytes", "evidence_free_bytes"):
            value[k] += gate.USERDATA_ALLOWANCE
        self.assertEqual(gate.before_probe(value, UUID)["status"], "admitted")

    def test_one_byte_below_each_guest_or_distinct_host_budget(self):
        for changes, reason in (({"userdata_free_bytes": gate.GIB + gate.USERDATA_ALLOWANCE - 1}, "userdata_headroom"),
                                ({"cache_free_bytes": 2 * gate.GIB - 1}, "cache_headroom"),
                                ({"userdata_host_free_bytes": 4 * gate.GIB + gate.USERDATA_ALLOWANCE - 1}, "host_headroom"),
                                ({"cache_host_free_bytes": 11 * gate.GIB - 1,
                                  "evidence_free_bytes": 11 * gate.GIB - 1}, "host_headroom")):
            with self.subTest(changes=changes):
                self.assertEqual(gate.before_probe(sample(**changes), UUID)["reasons"], [reason])

    def test_model_copy_adds_full_bytes_to_guest_and_actual_backing_host(self):
        size = 2588147712
        value = sample(cache_free_bytes=2 * gate.GIB + size, cache_host_free_bytes=11 * gate.GIB + size,
                       evidence_free_bytes=11 * gate.GIB + size)
        self.assertEqual(gate.before_probe(value, UUID, size)["status"], "admitted")
        for key in ("cache_free_bytes", "cache_host_free_bytes"):
            short = dict(value)
            short[key] -= 1
            if key == "cache_host_free_bytes":
                short["evidence_free_bytes"] -= 1
            self.assertEqual(gate.before_probe(short, UUID, size)["status"], "blocked")

    def test_invalid_copy_size_never_admits(self):
        for invalid in (True, -1, 1.0, "1", None, gate.MAX_BYTES):
            with self.subTest(value=invalid), self.assertRaises(gate.InvalidSample):
                gate.before_probe(sample(), UUID, invalid)

    def test_strict_shapes_versions_bytes_devices_flags_and_aliases(self):
        values = [None, [], {**sample(), "reserve": 0}, {**sample(), "version": True}, {**sample(), "version": 2}]
        for key in gate.KEYS:
            value = sample()
            value.pop(key)
            values.append(value)
        for key in gate.BYTE_KEYS:
            values.extend(sample(**{key: n}) for n in (True, -1, 1.0, "1", None, gate.MAX_BYTES + 1))
        for key in gate.DEVICE_KEYS:
            values.extend(sample(**{key: n}) for n in (True, 0, -1, 1.0, gate.MAX_BYTES + 1))
        for key in gate.BOOL_KEYS:
            values.extend(sample(**{key: n}) for n in (0, 1, "true", None))
        for key in gate.HOST_KEYS:
            values.extend(sample(**{key: n}) for n in ("", "/private/path", "x" * 65, None))
        for value in values:
            with self.subTest(value=value), self.assertRaises(gate.InvalidSample):
                gate.validate(value)

    def test_expected_uuid_required_bounded_and_exact(self):
        for invalid in (None, "", "/storage/ABCD-1234", "ABCD-1234\n", "A" * 100):
            with self.subTest(value=invalid), self.assertRaises(gate.InvalidSample):
                gate.before_probe(sample(), invalid)
        self.assertEqual(gate.before_probe(sample(), "FFFF-1234")["reasons"], ["volume_mismatch"])
        self.assertEqual(gate.before_probe(sample(volume_uuid="01234567-89ab-cdef-0123-456789abcdef"),
                                         "01234567-89ab-cdef-0123-456789abcdef")["status"], "admitted")

    def test_fuse_device_difference_alone_never_proves_independence(self):
        for changes, reason in (({"mounted": False}, "not_mounted"), ({"primary": True}, "primary_volume"),
                                ({"emulated": True}, "emulated_volume"), ({"writable": False}, "not_writable"),
                                ({"backing_verified": False}, "backing_unverified"),
                                ({"cache_device": 10}, "shared_guest_filesystem")):
            with self.subTest(changes=changes):
                self.assertEqual(gate.before_probe(sample(**changes), UUID)["reasons"], [reason])

    def test_shared_host_samples_must_be_one_actual_measurement(self):
        with self.assertRaises(gate.InvalidSample):
            gate.before_probe(sample(evidence_free_bytes=11 * gate.GIB + 1), UUID)

    def test_separate_evidence_floor_not_borrowed_from_cache_volume(self):
        value = sample(evidence_host_volume="evidence", evidence_free_bytes=10 * gate.GIB,
                       cache_host_free_bytes=5 * gate.GIB)
        self.assertEqual(gate.before_probe(value, UUID)["status"], "admitted")
        value["evidence_free_bytes"] -= 1
        self.assertEqual(gate.before_probe(value, UUID)["reasons"], ["host_headroom"])

    def test_after_exact_consumption_reserves_and_copy_accounting(self):
        size = 2588147712
        before = sample(cache_free_bytes=2 * gate.GIB + size, cache_host_free_bytes=11 * gate.GIB + size,
                        evidence_free_bytes=11 * gate.GIB + size)
        after = sample(userdata_free_bytes=gate.GIB, cache_free_bytes=gate.GIB, cache_bytes=gate.GIB,
                       userdata_host_free_bytes=4 * gate.GIB, cache_host_free_bytes=10 * gate.GIB,
                       evidence_free_bytes=10 * gate.GIB)
        self.assertEqual(gate.after_probe(before, after, UUID, size)["status"], "admitted")

    def test_after_reserve_violations_not_masked_by_other_volumes(self):
        before = sample(userdata_free_bytes=8 * gate.GIB, cache_free_bytes=8 * gate.GIB,
                        userdata_host_free_bytes=20 * gate.GIB, cache_host_free_bytes=20 * gate.GIB,
                        evidence_free_bytes=20 * gate.GIB)
        for changes, reason in (({"userdata_free_bytes": gate.GIB - 1}, "userdata_reserve"),
                                ({"cache_free_bytes": gate.GIB - 1}, "cache_reserve"),
                                ({"userdata_host_free_bytes": 4 * gate.GIB - 1}, "host_reserve"),
                                ({"cache_host_free_bytes": 10 * gate.GIB - 1,
                                  "evidence_free_bytes": 10 * gate.GIB - 1}, "host_reserve")):
            with self.subTest(changes=changes):
                self.assertIn(reason, gate.after_probe(before, {**before, **changes}, UUID)["reasons"])

    def test_cache_free_drop_on_preallocated_host_image_has_own_budget(self):
        before = sample(cache_free_bytes=8 * gate.GIB)
        after = {**before, "cache_free_bytes": 2 * gate.GIB}
        self.assertEqual(gate.after_probe(before, after, UUID)["reasons"], ["cache_consumption_budget"])

    def test_each_net_consumption_and_cache_growth_budget_independent(self):
        before = sample(userdata_free_bytes=3 * gate.GIB, cache_free_bytes=8 * gate.GIB,
                        userdata_host_free_bytes=10 * gate.GIB, cache_host_free_bytes=20 * gate.GIB,
                        evidence_free_bytes=20 * gate.GIB)
        for changes, reason in (({"cache_bytes": gate.GIB + 1}, "cache_growth_budget"),
                                ({"userdata_free_bytes": 3 * gate.GIB - gate.USERDATA_ALLOWANCE - 1}, "userdata_consumption_budget"),
                                ({"userdata_host_free_bytes": 10 * gate.GIB - gate.USERDATA_ALLOWANCE - 1}, "host_consumption_budget")):
            with self.subTest(changes=changes):
                self.assertEqual(gate.after_probe(before, {**before, **changes}, UUID)["reasons"], [reason])

    def test_cache_decrease_blocks_negative_os_delta_is_only_observation(self):
        before = sample(cache_bytes=123)
        self.assertEqual(gate.after_probe(before, sample(cache_bytes=122), UUID)["reasons"], ["cache_decreased"])
        after = {**before, "cache_free_bytes": before["cache_free_bytes"] + 123}
        result = gate.after_probe(before, after, UUID)
        self.assertEqual(result["status"], "admitted")
        self.assertEqual(result["observed_deltas"]["cache_net_consumption_bytes"], -123)

    def test_identity_drift_blocks_before_comparing_free_space(self):
        before = sample()
        for key, value in (("volume_uuid", "FFFF-1234"), ("cache_device", 21), ("userdata_device", 11),
                           ("cache_host_volume", "replacement"), ("mounted", False), ("backing_verified", False)):
            with self.subTest(key=key):
                self.assertEqual(gate.after_probe(before, {**before, key: value}, UUID)["reasons"], ["identity_changed"])

    def test_post_requires_admitted_pre(self):
        with self.assertRaises(gate.InvalidSample):
            gate.after_probe(sample(mounted=False), sample(), UUID)

    def test_blocked_invalid_or_failed_sampler_never_enters_whole_callback(self):
        for sampler in (mock.Mock(return_value=sample(backing_verified=False)), mock.Mock(return_value={}),
                        mock.Mock(side_effect=OSError("private diagnostic"))):
            operation = mock.Mock()
            observed = gate.run_with_admission(sampler, operation, UUID)
            operation.assert_not_called()
            sampler.assert_called_once_with()
            self.assertFalse(observed.dispatched)
            self.assertIsNone(observed.post)
            self.assertNotIn("private diagnostic", repr(observed))

    def test_order_single_dispatch_and_input_copy(self):
        order, value = [], sample()
        def measure():
            order.append("sample")
            return value
        def operation():
            order.append("operation")
            value["cache_bytes"] = 123
            return clean()
        observed = gate.run_with_admission(measure, operation, UUID)
        self.assertEqual(order, ["sample", "operation", "sample"])
        self.assertTrue(observed.metadata()["storage_checks_passed"])
        self.assertEqual(observed.post["observed_deltas"]["cache_growth_bytes"], 123)

    def test_operation_exception_keeps_identity_suppresses_all_post_reads(self):
        original = RuntimeError("private SDK diagnostic")
        measure = mock.Mock(return_value=sample())
        observed = gate.run_with_admission(measure, mock.Mock(side_effect=original), UUID)
        self.assertIs(observed.failure, original)
        measure.assert_called_once_with()
        self.assertEqual(observed.post["reasons"], ["operation_ownership_unknown"])
        self.assertNotIn("private SDK", repr(observed))

    def test_unknown_cleanup_in_all_shapes_never_reads_post(self):
        for result in (None, [], {}, clean(clients_cleaned=1), clean(process_absent=False)):
            measure = mock.Mock(return_value=sample())
            observed = gate.run_with_admission(measure, mock.Mock(return_value=result), UUID)
            self.assertIs(observed.result, result)
            measure.assert_called_once_with()
            self.assertEqual(observed.post["reasons"], ["operation_ownership_unknown"])

    def test_post_failure_never_overwrites_accepted_receipt_or_original_result(self):
        result = clean(receipt={"revision": 1, "accepted": True})
        observed = gate.run_with_admission(mock.Mock(side_effect=[sample(), sample(cache_free_bytes=0)]),
                                           mock.Mock(return_value=result), UUID)
        self.assertIs(observed.result, result)
        self.assertTrue(observed.result["receipt"]["accepted"])
        self.assertFalse(observed.metadata()["storage_checks_passed"])

    def test_post_sample_error_preserved_and_failed_probe_not_promoted(self):
        original = OSError("private mount path")
        result = clean(check_passed=False)
        observed = gate.run_with_admission(mock.Mock(side_effect=[sample(), original]),
                                           mock.Mock(return_value=result), UUID)
        self.assertIs(observed.sample_failure, original)
        self.assertIs(observed.result, result)
        self.assertNotIn("private mount", repr(observed))
        observed = gate.run_with_admission(sample, lambda: result, UUID)
        self.assertTrue(observed.metadata()["storage_checks_passed"])
        self.assertFalse(observed.result["check_passed"])

    def test_metadata_omits_uuid_aliases_paths_and_raw_result(self):
        observed = gate.run_with_admission(sample, lambda: clean(private="private text"), UUID)
        public = json.dumps(observed.metadata())
        for private in (UUID, "secondary", "system", "private text", "cache_device"):
            self.assertNotIn(private, public)

    def test_cli_assessment_only_and_strict_json_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            for raw, expected in ((json.dumps(sample()), 0), (json.dumps(sample(backing_verified=False)), 2),
                                  ('{"version":1,"version":1}', 1), ('{"version":NaN}', 1),
                                  ('x' * 16385, 1), ('[[]]', 1)):
                path.write_text(raw, encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    code = gate.main(["--sample", str(path), "--volume-uuid", UUID])
                self.assertEqual(code, expected)
                self.assertNotIn(UUID, output.getvalue())
                self.assertNotIn(str(path), output.getvalue())


if __name__ == "__main__":
    unittest.main()
