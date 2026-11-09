"""Host-only ordered SDK25 return tests."""
import copy
from pathlib import PureWindowsPath
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_bridge as bridge
from benchmarks import archive_roundtrip_return as returning
from benchmarks import owned_archive_roundtrip_client as client
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner
from scripts.tests.test_archive_roundtrip_outbound import CaptureFixture, binding
from scripts.tests.test_owned_archive_roundtrip_profile import admission
from scripts.tests.test_owned_target_contract import pin


class ReturnTests(unittest.TestCase):
    def setUp(self):
        self.admission = admission()
        fixture = self.fixture = CaptureFixture(self.admission, {
            "windows-return.json": b"source", "windows-continued.json": b"continued",
            "android-origin.json": b"origin",
        }).ready()
        self.start = len(fixture.steps)
        self.capture = fixture.capture
        self.capture.count = self.start
        self.capture.lease.claim_once = Mock(side_effect=self.spend)
        self.claim = None
        self.claim_pin = pin(PureWindowsPath(self.admission["root"]) / "claims-v1" /
                             "archive_return_write-v1.json")
        bridge_root = fixture.root / "windows-continuation-v1"
        self.receipt = pin(bridge_root / "receipt.json")
        self.raw = {
            "android-return.json": b"fixed Windows return archive",
            "expected-android-final.json": b"fixed final oracle archive",
        }
        a = self.admission
        self.context = {
            "outputs": {name: binding(bridge_root / "windows" / name, data)
                        for name, data in self.raw.items()},
            "records": tuple(step["pin"] for step in fixture.steps),
            "installed": {
                "product_apk": {"uid": 10001, "path": "/data/app/~~token/" + contract.APP + "-token/base.apk",
                                "sha256": a["artifacts"]["product_apk"]["sha256"]},
                "test_apk": {"uid": 10002, "path": "/data/app/~~token/" + contract.TEST + "-token/base.apk",
                             "sha256": a["artifacts"]["test_apk"]["sha256"]},
            },
        }
        self.prefix = copy.deepcopy(fixture.steps[-6:])
        self.installed()
        marker = contract.read_argv(a, "owner-v1")
        fixture.step("owner-marker", marker, contract.MARKER)
        fixture.step(contract.RETURN_WRITE, contract.return_write_argv(a), b"",
                     self.context["outputs"]["android-return.json"], 120)
        fixture.step("return-readback", contract.read_argv(a, "android-return.json"),
                     self.raw["android-return.json"])
        fixture.step(contract.RETURN, contract.return_argv(a), fixture.first("archive_outbound")["raw"], seconds=120)
        fixture.step("owner-marker", marker, contract.MARKER)
        fixture.step("return-final", contract.read_argv(a, "android-final.json"),
                     self.raw["expected-android-final.json"])
        self.installed()
        original_pin = fixture._pin
        fixture._pin = lambda path: (self.claim_pin if PureWindowsPath(str(path)).name ==
                                     "archive_return_write-v1.json" else original_pin(path))
        fixture._at = self.read_claim
        fixture.require_current_clients = self.roster
        self.capture.shell = lambda argv, label, **opts: self.dispatch(argv, None, label, **opts)
        self.capture.stream = lambda argv, source, label, **opts: self.dispatch(argv, source, label, **opts)
        self.verify = self.enterContext(patch.object(bridge, "verify_context",
                                                      return_value=copy.deepcopy(self.context)))
        self.enterContext(patch.object(bridge, "_read", side_effect=self.read_source))
        self.enterContext(patch.object(owner, "VERIFIER", fixture))

    def dispatch(self, argv, source, label, *, seconds, cap):
        kind = contract.return_kind(argv, self.admission)
        if kind is not None:
            receipt, operation = self.capture._return_permit
            self.assertEqual(operation, (argv, source, label, seconds, cap, source is not None))
            returning.authorize_dispatch(self.capture, receipt, kind, operation)
        return self.fixture.dispatch(argv, label, source)

    def roster(self, root, count, session, admission):
        self.assertEqual(PureWindowsPath(str(root)), self.fixture.root)
        self.assertEqual(session, self.fixture.session_pin)
        self.assertEqual(admission, self.admission)
        if count != len(self.fixture.steps):
            raise returning.ReturnRefused("command_roster")
        return self.fixture.steps

    def installed(self):
        for step in self.prefix:
            op = step["operation"]
            self.fixture.step(step["label"], op["argv"], step["raw"], op["stdin"])

    def spend(self, kind, digest):
        self.assertEqual(kind, contract.RETURN_WRITE)
        self.assertIsNone(self.claim)
        session = self.fixture.session
        self.claim = contract.claim_record(session["admission"], session["caller"], kind, digest)

    def read_claim(self, binding, path):
        self.assertEqual(binding, self.claim_pin)
        self.assertEqual(PureWindowsPath(str(path)), PureWindowsPath(binding["path"]))
        if self.claim is None:
            raise FileNotFoundError
        return self.claim

    def read_source(self, source, path, cap):
        self.assertEqual(source, self.context["outputs"][path.name])
        self.assertEqual(cap, contract.MAX_BYTES)
        return self.raw[path.name]

    def run_return(self):
        return returning.run(self.capture, self.receipt)

    def replay(self):
        return returning.replay(self.admission, self.fixture.session_pin, self.receipt)

    def test_live_and_closed_replay_match_the_fixed_return_segment(self):
        result = self.run_return()
        self.assertEqual(self.verify.call_count, 5)
        self.verify.assert_called_with(self.admission, self.fixture.session_pin, self.receipt)
        self.assertEqual(result["final"], self.raw["expected-android-final.json"])
        self.assertTrue(result["instrumentation"]["passed"])
        self.assertEqual(len(result["records"]), 18)
        self.assertEqual(result["outbound_records"], self.context["records"])
        self.capture.lease.claim_once.assert_called_once()
        self.assertEqual(self.replay(), result)
        self.capture.lease.claim_once.assert_called_once()
        self.capture.close.assert_called_once_with()

    def test_second_attempt_refuses_before_any_further_dispatch(self):
        self.run_return()
        before = self.capture.count
        with self.assertRaisesRegex(returning.ReturnRefused, "^session$"):
            self.run_return()
        self.assertEqual(self.capture.count, before)
        self.capture.lease.claim_once.assert_called_once()

    def test_bridge_refusal_happens_before_queries_or_write(self):
        self.verify.side_effect = bridge.BridgeRefused("receipt")
        with self.assertRaises(bridge.BridgeRefused):
            self.run_return()
        self.assertEqual(self.capture.count, self.start)
        self.capture.lease.claim_once.assert_not_called()

    def test_wrong_outbound_command_count_refuses_before_return(self):
        self.capture.count -= 1
        with self.assertRaisesRegex(returning.ReturnRefused, "^session$"):
            self.run_return()
        self.capture.lease.claim_once.assert_not_called()

    def test_marker_refusal_happens_before_exclusive_write(self):
        step = self.fixture.steps[self.start + 6]
        self.fixture.set_raw(step, b"foreign marker")
        with self.assertRaisesRegex(returning.ReturnRefused, "^owner_marker$"):
            self.run_return()
        self.capture.lease.claim_once.assert_not_called()

    def test_failed_write_spends_claim_and_never_attempts_readback(self):
        step = self.fixture.first(contract.RETURN_WRITE)
        self.fixture.set_raw(step, b"unexpected write stdout")
        with self.assertRaisesRegex(returning.ReturnRefused, "^return_write$"):
            self.run_return()
        self.assertEqual(self.capture.count, step["index"])
        self.capture.lease.claim_once.assert_called_once()

    def test_wrong_readback_refuses_before_return_instrumentation(self):
        step = self.fixture.first("return-readback")
        self.fixture.set_raw(step, b"x" * len(step["raw"]))
        with self.assertRaisesRegex(returning.ReturnRefused, "^return_readback$"):
            self.run_return()
        self.assertEqual(self.capture.count, step["index"])
        self.capture.close.assert_called_once_with()

    def test_wrong_final_archive_refuses_after_terminal(self):
        self.fixture.set_raw(self.fixture.first("return-final"), b"wrong archive")
        with self.assertRaisesRegex(returning.ReturnRefused, "^final_archive$"):
            self.run_return()

    def test_dispatch_refuses_forged_return_permit_with_wrong_count(self):
        operation = returning._return_operation(self.admission)
        with self.assertRaisesRegex(returning.ReturnRefused, "^return_authority$"):
            returning.authorize_dispatch(self.capture, self.receipt, contract.RETURN, operation)
        self.assertEqual(self.capture.count, self.start)
        self.capture.lease.claim_once.assert_not_called()

    def test_dispatch_replays_readback_before_instrumentation(self):
        self.run_return()
        step = self.fixture.first("return-readback")
        self.capture.count = step["index"]
        self.fixture.set_raw(step, b"substituted readback")
        with self.assertRaisesRegex(returning.ReturnRefused, "^return_readback$"):
            returning.authorize_dispatch(self.capture, self.receipt, contract.RETURN,
                                        returning._return_operation(self.admission))

    def test_closed_replay_refuses_extra_records_after_return(self):
        self.run_return()
        self.fixture.step("extra", ["getprop", "sys.boot_completed"], b"1\n")
        with self.assertRaisesRegex(returning.ReturnRefused, "^command_roster$"):
            self.replay()

    def test_closed_replay_requires_original_write_claim(self):
        self.run_return()
        self.claim["operation_sha256"] = "f" * 64
        with self.assertRaises(contract.TargetRefused):
            self.replay()


