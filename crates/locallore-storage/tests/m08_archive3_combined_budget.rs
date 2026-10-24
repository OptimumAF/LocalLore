// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Expensive opt-in actual accepted-record aggregate boundary. Frozen unrun.
//! SQL is read-only measurement of this test's private Store, never fixture admission.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord},
    contracts::*,
    engine::Engine,
};
use locallore_storage::{
    playable_archive::{MAX_ARCHIVE_BRANCHES, MAX_ARCHIVE_BYTES},
    validate_archive, ArchiveError, StorageError, Store, TurnError,
};
use rusqlite::{params, Connection, OpenFlags};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    path::{Path, PathBuf},
};

const CHILDREN: usize = 30;
const ROUNDS: usize = 20;
const SAY_BYTES: usize = 1024;
const PROJECTION_CAP: usize = 262_144;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
struct Cost {
    responses: usize,
    indexes: usize,
    records: usize,
}
impl Cost {
    fn plus(self, other: Self) -> Self {
        Self {
            responses: self.responses.checked_add(other.responses).unwrap(),
            indexes: self.indexes.checked_add(other.indexes).unwrap(),
            records: self.records.checked_add(other.records).unwrap(),
        }
    }
    fn combined(self) -> usize {
        self.responses.checked_add(self.indexes).unwrap()
    }
}

fn seed(story: &str) -> Seed {
    let mut value: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    value.scope.story = story.into();
    value.facts.get_mut("relic-location").unwrap().proposition = "BASE_A".into();
    value
}

fn create(store: &mut Store, story: &str) -> Scope {
    let value = seed(story);
    let scope = value.scope.clone();
    store
        .create_story("Synthetic combined archive boundary", value)
        .unwrap();
    scope
}

fn read_connection(path: &Path) -> Connection {
    Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap()
}

// The connection is local to each measurement and is dropped before the next
// Store transition. Author request_index is measured, NOT reimplemented here.
fn native_cost(path: &Path, engine: &Engine, record: &CanonicalRecord) -> Cost {
    let db = read_connection(path);
    let scope = record.original_scope();
    let (status, index, response): (String, String, String) = db.query_row(
        "SELECT status,request_json,response_json FROM turns WHERE story_id=?1 AND branch_id=?2 AND turn_id=?3",
        params![scope.story, scope.branch, record.turn_key()],
        |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
    ).unwrap();
    assert_eq!(status, "committed");
    assert_eq!(response.as_bytes(), serde_json::to_vec(record).unwrap());
    assert_eq!(engine.scope(), scope);
    if let Some(receipt) = record.receipt() {
        assert_eq!(
            index.as_bytes(),
            serde_json::to_vec(receipt.request()).unwrap()
        );
    }
    assert!(index.len() <= MAX_PROPOSAL_BYTES);
    assert!(response.len() <= MAX_RECEIPT_BYTES);
    Cost {
        responses: response.len(),
        indexes: index.len(),
        records: 1,
    }
}

fn aggregate_cost(path: &Path, story: &str) -> Cost {
    let db = read_connection(path);
    let (count, responses, indexes): (i64, i64, i64) = db.query_row(
        "SELECT count(*),coalesce(sum(length(CAST(response_json AS BLOB))),0),coalesce(sum(length(CAST(request_json AS BLOB))),0) FROM turns WHERE story_id=?1 AND status='committed'",
        [story],
        |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
    ).unwrap();
    let noncommitted: i64 = db
        .query_row(
            "SELECT count(*) FROM turns WHERE story_id=?1 AND status<>'committed'",
            [story],
            |row| row.get(0),
        )
        .unwrap();
    assert_eq!(noncommitted, 0);
    Cost {
        responses: usize::try_from(responses).unwrap(),
        indexes: usize::try_from(indexes).unwrap(),
        records: usize::try_from(count).unwrap(),
    }
}

fn scopes_and_engines(store: &mut Store, scopes: &[Scope]) -> Vec<Engine> {
    scopes
        .iter()
        .map(|scope| {
            let engine = store.resume(scope).unwrap().engine;
            assert!(engine.canonical_bytes().len() <= PROJECTION_CAP);
            assert!(engine.canonical_records().len() <= MAX_HISTORY_RECEIPTS);
            engine
        })
        .collect()
}

