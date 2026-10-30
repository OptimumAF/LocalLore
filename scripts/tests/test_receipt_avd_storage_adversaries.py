"""Original monotonic-charge regression using retained, tiny D-only files.

No SDK, real registry, guest, image retirement or deletion is performed.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_storage as storage


class ClosedChargeAdversaries(unittest.TestCase):
    def test_repeated_closure_cannot_release_the_previous_closed_charge(self):
        # Scale the 40/64 accounting ratio, not the production entry points.
        # Retain this isolated namespace for the source-bound failure capture.
        base = Path(tempfile.mkdtemp(prefix="locallore-closed-charge-", dir="D:/Dev/_Temp"))
        self.assertEqual(base.drive.upper(), "D:")
        registry, root, other = base / "registry", base / "closed", base / "other"
        digest = "6" * 64
        with patch.object(storage, "RESERVATION_BYTES", 4000), \
                patch.object(storage, "BUDGET_BYTES", 6400):
            storage.reserve_prepare(root, digest, registry)
            image = root / storage.CONTENT / "userdata-qemu.img"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"original synthetic image\n" * 120)
            closure = root / "verified-closure.json"
            closure.write_bytes(storage.encoded(dict(proposal_sha256=digest,
                closure_verified=True, cleanup_complete=True)))
            storage.record_closed(root, closure, registry)
            ledger_path = registry / "ledger-v1.json"
            first = storage.read_json(ledger_path)["entries"][0]
            measured = image.stat().st_size + closure.stat().st_size
            self.assertEqual(first["state"], "closed")
            self.assertEqual(first["reserved_bytes"], measured)
            self.assertLess(measured, storage.RESERVATION_BYTES)
            self.assertGreater(measured + storage.RESERVATION_BYTES, storage.BUDGET_BYTES)

            # External truncation is observable, but does not establish retirement.
            # Keep both the image path and the exact verified closure in place.
            image.write_bytes(b"shorter synthetic bytes")
            storage.record_closed(root, closure, registry)
            second = storage.read_json(ledger_path)["entries"][0]
            with self.subTest(invariant="previous closed charge remains the floor"):
                self.assertGreaterEqual(second["reserved_bytes"], first["reserved_bytes"])
            with self.subTest(invariant="shrinking cannot fund another reservation"):
                with self.assertRaisesRegex(storage.StorageRefused, "^storage_capacity_exceeded$"):
                    storage.reserve_prepare(other, digest, registry)
            self.assertFalse(other.exists())
            self.assertTrue(image.is_file())
            self.assertEqual(storage.binding(closure), first["closure"])


if __name__ == "__main__":
    unittest.main()
