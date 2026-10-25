// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen selected-read oracles, SOURCE-ONLY / UNRUN at handoff.
//! Actual scripted Host/Store producers and Core Query2, not native/UI execution.
//! Root owns desktop_read implementation and this child module's registration.
use crate::local_lane::{
    comparison::{
        self,
        desktop_api::{self as comparison_read, Arm, Edge, EvidenceRequest},
        selected::{self, desktop_read},
    },
    LaneFactory,
};
use crate::{encode, engine, Result};
use locallore::{
    engine::Engine,
    inference::Cancellation,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::OnceLock,
};

const INDEX: usize = 4;
const SECRET: &str = "SECRET-TIDE-731";
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-read-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&root).unwrap();
    root
}
// Whole inventories are read only after opaque lock owners and Store handles drop.
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                out.insert(relative, None);
                walk(root, &path, depth + 1, total, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(&path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                out.insert(relative, Some(bytes));
            }
        }
    }
    let mut out = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}
fn json_file(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn keys(value: &Value, expected: &[&str]) {
    assert_eq!(
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>()
    );
}
fn refused<T>(result: Result<T>) -> String {
    match result {
        Ok(_) => panic!("expected closed selected-reader refusal"),
        Err(error) => {
            assert!(!error.is_empty() && error.len() <= 96);
            assert!(error
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_'));
            error
        }
    }
}
fn template() -> &'static Path {
    static TEMPLATE: OnceLock<PathBuf> = OnceLock::new();
    TEMPLATE
        .get_or_init(|| {
            let root = root("actual-producers");
            let source = root.join("source");
            let produced = comparison::run_comparison(
                &source,
                false,
                comparison::ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!((produced.completed_scenes, produced.turns.len()), (1, 12));
            assert!(produced.turns.iter().all(|row| row.passed));
            let opened = comparison_read::open_read_only(&source).unwrap();
            let source_binding = comparison_read::summary(&opened, true).unwrap()["binding"]
                .as_str()
                .unwrap()
                .to_owned();
            drop(opened);
            let corpus = comparison::suite().unwrap();
            assert_eq!(corpus.steps()[INDEX].text(), "I move to pier.");
            let plan = selected::prepare_selected(
                &source,
                &source_binding,
                &comparison_read::RowId {
                    turn: corpus.steps()[INDEX].id().into(),
                    arm: Arm::Right,
                },
                selected::SelectedIntent {
                    client_id: "selected-read-fixture".into(),
                    lane: selected::SelectedLane::ScriptedBaseline,
                },
                &Cancellation::default(),
            )
            .unwrap();
            let report =
                selected::run_selected(plan, &root.join("selected"), &Cancellation::default())
                    .unwrap();
            assert!(report.completed && report.rows.iter().all(|row| row.passed));
            root
        })
        .as_path()
}
struct Fixture {
    root: PathBuf,
    source: PathBuf,
    target: PathBuf,
    execution: String,
}
impl Fixture {
    fn new(label: &str) -> Self {
        let original = inventory(template());
        let root = root(label);
        for (relative, bytes) in &original {
            match bytes {
                None => fs::create_dir_all(root.join(relative)).unwrap(),
                Some(bytes) => fs::write(root.join(relative), bytes).unwrap(),
            }
        }
        assert!(inventory(&root) == original);
        let source = root.join("source");
        let target = root.join("selected");
        let execution = json_file(&target.join("selected.json"))["binding"]
            .as_str()
            .unwrap()
            .to_owned();
        Self {
            root,
            source,
            target,
            execution,
        }
    }
    fn cp(&self, arm: &str) -> PathBuf {
        comparison::checkpoint_path(&self.target.join(arm), INDEX)
    }
    fn full(&self, arm: &str) -> Engine {
        let scope = comparison::suite().unwrap().seed().scope.clone();
        engine(&self.target.join(arm).join("synthetic.sqlite"), &scope).unwrap()
    }
}
fn snapshot_binding(summary: &Value) -> String {
    let value = summary["binding"].as_str().unwrap();
    assert!(value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit()));
    value.into()
}
fn safe_summary(summary: &Value, fixture: &Fixture, available: [bool; 2]) {
    keys(
        summary,
        &[
            "version",
            "kind",
            "binding",
            "selection",
            "lane",
            "arms",
            "read_only",
            "execution_available",
        ],
    );
    assert_eq!(summary["version"], 1);
    assert_eq!(summary["kind"], "selected_read");
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    assert_eq!(summary["lane"], "scripted_selected_case");
    assert_ne!(
        snapshot_binding(summary),
        fixture.execution,
        "read snapshot must not be an execution binding"
    );
    keys(&summary["selection"], &["turn", "clicked_arm", "index"]);
    assert_eq!(summary["selection"]["index"], INDEX);
    assert_eq!(
        summary["selection"]["turn"],
        comparison::suite().unwrap().steps()[INDEX].id()
    );
    assert_eq!(summary["selection"]["clicked_arm"], "right");
    assert_eq!(summary["arms"].as_array().unwrap().len(), 2);
    for (index, arm) in ["left", "right"].into_iter().enumerate() {
        let value = &summary["arms"][index];
        keys(
            value,
            &["arm", "scope", "before_head", "after_head", "available"],
        );
        assert_eq!(value["arm"], arm);
        assert_eq!(value["available"], available[index]);
        let manifest = json_file(&fixture.target.join("selected.json"));
        assert_eq!(value["scope"], manifest["source_inputs"][index]["scope"]);
        assert_eq!(
            value["before_head"],
            manifest["source_inputs"][index]["before_head"]
        );
        if available[index] {
            assert_eq!(
                value["after_head"],
                json_file(&fixture.cp(arm))["after_head"]
            );
        } else {
            assert!(value["after_head"].is_null());
        }
    }
    fn no_private(value: &Value) {
        match value {
            Value::Object(fields) => {
                for (key, value) in fields {
                    assert!(![
                        "report",
                        "request",
                        "trace",
                        "outputs",
                        "profile",
                        "metrics",
                        "narration",
                        "text",
                        "error",
                        "receipt",
                        "source_binding",
                        "source_profile",
                        "source_inputs"
                    ]
                    .contains(&key.as_str()));
                    no_private(value);
                }
            }
            Value::Array(values) => {
                for value in values {
                    no_private(value);
                }
            }
            Value::String(value) => {
                assert!(!value.contains(SECRET) && !value.contains("amber stitch"))
            }
            _ => {}
        }
    }
    no_private(summary);
}
fn expected_page(full: &Engine, head: u64, observer: Observer, view: View) -> Value {
    let cut = full.at_revision(head).unwrap();
    serde_json::to_value(
        inspection_query::query(
            &cut,
            &Query {
                version: 2,
                scope: cut.scope().clone(),
                expected_head: head,
                at_revision: None,
                observer,
                view,
                cursor: None,
                limit: MAX_ROWS,
                search: String::new(),
            },
            true,
        )
        .unwrap(),
    )
    .unwrap()
}
fn generation_contexts(full: &Engine) -> Value {
    json!([
        full.character_context(&full.seed().player, full.scope(), full.revision())
            .unwrap(),
        full.character_context("mira", full.scope(), full.revision())
            .unwrap(),
        full.character_context("sable", full.scope(), full.revision())
            .unwrap()
    ])
}
fn query(edge: Edge, observer: Observer, view: View) -> EvidenceRequest {
    EvidenceRequest::Query {
        edge,
        observer,
        view,
    }
}
fn envelope(value: &Value, expected_binding: &str, cp: &Value, arm: &str, observer: &Observer) {
    keys(
        value,
        &[
            "version",
            "binding",
            "row",
            "scope",
            "before_head",
            "after_head",
            "observer",
            "edge",
            "read_only",
            "generation_grant",
            "body",
        ],
    );
    assert_eq!(value["version"], 1);
    assert_eq!(value["binding"], expected_binding);
    assert_eq!(
        value["row"],
        json!({"turn": cp["request"]["turn"], "arm": arm})
    );
    assert_eq!(value["scope"], cp["request"]["scope"]);
    assert_eq!(value["before_head"], cp["before_head"]);
    assert_eq!(value["after_head"], cp["after_head"]);
    assert_eq!(value["observer"], serde_json::to_value(observer).unwrap());
    assert_eq!(value["read_only"], true);
    assert_eq!(value["generation_grant"], false);
    assert!(encode(value).unwrap().len() <= 256 * 1024);
}

#[test]
fn actual_selected_summary_and_query2_edges_keep_actor_knowledge_and_every_file_unchanged() {
    let fixture = Fixture::new("summary-query");
    let files = inventory(&fixture.root);
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&opened, true).unwrap();
    safe_summary(&summary, &fixture, [true, true]);
    let binding = snapshot_binding(&summary);
    for (arm, name) in [(Arm::Left, "left"), (Arm::Right, "right")] {
        let cp = json_file(&fixture.cp(name));
        let full = fixture.full(name);
        let canon = full.canonical_bytes();
        let basis = full.accepted_history_basis().unwrap();
        let contexts = generation_contexts(&full);
        for (edge, edge_name, head) in [
            (Edge::Before, "before", cp["before_head"].as_u64().unwrap()),
            (Edge::After, "after", cp["after_head"].as_u64().unwrap()),
        ] {
            for observer in [
                Observer::Player,
                Observer::Character { id: "mira".into() },
                Observer::Character { id: "sable".into() },
            ] {
                for view in [View::History, View::Knowledge] {
                    let value = desktop_read::evidence(
                        &opened,
                        &binding,
                        arm,
                        query(edge, observer.clone(), view),
                        true,
                    )
                    .unwrap();
                    envelope(&value, &binding, &cp, name, &observer);
                    assert_eq!(value["edge"], edge_name);
                    assert_eq!(value["body"]["kind"], "query");
                    assert_eq!(
                        value["body"]["page"],
                        expected_page(&full, head, observer.clone(), view)
                    );
                    if matches!(&observer, Observer::Character { .. }) {
                        assert!(!value.to_string().contains(SECRET));
                    }
                    if view == View::History
                        && matches!(&observer, Observer::Character { id } if id == "mira")
                    {
                        assert!(value["body"]["page"].to_string().contains("amber stitch"));
                    }
                    if view == View::History
                        && matches!(&observer, Observer::Character { id } if id == "sable")
                    {
                        assert!(value["body"]["page"]["rows"].as_array().unwrap().is_empty());
                    }
                }
            }
        }
        for request in [
            EvidenceRequest::Receipt {
                observer: Observer::Omniscient,
            },
            EvidenceRequest::Capture {
                observer: Observer::Omniscient,
            },
            EvidenceRequest::Outputs {
                observer: Observer::Omniscient,
            },
        ] {
            let value = desktop_read::evidence(&opened, &binding, arm, request, true).unwrap();
            assert_ne!(value["body"]["kind"], "missing");
        }
        assert!(full.canonical_bytes() == canon && full.accepted_history_basis().unwrap() == basis);
        assert_eq!(generation_contexts(&fixture.full(name)), contexts);
    }
    drop(opened);
    assert!(inventory(&fixture.root) == files);
    let reopened = desktop_read::open_read_only(&fixture.target).unwrap();
    assert_eq!(desktop_read::summary(&reopened, true).unwrap(), summary);
    drop(reopened);
    assert_eq!(
        refused(selected::resume_selected(
            &fixture.target,
            &fixture.source,
            &binding,
            &Cancellation::default()
        )),
        "CheckpointMismatch"
    );
    assert!(inventory(&fixture.root) == files);
}

