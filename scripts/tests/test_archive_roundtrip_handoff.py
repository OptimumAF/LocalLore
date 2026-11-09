"""Host-only tests for the SDK25 prepared owner handoff."""
import copy
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_handoff as handoff
from benchmarks import owned_archive_roundtrip_owner as owner
from benchmarks import receipt_avd_environment as env
from scripts.tests.test_owned_archive_roundtrip_profile import admission
from scripts.tests.test_owned_target_contract import pin


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.a = admission()
        self.admit = pin(handoff.admission.ADMISSION)
        self.authority = pin(handoff.admission.AUTHORITY)
        self.attempt = pin(handoff.admission.ATTEMPT)
        self.ledger = pin("D:/Synthetic/ledger.json")
        self.context = dict(admission=self.a, admission_pin=self.admit, ledger=self.ledger,
                            prepare_sha256="c" * 64)
        self.bound = pin(handoff.HANDOFF)
        self.supervisor = dict(pid=8000, creation_filetime=100, executable=self.a["python"]["executable"]["path"])
        self.parent = dict(pid=8001, creation_filetime=200, executable=self.supervisor["executable"])
        self.record = dict(version=1, scope=handoff.SCOPE, authority=self.authority, attempt=self.attempt,
                           admission=self.admit, supervisor=self.supervisor, began_ns=handoff.NS,
                           until_ns=(handoff.MAX_SECONDS + 1) * handoff.NS)
        self.enterContext(patch.dict(handoff.os.environ, {handoff.HANDOFF_ENV: self.bound["sha256"]}))
        self.enterContext(patch.object(handoff.time, "monotonic_ns", return_value=2 * handoff.NS))
        self.enterContext(patch.object(handoff.lifecycle, "_read",
                                       side_effect=lambda *args: (self.bound, copy.deepcopy(self.record))))
        self.enterContext(patch.object(handoff.lifecycle, "_at",
                                       side_effect=lambda *args: copy.deepcopy(self.record)))
        self.lineage = self.enterContext(patch.object(handoff, "_lineage"))
        self.claim = self.enterContext(patch.object(handoff.admission, "verify_spent", return_value=self.context))
        self.enterContext(patch.object(env, "check_binding"))
        self.enterContext(patch.object(subprocess, "Popen", side_effect=AssertionError("unexpected process")))

    def test_parent_and_worker_verify_same_context_with_distinct_root_state(self):
        self.assertEqual(handoff.verify_boot(self.admit, self.a), (self.bound, self.record, self.context))
        self.claim.assert_called_once_with(self.authority, self.attempt, owner_created=False)
        self.lineage.assert_called_with(self.record, None)
        self.assertEqual(handoff.verify_boot(self.admit, self.a, parent=self.parent)[2], self.context)
        self.claim.assert_called_with(self.authority, self.attempt, owner_created=True)
        self.lineage.assert_called_with(self.record, self.parent)

    def test_bad_env_digest_refuses_before_claim(self):
        with patch.dict(handoff.os.environ, {handoff.HANDOFF_ENV: "0" * 64}):
            with self.assertRaisesRegex(handoff.admission.AdmissionRefused, "^handoff$"):
                handoff.verify_boot(self.admit, self.a)
        self.claim.assert_not_called()

    def test_wrong_admission_or_stale_launch_window_refuses(self):
        with self.assertRaisesRegex(handoff.admission.AdmissionRefused, "^handoff$"):
            handoff.verify_boot(pin("D:/Synthetic/other.json"), self.a)
        self.record["until_ns"] = 500 * handoff.NS
        with self.assertRaisesRegex(handoff.admission.AdmissionRefused, "^deadline$"):
            handoff.verify_boot(self.admit, self.a)
        self.claim.assert_not_called()

    def test_claim_cannot_substitute_admission(self):
        self.context["admission_pin"] = pin("D:/Synthetic/other.json")
        with self.assertRaisesRegex(handoff.admission.AdmissionRefused, "^admission$"):
            handoff.verify_boot(self.admit, self.a)

    def test_handoff_writer_only_uses_exact_record_and_path(self):
        with (patch.object(handoff.output_control, "validate_output", return_value=handoff.HANDOFF) as output,
              patch.object(handoff, "_supervisor_identity", return_value=self.supervisor),
              patch.object(env, "create_json") as create):
            self.assertEqual(handoff.write(self.authority, self.attempt, began_ns=self.record["began_ns"],
                                           until_ns=self.record["until_ns"]), self.bound)
        output.assert_called_once_with(str(handoff.HANDOFF))
        create.assert_called_once_with(handoff.HANDOFF, self.record)


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.supervisor = dict(pid=8000, creation_filetime=100, executable="C:/Synthetic/python.exe")
        self.parent = dict(pid=8001, creation_filetime=200, executable=self.supervisor["executable"])
        self.api = SimpleNamespace(current_job_pids=Mock(return_value=[8000, 8001, 8002]),
                                   parent_pid=Mock(return_value=8000))
        self.handles = SimpleNamespace(add=Mock(return_value=("held-parent", self.parent)),
                                       guard=Mock(), close=Mock(return_value=True))
        self.enterContext(patch.object(handoff.shared, "_ProcessApi", return_value=self.api))
        self.enterContext(patch.object(handoff.shared.primitives, "ProcessHandles", return_value=self.handles))

    def test_fixed_owner_and_worker_ancestry_with_closed_handles(self):
        record = {"supervisor": self.supervisor}
        with patch.object(handoff.os, "getpid", return_value=8001), patch.object(handoff.os, "getppid", return_value=8000):
            handoff._lineage(record, None)
        with patch.object(handoff.os, "getpid", return_value=8002), patch.object(handoff.os, "getppid", return_value=8001):
            handoff._lineage(record, self.parent)
        self.handles.add.assert_any_call(8000, self.supervisor)
        self.handles.add.assert_any_call(8001, self.parent)
        self.api.parent_pid.assert_called_once_with("held-parent")
        self.assertEqual(self.handles.close.call_count, 2)

    def test_wrong_job_or_parent_refuses(self):
        record = {"supervisor": self.supervisor}
        with patch.object(handoff.os, "getpid", return_value=9000), patch.object(handoff.os, "getppid", return_value=8000):
            with self.assertRaisesRegex(handoff.admission.AdmissionRefused, "^identity$"):
                handoff._lineage(record, None)
        with patch.object(handoff.os, "getpid", return_value=8002), patch.object(handoff.os, "getppid", return_value=9000):
            with self.assertRaisesRegex(handoff.admission.AdmissionRefused, "^identity$"):
                handoff._lineage(record, self.parent)
        self.assertEqual(self.handles.close.call_count, 2)


