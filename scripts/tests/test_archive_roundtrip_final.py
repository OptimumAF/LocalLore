"""Host-only final archive replay tests."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_final as final
from benchmarks import receipt_avd_environment as env
from benchmarks.runtime_spike import ProcessResult
from scripts.tests.test_owned_archive_roundtrip_profile import admission
from scripts.tests.test_owned_target_contract import pin

PASSED = b'{"status":"passed","mode":"check-final"}\n'
REPORT = dict(version=1, fixture="locallore-platform-roundtrip-v1", status="passed", mode="check-final")


class FinalReplayTests(unittest.TestCase):
    def setUp(self):
        temp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        a = self.admission = admission()
        if temp.drive.upper() == "D:":
            a["root"], a["server"]["root"] = str(temp), str(temp / "server")
        else:
            self.enterContext(patch.object(final, "_root", return_value=temp / final.outbound.OUTPUT / final.DIRECTORY))
            self.enterContext(patch.object(final.bridge, "_root", return_value=temp / final.outbound.OUTPUT / final.bridge.DIRECTORY))
            self.enterContext(patch.object(final.contract, "binding"))
            self.enterContext(patch.object(final.bridge.files, "_read", side_effect=self.read_local))
            self.enterContext(patch.object(final.bridge.files, "_bound", side_effect=self.bound_local))
            self.enterContext(patch.object(final.output_control, "validate_output", side_effect=self.new_local))
        self.root = final._root(a)
        self.oracle = final.bridge._root(a) / "windows" / final.ORACLE
        self.oracle.parent.mkdir(parents=True)
        self.archive = b"synthetic final archive"
        self.oracle.write_bytes(self.archive)
        self.returned = dict(
            final=self.archive, session=pin("D:/Synthetic/session.json"),
            bridge=pin("D:/Synthetic/bridge.json"), outbound_records=(pin("D:/Synthetic/first.json"),),
            records=(pin("D:/Synthetic/last.json"),), write_claim=pin("D:/Synthetic/write.json"),
            instrumentation={"passed": True},
        )
        self.replay = self.enterContext(patch.object(final.returning, "replay",
                                                     side_effect=lambda *args: copy.deepcopy(self.returned)))
        self.enterContext(patch.object(final.build, "verify_current"))
        self.child = self.enterContext(patch.object(final.process, "run_process", side_effect=self.native))

    def read_local(self, path, cap):
        raw = env.safe_path(path).read_bytes()
        if len(raw) > cap:
            raise ValueError("size")
        return raw

    def bound_local(self, binding, cap):
        path = Path(binding["path"])
        raw = self.read_local(path, cap)
        if final.bridge._pin_bytes(path, raw) != binding:
            raise ValueError("binding")
        return raw

    def new_local(self, path):
        candidate = Path(path)
        if candidate.exists():
            raise FileExistsError
        return candidate

    def native(self, argv, **limits):
        executable = self.admission["artifacts"]["fixture_executable"]["path"]
        self.assertEqual(argv, [executable, "--owned-stdin", "--development-fixtures", "check-final",
                                "--directory", str(self.root / "checked"), "--inputs", str(self.root / "input"),
                                "--fixtures", str(self.oracle.parent)])
        self.assertEqual(limits, dict(deadline=120, max_output=4096))
        self.assertEqual((self.root / "input" / final.INPUT).read_bytes(), self.archive)
        self.assertEqual(json.loads((self.root / "request.json").read_bytes())["argv"], argv)
        checked = self.root / "checked"
        checked.mkdir()
        (checked / "result.json").write_bytes(env.encoded(REPORT))
        (checked / "android-final.sqlite3").write_bytes(b"synthetic database")
        return ProcessResult("completed", 50, PASSED, 0, 0, True)

    def run_final(self):
        return final.run(self.admission, copy.deepcopy(self.returned))

    def verify(self, receipt):
        return final.verify(self.admission, self.returned["session"], self.returned["bridge"], receipt)

    def test_final_child_receipt_is_verified_without_second_child(self):
        receipt = self.run_final()
        proof = self.verify(receipt)
        self.assertEqual(set(proof["outputs"]), {"result.json", "android-final.sqlite3"})
        self.assertEqual(self.replay.call_count, 3)
        self.child.assert_called_once()

    def test_substituted_android_result_refuses_before_start(self):
        wrong = dict(self.returned, final=b"foreign bytes")
        with self.assertRaisesRegex(final.FinalRefused, "^return_evidence$"):
            final.run(self.admission, wrong)
        self.child.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_oversized_request_refuses_before_writing_or_spawning(self):
        with patch.object(final.bridge, "RECEIPT_CAP", 128):
            with self.assertRaisesRegex(final.FinalRefused, "^request$"):
                self.run_final()
        self.child.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_request_changed_during_write_refuses_before_start(self):
        create_json = env.create_json

        def changed(path, value):
            return create_json(path, dict(value, deadline=1) if path.name == "request.json" else value)

        with patch.object(env, "create_json", side_effect=changed):
            with self.assertRaises(ValueError):
                self.run_final()
        self.child.assert_not_called()
        self.assertTrue((self.root / "request.json").exists())
        self.assertFalse((self.root / "receipt.json").exists())

    def test_oracle_drift_refuses_before_start(self):
        self.oracle.write_bytes(b"foreign oracle")
        with self.assertRaisesRegex(final.FinalRefused, "^final_archive$"):
            self.run_final()
        self.child.assert_not_called()

    def test_changed_return_record_after_native_refuses_publication(self):
        altered = dict(self.returned, records=(pin("D:/Synthetic/other.json"),))
        self.replay.side_effect = [self.returned, altered]
        with self.assertRaisesRegex(final.FinalRefused, "^return_evidence$"):
            self.run_final()
        self.assertTrue((self.root / "terminal.json").exists())
        self.assertFalse((self.root / "receipt.json").exists())

    def test_wrong_terminal_mode_retained_without_receipt_and_retry_refused(self):
        self.child.side_effect = None
        self.child.return_value = ProcessResult("completed", 50, b'{"status":"passed","mode":"verify"}\n', 0, 0, True)
        with self.assertRaisesRegex(final.bridge.BridgeRefused, "^terminal$"):
            self.run_final()
        self.assertTrue((self.root / "terminal.json").is_file())
        self.assertFalse((self.root / "receipt.json").exists())
        with self.assertRaises((ValueError, FileExistsError)):
            self.run_final()
        self.child.assert_called_once()

    def test_cleanup_failure_refuses_receipt(self):
        self.child.side_effect = None
        self.child.return_value = ProcessResult("cleanup_failed", 50, PASSED, 0, 0, False)
        with self.assertRaisesRegex(final.bridge.BridgeRefused, "^terminal$"):
            self.run_final()
        self.assertFalse((self.root / "receipt.json").exists())

    def test_unexpected_output_never_qualifies(self):
        def extra(*args, **kwargs):
            result = self.native(*args, **kwargs)
            (self.root / "checked" / "extra.bin").write_bytes(b"retained")
            return result
        self.child.side_effect = extra
        with self.assertRaisesRegex(final.FinalRefused, "^outputs$"):
            self.run_final()
        self.assertTrue((self.root / "checked" / "extra.bin").exists())
        self.assertFalse((self.root / "receipt.json").exists())

    def test_changed_terminal_before_publication_refuses(self):
        def replay(*args):
            target = self.root / "terminal.json"
            if target.exists():
                value = json.loads(target.read_bytes())
                value["elapsed_ms"] += 1
                target.write_bytes(env.encoded(value))
            return copy.deepcopy(self.returned)
        self.replay.side_effect = replay
        with self.assertRaisesRegex(final.FinalRefused, "^terminal$"):
            self.run_final()
        self.assertFalse((self.root / "receipt.json").exists())

    def test_closed_replay_refuses_substitute_bridge_and_retained_output(self):
        receipt = self.run_final()
        with self.assertRaisesRegex(final.FinalRefused, "^request$"):
            final.verify(self.admission, self.returned["session"], pin("D:/Synthetic/elsewhere.json"), receipt)
        (self.root / "checked" / "android-final.sqlite3").write_bytes(b"changed")
        with self.assertRaisesRegex(final.FinalRefused, "^outputs$"):
            self.verify(receipt)


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.capture = final.client.OwnedArchiveRoundtripSdkCapture.__new__(final.client.OwnedArchiveRoundtripSdkCapture)
        self.capture.clean = True
        self.capture.lease = SimpleNamespace(admission=admission())
        self.capture.close = Mock(side_effect=lambda: setattr(self.capture, "clean", False))
        self.calls = Mock()
        self.outbound = self.enterContext(patch.object(final.outbound, "run", return_value={"session": "session"}))
        self.bridge = self.enterContext(patch.object(final.bridge, "run", return_value="bridge"))
        self.returning = self.enterContext(patch.object(final.returning, "run", return_value="returned"))
        self.final = self.enterContext(patch.object(final, "run", return_value="final"))
        for name in ("outbound", "bridge", "returning", "final"):
            self.calls.attach_mock(getattr(self, name), name)

    def test_exchange_calls_all_legs_in_order_and_closes_capture(self):
        self.assertEqual(final.exchange(self.capture), {"session": "session", "bridge": "bridge", "final": "final"})
        self.assertEqual([call[0] for call in self.calls.mock_calls], ["outbound", "bridge", "returning", "final"])
        self.capture.close.assert_called_once_with()

    def test_bridge_failure_never_dispatches_return_and_closes_capture(self):
        self.bridge.side_effect = final.bridge.BridgeRefused("terminal")
        with self.assertRaises(final.bridge.BridgeRefused):
            final.exchange(self.capture)
        self.returning.assert_not_called()
        self.final.assert_not_called()
        self.capture.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
