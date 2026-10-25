"""Offline launcher tests; synthetic code wheels, no native imports or devices.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile
from scripts.tests import test_llguidance_oracle as checker

SPEC = importlib.util.spec_from_file_location(
    "llguidance_launcher_test", Path(__file__).resolve().parents[1] / "llguidance_oracle.py")
s = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s)


def wheel_bytes(extra=None, metadata=None):
    files = {
        s.DIST + "/METADATA": metadata or b"Name: llguidance\nVersion: 1.3.0\nRequires-Python: >=3.9\nLicense-Expression: MIT\n",
        s.DIST + "/WHEEL": b"Wheel-Version: 1.0\nTag: cp39-abi3-win_amd64\n",
        s.DIST + "/licenses/LICENSE": b"MIT License\nOriginal test fixture only",
        "llguidance/__init__.py": b"raise RuntimeError('MUST NEVER IMPORT')\n",
        "llguidance/_lib.pyd": b"synthetic, never executable",
    }
    files.update(extra or {})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    raw = stream.getvalue()
    # ZipInfo normalizes Windows separators when creating entries; construct
    # the adversarial archive name in both ZIP headers after serialization.
    if extra and "llguidance\\bad" in extra:
        raw = raw.replace(b"llguidance/bad", b"llguidance\\bad")
    return raw


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.platform = patch.object(s, "platform_check")
        self.platform.start()
        self.addCleanup(self.platform.stop)

    @contextlib.contextmanager
    def wheel(self, raw=None):
        raw = wheel_bytes() if raw is None else raw
        path = self.root / s.WHEEL_NAME
        path.write_bytes(raw)
        with patch.multiple(s, WHEEL_BYTES=len(raw), WHEEL_SHA256=s.digest(raw)):
            yield path

    def test_provision_and_reverify_without_import(self):
        with self.wheel() as wheel:
            runtime = self.root / "runtime"
            result = s.provision(wheel, runtime)
            self.assertEqual(result["status"], "provisioned")
            self.assertEqual(s.verify_runtime(runtime), runtime / "lib")
            self.assertTrue((runtime / "lib" / s.DIST / "licenses/LICENSE").is_file())

    def test_provision_is_create_only(self):
        with self.wheel() as wheel:
            runtime = self.root / "runtime"
            runtime.mkdir()
            sentinel = runtime / "keep"
            sentinel.write_bytes(b"untouched")
            with self.assertRaises(FileExistsError):
                s.provision(wheel, runtime)
            self.assertEqual(sentinel.read_bytes(), b"untouched")

    def test_hash_checked_before_zip(self):
        with self.wheel() as wheel:
            wheel.write_bytes(b"x" * wheel.stat().st_size)
            with self.assertRaisesRegex(s.OracleError, "wheel_hash"), patch.object(s.zipfile, "ZipFile") as zipper:
                s.wheel_files(wheel)
            zipper.assert_not_called()

    def test_wheel_size_bound(self):
        with self.wheel() as wheel:
            wheel.write_bytes(b"x")
            with self.assertRaisesRegex(s.OracleError, "wheel_size"):
                s.wheel_files(wheel)

    def test_unexpected_filename(self):
        with self.wheel() as wheel:
            with self.assertRaisesRegex(s.OracleError, "wheel_filename"):
                s.provision(wheel.with_name("other.whl"), self.root / "runtime")

    def test_dependency_metadata_rejected(self):
        raw = wheel_bytes(metadata=b"Name: llguidance\nVersion: 1.3.0\nRequires-Python: >=3.9\nLicense-Expression: MIT\nRequires-Dist: network-helper\n")
        with self.wheel(raw) as wheel:
            with self.assertRaisesRegex(s.OracleError, "wheel_metadata"):
                s.wheel_files(wheel)

    def test_path_traversal_and_foreign_modules_rejected(self):
        for name in ("../outside", "/absolute", "llguidance/../bad", "llguidance/a:stream", "llguidance\\bad", "sitecustomize.py"):
            with self.subTest(name=name), self.wheel(wheel_bytes({name: b"bad"})) as wheel:
                with self.assertRaisesRegex(s.OracleError, "wheel_layout"):
                    s.wheel_files(wheel)

    def test_runtime_tamper_and_added_file_rejected(self):
        with self.wheel() as wheel:
            for mutation in ("tamper", "extra", "missing"):
                with self.subTest(mutation=mutation):
                    runtime = self.root / mutation
                    s.provision(wheel, runtime)
                    target = runtime / "lib/llguidance/_lib.pyd"
                    if mutation == "tamper":
                        target.write_bytes(b"changed")
                    elif mutation == "extra":
                        (runtime / "lib/llguidance/extra.py").write_bytes(b"extra")
                    else:
                        target.unlink()
                    with self.assertRaisesRegex(s.OracleError, "runtime_integrity"):
                        s.verify_runtime(runtime)

    def test_repository_cannot_be_runtime_or_evidence(self):
        with self.assertRaisesRegex(s.OracleError, "private_directory_required"):
            s.private_path(s.ROOT / "private-test")

    def test_missing_barrier_prevents_child_or_native_action(self):
        fake = SimpleNamespace(buffer=io.BytesIO(b"wrong"))
        with patch.object(s.sys, "stdin", fake), patch.object(s.subprocess, "call") as child, patch.object(s, "verify_runtime") as verify:
            self.assertEqual(s.worker("check", self.root / "evidence", self.root / "runtime"), 2)
        child.assert_not_called()
        verify.assert_not_called()

    def test_run_owns_each_stage_and_retains_only_fixed_reports(self):
        with self.wheel() as wheel:
            runtime = self.root / "runtime"
            s.provision(wheel, runtime)
            output = self.root / "evidence"
            calls = []
            corpus = checker.encoded(checker.corpus())
            report = checker.o.run_oracle(corpus, checker.FakeBackend())
            report["native"] = True  # Simulated child wire; no native backend is constructed.
            def runner(command, **kwargs):
                calls.append((command, kwargs))
                stage = command[-3]
                data = b"" if stage == "build" else corpus if stage == "export" else json.dumps(report).encode()
                return SimpleNamespace(status="completed", elapsed_ms=1, returncode=0, cleanup_complete=True, stdout=data, stderr_bytes=0)
            with patch.object(s, "ROOT", self.root / "repo"):
                s.ROOT.mkdir()
                for name in ("Cargo.lock", "crates/locallore/Cargo.toml", "crates/locallore/examples/llguidance_cases.rs", "benchmarks/llguidance_oracle.py", "scripts/llguidance_oracle.py", "fixtures/llguidance_escape_reductions.json"):
                    target = s.ROOT / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(b"synthetic source")
                result = s.run(runtime, output, runner)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(len(calls), 3)
            for command, kwargs in calls:
                self.assertEqual(command[1:4], ["-I", "-S", "-B"])
                self.assertEqual(kwargs["request"], s.BARRIER)
                self.assertLessEqual(kwargs["deadline"], 180)
                self.assertEqual(kwargs["max_output"], 262144)
            self.assertEqual(json.loads((output / "run.json").read_bytes())["status"], "passed")

    def test_report_is_closed_complete_and_bound_to_corpus(self):
        corpus = checker.encoded(checker.corpus())
        report = checker.o.run_oracle(corpus, checker.FakeBackend())
        report["native"] = True  # Wire validation fixture only.
        self.assertTrue(s.validate_report(report, corpus))
        self.assertFalse(s.validate_report({"native": True, "status": "passed"}, corpus))
        changes = []
        for key, bad in (("version", True), ("scope", "wrong"), ("native", False),
                         ("corpus_sha256", "0" * 64), ("sample_count", True), ("cases", []),
                         ("refusals", True), ("status", "mismatch"), ("private", "PRIVATE")):
            value = copy.deepcopy(report)
            value[key] = bad
            changes.append(value)
        value = copy.deepcopy(report)
        value["controls"]["valid_complete"] = 1
        changes.append(value)
        for key, bad in (("index", True), ("sha256", "0" * 64), ("bytes", True),
                         ("checked_bytes", 0), ("outcome", "INCOMPLETE"), ("accepted", 1),
                         ("private", "PRIVATE")):
            value = copy.deepcopy(report)
            value["cases"][0]["positives"][0][key] = bad
            changes.append(value)
        for value in changes:
            self.assertFalse(s.validate_report(value, corpus))

    def test_failures_are_sanitized(self):
        capture = io.StringIO()
        with patch.object(s, "provision", side_effect=OSError("PRIVATE_PATH_OR_ERROR")), contextlib.redirect_stdout(capture):
            code = s.main(["provision", "--wheel", "unused", "--runtime", "unused"])
        self.assertEqual(code, 2)
        self.assertNotIn("PRIVATE", capture.getvalue())
        self.assertEqual(json.loads(capture.getvalue())["reason"], "local_tool_failure")

    def test_argument_errors_and_duplicates_never_echo_private_arguments(self):
        capture, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(errors):
            code = s.main(["run", "--runtime", "PRIVATE_PATH", "--output", "PRIVATE_OTHER", "--PRIVATE_CANARY"])
        self.assertEqual(code, 2)
        self.assertEqual(errors.getvalue(), "")
        self.assertNotIn("PRIVATE", capture.getvalue())
        self.assertEqual(json.loads(capture.getvalue())["reason"], "arguments")
        with self.assertRaises(ValueError):
            json.loads('{"status":"failed","status":"passed"}', object_pairs_hook=s.closed_pairs)

    def test_cleanup_failure_stops_before_export(self):
        with self.wheel() as wheel:
            runtime, output = self.root / "runtime", self.root / "evidence"
            s.provision(wheel, runtime)
            calls = []
            def runner(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(status="cleanup_failed", elapsed_ms=1, returncode=0,
                                       cleanup_complete=False, stdout=b"", stderr_bytes=0)
            report = s.run(runtime, output, runner)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(len(calls), 1)
            self.assertFalse((output / "corpus.json").exists())

    def test_reduction_fixture_is_original_bounded_and_keeps_nested_counterexample(self):
        raw = (s.ROOT / "fixtures/llguidance_escape_reductions.json").read_bytes()
        corpus = checker.o.validate_corpus(raw)
        self.assertEqual(len(corpus["cases"]), 16)
        self.assertEqual(sum(len(c[k]) for c in corpus["cases"] for k in ("positives", "negatives")), 40)
        self.assertEqual(corpus["refusals"], [])
        for case in corpus["cases"][:-1]:
            self.assertEqual(json.loads(case["schema_json"])["const"], json.loads(case["positives"][0]["json"]))
        full = next(c for c in corpus["cases"] if c["id"] == "full-escaped")
        nested = corpus["cases"][-1]
        literal = json.loads(full["schema_json"])["const"]
        self.assertEqual(nested["id"], "nested-original")
        self.assertEqual(json.loads(nested["schema_json"])["properties"]["commands"]["items"]["oneOf"][0]["properties"]["text"]["const"], literal)
        self.assertEqual(json.loads(nested["positives"][0]["json"])["commands"][0]["text"], literal)

    def test_reduction_mode_runs_only_owned_checker_and_labels_source(self):
        with self.wheel() as wheel:
            runtime, output = self.root / "runtime", self.root / "evidence"
            s.provision(wheel, runtime)
            raw = (s.ROOT / "fixtures/llguidance_escape_reductions.json").read_bytes()
            corpus = json.loads(raw)
            accepted = tuple(sample["json"].encode() for c in corpus["cases"] for sample in c["positives"])
            report = checker.o.run_oracle(raw, checker.FakeBackend(accepted=accepted))
            report["native"] = True  # Simulated report wire only; no native import.
            calls = []
            def runner(command, **kwargs):
                calls.append(command)
                self.assertEqual(kwargs["request"], s.BARRIER)
                return SimpleNamespace(status="completed", elapsed_ms=1, returncode=0,
                                       cleanup_complete=True, stdout=json.dumps(report).encode(), stderr_bytes=0)
            result = s.run(runtime, output, runner, reductions=True)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["corpus_source"], "reduction_fixture")
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][-3], "check")
            self.assertEqual((output / "corpus.json").read_bytes(), raw)

    def test_literal_probe_rejects_shortcut_report_and_unclean_worker(self):
        with self.wheel() as wheel:
            runtime = self.root / "runtime"
            s.provision(wheel, runtime)
            for status, clean in (("completed", True), ("cleanup_failed", False)):
                output = self.root / status
                def runner(command, **kwargs):
                    self.assertEqual(command[-3], "literal")
                    self.assertEqual(kwargs["request"], s.BARRIER)
                    self.assertEqual(kwargs["deadline"], 60)
                    self.assertEqual(kwargs["max_output"], 131072)
                    return SimpleNamespace(status=status, elapsed_ms=1, returncode=0, cleanup_complete=clean,
                                           stdout=b'{"version":1,"native":true,"status":"observed"}', stderr_bytes=0)
                report = s.literal_probe(runtime, output, runner)
                self.assertEqual(report["status"], "failed")
                self.assertFalse((output / "probe.json").exists())
                self.assertTrue((output / "rejected-probe.json").exists())


if __name__ == "__main__":
    unittest.main()
