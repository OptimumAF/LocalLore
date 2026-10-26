"""Host-driver regressions; actual Windows binary child plus synthetic refusals.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import copy
import io
import json
import os
import re
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks import android_process_verification as driver


class DriverTests(unittest.TestCase):
    def test_evidence_json_refuses_duplicates_nonfinite_and_invalid_utf8(self):
        self.assertEqual(driver.strict_json_bytes(b'{"original":[1,true,null]}'), {"original": [1, True, None]})
        for raw in (b'{"key":1,"key":2}', b'{"nested":{"x":1,"x":2}}', b'{"x":NaN}',
                    b'{"x":1e9999}', b'\xff', b'{} trailing', b'{}\n{}'):
            with self.subTest(raw=raw), self.assertRaises(driver.VerificationRefused):
                driver.strict_json_bytes(raw)
        with self.assertRaises(driver.VerificationRefused):
            driver.strict_json_bytes(b'{}', cap=1)

    def test_all_tracked_input_extensions_include_sql_and_future_assets(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            names = ["crates/store/migrations/001.sql", "fixtures/original.unknown", "apps/android/gradlew"]
            for name in names:
                p = out / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"original")
            with patch.object(driver, "ROOT", out), \
                 patch.object(driver.subprocess, "check_output", return_value=("\0".join(names) + "\0").encode()):
                before = driver.source_map()
                self.assertEqual(set(before), set(names))
                (out / names[0]).write_bytes(b"modified")
                after = driver.source_map()
                self.assertNotEqual(before[names[0]], after[names[0]])
                self.assertEqual(before[names[1]], after[names[1]])

    def test_existing_destination_is_never_reused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)
            marker = path / "original"
            marker.write_bytes(b"keep")
            with self.assertRaises(driver.VerificationRefused):
                driver.output_path(path)
            self.assertEqual(marker.read_bytes(), b"keep")

    def test_evidence_inside_source_is_refused_before_creation(self):
        path = driver.ROOT / "never-create-process-evidence"
        self.assertFalse(path.exists())
        with self.assertRaises(driver.VerificationRefused):
            driver.output_path(path)
        self.assertFalse(path.exists())

    def test_wrong_artifact_package_order_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "artifacts.json"
            path.write_text(json.dumps({"version": 1, "build_profile": "input-process", "apks":
                [{"package": p} for p in reversed(driver.PACKAGES)]}), encoding="utf-8")
            with self.assertRaises(driver.VerificationRefused):
                driver.checked_apks(path)

    def test_changed_apk_refuses_old_manifest_even_with_same_size(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            apks = []
            for n, package in enumerate(driver.PACKAGES):
                apk = directory / (str(n) + ".apk")
                apk.write_bytes(b"old")
                apks.append(dict(driver.env.binding(apk), package=package))
            path = directory / "artifacts.json"
            path.write_text(json.dumps({"version": 1, "build_profile": "input-process", "apks": apks}))
            driver.checked_apks(path)
            Path(apks[1]["path"]).write_bytes(b"new")
            with self.assertRaises(driver.env.EnvironmentRefused):
                driver.checked_apks(path)

    def test_passed_label_without_owner_and_bound_records_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "result-v1.json"
            path.write_text(json.dumps({"version": 1, "phase": "build", "passed": True}))
            with self.assertRaises(driver.VerificationRefused):
                driver.qualified_build(path)

    def test_boolean_returncode_cannot_qualify_an_owner(self):
        self.assertFalse(driver.owner_ok(dict(status="child_exited", worker_returncode=False,
            cleanup_complete=True, output_capture_complete=True)))

    def test_all_component_dispatches_fit_fixed_sdk_contract(self):
        labels = set()
        for index, name in enumerate(driver.CLASSES):
            command, label, seconds, cap = driver.instrumentation_dispatch(index)
            self.assertRegex(label, re.compile(r"^[a-z][a-z0-9_-]{0,47}$"))
            self.assertNotIn(label, labels)
            labels.add(label)
            self.assertEqual(command[:5], ["exec-out", "am", "instrument", "--user", "0"])
            self.assertIn("org.locallore.app." + name, command)
            self.assertEqual(command[-1], driver.APP + ".test/androidx.test.runner.AndroidJUnitRunner")
            self.assertEqual((seconds, cap), (180, 262144))
        for bad in (-1, 3, True):
            with self.assertRaises(driver.VerificationRefused):
                driver.instrumentation_dispatch(bad)

    def test_aapt_namespace_forms_preserve_exact_target_and_runner_guards(self):
        for namespace in ("android", "http://schemas.android.com/apk/res/android"):
            with self.subTest(namespace=namespace):
                raw = (f'  A: {namespace}:name(0x01010003)="androidx.test.runner.AndroidJUnitRunner"\n'
                       f'  A: {namespace}:targetPackage(0x01010021)="{driver.APP}"\n').encode()
                driver.validate_test_manifest(raw)
                for bad in (raw.replace(driver.APP.encode(), b"other.app"), raw + raw,
                            raw.replace(b"AndroidJUnitRunner", b"OtherRunner")):
                    with self.assertRaises(driver.VerificationRefused):
                        driver.validate_test_manifest(bad)

    def test_worker_source_drift_refuses_before_build_dispatch(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            snapshot = out / "sources.json"
            snapshot.write_text(json.dumps({"input": "before"}))
            request = dict(phase="build", out=root, sdk=root, java=root, build=None, running=None,
                proposal=None, server=None, powershell=None, inputs=[], sources=driver.env.binding(snapshot),
                driver_sha256=driver.env.digest(Path(driver.__file__)))
            path = out / "request-v1.json"
            path.write_text(json.dumps(request))
            data = (str(path) + "\n" + driver.env.digest(path) + "\n").encode()
            with patch.object(sys, "argv", ["driver", "_worker"]), \
                 patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data))), \
                 patch.object(driver, "source_map", return_value={"input": "after"}), \
                 patch.object(driver, "build_worker") as build:
                with self.assertRaises(driver.VerificationRefused):
                    driver.main()
                build.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_isolated_interpreter_can_load_versioned_driver(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            raw = driver.run_command(out, "isolated-help", [sys.executable, "-I", "-B",
                str(Path(driver.__file__)), "--help"], out, dict(os.environ))
            self.assertIn(b"components", raw)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_child_bytes_survive_ctrl_z_nul_non_ascii_and_lf(self):
        payload = bytes(range(256)) + b"\x1a\n\x00\xffEND\n"
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            command = [sys.executable, "-I", "-B", "-c",
                       "import sys;sys.stdout.buffer.write(bytes.fromhex('" + payload.hex() + "'))"]
            actual = driver.run_command(out, "binary-child", command, out, dict(os.environ))
            self.assertEqual(actual, payload)
            record = json.loads((out / "binary-child.json").read_text())
            self.assertEqual(record["stdout"]["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(record["stderr"]["bytes"], 0)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_child_failure_is_retained_and_not_passed(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            with self.assertRaises(driver.VerificationRefused):
                driver.run_command(out, "failed-child", [sys.executable, "-I", "-B", "-c",
                    "import sys;sys.stdout.buffer.write(b'partial');sys.exit(7)"], out, dict(os.environ))
            self.assertEqual((out / "failed-child.stdout.raw").read_bytes(), b"partial")
            self.assertEqual(json.loads((out / "failed-child.json").read_text())["returncode"], 7)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_existing_capture_refuses_before_child_spawn(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            (out / "existing.stdout.raw").write_bytes(b"keep")
            with patch.object(driver.subprocess, "Popen") as spawn:
                with self.assertRaises(FileExistsError):
                    driver.run_command(out, "existing", [sys.executable], out, dict(os.environ))
                spawn.assert_not_called()
            self.assertEqual((out / "existing.stdout.raw").read_bytes(), b"keep")

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_output_overflow_is_bounded_and_cannot_pass(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            with patch.object(driver, "MAX_COMMAND_BYTES", 512):
                with self.assertRaises(driver.VerificationRefused):
                    driver.run_command(out, "overflow", [sys.executable, "-I", "-B", "-c",
                        "import sys;sys.stdout.buffer.write(b'x'*1000000)"], out, dict(os.environ))
            record = json.loads((out / "overflow.json").read_text())
            self.assertTrue(record["output_limit"])
            self.assertLessEqual(record["stdout"]["bytes"] + record["stderr"]["bytes"], 512)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_deadline_refuses_even_when_child_finishes_zero_during_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            child = SimpleNamespace(stdout=io.BytesIO(b"done"), stderr=io.BytesIO(b""),
                                    poll=lambda: 0, wait=lambda timeout: 0, returncode=0)
            with patch.object(driver.subprocess, "Popen", return_value=child), \
                 patch.object(driver.time, "monotonic", side_effect=[0, 601]):
                with self.assertRaises(driver.VerificationRefused):
                    driver.run_command(out, "late", ["fixed-test-child"], out, dict(os.environ))
            record = json.loads((out / "late.json").read_text())
            self.assertEqual(record["returncode"], 0)
            self.assertTrue(record["timed_out"])

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_cleanup_failure_and_source_drift_cannot_publish_success(self):
        for cleanup, after in ((False, {"input": "same"}), (True, {"input": "changed"})):
            with self.subTest(cleanup=cleanup, after=after), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                request = dict(phase="build", out=str(out), sdk=root, java=root, build=None,
                               running=None, server=None, powershell=None)
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=cleanup,
                             output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                with patch.object(driver, "input_bindings", return_value=[]), \
                     patch.object(driver, "source_map", side_effect=[{"input": "same"}, after]), \
                     patch.object(driver.env, "supervise", return_value=owner):
                    with self.assertRaises(driver.VerificationRefused):
                        driver.supervise(request)
                self.assertEqual(json.loads((out / "owner-result-v1.json").read_text()), owner)
                result = json.loads((out / "result-v1.json").read_text())
                self.assertFalse(result["passed"])
                self.assertNotIn("artifacts", result)


def synthetic_regression_run(name, methods):
    """Original synthetic AndroidJUnitRunner bytes, never an execution receipt."""
    cls = "org.locallore.app." + name
    parts = []
    for index, method in enumerate(methods, 1):
        for code in (1, 0):
            parts.append(f"INSTRUMENTATION_STATUS: class={cls}\nINSTRUMENTATION_STATUS: test={method}\n"
                         f"INSTRUMENTATION_STATUS: current={index}\nINSTRUMENTATION_STATUS: numtests={len(methods)}\n"
                         f"INSTRUMENTATION_STATUS_CODE: {code}\n")
    noun = "test" if len(methods) == 1 else "tests"
    parts.append(f"INSTRUMENTATION_RESULT: stream=\n\nTime: 1.0\n\nOK ({len(methods)} {noun})\n\nINSTRUMENTATION_CODE: -1\n")
    return "".join(parts).encode()


class RegressionPhaseTests(unittest.TestCase):
    def fixture(self, out):
        from benchmarks.android_instrumentation_evidence import validate_instrumentation
        (out / "clients").mkdir()
        results = []
        for index, (name, methods) in enumerate(zip(driver.REGRESSION_CLASSES, driver.REGRESSION_METHODS), 1):
            raw = synthetic_regression_run(name, methods)
            (out / (name + ".stdout.raw")).write_bytes(raw)
            results.append(validate_instrumentation(raw, "org.locallore.app." + name, list(methods)))
            stem = out / "clients" / ("command-%04d" % index)
            stem.with_suffix(".stdout.bin").write_bytes(raw)
            driver.env.create_json(stem.with_suffix(".json"), {"version": 1, "index": index,
                "label": "instrument-" + str(index - 1), "status": "completed", "returncode": 0,
                "cleanup_complete": True, "stdout_bytes": len(raw), "stdout_sha256": hashlib.sha256(raw).hexdigest(),
                "stderr_bytes": 0})
        return {"version": 1, "phase": "regression", "results": results, "clients": 18,
                "clients_clean": True, "method_count": 89, "external_controller_case_executed": False}

    def test_frozen_broad_roster_matches_actual_sources_without_component_substitution(self):
        from benchmarks.android_instrumentation_evidence import test_roster
        self.assertEqual(driver.REGRESSION_VERSION, 1)
        self.assertEqual(len(driver.REGRESSION_CLASSES), 18)
        self.assertEqual(tuple(map(len, driver.REGRESSION_METHODS)), (12, 1, 10, 1, 2, 6, 8, 5, 9, 8, 7, 5, 2, 3, 3, 2, 2, 3))
        self.assertEqual(sum(map(len, driver.REGRESSION_METHODS)), 89)
        self.assertEqual(len(set(driver.REGRESSION_CLASSES)), 18)
        self.assertTrue(set(driver.CLASSES).isdisjoint(driver.REGRESSION_CLASSES))
        self.assertEqual(sum(map(len, driver.EXPECTED_METHODS)), 10)
        for name, methods in zip(driver.REGRESSION_CLASSES, driver.REGRESSION_METHODS):
            path = driver.ROOT / "apps/android/app/src/androidTest/java/org/locallore/app" / (name + ".kt")
            self.assertEqual(test_roster(path), list(methods), name)

    def test_all_eighteen_dispatches_are_fixed_classes_with_unchanged_bounds(self):
        for index, name in enumerate(driver.REGRESSION_CLASSES):
            command, label, seconds, cap = driver.regression_dispatch(index)
            self.assertEqual(command, ["exec-out", "am", "instrument", "--user", "0", "-w", "-r", "-e", "class",
                "org.locallore.app." + name, driver.APP + ".test/androidx.test.runner.AndroidJUnitRunner"])
            self.assertEqual((label, seconds, cap), ("instrument-" + str(index), 180, 262144))
        for bad in (-1, 18, True, 1.0, "1", None):
            with self.subTest(bad=bad), self.assertRaises(driver.VerificationRefused):
                driver.regression_dispatch(bad)

    def test_complete_synthetic_regression_requires_both_raw_copies(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            before = copy.deepcopy(record)
            driver.validate_regression_record(record, out)
            self.assertEqual(record, before)
            with self.assertRaises(driver.VerificationRefused):
                driver.validate_component_record(record, out)

    def test_closed_version_phase_counts_types_and_exact_order(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            variants = []
            for key, value in (("version", True), ("version", 2), ("phase", "components"), ("method_count", True),
                               ("method_count", 88), ("clients", True), ("clients_clean", False),
                               ("external_controller_case_executed", True), ("results", {})):
                variants.append(dict(record, **{key: value}))
            variants += [dict(record, extra=True), {k: v for k, v in record.items() if k != "phase"}]
            for mutation in ("drop", "extra", "reorder", "method", "class"):
                changed = copy.deepcopy(record)
                if mutation == "drop": changed["results"].pop()
                if mutation == "extra": changed["results"].append(changed["results"][0])
                if mutation == "reorder": changed["results"].reverse()
                if mutation == "method": changed["results"][0]["methods"].reverse()
                if mutation == "class": changed["results"][0]["class"] = "org.locallore.app.OtherTest"
                variants.append(changed)
            for changed in variants:
                with self.subTest(changed={k: v for k, v in changed.items() if k != "results"}), \
                     self.assertRaises(driver.VerificationRefused):
                    driver.validate_regression_record(changed, out)

    def test_bad_partial_extra_skipped_or_foreign_raw_cannot_be_hidden_by_passed_summary(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            name, methods = driver.REGRESSION_CLASSES[0], driver.REGRESSION_METHODS[0]
            path = out / (name + ".stdout.raw")
            raw = path.read_bytes()
            variants = [synthetic_regression_run(name, methods[:-1]), synthetic_regression_run(name, (*methods, "unselected")),
                synthetic_regression_run(name, (methods[0], *methods[:-1])),
                raw.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -3", 1),
                raw.replace(name.encode(), b"OtherTest", 1), raw + b"INSTRUMENTATION_CODE: -1\n"]
            for changed in variants:
                path.write_bytes(changed)
                with self.assertRaises(driver.VerificationRefused):
                    driver.validate_regression_record(record, out)
            path.write_bytes(raw)
            driver.validate_regression_record(record, out)

    def test_valid_but_different_client_copy_duplicate_missing_order_or_unknown_client_refuses(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            record = self.fixture(out)
            path = out / "clients/command-0001.json"
            original = driver.env.read_json(path)
            raw_path = path.with_suffix(".stdout.bin")
            raw = raw_path.read_bytes()
            # A valid alternative LF/CRLF rendering independently parses, but is not the retained class copy.
            changed = raw.replace(b"\n", b"\r\n")
            raw_path.write_bytes(changed)
            path.write_text(json.dumps(dict(original, stdout_bytes=len(changed), stdout_sha256=hashlib.sha256(changed).hexdigest())))
            with self.assertRaisesRegex(driver.VerificationRefused, "client_copy"):
                driver.validate_regression_record(record, out)
            raw_path.write_bytes(raw)
            for change in ({"label": "instrument-1"}, {"label": "unselected-client"}, {"returncode": False},
                           {"cleanup_complete": False}, {"stderr_bytes": 1}, {"stdout_sha256": "0" * 64}, {"extra": 1}):
                path.write_text(json.dumps(dict(original, **change)))
                with self.subTest(change=change), self.assertRaises(driver.VerificationRefused):
                    driver.validate_regression_record(record, out)
            path.write_text(json.dumps(original))
            extra = out / "clients/unlisted.json"
            extra.write_bytes(b"{}")
            with self.assertRaisesRegex(driver.VerificationRefused, "client_extra"):
                driver.validate_regression_record(record, out)
            extra.unlink()
            with self.assertRaisesRegex(driver.VerificationRefused, "client_order"):
                driver.validate_regression_record(dict(record, clients=17), out)

    def test_regression_worker_reuses_fresh_guest_admission_and_fixed_eighteen_calls(self):
        self.run_mock_worker()

    def test_existing_package_refuses_before_any_install_or_instrumentation(self):
        for package in driver.PACKAGES:
            with self.subTest(package=package):
                self.run_mock_worker(existing=package)

    def test_lease_failure_or_source_drift_stops_before_sdk_instantiation(self):
        for failure in ("owner", "source"):
            with self.subTest(failure=failure):
                self.run_mock_worker(early_failure=failure)

    def run_mock_worker(self, existing=None, early_failure=None):
        from benchmarks import android_process_client as client
        calls = []
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            apks = []
            for index, package in enumerate(driver.PACKAGES):
                path = out / (str(index) + ".apk")
                path.write_bytes(bytes([index]))
                apks.append(dict(driver.env.binding(path), package=package))
            live = SimpleNamespace(descriptor=dict(avd_name=driver.env.NAME, serial="emulator-5592", console_port=5592,
                guest_boot_verified=False, launcher={}), check=lambda: None)
            if early_failure == "owner":
                def broken(): raise driver.VerificationRefused("owner_closed")
                live.check = broken
            class FakeCapture:
                count, clean = 0, True
                def __init__(self, *args): calls.append(("construct", args[1]))
                def check_server(self): pass
                def capture(self, *args): return b"emulator-5592 device transport_id:7\n"
                def shell(self, args, label, seconds, cap):
                    calls.append(("shell", args))
                    if args == ["getprop", "sys.boot_completed"]: return b"1\n"
                    if args == ["getprop", "ro.build.version.sdk"]: return b"35\n"
                    if args == ["getprop", "ro.product.cpu.abi"]: return b"x86_64\n"
                    if args == ["am", "get-current-user"]: return b"0\n"
                    if args[:4] == ["cmd", "package", "list", "packages"]:
                        return b"package:present\n" if args[-1] == existing else b""
                    if args[:3] == ["cmd", "package", "path"]: return ("package:/data/app/" + str(driver.PACKAGES.index(args[-1])) + "/base.apk\n").encode()
                    if args[0] == "sha256sum": return (apks[int(args[1].split("/")[-2])]["sha256"] + "  base.apk\n").encode()
                    raise AssertionError(args)
                def adb(self, args, label, seconds, cap=131072):
                    calls.append(("adb", args, label, seconds, cap))
                    if args[0] == "install": return b"Success\n"
                    index = int(label.split("-")[1])
                    return synthetic_regression_run(driver.REGRESSION_CLASSES[index], driver.REGRESSION_METHODS[index])
            request = dict(build="build", running=str(out / "running"), proposal="proposal", sdk=str(out),
                           powershell=str(out / "powershell.exe"), server="server", sources={"path": "sources"})
            digest = driver.env.digest
            with patch.object(driver, "qualified_build", return_value={"apks": apks}), \
                 patch.object(driver.env, "open_live_owner", return_value=live), \
                 patch.object(driver.env, "digest", side_effect=lambda path: "hash" if str(path) == request["running"] else digest(path)), \
                 patch.object(driver.env, "read_json", return_value={}), \
                 patch.object(driver, "source_map", return_value={"changed": True} if early_failure == "source" else {}), \
                 patch.object(client, "SdkCapture", FakeCapture):
                if existing or early_failure:
                    with self.assertRaises(driver.VerificationRefused): driver.regression_worker(request, out)
                else:
                    driver.regression_worker(request, out)
            adb = [c for c in calls if c[0] == "adb"]
            if existing or early_failure:
                self.assertEqual(adb, [])
                if early_failure: self.assertEqual(calls, [])
                self.assertFalse((out / "regression-v1.json").exists())
            else:
                self.assertEqual(calls[0], ("construct", 850))
                self.assertEqual([c[1][0] for c in adb[:3]], ["install"] * 3)
                self.assertEqual(len(adb), 21)
                for index, call in enumerate(adb[3:]): self.assertEqual(call[1:], driver.regression_dispatch(index))
                result = json.loads((out / "regression-v1.json").read_text())
                self.assertEqual((result["phase"], result["method_count"], len(result["results"])), ("regression", 89, 18))
                self.assertFalse((out / "components-v1.json").exists())
                absent = [c[1][-1] for c in calls if c[0] == "shell" and c[1][:4] == ["cmd", "package", "list", "packages"]]
                self.assertEqual(absent, list(driver.PACKAGES))

    def test_cli_only_closed_phase_accepts_regression_without_selector(self):
        args = ["regression", "--out", "unused", "--sdk", "sdk", "--build", "build", "--running", "running",
                "--proposal", "proposal", "--server", "server", "--powershell", "powershell"]
        with patch.object(driver, "supervise") as run, patch("sys.stdout", io.StringIO()):
            self.assertEqual(driver.main(args), 0)
        self.assertEqual(run.call_args.args[0]["phase"], "regression")
        for extra in (["--class", "OtherTest"], ["--test", "method"]):
            with patch.object(driver, "supervise") as run, patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
                driver.main(args + extra)
            run.assert_not_called()

    def test_worker_admission_is_closed_and_preserves_source_input_guards(self):
        request = dict(phase="regression", out="out", sdk="sdk", java=None, build="build", running="running",
            proposal="proposal", server="server", powershell="powershell", inputs=["bound"], sources={"path": "sources"},
            driver_sha256="hash")
        with patch.object(driver.env, "digest", return_value="hash"), patch.object(driver.env, "check_binding"), \
             patch.object(driver.env, "read_json", return_value={"source": "same"}), \
             patch.object(driver, "source_map", return_value={"source": "same"}), \
             patch.object(driver, "input_bindings", return_value=["bound"]):
            driver.admit_worker(request)
            for delta in ({"phase": "regression-v2"}, {"class": "unselected"}, {"driver_sha256": "changed"},
                          {"inputs": []}, {"sources": {"path": "sources"}, "phase": "server"}):
                with self.subTest(delta=delta), self.assertRaises(driver.VerificationRefused):
                    driver.admit_worker(dict(request, **delta))

    def test_external_gate_refuses_regression_even_if_passed(self):
        from benchmarks import android_external_controller as external
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "result-v1.json"
            path.write_text(json.dumps(dict(version=1, phase="regression", passed=True, owner={}, owner_record={},
                request={}, sources_before={}, sources_after={}, regression={})))
            with self.assertRaises(external.ExternalRefused): external.qualified_gate(path, "build")

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_regression_parent_persists_owner_before_deep_validation_and_rejects_unknown_cleanup(self):
        for known in (True, False):
            with self.subTest(known=known), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                request = dict(phase="regression", out=str(out), sdk=root, java=None, build="build",
                               running="running", proposal="proposal", server="server", powershell="powershell")
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=known,
                             output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                def supervise(*_args):
                    driver.env.create_json(out / "regression-v1.json", {"not": "qualified"})
                    return owner
                def validate(*_args):
                    self.assertEqual(json.loads((out / "owner-result-v1.json").read_text()), owner)
                    raise driver.VerificationRefused("bad_raw_copy")
                with patch.object(driver, "input_bindings", return_value=[]), \
                     patch.object(driver, "source_map", return_value={"input": "same"}), \
                     patch.object(driver.env, "supervise", side_effect=supervise), \
                     patch.object(driver, "validate_regression_record", side_effect=validate) as deep:
                    with self.assertRaises(driver.VerificationRefused): driver.supervise(request)
                self.assertEqual(deep.call_count, int(known))
                result = json.loads((out / "result-v1.json").read_text())
                self.assertFalse(result["passed"])
                self.assertNotIn("components", result)
                self.assertNotIn("artifacts", result)
                if known: self.assertEqual(result["regression"]["path"], str(out / "regression-v1.json"))


if __name__ == "__main__":
    unittest.main()
