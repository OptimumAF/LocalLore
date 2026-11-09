"""Host-only synthetic tests for the fixed cold-navigation command sequence.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from benchmarks import cold_navigation_ui_controller as controller
from benchmarks import owned_cold_navigation_ui_contract as cold
from benchmarks import owned_target_contract as core
from scripts.tests import test_owned_cold_navigation_ui_contract as fixture
from scripts.tests import test_owned_target_contract as legacy


PACKAGES = (cold.APP, cold.TEST)
ROLES = ("product_apk", "test_apk")
STAGED = ("/data/local/tmp/locallore-product-v1.apk", "/data/local/tmp/locallore-test-v1.apk")
INSTALLED = tuple(f"/data/app/~~fixed/{package}-proof/base.apk" for package in PACKAGES)
BOOT = ["getprop", "sys.boot_completed"]


def package_list(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


class Guest:
    """A guest transport fixture that records attempts before producing a reply."""

    def __init__(self, boot=(b"1\n",)):
        self.boot = iter(boot)
        self.pins = cold.artifact_bindings()
        self.calls = []
        self.counts = Counter()
        self.pauses = 0
        self.replies = {}
        self.result = {"client": {"path": "synthetic"}, "instrumentation": {"method_count": 1}}

    def override(self, argv, occurrence, raw):
        self.replies[tuple(argv), occurrence] = raw

    def command(self, argv, label, *, source=None, seconds=15):
        key = tuple(argv)
        self.counts[key] += 1
        occurrence = self.counts[key]
        self.calls.append((argv, label, source, seconds))
        if (key, occurrence) in self.replies:
            return self.replies[key, occurrence]
        if argv == BOOT:
            return next(self.boot, b"0\n")
        if argv[0] == "getprop":
            return {
                "ro.build.version.sdk": b"35\n",
                "ro.product.cpu.abi": b"x86_64\n",
                "ro.kernel.qemu": b"1\n",
            }[argv[1]]
        if argv == ["am", "get-current-user"]:
            return b"0\n"
        if argv[:4] == ["cmd", "package", "list", "packages"]:
            if occurrence == 1:
                return b""
            index = PACKAGES.index(argv[-1])
            return f"package:{argv[-1]} uid:{10001 + index}\n".encode("ascii")
        if argv[:3] == ["cmd", "package", "path"]:
            path = INSTALLED[PACKAGES.index(argv[-1])]
            return f"package:{path}\n".encode("ascii")
        if argv[0] == "sha256sum":
            path = argv[1]
            index = STAGED.index(path) if path in STAGED else INSTALLED.index(path)
            return f"{self.pins[ROLES[index]]['sha256']}  {path}\n".encode("ascii")
        if argv[0] == "dd":
            return b""
        if argv[:2] == ["pm", "install"]:
            return b"Success\n"
        raise AssertionError(f"Unexpected guest command {argv!r}")

    def instrument(self):
        self.calls.append((cold.instrumentation_argv(), cold.KIND, None, 120))
        return self.result

    def pause(self):
        self.pauses += 1
        if self.pauses > 70:
            raise AssertionError("Unbounded boot polling")

    def run(self):
        return controller._journey(self.command, self.instrument, self.pause, self.pins)

    def argv(self):
        return [row[0] for row in self.calls]


class ColdNavigationControllerTests(unittest.TestCase):
    def test_complete_journey_uses_exact_order_no_replacement_and_one_instrumentation(self):
        guest = Guest((b"", b"0\n", b"1\n"))
        result = guest.run()
        setup = [
            BOOT, BOOT, BOOT,
            ["getprop", "ro.build.version.sdk"],
            ["getprop", "ro.product.cpu.abi"],
            ["getprop", "ro.kernel.qemu"],
            ["am", "get-current-user"],
            *[package_list(package) for package in PACKAGES],
        ]
        installs = [
            argv for path in STAGED for argv in (
                ["dd", f"of={path}", "bs=65536"],
                ["sha256sum", path],
                ["pm", "install", "-R", "-t", "--user", "0", path],
            )
        ]
        installed = [
            argv for package, path in zip(PACKAGES, INSTALLED) for argv in (
                package_list(package),
                ["cmd", "package", "path", "--user", "0", package],
                ["sha256sum", path],
            )
        ]
        self.assertEqual(guest.argv(), setup + installs + installed +
                         [cold.instrumentation_argv()] + installed)
        self.assertEqual(guest.pauses, 2)
        self.assertEqual(result["test"], guest.result)
        self.assertEqual(
            [source for argv, _, source, _ in guest.calls if argv[0] == "dd"],
            [guest.pins[role] for role in ROLES],
        )
        self.assertTrue(all(source is None for argv, _, source, _ in guest.calls if argv[0] != "dd"))

    def test_any_existing_package_refuses_before_the_first_write(self):
        for package in PACKAGES:
            guest = Guest()
            guest.override(package_list(package), 1, f"package:{package} uid:10001\n".encode())
            with self.subTest(package=package), self.assertRaises(core.TargetRefused):
                guest.run()
            self.assertFalse(any(argv[0] in ("dd", "pm") for argv in guest.argv()))
            self.assertNotIn(cold.instrumentation_argv(), guest.argv())

    def test_wrong_guest_properties_refuse_before_staging(self):
        for argv, value in (
            (["getprop", "ro.build.version.sdk"], b"34\n"),
            (["getprop", "ro.product.cpu.abi"], b"arm64-v8a\n"),
            (["getprop", "ro.kernel.qemu"], b"0\n"),
            (["am", "get-current-user"], b"10\n"),
        ):
            guest = Guest()
            guest.override(argv, 1, value)
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                guest.run()
            self.assertFalse(any(command[0] in ("dd", "pm") for command in guest.argv()))

    def test_bad_staged_hash_refuses_install_and_test(self):
        guest = Guest()
        guest.override(["sha256sum", STAGED[0]], 1, f"{'0' * 64}  {STAGED[0]}\n".encode())
        with self.assertRaises(core.TargetRefused):
            guest.run()
        self.assertFalse(any(argv[0] == "pm" for argv in guest.argv()))
        self.assertNotIn(cold.instrumentation_argv(), guest.argv())

    def test_bad_installed_hash_or_shared_uid_refuses_test(self):
        cases = (
            (["sha256sum", INSTALLED[1]], 1, f"{'0' * 64}  {INSTALLED[1]}\n".encode()),
            (package_list(PACKAGES[1]), 2, f"package:{PACKAGES[1]} uid:10001\n".encode()),
        )
        for argv, occurrence, value in cases:
            guest = Guest()
            guest.override(argv, occurrence, value)
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                guest.run()
            self.assertNotIn(cold.instrumentation_argv(), guest.argv())

    def test_identity_change_after_test_refuses_success_without_retry(self):
        guest = Guest()
        guest.override(package_list(PACKAGES[0]), 3, f"package:{PACKAGES[0]} uid:10003\n".encode())
        with self.assertRaises(core.TargetRefused):
            guest.run()
        self.assertEqual(guest.argv().count(cold.instrumentation_argv()), 1)

    def test_foreign_package_path_and_malformed_property_refuse(self):
        guest = Guest()
        command = ["cmd", "package", "path", "--user", "0", PACKAGES[0]]
        guest.override(command, 1, f"package:{INSTALLED[1]}\n".encode())
        with self.assertRaises(core.TargetRefused):
            guest.run()
        self.assertEqual(guest.argv()[-1], command)
        self.assertNotIn(cold.instrumentation_argv(), guest.argv())

        guest = Guest()
        guest.override(["getprop", "ro.build.version.sdk"], 1, b"35\xff\n")
        with self.assertRaises(core.TargetRefused):
            guest.run()
        self.assertFalse(any(argv[0] in ("dd", "pm") for argv in guest.argv()))

    def test_boot_polling_is_finite_and_precedes_all_other_commands(self):
        guest = Guest(boot=())
        with self.assertRaises(core.TargetRefused):
            guest.run()
        self.assertEqual(len(guest.calls), 61)
        self.assertEqual(guest.pauses, 60)
        self.assertEqual(guest.argv(), [BOOT] * len(guest.calls))

    def test_cold_install_refuses_replacement_and_legacy_vector_is_unchanged(self):
        no_replace = {"argv": ["pm", "install", "-R", "-t", "--user", "0", STAGED[0]], "stdin": None}
        replace = {"argv": ["pm", "install", "-r", "-t", "--user", "0", STAGED[0]], "stdin": None}
        implicit = {"argv": ["pm", "install", "-t", "--user", "0", STAGED[0]], "stdin": None}
        self.assertEqual(cold.validate_operation(no_replace, fixture.admission()), no_replace)
        for operation in (replace, implicit):
            with self.assertRaises(core.TargetRefused):
                cold.validate_operation(operation, fixture.admission())
        self.assertEqual(core.validate_operation(replace, legacy.admission()), replace)
        with self.assertRaises(core.TargetRefused):
            core.validate_operation(no_replace, legacy.admission())

    def test_run_retains_failure_and_records_observer_closure_separately(self):
        scenarios = (
            (core.TargetRefused("binding"), True, "checks_failed", None),
            (None, False, "resource_uncertain", {"installed": {}, "test": {"method_count": 1}}),
        )
        for failure, closed, reason, journey in scenarios:
            with self.subTest(reason=reason), TemporaryDirectory(prefix="cold-navigation-") as directory:
                root = Path(directory)
                admission = {"root": str(root), "artifacts": cold.artifact_bindings()}
                admission_pin = {"path": str(root / "admission.json")}
                running_pin = {"path": str(root / "running-v1.json")}
                live = Mock()
                live.close.return_value = closed
                cap = Mock(count=0, clean=True)
                cap.session_binding = {"path": str(root / "controller-v1" / cold.SESSION_FILE)}
                live.caller = {"pid": 12001}
                with patch.object(controller, "_admission", return_value=admission), \
                        patch.object(controller.client, "LiveOwnedColdNavigationUiTarget", return_value=live), \
                        patch.object(controller.client, "OwnedColdNavigationUiSdkCapture", return_value=cap), \
                        patch.object(controller, "_journey", return_value=journey, side_effect=failure), \
                        patch.object(controller, "_replay", return_value=journey) as replay:
                    result = controller.run(admission_pin, running_pin)
                live.close.assert_called_once_with()
                cap.close.assert_called_once_with()
                self.assertEqual(replay.call_count, 0 if failure else 1)
                self.assertEqual(result["outcome"], "refused")
                self.assertEqual(result["reason"], reason)
                self.assertIs(result["observer_handles_closed"], closed)
                self.assertIs(result["feature_acceptance"], False)
                self.assertEqual(result["journey"], journey)
                self.assertEqual(result, controller.env.read_json(root / "controller-v1" / controller.RESULT_FILE))

    def test_unqualified_boot_reply_refuses_before_the_next_command(self):
        for stderr_bytes, times in ((b"unexpected boot diagnostic\n", [0, 0, 1]),
                                    (b"", [0, 0, 121])):
            with self.subTest(stderr=bool(stderr_bytes)), TemporaryDirectory(prefix="cold-navigation-") as directory:
                self.assert_boot_refusal(directory, stderr_bytes, times)

    def assert_boot_refusal(self, directory, stderr_bytes, times):
        root = Path(directory)
        output = root / "controller-v1"
        admission = {"root": str(root), "artifacts": cold.artifact_bindings()}
        live = Mock(caller={"pid": 12001})
        live.close.return_value = True
        cap = Mock(count=0, clean=True, directory=output / "clients")
        cap.session_binding = {"path": str(output / cold.SESSION_FILE)}

        def shell(argv, label, **_):
            self.assertEqual((argv, label), (BOOT, "boot"))
            cap.directory.mkdir()
            cap.count += 1
            stdout = cap.directory / "command-0001.stdout.bin"
            stderr = cap.directory / "command-0001.stderr.bin"
            stdout.write_bytes(b"1\n")
            stderr.write_bytes(stderr_bytes)
            controller.env.create_json(cap.directory / "command-0001.json", {
                "client_qualified": True, "label": label, "operation": {"argv": argv, "stdin": None},
                "stdout": controller.env.binding(stdout), "stderr": controller.env.binding(stderr),
            })
            return b"1\n"

        cap.shell.side_effect = shell
        with patch.object(controller, "_admission", return_value=admission), \
                patch.object(controller.client, "LiveOwnedColdNavigationUiTarget", return_value=live), \
                patch.object(controller.client, "OwnedColdNavigationUiSdkCapture", return_value=cap), \
                patch.object(controller.time, "monotonic", side_effect=times):
            result = controller.run({}, {})
        cap.shell.assert_called_once()
        cap.stream.assert_not_called()
        cap.run_cold_navigation.assert_not_called()
        self.assertEqual(result["outcome"], "refused")
        self.assertEqual(result["client_count"], 1)
        self.assertEqual(result["clients"], [controller.env.binding(cap.directory / "command-0001.json")])
        self.assertTrue(result["observer_handles_closed"])

    def test_replay_refuses_reordered_or_extra_client_records(self):
        guest = Guest()
        expected = guest.run()
        output = Path("D:/Synthetic/controller-v1")
        reader = Mock()
        reader._pin.side_effect = lambda path: {"path": str(path)}
        session = {"scope": "synthetic"}
        reader._json.return_value = session
        admission = {"artifacts": guest.pins}
        rows, trace, payloads = [], [], {}
        replay_guest = Guest()
        for index, (argv, label, source, seconds) in enumerate(guest.calls, 1):
            stem = output / "clients" / f"command-{index:04d}"
            pin = reader._pin(stem.with_suffix(".json"))
            trace.append(pin)
            row = dict(label=label, operation={"argv": argv, "stdin": source},
                       stdout=str(stem.with_suffix(".stdout.bin")), stderr=str(stem.with_suffix(".stderr.bin")))
            rows.append(row)
            if argv == cold.instrumentation_argv():
                guest.result["client"] = pin
            else:
                payloads[row["stdout"]] = replay_guest.command(argv, label, source=source, seconds=seconds)
                payloads[row["stderr"]] = b""
        reader._raw.side_effect = lambda pin, *, cap: payloads[pin]
        reader.require_current_clients.return_value = rows
        with patch.object(controller.client, "_REPLAY", reader), \
                patch.object(controller.contract, "validate_session", return_value=session), \
                patch.object(controller.client, "replay_client_record",
                             return_value=guest.result["instrumentation"]) as instrument:
            self.assertEqual(controller._replay(output, len(rows), trace, {}, admission), expected)
            instrument.assert_called_once_with(guest.result["client"], session, admission)
            swapped = [trace[1], trace[0], *trace[2:]]
            instrument.reset_mock()
            with self.assertRaises(core.TargetRefused):
                controller._replay(output, len(rows), swapped, {}, admission)
            instrument.assert_not_called()
            reader.require_current_clients.return_value = rows + [rows[-1]]
            with self.assertRaises(core.TargetRefused):
                controller._replay(output, len(rows) + 1, trace + [trace[-1]], {}, admission)


if __name__ == "__main__":
    unittest.main()