#[test]
fn native_grant_and_actor_raw_refusals_precede_invalid_binding_and_private_artifact_probes() {
    let fixture = Fixture::new("grant-priority");
    let mut expected = inventory(&fixture.root);
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let binding = snapshot_binding(&desktop_read::summary(&opened, true).unwrap());
    let cp = fixture.cp("right");
    fs::write(&cp, b"[").unwrap();
    expected.insert(
        cp.strip_prefix(&fixture.root).unwrap().to_owned(),
        Some(b"[".to_vec()),
    );
    assert_eq!(refused(desktop_read::summary(&opened, false)), "Forbidden");
    for observer in [
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Character { id: "sable".into() },
    ] {
        for supplied in [binding.as_str(), "invalid-binding"] {
            for request in [
                EvidenceRequest::Receipt {
                    observer: observer.clone(),
                },
                EvidenceRequest::Capture {
                    observer: observer.clone(),
                },
                EvidenceRequest::Outputs {
                    observer: observer.clone(),
                },
            ] {
                assert_eq!(
                    refused(desktop_read::evidence(
                        &opened,
                        supplied,
                        Arm::Left,
                        request,
                        true
                    )),
                    "Forbidden"
                );
            }
        }
    }
    assert_eq!(
        refused(desktop_read::evidence(
            &opened,
            "invalid-binding",
            Arm::Left,
            query(Edge::After, Observer::Omniscient, View::History),
            false
        )),
        "Forbidden"
    );
    refused(desktop_read::summary(&opened, true));
    refused(desktop_read::evidence(
        &opened,
        &binding,
        Arm::Left,
        query(Edge::After, Observer::Player, View::History),
        true,
    ));
    drop(opened);
    assert!(inventory(&fixture.root) == expected);
}

