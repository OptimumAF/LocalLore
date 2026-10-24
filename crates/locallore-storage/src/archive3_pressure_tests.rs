// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen test-only real SQLite Busy/Full and exhaustive callback rollback.
//! No physical ENOSPC, process-death, provider, or platform-transfer claim.
use crate::{validate_archive, ArchiveError, StorageError, Store, TurnError};
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
};
use rusqlite::{types::ValueRef, Connection};
use std::{cell::Cell, collections::BTreeMap, path::PathBuf, time::Duration};

const SOURCE: &str = "archive3-pressure-source";
const CONTROL: &str = "archive3-pressure-control";
const MAX_POLLS: usize = 128;

struct Temp(PathBuf);
impl Temp {
    fn new(label: &str) -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-archive3-pressure-{label}-{}-{}", std::process::id(),
            std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()
        ));
        std::fs::create_dir(&path).unwrap();
        eprintln!("Archive3 pressure synthetic evidence: {}", path.display());
        Self(path)
    }
    fn path(&self, name: &str) -> PathBuf { self.0.join(name) }
    fn open(&self, name: &str) -> Store { Store::open(&self.path(name), None).unwrap() }
}

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
enum RawCell {
    Null,
    Integer(i64),
    Real(u64),
    Text(Vec<u8>),
    Blob(Vec<u8>),
}
type RawState = BTreeMap<String, Vec<Vec<RawCell>>>;

fn raw_state(connection: &Connection) -> RawState {
    let tables: Vec<String> = connection.prepare(
        "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"
    ).unwrap().query_map([], |row| row.get(0)).unwrap()
        .collect::<rusqlite::Result<_>>().unwrap();
    assert!(tables.len() <= 32);
    let mut state = BTreeMap::new();
    let mut total = 0usize;
    for table in tables {
        // Only names from this Store's actual schema; preserve cell types/bytes
        // and all columns, including sqlite_sequence and derived workflow rows.
        let quoted = table.replace('"', "\"\"");
        let mut query = connection.prepare(&format!("SELECT * FROM \"{quoted}\"" )).unwrap();
        let columns = query.column_count();
        assert!(columns <= 32);
        let mut rows = query.query_map([], |row| {
            (0..columns).map(|column| Ok(match row.get_ref(column)? {
                ValueRef::Null => RawCell::Null,
                ValueRef::Integer(value) => RawCell::Integer(value),
                ValueRef::Real(value) => RawCell::Real(value.to_bits()),
                ValueRef::Text(value) => RawCell::Text(value.to_vec()),
                ValueRef::Blob(value) => RawCell::Blob(value.to_vec()),
            })).collect::<rusqlite::Result<Vec<_>>>()
        }).unwrap().collect::<rusqlite::Result<Vec<_>>>().unwrap();
        assert!(rows.len() <= 4096);
        for row in &rows {
            for cell in row {
                if let RawCell::Text(bytes) | RawCell::Blob(bytes) = cell {
                    total = total.checked_add(bytes.len()).unwrap();
                    assert!(total <= 16 * 1024 * 1024);
                }
            }
        }
        rows.sort();
        state.insert(table, rows);
    }
    state
}

fn seed(story: &str) -> Seed {
    let mut seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "OBSERVED_A".into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    seed
}

fn apply(store: &mut Store, scope: &Scope, turn: &str, commands: Vec<Command>) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    assert!(serde_json::to_vec(&request).unwrap().len() <= MAX_PROPOSAL_BYTES);
    assert!(serde_json::to_vec(&proposal).unwrap().len() <= MAX_PROPOSAL_BYTES);
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    assert_eq!(store.commit_prepared(&receipt).unwrap(), receipt);
}

