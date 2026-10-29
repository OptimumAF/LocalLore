"""Independent presentation-phase evidence forgery/refusal tests; no Android execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_process_verification as d
from benchmarks.android_instrumentation_evidence import test_roster, validate_instrumentation
from scripts.tests.test_android_process_verification import synthetic_regression_run

# Approved source identities are an independent oracle, not copied from the driver's
# dispatch table: replacing its table and its passed label together must still fail.
CLASSES = ("StoryPresentationWireTest", "StoryPresentationDialogTest", "StoryPresentationMainActivityTest")
METHODS = (
    ("presentationPreviewRequiresClosedBoundedLiteralSettings",
     "presentedCreationPreservesLegacyWireAndProbeSemantics",
     "nativePresentationGatewayRefusesMalformedOrForeignResults"),
    ("presentationEditsRequireExplicitReviewBeforeCreate",
     "retainedPresentationActionsCannotBorrowAReplacementReview",
     "invalidPhraseDraftsAndBusyStatesDisableReviewAndCreate"),
    ("presentationReviewCancelPreservesTheSelectedLibraryAndDraft",
     "presentedCreationRetainsToneAndPhrasesOnNativeReopen"),
)


def fixture(out):
    """Original synthetic frames and measured-v2-shaped pairs, never device evidence."""
    (out / "clients").mkdir()
    results = []
    for index, (name, methods) in enumerate(zip(CLASSES, METHODS), 1):
        raw = synthetic_regression_run(name, methods)
        (out / (name + ".stdout.raw")).write_bytes(raw)
        results.append(validate_instrumentation(raw, "org.locallore.app." + name, list(methods)))
        stem = out / "clients" / ("command-%04d" % index)
        stem.with_suffix(".stdout.bin").write_bytes(raw)
        d.env.create_json(stem.with_suffix(".json"), dict(version=2, index=index,
            label="instrument-" + str(index - 1), status="completed", returncode=0,
            cleanup_complete=True, stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest(),
            stderr_bytes=0, elapsed_ms=20 + index, effective_deadline_ms=180000))
    return dict(version=1, phase="story-presentation", results=results, clients=3,
                clients_clean=True, method_count=8, external_controller_case_executed=False)


def rewrite_row(path, **delta):
    row = d.env.read_json(path)
    row.update(delta)
    path.write_text(json.dumps(row), encoding="utf-8")


def rebind_foreign_frame(out, record):
    # A fully hashed older phase is still not the new presentation UI test.
    foreign = synthetic_regression_run("StoryPlayerSetupWireTest", d.PLAYER_SETUP_METHODS[0])
    (out / (CLASSES[0] + ".stdout.raw")).write_bytes(foreign)
    pair = out / "clients/command-0001.stdout.bin"
    pair.write_bytes(foreign)
    rewrite_row(out / "clients/command-0001.json", stdout_bytes=len(foreign),
                stdout_sha256=hashlib.sha256(foreign).hexdigest())
    # The forged result keeps the approved class/method claims. Only raw replay
    # can distinguish it from a passed presentation label and valid pair hashes.
    return record


class StoryPresentationPhaseTests(unittest.TestCase):
    def test_fixed_dispatch_cannot_retarget_profile_selector_or_worker_phase(self):
        for index, name in enumerate(CLASSES):
            self.assertEqual(d.story_presentation_dispatch(index),
                (["exec-out", "am", "instrument", "--user", "0", "-w", "-r", "-e", "class",
                  "org.locallore.app." + name, d.APP + ".test/androidx.test.runner.AndroidJUnitRunner"],
                 "instrument-" + str(index), 180, 262144))
        for bad in (True, -1, 3, 1.5, "0", None):
            with self.subTest(selector=bad), self.assertRaises(d.VerificationRefused):
                d.story_presentation_dispatch(bad)
        args = ["story-presentation", "--out", "out", "--sdk", "sdk", "--build", "build",
                "--proposal", "proposal", "--running", "running", "--server", "server",
                "--powershell", "powershell"]
        for extra in (["--class", "StoryPlayerSetupWireTest"], ["--method", METHODS[0][0]],
                      ["--profile", "physical"], ["--seconds", "1800"]):
            with patch.object(d, "supervise") as owner, patch("sys.stderr", io.StringIO()), \
                 self.assertRaises(SystemExit):
                d.main(args + extra)
            owner.assert_not_called()
        with patch.object(d, "_instrumentation_worker", return_value="synthetic-only") as worker:
            self.assertEqual(d.story_presentation_worker({"fixed": "request"}, Path("out")), "synthetic-only")
        worker.assert_called_once_with({"fixed": "request"}, Path("out"), "story-presentation")

    def test_rebound_player_setup_bytes_and_phase_labels_cannot_qualify_presentation(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = fixture(out)
            d.validate_story_presentation_record(record, out)
            d.require_current_clients(out, 3)
            before = copy.deepcopy(record)
            for phase in ("player-setup", "starter-choice", "story-creation", "regression", "components"):
                with self.subTest(phase=phase), self.assertRaises(d.VerificationRefused):
                    d.validate_story_presentation_record(dict(record, phase=phase), out)
            for validator in (d.validate_player_setup_record, d.validate_starter_choice_record,
                              d.validate_story_creation_record, d.validate_regression_record,
                              d.validate_component_record):
                with self.assertRaises(d.VerificationRefused):
                    validator(record, out)
            self.assertEqual(record, before)
            rebind_foreign_frame(out, record)
            # Pair metadata has also been rebound to the foreign bytes; hashing
            # alone cannot rescue false class/method claims in this exact phase.
            d.require_current_clients(out, 3)
            with self.assertRaises(d.VerificationRefused):
                d.validate_story_presentation_record(record, out)

    def test_unreported_extra_method_or_changed_source_cannot_hide_in_clean_runner_output(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = fixture(out)
            path = out / (CLASSES[2] + ".stdout.raw")
            original = path.read_bytes()
            for methods in (METHODS[2] + ("hiddenForeignCommit",), METHODS[2][:1]):
                raw = synthetic_regression_run(CLASSES[2], methods)
                path.write_bytes(raw)
                pair = out / "clients/command-0003.stdout.bin"
                pair.write_bytes(raw)
                rewrite_row(out / "clients/command-0003.json", stdout_bytes=len(raw),
                            stdout_sha256=hashlib.sha256(raw).hexdigest())
                with self.subTest(methods=methods), self.assertRaises(d.VerificationRefused):
                    d.validate_story_presentation_record(record, out)
            path.write_bytes(original)
            (out / "clients/command-0003.stdout.bin").write_bytes(original)
            rewrite_row(out / "clients/command-0003.json", stdout_bytes=len(original),
                        stdout_sha256=hashlib.sha256(original).hexdigest())
            d.validate_story_presentation_record(record, out)
            actual_roster = test_roster
            def changed_source(source):
                methods = actual_roster(source)
                return methods + ["unreviewedPresentationCapability"] if source.name == CLASSES[0] + ".kt" else methods
            with patch("benchmarks.android_instrumentation_evidence.test_roster", side_effect=changed_source), \
                 self.assertRaises(d.VerificationRefused):
                d.validate_story_presentation_record(record, out)

    def test_current_admission_distinguishes_historical_pairs_from_measured_capture(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = fixture(out)
            path = out / "clients/command-0002.json"
            row = d.env.read_json(path)
            historical = {key: value for key, value in row.items()
                          if key not in ("elapsed_ms", "effective_deadline_ms")}
            historical["version"] = 1
            path.write_text(json.dumps(historical), encoding="utf-8")
            # Historical generic compatibility is deliberate; this must never
            # satisfy the additional current-run worker/parent admission gate.
            d.validate_story_presentation_record(record, out)
            with self.assertRaises(d.VerificationRefused):
                d.require_current_clients(out, 3)
            for value in (None, True, -1, "21"):
                path.write_text(json.dumps(dict(row, elapsed_ms=value)), encoding="utf-8")
                with self.subTest(elapsed_ms=value), self.assertRaises(d.VerificationRefused):
                    d.require_current_clients(out, 3)

    def test_worker_refuses_closed_wrong_profile_or_changed_source_before_sdk_capture(self):
        from benchmarks import android_process_client as client
        for failure in ("closed", "profile", "source"):
            lease = SimpleNamespace(descriptor=dict(avd_name=d.env.NAME, serial="emulator-5592",
                console_port=5592, guest_boot_verified=False), check=Mock())
            if failure == "profile":
                lease.descriptor["serial"] = "emulator-5594"
            request = dict(build="build", running="running", proposal="proposal",
                           sources={"path": "source.json"})
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as root, \
                 patch.object(d, "qualified_build", return_value={}), \
                 patch.object(d.env, "digest", return_value="0" * 64), \
                 patch.object(d.env, "open_live_owner", side_effect=d.VerificationRefused("closed_owner") if failure == "closed" else None, return_value=lease), \
                 patch.object(d.env, "read_json", return_value={"accepted": "source"}), \
                 patch.object(d, "source_map", return_value={"changed": "source"}), \
                 patch.object(client, "SdkCapture") as capture:
                with self.assertRaises(d.VerificationRefused):
                    d.story_presentation_worker(request, Path(root))
                capture.assert_not_called()
                if failure == "source":
                    lease.check.assert_called_once_with()

    def test_worker_refuses_roster_mutation_before_obtaining_any_guest_or_sdk_owner(self):
        from benchmarks import android_process_client as client
        actual_roster = test_roster
        def wrong_roster(source):
            methods = actual_roster(source)
            return list(reversed(methods)) if source.name == CLASSES[1] + ".kt" else methods
        with tempfile.TemporaryDirectory() as root, patch.object(d, "qualified_build", return_value={}), \
             patch("benchmarks.android_instrumentation_evidence.test_roster", side_effect=wrong_roster), \
             patch.object(d.env, "open_live_owner") as owner, patch.object(client, "SdkCapture") as capture:
            with self.assertRaises(d.VerificationRefused):
                d.story_presentation_worker({"build": "build"}, Path(root))
            owner.assert_not_called()
            capture.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_parent_replays_raw_and_current_pairs_instead_of_trusting_child_success(self):
        cases = (None, "passed_label", "foreign_phase", "foreign_raw", "missing_metadata", "missing_stdout",
                 "historical", "boolean_elapsed", "unknown_client_cleanup", "extra_method")
        for failure in cases:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                request = dict(phase="story-presentation", out=str(out), sdk=root, java=None, build="build",
                    running="running", proposal="proposal", server="server", powershell="powershell")
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=True,
                    output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                def supervised(*_):
                    body = fixture(out)
                    if failure == "passed_label": body = dict(version=1, phase="story-presentation", passed=True, method_count=8)
                    if failure == "foreign_phase": body["phase"] = "player-setup"
                    if failure == "foreign_raw": rebind_foreign_frame(out, body)
                    if failure == "missing_metadata": (out / "clients/command-0002.json").unlink()
                    if failure == "missing_stdout": (out / "clients/command-0002.stdout.bin").unlink()
                    if failure == "historical":
                        path = out / "clients/command-0002.json"
                        row = d.env.read_json(path)
                        row.pop("elapsed_ms"); row.pop("effective_deadline_ms"); row["version"] = 1
                        path.write_text(json.dumps(row), encoding="utf-8")
                    if failure == "boolean_elapsed": rewrite_row(out / "clients/command-0002.json", elapsed_ms=True)
                    if failure == "unknown_client_cleanup": rewrite_row(out / "clients/command-0002.json", cleanup_complete=None)
                    if failure == "extra_method":
                        raw = synthetic_regression_run(CLASSES[0], METHODS[0] + ("unreportedOverride",))
                        (out / (CLASSES[0] + ".stdout.raw")).write_bytes(raw)
                    d.env.create_json(out / "story_presentation-v1.json", body)
                    return owner
                with patch.object(d, "input_bindings", return_value=[]), \
                     patch.object(d, "source_map", return_value={"original": "source"}), \
                     patch.object(d.env, "supervise", side_effect=supervised) as run, \
                     patch.object(d, "validate_story_presentation_record", wraps=d.validate_story_presentation_record) as deep, \
                     patch.object(d, "require_current_clients", wraps=d.require_current_clients) as current:
                    if failure:
                        with self.assertRaises(d.VerificationRefused): d.supervise(request)
                    else:
                        d.supervise(request)
                self.assertEqual(run.call_args.args[3], 900)
                self.assertEqual(deep.call_count, 1)
                result = d.env.read_json(out / "result-v1.json")
                self.assertEqual(result["passed"], failure is None)
                self.assertEqual(current.call_count, int(failure in (None, "historical")))
                for other in ("components", "player_setup", "starter_choice", "story_creation", "regression"):
                    self.assertNotIn(other, result)

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_parent_unknown_ownership_or_source_drift_cannot_publish_any_qualified_record(self):
        for failure in ("cleanup", "capture", "status", "returncode", "source"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                request = dict(phase="story-presentation", out=str(out), sdk=root, java=None, build="build",
                    running="running", proposal="proposal", server="server", powershell="powershell")
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=True,
                    output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                if failure == "cleanup": owner["cleanup_complete"] = None
                if failure == "capture": owner["output_capture_complete"] = None
                if failure == "status": owner["status"] = "unknown"
                if failure == "returncode": owner["worker_returncode"] = None
                def supervised(*_):
                    body = fixture(out)
                    d.env.create_json(out / "story_presentation-v1.json", body)
                    return owner
                maps = [{"original": "source"}, {"changed": "source"}] if failure == "source" else [{"original": "source"}] * 2
                with patch.object(d, "input_bindings", return_value=[]), \
                     patch.object(d, "source_map", side_effect=maps), \
                     patch.object(d.env, "supervise", side_effect=supervised), \
                     patch.object(d, "validate_story_presentation_record", wraps=d.validate_story_presentation_record) as deep, \
                     patch.object(d, "require_current_clients", wraps=d.require_current_clients) as current:
                    with self.assertRaises(d.VerificationRefused): d.supervise(request)
                deep.assert_not_called()
                current.assert_not_called()
                result = d.env.read_json(out / "result-v1.json")
                self.assertIs(result["passed"], False)
                self.assertNotIn("story_presentation", result)
                self.assertEqual(d.env.read_json(out / "owner-result-v1.json"), owner)


if __name__ == "__main__":
    unittest.main()
