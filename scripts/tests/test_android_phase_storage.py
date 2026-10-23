"""Fixed Android /data output and independent device-identity refusal cases."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_phase_storage as storage


OBSERVED = (b"Filesystem       1K-blocks    Used Available Use% Mounted on\r\n"
            b"/dev/block/dm-46   6082144 4242236   1697696  72% /data/user/0\r\n")


class PhaseStorageTest(unittest.TestCase):
    def test_observed_alias_and_same_device(self):
        self.assertEqual(storage.parse_df(OBSERVED, 123, 123),
                         {"version": 1, "available_bytes": 1_738_440_704,
                          "display_mount": "/data/user/0"})

    def test_requested_mount_and_lf(self):
        raw = OBSERVED.replace(b"\r\n", b"\n").replace(b"/data/user/0", b"/data")
        self.assertEqual(storage.parse_df(raw, 123, 123)["available_bytes"], 1_738_440_704)

    def test_alias_device_mismatch(self):
        self.assertIsNone(storage.parse_df(OBSERVED, 123, 456))

    def test_invalid_device_facts(self):
        for left, right in ((True, True), (123, True), (0, 0), (-1, -1),
                            ("123", "123"), (2 ** 63, 2 ** 63), (1.0, 1.0)):
            with self.subTest(left=left, right=right):
                self.assertIsNone(storage.parse_df(OBSERVED, left, right))

    def test_unknown_mount_and_filesystem(self):
        for raw in (OBSERVED.replace(b"/data/user/0", b"/storage/emulated/0"),
                    OBSERVED.replace(b"/data/user/0", b"/data/user/0/"),
                    OBSERVED.replace(b"/dev/block/dm-46", b"untrusted")):
            self.assertIsNone(storage.parse_df(raw, 123, 123))

    def test_numeric_refusals(self):
        for value in (b"-1", b"+1", b"1.0", b"unknown", b"1,000", b"01",
                      b"9007199254740992", b"9999999999999999999999"):
            with self.subTest(value=value):
                self.assertIsNone(storage.parse_df(OBSERVED.replace(b"1697696", value), 123, 123))
        for raw in (OBSERVED.replace(b"1697696", b"6082145"),
                    OBSERVED.replace(b"4242236", b"6082144"),
                    OBSERVED.replace(b"6082144", b"0"),
                    OBSERVED.replace(b"72%", b"101%"),
                    OBSERVED.replace(b"72%", b"-1%")):
            self.assertIsNone(storage.parse_df(raw, 123, 123))

    def test_framing_and_fields(self):
        for raw in (OBSERVED + OBSERVED, b"chatter\n" + OBSERVED, OBSERVED[:-2],
                    OBSERVED.replace(b"\r\n", b"\n", 1),
                    OBSERVED.replace(b"\r\n", b"\r\r\n"),
                    OBSERVED.replace(b"Available", b"Free"),
                    OBSERVED.replace(b"  72%", b" extra 72%"),
                    OBSERVED.replace(b"dm-46", b"dm-\x0046"), b"x" * 2049, "text"):
            self.assertIsNone(storage.parse_df(raw, 123, 123))

    def test_zero_available_is_a_fact_not_admission(self):
        result = storage.parse_df(OBSERVED.replace(b"1697696", b"0"), 123, 123)
        self.assertEqual(result["available_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