fn same_engine(actual: &Engine, expected: &Engine) {
    assert_eq!(actual.scope(), expected.scope());
    assert_eq!(actual.seed(), expected.seed());
    assert_eq!(actual.domain_version(), expected.domain_version());
    assert_eq!(actual.revision(), expected.revision());
    assert!(actual.canonical_records() == expected.canonical_records());
    assert!(actual.canonical_bytes() == expected.canonical_bytes());
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        expected.accepted_history_basis().unwrap()
    );
}

fn canonical(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort_unstable();
            let mut out = serde_json::Map::new();
            for key in keys {
                out.insert(key.clone(), canonical(&map[key]));
            }
            Value::Object(out)
        }
        Value::Array(values) => Value::Array(values.iter().map(canonical).collect()),
        value => value.clone(),
    }
}

fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn json_hash(value: &Value) -> String {
    hash(&serde_json::to_vec(&canonical(value)).unwrap())
}

// Build untrusted sender bytes only from actual Store-resumed accepted records.
// No Native record/receipt is deserialized or manufactured by this envelope.
fn assembled_above(mut below: Value, actual: &[Engine]) -> Vec<u8> {
    let branches = below["payload"]["branches"].as_array_mut().unwrap();
    for branch in branches.iter_mut() {
        let id = branch["id"].as_str().unwrap();
        let engine = actual
            .iter()
            .find(|engine| engine.scope().branch == id)
            .unwrap();
        let local: Vec<_> = engine
            .canonical_records()
            .iter()
            .filter(|record| record.original_scope() == engine.scope())
            .collect();
        branch["head_revision"] = json!(engine.revision());
        branch["local_records"] = serde_json::to_value(local).unwrap();
    }
    let branches = below["payload"]["branches"].as_array().unwrap();
    let integrity: Vec<_> = branches
        .iter()
        .map(|branch| {
            let id = branch["id"].as_str().unwrap();
            let engine = actual
                .iter()
                .find(|engine| engine.scope().branch == id)
                .unwrap();
            json!({"id":id,"records_sha256":json_hash(&branch["local_records"]),
            "canonical_state_sha256":hash(&engine.canonical_bytes())})
        })
        .collect();
    below["integrity"]["branches"] = json!(integrity);
    below["integrity"]["payload_sha256"] = json!(json_hash(&below["payload"]));
    serde_json::to_vec(&canonical(&below)).unwrap()
}

fn inventory(directory: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    // Only the test-created, closed rejection destination; no arbitrary tree walk.
    let mut result = BTreeMap::new();
    for entry in std::fs::read_dir(directory).unwrap() {
        let entry = entry.unwrap();
        let metadata = std::fs::symlink_metadata(entry.path()).unwrap();
        assert!(metadata.is_file() && !metadata.file_type().is_symlink());
        assert!(metadata.len() <= 1024 * 1024);
        result.insert(
            entry.file_name().into(),
            std::fs::read(entry.path()).unwrap(),
        );
    }
    result
}

