"""Host-only run-input tests. No SDK, live ledger, credential or guest access."""
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_run_inputs as inputs
from scripts.tests.test_owned_archive_roundtrip_profile import admission
from scripts.tests.test_owned_target_contract import pin

gate = inputs.gate
env = inputs.env


class RunInputFixture(unittest.TestCase):
    def setUp(self):
        self.receipt = pin(str(inputs.preparation.RESULT))
        self.installation = pin(str(inputs.INSTALLATION))
        self.run = pin(str(gate.RUN_PROPOSAL))
        self.ledger = pin(str(inputs.preparation.LEDGER))
        self.authority = pin(str(gate.AUTHORITY))
        self.prepare_pins = dict(
            prepare_proposal=pin(str(gate.PREPARE_PROPOSAL)),
            prepared=pin(str(inputs.preparation.GUEST / "prepared-v1.json")),
            prepare_result=pin(str(inputs.preparation.GUEST / "prepare-result-v1.json")),
        )
        self.value = admission()
        self.sdk = Path("C:/Synthetic/SDK")
        self.tools = self.sdk / "platform-tools"
        self.emulator = self.sdk / "emulator"
        self.source = pin("D:/Synthetic/current/benchmarks/native/deny_adb_client.c",
                          size=189, sha=inputs.REFUSER_SOURCE_SHA256)
        self.files = {
            name: pin(str(self.tools / name), sha=inputs.server.ADB_SHA256 if name == "adb.exe" else "c" * 64)
            for name in inputs.server.TOOL_NAMES
        }
        self.proposal = dict(
            paths={"root": str(inputs.preparation.GUEST)}, sdk=str(self.sdk), adb_path=str(self.tools / "adb.exe"),
            memory_mib=8192, cores=4, max_seconds=gate.GUEST_SECONDS,
            bindings=[*self.files.values(), pin(str(self.emulator / "emulator.exe")),
                      pin(str(self.emulator / "qemu/windows-x86_64/qemu-system-x86_64-headless.exe"))],
            **self.prepare_pins,
        )
        self.installed = dict(version=1, refuser=pin("D:/Synthetic/deny-adb-client.exe",
                                                   size=95_744, sha=inputs.REFUSER_SHA256),
                              capabilities=pin("D:/Synthetic/capabilities.json"),
                              source_review=pin("D:/Synthetic/adb-source-review.md"),
                              compatibility=pin("D:/Synthetic/compatibility.md"))
        self.artifacts = self.value["artifacts"]
        self.authorization = dict(version=1, phase="run", run_scope=inputs.contract.RUN_SCOPE,
                                  proposal_sha256=self.run["sha256"], allow_environment_calls=True,
                                  root_go_pending=False)
        self.value["guest"]["authorization"] = inputs._pin(gate.RUN_AUTHORIZATION, self.authorization)
        self.plan = inputs._review(self.receipt, self.installation, self.run, self.ledger, self.value)
        self.plan_pin = inputs._pin(gate.CONTROL / "unused.json", self.plan)
        self.plan_pin["path"] = str(inputs._plan_path(self.plan_pin["sha256"]))
        self.approval = dict(admission=self.plan["admission"], ledger=self.ledger, prepare_receipt=self.receipt)
        self.check = self.enterContext(patch.object(env, "check_binding"))


