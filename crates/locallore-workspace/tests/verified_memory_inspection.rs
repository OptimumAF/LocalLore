// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE-ONLY actual Host/Repository/Store oracles. UNCOMPILED/UNRUN at freeze.
//! No SQL-authored history, providers, native IPC, frontend or device qualification.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::{Command, Intent, Scope, Seed},
    engine::Engine,
    host::{
        memory_inspection::{
            MemoryInspectionError as Error, MemoryInspectionRequestV1 as Request,
            MemoryInspectionViewV1 as View,
        },
        Host,
    },
    inspection_query::{self, Observer, Query, View as QueryView},
    memory_coverage::{CoverageRead, SourceRef},
};
use locallore_storage::{
    memory_jobs::{MemoryJobRequest, MemoryJobStatus},
    playable_archive::validate_archive,
    Store,
};
use serde_json::{json, Value};
use std::{
    cell::Cell,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-verified-inspection-{}-{}-{}",
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
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn select(host: &Host, scope: &Scope) -> String {
    let reply = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["session"].as_str().unwrap().into()
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn create(temp: &Temp) -> Engine {
    let mut store = temp.store();
    let seed = seed();
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic verified memory", seed)
        .unwrap();
    store.resume(&scope).unwrap().engine
}
fn apply(temp: &Temp, scope: &Scope, key: &str, commands: Vec<Command>) -> Engine {
    let mut store = temp.store();
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&preview).unwrap();
    store.resume(scope).unwrap().engine
}
fn four(temp: &Temp, scope: &Scope) -> Engine {
    apply(
        temp,
        scope,
        "actual-four",
        vec![
            Command::Say {
                text: "PUBLIC-INSPECTION".into(),
                audience: ["mira".into()].into(),
            },
            Command::Say {
                text: "PLAYER-ONLY-INSPECTION".into(),
                audience: ["player".into()].into(),
            },
            Command::Wait { ticks: 1 },
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        ],
    )
}
fn job(engine: &Engine) -> MemoryJobRequest {
    MemoryJobRequest {
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        observer: engine.seed().player.clone(),
    }
}
fn drain(temp: &Temp, engine: &Engine) {
    let mut store = temp.store();
    let mut info = store.ensure_memory_job(&job(engine), &|| false).unwrap();
    for _ in 0..32 {
        if info.status == MemoryJobStatus::Complete {
            return;
        }
        assert_eq!(info.status, MemoryJobStatus::Ready);
        let step = store
            .prepare_memory_job_step(&info.handle, &|| false)
            .unwrap();
        info = store.publish_memory_job_step(step, &|| false).unwrap();
    }
    panic!("bounded synthetic fixture did not complete");
}
fn packets(engine: &Engine, binding: Option<String>, limit: u16) -> Request {
    Request {
        version: 1,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        observer: Observer::Player,
        binding,
        view: View::Packets {
            cursor: None,
            limit,
        },
    }
}
fn inspect(host: &Host, session: &str, request: &Request) -> Value {
    let value =
        serde_json::to_value(host.memory_inspection(session, request, &|| false).unwrap()).unwrap();
    assert!(serde_json::to_vec(&value).unwrap().len() <= 65536);
    value
}
fn binding(value: &Value) -> String {
    value["binding"].as_str().unwrap().into()
}
fn assert_canon(temp: &Temp, engine: &Engine) {
    let actual = temp.store().resume(engine.scope()).unwrap().engine;
    assert_eq!(actual.canonical_bytes(), engine.canonical_bytes());
    assert_eq!(actual.canonical_records(), engine.canonical_records());
}

#[test]
fn missing_is_passive_and_real_verified_entries_drill_into_actual_query2_without_npc_grant() {
    let temp = Temp::new();
    let initial = create(&temp);
    let engine = four(&temp, initial.scope());
    let host = temp.host(true);
    let session = select(&host, engine.scope());
    let bytes = std::fs::read(temp.path()).unwrap();
    let missing = inspect(&host, &session, &packets(&engine, None, 64));
    assert_eq!(
        missing["coverage"],
        json!({"status":"raw_fallback","verified_head":null,
        "covered_through":null,"raw_delta_after":0,"fallback":"missing"})
    );
    assert_eq!(missing["rows"], json!([]));
    assert!(temp
        .store()
        .lookup_memory_job(&job(&engine), &engine, &|| false)
        .unwrap()
        .is_none());
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
    drain(&temp, &engine);
    let mut store = temp.store();
    let snapshot = store.context_snapshot(&job(&engine), &|| false).unwrap();
    let CoverageRead::Verified(proof) = snapshot.coverage else {
        panic!("real completed proof");
    };
    let npc_before =
        serde_json::to_value(engine.character_context("mira", engine.scope(), 4).unwrap()).unwrap();
    assert!(!npc_before.to_string().contains("PLAYER-ONLY-INSPECTION"));
    let bytes = std::fs::read(temp.path()).unwrap();
    let page = inspect(&host, &session, &packets(&engine, None, 64));
    assert_ne!(
        binding(&page),
        binding(&missing),
        "cache publication changes bound snapshot"
    );
    assert_eq!(page["observer"], engine.seed().player);
    assert_eq!(page["privacy"], "player_visible");
    assert_eq!(page["coverage"]["verified_head"], proof.verified_head());
    assert_eq!(page["coverage"]["covered_through"], proof.covered_through());
    assert_eq!(page["total"], proof.packets().len());
    for (index, packet) in proof.packets().iter().enumerate() {
        let row = &page["rows"][index];
        assert_eq!(row["index"], index);
        assert_eq!(row["version"], packet.version);
        assert_eq!(row["method"], packet.method);
        assert_eq!(
            row["closure"],
            serde_json::to_value(&packet.closure).unwrap()
        );
        assert_eq!(row["entry_count"], packet.entries.len());
        assert_eq!(row["source_event_count"], packet.source_events.len());
    }
    let packet = &proof.packets()[0];
    assert!(packet.entries.len() > 1);
    let mut request = packets(&engine, Some(binding(&page)), 64);
    request.view = View::Entries {
        packet_index: 0,
        cursor: None,
        limit: 1,
    };
    let mut actual_entries = vec![];
    for _ in 0..256 {
        let value = inspect(&host, &session, &request);
        actual_entries.extend(
            value["rows"]
                .as_array()
                .unwrap()
                .iter()
                .map(|row| row["value"].clone()),
        );
        match value["next_cursor"].as_str() {
            None => break,
            Some(cursor) => {
                request.view = View::Entries {
                    packet_index: 0,
                    cursor: Some(cursor.into()),
                    limit: 1,
                }
            }
        }
    }
    assert_eq!(
        actual_entries,
        packet
            .entries
            .iter()
            .map(|entry| serde_json::to_value(entry).unwrap())
            .collect::<Vec<_>>()
    );
    let source = packet.source_events[0].clone();
    request.view = View::Source {
        packet_index: 0,
        source: source.clone(),
    };
    let result = inspect(&host, &session, &request);
    let query = Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: Some(packet.through_revision),
        observer: Observer::Player,
        view: QueryView::History,
        cursor: None,
        limit: 64,
        search: format!("\"sequence\":{},", source.sequence),
    };
    let exact = inspection_query::query(&snapshot.engine, &query, true).unwrap();
    assert_eq!(result["page"], serde_json::to_value(exact).unwrap());
    assert_eq!(result["matched"], true);
    assert_eq!(result["source"], serde_json::to_value(source).unwrap());
    assert_eq!(
        serde_json::to_value(engine.character_context("mira", engine.scope(), 4).unwrap()).unwrap(),
        npc_before
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
    assert_canon(&temp, &engine);
}

#[test]
fn real_prefix_is_verified_with_raw_delta_and_cursor_cannot_cross_limit_view_or_publication() {
    let temp = Temp::new();
    let mut engine = create(&temp);
    for index in 0..129 {
        engine = apply(
            &temp,
            engine.scope(),
            &format!("prefix-{index}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    let mut store = temp.store();
    let info = store.ensure_memory_job(&job(&engine), &|| false).unwrap();
    let step = store
        .prepare_memory_job_step(&info.handle, &|| false)
        .unwrap();
    let first = store.publish_memory_job_step(step, &|| false).unwrap();
    assert!(first.next_from > 0 && first.next_from < engine.revision());
    let host = temp.host(true);
    let session = select(&host, engine.scope());
    let page = inspect(&host, &session, &packets(&engine, None, 64));
    assert_eq!(page["coverage"]["status"], "verified");
    assert_eq!(page["coverage"]["raw_delta_after"], first.next_from);
    assert_eq!(page["coverage"]["verified_head"], 129);
    let mut request = packets(&engine, Some(binding(&page)), 64);
    request.view = View::Entries {
        packet_index: 0,
        cursor: None,
        limit: 1,
    };
    let entries = inspect(&host, &session, &request);
    // Adjacent Waits can coalesce into one entry. The four-event fixture above
    // exercises actual multi-page traversal; use its cursor separately below.
    assert!(entries["total"].as_u64().unwrap() > 0);
    drain(&temp, &engine);
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::Binding
    );
    let complete = inspect(&host, &session, &packets(&engine, None, 64));
    assert_eq!(complete["coverage"]["covered_through"], 129);
    assert_ne!(binding(&complete), binding(&page));
    assert_canon(&temp, &engine);
}

#[test]
fn same_head_real_archive_replacement_changes_binding_even_when_both_extend_selected_zero() {
    let temp = Temp::new();
    let initial = create(&temp);
    let host = temp.host(true);
    let session = select(&host, initial.scope());
    let a = apply(
        &temp,
        initial.scope(),
        "a",
        vec![Command::Say {
            text: "FIRST-A".into(),
            audience: ["mira".into()].into(),
        }],
    );
    let first = inspect(&host, &session, &packets(&a, None, 64));
    let alternate = Temp::new();
    create(&alternate);
    let b = apply(
        &alternate,
        initial.scope(),
        "b",
        vec![Command::Say {
            text: "SECOND-B".into(),
            audience: ["mira".into()].into(),
        }],
    );
    assert_eq!(a.seed(), b.seed());
    assert_eq!(a.revision(), b.revision());
    assert_ne!(a.canonical_records(), b.canonical_records());
    let archive = alternate
        .store()
        .export_archive(&initial.scope().story, &|| false)
        .unwrap();
    let validated = validate_archive(archive.bytes(), &|| false).unwrap();
    let mut store = temp.store();
    let deletion = store
        .prepare_story_deletion(initial.scope(), 1, &|| false)
        .unwrap();
    store.delete_story(deletion, &|| false).unwrap();
    store.import_archive(validated, &|| false).unwrap();
    let bytes = std::fs::read(temp.path()).unwrap();
    assert_eq!(
        host.memory_inspection(&session, &packets(&b, Some(binding(&first)), 64), &|| false)
            .unwrap_err(),
        Error::Binding
    );
    assert_ne!(
        binding(&inspect(&host, &session, &packets(&b, None, 64))),
        binding(&first)
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
    assert_canon(&temp, &b);
}

#[test]
fn player_lab_source_and_request_fences_cancel_panics_do_not_write_or_poison_owner() {
    let temp = Temp::new();
    let zero = create(&temp);
    let engine = four(&temp, zero.scope());
    drain(&temp, &engine);
    let host = temp.host(true);
    let session = select(&host, engine.scope());
    let page = inspect(&host, &session, &packets(&engine, None, 64));
    let mut request = packets(&engine, None, 64);
    let bytes = std::fs::read(temp.path()).unwrap();
    for observer in [
        Observer::Omniscient,
        Observer::Character {
            id: "player".into(),
        },
        Observer::Character { id: "mira".into() },
    ] {
        request.observer = observer;
        assert_eq!(
            host.memory_inspection(&session, &request, &|| false)
                .unwrap_err(),
            Error::Forbidden
        );
    }
    request.observer = Observer::Player;
    let no_lab = temp.host(false);
    let no_lab_session = select(&no_lab, engine.scope());
    assert_eq!(
        no_lab
            .memory_inspection(&no_lab_session, &request, &|| false)
            .unwrap_err(),
        Error::Forbidden
    );
    request.version = 2;
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::Version
    );
    request.version = 1;
    request.expected_head = 9007199254740992;
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::InvalidInput
    );
    request.expected_head = engine.revision() + 1;
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::Stale
    );
    request.expected_head = engine.revision();
    for limit in [0, 65, u16::MAX] {
        request.view = View::Packets {
            cursor: None,
            limit,
        };
        assert_eq!(
            host.memory_inspection(&session, &request, &|| false)
                .unwrap_err(),
            Error::InvalidInput
        );
    }
    request = packets(&engine, Some(binding(&page)), 64);
    request.view = View::Entries {
        packet_index: 0,
        cursor: None,
        limit: 1,
    };
    let first = inspect(&host, &session, &request);
    let cursor = first["next_cursor"].as_str().unwrap().to_owned();
    request.view = View::Entries {
        packet_index: 0,
        cursor: Some(cursor.clone()),
        limit: 2,
    };
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::InvalidCursor
    );
    request.view = View::Packets {
        cursor: Some(cursor),
        limit: 1,
    };
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::InvalidCursor
    );
    request.view = View::Source {
        packet_index: 0,
        source: SourceRef {
            scope: Scope {
                branch: "foreign".into(),
                ..engine.scope().clone()
            },
            sequence: 1,
        },
    };
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::InvalidInput
    );
    request = packets(&engine, None, 64);
    assert_eq!(
        host.memory_inspection(&session, &request, &|| true)
            .unwrap_err(),
        Error::Cancelled
    );
    assert_eq!(
        host.memory_inspection(&session, &request, &|| panic!("synthetic cancellation"))
            .unwrap_err(),
        Error::Cancelled
    );
    let polls = Cell::new(0);
    assert_eq!(
        host.memory_inspection(&session, &request, &|| {
            polls.set(polls.get() + 1);
            polls.get() == 8
        })
        .unwrap_err(),
        Error::Cancelled
    );
    assert!(polls.get() >= 8);
    assert_eq!(
        inspect(&host, &session, &request)["coverage"]["status"],
        "verified"
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
    assert_canon(&temp, &engine);
}

