"""Independent literal phone measurements and shell-v2 grammar adversaries."""
import struct
import unittest

from benchmarks import physical_phone_inventory as inventory
from scripts.tests import test_physical_phone_inventory as fixture


class PhoneInventoryFactsTests(unittest.TestCase):
    def test_literal_measurements_preserve_units_and_do_not_claim_eligibility(self):
        expected = dict(current_user=0, properties={
            'ro.build.fingerprint': 'original/vendor/device:15/BUILD/1:user/release-keys',
            'ro.product.model': 'Original Phone', 'ro.build.version.sdk': '35',
            'ro.soc.model': 'Original SoC', 'ro.board.platform': 'original_board',
            'ro.product.cpu.abilist': 'arm64-v8a,armeabi-v7a', 'ro.kernel.qemu': '0'},
            page_bytes=4096, memory_total_bytes=8*1024**3,
            memory_available_bytes=4*1024**3, internal_free_bytes=4096000000,
            battery=dict(usb_powered=True, level=73, scale=100, temperature_tenths_celsius=315),
            thermal_status=2)
        self.assertEqual(inventory.parse_facts(fixture.FACT_BYTES), expected)
        changed = inventory.parse_facts(fixture.FACT_BYTES)
        changed['properties']['ro.product.model'] = 'MUTATED'
        self.assertEqual(inventory.parse_facts(fixture.FACT_BYTES), expected)
        raw = fixture.FACT_BYTES.replace(b'Original Phone', 'Original café Phone'.encode('utf-8'))
        self.assertEqual(inventory.parse_facts(raw)['properties']['ro.product.model'], 'Original café Phone')

    def test_missing_duplicate_reordered_or_injected_sections_are_not_partial_facts(self):
        raw = fixture.FACT_BYTES
        invalid = [raw[:-1], raw+b'\n', raw.replace(b'PAGE\n', b'PAGE\nPAGE\n'),
            raw.replace(b'USER\n0\n', b'USER\n10\n'), raw.replace(b'USER\n', b'USER\nunknown\n'),
            raw.replace(b'PROPERTIES\n', b'PROPERTIES\nro.extra=private\n'),
            raw.replace(b'ro.soc.model=Original SoC\n', b''),
            raw.replace(b'Original Phone', b'Original\x00Phone'),
            raw.replace(b'LLPI_V1', b'LLPI_V2'), b'\xff', b'x'*32769]
        for index, value in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ValueError):
                inventory.parse_facts(value)
        for value in (None, True, bytearray(raw), raw.decode('utf-8')):
            with self.subTest(kind=type(value).__name__), self.assertRaises(ValueError):
                inventory.parse_facts(value)

    def test_numeric_consistency_unknown_units_and_emulator_claims_refuse(self):
        mutations = [(b'4096\nMEMORY', b'6000\nMEMORY'), (b'4096\nMEMORY', b'0\nMEMORY'),
            (b'4194304 kB', b'999999999 kB'), (b'8388608 kB', b'8388608 MB'),
            (b'MemAvailable: 4194304 kB', b'MemTotal: 4194304 kB'),
            (b'1000000|4096', b'9223372036854775807|4096'),
            (b'1000000|4096', b'1000000|0'), (b'level: 73', b'level: 101'),
            (b'scale: 100', b'scale: 70'), (b'USB powered: true', b'USB powered: 1'),
            (b'temperature: 315', b'temperature: 2001'), (b'Thermal Status: 2', b'Thermal Status: 7'),
            (b'ro.kernel.qemu=0', b'ro.kernel.qemu=1'),
            (b'arm64-v8a,armeabi-v7a', b'arm64-v8a,arm64-v8a')]
        for old, new in mutations:
            with self.subTest(field=old), self.assertRaises(ValueError):
                inventory.parse_facts(fixture.FACT_BYTES.replace(old, new))

    def test_shell_v2_packet_boundaries_and_split_stdout_preserve_exact_facts(self):
        raw = fixture.FACT_BYTES
        prefix = b'OKAY'+struct.pack('<Q', 7)+b'OKAY'
        wire = prefix+b''.join(fixture.packet(1, raw[i:i+13]) for i in range(0, len(raw), 13))
        wire += fixture.packet(2, b'')+fixture.packet(3, b'\x00')
        self.assertEqual(inventory.decode_wire(wire, 7), inventory.parse_facts(raw))
        self.assertEqual(inventory.decode_wire(fixture.response(), 7), inventory.parse_facts(raw))
        for target in (True, 0, -1, 8, 2**64):
            with self.subTest(target=target), self.assertRaises(ValueError):
                inventory.decode_wire(wire, target)

    def test_unknown_post_exit_short_header_length_and_exit_shape_refuse(self):
        prefix = b'OKAY'+struct.pack('<Q', 7)+b'OKAY'
        payload = fixture.packet(1, fixture.FACT_BYTES)
        endings = [b'', b'\x03', b'\x03\x01\x00\x00', fixture.packet(3, b''),
            fixture.packet(3, b'\x00\x00'), fixture.packet(3, b'\x01'),
            fixture.packet(4, b''), fixture.packet(0, b'x'),
            fixture.packet(3, b'\x00')+fixture.packet(1, b''),
            fixture.packet(3, b'\x00')+fixture.packet(3, b'\x00')]
        for ending in endings:
            with self.subTest(ending=ending.hex()), self.assertRaises(ValueError):
                inventory.decode_wire(prefix+payload+ending, 7)
        for raw in (prefix+b'\x01'+struct.pack('<I', 32769)+b'x',
                    prefix+fixture.packet(1, b'x'*32769)+fixture.packet(3, b'\x00'),
                    prefix+payload+fixture.packet(2, b'x'*4097)+fixture.packet(3, b'\x00'),
                    prefix+payload+fixture.packet(2, b'warning')+fixture.packet(3, b'\x00'),
                    prefix+payload+fixture.packet(1, b'')*256+fixture.packet(3, b'\x00')):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                inventory.decode_wire(raw, 7)


if __name__ == '__main__': unittest.main()
