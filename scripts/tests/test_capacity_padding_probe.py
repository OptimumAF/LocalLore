# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Guard tests use only disposable synthetic databases; actual Host proof is explicit."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("capacity_padding_probe", Path(__file__).resolve().parents[1] / "capacity_padding_probe.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class CapacityPaddingGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.owner = "a" * 32
        self.directory = Path(self.temp.name).resolve() / ("capacity-relief-v4-" + self.owner)
        self.directory.mkdir()
        (self.directory / ".capacity-owner").write_text(self.owner, encoding="ascii")
        self.database = self.directory / "stories.sqlite"
        self.connection = sqlite3.connect(str(self.database), isolation_level=None)
        self.addCleanup(self.connection.close)
        for schema in PROBE.SCHEMAS:
            self.connection.executescript(schema.read_text(encoding="utf-8"))
        self.connection.execute("PRAGMA application_id=1280069458")
        self.connection.execute("PRAGMA user_version=4")

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
        self.assert_readonly_refusal("identity")
        self.assertEqual(self.connection.execute("PRAGMA application_id").fetchone()[0], 99)

    def test_future_schema_version_is_preserved(self):
        self.connection.execute("PRAGMA user_version=5")
        self.rejected("identity")
        self.assertEqual(self.connection.execute("PRAGMA user_version").fetchone()[0], 5)

    def assert_readonly_refusal(self, stage):
        opened = []
        connect = sqlite3.connect

        def observe(database, *args, **kwargs):
            opened.append(str(database))
            return connect(database, *args, **kwargs)

        with mock.patch.object(PROBE.sqlite3, "connect", side_effect=observe):
            self.rejected(stage)
        self.assertTrue(any("?mode=ro" in path for path in opened))
        self.assertFalse(any("?mode=rw" in path for path in opened))

    def test_schema1_schema2_and_schema3_refused_before_writable_open(self):
        for version in (1, 2, 3):
            with self.subTest(version=version):
                self.connection.execute("PRAGMA user_version=" + str(version))
                self.assert_readonly_refusal("identity")
                self.assertEqual(self.connection.execute("PRAGMA user_version").fetchone()[0], version)

    def test_exact_reference_schema4_digest_and_all_migrations(self):
        self.assertEqual(PROBE.schema_digest(PROBE.baseline()),
                         "e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362")
        self.assertEqual(self.connection.execute("SELECT version,contract FROM schema_migrations ORDER BY version").fetchall(), PROBE.MIGRATION_ROWS)

    def test_missing_migration_record_refused_before_writable_open(self):
        self.connection.execute("DELETE FROM schema_migrations WHERE version=2")
        self.assert_readonly_refusal("migrations")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0], 3)

    def test_missing_schema3_object_refused_before_writable_open(self):
        self.connection.execute("DROP TABLE branch_retention")
        self.assert_readonly_refusal("schema")

    def test_altered_schema3_object_refused_before_writable_open(self):
        self.connection.execute("ALTER TABLE branch_retention ADD COLUMN untrusted TEXT")
        self.assert_readonly_refusal("schema")

    def test_wal_is_not_silently_changed(self):
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.assert_readonly_refusal("journal")
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
        self.assertEqual(report["version"], 2)
        self.assertEqual(report["database_schema_version"], 4)
        self.assertEqual(report["schema_sha256"], PROBE.schema_digest(expected))

    def test_identity_rechecked_after_writable_open_before_drop(self):
        self.padding()
        connect = sqlite3.connect

        def change_before_rw(database, *args, **kwargs):
            if "?mode=rw" in str(database):
                self.connection.execute("PRAGMA user_version=2")
            return connect(database, *args, **kwargs)

        with mock.patch.object(PROBE.sqlite3, "connect", side_effect=change_before_rw):
            self.rejected("identity", "remove")
        self.assertIn(PROBE.TABLE, [row[1] for row in PROBE.rows(self.connection)])

    def test_marker_rechecked_after_readonly_preflight(self):
        self.padding()
        connect = sqlite3.connect

        def change_after_ro(database, *args, **kwargs):
            result = connect(database, *args, **kwargs)
            if "?mode=ro" in str(database):
                (self.directory / ".capacity-owner").write_text("b" * 32, encoding="ascii")
            return result

        with mock.patch.object(PROBE.sqlite3, "connect", side_effect=change_after_ro):
            self.rejected("marker", "remove")
        self.assertIn(PROBE.TABLE, [row[1] for row in PROBE.rows(self.connection)])

    def test_noncontiguous_padding_is_not_removed(self):
        self.padding()
        self.connection.execute("UPDATE locallore_capacity_pad_v1 SET id=2")
        self.rejected("padding_owner", "remove")

    def test_oversized_database_is_refused_without_writable_open(self):
        self.connection.execute("CREATE TABLE unrelated_large(payload BLOB)")
        self.connection.execute("INSERT INTO unrelated_large VALUES(zeroblob(150000))")
        self.rejected("database_size")

    def test_parent_alias_is_not_accepted_as_owned_directory(self):
        alias = self.directory / ".." / self.directory.name
        with self.assertRaisesRegex(PROBE.Rejected, "^directory$"):
            PROBE.execute(str(alias), self.owner, "fill")

    def test_unknown_action_is_refused(self):
        with mock.patch.object(PROBE.sqlite3, "connect") as connect:
            self.rejected("action", "other")
        connect.assert_not_called()

    def test_unknown_fault_is_refused_before_any_connection(self):
        with mock.patch.object(PROBE.sqlite3, "connect") as connect:
            with self.assertRaisesRegex(PROBE.Rejected, "^fault$"):
                PROBE.execute_fault(str(self.directory), self.owner, "fill", "arbitrary-script")
        connect.assert_not_called()

    def test_fault_requires_matching_additional_owned_marker(self):
        for marker in (None, self.owner + "\ntimeout"):
            with self.subTest(marker=marker):
                if marker is not None:
                    (self.directory / ".capacity-fault").write_text(marker, encoding="ascii")
                with mock.patch.object(PROBE.sqlite3, "connect") as connect:
                    with self.assertRaisesRegex(PROBE.Rejected, "^fault_marker$"):
                        PROBE.execute_fault(str(self.directory), self.owner, "fill", "malformed")
                connect.assert_not_called()

    def test_fault_cannot_select_an_unrelated_remove_operation(self):
        with mock.patch.object(PROBE.sqlite3, "connect") as connect:
            with self.assertRaisesRegex(PROBE.Rejected, "^fault_action$"):
                PROBE.execute_fault(str(self.directory), self.owner, "remove", "timeout")
        connect.assert_not_called()

    def test_cleanup_refusal_validates_readonly_then_preserves_padding(self):
        self.padding()
        (self.directory / ".capacity-fault").write_text(self.owner + "\ncleanup-refusal", encoding="ascii")
        before = self.connection.execute("SELECT * FROM locallore_capacity_pad_v1").fetchall()
        connect = sqlite3.connect
        opened = []

        def observe(database, *args, **kwargs):
            opened.append(str(database))
            return connect(database, *args, **kwargs)

        with mock.patch.object(PROBE.sqlite3, "connect", side_effect=observe):
            with self.assertRaisesRegex(PROBE.Rejected, "^injected_cleanup_refusal$"):
                PROBE.execute_fault(str(self.directory), self.owner, "remove", "cleanup-refusal")
        self.assertTrue(any("?mode=ro" in path for path in opened))
        self.assertFalse(any("?mode=rw" in path for path in opened))
        self.assertEqual(self.connection.execute("SELECT * FROM locallore_capacity_pad_v1").fetchall(), before)

    def test_fault_cannot_bypass_old_schema_refusal(self):
        self.padding()
        (self.directory / ".capacity-fault").write_text(self.owner + "\ncleanup-refusal", encoding="ascii")
        self.connection.execute("PRAGMA user_version=2")
        with self.assertRaisesRegex(PROBE.Rejected, "^identity$"):
            PROBE.execute_fault(str(self.directory), self.owner, "remove", "cleanup-refusal")

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
