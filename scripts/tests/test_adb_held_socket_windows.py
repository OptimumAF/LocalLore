"""Original synthetic adapter adversaries; every native and socket seam is fake."""
import copy
import hashlib
import types
import unittest
from unittest.mock import Mock, patch

from benchmarks import adb_held_socket_windows as w
from benchmarks.adb_held_socket import ProbeRefused, REQUEST, TableCapture
from scripts.tests import test_adb_held_socket as f


class FakeApi:
    def __init__(self):
        self.handles = {}
        self.closed = []
        self.next_handle = 100
        self.close_bad = {}
        self.capture_calls = []
        self.open_bad_pid = None

    def open_process(self, pid):
        if pid == self.open_bad_pid:
            raise OSError('synthetic acquisition failure')
        self.next_handle += 1
        self.handles[self.next_handle] = pid
        return self.next_handle

    def identity(self, handle):
        pid = self.handles[handle]
        return copy.deepcopy(f.admission()['server'] if pid == f.SERVER_PID else
                             dict(pid=f.CLIENT_PID, creation_filetime=223456789,
                                  executable='D:\\Synthetic\\client.exe'))

    def alive(self, handle):
        return True

    def close_handle(self, handle):
        self.closed.append(handle)
        result = self.close_bad.get(handle, True)
        if isinstance(result, BaseException):
            raise result
        return result

    def capture(self, family):
        self.capture_calls.append(family)
        return TableCapture(family, b'\0' * 4, 4)


class FakeSocket:
    def __init__(self):
        self.handle = 55
        self.local = ('127.0.0.1', f.CLIENT_PORT)
        self.peer = ('127.0.0.1', 5037)
        self.timeouts = []
        self.connects = []
        self.sends = []
        self.receives = []
        self.close_calls = 0
        self.close_error = None
        self.send_error = None
        self.connect_error = None
        self.reply = b'OKAY'

    def fileno(self): return self.handle
    def getsockname(self): return self.local
    def getpeername(self): return self.peer
    def settimeout(self, value): self.timeouts.append(value)
    def connect(self, endpoint):
        self.connects.append(endpoint)
        if self.connect_error: raise self.connect_error
    def sendall(self, value):
        self.sends.append(value)
        if self.send_error: raise self.send_error
    def recv(self, limit):
        self.receives.append(limit)
        return self.reply
    def close(self):
        self.close_calls += 1
        if self.close_error: raise self.close_error
        self.handle = -1


def backend():
    value = w.WindowsBackend()
    api = FakeApi()
    value._make_api = lambda: api
    value._current_pid = lambda: f.CLIENT_PID
    value.now = lambda: 100.0
    value._pin_file = lambda deadline: copy.deepcopy(f.admission()['adb_file'])
    return value, api


