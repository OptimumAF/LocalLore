"""Fixed starter-choice admission/evidence adversaries; no SDK or device execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import android_process_verification as driver
from benchmarks.android_instrumentation_evidence import test_roster, validate_instrumentation
from scripts.tests.test_android_process_verification import synthetic_regression_run


class StarterChoicePhaseTests(unittest.TestCase):
    def fixture(self, out):
        (out / "clients").mkdir()
        results = []
        for index, (name, methods) in enumerate(zip(driver.STARTER_CHOICE_CLASSES, driver.STARTER_CHOICE_METHODS), 1):
            raw = synthetic_regression_run(name, methods)
            (out / (name + ".stdout.raw")).write_bytes(raw)
            results.append(validate_instrumentation(raw, "org.locallore.app." + name, list(methods)))
            stem = out / "clients" / ("command-%04d" % index)
            stem.with_suffix(".stdout.bin").write_bytes(raw)
            driver.env.create_json(stem.with_suffix(".json"), dict(version=2, index=index,
                label="instrument-" + str(index - 1), status="completed", returncode=0, cleanup_complete=True,
                stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest(), stderr_bytes=0,
                elapsed_ms=7, effective_deadline_ms=180000))
        return dict(version=1, phase="starter-choice", results=results, clients=3, clients_clean=True,
                    method_count=7, external_controller_case_executed=False)

    def test_exact_three_class_seven_method_roster_matches_real_sources_and_preserves_old_rosters(self):
        self.assertEqual(driver.STARTER_CHOICE_VERSION, 1)
        self.assertEqual(driver.STARTER_CHOICE_CLASSES, ("StoryTemplateChoiceWireTest", "StoryTemplateChoiceDialogTest",
                                                       "StoryTemplateChoiceMainActivityTest"))
        self.assertEqual(tuple(map(len, driver.STARTER_CHOICE_METHODS)), (3, 3, 1))
        for name, methods in zip(driver.STARTER_CHOICE_CLASSES, driver.STARTER_CHOICE_METHODS):
            self.assertEqual(test_roster(driver.ROOT / "apps/android/app/src/androidTest/java/org/locallore/app" /
                                        (name + ".kt")), list(methods))
        self.assertEqual(tuple(sum(map(len, methods)) for methods in (driver.EXPECTED_METHODS,
            driver.REGRESSION_METHODS, driver.RETAINED_UI_METHODS, driver.RETAINED_ARCHIVE_METHODS,
            driver.STORY_CREATION_METHODS)), (10, 89, 2, 2, 19))
        self.assertTrue(set(driver.STARTER_CHOICE_CLASSES).isdisjoint(driver.CLASSES + driver.REGRESSION_CLASSES +
            driver.RETAINED_UI_CLASSES + driver.RETAINED_ARCHIVE_CLASSES + driver.STORY_CREATION_CLASSES))

    def test_fixed_dispatch_closed_cli_and_bound_admission_offer_no_selector(self):
        for index, name in enumerate(driver.STARTER_CHOICE_CLASSES):
            command, label, seconds, cap = driver.starter_choice_dispatch(index)
            self.assertEqual(command, ["exec-out", "am", "instrument", "--user", "0", "-w", "-r", "-e", "class",
                "org.locallore.app." + name, driver.APP + ".test/androidx.test.runner.AndroidJUnitRunner"])
            self.assertEqual((label, seconds, cap), ("instrument-" + str(index), 180, 262144))
        for bad in (-1, 3, True, 1.0, "0", None):
            with self.subTest(bad=bad), self.assertRaises(driver.VerificationRefused): driver.starter_choice_dispatch(bad)
        args = ["starter-choice", "--out", "unused", "--sdk", "sdk", "--build", "build", "--running", "running",
                "--proposal", "proposal", "--server", "server", "--powershell", "powershell"]
        with patch.object(driver, "supervise") as run, patch("sys.stdout", io.StringIO()):
            self.assertEqual(driver.main(args), 0)
        self.assertEqual(run.call_args.args[0]["phase"], "starter-choice")
        for extra in (["--class", "Other"], ["--test", "method"], ["--profile", "phone"], ["--seconds", "1800"]):
            with patch.object(driver, "supervise") as run, patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
                driver.main(args + extra)
            run.assert_not_called()
        request = dict(phase="starter-choice", out="out", sdk="sdk", java=None, build="build", running="running",
            proposal="proposal", server="server", powershell="powershell", inputs=["bound"], sources={"path":"sources"},
            driver_sha256="hash")
        with patch.object(driver.env, "digest", return_value="hash"), patch.object(driver.env, "check_binding"), \
             patch.object(driver.env, "read_json", return_value={"source":"same"}), \
             patch.object(driver, "source_map", return_value={"source":"same"}), \
             patch.object(driver, "input_bindings", return_value=["bound"]):
            driver.admit_worker(request)
            for delta in ({"phase":"starter_choice"}, {"phase":"starter-choice-v2"}, {"class":"Other"},
                          {"inputs":[]}, {"driver_sha256":"changed"}):
                with self.subTest(delta=delta), self.assertRaises(driver.VerificationRefused):
                    driver.admit_worker(dict(request, **delta))

    def test_complete_original_records_are_immutable_and_not_a_component_or_older_phase_gate(self):
        from benchmarks import android_external_controller as external
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); record = self.fixture(out); original = copy.deepcopy(record)
            driver.validate_starter_choice_record(record, out)
            driver.require_current_clients(out, 3)
            self.assertEqual(record, original)
            for validate in (driver.validate_component_record, driver.validate_regression_record,
                             driver.validate_retained_ui_record, driver.validate_retained_archive_record,
                             driver.validate_story_creation_record):
                with self.assertRaises(driver.VerificationRefused): validate(record, out)
            gate = out / "not-native.json"
            gate.write_text(json.dumps(dict(version=1, phase="starter-choice", passed=True, owner={}, owner_record={},
                request={}, sources_before={}, sources_after={}, starter_choice={})))
            with self.assertRaises(external.ExternalRefused): external.qualified_gate(gate, "build")

    def test_wrong_phase_class_methods_counts_and_partial_rosters_refuse(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); record = self.fixture(out)
            for delta in ({"version":True}, {"phase":"story-creation"}, {"method_count":6}, {"method_count":True},
                          {"clients_clean":False}, {"external_controller_case_executed":True}, {"extra":0}):
                with self.subTest(delta=delta), self.assertRaises(driver.VerificationRefused):
                    driver.validate_starter_choice_record(dict(record, **delta), out)
            for change in ("drop", "extra", "order", "class", "method"):
                altered = copy.deepcopy(record)
                if change == "drop": altered["results"].pop()
                if change == "extra": altered["results"].append(altered["results"][0])
                if change == "order": altered["results"].reverse()
                if change == "class": altered["results"][0]["class"] = "org.locallore.app.StoryCreationWireTest"
                if change == "method": altered["results"][0]["methods"][0] = "foreignMethod"
                with self.subTest(change=change), self.assertRaises(driver.VerificationRefused):
                    driver.validate_starter_choice_record(altered, out)

    def test_partial_skipped_extra_and_oversize_raw_frames_refuse(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); record = self.fixture(out)
            for name, methods in zip(driver.STARTER_CHOICE_CLASSES, driver.STARTER_CHOICE_METHODS):
                path = out / (name + ".stdout.raw"); original = path.read_bytes()
                for raw in (b"", b"x" * 262145, synthetic_regression_run(name, methods[:-1]),
                            original + b"INSTRUMENTATION_CODE: -1\n",
                            original.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -3", 1)):
                    path.write_bytes(raw)
                    with self.assertRaises(driver.VerificationRefused): driver.validate_starter_choice_record(record, out)
                path.write_bytes(original)

    def test_missing_extra_rebound_unclean_or_timingless_client_pairs_refuse(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); record = self.fixture(out)
            stem = out / "clients/command-0001"; path = stem.with_suffix(".json")
            original = path.read_bytes(); row = json.loads(original)
            for delta in ({"index":2}, {"label":"instrument-1"}, {"returncode":False}, {"cleanup_complete":False},
                          {"stderr_bytes":1}, {"stdout_bytes":262145}, {"stdout_sha256":"0" * 64}):
                path.write_text(json.dumps(dict(row, **delta)))
                with self.subTest(delta=delta), self.assertRaises(driver.VerificationRefused):
                    driver.validate_starter_choice_record(record, out)
            path.write_bytes(original)
            raw_path = stem.with_suffix(".stdout.bin"); raw = raw_path.read_bytes()
            foreign = synthetic_regression_run(driver.STARTER_CHOICE_CLASSES[1], driver.STARTER_CHOICE_METHODS[1])
            raw_path.write_bytes(foreign)
            path.write_text(json.dumps(dict(row, stdout_bytes=len(foreign), stdout_sha256=hashlib.sha256(foreign).hexdigest())))
            with self.assertRaises(driver.VerificationRefused): driver.validate_starter_choice_record(record, out)
            raw_path.write_bytes(raw); path.write_bytes(original)
            raw_path.unlink()
            with self.assertRaises((OSError, driver.env.EnvironmentRefused)):
                driver.validate_starter_choice_record(record, out)
            raw_path.write_bytes(raw)
            extra = out / "clients/extra.bin"; extra.write_bytes(b"synthetic")
            with self.assertRaises(driver.VerificationRefused): driver.validate_starter_choice_record(record, out)
            extra.unlink()
            historical = {key:value for key,value in row.items() if key not in ("elapsed_ms", "effective_deadline_ms")}
            historical["version"] = 1; path.write_text(json.dumps(historical))
            driver.validate_starter_choice_record(record, out)  # Historical readers remain readable.
            with self.assertRaises(driver.VerificationRefused): driver.require_current_clients(out, 3)

    def run_worker(self, existing=None, early=None, historical=False):
        from benchmarks import android_process_client as client
        calls = []
        with tempfile.TemporaryDirectory() as root:
            out = Path(root); apks = []
            for index, package in enumerate(driver.PACKAGES):
                path = out / (str(index) + ".apk"); path.write_bytes(bytes([index]))
                apks.append(dict(driver.env.binding(path), package=package))
            live = SimpleNamespace(descriptor=dict(avd_name=driver.env.NAME, serial="emulator-5592", console_port=5592,
                guest_boot_verified=False, launcher={}), check=lambda: None)
            if early == "owner":
                def refuse(): raise driver.VerificationRefused("closed_owner")
                live.check = refuse
            class FakeCapture:
                def __init__(self, directory, seconds, *_):
                    calls.append(("capture", seconds)); self.directory = directory; directory.mkdir()
                    self.count = 0; self.clean = True
                def record(self, raw, label, seconds=15, cap=131072):
                    self.count += 1; stem = self.directory / ("command-%04d" % self.count)
                    stem.with_suffix(".stdout.bin").write_bytes(raw)
                    row = dict(version=1 if historical else 2, index=self.count, label=label, status="completed",
                        returncode=0, cleanup_complete=True, stdout_bytes=len(raw),
                        stdout_sha256=hashlib.sha256(raw).hexdigest(), stderr_bytes=0)
                    if not historical: row.update(elapsed_ms=7, effective_deadline_ms=math.ceil(seconds * 1000))
                    driver.env.create_json(stem.with_suffix(".json"), row)
                    return raw
                def check_server(self): self.record(b"synthetic server", "adb-server", 15, 16384)
                def capture(self, *_): return self.record(b"emulator-5592 device transport_id:7\n", "devices")
                def shell(self, args, label, seconds, cap):
                    if args[0] == "getprop": raw = {"sys.boot_completed":b"1", "ro.build.version.sdk":b"35", "ro.product.cpu.abi":b"x86_64"}[args[1]]
                    elif args == ["am", "get-current-user"]: raw = b"0"
                    elif args[:4] == ["cmd", "package", "list", "packages"]: raw = b"present" if args[-1] == existing else b""
                    elif args[:3] == ["cmd", "package", "path"]: raw = ("package:/data/app/" + str(driver.PACKAGES.index(args[-1])) + "/base.apk").encode()
                    elif args[0] == "sha256sum": raw = (apks[int(args[1].split("/")[-2])]["sha256"] + " base.apk").encode()
                    else: raise AssertionError(args)
                    return self.record(raw, label, seconds, cap)
                def adb(self, args, label, seconds, cap=131072):
                    calls.append(("adb", args, label, seconds, cap))
                    if args[0] == "install": return self.record(b"Success", label, seconds, cap)
                    index = int(label.split("-")[1])
                    return self.record(synthetic_regression_run(driver.STARTER_CHOICE_CLASSES[index],
                        driver.STARTER_CHOICE_METHODS[index]), label, seconds, cap)
            request = dict(build="build", running=str(out / "running"), proposal="proposal", sdk=str(out),
                powershell=str(out / "powershell.exe"), server="server", sources={"path":"sources"})
            digest, read = driver.env.digest, driver.env.read_json
            with patch.object(driver, "qualified_build", return_value={"apks":apks}), \
                 patch.object(driver.env, "open_live_owner", return_value=live), \
                 patch.object(driver.env, "digest", side_effect=lambda p:"hash" if str(p) == request["running"] else digest(p)), \
                 patch.object(driver.env, "read_json", side_effect=lambda p:{} if str(p) in ("server", "sources") else read(p)), \
                 patch.object(driver, "source_map", return_value={"changed":True} if early == "source" else {}), \
                 patch.object(client, "SdkCapture", FakeCapture):
                if existing or early or historical:
                    with self.assertRaises(driver.VerificationRefused): driver.starter_choice_worker(request, out)
                else: driver.starter_choice_worker(request, out)
            adb = [call for call in calls if call[0] == "adb"]
            if existing or early:
                self.assertEqual(adb, [])
                if early: self.assertEqual(calls, [])
            elif not historical:
                self.assertEqual(calls[0], ("capture", 850))
                self.assertEqual(len(adb), 6)
                for index, call in enumerate(adb[3:]): self.assertEqual(call[1:], driver.starter_choice_dispatch(index))
                result = read(out / "starter_choice-v1.json")
                self.assertEqual((result["phase"], result["method_count"]), ("starter-choice", 7))
                self.assertFalse((out / "components-v1.json").exists())
            if existing or early or historical: self.assertFalse((out / "starter_choice-v1.json").exists())

    def test_worker_requires_current_clients_fixed_calls_fresh_packages_source_and_owner(self):
        self.run_worker()
        for package in driver.PACKAGES:
            with self.subTest(package=package): self.run_worker(existing=package)
        for early in ("owner", "source"):
            with self.subTest(early=early): self.run_worker(early=early)
        self.run_worker(historical=True)

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_parent_revalidates_original_frame_and_current_pairs_after_persisting_owner(self):
        for failure in (None, "historical", "frame", "cleanup"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                request = dict(phase="starter-choice", out=str(out), sdk=root, java=None, build="build", running="running",
                    proposal="proposal", server="server", powershell="powershell")
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=failure != "cleanup",
                    output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                def supervised(*_):
                    body = self.fixture(out)
                    if failure == "historical":
                        path = out / "clients/command-0001.json"; row = driver.env.read_json(path)
                        row.pop("elapsed_ms"); row.pop("effective_deadline_ms"); row["version"] = 1
                        path.write_text(json.dumps(row))
                    if failure == "frame":
                        (out / (driver.STARTER_CHOICE_CLASSES[0] + ".stdout.raw")).write_bytes(b"partial")
                    driver.env.create_json(out / "starter_choice-v1.json", body)
                    return owner
                original = driver.validate_starter_choice_record
                def validate(body, folder):
                    self.assertEqual(driver.env.read_json(out / "owner-result-v1.json"), owner)
                    return original(body, folder)
                with patch.object(driver, "input_bindings", return_value=[]), \
                     patch.object(driver, "source_map", return_value={"same":"source"}), \
                     patch.object(driver.env, "supervise", side_effect=supervised) as run, \
                     patch.object(driver, "validate_starter_choice_record", side_effect=validate) as deep:
                    if failure:
                        with self.assertRaises(driver.VerificationRefused): driver.supervise(request)
                    else: driver.supervise(request)
                self.assertEqual(run.call_args.args[3], 900)
                self.assertEqual(deep.call_count, int(failure != "cleanup"))
                result = driver.env.read_json(out / "result-v1.json")
                self.assertEqual(result["passed"], failure is None)
                for key in ("components", "regression", "retained_ui", "retained_archive", "story_creation"):
                    self.assertNotIn(key, result)


if __name__ == "__main__":
    unittest.main()