#[test]
fn actual_author_domain2_is_unsupported_and_player_id_is_native_not_literal() {
    let temp = Temp::new();
    let engine = create(&temp);
    let mut store = temp.store();
    let old = engine.seed().facts["relic-location"].proposition.clone();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: engine.scope().clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old,
            replacement: "PRIVATE-NEW".into(),
        },
        reason: "PRIVATE-REASON".into(),
    };
    let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
    let authored = store.apply_author_correction(&prepared, &|| false).unwrap();
    let child = store.resume(&authored.scope).unwrap().engine;
    assert_eq!(child.domain_version(), 2);
    let host = temp.host(true);
    let session = select(&host, child.scope());
    let bytes = std::fs::read(temp.path()).unwrap();
    assert_eq!(
        host.memory_inspection(&session, &packets(&child, None, 64), &|| false)
            .unwrap_err(),
        Error::Unsupported
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
    let other = Temp::new();
    let mut custom = seed();
    custom.player = "mira".into();
    let scope = custom.scope.clone();
    other
        .store()
        .create_story("Native Mira player", custom)
        .unwrap();
    let engine = other.store().resume(&scope).unwrap().engine;
    let host = other.host(true);
    let session = select(&host, &scope);
    assert_eq!(
        inspect(&host, &session, &packets(&engine, None, 64))["observer"],
        "mira"
    );
}

