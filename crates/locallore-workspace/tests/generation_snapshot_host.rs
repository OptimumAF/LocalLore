// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Real Host/Repository/SQLite reads; model-free, no canonical SQL fixture writes.
use locallore::{
    contracts::{Command, Intent, Request, Scope, Seed},
    host::{Host, HostGenerationSnapshot},
    inspection_query::{Observer, Query, View},
    memory_coverage::{CoverageRead, CoverageRequest, FallbackReason},
};
use locallore_storage::{
    memory_jobs::{MemoryJobInfo, MemoryJobRequest, MemoryJobStatus},
    playable_archive::validate_archive,
    Store,
};
use serde_json::{json, Value};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-generation-snapshot-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT_TEMP.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn host(&self, lab: bool) -> Host {
        locallore_workspace::open(&self.path(), lab).unwrap()
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn create(host: &Host) -> (String, Scope) {
    let v = call(host, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(v["status"], "ok", "{v}");
    (
        v["data"]["session"].as_str().unwrap().into(),
        serde_json::from_value(v["data"]["scope"].clone()).unwrap(),
    )
}
fn error(result: Result<HostGenerationSnapshot, String>) -> String {
    match result {
        Err(error) => error,
        Ok(_) => panic!("expected snapshot refusal"),
    }
}
fn commit_four(host: &Host, session: &str, scope: &Scope) {
    let request = Request {
        version: 1,
        scope: scope.clone(),
        turn: "snapshot-prefix".into(),
        expected_revision: 0,
        intent: Intent::Actions(vec![
            Command::Say {
                text: "SNAPSHOT-PUBLIC".into(),
                audience: ["mira".into()].into(),
            },
            Command::Say {
                text: "SNAPSHOT-PLAYER-ONLY".into(),
                audience: ["player".into()].into(),
            },
            Command::Wait { ticks: 1 },
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        ]),
    };
    let submit = call(
        host,
        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
    );
    assert_eq!(submit["data"]["phase"], "queued", "{submit}");
    let ready = call(
        host,
        json!({"op":"prepare","session":session,"scope":scope,"turn":request.turn}),
    );
    assert_eq!(ready["data"]["phase"], "ready", "{ready}");
    let committed = call(
        host,
        json!({"op":"commit","session":session,"scope":scope,"turn":request.turn}),
    );
    assert_eq!(committed["data"]["phase"], "committed", "{committed}");
}
fn drain(store: &mut Store, scope: &Scope, observer: &str) -> MemoryJobInfo {
    let mut info = store
        .ensure_memory_job(
            &MemoryJobRequest {
                scope: scope.clone(),
                observer: observer.into(),
                expected_head: 4,
            },
            &|| false,
        )
        .unwrap();
    for _ in 0..32 {
        if info.status == MemoryJobStatus::Complete {
            return info;
        }
        assert_eq!(info.status, MemoryJobStatus::Ready);
        let step = store
            .prepare_memory_job_step(&info.handle, &|| false)
            .unwrap();
        info = store.publish_memory_job_step(step, &|| false).unwrap();
    }
    panic!("four accepted events did not complete within the fixed packet limit");
}
fn query(scope: &Scope, head: u64, observer: Observer) -> Query {
    Query {
        version: 1,
        scope: scope.clone(),
        expected_head: head,
        at_revision: None,
        observer,
        view: View::History,
        cursor: None,
        limit: 64,
        search: String::new(),
    }
}

#[test]
fn absent_cache_is_honest_read_only_and_does_not_admit_a_job() {
    let temp = Temp::new();
    let host = temp.host(false);
    let (session, scope) = create(&host);
    let mut store = temp.store();
    let before = store.resume(&scope).unwrap().engine;
    let bytes = std::fs::read(temp.path()).unwrap();
    let counts = host.live_counts();
    let snapshot = host
        .generation_snapshot(&session, &scope, 0, &|| false)
        .unwrap();
    assert!(matches!(
        snapshot.coverage,
        CoverageRead::RawFallback(FallbackReason::Missing)
    ));
    assert_eq!(snapshot.engine.canonical_bytes(), before.canonical_bytes());
    assert_eq!(snapshot.engine.receipts(), before.receipts());
    assert_eq!(
        std::fs::read(temp.path()).unwrap(),
        bytes,
        "read admitted no job or other SQLite write"
    );
    assert_eq!(host.live_counts(), counts);
    commit_four(&host, &session, &scope);
    let snapshot = host
        .generation_snapshot(&session, &scope, 4, &|| false)
        .unwrap();
    assert_eq!(snapshot.engine.revision(), 4);
    assert_eq!(snapshot.engine.receipts().len(), 1);
    assert_eq!(snapshot.engine.receipts()[0].events().len(), 4);
    assert!(matches!(
        snapshot.coverage,
        CoverageRead::RawFallback(FallbackReason::Missing)
    ));
}

#[test]
fn coherent_verified_player_proof_survives_lab_inspection_without_npc_knowledge_grant() {
    let temp = Temp::new();
    let host = temp.host(true);
    let (session, scope) = create(&host);
    commit_four(&host, &session, &scope);
    let mut store = temp.store();
    let player_job = drain(&mut store, &scope, "player");
    let mira_job = drain(&mut store, &scope, "mira");
    let before = store.resume(&scope).unwrap().engine;
    let npc_before =
        serde_json::to_value(before.character_context("mira", &scope, 4).unwrap()).unwrap();
    assert!(!npc_before.to_string().contains("SNAPSHOT-PLAYER-ONLY"));
    host.inspection_query(&session, &query(&scope, 4, Observer::Omniscient))
        .unwrap();
    host.inspection_query(
        &session,
        &query(&scope, 4, Observer::Character { id: "mira".into() }),
    )
    .unwrap();
    let bytes = std::fs::read(temp.path()).unwrap();
    let snapshot = host
        .generation_snapshot(&session, &scope, 4, &|| false)
        .unwrap();
    let CoverageRead::Verified(proof) = &snapshot.coverage else {
        panic!("actual completed player cache must verify")
    };
    assert_eq!(proof.covered_through(), 4);
    assert_eq!(proof.verified_head(), snapshot.engine.revision());
    assert!(proof
        .packets()
        .iter()
        .all(|packet| packet.observer == "player"));
    let packets = serde_json::to_string(proof.packets()).unwrap();
    assert!(packets.contains("SNAPSHOT-PLAYER-ONLY"));
    assert!(matches!(
        proof
            .recheck(
                &snapshot.engine,
                &CoverageRequest {
                    scope: scope.clone(),
                    observer: "player".into(),
                    expected_head: 4
                },
                &|| false
            )
            .unwrap(),
        CoverageRead::Verified(_)
    ));
    let mira_snapshot = store
        .context_snapshot(
            &MemoryJobRequest {
                scope: scope.clone(),
                observer: "mira".into(),
                expected_head: 4,
            },
            &|| false,
        )
        .unwrap();
    let CoverageRead::Verified(mira_proof) = mira_snapshot.coverage else {
        panic!("actual NPC cache must verify")
    };
    assert!(!serde_json::to_string(mira_proof.packets())
        .unwrap()
        .contains("SNAPSHOT-PLAYER-ONLY"));
    assert_eq!(
        serde_json::to_value(
            snapshot
                .engine
                .character_context("mira", &scope, 4)
                .unwrap()
        )
        .unwrap(),
        npc_before
    );
    assert_eq!(snapshot.engine.canonical_bytes(), before.canonical_bytes());
    assert_eq!(snapshot.engine.receipts(), before.receipts());
    assert_eq!(
        store
            .memory_job_status(&player_job.handle, &|| false)
            .unwrap(),
        player_job
    );
    assert_eq!(
        store
            .memory_job_status(&mira_job.handle, &|| false)
            .unwrap(),
        mira_job
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
    assert_eq!(
        call(&host, json!({"op":"capabilities"}))["data"]["author"],
        false
    );
}

#[test]
fn durable_session_scope_head_cancel_and_json_boundaries_are_closed() {
    let temp = Temp::new();
    let host = temp.host(false);
    let (session, scope) = create(&host);
    assert_eq!(
        error(host.generation_snapshot("missing", &scope, 0, &|| false)),
        "Closed"
    );
    let other = Scope {
        branch: "other".into(),
        ..scope.clone()
    };
    assert_eq!(
        error(host.generation_snapshot(&session, &other, 0, &|| false)),
        "Scope"
    );
    assert_eq!(
        error(host.generation_snapshot(&session, &scope, 1, &|| false)),
        "Stale"
    );
    assert_eq!(
        error(host.generation_snapshot(&session, &scope, 0, &|| true)),
        "Cancelled"
    );
    assert_eq!(
        error(host.generation_snapshot(&session, &scope, 0, &|| panic!("synthetic cancel panic"))),
        "Cancelled"
    );
    assert!(host
        .generation_snapshot(&session, &scope, 0, &|| false)
        .is_ok());
    assert_eq!(
        host.inspection_query(&session, &query(&scope, 0, Observer::Omniscient))
            .unwrap_err(),
        "Forbidden"
    );
    assert_eq!(
        host.inspection_query(
            &session,
            &query(&scope, 0, Observer::Character { id: "mira".into() })
        )
        .unwrap_err(),
        "Forbidden"
    );
    let invented = call(
        &host,
        json!({"op":"generation_snapshot","session":session,"scope":scope,"expected_head":0,"observer":"mira"}),
    );
    assert_ne!(
        invented["status"], "ok",
        "native port must not become a JSON capability: {invented}"
    );
    assert_eq!(
        call(&host, json!({"op":"close","session":session,"scope":scope}))["status"],
        "ok"
    );
    assert_eq!(
        error(host.generation_snapshot(&session, &scope, 0, &|| false)),
        "Closed"
    );
}

fn replace_via_actual_archive(temp: &Temp, scope: &Scope, seed: Seed) {
    let alternate = Temp::new();
    let mut source = alternate.store();
    source
        .create_story("Replacement synthetic story", seed)
        .unwrap();
    let archive = source.export_archive(&scope.story, &|| false).unwrap();
    let validated = validate_archive(archive.bytes(), &|| false).unwrap();
    let mut target = temp.store();
    let deletion = target.prepare_story_deletion(scope, 0, &|| false).unwrap();
    target.delete_story(deletion, &|| false).unwrap();
    target.import_archive(validated, &|| false).unwrap();
}

#[test]
fn same_scope_head_id_and_player_seed_replacement_is_stale() {
    let temp = Temp::new();
    let host = temp.host(false);
    let (session, scope) = create(&host);
    let old = temp.store().resume(&scope).unwrap().engine;
    let mut seed = old.seed().clone();
    seed.facts.get_mut("ancestry").unwrap().proposition =
        "An independently imported replacement seed.".into();
    replace_via_actual_archive(&temp, &scope, seed.clone());
    let before = temp.store().resume(&scope).unwrap().engine;
    assert_eq!(before.scope(), old.scope());
    assert_eq!(before.revision(), old.revision());
    assert_eq!(before.seed().id, old.seed().id);
    assert_eq!(before.seed().player, old.seed().player);
    assert_ne!(before.seed(), old.seed());
    let bytes = std::fs::read(temp.path()).unwrap();
    assert_eq!(
        error(host.generation_snapshot(&session, &scope, 0, &|| false)),
        "Stale"
    );
    assert_eq!(temp.store().resume(&scope).unwrap().engine.seed(), &seed);
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
}

#[test]
fn replaced_seed_without_old_selected_player_maps_not_found_to_stale() {
    let temp = Temp::new();
    let host = temp.host(false);
    let (session, scope) = create(&host);
    let seed: Seed = serde_json::from_value(json!({
        "version":1,"id":"replacement-v1","scope":scope,"profile":"fantasy_v1","player":"replacement",
        "locations":["room"],"routes":[],"actors":{"replacement":{"name":"Replacement","location":"room","alive":true,"energy":0,
        "abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]}},
        "items":{},"abilities":{},"facts":{},"relationships":[],"story_time":0,"beliefs":[],"commitments":{}
    })).unwrap();
    replace_via_actual_archive(&temp, &scope, seed.clone());
    assert_eq!(
        error(host.generation_snapshot(&session, &scope, 0, &|| false)),
        "Stale"
    );
    let actual = temp.store().resume(&scope).unwrap().engine;
    assert_eq!(actual.seed(), &seed);
    assert!(!actual.seed().actors.contains_key("player"));
    assert_eq!(actual.revision(), 0);
}

#[test]
fn ephemeral_snapshot_is_actual_coherent_engine_and_explicit_raw_fallback() {
    let host = Host::new(false);
    let (session, scope) = create(&host);
    let snapshot = host
        .generation_snapshot(&session, &scope, 0, &|| false)
        .unwrap();
    assert_eq!(snapshot.engine.scope(), &scope);
    assert_eq!(snapshot.engine.seed().player, "player");
    assert_eq!(snapshot.engine.revision(), 0);
    assert!(matches!(
        snapshot.coverage,
        CoverageRead::RawFallback(FallbackReason::Missing)
    ));
    assert_eq!(
        error(host.generation_snapshot(&session, &scope, 1, &|| false)),
        "Stale"
    );
    assert_eq!(
        call(&host, json!({"op":"workspace"}))["data"]["persistent"],
        false
    );
}
