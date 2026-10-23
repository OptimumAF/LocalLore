# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Guard tests use only disposable synthetic databases; actual Host proof is explicit."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("capacity_padding_probe", Path(__file__).resolve().parents[1] / "capacity_padding_probe.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class CapacityPaddingGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.owner = "a" * 32
        self.directory = Path(self.temp.name).resolve() / ("capacity-relief-" + self.owner)
        self.directory.mkdir()
        (self.directory / ".capacity-owner").write_text(self.owner, encoding="ascii")
        self.database = self.directory / "stories.sqlite"
        self.connection = sqlite3.connect(str(self.database), isolation_level=None)
        self.addCleanup(self.connection.close)
        self.connection.executescript(PROBE.SCHEMA.read_text(encoding="utf-8"))
        self.connection.execute("PRAGMA application_id=1280069458")
        self.connection.execute("PRAGMA user_version=1")

    def rejected(self, stage, action="fill", owner=None):
        with self.assertRaisesRegex(PROBE.Rejected, "^" + stage + "$"):
            PROBE.execute(str(self.directory), self.owner if owner is None else owner, action)

    def padding(self, owner=None, malformed=False):
        self.connection.execute(PROBE.CREATE if not malformed else "CREATE TABLE locallore_capacity_pad_v1 (owner TEXT)")
        if not malformed:
            self.connection.execute("INSERT INTO locallore_capacity_pad_v1 (owner,payload) VALUES (?,zeroblob(3500))", (self.owner if owner is None else owner,))

    def test_invalid_owner_cannot_open_or_create(self):
        self.rejected("owner", owner="bad")

    def test_marker_mismatch_refuses_before_database_access(self):
        (self.directory / ".capacity-owner").write_text("b" * 32, encoding="ascii")
        self.rejected("marker")

    def test_missing_database_is_not_created(self):
        self.connection.close()
        self.database.unlink()
        self.rejected("database")
        self.assertFalse(self.database.exists())

    def test_foreign_identity_is_preserved(self):
        self.connection.execute("PRAGMA application_id=99")
        self.rejected("identity")
        self.assertEqual(self.connection.execute("PRAGMA application_id").fetchone()[0], 99)

    def test_future_schema_version_is_preserved(self):
        self.connection.execute("PRAGMA user_version=2")
        self.rejected("identity")
        self.assertEqual(self.connection.execute("PRAGMA user_version").fetchone()[0], 2)

    def test_wal_is_not_silently_changed(self):
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.rejected("journal")
        self.assertEqual(self.connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_altered_schema_is_not_adopted(self):
        self.connection.execute("CREATE TABLE unrelated_fixture(value TEXT)")
        self.rejected("schema")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM unrelated_fixture").fetchone()[0], 0)

    def test_existing_padding_is_not_overwritten_by_fill(self):
        self.padding()
        self.rejected("schema")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM locallore_capacity_pad_v1").fetchone()[0], 1)

    def test_wrong_initial_page_profile_never_creates_padding(self):
        self.rejected("initial_pages")
        self.assertNotIn(PROBE.TABLE, [row[1] for row in PROBE.rows(self.connection)])

    def test_wrong_padding_owner_cannot_be_removed(self):
        self.padding(owner="b" * 32)
        self.rejected("padding_owner", "remove")
        self.assertEqual(self.connection.execute("SELECT owner FROM locallore_capacity_pad_v1").fetchone()[0], "b" * 32)

    def test_wrong_padding_schema_cannot_be_removed(self):
        self.padding(malformed=True)
        self.rejected("schema", "remove")
        self.assertIn(PROBE.TABLE, [row[1] for row in PROBE.rows(self.connection)])

    def test_nonzero_payload_cannot_be_removed(self):
        self.padding()
        self.connection.execute("UPDATE locallore_capacity_pad_v1 SET payload=zeroblob(3499)||x'01'")
        self.rejected("padding_owner", "remove")

    def test_valid_owned_padding_removed_without_changing_canonical_rows(self):
        expected = PROBE.rows(self.connection)
        before = self.connection.execute("SELECT * FROM schema_migrations").fetchall()
        self.padding()
        report = PROBE.execute(str(self.directory), self.owner, "remove")
        self.assertEqual(report["rows_removed"], 1)
        self.assertGreater(report["free_pages"], 0)
        self.assertEqual(PROBE.rows(self.connection), expected)
        self.assertEqual(self.connection.execute("SELECT * FROM schema_migrations").fetchall(), before)
        self.assertFalse(self.connection.in_transaction)

    def test_unknown_action_is_refused(self):
        self.rejected("action", "other")

    def test_full_fallback_requires_exact_fixed_sqlite_message(self):
        self.assertTrue(PROBE.is_full(sqlite3.OperationalError("database or disk is full")))
        self.assertFalse(PROBE.is_full(sqlite3.OperationalError("database is locked")))
        self.assertFalse(PROBE.is_full(sqlite3.OperationalError("database or disk is full: private detail")))
        self.assertFalse(PROBE.is_full(ValueError("database or disk is full")))

    def test_available_error_code_takes_precedence_over_message(self):
        error = sqlite3.OperationalError("database or disk is full")
        error.sqlite_errorcode = 5
        self.assertFalse(PROBE.is_full(error))
        error.sqlite_errorcode = 13
        self.assertTrue(PROBE.is_full(error))
        error.sqlite_errorcode = 13 + 256
        self.assertTrue(PROBE.is_full(error))


if __name__ == "__main__":
    unittest.main()