#[test]
fn actual_accepted_unsafe_story_time_is_never_rounded_into_an_entry_or_source_reply() {
    let temp = Temp::new();
    let mut high = seed();
    high.story_time = 9_007_199_254_740_991;
    let scope = high.scope.clone();
    temp.store()
        .create_story("Safe-integer boundary fixture", high)
        .unwrap();
    let engine = apply(
        &temp,
        &scope,
        "unsafe-time",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(engine.state().story_time, 9_007_199_254_740_992);
    drain(&temp, &engine);
    let host = temp.host(true);
    let session = select(&host, &scope);
    let page = inspect(&host, &session, &packets(&engine, None, 64));
    assert_eq!(page["coverage"]["status"], "verified");
    let bytes = std::fs::read(temp.path()).unwrap();
    let mut request = packets(&engine, Some(binding(&page)), 64);
    request.view = View::Entries {
        packet_index: 0,
        cursor: None,
        limit: 64,
    };
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::TooLarge
    );
    request.view = View::Source {
        packet_index: 0,
        source: SourceRef { scope, sequence: 1 },
    };
    assert_eq!(
        host.memory_inspection(&session, &request, &|| false)
            .unwrap_err(),
        Error::TooLarge
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), bytes);
    assert_canon(&temp, &engine);
}
