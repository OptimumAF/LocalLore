-- Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
-- Only Rust's storage owner executes this schema. Payloads remain engine-owned.
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version = 1),
    contract TEXT NOT NULL CHECK (contract = 'locallore-storage-v1')
) STRICT;
INSERT INTO schema_migrations VALUES (1, 'locallore-storage-v1');

CREATE TABLE stories (
    story_id TEXT PRIMARY KEY CHECK (length(story_id) BETWEEN 1 AND 128),
    root_branch TEXT NOT NULL CHECK (length(root_branch) BETWEEN 1 AND 128),
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 256),
    seed_version INTEGER NOT NULL CHECK (seed_version = 1),
    seed_json TEXT NOT NULL CHECK (length(CAST(seed_json AS BLOB)) <= 131072 AND json_valid(seed_json)),
    FOREIGN KEY (story_id, root_branch) REFERENCES branches(story_id, branch_id)
        DEFERRABLE INITIALLY DEFERRED
) STRICT, WITHOUT ROWID;

CREATE TABLE branches (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL CHECK (length(branch_id) BETWEEN 1 AND 128),
    parent_branch TEXT,
    fork_revision INTEGER,
    head_revision INTEGER NOT NULL DEFAULT 0 CHECK (head_revision >= 0),
    PRIMARY KEY (story_id, branch_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id),
    FOREIGN KEY (story_id, parent_branch) REFERENCES branches(story_id, branch_id),
    CHECK ((parent_branch IS NULL AND fork_revision IS NULL) OR
           (parent_branch IS NOT NULL AND fork_revision >= 0 AND fork_revision IS NOT NULL)),
    CHECK (parent_branch IS NULL OR parent_branch <> branch_id)
) STRICT, WITHOUT ROWID;

-- IDs may overlap across types: an actor called 'quay' is not the location 'quay'.
CREATE TABLE entities (
    story_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('actor', 'item', 'location', 'ability', 'fact', 'commitment')),
    entity_id TEXT NOT NULL CHECK (length(entity_id) BETWEEN 1 AND 128),
    PRIMARY KEY (story_id, kind, entity_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE branch_entities (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    PRIMARY KEY (story_id, branch_id, kind, entity_id),
    FOREIGN KEY (story_id, branch_id) REFERENCES branches(story_id, branch_id),
    FOREIGN KEY (story_id, kind, entity_id) REFERENCES entities(story_id, kind, entity_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE turns (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    turn_id TEXT NOT NULL CHECK (length(turn_id) BETWEEN 1 AND 128),
    expected_revision INTEGER NOT NULL CHECK (expected_revision >= 0),
    status TEXT NOT NULL CHECK (status IN ('draft', 'cancelled', 'failed', 'stale', 'committed')),
    request_json TEXT NOT NULL CHECK (length(CAST(request_json AS BLOB)) <= 24576 AND json_valid(request_json)),
    response_json TEXT CHECK (response_json IS NULL OR
        (length(CAST(response_json AS BLOB)) <= 65536 AND json_valid(response_json))),
    PRIMARY KEY (story_id, branch_id, turn_id),
    FOREIGN KEY (story_id, branch_id) REFERENCES branches(story_id, branch_id),
    CHECK ((status = 'committed') = (response_json IS NOT NULL))
) STRICT, WITHOUT ROWID;

CREATE TABLE accepted_events (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    sequence INTEGER NOT NULL CHECK (sequence > 0),
    turn_id TEXT NOT NULL,
    event_version INTEGER NOT NULL CHECK (event_version = 1),
    envelope_json TEXT NOT NULL CHECK (length(CAST(envelope_json AS BLOB)) <= 65536 AND json_valid(envelope_json)),
    PRIMARY KEY (story_id, branch_id, sequence),
    FOREIGN KEY (story_id, branch_id, turn_id) REFERENCES turns(story_id, branch_id, turn_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE event_witnesses (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    observer_kind TEXT NOT NULL DEFAULT 'actor' CHECK (observer_kind = 'actor'),
    observer_id TEXT NOT NULL,
    PRIMARY KEY (story_id, branch_id, sequence, observer_id),
    FOREIGN KEY (story_id, branch_id, sequence) REFERENCES accepted_events(story_id, branch_id, sequence),
    FOREIGN KEY (story_id, branch_id, observer_kind, observer_id)
        REFERENCES branch_entities(story_id, branch_id, kind, entity_id)
) STRICT, WITHOUT ROWID;
CREATE INDEX witness_history ON event_witnesses(story_id, branch_id, observer_id, sequence);

-- Replaceable accelerator, never loaded as canonical state by this API.
CREATE TABLE branch_projections (
    story_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 0),
    projection_version INTEGER NOT NULL CHECK (projection_version = 1),
    projection_json TEXT NOT NULL CHECK (length(CAST(projection_json AS BLOB)) <= 262144 AND json_valid(projection_json)),
    PRIMARY KEY (story_id, branch_id),
    FOREIGN KEY (story_id, branch_id) REFERENCES branches(story_id, branch_id)
) STRICT, WITHOUT ROWID;