fn populate(store: &mut Store, story: &str, large: bool) -> Vec<Engine> {
    let seed = seed(story);
    let root = seed.scope.clone();
    store.create_story("Synthetic mixed Archive3 pressure", seed).unwrap();
    apply(store, &root, "prefix", vec![Command::Wait { ticks: 1 }]);
    let input = AuthorCorrectionInputV1 {
        version: 1, parent: root.clone(), expected_parent_revision: 1, fork_revision: 1,
        child_branch: "author-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(), expected_proposition: "OBSERVED_A".into(),
            replacement: "PRIVATE_B".into(),
        },
        reason: "PRIVATE_SYNTHETIC_AUTHOR_REASON".into(),
    };
    let plan = store.prepare_author_correction(&input, &|| false).unwrap();
    let child = store.apply_author_correction(&plan, &|| false).unwrap().scope;
    apply(store, &child, "observed-and-waited", vec![
        Command::Discover { fact: "relic-location".into() }, Command::Wait { ticks: 1 },
    ]);
    if large {
        // Fixed bound: 32 additional genuine typed receipts, 128 accepted Said
        // events. Large enough to exceed the entire small target page quota,
        // while its actual projection remains below the unchanged 256KiB cap.
        for turn in 0..32 {
            let commands = (0..4).map(|index| {
                let label = format!("SYNTHETIC_{turn:02}_{index}_");
                Command::Say {
                    text: format!("{label}{}", "x".repeat(1536 - label.len())),
                    audience: ["mira".into()].into(),
                }
            }).collect();
            apply(store, &child, &format!("large-{turn:02}"), commands);
        }
    }
    [root, child].iter().map(|scope| {
        let engine = store.resume(scope).unwrap().engine;
        assert!(engine.canonical_bytes().len() <= 262_144);
        engine
    }).collect()
}

struct Fixture { bytes: Vec<u8>, engines: Vec<Engine>, native_bytes: u64 }
fn fixture(temp: &Temp, large: bool) -> Fixture {
    let mut source = temp.open("source.sqlite");
    let engines = populate(&mut source, SOURCE, large);
    let native_bytes: i64 = source.connection.query_row(
        "SELECT sum(length(CAST(request_json AS BLOB))+length(CAST(response_json AS BLOB))) FROM turns WHERE story_id=?1 AND status='committed'",
        [SOURCE], |row| row.get(0),
    ).unwrap();
    let archive = source.export_archive(SOURCE, &|| false).unwrap();
    assert_eq!(archive.preview().version, 3);
    assert_eq!(archive.preview().committed_turns, if large { 35 } else { 3 });
    assert!(archive.bytes().len() <= 2 * 1024 * 1024);
    Fixture { bytes: archive.bytes().to_vec(), engines, native_bytes: u64::try_from(native_bytes).unwrap() }
}

fn same(actual: &Engine, expected: &Engine) {
    assert_eq!(actual.scope(), expected.scope());
    assert_eq!(actual.revision(), expected.revision());
    assert_eq!(actual.domain_version(), expected.domain_version());
    assert!(actual.seed() == expected.seed());
    assert!(actual.canonical_records() == expected.canonical_records());
    assert!(actual.canonical_bytes() == expected.canonical_bytes());
    assert_eq!(actual.accepted_history_basis().unwrap(), expected.accepted_history_basis().unwrap());
}

struct Baseline { rows: RawState, engines: Vec<Engine> }
fn destination(temp: &Temp, name: &str) -> (Store, Baseline) {
    let mut store = temp.open(name);
    let engines = populate(&mut store, CONTROL, false);
    let root = &engines[0];
    // Nonempty derived workflow and sqlite_sequence must survive failures too.
    let info = store.ensure_memory_job(&crate::memory_jobs::MemoryJobRequest {
        scope: root.scope().clone(), observer: root.seed().player.clone(), expected_head: root.revision(),
    }, &|| false).unwrap();
    assert_eq!(info.status, crate::memory_jobs::MemoryJobStatus::Ready);
    let rows = raw_state(&store.connection);
    assert!(!rows["memory_jobs"].is_empty());
    assert!(!rows["sqlite_sequence"].is_empty());
    (store, Baseline { rows, engines })
}

fn unchanged(store: &mut Store, before: &Baseline) {
    assert!(raw_state(&store.connection) == before.rows, "all logical raw-table rows must roll back");
    for engine in &before.engines { same(&store.resume(engine.scope()).unwrap().engine, engine); }
    assert_eq!(store.stories().unwrap().len(), 1);
    assert!(matches!(store.resume(&Scope { story: SOURCE.into(), branch: "main".into() }),
        Err(TurnError::Storage(StorageError::NotFound))));
    assert!(raw_state(&store.connection) == before.rows);
}

