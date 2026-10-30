"""Original native-byte closing-row oracles; no sockets or device operations.

History is derived only from the actual pure version proof in this fixture.
It never grants acquisition authority or replaces the live ownership join.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import unittest

from benchmarks import adb_device_roster as roster
from scripts.tests import test_adb_device_roster as original
from scripts.tests import test_adb_held_socket as held


CURRENT_PORT = 43002


def closing_row(**changes):
    values = dict(local='127.0.0.1', local_port=5037, remote='127.0.0.1',
                  remote_port=held.CLIENT_PORT, state=11, pid=0)
    values.update(changes)
    return held.row4(**values)


class HistoryBackend(original.RosterBackend):
    def __init__(self, history=None, phases=(0, 1, 2), *, current_port=CURRENT_PORT, live_server=True):
        super().__init__()
        history = [(2, closing_row())] if history is None else history
        for endpoint in self.endpoints:
            endpoint['local_port'] = current_port
        self.snapshots = []
        for phase in range(3):
            v4, v6 = [held.row4()], []
            if phase in phases:
                for family, row in history:
                    (v4 if family == 2 else v6).append(row)
            if phase:
                if live_server:
                    v4.append(held.row4(remote='127.0.0.1', remote_port=current_port, state=5))
                v4.append(held.row4(local_port=current_port, remote='127.0.0.1', remote_port=5037,
                                    state=0, pid=held.CLIENT_PID))
            self.snapshots.append(held.snapshot(tuple(v4), v6=tuple(v6)))


class DeviceRosterHistoryTests(unittest.TestCase):
    def test_exact_closed_version_tuple_is_retained_at_every_roster_snapshot(self):
        for phases in ((0,), (1,), (2,), (0, 1, 2)):
            with self.subTest(phases=phases):
                backend = HistoryBackend(phases=phases)
                native_before = [[table.raw for table in snapshot.tables] for snapshot in backend.snapshots]
                version = original.version_proof()
                version_before = copy.deepcopy(version)
                report = roster.probe(backend, original.admission(), version)
                self.assertEqual(report['status'], 'observed')
                self.assertTrue(roster.report_verified(report, original.admission()))
                self.assertEqual(backend.sent, [roster.REQUEST])
                self.assertEqual([backend.counts[name] for name in ('connect', 'send', 'snapshot', 'close')],
                                 [1, 1, 3, 1])
                self.assertEqual(version, version_before)
                self.assertEqual([[table.raw for table in snapshot.tables] for snapshot in backend.snapshots], native_before)
                stages = [stage for stage in report['stages'] if 'snapshot' in stage]
                for phase, stage in enumerate(stages):
                    matching = [row for row in stage['snapshot']['rows'] if row['raw_hex'] == closing_row().hex()]
                    self.assertEqual(len(matching), int(phase in phases))
                    if matching:
                        self.assertEqual(matching[0]['row']['state'], 11)
                        self.assertEqual(matching[0]['row']['pid'], 0)
                self.assertEqual(report['client_raw_state'], 0)
                self.assertFalse(report['feature_acceptance'])

    def test_unknown_wrong_tuple_state_pid_family_or_scope_refuses_before_send(self):
        bad = [(2, closing_row(remote_port=held.CLIENT_PORT+1)),
               (2, closing_row(local='0.0.0.0')), (2, closing_row(remote='127.0.0.2'))]
        bad += [(2, closing_row(state=state)) for state in (0, 1, 2, 5, 10, 12, 0xffffffff)]
        bad += [(2, closing_row(pid=pid)) for pid in (1, held.CLIENT_PID, held.SERVER_PID+7)]
        bad += [(23, held.row6(remote='::1', remote_port=held.CLIENT_PORT, state=11, pid=0, scope_id=scope))
                for scope in (0, 1)]
        for index, row in enumerate(bad):
            with self.subTest(row=index):
                backend = HistoryBackend(history=[row], phases=(0,))
                report = roster.probe(backend, original.admission(), original.version_proof())
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(backend.sent, [])
                self.assertEqual(backend.counts['connect'], 0)
                self.assertTrue(backend.closed)

    def test_duplicate_history_and_unrelated_second_pid_zero_row_are_not_ignored(self):
        for rows in ([(2, closing_row()), (2, closing_row())],
                     [(2, closing_row()), (2, closing_row(remote_port=49991))]):
            with self.subTest(rows=rows):
                backend = HistoryBackend(history=rows, phases=(0,))
                report = roster.probe(backend, original.admission(), original.version_proof())
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(backend.sent, [])
                self.assertEqual(backend.counts['connect'], 0)

    def test_partial_unclosed_foreign_or_changed_version_proof_cannot_authorize_history(self):
        for mutation in ('socket', 'handles', 'partial', 'tuple', 'worker'):
            with self.subTest(mutation=mutation):
                version = original.version_proof()
                backend = HistoryBackend(phases=(0,))
                if mutation == 'socket': version['socket_closed'] = False
                elif mutation == 'handles': version['process_handles_closed'] = False
                elif mutation == 'partial': version['stages'].pop()
                elif mutation == 'tuple': version['stages'][1]['endpoint']['local_port'] += 1
                else:
                    for bracket in backend.brackets:
                        bracket['client']['creation_filetime'] += 1
                report = roster.probe(backend, original.admission(), version)
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(backend.sent, [])
                self.assertEqual(backend.counts['connect'], 0)

    def test_closed_tuple_cannot_replace_live_established_server_when_port_is_reused(self):
        backend = HistoryBackend(current_port=held.CLIENT_PORT, live_server=False)
        report = roster.probe(backend, original.admission(), original.version_proof())
        self.assertEqual(report['status'], 'refused')
        self.assertEqual(backend.sent, [])
        self.assertFalse(report['request_sent'])
        self.assertFalse(roster.report_verified(report, original.admission()))
        self.assertTrue(backend.closed)


if __name__ == '__main__':
    unittest.main()
