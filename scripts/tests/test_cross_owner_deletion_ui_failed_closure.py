"""Host-only adversarial checks for SDK24 failed-activation review.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import cross_owner_deletion_ui_failed_closure as review
from benchmarks import receipt_avd_environment as env


FAILED_STDOUT = b'{"qualified_target": false, "reason": "owner", "feature_acceptance": false}'
REFUSALS = (OSError, RuntimeError, ValueError)


class CrossOwnerDeletionFailedClosureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.capture = self.root / "capture"
        self.capture.mkdir()
        self.stdout = self.capture / "owner-stdout-v1.bin"
        self.stderr = self.capture / "owner-stderr-v1.bin"
        self.result = self.root / "supervisor.json"

    @staticmethod
    def save(path, value):
        path.write_bytes(env.encoded(value))
        return env.binding(path)

    def terminal(self, stdout=FAILED_STDOUT + b"\r\n", stderr=b"", **changes):
        self.stdout.write_bytes(stdout)
        self.stderr.write_bytes(stderr)
        value = dict(status="child_exited", cleanup_complete=True, elapsed_ms=140,
                     output_capture_complete=True, worker_returncode=1,
                     stdout_bytes=len(stdout), stderr_bytes=len(stderr))
        return self.save(self.result, dict(value, **changes))

    def test_failed_joined_terminal_accepts_only_exact_output(self):
        pin = self.terminal()
        self.assertEqual(review._terminal(pin, self.result, self.capture, FAILED_STDOUT),
                         (env.binding(self.stdout), env.binding(self.stderr)))
        pin = self.terminal(stdout=b"")
        self.assertEqual(review._terminal(pin, self.result, self.capture, b""),
                         (env.binding(self.stdout), env.binding(self.stderr)))

    def test_terminal_refuses_changed_role_path_or_capture_bytes(self):
        pin = self.terminal()
        foreign = self.root / "foreign.json"
        foreign.write_bytes(self.result.read_bytes())
        with self.assertRaises(REFUSALS):
            review._terminal(pin, foreign, self.capture, FAILED_STDOUT)
        self.stdout.write_bytes(FAILED_STDOUT.replace(b"owner", b"other") + b"\r\n")
        with self.assertRaises(REFUSALS):
            review._terminal(pin, self.result, self.capture, FAILED_STDOUT)
        pin = self.terminal(stderr=b"x")
        with self.assertRaises(REFUSALS):
            review._terminal(pin, self.result, self.capture, FAILED_STDOUT)

    def test_review_refuses_if_success_evidence_exists(self):
        guest = self.root / "guest"
        owned = self.root / "owned"
        completion = self.root / "completion.json"
        with (patch.object(review.h, "GUEST", guest),
              patch.object(review.h, "OWNED_ROOT", owned),
              patch.object(review.h, "COMPLETION", completion)):
            review._without_success()
            completion.touch()
            with self.assertRaisesRegex(env.EnvironmentRefused, "^unexpected_success_evidence$"):
                review._without_success()

    def test_terminal_refuses_uncertain_cleanup_or_a_different_exit(self):
        for changes in (
            {"cleanup_complete": False}, {"output_capture_complete": False},
            {"worker_returncode": 0}, {"worker_returncode": True},
            {"status": "expired"}, {"elapsed_ms": -1}, {"stdout_bytes": 1},
        ):
            with self.subTest(changes=changes), self.assertRaises(REFUSALS):
                review._terminal(self.terminal(**changes), self.result, self.capture, FAILED_STDOUT)


class CrossOwnerDeletionFailedProcessTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        python = r"C:\Synthetic\python.exe"
        adb = r"D:\Synthetic\sdk\platform-tools\adb.exe"
        emulator = r"D:\Synthetic\sdk\emulator\emulator.exe"
        qemu = r"D:\Synthetic\sdk\emulator\qemu\windows-x86_64\qemu-system-x86_64-headless.exe"
        self.identities = [dict(pid=1001 + i, creation_filetime=90100 + i, executable=path)
                           for i, path in enumerate((python, python, python, python, adb, emulator, qemu))]
        parent, supervisor, owner, worker, server, launcher, guest = self.identities
        self.request = dict(parent=parent)
        self.outer = dict(worker=supervisor)
        self.worker = dict(worker=worker, server=server, launcher=launcher, guest=guest,
                           guest_ancestry=[launcher, guest])
        self.observation = dict(owner=owner, supervisor_worker=supervisor,
                                owner_request=None, worker_started=None)
        self.admission = dict(python={"executable": {"path": python}},
                              guest={"emulator": {"path": emulator}, "qemu": {"path": qemu}},
                              server={"adb": {"path": adb}})
        self.evidence = {}
        for role in ("operation", "observation", "ledger", "run"):
            path = self.root / (role + ".json")
            path.write_bytes(env.encoded({"synthetic": role}))
            self.evidence[role] = env.binding(path)
        self.pins = tuple(self.evidence[role] for role in ("operation", "observation", "ledger"))
        self.guest = self.root / "guest"
        self.enterContext(patch.object(review.h, "GUEST", self.guest))
        self.absence = self.enterContext(patch.object(review, "_without_success"))
        self.entry = dict(root=str(self.guest), state="retained", reserved_bytes=40 * 1024**3,
                          proposal_sha256=self.evidence["run"]["sha256"], closure=None,
                          recovery=None, retirement=None, retirement_receipt=None)

    def test_exact_roster_includes_all_seven_process_roles_in_order(self):
        self.assertEqual(review._identities(self.request, self.outer, self.worker, self.observation, self.admission),
                         self.identities)

    def test_process_roster_refuses_foreign_executable_duplicate_pid_or_ancestry(self):
        for label in ("executable", "duplicate_pid", "ancestry"):
            with self.subTest(label=label):
                worker = copy.deepcopy(self.worker)
                if label == "executable":
                    worker["server"]["executable"] = r"D:\Synthetic\foreign-adb.exe"
                elif label == "duplicate_pid":
                    worker["worker"]["pid"] = self.request["parent"]["pid"]
                else:
                    worker["guest_ancestry"].reverse()
                with self.assertRaises(REFUSALS):
                    review._identities(self.request, self.outer, worker, self.observation, self.admission)

    def process_rows(self):
        statuses = ("pid_absent", "pid_reused", "exited")
        return [dict(identity=identity, status=statuses[index % len(statuses)])
                for index, identity in enumerate(copy.deepcopy(self.identities))]

    def test_review_joins_all_ordered_closed_processes_without_authorizing_action(self):
        rows = self.process_rows()
        with (patch.object(review, "_snapshot", return_value=(self.evidence, self.identities)) as snapshot,
              patch.object(review.native, "closed_processes", return_value=rows) as native,
              patch.object(review.h, "ledger_entry", return_value=(self.pins[2], self.entry)) as ledger):
            report = review.inspect(*self.pins)
        self.assertEqual(report["disposition"], "guarded_closure_review_required")
        self.assertIs(report["existing_retirement_eligible"], False)
        self.assertIs(report["execution_authorized"], False)
        self.assertEqual(report["evidence"], self.evidence)
        self.assertEqual(report["processes"], rows)
        snapshot.assert_called_once_with(*self.pins)
        native.assert_called_once()
        self.assertEqual(native.call_args.args[0], self.identities)
        ledger.assert_called_once_with(self.pins[2])
        self.absence.assert_called_once_with()

    def test_review_refuses_partial_reordered_foreign_or_nonterminal_process_rows(self):
        rows = self.process_rows()
        mismatched = [dict(rows[0], identity=dict(rows[0]["identity"], creation_filetime=1)), *rows[1:]]
        for report in (rows[:-1], rows[::-1], mismatched, [dict(rows[0], status="live"), *rows[1:]],
                       [dict(rows[0], status="unknown"), *rows[1:]]):
            with (self.subTest(report=report),
                  patch.object(review, "_snapshot", return_value=(self.evidence, self.identities)),
                  patch.object(review.native, "closed_processes", return_value=report),
                  patch.object(review.h, "ledger_entry") as ledger,
                  self.assertRaises(REFUSALS)):
                review.inspect(*self.pins)
            ledger.assert_not_called()
        self.absence.assert_not_called()

    def test_review_refuses_if_ledger_drifts_during_liveness_check(self):
        def drift(*_):
            Path(self.pins[2]["path"]).write_bytes(env.encoded({"synthetic": "changed"}))
            return self.process_rows()

        with (patch.object(review, "_snapshot", return_value=(self.evidence, self.identities)),
              patch.object(review.native, "closed_processes", side_effect=drift),
              patch.object(review.h, "ledger_entry"),
              self.assertRaises(REFUSALS)):
            review.inspect(*self.pins)

    def test_review_requires_the_exact_retained_entry_after_liveness(self):
        for changes in ({"state": "closed"}, {"closure": self.evidence["operation"]},
                        {"proposal_sha256": "0" * 64}, {"reserved_bytes": 1}):
            entry = dict(self.entry, **changes)
            with (self.subTest(changes=changes),
                  patch.object(review, "_snapshot", return_value=(self.evidence, self.identities)),
                  patch.object(review.native, "closed_processes", return_value=self.process_rows()),
                  patch.object(review.h, "ledger_entry", return_value=(self.pins[2], entry)) as ledger,
                  self.assertRaisesRegex(env.EnvironmentRefused, "^retained$")):
                review.inspect(*self.pins)
            ledger.assert_called_once_with(self.pins[2])
        self.absence.assert_not_called()
