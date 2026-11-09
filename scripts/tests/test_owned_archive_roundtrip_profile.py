"""Synthetic SDK25 profile tests without sockets, processes, or a guest."""
import copy
from pathlib import Path, PureWindowsPath
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_build as build
from benchmarks import owned_archive_roundtrip_client as client
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner
from benchmarks import owned_target_contract as core
from scripts.tests import test_owned_target_contract as legacy


def admission():
    value = legacy.admission()
    value["protocol"] = contract.PROTOCOL
    value["guest"]["root"] = str(contract.GUEST_ROOT)
    value["artifacts"] = build._bindings((PureWindowsPath("D:/Synthetic/archive-apks"),
                                           PureWindowsPath("D:/Synthetic/archive-windows")))
    root = PureWindowsPath("D:/Synthetic/LocalLore/benchmarks")
    value["sources"] = [legacy.pin(root / name) for name in sorted(contract.SOURCE_NAMES)]
    return value


def operation(argv, source=None):
    return dict(argv=argv, stdin=source)


class ArchiveProfileTests(unittest.TestCase):
    def setUp(self):
        self.value = admission()

    def check(self, argv, source=None):
        expected = operation(argv, source)
        self.assertEqual(contract.validate_operation(expected, self.value), expected)

    def refuse(self, argv, source=None):
        with self.assertRaises(contract.TargetRefused):
            contract.validate_operation(operation(argv, source), self.value)

    def test_admission_uses_fixed_model_free_profile_without_io(self):
        with (patch.object(Path, "open", side_effect=AssertionError("file")),
              patch.object(socket, "socket", side_effect=AssertionError("socket")),
              patch.object(subprocess, "Popen", side_effect=AssertionError("process"))):
            decoded = contract.validate_admission(self.value)
        self.assertEqual(decoded, self.value)
        self.assertIsNot(decoded["artifacts"], self.value["artifacts"])
        self.assertFalse(contract.PROFILE.profile.MODEL_MATERIAL)
        self.assertEqual(contract.CLIENT_VERSION, 25)
        self.assertEqual(contract.RUN_SCOPE, "owned-emulator-archive-roundtrip-v1")
        self.assertEqual(contract.CLAIM_KINDS, ("archive_outbound", "archive_return_write", "archive_return"))
        self.assertEqual(contract.ARTIFACT_KEYS, build.ARTIFACT_KEYS)

    def test_old_or_retagged_profile_and_altered_inputs_refuse(self):
        for edit in (
                lambda a: a.update(protocol=core.PROTOCOL),
                lambda a: a.update(profile="caller-selected"),
                lambda a: a["guest"].update(root=str(core.GUEST_ROOT)),
                lambda a: a["guest"].update(serial="emulator-5554"),
                lambda a: a["artifacts"].update(model=legacy.pin("D:/Synthetic/model")),
                lambda a: a["artifacts"].pop("fixture_preflight"),
                lambda a: a["artifacts"]["product_apk"].update(sha256="f" * 64),
                lambda a: a["artifacts"]["expectations"].update(bytes=1),
                lambda a: a["artifacts"]["fixture_executable"].update(path="D:/Synthetic/other.exe"),
                lambda a: a["sources"].pop()):
            with self.subTest(edit=edit):
                changed = copy.deepcopy(self.value)
                edit(changed)
                with self.assertRaises(contract.TargetRefused):
                    contract.validate_admission(changed)
        with self.assertRaises(core.TargetRefused):
            core.validate_admission(self.value)

    def test_shared_registration_parses_only_fixed_owned_transport(self):
        waiting = owner.shared._waiting_devices
        self.assertIsNone(waiting(b"", _contract=contract))
        self.assertIsNone(waiting(b"emulator-5592 offline transport_id:7\n", _contract=contract))
        self.assertEqual(waiting(b"emulator-5592 device transport_id:7\n", _contract=contract), 7)
        for raw in (b"emulator-5554 device transport_id:7\n", b"emulator-5592 device\n"):
            with self.assertRaises(contract.TargetRefused):
                waiting(raw, _contract=contract)

    def test_outbound_exact_selector_and_derived_run(self):
        argv = ["am", "instrument", "-w", "-r", "-e", "class",
                "org.locallore.app.ArchivePlatformRoundTripTest#platformRoundTrip",
                "-e", "platform_phase", "outbound", "-e", "platform_run",
                "transfer-" + self.value["run_id"],
                "org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner"]
        self.assertEqual(contract.outbound_argv(self.value), argv)
        self.assertEqual(contract.instrumentation_kind(argv), "archive_outbound")
        self.check(argv)
        self.refuse(argv, self.value["artifacts"]["build"])
        for index, change in ((6, "other.Test#run"), (9, "invalid"),
                              (12, "transfer-" + "f" * 32), (12, "../escape"), (13, "foreign/runner")):
            bad = list(argv)
            bad[index] = change
            self.refuse(bad)
        with self.assertRaises(contract.TargetRefused):
            contract.instrumentation_kind(argv + ["-e", "extra", "value"])

    def test_staging_uses_bound_role_and_nonclobber_and_install_does_not_replace(self):
        staged = []
        for role in contract.ROLES:
            path = contract.staged_path(self.value, role)
            staged.append(path)
            self.assertIn("transfer-" + self.value["run_id"], path)
            stage = contract.stage_argv(self.value, role)
            self.assertEqual(stage[:2], ["sh", "-c"])
            self.assertIn("set -C && test ! -e " + path + " && test ! -L " + path, stage[2])
            self.check(stage, self.value["artifacts"][role])
            self.refuse(stage)
            self.refuse(stage, self.value["artifacts"]["build"])
            self.refuse(stage[:2] + [stage[2] + "; id"], self.value["artifacts"][role])
            install = ["pm", "install", "-R", "-t", "--user", "0", path]
            self.assertEqual(contract.install_argv(self.value, role), install)
            self.check(install)
            self.check(["sha256sum", path])
            self.refuse(["pm", "install", "-r", "-t", "--user", "0", path])
            self.refuse(["pm", "install", "-R", "-t", "--user", "10", path])
        self.assertEqual(len(set(staged)), 2)
        self.refuse(contract.stage_argv(self.value, "test_apk"), self.value["artifacts"]["product_apk"])

    def test_only_fixed_archive_leaves_are_read_with_owner_and_bounds(self):
        for leaf in ("owner-v1", "windows-return.json", "windows-continued.json", "android-origin.json"):
            argv = contract.read_argv(self.value, leaf)
            self.assertEqual(argv[:6], ["run-as", contract.APP, "--user", "0", "sh", "-c"])
            script = argv[-1]
            base = "no_backup/platform-roundtrip/transfer-" + self.value["run_id"]
            for guard in ("id -u", "test ! -L " + base, "stat -c %u", "stat -c %h",
                          "sha256sum " + base + "/owner-v1",
                          "head -c 131073 " + base + "/" + leaf):
                self.assertIn(guard, script)
            self.check(argv)
            self.refuse(argv, self.value["artifacts"]["build"])
            self.refuse(argv[:-1] + [script + "; cat files/story"])
        for leaf in ("android-other.json", "../files/story", "", None):
            with self.assertRaises(contract.TargetRefused):
                contract.read_argv(self.value, leaf)

    def test_queries_are_limited_to_the_two_isolated_packages(self):
        for package in (contract.APP, contract.TEST):
            self.check(["cmd", "package", "list", "packages", "-U", "--user", "0", package])
            self.check(["cmd", "package", "path", "--user", "0", package])
            self.check(["sha256sum", "/data/app/~~Token/" + package + "-Other/base.apk"])
        for bad in (["cmd", "package", "list", "packages"], ["cmd", "package", "path", "--user", "0", "org.locallore.app"],
                    ["sha256sum", "/data/app/../" + contract.APP + "-token/base.apk"],
                    ["sha256sum", "/data/app/org.locallore.app-token/base.apk"],
                    ["sha256sum", "/data/local/tmp/locallore-product-v1.apk"],
                    ["getprop", "ro.serialno"], ["dd", "of=/data/local/tmp/locallore-product-v1.apk", "bs=65536"],
                    ["am", "force-stop", "--user", "0", contract.APP], ["pm", "clear", contract.APP],
                    ["run-as", contract.APP, "sh", "-c", "id"], ["screencap", "-p"]):
            self.refuse(bad)

    @unittest.skipUnless(Path(tempfile.gettempdir()).drive.upper() == "D:", "physical D synthetic output")
    def test_shared_owner_spends_one_outbound_claim_across_lease_objects(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = copy.deepcopy(self.value)
            value["root"] = str(root)
            binding = legacy.pin(root / "admission.json")
            caller = legacy.running(self.value)["worker"]

            def lease():
                target = owner.LiveOwnedArchiveRoundtripTarget.__new__(owner.LiveOwnedArchiveRoundtripTarget)
                target._admission, target._admission_binding, target._caller = value, binding, caller
                target.guard = Mock()
                return target

            digest = contract.operation_digest(operation(contract.outbound_argv(self.value)))
            lease().claim_once(contract.OUTBOUND, digest)
            receipt = root / "claims-v1" / "archive_outbound-v1.json"
            before = receipt.read_bytes()
            with self.assertRaises((FileExistsError, owner.shared.OwnerRefused,
                                    owner.shared.output_control.ControlRefused)):
                lease().claim_once(contract.OUTBOUND, digest)
            self.assertEqual(receipt.read_bytes(), before)


class OwnerWireTests(unittest.TestCase):
    def test_worker_and_live_lease_verify_exact_artifacts_before_shared_process_code(self):
        a = admission()
        refusal = build.BuildRefused("digest")
        with (patch.object(owner.build, "verify_current", side_effect=refusal) as check,
              patch.object(owner.shared._TargetRuntimeCore, "__init__") as runtime,
              patch.object(owner.shared._LiveOwnedTarget, "__init__") as live,
              patch.object(owner.shared, "_read_json", return_value=a)):
            with self.assertRaises(build.BuildRefused):
                owner._ArchiveRuntime({"validated_admission": a}, {}, None)
            with self.assertRaises(build.BuildRefused):
                owner.LiveOwnedArchiveRoundtripTarget({}, {})
        self.assertEqual(check.call_count, 2)
        runtime.assert_not_called()
        live.assert_not_called()

    def test_closed_owner_replay_rechecks_input_bytes_before_guest_proof(self):
        with (patch.object(owner.build, "verify_current", side_effect=build.BuildRefused("digest")) as check,
              patch.object(owner.replay._Verifier, "verify_guest_inputs") as shared):
            value = admission()
            with self.assertRaises(build.BuildRefused):
                owner.VERIFIER.verify_guest_inputs({}, value, {})
        check.assert_called_once_with(value)
        shared.assert_not_called()

    def test_closed_client_replay_caps_combined_streams_before_readback(self):
        record = {"stdout": {"bytes": contract.MAX_BYTES - 1}, "stderr": {"bytes": 1}}
        with patch.object(core._Contract, "validate_client_record", return_value=record):
            self.assertEqual(contract.validate_client_record({}, {}), record)
            record["stderr"]["bytes"] = 2
            with self.assertRaises(contract.TargetRefused):
                contract.validate_client_record({}, {})

    def test_worker_only_entry_uses_fixed_profile_and_shared_replay(self):
        with patch.object(owner.shared, "_main_profile", return_value=0) as entry:
            self.assertEqual(owner.main(["--admission", "D:/Synthetic/plan.json", "--admission-sha256", "a" * 64]), 1)
            self.assertEqual(owner.main(["_worker", "other"]), 1)
            entry.assert_not_called()
            self.assertEqual(owner.main(["_worker"]), 0)
        entry.assert_called_once_with(["_worker"], _contract=contract,
                                      _verification=owner.VERIFIER, _runtime_type=owner._ArchiveRuntime)
        self.assertIs(owner.VERIFIER.c, contract)

    def test_client_chooses_exact_lease_and_bounds_capture_before_wire(self):
        capture = client.OwnedArchiveRoundtripSdkCapture.__new__(client.OwnedArchiveRoundtripSdkCapture)
        self.assertIs(capture._contract, contract)
        self.assertIs(capture._verification, owner.VERIFIER)
        self.assertIs(capture._expected_lease_class, owner.LiveOwnedArchiveRoundtripTarget)
        argv = ["getprop", "sys.boot_completed"]
        capture._poison = Mock()
        with patch.object(client.wire._OwnedTargetSdkCapture, "_execute", return_value=b"1") as run:
            with self.assertRaises(client.wire.ClientRefused):
                capture._execute(argv, None, "boot", 15, contract.MAX_BYTES + 1, False)
            run.assert_not_called()
            capture._poison.assert_called_once_with()
            self.assertEqual(capture._execute(argv, None, "boot", 15, 1, False), b"1")
        run.assert_called_once_with(argv, None, "boot", 15, 1, False)

    def test_client_wrong_lease_refuses_before_observing_target(self):
        foreign = Mock()
        with self.assertRaises(client.wire.ClientRefused):
            client.OwnedArchiveRoundtripSdkCapture(None, 1, foreign)
        foreign.guard.assert_not_called()


if __name__ == "__main__":
    unittest.main()
