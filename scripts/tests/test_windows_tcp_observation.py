"""Original binary Windows TCP fixtures; no OS, network, SDK or device calls.

Decoded LISTEN state is one observation only. It cannot establish service,
process ownership, listener identity, authorization or safe SDK admission.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from dataclasses import FrozenInstanceError
import ipaddress
import struct
from types import SimpleNamespace
import unittest

from benchmarks import windows_tcp_observation as t


def port(value, high=0):
    """A Windows DWORD whose least16 bits contain the network-order port."""
    return (high << 16) | int.from_bytes(value.to_bytes(2, 'big'), 'little')


def row4(*, local='127.0.0.1', local_port=5037, remote='0.0.0.0', remote_port=0,
         state=2, pid=401, high=0):
    address = lambda value: int.from_bytes(ipaddress.IPv4Address(value).packed, 'little')
    return struct.pack('<6I', state, address(local), port(local_port, high),
                       address(remote), port(remote_port, high), pid)


def row6(*, local='::1', local_port=5037, remote='::', remote_port=0, state=2,
         pid=402, local_scope=0, remote_scope=0, high=0):
    scope = lambda value: int.from_bytes(value.to_bytes(4, 'big'), 'little')
    return struct.pack('<16sII16sIIII', ipaddress.IPv6Address(local).packed,
                       scope(local_scope), port(local_port, high), ipaddress.IPv6Address(remote).packed,
                       scope(remote_scope), port(remote_port, high), state, pid)


def table(*rows, capacity=b''):
    return struct.pack('<I', len(rows)) + b''.join(rows) + capacity


class WindowsTcpObservationTests(unittest.TestCase):
    def refuse(self, raw, family, reason):
        with self.assertRaises(t.ObservationRefused) as caught:
            t.decode_table(raw, family)
        self.assertEqual(str(caught.exception), reason)

    def test_published_limits_and_empty_tables(self):
        self.assertEqual((t.AF_INET, t.AF_INET6), (2, 23))
        self.assertEqual((t.MAX_CAPTURE, t.MAX_ROWS), (1048576, 16384))
        for family in (t.AF_INET, t.AF_INET6):
            with self.subTest(family=family):
                self.assertEqual(t.decode_table(table(), family), ())

    def test_ipv4_state_is_first_dword_not_zeroed_padding(self):
        rows = t.decode_table(table(row4()), t.AF_INET)
        self.assertEqual(rows, (t.TcpRow(2, '127.0.0.1', 5037, '0.0.0.0', 0, 2, 401),))
        self.assertTrue(t.has_listen_state(rows[0]))
        self.assertEqual((rows[0].local_scope_id, rows[0].remote_scope_id), (0, 0))

    def test_ipv6_state_and_pid_follow_both_endpoints(self):
        raw = row6(local='2001:db8::1234', local_port=8443, remote='2001:db8::8',
                   remote_port=443, state=5, pid=4294967295)
        rows = t.decode_table(table(raw), t.AF_INET6)
        self.assertEqual(rows, (t.TcpRow(23, '2001:db8::1234', 8443,
                                       '2001:db8::8', 443, 5, 4294967295),))
        self.assertFalse(t.has_listen_state(rows[0]))

    def test_ipv6_scope_dwords_are_preserved_without_address_suffixes(self):
        rows = t.decode_table(table(row6(local='fe80::1', remote='fe80::2',
                                         local_scope=7, remote_scope=4294967295)), t.AF_INET6)
        self.assertEqual(rows[0].local_address, 'fe80::1')
        self.assertEqual(rows[0].remote_address, 'fe80::2')
        self.assertEqual(rows[0].local_scope_id, 7)
        self.assertEqual(rows[0].remote_scope_id, 4294967295)
        self.assertNotIn('%', rows[0].local_address)
        self.assertTrue(t.has_listen_state(rows[0]))

    def test_ipv6_scope_uses_all32_network_order_bits(self):
        raw = row6(local_scope=42, remote_scope=0x12345678)
        self.assertEqual(raw[16:20], b'\x00\x00\x00\x2a')
        self.assertEqual(raw[40:44], b'\x12\x34\x56\x78')
        row = t.decode_table(table(raw), t.AF_INET6)[0]
        self.assertEqual((row.local_scope_id, row.remote_scope_id), (42, 0x12345678))

    def test_ports_decode_low16_network_order_for_both_families(self):
        for family, make in ((t.AF_INET, row4), (t.AF_INET6, row6)):
            for local, remote in ((0, 65535), (1, 256), (255, 5037), (8443, 443)):
                with self.subTest(family=family, local=local, remote=remote):
                    rows = t.decode_table(table(make(local_port=local, remote_port=remote, high=0xabcd)), family)
                    self.assertEqual((rows[0].local_port, rows[0].remote_port), (local, remote))

    def test_ipv4_address_bytes_do_not_reverse_network_octets(self):
        for local, remote in (('0.0.0.0', '255.255.255.255'), ('192.0.2.19', '198.51.100.77')):
            with self.subTest(local=local):
                row = t.decode_table(table(row4(local=local, remote=remote)), t.AF_INET)[0]
                self.assertEqual((row.local_address, row.remote_address), (local, remote))

    def test_each_family_uses_its_own_row_stride_and_retains_order(self):
        for family, make in ((t.AF_INET, row4), (t.AF_INET6, row6)):
            rows = t.decode_table(table(*(make(state=s, pid=100+i) for i, s in enumerate((5, 0, 2, 12)))), family)
            with self.subTest(family=family):
                self.assertEqual([r.state for r in rows], [5, 0, 2, 12])
                self.assertEqual([r.pid for r in rows], [100, 101, 102, 103])
                self.assertEqual([t.has_listen_state(r) for r in rows], [False, False, True, False])

    def test_unknown_and_future_states_are_never_promoted_to_listen(self):
        for family, make in ((t.AF_INET, row4), (t.AF_INET6, row6)):
            states = (0, 1, 3, 5, 12, 255, 4294967295)
            rows = t.decode_table(table(*(make(state=value) for value in states)), family)
            with self.subTest(family=family):
                self.assertEqual(tuple(r.state for r in rows), states)
                self.assertFalse(any(t.has_listen_state(r) for r in rows))

    def test_trailing_capacity_is_not_a_second_row_or_listener(self):
        for family, make in ((t.AF_INET, row4), (t.AF_INET6, row6)):
            with self.subTest(family=family):
                self.assertEqual(t.decode_table(table(capacity=make(state=2)), family), ())
                rows = t.decode_table(table(make(state=0), capacity=make(state=2)+b'\xff'*17), family)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0].state, 0)
                self.assertFalse(t.has_listen_state(rows[0]))

    def test_exact_capture_cap_allows_only_declared_rows(self):
        raw = table(capacity=b'\x00'*(t.MAX_CAPTURE-4))
        for family in (t.AF_INET, t.AF_INET6):
            with self.subTest(family=family):
                self.assertEqual(t.decode_table(raw, family), ())
                self.refuse(raw+b'\x00', family, 'bounds')

    def test_exact_row_cap_fits_and_one_more_refuses_even_with_full_bytes(self):
        for family, make in ((t.AF_INET, row4), (t.AF_INET6, row6)):
            payload = make(state=0)
            with self.subTest(family=family):
                rows = t.decode_table(struct.pack('<I', t.MAX_ROWS)+payload*t.MAX_ROWS, family)
                self.assertEqual(len(rows), t.MAX_ROWS)
                self.assertFalse(any(t.has_listen_state(r) for r in rows))
                self.refuse(struct.pack('<I', t.MAX_ROWS+1)+payload*(t.MAX_ROWS+1), family, 'bounds')

    def test_declared_rows_must_fit_the_selected_family_layout(self):
        for family, make in ((t.AF_INET, row4), (t.AF_INET6, row6)):
            for raw in (struct.pack('<I', 1), table(make())[:-1],
                        struct.pack('<I', 2)+make(), table(make(), make())[:-1]):
                with self.subTest(family=family, size=len(raw)):
                    self.refuse(raw, family, 'layout')

    def test_short_header_and_nonbytes_capture_refuse_with_fixed_reason(self):
        for raw in (b'', b'\x00', b'\x00\x00', b'\x00\x00\x00', None, '', 4,
                    bytearray(table()), memoryview(table()), [0, 0, 0, 0]):
            with self.subTest(kind=type(raw).__name__):
                self.refuse(raw, t.AF_INET, 'bounds')

    def test_family_is_exact_known_integer_and_checked_before_capture(self):
        for family in (None, True, False, 0, 1, 22, 24, -1, 2.0, '2', b'2', [], {}):
            with self.subTest(family=repr(family)):
                self.refuse(table(), family, 'family')
                self.refuse(None, family, 'family')

    def test_listen_predicate_refuses_forged_rows_subclasses_and_boolean_state(self):
        class RowSubclass(t.TcpRow):
            pass

        for value in (None, {}, {'state': 2}, SimpleNamespace(state=2),
                      RowSubclass(2, '127.0.0.1', 5037, '0.0.0.0', 0, 2, 1),
                      t.TcpRow(2, '127.0.0.1', 5037, '0.0.0.0', 0, True, 1),
                      t.TcpRow(2, '127.0.0.1', 5037, '0.0.0.0', 0, 2.0, 1),
                      t.TcpRow(2, '127.0.0.1', 5037, '0.0.0.0', 0, '2', 1)):
            with self.subTest(kind=type(value).__name__):
                self.assertIs(t.has_listen_state(value), False)

    def test_listen_predicate_does_not_claim_endpoint_or_process_ownership(self):
        observation = t.TcpRow(2, '192.0.2.1', 4444, '198.51.100.2', 5555, 2, 0)
        self.assertIs(t.has_listen_state(observation), True)
        self.assertEqual(observation.pid, 0)  # A separate owner guard is still required.

    def test_decoded_tuple_and_rows_are_immutable(self):
        rows = t.decode_table(table(row4()), t.AF_INET)
        self.assertIs(type(rows), tuple)
        self.assertIs(type(rows[0]), t.TcpRow)
        with self.assertRaises(TypeError):
            rows[0] = rows[0]
        with self.assertRaises(FrozenInstanceError):
            rows[0].state = 2


if __name__ == '__main__':
    unittest.main()
