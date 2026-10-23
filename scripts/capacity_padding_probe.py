#!/usr/bin/env python3
# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Explicit synthetic capacity helper; never used by production or default checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import struct
import sys
import time

TABLE = "locallore_capacity_pad_v1"
CREATE = "CREATE TABLE locallore_capacity_pad_v1 (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, payload BLOB NOT NULL)"
MAX_PAGES = 32
MAX_ROWS = 64
PAYLOAD_BYTES = 3500
INITIAL_PAGES = 23  # Measured schema4 seeded Host draft/Ready profile, not empty SQL.
MIGRATIONS = Path(__file__).resolve().parent.parent / "crates/locallore-storage/migrations"
SCHEMAS = tuple(MIGRATIONS / name for name in (
    "001_initial.sql", "002_derived_memory.sql", "003_branch_retention.sql", "004_memory_jobs.sql"))
MIGRATION_ROWS = [(1, "locallore-storage-v1"),
                  (2, "locallore-storage-v2-derived-memory"),
                  (3, "locallore-storage-v3-branch-retention"),
                  (4, "locallore-storage-v4-memory-jobs")]
FAULTS = ("malformed", "overflow", "timeout", "after-fill", "cleanup-refusal")


class Rejected(Exception):
    pass


def require(condition, stage):
    if not condition:
        raise Rejected(stage)


def rows(connection):
    return connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name,tbl_name").fetchall()


def baseline():
    connection = sqlite3.connect(":memory:")
    try:
        for schema in SCHEMAS:
            connection.executescript(schema.read_text(encoding="utf-8"))
        require(connection.execute("SELECT version,contract FROM schema_migrations ORDER BY version").fetchall() == MIGRATION_ROWS, "reference")
        return rows(connection)
    finally:
        connection.close()


def scalar(connection, query):
    return connection.execute(query).fetchone()[0]


def schema_digest(expected):
    digest = hashlib.sha256()
    for row in expected:
        for value in row:
            if value is None:
                digest.update(b"\0")
            else:
                raw = value.encode("utf-8")
                digest.update(b"\1" + struct.pack(">I", len(raw)) + raw)
    return digest.hexdigest()


def owned_path(directory, owner):
    require(re.fullmatch("[0-9a-f]{32}", owner) is not None, "owner")
    path = Path(directory)
    require(path.is_absolute() and path.is_dir() and not path.is_symlink(), "directory")
    # Rust canonicalize emits Windows extended drive paths. Python resolve may
    # remove that prefix; compare the same absolute spelling after normalization.
    def spelling(value):
        text = str(value)
        if os.name == "nt" and text.startswith("\\\\?\\"):
            text = text[4:]
        return os.path.normcase(text)
    require(spelling(path.resolve()) == spelling(path), "directory")
    require(path.name == "capacity-relief-v4-" + owner, "directory_name")
    marker = path / ".capacity-owner"
    require(marker.is_file() and not marker.is_symlink() and marker.stat().st_size == 32, "marker")
    require(marker.read_text(encoding="ascii") == owner, "marker")
    database = path / "stories.sqlite"
    require(database.is_file() and not database.is_symlink(), "database")
    require(spelling(database.resolve()) == spelling(database), "database")
    require(0 < database.stat().st_size <= MAX_PAGES * 4096, "database_size")
    return database.resolve()


def metadata(connection):
    require(scalar(connection, "PRAGMA application_id") == 0x4C4C4F52, "identity")
    require(scalar(connection, "PRAGMA user_version") == 4, "identity")
    require(scalar(connection, "PRAGMA journal_mode") == "delete", "journal")
    require(scalar(connection, "PRAGMA page_size") == 4096, "page_size")
    require(scalar(connection, "PRAGMA auto_vacuum") == 0, "auto_vacuum")
    require(not connection.in_transaction, "transaction")


def padding_count(connection, owner):
    count, wrong, first, last = connection.execute(
        "SELECT count(*),coalesce(sum(owner!=? OR length(payload)!=3500 OR payload!=zeroblob(3500)),0),min(id),max(id) FROM locallore_capacity_pad_v1", (owner,)).fetchone()
    require(0 < count <= MAX_ROWS and wrong == 0 and first == 1 and last == count, "padding_owner")
    return count


def preflight(connection, expected, action, owner):
    metadata(connection)
    pad_row = ("table", TABLE, TABLE, CREATE)
    wanted = expected if action == "fill" else sorted(expected + [pad_row], key=lambda row: (row[0], row[1], row[2]))
    require(rows(connection) == wanted, "schema")
    require(connection.execute("SELECT version,contract FROM schema_migrations ORDER BY version").fetchall() == MIGRATION_ROWS, "migrations")
    pages = scalar(connection, "PRAGMA page_count")
    if action == "fill":
        require(pages == INITIAL_PAGES and scalar(connection, "PRAGMA freelist_count") == 0, "initial_pages")
    else:
        padding_count(connection, owner)
    return pages


def is_full(error):
    # Python 3.9/3.10 do not expose sqlite_errorcode. Only this exact SQLite
    # message from our fixed INSERT is accepted; arbitrary failures stay failures.
    code = getattr(error, "sqlite_errorcode", None)
    if code is not None:
        return code & 255 == 13
    return isinstance(error, sqlite3.OperationalError) and error.args == ("database or disk is full",)


