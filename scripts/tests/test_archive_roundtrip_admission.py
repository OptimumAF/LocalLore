"""Host-only tests for the fixed SDK25 prepared-run gate."""
import copy
from pathlib import PureWindowsPath
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import archive_roundtrip_admission as gate
from benchmarks import archive_roundtrip_prepare as preparation
from benchmarks import receipt_avd_environment as env
from scripts.tests.test_owned_archive_roundtrip_profile import admission
from scripts.tests.test_owned_target_contract import pin


class OperatorAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.data = {}
        self.a = admission()
        self.a["root"], self.a["server"]["root"] = str(gate.OWNED_ROOT), str(gate.OWNED_ROOT / "server")
        self.a["seconds"] = self.a["server"]["seconds"] = gate.OWNER_SECONDS
        self.admit = self.add(gate.ADMISSION, self.a)
        prepared = pin(PureWindowsPath(self.a["guest"]["root"]) / "prepared-v1.json")
        result = pin(PureWindowsPath(self.a["guest"]["root"]) / "prepare-result-v1.json")
        self.prepare = pin(gate.PREPARE_PROPOSAL)
        self.proposal = dict(paths={"root": self.a["guest"]["root"]}, prepare_proposal=self.prepare,
                             prepared=prepared, prepare_result=result, memory_mib=8192, cores=4,
                             max_seconds=gate.GUEST_SECONDS, adb_path=self.a["server"]["adb"]["path"],
                             sdk=str(PureWindowsPath(self.a["guest"]["emulator"]["path"]).parent.parent))
        proposal_pin = self.add(gate.RUN_PROPOSAL, self.proposal)
        auth = dict(version=1, phase="run", proposal_sha256=proposal_pin["sha256"],
                    allow_environment_calls=True, root_go_pending=False, run_scope=gate.contract.RUN_SCOPE)
        self.a["guest"]["proposal"] = proposal_pin
        self.a["guest"]["authorization"] = self.add(gate.RUN_AUTHORIZATION, auth)
        self.entry = dict(state="prepared", reserved_bytes=gate.storage.RESERVATION_BYTES,
                          proposal_sha256=self.prepare["sha256"], closure=None, recovery=None,
                          retirement=None, retirement_receipt=None)
        self.ledger = self.add(gate.storage.DEFAULT_REGISTRY / "ledger-v1.json", {"version": 2})
        self.prepare_receipt = pin(str(preparation.RESULT))
        self.authority = self.add(gate.AUTHORITY, dict(
            version=1, scope=gate.SCOPE, admission=self.admit, ledger=self.ledger, prepare_receipt=self.prepare_receipt,
            approval_reference="synthetic approval", allow_one_boot=True, allow_prepare=False,
            allow_model=False, allow_retirement=False, owner_seconds=gate.OWNER_SECONDS,
            guest_seconds=gate.GUEST_SECONDS))
        self.enterContext(patch.object(gate, "_at", side_effect=self.at))
        self.enterContext(patch.object(gate.lifecycle, "_read", side_effect=self.read))
        self.enterContext(patch.object(gate.output_control, "validate_output", side_effect=self.new))
        self.enterContext(patch.object(env, "create_json", side_effect=self.add))
        self.enterContext(patch.object(gate.os.path, "lexists", side_effect=self.exists))
        self.enterContext(patch.object(env, "validate_proposal"))
        self.authorize = self.enterContext(patch.object(env, "authorize",
                                                         side_effect=lambda *args, **kwargs: copy.deepcopy(self.proposal)))
        self.prepared = self.enterContext(patch.object(env, "verify_prepared"))
        self.receipt = self.enterContext(patch.object(preparation, "verify_receipt"))
        self.binding = self.enterContext(patch.object(env, "check_binding"))
        self.ledger_validate = self.enterContext(patch.object(gate.storage, "_validate"))
        self.enterContext(patch.object(gate.storage, "_entry", side_effect=lambda *args: self.entry))
        self.artifacts = self.enterContext(patch.object(gate.build, "verify_current"))
        self.sources = self.enterContext(patch.object(gate.contract, "revalidate_inputs"))
        self.enterContext(patch.object(subprocess, "Popen", side_effect=AssertionError("unexpected process")))

    def add(self, path, value):
        key = PureWindowsPath(str(path))
        bound = pin(key)
        self.data[key] = (bound, value)
        return bound

    def read(self, path, cap):
        bound, value = self.data[PureWindowsPath(str(path))]
        return bound, copy.deepcopy(value)

    def at(self, bound, path, cap=gate.lifecycle.RECORD_CAP):
        actual, value = self.read(path, cap)
        if bound != actual:
            raise ValueError("binding")
        return value

    def value(self, path):
        return self.data[PureWindowsPath(str(path))][1]

    def exists(self, path):
        return PureWindowsPath(str(path)) in self.data

    def new(self, path):
        if self.exists(path):
            raise FileExistsError
        return gate.ATTEMPT

    def test_read_only_preboot_checks_exact_fresh_context(self):
        context = gate.preboot(self.authority)
        self.assertEqual(context, dict(admission=self.a, admission_pin=self.admit, ledger=self.ledger,
                                       prepare_sha256=self.prepare["sha256"]))
        self.assertFalse(self.exists(gate.ATTEMPT))
        self.authorize.assert_called_once_with(str(gate.RUN_PROPOSAL), str(gate.RUN_AUTHORIZATION), "run",
            run_scope=gate.contract.RUN_SCOPE, expected_proposal_sha256=self.a["guest"]["proposal"]["sha256"])
        self.prepared.assert_called_once_with(self.proposal, initial=True)
        self.receipt.assert_called_once_with(self.prepare_receipt, self.proposal, self.a["artifacts"])
        self.sources.assert_called_once_with(self.a)
        self.artifacts.assert_called_once_with(self.a)
        self.ledger_validate.assert_called_once_with({"version": 2}, gate.storage.DEFAULT_REGISTRY)

    def test_generic_prepared_records_do_not_replace_the_scoped_receipt(self):
        self.receipt.side_effect = gate.AdmissionRefused("prepared")
        with self.assertRaisesRegex(gate.AdmissionRefused, "^prepared$"):
            gate.spend(self.authority)
        self.assertFalse(self.exists(gate.ATTEMPT))
        self.authorize.assert_not_called()
        self.prepared.assert_not_called()

    def test_one_shot_claim_and_revalidation(self):
        attempt = gate.spend(self.authority)
        self.assertTrue(self.exists(gate.ATTEMPT))
        self.assertTrue(self.value(gate.ATTEMPT)["no_retry"])
        self.assertEqual(gate.verify_spent(self.authority, attempt)["ledger"], self.ledger)
        with self.assertRaises(FileExistsError):
            gate.spend(self.authority)

    def test_authority_cannot_widen_scope_or_enable_other_operations(self):
        value = self.value(gate.AUTHORITY)
        original = copy.deepcopy(value)
        for key, changed in (("allow_prepare", True), ("allow_model", True), ("allow_retirement", True),
                             ("allow_one_boot", 1), ("owner_seconds", 1600), ("approval_reference", "\n"),
                             ("scope", "other")):
            with self.subTest(key=key):
                value.update(original)
                value[key] = changed
                with self.assertRaisesRegex(gate.AdmissionRefused, "^authority$"):
                    gate.preboot(self.authority)
        self.authorize.assert_not_called()

    def test_authority_pin_must_bind_exact_path_and_bytes(self):
        bad = dict(self.authority, sha256="a" * 64)
        with self.assertRaises(ValueError):
            gate.preboot(bad)
        self.authorize.assert_not_called()

    def test_unscoped_run_authorization_refuses_before_tool_readback(self):
        del self.value(gate.RUN_AUTHORIZATION)["run_scope"]
        with self.assertRaises(env.EnvironmentRefused):
            gate.preboot(self.authority)
        self.authorize.assert_not_called()

    def test_wrong_adb_and_foreign_prepare_paths_refuse_before_tool_readback(self):
        for key, wrong in (("adb_path", "C:/Synthetic/other.exe"), ("prepare_proposal", pin("D:/Other/prepare.json"))):
            with self.subTest(key=key):
                prior = self.proposal[key]
                self.proposal[key] = wrong
                with self.assertRaisesRegex(gate.AdmissionRefused, "^proposal$"):
                    gate.preboot(self.authority)
                self.proposal[key] = prior
        self.authorize.assert_not_called()

    def test_spent_owner_or_boot_claim_refuses_before_tool_readback(self):
        for path in (gate.OWNED_ROOT, PureWindowsPath(self.a["guest"]["root"]) / gate.contract.BOOT_CLAIM_FILE):
            with self.subTest(path=path):
                self.add(path, {})
                with self.assertRaisesRegex(gate.AdmissionRefused, "^already_used$"):
                    gate.preboot(self.authority)
                del self.data[PureWindowsPath(str(path))]
        self.authorize.assert_not_called()

    def test_ledger_requires_valid_v2_prepared_unrecovered_state(self):
        ledger_path = gate.storage.DEFAULT_REGISTRY / "ledger-v1.json"
        self.value(ledger_path)["version"] = 1
        with self.assertRaisesRegex(gate.AdmissionRefused, "^ledger_version$"):
            gate.preboot(self.authority)
        self.value(ledger_path)["version"] = 2
        for key, changed in (("state", "retained"), ("reserved_bytes", 1),
                             ("proposal_sha256", "f" * 64), ("recovery", {"old": True})):
            with self.subTest(key=key):
                previous = self.entry[key]
                self.entry[key] = changed
                with self.assertRaisesRegex(gate.AdmissionRefused, "^prepared$"):
                    gate.preboot(self.authority)
                self.entry[key] = previous
        self.authorize.assert_not_called()

    def test_existing_ledger_lock_refuses_before_spend(self):
        self.add(gate.storage.DEFAULT_REGISTRY / "admission.lock", {})
        with self.assertRaisesRegex(gate.AdmissionRefused, "^ledger_lock$"):
            gate.spend(self.authority)
        self.assertFalse(self.exists(gate.ATTEMPT))
        self.authorize.assert_not_called()

    def test_ledger_lock_during_verification_refuses_before_spend(self):
        self.prepared.side_effect = lambda *args, **kwargs: self.add(
            gate.storage.DEFAULT_REGISTRY / "admission.lock", {})
        with self.assertRaisesRegex(gate.AdmissionRefused, "^ledger_lock$"):
            gate.spend(self.authority)
        self.assertFalse(self.exists(gate.ATTEMPT))

    def test_changed_ledger_after_claim_refuses_handoff_and_keeps_claim(self):
        attempt = gate.spend(self.authority)
        self.entry["state"] = "retained"
        with self.assertRaisesRegex(gate.AdmissionRefused, "^prepared$"):
            gate.verify_spent(self.authority, attempt)
        self.assertTrue(self.exists(gate.ATTEMPT))

    def test_forged_claim_cannot_be_used_as_fresh_authority(self):
        attempt = gate.spend(self.authority)
        self.value(gate.ATTEMPT)["no_retry"] = False
        with self.assertRaisesRegex(gate.AdmissionRefused, "^attempt$"):
            gate.verify_spent(self.authority, attempt)


if __name__ == "__main__":
    unittest.main()
