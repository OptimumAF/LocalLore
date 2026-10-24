// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic test factory, NOT a production migration or story downgrade.
//! Build exact old DDL and copy already validated Domain1 payloads unchanged.
use locallore_storage::Store;
use rusqlite::{params_from_iter, types::Value, Connection, OptionalExtension};
use std::{path::Path, time::Duration};

pub fn original_columns(table: &str) -> &'static [&'static str] {
    match table {
        "stories" => &[
            "story_id",
            "root_branch",
            "title",
            "seed_version",
            "seed_json",
        ],
        "branches" => &[
            "story_id",
            "branch_id",
            "parent_branch",
            "fork_revision",
            "head_revision",
        ],
        "entities" => &["story_id", "kind", "entity_id"],
        "branch_entities" => &["story_id", "branch_id", "kind", "entity_id"],
        "turns" => &[
            "story_id",
            "branch_id",
            "turn_id",
            "expected_revision",
            "status",
            "request_json",
            "response_json",
        ],
        "accepted_events" => &[
            "story_id",
            "branch_id",
            "sequence",
            "turn_id",
            "event_version",
            "envelope_json",
        ],
        "event_witnesses" => &[
            "story_id",
            "branch_id",
            "sequence",
            "observer_kind",
            "observer_id",
        ],
        "branch_projections" => &[
            "story_id",
            "branch_id",
            "revision",
            "projection_version",
            "projection_json",
        ],
        "derived_memory" => &[
            "story_id",
            "branch_id",
            "observer_kind",
            "observer_id",
            "cache_key",
            "source_revision",
            "summary_version",
            "method",
            "visibility",
            "packet_json",
        ],
        "branch_retention" => &["story_id", "branch_id"],
        "memory_jobs" => &[
            "job_id",
            "story_id",
            "branch_id",
            "observer_kind",
            "observer_id",
            "method",
            "summary_version",
            "basis_revision",
            "seed_sha256",
            "lineage_sha256",
            "source_sha256",
            "next_from",
            "generation",
            "status",
            "last_error",
        ],
        "memory_job_packets" => &[
            "job_id",
            "story_id",
            "branch_id",
            "observer_id",
            "from_revision",
            "through_revision",
            "packet_json",
        ],
        _ => panic!("unexpected synthetic historical table"),
    }
}