class BindingTests(RunInputFixture):
    def setUp(self):
        super().setUp()
        self.enterContext(patch.object(inputs, "_at", return_value=self.installed))
        self.enterContext(patch.object(inputs.contract, "source_bindings", return_value=self.value["sources"]))
        self.enterContext(patch.object(inputs.python_tools, "_python_bindings", return_value=self.value["python"]))
        self.enterContext(patch.object(env, "token_path", return_value="C:/Synthetic/.emulator_console_auth_token"))
        self.source_read = self.enterContext(patch.object(env, "binding", return_value=self.source))
        self.build = self.enterContext(patch.object(gate.build, "verify_current"))
        self.server = self.enterContext(patch.object(inputs.server, "revalidate_inputs"))

    def prospective(self):
        return inputs._prospective(self.receipt, self.installation, self.run, self.proposal, self.artifacts)

    def test_prospective_values_use_real_contract_and_fixed_tool_join(self):
        auth, value = self.prospective()
        self.assertEqual(auth, self.authorization)
        self.assertEqual(value["guest"]["authorization"], inputs._pin(gate.RUN_AUTHORIZATION, auth))
        self.assertEqual(value["server"]["adb"], self.files["adb.exe"])
        self.assertEqual(value["server"]["tools"], [self.files[name] for name in sorted(inputs.server.TOOL_NAMES)])
        self.assertEqual(value["server"]["auth_key"], str(Path("C:/Synthetic/.android/adbkey")))
        self.assertEqual(value["guest"]["root"], str(inputs.preparation.GUEST))
        self.assertEqual(value["guest"]["refuser_source"], self.source)
        self.assertEqual(value["guest"]["max_seconds"], gate.GUEST_SECONDS)
        self.assertEqual(value["root"], str(gate.OWNED_ROOT))
        self.build.assert_called_once_with(value)
        self.server.assert_called_once_with(value["server"])
        self.source_read.assert_called_once_with(inputs.ROOT / "benchmarks/native/deny_adb_client.c")
        self.assertNotIn(value["server"]["auth_key"], [call.args[0]["path"] for call in self.check.call_args_list])

    def test_run_id_and_authorization_stay_stable_for_a_fresh_ledger_review(self):
        auth, value = self.prospective()
        first = inputs._review(self.receipt, self.installation, self.run, self.ledger, value)
        second = inputs._review(self.receipt, self.installation, self.run, dict(self.ledger, sha256="e" * 64), value)
        self.assertEqual(first["admission"], second["admission"])
        self.assertEqual(first["authorization"], second["authorization"])
        self.assertNotEqual(env.encoded(first), env.encoded(second))
        self.assertEqual(self.prospective(), (auth, value))

    def test_credential_path_and_foreign_refuser_refused_before_byte_reads(self):
        for role, value in (
            ("capabilities", pin("D:/Synthetic/.android/capabilities.json")),
            ("refuser", pin("D:/Synthetic/other.exe", size=95_744, sha=inputs.REFUSER_SHA256)),
            ("refuser", pin("D:/Synthetic/deny-adb-client.exe", size=95_744, sha="a" * 64)),
        ):
            with self.subTest(role=role), patch.dict(self.installed, {role: value}):
                with self.assertRaisesRegex(ValueError, "^" + ("auth" if role == "capabilities" else "installed") + "$"):
                    self.prospective()
        self.source_read.assert_not_called()
        self.check.assert_not_called()

    def test_refuser_source_drift_refuses_before_server_or_guest_pins(self):
        self.source["sha256"] = "d" * 64
        with self.assertRaisesRegex(gate.AdmissionRefused, "^installed$"):
            self.prospective()
        self.server.assert_not_called()
        self.check.assert_not_called()

    def test_wrong_adb_binary_refused_by_existing_contract(self):
        self.files["adb.exe"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.prospective()
        self.server.assert_not_called()
        self.check.assert_not_called()


class PreparationJoinTests(RunInputFixture):
    def setUp(self):
        super().setUp()
        self.prepare_authority = pin(str(inputs.preparation.AUTHORITY))
        self.record = dict(authority=self.prepare_authority, prepared=self.prepare_pins["prepared"],
                           prepare_result=self.prepare_pins["prepare_result"])
        self.enterContext(patch.object(inputs, "_at", return_value=self.record))
        self.enterContext(patch.object(inputs, "_verify_json"))
        self.enterContext(patch.object(inputs.preparation, "_authority", return_value=dict(
            prepare=self.prepare_pins["prepare_proposal"], artifacts=self.artifacts)))
        self.verify = self.enterContext(patch.object(inputs.preparation, "verify_receipt"))
        self.fresh = self.enterContext(patch.object(gate, "_prepared_entry"))

    def test_exact_receipt_is_replayed_against_fresh_ledger(self):
        self.assertEqual(inputs._prepared(self.receipt, self.ledger), (self.prepare_pins, self.artifacts))
        self.verify.assert_called_once_with(self.receipt, self.prepare_pins, self.artifacts)
        self.fresh.assert_called_once_with(self.ledger, {"guest": {"root": str(inputs.preparation.GUEST)}},
                                           self.prepare_pins)

    def test_receipt_cannot_redirect_prepared_file(self):
        self.record["prepared"] = pin("D:/Synthetic/elsewhere.json")
        with self.assertRaisesRegex(gate.AdmissionRefused, "^prepared$"):
            inputs._prepared(self.receipt, self.ledger)
        self.verify.assert_not_called()
        self.fresh.assert_not_called()


class PublicationTests(RunInputFixture):
    def setUp(self):
        super().setUp()
        self.calls = Mock()
        self.calls.at.return_value = self.plan
        self.calls.authority.return_value = self.approval
        self.calls.prepared.return_value = self.prepare_pins, self.artifacts
        self.calls.proposal.return_value = self.proposal
        self.calls.prospective.return_value = self.authorization, self.value
        self.calls.read.side_effect = lambda path, *args: (
            (self.ledger, {}) if path == inputs.preparation.LEDGER else (self.run, self.proposal))
        self.calls.plan_run.return_value = self.proposal
        self.calls.save.side_effect = lambda expected, value: expected
        for module, name, value in (
            (inputs.os, "name", "nt"),
            (inputs.output_control, "_prepare_environment", Mock()),
            (inputs.output_control, "validate_output", Mock(return_value=gate.RUN_PROPOSAL)),
            (inputs.os.path, "lexists", Mock(return_value=False)),
            (inputs, "_unspent", Mock()),
            (inputs, "_installed", Mock()),
            (inputs, "_at", self.calls.at),
            (inputs, "_read", self.calls.read),
            (gate, "_authority", self.calls.authority),
            (gate, "_check_ledger_unlocked", Mock()),
            (inputs, "_prepared", self.calls.prepared),
            (inputs, "_proposal", self.calls.proposal),
            (inputs, "_prospective", self.calls.prospective),
            (inputs, "_save_exact", self.calls.save),
            (inputs, "_verify_json", Mock()),
            (inputs, "_recheck", self.calls.recheck),
            (env, "plan_run", self.calls.plan_run),
            (env, "verify_prepared", self.calls.verify_prepared),
        ):
            self.enterContext(patch.object(module, name, value))

    def test_stage_writes_proposal_and_review_but_never_materializes_inputs(self):
        self.assertEqual(inputs.stage(self.receipt, self.installation), self.plan_pin)
        self.calls.plan_run.assert_called_once_with(
            self.prepare_pins["prepare_proposal"]["path"], self.prepare_pins["prepared"]["path"], gate.RUN_PROPOSAL,
            max_seconds=gate.GUEST_SECONDS,
        )
        self.calls.save.assert_called_once_with(self.plan_pin, self.plan)
        self.calls.authority.assert_not_called()
        self.assertFalse(self.calls.save.call_args.args[1]["execution_authorized"])

    def test_stage_replays_existing_proposal_create_only(self):
        inputs.os.path.lexists.side_effect = lambda path: path == gate.RUN_PROPOSAL
        self.assertEqual(inputs.stage(self.receipt, self.installation), self.plan_pin)
        self.calls.plan_run.assert_not_called()
        self.calls.verify_prepared.assert_called_once_with(self.proposal, initial=True)

    def test_materialize_requires_exact_external_authority_then_replays_full_plan(self):
        self.assertEqual(inputs.materialize(self.plan_pin, self.authority), self.plan["admission"])
        self.calls.authority.assert_called_once_with(self.authority)
        self.calls.prepared.assert_called_once_with(self.receipt, self.ledger)
        self.calls.verify_prepared.assert_called_once_with(self.proposal, initial=True)
        self.assertEqual(self.calls.save.call_args_list[0].args, (self.plan["authorization"], self.authorization))
        self.assertEqual(self.calls.save.call_args_list[1].args, (self.plan["admission"], self.value))
        self.assertEqual(self.calls.recheck.call_count, 3)

    def test_foreign_authority_cannot_start_materialization(self):
        self.approval["ledger"] = dict(self.ledger, sha256="f" * 64)
        with self.assertRaisesRegex(gate.AdmissionRefused, "^authority$"):
            inputs.materialize(self.plan_pin, self.authority)
        self.calls.prepared.assert_not_called()
        self.calls.save.assert_not_called()

    def test_fresh_binding_drift_refuses_before_any_output(self):
        self.calls.prospective.return_value = self.authorization, dict(self.value, seconds=1600)
        with self.assertRaisesRegex(gate.AdmissionRefused, "^plan$"):
            inputs.materialize(self.plan_pin, self.authority)
        self.calls.save.assert_not_called()

    def test_drift_after_first_file_keeps_partial_without_publishing_admission(self):
        self.calls.recheck.side_effect = [None, gate.AdmissionRefused("ledger")]
        with self.assertRaisesRegex(gate.AdmissionRefused, "^ledger$"):
            inputs.materialize(self.plan_pin, self.authority)
        self.calls.save.assert_called_once_with(self.plan["authorization"], self.authorization)


@unittest.skipUnless(os.name == "nt" and Path(tempfile.gettempdir()).drive.upper() == "D:", "physical D: fixture")
class ExactFileTests(unittest.TestCase):
    def test_new_record_is_published_with_exact_bytes(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        path = root / "materialization.json"
        value = dict(version=1, synthetic=True)
        expected = inputs._pin(path, value)
        self.assertEqual(inputs._save_exact(expected, value), expected)
        self.assertEqual(path.read_bytes(), env.encoded(value))
        self.assertFalse(path.with_name(path.name + ".pending").exists())

    def test_incomplete_pending_file_remains_unpublished(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        path = root / "materialization.json"
        value = dict(version=1, synthetic=True)
        pending = path.with_name(path.name + ".pending")
        pending.write_bytes(b"truncated")
        with self.assertRaises(ValueError):
            inputs._save_exact(inputs._pin(path, value), value)
        self.assertFalse(path.exists())
        self.assertEqual(pending.read_bytes(), b"truncated")

    def test_create_only_continuation_verifies_exact_existing_bytes(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        path = root / "materialization.json"
        record = dict(version=1, synthetic=True)
        expected = inputs._pin(path, record)
        pending = path.with_name(path.name + ".pending")
        env.create_json(pending, record)
        self.assertEqual(inputs._save_exact(expected, record), expected)
        self.assertFalse(pending.exists())
        self.assertEqual(inputs._save_exact(expected, record), expected)
        with self.assertRaises(ValueError):
            inputs._save_exact(inputs._pin(path, {"changed": True}), {"changed": True})
        self.assertEqual(path.read_bytes(), env.encoded(record))


class CliTests(unittest.TestCase):
    def test_wrong_digest_never_reaches_materialize(self):
        with (patch.object(inputs.os, "name", "nt"),
              patch.object(inputs, "_by_digest") as read,
              patch.object(inputs, "materialize") as publish,
              patch("sys.stderr", new_callable=io.StringIO) as error):
            self.assertEqual(inputs.main(["materialize", "--plan-sha256", "bad",
                                          "--authority-sha256", "f" * 64]), 1)
            read.assert_not_called()
            publish.assert_not_called()
            self.assertEqual(error.getvalue(), "SDK25 run inputs refused\n")


if __name__ == "__main__":
    unittest.main()
