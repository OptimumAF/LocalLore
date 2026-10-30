"""Original synthetic held-roster fixtures; no service or device authority.

The legacy version witness and new roster verdict both use real pure validators.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from dataclasses import asdict
import hashlib
import json
import struct
import unittest

from benchmarks import adb_device_roster as roster
from benchmarks import adb_held_socket as legacy
from scripts.tests import test_adb_held_socket as held


BODY = (b'ORIGINAL_USB'.ljust(22, b' ')+b' device usb:1-2 product:fixture model:Original_Model '
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


def device_row(serial='ORIGINAL_USB', state='device', transport_id=7, *,
               devpath=None, product=None, model=None, device=None):
    """Original byte-width %-22s producer fixture, independent of the parser."""
    value = serial.encode('utf-8').ljust(22, b' ')+b' '+state.encode('utf-8')
    if devpath is not None:
        value += b' '+devpath.encode('utf-8')
    for key, text in (('product', product), ('model', model), ('device', device)):
        if text is not None:
            value += (' '+key+':'+text).encode('utf-8')
    return value+(' transport_id:'+str(transport_id)+'\n').encode('ascii')


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

    def test_parser_retains_untrusted_network_emulator_and_unicode_metadata(self):
        specifications = [dict(serial='ORIGINAL_USB', state='device', transport_id=7,
            devpath='usb:1-2', product='original café product', model='Original_Model', device='original device'),
            dict(serial='192.0.2.11:5555', state='offline', transport_id=8),
            dict(serial='emulator-7770', state='connecting', transport_id=9),
            dict(serial='原創端末', state='unauthorized', transport_id=10, devpath='usb:3-1')]
        body = b''.join(device_row(**specification) for specification in specifications)
        expected = [dict(serial=None, state=None, devpath=None, product=None, model=None, device=None,
                         transport_id=None) for _ in specifications]
        for row, specification in zip(expected, specifications): row.update(specification)
        actual = roster.parse_devices(body)
        self.assertEqual(actual, expected)
        actual[0]['product'] = 'changed'
        self.assertEqual(roster.parse_devices(body), expected)
        self.assertEqual(roster.parse_devices(b''), [])
        for state in ('offline', 'bootloader', 'device', 'host', 'recovery', 'rescue',
                      'sideload', 'unauthorized', 'authorizing', 'connecting', 'detached', 'any'):
            self.assertEqual(roster.parse_devices(device_row(state=state))[0]['state'], state)

    def test_parser_preserves_complete_no_permissions_and_missing_serial_placeholders(self):
        states = ['no permissions; see [http://developer.android.com/tools/device.html]',
            'no permissions (user in plugdev group; are your udev rules wrong?); see [http://developer.android.com/tools/device.html]']
        body = b''.join(device_row('(no serial number)', state, index+1, devpath='usb:1-2')
                        for index, state in enumerate(states))
        rows = roster.parse_devices(body)
        self.assertEqual([row['serial'] for row in rows], [None, None])
        self.assertEqual([row['state'] for row in rows], states)
        self.assertEqual([row['transport_id'] for row in rows], [1, 2])
        self.assertEqual([row['devpath'] for row in rows], ['usb:1-2', 'usb:1-2'])

    def test_parser_refuses_duplicate_identity_metadata_markers_and_wrong_order(self):
        bodies = [device_row()+device_row(transport_id=8),
                  device_row()+device_row(serial='OTHER', transport_id=7),
                  device_row(product='a product:b'), device_row(model='A model:B'),
                  device_row(device='a device:b'), device_row(product='a transport_id:8'),
                  device_row(model='A product:late'), device_row(device='a model:Late'),
                  device_row(product=''), device_row(model=''), device_row(device='')]
        for index, body in enumerate(bodies):
            with self.subTest(index=index): self.refused(lambda: roster.parse_devices(body))

    def test_parser_refuses_unsupported_wire_controls_partial_rows_and_ambiguous_serials(self):
        valid = device_row(product='original')
        bad = [b'\xff', b'\n', valid[:-1], valid+b'\n', b'X device transport_id:1\n',
               device_row(serial='INTERIOR SPACE'), device_row(state='unknown-state'),
               device_row(state='no permissions'), device_row(model='Invalid-Model'),
               device_row(model='模型'), valid.replace(b'original', b'orig\x00inal'),
               valid.replace(b'original', b'orig\tinal'), valid.replace(b'original', b'orig\rinal'),
               valid.replace(b'original', b'orig\x7final')]
        for index, body in enumerate(bad):
            with self.subTest(index=index): self.refused(lambda: roster.parse_devices(body))
        for value in (None, True, '', [], bytearray(valid)):
            self.refused(lambda: roster.parse_devices(value))

    def test_parser_enforces_utf8_byte_field_caps_and_positive_uint64_transport(self):
        full = device_row(serial='s'*256, product='é'*128, devpath='d'*256, device='v'*256,
                          transport_id=2**64-1)
        self.assertEqual(roster.parse_devices(full)[0]['transport_id'], 2**64-1)
        for specification in (dict(serial='s'*257), dict(product='é'*128+'x'),
                              dict(devpath='d'*257), dict(device='v'*257),
                              dict(model='M'*257), dict(transport_id=0), dict(transport_id=-1),
                              dict(transport_id=2**64), dict(transport_id='+1')):
            with self.subTest(specification=specification):
                self.refused(lambda: roster.parse_devices(device_row(**specification)))
        prefix = 'no permissions ('
        suffix = '); see [http://developer.android.com/tools/device.html]'
        state = prefix+'r'*(512-len(prefix+suffix))+suffix
        self.assertEqual(roster.parse_devices(device_row(state=state))[0]['state'], state)
        self.refused(lambda: roster.parse_devices(device_row(state=prefix+'r'+state[len(prefix):])))

    def test_parser_row_body_caps_and_last_malformed_row_are_not_silent_truncation(self):
        body = b''.join(device_row('ROW%d' % index, transport_id=index+1) for index in range(256))
        self.assertEqual(len(roster.parse_devices(body)), 256)
        self.refused(lambda: roster.parse_devices(body+device_row('EXTRA', transport_id=257)))
        self.refused(lambda: roster.parse_devices(body+b'LAST malformed\n'))
        self.refused(lambda: roster.parse_devices(b'x'*65536))

    def test_received_bytes_survive_expiry_during_the_same_receive_call(self):
        class LateReceive(RosterBackend):
            def recv(self, limit, deadline):
                part = super().recv(limit, deadline)
                self.clock = deadline
                return part
        backend = LateReceive(body=b'')
        report = roster.probe(backend, admission(), version_proof())
        self.assertEqual(report['status'], 'refused')
        self.assertEqual(report['reason'], 'deadline')
        self.assertEqual(backend.received, [b'OKAY0000'])
        self.assertEqual(report['response_hex'], b'OKAY0000'.hex())
        self.assertFalse(report['response_complete'])
        self.assertEqual(backend.counts['send'], 1)
        self.assertTrue(backend.closed)

    def test_well_formed_unrelated_tcp_row_never_passes_verdict_or_serialization(self):
        report = roster.probe(RosterBackend(), admission(), version_proof())
        selected = report['stages'][0]['snapshot']
        unrelated = held.row4(local_port=6000)
        decoded = legacy.decode_table(b'\x01\x00\x00\x00'+unrelated, 2)[0]
        selected['rows'].append(dict(family=2, ordinal=1, raw_hex=unrelated.hex(),
            raw_sha256=hashlib.sha256(unrelated).hexdigest(), row=asdict(decoded)))
        table = selected['tables'][0]
        full_table = struct.pack('<I', 2)+bytes.fromhex(selected['rows'][0]['raw_hex'])+unrelated
        table.update(count=2, returned_bytes=len(full_table), allocated_bytes=len(full_table),
                     raw_sha256=hashlib.sha256(full_table).hexdigest())
        with self.subTest(boundary='verdict'):
            self.assertIs(roster.report_verified(report, admission()), False)
        with self.subTest(boundary='serialization'):
            self.refused(lambda: roster.report_bytes(report, admission()))


if __name__ == '__main__':
    unittest.main()
