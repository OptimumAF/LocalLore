// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent tests of the actual schema4 Store API. No inference or canonical SQL writes.
//! Expected oracles are frozen before first execution; production is coordinator-owned.
use locallore::{
    contracts::*,
    engine::Engine,
    memory_coverage::{self, ChunkRequest, Closure, CoverageRead, CoverageRequest, TypedPacket},
};
use locallore_storage::{
    derived_memory::MemoryError,
    memory_jobs::{
        MemoryJobFailure, MemoryJobHandle, MemoryJobInfo, MemoryJobRequest, MemoryJobStatus,
    },
    playable_archive::validate_archive,
    ForkRequest, Store,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    cell::Cell,
    path::PathBuf,
    process::Command as ProcessCommand,
    sync::{
        atomic::{AtomicU64, Ordering},
        mpsc,
    },
    time::{Duration, Instant},
};

const EVENTS: u64 = 384;
const RECEIPTS: usize = 96;
const PRIVATE: &str = "JOB-PLAYER-PRIVATE";
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-jobs-review-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        Self(directory)
    }
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
    fn open(&self) -> Store {
        Store::open_application(&self.path("source.sqlite")).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed(story: &str) -> Seed {
    serde_json::from_value(json!({
        "version":1,"id":format!("job-seed-{story}"),"scope":{"story":story,"branch":"main"},
        "profile":"fantasy_v1","player":"player","locations":["garden","tower"],"routes":[],
        "actors":{
            "player":{"name":"Iris","location":"garden","alive":true,"energy":2,"abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]},
            "agent":{"name":"Robin","location":"garden","alive":true,"energy":2,"abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]},
            "silent":{"name":"Robin","location":"tower","alive":true,"energy":2,"abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]}
        },"items":{},"abilities":{},"facts":{},"relationships":[],"story_time":100,"beliefs":[],"commitments":{}
    })).unwrap()
}
fn say(text: &str, audience: &str) -> Command {
    Command::Say {
        text: text.into(),
        audience: [audience.into()].into(),
    }
}
fn apply(store: &mut Store, engine: &mut Engine, key: &str, commands: Vec<Command>) {
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    let actual = store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap();
    assert_eq!(actual, preview);
    assert_eq!(
        engine
            .commit(&request, &proposal, preview.narration())
            .unwrap(),
        actual
    );
}
fn fixture() -> (Temp, Store, Engine) {
    let temp = Temp::new();
    let mut store = temp.open();
    let seed = seed("job-review");
    let mut engine = Engine::new(seed.clone()).unwrap();
    store
        .create_story("Original job review fixture", seed)
        .unwrap();
    for batch in 0..RECEIPTS {
        let commands = (0..4)
            .map(|slot| {
                let index = batch * 4 + slot;
                if index == 0 {
                    Command::Promise {
                        id: "old-promise".into(),
                        to: "agent".into(),
                        terms: "Bring the amber lantern.".into(),
                        deadline: 600,
                        return_item: None,
                    }
                } else if index == 1 {
                    say(PRIVATE, "player")
                } else {
                    say(&format!("Garden ledger slate {index:03}."), "agent")
                }
            })
            .collect();
        apply(
            &mut store,
            &mut engine,
            &format!("batch-{batch:03}"),
            commands,
        );
    }
    assert_eq!(engine.revision(), EVENTS);
    assert_eq!(engine.receipts().len(), RECEIPTS);
    assert_eq!(
        engine
            .receipts()
            .iter()
            .map(|r| r.events().len())
            .sum::<usize>(),
        EVENTS as usize
    );
    (temp, store, engine)
}
fn request(engine: &Engine, observer: &str) -> MemoryJobRequest {
    MemoryJobRequest {
        scope: engine.scope().clone(),
        observer: observer.into(),
        expected_head: engine.revision(),
    }
}
fn core_request(request: &MemoryJobRequest) -> CoverageRequest {
    CoverageRequest {
        scope: request.scope.clone(),
        observer: request.observer.clone(),
        expected_head: request.expected_head,
    }
}
fn packets(engine: &Engine, observer: &str) -> Vec<TypedPacket> {
    let mut cursor = 0;
    let mut packets = vec![];
    while cursor < engine.revision() {
        assert!(packets.len() < memory_coverage::MAX_PACKETS);
        let packet = memory_coverage::build_chunk(
            engine,
            &ChunkRequest {
                scope: engine.scope().clone(),
                expected_head: engine.revision(),
                observer: observer.into(),
                from_exclusive: cursor,
            },
            &|| false,
        )
        .unwrap()
        .expect("nonempty completed history advances a packet boundary");
        assert!(packet.through_revision > cursor);
        cursor = packet.through_revision;
        packets.push(packet);
    }
    packets
}
fn status_name(status: &MemoryJobStatus) -> &'static str {
    match status {
        MemoryJobStatus::Ready => "ready",
        MemoryJobStatus::Cancelled => "cancelled",
        MemoryJobStatus::Stale => "stale",
        MemoryJobStatus::Complete => "complete",
        MemoryJobStatus::Blocked => "blocked",
    }
}
fn identity(info: &MemoryJobInfo) -> (u64, &'static str, u64, u64, u64, bool) {
    (
        info.handle.id(),
        status_name(&info.status),
        info.basis_revision,
        info.next_from,
        info.generation,
        info.last_error.is_some(),
    )
}
fn drain(store: &mut Store, handle: &MemoryJobHandle) -> MemoryJobInfo {
    for _ in 0..=memory_coverage::MAX_PACKETS {
        let before = store.memory_job_status(handle, &|| false).unwrap();
        if matches!(before.status, MemoryJobStatus::Complete) {
            return before;
        }
        assert!(
            matches!(before.status, MemoryJobStatus::Ready),
            "maintenance did not remain ready"
        );
        let prepared = store.prepare_memory_job_step(handle, &|| false).unwrap();
        let after = store.publish_memory_job_step(prepared, &|| false).unwrap();
        assert!(
            after.next_from > before.next_from || matches!(after.status, MemoryJobStatus::Complete)
        );
    }
    panic!("bounded packet quota was exhausted without a terminal result");
}
fn assert_canon(store: &mut Store, expected: &Engine) {
    let actual = store.resume(expected.scope()).unwrap().engine;
    assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(actual.receipts(), expected.receipts());
}
fn fingerprint(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn sql_integer(value: u64) -> i64 {
    i64::try_from(value).expect("public job identity fits the actual SQLite integer range")
}
fn sql_unsigned(row: &rusqlite::Row<'_>, index: usize) -> rusqlite::Result<u64> {
    let value: i64 = row.get(index)?;
    u64::try_from(value).map_err(|error| {
        rusqlite::Error::FromSqlConversionFailure(
            index,
            rusqlite::types::Type::Integer,
            Box::new(error),
        )
    })
}
fn cache_rows(db: &Connection, handle: &MemoryJobHandle) -> Vec<(u64, u64, String)> {
    let mut query = db.prepare("SELECT from_revision,through_revision,packet_json FROM memory_job_packets WHERE job_id=?1 ORDER BY from_revision").unwrap();
    let rows = query
        .query_map([sql_integer(handle.id())], |row| {
            Ok((sql_unsigned(row, 0)?, sql_unsigned(row, 1)?, row.get(2)?))
        })
        .unwrap()
        .map(Result::unwrap)
        .collect();
    rows
}
fn job_row(db: &Connection, handle: &MemoryJobHandle) -> String {
    db.query_row("SELECT json_object('id',job_id,'story',story_id,'branch',branch_id,'observer',observer_id,'method',method,'version',summary_version,'basis',basis_revision,'seed',seed_sha256,'lineage',lineage_sha256,'source',source_sha256,'cursor',next_from,'generation',generation,'status',status,'last_error',last_error) FROM memory_jobs WHERE job_id=?1", [sql_integer(handle.id())], |row| row.get(0)).unwrap()
}
fn verified(
    store: &mut Store,
    expected: &Engine,
    req: &MemoryJobRequest,
) -> memory_coverage::VerifiedCoverage {
    let snapshot = store.context_snapshot(req, &|| false).unwrap();
    assert_eq!(
        snapshot.engine.canonical_bytes(),
        expected.canonical_bytes()
    );
    assert_eq!(snapshot.engine.receipts(), expected.receipts());
    let CoverageRead::Verified(proof) = snapshot.coverage else {
        panic!("expected actual verified coverage, not fallback");
    };
    assert_eq!(proof.verified_head(), snapshot.engine.revision());
    assert!(matches!(
        proof
            .recheck(&snapshot.engine, &core_request(req), &|| false)
            .unwrap(),
        CoverageRead::Verified(_)
    ));
    proof
}

#[test]
fn packet_cursor_is_durable_and_core_bound_without_canonical_mutation() {
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let expected = packets(&engine, "agent");
    assert!(
        expected.len() >= 2,
        "384 accepted events cannot fit one 256-event packet"
    );
    assert!(expected[0].closure.is_sealed());
    let initial = store.ensure_memory_job(&req, &|| false).unwrap();
    assert_eq!((initial.basis_revision, initial.next_from), (EVENTS, 0));
    assert!(matches!(initial.status, MemoryJobStatus::Ready));
    assert_eq!(
        identity(&store.ensure_memory_job(&req, &|| false).unwrap()),
        identity(&initial)
    );
    let prepared = store
        .prepare_memory_job_step(&initial.handle, &|| false)
        .unwrap();
    assert_eq!(
        identity(&store.memory_job_status(&initial.handle, &|| false).unwrap()),
        identity(&initial)
    );
    assert_canon(&mut store, &engine);
    let first = store.publish_memory_job_step(prepared, &|| false).unwrap();
    assert_eq!(first.next_from, expected[0].through_revision);
    let proof = verified(&mut store, &engine, &req);
    assert_eq!(proof.covered_through(), first.next_from);
    assert_eq!(proof.raw_delta_after(), first.next_from);
    assert_eq!(proof.packets(), &expected[..1]);
    let first_packet_hash = fingerprint(&proof.packets()[0].bytes().unwrap());
    let before = identity(&first);
    let handle = first.handle.clone();
    drop(store);
    let mut store = temp.open();
    assert!(
        matches!(
            store.memory_job_status(&handle, &|| false),
            Err(MemoryError::NotFound)
        ),
        "native handle expires with its Store owner"
    );
    let reopened = store.ensure_memory_job(&req, &|| false).unwrap();
    assert_eq!(
        identity(&reopened),
        before,
        "durable checkpoint must survive owner replacement"
    );
    let handle = reopened.handle;
    assert_eq!(
        identity(&store.memory_job_status(&handle, &|| false).unwrap()),
        before
    );
    assert_eq!(
        fingerprint(
            &verified(&mut store, &engine, &req).packets()[0]
                .bytes()
                .unwrap()
        ),
        first_packet_hash
    );
    let complete = drain(&mut store, &handle);
    assert_eq!(complete.next_from, EVENTS);
    assert_eq!(verified(&mut store, &engine, &req).packets(), expected);
    assert!(matches!(
        store.prepare_memory_job_step(&handle, &|| false),
        Err(MemoryError::InvalidInput)
    ));
    let cancelled_complete = store.cancel_memory_job(&handle, &|| false).unwrap();
    assert!(matches!(
        cancelled_complete.status,
        MemoryJobStatus::Complete
    ));
    assert_eq!(cancelled_complete.next_from, EVENTS);
    assert_canon(&mut store, &engine);
}

#[test]
fn two_owners_compete_at_one_cursor_and_only_one_prepared_step_advances() {
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let info = store.ensure_memory_job(&req, &|| false).unwrap();
    let mut other = temp.open();
    let other_info = other.ensure_memory_job(&req, &|| false).unwrap();
    assert_eq!(identity(&other_info), identity(&info));
    let a = store
        .prepare_memory_job_step(&info.handle, &|| false)
        .unwrap();
    let b = other
        .prepare_memory_job_step(&other_info.handle, &|| false)
        .unwrap();
    let winner = store.publish_memory_job_step(a, &|| false).unwrap();
    assert!(matches!(
        other.publish_memory_job_step(b, &|| false),
        Err(MemoryError::Stale)
    ));
    assert_eq!(
        identity(
            &other
                .memory_job_status(&other_info.handle, &|| false)
                .unwrap()
        ),
        identity(&winner)
    );
    assert_eq!(verified(&mut other, &engine, &req).packets().len(), 1);
    assert_canon(&mut store, &engine);
}

#[test]
fn opaque_handle_and_prepared_step_cannot_cross_matching_store_instances() {
    let (_first_temp, mut first, first_engine) = fixture();
    let (_second_temp, mut second, second_engine) = fixture();
    assert_eq!(
        first_engine.canonical_bytes(),
        second_engine.canonical_bytes()
    );
    let first_info = first
        .ensure_memory_job(&request(&first_engine, "agent"), &|| false)
        .unwrap();
    let second_info = second
        .ensure_memory_job(&request(&second_engine, "agent"), &|| false)
        .unwrap();
    assert_eq!(
        first_info.handle.id(),
        second_info.handle.id(),
        "actual independent AUTOINCREMENT IDs deliberately collide"
    );
    assert_eq!(first_engine.scope(), second_engine.scope());
    assert!(matches!(
        second.memory_job_status(&first_info.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert!(matches!(
        second.prepare_memory_job_step(&first_info.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert!(matches!(
        second.cancel_memory_job(&first_info.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert!(matches!(
        second.prune_memory_job(&first_info.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    let prepared = first
        .prepare_memory_job_step(&first_info.handle, &|| false)
        .unwrap();
    assert!(matches!(
        second.publish_memory_job_step(prepared, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert_eq!(
        identity(
            &first
                .memory_job_status(&first_info.handle, &|| false)
                .unwrap()
        ),
        identity(&first_info)
    );
    assert_eq!(
        identity(
            &second
                .memory_job_status(&second_info.handle, &|| false)
                .unwrap()
        ),
        identity(&second_info)
    );
    let a = first
        .prepare_memory_job_step(&first_info.handle, &|| false)
        .unwrap();
    let b = second
        .prepare_memory_job_step(&second_info.handle, &|| false)
        .unwrap();
    first.publish_memory_job_step(a, &|| false).unwrap();
    second.publish_memory_job_step(b, &|| false).unwrap();
    assert_eq!(
        verified(&mut first, &first_engine, &request(&first_engine, "agent")).packets(),
        verified(
            &mut second,
            &second_engine,
            &request(&second_engine, "agent")
        )
        .packets()
    );
    assert_canon(&mut first, &first_engine);
    assert_canon(&mut second, &second_engine);
}

#[test]
fn engine_and_coverage_share_read_snapshot_while_another_owner_commits_and_retargets() {
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let info = store.ensure_memory_job(&req, &|| false).unwrap();
    drain(&mut store, &info.handle);
    let expected = packets(&engine, "agent");
    // Local synthetic WAL permits a writer to finish under the held reader;
    // this is a database fixture setting, not an OS/app configuration change.
    Connection::open(temp.path("source.sqlite"))
        .unwrap()
        .pragma_update(None, "journal_mode", "WAL")
        .unwrap();
    let mut other = temp.open();
    let mut newer = engine.clone();
    let (go_tx, go_rx) = mpsc::channel();
    let (done_tx, done_rx) = mpsc::channel();
    let worker = std::thread::spawn(move || {
        go_rx.recv_timeout(Duration::from_secs(10)).unwrap();
        apply(
            &mut other,
            &mut newer,
            "concurrent-newer-head",
            vec![say("Concurrent newer source.", "agent"); 4],
        );
        let retargeted = other
            .ensure_memory_job(&request(&newer, "agent"), &|| false)
            .unwrap();
        drain(&mut other, &retargeted.handle);
        done_tx.send(newer.revision()).unwrap();
    });
    let checks = Cell::new(0);
    let snapshot = store
        .context_snapshot(&req, &|| {
            checks.set(checks.get() + 1);
            // Frozen e98 context_snapshot: initial check, memory_engine entry, then
            // memory_engine's post-strict-replay check within the same read txn.
            if checks.get() == 3 {
                go_tx.send(()).unwrap();
                assert_eq!(
                    done_rx.recv_timeout(Duration::from_secs(10)).unwrap(),
                    EVENTS + 4
                );
            }
            false
        })
        .unwrap();
    worker.join().unwrap();
    assert!(checks.get() >= 3);
    assert_eq!(snapshot.engine.canonical_bytes(), engine.canonical_bytes());
    let CoverageRead::Verified(proof) = snapshot.coverage else {
        panic!("mixed snapshots lost the original complete proof");
    };
    assert_eq!(proof.verified_head(), EVENTS);
    assert_eq!(proof.covered_through(), EVENTS);
    assert_eq!(proof.packets(), expected);
    assert!(matches!(
        proof
            .recheck(&snapshot.engine, &core_request(&req), &|| false)
            .unwrap(),
        CoverageRead::Verified(_)
    ));
    assert_eq!(
        store.resume(engine.scope()).unwrap().engine.revision(),
        EVENTS + 4
    );
    assert!(matches!(
        store.context_snapshot(&req, &|| false),
        Err(MemoryError::Stale)
    ));
}

#[test]
fn persisted_cancel_blocks_old_prepared_work_and_ensure_never_resurrects() {
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let initial = store.ensure_memory_job(&req, &|| false).unwrap();
    let prepared = store
        .prepare_memory_job_step(&initial.handle, &|| false)
        .unwrap();
    let mut other = temp.open();
    let other_info = other.ensure_memory_job(&req, &|| false).unwrap();
    let cancelled = other
        .cancel_memory_job(&other_info.handle, &|| false)
        .unwrap();
    assert!(matches!(cancelled.status, MemoryJobStatus::Cancelled));
    assert!(cancelled.generation > initial.generation);
    assert_eq!(cancelled.next_from, 0);
    assert!(matches!(
        store.publish_memory_job_step(prepared, &|| false),
        Err(MemoryError::Stale)
    ));
    assert!(matches!(
        store.prepare_memory_job_step(&initial.handle, &|| false),
        Err(MemoryError::Cancelled)
    ));
    let expected = identity(&cancelled);
    drop(other);
    drop(store);
    let mut store = temp.open();
    assert!(matches!(
        store.memory_job_status(&initial.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    let reopened = store.ensure_memory_job(&req, &|| false).unwrap();
    assert_eq!(identity(&reopened), expected);
    assert_eq!(
        identity(
            &store
                .memory_job_status(&reopened.handle, &|| false)
                .unwrap()
        ),
        expected
    );
    assert_eq!(
        identity(&store.ensure_memory_job(&req, &|| false).unwrap()),
        expected
    );
    assert_canon(&mut store, &engine);
}

#[test]
fn explicit_terminal_prune_releases_identity_without_reusing_job_id() {
    let (_temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let old = store.ensure_memory_job(&req, &|| false).unwrap();
    assert!(matches!(
        store.prune_memory_job(&old.handle, &|| false),
        Err(MemoryError::Busy)
    ));
    store.cancel_memory_job(&old.handle, &|| false).unwrap();
    store.prune_memory_job(&old.handle, &|| false).unwrap();
    assert!(matches!(
        store.memory_job_status(&old.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    let new = store.ensure_memory_job(&req, &|| false).unwrap();
    assert!(new.handle.id() > old.handle.id());
    assert_eq!(new.next_from, 0);
    assert!(matches!(new.status, MemoryJobStatus::Ready));
    assert_canon(&mut store, &engine);
}

#[test]
fn head_advance_invalidates_prepared_work_and_retargets_same_job() {
    let (_temp, mut store, mut engine) = fixture();
    let old_req = request(&engine, "agent");
    let old = store.ensure_memory_job(&old_req, &|| false).unwrap();
    let prepared = store
        .prepare_memory_job_step(&old.handle, &|| false)
        .unwrap();
    apply(
        &mut store,
        &mut engine,
        "new-head",
        vec![say("New-head delta.", "agent"); 4],
    );
    assert!(matches!(
        store.publish_memory_job_step(prepared, &|| false),
        Err(MemoryError::Stale)
    ));
    let unchanged = store.memory_job_status(&old.handle, &|| false).unwrap();
    assert_eq!(unchanged.next_from, 0);
    assert!(matches!(
        store.context_snapshot(&old_req, &|| false),
        Err(MemoryError::Stale)
    ));
    let new = store
        .ensure_memory_job(&request(&engine, "agent"), &|| false)
        .unwrap();
    assert_eq!(new.handle.id(), old.handle.id());
    assert_eq!(new.basis_revision, EVENTS + 4);
    assert!(new.generation > old.generation);
    assert_eq!(new.next_from, 0);
    drain(&mut store, &new.handle);
    assert_eq!(
        verified(&mut store, &engine, &request(&engine, "agent")).packets(),
        packets(&engine, "agent")
    );
    assert_canon(&mut store, &engine);
}

#[test]
fn advancing_head_keeps_verified_sealed_prefix_and_rebuilds_open_tail() {
    let (_temp, mut store, mut engine) = fixture();
    let old_req = request(&engine, "agent");
    let old = store.ensure_memory_job(&old_req, &|| false).unwrap();
    let complete = drain(&mut store, &old.handle);
    let old_packets = packets(&engine, "agent");
    assert!(matches!(
        old_packets.last().unwrap().closure,
        Closure::OpenTail
    ));
    let sealed = &old_packets[..old_packets.len() - 1];
    assert!(!sealed.is_empty());
    let sealed_through = sealed.last().unwrap().through_revision;
    apply(
        &mut store,
        &mut engine,
        "open-tail-delta",
        vec![say("Later exact raw tail.", "agent"); 4],
    );
    let req = request(&engine, "agent");
    let retargeted = store.ensure_memory_job(&req, &|| false).unwrap();
    assert_eq!(retargeted.handle.id(), complete.handle.id());
    assert!(retargeted.generation > complete.generation);
    assert_eq!(retargeted.next_from, sealed_through);
    assert!(matches!(retargeted.status, MemoryJobStatus::Ready));
    let prefix = verified(&mut store, &engine, &req);
    assert_eq!(prefix.packets(), sealed);
    assert_eq!(prefix.raw_delta_after(), sealed_through);
    drain(&mut store, &retargeted.handle);
    assert_eq!(
        verified(&mut store, &engine, &req).packets(),
        packets(&engine, "agent")
    );
    assert_canon(&mut store, &engine);
}

#[test]
fn invalid_scope_actor_stale_head_and_precancel_refuse_without_maintenance() {
    let (_temp, mut store, engine) = fixture();
    let good = request(&engine, "agent");
    assert!(matches!(
        store.context_snapshot(&good, &|| false).unwrap().coverage,
        CoverageRead::RawFallback(_)
    ));
    assert!(matches!(
        store.ensure_memory_job(&good, &|| true),
        Err(MemoryError::Cancelled)
    ));
    let wrong = MemoryJobRequest {
        scope: Scope {
            story: "missing-story".into(),
            branch: "main".into(),
        },
        ..request(&engine, "agent")
    };
    assert!(matches!(
        store.ensure_memory_job(&wrong, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert!(matches!(
        store.ensure_memory_job(&request(&engine, "missing-actor"), &|| false),
        Err(MemoryError::NotFound)
    ));
    let stale = MemoryJobRequest {
        expected_head: EVENTS - 4,
        ..request(&engine, "agent")
    };
    assert!(matches!(
        store.ensure_memory_job(&stale, &|| false),
        Err(MemoryError::Stale)
    ));
    assert!(matches!(
        store.context_snapshot(&stale, &|| false),
        Err(MemoryError::Stale)
    ));
    assert_canon(&mut store, &engine);
}

#[test]
fn writer_busy_cannot_advance_cursor_and_prepare_needs_no_writer() {
    let (temp, mut store, engine) = fixture();
    let info = store
        .ensure_memory_job(&request(&engine, "agent"), &|| false)
        .unwrap();
    let locker = Connection::open(temp.path("source.sqlite")).unwrap();
    locker.execute_batch("BEGIN IMMEDIATE").unwrap();
    let prepared = store
        .prepare_memory_job_step(&info.handle, &|| false)
        .unwrap();
    let result = store.publish_memory_job_step(prepared, &|| false);
    locker.execute_batch("ROLLBACK").unwrap();
    assert!(matches!(result, Err(MemoryError::Busy)));
    assert_eq!(
        identity(&store.memory_job_status(&info.handle, &|| false).unwrap()),
        identity(&info)
    );
    let step = store
        .prepare_memory_job_step(&info.handle, &|| false)
        .unwrap();
    assert!(
        store
            .publish_memory_job_step(step, &|| false)
            .unwrap()
            .next_from
            > 0
    );
    assert_canon(&mut store, &engine);
}

#[test]
fn actor_partition_with_no_eligible_events_advances_completed_cursor_without_secrets() {
    let (_temp, mut store, engine) = fixture();
    let actor = request(&engine, "agent");
    let player = request(&engine, "player");
    let silent = request(&engine, "silent");
    let a = store.ensure_memory_job(&actor, &|| false).unwrap();
    let p = store.ensure_memory_job(&player, &|| false).unwrap();
    let s = store.ensure_memory_job(&silent, &|| false).unwrap();
    assert_ne!(a.handle.id(), p.handle.id());
    assert_ne!(a.handle.id(), s.handle.id());
    for handle in [&a.handle, &p.handle, &s.handle] {
        assert_eq!(drain(&mut store, handle).next_from, EVENTS);
    }
    let a = verified(&mut store, &engine, &actor);
    let p = verified(&mut store, &engine, &player);
    let s = verified(&mut store, &engine, &silent);
    assert!(!serde_json::to_string(a.packets())
        .unwrap()
        .contains(PRIVATE));
    assert!(serde_json::to_string(p.packets())
        .unwrap()
        .contains(PRIVATE));
    assert!(s
        .packets()
        .iter()
        .all(|packet| packet.source_events.is_empty() && packet.entries.is_empty()));
    assert_eq!(s.covered_through(), EVENTS);
    assert_canon(&mut store, &engine);
}

#[test]
fn branches_do_not_copy_jobs_or_packets_and_original_scopes_remain_isolated() {
    let (_temp, mut store, mut root) = fixture();
    let original = store
        .ensure_memory_job(&request(&root, "agent"), &|| false)
        .unwrap();
    drain(&mut store, &original.handle);
    let child = store
        .fork_branch(
            &ForkRequest {
                parent: root.scope().clone(),
                child_branch: "child".into(),
                expected_parent_revision: EVENTS,
                at_revision: EVENTS,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    let sibling = store
        .fork_branch(
            &ForkRequest {
                parent: root.scope().clone(),
                child_branch: "sibling".into(),
                expected_parent_revision: EVENTS,
                at_revision: EVENTS,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    let mut child_engine = store.resume(&child).unwrap().engine;
    assert!(matches!(
        store
            .context_snapshot(&request(&child_engine, "agent"), &|| false)
            .unwrap()
            .coverage,
        CoverageRead::RawFallback(_)
    ));
    let mut sibling_engine = store.resume(&sibling).unwrap().engine;
    apply(
        &mut store,
        &mut root,
        "future-parent",
        vec![say("JOB-PARENT-FUTURE", "agent"); 4],
    );
    apply(
        &mut store,
        &mut child_engine,
        "child-local",
        vec![say("JOB-CHILD-LOCAL", "agent"); 4],
    );
    apply(
        &mut store,
        &mut sibling_engine,
        "sibling-local",
        vec![say("JOB-SIBLING-ONLY", "agent"); 4],
    );
    assert_eq!(root.revision(), child_engine.revision());
    assert_eq!(sibling_engine.revision(), child_engine.revision());
    let req = request(&child_engine, "agent");
    let child_job = store.ensure_memory_job(&req, &|| false).unwrap();
    assert_ne!(child_job.handle.id(), original.handle.id());
    assert_eq!(child_job.next_from, 0);
    drain(&mut store, &child_job.handle);
    let proof = verified(&mut store, &child_engine, &req);
    let text = serde_json::to_string(proof.packets()).unwrap();
    assert!(text.contains("JOB-CHILD-LOCAL"));
    assert!(
        !text.contains("JOB-PARENT-FUTURE")
            && !text.contains("JOB-SIBLING-ONLY")
            && !text.contains(PRIVATE)
    );
    assert!(proof
        .packets()
        .iter()
        .flat_map(|p| &p.source_events)
        .filter(|s| s.sequence <= EVENTS)
        .all(|s| &s.scope == root.scope()));
    assert_canon(&mut store, &root);
    assert_canon(&mut store, &child_engine);
    assert_canon(&mut store, &sibling_engine);
}

#[test]
fn retired_parent_loses_its_job_without_breaking_live_child_or_reusing_ids() {
    let (_temp, mut store, root) = fixture();
    let old = store
        .ensure_memory_job(&request(&root, "agent"), &|| false)
        .unwrap();
    drain(&mut store, &old.handle);
    let child = store
        .fork_branch(
            &ForkRequest {
                parent: root.scope().clone(),
                child_branch: "retained-child".into(),
                expected_parent_revision: EVENTS,
                at_revision: EVENTS,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    let child_engine = store.resume(&child).unwrap().engine;
    let child_job = store
        .ensure_memory_job(&request(&child_engine, "agent"), &|| false)
        .unwrap();
    drain(&mut store, &child_job.handle);
    let prepared = store
        .prepare_branch_deletion(root.scope(), EVENTS, &|| false)
        .unwrap();
    store.delete_branch(prepared, &|| false).unwrap();
    assert!(matches!(
        store.memory_job_status(&old.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert!(matches!(
        store.ensure_memory_job(&request(&root, "agent"), &|| false),
        Err(MemoryError::NotFound)
    ));
    assert_eq!(
        store
            .memory_job_status(&child_job.handle, &|| false)
            .unwrap()
            .next_from,
        EVENTS
    );
    verified(&mut store, &child_engine, &request(&child_engine, "agent"));
    assert_canon(&mut store, &child_engine);
}

#[test]
fn playable_archive_excludes_jobs_and_cache_and_import_starts_without_proof() {
    let (temp, mut store, engine) = fixture();
    let before = store
        .export_archive(&engine.scope().story, &|| false)
        .unwrap()
        .bytes()
        .to_vec();
    let job = store
        .ensure_memory_job(&request(&engine, "agent"), &|| false)
        .unwrap();
    drain(&mut store, &job.handle);
    let after = store
        .export_archive(&engine.scope().story, &|| false)
        .unwrap();
    assert_eq!(after.bytes(), before);
    let text = std::str::from_utf8(after.bytes()).unwrap();
    assert!(!text.contains("memory_jobs") && !text.contains(memory_coverage::METHOD));
    let mut target = Store::open_application(&temp.path("imported.sqlite")).unwrap();
    target
        .import_archive(validate_archive(after.bytes(), &|| false).unwrap(), &|| {
            false
        })
        .unwrap();
    assert_canon(&mut target, &engine);
    assert!(matches!(
        target
            .context_snapshot(&request(&engine, "agent"), &|| false)
            .unwrap()
            .coverage,
        CoverageRead::RawFallback(_)
    ));
    let fresh = target
        .ensure_memory_job(&request(&engine, "agent"), &|| false)
        .unwrap();
    assert_eq!(fresh.next_from, 0);
}

#[test]
fn aborted_prepare_publish_and_cancel_call_leave_ready_checkpoint_unchanged() {
    let (_temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let initial = store.ensure_memory_job(&req, &|| false).unwrap();
    assert!(matches!(
        store.prepare_memory_job_step(&initial.handle, &|| true),
        Err(MemoryError::Cancelled)
    ));
    let prepared = store
        .prepare_memory_job_step(&initial.handle, &|| false)
        .unwrap();
    assert!(matches!(
        store.publish_memory_job_step(prepared, &|| true),
        Err(MemoryError::Cancelled)
    ));
    assert!(matches!(
        store.cancel_memory_job(&initial.handle, &|| true),
        Err(MemoryError::Cancelled)
    ));
    assert_eq!(
        identity(&store.memory_job_status(&initial.handle, &|| false).unwrap()),
        identity(&initial)
    );
    assert!(matches!(
        store.context_snapshot(&req, &|| false).unwrap().coverage,
        CoverageRead::RawFallback(_)
    ));
    assert_canon(&mut store, &engine);
}

#[test]
fn story_deletion_cascades_job_and_a_new_story_gets_a_higher_job_id() {
    let (_temp, mut store, engine) = fixture();
    let old = store
        .ensure_memory_job(&request(&engine, "agent"), &|| false)
        .unwrap();
    drain(&mut store, &old.handle);
    let prepared = store
        .prepare_story_deletion(engine.scope(), EVENTS, &|| false)
        .unwrap();
    store.delete_story(prepared, &|| false).unwrap();
    assert!(matches!(
        store.memory_job_status(&old.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert!(matches!(
        store.ensure_memory_job(&request(&engine, "agent"), &|| false),
        Err(MemoryError::NotFound)
    ));
    let fresh_seed = seed("after-deletion");
    let fresh = Engine::new(fresh_seed.clone()).unwrap();
    store
        .create_story("New original story", fresh_seed)
        .unwrap();
    let new = store
        .ensure_memory_job(&request(&fresh, "agent"), &|| false)
        .unwrap();
    assert!(new.handle.id() > old.handle.id());
    assert_canon(&mut store, &fresh);
}

#[test]
fn store_quota_counts_retained_terminal_jobs_and_pruning_releases_one_slot() {
    let temp = Temp::new();
    let mut store = temp.open();
    let mut handles = vec![];
    let mut refused = None;
    for index in 0..86 {
        let fresh_seed = seed(&format!("quota-{index:03}"));
        let engine = Engine::new(fresh_seed.clone()).unwrap();
        store
            .create_story("Original quota fixture", fresh_seed)
            .unwrap();
        for actor in ["player", "agent", "silent"] {
            let req = request(&engine, actor);
            if handles.len() == 256 {
                refused = Some(req);
                break;
            }
            let info = store.ensure_memory_job(&req, &|| false).unwrap();
            // Retain the terminal row. No SQL insertion bypasses public admission.
            store.cancel_memory_job(&info.handle, &|| false).unwrap();
            handles.push(info.handle);
        }
        if refused.is_some() {
            break;
        }
    }
    assert_eq!(handles.len(), 256);
    let req = refused.expect("257th distinct observer partition must be available");
    assert!(matches!(
        store.ensure_memory_job(&req, &|| false),
        Err(MemoryError::TooLarge)
    ));
    let highest = handles.iter().map(MemoryJobHandle::id).max().unwrap();
    store.prune_memory_job(&handles[0], &|| false).unwrap();
    let new = store.ensure_memory_job(&req, &|| false).unwrap();
    assert!(new.handle.id() > highest);
    assert!(matches!(
        store.memory_job_status(&handles[0], &|| false),
        Err(MemoryError::NotFound)
    ));
}

#[test]
fn untrusted_packet_schema_actor_and_resealed_sources_never_become_verified() {
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let info = store.ensure_memory_job(&req, &|| false).unwrap();
    let mut old = drain(&mut store, &info.handle);
    let expected = packets(&engine, "agent");
    let mut schema: Value = serde_json::from_slice(&expected[0].bytes().unwrap()).unwrap();
    schema["version"] = json!(1);
    let mut source: Value = serde_json::from_slice(&expected[0].bytes().unwrap()).unwrap();
    source["source_events"][0]["sequence"] = json!(EVENTS);
    source["source_sha256"] = json!("0".repeat(64));
    let mut extra: Value = serde_json::from_slice(&expected[0].bytes().unwrap()).unwrap();
    extra["unexpected"] = json!(true);
    let player: Value =
        serde_json::from_slice(&packets(&engine, "player")[0].bytes().unwrap()).unwrap();
    let mut foreign: Value = serde_json::from_slice(&expected[0].bytes().unwrap()).unwrap();
    foreign["scope"]["story"] = json!("foreign-job-review");
    let variants = [
        ("missing-schema", json!({})),
        ("old-schema", schema),
        ("source-forgery", source),
        ("unknown-field", extra),
        ("player-packet", player),
        ("foreign-scope", foreign),
    ];
    let db = Connection::open(temp.path("source.sqlite")).unwrap();
    for (case, packet) in variants {
        assert_eq!(
            db.execute(
                "UPDATE memory_job_packets SET packet_json=?1 WHERE job_id=?2 AND from_revision=0",
                params![packet.to_string(), sql_integer(info.handle.id())]
            )
            .unwrap(),
            1,
            "{case}"
        );
        let before = job_row(&db, &info.handle);
        let bytes = cache_rows(&db, &info.handle);
        let snapshot = store.context_snapshot(&req, &|| false).unwrap();
        assert!(
            matches!(snapshot.coverage, CoverageRead::RawFallback(_)),
            "{case}"
        );
        assert_eq!(
            snapshot.engine.canonical_bytes(),
            engine.canonical_bytes(),
            "{case}"
        );
        assert_eq!(
            job_row(&db, &info.handle),
            before,
            "context view wrote job metadata: {case}"
        );
        assert_eq!(
            cache_rows(&db, &info.handle),
            bytes,
            "context view rewrote cache: {case}"
        );
        let reset = store.ensure_memory_job(&req, &|| false).unwrap();
        assert_eq!(reset.handle.id(), info.handle.id());
        assert_eq!(reset.next_from, 0, "{case}");
        assert!(reset.generation > old.generation, "{case}");
        old = drain(&mut store, &info.handle);
        assert_eq!(verified(&mut store, &engine, &req).packets(), expected);
        assert_canon(&mut store, &engine);
    }
}

#[test]
fn missing_prefix_resets_and_untrusted_job_binding_never_changes_canon() {
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let info = store.ensure_memory_job(&req, &|| false).unwrap();
    drain(&mut store, &info.handle);
    let expected = packets(&engine, "agent");
    let db = Connection::open(temp.path("source.sqlite")).unwrap();
    let metadata: Value = serde_json::from_str(&job_row(&db, &info.handle)).unwrap();
    for field in ["seed", "lineage", "source"] {
        let digest = metadata[field].as_str().unwrap();
        assert_eq!(digest.len(), 64);
        assert!(digest.bytes().all(|byte| byte.is_ascii_hexdigit()));
    }
    assert_eq!(
        db.execute(
            "DELETE FROM memory_job_packets WHERE job_id=?1 AND from_revision=0",
            [sql_integer(info.handle.id())]
        )
        .unwrap(),
        1
    );
    assert!(matches!(
        store.context_snapshot(&req, &|| false).unwrap().coverage,
        CoverageRead::RawFallback(_)
    ));
    let reset = store.ensure_memory_job(&req, &|| false).unwrap();
    assert_eq!(reset.next_from, 0);
    drain(&mut store, &info.handle);
    db.execute(
        "UPDATE memory_jobs SET source_sha256=?1 WHERE job_id=?2",
        params!["0".repeat(64), sql_integer(info.handle.id())],
    )
    .unwrap();
    // Job metadata is not canonical authority. Valid packets may still verify
    // only by rebuilding against this exact Engine, never by trusting this row.
    let snapshot = store.context_snapshot(&req, &|| false).unwrap();
    assert_eq!(snapshot.engine.canonical_bytes(), engine.canonical_bytes());
    if let CoverageRead::Verified(proof) = snapshot.coverage {
        assert!(matches!(
            proof
                .recheck(&snapshot.engine, &core_request(&req), &|| false)
                .unwrap(),
            CoverageRead::Verified(_)
        ));
        assert_eq!(proof.packets(), expected);
    }
    let rebound = store.ensure_memory_job(&req, &|| false).unwrap();
    assert_eq!(rebound.handle.id(), info.handle.id());
    drain(&mut store, &info.handle);
    let rebuilt: Value = serde_json::from_str(&job_row(&db, &info.handle)).unwrap();
    assert_eq!(rebuilt["source"], metadata["source"]);
    assert_eq!(verified(&mut store, &engine, &req).packets(), expected);
    assert_canon(&mut store, &engine);
}

#[test]
fn actual_derived_trigger_failures_roll_back_packet_and_cursor_together() {
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let info = store.ensure_memory_job(&req, &|| false).unwrap();
    let db = Connection::open(temp.path("source.sqlite")).unwrap();
    for trigger in [
        "CREATE TRIGGER job_review_abort AFTER INSERT ON memory_job_packets BEGIN SELECT RAISE(ABORT,'synthetic packet rollback'); END;",
        "CREATE TRIGGER job_review_abort BEFORE UPDATE OF next_from ON memory_jobs WHEN NEW.next_from>OLD.next_from BEGIN SELECT RAISE(ABORT,'synthetic cursor rollback'); END;",
    ] {
        let before_job = job_row(&db, &info.handle);
        let before_packets = cache_rows(&db, &info.handle);
        let step = store.prepare_memory_job_step(&info.handle, &|| false).unwrap();
        db.execute_batch(trigger).unwrap();
        let result = store.publish_memory_job_step(step, &|| false);
        db.execute_batch("DROP TRIGGER job_review_abort").unwrap();
        assert!(matches!(result, Err(MemoryError::Database)));
        assert_eq!(job_row(&db, &info.handle), before_job);
        assert_eq!(cache_rows(&db, &info.handle), before_packets);
        assert_canon(&mut store, &engine);
        let step = store.prepare_memory_job_step(&info.handle, &|| false).unwrap();
        store.publish_memory_job_step(step, &|| false).unwrap();
    }
    drain(&mut store, &info.handle);
    assert_eq!(
        verified(&mut store, &engine, &req).packets(),
        packets(&engine, "agent")
    );
}

#[test]
fn legacy_v1_invalidation_does_not_erase_or_relabel_v2_jobs() {
    use locallore_storage::derived_memory::{EntityKind, PrepareRequest, Target};
    let (temp, mut store, engine) = fixture();
    let req = request(&engine, "agent");
    let info = store.ensure_memory_job(&req, &|| false).unwrap();
    let complete = drain(&mut store, &info.handle);
    let legacy = PrepareRequest {
        scope: engine.scope().clone(),
        observer: "agent".into(),
        expected_revision: EVENTS,
        from_exclusive: 0,
        through_revision: EVENTS,
        target: Target::Entity {
            kind: EntityKind::Commitment,
            id: "old-promise".into(),
        },
    };
    let prepared = store.prepare_memory(&legacy, &|| false).unwrap();
    store.publish_memory(prepared, &|| false).unwrap();
    let db = Connection::open(temp.path("source.sqlite")).unwrap();
    let before = cache_rows(&db, &info.handle);
    store
        .invalidate_memory(engine.scope(), "agent", EVENTS, &|| false)
        .unwrap();
    assert_eq!(
        identity(&store.memory_job_status(&info.handle, &|| false).unwrap()),
        identity(&complete)
    );
    assert_eq!(cache_rows(&db, &info.handle), before);
    assert_eq!(
        verified(&mut store, &engine, &req).packets(),
        packets(&engine, "agent")
    );
    assert_canon(&mut store, &engine);
}

#[test]
fn derived_blocked_state_refuses_prepare_and_can_only_be_explicitly_pruned() {
    let (temp, mut store, engine) = fixture();
    let info = store
        .ensure_memory_job(&request(&engine, "agent"), &|| false)
        .unwrap();
    // Adversarial DERIVED metadata, not proof that valid corpus384 exhausts a budget.
    let db = Connection::open(temp.path("source.sqlite")).unwrap();
    db.execute(
        "UPDATE memory_jobs SET status='blocked',last_error='budget' WHERE job_id=?1",
        [sql_integer(info.handle.id())],
    )
    .unwrap();
    let blocked = store.memory_job_status(&info.handle, &|| false).unwrap();
    assert!(matches!(blocked.status, MemoryJobStatus::Blocked));
    assert!(matches!(blocked.last_error, Some(MemoryJobFailure::Budget)));
    assert!(matches!(
        store.prepare_memory_job_step(&info.handle, &|| false),
        Err(MemoryError::InvalidInput)
    ));
    assert_canon(&mut store, &engine);
    store.prune_memory_job(&info.handle, &|| false).unwrap();
    assert!(matches!(
        store.memory_job_status(&info.handle, &|| false),
        Err(MemoryError::NotFound)
    ));
}

#[test]
fn own_process_death_before_and_after_checkpoint_recovers_exact_progress() {
    for stage in ["before", "after"] {
        let (temp, mut store, engine) = fixture();
        let req = request(&engine, "agent");
        let info = store.ensure_memory_job(&req, &|| false).unwrap();
        let expected_first = packets(&engine, "agent")[0].through_revision;
        drop(store);
        let marker = temp.path("child-ready.json");
        let output = std::fs::File::create(temp.path("child-output.log")).unwrap();
        let errors = output.try_clone().unwrap();
        let mut child = ProcessCommand::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "memory_job_checkpoint_child_process",
                "--ignored",
                "--nocapture",
            ])
            .env("LOCALLORE_JOB_REVIEW_CHILD", stage)
            .env("LOCALLORE_JOB_REVIEW_DATABASE", temp.path("source.sqlite"))
            .env("LOCALLORE_JOB_REVIEW_MARKER", &marker)
            .stdout(output)
            .stderr(errors)
            .spawn()
            .unwrap();
        let until = Instant::now() + Duration::from_secs(20);
        while !marker.exists() {
            if let Some(status) = child.try_wait().unwrap() {
                panic!(
                    "owned checkpoint child exited before its barrier: {status}; {}",
                    std::fs::read_to_string(temp.path("child-output.log")).unwrap()
                );
            }
            if Instant::now() >= until {
                child.kill().unwrap();
                child.wait().unwrap();
                panic!("owned checkpoint child failed to reach its bounded barrier");
            }
            std::thread::sleep(Duration::from_millis(10));
        }
        let marker_value: Value = serde_json::from_slice(&std::fs::read(&marker).unwrap()).unwrap();
        // Kill only this returned child process, never a process found by name or PID inventory.
        child.kill().unwrap();
        assert!(!child.wait().unwrap().success());
        let mut store = temp.open();
        assert!(matches!(
            store.memory_job_status(&info.handle, &|| false),
            Err(MemoryError::NotFound)
        ));
        let renewed = store.ensure_memory_job(&req, &|| false).unwrap();
        let actual = store.memory_job_status(&renewed.handle, &|| false).unwrap();
        let expected_cursor = if stage == "before" { 0 } else { expected_first };
        assert_eq!(actual.handle.id(), info.handle.id());
        assert_eq!(actual.next_from, expected_cursor);
        assert_eq!(marker_value["job_id"], info.handle.id());
        assert_eq!(marker_value["next_from"], expected_cursor);
        if stage == "before" {
            assert!(matches!(
                store.context_snapshot(&req, &|| false).unwrap().coverage,
                CoverageRead::RawFallback(_)
            ));
        } else {
            assert_eq!(
                verified(&mut store, &engine, &req).covered_through(),
                expected_cursor
            );
        }
        assert_canon(&mut store, &engine);
        drain(&mut store, &renewed.handle);
        assert_eq!(
            verified(&mut store, &engine, &req).packets(),
            packets(&engine, "agent")
        );
    }
}

#[test]
#[ignore = "only spawned by the fixed own-process checkpoint integration test"]
fn memory_job_checkpoint_child_process() {
    let stage = std::env::var("LOCALLORE_JOB_REVIEW_CHILD").expect("owned child mode");
    assert!(matches!(stage.as_str(), "before" | "after"));
    let path = PathBuf::from(std::env::var_os("LOCALLORE_JOB_REVIEW_DATABASE").unwrap());
    let marker = PathBuf::from(std::env::var_os("LOCALLORE_JOB_REVIEW_MARKER").unwrap());
    assert_eq!(path.parent(), marker.parent());
    assert!(path
        .parent()
        .unwrap()
        .file_name()
        .unwrap()
        .to_string_lossy()
        .starts_with("locallore-jobs-review-"));
    assert_eq!(path.file_name().unwrap(), "source.sqlite");
    assert_eq!(marker.file_name().unwrap(), "child-ready.json");
    let mut store = Store::open_application(&path).unwrap();
    let engine = store
        .resume(&Scope {
            story: "job-review".into(),
            branch: "main".into(),
        })
        .unwrap()
        .engine;
    assert_eq!(engine.revision(), EVENTS);
    let info = store
        .ensure_memory_job(&request(&engine, "agent"), &|| false)
        .unwrap();
    let prepared = store
        .prepare_memory_job_step(&info.handle, &|| false)
        .unwrap();
    let paused = if stage == "after" {
        store.publish_memory_job_step(prepared, &|| false).unwrap()
    } else {
        // Keep the actual prepared token alive until this process is terminated.
        let _keep_prepared = prepared;
        let temporary = marker.with_extension("pending");
        std::fs::write(
            &temporary,
            serde_json::to_vec(&json!({"job_id":info.handle.id(),"next_from":info.next_from}))
                .unwrap(),
        )
        .unwrap();
        std::fs::rename(temporary, &marker).unwrap();
        std::thread::sleep(Duration::from_secs(30));
        panic!("parent failed to terminate the owned pre-publication child");
    };
    let temporary = marker.with_extension("pending");
    std::fs::write(
        &temporary,
        serde_json::to_vec(&json!({"job_id":paused.handle.id(),"next_from":paused.next_from}))
            .unwrap(),
    )
    .unwrap();
    std::fs::rename(temporary, &marker).unwrap();
    std::thread::sleep(Duration::from_secs(30));
    panic!("parent failed to terminate the owned committed-checkpoint child");
}
