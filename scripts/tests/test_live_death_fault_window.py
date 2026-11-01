"""Original finite fault-window plumbing; shell IO is synthetic, verdicts are real.

These tests confer no SDK authority and perform no process or device operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import unittest
from unittest.mock import patch

from benchmarks import android_live_death_witness as witness
from benchmarks import original_author_live_death_controller as controller
from scripts.tests import test_live_process_death_witness as fixtures


class PendingAuthor:
    def __init__(self, fail_at=None):
        self.calls = 0
        self.fail_at = fail_at

    def require_pending(self):
        self.calls += 1
        if self.calls == self.fail_at:
            raise RuntimeError('synthetic author already terminal')


class LiveDeathFaultWindowTests(unittest.TestCase):
    def setUp(self):
        self.checkpoint = witness.validate_checkpoint(fixtures.raw(fixtures.checkpoint()),
            expected_process=fixtures.PROCESS, **fixtures.PINS)
        self.cap, self.live = object(), object()
        self.pending = PendingAuthor()
        self.calls = []
        self.before = fixtures.packet()
        self.after = fixtures.packet('absent', fixtures.READY + 2)
        self.stop = b''
        self.fail_label = None
        self.pins = {label: dict(path='D:/Synthetic/' + label + '.json', bytes=9,
                                sha256=str(index) * 64)
                     for index, label in enumerate(('live-process-before', 'live-force-stop',
                                                     'live-process-after'), 1)}

    def shell(self, cap, live, argv, label, *, seconds=20, limit=4096):
        self.assertIs(cap, self.cap)
        self.assertIs(live, self.live)
        self.assertEqual((seconds, limit), (20, 4096))
        self.calls.append((list(argv), label))
        if label == self.fail_label:
            raise RuntimeError('synthetic uncertain shell completion')
        raw = (fixtures.raw(self.before) if label == 'live-process-before' else
               fixtures.raw(self.after) if label == 'live-process-after' else self.stop)
        return raw, copy.deepcopy(self.pins[label])

    def run_window(self):
        with patch.object(controller, '_shell', self.shell):
            return controller._fault_window(self.cap, self.live, self.pending,
                                            self.checkpoint, fixtures.BOOT)

    def labels(self):
        return [label for _, label in self.calls]

    def test_matching_alive_then_gone_has_one_exact_stop_and_opaque_record_bindings(self):
        for final_state in ('absent', 'exited'):
            with self.subTest(final_state=final_state):
                self.calls.clear(); self.pending = PendingAuthor()
                self.after = fixtures.packet(final_state, fixtures.READY + 2)
                before = copy.deepcopy(self.checkpoint)
                result = self.run_window()
                self.assertEqual(set(result), {'before', 'after', 'probe_before', 'force_stop', 'probe_after'})
                self.assertEqual(result['before'], self.before)
                self.assertEqual(result['after'], self.after)
                for key, label in (('probe_before', 'live-process-before'),
                                   ('force_stop', 'live-force-stop'), ('probe_after', 'live-process-after')):
                    self.assertEqual(result[key], self.pins[label])
                native = [controller.c6.PROCESS_PROBE, '--snapshot-v2',
                          str(fixtures.PROCESS['pid']), str(fixtures.PROCESS['uid'])]
                self.assertEqual(self.calls, [(native, 'live-process-before'),
                    (['am', 'force-stop', '--user', '0', 'org.locallore.app.litertverify'], 'live-force-stop'),
                    (native, 'live-process-after')])
                self.assertEqual(self.pending.calls, 2)
                self.assertEqual(self.checkpoint, before)

    def test_bad_before_witness_prevents_any_force_stop_or_later_probe(self):
        mutations = [lambda v: v.update(state='absent', observed_uid=None, start_ticks=None,
                         pidfd_opened=False, pidfd_closed=None, proc_opened=False,
                         proc_closed=None, poll_revents=None, errno=3),
                     lambda v: v.update(state='exited', poll_revents=1),
                     lambda v: v.update(state='refused', error='proc_race', errno=3)]
        mutations += [lambda v, k=k, x=x: v.update({k: x}) for k, x in (
            ('start_ticks', fixtures.TICKS + 1), ('expected_uid', fixtures.PROCESS['uid'] + 1),
            ('pid', fixtures.PROCESS['pid'] + 1), ('proc_closed', None),
            ('pidfd_closed', False), ('observed_boottime_ns', fixtures.EXPIRES - 59_999_999_999),
            ('boot_id', '11223344-5566-7788-99aa-bbccddeeff00'))]
        for index, mutate in enumerate(mutations):
            self.calls.clear(); self.pending = PendingAuthor(); self.before = fixtures.packet()
            mutate(self.before)
            with self.subTest(mutation=index), self.assertRaises(witness.LiveDeathRefused):
                self.run_window()
            self.assertEqual(self.labels(), ['live-process-before'])
            self.assertEqual(self.pending.calls, 1)

    def test_author_completion_blocks_before_or_immediately_before_stop(self):
        for fail_at, expected in ((1, []), (2, ['live-process-before'])):
            self.calls.clear(); self.pending = PendingAuthor(fail_at)
            with self.subTest(fail_at=fail_at), self.assertRaises(Exception):
                self.run_window()
            self.assertEqual(self.labels(), expected)
            self.assertEqual(self.pending.calls, fail_at)

    def test_nonempty_stop_output_is_not_repaired_or_followed_by_after_probe(self):
        for output in (b'\n', b'Success\n', b'uncertain\x00\x1a'):
            self.calls.clear(); self.pending = PendingAuthor(); self.stop = output
            with self.subTest(output=output), self.assertRaises(Exception):
                self.run_window()
            self.assertEqual(self.labels(), ['live-process-before', 'live-force-stop'])

    def test_bad_after_witness_refuses_without_retry_or_new_stop(self):
        for state, changes in (('alive', {}), ('exited', {'start_ticks': fixtures.TICKS + 1}),
                               ('exited', {'pidfd_closed': None}),
                               ('absent', {'observed_boottime_ns': fixtures.READY + 1}),
                               ('absent', {'observed_boottime_ns': fixtures.EXPIRES}),
                               ('absent', {'boot_id': '11223344-5566-7788-99aa-bbccddeeff00'})):
            self.calls.clear(); self.pending = PendingAuthor()
            self.after = fixtures.packet(state, fixtures.READY + 2); self.after.update(changes)
            with self.subTest(state=state, changes=changes), self.assertRaises(witness.LiveDeathRefused):
                self.run_window()
            self.assertEqual(self.labels(), ['live-process-before', 'live-force-stop', 'live-process-after'])

    def test_uncertain_shell_call_stops_at_that_operation_without_retry(self):
        labels = ['live-process-before', 'live-force-stop', 'live-process-after']
        for index, label in enumerate(labels):
            self.calls.clear(); self.pending = PendingAuthor(); self.fail_label = label
            with self.subTest(label=label), self.assertRaises(Exception):
                self.run_window()
            self.assertEqual(self.labels(), labels[:index + 1])


if __name__ == '__main__':
    unittest.main()
