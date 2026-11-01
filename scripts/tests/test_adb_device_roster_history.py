"""Original native-byte closing-row oracles; no sockets or device operations.

History is derived only from the actual pure version proof in this fixture.
It never grants acquisition authority or replaces the live ownership join.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import unittest

from benchmarks import adb_device_roster as roster
from benchmarks import adb_held_socket as legacy
from scripts.tests import test_adb_device_roster as original
from scripts.tests import test_adb_held_socket as held


CURRENT_PORT = 43002


def closing_row(**changes):
    values = dict(local='127.0.0.1', local_port=5037, remote='127.0.0.1',
                  remote_port=held.CLIENT_PORT, state=11, pid=0)
    values.update(changes)
    return held.row4(**values)


def native_rows(*v4, v6=()):
    captured = held.snapshot(v4, v6=v6)
    return [row for table in captured.tables for row in legacy.decode_table(table.raw, table.family)]


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

    def completed(self, version=None, current_port=CURRENT_PORT):
        version = original.version_proof() if version is None else version
        value = roster.probe(HistoryBackend(history=[], current_port=current_port), original.admission(), version)
        self.assertTrue(roster.report_verified(value, original.admission()))
        return value

    def test_post_readback_accepts_only_the_two_qualified_completed_endpoints(self):
        version = original.version_proof()
        completed = self.completed(version)
        rows = native_rows(held.row4(), closing_row(), closing_row(remote_port=CURRENT_PORT))
        before = copy.deepcopy(rows)
        with self.assertRaises(roster.RosterRefused):
            roster.validate_candidates(rows, original.admission(), version)
        self.assertIsNone(roster.validate_candidates(rows, original.admission(), version, completed))
        self.assertEqual(rows, before)
        self.assertEqual([(row.pid, row.state) for row in rows], [(held.SERVER_PID, 0), (0, 11), (0, 11)])
        self.assertIsNone(roster.validate_candidates(native_rows(held.row4()), original.admission()))
        with self.assertRaises(roster.RosterRefused):
            roster.validate_candidates(rows, original.admission())

    def test_completed_report_requires_closed_verdict_and_exact_embedded_version(self):
        version = original.version_proof()
        completed = self.completed(version)
        rows = native_rows(held.row4(), closing_row(), closing_row(remote_port=CURRENT_PORT))
        for key, value in (('socket_closed', False), ('process_handles_closed', None),
                           ('status', 'refused'), ('ownership_verified', False)):
            bad = copy.deepcopy(completed); bad[key] = value
            with self.subTest(field=key), self.assertRaises(roster.RosterRefused):
                roster.validate_candidates(rows, original.admission(), version, bad)
        other_version = legacy.probe(held.FakeBackend(client_state=1), held.admission())
        self.assertTrue(legacy.report_verified(other_version, held.admission()))
        other_completed = self.completed(other_version)
        with self.assertRaises(roster.RosterRefused):
            roster.validate_candidates(rows, original.admission(), version, other_completed)
        with self.assertRaises(roster.RosterRefused):
            roster.validate_candidates(rows, original.admission(), None, completed)
        bad_version = copy.deepcopy(version); bad_version['socket_closed'] = False
        with self.assertRaises(roster.RosterRefused):
            roster.validate_candidates(rows, original.admission(), bad_version, completed)
        backend = HistoryBackend()
        refused = roster.probe(backend, original.admission(), bad_version)
        self.assertEqual(refused['status'], 'refused')
        self.assertEqual(backend.counts['open'], 0)
        self.assertEqual(backend.sent, [])

    def test_post_history_refuses_unknown_extra_duplicates_state_pid_family_and_scope(self):
        version = original.version_proof(); completed = self.completed(version)
        bad = [(2, closing_row(remote_port=49992)), (2, closing_row()),
               (2, closing_row(remote_port=CURRENT_PORT, pid=held.CLIENT_PID))]
        bad += [(2, closing_row(remote_port=CURRENT_PORT, state=state)) for state in (0, 5, 10, 12)]
        bad += [(23, held.row6(remote='::1', remote_port=CURRENT_PORT, state=11, pid=0, scope_id=scope))
                for scope in (0, 1)]
        for index, (family, row) in enumerate(bad):
            rows = native_rows(held.row4(), closing_row(), closing_row(remote_port=CURRENT_PORT),
                               *([row] if family == 2 else []), v6=([row] if family == 23 else []))
            with self.subTest(row=index), self.assertRaises(roster.RosterRefused):
                roster.validate_candidates(rows, original.admission(), version, completed)

    def test_equal_completed_endpoints_deduplicate_permission_not_raw_rows(self):
        version = original.version_proof()
        completed = self.completed(version, current_port=held.CLIENT_PORT)
        rows = native_rows(held.row4(), closing_row())
        self.assertIsNone(roster.validate_candidates(rows, original.admission(), version, completed))
        duplicate = native_rows(held.row4(), closing_row(), closing_row())
        with self.assertRaises(roster.RosterRefused):
            roster.validate_candidates(duplicate, original.admission(), version, completed)


if __name__ == '__main__':
    unittest.main()
