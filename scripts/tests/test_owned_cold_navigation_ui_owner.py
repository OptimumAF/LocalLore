"""Synthetic SDK20 owner gates with inert record, SDK and native ports."""

from contextlib import ExitStack, contextmanager, redirect_stdout
import copy
import hashlib
from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_cold_navigation_ui_owner as owner
from scripts.tests.test_owned_cold_navigation_ui_contract import admission as cold_admission
from scripts.tests.test_owned_target_contract import pin


REFUSED = (ValueError, RuntimeError)


class BootRecords:
    """Seal a coherent synthetic graph, including any semantic adversary."""

    def __init__(self, change=None):
        self.change = change
        self.records = {}
        self.present = set()
        self.guest = Path(owner.contract.GUEST_ROOT)

        self.admission = cold_admission()
        self.admission.update(root=str(owner.OWNED_ROOT), seconds=owner.OWNER_SECONDS)
        self.admission["server"].update(root=str(owner.OWNED_ROOT / "server"), seconds=owner.OWNER_SECONDS)
        server = self.admission["server"]
        guest = self.admission["guest"]
        installed = {role: copy.deepcopy(guest[role])
                     for role in ("emulator", "qemu", "refuser", "refuser_source")}
        installed.update({role: copy.deepcopy(server[role])
                          for role in ("adb", "tools", "capabilities", "source_review")})
        installed.update(auth_key_path=server["auth_key"],
                         compatibility=copy.deepcopy(self.admission["compatibility"]))
        self.prepare = dict(phase="prepare", paths=dict(root=str(self.guest)),
                            memory_mib=8192, cores=4, adb_path=installed["adb"]["path"])
        prepare_pin = self.add("prepare", owner.PREPARE, self.prepare)
        plan = dict(version=1, scope=owner.PLAN_SCOPE, source_root=str(owner.ROOT),
                    sources=copy.deepcopy(self.admission["sources"]),
                    python=copy.deepcopy(self.admission["python"]),
                    artifacts=copy.deepcopy(self.admission["artifacts"]),
                    prepare=prepare_pin, installed=installed,
                    execution_authorized=False, model_material=False)
        plan_pin = self.add("plan", owner.PLAN, plan)
        self.baseline = pin(owner.LEDGER)
        proposal = (f"# Reviewed proposal\nPlan SHA-256 {plan_pin['sha256']}\n"
                    f"Ledger SHA-256 {self.baseline['sha256']}\n").encode()
        proposal_pin = self.add("proposal", owner.PROPOSAL, proposal)
        authority = dict(version=1, scope=owner.OPERATION_SCOPE, proposal=proposal_pin,
                         plan=plan_pin, ledger=self.baseline,
                         approval_reference="synthetic-only-reviewed-approval",
                         allow_sdk_prepare=True, allow_one_boot=True, allow_model=False,
                         allow_retirement=False, max_operation_seconds=owner.SECONDS)
        authority_pin = self.add("authority", owner.AUTHORITY, authority)
        attempt = dict(version=1, scope=owner.OPERATION_SCOPE, authority=authority_pin, no_retry=True)
        attempt_pin = self.add("attempt", owner.ATTEMPT, attempt)

        prepared_result = dict(version=1, proposal_sha256=prepare_pin["sha256"],
                               status="completed", closure_verified=True,
                               child_cleanup_complete=True, prepared_created=True)
        prepared_result_pin = self.add("prepared_result", self.guest / "prepare-result-v1.json",
                                       prepared_result)
        prepared_pin = self.add("prepared", self.guest / "prepared-v1.json",
                                dict(proposal_sha256=prepare_pin["sha256"]))
        self.run_proposal = dict(self.prepare, phase="run", max_seconds=1800,
                                 prepare_proposal=prepare_pin, prepared=prepared_pin,
                                 prepare_result=prepared_result_pin)
        run_pin = self.add("run", owner.RUN, self.run_proposal)
        run_authority = dict(version=1, phase="run", run_scope=owner.contract.PROTOCOL,
                             proposal_sha256=run_pin["sha256"],
                             allow_environment_calls=True, root_go_pending=False)
        guest.update(proposal=run_pin, authorization=self.add("run_authority", owner.RUN_AUTHORITY,
                                                              run_authority))
        self.admission_pin = self.add("admission", owner.ADMISSION, self.admission)
        handoff = dict(version=1, scope=owner.HANDOFF_SCOPE, authority=authority_pin,
                       attempt=attempt_pin, admission=self.admission_pin)
        self.add("handoff", owner.HANDOFF, handoff)

        self.entry = dict(root=str(self.guest), proposal_sha256=prepare_pin["sha256"], state="prepared",
                          reserved_bytes=40 * 1024**3, closure=None, retirement=None,
                          retirement_receipt=None, recovery=None)
        self.mutate("entry", self.entry)
        ledger = dict(version=2, max_guests=2, budget_bytes=64 * 1024**3,
                      reservation_bytes=40 * 1024**3, entries=[self.entry])
        self.ledger_pin = self.add("ledger", owner.LEDGER, ledger)
        self.verify_prepared = Mock(return_value=dict(proposal_sha256=prepare_pin["sha256"]))
        self.revalidate = Mock()
        self.verify_artifacts = Mock()
        self.validate_proposal = Mock()
        self.check_binding = Mock(side_effect=self.check_pin)
        self.check_ledger = Mock(side_effect=self.current_ledger)

    def mutate(self, role, value):
        if self.change is not None and self.change[0] == role:
            self.change[1](value)

    def add(self, role, path, value):
        self.mutate(role, value)
        payload = value if type(value) is bytes else owner.env.encoded(value)
        binding = pin(Path(path), size=len(payload), sha=hashlib.sha256(payload).hexdigest())
        self.records[Path(path)] = binding, copy.deepcopy(value)
        return copy.deepcopy(binding)

    def read(self, path, *_args, **_kwargs):
        if Path(path) not in self.records:
            raise owner.env.EnvironmentRefused("binding")
        return copy.deepcopy(self.records[Path(path)])

    def bound(self, expected, *, cap):
        binding, value = self.read(expected["path"])
        if expected != binding or binding["bytes"] > cap:
            raise owner.env.EnvironmentRefused("binding")
        return value if type(value) is bytes else owner.env.encoded(value)

    def raw(self, path, cap):
        binding, _ = self.read(path)
        return self.bound(binding, cap=cap)

    def check_pin(self, expected):
        self.bound(expected, cap=16 * 1024**2)

    def current_ledger(self, root):
        if Path(root) != self.guest:
            raise owner.env.EnvironmentRefused("ledger")
        return copy.deepcopy((self.ledger_pin, self.entry))

    @contextmanager
    def ports(self):
        with ExitStack() as stack:
            for module, name, substitute in (
                (owner.files, "_read", self.raw),
                (owner, "_ledger", self.check_ledger),
                (owner.files, "_bound", self.bound),
                (owner.env, "check_binding", self.check_binding),
                (owner.env, "validate_proposal", self.validate_proposal),
                (owner.env, "verify_prepared", self.verify_prepared),
                (owner.contract, "revalidate_inputs", self.revalidate),
                (owner.contract, "verify_artifacts", self.verify_artifacts),
                (owner.os.path, "lexists", lambda path: Path(path) in self.present),
            ):
                stack.enter_context(patch.object(module, name, substitute))
            yield

    def check(self):
        with self.ports():
            return owner._check_boot_handoff(self.admission_pin, self.admission)


