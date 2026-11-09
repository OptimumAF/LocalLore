"""Host-only SDK25 controller and owner closure tests."""
import copy
from pathlib import Path, PureWindowsPath
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_lifecycle as lifecycle
from benchmarks import receipt_avd_environment as env
from scripts.tests.test_owned_archive_roundtrip_profile import admission
from scripts.tests import test_owned_target_contract as legacy

contract = lifecycle.contract


def running(admitted):
    value = legacy.running(admitted)
    value["protocol"] = contract.PROTOCOL
    return value


def caller(value):
    return dict(pid=7106, creation_filetime=107106, executable=value["python"]["executable"]["path"])


class DriveTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.admission = admission()
        self.admission["seconds"] = self.admission["server"]["seconds"] = 1700
        self.admission["root"], self.admission["server"]["root"] = str(self.temp), str(self.temp / "server")
        self.running = running(self.admission)
        self.admit = legacy.pin("D:/Synthetic/admission.json")
        self.live = legacy.pin("D:/Synthetic/running-v1.json")
        self.caller = caller(self.running)
        self.exchange = {name: legacy.pin("D:/Synthetic/" + name) for name in ("session", "bridge", "final")}
        self.observer = SimpleNamespace(caller=self.caller, guard=Mock(), close=Mock(return_value=True))
        self.capture = SimpleNamespace(clean=False)
        self.enterContext(patch.object(lifecycle, "_inputs", return_value=(self.admission, self.running)))
        self.enterContext(patch.object(lifecycle.owner, "LiveOwnedArchiveRoundtripTarget", return_value=self.observer))
        self.enterContext(patch.object(lifecycle.client, "OwnedArchiveRoundtripSdkCapture", return_value=self.capture))
        self.native = self.enterContext(patch.object(lifecycle.final, "exchange", return_value=self.exchange))
        self.verify_exchange = self.enterContext(patch.object(lifecycle, "_verify_exchange"))
        self.output = self.temp / lifecycle.outbound.OUTPUT
        if self.temp.drive.upper() != "D:":
            def bounded(path, cap):
                raw = env.safe_path(path).read_bytes()
                if len(raw) > cap:
                    raise ValueError("size")
                return raw

            def read(pin, path, cap):
                raw = bounded(path, cap)
                if lifecycle.bridge._pin_bytes(path, raw) != pin:
                    raise ValueError("binding")
                return raw

            def new(path):
                result = Path(path)
                if result.exists():
                    raise FileExistsError
                return result

            self.enterContext(patch.object(lifecycle.bridge.files, "_read", side_effect=bounded))
            self.enterContext(patch.object(lifecycle.bridge, "_read", side_effect=read))
            self.enterContext(patch.object(lifecycle.output_control, "validate_output", side_effect=new))

    def drive(self):
        return lifecycle.drive(self.admit, self.live)

    def test_exchange_verified_then_shared_stop_and_observer_receipt(self):
        def verify_before_stop(*args):
            self.assertFalse((self.temp / "stop-v1.json").exists())
        self.verify_exchange.side_effect = verify_before_stop
        proof = self.drive()
        self.assertEqual(Path(proof["path"]), self.output / lifecycle.RESULT)
        stop = env.read_json(self.temp / "stop-v1.json")
        self.assertEqual(stop, dict(version=1, protocol=contract.PROTOCOL,
                                    admission_sha256=self.admit["sha256"], action="stop"))
        self.assertFalse((self.temp / "stop.pending-v1.json").exists())
        self.verify_exchange.assert_called_once_with(self.admit, self.live, self.admission, self.running,
                                                     self.caller, self.exchange)
        self.observer.guard.assert_any_call(min_seconds=lifecycle.SECONDS + lifecycle.STOP_RESERVE)
        self.observer.close.assert_called_once_with()

    def test_exchange_failure_preserves_attempt_closes_observer_and_never_stops(self):
        self.native.side_effect = RuntimeError("child failure")
        with self.assertRaises(RuntimeError):
            self.drive()
        self.assertTrue(self.output.is_dir())
        self.assertFalse((self.temp / "stop-v1.json").exists())
        self.assertFalse((self.output / lifecycle.RESULT).exists())
        self.observer.close.assert_called_once_with()

    def test_uncertain_observer_close_refuses_result_and_retains_stop(self):
        self.observer.close.return_value = False
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^observer_cleanup$"):
            self.drive()
        self.assertTrue((self.temp / "stop-v1.json").is_file())
        self.assertFalse((self.output / lifecycle.RESULT).exists())

    def test_exchange_error_with_unknown_observer_cleanup_is_distinct(self):
        self.native.side_effect = RuntimeError("transfer failure")
        self.observer.close.return_value = False
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^observer_cleanup$") as error:
            self.drive()
        self.assertIsInstance(error.exception.__context__, RuntimeError)
        self.assertFalse((self.temp / "stop-v1.json").exists())

    def test_inadequate_owner_budget_refuses_before_exchange(self):
        self.admission["seconds"] = 1200
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^controller_budget$"):
            self.drive()
        self.native.assert_not_called()
        self.observer.guard.assert_not_called()

    def test_existing_stop_is_never_overwritten(self):
        existing = self.temp / "stop-v1.json"
        existing.write_bytes(b"prior stop")
        with self.assertRaises((FileExistsError, ValueError)):
            self.drive()
        self.assertEqual(existing.read_bytes(), b"prior stop")
        self.native.assert_not_called()
        self.assertFalse((self.output / lifecycle.RESULT).exists())

    def test_controller_cannot_reuse_owner_identity(self):
        self.observer.caller = self.running["owner"]
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^controller_identity$"):
            self.drive()
        self.native.assert_not_called()
        self.observer.close.assert_called_once_with()


