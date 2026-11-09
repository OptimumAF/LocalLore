"""Synthetic-only checks for SDK25's scoped preparation handoff."""
import copy
import hashlib
import io
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_prepare as prepare
from scripts.tests.test_owned_target_contract import pin

admission = prepare.admission
env = prepare.env


class PrepareFixture(unittest.TestCase):
    def setUp(self):
        self.authority_pin = pin(str(prepare.AUTHORITY))
        self.auth_pin = pin(str(prepare.AUTHORIZATION))
        self.prepare_pin = pin(str(admission.PREPARE_PROPOSAL))
        self.ledger = pin(str(prepare.LEDGER))
        self.attempt = pin(str(prepare.ATTEMPT))
        self.result = pin(str(prepare.RESULT))
        self.sources = [pin("D:/Synthetic/benchmarks/archive_roundtrip_prepare.py")]
        self.artifacts = {"fixed": pin("D:/Synthetic/fixture.json")}
        self.authority = dict(
            version=1, scope=prepare.SCOPE, prepare=self.prepare_pin, authorization=self.auth_pin,
            ledger=self.ledger, artifacts=self.artifacts,
            source_sha256=hashlib.sha256(env.encoded(self.sources)).hexdigest(),
            approval_reference="synthetic scope only", allow_prepare=True, allow_boot=False,
        )
        self.proposal = dict(paths={"root": str(prepare.GUEST)}, memory_mib=8192, cores=4)
        self.authorization = dict(version=1, phase="prepare", proposal_sha256=self.prepare_pin["sha256"],
                                  prepare_scope=prepare.SCOPE, allow_environment_calls=True, root_go_pending=False)
        self.preview = dict(ledger=self.ledger, would_fit=True, admission_granted=False)
        self.prepared_pin = pin(str(prepare.GUEST / "prepared-v1.json"))
        self.child_pin = pin(str(prepare.GUEST / "prepare-result-v1.json"))
        self.prepared = dict(proposal_sha256=self.prepare_pin["sha256"], userdata_absent=True, guest_boot_verified=False)
        self.child_result = dict(version=1, proposal_sha256=self.prepare_pin["sha256"], status="completed",
                                 closure_verified=True, child_cleanup_complete=True, prepared_created=True)
        self.owner = dict(pid=751, creation_filetime=100, executable=r"C:\Synthetic\python.exe")
        self.worker = dict(self.owner, pid=752, creation_filetime=200)
        self.binding = self.enterContext(patch.object(env, "check_binding"))


