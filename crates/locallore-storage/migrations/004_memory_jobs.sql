-- Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
-- Derived work only: accepted history, turns and projections are unchanged.
ALTER TABLE schema_migrations RENAME TO schema_migrations_v3;
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version IN (1, 2, 3, 4)),
    contract TEXT NOT NULL CHECK (
        (version = 1 AND contract = 'locallore-storage-v1') OR
        (version = 2 AND contract = 'locallore-storage-v2-derived-memory') OR
        (version = 3 AND contract = 'locallore-storage-v3-branch-retention') OR
        (version = 4 AND contract = 'locallore-storage-v4-memory-jobs'))
) STRICT;
INSERT INTO schema_migrations SELECT version, contract FROM schema_migrations_v3;
DROP TABLE schema_migrations_v3;
INSERT INTO schema_migrations VALUES (4, 'locallore-storage-v4-memory-jobs');

CREATE TABLE memory_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    observer_kind TEXT NOT NULL DEFAULT 'actor' CHECK(observer_kind='actor'),
    observer_id TEXT NOT NULL,
    method TEXT NOT NULL CHECK(method='deterministic-event-extractive-v2'),
    summary_version INTEGER NOT NULL CHECK(summary_version=2),
    basis_revision INTEGER NOT NULL CHECK(basis_revision>=0),
    seed_sha256 TEXT NOT NULL CHECK(length(seed_sha256)=64),
    lineage_sha256 TEXT NOT NULL CHECK(length(lineage_sha256)=64),
    source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
    next_from INTEGER NOT NULL CHECK(next_from BETWEEN 0 AND basis_revision),
    generation INTEGER NOT NULL CHECK(generation>=1),
    status TEXT NOT NULL CHECK(status IN ('ready','cancelled','stale','complete','blocked')),
    last_error TEXT CHECK(last_error IN ('budget','packet_limit','integrity')),
    UNIQUE(job_id,story_id,branch_id,observer_id),
    UNIQUE(story_id,branch_id,observer_id,method),
    FOREIGN KEY(story_id,branch_id) REFERENCES branches(story_id,branch_id),
    FOREIGN KEY(story_id,branch_id,observer_kind,observer_id)
        REFERENCES branch_entities(story_id,branch_id,kind,entity_id)
) STRICT;
CREATE TABLE memory_job_packets (
    job_id INTEGER NOT NULL,
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    observer_id TEXT NOT NULL,
    from_revision INTEGER NOT NULL CHECK(from_revision>=0),
    through_revision INTEGER NOT NULL CHECK(through_revision>from_revision),
    packet_json TEXT NOT NULL CHECK(json_valid(packet_json) AND length(CAST(packet_json AS BLOB))<=65536),
    PRIMARY KEY(job_id,from_revision),
    FOREIGN KEY(job_id,story_id,branch_id,observer_id)
        REFERENCES memory_jobs(job_id,story_id,branch_id,observer_id) ON DELETE CASCADE
) STRICT, WITHOUT ROWID;
