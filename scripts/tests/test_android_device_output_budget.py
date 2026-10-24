"""Encoded recovery wire budgets preserve ordinary device-call limits; no ADB."""
import base64
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_runtime_spike as spike


class DeviceOutputBudgetTests(unittest.TestCase):
    def test_default_call_contract_and_explicit_bounded_forwarding(self):
        device = spike.Device("trusted-adb", "authorized-target")
        arguments = ["shell", "-e", "none", "trusted command"]
        for budget in (None, 1, 262144):
            with self.subTest(budget=budget), patch.object(spike.host, "run_process") as runner:
                result = device.raw(arguments, b"input", deadline=7, max_output=budget)
                expected = {} if budget is None else {"max_output": budget}
                runner.assert_called_once_with(["trusted-adb", "-s", "authorized-target", "shell", "-T", "-e", "none", "trusted command"], b"input", deadline=7, cancel=None, **expected)
                self.assertIs(result, runner.return_value)
                self.assertEqual(arguments, ["shell", "-e", "none", "trusted command"])

    def test_invalid_budget_refused_before_spawn_with_known_cleanup(self):
        device = spike.Device("unused-adb", "unused-target")
        for budget in (True, False, 0, -1, 262145, 1.0, "262144", []):
            with self.subTest(budget=budget), patch.object(spike.host, "run_process") as runner:
                with self.assertRaises(spike.Failure) as error:
                    device.raw(["features"], max_output=budget)
                self.assertEqual(str(error.exception), "invalid_output_budget")
                self.assertTrue(error.exception.command_cleaned)
                runner.assert_not_called()

    def test_real_host_child_large_encoded_payload_needs_explicit_wire_budget(self):
        # Python consumes -s and -c here: this explicitly synthetic device
        # adapter invokes only a trusted host child, never adb or a model.
        device = spike.Device(sys.executable, "-c")
        script = "import base64,sys;sys.stdout.buffer.write(base64.b64encode(bytes(range(256))*512))"
        expected = base64.b64encode(bytes(range(256)) * 512)
        self.assertEqual(len(expected), 174764)
        refused = device.raw([script], deadline=10)
        self.assertEqual(refused.status, "output_limit")
        self.assertTrue(refused.cleanup_complete)
        self.assertLessEqual(len(refused.stdout), 131072)
        admitted = device.raw([script], deadline=10, max_output=262144)
        self.assertEqual((admitted.status, admitted.returncode, admitted.stderr_bytes), ("completed", 0, 0))
        self.assertTrue(admitted.cleanup_complete)
        self.assertEqual(admitted.stdout, expected)


if __name__ == "__main__":
    unittest.main()