#[test]
fn missing_checkpoint_is_unavailable_and_query_observer_uses_only_actual_before_engine() {
    let fixture = Fixture::new("missing-checkpoint");
    let mut expected = inventory(&fixture.root);
    let cp = fixture.cp("left");
    assert!(expected
        .remove(cp.strip_prefix(&fixture.root).unwrap())
        .is_some());
    fs::remove_file(&cp).unwrap();
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&opened, true).unwrap();
    safe_summary(&summary, &fixture, [false, true]);
    let binding = snapshot_binding(&summary);
    for request in [
        query(Edge::Before, Observer::Player, View::History),
        EvidenceRequest::Receipt {
            observer: Observer::Omniscient,
        },
        EvidenceRequest::Capture {
            observer: Observer::Omniscient,
        },
        EvidenceRequest::Outputs {
            observer: Observer::Omniscient,
        },
    ] {
        let value = desktop_read::evidence(&opened, &binding, Arm::Left, request, true).unwrap();
        assert_eq!(
            value["body"],
            json!({"kind":"missing","reason":"checkpoint_unavailable"})
        );
    }
    assert_eq!(
        refused(desktop_read::evidence(
            &opened,
            &binding,
            Arm::Left,
            query(
                Edge::Before,
                Observer::Character {
                    id: "unknown-reader-actor".into()
                },
                View::Knowledge
            ),
            true
        )),
        "InspectionUnknownObserver"
    );
    drop(opened);
    assert!(inventory(&fixture.root) == expected);
    // With no actual DB, do not invent a seed Engine to infer actor eligibility.
    let database = fixture.target.join("left/synthetic.sqlite");
    assert!(expected
        .remove(database.strip_prefix(&fixture.root).unwrap())
        .is_some());
    fs::remove_file(database).unwrap();
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&opened, true).unwrap();
    let value = desktop_read::evidence(
        &opened,
        &snapshot_binding(&summary),
        Arm::Left,
        query(
            Edge::Before,
            Observer::Character {
                id: "unknown-reader-actor".into(),
            },
            View::Knowledge,
        ),
        true,
    )
    .unwrap();
    assert_eq!(value["body"]["reason"], "checkpoint_unavailable");
    drop(opened);
    assert!(inventory(&fixture.root) == expected);
}