class PreflightTests(PrepareFixture):
    def setUp(self):
        super().setUp()
        self.ledger_record = dict(version=2)
        self.files = {
            prepare.AUTHORITY: (self.authority_pin, self.authority),
            admission.PREPARE_PROPOSAL: (self.prepare_pin, self.proposal),
            prepare.AUTHORIZATION: (self.auth_pin, self.authorization),
            prepare.LEDGER: (self.ledger, self.ledger_record),
        }

        def at(expected, path, cap=prepare.lifecycle.RECORD_CAP):
            pinned, value = self.files[path]
            self.assertEqual(expected, pinned)
            self.assertLess(len(env.encoded(value)), cap)
            return copy.deepcopy(value)

        self.read = self.enterContext(patch.object(prepare, "_at", side_effect=at))
        self.enterContext(patch.object(prepare.contract, "source_bindings", return_value=self.sources))
        self.validate = self.enterContext(patch.object(env, "validate_proposal"))
        self.capacity = self.enterContext(patch.object(prepare.storage, "preview_prepare", return_value=self.preview))
        self.build = self.enterContext(patch.object(prepare.build, "verify_current"))
        self.authorize = self.enterContext(patch.object(env, "authorize", return_value=self.proposal))
        self.facts = self.enterContext(patch.object(env, "resource_facts"))

    def test_exact_prepare_scope_artifacts_and_current_ledger(self):
        self.assertEqual(prepare._preflight(self.authority_pin), self.authority)
        self.validate.assert_called_once_with(self.proposal, "prepare")
        self.capacity.assert_called_once_with(prepare.GUEST)
        self.build.assert_called_once_with(dict(artifacts=self.artifacts))
        self.authorize.assert_called_once_with(str(admission.PREPARE_PROPOSAL), str(prepare.AUTHORIZATION), "prepare",
                                               prepare_scope=prepare.SCOPE,
                                               expected_proposal_sha256=self.prepare_pin["sha256"])
        self.facts.assert_called_once_with(self.proposal)
        self.assertEqual([entry.args[0] for entry in self.binding.call_args_list],
                         [self.authority_pin, self.prepare_pin, self.auth_pin, self.ledger])

    def test_authority_cannot_grant_boot_or_change_sources(self):
        for field, value, reason in (("allow_boot", True, "authority"),
                                     ("source_sha256", "a" * 64, "source")):
            with self.subTest(field=field), patch.dict(self.authority, {field: value}):
                with self.assertRaisesRegex(admission.AdmissionRefused, "^" + reason + "$"):
                    prepare._preflight(self.authority_pin)
        self.validate.assert_not_called()
        self.capacity.assert_not_called()

    def test_wrong_guest_or_small_profile_refuses_before_storage_preview(self):
        for changes in (dict(paths={"root": "D:/Synthetic/OtherGuest"}), dict(cores=2)):
            with self.subTest(changes=changes), patch.dict(self.proposal, changes):
                with self.assertRaisesRegex(admission.AdmissionRefused, "^profile$"):
                    prepare._preflight(self.authority_pin)
        self.capacity.assert_not_called()
        self.build.assert_not_called()

    def test_unscoped_authorization_refuses_before_storage_preview(self):
        del self.authorization["prepare_scope"]
        with self.assertRaisesRegex(env.EnvironmentRefused, "^not_authorized$"):
            prepare._preflight(self.authority_pin)
        self.capacity.assert_not_called()

    def test_installed_environment_and_resources_checked_before_spend(self):
        self.authorize.side_effect = env.EnvironmentRefused("binding_changed")
        with self.assertRaisesRegex(env.EnvironmentRefused, "^binding_changed$"):
            prepare._preflight(self.authority_pin)
        self.facts.assert_not_called()
        self.authorize.side_effect = None
        self.facts.side_effect = env.EnvironmentRefused("host_capacity")
        with self.assertRaisesRegex(env.EnvironmentRefused, "^host_capacity$"):
            prepare._preflight(self.authority_pin)

    def test_unsupported_ledger_refuses_before_capacity(self):
        self.ledger_record["version"] = 1
        with self.assertRaisesRegex(admission.AdmissionRefused, "^ledger_version$"):
            prepare._preflight(self.authority_pin)
        self.capacity.assert_not_called()

    def test_closed_capacity_or_changed_ledger_refuses_before_artifacts(self):
        for changes in (dict(would_fit=False), dict(admission_granted=True),
                        dict(ledger=pin("D:/Synthetic/other-ledger.json"))):
            with self.subTest(changes=changes), patch.dict(self.preview, changes):
                with self.assertRaisesRegex(admission.AdmissionRefused, "^capacity$"):
                    prepare._preflight(self.authority_pin)
        self.build.assert_not_called()