class ClosureTests(unittest.TestCase):
    def setUp(self):
        a = self.admission = admission()
        self.running = running(a)
        self.caller = caller(self.running)
        self.owner = self.running["owner"]
        self.root = PureWindowsPath(a["root"])
        self.guest = PureWindowsPath(a["guest"]["root"])
        self.data = {}
        self.admit = self.add("D:/Synthetic/admission.json", a)
        self.running["admission"] = self.admit
        self.live = self.add(self.root / "running-v1.json", self.running)
        self.request = self.add(self.root / "request-v1.json", dict(
            version=1, protocol=contract.PROTOCOL, admission=self.admit, validated_admission=a,
            owner=self.owner, sources=a["sources"], python=a["python"],
            worker_script=legacy.pin("D:/Synthetic/owner.py"), owner_seconds=a["seconds"] + 30))
        self.started = self.add(self.root / "started-v1.json", dict(worker=self.running["worker"],
                                                                  request=self.request))
        self.owner_result = self.add(self.root / "owner-result-v1.json", dict(status="child_exited"))
        self.worker_result = self.add(self.root / "worker-result-v1.json", {})
        self.after = self.add(self.root / "after-v1.json", dict(admission=self.admit, sources=a["sources"],
            python=a["python"], tools=a["server"]["tools"], owner=self.owner, process_handles_closed=True))
        self.public = self.add(self.root / "result-v1.json", dict(
            version=1, protocol=contract.PROTOCOL, admission=self.admit, request=self.request,
            started=self.started, worker_result=self.worker_result, owner=self.owner_result, after=self.after,
            qualified_target=True, reason="stop_requested", feature_acceptance=False))
        self.closure = self.add(self.guest / "guest-storage-closure-v1.json", dict(
            version=1, proposal_sha256=a["guest"]["proposal"]["sha256"], closure_verified=True,
            cleanup_complete=True, admission=self.admit, owner_result=self.owner_result,
            worker_result=self.worker_result, after=self.after))
        self.ledger = legacy.pin("D:/Synthetic/ledger-v1.json")
        self.entry = dict(state="closed", proposal_sha256=a["guest"]["proposal"]["sha256"],
                          recovery=None, retirement=None, closure=self.closure)
        self.stop = self.add(self.root / "stop-v1.json", dict(version=1, protocol=contract.PROTOCOL,
                                                admission_sha256=self.admit["sha256"], action="stop"))
        self.exchange = {name: legacy.pin("D:/Synthetic/" + name) for name in ("session", "bridge", "final")}
        self.controller = self.add(self.root / lifecycle.outbound.OUTPUT / lifecycle.RESULT, dict(
            version=1, scope=lifecycle.SCOPE, admission=self.admit, running=self.live, caller=self.caller,
            exchange=self.exchange, stop=self.stop, observer_closed=True))
        self.session = legacy.session(a)
        self.session.update(admission=self.admit, running=self.live, descriptor=self.running, caller=self.caller)
        self.worker = dict(reason="stop_requested", stop_requested=True, running=self.live,
                           cleanup={key: True for key in contract.CLEANUP_KEYS})
        self.enterContext(patch.object(lifecycle, "_read", side_effect=self.read))
        self.enterContext(patch.object(lifecycle, "_at", side_effect=self.at))
        self.enterContext(patch.object(lifecycle, "_ledger", return_value=(self.ledger, self.entry)))
        self.enterContext(patch.object(env, "check_binding"))
        self.owner_ok = self.enterContext(patch.object(lifecycle.process, "_owner_ok", return_value=True))
        self.worker_verify = self.enterContext(patch.object(lifecycle.owner.VERIFIER, "verify_owned_target_result",
                                                            return_value=self.worker))
        self.enterContext(patch.object(lifecycle.outbound, "_session", return_value=self.session))
        self.final = self.enterContext(patch.object(lifecycle.final, "verify"))

    def add(self, path, value):
        pin = legacy.pin(PureWindowsPath(path))
        self.data[PureWindowsPath(path)] = (pin, value)
        return pin

    def read(self, path, cap=lifecycle.RECORD_CAP):
        pin, value = self.data[PureWindowsPath(str(path))]
        return pin, copy.deepcopy(value)

    def at(self, pin, path, cap=lifecycle.RECORD_CAP):
        actual, value = self.read(path, cap)
        if pin != actual:
            raise ValueError("binding")
        return value

    def value(self, pin):
        return self.data[PureWindowsPath(pin["path"])][1]

    def verify(self, **overrides):
        arguments = dict(expected_owner=self.owner, expected_caller=self.caller)
        arguments.update(overrides)
        return lifecycle.verify(self.admit, self.live, self.controller, **arguments)

    def test_full_controller_process_and_closed_ledger_bindings(self):
        self.assertEqual(self.verify(), dict(owner=self.public, closure=self.closure, ledger=self.ledger,
                                            controller=self.controller, final=self.exchange["final"]))
        self.worker_verify.assert_called_once_with(self.worker_result, self.admission, self.admit,
                                                   self.request, self.running["worker"])
        self.final.assert_called_once_with(self.admission, self.exchange["session"],
                                           self.exchange["bridge"], self.exchange["final"])

    def test_closed_ledger_v1_entry_needs_no_recovery_field(self):
        del self.entry["recovery"]
        self.assertEqual(self.verify()["closure"], self.closure)

    def test_wrong_held_identities_fail(self):
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^owner$"):
            self.verify(expected_owner=dict(self.owner, creation_filetime=1))
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^controller_result$"):
            self.verify(expected_caller=dict(self.caller, creation_filetime=1))

    def test_changed_session_binding_refuses_before_owner_replay(self):
        self.session["running"] = legacy.pin("D:/Synthetic/other-running.json")
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^session$"):
            self.verify()
        self.worker_verify.assert_not_called()

    def test_foreign_stop_refuses_before_transfer_replay(self):
        self.value(self.stop)["admission_sha256"] = "f" * 64
        with self.assertRaises(contract.TargetRefused):
            self.verify()
        self.final.assert_not_called()

    def test_controller_uncertain_close_cannot_qualify(self):
        self.value(self.controller)["observer_closed"] = False
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^controller_result$"):
            self.verify()

    def test_unqualified_owner_or_incomplete_worker_cleanup_refuses(self):
        self.owner_ok.return_value = False
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^owner$"):
            self.verify()
        self.owner_ok.return_value = True
        key = next(iter(contract.CLEANUP_KEYS))
        self.worker["cleanup"][key] = False
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^worker_cleanup$"):
            self.verify()

    def test_wrong_closure_or_nonclosed_ledger_never_qualifies(self):
        value = self.value(self.closure)
        value["cleanup_complete"] = False
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^closure$"):
            self.verify()
        value["cleanup_complete"] = True
        self.entry["state"] = "retained"
        with self.assertRaisesRegex(lifecycle.LifecycleRefused, "^ledger$"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
