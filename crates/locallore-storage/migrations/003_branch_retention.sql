-- Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
-- Original canonical rows are unchanged. Deleted IDs outlive ancestry GC.
ALTER TABLE schema_migrations RENAME TO schema_migrations_v2;
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version IN (1, 2, 3)),
    contract TEXT NOT NULL CHECK (
        (version = 1 AND contract = 'locallore-storage-v1') OR
        (version = 2 AND contract = 'locallore-storage-v2-derived-memory') OR
        (version = 3 AND contract = 'locallore-storage-v3-branch-retention'))
) STRICT;
INSERT INTO schema_migrations SELECT version, contract FROM schema_migrations_v2;
DROP TABLE schema_migrations_v2;
INSERT INTO schema_migrations VALUES (3, 'locallore-storage-v3-branch-retention');

CREATE TABLE branch_retention (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL CHECK (length(branch_id) BETWEEN 1 AND 64),
    PRIMARY KEY (story_id, branch_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
) STRICT, WITHOUT ROWID;
