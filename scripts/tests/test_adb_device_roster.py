"""Original synthetic held-roster fixtures; no service or device authority.

The legacy version witness and new roster verdict both use real pure validators.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import unittest

from benchmarks import adb_device_roster as roster
from benchmarks import adb_held_socket as legacy
from scripts.tests import test_adb_held_socket as held


BODY = (b'ORIGINAL_USB device usb:1-2 product:fixture model:Original_Model '
        b'device:fixture transport_id:7\n')


def admission():
    value = held.admission()
    value['protocol'] = 'adb-held-device-roster-v1'
    return value


def frame(body=BODY):
    return b'OKAY'+('%04x' % len(body)).encode('ascii')+body


def version_proof():
    value = legacy.probe(held.FakeBackend(), held.admission())
    if not legacy.report_verified(value, held.admission()):
        raise AssertionError('original version fixture is not valid')
    return value


class RosterBackend(held.FakeBackend):
    def __init__(self, body=BODY, chunks=None, **kwargs):
        super().__init__(chunks=[frame(body), b''] if chunks is None else chunks, **kwargs)
        self.received = []

    def send(self, data, deadline):
        if data != b'000Ehost:devices-l':
            raise AssertionError('not the one fixed roster request')
        super().send(data, deadline)

    def recv(self, limit, deadline):
        value = super().recv(limit, deadline)
        if len(value) > limit:
            self.chunks.insert(0, value[limit:])
            value = value[:limit]
        self.received.append(value)
        return value


class DeviceRosterTests(unittest.TestCase):
    def refused(self, action):
        with self.assertRaises(roster.RosterRefused):
            action()

    def test_admission_translation_is_fixed_and_independent(self):
        selected = admission()
        self.assertEqual(roster.validate_admission(selected), selected)
        translated = roster.backend_admission(selected)
        self.assertEqual(translated, held.admission())
        translated['server']['pid'] += 1
        self.assertEqual(selected, admission())
        for change in (dict(protocol=legacy.PROTOCOL), dict(version=True),
                       dict(expected_version='002A'), dict(command='host:devices'),
                       dict(target='ORIGINAL_USB')):
            changed = admission(); changed.update(change)
            self.refused(lambda: roster.validate_admission(changed))

    def test_version_and_roster_are_distinct_one_shot_exchanges(self):
        backend = RosterBackend()
        version = version_proof()
        value = roster.probe(backend, admission(), version)
        self.assertEqual(value['status'], 'observed')
        self.assertIsNone(value['reason'])
        self.assertTrue(roster.report_verified(value, admission()))
        self.assertEqual(value['version_proof'], version)
        self.assertEqual(value['rows'], roster.parse_devices(BODY))
        self.assertFalse(value['feature_acceptance'])
        self.assertEqual(backend.sent, [b'000Ehost:devices-l'])
        self.assertEqual([backend.counts[name] for name in ('open', 'connect', 'send', 'snapshot', 'close')],
                         [1, 1, 1, 3, 1])
        self.assertTrue(backend.closed)

    def test_invalid_version_is_not_embedded_or_followed_by_new_open(self):
        for version in (None, {}, {'private': 'PRIVATE_CANARY'},
                        {**version_proof(), 'ownership_verified': False},
                        {**version_proof(), 'response_hex': b'OKAY0004002a'.hex()}):
            backend = RosterBackend()
            with self.subTest(version_type=type(version).__name__):
                value = roster.probe(backend, admission(), version)
                self.assertEqual(value['status'], 'refused')
                self.assertIsNone(value['version_proof'])
                self.assertIsNone(value['rows'])
                self.assertEqual(backend.counts['open'], 0)
                self.assertEqual(backend.counts['connect'], 0)
                self.assertEqual(backend.sent, [])
                self.assertTrue(backend.closed)
                self.assertFalse(roster.report_verified(value, admission()))

    def test_same_actual_client_identity_is_required_before_connect(self):
        for key, value in (('pid', held.CLIENT_PID+1), ('creation_filetime', 223456790),
                           ('executable', 'D:\\Synthetic\\foreign-client.exe')):
            backend = RosterBackend()
            for bracket in backend.brackets:
                bracket['client'][key] = value
            with self.subTest(field=key):
                report = roster.probe(backend, admission(), version_proof())
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(backend.counts['connect'], 0)
                self.assertEqual(backend.sent, [])
                self.assertTrue(backend.closed)

    def test_fragmented_frame_and_empty_roster_require_exact_eof(self):
        for body in (BODY, b''):
            reply = frame(body)
            backend = RosterBackend(chunks=[reply[i:i+1] for i in range(len(reply))]+[b''])
            report = roster.probe(backend, admission(), version_proof())
            self.assertTrue(roster.report_verified(report, admission()))
            self.assertEqual(report['response_hex'], reply.hex())
            self.assertEqual(report['rows'], roster.parse_devices(body))
            self.assertTrue(report['response_complete'])
            self.assertEqual(backend.sent, [roster.REQUEST])

    def test_framing_refusal_retains_exact_partial_bytes_and_never_rows(self):
        invalid = [b'FAIL0004oops', b'OKAY000x', b'OKAY0004abc', frame()+b'X',
                   b'OKAY0000\n', b'OKAY', b'NOPE0000']
        for reply in invalid:
            backend = RosterBackend(chunks=[reply, b''])
            with self.subTest(reply=reply[:12]):
                report = roster.probe(backend, admission(), version_proof())
                self.assertEqual(report['status'], 'refused')
                self.assertIsNone(report['rows'])
                self.assertEqual(bytes.fromhex(report['response_hex']), b''.join(backend.received))
                self.assertTrue(reply.startswith(bytes.fromhex(report['response_hex'])))
                self.assertFalse(roster.report_verified(report, admission()))
                self.assertTrue(backend.closed)
                self.assertEqual(backend.counts['send'], 1)

    def test_timeout_cancel_and_unknown_cleanup_preserve_refusal_without_retries(self):
        for fault in ('timeout', 'cancel', 'close'):
            backend = RosterBackend(chunks=None if fault == 'close' else [b'OKAY0005abc'])
            if fault == 'timeout': backend.empty_error = TimeoutError('PRIVATE_CANARY')
            elif fault == 'cancel': backend.empty_error = KeyboardInterrupt('PRIVATE_CANARY')
            else: backend.close_result['socket_closed'] = None
            with self.subTest(fault=fault):
                report = roster.probe(backend, admission(), version_proof())
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(bytes.fromhex(report['response_hex']), b''.join(backend.received))
                self.assertEqual(backend.counts['send'], 1)
                self.assertEqual(backend.counts['connect'], 1)
                self.assertEqual(backend.counts['close'], 1)
                self.assertNotIn('PRIVATE_CANARY', str(report['reason']))
                self.assertFalse(roster.report_verified(report, admission()))

    def test_client_raw_state_is_preserved_while_server_state_must_be_established(self):
        for state in (0, 1, 5, 14, 2**32-1):
            backend = RosterBackend(client_state=state)
            report = roster.probe(backend, admission(), version_proof())
            self.assertTrue(roster.report_verified(report, admission()))
            self.assertEqual(report['client_raw_state'], state)
        for state in (0, 1, 2, 4, 6, 14):
            backend = RosterBackend(server_state=state)
            report = roster.probe(backend, admission(), version_proof())
            self.assertEqual(report['status'], 'refused')
            self.assertEqual(backend.sent, [])

    def test_rows_must_be_replayed_from_exact_response_and_embedded_version(self):
        report = roster.probe(RosterBackend(), admission(), version_proof())
        for mutate in (lambda v: v['rows'][0].update(serial='BORROWED'),
                       lambda v: v.update(response_hex=frame(b'').hex()),
                       lambda v: v['version_proof'].update(socket_closed=False),
                       lambda v: v.update(elapsed_ms=True),
                       lambda v: v.update(rows=[]),
                       lambda v: v.update(feature_acceptance=True)):
            changed = copy.deepcopy(report); mutate(changed)
            with self.subTest(mutation=mutate):
                self.assertIs(roster.report_verified(changed, admission()), False)
        for malformed in (None, True, [], {'private': object()}):
            self.assertIs(roster.report_verified(malformed, admission()), False)

    def test_response_limit_and_deadline_do_not_turn_into_another_request(self):
        backend = RosterBackend(chunks=[b'OKAYffff'+b'x'*65536, b''])
        report = roster.probe(backend, admission(), version_proof())
        self.assertEqual(report['status'], 'refused')
        self.assertLessEqual(len(bytes.fromhex(report['response_hex'])), 65544)
        self.assertEqual(backend.sent, [roster.REQUEST])
        self.assertTrue(all(type(limit) is int and 0 < limit <= 65544 for limit in backend.recv_limits))
        backend = RosterBackend(); backend.jumps[('bracket', 1)] = 3.1
        report = roster.probe(backend, admission(), version_proof())
        self.assertEqual(report['status'], 'refused')
        self.assertEqual(backend.sent, [])


if __name__ == '__main__':
    unittest.main()
