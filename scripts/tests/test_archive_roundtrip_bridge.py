"""Windows continuation receipt tests with isolated host-only fixtures."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_bridge as bridge
from benchmarks import archive_roundtrip_outbound as outbound
from benchmarks import receipt_avd_environment as env
from benchmarks.runtime_spike import ProcessResult
from scripts.tests import test_owned_archive_roundtrip_profile as profile
from scripts.tests import test_owned_target_contract as legacy

TERMINAL = b'{"status":"passed","mode":"verify"}\n'
REPORT = b'{"version":1,"fixture":"locallore-platform-roundtrip-v1","status":"passed","mode":"verify"}'


class BridgeTests(unittest.TestCase):
    def setUp(self):
        temporary = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.admission = profile.admission()
        if temporary.drive.upper() == "D:":
            self.admission["root"] = str(temporary)
            self.admission["server"]["root"] = str(temporary / "server")
        else:
            self.enterContext(patch.object(bridge, "_root", return_value=temporary / outbound.OUTPUT / bridge.DIRECTORY))
            self.enterContext(patch.object(bridge.contract, "binding"))
        self.root = bridge._root(self.admission)
        self.root.parent.mkdir()
        self.session = legacy.pin("D:/Synthetic/session.json")
        self.result = dict(session=self.session,
                           records=(legacy.pin("D:/Synthetic/command-0001.json"),),
                           files={name: ("fixture:" + name).encode() for name in bridge.INPUTS},
                           installed={}, instrumentation={"passed": True})
        self.replay = self.enterContext(patch.object(outbound, "replay_prefix",
                                                     side_effect=lambda *args: copy.deepcopy(self.result)))
        self.enterContext(patch.object(bridge.build, "verify_current"))
        self.process = self.enterContext(patch.object(bridge.process, "run_process", side_effect=self.native))
        if temporary.drive.upper() != "D:":
            def read(path, cap):
                value = env.safe_path(path).read_bytes()
                if len(value) > cap:
                    raise ValueError("size")
                return value

            def bound(pin, cap):
                raw = read(pin["path"], cap)
                if bridge._pin_bytes(Path(pin["path"]), raw) != pin:
                    raise ValueError("binding")
                return raw

            self.enterContext(patch.object(bridge.files, "_read", side_effect=read))
            self.enterContext(patch.object(bridge.files, "_bound", side_effect=bound))
            def new_root(path):
                candidate = Path(path)
                if candidate.exists():
                    raise FileExistsError
                return candidate
            self.enterContext(patch.object(bridge.output_control, "validate_output", side_effect=new_root))

    def native(self, argv, **limits):
        self.assertEqual(argv, [
            self.admission["artifacts"]["fixture_executable"]["path"], "--owned-stdin",
            "--development-fixtures", "verify", "--directory", str(self.root / "windows"),
            "--inputs", str(self.root / "outbound"),
            "--fixtures", str(Path(self.admission["artifacts"]["expectations"]["path"]).parent),
        ])
        self.assertEqual(limits, {"deadline": 120, "max_output": 4096})
        request = json.loads((self.root / "request.json").read_bytes())
        self.assertEqual(request["argv"], argv)
        for name, data in self.result["files"].items():
            self.assertEqual((self.root / "outbound" / name).read_bytes(), data)
        output = self.root / "windows"
        output.mkdir()
        for name in bridge.OUTPUTS:
            (output / name).write_bytes(REPORT if name == "result.json" else name.encode())
        return ProcessResult("completed", 40, TERMINAL, 0, 0, True)

    def run_bridge(self):
        return bridge.run(self.admission, copy.deepcopy(self.result))

    def verify(self, receipt):
        return bridge.verify(self.admission, self.session, receipt)

    def test_qualified_child_publishes_replayable_return_pins(self):
        receipt = self.run_bridge()
        outputs = self.verify(receipt)
        self.assertEqual(set(outputs), {"android-return.json", "expected-android-final.json"})
        self.assertEqual(outputs["android-return.json"], bridge._pin_bytes(
            self.root / "windows" / "android-return.json", b"android-return.json"))
        self.process.assert_called_once()
        self.assertEqual(self.replay.call_count, 3)

    def test_published_and_failed_attempts_cannot_restart(self):
        receipt = self.run_bridge()
        with self.assertRaises(ValueError if self.root.drive else FileExistsError):
            self.run_bridge()
        self.assertEqual(self.verify(receipt)["android-return.json"]["bytes"], len(b"android-return.json"))
        self.process.assert_called_once()

    def test_unsafe_terminal_retains_request_and_no_receipt(self):
        self.process.side_effect = None
        self.process.return_value = ProcessResult("cleanup_failed", 44, TERMINAL, 0, 0, False)
        with self.assertRaisesRegex(bridge.BridgeRefused, "^terminal$"):
            self.run_bridge()
        self.assertTrue((self.root / "request.json").is_file())
        self.assertTrue((self.root / "terminal.json").is_file())
        self.assertFalse((self.root / "receipt.json").exists())
        with self.assertRaises((ValueError, FileExistsError)):
            self.run_bridge()
        self.process.assert_called_once()

    def test_unexpected_stdout_or_stderr_does_not_publish(self):
        self.process.side_effect = None
        self.process.return_value = ProcessResult("completed", 44, TERMINAL + b"extra", 0, 0, True)
        with self.assertRaisesRegex(bridge.BridgeRefused, "^terminal$"):
            self.run_bridge()
        self.assertFalse((self.root / "receipt.json").exists())
        terminal = dict(status="completed", exit_code=0, stderr_bytes=1,
                        elapsed_ms=44, cleanup_complete=True, stdout={})
        with self.assertRaisesRegex(bridge.BridgeRefused, "^terminal$"):
            bridge._check_terminal(terminal, self.root)

    def test_substituted_live_bytes_refuse_before_materialization(self):
        altered = copy.deepcopy(self.result)
        altered["files"]["android-origin.json"] = b"replacement"
        with self.assertRaisesRegex(bridge.BridgeRefused, "^outbound$"):
            bridge.run(self.admission, altered)
        self.assertFalse(self.root.exists())
        self.process.assert_not_called()

    def test_changed_capture_prefix_refuses_before_publish(self):
        changed = copy.deepcopy(self.result)
        changed["records"] = (legacy.pin("D:/Synthetic/replacement.json"),)
        self.replay.side_effect = [self.result, changed]
        with self.assertRaisesRegex(bridge.BridgeRefused, "^outbound$"):
            self.run_bridge()
        self.assertTrue((self.root / "terminal.json").exists())
        self.assertFalse((self.root / "receipt.json").exists())

    def test_changed_terminal_after_child_refuses_before_publication(self):
        def replay(*args):
            terminal = self.root / "terminal.json"
            if terminal.exists():
                content = json.loads(terminal.read_bytes())
                content["elapsed_ms"] += 1
                terminal.write_bytes(env.encoded(content))
            return copy.deepcopy(self.result)

        self.replay.side_effect = replay
        with self.assertRaisesRegex(bridge.BridgeRefused, "^terminal$"):
            self.run_bridge()
        self.assertTrue((self.root / "terminal.json").is_file())
        self.assertFalse((self.root / "receipt.json").exists())

    def test_extra_native_output_refuses_even_after_passed_terminal(self):
        def unexpected(*args, **kwargs):
            result = self.native(*args, **kwargs)
            (self.root / "windows" / "unexpected.db").write_bytes(b"retained")
            return result
        self.process.side_effect = unexpected
        with self.assertRaisesRegex(bridge.BridgeRefused, "^outputs$"):
            self.run_bridge()
        self.assertTrue((self.root / "windows" / "unexpected.db").is_file())
        self.assertFalse((self.root / "receipt.json").exists())

    def test_unexpected_root_entry_refuses_publication_and_replay(self):
        def extra(*args, **kwargs):
            result = self.native(*args, **kwargs)
            (self.root / "unexpected.bin").write_bytes(b"retained")
            return result
        self.process.side_effect = extra
        with self.assertRaisesRegex(bridge.BridgeRefused, "^outputs$"):
            self.run_bridge()
        self.assertFalse((self.root / "receipt.json").exists())
        self.assertTrue((self.root / "unexpected.bin").is_file())

    def test_later_root_entry_refuses_closed_replay(self):
        receipt = self.run_bridge()
        (self.root / "unexpected.bin").write_bytes(b"retained")
        with self.assertRaisesRegex(bridge.BridgeRefused, "^outputs$"):
            self.verify(receipt)

    def test_altered_return_archive_refuses_on_readback(self):
        receipt = self.run_bridge()
        archive = self.root / "windows" / "android-return.json"
        archive.write_bytes(b"x" * archive.stat().st_size)
        with self.assertRaisesRegex(bridge.BridgeRefused, "^outputs$"):
            self.verify(receipt)

    def test_foreign_session_and_receipt_paths_refuse(self):
        receipt = self.run_bridge()
        with self.assertRaisesRegex(bridge.BridgeRefused, "^session$"):
            bridge.verify(self.admission, legacy.pin("D:/Synthetic/other-session.json"), receipt)
        forged = dict(receipt, path=str(self.root / "different.json"))
        with self.assertRaisesRegex(bridge.BridgeRefused, "^path$"):
            self.verify(forged)

    def test_changed_materialized_input_refuses_on_closed_verify(self):
        receipt = self.run_bridge()
        (self.root / "outbound" / "android-origin.json").write_bytes(b"replaced")
        with self.assertRaises(ValueError):
            self.verify(receipt)


if __name__ == "__main__":
    unittest.main()