class DispatchTests(PrepareFixture):
    def setUp(self):
        super().setUp()
        self.calls = Mock()
        self.proof = dict(prepared=self.prepared_pin, prepare_result=self.child_pin,
                          prepared_ledger=self.ledger, child={})
        self.calls.output.side_effect = (prepare.ATTEMPT, prepare.RESULT)
        self.calls.preflight.return_value = self.authority
        self.calls.authority.return_value = self.authority
        self.calls.save.side_effect = (self.attempt, self.result)
        self.calls.dispatch.return_value = self.prepared
        self.calls.verify.return_value = self.proof
        for module, name, replacement in (
            (prepare.os, "name", "nt"),
            (prepare.output_control, "_prepare_environment", Mock()),
            (prepare.supervisor, "_identity", Mock(return_value=self.owner)),
            (prepare.output_control, "validate_output", self.calls.output),
            (prepare, "_preflight", self.calls.preflight),
            (prepare, "_authority", self.calls.authority),
            (prepare, "_save", self.calls.save),
            (env, "prepare", self.calls.dispatch),
            (prepare, "_verify_result", self.calls.verify),
        ):
            self.enterContext(patch.object(module, name, replacement))

    def test_create_only_attempt_precedes_one_shared_dispatch_and_receipt(self):
        self.assertEqual(prepare.execute(self.authority_pin), self.result)
        self.assertEqual([call[0] for call in self.calls.mock_calls],
                         ["output", "output", "preflight", "save", "authority", "dispatch", "verify", "authority", "save"])
        self.calls.verify.assert_called_once_with(self.authority, self.prepared, self.owner)
        self.calls.dispatch.assert_called_once_with(
            str(admission.PREPARE_PROPOSAL), str(prepare.AUTHORIZATION),
            expected_ledger=self.ledger, expected_proposal_sha256=self.prepare_pin["sha256"],
            prepare_scope=prepare.SCOPE,
        )
        self.assertEqual(self.calls.save.call_args_list[0].args, (prepare.ATTEMPT, dict(
            version=1, scope=prepare.SCOPE, authority=self.authority_pin,
            prepare=self.prepare_pin, ledger=self.ledger, no_retry=True)))
        self.assertEqual(self.calls.save.call_args.args, (prepare.RESULT, dict(
            version=1, scope=prepare.SCOPE, authority=self.authority_pin, attempt=self.attempt, **self.proof)))

    def test_preflight_or_claim_refusal_does_not_dispatch(self):
        self.calls.preflight.side_effect = admission.AdmissionRefused("capacity")
        with self.assertRaisesRegex(admission.AdmissionRefused, "^capacity$"):
            prepare.execute(self.authority_pin)
        self.calls.save.assert_not_called()
        self.calls.output.side_effect = (prepare.ATTEMPT, prepare.RESULT)
        self.calls.preflight.side_effect = None
        self.calls.save.side_effect = FileExistsError("prior attempt")
        with self.assertRaises(FileExistsError):
            prepare.execute(self.authority_pin)
        self.calls.dispatch.assert_not_called()

    def test_authority_replacement_after_spend_cannot_dispatch(self):
        self.calls.authority.return_value = dict(self.authority, approval_reference="another scope")
        with self.assertRaisesRegex(admission.AdmissionRefused, "^authority$"):
            prepare.execute(self.authority_pin)
        self.assertEqual(self.calls.save.call_count, 1)
        self.calls.dispatch.assert_not_called()

    def test_shared_prepare_failure_keeps_spent_record_without_receipt(self):
        self.calls.dispatch.side_effect = env.EnvironmentRefused("prepare_failed")
        with self.assertRaisesRegex(env.EnvironmentRefused, "^prepare_failed$"):
            prepare.execute(self.authority_pin)
        self.calls.verify.assert_not_called()
        self.assertEqual(self.calls.save.call_count, 1)


class ReceiptTests(PrepareFixture):
    def setUp(self):
        super().setUp()
        self.read = self.enterContext(patch.object(prepare, "_read", side_effect=[
            (self.prepared_pin, self.prepared), (self.child_pin, self.child_result), (self.ledger, {})]))
        self.ledger_check = self.enterContext(patch.object(admission, "_prepared_entry"))
        self.evidence = self.enterContext(patch.object(prepare, "_child_evidence", return_value={}))

    def test_only_matching_prepared_result_and_ledger_qualify(self):
        self.assertEqual(prepare._verify_result(self.authority, self.prepared, self.owner),
                         dict(prepared=self.prepared_pin, prepare_result=self.child_pin, prepared_ledger=self.ledger, child={}))
        self.evidence.assert_called_once_with(self.prepare_pin, self.owner)
        self.ledger_check.assert_called_once_with(self.ledger, {"guest": {"root": str(prepare.GUEST)}},
                                                  {"prepare_proposal": self.prepare_pin})

    def test_unknown_child_cleanup_refuses_before_ledger_claim(self):
        self.child_result["child_cleanup_complete"] = False
        with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
            prepare._verify_result(self.authority, self.prepared, self.owner)
        self.ledger_check.assert_not_called()

    def test_changed_prepared_bytes_refuse(self):
        with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
            prepare._verify_result(self.authority, dict(self.prepared, userdata_absent=False), self.owner)
        self.ledger_check.assert_not_called()


