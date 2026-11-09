"""Exercise the SDK23 resume readiness audit using inert host inputs.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import redirect_stdout
import copy
from io import StringIO
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from scripts import inspect_sdk23_resume_readiness as audit


GIB = 1024 ** 3
RECORDS = 256 * 1024 ** 2
SEALED = dict(source_head="a" * 40, proposal_sha256="b" * 64, plan_sha256="c" * 64,
              manifest_sha256="d" * 64, ledger_sha256="e" * 64, floors={"C:": 16 * GIB, "D:": 40 * GIB})
REQUIRED = {"C:": 16 * GIB, "D:": 40 * GIB + RECORDS}


class SDK23ResumeReadinessAuditTests(unittest.TestCase):
    def test_proposal_uses_the_full_unambiguous_source_literal(self):
        path = "D:/Worktrees/LocalLore-frozen"
        head = "a" * 40

        def line(value):
            return ("This proposal requests one invocation of the SDK23 resume operator from "
                    "[draft PR #488](https://github.com/OptimumAF/LocalLore/pull/488) "
                    f"at `{value}` in `{path}`.")

        self.assertEqual(audit._proposal_head(line(head)), (head, path))
        for text in (line(head[:-2]), line(head + "0"), line(head.upper()), line("g" * 40),
                     line(head[:-2]) + "\n" + line(head), line(head) + "\n" + line("b" * 40),
                     line(head) + "\n" + line(head)):
            with self.subTest(text=text), self.assertRaisesRegex(audit.ReadinessRefused, "^proposal_source$"):
                audit._proposal_head(text)

    def test_dirty_or_foreign_frozen_source_refuses_before_reading_plan(self):
        text = f"Operator at `{audit.FROZEN_HEAD}` in `{audit.FROZEN_SOURCE.as_posix()}`.".encode("utf-8")
        bindings = [{"sha256": audit.EXPECTED["proposal_sha256"]}, {"sha256": audit.ORIGINAL_SHA256}]
        for replies in (["f" * 40 + "\n", ""], [audit.FROZEN_HEAD + "\n", "?? synthetic\n"]):
            with (self.subTest(replies=replies), patch.object(audit.handoff.env, "safe_path"),
                  patch.object(audit.os.path, "lexists", return_value=False),
                  patch.object(audit.handoff.env, "binding", side_effect=bindings),
                  patch.object(audit.handoff.files, "_bound", return_value=text),
                  patch.object(audit.subprocess, "check_output", side_effect=replies) as git,
                  patch.object(audit.handoff, "read") as read):
                with self.assertRaisesRegex(audit.ReadinessRefused, "^proposal_source$"):
                    audit._sealed_inputs()
            self.assertEqual(git.call_args_list, [
                call(["git", "rev-parse", "HEAD"], cwd=audit.FROZEN_SOURCE, text=True, timeout=15),
                call(["git", "status", "--porcelain"], cwd=audit.FROZEN_SOURCE, text=True, timeout=15),
            ])
            read.assert_not_called()

    def test_existing_authority_or_attempt_refuses_before_bound_input_reads(self):
        for protected in (audit.resume.AUTHORITY, audit.resume.ATTEMPT_ROOT):
            with (self.subTest(protected=protected), patch.object(audit.handoff.env, "safe_path"),
                  patch.object(audit.os.path, "lexists", side_effect=lambda path: path == protected),
                  patch.object(audit.handoff.env, "binding") as bind,
                  patch.object(audit.subprocess, "check_output") as git):
                with self.assertRaisesRegex(audit.ReadinessRefused, "^already_used$"):
                    audit._sealed_inputs()
            bind.assert_not_called()
            git.assert_not_called()

    def test_existing_guest_does_not_reduce_the_disk_or_records_floor(self):
        free = {"C:": 50 * GIB, "D:": 40 * GIB}
        with (patch.object(audit, "_sealed_inputs", return_value=copy.deepcopy(SEALED)),
              patch.object(audit, "_free_bytes", return_value=free),
              patch.object(audit, "_full_preflight", side_effect=AssertionError("preflight was not gated")) as full):
            result = audit.inspect()
        self.assertEqual(audit.RECORDS_BYTES, RECORDS)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason"], "host_disk_capacity")
        self.assertEqual(result["free_bytes"], free)
        self.assertEqual(result["required_bytes"], REQUIRED)
        self.assertEqual(result["shortfall_bytes"], {"C:": 0, "D:": RECORDS})
        self.assertIs(result["execution_authorized"], False)
        full.assert_not_called()

    def test_one_byte_below_either_floor_refuses_before_full_preflight(self):
        for drive in REQUIRED:
            with self.subTest(drive=drive):
                free = dict(REQUIRED)
                free[drive] -= 1
                with (patch.object(audit, "_sealed_inputs", return_value=copy.deepcopy(SEALED)),
                      patch.object(audit, "_free_bytes", return_value=free),
                      patch.object(audit, "_full_preflight",
                                   side_effect=AssertionError("preflight was not gated")) as full):
                    result = audit.inspect()
                self.assertEqual((result["status"], result["reason"]), ("refused", "host_disk_capacity"))
                self.assertEqual(result["shortfall_bytes"][drive], 1)
                self.assertIs(result["execution_authorized"], False)
                full.assert_not_called()

    def test_exact_floors_allow_advisory_preflight_with_late_rechecks(self):
        io = Mock()
        io.sealed.side_effect = [copy.deepcopy(SEALED), copy.deepcopy(SEALED)]
        io.free.side_effect = [dict(REQUIRED), dict(REQUIRED)]
        facts = {"status": "ready", "reason": None, "resources": {"ports_free": True}}
        io.preflight.return_value = facts
        with (patch.object(audit, "_sealed_inputs", io.sealed),
              patch.object(audit, "_free_bytes", io.free),
              patch.object(audit, "_full_preflight", io.preflight)):
            result = audit.inspect()
        self.assertEqual((result["status"], result["reason"]), ("ready", None))
        self.assertIs(result["execution_authorized"], False)
        self.assertEqual(result["preflight"], facts)
        self.assertEqual(result["shortfall_bytes"], {"C:": 0, "D:": 0})
        for key in ("source_head", "proposal_sha256", "plan_sha256", "manifest_sha256", "ledger_sha256"):
            self.assertEqual(result[key], SEALED[key])
        self.assertEqual(io.mock_calls, [call.sealed(), call.free(), call.preflight(SEALED), call.sealed(),
                                         call.free()])

    def test_new_disk_shortfall_after_successful_full_preflight_refuses(self):
        final = dict(REQUIRED)
        final["D:"] -= 1
        facts = {"status": "ready", "reason": None, "resources": {}}
        with (patch.object(audit, "_sealed_inputs", side_effect=[copy.deepcopy(SEALED), copy.deepcopy(SEALED)]),
              patch.object(audit, "_free_bytes", side_effect=[dict(REQUIRED), final]),
              patch.object(audit, "_full_preflight", return_value=facts) as full):
            result = audit.inspect()
        self.assertEqual((result["status"], result["reason"]), ("refused", "host_disk_capacity"))
        self.assertEqual(result["free_bytes"], final)
        self.assertEqual(result["shortfall_bytes"], {"C:": 0, "D:": 1})
        self.assertIs(result["execution_authorized"], False)
        full.assert_called_once_with(SEALED)

    def test_late_source_or_ledger_drift_refuses_after_full_preflight(self):
        for key in ("source_head", "ledger_sha256"):
            with self.subTest(key=key):
                changed = dict(copy.deepcopy(SEALED), **{key: "f" * len(SEALED[key])})
                with (patch.object(audit, "_sealed_inputs", side_effect=[copy.deepcopy(SEALED), changed]),
                      patch.object(audit, "_free_bytes", return_value=dict(REQUIRED)),
                      patch.object(audit, "_full_preflight",
                                   return_value={"status": "ready", "reason": None}) as full):
                    with self.assertRaises(audit.ReadinessRefused):
                        audit.inspect()
                full.assert_called_once_with(SEALED)

    def test_full_preflight_refusal_is_not_replaced_by_available_disk(self):
        facts = {"status": "refused", "reason": "host_commit_capacity"}
        with (patch.object(audit, "_sealed_inputs", return_value=copy.deepcopy(SEALED)),
              patch.object(audit, "_free_bytes", return_value=dict(REQUIRED)),
              patch.object(audit, "_full_preflight", return_value=facts)):
            result = audit.inspect()
        self.assertEqual((result["status"], result["reason"]), ("refused", "host_commit_capacity"))
        self.assertEqual(result["preflight"], facts)
        self.assertIs(result["execution_authorized"], False)

    def test_cli_reports_seal_refusal_without_sampling_or_dispatch(self):
        stdout = StringIO()
        with (patch.object(audit, "_sealed_inputs", side_effect=audit.ReadinessRefused("proposal_source")),
              patch.object(audit, "_free_bytes") as free, patch.object(audit, "_full_preflight") as full,
              redirect_stdout(stdout)):
            code = audit.main([])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual((report["status"], report["reason"]), ("refused", "proposal_source"))
        self.assertIs(report["execution_authorized"], False)
        free.assert_not_called()
        full.assert_not_called()

    def test_full_preflight_delegates_to_pinned_python_with_bounded_output_contract(self):
        executable = {"path": audit.sys.executable}
        plan = {"python": {"executable": executable}}
        reply = {"status": "ready", "reason": None, "resources": {}}
        result = SimpleNamespace(returncode=0, stdout=json.dumps(reply).encode(), stderr=b"")
        with (patch.object(audit.handoff, "read", return_value=({"sha256": SEALED["plan_sha256"]}, plan)),
              patch.object(audit.handoff.env, "check_binding") as verify,
              patch.object(audit.subprocess, "run", return_value=result) as child):
            self.assertEqual(audit._full_preflight(SEALED), reply)
            result.stdout = json.dumps(dict(reply, execution_authorized=True)).encode()
            with self.assertRaisesRegex(audit.ReadinessRefused, "^preflight_child$"):
                audit._full_preflight(SEALED)
        self.assertEqual(verify.call_args_list, [call(executable), call(executable)])
        command = [audit.sys.executable, "-I", "-S", "-B", "-c", audit._CHILD]
        run = call(command, cwd=audit.FROZEN_SOURCE, input=audit.handoff.env.encoded(SEALED),
                   capture_output=True, timeout=120, creationflags=audit.subprocess.CREATE_NO_WINDOW)
        self.assertEqual(child.call_args_list, [run, run])