class AdapterTests(unittest.TestCase):
    def opened(self):
        value, api = backend()
        value.open(f.admission(), 103.0)
        def synthetic_cleanup():
            # A failed assertion may leave an invented descriptor in the set.
            # Never let automatic unittest cleanup dispatch it to the real OS.
            with patch.object(w.os, 'close', side_effect=OSError('synthetic cleanup only')):
                value.close()
        self.addCleanup(synthetic_cleanup)
        return value, api

    def connected(self):
        value, api = self.opened()
        sock = FakeSocket()
        with patch.object(w.socket, 'socket', return_value=sock) as factory:
            value.connect(103.0)
            factory.assert_called_once_with(w.socket.AF_INET, w.socket.SOCK_STREAM, w.socket.IPPROTO_TCP)
        return value, api, sock

    def refused(self, reason, call):
        with self.assertRaises(ProbeRefused) as error: call()
        self.assertEqual(error.exception.reason, reason)

    def test_constructor_has_no_io(self):
        with patch.object(w, '_WindowsApi', side_effect=AssertionError('native')), \
             patch.object(w.socket, 'socket', side_effect=AssertionError('socket')), \
             patch.object(w.os, 'open', side_effect=AssertionError('file')):
            self.assertIsNone(w.WindowsBackend()._api)

    def test_partial_process_acquisition_is_closed(self):
        value, api = backend(); api.open_bad_pid = f.CLIENT_PID
        self.refused('backend', lambda: value.open(f.admission(), 103.0))
        self.assertEqual(value.close(), dict(socket_closed=True, process_handles_closed=True))
        self.assertEqual(api.closed, [101])

    def test_failed_final_handle_close_is_not_retried(self):
        value, api = self.opened(); handle = value._handles[0]
        api.close_bad[handle] = False
        first = value.close(); calls = list(api.closed)
        second = value.close()
        self.assertFalse(first['process_handles_closed']); self.assertFalse(second['process_handles_closed'])
        self.assertEqual(api.closed, calls, 'uncertain native handle must never be blindly retried')
        self.assertTrue(set(value._held[name][0] for name in ('server', 'client')) <= set(calls))

    def test_raised_final_handle_close_is_not_retried(self):
        value, api = self.opened(); handle = value._handles[0]
        api.close_bad[handle] = OSError('uncertain close')
        self.assertFalse(value.close()['process_handles_closed']); calls = list(api.closed)
        self.assertFalse(value.close()['process_handles_closed'])
        self.assertEqual(api.closed, calls)

    def test_failed_final_file_close_is_not_retried(self):
        value, api = self.opened(); value._file_fds.update((901, 902))
        def close(fd):
            if fd == 901: raise OSError('uncertain descriptor close')
        with patch.object(w.os, 'close', side_effect=close) as close_file:
            self.assertFalse(value.close()['process_handles_closed'])
            calls = close_file.call_args_list[:]
            self.assertFalse(value.close()['process_handles_closed'])
            self.assertEqual(close_file.call_args_list, calls)
        self.assertEqual({c.args[0] for c in calls}, {901, 902})
        self.assertTrue(set(value._held[name][0] for name in ('server', 'client')) <= set(api.closed))

    def test_failed_fresh_identity_close_remains_uncertain(self):
        value, api = self.opened(); api.close_bad[api.next_handle + 1] = False
        self.refused('identity', lambda: value.bracket(f.admission(), 103.0))
        failed = api.closed[-1]; before = api.closed.count(failed)
        self.assertFalse(value.close()['process_handles_closed'])
        self.assertEqual(api.closed.count(failed), before)

    def test_process_identity_mutation_refuses(self):
        value, api = self.opened(); original = api.identity
        def changed(handle):
            result = original(handle); result['creation_filetime'] += 1; return result
        api.identity = changed
        self.refused('identity', lambda: value.bracket(f.admission(), 103.0))

    def test_process_liveness_requires_exact_true(self):
        for invalid in (False, 1, None):
            with self.subTest(invalid=invalid):
                value, api = backend(); api.alive = lambda handle: invalid
                self.refused('identity', lambda: value.open(f.admission(), 103.0)); value.close()

    def test_snapshot_full_family_roster_once(self):
        value, api = self.opened()
        with patch.object(w, '_check_abi'):
            result = value.snapshot(103.0)
        self.assertEqual(api.capture_calls, [2, 23]); self.assertTrue(result.abi_checked)

    def test_snapshot_truncation_refuses_without_retry(self):
        value, api = self.opened()
        api.capture = Mock(return_value=TableCapture(2, b'\1\0\0\0', 4))
        with patch.object(w, '_check_abi'):
            self.refused('snapshot', lambda: value.snapshot(103.0))
        api.capture.assert_called_once_with(2)

    def test_connect_send_receive_single_socket_and_remaining_budget(self):
        value, api, sock = self.connected()
        value.send(REQUEST, 103.0); self.assertEqual(value.recv(4, 103.0), b'OKAY')
        self.assertEqual(sock.connects, [('127.0.0.1', 5037)])
        self.assertEqual(sock.sends, [REQUEST]); self.assertEqual(sock.receives, [4])
        self.assertEqual(sock.timeouts, [3.0, 3.0, 3.0])
        self.refused('backend', lambda: value.send(REQUEST, 103.0))
        self.assertEqual(sock.sends, [REQUEST])

    def test_failed_connect_never_retries_and_socket_closes(self):
        value, api = self.opened(); sock = FakeSocket(); sock.connect_error = TimeoutError()
        with patch.object(w.socket, 'socket', return_value=sock) as factory:
            self.refused('backend', lambda: value.connect(103.0))
            self.refused('backend', lambda: value.connect(103.0))
            factory.assert_called_once()
        self.assertTrue(value.close()['socket_closed']); self.assertEqual(len(sock.connects), 1)

    def test_partial_send_never_retries(self):
        value, api, sock = self.connected(); sock.send_error = TimeoutError()
        self.refused('backend', lambda: value.send(REQUEST, 103.0))
        self.refused('backend', lambda: value.send(REQUEST, 103.0))
        self.assertEqual(sock.sends, [REQUEST]); self.assertFalse(value._sent)

    def test_socket_object_replacement_refuses_and_closes_original(self):
        value, api, sock = self.connected(); replacement = FakeSocket(); value._socket = replacement
        self.refused('endpoint', lambda: value.endpoint(103.0))
        self.assertTrue(value.close()['socket_closed']); self.assertEqual(sock.close_calls, 1)
        self.assertEqual(replacement.close_calls, 0)

    def test_socket_handle_and_endpoint_mutations_refuse(self):
        for field, changed in (('handle', 99), ('local', ('127.0.0.1', f.CLIENT_PORT + 1)),
                               ('peer', ('127.0.0.1', 5038))):
            with self.subTest(field=field):
                value, api, sock = self.connected(); setattr(sock, field, changed)
                self.refused('endpoint', lambda: value.endpoint(103.0))

    def test_failed_socket_close_does_not_skip_process_handles(self):
        value, api, sock = self.connected(); sock.close_error = OSError('socket close')
        result = value.close()
        self.assertFalse(result['socket_closed']); self.assertTrue(result['process_handles_closed'])
        self.assertFalse(value._handles)

    def test_deadline_expiry_and_rollback_refuse_before_socket(self):
        for clock in (103.0, 99.0, float('nan')):
            with self.subTest(clock=clock):
                value, api = self.opened(); value.now = lambda: clock
                with patch.object(w.socket, 'socket') as factory:
                    self.refused('deadline', lambda: value.connect(103.0))
                    factory.assert_not_called()

    def test_changed_deadline_refuses(self):
        value, api = self.opened()
        self.refused('deadline', lambda: value.bracket(f.admission(), 104.0))

    def test_file_pin_checks_exact_bytes_and_releases_descriptor(self):
        value, api = self.opened(); data = b'synthetic'
        expected = copy.deepcopy(f.admission()['adb_file']); expected['sha256'] = hashlib.sha256(data).hexdigest()
        value._admission['adb_file'] = expected
        info = types.SimpleNamespace(st_dev=3, st_ino=7, st_size=9, st_mtime_ns=100, st_ctime_ns=101, st_birthtime_ns=77)
        with patch.object(value, '_regular_stat', return_value=info), \
             patch.object(w.os, 'open', return_value=911), patch.object(w.os, 'fstat', return_value=info), \
             patch.object(w.os, 'read', side_effect=[data, b'']), patch.object(w.os, 'close') as close:
            result = w.WindowsBackend._pin_file(value, 103.0)
        self.assertEqual(result, expected); close.assert_called_once_with(911); self.assertFalse(value._file_fds)

    def test_file_pin_hash_failure_still_closes_descriptor(self):
        value, api = self.opened()
        info = types.SimpleNamespace(st_dev=3, st_ino=7, st_size=9, st_mtime_ns=100, st_ctime_ns=101, st_birthtime_ns=77)
        with patch.object(value, '_regular_stat', return_value=info), \
             patch.object(w.os, 'open', return_value=912), patch.object(w.os, 'fstat', return_value=info), \
             patch.object(w.os, 'read', side_effect=[b'incorrect', b'']), patch.object(w.os, 'close') as close:
            self.refused('identity', lambda: w.WindowsBackend._pin_file(value, 103.0))
        close.assert_called_once_with(912)

    def test_socket_uncertain_close_is_not_retried(self):
        value, api, sock = self.connected(); sock.close_error = OSError('uncertain socket close')
        self.assertFalse(value.close()['socket_closed'])
        self.assertFalse(value.close()['socket_closed'])
        self.assertEqual(sock.close_calls, 1)

    def test_socket_handle_replacement_is_never_closed_as_owned(self):
        value, api, sock = self.connected(); sock.handle += 1
        result = value.close()
        self.assertFalse(result['socket_closed']); self.assertTrue(result['process_handles_closed'])
        self.assertEqual(sock.close_calls, 0)

    def test_file_pin_failed_close_sticky_and_other_resources_still_close(self):
        value, api = self.opened(); data = b'synthetic'
        value._admission['adb_file']['sha256'] = hashlib.sha256(data).hexdigest()
        info = types.SimpleNamespace(st_dev=3, st_ino=7, st_size=9, st_mtime_ns=100, st_ctime_ns=101, st_birthtime_ns=77)
        with patch.object(value, '_regular_stat', return_value=info), \
             patch.object(w.os, 'open', return_value=913), patch.object(w.os, 'fstat', return_value=info), \
             patch.object(w.os, 'read', side_effect=[data, b'']), \
             patch.object(w.os, 'close', side_effect=OSError('uncertain close')) as close:
            self.refused('identity', lambda: w.WindowsBackend._pin_file(value, 103.0))
            self.assertFalse(value.close()['process_handles_closed'])
            close.assert_called_once_with(913)
        self.assertFalse(value._handles)

    def pin_context(self, value, path_info, held_infos, blocks):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch.object(value, '_regular_stat',
                                        **({'side_effect':path_info} if type(path_info) is list else {'return_value':path_info})))
        stack.enter_context(patch.object(w.os, 'open', return_value=914))
        stack.enter_context(patch.object(w.os, 'fstat', side_effect=held_infos))
        stack.enter_context(patch.object(w.os, 'read', side_effect=blocks))
        stack.enter_context(patch.object(w.os, 'close'))
        return stack

    def pin_fixture(self, *, held_ctime=202, held_birth=77, path_birth=77):
        value, api = self.opened(); data = b'synthetic'
        value._admission['adb_file']['sha256'] = hashlib.sha256(data).hexdigest()
        path_info = types.SimpleNamespace(st_dev=3, st_ino=7, st_size=9, st_mtime_ns=100,
                                          st_ctime_ns=101, st_birthtime_ns=path_birth)
        held_info = types.SimpleNamespace(st_dev=3, st_ino=7, st_size=9, st_mtime_ns=100,
                                          st_ctime_ns=held_ctime, st_birthtime_ns=held_birth)
        return value, data, path_info, held_info

    def test_same_birthtime_separately_stable_different_ctimes_are_accepted(self):
        value, data, path_info, held_info = self.pin_fixture()
        with self.pin_context(value,path_info,[held_info,held_info],[data,b'']):
            result = w.WindowsBackend._pin_file(value,103.0)
        self.assertEqual(result,value._admission['adb_file'])
        self.assertEqual(result['identity'][-1],101, 'PATH5 admission is preserved exactly')

    def test_missing_cross_api_birthtime_refuses_without_fallback(self):
        value, data, path_info, held_info = self.pin_fixture(held_ctime=101)
        del held_info.st_birthtime_ns
        with self.pin_context(value,path_info,[held_info,held_info],[data,b'']):
            self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))

    def test_mismatched_cross_api_birthtime_refuses(self):
        value, data, path_info, held_info = self.pin_fixture(held_ctime=101,held_birth=78)
        with self.pin_context(value,path_info,[held_info,held_info],[data,b'']):
            self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))

    def test_held_ctime_mutation_during_read_refuses(self):
        value, data, path_info, held_info = self.pin_fixture()
        changed = copy.deepcopy(held_info); changed.st_ctime_ns += 1
        with self.pin_context(value,path_info,[held_info,changed],[data,b'']):
            self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))

    def test_held_ctime_mutation_across_brackets_refuses(self):
        value, data, path_info, held_info = self.pin_fixture()
        changed = copy.deepcopy(held_info); changed.st_ctime_ns += 1
        with self.pin_context(value,path_info,[held_info,held_info,changed,changed],[data,b'',data,b'']):
            self.assertEqual(w.WindowsBackend._pin_file(value,103.0),value._admission['adb_file'])
            self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))

    def test_birthtime_missing_or_malformed_on_either_api_refuses(self):
        for api_name in ('path','held'):
            for bad in (None,True,77.0,-1):
                with self.subTest(api=api_name,birth=bad):
                    value, data, path_info, held_info = self.pin_fixture()
                    selected = path_info if api_name == 'path' else held_info
                    if bad is None: del selected.st_birthtime_ns
                    else: selected.st_birthtime_ns = bad
                    with self.pin_context(value,path_info,[held_info,held_info],[data,b'']):
                        self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))

    def test_shared_cross_api_identity_fields_must_match(self):
        for field in ('st_dev','st_ino','st_size','st_mtime_ns'):
            with self.subTest(field=field):
                value, data, path_info, held_info = self.pin_fixture()
                setattr(held_info,field,getattr(held_info,field)+1)
                with self.pin_context(value,path_info,[held_info,held_info],[data,b'']):
                    self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))

    def test_each_api_identity_field_mutation_during_read_refuses(self):
        for api_name in ('path','held'):
            for field in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_birthtime_ns'):
                with self.subTest(api=api_name,field=field):
                    value, data, path_info, held_info = self.pin_fixture()
                    path_after = copy.deepcopy(path_info); held_after = copy.deepcopy(held_info)
                    selected = path_after if api_name == 'path' else held_after
                    setattr(selected,field,getattr(selected,field)+1)
                    with self.pin_context(value,[path_info,path_after],[held_info,held_after],[data,b'']):
                        self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))

    def test_changed_birthtime_on_both_apis_across_brackets_refuses(self):
        value, data, path_info, held_info = self.pin_fixture()
        path_changed = copy.deepcopy(path_info); path_changed.st_birthtime_ns += 1
        held_changed = copy.deepcopy(held_info); held_changed.st_birthtime_ns += 1
        with self.pin_context(value,[path_info,path_info,path_changed,path_changed],
                              [held_info,held_info,held_changed,held_changed],[data,b'',data,b'']):
            self.assertEqual(w.WindowsBackend._pin_file(value,103.0),value._admission['adb_file'])
            self.refused('identity',lambda:w.WindowsBackend._pin_file(value,103.0))


if __name__ == '__main__': unittest.main()
