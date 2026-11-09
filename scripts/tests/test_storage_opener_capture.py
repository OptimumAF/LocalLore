"""Host-only regressions for fixed storage opener runner evidence.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from io import BytesIO
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import owned_target_contract as core
from benchmarks import storage_opener_capture as capture
from scripts.tests.test_android_instrumentation_evidence import bundle, ending


KINDS = ("archive_opener", "deletion_opener")
CLASSES = (
    "org.locallore.app.ui.ArchiveOpenScopeScreenTest",
    "org.locallore.app.ui.DeletionOpenScopeScreenTest",
)
METHODS = (
    "retainedArchiveOpenerCannotBorrowAReplacementRenderedFrame",
    "retainedDeletionOpenersCannotBorrowTheReplacementStoryOrTimeline",
)
SELECTORS = [f"{klass}#{method}" for klass, method in zip(CLASSES, METHODS)]
RUNNER = "org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner"


def argv(index):
    return ["am", "instrument", "-w", "-r", "-e", "class", SELECTORS[index], RUNNER]


def stdout(index, *, completion=0):
    return (bundle(METHODS[index], 1, 1, cls=CLASSES[index], count=1)
            + bundle(METHODS[index], 1, completion, cls=CLASSES[index], count=1)
            + ending(1)).encode()


def expected_result(index, raw):
    return {
        "kind": KINDS[index],
        "class": CLASSES[index],
        "methods": [METHODS[index]],
        "method_count": 1,
        "stdout_sha256": hashlib.sha256(raw).hexdigest(),
        "passed": True,
    }


class StorageOpenerCaptureTests(unittest.TestCase):
    def setUp(self):
        self.pins = capture.artifact_bindings()
        self.verify = self.enterContext(
            patch.object(capture, "verify_artifacts", return_value=SELECTORS),
        )

    def test_exact_selectors_use_only_the_paired_archive_runner(self):
        for index, kind in enumerate(KINDS):
            self.assertEqual(capture.instrumentation_argv(kind), argv(index))
        for kind in ("archive", "deletion", "archive_opener ", "ARCHIVE_OPENER", "", None, True):
            with self.subTest(kind=kind), self.assertRaises(core.TargetRefused):
                capture.instrumentation_argv(kind)

    def test_fresh_artifact_pin_map_has_exact_roles_and_no_nested_aliases(self):
        fresh = capture.artifact_bindings()
        self.assertEqual(fresh, self.pins)
        self.assertEqual(set(fresh), {"build", "product_apk", "test_apk"})
        for pin in fresh.values():
            self.assertEqual(set(pin), {"path", "bytes", "sha256"})
            self.assertGreater(pin["bytes"], 0)
            self.assertRegex(pin["sha256"], "^[0-9a-f]{64}$")
        fresh["build"]["sha256"] = "0" * 64
        fresh.pop("test_apk")
        self.assertEqual(capture.artifact_bindings(), self.pins)

    def test_artifact_refusal_never_reaches_command(self):
        command = Mock(side_effect=AssertionError("unexpected command"))
        self.verify.side_effect = core.TargetRefused("binding")
        with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
            capture.capture_tests(self.pins, command)
        self.verify.assert_called_once_with(self.pins)
        command.assert_not_called()

    def test_validated_commands_run_once_in_order_after_artifact_verification(self):
        raw = [stdout(0), stdout(1).replace(b"\n", b"\r\n")]
        calls = []

        def verified(pins):
            self.assertEqual(pins, self.pins)
            calls.append("verified")
            return SELECTORS

        def dispatch(command, kind, *, seconds, limit):
            index = KINDS.index(kind)
            self.assertEqual(calls, ["verified", *KINDS[:index]])
            self.assertEqual((command, kind, seconds, limit),
                             (argv(index), KINDS[index], 90, evidence.MAX_BYTES))
            calls.append(kind)
            return raw[index]

        self.verify.side_effect = verified
        self.assertEqual(capture.capture_tests(self.pins, dispatch),
                         [expected_result(index, raw[index]) for index in range(2)])
        self.assertEqual(calls, ["verified", *KINDS])
        self.verify.assert_called_once_with(self.pins)

    def test_invalid_first_capture_never_dispatches_the_second(self):
        bad_captures = (
            stdout(1),
            stdout(0)[:-1],
            stdout(0, completion=-2),
            stdout(0) + ending(1).encode(),
            bytearray(stdout(0)),
            b"x" * (evidence.MAX_BYTES + 1),
        )
        for raw in bad_captures:
            with self.subTest(size=len(raw), raw_type=type(raw).__name__):
                command = Mock(return_value=raw)
                with self.assertRaisesRegex(evidence.EvidenceRefused, "^instrumentation_refused$"):
                    capture.capture_tests(self.pins, command)
                command.assert_called_once_with(argv(0), KINDS[0], seconds=90, limit=evidence.MAX_BYTES)

    def test_second_capture_must_match_deletion_and_cannot_return_a_partial_result(self):
        command = Mock(side_effect=[stdout(0), stdout(0)])
        with self.assertRaisesRegex(evidence.EvidenceRefused, "^instrumentation_refused$"):
            capture.capture_tests(self.pins, command)
        self.assertEqual(command.call_args_list, [
            call(argv(index), KINDS[index], seconds=90, limit=evidence.MAX_BYTES)
            for index in range(2)
        ])

class StorageOpenerArtifactTests(unittest.TestCase):
    def setUp(self):
        self.pins = capture.artifact_bindings()
        self.product, self.test = b"synthetic product bytes", b"synthetic test bytes"
        self.report = dict(version=1, scope="storage-opener-apk-pair-v1",
                           app_source="0ea7a68896242a7e1c90dfe280a9184af59306fa",
                           audit_source="968db00448a3a821d215bacd04123bd6d5c817cf",
                           android_executed=False, apk_audit={"status": "passed"},
                           pair_audit=dict(status="passed", package="org.locallore.app.archiveverify",
                                           test_package="org.locallore.app.archiveverify.test",
                                           runner="androidx.test.runner.AndroidJUnitRunner",
                                           selectors=SELECTORS))
        for role, name in (("product_apk", "app"), ("test_apk", "test")):
            self.report["pair_audit"][name] = {key: self.pins[role][key] for key in ("bytes", "sha256")}
        self.read_json = self.enterContext(patch.object(capture.files, "_json", return_value=self.report))
        self.read_bytes = self.enterContext(
            patch.object(capture.files, "_bound", side_effect=[self.product, self.test]),
        )
        self.dex = self.enterContext(patch.object(capture, "dex_classes", side_effect=self.classes))

    def classes(self, stream, *, with_code=False):
        self.assertIsInstance(stream, BytesIO)
        raw = stream.read()
        if raw == self.product:
            return {}
        self.assertEqual(raw, self.test)
        self.assertIs(with_code, True)
        return {("L" + klass.replace(".", "/") + ";").encode("ascii"):
                (17, [(method.encode("ascii"), (b"V", 0), 17, True, 10)])
                for klass, method in zip(CLASSES, METHODS)}

    def test_pins_join_exact_frozen_audit_and_already_bound_dex_bytes(self):
        self.assertEqual(capture.verify_artifacts(self.pins), SELECTORS)
        self.read_json.assert_called_once_with(self.pins["build"])
        self.assertEqual(self.read_bytes.call_args_list, [
            call(self.pins[role], cap=self.pins[role]["bytes"]) for role in ("product_apk", "test_apk")
        ])
        self.assertEqual(self.dex.call_count, 2)

    def test_foreign_pin_refuses_before_opening_report_or_apks(self):
        supplied = copy.deepcopy(self.pins)
        supplied["test_apk"]["path"] = supplied["product_apk"]["path"]
        with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
            capture.verify_artifacts(supplied)
        self.read_json.assert_not_called()
        self.read_bytes.assert_not_called()
        self.dex.assert_not_called()

    def test_inconsistent_audit_never_dispatches_a_command(self):
        candidates = (
            dict(self.report, android_executed=True),
            dict(self.report, app_source="0" * 40),
            dict(self.report, pair_audit=dict(self.report["pair_audit"], runner="ForeignRunner")),
            dict(self.report, pair_audit=dict(self.report["pair_audit"],
                                              test={"bytes": 1, "sha256": "0" * 64})),
        )
        for report in candidates:
            with self.subTest(report=report):
                self.read_json.return_value = report
                command = Mock(side_effect=AssertionError("unexpected command"))
                with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                    capture.capture_tests(self.pins, command)
                command.assert_not_called()
        self.read_bytes.assert_not_called()
        self.dex.assert_not_called()

    def test_pair_audit_selector_order_must_match_compiled_selectors(self):
        self.report["pair_audit"]["selectors"] = SELECTORS[::-1]
        command = Mock(side_effect=AssertionError("unexpected command"))
        with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
            capture.capture_tests(self.pins, command)
        self.assertEqual(self.dex.call_count, 2)
        command.assert_not_called()
