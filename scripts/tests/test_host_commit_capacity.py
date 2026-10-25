"""Mocked Windows ABI and pure commit policy; never call the actual host API.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("host_commit_under_test",
    Path(__file__).resolve().parents[2] / "benchmarks/host_commit_capacity.py")
h = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(h)
GIB = 1024 ** 3
PRIVATE = "ORIGINAL_PRIVATE_COMMIT_CANARY"
NAMES = ["cb", "CommitTotal", "CommitLimit", "CommitPeak", "PhysicalTotal", "PhysicalAvailable",
         "SystemCache", "KernelTotal", "KernelPaged", "KernelNonpaged", "PageSize",
         "HandleCount", "ProcessCount", "ThreadCount"]


class FakeFunction:
    def __init__(self, total=5, limit=20, page=4096, status=1, change_cb=False, throw=False):
        self.total, self.limit, self.page, self.status = total, limit, page, status
        self.change_cb, self.throw, self.calls = change_cb, throw, []

    def __call__(self, pointer, size):
        value = ctypes.cast(pointer, ctypes.POINTER(h.PERFORMANCE_INFORMATION)).contents
        self.calls.append((size, value.cb))
        if self.throw: raise OSError(PRIVATE)
        value.CommitTotal, value.CommitLimit, value.PageSize = self.total, self.limit, self.page
        value.PhysicalAvailable = 123; value.HandleCount = 42
        if self.change_cb: value.cb = 0
        return self.status


class HostCommitTest(unittest.TestCase):
    def refuses(self, reason, block):
        with self.assertRaises(h.HostCommitRefused) as caught: block()
        self.assertEqual(reason, caught.exception.reason); self.assertEqual(reason, str(caught.exception))
        self.assertNotIn(PRIVATE, str(caught.exception)); self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(caught.exception.__cause__)

    def api(self, function):
        return patch.object(h.ctypes, "WinDLL", return_value=types.SimpleNamespace(GetPerformanceInfo=function), create=True)

    def test_page_conversion_is_exact_closed_and_does_not_assume_4096(self):
        for page in [1, 512, 4096, 8192, 65536, 1 << 32]:
            self.assertEqual({"version": 1, "commit_total_bytes": 5 * page, "commit_limit_bytes": 20 * page,
                              "available_commit_bytes": 15 * page}, h.snapshot_from_pages(5, 20, page))
        self.assertEqual(0, h.snapshot_from_pages(20, 20, 4096)["available_commit_bytes"])
        self.assertEqual(h.UINT64_MAX, h.snapshot_from_pages(0, h.UINT64_MAX, 1)["available_commit_bytes"])

    def test_pages_strict_types_negative_zero_power_two_and_overflow_refuse(self):
        for values in [(True, 20, 4096), (0, False, 4096), (0, 20, True), (1.0, 20, 4096), (0, "20", 4096),
                       (0, 20, None), (-1, 20, 4096), (0, 0, 4096), (21, 20, 4096), (0, 20, 0),
                       (0, 20, -1), (0, 20, 4095), (0, 20, 12288), (0, h.UINT64_MAX + 1, 1),
                       (h.UINT64_MAX + 1, h.UINT64_MAX, 1), (0, 1, h.UINT64_MAX + 1),
                       (0, h.UINT64_MAX // 4096 + 1, 4096)]:
            self.refuses("commit_invalid", lambda: h.snapshot_from_pages(*values))
        maximum = h.UINT64_MAX // 4096
        self.assertEqual(maximum * 4096, h.snapshot_from_pages(0, maximum, 4096)["commit_limit_bytes"])

    def test_capacity_exact_boundaries_for_both_profiles(self):
        for guest, required in [(2048, 6 * GIB), (8192, 18 * GIB)]:
            snapshot = h.snapshot_from_pages(3 * GIB, 3 * GIB + required, 1)
            result = h.require_capacity(snapshot, guest)
            self.assertEqual(set(snapshot) | {"guest_memory_bytes", "required_commit_bytes", "reserve_bytes"}, set(result))
            self.assertEqual(guest * 1024 ** 2, result["guest_memory_bytes"])
            self.assertEqual(required, result["required_commit_bytes"]); self.assertEqual(2 * GIB, result["reserve_bytes"])
            self.assertEqual(required, result["available_commit_bytes"])
            short = h.snapshot_from_pages(3 * GIB, 3 * GIB + required - 1, 1)
            self.refuses("commit_capacity", lambda: h.require_capacity(short, guest))
            self.assertEqual(required + 1, h.require_capacity(h.snapshot_from_pages(0, required + 1, 1), guest)["available_commit_bytes"])

    def test_policy_is_not_physical_availability_reservation_or_allocation_guarantee(self):
        recorded = h.snapshot_from_pages(58_004_791_296, 72_694_566_912, 1)
        self.refuses("commit_capacity", lambda: h.require_capacity(recorded, 8192))
        self.assertEqual(6 * GIB, h.require_capacity(recorded, 2048)["required_commit_bytes"])
        result = h.require_capacity(h.snapshot_from_pages(0, 18 * GIB, 1), 8192)
        for absent in ["physical_available_bytes", "reservation", "allocated", "guaranteed", "pid", "path", "timestamp"]:
            self.assertNotIn(absent, result)

    def test_snapshot_and_returned_assessment_are_distinct_plain_dicts(self):
        snapshot = h.snapshot_from_pages(0, 18 * GIB, 1); original = dict(snapshot)
        result = h.require_capacity(snapshot, 8192)
        self.assertIs(type(result), dict); self.assertIsNot(snapshot, result); self.assertEqual(original, snapshot)
        result["available_commit_bytes"] = 0; self.assertEqual(original, snapshot)
        snapshot["available_commit_bytes"] = 1
        self.refuses("commit_invalid", lambda: h.require_capacity(snapshot, 8192))

    def test_guest_is_only_exact_integer_2048_or_8192(self):
        snapshot = h.snapshot_from_pages(0, 100 * GIB, 1)
        for guest in [True, False, None, 2048.0, "8192", 0, -1, 1024, 4096, 8193, [], {}]:
            self.refuses("commit_invalid", lambda: h.require_capacity(snapshot, guest))

    def test_snapshot_missing_extra_private_non_dict_and_numeric_type_fields_refuse(self):
        snapshot = h.snapshot_from_pages(0, 20 * GIB, 1)
        for key in snapshot:
            changed = dict(snapshot); del changed[key]
            self.refuses("commit_invalid", lambda: h.require_capacity(changed, 8192))
        for extra in ["pid", "path", "error", "physical_available_bytes", "guest_memory_bytes"]:
            self.refuses("commit_invalid", lambda: h.require_capacity(snapshot | {extra: PRIVATE}, 8192))
        for invalid in [None, True, [], list(snapshot.items())]:
            self.refuses("commit_invalid", lambda: h.require_capacity(invalid, 8192))
        for key in snapshot:
            for value in [True, False, None, 1.0, "1", -1, h.UINT64_MAX + 1]:
                changed = snapshot | {key: value}
                self.refuses("commit_invalid", lambda: h.require_capacity(changed, 8192))
        self.refuses("commit_invalid", lambda: h.require_capacity(snapshot | {"version": 2}, 8192))

    def test_snapshot_correlations_and_zero_available_remain_fail_closed(self):
        for value in [{"version": 1, "commit_total_bytes": 2, "commit_limit_bytes": 1, "available_commit_bytes": 0},
                      {"version": 1, "commit_total_bytes": 0, "commit_limit_bytes": 0, "available_commit_bytes": 0},
                      {"version": 1, "commit_total_bytes": 1, "commit_limit_bytes": 20 * GIB, "available_commit_bytes": 20 * GIB}]:
            self.refuses("commit_invalid", lambda: h.require_capacity(value, 8192))
        self.refuses("commit_capacity", lambda: h.require_capacity(h.snapshot_from_pages(10, 10, 4096), 2048))

    def test_abi_field_order_widths_offsets_and_size(self):
        self.assertEqual(NAMES, [name for name, _ in h.PERFORMANCE_INFORMATION._fields_])
        self.assertEqual(4, ctypes.sizeof(h.DWORD)); self.assertEqual(4, ctypes.sizeof(h.BOOL))
        for index, (_, field_type) in enumerate(h.PERFORMANCE_INFORMATION._fields_):
            self.assertIs(h.SIZE_T if 1 <= index <= 10 else h.DWORD, field_type)
        offsets = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 92, 96] if ctypes.sizeof(h.SIZE_T) == 8 else list(range(0, 56, 4))
        self.assertEqual(offsets, [getattr(h.PERFORMANCE_INFORMATION, name).offset for name in NAMES])
        self.assertEqual(104 if ctypes.sizeof(h.SIZE_T) == 8 else 56, ctypes.sizeof(h.PERFORMANCE_INFORMATION))
        self.assertEqual(ctypes.sizeof(ctypes.c_void_p), ctypes.sizeof(h.SIZE_T))

    def test_mock_call_uses_system32_dll_stdcall_signature_and_exact_cb(self):
        function = FakeFunction()
        with patch.object(h.sys, "platform", "win32"), self.api(function) as loader:
            result = h.read_commit()
        loader.assert_called_once_with("psapi.dll", winmode=0x00000800, use_last_error=True)
        self.assertEqual([ctypes.POINTER(h.PERFORMANCE_INFORMATION), h.DWORD], function.argtypes)
        self.assertIs(h.BOOL, function.restype)
        self.assertEqual([(ctypes.sizeof(h.PERFORMANCE_INFORMATION), ctypes.sizeof(h.PERFORMANCE_INFORMATION))], function.calls)
        self.assertEqual(h.snapshot_from_pages(5, 20, 4096), result)
        self.assertNotIn("HandleCount", result); self.assertNotIn("PhysicalAvailable", result)

    def test_api_nonzero_bool_is_success_but_false_or_malformed_return_is_unavailable(self):
        for status in [1, -1, 7]:
            with patch.object(h.sys, "platform", "win32"), self.api(FakeFunction(status=status)):
                self.assertEqual(15 * 4096, h.read_commit()["available_commit_bytes"])
        for status in [0, None, True, False, 1.0, PRIVATE, 1 << 31, -(1 << 31) - 1]:
            with patch.object(h.sys, "platform", "win32"), self.api(FakeFunction(status=status)):
                self.refuses("commit_unavailable", h.read_commit)

    def test_api_exception_missing_function_and_dll_failure_are_safe_unavailable(self):
        for loader in [patch.object(h.ctypes, "WinDLL", side_effect=OSError(PRIVATE), create=True),
                       patch.object(h.ctypes, "WinDLL", return_value=object(), create=True), self.api(FakeFunction(throw=True))]:
            with patch.object(h.sys, "platform", "win32"), loader:
                self.refuses("commit_unavailable", h.read_commit)
        with patch.object(h.sys, "platform", "linux"), self.api(FakeFunction()) as loader:
            self.refuses("commit_unavailable", h.read_commit); loader.assert_not_called()

    def test_api_corrupt_cb_pages_or_page_size_are_invalid_not_available_capacity(self):
        functions = [FakeFunction(change_cb=True), FakeFunction(total=21), FakeFunction(limit=0),
                     FakeFunction(page=0), FakeFunction(page=4095)]
        if ctypes.sizeof(h.SIZE_T) == 8: functions.append(FakeFunction(limit=h.UINT64_MAX, page=4096))
        for function in functions:
            with patch.object(h.sys, "platform", "win32"), self.api(function):
                self.refuses("commit_invalid", h.read_commit)

    def test_refusal_constructor_and_module_import_do_not_echo_or_call_apis(self):
        for reason in ["commit_unavailable", "commit_invalid", "commit_capacity", PRIVATE, True, None, {}]:
            value = h.HostCommitRefused(reason)
            self.assertIn(value.reason, ("commit_unavailable", "commit_invalid", "commit_capacity"))
            self.assertEqual(value.reason, str(value)); self.assertNotIn(PRIVATE, str(value))
        code = SPEC.loader.get_code(SPEC.name); probe = types.ModuleType("host_commit_inert_probe")
        with patch("builtins.open", side_effect=AssertionError(PRIVATE)), patch.object(Path, "open", side_effect=AssertionError(PRIVATE)), \
             patch.object(ctypes, "WinDLL", side_effect=AssertionError("OS API called on import"), create=True) as loader:
            exec(code, probe.__dict__)
        loader.assert_not_called()
        for name in ["main", "Path", "open", "os", "subprocess"]: self.assertFalse(hasattr(probe, name))


if __name__ == "__main__":
    unittest.main()