fn cold_unchanged(temp: &Temp, name: &str, store: Store, before: &Baseline) -> Store {
    drop(store);
    let mut reopened = temp.open(name);
    unchanged(&mut reopened, before);
    reopened
}

fn succeeds(store: &mut Store, fixture: &Fixture, before: &Baseline) {
    let outcome = store.import_archive(validate_archive(&fixture.bytes, &|| false).unwrap(), &|| false).unwrap();
    assert_eq!(outcome.branches, 2);
    assert_eq!(outcome.committed_turns, if fixture.engines[1].canonical_record_count() > 3 { 35 } else { 3 });
    for engine in &fixture.engines { same(&store.resume(engine.scope()).unwrap().engine, engine); }
    for engine in &before.engines { same(&store.resume(engine.scope()).unwrap().engine, engine); }
    let after = raw_state(&store.connection);
    for (table, rows) in &before.rows {
        assert!(rows.iter().all(|row| after[table].contains(row)), "retained rows changed in {table}");
    }
    assert_eq!(store.stories().unwrap().len(), 2);
    assert!(store.export_archive(SOURCE, &|| false).unwrap().bytes() == fixture.bytes);
    let won = raw_state(&store.connection);
    assert_eq!(store.import_archive(validate_archive(&fixture.bytes, &|| false).unwrap(), &|| false), Err(ArchiveError::Conflict));
    assert!(raw_state(&store.connection) == won);
}

fn pragma(connection: &Connection, name: &str) -> u64 {
    let value: i64 = connection.pragma_query_value(None, name, |row| row.get(0)).unwrap();
    u64::try_from(value).unwrap()
}

#[test]
fn actual_mixed_archive_busy_writer_rolls_back_and_fresh_token_retries_after_release() {
    let temp = Temp::new("busy");
    let fixture = fixture(&temp, false);
    let (mut store, before) = destination(&temp, "target.sqlite");
    let old_timeout = pragma(&store.connection, "busy_timeout");
    store.connection.busy_timeout(Duration::ZERO).unwrap();
    let blocker = Connection::open(temp.path("target.sqlite")).unwrap();
    blocker.execute_batch("BEGIN IMMEDIATE").unwrap();
    let result = store.import_archive(validate_archive(&fixture.bytes, &|| false).unwrap(), &|| false);
    blocker.execute_batch("ROLLBACK").unwrap();
    drop(blocker);
    store.connection.busy_timeout(Duration::from_millis(old_timeout)).unwrap();
    assert_eq!(result, Err(ArchiveError::Busy), "actual lock contention must be Busy");
    unchanged(&mut store, &before);
    let mut reopened = cold_unchanged(&temp, "target.sqlite", store, &before);
    succeeds(&mut reopened, &fixture, &before);
    drop(reopened);
    let mut reopened = temp.open("target.sqlite");
    for engine in &fixture.engines { same(&reopened.resume(engine.scope()).unwrap().engine, engine); }
    for engine in &before.engines { same(&reopened.resume(engine.scope()).unwrap().engine, engine); }
}