def execute(directory, owner, action):
    require(action in ("fill", "remove"), "action")
    database = owned_path(directory, owner)
    expected = baseline()
    # Refuse foreign/old/altered databases before a writable open or any ceiling
    # or journal setting. Recheck path identity and all metadata after reopening.
    before = database.stat()
    readonly = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True,
                               timeout=0.25, isolation_level=None)
    try:
        readonly.execute("PRAGMA query_only=ON")
        preflight(readonly, expected, action, owner)
    finally:
        readonly.close()
    require(owned_path(directory, owner) == database, "database")
    after = database.stat()
    require((before.st_dev, before.st_ino, before.st_size) ==
            (after.st_dev, after.st_ino, after.st_size), "database_changed")
    connection = sqlite3.connect(database.as_uri() + "?mode=rw", uri=True,
                                 timeout=0.25, isolation_level=None)
    try:
        initial_pages = preflight(connection, expected, action, owner)
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA foreign_keys=ON")
        require(scalar(connection, "PRAGMA max_page_count=32") == MAX_PAGES, "ceiling")
        if action == "fill":
            connection.execute(CREATE)
            inserted = 0
            observed_full = False
            errorcode_api = False
            attempts = 0
            for _ in range(MAX_ROWS + 1):
                attempts += 1
                try:
                    connection.execute("INSERT INTO locallore_capacity_pad_v1 (owner,payload) VALUES (?,zeroblob(3500))", (owner,))
                    inserted += 1
                    require(inserted <= MAX_ROWS, "row_bound")
                except sqlite3.Error as error:
                    require(is_full(error), "insert")
                    errorcode_api = getattr(error, "sqlite_errorcode", None) is not None
                    observed_full = True
                    break
            require(observed_full and 0 < inserted <= MAX_ROWS, "full")
            require(scalar(connection, "PRAGMA page_count") == MAX_PAGES, "full_pages")
            require(scalar(connection, "PRAGMA freelist_count") == 0, "full_freelist")
            require(not connection.in_transaction, "transaction")
            return {"version": 2, "database_schema_version": 4, "schema_sha256": schema_digest(expected), "status": "passed", "action": action, "initial_pages": initial_pages,
                    "pages": MAX_PAGES, "free_pages": 0, "rows": inserted, "insert_attempts": attempts,
                    "sqlite_full": True, "sqlite_version": sqlite3.sqlite_version,
                    "errorcode_api": errorcode_api}
        count = padding_count(connection, owner)
        connection.execute("DROP TABLE locallore_capacity_pad_v1")
        metadata(connection)
        require(rows(connection) == expected, "restored_schema")
        require(connection.execute("SELECT version,contract FROM schema_migrations ORDER BY version").fetchall() == MIGRATION_ROWS, "restored_migrations")
        free = scalar(connection, "PRAGMA freelist_count")
        require(free > 0, "relief")
        return {"version": 2, "database_schema_version": 4, "schema_sha256": schema_digest(expected), "status": "passed", "action": action, "initial_pages": initial_pages,
                "pages": scalar(connection, "PRAGMA page_count"), "free_pages": free,
                "rows_removed": count, "schema_restored": True, "sqlite_version": sqlite3.sqlite_version}
    finally:
        connection.close()


def fault_authorized(directory, owner, action, fault):
    # Opt-in fixed synthetic faults have no SQL/script/path payload. Refuse an
    # unknown selector before opening any database, including the reference.
    require(fault in FAULTS, "fault")
    require(action == "fill" or (action == "remove" and fault == "cleanup-refusal"), "fault_action")
    database = owned_path(directory, owner)
    marker = Path(directory) / ".capacity-fault"
    require(marker.is_file() and not marker.is_symlink() and marker.stat().st_size <= 128, "fault_marker")
    require(marker.read_text(encoding="ascii") == owner + "\n" + fault, "fault_marker")
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True,
                                 timeout=0.25, isolation_level=None)
    try:
        connection.execute("PRAGMA query_only=ON")
        preflight(connection, baseline(), action, owner)
    finally:
        connection.close()


def execute_fault(directory, owner, action, fault):
    fault_authorized(directory, owner, action, fault)
    if action == "remove":
        raise Rejected("injected_cleanup_refusal")
    report = execute(directory, owner, action)
    require(report["rows"] == 14 and report["insert_attempts"] == 15 and report["sqlite_full"], "fault_fill_profile")
    ready = {"version": 1, "owner": owner, "fault": fault, "rows": report["rows"],
             "insert_attempts": report["insert_attempts"], "pages": report["pages"], "sqlite_full": True}
    with (Path(directory) / ".capacity-fault-ready").open("xb") as output:
        output.write(json.dumps(ready, sort_keys=True).encode("ascii"))
        output.flush()
        os.fsync(output.fileno())
    if fault == "malformed":
        print("capacity-malformed-v1", flush=True)
        return None
    if fault == "overflow":
        # Fixed8KiB payload: the parent observes a4KiB polling threshold, not a
        # hard file quota. Remain alive so its kill/reap path is actually used.
        sys.stdout.write("X" * 8192)
        sys.stdout.flush()
    if fault in ("overflow", "timeout"):
        time.sleep(120)  # Parent owns a10s deadline and must kill+reap this child.
        raise Rejected("fault_parent_did_not_stop_child")
    raise Rejected("injected_after_fill")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--action", choices=("fill", "remove"), required=True)
    parser.add_argument("--fault", choices=FAULTS)
    arguments = parser.parse_args()
    try:
        report = (execute(arguments.directory, arguments.owner, arguments.action)
                  if arguments.fault is None else execute_fault(arguments.directory, arguments.owner, arguments.action, arguments.fault))
        if report is None:
            return 0  # Deliberately malformed terminal fault, already emitted.
    except Rejected as error:
        report = {"version": 2, "status": "failed", "stage": str(error)}
    except Exception:
        report = {"version": 2, "status": "failed", "stage": "helper"}
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
