"""Synthetic integration checks for the owned story-deletion capture bridge.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import cross_owner_deletion_ui_capture as capture
from benchmarks import cross_owner_deletion_ui_replay as journey
from benchmarks import owned_target_contract as core
from scripts.tests.test_cross_owner_deletion_ui_replay import command_tape


KIND = "cross_owner_deletion_recovery"
PACKAGE_RECORDS = (
    ("package", 15_000), ("package-path", 15_000), ("package-hash", 15_000),
)
RECORDS = (
    ("boot", 15_000), *(("property", 15_000),) * 3, ("user", 15_000),
    *(("package-absent", 15_000),) * 2,
    *(("apk-stage", 120_000), ("staged-hash", 15_000), ("install", 120_000)) * 2,
    *PACKAGE_RECORDS * 2, (KIND, 90_000), *PACKAGE_RECORDS * 2,
)


def pin(path, raw=b""):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class CrossOwnerDeletionUiCaptureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("D:/Synthetic/story-deletion")
        self.output = self.root / "controller-v1"
        self.caller = dict(pid=1234, started_epoch=123.0)
        self.pins = binding.artifact_bindings()
        self.admission = dict(root=str(self.root), artifacts=self.pins)
        self.running = dict(transport_id=1)
        self.admission_pin = pin(self.root / "admission-v1.json", b"admission")
        self.running_pin = pin(self.root / "running-v1.json", b"running")
        self.session_pin = pin(self.output / "sdk-session-v24.json", b"session")
        self.session = dict(admission=self.admission_pin, running=self.running_pin,
                            descriptor=self.running, caller=self.caller, seconds=1200,
                            root=str(self.output))

        self.contract = SimpleNamespace(
            APP=binding.APP, TEST=binding.TEST, MODEL_MATERIAL=False,
            INSTRUMENTATIONS=binding.INSTRUMENTATIONS,
            ARTIFACT_KEYS=frozenset(self.pins), CLAIM_KINDS=(KIND,),
            SESSION_FILE="sdk-session-v24.json",
            validate_admission=Mock(side_effect=lambda value: copy.deepcopy(value)),
            validate_running=Mock(side_effect=lambda value, *_: copy.deepcopy(value)),
            validate_session=Mock(side_effect=lambda value, *_: copy.deepcopy(value)),
            revalidate_inputs=Mock(),
        )
        self.tape = command_tape(self.pins)
        self.rows = []
        self.raw = {}
        for index, (step, (label, deadline)) in enumerate(zip(self.tape, RECORDS, strict=True), 1):
            row = dict(index=index, label=label, effective_deadline_ms=deadline,
                       client_qualified=True, status="completed", returncode=step["returncode"],
                       operation=dict(argv=step["argv"], stdin=step["stdin"]))
            for channel in ("stdout", "stderr"):
                path = self.output / "clients" / f"command-{index:04d}.{channel}.bin"
                row[channel] = pin(path, step[channel])
                self.raw[str(path)] = step[channel]
            self.rows.append(row)

        self.reader = Mock(spec=capture.shared._Verifier)
        self.reader._json.return_value = self.admission
        self.reader._at.side_effect = lambda bound, _: {
            self.running_pin["path"]: self.running,
            self.session_pin["path"]: self.session,
        }[bound["path"]]
        self.reader._raw.side_effect = lambda bound, **_: self.raw[bound["path"]]
        self.reader.require_current_clients.return_value = self.rows
        patch_reader = patch.object(capture.shared, "_Verifier", return_value=self.reader)
        patch_artifacts = patch.object(binding, "verify_artifacts")
        self.make_reader = patch_reader.start()
        self.verify_artifacts = patch_artifacts.start()
        self.addCleanup(patch_reader.stop)
        self.addCleanup(patch_artifacts.stop)

    def verify(self):
        return capture.verify_capture(self.contract, self.admission_pin, self.running_pin,
                                      self.session_pin, self.caller)

    def test_exact_qualified_capture_replays_the_existing_tape(self):
        def qualified(root, count, session, admission):
            self.contract.revalidate_inputs.assert_called_once_with(self.admission)
            self.verify_artifacts.assert_called_once_with(self.pins)
            return self.rows

        self.reader.require_current_clients.side_effect = qualified
        result = self.verify()
        self.assertEqual(result, journey.replay(self.tape, self.pins))
        self.assertIs(result["runtime_verified"], False)
        self.assertIs(result["execution_authorized"], False)
        self.make_reader.assert_called_once_with(self.contract)
        self.reader._json.assert_called_once_with(self.admission_pin)
        self.reader._at.assert_has_calls([
            call(self.running_pin, self.root / "running-v1.json"),
            call(self.session_pin, self.output / "sdk-session-v24.json"),
        ])
        self.contract.validate_running.assert_called_once_with(
            self.running, self.admission, self.admission_pin)
        self.contract.validate_session.assert_called_once_with(self.session, self.admission)
        self.reader.require_current_clients.assert_called_once_with(
            self.output, 26, self.session_pin, self.admission)
        expected_reads = [
            call(row[channel], cap=evidence.MAX_BYTES if row["label"] == KIND else 131_072)
            for row in self.rows for channel in ("stdout", "stderr")
        ]
        self.assertEqual(self.reader._raw.call_args_list, expected_reads)

    def test_wrong_profile_never_constructs_the_reader(self):
        for attr, replacement in (
            ("APP", "org.locallore.app"), ("TEST", binding.APP),
            ("MODEL_MATERIAL", 0), ("INSTRUMENTATIONS", ()),
            ("ARTIFACT_KEYS", frozenset((*self.pins, "model"))),
            ("CLAIM_KINDS", (KIND, "restart")),
            ("SESSION_FILE", "../sdk-session-v24.json"),
            ("SESSION_FILE", "D:/Synthetic/sdk-session-v24.json"),
        ):
            with self.subTest(attr=attr, replacement=replacement), patch.object(
                    self.contract, attr, replacement), self.assertRaises(core.TargetRefused):
                self.verify()
        self.make_reader.assert_not_called()

    def test_session_must_bind_the_exact_admission_running_descriptor_and_caller(self):
        for attr, replacement in (
            ("admission", {**self.admission_pin, "sha256": "0" * 64}),
            ("running", {**self.running_pin, "bytes": 0}),
            ("descriptor", {"transport_id": 2}),
            ("caller", {**self.caller, "pid": 5678}),
            ("seconds", 1200.0), ("seconds", 1700),
        ):
            with self.subTest(attr=attr, replacement=replacement), patch.dict(
                    self.session, {attr: replacement}), self.assertRaises(core.TargetRefused):
                self.verify()
        self.reader.require_current_clients.assert_not_called()
        self.reader._raw.assert_not_called()

    def test_unverified_sources_or_artifacts_stop_before_capture(self):
        self.contract.revalidate_inputs.side_effect = core.TargetRefused("source")
        with self.assertRaises(core.TargetRefused):
            self.verify()
        self.verify_artifacts.assert_not_called()

        self.contract.revalidate_inputs.side_effect = None
        self.verify_artifacts.side_effect = core.TargetRefused("binding")
        with self.assertRaises(core.TargetRefused):
            self.verify()
        self.reader.require_current_clients.assert_not_called()
        self.reader._raw.assert_not_called()

    def test_failed_capture_proof_or_wrong_record_count_cannot_replay(self):
        self.reader.require_current_clients.side_effect = core.TargetRefused("observation")
        with self.assertRaises(core.TargetRefused):
            self.verify()
        self.reader.require_current_clients.side_effect = None
        for rows in (self.rows[:-1], [*self.rows, self.rows[-1]]):
            with self.subTest(count=len(rows)):
                self.reader.require_current_clients.return_value = rows
                with self.assertRaises(core.TargetRefused):
                    self.verify()
        self.reader._raw.assert_not_called()

    def test_unqualified_mislabeled_or_over_budget_records_refuse(self):
        for index, changes in (
            (0, {"index": True}), (0, {"index": 2}),
            (0, {"label": "property"}),
            (0, {"client_qualified": False}),
            (0, {"client_qualified": 1}),
            (0, {"status": "timeout"}),
            (0, {"effective_deadline_ms": 15_001}),
            (0, {"effective_deadline_ms": True}),
            (7, {"effective_deadline_ms": 120_001}),
            (19, {"effective_deadline_ms": 90_001}),
        ):
            with self.subTest(index=index, changes=changes), patch.dict(
                    self.rows[index], changes), self.assertRaises(core.TargetRefused):
                self.verify()

    def test_output_readback_failure_has_no_path_in_refusal(self):
        self.reader._raw.side_effect = OSError("D:/private/capture.bin")
        with self.assertRaises(core.TargetRefused) as refused:
            self.verify()
        self.assertNotIn("private", str(refused.exception))

    def test_qualified_rows_still_need_to_match_semantic_replay(self):
        stdout_path = self.rows[8]["stdout"]["path"]
        with patch.dict(self.raw, {stdout_path: b"0" * 64 + b"  wrong.apk\n"}):
            with self.assertRaises(core.TargetRefused):
                self.verify()


if __name__ == "__main__":
    unittest.main()
