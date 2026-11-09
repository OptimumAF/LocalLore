"""Synthetic checks for the fixed story-deletion owner contract.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import android_process_verification_v4 as verification
from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import cross_owner_deletion_ui_capture as capture
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from scripts.tests import test_owned_target_contract as fixture
from scripts.tests.test_cross_owner_deletion_ui_replay import (
    APP, CLASS, INSTRUMENT, KIND, TARGETS, TEST, command_tape,
)


SOURCE_ROOT = PureWindowsPath("D:/Synthetic/LocalLore")
AUDIT_NAMES = ("audit_apk.py", "audit_physical_model_apk.py")
GUEST_ROOT = PureWindowsPath(
    "D:/Dev/Experiments/LocalLore/2026-11-09-cross-owner-deletion-owned-guest-v1/avd-v1"
)


class CrossOwnerDeletionUiProfileTests(unittest.TestCase):
    def setUp(self):
        self.admission = fixture.admission()
        self.pins = binding.artifact_bindings()
        self.admission.update(protocol=owned.PROTOCOL, artifacts=self.pins)
        self.admission["guest"]["root"] = str(GUEST_ROOT)
        paths = [*(SOURCE_ROOT / "benchmarks" / name for name in owned.SOURCE_NAMES),
                 *(SOURCE_ROOT / "scripts" / name for name in AUDIT_NAMES)]
        self.admission["sources"] = sorted(map(fixture.pin, paths), key=lambda pin: pin["path"])

    def assert_operation_refused(self, argv, stdin=None):
        with self.assertRaises(core.TargetRefused):
            owned.validate_operation({"argv": argv, "stdin": stdin}, self.admission)

    def test_fixed_profile_accepts_the_exact_replay_operations(self):
        self.assertEqual((owned.APP, owned.TEST), (APP, TEST))
        self.assertIs(owned.MODEL_MATERIAL, False)
        self.assertEqual(owned.INSTRUMENTATIONS, binding.INSTRUMENTATIONS)
        self.assertEqual(owned.ARTIFACT_KEYS, frozenset(self.pins))
        self.assertEqual(owned.CLAIM_KINDS, (KIND,))
        self.assertEqual(owned.GUEST_ROOT, GUEST_ROOT)
        self.assertEqual((owned.CLIENT_VERSION, owned.SESSION_FILE), (24, "sdk-session-v24.json"))
        self.assertEqual(owned.validate_admission(self.admission), self.admission)

        tape = command_tape(self.pins)
        self.assertEqual(len(tape), 26)
        for row in tape:
            with self.subTest(argv=row["argv"]):
                operation = {key: row[key] for key in ("argv", "stdin")}
                self.assertEqual(owned.validate_operation(operation, self.admission), operation)
        self.assertEqual(owned.instrumentation_kind(INSTRUMENT), KIND)

    def test_source_roster_requires_exact_sibling_audit_files(self):
        sources = self.admission["sources"]
        first_audit = str(SOURCE_ROOT / "scripts" / AUDIT_NAMES[0])
        without_audit = [pin for pin in sources if pin["path"] != first_audit]
        variants = (
            without_audit,
            [*without_audit, fixture.pin(SOURCE_ROOT / "benchmarks" / AUDIT_NAMES[0])],
            [*without_audit, fixture.pin(SOURCE_ROOT.parent / "Foreign/scripts" / AUDIT_NAMES[0])],
            [*sources, fixture.pin(SOURCE_ROOT / "scripts/extra.py")],
            [*sources, fixture.pin(SOURCE_ROOT.parent / "Foreign/benchmarks/__init__.py")],
        )
        for variant in variants:
            with self.subTest(source_paths=[pin["path"] for pin in variant]):
                admission = dict(self.admission, sources=sorted(variant, key=lambda pin: pin["path"]))
                with self.assertRaisesRegex(core.TargetRefused, "^source$"):
                    owned.validate_admission(admission)

    def test_refuses_a_different_guest_and_substituted_artifacts(self):
        app, test = self.pins["product_apk"], self.pins["test_apk"]
        variants = (
            dict(self.admission, guest=dict(self.admission["guest"], root="D:/Synthetic/foreign-guest")),
            dict(self.admission, artifacts={**self.pins, "product_apk": test, "test_apk": app}),
            dict(self.admission, artifacts={**self.pins, "model": fixture.pin("D:/Synthetic/model.task")}),
            dict(self.admission, artifacts={**self.pins, "product_apk": dict(app, sha256="0" * 64)}),
        )
        for admission in variants:
            with self.subTest(admission=admission), self.assertRaises(core.TargetRefused):
                owned.validate_admission(admission)
        for role, _, path, _ in TARGETS:
            other = test if role == "product_apk" else app
            with self.subTest(role=role):
                self.assert_operation_refused(["dd", "of=" + path, "bs=65536"], stdin=other)

    def test_registration_facade_treats_the_owned_offline_reply_as_waiting(self):
        raw = b"emulator-5592          offline transport_id:1\n"
        self.assertIsNone(mechanisms._waiting_devices(raw, _contract=owned))
        self.assertIsNone(mechanisms._waiting_devices(b"", _contract=owned))
        self.assertEqual(mechanisms._waiting_devices(b"emulator-5592 device transport_id:1\n",
                                                      _contract=owned), 1)

    def test_registration_facade_refuses_a_foreign_or_malformed_transport(self):
        for raw in (b"emulator-5594 offline transport_id:1\n",
                    b"emulator-5592 device\n",
                    b"emulator-5592 offline transport_id:0\n",
                    b"emulator-5592 offline transport_id:1\nemulator-5594 device transport_id:2\n"):
            with self.subTest(raw=raw), self.assertRaises(core.TargetRefused):
                mechanisms._waiting_devices(raw, _contract=owned)

    def test_install_requires_the_exact_no_replacement_recipe(self):
        for _, _, path, _ in TARGETS:
            for options in ([], ["-r"], ["-R", "-r"]):
                with self.subTest(path=path, options=options):
                    self.assert_operation_refused(["pm", "install", *options, "-t", "--user", "0", path])

    def test_refuses_foreign_packages_and_other_runner_selectors(self):
        for argv in (
            ["cmd", "package", "list", "packages", "-U", "--user", "0", "org.locallore.app"],
            ["cmd", "package", "path", "--user", "0", APP + ".foreign"],
            ["sha256sum", "/data/app/foreign.app-instance/base.apk"],
            [*INSTRUMENT[:-1], "org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner"],
            [*INSTRUMENT[:6], CLASS, INSTRUMENT[-1]],
            [*INSTRUMENT[:6], CLASS + "#otherMethod", INSTRUMENT[-1]],
        ):
            with self.subTest(argv=argv):
                self.assert_operation_refused(argv)

    def test_refuses_model_process_and_shell_control_operations(self):
        for argv in (
            ["pidof", APP],
            ["am", "force-stop", "--user", "0", TEST],
            ["run-as", APP, "--user", "0", "ls", "files"],
            ["df", "-k", "/data"],
            ["screencap", "-p"],
            ["dd", "of=/data/local/tmp/locallore-author-process-probe-v1", "bs=65536"],
            ["rm", "-f", TARGETS[0][2]],
        ):
            with self.subTest(argv=argv):
                self.assert_operation_refused(argv)

    def test_shared_verifier_rejects_invalid_capture_count_before_reading(self):
        reader = verification._Verifier(owned)
        with patch.object(reader, "_json") as read:
            for count in (0, True, 10_001):
                with self.subTest(count=count), self.assertRaises(core.TargetRefused):
                    reader.require_current_clients(self.admission["root"], count, None, self.admission)
        read.assert_not_called()

    def test_capture_facade_always_uses_the_fixed_contract(self):
        args = tuple(object() for _ in range(4))
        result = object()
        with patch.object(capture, "verify_capture", return_value=result) as verify:
            self.assertIs(owned.verify_capture(*args), result)
        verify.assert_called_once_with(owned, *args)
