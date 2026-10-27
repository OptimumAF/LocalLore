"""Original player-setup roster/admission/evidence adversaries, without a device.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import android_process_verification as d
from benchmarks.android_instrumentation_evidence import test_roster, validate_instrumentation
from scripts.tests.test_android_process_verification import synthetic_regression_run


class PlayerSetupPhaseTests(unittest.TestCase):
    def fixture(self, out):
        (out / "clients").mkdir()
        results = []
        for index, (name, methods) in enumerate(zip(d.PLAYER_SETUP_CLASSES, d.PLAYER_SETUP_METHODS), 1):
            raw = synthetic_regression_run(name, methods)
            (out / (name + ".stdout.raw")).write_bytes(raw)
            results.append(validate_instrumentation(raw, "org.locallore.app." + name, list(methods)))
            stem = out / "clients" / ("command-%04d" % index)
            stem.with_suffix(".stdout.bin").write_bytes(raw)
            d.env.create_json(stem.with_suffix(".json"), dict(version=2, index=index,
                label="instrument-" + str(index - 1), status="completed", returncode=0, cleanup_complete=True,
                stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest(), stderr_bytes=0,
                elapsed_ms=11 + index, effective_deadline_ms=180000))
        return dict(version=1, phase="player-setup", results=results, clients=3, clients_clean=True,
                    method_count=8, external_controller_case_executed=False)

    def test_actual_roster_is_exactly_eight_new_methods_without_expanding_existing_phases(self):
        self.assertEqual(d.PLAYER_SETUP_VERSION, 1)
        self.assertEqual(tuple(map(len, d.PLAYER_SETUP_METHODS)), (3, 3, 2))
        for name, methods in zip(d.PLAYER_SETUP_CLASSES, d.PLAYER_SETUP_METHODS):
            self.assertEqual(test_roster(d.ROOT / "apps/android/app/src/androidTest/java/org/locallore/app" /
                (name + ".kt")), list(methods))
        old = (d.CLASSES + d.REGRESSION_CLASSES + d.STORY_CREATION_CLASSES + d.STARTER_CHOICE_CLASSES)
        self.assertTrue(set(d.PLAYER_SETUP_CLASSES).isdisjoint(old))
        self.assertEqual(tuple(sum(map(len, methods)) for methods in
            (d.EXPECTED_METHODS, d.REGRESSION_METHODS, d.STORY_CREATION_METHODS, d.STARTER_CHOICE_METHODS)),
            (10, 89, 19, 7))

    def test_dispatch_and_cli_cannot_select_a_different_class_profile_or_deadline(self):
        for index, name in enumerate(d.PLAYER_SETUP_CLASSES):
            self.assertEqual(d.player_setup_dispatch(index),
                (["exec-out", "am", "instrument", "--user", "0", "-w", "-r", "-e", "class",
                  "org.locallore.app." + name, d.APP + ".test/androidx.test.runner.AndroidJUnitRunner"],
                 "instrument-" + str(index), 180, 262144))
        for value in (True, -1, 3, 0.0, "1", None):
            with self.subTest(value=value), self.assertRaises(d.VerificationRefused):
                d.player_setup_dispatch(value)
        args = ["player-setup", "--out", "out", "--sdk", "sdk", "--build", "build", "--proposal", "proposal",
                "--running", "running", "--server", "server", "--powershell", "powershell"]
        with patch.object(d, "supervise") as run, patch("sys.stdout", io.StringIO()):
            self.assertEqual(d.main(args), 0)
        self.assertEqual(run.call_args.args[0]["phase"], "player-setup")
        for extra in (["--class", "Foreign"], ["--profile", "phone"], ["--seconds", "1800"], ["--method", "other"]):
            with patch.object(d, "supervise") as run, patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
                d.main(args + extra)
            run.assert_not_called()
        with patch.object(d, "_instrumentation_worker", return_value="fixed") as worker:
            self.assertEqual(d.player_setup_worker({"request": "original"}, Path("out")), "fixed")
        worker.assert_called_once_with({"request": "original"}, Path("out"), "player-setup")

    def test_complete_original_frames_are_immutable_and_cannot_qualify_a_different_gate(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            before = copy.deepcopy(record)
            d.validate_player_setup_record(record, out)
            d.require_current_clients(out, 3)
            self.assertEqual(record, before)
            for validate in (d.validate_component_record, d.validate_regression_record,
                             d.validate_story_creation_record, d.validate_starter_choice_record):
                with self.assertRaises(d.VerificationRefused):
                    validate(record, out)

    def test_rebound_class_method_order_extra_fields_and_noninteger_counts_cannot_forge_the_phase(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            for delta in ({"phase": "starter-choice"}, {"version": True}, {"method_count": True},
                          {"method_count": 7}, {"clients_clean": False}, {"private": "original-canary"},
                          {"external_controller_case_executed": True}):
                with self.subTest(delta=delta), self.assertRaises(d.VerificationRefused):
                    d.validate_player_setup_record(dict(record, **delta), out)
            for mutation in ("duplicate", "reverse", "method", "foreign", "truncated"):
                candidate = copy.deepcopy(record)
                if mutation == "duplicate": candidate["results"][1] = candidate["results"][0]
                if mutation == "reverse": candidate["results"].reverse()
                if mutation == "method": candidate["results"][0]["methods"][0] = "foreignSetup"
                if mutation == "foreign": candidate["results"][0]["class"] = "org.locallore.app.StoryCreationWireTest"
                if mutation == "truncated": candidate["results"].pop()
                with self.subTest(mutation=mutation), self.assertRaises(d.VerificationRefused):
                    d.validate_player_setup_record(candidate, out)

    def test_skipped_truncated_duplicate_terminal_and_oversize_runner_frames_refuse(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            name, methods = d.PLAYER_SETUP_CLASSES[2], d.PLAYER_SETUP_METHODS[2]
            path = out / (name + ".stdout.raw")
            original = path.read_bytes()
            for raw in (b"", synthetic_regression_run(name, methods[:1]), b"x" * 262145,
                        original + b"INSTRUMENTATION_CODE: -1\n",
                        original.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -3", 1)):
                path.write_bytes(raw)
                with self.subTest(length=len(raw)), self.assertRaises(d.VerificationRefused):
                    d.validate_player_setup_record(record, out)
            path.write_bytes(original)
            d.validate_player_setup_record(record, out)

    def test_hash_rebinding_or_legacy_timing_cannot_replace_original_current_client_pairs(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            path = out / "clients/command-0001.json"
            row = d.env.read_json(path)
            raw_path = path.with_suffix(".stdout.bin")
            original = raw_path.read_bytes()
            foreign = (out / (d.PLAYER_SETUP_CLASSES[1] + ".stdout.raw")).read_bytes()
            raw_path.write_bytes(foreign)
            path.write_text(json.dumps(dict(row, stdout_bytes=len(foreign), stdout_sha256=hashlib.sha256(foreign).hexdigest())))
            with self.assertRaises(d.VerificationRefused): d.validate_player_setup_record(record, out)
            raw_path.write_bytes(original)
            for delta in ({"cleanup_complete": False}, {"returncode": 1}, {"stderr_bytes": 1},
                          {"index": True}, {"label": "instrument-1"}):
                path.write_text(json.dumps(dict(row, **delta)))
                with self.subTest(delta=delta), self.assertRaises(d.VerificationRefused):
                    d.validate_player_setup_record(record, out)
            historical = {key: value for key, value in row.items() if key not in ("elapsed_ms", "effective_deadline_ms")}
            historical["version"] = 1
            path.write_text(json.dumps(historical))
            d.validate_player_setup_record(record, out)
            with self.assertRaises(d.VerificationRefused): d.require_current_clients(out, 3)
            path.write_text(json.dumps(row))
            (out / "clients/original-extra.json").write_text("{}")
            with self.assertRaises(d.VerificationRefused): d.validate_player_setup_record(record, out)

    def test_closed_owned_guest_refuses_before_creating_any_sdk_capture(self):
        from benchmarks import android_process_client as client
        request = dict(build="build", running="running", proposal="proposal")
        with tempfile.TemporaryDirectory() as root, patch.object(d, "qualified_build", return_value={}), \
             patch.object(d.env, "digest", return_value="0" * 64), \
             patch.object(d.env, "open_live_owner", side_effect=d.VerificationRefused("closed_owner")), \
             patch.object(client, "SdkCapture") as capture:
            with self.assertRaises(d.VerificationRefused):
                d.player_setup_worker(request, Path(root))
            capture.assert_not_called()


if __name__ == "__main__":
    unittest.main()