class ReturnWireTests(unittest.TestCase):
    def setUp(self):
        self.admission = admission()
        self.capture = client.OwnedArchiveRoundtripSdkCapture.__new__(client.OwnedArchiveRoundtripSdkCapture)
        self.capture._admission = self.admission
        self.capture._poison = Mock()
        self.execute = self.enterContext(patch.object(client.wire._OwnedTargetSdkCapture,
                                                       "_execute", return_value=b""))

    def test_generic_wire_refuses_all_return_authority_without_permit(self):
        for argv in (contract.return_argv(self.admission), contract.return_write_argv(self.admission),
                     contract.read_argv(self.admission, "android-return.json"),
                     contract.read_argv(self.admission, "android-final.json")):
            with self.assertRaises(client.wire.ClientRefused):
                self.capture._execute(argv, None, "unauthorized", 15, 4096, False)
        self.execute.assert_not_called()

    def test_exact_permit_consumed_before_wire_and_cannot_reuse(self):
        argv = contract.return_argv(self.admission)
        receipt = pin("D:/Synthetic/receipt.json")
        operation = (argv, None, contract.RETURN, 120, contract.MAX_BYTES, False)
        self.capture._return_permit = (receipt, operation)
        with patch.object(returning, "authorize_dispatch") as authorize:
            self.capture._execute(*operation)
        authorize.assert_called_once_with(self.capture, receipt, contract.RETURN, operation)
        self.assertIsNone(self.capture._return_permit)
        with self.assertRaises(client.wire.ClientRefused):
            self.capture._execute(argv, None, contract.RETURN, 120, contract.MAX_BYTES, False)
        self.execute.assert_called_once()

    def test_contract_rejects_unbound_host_file_and_foreign_return_phase(self):
        a = self.admission
        path = PureWindowsPath(a["root"]) / contract.TRANSFER_OUTPUT / contract.BRIDGE_DIRECTORY
        source = pin(path / "windows/android-return.json")
        argv = contract.return_write_argv(a)
        self.assertIn("set -C && test ! -e", argv[-1])
        self.assertIn("sha256sum", argv[-1])
        contract.validate_operation(dict(argv=argv, stdin=source), a)
        for wrong in (None, dict(source, bytes=0), dict(source, bytes=contract.MAX_BYTES + 1),
                      dict(source, path="D:/Synthetic/other/android-return.json")):
            with self.assertRaises(contract.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=wrong), a)
        foreign = contract.return_argv(a)
        foreign[12] = "transfer-" + "f" * 32
        with self.assertRaises(contract.TargetRefused):
            contract.validate_operation(dict(argv=foreign, stdin=None), a)


if __name__ == "__main__":
    unittest.main()
