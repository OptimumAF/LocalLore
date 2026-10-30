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


if __name__ == '__main__': unittest.main()
