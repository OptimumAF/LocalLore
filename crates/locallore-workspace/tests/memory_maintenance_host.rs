// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual native Host/Repository/Store operations. No inference or UI execution.
use locallore::{
    contracts::*,
    engine::Engine,
    host::memory_maintenance::{
        MaintenanceAction as Action, MaintenanceError as Error, MaintenanceReply,
        MaintenanceStatus as Status,
    },
    host::Host,
    memory_coverage::CoverageRead,
};
use locallore_storage::{memory_jobs::MemoryJobRequest, playable_archive::validate_archive, Store};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-maintenance-host-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
    fn host(&self, lab: bool) -> Host {
        locallore_workspace::open(&self.path(), lab).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn fixture(turns: usize, prefix: &str) -> (Temp, Engine) {
    let temp = Temp::new();
    let mut store = temp.store();
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let scope = seed.scope.clone();
    store.create_story("Synthetic maintenance", seed).unwrap();
    let mut engine = store.resume(&scope).unwrap().engine;
    for index in 0..turns {
        let request = engine.request(
            &format!("{prefix}-{index}"),
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let preview = engine.preview(&request, &proposal).unwrap();
        store.begin_turn(&request).unwrap();
        let receipt = store
            .commit_turn(&request, &proposal, preview.narration())
            .unwrap();
        engine.commit_prepared(&receipt).unwrap();
    }
    (temp, engine)
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn select(host: &Host, engine: &Engine) -> String {
    let reply = call(host, json!({"op":"resume","scope":engine.scope()}));
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["session"].as_str().unwrap().into()
}
fn run(host: &Host, session: &str, engine: &Engine, action: Action) -> MaintenanceReply {
    host.memory_maintenance(session, engine.scope(), engine.revision(), action, &|| {
        false
    })
    .unwrap()
}
fn request(engine: &Engine) -> MemoryJobRequest {
    MemoryJobRequest {
        scope: engine.scope().clone(),
        observer: engine.seed().player.clone(),
        expected_head: engine.revision(),
    }
}
fn assert_canon(temp: &Temp, engine: &Engine) {
    let actual = temp.store().resume(engine.scope()).unwrap().engine;
    assert_eq!(actual.canonical_bytes(), engine.canonical_bytes());
    assert_eq!(actual.receipts(), engine.receipts());
}
#[test]
fn passive_status_never_admits_and_reopen_does_not_resume_work() {
    let (temp, engine) = fixture(1, "passive");
    let host = temp.host(false);
    let session = select(&host, &engine);
    let before = std::fs::read(temp.path()).unwrap();
    for _ in 0..3 {
        assert_eq!(run(&host, &session, &engine, Action::Status).job, None);
    }
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    let admitted = run(&host, &session, &engine, Action::Admit).job.unwrap();
    assert_eq!(admitted.status, Status::Ready);
    assert_eq!(admitted.next_from, 0);
    drop(host);
    let host = temp.host(true);
    let session = select(&host, &engine);
    let before = std::fs::read(temp.path()).unwrap();
    assert_eq!(
        run(&host, &session, &engine, Action::Status).job.unwrap(),
        admitted
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    assert_canon(&temp, &engine);
}
#[test]
fn each_step_publishes_at_most_one_actual_core_chunk_then_reopen_preserves_it() {
    //129 complete receipts exceed Core's128-receipt chunk cap, independently
    // of whichever byte/event cap seals the first chunk earlier.
    let (temp, engine) = fixture(129, "chunk");
    let host = temp.host(false);
    let session = select(&host, &engine);
    let admitted = run(&host, &session, &engine, Action::Admit).job.unwrap();
    let first = run(&host, &session, &engine, Action::Step).job.unwrap();
    assert_eq!(first.generation, admitted.generation + 1);
    assert!(first.next_from > 0 && first.next_from < engine.revision());
    assert_eq!(first.status, Status::Ready);
    match temp
        .store()
        .context_snapshot(&request(&engine), &|| false)
        .unwrap()
        .coverage
    {
        CoverageRead::Verified(proof) => {
            assert_eq!(proof.packets().len(), 1);
            assert_eq!(proof.covered_through(), first.next_from);
        }
        _ => panic!("actual first published chunk must verify"),
    }
    drop(host);
    let host = temp.host(false);
    let session = select(&host, &engine);
    assert_eq!(
        run(&host, &session, &engine, Action::Status).job.unwrap(),
        first
    );
    let mut current = first;
    for _ in 0..32 {
        if current.status != Status::Ready {
            break;
        }
        let next = run(&host, &session, &engine, Action::Step).job.unwrap();
        assert_eq!(next.generation, current.generation + 1);
        assert!(next.next_from > current.next_from);
        current = next;
    }
    assert_eq!(current.status, Status::Complete);
    assert_eq!(current.next_from, engine.revision());
    assert_eq!(
        run(&host, &session, &engine, Action::Step).job.unwrap(),
        current
    );
    assert_eq!(
        run(&host, &session, &engine, Action::Cancel).job.unwrap(),
        current,
        "late cancellation must not pretend publication rolled back"
    );
    assert_canon(&temp, &engine);
}
#[test]
fn explicit_cancel_is_terminal_until_explicit_prune_and_readmission() {
    let (temp, engine) = fixture(2, "terminal");
    let host = temp.host(false);
    let session = select(&host, &engine);
    run(&host, &session, &engine, Action::Admit);
    assert_eq!(
        host.memory_maintenance(
            &session,
            engine.scope(),
            engine.revision(),
            Action::Prune,
            &|| false
        ),
        Err(Error::Busy)
    );
    let cancelled = run(&host, &session, &engine, Action::Cancel).job.unwrap();
    assert_eq!(cancelled.status, Status::Cancelled);
    assert_eq!(
        run(&host, &session, &engine, Action::Admit).job.unwrap(),
        cancelled
    );
    assert_eq!(
        host.memory_maintenance(
            &session,
            engine.scope(),
            engine.revision(),
            Action::Step,
            &|| false
        ),
        Err(Error::Cancelled)
    );
    drop(host);
    let host = temp.host(false);
    let session = select(&host, &engine);
    assert_eq!(
        run(&host, &session, &engine, Action::Status).job.unwrap(),
        cancelled
    );
    assert_eq!(run(&host, &session, &engine, Action::Prune).job, None);
    assert_eq!(run(&host, &session, &engine, Action::Prune).job, None);
    let new = run(&host, &session, &engine, Action::Admit).job.unwrap();
    assert_eq!(new.status, Status::Ready);
    assert_eq!(new.next_from, 0);
    assert_canon(&temp, &engine);
}
#[test]
fn operation_cancellation_and_panic_do_not_admit_or_poison_owner() {
    let (temp, engine) = fixture(1, "cancel-op");
    let host = temp.host(false);
    let session = select(&host, &engine);
    let before = std::fs::read(temp.path()).unwrap();
    assert_eq!(
        host.memory_maintenance(
            &session,
            engine.scope(),
            engine.revision(),
            Action::Admit,
            &|| true
        ),
        Err(Error::Cancelled)
    );
    assert_eq!(
        host.memory_maintenance(
            &session,
            engine.scope(),
            engine.revision(),
            Action::Admit,
            &|| panic!("synthetic private callback")
        ),
        Err(Error::Cancelled)
    );
    assert_eq!(run(&host, &session, &engine, Action::Status).job, None);
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    assert_canon(&temp, &engine);
}
#[test]
fn same_head_receipt_replacement_is_refused_without_job_or_canonical_writes() {
    let (temp, engine) = fixture(1, "original");
    let host = temp.host(false);
    let session = select(&host, &engine);
    let (alternate, changed) = fixture(1, "changed");
    let archive = alternate
        .store()
        .export_archive(&changed.scope().story, &|| false)
        .unwrap();
    let mut writer = temp.store();
    let deletion = writer
        .prepare_story_deletion(engine.scope(), engine.revision(), &|| false)
        .unwrap();
    writer.delete_story(deletion, &|| false).unwrap();
    writer
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let before = std::fs::read(temp.path()).unwrap();
    for action in [
        Action::Status,
        Action::Admit,
        Action::Step,
        Action::Cancel,
        Action::Prune,
    ] {
        assert_eq!(
            host.memory_maintenance(&session, engine.scope(), engine.revision(), action, &|| {
                false
            }),
            Err(Error::Stale)
        );
    }
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    assert_canon(&temp, &changed);
}
#[test]
fn count_only_reply_and_lab_inspection_never_choose_another_observer() {
    let (temp, engine) = fixture(1, "private-counts");
    let ordinary = temp.host(false);
    let session = select(&ordinary, &engine);
    let missing = run(&ordinary, &session, &engine, Action::Status);
    let lab = temp.host(true);
    let lab_session = select(&lab, &engine);
    assert_eq!(run(&lab, &lab_session, &engine, Action::Status), missing);
    let reply = run(&ordinary, &session, &engine, Action::Admit);
    let json = serde_json::to_string(&reply).unwrap();
    assert!(json.len() < 4096);
    for excluded in [
        "handle",
        "observer",
        "packet_json",
        "source_sha256",
        "player",
        "mira",
        "prompt",
        temp.path().to_str().unwrap(),
    ] {
        assert!(!json.contains(excluded), "{excluded}");
    }
    let mut npc = request(&engine);
    npc.observer = "mira".into();
    let mut store = temp.store();
    // Existing actor-general API is unchanged; this creates a distinct NPC row.
    let npc_job = store.ensure_memory_job(&npc, &|| false).unwrap();
    let player_job = store
        .lookup_memory_job(&request(&engine), &engine, &|| false)
        .unwrap()
        .unwrap();
    assert_ne!(npc_job.handle.id(), player_job.handle.id());
    let player_view = run(&lab, &lab_session, &engine, Action::Status)
        .job
        .unwrap();
    assert_eq!(player_view.next_from, 0);
    assert_canon(&temp, &engine);
}
