"""Pure hostile physical-profile observations, never actual device admission.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import physical_model_contract as p


def sample():
    return {"version": 1, "authorized": True, "physical": True, "model": "SM-S918U1", "api": 36,
            "soc_model": "SM8550", "board_platform": "kalama", "abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
            "page_bytes": 4096, "memory_total_bytes": 11_581_173_760,
            "memory_available_bytes": p.MIN_AVAILABLE_MEMORY_BYTES, "internal_free_bytes": p.REQUIRED_INTERNAL_FREE_BYTES,
            "battery_level": 91, "battery_scale": 100, "usb_powered": True, "temperature_tenths_celsius": 309,
            "thermal_status": 0, "new_app_absent": True, "new_test_absent": True, "prior_pair_unchanged": True}


class PhysicalModelContractTests(unittest.TestCase):
    def assert_invalid(self, value):
        result = p.assess(value)
        self.assertEqual("refused", result["status"])
        self.assertEqual(["invalid_sample"], result["reasons"])
        self.assertIsNone(result["observed"])
        return result

    def test_fixed_model_namespace_and_single_filesystem_cost(self):
        self.assertEqual(2_588_147_712, p.MODEL_BYTES)
        self.assertEqual("181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c", p.MODEL_SHA256)
        self.assertEqual("org.locallore.app.phoneverify", p.APP)
        self.assertEqual(p.APP + ".test", p.TEST)
        self.assertNotEqual("org.locallore.app.modelverify", p.APP)
        self.assertEqual("s918u1_api36_arm64_4k_v1", p.PROFILE)
        self.assertEqual(7_323_779_072, p.REQUIRED_INTERNAL_FREE_BYTES)
        self.assertEqual(2 * p.MODEL_BYTES + 2 * p.GIB, p.REQUIRED_INTERNAL_FREE_BYTES)
        self.assertGreaterEqual(p.SHARED_RESERVE_BYTES, p.GIB + 128 * 1024 ** 2)
        self.assertGreaterEqual(p.SHARED_RESERVE_BYTES, 256 * 1024 ** 2)

    def test_exact_capacity_boundary_and_closed_report(self):
        result = p.assess(sample())
        self.assertEqual({"version", "scope", "profile", "status", "reasons", "required_internal_free_bytes",
                          "required_available_memory_bytes", "observed"}, set(result))
        self.assertEqual("physical_model_admission", result["scope"])
        self.assertEqual("admitted", result["status"]); self.assertEqual([], result["reasons"])
        self.assertEqual(4 * p.GIB, result["required_available_memory_bytes"])
        self.assertEqual({"memory_total_bytes", "memory_available_bytes", "internal_free_bytes", "battery_level",
                          "battery_scale", "temperature_tenths_celsius", "thermal_status"}, set(result["observed"]))

    def test_prior_inventory_memory_is_a_refusal_not_a_pass(self):
        value = sample(); value["memory_available_bytes"] = 3_311_497_216
        value["internal_free_bytes"] = 293_887_492_096
        self.assertEqual(["memory_capacity"], p.assess(value)["reasons"])

    def test_one_byte_short_memory_and_storage_fail_independently(self):
        for key, reason in (("memory_available_bytes", "memory_capacity"), ("internal_free_bytes", "storage_capacity")):
            value = sample(); value[key] -= 1
            with self.subTest(key=key): self.assertEqual([reason], p.assess(value)["reasons"])
        value["memory_available_bytes"] = p.MIN_AVAILABLE_MEMORY_BYTES - 1
        self.assertEqual(["memory_capacity", "storage_capacity"], p.assess(value)["reasons"])

    def test_shared_storage_cannot_be_credited_twice_or_relabelled(self):
        value = sample(); value["internal_free_bytes"] = (p.REQUIRED_INTERNAL_FREE_BYTES + 1) // 2
        self.assertEqual(["storage_capacity"], p.assess(value)["reasons"])
        for extra in ("external_free_bytes", "shared_free_bytes", "cache_free_bytes", "filesystem", "volume_uuid"):
            with self.subTest(extra=extra): self.assert_invalid(dict(value, **{extra: p.REQUIRED_INTERNAL_FREE_BYTES}))

    def test_observed_kernel_ram_band_is_inclusive_and_profile_specific(self):
        for total in (10 * p.GIB, 12 * p.GIB):
            value = sample(); value["memory_total_bytes"] = total
            with self.subTest(total=total): self.assertEqual("admitted", p.assess(value)["status"])
        for total in (10 * p.GIB - 1, 12 * p.GIB + 1):
            value = sample(); value["memory_total_bytes"] = total
            with self.subTest(total=total): self.assertEqual(["profile_mismatch"], p.assess(value)["reasons"])

    def test_hardware_identity_page_size_and_first_abi_are_pinned(self):
        for key, other in (("model", "SM-S918B"), ("api", 35), ("soc_model", "SM8650"),
                           ("board_platform", "other"), ("abis", ["armeabi-v7a", "arm64-v8a"]), ("page_bytes", 16384)):
            with self.subTest(key=key): self.assertEqual(["profile_mismatch"], p.assess(dict(sample(), **{key: other}))["reasons"])
        self.assertEqual("admitted", p.assess(dict(sample(), abis=["arm64-v8a"]))["status"])

    def test_unauthorized_and_nonphysical_never_admit(self):
        self.assertEqual(["unauthorized"], p.assess(dict(sample(), authorized=False))["reasons"])
        self.assertEqual(["not_physical"], p.assess(dict(sample(), physical=False))["reasons"])
        self.assertEqual(["unauthorized", "not_physical"], p.assess(dict(sample(), authorized=False, physical=False))["reasons"])

    def test_new_namespace_absence_and_old_pair_preservation_are_separate(self):
        for app, test in ((False, True), (True, False), (False, False)):
            with self.subTest(app=app, test=test):
                self.assertEqual(["namespace_collision"], p.assess(dict(sample(), new_app_absent=app, new_test_absent=test))["reasons"])
        self.assertEqual(["prior_pair_changed"], p.assess(dict(sample(), prior_pair_unchanged=False))["reasons"])

    def test_battery_power_and_temperature_exact_boundaries(self):
        for changes in ({"battery_level": 20}, {"temperature_tenths_celsius": 0}, {"temperature_tenths_celsius": 399}):
            with self.subTest(changes=changes): self.assertEqual("admitted", p.assess(dict(sample(), **changes))["status"])
        for changes in ({"battery_level": 19}, {"usb_powered": False}, {"temperature_tenths_celsius": -1},
                        {"temperature_tenths_celsius": 400}, {"battery_scale": 99}):
            with self.subTest(changes=changes): self.assertEqual(["power_or_temperature"], p.assess(dict(sample(), **changes))["reasons"])

    def test_nonzero_known_thermal_status_refuses(self):
        for status in range(1, 7):
            with self.subTest(status=status): self.assertEqual(["thermal_capacity"], p.assess(dict(sample(), thermal_status=status))["reasons"])

    def test_valid_multiple_failures_have_declared_order_without_duplicates(self):
        value = dict(sample(), authorized=False, physical=False, model="other", memory_available_bytes=0,
                     internal_free_bytes=0, usb_powered=False, thermal_status=1,
                     new_app_absent=False, new_test_absent=False, prior_pair_unchanged=False)
        self.assertEqual(["unauthorized", "not_physical", "profile_mismatch", "memory_capacity", "storage_capacity",
                          "power_or_temperature", "thermal_capacity", "namespace_collision", "prior_pair_changed"],
                         p.assess(value)["reasons"])

    def test_booleans_cannot_replace_any_numeric_field(self):
        for key in ("version", "api", "page_bytes", "memory_total_bytes", "memory_available_bytes", "internal_free_bytes",
                    "battery_level", "battery_scale", "temperature_tenths_celsius", "thermal_status"):
            for value in (True, False):
                with self.subTest(key=key, value=value): self.assert_invalid(dict(sample(), **{key: value}))

    def test_boolean_observations_reject_truthy_integer_strings_and_unavailable(self):
        for key in ("authorized", "physical", "usb_powered", "new_app_absent", "new_test_absent", "prior_pair_unchanged"):
            for value in (1, 0, "true", None):
                with self.subTest(key=key, value=value): self.assert_invalid(dict(sample(), **{key: value}))

    def test_negative_overflow_and_inconsistent_byte_values_refuse(self):
        for key in ("page_bytes", "memory_total_bytes", "memory_available_bytes", "internal_free_bytes"):
            for value in (-1, 1 << 63, 1.0, "4294967296", None):
                with self.subTest(key=key, value=value): self.assert_invalid(dict(sample(), **{key: value}))
        self.assert_invalid(dict(sample(), memory_available_bytes=sample()["memory_total_bytes"] + 1))
        self.assertEqual("admitted", p.assess(dict(sample(), internal_free_bytes=(1 << 63) - 1))["status"])

    def test_invalid_versions_battery_thermal_and_missing_observations_refuse(self):
        for key, value in (("version", 2), ("api", -1), ("api", 1 << 31), ("battery_level", -1),
                           ("battery_level", 101), ("battery_scale", 0), ("battery_scale", 101),
                           ("battery_scale", 90), ("temperature_tenths_celsius", -1001),
                           ("temperature_tenths_celsius", 2001), ("thermal_status", -1), ("thermal_status", 7)):
            with self.subTest(key=key, value=value): self.assert_invalid(dict(sample(), **{key: value}))
        for key in sample():
            value = sample(); del value[key]
            with self.subTest(missing=key): self.assert_invalid(value)

    def test_unknown_private_fields_and_malformed_strings_never_echo(self):
        canary = "private-serial-device-path-example"
        for key in ("serial", "uid", "path", "model_path", "device_id", "error", "expected_package"):
            with self.subTest(key=key):
                result = self.assert_invalid(dict(sample(), **{key: canary}))
                self.assertNotIn(canary, json.dumps(result)); self.assertNotIn(key, result)
        for key in ("model", "soc_model", "board_platform"):
            for value in (None, "", "x" * 65, "path/secret", "wrong\nvalue", "\u212a"):
                with self.subTest(key=key): self.assert_invalid(dict(sample(), **{key: value}))

    def test_abi_shape_types_duplicates_unknowns_and_order(self):
        for abis in (None, "arm64-v8a", ("arm64-v8a",), [], ["arm64-v8a"] * 2,
                     ["arm64-v8a", True], ["arm64-v8a", "unknown"], ["arm64-v8a"] * 9):
            with self.subTest(abis=abis): self.assert_invalid(dict(sample(), abis=abis))

    def test_malformed_top_level_and_hostile_values_are_closed_without_stringification(self):
        class Secret:
            def __str__(self): raise AssertionError("Do not serialize input")
            def __repr__(self): raise AssertionError("Do not format input")
        class Mapping(dict): pass
        for value in (None, True, [], "secret", 1, Mapping(sample())):
            self.assert_invalid(value)
        self.assert_invalid(dict(sample(), model=Secret()))
        value = sample(); value[object()] = Secret(); self.assert_invalid(value)

    def test_input_is_unchanged_and_reports_have_no_shared_mutable_state(self):
        value = sample(); original = copy.deepcopy(value); first = p.assess(value)
        self.assertEqual(original, value)
        value["memory_available_bytes"] = 0; value["abis"].clear()
        self.assertEqual(p.MIN_AVAILABLE_MEMORY_BYTES, first["observed"]["memory_available_bytes"])
        first["reasons"].append("not-an-observation"); first["observed"]["internal_free_bytes"] = 0
        self.assertEqual([], p.assess(sample())["reasons"])
        self.assertEqual(p.REQUIRED_INTERNAL_FREE_BYTES, p.assess(sample())["observed"]["internal_free_bytes"])

    def test_assessment_performs_no_file_process_or_network_work(self):
        with patch("builtins.open", side_effect=AssertionError("Unexpected IO")), \
             patch.object(Path, "open", side_effect=AssertionError("Unexpected path access")), \
             patch.object(subprocess, "run", side_effect=AssertionError("Unexpected subprocess")), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("Unexpected process")), \
             patch.object(socket, "socket", side_effect=AssertionError("Unexpected network")):
            self.assertEqual("admitted", p.assess(sample())["status"])
            self.assert_invalid(None)
            self.assertEqual(["not_physical"], p.assess(dict(sample(), physical=False))["reasons"])


if __name__ == "__main__":
    unittest.main()