#[test]
#[ignore = "expensive explicit accepted-record 16MiB boundary; coordinator runs serially"]
fn actual_records_cross_only_combined_response_and_native_index_archive_budget() {
    assert!(CHILDREN + 1 <= MAX_ARCHIVE_BRANCHES);
    assert!(SAY_BYTES <= MAX_TEXT_BYTES);
    let directory = std::env::temp_dir().join(format!(
        "locallore-archive3-combined-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&directory).unwrap();
    // Retain bounded generated data locally for exact failure/cost inspection.
    // The coordinator supplies its own D-drive TEMP; no repository artifact write.
    eprintln!(
        "combined-budget synthetic evidence: {}",
        directory.display()
    );
    let source_path = directory.join("source.sqlite");
    let mut source = Store::open(&source_path, None).unwrap();
    let root = create(&mut source, "archive3-combined");
    assert!(serde_json::to_vec(&seed(&root.story)).unwrap().len() <= 131_072);
    let mut scopes = vec![root.clone()];
    let mut engines = Vec::new();
    let mut totals = Cost::default();
    for index in 0..CHILDREN {
        let input = AuthorCorrectionInputV1 {
            version: 1,
            parent: root.clone(),
            expected_parent_revision: 0,
            fork_revision: 0,
            child_branch: format!("b{index:02}"),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "relic-location".into(),
                expected_proposition: "BASE_A".into(),
                replacement: format!("PRIVATE_B_{index:02}"),
            },
            reason: format!("Synthetic independent authored branch {index:02}"),
        };
        let prepared = source.prepare_author_correction(&input, &|| false).unwrap();
        let outcome = source
            .apply_author_correction(&prepared, &|| false)
            .unwrap();
        assert!(outcome.created);
        let engine = source.resume(&outcome.scope).unwrap().engine;
        assert_eq!(engine.domain_version(), 2);
        let record = engine.canonical_records().last().unwrap();
        assert!(matches!(record, CanonicalRecord::AuthorV1(_)));
        totals = totals.plus(native_cost(&source_path, &engine, record));
        scopes.push(outcome.scope);
        engines.push(engine);
    }
    assert_eq!(aggregate_cost(&source_path, &root.story), totals);
    let mut below_archive = None;
    let mut below_cost = None;
    let mut crossing_cost = None;
    'construction: for round in 0..ROUNDS {
        for (index, engine) in engines.iter_mut().enumerate() {
            let commands: Vec<_> = (0..MAX_COMMANDS)
                .map(|command| {
                    let label = format!("SYNTHETIC_{index:02}_{round:02}_{command}_");
                    let text = format!("{label}{}", "x".repeat(SAY_BYTES - label.len()));
                    assert_eq!(text.len(), SAY_BYTES);
                    Command::Say {
                        text,
                        audience: ["mira".into()].into(),
                    }
                })
                .collect();
            let request = engine.request(&format!("bytes-{round:02}"), Intent::Actions(commands));
            let proposal = Engine::proposal(&request).unwrap();
            assert!(serde_json::to_vec(&request).unwrap().len() <= MAX_PROPOSAL_BYTES);
            assert!(serde_json::to_vec(&proposal).unwrap().len() <= MAX_PROPOSAL_BYTES);
            let approved = engine.preview(&request, &proposal).unwrap();
            let mut predicted = engine.clone();
            predicted.commit_prepared(&approved).unwrap();
            assert!(predicted.canonical_bytes().len() <= PROJECTION_CAP);
            let record = predicted.canonical_records().last().unwrap();
            let next = Cost {
                responses: serde_json::to_vec(record).unwrap().len(),
                indexes: serde_json::to_vec(&request).unwrap().len(),
                records: 1,
            };
            assert!(next.responses <= MAX_RECEIPT_BYTES);
            let after = totals.plus(next);
            assert!(after.responses <= MAX_HISTORY_BYTES);
            assert!(after.records <= MAX_HISTORY_RECEIPTS);
            let crosses = after.combined() > MAX_HISTORY_BYTES;
            if crosses {
                assert!(totals.combined() <= MAX_HISTORY_BYTES);
                assert_eq!(aggregate_cost(&source_path, &root.story), totals);
                let original = scopes_and_engines(&mut source, &scopes);
                let archive = source.export_archive(&root.story, &|| false).unwrap();
                assert_eq!(archive.preview().version, 3);
                assert_eq!(archive.preview().committed_turns, totals.records);
                assert!(archive.bytes().len() <= MAX_ARCHIVE_BYTES);
                eprintln!(
                    "combined-budget last-below: responses={} indexes={} combined={} gap={} records={} branches={} archive_bytes={}",
                    totals.responses, totals.indexes, totals.combined(),
                    MAX_HISTORY_BYTES - totals.combined(), totals.records, scopes.len(), archive.bytes().len()
                );
                let raw: Value = serde_json::from_slice(archive.bytes()).unwrap();
                assert_eq!(
                    raw["payload"]["branches"].as_array().unwrap().len(),
                    CHILDREN + 1
                );
                let imported_path = directory.join("below.sqlite");
                let mut target = Store::open(&imported_path, None).unwrap();
                target
                    .import_archive(
                        validate_archive(archive.bytes(), &|| false).unwrap(),
                        &|| false,
                    )
                    .unwrap();
                assert_eq!(aggregate_cost(&imported_path, &root.story), totals);
                for expected in &original {
                    same_engine(&target.resume(expected.scope()).unwrap().engine, expected);
                }
                assert!(
                    target
                        .export_archive(&root.story, &|| false)
                        .unwrap()
                        .bytes()
                        == archive.bytes()
                );
                drop(target);
                let mut reopened = Store::open(&imported_path, None).unwrap();
                for expected in &original {
                    same_engine(&reopened.resume(expected.scope()).unwrap().engine, expected);
                }
                assert!(
                    reopened
                        .export_archive(&root.story, &|| false)
                        .unwrap()
                        .bytes()
                        == archive.bytes()
                );
                drop(reopened);
                below_archive = Some(raw);
                below_cost = Some(totals);
            }
            source.begin_turn(&request).unwrap();
            let committed = source.commit_prepared(&approved).unwrap();
            assert_eq!(committed, approved);
            engine.commit_prepared(&committed).unwrap();
            same_engine(engine, &predicted);
            assert_eq!(
                native_cost(
                    &source_path,
                    engine,
                    engine.canonical_records().last().unwrap()
                ),
                next
            );
            totals = after;
            if crosses {
                crossing_cost = Some(next);
                break 'construction;
            }
        }
    }
    let before =
        below_cost.expect("bounded 600-play-record construction must reach combined boundary");
    let crossing = crossing_cost.unwrap();
    assert_eq!(before.plus(crossing), totals);
    assert!(before.combined() <= MAX_HISTORY_BYTES && totals.combined() > MAX_HISTORY_BYTES);
    assert!(MAX_HISTORY_BYTES - before.combined() < crossing.combined());
    assert!(totals.responses <= MAX_HISTORY_BYTES);
    assert!(totals.records <= CHILDREN * (ROUNDS + 1));
    assert!(totals.records <= MAX_HISTORY_RECEIPTS);
    assert_eq!(aggregate_cost(&source_path, &root.story), totals);
    let actual = scopes_and_engines(&mut source, &scopes);
    for tracked in &engines {
        same_engine(
            actual
                .iter()
                .find(|actual| actual.scope() == tracked.scope())
                .unwrap(),
            tracked,
        );
    }
    let wire = assembled_above(below_archive.unwrap(), &actual);
    assert!(
        wire.len() <= MAX_ARCHIVE_BYTES,
        "wire cap must not explain refusal"
    );
    let raw: Value = serde_json::from_slice(&wire).unwrap();
    assert_eq!(raw["payload"]["domain_version"], 2);
    assert_eq!(raw["payload"]["source_database_schema_version"], 5);
    assert_eq!(raw["payload"]["model_references"], json!([]));
    assert_eq!(raw["payload"]["required_policies"], json!([]));
    assert_eq!(raw["payload"]["retired_branch_ids"], json!([]));
    assert_eq!(
        raw["payload"]["branches"].as_array().unwrap().len(),
        CHILDREN + 1
    );
    let mut response_count = 0;
    let mut response_bytes = 0;
    for branch in raw["payload"]["branches"].as_array().unwrap() {
        for record in branch["local_records"].as_array().unwrap() {
            let size = serde_json::to_vec(record).unwrap().len();
            assert!(size <= MAX_RECEIPT_BYTES);
            response_count += 1;
            response_bytes += size;
        }
    }
    assert_eq!(response_count, totals.records);
    assert_eq!(response_bytes, totals.responses);
    assert!(response_bytes <= MAX_HISTORY_BYTES);
    // Source export and untrusted independent validation must both reach the
    // combined cap. The destination has a different, unrelated retained story.
    let rejection_dir = directory.join("rejected-target");
    std::fs::create_dir(&rejection_dir).unwrap();
    let rejection_path = rejection_dir.join("target.sqlite");
    let mut destination = Store::open(&rejection_path, None).unwrap();
    let control = create(&mut destination, "foreign-control");
    let retained = destination.resume(&control).unwrap().engine;
    let keep = retained.request(
        "keep-accepted",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&keep).unwrap();
    let accepted = retained.preview(&keep, &proposal).unwrap();
    destination.begin_turn(&keep).unwrap();
    destination.commit_prepared(&accepted).unwrap();
    let retained = destination.resume(&control).unwrap().engine;
    drop(destination);
    let destination_bytes = inventory(&rejection_dir);
    eprintln!(
        "combined-budget measured: below responses={} indexes={} combined={} gap={}; crossing responses={} indexes={}; above responses={} indexes={} combined={} records={} branches={} hostile_wire={} cap={}",
        before.responses, before.indexes, before.combined(), MAX_HISTORY_BYTES - before.combined(),
        crossing.responses, crossing.indexes, totals.responses, totals.indexes, totals.combined(),
        totals.records, scopes.len(), wire.len(), MAX_HISTORY_BYTES
    );
    assert_eq!(
        source.export_archive(&root.story, &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
    assert_eq!(
        validate_archive(&wire, &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
    assert!(inventory(&rejection_dir) == destination_bytes);
    let mut destination = Store::open(&rejection_path, None).unwrap();
    same_engine(&destination.resume(&control).unwrap().engine, &retained);
    assert_eq!(destination.stories().unwrap().len(), 1);
    assert!(matches!(
        destination.resume(&root),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
    drop(destination);
    assert!(inventory(&rejection_dir) == destination_bytes);
}
