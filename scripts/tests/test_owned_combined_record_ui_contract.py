"""Host-only authority and adapter checks for the fixed SDK21 Record profile."""
import copy
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import combined_record_ui_binding as policy
from benchmarks import owned_combined_record_ui_client as client
from benchmarks import owned_combined_record_ui_contract as contract
from benchmarks import owned_combined_record_ui_owner as owner
from benchmarks import owned_record_ui_contract as sdk7
from scripts.tests import test_owned_target_contract as fixture


def admission():
    value = fixture.admission()
    value.update(protocol=contract.PROTOCOL, artifacts=policy.artifact_bindings())
    value["guest"]["root"] = str(contract.GUEST_ROOT)
    root = PureWindowsPath("D:/Synthetic/LocalLore/benchmarks")
    value["sources"] = [fixture.pin(root / name) for name in sorted(contract.SOURCE_NAMES)]
    return value


class CombinedRecordUiContractTests(unittest.TestCase):
    def test_twelve_fixed_selectors_bind_unique_claims(self):
        value = admission()
        caller = fixture.running(value)["worker"]
        admission_pin = fixture.pin("D:/Synthetic/combined-admission-v1.json")
        self.assertEqual(contract.CLIENT_VERSION, 21)
        self.assertEqual(contract.SESSION_FILE, "sdk-session-v21.json")
        self.assertIs(contract.MODEL_MATERIAL, False)
        self.assertIs(client.REPLAY, owner.REPLAY)
        self.assertIs(client.REPLAY.c, contract)
        self.assertEqual(contract.INSTRUMENTATIONS, policy.INSTRUMENTATIONS)
        self.assertEqual(contract.CLAIM_KINDS, tuple(kind for kind, _, _ in policy.INSTRUMENTATIONS))
        self.assertEqual(len(set(contract.CLAIM_KINDS)), 12)
        digests = set()
        for kind, klass, method in policy.INSTRUMENTATIONS:
            with self.subTest(kind=kind):
                argv = ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
                        "org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner"]
                operation = {"argv": argv, "stdin": None}
                self.assertEqual(contract.validate_operation(operation, value), operation)
                self.assertEqual(contract.instrumentation_kind(argv), kind)
                digest = contract.operation_digest(operation)
                claim = contract.claim_record(admission_pin, caller, kind, digest)
                self.assertEqual(contract.validate_claim(claim, admission_pin, caller, kind, digest), claim)
                self.assertNotIn(digest, digests)
                digests.add(digest)

    def test_wrong_artifact_pins_and_legacy_admissions_refuse(self):
        value = admission()
        decoded = contract.validate_admission(value)
        self.assertEqual(decoded, value)
        decoded["artifacts"]["build"].clear()
        self.assertEqual(value["artifacts"], policy.artifact_bindings())
        for role in value["artifacts"]:
            bad = copy.deepcopy(value)
            bad["artifacts"][role]["sha256"] = "0" * 64
            with self.subTest(role=role), self.assertRaises(contract.TargetRefused):
                contract.validate_admission(bad)
        for foreign in (
            fixture.admission(),
            dict(value, protocol=sdk7.PROTOCOL),
            dict(value, artifacts=dict(value["artifacts"], model=fixture.pin("D:/Synthetic/model.task"))),
        ):
            with self.assertRaises(contract.TargetRefused):
                contract.validate_admission(foreign)
        with self.assertRaises(sdk7.TargetRefused):
            sdk7.validate_admission(value)

    def test_legacy_selectors_model_and_process_commands_refuse(self):
        value = admission()
        _, klass, method = sdk7.INSTRUMENTATIONS[0]
        for argv in (
            ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
             sdk7.TEST + "/androidx.test.runner.AndroidJUnitRunner"],
            ["pidof", contract.APP],
            ["am", "force-stop", "--user", "0", contract.TEST],
            ["run-as", contract.APP, "--user", "0", "ls", "files"],
            ["df", "-k", "/data"],
            ["sha256sum", "/data/app/foreign.app-x/base.apk"],
        ):
            with self.subTest(argv=argv), self.assertRaises(contract.TargetRefused):
                contract.validate_operation({"argv": argv, "stdin": None}, value)

    def test_staging_accepts_only_exact_apk_role(self):
        value = admission()
        for role, name in (("product_apk", "locallore-product-v1.apk"),
                           ("test_apk", "locallore-test-v1.apk")):
            with self.subTest(role=role):
                argv = ["dd", "of=/data/local/tmp/" + name, "bs=65536"]
                source = value["artifacts"][role]
                operation = {"argv": argv, "stdin": source}
                self.assertEqual(contract.validate_operation(operation, value), operation)
                for wrong in (None, value["artifacts"]["build"], dict(source, bytes=source["bytes"] - 1)):
                    with self.assertRaises(contract.TargetRefused):
                        contract.validate_operation(dict(operation, stdin=wrong), value)

    def test_observer_verifies_artifact_bytes_before_delegating_to_handle_owner(self):
        value = admission()
        events = []

        def verify(pins):
            self.assertEqual(pins, policy.artifact_bindings())
            events.append("verify")

        admission_pin = fixture.pin("D:/Synthetic/combined-admission-v1.json")
        running_pin = fixture.pin("D:/Synthetic/running-v1.json")
        with (patch.object(owner.mechanisms, "_read_json", return_value=value),
              patch.object(policy, "verify_artifacts", side_effect=verify),
              patch.object(owner.mechanisms._LiveOwnedTarget, "__init__",
                           side_effect=lambda *_: events.append("open"))):
            owner.LiveOwnedCombinedRecordUiTarget(admission_pin, running_pin)
        self.assertEqual(events, ["verify", "open"])

        with (patch.object(owner.mechanisms, "_read_json", return_value=value),
              patch.object(policy, "verify_artifacts", side_effect=contract.TargetRefused("binding")),
              patch.object(owner.mechanisms._LiveOwnedTarget, "__init__") as open_handles):
            with self.assertRaises(contract.TargetRefused):
                owner.LiveOwnedCombinedRecordUiTarget(admission_pin, running_pin)
            open_handles.assert_not_called()
