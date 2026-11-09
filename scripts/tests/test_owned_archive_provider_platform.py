"""Host-only checks for the fixed SDK26 archive-provider owner and capture."""
import copy
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import archive_provider_platform_binding as binding
from benchmarks import owned_archive_provider_platform as owner
from scripts.tests import test_owned_target_contract as fixture


SYNTHETIC_SOURCE_ROOT = PureWindowsPath("D:/Synthetic/LocalLore")
AUDIT_SOURCES = ("audit_apk.py", "audit_physical_model_apk.py")
ADMISSION_PIN = fixture.pin("D:/Synthetic/archive-provider-admission-v1.json")
RUNNING_PIN = fixture.pin("D:/Synthetic/owned-target-v1/running-v1.json")


def admission():
    value = fixture.admission()
    value.update(protocol=owner.PROTOCOL, artifacts=binding.artifact_bindings())
    value["guest"]["root"] = str(owner.GUEST_ROOT)
    paths = [SYNTHETIC_SOURCE_ROOT / "benchmarks" / name for name in owner.SOURCE_NAMES]
    paths.extend(SYNTHETIC_SOURCE_ROOT / "scripts" / name for name in AUDIT_SOURCES)
    value["sources"] = [fixture.pin(path) for path in sorted(paths, key=str)]
    return value


