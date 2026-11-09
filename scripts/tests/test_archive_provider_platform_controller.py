"""Host-only checks for the two SDK26 archive-provider controller methods.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_provider_platform_binding as binding
from benchmarks import archive_provider_platform_controller as controller
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import receipt_avd_environment as env
from scripts.tests.test_archive_provider_platform_binding import runner_bytes
from scripts.tests.test_owned_archive_provider_platform import admission
from scripts.tests.test_saved_library_status_controller import Step, boot, package_path, package_query

TARGETS = (
    ("product_apk", binding.APP, "/data/local/tmp/locallore-product-v1.apk", 10001),
    ("test_apk", binding.TEST, "/data/local/tmp/locallore-test-v1.apk", 10002),
)
IMPORT, EXPORT = binding.INSTRUMENTATIONS
REFUSALS = (env.EnvironmentRefused, owned.TargetRefused)


def installed_steps(pins):
    for role, package, _, uid in TARGETS:
        path = package_path(package)
        listing = f"package:{package} uid:{uid}\n"
        if package == binding.APP:
            listing += f"package:{binding.TEST} uid:10002\n"
        yield Step(package_query(package), "package", listing.encode())
        yield Step(["cmd", "package", "path", "--user", "0", package],
                   "package-path", f"package:{path}\n".encode())
        yield Step(["sha256sum", path], "package-hash",
                   f"{pins[role]['sha256']}  {path}\n".encode())


def command_tape(pins):
    steps = [
        boot(b"1\n"),
        Step(["getprop", "ro.build.version.sdk"], "property", b"35\n"),
        Step(["getprop", "ro.product.cpu.abi"], "property", b"x86_64\n"),
        Step(["getprop", "ro.kernel.qemu"], "property", b"1\n"),
        Step(["am", "get-current-user"], "user", b"0\n"),
        *[Step(package_query(package), "package-absent", b"") for _, package, _, _ in TARGETS],
    ]
    for role, _, path, _ in TARGETS:
        pin = pins[role]
        steps.extend((
            Step(["dd", "of=" + path, "bs=65536"], "apk-stage", b"", source=pin, seconds=120),
            Step(["sha256sum", path], "staged-hash", f"{pin['sha256']}  {path}\n".encode()),
            Step(["pm", "install", "-R", "-t", "--user", "0", path],
                 "install", b"Success\n", seconds=120),
        ))
    steps.extend(installed_steps(pins))
    for kind, klass, method in (IMPORT, EXPORT):
        argv = ["am", "instrument", "-w", "-r", "-e", "class", f"{klass}#{method}",
                f"{binding.TEST}/androidx.test.runner.AndroidJUnitRunner"]
        steps.append(Step(argv, kind, runner_bytes(method), seconds=90, limit=evidence.MAX_BYTES))
        steps.extend(installed_steps(pins))
    return steps


def expected_journey(pins):
    return {
        "installed": {
            role: dict(package=package, uid=uid, path=package_path(package), sha256=pins[role]["sha256"])
            for role, package, _, uid in TARGETS
        },
        "tests": [
            {
                "kind": kind, "class": klass, "methods": [method], "method_count": 1,
                "stdout_sha256": hashlib.sha256(runner_bytes(method)).hexdigest(), "passed": True,
            }
            for kind, klass, method in (IMPORT, EXPORT)
        ],
    }


class ArchiveProviderJourneyTests(unittest.TestCase):
    def setUp(self):
        self.admission = admission()
        self.pins = self.admission["artifacts"]
        self.steps = command_tape(self.pins)

    def run_tape(self, steps):
        self.calls = []
        self.pauses = 0

        def command(argv, label, *, source=None, seconds=15, limit=131072):
            index = len(self.calls)
            self.assertLess(index, len(steps), "Unexpected or retried command")
            step = steps[index]
            self.assertEqual((argv, label, source, seconds, limit),
                             (step.argv, step.label, step.source, step.seconds, step.limit))
            owned.validate_operation({"argv": argv, "stdin": source}, self.admission)
            self.calls.append(step)
            return step.reply

        def pause():
            self.pauses += 1

        return controller._journey(command, pause, self.pins)

    def refuse_reply(self, label, occurrence, reply, error=env.EnvironmentRefused, *, immediate=True):
        index = [i for i, step in enumerate(self.steps) if step.label == label][occurrence - 1]
        steps = list(self.steps)
        steps[index] = replace(steps[index], reply=reply)
        with self.assertRaises(error):
            self.run_tape(steps)
        if immediate:
            self.assertEqual(self.calls, steps[:index + 1])

    def test_exact_tape_rechecks_identity_after_each_method(self):
        self.assertEqual(len(self.steps), 33)
        steps = [boot(b""), boot(b"0\n"), *self.steps]
        self.assertEqual(self.run_tape(steps), expected_journey(self.pins))
        self.assertEqual(self.calls, steps)
        self.assertEqual(self.pauses, 2)

    def test_boot_poll_exhaustion_performs_no_setup(self):
        steps = [boot(b"0\n")] * 61
        with self.assertRaisesRegex(env.EnvironmentRefused, "^deadline$"):
            self.run_tape(steps)
        self.assertEqual(self.calls, steps)
        self.assertEqual(self.pauses, 60)

    def test_foreign_guest_or_existing_packages_refuse_before_any_staging(self):
        for label, occurrence, reply in (
            ("property", 1, b"34\n"),
            ("property", 2, b"arm64-v8a\n"),
            ("property", 3, b"0\n"),
            ("user", 1, b"10\n"),
            ("package-absent", 2, f"package:{binding.TEST} uid:10002\n".encode()),
        ):
            with self.subTest(label=label, occurrence=occurrence):
                self.refuse_reply(label, occurrence, reply)
                self.assertFalse(any(step.argv[0] in ("dd", "pm") for step in self.calls))

    def test_wrong_or_aggregate_import_evidence_stops_before_export(self):
        for reply in (runner_bytes(EXPORT[2]), runner_bytes(IMPORT[2], EXPORT[2])):
            with self.subTest(reply=reply):
                self.refuse_reply(IMPORT[0], 1, reply, evidence.EvidenceRefused)
                self.assertNotIn(EXPORT[0], [step.label for step in self.calls])

    def test_failed_installed_recheck_stops_before_next_test_or_refuses_completion(self):
        for occurrence, attempted in ((3, [IMPORT[0]]), (5, [IMPORT[0], EXPORT[0]])):
            with self.subTest(occurrence=occurrence):
                self.refuse_reply("package-hash", occurrence,
                                  f"{'0' * 64}  {package_path(binding.APP)}\n".encode())
                self.assertEqual([step.label for step in self.calls if step.argv[:2] == ["am", "instrument"]],
                                 attempted)

    def test_uid_drift_after_import_cannot_dispatch_export(self):
        self.refuse_reply("package", 3, f"package:{binding.APP} uid:10003\n".encode(), immediate=False)
        self.assertEqual([step.label for step in self.calls if step.argv[:2] == ["am", "instrument"]],
                         [IMPORT[0]])


class ArchiveProviderReplayTests(unittest.TestCase):
    def setUp(self):
        self.admission = admission()
        self.output = Path(self.admission["root"]) / "controller-v1"
        self.session_pin = self.pin(self.output / owned.SESSION_FILE)
        self.trace = []
        self.rows = []
        self.raw = {}
        for index, step in enumerate(command_tape(self.admission["artifacts"]), 1):
            stem = self.output / "clients" / f"command-{index:04d}"
            stdout = self.pin(stem.with_suffix(".stdout.bin"))
            stderr = self.pin(stem.with_suffix(".stderr.bin"))
            self.raw[stdout["path"]] = step.reply
            self.raw[stderr["path"]] = b"synthetic dd status\n" if step.source is not None else b""
            self.trace.append(self.pin(stem.with_suffix(".json")))
            self.rows.append(dict(index=index, effective_deadline_ms=step.seconds * 1000,
                                  label=step.label, operation={"argv": step.argv, "stdin": step.source},
                                  client_qualified=True, status="completed", returncode=0,
                                  stdout=stdout, stderr=stderr))

    @staticmethod
    def pin(path):
        return {"path": str(path), "bytes": 1, "sha256": "a" * 64}

    def replay(self):
        with (patch.object(owned.REPLAY, "require_current_clients", return_value=self.rows) as read,
              patch.object(owned.REPLAY, "_pin", side_effect=self.pin),
              patch.object(owned.REPLAY, "_raw", side_effect=lambda pin, cap: self.raw[pin["path"]])):
            result = controller._replay(
                self.output, len(self.trace), self.trace, self.session_pin, self.admission)
        read.assert_called_once_with(self.output, len(self.trace), self.session_pin, self.admission)
        return result

    def test_exact_pinned_tape_replays_both_results(self):
        self.assertEqual(self.replay(), expected_journey(self.admission["artifacts"]))

    def test_duplicate_tail_refuses_even_with_an_extra_trace_pin(self):
        self.rows.append(dict(self.rows[-1], index=len(self.rows) + 1))
        self.trace.append(self.pin(self.output / "clients" / f"command-{len(self.rows):04d}.json"))
        with self.assertRaises(REFUSALS):
            self.replay()

    def test_replay_refuses_substituted_pin_swapped_selectors_and_shell_stderr(self):
        i = next(i for i, row in enumerate(self.rows) if row["label"] == IMPORT[0])
        row = self.rows[i]
        original_trace = self.trace[i]
        original_row = deepcopy(row)
        self.trace[i] = dict(original_trace, sha256="b" * 64)
        with self.assertRaises(REFUSALS):
            self.replay()
        self.trace[i] = original_trace
        row["operation"]["argv"] = binding.instrumentation_argv(EXPORT[0])
        with self.assertRaises(REFUSALS):
            self.replay()
        self.rows[i] = original_row
        self.raw[original_row["stderr"]["path"]] = b"unexpected stderr\n"
        with self.assertRaises(REFUSALS):
            self.replay()


class ArchiveProviderControllerOwnershipTests(unittest.TestCase):
    def test_failed_journey_closes_both_handles_and_retains_refusal_once(self):
        for close_known, reason in ((True, "checks_failed"), (False, "resource_uncertain")):
            with self.subTest(close_known=close_known), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                live = Mock()
                live.caller = {"synthetic": True}
                live.close.return_value = close_known
                capture = Mock()
                capture.until = float("inf")
                capture.count = 0
                capture.session_binding = {"synthetic": True}
                with (patch.object(controller, "_admission",
                                   return_value={"root": str(root), "artifacts": binding.artifact_bindings()}),
                      patch.object(owned, "LiveOwnedArchiveProviderPlatformTarget", return_value=live),
                      patch.object(owned, "OwnedArchiveProviderPlatformSdkCapture", return_value=capture),
                      patch.object(controller, "_journey", side_effect=env.EnvironmentRefused("checks_failed"))):
                    result = controller.run({"synthetic": "admission"}, {"synthetic": "running"})
                    self.assertEqual(result["outcome"], "refused")
                    self.assertEqual(result["reason"], reason)
                    self.assertIs(result["observer_handles_closed"], close_known)
                    self.assertEqual(result["client_count"], 0)
                    self.assertEqual(env.read_json(root / "controller-v1" / controller.RESULT_FILE), result)
                capture.close.assert_called_once_with()
                live.close.assert_called_once_with()
