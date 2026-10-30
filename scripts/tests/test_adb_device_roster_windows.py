"""Original fake-IO roster adapter checks; never native/socket/SDK observations."""
import socket
import unittest
from unittest.mock import patch

from benchmarks import adb_device_roster_windows as roster
from benchmarks import adb_held_socket_windows as old
from benchmarks.adb_held_socket import ProbeRefused


class FakeSocket:
    def __init__(self):
        self.sent, self.receives, self.timeouts = [], [], []
        self.data = b'OKAY0000'
        self.handle, self.port, self.closes = 123, 42001, 0
        self.send_error = None
    def fileno(self): return self.handle
    def getsockname(self): return ('127.0.0.1', self.port)
    def getpeername(self): return ('127.0.0.1', 5037)
    def settimeout(self, value): self.timeouts.append(value)
    def sendall(self, data):
        if self.send_error is not None: raise self.send_error
        self.sent.append(data)
    def recv(self, limit): self.receives.append(limit); return self.data
    def close(self): self.closes += 1


def active():
    value, owned = roster.WindowsRosterBackend(), FakeSocket()
    value.now = lambda: 1.0
    value._deadline = 4.0
    value._opened = value._connected = True
    value._socket = value._socket_anchor = owned
    value._socket_handle, value._socket_id = owned.handle, id(owned)
    value._socket_closed = False
    value._endpoint_pin = value._read_endpoint()
    return value, owned


class RosterWindowsTests(unittest.TestCase):
    def test_constructor_inherits_resource_owner_without_any_native_or_socket_io(self):
        with patch.object(old, '_WindowsApi') as native, patch.object(old.socket, 'socket') as network:
            value = roster.WindowsRosterBackend()
            self.assertIsInstance(value, old.WindowsBackend)
            self.assertFalse(value._open_called)
            native.assert_not_called(); network.assert_not_called()

    def test_fixed_request_is_sent_once_on_the_original_owned_socket(self):
        value, owned = active(); value.send(roster.REQUEST, 4.0)
        self.assertEqual(owned.sent, [b'000Ehost:devices-l'])
        self.assertTrue(value._sent); self.assertEqual(owned.timeouts, [3.0])
        with self.assertRaises(ProbeRefused): value.send(roster.REQUEST, 4.0)
        self.assertEqual(len(owned.sent), 1); self.assertTrue(value._poisoned)

    def test_version_arbitrary_and_mutable_requests_never_dispatch(self):
        for payload in (b'000Chost:version', b'000Chost:devices', bytearray(roster.REQUEST), ''):
            with self.subTest(payload=type(payload).__name__):
                value, owned = active()
                with self.assertRaises(ProbeRefused): value.send(payload, 4.0)
                self.assertEqual(owned.sent, []); self.assertTrue(value._poisoned)

    def test_receive_admits_one_overflow_detection_byte_above_max_response(self):
        value, owned = active(); value.send(roster.REQUEST, 4.0)
        owned.data = b'x' * (roster.MAX_RESPONSE + 1)
        self.assertEqual(value.recv(roster.MAX_RESPONSE + 1, 4.0), owned.data)
        self.assertEqual(owned.receives, [roster.MAX_RESPONSE + 1])

    def test_receive_zero_and_bool_and_overflow_limits_refuse_before_io(self):
        for limit in (0, -1, True, 1.5, roster.MAX_RESPONSE + 2):
            with self.subTest(limit=limit):
                value, owned = active(); value.send(roster.REQUEST, 4.0)
                with self.assertRaises(ProbeRefused): value.recv(limit, 4.0)
                self.assertEqual(owned.receives, []); self.assertTrue(value._poisoned)

    def test_receive_before_send_refuses(self):
        value, owned = active()
        with self.assertRaises(ProbeRefused): value.recv(1, 4.0)
        self.assertEqual(owned.receives, [])

    def test_receive_requires_bounded_bytes_and_preserves_empty_eof(self):
        for data in (bytearray(b'x'), None, b'xx'):
            with self.subTest(data=type(data).__name__):
                value, owned = active(); value.send(roster.REQUEST, 4.0); owned.data = data
                with self.assertRaises(ProbeRefused): value.recv(1, 4.0)
                self.assertTrue(value._poisoned)
        value, owned = active(); value.send(roster.REQUEST, 4.0); owned.data = b''
        self.assertEqual(value.recv(1, 4.0), b'')

    def test_replaced_socket_cannot_send_or_receive(self):
        for method in ('send', 'recv'):
            with self.subTest(method=method):
                value, owned = active()
                if method == 'recv': value.send(roster.REQUEST, 4.0)
                value._socket = FakeSocket()
                with self.assertRaises(ProbeRefused):
                    getattr(value, method)(roster.REQUEST if method == 'send' else 1, 4.0)
                self.assertEqual(owned.receives, [])
                self.assertEqual(len(owned.sent), int(method == 'recv'))

    def test_changed_handle_or_endpoint_refuses_before_io(self):
        for attribute in ('handle', 'port'):
            with self.subTest(attribute=attribute):
                value, owned = active(); setattr(owned, attribute, getattr(owned, attribute)+1)
                with self.assertRaises(ProbeRefused): value.send(roster.REQUEST, 4.0)
                self.assertEqual(owned.sent, [])

    def test_expired_or_changed_or_rolled_back_deadline_never_dispatches(self):
        for clock, deadline, previous in ((4.0,4.0,None),(1.0,5.0,None),(1.0,4.0,2.0)):
            with self.subTest(clock=clock, deadline=deadline, previous=previous):
                value, owned = active(); value.now = lambda: clock; value._last_clock = previous
                with self.assertRaises(ProbeRefused): value.send(roster.REQUEST, deadline)
                self.assertEqual(owned.sent, [])

    def test_timeout_poisons_owner_without_retry(self):
        value, owned = active(); owned.send_error = socket.timeout('synthetic private text')
        with self.assertRaises(ProbeRefused) as caught: value.send(roster.REQUEST, 4.0)
        self.assertEqual(str(caught.exception), 'backend'); self.assertTrue(value._poisoned)
        with self.assertRaises(ProbeRefused): value.send(roster.REQUEST, 4.0)
        self.assertEqual(owned.sent, [])

    def test_cancellation_exception_identity_is_preserved_and_poisons_owner(self):
        value, owned = active(); failure = KeyboardInterrupt('synthetic cancellation'); owned.send_error = failure
        with self.assertRaises(KeyboardInterrupt) as caught: value.send(roster.REQUEST, 4.0)
        self.assertIs(caught.exception, failure); self.assertTrue(value._poisoned)

    def test_inherited_close_attempts_original_socket_once_and_forbids_reuse(self):
        value, owned = active(); value.send(roster.REQUEST, 4.0)
        self.assertEqual(value.close(), dict(socket_closed=True, process_handles_closed=True))
        self.assertEqual(value.close(), dict(socket_closed=True, process_handles_closed=True))
        self.assertEqual(owned.closes, 1)
        with self.assertRaises(ProbeRefused): value.recv(1, 4.0)
        self.assertEqual(owned.receives, [])


if __name__ == '__main__': unittest.main()