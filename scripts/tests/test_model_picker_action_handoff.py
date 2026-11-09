"""Synthetic SDK22 picker approval and prepared-guest binding regressions.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack, contextmanager
import copy
import hashlib
from pathlib import Path, PureWindowsPath
import unittest
from unittest.mock import Mock, patch

from benchmarks import model_picker_action_binding as artifacts
from benchmarks import model_picker_action_handoff as handoff
from benchmarks import owned_model_picker_action as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from scripts.tests.test_owned_target_contract import admission as base_admission
from scripts.tests.test_owned_target_contract import pin


REFUSED = (ValueError, RuntimeError)
NOW = 6000 * handoff.NS


class BootRecords:
    """Reseal downstream pins so adversaries reach the intended semantic check."""

    def __init__(self, change=None):
        self.change = change
        self.records = {}
        self.present = set()
        self.admission = base_admission()
        self.admission.update(protocol=contract.PROTOCOL, artifacts=artifacts.artifact_bindings())
        self.admission["guest"]["root"] = str(contract.GUEST_ROOT)
        sources_root = PureWindowsPath("D:/Synthetic/LocalLore/benchmarks")
        self.admission["sources"] = [pin(sources_root / name) for name in sorted(contract.SOURCE_NAMES)]
        self.admission.update(root=str(handoff.OWNED_ROOT), seconds=handoff.OWNER_SECONDS)
        self.admission["server"].update(root=str(handoff.OWNED_ROOT / "server"),
                                       seconds=handoff.OWNER_SECONDS)
        guest, server = self.admission["guest"], self.admission["server"]
        installed = {key: copy.deepcopy(server[key])
                     for key in ("adb", "tools", "capabilities", "source_review")}
        installed.update({key: copy.deepcopy(guest[key])
                          for key in ("emulator", "qemu", "refuser", "refuser_source")})
        installed.update(auth_key_path=server["auth_key"],
                         compatibility=copy.deepcopy(self.admission["compatibility"]))
        self.prepare = dict(phase="prepare", paths=dict(root=str(handoff.GUEST)),
                            adb_path=installed["adb"]["path"], memory_mib=8192, cores=4)
        self.prepare_pin = self.add("prepare", handoff.PREPARE, self.prepare)
        plan = dict(version=1, scope=handoff.PLAN_SCOPE, source_root=str(handoff.ROOT),
                    sources=copy.deepcopy(self.admission["sources"]),
                    python=copy.deepcopy(self.admission["python"]),
                    artifacts=copy.deepcopy(self.admission["artifacts"]),
                    prepare=self.prepare_pin, installed=installed,
                    execution_authorized=False, model_material=False)
        plan_pin = self.add("plan", handoff.PLAN, plan)
        historical_ledger = pin(handoff.LEDGER)
        proposal = (f"# Synthetic reviewed proposal\nPlan SHA-256 {plan_pin['sha256']}\n"
                    f"Ledger SHA-256 {historical_ledger['sha256']}\n").encode()
        if change and change[0] == "proposal":
            proposal = change[1](proposal)
        proposal_pin = self.add("proposal", handoff.PROPOSAL, proposal)
        authority = dict(version=1, scope=handoff.OPERATION_SCOPE, proposal=proposal_pin,
                         plan=plan_pin, ledger=historical_ledger,
                         approval_reference="synthetic-reviewed-approval",
                         allow_sdk_prepare=True, allow_one_boot=True, allow_model=False,
                         allow_retirement=False, max_operation_seconds=handoff.SECONDS)
        self.authority_pin = self.add("authority", handoff.AUTHORITY, authority)
        attempt = dict(version=1, scope=handoff.OPERATION_SCOPE, authority=self.authority_pin,
                       no_retry=True)
        attempt_pin = self.add("attempt", handoff.ATTEMPT, attempt)

        prepare_auth = dict(version=1, phase="prepare", proposal_sha256=self.prepare_pin["sha256"],
                            prepare_scope=handoff.OPERATION_SCOPE, allow_environment_calls=True,
                            root_go_pending=False)
        self.add("prepare_auth", handoff.PREPARE_AUTH, prepare_auth)
        executable = self.admission["python"]["executable"]["path"]
        self.prepare_owner = dict(pid=701, creation_filetime=800, executable=executable)
        self.prepare_worker = dict(pid=702, creation_filetime=801, executable=executable)
        self.add("prepare_start", handoff.GUEST / "prepare-start-v1.json",
                 dict(proposal_sha256=self.prepare_pin["sha256"], facts={},
                      owner=self.prepare_owner, prepare_scope=handoff.OPERATION_SCOPE))
        self.add("prepare_worker", handoff.GUEST / "prepare-worker-claimed-v1.json",
                 dict(proposal_sha256=self.prepare_pin["sha256"], worker=self.prepare_worker,
                      prepare_scope=handoff.OPERATION_SCOPE))
        prepare_result = dict(version=1, proposal_sha256=self.prepare_pin["sha256"],
                              status="completed", closure_verified=True,
                              child_cleanup_complete=True, prepared_created=True)
        prepare_result_pin = self.add("prepare_result", handoff.GUEST / "prepare-result-v1.json",
                                      prepare_result)
        prepared_pin = self.add("prepared", handoff.GUEST / "prepared-v1.json",
                                dict(proposal_sha256=self.prepare_pin["sha256"]))
        self.run_proposal = dict(self.prepare, phase="run", max_seconds=handoff.ACTIVATION_SECONDS,
                                 prepare_proposal=self.prepare_pin, prepared=prepared_pin,
                                 prepare_result=prepare_result_pin)
        run_pin = self.add("run", handoff.RUN, self.run_proposal)
        run_auth = dict(version=1, phase="run", run_scope=contract.RUN_SCOPE,
                        proposal_sha256=run_pin["sha256"], allow_environment_calls=True,
                        root_go_pending=False)
        guest.update(proposal=run_pin, authorization=self.add("run_auth", handoff.RUN_AUTHORITY,
                                                              run_auth))
        self.admission_pin = self.add("admission", handoff.ADMISSION, self.admission)
        receipt = dict(version=1, scope=handoff.HANDOFF_SCOPE, authority=self.authority_pin,
                       attempt=attempt_pin, admission=self.admission_pin,
                       supervisor=dict(pid=710, creation_filetime=810, executable=executable),
                       began_ns=NOW - 10 * handoff.NS, until_ns=NOW + 1600 * handoff.NS)
        self.add("handoff", handoff.HANDOFF, receipt)

        self.entry = dict(root=str(handoff.GUEST), proposal_sha256=self.prepare_pin["sha256"],
                          state="prepared", reserved_bytes=storage.RESERVATION_BYTES,
                          closure=None, retirement=None, retirement_receipt=None, recovery=None)
        self.mutate("entry", self.entry)
        ledger = dict(version=2, max_guests=storage.MAX_GUESTS, budget_bytes=storage.BUDGET_BYTES,
                      reservation_bytes=storage.RESERVATION_BYTES, entries=[self.entry])
        self.ledger_pin = self.add("ledger", handoff.LEDGER, ledger)
        self.verify_prepared = Mock(return_value=dict(proposal_sha256=self.prepare_pin["sha256"]))
        self.verify_artifacts = Mock()
        self.validate_ledger = Mock()

    def mutate(self, role, value):
        if self.change and role == self.change[0] and role != "proposal":
            self.change[1](value)

    def add(self, role, path, value):
        self.mutate(role, value)
        raw = value if type(value) is bytes else env.encoded(value)
        binding = pin(Path(path), size=len(raw), sha=hashlib.sha256(raw).hexdigest())
        self.records[Path(path)] = binding, copy.deepcopy(value)
        return copy.deepcopy(binding)

    def read(self, path):
        if Path(path) not in self.records:
            raise env.EnvironmentRefused("binding")
        return copy.deepcopy(self.records[Path(path)])

    def bound(self, expected, *, cap):
        binding, value = self.read(expected["path"])
        if not contract._same(expected, binding) or binding["bytes"] > cap:
            raise env.EnvironmentRefused("binding")
        return value if type(value) is bytes else env.encoded(value)

    def raw(self, path, cap):
        return self.bound(self.read(path)[0], cap=cap)

    def check_binding(self, binding):
        self.bound(binding, cap=16 * 1024**2)

    @contextmanager
    def ports(self):
        with ExitStack() as stack:
            for module, name, replacement in (
                (handoff.files, "_read", self.raw),
                (handoff.files, "_bound", self.bound),
                (env, "check_binding", self.check_binding),
                (env, "validate_proposal", Mock()),
                (env, "verify_prepared", self.verify_prepared),
                (contract, "revalidate_inputs", Mock()),
                (artifacts, "verify_artifacts", self.verify_artifacts),
                (storage, "_validate", self.validate_ledger),
                (storage, "safe_path", Path),
                (handoff.os.path, "lexists", lambda path: Path(path) in self.present),
                (handoff.time, "monotonic_ns", lambda: NOW),
            ):
                stack.enter_context(patch.object(module, name, replacement))
            yield

    def check(self):
        with self.ports():
            return handoff.verify_boot_handoff(self.admission_pin, self.admission)


class PickerActionHandoffTests(unittest.TestCase):
    def test_exact_handoff_replays_both_scoped_receipts_and_the_current_ledger(self):
        graph = BootRecords()
        self.assertEqual(graph.check(), graph.read(handoff.HANDOFF))
        graph.verify_prepared.assert_called_once_with(graph.run_proposal, initial=True)
        graph.verify_artifacts.assert_called_once_with(graph.admission["artifacts"])
        graph.validate_ledger.assert_called_once_with(graph.read(handoff.LEDGER)[1],
                                                      storage.DEFAULT_REGISTRY)

    def test_authority_missing_or_wrongly_pinned_refuses_before_prepared_io(self):
        for missing in (handoff.AUTHORITY, handoff.PROPOSAL, handoff.PLAN, handoff.ATTEMPT):
            graph = BootRecords()
            del graph.records[missing]
            with self.subTest(missing=missing), self.assertRaises(REFUSED):
                graph.check()
            graph.verify_prepared.assert_not_called()

        graph = BootRecords()
        foreign = dict(graph.authority_pin, path=str(handoff.OUT / "foreign-authority.json"))
        with graph.ports(), self.assertRaises(REFUSED):
            handoff.read_authority(foreign)

    def test_preparation_evidence_cannot_be_absent(self):
        for missing in (handoff.PREPARE_AUTH, handoff.GUEST / "prepare-start-v1.json",
                        handoff.GUEST / "prepare-worker-claimed-v1.json",
                        handoff.GUEST / "prepare-result-v1.json"):
            graph = BootRecords()
            del graph.records[missing]
            with self.subTest(missing=missing), self.assertRaises(REFUSED):
                graph.check()

    def test_pinned_admission_cannot_be_replaced_by_an_in_memory_copy(self):
        graph = BootRecords()
        changed = copy.deepcopy(graph.admission)
        changed["run_id"] = changed["server"]["run_id"] = "f" * 32
        with graph.ports(), self.assertRaises(REFUSED):
            handoff.verify_boot_handoff(graph.admission_pin, changed)

    def test_authority_rejects_duplicate_or_disagreeing_reviewed_proposal_digests(self):
        for mutate in (
            lambda raw: raw + next(line for line in raw.splitlines(keepends=True)
                                   if line.startswith(b"Plan SHA-256")),
            lambda raw: raw.replace(b"Ledger SHA-256 ", b"Ledger SHA-256 0"),
            lambda raw: raw.replace(b"Plan SHA-256", b"Other SHA-256"),
        ):
            with self.subTest(mutate=mutate), self.assertRaises(REFUSED):
                BootRecords(("proposal", mutate)).check()

    def test_malformed_plan_pin_is_refused_before_reviewed_proposal_read(self):
        graph = BootRecords(("authority", lambda row: row["plan"].pop("sha256")))
        with (graph.ports(),
              patch.object(handoff.files, "_bound", wraps=graph.bound) as bound,
              self.assertRaisesRegex(contract.TargetRefused, "^binding$")):
            handoff.read_authority(graph.authority_pin)
        self.assertEqual([call.args[0]["path"] for call in bound.call_args_list],
                         [str(handoff.AUTHORITY)])

    def test_handoff_refuses_resealed_semantic_drift(self):
        for role, mutation in (
            ("authority", lambda row: row.update(scope="sdk21-prepare-and-one-combined-record-run-v1")),
            ("authority", lambda row: row.update(allow_one_boot=1)),
            ("authority", lambda row: row.update(allow_model=True)),
            ("authority", lambda row: row.update(approval_reference="synthetic\nsecond-line")),
            ("attempt", lambda row: row.update(no_retry=False)),
            ("plan", lambda row: row.update(model_material=True)),
            ("plan", lambda row: row.update(source_root=r"D:\Synthetic\foreign")),
            ("plan", lambda row: row.update(execution_authorized=True)),
            ("plan", lambda row: row["artifacts"]["test_apk"].update(sha256="0" * 64)),
            ("plan", lambda row: row["installed"]["adb"].update(sha256="0" * 64)),
            ("prepare_auth", lambda row: row.update(prepare_scope="other-scope")),
            ("prepare_auth", lambda row: row.pop("prepare_scope")),
            ("prepare_start", lambda row: row.update(prepare_scope="other-scope")),
            ("prepare_start", lambda row: row["owner"].update(executable=r"D:\Synthetic\other.exe")),
            ("prepare_worker", lambda row: row["worker"].update(pid=701)),
            ("prepare_worker", lambda row: row["worker"].update(creation_filetime=799)),
            ("prepare_result", lambda row: row.update(closure_verified=1)),
            ("run", lambda row: row.update(max_seconds=1799)),
            ("run_auth", lambda row: row.update(run_scope="owned-emulator-combined-record-ui-v1")),
            ("run_auth", lambda row: row.pop("run_scope")),
            ("handoff", lambda row: row.update(version=True)),
            ("handoff", lambda row: row.update(scope="combined-record-boot-handoff-v1")),
            ("handoff", lambda row: row["admission"].update(sha256="0" * 64)),
            ("handoff", lambda row: row["attempt"].update(sha256="0" * 64)),
            ("handoff", lambda row: row["supervisor"].update(executable=r"D:\Synthetic\other.exe")),
        ):
            with self.subTest(role=role, mutation=mutation), self.assertRaises(REFUSED):
                BootRecords((role, mutation)).check()

    def test_prepared_ledger_must_be_v2_and_reserved_for_the_exact_preparation(self):
        for role, mutation in (
            ("ledger", lambda row: row.update(version=1)),
            ("ledger", lambda row: row.update(version=True)),
            ("entry", lambda row: row.update(root=r"D:\Synthetic\different-guest")),
            ("entry", lambda row: row.update(state="closed")),
            ("entry", lambda row: row.update(proposal_sha256="0" * 64)),
            ("entry", lambda row: row.update(reserved_bytes=0)),
            ("entry", lambda row: row.update(closure=pin(r"D:\Synthetic\closure.json"))),
            ("entry", lambda row: row.update(recovery={})),
            ("entry", lambda row: row.update(retirement={})),
            ("entry", lambda row: row.update(retirement_receipt={})),
        ):
            with self.subTest(role=role, mutation=mutation), self.assertRaises(REFUSED):
                BootRecords((role, mutation)).check()

    def test_existing_boot_claim_refuses_reuse(self):
        graph = BootRecords()
        graph.present.add(handoff.GUEST / contract.BOOT_CLAIM_FILE)
        with self.assertRaises(REFUSED):
            graph.check()

    def test_handoff_drift_during_prepared_verification_refuses(self):
        graph = BootRecords()
        _, record = graph.read(handoff.HANDOFF)
        graph.verify_prepared.side_effect = lambda *_args, **_kwargs: graph.add(
            "handoff", handoff.HANDOFF, dict(record, scope="replaced"))
        with self.assertRaises(REFUSED):
            graph.check()

    def test_prepared_manifest_drift_during_verification_refuses(self):
        graph = BootRecords()
        path = handoff.GUEST / "prepared-v1.json"
        _, record = graph.read(path)
        graph.verify_prepared.side_effect = lambda *_args, **_kwargs: graph.add(
            "prepared", path, dict(record, proposal_sha256="0" * 64))
        with self.assertRaises(REFUSED):
            graph.check()

    def test_deadlines_reject_expired_or_overlong_operation_and_launch_window(self):
        with patch.object(handoff.time, "monotonic_ns", return_value=NOW):
            self.assertEqual(handoff.check_window(NOW - handoff.NS, NOW + handoff.NS), NOW)
            for began, until in (
                (True, NOW + handoff.NS),
                (NOW + handoff.NS, NOW + 2 * handoff.NS),
                (NOW - handoff.NS, NOW),
                (NOW - handoff.SECONDS * handoff.NS, NOW + handoff.NS),
                (NOW - handoff.NS, NOW + (handoff.ACTIVATION_SECONDS + 1) * handoff.NS),
            ):
                with self.subTest(began=began, until=until), self.assertRaises(REFUSED):
                    handoff.check_window(began, until)
            just_enough = NOW + (1200 + handoff.TAIL_SECONDS) * handoff.NS
            with self.assertRaises(REFUSED):
                handoff.check_launch_window(NOW - handoff.NS, just_enough)
            self.assertEqual(handoff.check_launch_window(NOW - handoff.NS, just_enough + 1), NOW)


    def test_fixed_scope_and_paths_are_distinct_from_the_pending_record_run(self):
        self.assertEqual(
            handoff.OUT,
            Path("D:/Dev/Experiments/LocalLore/2026-11-09-model-picker-owned-operation-v1"),
        )
        self.assertEqual(handoff.GUEST, Path(contract.GUEST_ROOT))
        self.assertEqual(contract.RUN_SCOPE, contract.PROTOCOL)
        self.assertNotEqual(handoff.OPERATION_SCOPE, "sdk21-prepare-and-one-combined-record-run-v1")
        self.assertNotEqual(handoff.HANDOFF_SCOPE, "combined-record-boot-handoff-v1")
        self.assertNotEqual(handoff.HANDOFF_ENV, "LOCALLORE_COMBINED_RECORD_HANDOFF_SHA256")

    def test_ledger_drift_during_final_pin_readback_refuses(self):
        graph = BootRecords()
        _, ledger = graph.read(handoff.LEDGER)
        check_binding = graph.check_binding

        def check_with_drift(binding):
            if binding == graph.admission_pin:
                graph.add("ledger", handoff.LEDGER, dict(ledger, version=1))
            check_binding(binding)

        graph.check_binding = check_with_drift
        with self.assertRaises(REFUSED):
            graph.check()
