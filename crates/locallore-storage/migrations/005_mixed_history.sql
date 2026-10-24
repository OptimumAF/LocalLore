-- Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
-- One canonical turns ledger. Existing request/response limits stay unchanged.
ALTER TABLE schema_migrations RENAME TO schema_migrations_v4;
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version IN (1,2,3,4,5)),
    contract TEXT NOT NULL CHECK (
        (version=1 AND contract='locallore-storage-v1') OR
        (version=2 AND contract='locallore-storage-v2-derived-memory') OR
        (version=3 AND contract='locallore-storage-v3-branch-retention') OR
        (version=4 AND contract='locallore-storage-v4-memory-jobs') OR
        (version=5 AND contract='locallore-storage-v5-mixed-history'))
) STRICT;
INSERT INTO schema_migrations SELECT version,contract FROM schema_migrations_v4;
DROP TABLE schema_migrations_v4;
INSERT INTO schema_migrations VALUES(5,'locallore-storage-v5-mixed-history');
ALTER TABLE turns ADD COLUMN canonical_kind TEXT NOT NULL DEFAULT 'legacy_play'
    CHECK(canonical_kind IN ('legacy_play','play_v2','author_v1') AND
          (canonical_kind <> 'author_v1' OR status='committed'));
ALTER TABLE accepted_events ADD COLUMN record_kind TEXT NOT NULL DEFAULT 'play'
    CHECK(record_kind IN ('play','author_correction'));
ALTER TABLE branch_projections RENAME TO branch_projections_v4;
CREATE TABLE branch_projections (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK(revision>=0),
    projection_version INTEGER NOT NULL CHECK(projection_version IN (1,2)),
    projection_json TEXT NOT NULL CHECK(length(CAST(projection_json AS BLOB))<=262144 AND json_valid(projection_json)),
    PRIMARY KEY(story_id,branch_id),
    FOREIGN KEY(story_id,branch_id) REFERENCES branches(story_id,branch_id)
) STRICT, WITHOUT ROWID;
INSERT INTO branch_projections SELECT * FROM branch_projections_v4;
DROP TABLE branch_projections_v4;
