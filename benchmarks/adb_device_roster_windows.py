"""Fixed roster IO on the unchanged held Windows resource owner.

Import/construction does no IO. This permits only one devices-l request; it
never launches an ADB executable, selects a device or changes a service.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks.adb_device_roster import REQUEST, MAX_RESPONSE
from benchmarks.adb_held_socket_windows import WindowsBackend, _need


class WindowsRosterBackend(WindowsBackend):
    """Retain legacy ownership/poison/closure; enlarge only fixed roster IO."""
    def send(self, data, deadline):
        def action():
            _need(self._connected and not self._send_called and type(data) is bytes and data == REQUEST)
            self._send_called = True
            self._read_endpoint()
            owned = self._owned_socket()
            owned.settimeout(self._remaining(deadline))
            owned.sendall(REQUEST)
            self._sent = True
        return self._operation(deadline, action)

    def recv(self, limit, deadline):
        def action():
            _need(self._sent and type(limit) is int and 1 <= limit <= MAX_RESPONSE + 1)
            self._read_endpoint()
            owned = self._owned_socket()
            owned.settimeout(self._remaining(deadline))
            data = owned.recv(limit)
            _need(type(data) is bytes and len(data) <= limit)
            return data
        return self._operation(deadline, action)