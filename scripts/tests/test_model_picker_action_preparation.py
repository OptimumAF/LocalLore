"""Synthetic picker preparation-input adversaries with host, SDK and port effects mocked.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack, contextmanager
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import model_picker_action_preparation as preparation
from scripts.tests.test_model_picker_action_handoff import BootRecords
from scripts.tests.test_owned_target_contract import pin


h = preparation.h
env = preparation.env
storage = preparation.storage
contract = preparation.contract
REFUSED = (ValueError, RuntimeError)


class Ports:
    def __init__(self):
        sample = BootRecords().admission
        server, guest = sample["server"], sample["guest"]
        source = pin(h.ROOT / "benchmarks/native/deny_adb_client.c")
        sdk = Path(server["adb"]["path"]).parent.parent
        emulator = pin(sdk / "emulator/emulator.exe")
        qemu = pin(sdk / "emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe")
        self.authority = {"ledger": pin(h.LEDGER)}
        self.plan = dict(
            sources=sample["sources"], python=sample["python"], artifacts=sample["artifacts"],
            prepare=pin(h.PREPARE),
            installed=dict(adb=server["adb"], tools=server["tools"], auth_key_path=server["auth_key"],
                           capabilities=server["capabilities"], source_review=server["source_review"],
                           emulator=emulator, qemu=qemu, refuser=guest["refuser"],
                           refuser_source=source, compatibility=sample["compatibility"]),
        )
        self.prepare = dict(sdk=str(sdk), adb_path=server["adb"]["path"])
        self.ledger = {"version": 2}
        self.preview = dict(root=str(h.GUEST), ledger=self.authority["ledger"], would_fit=True,
                            admission_granted=False)
        self.entry = dict(state="prepared", proposal_sha256=self.plan["prepare"]["sha256"],
                          reserved_bytes=storage.RESERVATION_BYTES,
                          closure=None, recovery=None, retirement=None, retirement_receipt=None)
        self.bind = Mock(return_value=source)
        self.key_info = SimpleNamespace(st_size=1704, st_nlink=1)
        self.files = set()
        self.records = {}
        self.native = Mock()
        self.private = Mock(return_value=dict(exclusive_bind_succeeded=True, created_mask=1,
                                             close_attempted_mask=1, closed_mask=1))
        self.ports = Mock()
        self.verify_artifacts = Mock()
        self.revalidate = Mock()
        self.adb_inputs = Mock(side_effect=preparation.server.validate_admission)
        self.resources = Mock(return_value={"free_bytes": {"D:": 60 * 1024**3}})
        self.check_binding = Mock()
        self.save = Mock(side_effect=self._save)
        self.plan_run = Mock(side_effect=self._run_plan)
        self.publish = dict(prepare_proposal=self.plan["prepare"])

    def _save(self, path, value):
        if path in self.files:
            raise AssertionError("synthetic record overwritten")
        self.files.add(path)
        self.records[path] = copy.deepcopy(value)
        return pin(path)

    def _run_plan(self, prepare, prepared, output, *, max_seconds):
        self._save(output, self.publish)
        return self.publish

    def _safe_path(self, path, **kwargs):
        if Path(path) == Path(self.plan["installed"]["auth_key_path"]):
            return SimpleNamespace(stat=lambda: self.key_info)
        return path

    @contextmanager
    def inert(self):
        token = str(Path(self.plan["installed"]["auth_key_path"]).parent.parent / ".emulator_console_auth_token")
        with ExitStack() as stack:
            for module, name, options in (
                (h, "at", {"return_value": self.ledger}),
                (h, "prepare_plan", {"return_value": self.prepare}),
                (h, "ledger_entry", {"return_value": (self.authority["ledger"], self.entry)}),
                (h, "read", {"side_effect": lambda path, cap: (pin(path), self.records[path])}),
                (storage, "_validate", {}),
                (storage, "preview_prepare", {"return_value": self.preview}),
                (contract, "source_bindings", {"return_value": self.plan["sources"]}),
                (preparation.artifacts, "verify_artifacts", {"new": self.verify_artifacts}),
                (contract, "revalidate_inputs", {"new": self.revalidate}),
                (preparation.server, "revalidate_inputs", {"new": self.adb_inputs}),
                (env, "safe_path", {"side_effect": self._safe_path}),
                (env, "verify_installation", {}),
                (env, "check_external_state", {}),
                (env, "check_binding", {"new": self.check_binding}),
                (env, "binding", {"new": self.bind}),
                (env, "token_path", {"return_value": token}),
                (env, "resource_facts", {"new": self.resources}),
                (env, "ports_free", {"new": self.ports}),
                (env, "plan_run", {"new": self.plan_run}),
                (preparation.mechanisms, "_ProcessApi", {"new": self.native}),
                (preparation.process, "_exclusive_preflight", {"new": self.private}),
                (preparation.os.path, "lexists", {"side_effect": self.files.__contains__}),
                (h, "save", {"new": self.save}),
            ):
                stack.enter_context(patch.object(module, name, **options))
            yield

    def preflight(self):
        with self.inert():
            return preparation.preflight(self.authority, self.plan, self.prepare)

    def pending(self):
        with self.inert():
            return preparation.preflight_pending(self.authority["ledger"], self.plan, self.prepare)

    def create(self):
        with self.inert():
            return preparation.create_admission(self.plan)


class PickerActionPreparationTests(unittest.TestCase):
    def test_preflight_checks_exact_inputs_without_writing(self):
        ports = Ports()
        self.assertEqual(ports.preflight(), dict(
            resources=ports.resources.return_value, storage=ports.preview, ports_free=True,
        ))
        checked_server, = ports.adb_inputs.call_args.args
        self.assertEqual(checked_server["root"], str(h.OWNED_ROOT / "server"))
        self.assertEqual(checked_server["python"], ports.plan["python"])
        self.assertEqual(checked_server["adb"], ports.plan["installed"]["adb"])
        ports.resources.assert_called_once_with(ports.prepare)
        ports.ports.assert_called_once_with()
        ports.private.assert_called_once_with(ports.native.return_value, port=contract.PORT)
        self.assertEqual(ports.verify_artifacts.call_count, 2)
        self.assertEqual(ports.check_binding.call_args_list[-2].args, (ports.plan["prepare"],))
        self.assertEqual(ports.check_binding.call_args_list[-1].args, (ports.authority["ledger"],))
        self.assertEqual(ports.records, {})

    def test_pending_preflight_requires_absent_authority_and_attempt(self):
        self.assertTrue(Ports().pending()["ports_free"])
        for path in (h.AUTHORITY, h.ATTEMPT_ROOT):
            with self.subTest(path=path):
                ports = Ports()
                ports.files.add(path)
                with self.assertRaisesRegex(REFUSED, "already_used"):
                    ports.pending()
                ports.adb_inputs.assert_not_called()
                ports.private.assert_not_called()
                self.assertEqual(ports.records, {})

    def test_preflight_refuses_a_prepare_object_different_from_the_pinned_plan(self):
        ports = Ports()
        foreign = dict(ports.prepare, sdk="C:/Synthetic/other-sdk")
        with ports.inert(), self.assertRaisesRegex(REFUSED, "plan"):
            preparation.preflight(ports.authority, ports.plan, foreign)
        ports.adb_inputs.assert_not_called()
        ports.ports.assert_not_called()

    def test_late_artifact_drift_refuses_pending_and_approved_preflight(self):
        for mode in ("pending", "preflight"):
            with self.subTest(mode=mode):
                ports = Ports()
                ports.verify_artifacts.side_effect = [None, contract.TargetRefused("binding")]
                with self.assertRaisesRegex(REFUSED, "binding"):
                    getattr(ports, mode)()
                ports.private.assert_called_once()
                self.assertEqual(ports.records, {})

    def test_existing_outputs_refuse_before_capacity_or_ports(self):
        for path in (h.GUEST, h.ADMISSION, h.RUN, h.RUN_AUTHORITY, h.HANDOFF,
                     h.OWNED_ROOT, preparation.CONTROL):
            with self.subTest(path=path):
                ports = Ports()
                ports.files.add(path)
                with self.assertRaisesRegex(REFUSED, "already_used"):
                    ports.preflight()
                ports.resources.assert_not_called()
                ports.ports.assert_not_called()

    def test_unreviewed_or_over_capacity_ledger_refuses_before_port_probe(self):
        for key, value in (("ledger", pin(h.LEDGER, sha="0" * 64)), ("root", "D:/Synthetic/other"),
                           ("would_fit", False), ("admission_granted", True), ("would_fit", 1)):
            with self.subTest(key=key, value=value):
                ports = Ports()
                ports.preview[key] = value
                with self.assertRaises(REFUSED):
                    ports.preflight()
                ports.adb_inputs.assert_not_called()
                ports.ports.assert_not_called()
        ports = Ports()
        ports.ledger["version"] = 1
        with self.assertRaisesRegex(REFUSED, "ledger"):
            ports.preflight()
        ports.ports.assert_not_called()

    def test_unmatched_installed_tool_or_auth_key_metadata_refuses_before_port_probe(self):
        for mutate in (
            lambda ports: ports.plan["installed"]["qemu"].update(path=str(Path("C:/Synthetic/other.exe"))),
            lambda ports: setattr(ports.key_info, "st_nlink", 2),
            lambda ports: setattr(ports.key_info, "st_size", 0),
        ):
            with self.subTest(mutation=mutate):
                ports = Ports()
                mutate(ports)
                with self.assertRaises(REFUSED):
                    ports.preflight()
                ports.resources.assert_not_called()
                ports.ports.assert_not_called()

    def test_partial_private_port_cleanup_refuses(self):
        for field, value in (("exclusive_bind_succeeded", 1), ("created_mask", True),
                             ("close_attempted_mask", 0), ("closed_mask", 0)):
            with self.subTest(field=field):
                ports = Ports()
                ports.private.return_value[field] = value
                with self.assertRaisesRegex(REFUSED, "ports_unavailable"):
                    ports.preflight()
                self.assertEqual(ports.records, {})

    def test_postflight_ledger_drift_or_freshness_change_refuses(self):
        ports = Ports()
        def check_binding(pin_value):
            if pin_value == ports.authority["ledger"]:
                raise env.EnvironmentRefused("binding_changed")
        ports.check_binding.side_effect = check_binding
        with self.assertRaisesRegex(REFUSED, "binding_changed"):
            ports.preflight()
        ports.private.assert_called_once()

        ports = Ports()
        def changed_root(*args, **kwargs):
            ports.files.add(h.GUEST)
            return dict(exclusive_bind_succeeded=True, created_mask=1, close_attempted_mask=1, closed_mask=1)
        ports.private.side_effect = changed_root
        with self.assertRaisesRegex(REFUSED, "already_used"):
            ports.preflight()

    def test_exact_scoped_run_auth_and_valid_admission_are_published_once(self):
        ports = Ports()
        self.assertEqual(ports.create(), pin(h.ADMISSION))
        ports.plan_run.assert_called_once_with(ports.plan["prepare"]["path"],
                                              h.GUEST / "prepared-v1.json", h.RUN,
                                              max_seconds=1800)
        value = ports.records[h.ADMISSION]
        self.assertEqual(value["root"], str(h.OWNED_ROOT))
        self.assertEqual(value["guest"]["root"], str(h.GUEST))
        self.assertEqual(value["server"]["run_id"], value["run_id"])
        self.assertEqual(value["artifacts"], preparation.artifacts.artifact_bindings())
        self.assertEqual(value["guest"]["authorization"], pin(h.RUN_AUTHORITY))
        self.assertEqual(value["guest"]["proposal"], pin(h.RUN))
        self.assertEqual(set(ports.records), {h.RUN, h.RUN_AUTHORITY, h.ADMISSION})
        self.assertEqual(ports.revalidate.call_args.args, (value,))
        receipt = ports.records[h.RUN_AUTHORITY]
        digest = value["guest"]["proposal"]["sha256"]
        env.check_authorization(receipt, "run", digest, run_scope=contract.RUN_SCOPE)
        with self.assertRaisesRegex(REFUSED, "not_authorized"):
            env.check_authorization(receipt, "run", digest)
        with self.assertRaisesRegex(REFUSED, "already_used"):
            ports.create()
        ports.plan_run.assert_called_once()

    def test_changed_prepared_entry_refuses_before_run_proposal_publication(self):
        for key, value in (("state", "closed"), ("proposal_sha256", "0" * 64),
                           ("reserved_bytes", 1), ("recovery", {}), ("closure", {}),
                           ("retirement_receipt", {})):
            with self.subTest(key=key):
                ports = Ports()
                ports.entry[key] = value
                with self.assertRaisesRegex(REFUSED, "prepared"):
                    ports.create()
                ports.plan_run.assert_not_called()
                self.assertEqual(ports.records, {})

    def test_changed_artifact_refuses_before_run_proposal_publication(self):
        ports = Ports()
        ports.verify_artifacts.side_effect = contract.TargetRefused("binding")
        with self.assertRaisesRegex(REFUSED, "binding"):
            ports.create()
        ports.plan_run.assert_not_called()
        self.assertEqual(ports.records, {})

    def test_spent_boot_claim_refuses_before_run_proposal_publication(self):
        ports = Ports()
        ports.files.add(h.GUEST / contract.BOOT_CLAIM_FILE)
        with self.assertRaisesRegex(REFUSED, "already_used"):
            ports.create()
        ports.plan_run.assert_not_called()
        self.assertEqual(ports.records, {})

    def test_wrong_prepare_binding_keeps_run_proposal_without_run_auth(self):
        ports = Ports()
        ports.publish["prepare_proposal"] = pin(h.PREPARE, sha="0" * 64)
        with self.assertRaisesRegex(REFUSED, "proposal"):
            ports.create()
        self.assertEqual(set(ports.records), {h.RUN})
        ports.save.assert_not_called()

    def test_changed_ledger_after_run_plan_keeps_inputs_without_admission(self):
        ports = Ports()
        ports.check_binding.side_effect = env.EnvironmentRefused("binding_changed")
        with self.assertRaisesRegex(REFUSED, "binding_changed"):
            ports.create()
        self.assertEqual(set(ports.records), {h.RUN, h.RUN_AUTHORITY})
