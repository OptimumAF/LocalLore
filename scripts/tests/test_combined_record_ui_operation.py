"""Exercise the SDK21 combined Story Record operation with synthetic ownership and receipts.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack, contextmanager
import copy
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import combined_record_ui_operation as operation
from benchmarks import combined_record_ui_handoff as handoff
from scripts.tests.test_combined_record_ui_handoff import BootRecords


NS = handoff.NS
REFUSED = (ValueError, RuntimeError)


class SyntheticOperation(BootRecords):
    """Real approval and result bindings with inert preparation and job ports."""

    def __init__(self, *, claimed=True):
        super().__init__()
        self.began_ns = 100 * NS
        self.now_ns = 110 * NS
        self.worker = dict(pid=3201, creation_filetime=750,
                           executable=self.admission["python"]["executable"]["path"])
        self.parent = dict(self.worker, pid=3200, creation_filetime=700)
        self.directories = {handoff.ATTEMPT_ROOT} if claimed else set()
        self.mkdir = Mock(side_effect=self.create_directory)
        self.plan_pin, self.plan = self.read(handoff.PLAN)
        ledger = dict(version=2, max_guests=2, budget_bytes=64 * 1024**3,
                      reservation_bytes=40 * 1024**3, entries=[])
        baseline = self.add("baseline", handoff.LEDGER, ledger)
        markdown = (f"# Reviewed operation\nPlan SHA-256 {self.plan_pin['sha256']}\n"
                    f"Ledger SHA-256 {baseline['sha256']}\n").encode()
        proposal = self.add("proposal", handoff.PROPOSAL, markdown)
        _, self.authority = self.read(handoff.AUTHORITY)
        self.authority.update(proposal=proposal, ledger=baseline)
        self.authority_pin = self.add("authority", handoff.AUTHORITY, self.authority)
        self.records.pop(handoff.ATTEMPT)
        attempt = dict(version=1, scope=handoff.OPERATION_SCOPE, authority=self.authority_pin,
                       no_retry=True)
        self.attempt_pin = self.publish(handoff.ATTEMPT, attempt) if claimed else None
        self.records.pop(handoff.HANDOFF)
        self.records.pop(handoff.ADMISSION)
        self.records.pop(handoff.PREPARE_AUTH)
        self.prepared_path = handoff.GUEST / "prepared-v1.json"
        self.prepare_result_path = handoff.GUEST / "prepare-result-v1.json"
        self.prepare_evidence_paths = {
            role: handoff.GUEST / name
            for role, name in (("start", "prepare-start-v1.json"),
                               ("worker", "prepare-worker-claimed-v1.json"),
                               ("client", "prepare-client-v1.json"),
                               ("stdout", "prepare-stdout-v1.bin"))
        }
        self.records.pop(self.prepare_evidence_paths["start"])
        self.records.pop(self.prepare_evidence_paths["worker"])
        _, self.prepared = self.records.pop(self.prepared_path)
        _, self.prepare_result = self.records.pop(self.prepare_result_path)
        self.preflight_result = dict(resources={"synthetic": "host capacity"},
                                     storage=dict(ledger=baseline, would_fit=True, admission_granted=False),
                                     ports_free=True)
        self.preflight = Mock(return_value=self.preflight_result)
        self.prepare_once = Mock(side_effect=self.complete_prepare)
        self.admit = Mock(side_effect=self.complete_admission)
        self.activate = Mock(side_effect=self.complete_activation)
        self.verify_activation = Mock(side_effect=self.replay_activation)
        self.supervise_operation = Mock(side_effect=AssertionError("must not dispatch a real watchdog"))
        self.closure = None

    def create_directory(self, path, *args, **kwargs):
        if path in self.directories:
            raise FileExistsError(str(path))
        self.directories.add(path)

    def exists(self, path):
        return Path(path) in self.directories or Path(path) in self.records or Path(path) in self.present

    def publish(self, path, value):
        if self.exists(path):
            raise FileExistsError(str(path))
        return self.add("publication", path, value)

    def complete_prepare(self, *args, **kwargs):
        paths = self.prepare_evidence_paths
        common = dict(proposal_sha256=self.plan["prepare"]["sha256"], prepare_scope=handoff.OPERATION_SCOPE)
        self.publish(paths["start"], dict(common, facts={}, owner=self.worker))
        sdk_worker = dict(self.worker, pid=self.worker["pid"] + 1,
                          creation_filetime=self.worker["creation_filetime"] + 1)
        self.publish(paths["worker"], dict(common, worker=sdk_worker))
        capture = self.publish(paths["stdout"], b"synthetic prepare output")
        self.publish(paths["client"], dict(status="completed", returncode=0, cleanup_complete=True,
                                           elapsed_ms=1, stdout_sha256=capture["sha256"], stderr_bytes=0))
        self.publish(self.prepared_path, self.prepared)
        self.publish(self.prepare_result_path, self.prepare_result)
        return copy.deepcopy(self.prepared)

    def complete_admission(self, plan):
        return self.publish(handoff.ADMISSION, self.admission)

    def complete_activation(self, admission, authority, attempt, *, began_ns):
        self.closure = dict(
            owner=self.publish(handoff.OWNED_ROOT / "result-v1.json", {"synthetic": "owner closed"}),
            closure=self.publish(handoff.GUEST / "guest-storage-closure-v1.json", {"synthetic": "guest closed"}),
            ledger=self.add("closure_ledger", handoff.LEDGER, {"synthetic": "new closed ledger"}),
        )
        value = dict(version=1, scope=operation.activation.SCOPE, admission=admission, authority=authority,
                     attempt=attempt, supervisor=None, runtime=None, passed=True, reason=None,
                     feature_acceptance=False)
        self.publish(operation.activation.CONTROL / "activation-result-v1.json", value)
        return value

    def replay_activation(self, binding, admission, authority, attempt, *, began_ns, expected_parent):
        path = operation.activation.CONTROL / "activation-result-v1.json"
        actual_pin, value = self.read(path)
        handoff.env.require(actual_pin == binding and value["admission"] == admission
                          and value["authority"] == authority and value["attempt"] == attempt
                          and value["passed"] is True and began_ns == self.began_ns
                          and expected_parent == self.worker, "activation")
        return copy.deepcopy(self.closure)

    def enter_records(self):
        request = dict(version=1, scope=handoff.OPERATION_SCOPE, authority=self.authority_pin,
                       attempt=self.attempt_pin, parent=self.parent, began_ns=self.began_ns)
        request_pin = self.publish(operation.REQUEST, request)
        self.publish(operation.STARTED, dict(request=request_pin, worker=self.worker))
        return request_pin, request

    def rename(self, source, target):
        if self.exists(target):
            raise FileExistsError(str(target))
        _, value = self.records.pop(source)
        self.publish(target, value)
        return target

    def run_watchdog(self, command, request, capture, seconds, started):
        handoff.env.require(started(SimpleNamespace(pid=self.worker["pid"])) is True, "identity")
        with patch.object(operation.sys, "stdin", SimpleNamespace(buffer=BytesIO(request))), \
             patch.object(operation.os, "getpid", return_value=self.worker["pid"]), \
             patch.object(operation.os, "getppid", return_value=self.parent["pid"]), \
             patch.object(operation.mechanisms, "_ProcessApi", return_value=SimpleNamespace(
                 current_job_pids=lambda: [self.worker["pid"]])):
            code = operation.main(["_worker"])
        return dict(status="child_exited", cleanup_complete=self.watchdog_cleanup,
                    output_capture_complete=self.watchdog_capture,
                    worker_returncode=code if self.watchdog_returncode is None else self.watchdog_returncode,
                    elapsed_ms=8, stdout_bytes=0, stderr_bytes=0)

    def capture_stream(self, path, mode):
        if path.parent != operation.CAPTURE or path.name not in handoff.env.LiveOutput.names or mode != "rb":
            raise AssertionError("unexpected synthetic capture read")
        return BytesIO()

    def read_operation(self, path, cap=handoff.RECORD_CAP):
        binding, value = self.read(path)
        handoff.env.require(binding["bytes"] <= cap, "binding")
        return binding, value

    def execute(self, *, cleanup=True, capture=True, returncode=None):
        self.watchdog_cleanup = cleanup
        self.watchdog_capture = capture
        self.watchdog_returncode = returncode
        self.supervise_operation.side_effect = self.run_watchdog
        with self.ports(), patch.object(operation, "_identity", side_effect=lambda pid, expected=None:
                self.worker if pid == self.worker["pid"] else self.parent), \
             patch.object(operation.sys, "executable", self.parent["executable"]), \
             patch.object(Path, "rename", lambda source, target: self.rename(source, target)), \
             patch.object(Path, "open", lambda path, mode: self.capture_stream(path, mode)):
            return operation.execute(self.authority_pin, began_ns=self.began_ns)

    @contextmanager
    def ports(self):
        with super().ports(), ExitStack() as stack:
            for module, name, substitute in (
                (operation, "_read", self.read_operation),
                (operation, "_save", self.publish),
                (operation.preparation, "preflight", self.preflight),
                (operation.env, "prepare", self.prepare_once),
                (operation.preparation, "create_admission", self.admit),
                (operation.activation, "execute", self.activate),
                (operation.activation, "verify_result", self.verify_activation),
                (operation.env, "supervise_operation", self.supervise_operation),
                (operation.env, "safe_path", lambda path, **kwargs: Path(path)),
                (operation.time, "monotonic_ns", lambda: self.now_ns),
                (operation.os.path, "lexists", self.exists),
                (Path, "exists", lambda path: self.exists(path)),
                (Path, "mkdir", lambda path, *args, **kwargs: self.mkdir(path, *args, **kwargs)),
            ):
                stack.enter_context(patch.object(module, name, substitute))
            stack.enter_context(patch.object(Path, "cwd", return_value=handoff.ROOT))
            stack.enter_context(patch.dict(operation.os.environ, {
                "TEMP": "D:/Dev/_Temp", "TMP": "D:/Dev/_Temp", "TMPDIR": "D:/Dev/_Temp",
            }))
            yield

    def stages(self):
        with self.ports():
            return operation._run_stages(self.authority_pin, self.attempt_pin, self.began_ns, self.worker)


class CombinedRecordUiOperationTests(unittest.TestCase):
    def test_missing_human_authority_refuses_before_allocating_attempt(self):
        graph = SyntheticOperation(claimed=False)
        graph.records.pop(handoff.AUTHORITY)
        with graph.ports(), self.assertRaises(REFUSED):
            operation.execute(graph.authority_pin, began_ns=graph.began_ns)

        graph.mkdir.assert_not_called()
        graph.supervise_operation.assert_not_called()
        self.assertNotIn(handoff.ATTEMPT, graph.records)

    def test_existing_attempt_blocks_reuse_even_without_a_terminal_result(self):
        graph = SyntheticOperation()
        existing = graph.read(handoff.ATTEMPT)
        with graph.ports(), self.assertRaises((OSError, *REFUSED)):
            operation.execute(graph.authority_pin, began_ns=graph.began_ns)

        graph.supervise_operation.assert_not_called()
        self.assertEqual(graph.read(handoff.ATTEMPT), existing)

    def test_old_operation_window_refuses_before_claim_or_watchdog(self):
        graph = SyntheticOperation(claimed=False)
        graph.now_ns = graph.began_ns + handoff.SECONDS * NS
        with graph.ports(), self.assertRaises(REFUSED):
            operation.execute(graph.authority_pin, began_ns=graph.began_ns)

        graph.mkdir.assert_not_called()
        graph.supervise_operation.assert_not_called()

    def test_execute_replays_completed_child_only_after_qualified_watchdog_result(self):
        for cleanup, capture, returncode, qualified in (
            (True, True, None, True),
            (False, True, None, False),
            (True, False, None, False),
            (True, True, 1, False),
        ):
            with self.subTest(cleanup=cleanup, capture=capture, returncode=returncode):
                graph = SyntheticOperation(claimed=False)
                result = graph.execute(cleanup=cleanup, capture=capture, returncode=returncode)
                self.assertIs(result["passed"], qualified)
                self.assertIs(result["feature_acceptance"], False)
                self.assertEqual(graph.read(operation.RESULT)[1], result)
                stage_pin, stage = graph.read(operation.STAGE)
                self.assertIs(stage["passed"], True)
                self.assertEqual(result["stages"], stage_pin)
                self.assertEqual(result["supervisor"], graph.read(operation.TERMINAL)[0])
                request_pin, request = graph.read(operation.REQUEST)
                self.assertEqual(request["authority"], graph.authority_pin)
                self.assertEqual(request["attempt"], result["attempt"])
                self.assertEqual(graph.read(operation.WORKER_CLAIM)[1],
                                 dict(request=request_pin, worker=graph.worker))
                graph.supervise_operation.assert_called_once()
                command, barrier, capture, seconds, _ = graph.supervise_operation.call_args.args
                self.assertEqual(command[-1], "_worker")
                self.assertEqual(barrier, operation.BARRIER + handoff.env.encoded(request_pin))
                self.assertEqual(capture, operation.CAPTURE)
                self.assertEqual(seconds, handoff.SECONDS - handoff.TAIL_SECONDS - 10)
                graph.prepare_once.assert_called_once()
                self.assertEqual(graph.verify_activation.call_count, 2 if qualified else 1)

    def test_success_forwards_only_approved_prepare_and_bound_activation(self):
        graph = SyntheticOperation()
        stage = graph.stages()
        auth_pin, receipt = graph.read(operation.PREPARE_AUTH)

        self.assertIs(stage["passed"], True)
        self.assertIs(stage["feature_acceptance"], False)
        self.assertEqual(stage["phase"], "completed")
        self.assertEqual(stage["worker"], graph.worker)
        self.assertEqual(stage["prepare"], graph.read(graph.prepare_result_path)[0])
        self.assertEqual(stage["prepare_evidence"], {
            role: graph.read(path)[0] for role, path in graph.prepare_evidence_paths.items()
        })
        self.assertEqual(stage["closure"], graph.closure)
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        graph.preflight.assert_called_once_with(graph.authority, graph.plan, graph.prepare)
        graph.prepare_once.assert_called_once_with(
            graph.plan["prepare"]["path"], auth_pin["path"], expected_ledger=graph.authority["ledger"],
            expected_proposal_sha256=graph.plan["prepare"]["sha256"], prepare_scope=handoff.OPERATION_SCOPE,
        )
        self.assertEqual(receipt["proposal_sha256"], graph.plan["prepare"]["sha256"])
        self.assertEqual(receipt["prepare_scope"], handoff.OPERATION_SCOPE)
        graph.activate.assert_called_once_with(
            stage["admission"], graph.authority_pin, graph.attempt_pin, began_ns=graph.began_ns,
        )
        graph.verify_activation.assert_called_once_with(
            stage["activation"], stage["admission"], graph.authority_pin, graph.attempt_pin,
            began_ns=graph.began_ns, expected_parent=graph.worker,
        )

    def test_stale_ledger_preserves_preflight_refusal_before_prepare(self):
        graph = SyntheticOperation()
        graph.preflight.side_effect = handoff.env.EnvironmentRefused("storage_ledger_changed")
        stage = graph.stages()

        self.assertIs(stage["passed"], False)
        self.assertIsNotNone(stage["reason"])
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        self.assertNotIn(operation.PREPARE_AUTH, graph.records)
        graph.prepare_once.assert_not_called()
        graph.activate.assert_not_called()

    def test_rebound_reviewed_plan_after_preflight_cannot_dispatch(self):
        graph = SyntheticOperation()

        def move_plan(*args):
            graph.add("changed_plan", handoff.PLAN, dict(graph.plan, model_material=True))
            return graph.preflight_result

        graph.preflight.side_effect = move_plan
        stage = graph.stages()
        self.assertIs(stage["passed"], False)
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        graph.prepare_once.assert_not_called()
        graph.activate.assert_not_called()

    def test_preflight_time_does_not_reset_full_operation_window(self):
        graph = SyntheticOperation()

        def elapse_during_preflight(*args):
            graph.now_ns = graph.began_ns + (handoff.SECONDS - 1) * NS
            return graph.preflight_result

        graph.preflight.side_effect = elapse_during_preflight
        stage = graph.stages()

        self.assertIs(stage["passed"], False)
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        graph.prepare_once.assert_not_called()
        graph.activate.assert_not_called()

    def test_prepare_plan_drift_at_authorization_publication_refuses_dispatch(self):
        graph = SyntheticOperation()

        def publish_and_drift(path, value):
            binding = graph.publish(path, value)
            if path == operation.PREPARE_AUTH:
                graph.add("changed_prepare", handoff.PREPARE, dict(graph.prepare, memory_mib=2048))
            return binding

        with graph.ports(), patch.object(operation, "_save", side_effect=publish_and_drift):
            stage = operation._run_stages(
                graph.authority_pin, graph.attempt_pin, graph.began_ns, graph.worker,
            )

        self.assertIs(stage["passed"], False)
        self.assertIn(operation.PREPARE_AUTH, graph.records)
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        graph.prepare_once.assert_not_called()
        graph.activate.assert_not_called()

    def test_uncertain_prepare_preserves_prefix_and_never_retries(self):
        graph = SyntheticOperation()
        graph.prepare_once.side_effect = handoff.env.EnvironmentRefused("prepare_failed")
        stage = graph.stages()

        self.assertIs(stage["passed"], False)
        self.assertIsNotNone(stage["preflight"])
        self.assertIn(operation.PREPARE_AUTH, graph.records)
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        graph.prepare_once.assert_called_once()
        graph.admit.assert_not_called()
        graph.activate.assert_not_called()

    def test_failed_prepare_with_readable_refusal_keeps_receipt(self):
        graph = SyntheticOperation()
        refused = dict(graph.prepare_result, status="refused", closure_verified=False,
                       child_cleanup_complete=False, prepared_created=False)

        def fail_after_evidence(*args, **kwargs):
            graph.publish(graph.prepare_result_path, refused)
            raise handoff.env.EnvironmentRefused("prepare_failed")

        graph.prepare_once.side_effect = fail_after_evidence
        stage = graph.stages()

        self.assertIs(stage["passed"], False)
        self.assertEqual(stage["prepare"], graph.read(graph.prepare_result_path)[0])
        self.assertEqual(graph.read(graph.prepare_result_path)[1], refused)
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        graph.prepare_once.assert_called_once()
        graph.admit.assert_not_called()

    def test_unverified_activation_retains_its_pinned_result_and_refuses(self):
        graph = SyntheticOperation()
        graph.verify_activation.side_effect = handoff.env.EnvironmentRefused("activation")
        stage = graph.stages()

        self.assertIs(stage["passed"], False)
        self.assertEqual(stage["activation"], graph.read(operation.activation.CONTROL / "activation-result-v1.json")[0])
        self.assertIsNone(stage["closure"])
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        graph.prepare_once.assert_called_once()
        graph.activate.assert_called_once()

    def test_foreign_stage_identity_refuses_before_activation_replay(self):
        graph = SyntheticOperation()
        stage = graph.stages()
        graph.verify_activation.reset_mock()
        wrong = dict(stage, worker=dict(graph.worker, pid=99999))
        wrong_pin = graph.add("foreign_stage", operation.STAGE, wrong)

        with graph.ports(), self.assertRaises(REFUSED):
            operation._verify_stage(wrong_pin, graph.authority_pin, graph.attempt_pin,
                                    graph.began_ns, graph.worker)

        graph.verify_activation.assert_not_called()

    def test_stage_replay_refuses_replaced_prepare_result_bytes(self):
        graph = SyntheticOperation()
        graph.stages()
        graph.verify_activation.reset_mock()
        stage_pin, _ = graph.read(operation.STAGE)
        graph.add("changed_prepare_result", graph.prepare_result_path,
                  dict(graph.prepare_result, child_cleanup_complete=False))

        with graph.ports(), self.assertRaises(REFUSED):
            operation._verify_stage(stage_pin, graph.authority_pin, graph.attempt_pin,
                                    graph.began_ns, graph.worker)

        graph.verify_activation.assert_not_called()

    def test_stage_replay_refuses_replaced_prepare_owner_or_worker_claim(self):
        for role, identity in (("start", "owner"), ("worker", "worker")):
            with self.subTest(role=role):
                graph = SyntheticOperation()
                self.assertIs(graph.stages()["passed"], True)
                graph.verify_activation.reset_mock()
                stage_pin, _ = graph.read(operation.STAGE)
                path = graph.prepare_evidence_paths[role]
                _, value = graph.read(path)
                graph.add("changed_prepare_evidence", path,
                          dict(value, **{identity: dict(value[identity], pid=99999)}))

                with graph.ports(), self.assertRaises(REFUSED):
                    operation._verify_stage(stage_pin, graph.authority_pin, graph.attempt_pin,
                                            graph.began_ns, graph.worker)

                graph.verify_activation.assert_not_called()

    def test_bad_prepare_capture_refuses_before_admission_or_activation(self):
        graph = SyntheticOperation()

        def complete_with_changed_stdout(*args, **kwargs):
            result = graph.complete_prepare(*args, **kwargs)
            path = graph.prepare_evidence_paths["stdout"]
            _, stdout = graph.read(path)
            graph.add("changed_prepare_output", path, b"z" * len(stdout))
            return result

        graph.prepare_once.side_effect = complete_with_changed_stdout
        stage = graph.stages()

        self.assertIs(stage["passed"], False)
        self.assertEqual(stage["prepare"], graph.read(graph.prepare_result_path)[0])
        self.assertIsNone(stage["prepare_evidence"])
        graph.admit.assert_not_called()
        graph.activate.assert_not_called()

    def test_stage_replay_refuses_cross_profile_prepare_authorization(self):
        graph = SyntheticOperation()
        graph.stages()
        graph.verify_activation.reset_mock()
        stage_pin, _ = graph.read(operation.STAGE)
        _, authorization = graph.read(operation.PREPARE_AUTH)
        graph.add("changed_prepare_authorization", operation.PREPARE_AUTH,
                  dict(authorization, prepare_scope="synthetic-foreign-profile"))

        with graph.ports(), self.assertRaises(REFUSED):
            operation._verify_stage(stage_pin, graph.authority_pin, graph.attempt_pin,
                                    graph.began_ns, graph.worker)

        graph.verify_activation.assert_not_called()

    def test_stage_replay_refuses_late_approved_input_drift_after_activation_replay(self):
        for path in (handoff.PROPOSAL, handoff.PLAN, handoff.PREPARE):
            with self.subTest(path=path):
                graph = SyntheticOperation()
                self.assertIs(graph.stages()["passed"], True)
                graph.verify_activation.reset_mock()
                stage_pin, _ = graph.read(operation.STAGE)

                def replay_then_drift(*args, **kwargs):
                    closure = graph.replay_activation(*args, **kwargs)
                    _, value = graph.read(path)
                    changed = value + b"\nchanged" if type(value) is bytes else dict(value, changed=True)
                    graph.add("changed_approved_input", path, changed)
                    return closure

                graph.verify_activation.side_effect = replay_then_drift
                with graph.ports(), self.assertRaises(REFUSED):
                    operation._verify_stage(stage_pin, graph.authority_pin, graph.attempt_pin,
                                            graph.began_ns, graph.worker)

                graph.verify_activation.assert_called_once()

    def test_worker_entry_requires_the_announced_identity_in_its_job(self):
        graph = SyntheticOperation()
        request_pin, request = graph.enter_records()
        for members in ([graph.worker["pid"]], [123]):
            with self.subTest(members=members), graph.ports(), \
                 patch.object(operation.sys, "stdin", SimpleNamespace(
                     buffer=BytesIO(operation.BARRIER + handoff.env.encoded(request_pin)))), \
                 patch.object(operation.os, "getppid", return_value=graph.parent["pid"]), \
                 patch.object(operation.os, "getpid", return_value=graph.worker["pid"]), \
                 patch.object(operation, "_identity", side_effect=lambda pid, expected=None: expected), \
                 patch.object(operation.mechanisms, "_ProcessApi",
                              return_value=SimpleNamespace(current_job_pids=lambda: members)):
                if graph.worker["pid"] in members:
                    self.assertEqual(operation._enter(), (request_pin, request, graph.worker))
                else:
                    with self.assertRaises(REFUSED):
                        operation._enter()

        graph.prepare_once.assert_not_called()

    def test_already_claimed_worker_cannot_enter_stages_again(self):
        graph = SyntheticOperation()
        request_pin, request = graph.enter_records()
        existing = graph.publish(operation.WORKER_CLAIM, dict(request=request_pin, worker=graph.worker))
        with graph.ports(), patch.object(operation, "_enter", return_value=(request_pin, request, graph.worker)), \
             patch.object(operation, "_run_stages", side_effect=AssertionError("spent claim dispatched")) as run:
            self.assertEqual(operation.main(["_worker"]), 1)

        run.assert_not_called()
        self.assertEqual(graph.read(operation.WORKER_CLAIM)[0], existing)


if __name__ == "__main__":
    unittest.main()