class OwnedArchiveProviderPlatformTests(unittest.TestCase):
    def test_profile_binds_only_two_operations_and_distinct_claims(self):
        value = admission()
        caller = fixture.running(value)["worker"]
        self.assertEqual(owner.PROTOCOL, "owned-emulator-archive-provider-platform-v1")
        self.assertEqual(owner.SDK_PROTOCOL, "sdk-archive-provider-platform-v1")
        self.assertEqual(owner.CLIENT_VERSION, 26)
        self.assertEqual(owner.SESSION_FILE, "sdk-session-v26.json")
        self.assertEqual(owner.GUEST_ROOT, PureWindowsPath(
            "D:/Dev/Experiments/LocalLore/2026-11-09-archive-provider-platform-guest-v1/avd-v1"))
        self.assertEqual((owner.APP, owner.TEST), (binding.APP, binding.TEST))
        self.assertIs(owner.MODEL_MATERIAL, False)
        self.assertEqual(owner.INSTRUMENTATIONS, binding.INSTRUMENTATIONS)
        self.assertEqual(owner.CLAIM_KINDS, ("archive_import_open", "archive_export_open"))
        self.assertEqual(owner.ARTIFACT_KEYS, frozenset(binding.artifact_bindings()))
        claims = []
        for kind in owner.CLAIM_KINDS:
            with self.subTest(kind=kind):
                argv = binding.instrumentation_argv(kind)
                operation = {"argv": argv, "stdin": None}
                self.assertEqual(owner.validate_operation(operation, value), operation)
                self.assertEqual(owner.instrumentation_kind(argv), kind)
                digest = owner.operation_digest(operation)
                claim = owner.claim_record(ADMISSION_PIN, caller, kind, digest)
                self.assertEqual(owner.validate_claim(claim, ADMISSION_PIN, caller, kind, digest), claim)
                claims.append((kind, digest, claim))
        self.assertNotEqual(claims[0][1], claims[1][1])
        with self.assertRaises(owner.TargetRefused):
            owner.validate_claim(claims[0][2], ADMISSION_PIN, caller, claims[1][0], claims[1][1])

    def test_admission_refuses_foreign_guest_protocol_or_artifact_pin(self):
        value = admission()
        accepted = owner.validate_admission(value)
        self.assertEqual(accepted, value)
        accepted["artifacts"]["build"].clear()
        self.assertEqual(value["artifacts"], binding.artifact_bindings())
        foreign_guest = copy.deepcopy(value)
        foreign_guest["guest"]["root"] = "D:/Synthetic/other-avd"
        with_model = copy.deepcopy(value)
        with_model["artifacts"]["model"] = fixture.pin("D:/Synthetic/foreign.task")
        swapped = copy.deepcopy(value)
        swapped["artifacts"]["product_apk"] = swapped["artifacts"]["test_apk"]
        different_bytes = copy.deepcopy(value)
        different_bytes["artifacts"]["test_apk"]["sha256"] = "0" * 64
        for foreign in (fixture.admission(), foreign_guest, with_model, swapped, different_bytes):
            with self.subTest(foreign=foreign), self.assertRaises(owner.TargetRefused):
                owner.validate_admission(foreign)

    def test_source_roster_refuses_missing_audits_storage_and_foreign_paths(self):
        self.assertIn("prepare_recovery_contract.py", owner.SOURCE_NAMES)
        for name in (*AUDIT_SOURCES, "prepare_recovery_contract.py"):
            with self.subTest(name=name):
                value = admission()
                value["sources"] = [pin for pin in value["sources"]
                                    if PureWindowsPath(pin["path"]).name != name]
                with self.assertRaises(owner.TargetRefused):
                    owner.validate_admission(value)
        value = admission()
        value["sources"] = [fixture.pin(PureWindowsPath("D:/Foreign/scripts") / "audit_apk.py")
                            if PureWindowsPath(pin["path"]).name == "audit_apk.py" else pin
                            for pin in value["sources"]]
        value["sources"].sort(key=lambda pin: pin["path"])
        with self.assertRaises(owner.TargetRefused):
            owner.validate_admission(value)
        value = admission()
        value["server"]["sources"][0]["sha256"] = "0" * 64
        with self.assertRaises(owner.TargetRefused):
            owner.validate_admission(value)

    def test_stage_only_matching_apk_and_install_without_replacement(self):
        value = admission()
        for role, other, leaf in (
            ("product_apk", "test_apk", "locallore-product-v1.apk"),
            ("test_apk", "product_apk", "locallore-test-v1.apk"),
        ):
            with self.subTest(role=role):
                path = "/data/local/tmp/" + leaf
                stage = {"argv": ["dd", "of=" + path, "bs=65536"], "stdin": value["artifacts"][role]}
                self.assertEqual(owner.validate_operation(stage, value), stage)
                for bad_source in (None, value["artifacts"][other], value["artifacts"]["build"]):
                    with self.assertRaises(owner.TargetRefused):
                        owner.validate_operation(dict(stage, stdin=bad_source), value)
                install = {"argv": ["pm", "install", "-R", "-t", "--user", "0", path], "stdin": None}
                self.assertEqual(owner.validate_operation(install, value), install)
                for flags in ([], ["-r"], ["-R", "-r"]):
                    argv = ["pm", "install", *flags, "-t", "--user", "0", path]
                    with self.assertRaises(owner.TargetRefused):
                        owner.validate_operation(dict(install, argv=argv), value)

    def test_foreign_selectors_and_process_or_model_commands_refuse(self):
        value = admission()
        first = binding.instrumentation_argv("archive_import_open")
        second = binding.instrumentation_argv("archive_export_open")
        for argv in (
            [*first[:6], first[6].split("#")[0], first[7]],
            [*first[:6], first[6] + "," + second[6], first[7]],
            [*first[:7], "org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner"],
            ["pidof", owner.APP],
            ["am", "force-stop", "--user", "0", owner.TEST],
            ["run-as", owner.APP, "--user", "0", "ls", "files"],
            ["dd", "of=/data/local/tmp/model.task", "bs=65536"],
            ["sha256sum", "/data/app/foreign.app-x/base.apk"],
        ):
            with self.subTest(argv=argv), self.assertRaises(owner.TargetRefused):
                owner.validate_operation({"argv": argv, "stdin": None}, value)

    def test_live_observer_validates_and_replays_apks_before_shared_handles(self):
        events = []

        def read(*_args, **_kwargs):
            events.append("read")
            return admission()

        def verify(pins):
            self.assertEqual(pins, binding.artifact_bindings())
            events.append("verify")

        with (patch.object(owner.mechanisms, "_read_json", side_effect=read),
              patch.object(binding, "verify_artifacts", side_effect=verify),
              patch.object(owner.mechanisms._LiveOwnedTarget, "__init__",
                           side_effect=lambda *_: events.append("handles"))):
            instance = owner.LiveOwnedArchiveProviderPlatformTarget(ADMISSION_PIN, RUNNING_PIN)
        self.assertEqual(events, ["read", "verify", "handles"])
        self.assertIs(instance._contract, owner)
        self.assertIs(instance._verification, owner.REPLAY)
        self.assertIs(owner.REPLAY.c, owner)

        with (patch.object(owner.mechanisms, "_read_json", return_value=admission()),
              patch.object(binding, "verify_artifacts", side_effect=owner.TargetRefused("binding")),
              patch.object(owner.mechanisms._LiveOwnedTarget, "__init__") as handles):
            with self.assertRaisesRegex(owner.TargetRefused, "^binding$"):
                owner.LiveOwnedArchiveProviderPlatformTarget(ADMISSION_PIN, RUNNING_PIN)
            handles.assert_not_called()

    def test_capture_pins_exact_lease_and_refuses_foreign_instances_before_io(self):
        capture = object.__new__(owner.OwnedArchiveProviderPlatformSdkCapture)
        self.assertIs(capture._contract, owner)
        self.assertIs(capture._verification, owner.REPLAY)
        self.assertIs(capture._expected_lease_class, owner.LiveOwnedArchiveProviderPlatformTarget)
        with (patch.object(wire.socket, "socket") as open_socket,
              patch.object(wire.output_control, "validate_output") as open_output):
            with self.assertRaises(wire.ClientRefused):
                owner.OwnedArchiveProviderPlatformSdkCapture("D:/Synthetic/clients", 1200, object())
            open_socket.assert_not_called()
            open_output.assert_not_called()

    def test_subclasses_refuse_before_delegating_to_base(self):
        class ForeignObserver(owner.LiveOwnedArchiveProviderPlatformTarget):
            pass

        class ForeignCapture(owner.OwnedArchiveProviderPlatformSdkCapture):
            pass

        with (patch.object(owner.mechanisms, "_read_json") as read,
              patch.object(owner.mechanisms._LiveOwnedTarget, "__init__") as handles,
              patch.object(wire._OwnedTargetSdkCapture, "__init__") as capture):
            with self.assertRaises(owner.mechanisms.OwnerRefused):
                ForeignObserver(ADMISSION_PIN, RUNNING_PIN)
            with self.assertRaises(wire.ClientRefused):
                ForeignCapture("D:/Synthetic/clients", 1200, object())
            read.assert_not_called()
            handles.assert_not_called()
            capture.assert_not_called()
