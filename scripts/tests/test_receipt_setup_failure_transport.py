"""Original adversarial negative-transport fixtures; every device call is mocked.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import shlex
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts.tests import test_receipt_setup_qualification as fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import receipt_setup_failure_transport as n

q = n.q


def transcript():
    stack = n.SENTINEL + "\n\tat " + n.CLASS + "." + n.METHOD + "(ReceiptSetupFailureTransportTest.kt:40)"
    fields = {"class": n.CLASS, "current": "1", "id": "AndroidJUnitRunner", "numtests": "1", "test": n.METHOD}
    def status(values, code):
        return "".join("INSTRUMENTATION_STATUS: " + key + "=" + value + "\n" for key, value in values.items()) + \
               "INSTRUMENTATION_STATUS_CODE: " + str(code) + "\n"
    start = status(dict(fields, stream="\n" + n.CLASS + ":"), 1)
    trace = status({"locallore_receipt_failure_v1": json.dumps(n.expected_trace(), separators=(",", ":"))}, 1337)
    end = status(dict(fields, stack=stack + "\n", stream="\nError in " + n.METHOD + "(" + n.CLASS + "):\n" + stack + "\n"), -2)
    return (start + trace + end + "INSTRUMENTATION_RESULT: stream=\n\nTime: 0.04\nThere was 1 failure:\n1) " +
            n.METHOD + "(" + n.CLASS + ")\n" + stack + "\n\nFAILURES!!!\nTests run: 1,  Failures: 1\n\n\n" +
            "INSTRUMENTATION_CODE: -1\n").encode("ascii")


def proposal(directory):
    value = fixture.proposal(directory)
    value["scope"] = n.SCOPE
    for name in n.SOURCE_FILES:
        path = (q.ROOT / name).resolve()
        value["bindings"][str(path)] = q.sha(path.read_bytes())
    return value


class NegativeTransportTests(unittest.TestCase):
    def reject(self, raw):
        with self.assertRaises((AssertionError, ValueError, UnicodeError)):
            n.parse_negative_instrumentation(raw)

    def test_exact_failure_observes_transport_without_qualifying_setup(self):
        for ending in (b"\n", b"\r\n"):
            raw = transcript().replace(b"\n", ending)
            observed = n.parse_negative_instrumentation(raw)
            self.assertTrue(observed["negative_transport_observed"])
            self.assertEqual(observed["failed_methods"], 1)
            self.assertTrue(observed["normal_setup_gate_rejected"])
            with self.assertRaises(AssertionError):
                q.parse_instrumentation(raw, q.INITIAL_CLASS, q.INITIAL_METHODS)

    def test_success_missing_duplicate_or_wrong_status_never_qualifies(self):
        self.reject(fixture.transcript())
        raw = transcript()
        for wrong in (raw.replace(b"1337", b"1338"), raw.replace(b"INSTRUMENTATION_STATUS_CODE: -2", b"INSTRUMENTATION_STATUS_CODE: 0"),
                      raw + b"OK (1 test)\n", raw + raw, raw.replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0")):
            self.reject(wrong)

    def test_trace_must_equal_the_synthetic_probe_not_just_any_valid_trace(self):
        raw = transcript()
        for before, after in ((b'"MISSING"', b'"FAILED"'), (b'"NONE"', b'"STORAGE"'), (b'"opened":0', b'"opened":1'),
                              (b'"events_total":2', b'"events_total":3')):
            self.reject(raw.replace(before, after))

    def test_wrong_original_or_wrapped_or_suppressed_failure_refuses(self):
        raw = transcript()
        for wrong in (raw.replace(n.SENTINEL.encode(), b"java.lang.RuntimeException: wrapped"),
                      raw.replace(n.SENTINEL.encode(), b"java.lang.RuntimeException: wrapper\nCaused by: " + n.SENTINEL.encode()),
                      raw.replace(b"\tat ", b"Suppressed: java.lang.AssertionError: extra\n\tat "),
                      raw.replace(n.SENTINEL.encode(), n.SENTINEL.encode() + b" extra"),
                      raw.replace(b"ReceiptSetupFailureTransportTest.kt:40", b"Other.kt:40")):
            self.reject(wrong)

    def test_identity_counts_order_and_failure_summary_are_closed(self):
        raw = transcript()
        for before, after in ((n.CLASS.encode(), b"org.locallore.app.OtherTest"), (n.METHOD.encode(), b"otherMethod"),
                              (b"numtests=1", b"numtests=2"), (b"current=1", b"current=2"),
                              (b"Tests run: 1,  Failures: 1", b"Tests run: 2,  Failures: 1"),
                              (b"There was 1 failure:", b"There were 2 failures:"),
                              (b"Time: 0.04", b"Time: 121"), (b"id=AndroidJUnitRunner", b"id=OtherRunner")):
            self.reject(raw.replace(before, after))
        self.reject(raw.replace(b"INSTRUMENTATION_STATUS_CODE: 1\n", b"INSTRUMENTATION_STATUS_CODE: 1\nINSTRUMENTATION_STATUS: unknown=x\n", 1))

    def test_framing_and_machine_injection_refuse(self):
        for wrong in (transcript().replace(b"\n", b"\r\r\n"), transcript() + b"private trailing data\n",
                      transcript().replace(b"\tat ", b"INSTRUMENTATION_UNKNOWN: injection\n\tat "),
                      transcript().replace(b"FAILURES!!!", b"FAILURES!!!\nCaused by: extra")):
            self.reject(wrong)

    def test_scope_and_exact_authorization_are_separate_from_positive_controller(self):
        with tempfile.TemporaryDirectory() as directory:
            value = proposal(Path(directory)); original = copy.deepcopy(value)
            with patch.object(q, "APK_HASHES", value["apk_sha256"]):
                self.assertTrue(n.validate_proposal(value))
                self.assertEqual(value, original)
                with self.assertRaises(AssertionError): q.validate_proposal(value)
                positive = dict(value, scope="receipt_setup_qualification")
                with self.assertRaises(AssertionError): n.validate_proposal(positive)
                path, auth = Path(directory) / "proposal.json", Path(directory) / "auth.json"
                path.write_bytes(json.dumps(value).encode())
                grant = {"version": 1, "proposal_sha256": q.sha(path.read_bytes()), "allow_device_calls": True, "root_go_pending": False}
                auth.write_text(json.dumps(grant))
                self.assertEqual(n.authorize(path, auth, directory), value)
                for key, invalid in (("version", True), ("allow_device_calls", 1), ("root_go_pending", 0), ("proposal_sha256", "0" * 64)):
                    auth.write_text(json.dumps(dict(grant, **{key: invalid})))
                    with self.assertRaises(AssertionError): n.authorize(path, auth, directory)

    def test_negative_owner_and_positive_owner_cannot_select_each_others_tests(self):
        for negative in (True, False):
            with tempfile.TemporaryDirectory() as directory:
                value = fixture.proposal(Path(directory)); owner = (n.NegativeOwner if negative else q.Owner)(value, fixture.Lease(value))
                owner.stage = "negative" if negative else "instrumentation"
                forbidden = q.INITIAL_INSTRUMENT if negative else n.INSTRUMENT
                with patch.object(q.host, "run_process", side_effect=AssertionError("must not dispatch")) as run:
                    with self.assertRaises(AssertionError): owner.shell(forbidden)
                    run.assert_not_called()

    def execute(self, directory, observed):
        value = fixture.proposal(directory); lease = fixture.Lease(value); owner = n.NegativeOwner(value, lease)
        transport = fixture.Transport(value, lease)
        def dispatch(command, **kwargs):
            if command[3] == "shell" and tuple(shlex.split(command[4])) == n.INSTRUMENT:
                transport.instruments += 1
                transport.calls.append((command, kwargs))
                return SimpleNamespace(status="completed", returncode=0, cleanup_complete=True,
                                       stdout=observed, stderr_bytes=0, elapsed_ms=1)
            return transport(command, **kwargs)
        with patch.object(q.host, "run_process", side_effect=dispatch), patch.object(q.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
            return owner, transport, n.run_cohort(owner)

    def test_actual_mock_owner_runs_only_two_installs_and_one_failed_test(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, transport, value = self.execute(Path(directory), transcript())
            self.assertEqual(transport.instruments, 1)
            self.assertEqual(transport.installs, 2)
            self.assertFalse(value["normal_setup_qualified"])
            self.assertFalse(value["restart_qualified"])
            self.assertEqual(owner.process_boundary._next, 2)
            self.assertTrue((owner.directory / "negative-transport-v1.json").is_file())
            self.assertFalse((owner.directory / "after-initial-facts.json").exists())
            self.assertEqual((owner.commands / ("command-%04d.stdout.bin" % owner.count)).read_bytes(), transcript())

    def test_unexpected_failed_runner_retains_raw_trace_then_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = transcript().replace(n.SENTINEL.encode(), b"java.lang.AssertionError: wrong")
            with self.assertRaises(AssertionError): self.execute(Path(directory), raw)
            root = Path(directory) / "cohort"
            self.assertTrue((root / "initial-failure-trace-v1.json").is_file())
            self.assertFalse((root / "negative-transport-v1.json").exists())
            records = sorted((root / "commands").glob("*.stdout.bin"))
            self.assertEqual(records[-1].read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
