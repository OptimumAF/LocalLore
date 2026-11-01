"""Fixed USB transport/inventory IO on the unchanged held Windows owner.

No import/construction IO. No ADB executable, lifecycle, arbitrary shell/query,
backend selection or public socket access is introduced.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks.physical_phone_inventory import (
    TPORT_REQUEST, SHELL_REQUEST, CLOSE_STDIN, MAX_WIRE, InventoryReceiveRefused,
)
from benchmarks.adb_held_socket import ProbeRefused
from benchmarks.adb_held_socket_windows import WindowsBackend, _need


class WindowsPhoneInventoryBackend(WindowsBackend):
    """Only three code-fixed sends; inherit identity, endpoint and close guards."""
    def __init__(self):
        super().__init__()
        self._inventory_send_index = 0

    def send(self, data, deadline):
        def action():
            sequence = (TPORT_REQUEST, SHELL_REQUEST, CLOSE_STDIN)
            index = self._inventory_send_index
            _need(self._connected and type(index) is int and 0 <= index < len(sequence)
                  and type(data) is bytes and data == sequence[index])
            # A partially transmitted send is spent, never retried.
            self._inventory_send_index += 1
            self._send_called = True
            self._read_endpoint()
            owned = self._owned_socket()
            owned.settimeout(self._remaining(deadline))
            owned.sendall(sequence[index])
            self._sent = True
        return self._operation(deadline, action)

    def recv(self, limit, deadline):
        received = None
        def action():
            nonlocal received
            _need(self._sent and type(limit) is int and 1 <= limit <= MAX_WIRE + 1)
            self._read_endpoint()
            owned = self._owned_socket()
            owned.settimeout(self._remaining(deadline))
            data = owned.recv(limit)
            if type(data) is bytes:
                received = data[:MAX_WIRE + 1]
            _need(type(data) is bytes and len(data) <= limit)
            self._read_endpoint()
            return data
        try:
            return self._operation(deadline, action)
        except BaseException as error:
            if received is None:
                raise
            reason = (error.reason if isinstance(error, ProbeRefused) else
                      'cancelled' if isinstance(error, (KeyboardInterrupt, InterruptedError)) else 'backend')
            raise InventoryReceiveRefused(reason, received) from None