#[test]
fn genuine_recovery_has_missing_capture_while_corrupt_required_capture_invalidates_all_reads() {
    let fixture = Fixture::new("recovered-capture");
    let source = inventory(&fixture.source);
    let before = [fixture.full("left"), fixture.full("right")];
    fs::remove_file(fixture.cp("left")).unwrap();
    // Fixture setup uses actual public recovery, never manually clears capture metadata.
    selected::resume_selected(
        &fixture.target,
        &fixture.source,
        &fixture.execution,
        &Cancellation::default(),
    )
    .unwrap();
    let recovered = json_file(&fixture.cp("left"));
    assert_eq!(recovered["row"]["recovered_without_checkpoint"], true);
    assert!(recovered["capture_file"].is_null());
    let files = inventory(&fixture.root);
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&opened, true).unwrap();
    safe_summary(&summary, &fixture, [true, true]);
    let value = desktop_read::evidence(
        &opened,
        &snapshot_binding(&summary),
        Arm::Left,
        EvidenceRequest::Capture {
            observer: Observer::Omniscient,
        },
        true,
    )
    .unwrap();
    assert_eq!(
        value["body"],
        json!({"kind":"missing","reason":"capture_unavailable"})
    );
    drop(opened);
    assert!(inventory(&fixture.root) == files && inventory(&fixture.source) == source);
    for (index, arm) in ["left", "right"].into_iter().enumerate() {
        assert!(fixture.full(arm).receipts() == before[index].receipts());
        assert!(
            fixture.full(arm).accepted_history_basis().unwrap()
                == before[index].accepted_history_basis().unwrap()
        );
    }
    let fixture = Fixture::new("required-capture-corrupt");
    let mut expected = inventory(&fixture.root);
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let binding = snapshot_binding(&desktop_read::summary(&opened, true).unwrap());
    let cp = json_file(&fixture.cp("right"));
    let capture = fixture
        .target
        .join("right")
        .join(cp["capture_file"].as_str().unwrap());
    let mut changed = json_file(&capture);
    changed["status"] = json!("rejected");
    let changed = encode(&changed).unwrap();
    fs::write(&capture, &changed).unwrap();
    expected.insert(
        capture.strip_prefix(&fixture.root).unwrap().to_owned(),
        Some(changed),
    );
    refused(desktop_read::summary(&opened, true));
    refused(desktop_read::evidence(
        &opened,
        &binding,
        Arm::Left,
        query(Edge::After, Observer::Player, View::History),
        true,
    ));
    drop(opened);
    assert!(inventory(&fixture.root) == expected);
}

