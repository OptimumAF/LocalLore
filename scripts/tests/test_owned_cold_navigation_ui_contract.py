"""Synthetic cold-navigation command and replay tests. No live target I/O."""

import copy
import hashlib
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import owned_cold_navigation_ui_contract as cold
from benchmarks import owned_target_contract as core
from scripts.tests import test_android_instrumentation_evidence as evidence_fixture
from scripts.tests import test_owned_target_contract as owned_fixture


def admission():
    value = owned_fixture.admission()
    value["protocol"] = cold.PROTOCOL
    value["guest"]["root"] = str(cold.GUEST_ROOT)
    value["artifacts"] = cold.artifact_bindings()
    roster = {PureWindowsPath(row["path"]).name: row for row in value["sources"]}
    source_root = PureWindowsPath("D:/Synthetic/LocalLore/benchmarks")
    value["sources"] = [roster[name] if name in roster else owned_fixture.pin(source_root / name)
                        for name in sorted(cold.SOURCE_NAMES)]
    return value


def pass_capture():
    return (evidence_fixture.bundle(cold.METHOD, 1, 1, cls=cold.CLASS, count=1) +
            evidence_fixture.bundle(cold.METHOD, 1, 0, cls=cold.CLASS, count=1) +
            evidence_fixture.ending(1)).encode()


