"""Synthetic timing diagnostics only; no SDK, process or listener is observed.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from benchmarks import android_external_controller as external
from benchmarks import android_process_client as client
from benchmarks import android_process_verification as driver
from benchmarks.android_instrumentation_evidence import validate_instrumentation
from scripts.tests import test_android_process_client as client_fixture
from scripts.tests import test_android_process_verification as phase_fixture
from scripts.tests import test_android_external_controller as external_fixture
from scripts.tests import test_android_external_current_creation as current_fixture


def timed(row, **changes):
    result = dict(row, version=2, elapsed_ms=180007, effective_deadline_ms=15000)
    result.update(changes)
    return result


def malformed_rows(original):
    variants = []
    for key in ("elapsed_ms", "effective_deadline_ms"):
        missing = dict(original)
        missing.pop(key)
        variants.append(missing)
        for value in (True, False, -1, 0.5, "15000", None, 2**63, 10**100):
            variants.append(dict(original, **{key: value}))
    variants.extend((dict(original, effective_deadline_ms=0),
                     dict(original, effective_deadline_ms=180001),
                     dict(original, extra=0), dict(original, version=True),
                     dict(original, version=3), dict(original, version=1)))
    return variants


class CaptureTimingTests(unittest.TestCase):
    def setUp(self):
        # Reuse only the original fake environment, not its test methods/roster.
        self.fake = client_fixture.AndroidProcessClientTests()
        self.fake.setUp()
        self.addCleanup(self.fake.doCleanups)

    def test_measured_timing_and_exact_ceil_budget_preserve_binary_bytes(self):
        f = self.fake
        for index, (seconds, remaining) in enumerate(((15, 1000), (120, 1000), (180, 1000),
                                                      (15, 1.2501), (15, 0.0004))):
            with self.subTest(seconds=seconds, remaining=remaining):
                owner = client.SdkCapture(f.root / ("timing-%d" % index), 1000, f.adb, f.powershell, f.pin)
                owner.until = f.now + remaining
                result = f.completed(f.payload)
                result.elapsed_ms = 37
                f.runner.side_effect = lambda *a, **k: result
                raw = owner.capture(client._server_command(f.powershell), "observation", seconds=seconds)
                exact = min(seconds, owner.until - f.now)
                row = f.records(owner)[0]
                self.assertEqual(2, row["version"])
                self.assertEqual(37, row["elapsed_ms"])
                self.assertEqual(math.ceil(exact * 1000), row["effective_deadline_ms"])
                self.assertEqual(exact, f.runner.call_args.kwargs["deadline"])
                self.assertEqual(f.payload, raw)
                self.assertEqual(raw, (owner.directory / "command-0001.stdout.bin").read_bytes())
                self.assertTrue(owner.clean)

    def test_timeout_observer_retains_measured_overrun_and_stops_before_sdk(self):
        f = self.fake
        owner = f.owner()
        owner.target = {"transport_id": 7}
        f.runner.side_effect = lambda *a, **k: client.host.ProcessResult("timeout", 15073, b"", 0, 1, True)
        with self.assertRaises(client.ClientRefused):
            owner.adb(["exec-out", "fixed"], "binary")
        self.assertEqual(1, f.runner.call_count)
        self.assertEqual(str(f.powershell), f.runner.call_args.args[0][0])
        self.assertEqual(15, f.runner.call_args.kwargs["deadline"])
        row = f.records(owner)[0]
        self.assertEqual(("adb-server", "timeout", 15073, 15000),
                         (row["label"], row["status"], row["elapsed_ms"], row["effective_deadline_ms"]))
        self.assertIs(row["cleanup_complete"], True)
        self.assertEqual(b"", (owner.directory / "command-0001.stdout.bin").read_bytes())
        f.assert_stopped(owner)
        self.assertEqual(1, owner.count)

    def test_sdk_still_has_two_fixed_observers_and_independent_timings(self):
        f = self.fake
        owner = f.owner()
        owner.target = {"transport_id": 7}
        original = f.fake_run
        values = iter((4, 51, 6))
        def run(command, **kwargs):
            result = original(command, **kwargs)
            result.elapsed_ms = next(values)
            return result
        f.runner.side_effect = run
        self.assertEqual(f.payload, owner.adb(["exec-out", "fixed"], "binary", seconds=120))
        rows = f.records(owner)
        self.assertEqual(["adb-server", "binary", "adb-server"], [r["label"] for r in rows])
        self.assertEqual([4, 51, 6], [r["elapsed_ms"] for r in rows])
        self.assertEqual([15000, 100000, 15000], [r["effective_deadline_ms"] for r in rows])
        self.assertEqual([15, 100.0, 15], [c.kwargs["deadline"] for c in f.runner.call_args_list])

    def test_invalid_measured_timing_cannot_be_persisted_as_success(self):
        f = self.fake
        for index, value in enumerate((True, -1, 0.5, "1", None, 2**63)):
            with self.subTest(value=value):
                owner = client.SdkCapture(f.root / ("bad-time-%d" % index), 100, f.adb, f.powershell, f.pin)
                result = f.completed(f.payload)
                result.elapsed_ms = value
                f.runner.side_effect = lambda *a, **k: result
                with self.assertRaises(client.ClientRefused):
                    owner.capture(client._server_command(f.powershell), "observation")
                row = f.records(owner)[0]
                self.assertEqual(("spawn_failed", None, False),
                                 (row["status"], row["elapsed_ms"], row["cleanup_complete"]))
                f.assert_stopped(owner)

    def test_unavailable_runner_result_has_null_measurement_not_synthetic_zero(self):
        f = self.fake
        owner = f.owner()
        f.runner.side_effect = OSError("CANARY private exception")
        with self.assertRaises(client.ClientRefused):
            owner.capture(client._server_command(f.powershell), "observation")
        row = f.records(owner)[0]
        self.assertIsNone(row["elapsed_ms"])
        self.assertEqual(15000, row["effective_deadline_ms"])
        self.assertTrue(driver.client_record_shape(row))
        self.assertNotIn("CANARY", json.dumps(row))
        self.assertEqual(b"", (owner.directory / "command-0001.stdout.bin").read_bytes())
        f.assert_stopped(owner)


class RecordTimingValidationTests(unittest.TestCase):
    def row(self, raw=b"binary\x00\x1a\xff\r\n"):
        return dict(version=1, index=1, label="controller", status="completed", returncode=0,
                    cleanup_complete=True, stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest(),
                    stderr_bytes=0)

    def test_closed_shapes_preserve_v1_and_typed_v2_without_overrun_refusal(self):
        original = self.row()
        for row in (original, timed(original)):
            self.assertTrue(driver.client_record_shape(row))
        for elapsed, deadline in ((0, 1), (2**63 - 1, 180000)):
            row = timed(original)
            row.update(elapsed_ms=elapsed, effective_deadline_ms=deadline)
            self.assertTrue(driver.client_record_shape(row))
        for row in malformed_rows(timed(original)) + [dict(original, elapsed_ms=0),
                dict(original, effective_deadline_ms=1), [], None]:
            with self.subTest(row=row):
                self.assertFalse(driver.client_record_shape(row))

    def test_null_is_only_the_closed_unavailable_unclean_spawn_failure(self):
        failure = timed(self.row(b""), status="spawn_failed", returncode=None,
                        cleanup_complete=False, elapsed_ms=None)
        self.assertTrue(driver.client_record_shape(failure))
        for changes in ({"status": "completed"}, {"status": "timeout"}, {"status": "cancelled"},
                        {"status": "output_limit"}, {"status": "cleanup_failed"},
                        {"cleanup_complete": True}, {"returncode": 0}, {"stdout_bytes": 1},
                        {"stderr_bytes": True}, {"stdout_sha256": "a" * 64}):
            with self.subTest(changes=changes):
                self.assertFalse(driver.client_record_shape(dict(failure, **changes)))
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "clients").mkdir()
            stem = out / "clients/command-0001"
            stem.with_suffix(".stdout.bin").write_bytes(b"")
            stem.with_suffix(".json").write_text(json.dumps(failure))
            with self.assertRaises(external.ExternalRefused):
                external.validate_clients(out, 1, {"controller": b""})

    def test_external_validator_checks_timing_before_copy_credit(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "clients").mkdir()
            stem = out / "clients/command-0001"
            raw = b"binary\x00\x1a\xff\r\n"
            stem.with_suffix(".stdout.bin").write_bytes(raw)
            original = self.row(raw)
            for row in (original, timed(original)):
                stem.with_suffix(".json").write_text(json.dumps(row))
                external.validate_clients(out, 1, {"controller": raw})
            for row in malformed_rows(timed(original)) + [dict(original, elapsed_ms=0)]:
                with self.subTest(row=row):
                    stem.with_suffix(".json").write_text(json.dumps(row))
                    with self.assertRaises(external.ExternalRefused):
                        external.validate_clients(out, 1, {"controller": raw})

    def test_component_validator_preserves_full_roster_and_refuses_bad_timing(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "clients").mkdir()
            results = []
            for index, (name, methods) in enumerate(zip(driver.CLASSES, driver.EXPECTED_METHODS), 1):
                raw = phase_fixture.synthetic_regression_run(name, methods)
                (out / (name + ".stdout.raw")).write_bytes(raw)
                results.append(validate_instrumentation(raw, "org.locallore.app." + name, list(methods)))
                stem = out / "clients" / ("command-%04d" % index)
                stem.with_suffix(".stdout.bin").write_bytes(raw)
                row = self.row(raw)
                row.update(index=index, label="instrument-" + str(index - 1))
                stem.with_suffix(".json").write_text(json.dumps(row))
            record = dict(version=1, results=results, clients=3, clients_clean=True,
                          method_count=10, external_controller_case_executed=False)
            driver.validate_component_record(record, out)
            path = out / "clients/command-0001.json"
            original = json.loads(path.read_bytes())
            path.write_text(json.dumps(timed(original)))
            driver.validate_component_record(record, out)
            for row in malformed_rows(timed(original)) + [dict(original, elapsed_ms=0)]:
                with self.subTest(row=row):
                    path.write_text(json.dumps(row))
                    with self.assertRaises(driver.VerificationRefused):
                        driver.validate_component_record(record, out)

    def test_full_regression_validator_accepts_historical_then_v2_and_refuses_bad_timing(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            record = phase_fixture.RegressionPhaseTests().fixture(out, interleaved=True)
            driver.validate_regression_record(record, out)
            for path in (out / "clients").glob("*.json"):
                path.write_text(json.dumps(timed(json.loads(path.read_bytes()))))
            driver.validate_regression_record(record, out)
            path = out / "clients/command-0001.json"
            original = json.loads(path.read_bytes())
            before = copy.deepcopy(record)
            for row in malformed_rows(original):
                with self.subTest(row=row):
                    path.write_text(json.dumps(row))
                    with self.assertRaises(driver.VerificationRefused):
                        driver.validate_regression_record(record, out)
            self.assertEqual(before, record)


class CurrentTimingCoverageTests(unittest.TestCase):
    def fixture(self, root, case):
        fixture = current_fixture.upgrade(external_fixture.deep_fixture(root, case, record_version=2))
        for path in (fixture.out / "clients").glob("command-*.json"):
            path.write_text(json.dumps(timed(json.loads(path.read_bytes()))))
        # An additional synthetic observer row retains its original raw bytes
        # and index, just like SDK rows; it cannot lose timing independently.
        fixture.record["clients"] += 1
        index = fixture.record["clients"]
        raw = b'{"pid":41,"listeners":[{"address":"127.0.0.1","port":5037,"pid":41}]}\r\n'
        stem = fixture.out / "clients" / ("command-%04d" % index)
        stem.with_suffix(".stdout.bin").write_bytes(raw)
        row = dict(version=1, index=index, label="adb-server", status="completed", returncode=0,
                   cleanup_complete=True, stdout_bytes=len(raw), stdout_sha256=hashlib.sha256(raw).hexdigest(),
                   stderr_bytes=0)
        stem.with_suffix(".json").write_text(json.dumps(timed(row)))
        current_fixture.publish_record(fixture)
        return fixture

    def validate(self, fixture, current=True):
        # Reuse the original boundary mocks; all raw/hash/domain/client
        # validators inside the generic and current entrypoints remain real.
        return current_fixture.CurrentCreationExecutionTests().validate(fixture, current=current)

    def test_all_four_fully_bound_proof2_with_all_client2_rows_pass_current(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture = self.fixture(Path(temporary), case)
                self.assertEqual(self.validate(fixture, current=False), fixture.record)
                self.assertEqual(self.validate(fixture), fixture.record)

    def downgrade(self, fixture, labels):
        changed = 0
        for path in (fixture.out / "clients").glob("command-*.json"):
            row = json.loads(path.read_bytes())
            if labels is None or row["label"] in labels:
                original = dict(row)
                raw_before = path.with_suffix(".stdout.bin").read_bytes()
                row["version"] = 1
                del row["elapsed_ms"]
                del row["effective_deadline_ms"]
                path.write_text(json.dumps(row))
                self.assertEqual(raw_before, path.with_suffix(".stdout.bin").read_bytes())
                self.assertEqual({k: v for k, v in original.items()
                                  if k not in ("version", "elapsed_ms", "effective_deadline_ms")},
                                 {k: v for k, v in row.items() if k != "version"})
                changed += 1
        self.assertGreater(changed, 0)

    def test_fully_bound_observer_row_downgrade_stays_historical_but_refuses_current(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture = self.fixture(Path(temporary), case)
                self.downgrade(fixture, {"adb-server"})
                self.assertEqual(self.validate(fixture, current=False), fixture.record)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_fully_bound_sdk_row_downgrade_stays_historical_but_refuses_current(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture = self.fixture(Path(temporary), case)
                self.downgrade(fixture, {"controller"})
                self.assertEqual(self.validate(fixture, current=False), fixture.record)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_all_timing_rows_can_be_historical_but_cannot_qualify_current(self):
        for case in external.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                fixture = self.fixture(Path(temporary), case)
                self.downgrade(fixture, None)
                self.assertEqual(self.validate(fixture, current=False), fixture.record)
                with self.assertRaises(RuntimeError):
                    self.validate(fixture)

    def test_current_worker_and_parent_sources_require_client2_without_changing_historical_readers(self):
        for module, name, call in ((driver, "_instrumentation_worker", "require_current_clients"),
                                   (driver, "supervise", "require_current_clients"),
                                   (external, "worker", "driver.require_current_clients"),
                                   (external, "validate_current_execution", "driver.require_current_clients")):
            with self.subTest(function=name):
                tree = ast.parse(Path(module.__file__).read_bytes())
                function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
                calls = [n for n in ast.walk(function) if isinstance(n, ast.Call)]
                self.assertTrue(any(ast.unparse(n.func) == call for n in calls))
                current = next(n for n in calls if ast.unparse(n.func) == call)
                generic_name = {"_instrumentation_worker": "validator", "supervise": "validator",
                                "worker": "validate_clients", "validate_current_execution": "validate_execution"}[name]
                generic = next(n for n in calls if ast.unparse(n.func) == generic_name)
                self.assertLess(generic.lineno, current.lineno)
                if name in ("worker", "_instrumentation_worker"):
                    writes = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "create_json"]
                    # The instrumentation phase has only its result publication;
                    # external proof JSON is deliberately retained before this.
                    publication = max(writes, key=lambda n: n.lineno)
                    self.assertLess(current.lineno, publication.lineno)
        for module, names in ((driver, ("validate_component_record", "_validate_fixed_roster_record")),
                              (external, ("validate_clients", "validate_execution"))):
            tree = ast.parse(Path(module.__file__).read_bytes())
            for name in names:
                function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
                self.assertFalse(any(isinstance(n, ast.Call) and "require_current_clients" in ast.unparse(n.func)
                                     for n in ast.walk(function)))

    def test_current_client_helper_checks_every_numbered_row_and_strict_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "clients").mkdir()
            row = timed(RecordTimingValidationTests().row())
            paths = [out / "clients" / ("command-%04d.json" % i) for i in (1, 2)]
            for index, path in enumerate(paths, 1):
                path.write_text(json.dumps(dict(row, index=index)))
            driver.require_current_clients(out, 2)
            for bad in (True, 0, -1, 10001, 2.0, "2", None):
                with self.subTest(count=bad), self.assertRaises(driver.VerificationRefused):
                    driver.require_current_clients(out, bad)
            original = dict(row, index=2)
            for replacement in malformed_rows(original) + [dict(original, index=True), dict(original, index=1)]:
                with self.subTest(row=replacement):
                    paths[1].write_text(json.dumps(replacement))
                    with self.assertRaises(driver.VerificationRefused):
                        driver.require_current_clients(out, 2)


if __name__ == "__main__":
    unittest.main()
