#!/usr/bin/env python3
# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Explicit synthetic capacity helper; never used by production or default checks."""
import argparse
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

TABLE = "locallore_capacity_pad_v1"
CREATE = "CREATE TABLE locallore_capacity_pad_v1 (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, payload BLOB NOT NULL)"
MAX_PAGES = 32
MAX_ROWS = 64
PAYLOAD_BYTES = 3500
SCHEMA = Path(__file__).resolve().parent.parent / "crates/locallore-storage/migrations/001_initial.sql"


class Rejected(Exception):
    pass


def require(condition, stage):
    if not condition:
        raise Rejected(stage)


def rows(connection):
    return connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name").fetchall()


def baseline():
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        return rows(connection)
    finally:
        connection.close()


def scalar(connection, query):
    return connection.execute(query).fetchone()[0]


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
    require(path.name == "capacity-relief-" + owner, "directory_name")
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
    require(scalar(connection, "PRAGMA user_version") == 1, "identity")
    require(scalar(connection, "PRAGMA journal_mode") == "delete", "journal")
    require(scalar(connection, "PRAGMA page_size") == 4096, "page_size")
    require(scalar(connection, "PRAGMA auto_vacuum") == 0, "auto_vacuum")
    require(not connection.in_transaction, "transaction")


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
    connection = sqlite3.connect(database.as_uri() + "?mode=rw", uri=True,
                                 timeout=0.25, isolation_level=None)
    try:
        metadata(connection)
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA foreign_keys=ON")
        require(scalar(connection, "PRAGMA max_page_count=32") == MAX_PAGES, "ceiling")
        initial_pages = scalar(connection, "PRAGMA page_count")
        if action == "fill":
            require(rows(connection) == expected, "schema")
            require(initial_pages == 15 and scalar(connection, "PRAGMA freelist_count") == 0, "initial_pages")
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
            return {"version": 1, "status": "passed", "action": action, "initial_pages": initial_pages,
                    "pages": MAX_PAGES, "free_pages": 0, "rows": inserted, "insert_attempts": attempts,
                    "sqlite_full": True, "sqlite_version": sqlite3.sqlite_version,
                    "errorcode_api": errorcode_api}
        pad_row = ("table", TABLE, TABLE, CREATE)
        require(rows(connection) == sorted(expected + [pad_row], key=lambda row: (row[0], row[1])), "schema")
        count, wrong, first, last = connection.execute(
            "SELECT count(*),coalesce(sum(owner!=? OR length(payload)!=3500 OR payload!=zeroblob(3500)),0),min(id),max(id) FROM locallore_capacity_pad_v1", (owner,)).fetchone()
        require(0 < count <= MAX_ROWS and wrong == 0 and first == 1 and last == count, "padding_owner")
        connection.execute("DROP TABLE locallore_capacity_pad_v1")
        metadata(connection)
        require(rows(connection) == expected, "restored_schema")
        free = scalar(connection, "PRAGMA freelist_count")
        require(free > 0, "relief")
        return {"version": 1, "status": "passed", "action": action, "initial_pages": initial_pages,
                "pages": scalar(connection, "PRAGMA page_count"), "free_pages": free,
                "rows_removed": count, "schema_restored": True, "sqlite_version": sqlite3.sqlite_version}
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--action", choices=("fill", "remove"), required=True)
    arguments = parser.parse_args()
    try:
        report = execute(arguments.directory, arguments.owner, arguments.action)
    except Rejected as error:
        report = {"version": 1, "status": "failed", "stage": str(error)}
    except Exception:
        report = {"version": 1, "status": "failed", "stage": "helper"}
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
