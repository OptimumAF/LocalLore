"""Synthetic command tapes for the guarded model picker setup action controller.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path, PureWindowsPath
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import model_picker_action_binding as binding
from benchmarks import model_picker_action_controller as controller
from benchmarks import owned_model_picker_action as owned
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_owned_target_contract as fixture
from scripts.tests.test_model_picker_action_binding import runner_pass


APP = "org.locallore.app.modelpickerverify"
TEST = APP + ".test"
KIND = "picker_action_scope"
CLASS = "org.locallore.app.ModelPickerActionScopeTest"
METHOD = "retiredChooseAndCheckCannotActOnReplacementStatus"
INSTRUMENT = ["am", "instrument", "-w", "-r", "-e", "class", CLASS + "#" + METHOD,
              TEST + "/androidx.test.runner.AndroidJUnitRunner"]
TARGETS = (
    ("product_apk", APP, "/data/local/tmp/locallore-product-v1.apk", 10001),
    ("test_apk", TEST, "/data/local/tmp/locallore-test-v1.apk", 10002),
)


@dataclass(frozen=True)
class Step:
    argv: list
    label: str
    reply: bytes
    source: dict | None = None
    seconds: int = 15
    limit: int = 131072


def package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def package_path(package):
    return f"/data/app/~~synthetic/{package}-instance/base.apk"


def boot(reply):
    return Step(["getprop", "sys.boot_completed"], "boot", reply)


def installed_steps(pins):
    for role, package, _, uid in TARGETS:
        path = package_path(package)
        listing = f"package:{package} uid:{uid}\n"
        if package == APP:
            listing = f"package:{TEST} uid:{TARGETS[1][3]}\n" + listing
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
            Step(["pm", "install", "-r", "-t", "--user", "0", path],
                 "install", b"Success\n", seconds=120),
        ))
    steps.extend(installed_steps(pins))
    steps.append(Step(INSTRUMENT, KIND, runner_pass(), seconds=90, limit=evidence.MAX_BYTES))
    steps.extend(installed_steps(pins))
    return steps


class PickerJourneyTests(unittest.TestCase):
    def setUp(self):
        self.pins = binding.artifact_bindings()
        self.steps = command_tape(self.pins)

    def run_tape(self, steps=None):
        steps = self.steps if steps is None else steps
        self.calls = []
        self.pauses = 0

        def command(argv, label, *, source=None, seconds=15, limit=131072):
            index = len(self.calls)
            self.assertLess(index, len(steps), "Unplanned or retried command")
            step = steps[index]
            self.assertEqual((argv, label, source, seconds, limit),
                             (step.argv, step.label, step.source, step.seconds, step.limit))
            self.calls.append(step)
            return step.reply

        def pause():
            self.pauses += 1

        return controller._journey(command, pause, self.pins)

    def replace_reply(self, label, occurrence, reply):
        matches = [index for index, step in enumerate(self.steps) if step.label == label]
        index = matches[occurrence - 1]
        steps = list(self.steps)
        steps[index] = replace(steps[index], reply=reply)
        return index, steps

    def assert_refusal(self, label, occurrence, reply, error=env.EnvironmentRefused):
        index, steps = self.replace_reply(label, occurrence, reply)
        with self.assertRaises(error):
            self.run_tape(steps)
        self.assertEqual(self.calls, steps[:index + 1])

    def test_exact_install_and_one_test_with_verified_identity_before_and_after(self):
        steps = [boot(b""), boot(b"0\n"), *self.steps]
        self.assertEqual(self.run_tape(steps), {
            "installed": {
                role: {
                    "package": package,
                    "uid": uid,
                    "path": package_path(package),
                    "sha256": self.pins[role]["sha256"],
                }
                for role, package, _, uid in TARGETS
            },
            "tests": [{
                "kind": KIND,
                "class": CLASS,
                "methods": [METHOD],
                "method_count": 1,
                "stdout_sha256": hashlib.sha256(runner_pass()).hexdigest(),
                "passed": True,
            }],
        })
        self.assertEqual(self.calls, steps)
        self.assertEqual(self.pauses, 2)

    def test_boot_exhaustion_stops_at_sixty_one_reads(self):
        steps = [boot(b"0\n")] * 61
        with self.assertRaisesRegex(env.EnvironmentRefused, "^deadline$"):
            self.run_tape(steps)
        self.assertEqual(self.calls, steps)
        self.assertEqual(self.pauses, 60)

    def test_wrong_target_and_existing_package_refuse_before_staging(self):
        cases = [
            ("boot", 1, b"ready\n"),
            ("property", 1, b"34\n"),
            ("property", 2, b"arm64-v8a\n"),
            ("property", 3, b"0\n"),
            ("user", 1, b"10\n"),
            ("package-absent", 1, f"package:{APP} uid:10001\n".encode()),
            ("package-absent", 2, f"package:{TEST} uid:10002\n".encode()),
        ]
        for label, occurrence, reply in cases:
            with self.subTest(label=label, occurrence=occurrence):
                self.assert_refusal(label, occurrence, reply)
                self.assertFalse(any(step.source is not None for step in self.calls))

    def test_bad_stage_or_install_refuses_before_test(self):
        for label, reply in (
            ("apk-stage", b"unexpected output\n"),
            ("staged-hash", ("0" * 64 + "  " + TARGETS[0][2] + "\n").encode()),
            ("install", b"Failure [synthetic]\n"),
        ):
            with self.subTest(label=label):
                self.assert_refusal(label, 1, reply)
                self.assertFalse(any(step.label == KIND for step in self.calls))
                if label != "install":
                    self.assertFalse(any(step.label == "install" for step in self.calls))

    def test_duplicate_uid_rows_malformed_uid_and_nonbase_or_foreign_path_refuse(self):
        cases = (
            ("package", f"package:{APP} uid:10001\npackage:{APP} uid:10001\n".encode()),
            ("package", f"package:{APP} uid:01\n".encode()),
            ("package", f"package:{APP} uid:9999\n".encode()),
            ("package", f"package:{APP} uid:2147483648\n".encode()),
            ("package-path", f"package:{package_path(TEST)}\n".encode()),
            ("package-path", f"package:{package_path(APP)}\npackage:/data/app/extra/split.apk\n".encode()),
            ("package-hash", ("0" * 64 + "  " + package_path(APP) + "\n").encode()),
        )
        for label, reply in cases:
            with self.subTest(label=label, reply=reply):
                self.assert_refusal(label, 1, reply)
                self.assertFalse(any(step.label == KIND for step in self.calls))

    def test_shared_uid_refuses_even_with_distinct_package_paths_and_correct_hashes(self):
        _, steps = self.replace_reply("package", 2, f"package:{TEST} uid:10001\n".encode())
        with self.assertRaises(env.EnvironmentRefused):
            self.run_tape(steps)
        instrument_index = next(index for index, step in enumerate(steps) if step.label == KIND)
        self.assertEqual(self.calls, steps[:instrument_index])

    def test_uid_drift_after_test_cannot_pass_or_retry_instrumentation(self):
        _, steps = self.replace_reply("package", 3, f"package:{APP} uid:10003\n".encode())
        with self.assertRaises(env.EnvironmentRefused):
            self.run_tape(steps)
        self.assertEqual(self.calls, steps)
        self.assertEqual([step.argv for step in self.calls if step.label == KIND], [INSTRUMENT])

    def test_failed_wrong_or_incomplete_junit_never_retries_or_reaches_postcheck(self):
        good = runner_pass()
        for reply in (
            good.replace(METHOD.encode(), b"anotherMethod"),
            good.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2"),
            good.rsplit(b"INSTRUMENTATION_CODE:", 1)[0],
        ):
            with self.subTest(reply=reply):
                self.assert_refusal(KIND, 1, reply, error=evidence.EvidenceRefused)
                self.assertEqual([step.argv for step in self.calls if step.label == KIND], [INSTRUMENT])


class PickerOwnedContractTests(unittest.TestCase):
    def setUp(self):
        self.value = fixture.admission()
        self.value.update(protocol=owned.PROTOCOL, artifacts=binding.artifact_bindings())
        self.value["guest"]["root"] = str(owned.GUEST_ROOT)
        directory = PureWindowsPath("D:/Synthetic/LocalLore/benchmarks")
        self.value["sources"] = [fixture.pin(directory / name) for name in sorted(owned.SOURCE_NAMES)]

    def test_contract_admits_the_exact_tape_including_large_product_apk(self):
        self.assertEqual(owned.validate_admission(self.value), self.value)
        self.assertGreater(self.value["artifacts"]["product_apk"]["bytes"], 64 * 1024 * 1024)
        for step in command_tape(self.value["artifacts"]):
            with self.subTest(argv=step.argv):
                operation = {"argv": step.argv, "stdin": step.source}
                self.assertEqual(owned.validate_operation(operation, self.value), operation)
        self.assertEqual(owned.instrumentation_kind(INSTRUMENT), KIND)

    def test_substituted_apk_refuses_at_admission_and_staging(self):
        app = self.value["artifacts"]["product_apk"]
        wrong = dict(app, sha256="0" * 64)
        swapped = dict(self.value, artifacts=dict(self.value["artifacts"], product_apk=wrong))
        with self.assertRaises(owned.TargetRefused):
            owned.validate_admission(swapped)
        stage = next(step for step in command_tape(self.value["artifacts"]) if step.label == "apk-stage")
        with self.assertRaises(owned.TargetRefused):
            owned.validate_operation({"argv": stage.argv, "stdin": wrong}, self.value)

    def test_foreign_test_and_model_or_process_operations_refuse(self):
        for argv in (
            [*INSTRUMENT[:-1], "org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner"],
            ["pidof", APP],
            ["am", "force-stop", "--user", "0", TEST],
            ["run-as", APP, "--user", "0", "ls", "files"],
            ["sha256sum", "/data/app/foreign.app-x/base.apk"],
        ):
            with self.subTest(argv=argv), self.assertRaises(owned.TargetRefused):
                owned.validate_operation({"argv": argv, "stdin": None}, self.value)


class PickerReplayTests(unittest.TestCase):
    def setUp(self):
        self.admission = {"artifacts": binding.artifact_bindings()}
        self.steps = command_tape(self.admission["artifacts"])
        self.rows = [
            dict(index=index, effective_deadline_ms=step.seconds * 1000,
                 label=step.label, operation={"argv": step.argv, "stdin": step.source},
                 client_qualified=True, status="completed", returncode=0,
                 stdout=step.reply, stderr=b"")
            for index, step in enumerate(self.steps, 1)
        ]

    def replay(self):
        output = Path("unused-synthetic-output")
        session_pin = {"synthetic": True}
        with patch.object(owned.REPLAY, "require_current_clients", return_value=self.rows) as read, \
                patch.object(owned.REPLAY, "_raw", side_effect=lambda raw, cap: raw):
            result = controller._replay(output, len(self.rows), session_pin, self.admission)
        read.assert_called_once_with(output, len(self.rows), session_pin, self.admission)
        return result

    def test_complete_replay_matches_live_journey(self):
        replies = iter(step.reply for step in self.steps)
        live = controller._journey(lambda *args, **kwargs: next(replies), lambda: None,
                                   self.admission["artifacts"])
        self.assertEqual(self.replay(), live)

    def test_replay_refuses_changed_recipe_and_unqualified_capture(self):
        test_index = next(i for i, row in enumerate(self.rows) if row["label"] == KIND)
        original = self.rows[test_index]
        for changes in (
            {"operation": {"argv": INSTRUMENT[:-1], "stdin": None}},
            {"client_qualified": False},
            {"stderr": b"unexpected output"},
            {"effective_deadline_ms": 90_001},
        ):
            with self.subTest(changes=changes):
                self.rows[test_index] = {**original, **changes}
                with self.assertRaises((env.EnvironmentRefused, owned.TargetRefused)):
                    self.replay()
        self.rows[test_index] = original

    def test_replay_refuses_an_extra_record_after_exact_journey(self):
        self.rows.append(dict(self.rows[-1], index=len(self.rows) + 1))
        with self.assertRaisesRegex(env.EnvironmentRefused, "binding"):
            self.replay()


class PickerControllerOwnershipTests(unittest.TestCase):
    def test_failed_capture_setup_closes_observer_and_records_refusal_once(self):
        for close_known, reason in ((True, "checks_failed"), (False, "resource_uncertain")):
            with self.subTest(close_known=close_known), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                live = Mock()
                live.close.return_value = close_known
                with patch.object(controller, "_admission", return_value={"root": str(root)}), \
                        patch.object(owned, "LiveOwnedModelPickerActionTarget", return_value=live), \
                        patch.object(owned, "OwnedModelPickerActionSdkCapture",
                                     side_effect=owned.ClientRefused("client_guard")) as capture:
                    result = controller.run({"admission": True}, {"running": True})
                    self.assertEqual(result["outcome"], "refused")
                    self.assertEqual(result["reason"], reason)
                    self.assertEqual(result["observer_handles_closed"], close_known)
                    self.assertEqual(result["client_count"], 0)
                    self.assertEqual(env.read_json(root / "controller-v1" / controller.RESULT_FILE), result)
                    live.close.assert_called_once_with()
                    with self.assertRaises(FileExistsError):
                        controller.run({"admission": True}, {"running": True})
                    capture.assert_called_once()
