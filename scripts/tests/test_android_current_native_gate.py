"""Original synthetic native-gate evidence; no SDK or native owner is observed.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_external_controller as external
from benchmarks.android_instrumentation_evidence import validate_instrumentation
from scripts.tests import test_android_external_controller as external_fixture
from scripts.tests import test_android_external_current_creation as current_fixture
from scripts.tests import test_android_process_verification as phase_fixture


def write_json(path, value):
    path.write_bytes(external.environment.encoded(value))


def native_gate(root, caller):
    """Full original ten-method gate, not a passed-label substitute."""
    root.mkdir()
    (root / "clients").mkdir()
    results, captures = [], [("adb-server", b'{"original_synthetic_listener":1}\n')]
    for index, (name, methods) in enumerate(zip(external.driver.CLASSES, external.driver.EXPECTED_METHODS)):
        raw = phase_fixture.synthetic_regression_run(name, methods)
        (root / (name + ".stdout.raw")).write_bytes(raw)
        results.append(validate_instrumentation(raw, "org.locallore.app." + name, list(methods)))
        captures.append(("instrument-" + str(index), raw))
    for index, (label, raw) in enumerate(captures, 1):
        stem = root / "clients" / ("command-%04d" % index)
        stem.with_suffix(".stdout.bin").write_bytes(raw)
        write_json(stem.with_suffix(".json"), dict(version=2, index=index, label=label,
            status="completed", returncode=0, cleanup_complete=True, stdout_bytes=len(raw),
            stdout_sha256=hashlib.sha256(raw).hexdigest(), stderr_bytes=0,
            elapsed_ms=7, effective_deadline_ms=15000 if index == 1 else 180000))
    for name in ("sources-before-v1.json", "sources-after-v1.json"):
        write_json(root / name, {})
    request = dict(phase="components", out=str(root), build=caller["build"], inputs=[],
        sources=external.environment.binding(root / "sources-before-v1.json"),
        sdk=caller["sdk"], powershell=caller["powershell"],
        running=str(root / "original-native-running.json"), proposal=str(root / "original-native-proposal.json"))
    write_json(root / "request-v1.json", request)
    raw = b"worker_completed\n"
    (root / "owner-stdout-v1.bin").write_bytes(raw)
    (root / "owner-stderr-v1.bin").write_bytes(b"")
    owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=True,
        output_capture_complete=True, elapsed_ms=100, stdout_bytes=len(raw), stderr_bytes=0)
    write_json(root / "owner-result-v1.json", owner)
    components = dict(version=1, results=results, clients=len(captures), clients_clean=True,
                      method_count=10, external_controller_case_executed=False)
    write_json(root / "components-v1.json", components)
    record = dict(version=1, phase="components", passed=True, owner=owner,
        **{key: external.environment.binding(root / name) for key, name in (
            ("owner_record", "owner-result-v1.json"), ("request", "request-v1.json"),
            ("sources_before", "sources-before-v1.json"), ("sources_after", "sources-after-v1.json"),
            ("components", "components-v1.json"))})
    write_json(root / "result-v1.json", record)
    return SimpleNamespace(out=root, path=root / "result-v1.json", request=request, record=record)


def downgrade(gate, index):
    path = gate.out / "clients" / ("command-%04d.json" % index)
    row = json.loads(path.read_bytes())
    row["version"] = 1
    del row["elapsed_ms"]
    del row["effective_deadline_ms"]
    write_json(path, row)


def originals(gate):
    """No timing edit may silently substitute a runner, owner, or raw capture."""
    return {path.relative_to(gate.out).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in gate.out.rglob("*") if path.is_file()
            and not (path.parent.name == "clients" and path.suffix == ".json")}


@contextmanager
def admission_boundaries(expected=None):
    # These are existing OS/tool/artifact/source identity boundaries. Gate,
    # current wrapper, deep execution, rosters, raw and client validators run.
    with ExitStack() as stack:
        stack.enter_context(patch.object(external, "admit"))
        stack.enter_context(patch.object(external.driver, "admit_worker"))
        stack.enter_context(patch.object(external.driver, "input_bindings", return_value=[]))
        stack.enter_context(patch.object(external.driver, "source_map", return_value={}))
        stack.enter_context(patch.object(external.driver, "qualified_build", return_value={}))
        if expected is not None:
            stack.enter_context(patch.object(external, "expected_pins", return_value=expected))
        yield


class ReachedSession(RuntimeError):
    """Sentinel: stop before any constructor/native/SDK observation."""


class CurrentNativeGateTests(unittest.TestCase):
    def worker_fixture(self, root):
        out, guest = root / "external", root / "fresh-guest"
        out.mkdir(); guest.mkdir()
        request = dict(case=external.CASES[0], run_id="0123456789abcdef", out=str(out),
                       sdk=str(root / "synthetic-sdk"), powershell=str(root / "powershell"),
                       driver_sha256="a" * 64)
        for key in ("build", "running", "proposal", "server"):
            path = root / (key + ".json")
            write_json(path, {"synthetic": key})
            request[key] = str(path)
        write_json(out / "sources-before-v1.json", {})
        request["sources"] = external.environment.binding(out / "sources-before-v1.json")
        gate = native_gate(root / "native", request)
        request["gate"] = str(gate.path)
        write_json(out / "request-v1.json", request)
        live = SimpleNamespace(descriptor={"root": str(guest)}, check=Mock())
        return SimpleNamespace(request=request, out=out, guest=guest, gate=gate, live=live)

    def run_worker(self, fixture, *, refused):
        with admission_boundaries(), \
             patch.object(external.environment, "open_live_owner", return_value=fixture.live), \
             patch.object(external, "Session", side_effect=ReachedSession("gate_reached_session")) as session, \
             patch.object(external, "SdkCapture") as capture:
            if refused:
                with self.assertRaises((RuntimeError, OSError)) as raised:
                    external.worker(fixture.request, fixture.out)
                self.assertNotIsInstance(raised.exception, ReachedSession,
                    "timingless_native_gate_reached_current_session")
                session.assert_not_called()
            else:
                with self.assertRaises(ReachedSession):
                    external.worker(fixture.request, fixture.out)
                session.assert_called_once_with(fixture.request, fixture.out)
            capture.assert_not_called()

    def parent_fixture(self, root, case):
        fixture = current_fixture.upgrade(external_fixture.deep_fixture(root, case, record_version=2))
        gate = native_gate(root / "native", fixture.request)
        fixture.request["gate"] = str(gate.path)
        write_json(fixture.out / "request-v1.json", fixture.request)
        write_json(fixture.guest / external.CLAIM, external.claim_value(fixture.request))
        fixture.record["claim"] = external.environment.binding(fixture.guest / external.CLAIM)
        current_fixture.publish_record(fixture)
        return fixture, gate

    def test_real_current_worker_accepts_measured_native_gate_before_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.worker_fixture(Path(temporary))
            self.run_worker(fixture, refused=False)
            self.assertTrue((fixture.guest / external.CLAIM).is_file())

    def test_current_worker_refuses_timingless_observer_and_sdk_gate_rows(self):
        for index in (1, 3):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temporary:
                fixture = self.worker_fixture(Path(temporary)); before = originals(fixture.gate)
                downgrade(fixture.gate, index)
                with admission_boundaries():
                    self.assertEqual(external.qualified_gate(fixture.gate.path, fixture.request["build"]),
                                     fixture.gate.request)
                self.run_worker(fixture, refused=True)
                self.assertEqual(originals(fixture.gate), before)

    def test_full_current_parent_accepts_original_measured_gate_in_all_four_cases(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture, gate = self.parent_fixture(Path(temporary), case)
                before = originals(gate)
                with admission_boundaries(fixture.expected):
                    self.assertEqual(external.validate_current_execution(fixture.request, fixture.out), fixture.record)
                self.assertEqual(originals(gate), before)

    def test_current_parent_refuses_downgraded_gate_despite_complete_current_external_proof(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture, gate = self.parent_fixture(Path(temporary), case); before = originals(gate)
                downgrade(gate, 1)
                with admission_boundaries(fixture.expected):
                    self.assertEqual(external.qualified_gate(gate.path, fixture.request["build"]), gate.request)
                    self.assertEqual(external.validate_execution(fixture.request, fixture.out), fixture.record)
                    with self.assertRaises(RuntimeError):
                        external.validate_current_execution(fixture.request, fixture.out)
                self.assertEqual(originals(gate), before)

    def test_missing_or_null_gate_timing_is_refused_before_current_worker_session(self):
        for field, value in (("elapsed_ms", None), ("elapsed_ms", "missing"),
                             ("effective_deadline_ms", None), ("effective_deadline_ms", "missing")):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temporary:
                fixture = self.worker_fixture(Path(temporary))
                path = fixture.gate.out / "clients/command-0002.json"
                row = json.loads(path.read_bytes())
                if value == "missing":
                    del row[field]
                else:
                    row[field] = value
                write_json(path, row)
                self.run_worker(fixture, refused=True)

    def test_gate_client_set_cannot_be_truncated_or_augmented_before_session(self):
        for change in ("lower-count", "extra-row", "missing-raw"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                fixture = self.worker_fixture(Path(temporary)); gate = fixture.gate
                if change == "lower-count":
                    path = gate.out / "components-v1.json"; row = json.loads(path.read_bytes()); row["clients"] = 3
                    write_json(path, row)
                    gate.record["components"] = external.environment.binding(path)
                    write_json(gate.path, gate.record)
                elif change == "extra-row":
                    write_json(gate.out / "clients/command-0005.json", {"original_extra": True})
                else:
                    # Only a disposable original synthetic file is removed.
                    (gate.out / "clients/command-0004.stdout.bin").unlink()
                self.run_worker(fixture, refused=True)

    def test_gate_original_raw_hash_and_class_copy_checks_still_precede_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.worker_fixture(Path(temporary))
            stem = fixture.gate.out / "clients/command-0003"
            raw = b"different original synthetic runner bytes"
            stem.with_suffix(".stdout.bin").write_bytes(raw)
            row = json.loads(stem.with_suffix(".json").read_bytes())
            row.update(stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest())
            write_json(stem.with_suffix(".json"), row)
            self.run_worker(fixture, refused=True)


if __name__ == "__main__":
    unittest.main()
