"""Bounded Windows TCP table decoding for host diagnostics, not SDK admission.

This module performs no OS calls, I/O, socket operations or inference. A decoded
row or LISTEN state alone proves neither process ownership nor a usable service.
Unknown state values are retained and are never interpreted as LISTEN.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from dataclasses import dataclass
import ipaddress
import struct

AF_INET = 2
AF_INET6 = 23
MAX_CAPTURE = 1024 * 1024
MAX_ROWS = 16384
_ROW4 = struct.Struct("<6I")
_ROW6 = struct.Struct("<16sII16sIIII")


class ObservationRefused(ValueError):
    def __init__(self, reason):
        self.reason = reason if reason in ("bounds", "layout", "family") else "layout"
        super().__init__(self.reason)


@dataclass(frozen=True, slots=True)
class TcpRow:
    family: int
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    state: int
    pid: int
    local_scope_id: int = 0
    remote_scope_id: int = 0


def _port(value):
    # The port occupies the low 16 bits in network byte order inside a DWORD.
    return int.from_bytes((value & 0xffff).to_bytes(2, "little"), "big")


def decode_table(raw: bytes, family: int) -> tuple[TcpRow, ...]:
    """Decode the DWORD-aligned OWNER_PID ABI after the caller verifies layout.

    Header offset4 and row sizes24/56 are explicit. Native callers must verify
    their structure offsets/strides, rather than guess an alternate layout.
    Unused returned buffer capacity is not another row and grants no authority.
    """
    if type(family) is not int or family not in (AF_INET, AF_INET6):
        raise ObservationRefused("family")
    if type(raw) is not bytes or not 4 <= len(raw) <= MAX_CAPTURE:
        raise ObservationRefused("bounds")
    count = struct.unpack_from("<I", raw)[0]
    if count > MAX_ROWS:
        raise ObservationRefused("bounds")
    row = _ROW4 if family == AF_INET else _ROW6
    if 4 + count * row.size > len(raw):
        raise ObservationRefused("layout")
    result = []
    for offset in range(4, 4 + count * row.size, row.size):
        if family == AF_INET:
            state, local, local_port, remote, remote_port, pid = row.unpack_from(raw, offset)
            result.append(TcpRow(family,
                str(ipaddress.IPv4Address(local.to_bytes(4, "little"))), _port(local_port),
                str(ipaddress.IPv4Address(remote.to_bytes(4, "little"))), _port(remote_port),
                state, pid))
        else:
            local, local_scope, local_port, remote, remote_scope, remote_port, state, pid = row.unpack_from(raw, offset)
            result.append(TcpRow(family, str(ipaddress.IPv6Address(local)), _port(local_port),
                str(ipaddress.IPv6Address(remote)), _port(remote_port), state, pid,
                local_scope, remote_scope))
    return tuple(result)


def has_listen_state(row: TcpRow) -> bool:
    """Test only the raw state field; never qualify an endpoint or service."""
    return type(row) is TcpRow and type(row.state) is int and row.state == 2
