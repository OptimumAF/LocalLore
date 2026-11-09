"""Host-only authority checks for the fixed SDK27 storage-opener owner profile.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path, PureWindowsPath
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_storage_opener as owned
from benchmarks import owned_target_contract as core
from benchmarks import storage_opener_capture as capture
from scripts.tests import test_owned_target_contract as fixture
from scripts.tests.test_storage_opener_capture import CLASSES, KINDS, METHODS, argv as instrumentation_argv
from scripts.tests.test_storage_opener_journey import Tape


SOURCE_ROOT = PureWindowsPath("D:/Synthetic/LocalLore")
GUEST = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-storage-opener-owned-guest-v1/avd-v1")


def admission():
    value = fixture.admission()
    value.update(protocol=owned.PROTOCOL, artifacts=capture.artifact_bindings())
    value["guest"]["root"] = str(GUEST)
    paths = [*(SOURCE_ROOT / "benchmarks" / name for name in owned.SOURCE_NAMES),
             *(SOURCE_ROOT / "scripts" / name for name in owned.SCRIPT_SOURCE_NAMES)]
    value["sources"] = sorted(map(fixture.pin, paths), key=lambda pin: pin["path"])
    return value


class StorageOpenerOwnerTests(unittest.TestCase):
    def setUp(self):
        self.admission = admission()

    def assert_operation_refused(self, args, source=None):
        with self.assertRaises(core.TargetRefused):
            owned.validate_operation({"argv": args, "stdin": source}, self.admission)

    def test_fixed_profile_accepts_all_exact_journey_operations(self):
        self.assertEqual(owned.PROTOCOL, "owned-emulator-storage-opener-v1")
        self.assertEqual(owned.SDK_PROTOCOL, "sdk-storage-opener-v1")
        self.assertEqual(owned.PROOF_PROTOCOL, "storage-opener-socket-proof-v1")
        self.assertEqual((owned.CLIENT_VERSION, owned.SESSION_FILE), (27, "sdk-session-v27.json"))
        self.assertEqual(owned.GUEST_ROOT, GUEST)
        self.assertEqual((owned.APP, owned.TEST), ("org.locallore.app.archiveverify", "org.locallore.app.archiveverify.test"))
        self.assertIs(owned.MODEL_MATERIAL, False)
        self.assertEqual(owned.INSTRUMENTATIONS, tuple(zip(KINDS, CLASSES, METHODS)))
        self.assertEqual(owned.CLAIM_KINDS, KINDS)
        self.assertIs(owned.REPLAY.c, owned)
        self.assertTrue(core.CURRENT_STORAGE_SOURCES <= owned.SOURCE_NAMES)
        self.assertEqual(owned.validate_admission(self.admission), self.admission)

        for row in Tape(self.admission["artifacts"]).rows:
            operation = row["operation"]
            with self.subTest(operation=operation):
                self.assertEqual(owned.validate_operation(operation, self.admission), operation)

    def test_shared_registration_facade_accepts_only_the_expected_waiting_or_ready_target(self):
        wait = owned.mechanisms._waiting_devices
        self.assertIsNone(wait(b"", _contract=owned))
        self.assertIsNone(wait(b"emulator-5592          offline transport_id:7\n", _contract=owned))
        self.assertEqual(wait(b"emulator-5592 device transport_id:7\n", _contract=owned), 7)
        with self.assertRaises(core.TargetRefused):
            wait(b"emulator-5594 offline transport_id:7\n", _contract=owned)

    def test_session_rejects_foreign_controller_root_and_non_exact_duration(self):
        session = fixture.session(self.admission)
        descriptor = session["descriptor"]
        descriptor["protocol"] = owned.PROTOCOL
        session.update(protocol=owned.SDK_PROTOCOL,
                       root=str(PureWindowsPath(self.admission["root"]) / "controller-v1"),
                       seconds=1200, started_epoch=descriptor["started_epoch"],
                       deadline_epoch=descriptor["deadline_epoch"])
        self.assertEqual(owned.validate_session(session, self.admission), session)
        variants = (
            dict(session, root=str(PureWindowsPath(self.admission["root"]) / "foreign")),
            dict(session, seconds=1199, deadline_epoch=session["deadline_epoch"] - 1),
            dict(session, protocol="sdk-combined-record-ui-v1"),
        )
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(core.TargetRefused):
                owned.validate_session(variant, self.admission)

    def test_capture_refuses_wrong_duration_and_foreign_lease_before_output_access(self):
        directory = SOURCE_ROOT / "controller-v1" / "clients"
        with patch.object(owned.wire.output_control, "validate_output") as output:
            with self.assertRaisesRegex(owned.wire.ClientRefused, "^client_type$"):
                owned.OwnedStorageOpenerSdkCapture(directory, 1199, object())
            with self.assertRaisesRegex(owned.wire.ClientRefused, "^client_guard$"):
                owned.OwnedStorageOpenerSdkCapture(directory, 1200, object())
        output.assert_not_called()

    def test_exact_two_selectors_make_distinct_nontransferable_claims(self):
        admission_pin = fixture.pin(SOURCE_ROOT / "sdk27-admission.json")
        caller = fixture.running(self.admission)["worker"]
        claims = []
        for index, kind in enumerate(KINDS):
            args = instrumentation_argv(index)
            operation = dict(argv=args, stdin=None)
            digest = owned.operation_digest(operation)
            self.assertEqual(owned.instrumentation_kind(args), kind)
            claim = owned.claim_record(admission_pin, caller, kind, digest)
            self.assertEqual(owned.validate_claim(claim, admission_pin, caller, kind, digest), claim)
            claims.append((kind, digest, claim))
        first, second = claims
        self.assertNotEqual(first[1], second[1])
        with self.assertRaises(core.TargetRefused):
            owned.validate_claim(first[2], admission_pin, caller, second[0], second[1])
        with self.assertRaises(core.TargetRefused):
            owned.claim_record(admission_pin, caller, "foreign", first[1])

    def test_other_installs_foreign_selectors_and_process_commands_are_refused(self):
        apk = "/data/local/tmp/locallore-product-v1.apk"
        selector = instrumentation_argv(0)
        for args in (
            ["pm", "install", "-r", "-t", "--user", "0", apk],
            ["pm", "install", "-R", "-r", "-t", "--user", "0", apk],
            ["pm", "install", "-R", "-t", "--user", "10", apk],
            [*selector[:6], CLASSES[0], selector[-1]],
            [*selector[:6], CLASSES[0] + "#foreign", selector[-1]],
            [*selector[:-1], "org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner"],
            ["cmd", "package", "list", "packages", "-U", "--user", "0", "org.locallore.app"],
            ["sha256sum", "/data/app/foreign.app-fixture/base.apk"],
            ["pidof", owned.APP],
            ["am", "force-stop", "--user", "0", owned.APP],
            ["run-as", owned.APP, "ls", "files"],
            ["df", "-k", "/data"],
            ["dd", "of=/data/local/tmp/model.task", "bs=65536"],
        ):
            with self.subTest(args=args):
                self.assert_operation_refused(args)

    def test_staging_rejects_a_substituted_or_missing_apk(self):
        artifacts = self.admission["artifacts"]
        for role, filename, other in (("product_apk", "product", "test_apk"), ("test_apk", "test", "product_apk")):
            args = ["dd", f"of=/data/local/tmp/locallore-{filename}-v1.apk", "bs=65536"]
            for source in (None, artifacts[other], dict(artifacts[role], sha256="0" * 64)):
                with self.subTest(role=role, source=source):
                    self.assert_operation_refused(args, source)

    def test_admission_refuses_foreign_guest_protocol_or_artifact_roles(self):
        artifacts = self.admission["artifacts"]
        variants = [
            dict(self.admission, protocol="owned-emulator-combined-record-ui-v1"),
            dict(self.admission, guest=dict(self.admission["guest"], root=str(GUEST.parent / "foreign"))),
            dict(self.admission, artifacts=dict(artifacts, model=fixture.pin(SOURCE_ROOT / "model.task"))),
            dict(self.admission, artifacts=dict(artifacts, test_apk=artifacts["product_apk"])),
        ]
        for role in artifacts:
            variants.append(dict(self.admission, artifacts=dict(artifacts, **{
                role: dict(artifacts[role], sha256="0" * 64),
            })))
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(core.TargetRefused):
                owned.validate_admission(variant)

    def test_source_roster_refuses_missing_foreign_and_extra_script_pins(self):
        sources = self.admission["sources"]
        script = next(pin for pin in sources if PureWindowsPath(pin["path"]).parent.name == "scripts")
        leaf = PureWindowsPath(script["path"]).name
        without = [pin for pin in sources if pin != script]
        for variant in (
            without,
            [*without, fixture.pin(SOURCE_ROOT.parent / "Foreign" / "scripts" / leaf)],
            [*without, fixture.pin(SOURCE_ROOT / "benchmarks" / leaf)],
            [*sources, fixture.pin(SOURCE_ROOT / "scripts" / "unreviewed.py")],
        ):
            candidate = dict(self.admission, sources=sorted(variant, key=lambda pin: pin["path"]))
            with self.subTest(variant=variant), self.assertRaises(core.TargetRefused):
                owned.validate_admission(candidate)

    def test_observer_checks_archived_apks_before_any_owner_handle_acquisition(self):
        admission_pin = fixture.pin(SOURCE_ROOT / "sdk27-admission.json")
        running_pin = fixture.pin(SOURCE_ROOT / "running-v1.json")
        events = []

        def verify(pins):
            self.assertEqual(pins, capture.artifact_bindings())
            events.append("verify")

        with (patch.object(owned.mechanisms, "_read_json", return_value=self.admission),
              patch.object(capture, "verify_artifacts", side_effect=verify),
              patch.object(owned.mechanisms._LiveOwnedTarget, "__init__",
                           side_effect=lambda *_: events.append("open"))):
            owned.LiveOwnedStorageOpenerTarget(admission_pin, running_pin)
        self.assertEqual(events, ["verify", "open"])

        with (patch.object(owned.mechanisms, "_read_json", return_value=self.admission),
              patch.object(capture, "verify_artifacts", side_effect=core.TargetRefused("binding")),
              patch.object(owned.mechanisms._LiveOwnedTarget, "__init__") as open_handles):
            with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                owned.LiveOwnedStorageOpenerTarget(admission_pin, running_pin)
        open_handles.assert_not_called()

    def test_capture_bridge_replays_its_exact_commands_and_refuses_reuse(self):
        session = fixture.session(self.admission)
        descriptor = session["descriptor"]
        descriptor["protocol"] = owned.PROTOCOL
        root = Path(self.admission["root"]) / "controller-v1"
        session.update(protocol=owned.SDK_PROTOCOL, root=str(root), seconds=owned.SECONDS,
                       started_epoch=descriptor["started_epoch"], deadline_epoch=descriptor["deadline_epoch"])
        tape = Tape(self.admission["artifacts"])
        client = object.__new__(owned.OwnedStorageOpenerSdkCapture)
        client.clean, client.count = True, 0
        client.until = owned.time.monotonic() + owned.SECONDS
        client.directory = root / "clients"
        client._session = session
        client._session_binding = fixture.pin(root / owned.SESSION_FILE)
        client.lease = Mock()

        def dispatch(argv, label, *, seconds, cap, source=None):
            expected, kind, pin, budget, limit = tape.expected[client.count]
            self.assertEqual((argv, label, source, cap), (expected, kind, pin, limit))
            self.assertTrue(0 < seconds <= budget)
            client.count += 1
            return tape.read_raw(tape.rows[client.count - 1]["stdout"], cap=cap)

        def read_json(pin):
            if pin == session["admission"]:
                return self.admission
            self.assertEqual(pin["path"], str(client.directory / f"command-{client.count:04d}.json"))
            return tape.rows[client.count - 1]

        with (patch.object(capture, "verify_artifacts"),
              patch.object(client, "shell", side_effect=dispatch),
              patch.object(client, "stream", side_effect=lambda argv, source, label, **options:
                           dispatch(argv, label, source=source, **options)),
              patch.object(owned.REPLAY, "_json", side_effect=read_json),
              patch.object(owned.REPLAY, "_pin", side_effect=fixture.pin),
              patch.object(owned.REPLAY, "_at", return_value=session),
              patch.object(owned.REPLAY, "_raw", side_effect=tape.read_raw),
              patch.object(owned.REPLAY, "require_current_clients", return_value=tape.rows) as replay,
              patch.object(owned, "revalidate_inputs") as revalidate,
              patch.object(owned.time, "sleep")):
            result = owned.run_owned_journey(client)
            replay.assert_called_once_with(root, 34, client.session_binding, self.admission)
            revalidate.assert_called_once_with(self.admission)
            self.assertEqual([test["kind"] for test in result["tests"]], list(KINDS))
            with self.assertRaisesRegex(owned.wire.ClientRefused, "^client_guard$"):
                owned.run_owned_journey(client)
