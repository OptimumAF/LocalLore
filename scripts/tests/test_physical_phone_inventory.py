"""Original byte-backed inventory oracles; no service or device authority.

Only synthetic resource IO is supplied. Prior version/roster and all inventory
verdicts are real pure validators, not substitute booleans.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import struct
import unittest

from benchmarks import physical_phone_inventory as inventory
from scripts.tests import test_adb_device_roster as roster_fixture
from scripts.tests import test_adb_device_roster_history as history
from scripts.tests import test_adb_held_socket as held


SERIAL = 'ORIGINAL_USB'
PORT = 44003
FACT_BYTES = (
    b'LLPI_V1\nUSER\n0\nPROPERTIES\n'
    b'ro.build.fingerprint=original/vendor/device:15/BUILD/1:user/release-keys\n'
    b'ro.product.model=Original Phone\nro.build.version.sdk=35\n'
    b'ro.soc.model=Original SoC\nro.board.platform=original_board\n'
    b'ro.product.cpu.abilist=arm64-v8a,armeabi-v7a\nro.kernel.qemu=0\n'
    b'PAGE\n4096\nMEMORY\nMemTotal:       8388608 kB\nMemAvailable: 4194304 kB\n'
    b'SPACE\n1000000|4096\nBATTERY\n  USB powered: true\n  level: 73\n'
    b'  scale: 100\n  temperature: 315\nTHERMAL\nThermal Status: 2\nEND\n'
)


def admission():
    value = roster_fixture.admission()
    value.update(protocol='physical-phone-inventory-v1', authorized_serial=SERIAL)
    return value


def prior_roster(body=roster_fixture.BODY):
    value = roster_fixture.roster.probe(roster_fixture.RosterBackend(body=body),
        roster_fixture.admission(), roster_fixture.version_proof())
    if not roster_fixture.roster.report_verified(value, roster_fixture.admission()):
        raise AssertionError('invalid original roster fixture')
    return value


def packet(channel, payload):
    return bytes((channel,)) + struct.pack('<I', len(payload)) + payload


def response(stdout=FACT_BYTES, *, transport=7, stderr=b'', exit_code=0):
    return (b'OKAY'+struct.pack('<Q', transport)+b'OKAY'+packet(1, stdout)+
            (packet(2, stderr) if stderr else b'')+packet(3, bytes((exit_code,))))


class InventoryBackend(held.FakeBackend):
    def __init__(self, wire=None, *, chunks=None):
        super().__init__(chunks=[response() if wire is None else wire, b''] if chunks is None else chunks)
        self.received = []
        self.brackets = [copy.deepcopy(self.brackets[0]) for _ in range(5)]
        endpoint = copy.deepcopy(self.endpoints[0]); endpoint['local_port'] = PORT
        self.endpoints = [copy.deepcopy(endpoint) for _ in range(12)]
        history_row = history.closing_row()
        self.snapshots = [held.snapshot((held.row4(), history_row))]
        self.snapshots += [held.snapshot((held.row4(), history_row,
            held.row4(remote='127.0.0.1', remote_port=PORT, state=5),
            held.row4(local_port=PORT, remote='127.0.0.1', remote_port=5037,
                      state=0, pid=held.CLIENT_PID))) for _ in range(4)]

    def recv(self, limit, deadline):
        value = super().recv(limit, deadline)
        if len(value) > limit:
            self.chunks.insert(0, value[limit:]); value = value[:limit]
        self.received.append(value)
        return value


class PhoneInventoryTests(unittest.TestCase):
    def test_admission_is_fixed_copied_and_serial_cannot_select_arbitrary_operations(self):
        original = admission()
        copied = inventory.validate_admission(original)
        self.assertEqual(copied, original)
        copied['adb_file']['identity'][0] += 1
        self.assertEqual(original, admission())
        self.assertEqual(inventory.roster_admission(original), roster_fixture.admission())
        self.assertEqual(inventory.backend_admission(original), held.admission())
        for serial in ('', 'abc', 'emulator-5554', '192.0.2.1:5555', 'a bcd', 'éabc', 'x'*129, True):
            changed = admission(); changed['authorized_serial'] = serial
            with self.subTest(serial_type=type(serial).__name__), self.assertRaises(ValueError):
                inventory.validate_admission(changed)
        for key, value in (('protocol', roster_fixture.roster.PROTOCOL), ('version', True),
                           ('command', 'shell:id'), ('transport_id', 7)):
            changed = admission(); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                inventory.validate_admission(changed)

    def test_exact_authorized_device_is_required_before_resource_open(self):
        bodies = [b'', roster_fixture.device_row('OTHER_USB', product='p', model='M', device='d'),
            roster_fixture.device_row(SERIAL, state='unauthorized', product='p', model='M', device='d'),
            roster_fixture.device_row(SERIAL, product='p', model='M'),
            roster_fixture.device_row(SERIAL, product='p', device='d')]
        proofs = [prior_roster(body) for body in bodies]
        bad = prior_roster(); bad['socket_closed'] = False; proofs.append(bad)
        for proof in proofs:
            with self.subTest(rows=len(proof['rows'])):
                backend = InventoryBackend()
                report = inventory.probe(backend, admission(), proof)
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(backend.counts['open'], 0)
                self.assertEqual(backend.counts['connect'], 0)
                self.assertEqual(backend.sent, [])
                self.assertEqual(backend.counts['close'], 1)

    def test_same_worker_identity_is_required_before_connect(self):
        for key, value in (('pid', held.CLIENT_PID+1), ('creation_filetime', 223456790),
                           ('executable', 'D:\\Synthetic\\different-worker.exe')):
            backend = InventoryBackend()
            for bracket in backend.brackets: bracket['client'][key] = value
            with self.subTest(key=key):
                report = inventory.probe(backend, admission(), prior_roster())
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(backend.counts['connect'], 0)
                self.assertEqual(backend.sent, [])
                self.assertTrue(backend.closed)

    def test_host_transport_mismatch_never_sends_any_device_request(self):
        for wire in (b'OKAY'+struct.pack('<Q', 8), b'OKAY'+struct.pack('>Q', 7),
                     b'FAIL0004oops', b'OKAY'+struct.pack('<Q', 0)):
            with self.subTest(wire=wire.hex()):
                backend = InventoryBackend(wire)
                report = inventory.probe(backend, admission(), prior_roster())
                self.assertEqual(report['status'], 'refused')
                self.assertEqual(backend.sent, [inventory.TPORT_REQUEST])
                self.assertFalse(report['device_request_sent'])
                self.assertEqual(bytes.fromhex(report['wire_hex']), b''.join(backend.received))
                self.assertEqual(backend.counts['connect'], 1)
                self.assertTrue(backend.closed)

    def test_fragmented_complete_exchange_requires_three_fixed_sends_and_five_owned_brackets(self):
        wire = response()
        backend = InventoryBackend(chunks=[wire[i:i+1] for i in range(len(wire))]+[b''])
        report = inventory.probe(backend, admission(), prior_roster())
        self.assertEqual(report['status'], 'observed')
        self.assertTrue(inventory.report_verified(report, admission()))
        self.assertEqual(backend.sent, [inventory.TPORT_REQUEST, inventory.SHELL_REQUEST, inventory.CLOSE_STDIN])
        self.assertEqual([backend.counts[name] for name in ('open', 'connect', 'bracket', 'snapshot', 'close')],
                         [1, 1, 5, 5, 1])
        self.assertEqual(report['wire_hex'], wire.hex())
        self.assertEqual(report['client_raw_state'], 0)
        self.assertFalse(report['feature_acceptance'])
        self.assertEqual([stage['stage'] for stage in report['stages']],
                         ['initial', 'connected', 'tport', 'service', 'stdin', 'final'])

    def test_each_send_requires_fresh_unchanged_source_and_live_server_join(self):
        for stage in range(1, 4):
            for fault in ('source', 'server'):
                backend = InventoryBackend()
                if fault == 'source': backend.brackets[stage]['adb_file']['sha256'] = 'b'*64
                else:
                    backend.snapshots[stage] = held.snapshot((held.row4(), history.closing_row(),
                        held.row4(remote='127.0.0.1', remote_port=PORT, state=0),
                        held.row4(local_port=PORT, remote='127.0.0.1', remote_port=5037,
                                  state=0, pid=held.CLIENT_PID)))
                with self.subTest(stage=stage, fault=fault):
                    report = inventory.probe(backend, admission(), prior_roster())
                    self.assertEqual(report['status'], 'refused')
                    self.assertEqual(backend.sent, [inventory.TPORT_REQUEST, inventory.SHELL_REQUEST,
                                                    inventory.CLOSE_STDIN][:stage-1])
                    self.assertTrue(backend.closed)

    def test_truncated_trailing_stderr_nonzero_and_cancelled_streams_retain_actual_bytes(self):
        wires = [response()[:-1], response()+b'x', response(stderr=b'private diagnostic'),
                 response(exit_code=1), response()+packet(3, b'\x00')]
        for wire in wires:
            with self.subTest(wire_bytes=len(wire)):
                backend = InventoryBackend(wire)
                report = inventory.probe(backend, admission(), prior_roster())
                self.assertEqual(report['status'], 'refused')
                self.assertFalse(inventory.report_verified(report, admission()))
                self.assertEqual(report['wire_hex'], b''.join(backend.received).hex())
                self.assertEqual(backend.counts['close'], 1)
        backend = InventoryBackend(chunks=[b'OKAY', KeyboardInterrupt('PRIVATE_CANCEL')])
        report = inventory.probe(backend, admission(), prior_roster())
        self.assertEqual(report['reason'], 'cancelled')
        self.assertEqual(report['wire_hex'], b'OKAY'.hex())
        self.assertEqual(backend.sent, [inventory.TPORT_REQUEST])
        self.assertNotIn('PRIVATE_CANCEL', str(report['reason']))

    def test_post_read_deadline_retains_bytes_and_uncertain_close_cannot_qualify(self):
        class Late(InventoryBackend):
            def recv(self, limit, deadline):
                value = super().recv(limit, deadline); self.clock = deadline; return value
        backend = Late()
        report = inventory.probe(backend, admission(), prior_roster())
        self.assertEqual(report['reason'], 'deadline')
        self.assertEqual(report['wire_hex'], b''.join(backend.received).hex())
        self.assertTrue(backend.received)
        self.assertEqual(backend.sent, [inventory.TPORT_REQUEST])
        for value in (False, None, True):
            backend = InventoryBackend(); backend.close_result['socket_closed'] = value
            if value is True: backend.close_result['process_handles_closed'] = None
            report = inventory.probe(backend, admission(), prior_roster())
            self.assertEqual(report['status'], 'refused')
            self.assertEqual(backend.counts['close'], 1)
            self.assertFalse(inventory.report_verified(report, admission()))

    def test_closed_report_replays_order_raw_bytes_target_and_typed_measurements(self):
        report = inventory.probe(InventoryBackend(), admission(), prior_roster())
        self.assertTrue(inventory.report_verified(report, admission()))
        mutations = [lambda r: r['stages'][2].update(stage='service'),
            lambda r: r['target'].update(transport_id=8),
            lambda r: r['facts'].update(page_bytes=65536),
            lambda r: r.update(wire_hex=response(exit_code=1).hex()),
            lambda r: r.update(elapsed_ms=True),
            lambda r: r['roster_proof'].update(socket_closed=False)]
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(report); mutate(changed)
            with self.subTest(mutation=index):
                self.assertIs(inventory.report_verified(changed, admission()), False)


if __name__ == '__main__': unittest.main()
