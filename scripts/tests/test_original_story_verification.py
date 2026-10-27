"""Independent original-story evidence adversaries; synthetic metadata, never SDK proof.

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


CLASSES = ("OriginalStoryWireTest", "OriginalStoryDialogTest", "OriginalStoryMainActivityTest")
METHODS = (
    ("strictAuthorInputAndProposalRejectForeignFieldsAndBounds",
     "nativeAuthoringReadsNeverCreateAndCancelKeepsLibrary",
     "nativeReviewedCreateRetriesAfterReopenWithoutGeneration"),
    ("scriptedProviderIsLabelledAndGenerateDoesNotCreate",
     "editsInvalidateReviewAndStaleCreateCannotBorrowNewConsent"),
    ("originalPremiseEditedWorldCreatesAndOrdinaryReopenRetainsPlayer",
     "cancelOriginalDraftPreservesCurrentScopeAndPlayerDraft",
     "createdOriginalStoryCanAcceptGeneratedTurnWithScopedReceipts"),
)


def fixture(out):
    (out / "clients").mkdir()
    results = []
    for i, (name, methods) in enumerate(zip(CLASSES, METHODS), 1):
        raw = synthetic_regression_run(name, methods)
        (out / (name + ".stdout.raw")).write_bytes(raw)
        results.append(validate_instrumentation(raw, "org.locallore.app." + name, list(methods)))
        stem = out / "clients" / ("command-%04d" % i)
        stem.with_suffix(".stdout.bin").write_bytes(raw)
        d.env.create_json(stem.with_suffix(".json"), dict(version=2, index=i,
            label="instrument-" + str(i - 1), status="completed", returncode=0,
            cleanup_complete=True, stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest(),
            stderr_bytes=0, elapsed_ms=37 + i, effective_deadline_ms=180000))
    return dict(version=1, phase="original-story", results=results, clients=3,
        clients_clean=True, method_count=8, external_controller_case_executed=False)


def row_update(out, i, **delta):
    path = out / "clients" / ("command-%04d.json" % i)
    value = d.env.read_json(path)
    value.update(delta)
    path.write_text(json.dumps(value), encoding="utf-8")


def replace_frame(out, i, raw):
    """Rebind both copies/hashes: refusal must depend on evidence semantics."""
    (out / (CLASSES[i - 1] + ".stdout.raw")).write_bytes(raw)
    (out / "clients" / ("command-%04d.stdout.bin" % i)).write_bytes(raw)
    row_update(out, i, stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest())


class OriginalStoryVerificationTests(unittest.TestCase):
    def test_roster_and_dispatch_are_independent_exact_eight_with_unchanged_caps(self):
        self.assertEqual(d.ORIGINAL_STORY_VERSION, 1)
        self.assertEqual(d.ORIGINAL_STORY_CLASSES, CLASSES)
        self.assertEqual(d.ORIGINAL_STORY_METHODS, METHODS)
        for i, (name, methods) in enumerate(zip(CLASSES, METHODS)):
            self.assertEqual(test_roster(d.ROOT / "apps/android/app/src/androidTest/java/org/locallore/app" /
                (name + ".kt")), list(methods))
            self.assertEqual(d.original_story_dispatch(i),
                (["exec-out", "am", "instrument", "--user", "0", "-w", "-r", "-e", "class",
                  "org.locallore.app." + name, d.APP + ".test/androidx.test.runner.AndroidJUnitRunner"],
                 "instrument-" + str(i), 180, 262144))
        for selector in (True, False, -1, 3, "0", 0.0, None):
            with self.subTest(selector=selector), self.assertRaises(d.VerificationRefused):
                d.original_story_dispatch(selector)
        self.assertTrue(set(CLASSES).isdisjoint(d.CLASSES + d.REGRESSION_CLASSES + d.STORY_CREATION_CLASSES +
            d.STARTER_CHOICE_CLASSES + d.PLAYER_SETUP_CLASSES + d.STORY_PRESENTATION_CLASSES))
        self.assertEqual(tuple(sum(map(len, rows)) for rows in (d.EXPECTED_METHODS, d.REGRESSION_METHODS,
            d.STORY_CREATION_METHODS, d.STARTER_CHOICE_METHODS, d.RETAINED_ARCHIVE_METHODS,
            d.PLAYER_SETUP_METHODS, d.STORY_PRESENTATION_METHODS)), (10, 89, 19, 7, 2, 8, 8))

    def test_cli_has_no_arbitrary_method_class_profile_or_extended_budget_selector(self):
        args = ["original-story", "--out", "out", "--sdk", "sdk", "--build", "build",
            "--proposal", "proposal", "--running", "running", "--server", "server", "--powershell", "powershell"]
        with patch.object(d, "supervise") as owner, patch("sys.stdout", io.StringIO()):
            self.assertEqual(d.main(args), 0)
        self.assertEqual(owner.call_args.args[0]["phase"], "original-story")
        for extra in (["--class", "OriginalStoryMainActivityTest"], ["--method", METHODS[2][2]],
                      ["--profile", "phone"], ["--seconds", "1800"], ["--skip-native"]):
            with self.subTest(extra=extra), patch.object(d, "supervise") as owner, \
                 patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
                d.main(args + extra)
            owner.assert_not_called()

    def test_exact_synthetic_record_is_read_only_and_cannot_unlock_another_phase(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); record = fixture(out); before = copy.deepcopy(record)
            d.validate_original_story_record(record, out); d.require_current_clients(out, 3)
            self.assertEqual(record, before)
            for validator in (d.validate_component_record, d.validate_regression_record,
                d.validate_story_creation_record, d.validate_starter_choice_record,
                d.validate_player_setup_record, d.validate_story_presentation_record,
                d.validate_retained_archive_record):
                with self.assertRaises(d.VerificationRefused): validator(record, out)
            for delta in ({"phase": "story-presentation"}, {"version": True}, {"method_count": True},
                {"method_count": 9}, {"clients_clean": None}, {"external_controller_case_executed": True},
                {"private_origin": "unrequested"}):
                with self.subTest(delta=delta), self.assertRaises(d.VerificationRefused):
                    d.validate_original_story_record(dict(record, **delta), out)

    def test_fully_rebound_foreign_class_or_same_count_foreign_methods_still_refuse(self):
        for foreign in (synthetic_regression_run("StoryPresentationMainActivityTest", METHODS[2]),
            synthetic_regression_run(CLASSES[2], ("grantAuthorAuthority", "skipReview", "replaceExistingStory"))):
            with tempfile.TemporaryDirectory() as root:
                out = Path(root); record = fixture(out)
                replace_frame(out, 3, foreign)
                d.require_current_clients(out, 3)
                with self.assertRaises(d.VerificationRefused): d.validate_original_story_record(record, out)

    def test_extra_missing_skipped_failed_or_incomplete_junit_frames_refuse_after_hash_rebinding(self):
        original = synthetic_regression_run(CLASSES[2], METHODS[2])
        frames = [b"", original.rsplit(b"INSTRUMENTATION_CODE:", 1)[0],
            original + b"INSTRUMENTATION_CODE: -1\n", b"x" * 262145,
            original.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -3", 1),
            original.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2", 1),
            original.replace(b"OK (3 tests)", b"OK (2 tests)"),
            synthetic_regression_run(CLASSES[2], METHODS[2] + ("unapprovedPrivilegedCreate",)),
            synthetic_regression_run(CLASSES[2], METHODS[2][:-1])]
        for raw in frames:
            with self.subTest(raw_bytes=len(raw)), tempfile.TemporaryDirectory() as root:
                out = Path(root); record = fixture(out); replace_frame(out, 3, raw)
                with self.assertRaises(d.VerificationRefused): d.validate_original_story_record(record, out)

    def test_result_order_duplicate_class_and_claimed_methods_cannot_hide_wrong_raw(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); record = fixture(out)
            for mutation in ("order", "duplicate", "missing", "method", "wrong_class"):
                value = copy.deepcopy(record)
                if mutation == "order": value["results"].reverse()
                if mutation == "duplicate": value["results"][1] = value["results"][0]
                if mutation == "missing": value["results"].pop()
                if mutation == "method": value["results"][0]["methods"][0] = "grantHiddenCapability"
                if mutation == "wrong_class": value["results"][1]["class"] = "org.locallore.app.StoryCreationDialogTest"
                with self.subTest(mutation=mutation), self.assertRaises(d.VerificationRefused):
                    d.validate_original_story_record(value, out)

    def test_changed_source_roster_is_refused_before_any_guest_or_capture_is_acquired(self):
        from benchmarks import android_process_client as client
        def changed(source):
            roster = test_roster(source)
            return roster + ["unreviewedAuthorMutation"] if source.name == CLASSES[1] + ".kt" else roster
        with tempfile.TemporaryDirectory() as root, patch.object(d, "qualified_build", return_value={}), \
             patch("benchmarks.android_instrumentation_evidence.test_roster", side_effect=changed), \
             patch.object(d.env, "open_live_owner") as owner, patch.object(client, "SdkCapture") as capture:
            with self.assertRaises(d.VerificationRefused):
                d._instrumentation_worker({"build": "build"}, Path(root), "original-story")
            owner.assert_not_called(); capture.assert_not_called()

    def test_closed_owner_wrong_guest_or_source_drift_cannot_begin_sdk_capture(self):
        from benchmarks import android_process_client as client
        for failure in ("owner", "guest", "source"):
            lease = SimpleNamespace(descriptor=dict(avd_name=d.env.NAME, serial="emulator-5592",
                console_port=5592, guest_boot_verified=False), check=Mock())
            if failure == "guest": lease.descriptor["console_port"] = 5594
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as root, \
                 patch.object(d, "qualified_build", return_value={}), \
                 patch.object(d.env, "digest", return_value="0" * 64), \
                 patch.object(d.env, "open_live_owner", side_effect=d.VerificationRefused("closed") if failure == "owner" else None, return_value=lease), \
                 patch.object(d.env, "read_json", return_value={"expected": "source"}), \
                 patch.object(d, "source_map", return_value={"unexpected": "source"}), \
                 patch.object(client, "SdkCapture") as capture:
                request = dict(build="build", proposal="proposal", running="running", sources={"path": "source"})
                with self.assertRaises(d.VerificationRefused):
                    d._instrumentation_worker(request, Path(root), "original-story")
                capture.assert_not_called()

    def test_historical_or_unmeasured_client_rows_cannot_qualify_current_execution(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); record = fixture(out); path = out / "clients/command-0002.json"
            original = d.env.read_json(path)
            historical = {k: v for k, v in original.items() if k not in ("elapsed_ms", "effective_deadline_ms")}
            historical["version"] = 1; path.write_text(json.dumps(historical), encoding="utf-8")
            # This new phase has no historical SDK1 cohort to preserve: both
            # its phase validator and generic current-run gate must refuse it.
            with self.assertRaises(d.VerificationRefused):
                d.validate_original_story_record(record, out)
            with self.assertRaises(d.VerificationRefused): d.require_current_clients(out, 3)
            for delta in ({"elapsed_ms": None}, {"elapsed_ms": True}, {"elapsed_ms": -1},
                {"elapsed_ms": 1.5}, {"effective_deadline_ms": True}, {"effective_deadline_ms": 180001},
                {"cleanup_complete": None}, {"returncode": None}, {"stdout_sha256": "0" * 64}):
                path.write_text(json.dumps(dict(original, **delta)), encoding="utf-8")
                with self.subTest(delta=delta), self.assertRaises(d.VerificationRefused):
                    d.validate_original_story_record(record, out); d.require_current_clients(out, 3)

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_parent_replays_evidence_instead_of_trusting_a_successful_child_exit(self):
        for poison in (None, "label", "foreign_phase", "missing_pair", "foreign_raw", "extra_method", "historical"):
            with self.subTest(poison=poison), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=True,
                    output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                def supervised(*_):
                    body = fixture(out)
                    if poison == "label": body = dict(version=1, passed=True, phase="original-story", method_count=8)
                    if poison == "foreign_phase": body["phase"] = "story-presentation"
                    if poison == "missing_pair": (out / "clients/command-0001.stdout.bin").unlink()
                    if poison == "foreign_raw": replace_frame(out, 1, synthetic_regression_run("StoryPresentationWireTest", METHODS[0]))
                    if poison == "extra_method": replace_frame(out, 2, synthetic_regression_run(CLASSES[1], METHODS[1] + ("hiddenCreate",)))
                    if poison == "historical":
                        p = out / "clients/command-0001.json"; row = d.env.read_json(p)
                        row.pop("elapsed_ms"); row.pop("effective_deadline_ms"); row["version"] = 1
                        p.write_text(json.dumps(row), encoding="utf-8")
                    d.env.create_json(out / "original_story-v1.json", body)
                    return owner
                request = dict(phase="original-story", out=str(out), sdk=root, java=None, build="build",
                    running="running", proposal="proposal", server="server", powershell="powershell")
                with patch.object(d, "input_bindings", return_value=[]), patch.object(d, "source_map", return_value={"same": "source"}), \
                     patch.object(d.env, "supervise", side_effect=supervised) as run, \
                     patch.object(d, "validate_original_story_record", wraps=d.validate_original_story_record) as deep:
                    if poison:
                        with self.assertRaises(d.VerificationRefused): d.supervise(request)
                    else: d.supervise(request)
                self.assertEqual(run.call_args.args[3], 900); deep.assert_called_once()
                result = d.env.read_json(out / "result-v1.json")
                self.assertEqual(result["passed"], poison is None)
                self.assertEqual(result["phase"], "original-story")
                for foreign in ("components", "regression", "story_presentation", "player_setup"):
                    self.assertNotIn(foreign, result)

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_parent_retains_original_owner_but_refuses_unknown_cleanup_or_source_change(self):
        for failure in ("cleanup", "capture", "status", "returncode", "source"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=True,
                    output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                field = {"cleanup": "cleanup_complete", "capture": "output_capture_complete",
                    "status": "status", "returncode": "worker_returncode"}.get(failure)
                if field: owner[field] = None
                def supervised(*_):
                    d.env.create_json(out / "original_story-v1.json", fixture(out)); return owner
                request = dict(phase="original-story", out=str(out), sdk=root, java=None, build="build",
                    running="running", proposal="proposal", server="server", powershell="powershell")
                maps = [{"before": "source"}, {"after": "source"}] if failure == "source" else [{"same": "source"}] * 2
                with patch.object(d, "input_bindings", return_value=[]), patch.object(d, "source_map", side_effect=maps), \
                     patch.object(d.env, "supervise", side_effect=supervised), \
                     patch.object(d, "validate_original_story_record", wraps=d.validate_original_story_record) as deep:
                    with self.assertRaises(d.VerificationRefused): d.supervise(request)
                deep.assert_not_called(); result = d.env.read_json(out / "result-v1.json")
                self.assertIs(result["passed"], False); self.assertNotIn("original_story", result)
                self.assertEqual(d.env.read_json(out / "owner-result-v1.json"), owner)


if __name__ == "__main__":
    unittest.main()
