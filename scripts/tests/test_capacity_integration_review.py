# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Independent actual fixed helper CLI checks; synthetic schema/rows, not a Full proof."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/capacity_padding_probe.py"
PAD = "locallore_capacity_pad_v1"
CREATE = "CREATE TABLE locallore_capacity_pad_v1 (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, payload BLOB NOT NULL)"


class ActualCapacityHelperCliReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="locallore-capacity-review-")
        self.addCleanup(self.temp.cleanup)
        self.owner = "c" * 32
        self.directory = Path(self.temp.name).resolve() / ("capacity-relief-" + self.owner)
        self.directory.mkdir()
        (self.directory / ".capacity-owner").write_text(self.owner, encoding="ascii")
        self.path = self.directory / "stories.sqlite"
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            for name in ("001_initial.sql", "002_derived_memory.sql", "003_branch_retention.sql"):
                db.executescript((ROOT / "crates/locallore-storage/migrations" / name).read_text(encoding="utf-8"))
            db.execute("PRAGMA application_id=1280069458")
            db.execute("PRAGMA user_version=3")
            seed = json.loads((ROOT / "fixtures/lantern_quay.json").read_text(encoding="utf-8"))
            db.execute("INSERT INTO stories(story_id,root_branch,title,seed_version,seed_json) VALUES(?,?,?,?,?)",
                       (seed["scope"]["story"], seed["scope"]["branch"], "Synthetic CLI control", 1, json.dumps(seed)))
            db.execute("INSERT INTO branches(story_id,branch_id,parent_branch,fork_revision,head_revision) VALUES(?,?,NULL,NULL,0)",
                       (seed["scope"]["story"], seed["scope"]["branch"]))
            db.execute(CREATE)
            db.execute("INSERT INTO locallore_capacity_pad_v1(owner,payload) VALUES(?,zeroblob(3500))", (self.owner,))

    def cli(self, expected_exit, stage=None):
        # Fixed trusted script/args and this freshly owned root only. No shell,
        # model, arbitrary command, external workspace or descendant process.
        result = subprocess.run([sys.executable, "-B", str(HELPER), "--directory", str(self.directory),
                                 "--owner", self.owner, "--action", "remove"],
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=5, check=False)
        self.assertEqual(result.returncode, expected_exit, (result.stdout[:4096], result.stderr[:4096]))
        self.assertEqual(result.stderr, b"")
        self.assertLessEqual(len(result.stdout), 4096)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        value = json.loads(result.stdout)
        if stage is not None:
            self.assertEqual(value, {"version": 2, "status": "failed", "stage": stage})
        # The public result contains no selected path, token or private seed.
        for private in (str(self.path), self.owner, "SECRET-TIDE-731"):
            self.assertNotIn(private, result.stdout.decode("utf-8"))
        return value

    def control_rows(self):
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            return {name: db.execute("SELECT * FROM " + name + " ORDER BY 1").fetchall()
                    for name in ("stories", "branches", "schema_migrations", "branch_retention")}

    def test_actual_remove_cli_restores_exact_schema_without_mutating_control_rows(self):
        before = self.control_rows()
        value = self.cli(0)
        self.assertEqual(value["version"], 2)
        self.assertEqual(value["database_schema_version"], 3)
        self.assertEqual(value["schema_sha256"], "c05ced1f0439fb767f97d2ff93a34ef44eb6fbc27da6814a75fad455fb0b2c17")
        self.assertEqual(value["status"], "passed")
        self.assertEqual(value["rows_removed"], 1)
        self.assertTrue(value["schema_restored"])
        self.assertGreater(value["free_pages"], 0)
        self.assertEqual(self.control_rows(), before)
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM sqlite_schema WHERE name=?", (PAD,)).fetchone()[0], 0)
        # No claim of seeded Ready17, actual Full32, native recovery or gameplay.

    def test_unknown_main_schema_is_refused_by_actual_cli_without_touching_database(self):
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("CREATE TABLE unrelated_review_canary(value TEXT)")
            db.execute("INSERT INTO unrelated_review_canary VALUES('preserve')")
        before = hashlib.sha256(self.path.read_bytes()).digest()
        self.cli(1, "schema")
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).digest(), before)
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            self.assertEqual(db.execute("SELECT value FROM unrelated_review_canary").fetchall(), [("preserve",)])
            self.assertEqual(db.execute("SELECT count(*) FROM " + PAD).fetchone()[0], 1)

    def test_foreign_padding_owner_is_refused_by_actual_cli_without_partial_drop(self):
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("UPDATE locallore_capacity_pad_v1 SET owner=?", ("d" * 32,))
        before = hashlib.sha256(self.path.read_bytes()).digest()
        self.cli(1, "padding_owner")
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).digest(), before)
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            self.assertEqual(db.execute("SELECT owner FROM " + PAD).fetchall(), [("d" * 32,)])


if __name__ == "__main__":
    unittest.main()