class ChildEvidenceTests(PrepareFixture):
    def setUp(self):
        super().setUp()
        self.raw = b"synthetic SDK output"
        self.start = dict(proposal_sha256=self.prepare_pin["sha256"], facts={}, owner=self.owner,
                          prepare_scope=prepare.SCOPE)
        self.claim = dict(proposal_sha256=self.prepare_pin["sha256"], worker=self.worker,
                          prepare_scope=prepare.SCOPE)
        self.client = dict(status="completed", returncode=0, cleanup_complete=True, elapsed_ms=20,
                           stdout_sha256=hashlib.sha256(self.raw).hexdigest(), stderr_bytes=0)
        self.paths = dict(zip(("start", "worker", "client"),
                              ("prepare-start-v1.json", "prepare-worker-claimed-v1.json", "prepare-client-v1.json")))
        self.records = dict(zip(self.paths.values(), (self.start, self.claim, self.client)))
        self.enterContext(patch.object(prepare, "_read",
                                       side_effect=lambda path, cap: (pin(str(path)), self.records[path.name])))
        self.output = self.enterContext(patch.object(prepare.lifecycle.bridge.files, "_read", return_value=self.raw))

    def test_scoped_claim_parent_identity_and_exact_output(self):
        output_path = prepare.GUEST / "prepare-stdout-v1.bin"
        expected = {key: pin(str(prepare.GUEST / name)) for key, name in self.paths.items()}
        expected["stdout"] = prepare.lifecycle.bridge._pin_bytes(output_path, self.raw)
        self.assertEqual(prepare._child_evidence(self.prepare_pin, self.owner), expected)
        self.output.assert_called_once_with(output_path, env.MAX_OUTPUT)

    def test_wrong_child_scope_or_owner_refuses_before_raw_read(self):
        with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
            prepare._child_evidence(self.prepare_pin, dict(self.owner, pid=753))
        self.claim["prepare_scope"] = admission.SCOPE
        with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
            prepare._child_evidence(self.prepare_pin, self.owner)
        self.output.assert_not_called()

    def test_missing_cleanup_or_different_capture_refuses(self):
        for values in (dict(cleanup_complete=False), dict(stdout_sha256="a" * 64),
                       dict(stderr_bytes=env.MAX_OUTPUT), dict(returncode=1)):
            with self.subTest(values=values), patch.dict(self.client, values):
                with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
                    prepare._child_evidence(self.prepare_pin, self.owner)


class ReceiptReplayTests(PrepareFixture):
    def setUp(self):
        super().setUp()
        self.child = {"client": pin(str(prepare.GUEST / "prepare-client-v1.json"))}
        self.proposal = dict(prepare_proposal=self.prepare_pin, prepared=self.prepared_pin, prepare_result=self.child_pin)
        self.receipt = dict(version=1, scope=prepare.SCOPE, authority=self.authority_pin, attempt=self.attempt,
                            prepared=self.prepared_pin, prepare_result=self.child_pin,
                            prepared_ledger=dict(self.ledger, sha256="b" * 64), child=self.child)
        self.attempt_record = prepare._attempt(self.authority_pin, self.authority)
        records = {prepare.RESULT: self.receipt, prepare.ATTEMPT: self.attempt_record,
                   prepare.AUTHORIZATION: self.authorization}

        def at(bound, path, cap=prepare.lifecycle.RECORD_CAP):
            self.assertEqual(bound["path"], str(path))
            return records[path]

        self.enterContext(patch.object(prepare, "_at", side_effect=at))
        self.enterContext(patch.object(prepare, "_authority", return_value=self.authority))
        self.evidence = self.enterContext(patch.object(prepare, "_child_evidence", return_value=self.child))

    def test_receipt_binds_prepared_inputs_without_requiring_historical_ledger_to_still_be_live(self):
        prepare.verify_receipt(self.result, self.proposal, self.artifacts)
        self.evidence.assert_called_once_with(self.prepare_pin)
        self.binding.assert_any_call(self.result)
        self.assertNotIn(self.receipt["prepared_ledger"], [call.args[0] for call in self.binding.call_args_list])

    def test_receipt_refuses_changed_prepared_bytes_artifacts_or_attempt(self):
        with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
            prepare.verify_receipt(self.result, dict(self.proposal, prepared=self.child_pin), self.artifacts)
        with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
            prepare.verify_receipt(self.result, self.proposal, {})
        self.attempt_record["no_retry"] = False
        with self.assertRaisesRegex(admission.AdmissionRefused, "^prepared$"):
            prepare.verify_receipt(self.result, self.proposal, self.artifacts)
        self.evidence.assert_not_called()


class CliTests(PrepareFixture):
    def test_cli_refuses_wrong_digest_before_execute(self):
        with (patch.object(prepare.os, "name", "nt"),
              patch.object(prepare, "_read", return_value=(self.authority_pin, self.authority)) as read,
              patch.object(prepare, "execute") as dispatch,
              patch("sys.stderr", new_callable=io.StringIO) as error):
            self.assertEqual(prepare.main(["--authority-sha256", "a" * 64]), 1)
            read.assert_called_once_with(prepare.AUTHORITY, admission.AUTHORITY_CAP)
            dispatch.assert_not_called()
            self.assertEqual(error.getvalue(), "SDK25 preparation refused\n")


if __name__ == "__main__":
    unittest.main()