class ColdNavigationOwnerTests(unittest.TestCase):
    def test_fresh_reviewed_graph_allows_only_the_guarded_handoff(self):
        graph = BootRecords()
        self.assertIsNone(graph.check())
        graph.verify_prepared.assert_called_once_with(graph.run_proposal, initial=True)
        graph.check_ledger.assert_called_once_with(graph.guest)
        graph.verify_artifacts.assert_called_once_with(graph.admission["artifacts"])

    def test_missing_authority_refuses_before_current_ledger_access(self):
        graph = BootRecords()
        graph.records.pop(owner.AUTHORITY)
        with self.assertRaises(REFUSED):
            graph.check()
        graph.check_ledger.assert_not_called()

    def test_coherently_rebound_but_invalid_authority_plan_or_proof_refuses(self):
        for role, mutation in (
            ("handoff", lambda row: row.update(scope="other-operation")),
            ("handoff", lambda row: row["admission"].update(sha256="0" * 64)),
            ("authority", lambda row: row.update(allow_one_boot=False)),
            ("authority", lambda row: row.update(allow_model=True)),
            ("authority", lambda row: row.update(ledger=pin(owner.LEDGER, sha="0" * 64))),
            ("attempt", lambda row: row.update(no_retry=False)),
            ("plan", lambda row: row.update(scope="other-plan")),
            ("plan", lambda row: row.update(execution_authorized=True)),
            ("plan", lambda row: row["installed"]["adb"].update(sha256="0" * 64)),
            ("plan", lambda row: row["sources"][0].update(sha256="0" * 64)),
            ("plan", lambda row: row["artifacts"]["test_apk"].update(sha256="0" * 64)),
            ("run", lambda row: row.update(max_seconds=1799)),
            ("run_authority", lambda row: row.update(proposal_sha256="0" * 64)),
            ("run_authority", lambda row: row.pop("run_scope")),
            ("run_authority", lambda row: row.update(run_scope="other-profile")),
            ("prepared_result", lambda row: row.update(closure_verified=1)),
        ):
            with self.subTest(role=role, mutation=mutation), self.assertRaises(REFUSED):
                BootRecords((role, mutation)).check()

    def test_scoped_run_authority_refuses_under_the_legacy_guard(self):
        graph = BootRecords()
        _, scoped = graph.read(owner.RUN_AUTHORITY)
        run_digest = graph.admission["guest"]["proposal"]["sha256"]
        with self.assertRaises(REFUSED):
            owner.env.check_authorization(scoped, "run", run_digest)
        legacy = {key: value for key, value in scoped.items() if key != "run_scope"}
        owner.env.check_authorization(legacy, "run", run_digest)

    def test_changed_handoff_is_refused_after_prepared_verification(self):
        graph = BootRecords()
        original_pin, handoff = graph.read(owner.HANDOFF)

        def change_handoff(*_args, **_kwargs):
            graph.add("handoff", owner.HANDOFF, dict(handoff, scope="replaced"))

        graph.verify_prepared.side_effect = change_handoff
        with self.assertRaises(REFUSED):
            graph.check()
        graph.check_binding.assert_any_call(original_pin)

    def test_spent_or_mismatched_ledger_reservation_refuses(self):
        for field, value in (
            ("state", "closed"), ("reserved_bytes", 0), ("proposal_sha256", "0" * 64),
            ("closure", pin("D:/Synthetic/closure.json")), ("recovery", {}),
            ("retirement", {}),
        ):
            with self.subTest(field=field), self.assertRaises(REFUSED):
                BootRecords(("entry", lambda row: row.update({field: value}))).check()

    def test_existing_boot_claim_is_spent(self):
        graph = BootRecords()
        graph.present.add(graph.guest / owner.contract.BOOT_CLAIM_FILE)
        with self.assertRaises(REFUSED):
            graph.check()

    def test_live_ledger_reader_requires_version_two_and_the_exact_guest(self):
        for version, root in ((2, owner.GUEST), (1, owner.GUEST), (True, owner.GUEST),
                              (2, Path("D:/Synthetic/foreign-guest"))):
            graph = BootRecords()
            ledger = graph.read(owner.LEDGER)[1]
            ledger.update(version=version)
            ledger["entries"][0]["root"] = str(root)
            ledger_pin = graph.add("ledger", owner.LEDGER, ledger)
            with self.subTest(version=version, root=root), \
                 patch.object(owner, "_read", side_effect=graph.read), \
                 patch.object(owner.env, "check_binding", side_effect=graph.check_pin), \
                 patch.object(owner.storage, "_validate"), \
                 patch.object(owner.storage, "safe_path", side_effect=Path):
                if version == 2 and root == owner.GUEST:
                    self.assertEqual(owner._ledger(owner.GUEST), (ledger_pin, graph.entry))
                else:
                    with self.assertRaises(REFUSED):
                        owner._ledger(owner.GUEST)

    def test_parent_refuses_failed_handoff_and_existing_owner_before_native_dispatch(self):
        for existing in (False, True):
            graph = BootRecords()
            if existing:
                graph.present.add(owner.OWNED_ROOT)
            args = ["--admission", str(owner.ADMISSION), "--admission-sha256", graph.admission_pin["sha256"]]
            output = StringIO()
            with self.subTest(existing=existing), graph.ports(), redirect_stdout(output), \
                 patch.object(owner, "_check_boot_handoff",
                              side_effect=owner.env.EnvironmentRefused("authority")) as gate, \
                 patch.object(owner.mechanisms.file_guard, "_existing_D_file", return_value=owner.ADMISSION), \
                 patch.object(owner.mechanisms.file_guard, "_read_bound",
                              return_value=(graph.admission_pin, graph.admission)), \
                 patch.object(owner.mechanisms, "_parent", side_effect=AssertionError("no native dispatch")) as launch:
                self.assertEqual(owner.main(args), 1)
            if existing:
                gate.assert_not_called()
            else:
                gate.assert_called_once_with(graph.admission_pin, graph.admission)
            launch.assert_not_called()
            self.assertFalse(json.loads(output.getvalue())["qualified_target"])

    def test_parent_only_accepts_the_fixed_admission_path_and_worker_command(self):
        args = ["--admission", "D:/Synthetic/admission-v1.json", "--admission-sha256", "0" * 64]
        with patch.object(owner.mechanisms, "_main_profile", return_value=27) as profile:
            self.assertEqual(owner.main(args), 1)
            self.assertEqual(owner.main(["_worker", "extra"]), 1)
            profile.assert_not_called()
            self.assertEqual(owner.main(["_worker"]), 27)
            self.assertEqual(profile.call_args.args, (["_worker"],))
            self.assertIs(profile.call_args.kwargs["_runtime_type"], owner._ColdNavigationTargetRuntime)

    def test_worker_refusal_precedes_native_runtime_construction(self):
        graph = BootRecords()
        request = {"admission": graph.admission_pin, "validated_admission": graph.admission}
        with patch.object(owner, "_check_boot_handoff",
                          side_effect=owner.env.EnvironmentRefused("already_used")) as gate, \
             patch.object(owner.mechanisms._TargetRuntimeCore, "__init__",
                          side_effect=AssertionError("no native runtime")) as runtime, self.assertRaises(REFUSED):
            owner._ColdNavigationTargetRuntime(request, pin("D:/Synthetic/request.json"),
                                               Path(graph.admission["root"]))
        gate.assert_called_once_with(graph.admission_pin, graph.admission)
        runtime.assert_not_called()

    def test_runtime_retention_compares_the_prepared_digest_at_transition(self):
        graph = BootRecords()
        runtime = object.__new__(owner._ColdNavigationTargetRuntime)
        runtime.admission = graph.admission
        runtime.proposal = graph.run_proposal
        with patch.object(owner.env, "storage_transition") as transition:
            runtime._retain_guest()
        transition.assert_called_once_with(
            owner.storage.record_state, graph.guest, "retained",
            proposal_sha256=graph.admission["guest"]["proposal"]["sha256"],
            expected_prepare_sha256=graph.run_proposal["prepare_proposal"]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()
