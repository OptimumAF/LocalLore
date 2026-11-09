"""SDK24 preparation gates with real synthetic records and no SDK execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import cross_owner_deletion_ui_preparation as prep


class CrossOwnerDeletionPreparationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        records = self.root / "preparation"
        records.mkdir()
        guest_parent = self.root / "guest-parent"
        guest_parent.mkdir()
        for name, value in dict(
            PREP_ROOT=records, PLAN=records / "plan-v1.json", PREPARE=records / "prepare-proposal-v1.json",
            PROPOSED_PREPARATION=records / "PROPOSED_PREPARATION.md", AUTHORITY=records / "human-authority-v1.json",
            CLAIM=records / "claim-v1.json", PREPARE_AUTH=records / "prepare-authorization-v1.json",
            RESULT=records / "preparation-result-v1.json",
        ).items():
            self.enterContext(patch.object(prep, name, value))
        self.enterContext(patch.multiple(prep.h, GUEST=guest_parent / "avd-v1", OUT=self.root / "activation",
                                         LEDGER=self.root / "ledger-v1.json", OWNED_ROOT=self.root / "owner"))
        self.sdk = self.root / "sdk"
        self.java = self.root / "java"
        adb = self._file(self.sdk / "platform-tools/adb.exe")
        emulator = self._file(self.sdk / "emulator/emulator.exe")
        qemu = self._file(self.sdk / "emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe")
        self.python = dict(executable=self._file(self.root / "python.exe"), runtime_dll=None)
        self.source = self._file(self.root / "benchmarks/source.py")
        self.key = self.root / ".android/adbkey"
        self._file(self.key)
        self.installed = dict(
            adb=adb, tools=[adb], auth_key_path=str(self.key),
            capabilities=self._file(self.root / "capabilities.json"),
            source_review=self._file(self.root / "source-review.md"), emulator=emulator, qemu=qemu,
            refuser=self._file(self.root / "deny-adb-client.exe"),
            refuser_source=self._file(self.root / "old/deny_adb_client.c"),
            compatibility=self._file(self.root / "compatibility.md"),
        )
        self.proposal = dict(paths={"root": str(prep.h.GUEST)}, memory_mib=8192, cores=4, sdk=str(self.sdk),
                             adb_path=adb["path"], host_free_min={"D:": 40 * 1024**3})
        self.pins = {"build": self._file(self.root / "fake-build.json")}
        self.ledger = self._save(prep.h.LEDGER, {"version": 2})
        self.preview = dict(root=str(prep.h.GUEST), ledger=self.ledger, would_fit=True, admission_granted=False)
        self.plan_tool = self.enterContext(patch.object(prep.env, "plan_prepare", side_effect=self._plan_prepare))
        self.sdk_prepare = self.enterContext(patch.object(prep.env, "prepare", side_effect=self._perform_prepare))
        self.enterContext(patch.object(prep.env, "validate_proposal"))
        self.enterContext(patch.object(prep.env, "verify_prepared"))
        self.enterContext(patch.object(prep.env, "verify_installation"))
        self.enterContext(patch.object(prep.env, "check_external_state"))
        self.enterContext(patch.object(prep.env, "token_path", return_value=self.root / ".emulator_console_auth_token"))
        self.enterContext(patch.object(prep.env, "resource_facts", return_value={"free_bytes": {"D:": 42 * 1024**3}}))
        self.ports = self.enterContext(patch.object(prep.env, "ports_free"))
        self.enterContext(patch.object(prep.mechanisms, "_ProcessApi"))
        self.private = self.enterContext(patch.object(
            prep.process, "_exclusive_preflight",
            return_value=dict(exclusive_bind_succeeded=True, created_mask=1, close_attempted_mask=1, closed_mask=1),
        ))
        self.enterContext(patch.object(prep.storage, "preview_prepare", return_value=self.preview))
        self.enterContext(patch.object(prep.owned, "source_bindings", return_value=[self.source]))
        self.enterContext(patch.object(prep.python_probe, "_python_bindings", return_value=self.python))
        self.enterContext(patch.object(prep.artifacts, "artifact_bindings", return_value=self.pins))
        self.artifacts = self.enterContext(patch.object(prep.artifacts, "verify_artifacts"))
        self.adb = self.enterContext(patch.object(prep.server, "revalidate_inputs"))
        self.plan = prep.build_plan(self.sdk, self.java, self.installed)
        self.prepare_pin = prep.env.binding(prep.PREPARE)
        self.entry = dict(state="prepared", proposal_sha256=self.prepare_pin["sha256"],
                          reserved_bytes=prep.storage.RESERVATION_BYTES, closure=None, recovery=None,
                          retirement=None, retirement_receipt=None)
        self.ledger_entry = self.enterContext(patch.object(prep.h, "ledger_entry", side_effect=self._ledger_entry))

    @staticmethod
    def _file(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic\n")
        return prep.env.binding(path)

    @staticmethod
    def _save(path, value):
        prep.env.create_json(path, value)
        return prep.env.binding(path)

    def _plan_prepare(self, root, sdk, java_home, output, **options):
        self.assertEqual((root, sdk, java_home, output), (prep.h.GUEST, self.sdk, self.java, prep.PREPARE))
        self.assertEqual(options, dict(real_candidate=True, four_core_candidate=True))
        self._save(output, self.proposal)
        return self.proposal

    def _ledger_entry(self):
        return prep.env.binding(prep.h.LEDGER), self.entry

    def _approve(self, **overrides):
        text = f"Plan SHA-256 {self.plan['sha256']}\nLedger SHA-256 {self.ledger['sha256']}\n"
        prep.PROPOSED_PREPARATION.write_text(text, encoding="utf-8", newline="\n")
        authority = dict(version=1, scope=prep.PREPARE_SCOPE,
                         proposal=prep.env.binding(prep.PROPOSED_PREPARATION), plan=self.plan, ledger=self.ledger,
                         approval_reference="synthetic user approval", allow_sdk_prepare=True,
                         allow_one_boot=False, allow_model=False, allow_retirement=False)
        return self._save(prep.AUTHORITY, dict(authority, **overrides))

    def _perform_prepare(self, *_args, **_kwargs):
        root = prep.h.GUEST
        root.mkdir()
        python = self.python["executable"]["path"]
        owned = dict(pid=111, creation_filetime=100, executable=python)
        worker = dict(pid=222, creation_filetime=102, executable=python)
        fields = dict(proposal_sha256=self.prepare_pin["sha256"], prepare_scope=prep.PREPARE_SCOPE)
        self._save(root / "prepare-start-v1.json", dict(**fields, facts={}, owner=owned))
        self._save(root / "prepare-worker-claimed-v1.json", dict(**fields, worker=worker))
        raw = b"synthetic\n"
        (root / "prepare-stdout-v1.bin").write_bytes(raw)
        self._save(root / "prepare-client-v1.json", dict(status="completed", returncode=0,
                   cleanup_complete=True, elapsed_ms=10, stdout_sha256=hashlib.sha256(raw).hexdigest(),
                   stderr_bytes=0))
        self._save(root / "prepared-v1.json", {"proposal_sha256": self.prepare_pin["sha256"]})
        self._save(root / "prepare-result-v1.json", {"status": "completed"})

    def test_build_publishes_only_fixed_plan_inputs_and_current_refuser_source(self):
        self.assertEqual({p.name for p in prep.PREP_ROOT.iterdir()}, {prep.PLAN.name, prep.PREPARE.name})
        self.assertFalse(prep.h.GUEST.exists())
        self.assertFalse(prep.h.OUT.exists())
        plan, proposal = prep.load_plan(self.plan)
        self.assertEqual(plan["prepare"], self.prepare_pin)
        self.assertEqual(plan["installed"]["refuser_source"],
                         prep.env.binding(prep.ROOT / "benchmarks/native/deny_adb_client.c"))
        self.assertEqual(proposal, self.proposal)
        self.sdk_prepare.assert_not_called()

    def test_file_only_preflight_checks_all_ports_without_authorizing(self):
        observed = prep.inspect(self.plan, self.ledger)
        self.assertFalse(observed["execution_authorized"])
        self.assertTrue(observed["ports_free"])
        self.assertFalse(observed["storage"]["admission_granted"])
        self.ports.assert_called_once_with()
        self.private.assert_called_once()
        self.assertEqual(self.private.call_args.kwargs, {"port": prep.owned.PORT})
        self.adb.assert_called_once()
        self.sdk_prepare.assert_not_called()
        self.assertFalse(prep.AUTHORITY.exists())
        self.assertFalse(prep.CLAIM.exists())
        self.assertFalse(prep.PREPARE_AUTH.exists())

    def test_preflight_refuses_ledger_drift_before_tool_or_port_checks(self):
        prep.h.LEDGER.write_text('{"version":2,"changed":true}\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "binding"):
            prep.inspect(self.plan, self.ledger)
        self.adb.assert_not_called()
        self.ports.assert_not_called()
        self.sdk_prepare.assert_not_called()

    def test_preflight_refuses_capacity_or_unknown_port_close(self):
        self.preview["would_fit"] = False
        with self.assertRaisesRegex(RuntimeError, "storage_capacity"):
            prep.inspect(self.plan, self.ledger)
        self.ports.assert_not_called()
        self.preview["would_fit"] = True
        self.private.return_value["closed_mask"] = 0
        with self.assertRaisesRegex(RuntimeError, "ports_unavailable"):
            prep.inspect(self.plan, self.ledger)
        self.sdk_prepare.assert_not_called()
        self.assertFalse(prep.CLAIM.exists())

    def test_extra_records_capacity_is_required_before_port_checks(self):
        prep.env.resource_facts.return_value["free_bytes"]["D:"] = 40 * 1024**3
        with self.assertRaisesRegex(RuntimeError, "records_capacity"):
            prep.inspect(self.plan, self.ledger)
        self.ports.assert_not_called()

    def test_wrong_approval_scope_or_flags_refuse_before_claim(self):
        authority = self._approve(allow_one_boot=True)
        with self.assertRaisesRegex(RuntimeError, "authority"):
            prep.prepare(authority)
        self.assertFalse(prep.CLAIM.exists())
        self.sdk_prepare.assert_not_called()

    def test_approval_markdown_pin_drift_refuses_before_claim(self):
        authority = self._approve()
        prep.PROPOSED_PREPARATION.write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "binding"):
            prep.prepare(authority)
        self.assertFalse(prep.CLAIM.exists())
        self.sdk_prepare.assert_not_called()

    def test_preparation_binds_exact_grant_once_and_leaves_activation_absent(self):
        authority = self._approve()
        result = prep.prepare(authority)
        self.sdk_prepare.assert_called_once_with(
            str(prep.PREPARE), str(prep.PREPARE_AUTH), expected_ledger=self.ledger,
            expected_proposal_sha256=self.prepare_pin["sha256"], prepare_scope=prep.PREPARE_SCOPE,
        )
        self.assertFalse(prep.h.OUT.exists())
        self.assertTrue(prep.CLAIM.exists())
        self.assertEqual(prep.verify_preparation(self.plan), result)
        with self.assertRaisesRegex(RuntimeError, "already_used"):
            prep.prepare(authority)
        self.assertEqual(self.sdk_prepare.call_count, 1)

    def test_sdk_failure_retains_claim_and_refuses_retry_without_result(self):
        authority = self._approve()
        self.sdk_prepare.side_effect = prep.env.EnvironmentRefused("prepare_failed")
        with self.assertRaisesRegex(RuntimeError, "prepare_failed"):
            prep.prepare(authority)
        self.assertTrue(prep.CLAIM.exists())
        self.assertTrue(prep.PREPARE_AUTH.exists())
        self.assertFalse(prep.RESULT.exists())
        with self.assertRaisesRegex(RuntimeError, "already_used"):
            prep.prepare(authority)
        self.assertEqual(self.sdk_prepare.call_count, 1)

    def test_prepared_replay_refuses_failed_cleanup_and_changed_row(self):
        authority = self._approve()
        prep.prepare(authority)
        client = prep.h.GUEST / "prepare-client-v1.json"
        original = prep.env.read_json(client)
        client.write_bytes(prep.env.encoded(dict(original, cleanup_complete=False)))
        with self.assertRaisesRegex(RuntimeError, "prepared"):
            prep.verify_preparation(self.plan)
        client.write_bytes(prep.env.encoded(original))
        self.entry["proposal_sha256"] = "b" * 64
        with self.assertRaisesRegex(RuntimeError, "prepared"):
            prep.verify_preparation(self.plan)

    def test_cold_cli_cannot_dispatch_preparation(self):
        with patch("builtins.print"):
            self.assertEqual(prep.main([]), 1)
            self.assertEqual(prep.main(["--authority-sha256", "a" * 64]), 1)
        self.sdk_prepare.assert_not_called()
