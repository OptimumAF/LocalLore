-- Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
-- Canonical v1 tables are unchanged. Only the owner runs this backed-up migration.
ALTER TABLE schema_migrations RENAME TO schema_migrations_v1;
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version IN (1, 2)),
    contract TEXT NOT NULL CHECK (
        (version = 1 AND contract = 'locallore-storage-v1') OR
        (version = 2 AND contract = 'locallore-storage-v2-derived-memory'))
) STRICT;
INSERT INTO schema_migrations SELECT version, contract FROM schema_migrations_v1;
DROP TABLE schema_migrations_v1;
INSERT INTO schema_migrations VALUES (2, 'locallore-storage-v2-derived-memory');

CREATE TABLE derived_memory (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    observer_kind TEXT NOT NULL DEFAULT 'actor' CHECK(observer_kind='actor'),
    observer_id TEXT NOT NULL,
    cache_key TEXT NOT NULL CHECK(length(CAST(cache_key AS BLOB)) BETWEEN 1 AND 512),
    source_revision INTEGER NOT NULL CHECK(source_revision>=0),
    summary_version INTEGER NOT NULL CHECK(summary_version=1),
    method TEXT NOT NULL CHECK(method='deterministic-event-extractive-v1'),
    visibility TEXT NOT NULL CHECK(visibility='actor_observations'),
    packet_json TEXT NOT NULL CHECK(json_valid(packet_json) AND length(CAST(packet_json AS BLOB))<=65536),
    PRIMARY KEY(story_id,branch_id,observer_id,cache_key),
    FOREIGN KEY(story_id,branch_id) REFERENCES branches(story_id,branch_id),
    FOREIGN KEY(story_id,branch_id,observer_kind,observer_id)
        REFERENCES branch_entities(story_id,branch_id,kind,entity_id)
) STRICT, WITHOUT ROWID;