#[test]
fn reader_lock_excludes_open_and_resume_and_other_arm_valid_drift_invalidates_entire_snapshot() {
    let fixture = Fixture::new("lock-and-drift");
    let files = inventory(&fixture.root);
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let binding = snapshot_binding(&desktop_read::summary(&opened, true).unwrap());
    assert_eq!(
        refused(desktop_read::open_read_only(&fixture.target)),
        "RunBusy"
    );
    assert_eq!(
        refused(selected::resume_selected(
            &fixture.target,
            &fixture.source,
            &fixture.execution,
            &Cancellation::default()
        )),
        "RunBusy"
    );
    drop(opened);
    assert!(inventory(&fixture.root) == files);
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let mut cp = json_file(&fixture.cp("right"));
    let elapsed = cp["row"]["elapsed_ms"].as_u64().unwrap();
    let admission = cp["row"]["admission"].as_u64().unwrap();
    let settlement_path = fixture
        .target
        .join("right")
        .join(format!("admission-{admission:02}-settled.json"));
    let mut settlement = json_file(&settlement_path);
    assert_eq!(settlement["ms"].as_u64(), Some(elapsed));
    // Coordinated synthetic diagnostic drift remains valid under load_turn's
    // actual checkpoint/settlement agreement; this is not measured new work.
    cp["row"]["elapsed_ms"] = json!(elapsed.checked_add(1).unwrap());
    settlement["ms"] = cp["row"]["elapsed_ms"].clone();
    let bytes = encode(&cp).unwrap();
    fs::write(fixture.cp("right"), &bytes).unwrap();
    let settlement_bytes = encode(&settlement).unwrap();
    fs::write(&settlement_path, &settlement_bytes).unwrap();
    let mut expected = files;
    expected.insert(
        fixture
            .cp("right")
            .strip_prefix(&fixture.root)
            .unwrap()
            .to_owned(),
        Some(bytes),
    );
    expected.insert(
        settlement_path
            .strip_prefix(&fixture.root)
            .unwrap()
            .to_owned(),
        Some(settlement_bytes),
    );
    assert_eq!(
        refused(desktop_read::summary(&opened, true)),
        "SnapshotMismatch"
    );
    assert_eq!(
        refused(desktop_read::evidence(
            &opened,
            &binding,
            Arm::Left,
            query(
                Edge::Before,
                Observer::Character { id: "mira".into() },
                View::History
            ),
            true
        )),
        "SnapshotMismatch"
    );
    drop(opened);
    assert!(inventory(&fixture.root) == expected);
    // A fresh cap can bind the new valid diagnostics. Old cap never silently rebinds.
    let fresh = desktop_read::open_read_only(&fixture.target).unwrap();
    assert_ne!(
        desktop_read::summary(&fresh, true).unwrap()["binding"],
        binding
    );
    drop(fresh);
    assert!(inventory(&fixture.root) == expected);
}