class ColdNavigationContractTests(unittest.TestCase):
    def test_exact_audited_selector_drives_operation_and_claim(self):
        expected = [
            "am", "instrument", "-w", "-r", "-e", "class",
            "org.locallore.app.ColdNavigationFreshTaskTest#reopensConfirmedChildFromPrivateHintWithoutSavedTaskState",
            "-e", "cold_navigation_v1", "true",
            "org.locallore.app.draftprocessverify.test/androidx.test.runner.AndroidJUnitRunner",
        ]
        self.assertEqual(cold.instrumentation_argv(), expected)
        self.assertEqual(cold.KIND, "cold_navigation")
        operation = {"argv": cold.instrumentation_argv(), "stdin": None}
        admitted = admission()
        validated = cold.PROFILE.validate_operation(operation, admitted)
        self.assertEqual(validated, operation)
        self.assertIsNot(validated["argv"], operation["argv"])
        kind = cold.PROFILE.instrumentation_kind(validated["argv"])
        self.assertEqual(kind, cold.KIND)
        pin = owned_fixture.pin("D:/Synthetic/cold-admission-v1.json")
        caller = owned_fixture.running(admitted)["worker"]
        digest = cold.PROFILE.operation_digest(validated)
        claim = cold.PROFILE.claim_record(pin, caller, kind, digest)
        self.assertEqual(cold.PROFILE.validate_claim(claim, pin, caller, kind, digest), claim)
        with self.assertRaises(core.TargetRefused):
            cold.PROFILE.validate_claim(claim, pin, caller, kind, "0" * 64)

    def test_argument_and_type_substitutions_refuse_in_both_paths(self):
        argv = cold.instrumentation_argv()
        mutations = (
            argv[:7] + argv[-1:],
            argv[:4] + argv[7:10] + argv[4:7] + argv[-1:],
            argv[:9] + ["false"] + argv[-1:],
            argv[:9] + [True] + argv[-1:],
            argv[:8] + ["other_opt_in"] + argv[9:],
            argv[:6] + [cold.CLASS + "#foreignMethod"] + argv[7:],
            argv[:-1] + ["org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner"],
            argv[:-1] + ["-e", "cold_navigation_v1", "true"] + argv[-1:],
            tuple(argv),
        )
        for alternate in mutations:
            with self.subTest(alternate=alternate):
                with self.assertRaises(core.TargetRefused):
                    cold.PROFILE.validate_operation({"argv": alternate, "stdin": None}, admission())
                with self.assertRaises(core.TargetRefused):
                    cold.PROFILE.instrumentation_kind(alternate)
        with self.assertRaises(core.TargetRefused):
            cold.PROFILE.validate_operation({"argv": argv, "stdin": cold.artifact_bindings()["test_apk"]},
                                            admission())

    def test_legacy_profile_still_accepts_only_its_original_shape(self):
        _, class_name, method = core.INSTRUMENTATIONS[0]
        argv = ["am", "instrument", "-w", "-r", "-e", "class", f"{class_name}#{method}",
                f"{core.TEST}/androidx.test.runner.AndroidJUnitRunner"]
        operation = {"argv": argv, "stdin": None}
        self.assertEqual(core.validate_operation(operation, owned_fixture.admission()), operation)
        self.assertEqual(core.instrumentation_kind(argv), core.INSTRUMENTATIONS[0][0])
        opted_in = argv[:-1] + ["-e", "cold_navigation_v1", "true"] + argv[-1:]
        with self.assertRaises(core.TargetRefused):
            core.validate_operation({"argv": opted_in, "stdin": None}, owned_fixture.admission())
        with self.assertRaises(core.TargetRefused):
            core.instrumentation_kind(opted_in)

    def test_artifact_paths_hashes_roles_and_sizes_refuse_before_reading(self):
        for field, replacement in (("path", "D:/Synthetic/rebound.apk"), ("sha256", "0" * 64),
                                   ("bytes", 1), ("bytes", True)):
            pins = cold.artifact_bindings()
            pins["product_apk"][field] = replacement
            self.assertNotEqual(pins, cold.artifact_bindings())
            with self.subTest(field=field, replacement=replacement):
                self.assert_bad_pins(pins)
        pins = cold.artifact_bindings()
        pins["model"] = owned_fixture.pin("D:/Synthetic/unauthorized-model.task")
        self.assert_bad_pins(pins)
        pins = cold.artifact_bindings()
        del pins["build"]
        self.assert_bad_pins(pins)

    def assert_bad_pins(self, pins):
        value = admission()
        value["artifacts"] = pins
        with self.assertRaises(core.TargetRefused):
            cold.PROFILE.validate_admission(value)
        with patch.object(cold.files, "_bound") as read:
            with self.assertRaises(core.TargetRefused):
                cold.verify_artifacts(pins)
        read.assert_not_called()

    def test_unreadable_or_unbound_attestation_stops_before_apk_reads(self):
        pins = cold.artifact_bindings()
        for outcome in ({"side_effect": OSError("synthetic private path")},
                        {"return_value": b'{"operation_authority":true}'}):
            with self.subTest(outcome=outcome), patch.object(cold.files, "_bound", **outcome) as read:
                with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                    cold.verify_artifacts(pins)
                read.assert_called_once_with(pins["build"], cap=pins["build"]["bytes"])

    def test_cold_navigation_disallows_process_stop_model_and_foreign_apk(self):
        allowed = {"argv": ["getprop", "sys.boot_completed"], "stdin": None}
        self.assertEqual(cold.PROFILE.validate_operation(allowed, admission()), allowed)
        product = {"argv": ["dd", "of=/data/local/tmp/locallore-product-v1.apk", "bs=65536"],
                   "stdin": cold.artifact_bindings()["product_apk"]}
        self.assertEqual(cold.PROFILE.validate_operation(product, admission()), product)
        foreign = dict(product, stdin=cold.artifact_bindings()["test_apk"])
        for operation in (foreign, *({"argv": argv, "stdin": None} for argv in (
            ["am", "force-stop", "--user", "0", cold.APP],
            ["am", "force-stop", "--user", "0", cold.TEST],
            ["pidof", cold.APP],
            ["run-as", cold.APP, "--user", "0", "cat", "no_backup/model.litertlm"],
            ["screencap", "-p"],
        ))):
            with self.subTest(operation=operation):
                with self.assertRaises(core.TargetRefused):
                    cold.PROFILE.validate_operation(operation, admission())

    def test_replay_binds_exact_start_and_pass_to_command(self):
        raw = pass_capture()
        operation = {"argv": cold.instrumentation_argv(), "stdin": None}
        value = admission()
        before = copy.deepcopy((operation, value))
        self.assertEqual(cold.replay_instrumentation(operation, value, 0, raw, b""),
                         {"class": cold.CLASS, "methods": [cold.METHOD], "method_count": 1,
                          "stdout_sha256": hashlib.sha256(raw).hexdigest(), "passed": True})
        self.assertEqual((operation, value), before)

    def test_replay_refuses_incomplete_foreign_and_nonpassing_capture(self):
        raw = pass_capture()
        operation = {"argv": cold.instrumentation_argv(), "stdin": None}
        cases = [
            (operation, 1, raw, b""),
            (operation, False, raw, b""),
            (operation, 0, raw, b"unexpected stderr"),
            (operation, 0, raw, ""),
            (operation, 0, raw[:-1], b""),
            (operation, 0, evidence_fixture.ending(1).encode(), b""),
            (operation, 0, raw.replace(cold.CLASS.encode(), b"org.locallore.app.OtherTest"), b""),
            (operation, 0, raw.replace(cold.METHOD.encode(), b"foreignMethod"), b""),
            ({"argv": ["getprop", "sys.boot_completed"], "stdin": None}, 0, raw, b""),
        ]
        for code in (b"-2", b"-3", b"-4"):
            cases.append((operation, 0, raw.replace(b"INSTRUMENTATION_STATUS_CODE: 0",
                                                    b"INSTRUMENTATION_STATUS_CODE: " + code), b""))
        for command, returncode, stdout, stderr in cases:
            with self.subTest(command=command["argv"][:2], returncode=returncode, stderr=stderr):
                with self.assertRaises(core.TargetRefused):
                    cold.replay_instrumentation(command, admission(), returncode, stdout, stderr)
