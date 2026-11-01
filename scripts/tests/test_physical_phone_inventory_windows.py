"""Original adapter failure tests; native and socket operations stay fake."""
import socket
import unittest
from unittest.mock import patch

from benchmarks import physical_phone_inventory as contract
from benchmarks import physical_phone_inventory_windows as windows
from benchmarks import adb_held_socket_windows as old
from scripts.tests import test_adb_device_roster_windows as fixture


SEQUENCE = lambda: (contract.TPORT_REQUEST, contract.SHELL_REQUEST, contract.CLOSE_STDIN)


def active():
    return fixture.active(windows.WindowsPhoneInventoryBackend)


class PhoneInventoryWindowsTests(unittest.TestCase):
    def test_constructor_is_inert_and_only_fixed_order_can_use_the_owned_socket(self):
        with patch.object(old, '_WindowsApi') as native, patch.object(old.socket, 'socket') as network:
            value = windows.WindowsPhoneInventoryBackend()
            self.assertIsInstance(value, old.WindowsBackend)
            native.assert_not_called(); network.assert_not_called()
        value, owned = active()
        for request in SEQUENCE(): value.send(request, 4.0)
        self.assertEqual(owned.sent, list(SEQUENCE()))
        self.assertEqual(owned.timeouts, [3.0]*3)
        self.assertEqual(owned.sent[0], b'000ehost:tport:usb')
        self.assertEqual(owned.sent[2], b'\x04\x00\x00\x00\x00')
        with self.assertRaises(ValueError): value.send(contract.CLOSE_STDIN, 4.0)
        self.assertEqual(len(owned.sent), 3)

    def test_out_of_order_repeated_mutable_or_arbitrary_sends_poison_without_dependent_io(self):
        for stage in range(3):
            invalid = [b'000Chost:version', b'000Ehost:devices-l', b'0007shell:id',
                       bytearray(SEQUENCE()[stage]), SEQUENCE()[(stage+1)%3]]
            for request in invalid:
                with self.subTest(stage=stage, request_type=type(request).__name__):
                    value, owned = active()
                    for earlier in SEQUENCE()[:stage]: value.send(earlier, 4.0)
                    with self.assertRaises(ValueError): value.send(request, 4.0)
                    self.assertEqual(owned.sent, list(SEQUENCE()[:stage]))
                    with self.assertRaises(ValueError): value.send(SEQUENCE()[stage], 4.0)
                    self.assertEqual(owned.sent, list(SEQUENCE()[:stage]))

    def test_every_send_rechecks_original_socket_endpoint_and_fixed_deadline(self):
        for stage in range(3):
            for fault in ('replacement', 'handle', 'endpoint', 'expired', 'extended', 'rollback'):
                with self.subTest(stage=stage, fault=fault):
                    value, owned = active()
                    for request in SEQUENCE()[:stage]: value.send(request, 4.0)
                    deadline = 4.0
                    if fault == 'replacement': value._socket = fixture.FakeSocket()
                    elif fault == 'handle': owned.handle += 1
                    elif fault == 'endpoint': owned.port += 1
                    elif fault == 'expired': value.now = lambda: 4.0
                    elif fault == 'extended': deadline = 5.0
                    else: value._last_clock = 2.0
                    with self.assertRaises(ValueError): value.send(SEQUENCE()[stage], deadline)
                    self.assertEqual(owned.sent, list(SEQUENCE()[:stage]))

    def test_failed_partial_send_is_spent_and_cancellation_identity_is_preserved(self):
        for failure in (socket.timeout('PRIVATE_TIMEOUT'), KeyboardInterrupt('PRIVATE_CANCEL')):
            value, owned = active(); value.send(contract.TPORT_REQUEST, 4.0)
            owned.send_error = failure
            with self.assertRaises(BaseException) as caught: value.send(contract.SHELL_REQUEST, 4.0)
            if isinstance(failure, KeyboardInterrupt): self.assertIs(caught.exception, failure)
            self.assertTrue(value._poisoned)
            owned.send_error = None
            with self.assertRaises(ValueError): value.send(contract.SHELL_REQUEST, 4.0)
            self.assertEqual(owned.sent, [contract.TPORT_REQUEST])

    def test_receive_caps_types_and_unsent_state_are_checked_before_socket_read(self):
        value, owned = active()
        with self.assertRaises(ValueError): value.recv(1, 4.0)
        self.assertEqual(owned.receives, [])
        for limit in (0, -1, True, None, 1.5, contract.MAX_WIRE+2):
            value, owned = active(); value.send(contract.TPORT_REQUEST, 4.0)
            with self.subTest(limit=limit), self.assertRaises(ValueError): value.recv(limit, 4.0)
            self.assertEqual(owned.receives, [])
        value, owned = active(); value.send(contract.TPORT_REQUEST, 4.0)
        owned.data = b'x'*(contract.MAX_WIRE+1)
        self.assertEqual(value.recv(contract.MAX_WIRE+1, 4.0), owned.data)
        owned.data = b''; self.assertEqual(value.recv(1, 4.0), b'')

    def test_actual_post_read_bytes_survive_late_deadline_or_endpoint_refusal(self):
        for fault in ('late', 'endpoint'):
            value, owned = active(); value.send(contract.TPORT_REQUEST, 4.0)
            raw = b'OKAY\x07\x00\x00\x00\x00\x00\x00\x00'
            def receive(limit):
                if fault == 'late': value.now = lambda: 4.0
                else: owned.port += 1
                return raw
            with self.subTest(fault=fault), patch.object(owned, 'recv', side_effect=receive):
                with self.assertRaises(contract.InventoryReceiveRefused) as caught:
                    value.recv(len(raw), 4.0)
                self.assertEqual(caught.exception.received, raw)
                self.assertTrue(value._poisoned)
                with self.assertRaises(ValueError): value.recv(1, 4.0)

    def test_close_is_one_attempt_and_failed_close_remains_unqualified(self):
        for fails in (False, True):
            value, owned = active(); value.send(contract.TPORT_REQUEST, 4.0)
            attempts = []
            def close():
                attempts.append(True)
                if fails: raise OSError('PRIVATE_CLOSE')
                owned.handle = -1
            with self.subTest(fails=fails), patch.object(owned, 'close', side_effect=close):
                first = value.close(); second = value.close()
                self.assertEqual(first, second)
                self.assertIs(first['socket_closed'], not fails)
                self.assertIs(first['process_handles_closed'], True)
                self.assertEqual(len(attempts), 1)
                with self.assertRaises(ValueError): value.recv(1, 4.0)


if __name__ == '__main__': unittest.main()