class OwnerHandoffTests(unittest.TestCase):
    def setUp(self):
        self.a = admission()
        self.context = {"ledger": pin("D:/Synthetic/ledger.json"), "prepare_sha256": "c" * 64}
        self.runtime = owner._ArchiveRuntime.__new__(owner._ArchiveRuntime)
        self.runtime._launch = (pin(handoff.HANDOFF), {}, self.context)
        self.runtime.admission = self.a
        self.runtime.proposal = {"prepare_proposal": {"sha256": "c" * 64}}
        self.runtime._launch_guard = Mock()

    def test_retain_uses_exact_ledger_and_prepare_digest_under_shared_lock(self):
        with patch.object(env, "storage_transition") as transition:
            self.runtime._retain_guest()
        guest = self.a["guest"]
        transition.assert_called_once_with(owner.storage.record_state, Path(guest["root"]), "retained",
            proposal_sha256=guest["proposal"]["sha256"], expected_prepare_sha256="c" * 64,
            expected_ledger=self.context["ledger"])
        self.assertEqual(self.runtime._launch_guard.call_count, 2)

    def test_changed_prepare_digest_refuses_before_transition(self):
        self.runtime.proposal["prepare_proposal"]["sha256"] = "d" * 64
        with patch.object(env, "storage_transition") as transition:
            with self.assertRaises(owner.shared.OwnerRefused):
                self.runtime._retain_guest()
        transition.assert_not_called()

    def test_transition_refusal_has_no_second_guard_or_fallback(self):
        with patch.object(env, "storage_transition", side_effect=env.EnvironmentRefused("storage_ledger_changed")) as run:
            with self.assertRaises(env.EnvironmentRefused):
                self.runtime._retain_guest()
        self.runtime._launch_guard.assert_called_once()
        run.assert_called_once()

    def test_private_server_refuses_drift_before_dispatch(self):
        with (patch.object(env, "check_binding", side_effect=env.EnvironmentRefused("binding")) as check,
              patch.object(owner.shared._TargetRuntimeCore, "start_server") as start):
            with self.assertRaises(env.EnvironmentRefused):
                self.runtime.start_server()
        check.assert_called_once_with(self.context["ledger"])
        start.assert_not_called()

    def test_last_pre_boot_guard_checks_live_handoff_after_shared_checks(self):
        self.runtime.guest_child = None
        order = Mock()
        self.runtime._launch_guard.side_effect = handoff.admission.AdmissionRefused("handoff")
        order.attach_mock(self.runtime._launch_guard, "handoff")
        with patch.object(owner.shared._TargetRuntimeCore, "guard") as shared:
            order.attach_mock(shared, "shared")
            with self.assertRaises(handoff.admission.AdmissionRefused):
                self.runtime.guard()
        self.assertEqual([call[0] for call in order.mock_calls], ["shared", "handoff"])

    def test_supervisor_loss_after_boot_claim_never_launches_emulator(self):
        runtime = self.runtime
        runtime.guest_child = None
        runtime.worker = {"pid": 8002}
        runtime.binding = pin("D:/Synthetic/admission.json")
        runtime.root = Path(runtime.admission["root"])
        runtime._launch_guard.side_effect = [None, None, None, handoff.admission.AdmissionRefused("handoff")]
        with (patch.object(owner.shared._TargetRuntimeCore, "guard"),
              patch.object(env, "verify_prepared"),
              patch.object(env, "check_binding"),
              patch.object(env, "storage_transition") as retained,
              patch.object(env, "create_json") as claim,
              patch.object(env, "scoped_env", return_value={}),
              patch.object(env, "emulator_command", return_value=["emulator.exe"]),
              patch.object(owner.shared.server_contract, "child_environment", return_value={}),
              patch.object(owner.shared.primitives, "ServerCapture"),
              patch.object(subprocess, "Popen") as launch):
            with self.assertRaisesRegex(handoff.admission.AdmissionRefused, "^handoff$"):
                runtime.start_guest()
        retained.assert_called_once()
        claim.assert_called_once()
        self.assertEqual(claim.call_args.args[0].name, owner.contract.BOOT_CLAIM_FILE)
        launch.assert_not_called()

    def test_parent_admission_callback_is_exact_and_pre_dispatch(self):
        admitted = self.a
        admit_pin = pin(handoff.admission.ADMISSION)
        argv = ["--admission", str(handoff.admission.ADMISSION), "--admission-sha256", admit_pin["sha256"]]
        with (patch.dict(owner.os.environ, {handoff.HANDOFF_ENV: "a" * 64}),
              patch.object(handoff.lifecycle, "_read", return_value=(admit_pin, admitted)),
              patch.object(handoff, "verify_boot") as verify,
              patch.object(owner.shared, "_main_profile") as main):
            main.side_effect = lambda args, **kwargs: kwargs["_admission_check"](admitted)
            owner.main(argv)
            verify.assert_called_once_with(admit_pin, admitted)
            with self.assertRaises(owner.shared.OwnerRefused):
                owner.main(argv[:3] + ["b" * 64])


if __name__ == "__main__":
    unittest.main()