/// Check new metadata separately instead of silently omitting it from parity.
pub fn assert_legacy_defaults(db: &Connection) {
    let version: u32 = db
        .pragma_query_value(None, "user_version", |r| r.get(0))
        .unwrap();
    if version >= 5 {
        assert_eq!(
            db.query_row(
                "SELECT count(*) FROM turns WHERE canonical_kind<>'legacy_play'",
                [],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
            0,
            "cannot cast mixed history to an old schema"
        );
        assert_eq!(
            db.query_row(
                "SELECT count(*) FROM accepted_events WHERE record_kind<>'play'",
                [],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
            0,
            "ordinary normalized events must retain their legacy kind"
        );
    }
    assert_eq!(
        db.query_row(
            "SELECT count(*) FROM branch_projections WHERE projection_version<>1",
            [],
            |r| r.get::<_, i64>(0)
        )
        .unwrap(),
        0,
        "historical Domain1 projection version must remain1"
    );
}

/// Caller must close its Store before invoking this factory. Only three known
/// synthetic fixture families under this process's TEMP root are eligible.
pub fn replace_current_fixture(path: &Path, version: u32) {
    assert!((1..=4).contains(&version));
    let metadata = std::fs::symlink_metadata(path).unwrap();
    assert!(metadata.is_file() && !metadata.file_type().is_symlink());
    let path = path.canonicalize().unwrap();
    let temp = std::env::temp_dir().canonicalize().unwrap();
    let parent = path.parent().unwrap();
    assert!(parent.starts_with(&temp) && parent != temp);
    let family = parent.file_name().unwrap().to_str().unwrap();
    assert!([
        "locallore-derived-owner-",
        "locallore-memory-owner-review-",
        "locallore-schema3-migration-",
    ]
    .iter()
    .any(|prefix| family.starts_with(&format!("{prefix}{}-", std::process::id()))));
    assert!(
        metadata.len() <= 64 * 1024 * 1024,
        "bounded synthetic input only"
    );

    // Validate actual source history, including retained ancestry, before any
    // fixture rewrite. This never accepts caller-authored projections as canon.
    {
        let mut source = Store::open_read_only(&path).unwrap();
        for story in source.stories().unwrap() {
            source
                .branch_catalog(&story.scope.story, &|| false)
                .unwrap();
        }
    }
    let mut destination = Connection::open(&path).unwrap();
    assert_legacy_defaults(&destination);
    let mut historical = Connection::open_in_memory().unwrap();
    historical
        .pragma_update(None, "foreign_keys", true)
        .unwrap();
    historical
        .execute_batch(include_str!("../../migrations/001_initial.sql"))
        .unwrap();
    if version >= 2 {
        historical
            .execute_batch(include_str!("../../migrations/002_derived_memory.sql"))
            .unwrap();
    }
    if version >= 3 {
        historical
            .execute_batch(include_str!("../../migrations/003_branch_retention.sql"))
            .unwrap();
    }
    if version >= 4 {
        historical
            .execute_batch(include_str!("../../migrations/004_memory_jobs.sql"))
            .unwrap();
    }
    historical
        .pragma_update(None, "application_id", 0x4c4c4f52_u32)
        .unwrap();
    historical
        .pragma_update(None, "user_version", version)
        .unwrap();
    let mut tables = vec![
        "stories",
        "branches",
        "entities",
        "branch_entities",
        "turns",
        "accepted_events",
        "event_witnesses",
        "branch_projections",
    ];
    if version >= 2 {
        tables.push("derived_memory");
    }
    if version >= 3 {
        tables.push("branch_retention");
    }
    if version >= 4 {
        tables.extend(["memory_jobs", "memory_job_packets"]);
    }
    {
        let tx = historical.transaction().unwrap();
        tx.pragma_update(None, "defer_foreign_keys", true).unwrap();
        for table in tables {
            let columns = original_columns(table);
            let actual_columns: Vec<String> = tx
                .prepare(&format!("PRAGMA table_info({table})"))
                .unwrap()
                .query_map([], |r| r.get(1))
                .unwrap()
                .map(Result::unwrap)
                .collect();
            assert_eq!(
                actual_columns,
                columns
                    .iter()
                    .map(|name| name.to_string())
                    .collect::<Vec<_>>(),
                "old fixture column inventory drift"
            );
            let names = columns.join(",");
            let mut read = destination
                .prepare(&format!("SELECT {names} FROM {table}"))
                .unwrap();
            let values = read
                .query_map([], |r| {
                    (0..columns.len())
                        .map(|n| r.get::<_, Value>(n))
                        .collect::<rusqlite::Result<Vec<_>>>()
                })
                .unwrap();
            let placeholders = (1..=columns.len())
                .map(|n| format!("?{n}"))
                .collect::<Vec<_>>()
                .join(",");
            let mut write = tx
                .prepare(&format!(
                    "INSERT INTO {table}({names}) VALUES({placeholders})"
                ))
                .unwrap();
            for row in values {
                write
                    .execute(params_from_iter(row.unwrap().iter()))
                    .unwrap();
            }
        }
        if version >= 4 {
            // Preserve the monotonic job-ID counter even when earlier jobs were
            // pruned; this is derived workflow metadata, not canonical history.
            let seq: Option<i64> = destination
                .query_row(
                    "SELECT seq FROM sqlite_sequence WHERE name='memory_jobs'",
                    [],
                    |r| r.get(0),
                )
                .optional()
                .unwrap();
            if let Some(seq) = seq {
                tx.execute("DELETE FROM sqlite_sequence WHERE name='memory_jobs'", [])
                    .unwrap();
                tx.execute(
                    "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_jobs',?1)",
                    [seq],
                )
                .unwrap();
            }
        }
        assert!(!tx
            .prepare("PRAGMA foreign_key_check")
            .unwrap()
            .exists([])
            .unwrap());
        tx.commit().unwrap();
    }
    assert_legacy_defaults(&historical);
    // Replace only this already guarded, closed synthetic fixture with a fully
    // constructed old database. No current columns are retained or relabeled.
    rusqlite::backup::Backup::new(&historical, &mut destination)
        .unwrap()
        .run_to_completion(128, Duration::ZERO, None)
        .unwrap();
    assert!(!destination
        .prepare("PRAGMA foreign_key_check")
        .unwrap()
        .exists([])
        .unwrap());
    drop(destination);
    let mut old = Store::open_read_only(&path).unwrap();
    assert_eq!(old.info().unwrap().schema_version, version);
    for story in old.stories().unwrap() {
        old.branch_catalog(&story.scope.story, &|| false).unwrap();
    }
}