#[test]
fn actual_mixed_archive_full_rolls_back_cold_and_retries_only_after_local_cap_restoration() {
    let temp = Temp::new("full");
    let fixture = fixture(&temp, true);
    let (mut store, before) = destination(&temp, "target.sqlite");
    let pages = pragma(&store.connection, "page_count");
    let free = pragma(&store.connection, "freelist_count");
    let page_size = pragma(&store.connection, "page_size");
    assert!(pages <= 1024 && free <= pages);
    let quota_bytes = pages.checked_mul(page_size).unwrap();
    eprintln!("mixed Full calibration pages={pages} free={free} page_size={page_size} quota_bytes={quota_bytes} incoming_native_bytes={} archive_bytes={}", fixture.native_bytes, fixture.bytes.len());
    // Stronger than merely counting freelist pages: the incoming uncompressed
    // canonical+index TEXT alone exceeds the ENTIRE capped target file.
    assert!(fixture.native_bytes > quota_bytes, "fixed fixture must genuinely need growth");
    for attempt in 0..2 {
        let original_max = pragma(&store.connection, "max_page_count");
        assert!(original_max > pages);
        store.connection.pragma_update(None, "max_page_count", i64::try_from(pages).unwrap()).unwrap();
        assert_eq!(pragma(&store.connection, "max_page_count"), pages);
        let observed = Cell::new(0usize);
        let result = store.import_archive(validate_archive(&fixture.bytes, &|| false).unwrap(), &|| {
            observed.set(observed.get() + 1);
            assert!(observed.get() <= 512, "bounded large-fixture import polls");
            false
        });
        let limited_max = pragma(&store.connection, "max_page_count");
        // Only this actual Store connection's test quota is restored. No cache,
        // canonical row, global SQLite setting, or compiled limit is modified.
        store.connection.pragma_update(None, "max_page_count", i64::try_from(original_max).unwrap()).unwrap();
        assert_eq!(pragma(&store.connection, "max_page_count"), original_max);
        assert_eq!(limited_max, pages);
        eprintln!("mixed Full attempt={attempt} observed_import_polls={}; exact failing SQL statement is not observed", observed.get());
        assert_eq!(result, Err(ArchiveError::Full), "attempt {attempt}: require real SQLITE_FULL");
        unchanged(&mut store, &before);
        assert_eq!(pragma(&store.connection, "page_count"), pages);
        assert_eq!(pragma(&store.connection, "freelist_count"), free);
        store = cold_unchanged(&temp, "target.sqlite", store, &before);
    }
    eprintln!("mixed Full retry relief: restored only connection-local max_page_count; no deletion/physical-space claim");
    succeeds(&mut store, &fixture, &before);
    drop(store);
    let mut reopened = temp.open("target.sqlite");
    for engine in &fixture.engines { same(&reopened.resume(engine.scope()).unwrap().engine, engine); }
    for engine in &before.engines { same(&reopened.resume(engine.scope()).unwrap().engine, engine); }
}

#[test]
fn every_observed_mixed_import_cancel_or_panic_poll_rolls_back_including_final_precommit() {
    let temp = Temp::new("cancel");
    let fixture = fixture(&temp, false);
    let (mut counter, _) = destination(&temp, "count.sqlite");
    let polls = Cell::new(0usize);
    counter.import_archive(validate_archive(&fixture.bytes, &|| false).unwrap(), &|| {
        polls.set(polls.get() + 1);
        assert!(polls.get() <= MAX_POLLS, "fixed fixture callback budget");
        false
    }).unwrap();
    let total = polls.get();
    assert!(total > 4 && total <= MAX_POLLS);
    drop(counter);
    eprintln!("mixed import exhaustive observed callback count={total}; cases={} final_precommit_poll={total}", total * 2);
    // Store import has no callback after tx.commit: the final observed callback
    // is its existing last precommit check, not an invented postcommit hook.
    for panic_at_stop in [false, true] {
        for stop in 1..=total {
            let name = format!("cancel-{}-{stop:03}.sqlite", if panic_at_stop { "panic" } else { "true" });
            let (mut store, before) = destination(&temp, &name);
            let seen = Cell::new(0usize);
            let result = store.import_archive(validate_archive(&fixture.bytes, &|| false).unwrap(), &|| {
                seen.set(seen.get() + 1);
                if seen.get() == stop {
                    assert!(!panic_at_stop, "synthetic Archive3 cancellation panic at poll {stop}");
                    return true;
                }
                false
            });
            assert_eq!(seen.get(), stop);
            assert_eq!(result, Err(ArchiveError::Cancelled), "stop {stop}/{total} panic={panic_at_stop}");
            unchanged(&mut store, &before);
            let mut reopened = cold_unchanged(&temp, &name, store, &before);
            // A consumed import plan is not reused; same immutable bytes are
            // freshly validated. Cancellation has left no terminal import key.
            succeeds(&mut reopened, &fixture, &before);
        }
    }
}
