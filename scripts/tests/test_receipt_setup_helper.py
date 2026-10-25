"""Process-boundary tests; every Android transport below is synthetic.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
from pathlib import Path
import shlex
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.tests import test_receipt_setup_qualification as fixture

q, c = fixture.q, fixture.c
UIDS = {q.APP: 10310, q.TEST: 10311}
HELPER = (701, 10311, q.TEST)


def processes(*rows):
    return ("PID UID NAME\n1 1000 system_server\n" +
            "".join("%d %d %s\n" % row for row in rows)).encode()


def observe(boundary, index, rows=(), **changes):
    label, stage, methods = q.ProcessBoundary.observations[index]
    args = dict(label=label, stage=stage, methods=methods)
    args.update(changes)
    return boundary.observe(processes(*rows), {} if index == 0 else dict(UIDS), **args)


def ready_boundary():
    boundary = q.ProcessBoundary()
    observe(boundary, 0)
    observe(boundary, 1)
    return boundary


class HelperTransport(fixture.Transport):
    """Replace only PS observations; retain the existing closed mock transport."""
    def __init__(self, value, lease, snapshots):
        super().__init__(value, lease)
        self.snapshots = snapshots
        self.ps_count = 0
        self.fail_cleanup_at = self.lose_owner_at = None

    def __call__(self, command, **kwargs):
        value = super().__call__(command, **kwargs)
        if command[3] == "shell" and tuple(shlex.split(command[4])) == c.PS:
            assert self.ps_count < len(self.snapshots), "Unexpected repeated PS"
            value.stdout = processes(*self.snapshots[self.ps_count])
            self.ps_count += 1
            if self.ps_count == self.fail_cleanup_at:
                value.cleanup_complete = False
            if self.ps_count == self.lose_owner_at:
                self.lease.live = False
        return value


class ReceiptSetupHelperBoundaryTests(unittest.TestCase):
    def test_exact_sequence_tracks_test_main_separately(self):
        boundary = q.ProcessBoundary()
        for index in range(5):
            rows = () if index < 2 else (HELPER,)
            result = observe(boundary, index, rows)
            self.assertEqual(set(result), {"target", "test_helper"})
            self.assertEqual(result["target"], [])
            self.assertEqual(result["test_helper"], [] if not rows else
                             [dict(pid=701, uid=10311, name=q.TEST)])
        with self.assertRaises(AssertionError):
            observe(boundary, 4, (HELPER,))

    def test_all_absent_and_natural_disappearance_are_valid(self):
        for snapshots in (((), (), (), (), ()), ((), (), (HELPER,), (), ()),
                          ((), (), (HELPER,), (HELPER,), ())):
            with self.subTest(snapshots=snapshots):
                boundary = q.ProcessBoundary()
                for index, rows in enumerate(snapshots):
                    observe(boundary, index, rows)

    def test_diagnostic_copy_cannot_rebind_observed_identity(self):
        boundary = ready_boundary()
        first = observe(boundary, 2, (HELPER,))
        first["test_helper"][0].update(pid=999, uid=10310, name=q.APP)
        first["test_helper"].clear()
        first["target"].append({"name": q.APP})
        self.assertEqual(observe(boundary, 3, (HELPER,))["test_helper"][0]["pid"], 701)
        self.assertEqual(observe(boundary, 4, (HELPER,))["target"], [])

    def test_absent_binding_cannot_acquire_later_helper(self):
        boundary = ready_boundary()
        observe(boundary, 2)
        with self.assertRaises(AssertionError):
            observe(boundary, 3, (HELPER,))
        with self.assertRaises(AssertionError):
            observe(boundary, 3)

    def test_disappearance_permanently_revokes_helper(self):
        boundary = ready_boundary()
        observe(boundary, 2, (HELPER,))
        observe(boundary, 3)
        with self.assertRaises(AssertionError):
            observe(boundary, 4, (HELPER,))
        with self.assertRaises(AssertionError):
            observe(boundary, 4)

    def test_replacement_and_wrong_uid_refuse_stickily(self):
        for row in ((702, 10311, q.TEST), (701, 10310, q.TEST)):
            with self.subTest(row=row):
                boundary = ready_boundary()
                observe(boundary, 2, (HELPER,))
                with self.assertRaises(AssertionError):
                    observe(boundary, 3, (row,))
                with self.assertRaises(AssertionError):
                    observe(boundary, 3, (HELPER,))

    def test_no_target_service_provider_or_foreign_authority(self):
        rows = ((601, 10310, q.APP), (602, 10310, c.SERVICE),
                (603, 10311, c.PROVIDER), (604, 10311, q.TEST + ":unknown"),
                (605, 10310, "org.locallore.foreign"),
                (606, 10311, "org.locallore.old.test:chooser_test_provider"))
        for row in rows:
            with self.subTest(row=row):
                boundary = ready_boundary()
                with self.assertRaises(AssertionError):
                    observe(boundary, 2, (row,))
                with self.assertRaises(AssertionError):
                    observe(boundary, 2, (HELPER,))

    def test_two_helpers_and_duplicate_pid_or_name_refuse(self):
        for rows in ((HELPER, (702, 10311, q.TEST)),
                     (HELPER, (701, 10310, q.APP)),
                     (HELPER, (702, 10310, q.APP))):
            with self.subTest(rows=rows):
                with self.assertRaises(AssertionError):
                    observe(ready_boundary(), 2, rows)

    def test_before_and_installed_must_be_empty(self):
        for index in (0, 1):
            with self.subTest(index=index):
                boundary = q.ProcessBoundary()
                if index:
                    observe(boundary, 0)
                with self.assertRaises((AssertionError, KeyError)):
                    observe(boundary, index, (HELPER,))
                with self.assertRaises(AssertionError):
                    observe(boundary, index)

    def test_wrong_after_initial_order_stage_count_and_types_are_sticky(self):
        changes = ({"label": "final"}, {"stage": "instrumentation"}, {"methods": 0},
                   {"methods": 2}, {"methods": True}, {"methods": 1.0},
                   {"label": b"after-initial"}, {"stage": None})
        for change in changes:
            with self.subTest(change=change):
                boundary = ready_boundary()
                with self.assertRaises(AssertionError):
                    observe(boundary, 2, (HELPER,), **change)
                with self.assertRaises(AssertionError):
                    observe(boundary, 2, (HELPER,))
        with self.assertRaises(AssertionError):
            observe(q.ProcessBoundary(), 1)

    def test_uid_maps_are_closed_typed_and_distinct(self):
        bad = (None, [], {}, {q.APP: 10310}, dict(UIDS, foreign=10312),
               {q.APP: 10310, q.TEST: 10310}, {q.APP: True, q.TEST: 10311},
               {q.APP: 10310, q.TEST: 10311.0}, {q.APP: 9999, q.TEST: 10311},
               {q.APP: 10310, q.TEST: 2 ** 31})
        for uids in bad:
            with self.subTest(uids=uids):
                boundary = q.ProcessBoundary()
                observe(boundary, 0)
                with self.assertRaises(AssertionError):
                    boundary.observe(processes(), uids, label="installed", stage="installed", methods=0)
                with self.assertRaises(AssertionError):
                    observe(boundary, 1)
        with self.assertRaises(AssertionError):
            q.ProcessBoundary().observe(processes(), UIDS, label="before", stage="before", methods=0)

    def test_malformed_ps_refuses_without_recovery(self):
        for raw in (b"", b"PID UID CMD\n", b"PID UID NAME\n-1 10311 bad\n",
                    b"PID UID NAME\n701 10311 " + q.TEST.encode() + b" extra\n"):
            boundary = ready_boundary()
            with self.subTest(raw=raw), self.assertRaises(AssertionError):
                boundary.observe(raw, UIDS, label="after-initial", stage="after", methods=1)
            with self.assertRaises(AssertionError):
                observe(boundary, 2)

    def test_shared_parser_stays_strict_and_does_not_classify_helper(self):
        expected = dict(pid=701, uid=10311, name=q.TEST)
        self.assertEqual(c.parse_processes(processes(HELPER), UIDS, {}),
                         {"owned": [expected], "passive": []})
        for name, uid in ((q.APP, 10310), (c.SERVICE, 10310), (c.PROVIDER, 10311)):
            self.assertEqual(c.parse_processes(processes((702, uid, name)), UIDS, {})["owned"],
                             [dict(pid=702, uid=uid, name=name)])
        for row in ((701, 10310, q.TEST), (702, 10311, "org.locallore.other")):
            with self.assertRaises(AssertionError):
                c.parse_processes(processes(row), UIDS, {})


class ReceiptSetupHelperCohortTests(unittest.TestCase):
    def run_mock(self, snapshots, check, **flags):
        with tempfile.TemporaryDirectory() as directory:
            value = fixture.proposal(Path(directory))
            lease = fixture.Lease(value)
            transport = HelperTransport(value, lease, snapshots)
            for key, flag in flags.items():
                setattr(transport, key, flag)
            owner = q.Owner(value, lease)
            with patch.object(q.host, "run_process", side_effect=transport), patch.object(
                    q.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                check(owner, transport)

    def assert_raw_retained(self, owner, transport):
        raw_path = owner.commands / ("command-%04d.stdout.bin" % owner.count)
        self.assertTrue(raw_path.is_file())
        receipt = json.loads(raw_path.with_suffix("").with_suffix(".json").read_bytes())
        self.assertEqual(receipt["stdout_sha256"], q.sha(raw_path.read_bytes()))
        self.assertEqual(owner.count, len(transport.calls))

    def test_complete_cohort_keeps_same_helper_separate_from_target(self):
        def check(owner, transport):
            result = q.run_cohort(owner)
            self.assertEqual((transport.installs, transport.instruments, transport.ps_count), (2, 2, 5))
            self.assertEqual((result["initial_tests"]["passed"], result["restart_test"]["passed"]), (3, 1))
            for facts in (result["after_initial"], result["final"]):
                self.assertEqual(facts["version"], 2)
                self.assertEqual(facts["processes"], {"target": [], "test_helper":
                                 [dict(pid=701, uid=10311, name=q.TEST)]})
            self.assertFalse(result["real_model_or_SDK_qualified"])
            self.assertEqual(sum(len(p["checks"]) for p in result["proofs"].values()), 44)
            self.assertTrue(owner.clean)
        self.run_mock([(), (), (HELPER,), (HELPER,), (HELPER,)], check)

    def test_complete_cohort_allows_natural_disappearance_without_stop(self):
        def check(owner, transport):
            result = q.run_cohort(owner)
            self.assertEqual(result["after_initial"]["processes"]["test_helper"][0]["pid"], 701)
            self.assertEqual(result["final"]["processes"], {"target": [], "test_helper": []})
            self.assertEqual(transport.instruments, 2)
            self.assertFalse(any("force-stop" in cmd or "clear" in cmd or "uninstall" in cmd
                                 for command, _ in transport.calls for cmd in command))
        self.run_mock([(), (), (HELPER,), (), ()], check)

    def test_pretest_processes_refuse_before_any_instrumentation(self):
        for snapshots, installs in (([(HELPER,)], 0), ([(), (HELPER,)], 2)):
            def check(owner, transport):
                with self.assertRaises((AssertionError, KeyError)):
                    q.run_cohort(owner)
                self.assertEqual((transport.installs, transport.instruments), (installs, 0))
                self.assert_raw_retained(owner, transport)
            with self.subTest(installs=installs):
                self.run_mock(snapshots, check)

    def test_surviving_app_service_provider_or_foreign_refuses_restart(self):
        for row in ((601, 10310, q.APP), (602, 10310, c.SERVICE),
                    (603, 10311, c.PROVIDER), (604, 10311, "org.locallore.foreign")):
            def check(owner, transport):
                with self.assertRaises(AssertionError):
                    q.run_cohort(owner)
                self.assertEqual(transport.instruments, 1)
                self.assertEqual(transport.ps_count, 3)
                self.assert_raw_retained(owner, transport)
                self.assertIn(row[2].encode(), (owner.commands / ("command-%04d.stdout.bin" % owner.count)).read_bytes())
                self.assertFalse((owner.directory / "after-initial-facts.json").exists())
                self.assertFalse((owner.directory / "restart-instrumentation-v1.json").exists())
                self.assertNotIn(q.RESTART_INSTRUMENT, [tuple(shlex.split(cmd[4]))
                    for cmd, _ in transport.calls if cmd[3] == "shell"])
            with self.subTest(row=row):
                self.run_mock([(), (), (row,)], check)

    def test_replacement_late_appearance_and_reappearance_stop_without_retry(self):
        cases = ([(), (), (HELPER,), ((702, 10311, q.TEST),)],
                 [(), (), (), (HELPER,)], [(), (), (HELPER,), (), (HELPER,)])
        for snapshots in cases:
            def check(owner, transport):
                with self.assertRaises(AssertionError):
                    q.run_cohort(owner)
                self.assertEqual(transport.instruments, 2)
                self.assertEqual(transport.ps_count, len(snapshots))
                self.assert_raw_retained(owner, transport)
                self.assertFalse((owner.directory / "final-facts.json").exists())
                ops = [tuple(shlex.split(cmd[4])) for cmd, _ in transport.calls if cmd[3] == "shell"]
                self.assertEqual(ops.count(q.INITIAL_INSTRUMENT), 1)
                self.assertEqual(ops.count(q.RESTART_INSTRUMENT), 1)
            with self.subTest(snapshots=snapshots):
                self.run_mock(snapshots, check)

    def test_initial_failure_never_reaches_helper_binding_or_restart(self):
        def check(owner, transport):
            with self.assertRaises(AssertionError):
                q.run_cohort(owner)
            self.assertEqual((transport.ps_count, transport.instruments), (2, 1))
            self.assert_raw_retained(owner, transport)
            self.assertFalse((owner.directory / "after-initial-facts.json").exists())
        self.run_mock([(), (), (HELPER,)], check, bad_initial=True)

    def test_helper_ps_owner_loss_and_uncertain_cleanup_stop_after_raw(self):
        for flag in ("lose_owner_at", "fail_cleanup_at"):
            def check(owner, transport):
                with self.assertRaises((AssertionError, RuntimeError)):
                    q.run_cohort(owner)
                self.assertEqual((transport.ps_count, transport.instruments), (3, 1))
                self.assert_raw_retained(owner, transport)
                before = len(transport.calls)
                with self.assertRaises((AssertionError, RuntimeError)):
                    owner.shell(c.PS)
                self.assertEqual(len(transport.calls), before)
            with self.subTest(flag=flag):
                self.run_mock([(), (), (HELPER,)], check, **{flag: 3})


if __name__ == "__main__":
    unittest.main()
