"""Original phone-service profile oracles; all processes and sockets are fake.

Synthetic native identities/rows establish consistency only, never authority to
start a real service or contact a device. Existing isolated tests stay intact.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import isolated_adb_lease as lease
from benchmarks import isolated_adb_owner as owner
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_isolated_adb_lease as original
from scripts.tests import test_adb_held_socket as tcp


PHONE_PROTOCOL = 'owned-phone-discovery-service-v1'
PHONE_PORT = 5037


def admission():
    value = original.admission()
    value.update(protocol=PHONE_PROTOCOL, port=PHONE_PORT, seconds=30)
    return value


def running(value):
    result = original.running(value)
    result.update(protocol=PHONE_PROTOCOL, port=PHONE_PORT, version_proof=None, devices_proof=None)
    return result


class FakeApi:
    def __init__(self, v4=(), v6=()):
        self.tables = {2:tcp.capture(2, *v4), 23:tcp.capture(23, *v6)}
    def capture(self, family): return self.tables[family]


class FakeBindSocket:
    def __init__(self): self.binds, self.options, self.closed = [], [], False
    def setsockopt(self, *args): self.options.append(args)
    def bind(self, endpoint): self.binds.append(endpoint)
    def close(self): self.closed = True
    def fileno(self): return -1 if self.closed else 77


class WorkerCase:
    """Actual worker/guard/readiness/cleanup algorithms, with only IO replaced."""
    def __init__(self, *, fault=None):
        self.root = Path(tempfile.mkdtemp(prefix='locallore-phone-owner-', dir='D:/Dev/_Temp'))
        self.admission = admission(); self.admission['root'] = str(self.root)
        self.admission_path = self.root/'admission-input-v1.json'
        env.create_json(self.admission_path, self.admission); self.binding = env.binding(self.admission_path)
        self.request = dict(version=1, protocol=PHONE_PROTOCOL, admission=self.binding,
            validated_admission=self.admission, owner=copy.deepcopy(original.OWNER),
            sources=self.admission['sources'], python=self.admission['python'],
            worker_script=next(pin for pin in self.admission['sources'] if Path(pin['path']).name == 'isolated_adb_owner.py'),
            owner_seconds=60)
        env.create_json(self.root/'request-v1.json', self.request); self.request_pin = env.binding(self.root/'request-v1.json')
        if fault != 'receipt':
            env.create_json(self.root/'started-v1.json', dict(worker=original.CLIENT, request=self.request_pin))
        if fault != 'deadline':
            env.create_json(self.root/'stop-v1.json', dict(version=1, protocol=PHONE_PROTOCOL,
                admission_sha256=self.binding['sha256'], action='stop'))
        self.runtime = owner.WorkerRuntime(self.request, self.request_pin, self.root)
        self.runtime.worker = copy.deepcopy(original.CLIENT)
        self.api = FakeApi()
        self.processes = SimpleNamespace(guard=Mock(), add=Mock(return_value=(903, copy.deepcopy(original.SERVER))),
                                       close=Mock(return_value=True), failed_close=False)
        self.auth = SimpleNamespace(key=None, descriptor=None, failed_close=False, close=Mock(return_value=True))
        descriptor = dict(path=self.admission['auth_key'], native_profile='C:\\Users\\Synthetic',
            metadata=dict(volume_serial=3, file_index=9, bytes=2048, attributes=0x20,
                          creation_filetime=1001, write_filetime=1002, links=1))
        def auth_open(path):
            if path != self.admission['auth_key']: raise AssertionError('unselected credential metadata')
            self.auth.key = 901; self.auth.descriptor = copy.deepcopy(descriptor)
        self.auth.open = Mock(side_effect=auth_open)
        self.auth.check = Mock(side_effect=lambda: copy.deepcopy(self.auth.descriptor))
        self.runtime.auth = self.auth
        self.runtime.open_identity = Mock(side_effect=self.open_identity)
        self.handle = SimpleNamespace(closed=False)
        def close_handle(): self.handle.closed = True
        self.handle.Close = Mock(side_effect=close_handle)
        self.child = SimpleNamespace(pid=original.SERVER['pid'], poll=Mock(return_value=None),
                                    terminate=Mock(), wait=Mock(return_value=0), _handle=self.handle)
        self.socket = FakeBindSocket()
        self.capture = None; self.clock = 1.0; self.fault = fault

    def open_identity(self):
        self.runtime.api = self.api; self.runtime.processes = self.processes

    def now(self): self.clock += .01; return self.clock

    def make_capture(self, path):
        path.mkdir()
        (path/'owner-stdout-v1.bin').write_bytes(b''); (path/'owner-stderr-v1.bin').write_bytes(b'')
        self.capture = SimpleNamespace(start=Mock(), guard=Mock(), close=Mock(return_value=self.fault != 'close'),
                                       pipes_closed=True, capture=SimpleNamespace(sizes=[0, 0]))
        return self.capture

    def popen(self, command, **kwargs):
        if self.fault == 'start': raise OSError('PRIVATE_START_CANARY')
        if command != [self.admission['adb']['path'], '-L', 'tcp:localhost:5037', 'server', 'nodaemon']:
            raise AssertionError('wrong service command')
        if kwargs['env']['ADB_USB'] != '1': raise AssertionError('USB profile lost')
        self.api.tables[2] = tcp.capture(2, tcp.row4(local_port=5037, pid=original.SERVER['pid']))
        return self.child

    def run(self):
        actual_create = env.create_json
        def publish(path, value):
            result = actual_create(path, value)
            if Path(path) == self.root/'running-v1.json':
                if self.fault == 'deadline': self.clock = 1000.0
                elif self.fault == 'cancel': self.runtime.guard = Mock(side_effect=KeyboardInterrupt('PRIVATE_CANCEL'))
            return result
        with ExitStack() as stack:
            stack.enter_context(patch.object(owner, 'WorkerRuntime', return_value=self.runtime))
            stack.enter_context(patch.object(owner, '_guards'))
            stack.enter_context(patch.object(owner.native, '_check_abi'))
            stack.enter_context(patch.object(owner.socket, 'socket', return_value=self.socket))
            self.spawn = stack.enter_context(patch.object(owner.subprocess, 'Popen', side_effect=self.popen))
            stack.enter_context(patch.object(owner, 'ServerCapture', side_effect=self.make_capture))
            self.exchange = stack.enter_context(patch.object(owner, '_exchange', side_effect=AssertionError('phone profile emitted host frame')))
            stack.enter_context(patch.object(owner.lease, 'source_bindings', return_value=self.admission['sources']))
            stack.enter_context(patch.object(owner.file_guard, '_python_bindings', return_value=self.admission['python']))
            stack.enter_context(patch.object(owner.time, 'monotonic', side_effect=self.now))
            stack.enter_context(patch.object(owner.time, 'time', return_value=1800000000.25))
            stack.enter_context(patch.object(owner.time, 'sleep'))
            stack.enter_context(patch.object(owner.env, 'create_json', side_effect=publish))
            code = owner._run_worker(self.request, self.request_pin, self.root)
        return code, env.read_json(self.root/'worker-result-v1.json')


class OwnedPhoneServiceTests(unittest.TestCase):
    def accepted(self, action):
        error, value = None, None
        try: value = action()
        except (ValueError, TypeError) as caught: error = caught
        self.assertIsNone(error, 'the explicitly declared phone profile must be implemented')
        return value

    def test_profile_is_literal_bounded_copied_and_has_no_runtime_side_effect(self):
        self.assertEqual(getattr(lease, 'PHONE_PROTOCOL', None), PHONE_PROTOCOL)
        self.assertEqual(getattr(lease, 'PHONE_PORT', None), PHONE_PORT)
        for seconds in (30, 120):
            value = admission(); value['seconds'] = seconds
            with self.subTest(seconds=seconds), patch.object(Path, 'open', side_effect=AssertionError('file IO')), \
                 patch.object(owner.native, '_WindowsApi') as native, patch.object(owner.socket, 'socket') as sock, \
                 patch.object(owner.subprocess, 'Popen') as process:
                copied = self.accepted(lambda: lease.validate_admission(value))
                self.assertEqual(copied, value)
                copied['tools'][0]['bytes'] += 1
                self.assertNotEqual(copied, value)
                native.assert_not_called(); sock.assert_not_called(); process.assert_not_called()

    def test_profile_port_duration_and_command_cannot_fall_back_to_old_or_arbitrary_listener(self):
        value = admission()
        command = self.accepted(lambda: lease.server_command(value))
        self.assertEqual(command, [value['adb']['path'], '-L', 'tcp:localhost:5037', 'server', 'nodaemon'])
        for field, bad in (('port', 15937), ('port', 5038), ('port', True), ('seconds', 29),
                           ('seconds', 121), ('seconds', True), ('protocol', 'owned-phone-discovery-service-v2')):
            changed = admission(); changed[field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(lease.LeaseRefused):
                lease.validate_admission(changed)
        old = original.admission()
        self.assertEqual(lease.validate_admission(old), old)
        self.assertEqual(lease.server_command(old), [old['adb']['path'], '-L', 'tcp:localhost:15937', 'server', 'nodaemon'])
        old['port'] = PHONE_PORT
        with self.assertRaises(lease.LeaseRefused): lease.validate_admission(old)

    def test_child_environment_cannot_inherit_usb_backend_vendor_emulator_mdns_or_trace_routes(self):
        inherited = dict(PATH='retained PATH', HOME='C:\\Users\\Synthetic', USERPROFILE='C:\\Users\\Synthetic',
            SystemRoot='C:\\Windows', adb_usb='0', ADB_LIBUSB='0', AdB_VENDOR_KEYS='PRIVATE_KEY_CANARY',
            ADB_TRACE='all', aNdRoId_AdB_SeRvEr_PoRt='5038', ADBHOST='foreign', ADBPORT='5555',
            ADBSERVERPORT='5556', ANDROIDADBPORT='5557', TEMP='C:\\PrivateTemp', tmp='C:\\OtherTemp',
            ADB_MDNS_AUTO_CONNECT='1', ADB_LOCAL_TRANSPORT_MAX_PORT='65535', ANDROID_SERIAL='foreign')
        before = copy.deepcopy(inherited)
        result = self.accepted(lambda: lease.child_environment(admission(), inherited))
        self.assertEqual(inherited, before)
        expected = dict(ADB_USB='1', ADB_EMU='0', ADB_MDNS='0', ADB_MDNS_AUTO_CONNECT='0',
                        ADB_LOCAL_TRANSPORT_MAX_PORT='0')
        for key, value in expected.items(): self.assertEqual(result[key], value)
        for key in ('PATH', 'HOME', 'USERPROFILE', 'SystemRoot'): self.assertEqual(result[key], inherited[key])
        for key in ('TEMP', 'TMP', 'TMPDIR'): self.assertEqual(result[key], 'D:\\Dev\\_Temp')
        self.assertNotIn('PRIVATE_KEY_CANARY', str(result))
        self.assertNotIn('ADB_LIBUSB', result); self.assertNotIn('adb_usb', result)
        for key in ('ADBHOST', 'ADBPORT', 'ADBSERVERPORT', 'ANDROIDADBPORT', 'ANDROID_SERIAL', 'ADB_TRACE'):
            self.assertNotIn(key, result)
        old = lease.child_environment(original.admission(), inherited)
        self.assertEqual(old['ADB_USB'], '0')

    def test_running_and_stop_are_profile_bound_without_fabricating_host_protocol_proofs(self):
        admitted = admission(); value = running(admitted)
        copied = self.accepted(lambda: lease.validate_running(value, admitted, original.admitted_binding()))
        self.assertEqual(copied, value)
        stop = dict(version=1, protocol=PHONE_PROTOCOL, admission_sha256='a'*64, action='stop')
        self.accepted(lambda: lease.check_stop(stop, 'a'*64, protocol=PHONE_PROTOCOL))
        with self.assertRaises(lease.LeaseRefused): lease.check_stop(stop, 'a'*64)
        old_stop = {**stop, 'protocol':original.PROTOCOL}
        with self.assertRaises(lease.LeaseRefused): lease.check_stop(old_stop, 'a'*64, protocol=PHONE_PROTOCOL)
        for field, bad in (('protocol', original.PROTOCOL), ('port', 15937),
                           ('version_proof', original.pin('D:\\Synthetic\\proof-version-v1.json')),
                           ('devices_proof', original.pin('D:\\Synthetic\\proof-devices-v1.json'))):
            changed = copy.deepcopy(value); changed[field] = bad
            with self.subTest(field=field), self.assertRaises(lease.LeaseRefused):
                lease.validate_running(changed, admitted, original.admitted_binding())
        old_running = original.running(); old_running['version_proof'] = None
        with self.assertRaises(lease.LeaseRefused):
            lease.validate_running(old_running, original.admission(), original.admitted_binding())

    def test_observation_selects_admitted_port_and_refuses_unknown_port_before_capture(self):
        api = FakeApi(v4=(tcp.row4(local_port=5037), tcp.row4(local_port=15937)))
        with patch.object(owner.native, '_check_abi'):
            observed, tables = self.accepted(lambda: owner._observe(api, port=5037))
            self.assertEqual(observed['port'], 5037)
            self.assertEqual([row['local_port'] for row in observed['rows']], [5037])
            self.assertEqual([table['count'] for table in tables], [2, 0])
            old, _ = owner._observe(api)
            self.assertEqual([row['local_port'] for row in old['rows']], [15937])
            for port in (0, 5038, True, '5037'):
                capture = Mock(side_effect=AssertionError('bad port reached native capture'))
                with self.subTest(port=port), patch.object(api, 'capture', capture):
                    with self.assertRaises((ValueError, TypeError)): owner._observe(api, port=port)
                capture.assert_not_called()

    def test_occupied_ipv4_wildcard_or_ipv6_port_refuses_before_bind_or_spawn(self):
        occupied = [(tcp.row4(local_port=5037),), (tcp.row4(local='0.0.0.0', local_port=5037),)]
        for family, rows in [(2, rows) for rows in occupied]+[(23, (tcp.row6(local='::', local_port=5037),)),
                                                            (23, (tcp.row6(local='::1', local_port=5037),))]:
            api = FakeApi(v4=rows if family == 2 else (), v6=rows if family == 23 else ())
            with self.subTest(family=family, raw=rows[0].hex()), patch.object(owner.native, '_check_abi'), \
                 patch.object(owner.socket, 'socket') as sock, patch.object(owner.subprocess, 'Popen') as child:
                with self.assertRaises((ValueError, TypeError)): owner._exclusive_preflight(api, port=5037)
                sock.assert_not_called(); child.assert_not_called()

    def test_empty_exclusive_preflight_binds_only_literal_loopback_and_closes_its_socket(self):
        item = FakeBindSocket()
        with patch.object(owner.native, '_check_abi'), patch.object(owner.socket, 'socket', return_value=item) as opened, \
             patch.object(owner.subprocess, 'Popen') as child:
            result = self.accepted(lambda: owner._exclusive_preflight(FakeApi(), port=5037))
        self.assertTrue(result['exclusive_bind_succeeded'])
        self.assertEqual(item.binds, [('127.0.0.1', 5037)])
        self.assertEqual((result['created_mask'], result['close_attempted_mask'], result['closed_mask']), (1, 1, 1))
        self.assertTrue(item.closed); opened.assert_called_once(); child.assert_not_called()

    def test_actual_phone_worker_stops_with_zero_host_frames_and_real_closed_receipt_reader(self):
        case = WorkerCase()
        code, value = case.run()
        self.assertEqual(code, 0)
        self.assertEqual(value['protocol'], PHONE_PROTOCOL)
        self.assertEqual(value['proofs'], [])
        self.assertIsNotNone(value['running'])
        live = env.read_json(case.root/'running-v1.json')
        self.assertEqual(live['port'], 5037)
        self.assertIsNone(live['version_proof']); self.assertIsNone(live['devices_proof'])
        self.assertEqual(value['reason'], 'stop_requested')
        self.assertTrue(all(value['cleanup'].values()))
        self.assertEqual(lease.validate_worker_result(env.binding(case.root/'worker-result-v1.json'),
            case.admission, case.binding, case.request_pin, original.CLIENT), value)
        case.exchange.assert_not_called(); case.spawn.assert_called_once()
        case.child.terminate.assert_called_once(); case.child.wait.assert_called_once()
        case.handle.Close.assert_called_once(); case.auth.close.assert_called_once(); case.processes.close.assert_called_once()

    def test_worker_deadline_cancel_start_failure_and_uncertain_close_never_retry_or_query(self):
        for fault in ('deadline', 'cancel', 'start', 'close'):
            case = WorkerCase(fault=fault)
            code, value = case.run()
            with self.subTest(fault=fault):
                self.assertEqual(value['protocol'], PHONE_PROTOCOL)
                self.assertEqual(value['proofs'], [])
                case.exchange.assert_not_called()
                self.assertLessEqual(case.spawn.call_count, 1)
                case.auth.close.assert_called_once(); case.processes.close.assert_called_once()
                if fault == 'deadline':
                    self.assertEqual((code, value['reason']), (0, 'expired'))
                    self.assertTrue(all(value['cleanup'].values()))
                else:
                    self.assertEqual(code, 1)
                    if fault == 'cancel': self.assertEqual(value['reason'], 'cancelled')
                    if fault == 'close': self.assertEqual(value['reason'], 'cleanup')
                if fault == 'start':
                    case.child.terminate.assert_not_called(); case.handle.Close.assert_not_called()
                else:
                    case.child.terminate.assert_called_once(); case.handle.Close.assert_called_once()
                self.assertNotIn('PRIVATE_', value['reason'])

    def test_missing_started_receipt_blocks_auth_port_spawn_and_host_exchange(self):
        case = WorkerCase(fault='receipt')
        with patch.object(owner, '_exclusive_preflight') as preflight:
            code, value = case.run()
        self.assertEqual(code, 1)
        self.assertIsNone(value['running']); self.assertEqual(value['proofs'], [])
        case.auth.open.assert_not_called(); case.spawn.assert_not_called(); case.exchange.assert_not_called()
        preflight.assert_not_called(); case.child.terminate.assert_not_called()
        case.auth.close.assert_called_once(); case.processes.close.assert_called_once()


if __name__ == '__main__': unittest.main()