#[test]
fn offsetting_genuine_invocation_settlements_change_snapshot_even_when_report_and_charges_match() {
    let fixture = Fixture::new("accounting-seal");
    let source_files = inventory(&fixture.source);
    let canonical = [fixture.full("left"), fixture.full("right")];
    // Produce a second real invocation through the existing model-free recovery.
    fs::remove_file(fixture.cp("left")).unwrap();
    selected::resume_selected(&fixture.target, &fixture.source, &fixture.execution,
        &Cancellation::default()).unwrap();
    let manifest: selected::SelectedManifest = comparison::decode(
        &fixture.target.join("selected.json"), 128 * 1024).unwrap();
    let private_report = || {
        // Unit-test-only access avoids trying to acquire a second run lock.
        let turns = selected::validate_destination(&fixture.target, &manifest, None).unwrap();
        let ledgers = selected::ledgers(&fixture.target, &manifest.binding).unwrap();
        serde_json::to_value(selected::report(&fixture.target, &manifest, &turns, &ledgers).unwrap()).unwrap()
    };
    let before_report = private_report();
    let mut expected = inventory(&fixture.root);
    let paths = [fixture.target.join("left/invocation-00-settled.json"),
        fixture.target.join("left/invocation-01-settled.json")];
    assert!(paths.iter().all(|path| path.is_file()), "two actual completed invocation settlements required");
    let mut settlements = [json_file(&paths[0]), json_file(&paths[1])];
    for (index, settlement) in settlements.iter().enumerate() {
        assert_eq!(settlement["index"], index);
        assert_eq!(settlement["binding"], fixture.execution);
        assert_eq!(settlement["roles"], 0);
    }
    let original = [settlements[0]["ms"].as_u64().unwrap(), settlements[1]["ms"].as_u64().unwrap()];
    let debit = original.iter().position(|ms| *ms > 0)
        .expect("actual measured invocation overhead supplies a positive debit");
    let credit = 1 - debit;
    settlements[debit]["ms"] = json!(original[debit] - 1);
    settlements[credit]["ms"] = json!(original[credit].checked_add(1).unwrap());
    assert_eq!(settlements[0]["ms"].as_u64().unwrap() + settlements[1]["ms"].as_u64().unwrap(),
        original[0] + original[1]);
    let opened = desktop_read::open_read_only(&fixture.target).unwrap();
    let old_binding = snapshot_binding(&desktop_read::summary(&opened, true).unwrap());
    for (path, settlement) in paths.iter().zip(&settlements) {
        // Synthetic offset of existing diagnostics only; no invented reservations,
        // measured-work claim, checkpoint change or canonical rewrite.
        let bytes = encode(settlement).unwrap(); fs::write(path, &bytes).unwrap();
        assert!(expected.insert(path.strip_prefix(&fixture.root).unwrap().to_owned(), Some(bytes)).is_some());
    }
    assert_eq!(private_report(), before_report, "aggregate/report equality must not bypass exact accounting seal");
    assert_eq!(refused(desktop_read::summary(&opened, true)), "SnapshotMismatch");
    assert_eq!(refused(desktop_read::evidence(&opened, &old_binding, Arm::Right,
        query(Edge::After, Observer::Character { id: "mira".into() }, View::History), true)), "SnapshotMismatch");
    drop(opened);
    assert!(inventory(&fixture.root) == expected);
    let fresh = desktop_read::open_read_only(&fixture.target).unwrap();
    assert_ne!(desktop_read::summary(&fresh, true).unwrap()["binding"], old_binding);
    drop(fresh);
    assert!(inventory(&fixture.root) == expected && inventory(&fixture.source) == source_files);
    for (index, arm) in ["left", "right"].into_iter().enumerate() {
        let after = fixture.full(arm);
        assert!(after.receipts() == canonical[index].receipts());
        assert!(after.accepted_history_basis().unwrap() == canonical[index].accepted_history_basis().unwrap());
    }
}
