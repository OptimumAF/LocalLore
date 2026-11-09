"""Inert authorization and binding checks for reuse of the prepared SDK23 guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack, contextmanager
import copy
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from benchmarks import adb_held_socket_probe as python_pins
from benchmarks import isolated_adb_lease as lease
from benchmarks import owned_saved_library_status as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import saved_library_status_handoff as original
from benchmarks import saved_library_status_prepared_review as review
from benchmarks import saved_library_status_resume_handoff as resume
from scripts.tests.test_saved_library_status_handoff import BootRecords, NOW, REFUSED


class ResumeRecords(BootRecords):
    """Keep original and prospective operation bytes in one inert file graph."""

    def __init__(self):
        super().__init__(("run", lambda row: row["paths"].update(content=str(original.GUEST / "content"))))
        self.present.update((original.ATTEMPT_ROOT, original.OWNED_ROOT))
        self.original_admission = self.admission_pin
        self.original_authority = self.authority_pin
        self.original_run = self.read(original.RUN)[0]
        self.original_reference = self.read(original.AUTHORITY)[1]["approval_reference"]
        self.manifest_pin = self.add("manifest", review.MANIFEST, dict(records_by_name={
            "attempt/admission-v1.json": self.original_admission,
            "attempt/run-proposal-v1.json": self.original_run,
            "plan/human-authority-v1.json": self.original_authority,
        }))
        receipt = self.add("guest_inputs", original.OWNED_ROOT / "guest-inputs-v1.json", {})
        self.evidence = dict(
            version=1, scope=review.SCOPE, status="prepared_candidate",
            manifest=self.manifest_pin, ledger=self.ledger_pin, guest_inputs=receipt,
            reserved_bytes=storage.RESERVATION_BYTES, execution_authorized=False,
        )
        self.inspect = Mock(side_effect=self.review)
        self.source_pin = self.add("handoff_source", Path(resume.__file__).resolve(), b"synthetic handoff source")
        self.review_pin = self.add("review_source", Path(review.__file__).resolve(), b"synthetic review source")
        self.operation_pin = self.add("operation_source", Path(resume.__file__).with_name(
            "saved_library_status_resume_operation.py").resolve(), b"synthetic operation source")
        self.refuser_pin = dict(self.admission["guest"]["refuser_source"],
                                path=str(original.ROOT / "benchmarks/native/deny_adb_client.c"))
        self.created = []
        self.directories = []
        self.plan = dict(
            version=1, scope=resume.PLAN_SCOPE, source_root=str(original.ROOT),
            sources=self.admission["sources"], handoff_source=self.source_pin, review_source=self.review_pin,
            operation_source=self.operation_pin,
            python=self.admission["python"], artifacts=self.admission["artifacts"],
            evidence=self.evidence, original_authority=self.original_authority,
            original_run=self.original_run, original_admission=self.original_admission,
        )
        self.reseal_authority()

    def review(self, manifest_pin, ledger_pin):
        self.check_binding(manifest_pin)
        self.check_binding(ledger_pin)
        if (manifest_pin, ledger_pin) != (self.manifest_pin, self.ledger_pin):
            raise env.EnvironmentRefused("binding")
        return copy.deepcopy(self.evidence)

    def reseal_authority(self, change=None, proposal_change=None):
        plan_pin = self.add("resume_plan", resume.PLAN, self.plan)
        lines = (
            "# Synthetic activation-only approval proposal\n"
            f"Plan SHA-256 {plan_pin['sha256']}\n"
            f"Manifest SHA-256 {self.evidence['manifest']['sha256']}\n"
            f"Ledger SHA-256 {self.evidence['ledger']['sha256']}\n"
        )
        if proposal_change is not None:
            lines = proposal_change(lines)
        proposal_pin = self.add("resume_proposal", resume.PROPOSAL, lines.encode())
        self.grant = dict(
            version=1, scope=resume.OPERATION_SCOPE, proposal=proposal_pin, plan=plan_pin,
            approval_reference="synthetic-fresh-activation-approval",
            allow_sdk_prepare=False, allow_one_boot=True, allow_model=False,
            allow_retirement=False, max_operation_seconds=original.SECONDS,
        )
        if change is not None:
            change(self.grant)
        self.resume_authority = self.add("resume_authority", resume.AUTHORITY, self.grant)

    def binding(self, path, **_kwargs):
        if Path(path) == Path(self.refuser_pin["path"]):
            return copy.deepcopy(self.refuser_pin)
        return self.read(path)[0]

    def mkdir(self, path, *args, **kwargs):
        path = Path(path)
        if path != resume.ATTEMPT_ROOT or path in self.present:
            raise FileExistsError(path)
        self.present.add(path)
        self.directories.append(path)

    def create(self, path, value):
        path = Path(path)
        if path in self.records or path.parent != resume.ATTEMPT_ROOT or path.parent not in self.present:
            raise FileExistsError(path)
        self.created.append(path)
        self.present.add(path)
        return self.add("create", path, value)["sha256"]

    @contextmanager
    def ports(self):
        with super().ports(), ExitStack() as stack:
            for module, name, replacement in (
                (review, "inspect", self.inspect),
                (contract, "source_bindings", lambda: copy.deepcopy(self.admission["sources"])),
                (lease, "source_bindings", lambda: copy.deepcopy(self.admission["server"]["sources"])),
                (python_pins, "_python_bindings", lambda: copy.deepcopy(self.admission["python"])),
                (env, "binding", self.binding),
                (env, "create_json", self.create),
                (Path, "mkdir", lambda path, *args, **kwargs: self.mkdir(path, *args, **kwargs)),
                (Path, "open", Mock(side_effect=AssertionError("unexpected file access"))),
            ):
                stack.enter_context(patch.object(module, name, replacement))
            yield

    def begin(self):
        with self.ports():
            return resume.begin_attempt(self.resume_authority)

    def bind(self, attempt_pin):
        with self.ports():
            return resume.bind_admission(self.resume_authority, attempt_pin)

    def handoff(self, attempt_pin, admission_pin, change=None):
        record = dict(
            version=1, scope=resume.HANDOFF_SCOPE, authority=self.resume_authority,
            attempt=attempt_pin, admission=admission_pin,
            supervisor=dict(pid=701, creation_filetime=800,
                            executable=self.admission["python"]["executable"]["path"]),
            began_ns=NOW - 10 * original.NS, until_ns=NOW + 1600 * original.NS,
        )
        if change is not None:
            change(record)
        return self.add("handoff", resume.HANDOFF, record)


class SavedLibraryStatusResumeHandoffTests(unittest.TestCase):
    def test_read_only_inspection_carries_the_original_pins_into_a_distinct_plan(self):
        graph = ResumeRecords()
        with graph.ports():
            result = resume.inspect_plan(graph.manifest_pin, graph.ledger_pin)
        self.assertEqual(result, graph.plan)
        self.assertFalse(result["evidence"]["execution_authorized"])
        self.assertEqual(graph.directories, [])
        self.assertEqual(graph.created, [])

    def test_scope_and_control_paths_are_disjoint_from_the_spent_run(self):
        for label in ("OPERATION_SCOPE", "PLAN_SCOPE", "HANDOFF_SCOPE"):
            self.assertNotEqual(getattr(resume, label), getattr(original, label))
        self.assertNotEqual(resume.RUN_SCOPE, contract.RUN_SCOPE)
        for name in ("OUT", "PLAN", "PROPOSAL", "AUTHORITY", "ATTEMPT_ROOT", "ATTEMPT",
                     "RUN", "RUN_AUTHORITY", "ADMISSION", "HANDOFF", "OWNED_ROOT"):
            self.assertNotEqual(getattr(resume, name), getattr(original, name))

    def test_a_fresh_activation_only_grant_reads_back_exactly(self):
        graph = ResumeRecords()
        with graph.ports():
            self.assertEqual(resume.read_authority(graph.resume_authority), (graph.grant, graph.plan))
        self.assertEqual(graph.created, [])

    def test_spent_grant_and_its_reference_cannot_authorize_the_new_attempt(self):
        graph = ResumeRecords()
        with graph.ports(), self.assertRaises(REFUSED):
            resume.begin_attempt(graph.original_authority)
        graph.reseal_authority(lambda row: row.update(approval_reference=graph.original_reference))
        with self.assertRaises(REFUSED):
            graph.begin()
        self.assertEqual(graph.directories, [])
        self.assertEqual(graph.created, [])

    def test_grant_rejects_each_permission_outside_one_activation(self):
        for key, value in (
            ("scope", original.OPERATION_SCOPE), ("allow_sdk_prepare", True), ("allow_one_boot", 1),
            ("allow_model", True), ("allow_retirement", True), ("max_operation_seconds", 2401),
            ("version", True), ("approval_reference", " untrimmed"),
        ):
            with self.subTest(key=key, value=value):
                graph = ResumeRecords()
                graph.reseal_authority(lambda row: row.update({key: value}))
                with self.assertRaises(REFUSED):
                    graph.begin()
                self.assertEqual(graph.directories, [])
                self.assertEqual(graph.created, [])

    def test_proposal_requires_one_correct_line_for_each_digest(self):
        for label in ("Plan SHA-256", "Manifest SHA-256", "Ledger SHA-256"):
            for duplicate in (False, True):
                with self.subTest(label=label, duplicate=duplicate):
                    graph = ResumeRecords()

                    def change(text):
                        if duplicate:
                            line = next(line for line in text.splitlines() if line.startswith(label))
                            return text + line + "\n"
                        return text.replace(label, "Foreign digest", 1)

                    graph.reseal_authority(proposal_change=change)
                    with self.assertRaises(REFUSED):
                        graph.begin()
                    self.assertEqual(graph.directories, [])

    def test_consumed_attempt_refuses_a_second_begin_without_touching_the_old_run(self):
        graph = ResumeRecords()
        old = {path: copy.deepcopy(record) for path, record in graph.records.items()
               if path.is_relative_to(original.OUT)}
        attempt_pin = graph.begin()
        self.assertEqual(attempt_pin, graph.read(resume.ATTEMPT)[0])
        with self.assertRaises(REFUSED):
            graph.begin()
        self.assertEqual(graph.directories, [resume.ATTEMPT_ROOT])
        self.assertEqual(graph.created, [resume.ATTEMPT])
        self.assertEqual(old, {path: graph.records[path] for path in old})

    def test_a_preexisting_attempt_directory_blocks_even_without_a_claim(self):
        graph = ResumeRecords()
        graph.present.add(resume.ATTEMPT_ROOT)
        with self.assertRaises(REFUSED):
            graph.begin()
        self.assertEqual(graph.directories, [])
        self.assertEqual(graph.created, [])

    def test_ledger_digest_drift_cannot_consume_the_new_attempt(self):
        graph = ResumeRecords()
        ledger = graph.read(original.LEDGER)[1]
        ledger["entries"][0]["state"] = "retained"
        graph.add("drifted_ledger", original.LEDGER, ledger)
        with self.assertRaises(REFUSED):
            graph.begin()
        self.assertEqual(graph.directories, [])
        self.assertEqual(graph.created, [])

    def test_admission_keeps_original_proposal_bytes_and_new_activation_scope(self):
        graph = ResumeRecords()
        attempt_pin = graph.begin()
        admission_pin = graph.bind(attempt_pin)
        run_pin, run = graph.read(resume.RUN)
        admission = graph.read(resume.ADMISSION)[1]
        self.assertEqual(admission_pin, graph.read(resume.ADMISSION)[0])
        self.assertEqual(run, graph.read(original.RUN)[1])
        self.assertEqual(run_pin["sha256"], graph.original_run["sha256"])
        self.assertEqual(admission["root"], str(resume.OWNED_ROOT))
        self.assertEqual(admission["server"]["root"], str(resume.OWNED_ROOT / "server"))
        self.assertEqual(admission["guest"]["proposal"], run_pin)
        self.assertEqual(admission["guest"]["authorization"], graph.read(resume.RUN_AUTHORITY)[0])
        self.assertEqual(graph.read(resume.RUN_AUTHORITY)[1]["run_scope"], resume.RUN_SCOPE)
        self.assertEqual(graph.read(original.RUN)[0], graph.original_run)
        self.assertEqual(admission["guest"]["root"], str(original.GUEST))
        self.assertEqual(admission["guest"]["refuser_source"], graph.refuser_pin)
        self.assertEqual(admission["artifacts"], graph.admission["artifacts"])

    def test_source_pin_drift_refuses_before_creating_an_attempt(self):
        for source in ("source_pin", "review_pin"):
            with self.subTest(source=source):
                graph = ResumeRecords()
                graph.add("drifted_source", getattr(graph, source)["path"], b"changed source")
                with self.assertRaises(REFUSED):
                    graph.begin()
                self.assertEqual(graph.directories, [])

    def test_original_run_bytes_drift_refuses_before_creating_an_attempt(self):
        graph = ResumeRecords()
        old_run = graph.read(original.RUN)[1]
        graph.add("drifted_run", original.RUN, dict(old_run, max_seconds=1799))
        with self.assertRaises(REFUSED):
            graph.begin()
        self.assertEqual(graph.directories, [])

    def test_a_new_boot_marker_or_lock_refuses_to_bind_run_inputs_after_claim(self):
        for path in (
            original.LEDGER.with_name("admission.lock"),
            original.GUEST / contract.BOOT_CLAIM_FILE,
            original.GUEST / "guest-storage-closure-v1.json",
            original.GUEST / "content/userdata-qemu.img",
            original.OWNED_ROOT / "running-v1.json",
            original.OWNED_ROOT / "guest-output-v1",
        ):
            with self.subTest(path=path):
                graph = ResumeRecords()
                attempt_pin = graph.begin()
                graph.present.add(path)
                with self.assertRaises(REFUSED):
                    graph.bind(attempt_pin)
                self.assertEqual(graph.created, [resume.ATTEMPT])

    def test_refuser_source_bytes_must_match_the_original_preparation(self):
        graph = ResumeRecords()
        attempt_pin = graph.begin()
        graph.refuser_pin["sha256"] = "1" * 64
        with self.assertRaises(REFUSED):
            graph.bind(attempt_pin)
        self.assertNotIn(resume.ADMISSION, graph.records)

    def test_ledger_drift_during_admission_revalidation_keeps_partial_inputs_and_refuses(self):
        graph = ResumeRecords()
        attempt_pin = graph.begin()

        def drift(_admission):
            ledger = graph.read(original.LEDGER)[1]
            ledger["entries"][0]["state"] = "retained"
            graph.add("drifted_ledger", original.LEDGER, ledger)

        with graph.ports(), patch.object(contract, "revalidate_inputs", side_effect=drift):
            with self.assertRaises(REFUSED):
                resume.bind_admission(graph.resume_authority, attempt_pin)
        self.assertEqual(graph.created, [resume.ATTEMPT, resume.RUN, resume.RUN_AUTHORITY])
        self.assertNotIn(resume.ADMISSION, graph.records)
        with self.assertRaises(REFUSED):
            graph.begin()

    def test_foreign_attempt_pin_refuses_before_writing_any_run_inputs(self):
        graph = ResumeRecords()
        graph.begin()
        with self.assertRaises(REFUSED):
            graph.bind(graph.read(original.ATTEMPT)[0])
        self.assertEqual(graph.created, [resume.ATTEMPT])

    def test_handoff_rejects_the_spent_run_scope_even_when_admission_is_resealed(self):
        graph = ResumeRecords()
        attempt_pin = graph.begin()
        graph.bind(attempt_pin)
        authorization = graph.read(resume.RUN_AUTHORITY)[1]
        wrong_scope = graph.add("foreign_scope", resume.RUN_AUTHORITY,
                                dict(authorization, run_scope=contract.RUN_SCOPE))
        admission = graph.read(resume.ADMISSION)[1]
        admission["guest"]["authorization"] = wrong_scope
        admission_pin = graph.add("changed_admission", resume.ADMISSION, admission)
        handoff_pin = graph.handoff(attempt_pin, admission_pin)
        with graph.ports(), self.assertRaises(REFUSED):
            resume.verify_handoff(handoff_pin, admission_pin)

    def test_handoff_accepts_only_the_bound_admission_and_live_supervisor_window(self):
        graph = ResumeRecords()
        attempt_pin = graph.begin()
        admission_pin = graph.bind(attempt_pin)
        handoff_pin = graph.handoff(attempt_pin, admission_pin)
        with graph.ports():
            self.assertEqual(resume.verify_handoff(handoff_pin, admission_pin),
                             (graph.read(resume.HANDOFF)[1], graph.read(resume.ADMISSION)[1]))
        for change in (
            lambda row: row.update(admission=graph.original_admission),
            lambda row: row.update(until_ns=NOW),
            lambda row: row.update(supervisor=dict(row["supervisor"], executable=r"C:\Synthetic\other.exe")),
        ):
            with self.subTest(change=change):
                handoff_pin = graph.handoff(attempt_pin, admission_pin, change)
                with graph.ports(), self.assertRaises(REFUSED):
                    resume.verify_handoff(handoff_pin, admission_pin)


if __name__ == "__main__":
    unittest.main()
