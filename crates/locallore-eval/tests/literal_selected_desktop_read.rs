// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE-ONLY / UNCOMPILED / UNRUN public selected2 reader oracles.
//! Actual scripted V3/selected producers, Store/Core queries and diagnostic-only
//! hostile copies. No model, native IPC, renderer, forged history or SQL writer.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --test literal_selected_desktop_read -- --nocapture --test-threads=1
use locallore::{
    engine::Engine,
    inference::Cancellation,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
use locallore_eval::{
    local_lane::{
        comparison::{
            self,
            desktop_api::{self as common, Arm, Edge, EvidenceRequest},
            literal_v3::{
                self, desktop_api as source_read,
                selected_v2::{self, desktop_read},
            },
            selected::{self as selected1, desktop_read as read1},
            ComparisonKind,
        },
        LaneFactory,
    },
    memory_comparison::frozen_suite,
    memory_comparison_v3::arm_descriptors,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        OnceLock,
    },
};

const INDEX: usize = 4;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
static NEXT: AtomicU64 = AtomicU64::new(0);
fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "literal-selected-read-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&path).unwrap();
    path
}
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
                let bytes = fs::read(path).unwrap();
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
fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn refused<T>(result: Result<T, String>) -> String {
    match result {
        Ok(_) => panic!("expected closed selected reader refusal"),
        Err(error) => {
            assert!(!error.is_empty() && error.len() <= 96);
            assert!(error
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'_'));
            error
        }
    }
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
fn template() -> &'static Path {
    static TEMPLATE: OnceLock<PathBuf> = OnceLock::new();
    TEMPLATE
        .get_or_init(|| {
            let root = root("actual-producers");
            let source = root.join("source");
            let report = literal_v3::run_comparison(
                &source,
                false,
                ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
            assert!(report.turns.iter().all(|row| row.passed));
            let cap = source_read::open_read_only(&source).unwrap();
            let binding = source_read::summary(&cap, true).unwrap()["binding"]
                .as_str()
                .unwrap()
                .to_owned();
            drop(cap);
            let corpus = frozen_suite().unwrap();
            assert_eq!(corpus.steps()[INDEX].text(), "I move to pier.");
            let plan = selected_v2::prepare_selected(
                &source,
                &binding,
                &common::RowId {
                    turn: corpus.steps()[INDEX].id().into(),
                    arm: Arm::Left,
                },
                selected1::SelectedIntent {
                    client_id: "literal-selected-read".into(),
                    lane: selected1::SelectedLane::ScriptedBaseline,
                },
                &Cancellation::default(),
            )
            .unwrap();
            let selected = serde_json::to_value(
                selected_v2::run_selected(plan, &root.join("selected"), &Cancellation::default())
                    .unwrap(),
            )
            .unwrap();
            assert_eq!(selected["version"], 2);
            assert_eq!(selected["source_protocol_version"], 3);
            assert_eq!(selected["completed"], true);
            assert!(selected["rows"]
                .as_array()
                .unwrap()
                .iter()
                .all(|row| row["passed"] == true));
            root
        })
        .as_path()
}
struct Fixture {
    root: PathBuf,
    source: PathBuf,
    target: PathBuf,
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
        Self {
            source: root.join("source"),
            target: root.join("selected"),
            root,
        }
    }
    fn cp(&self, arm: &str) -> PathBuf {
        self.target
            .join(arm)
            .join(format!("attempt-{INDEX:02}.json"))
    }
    fn full(&self, arm: &str) -> Engine {
        let mut store =
            Store::open_read_only(&self.target.join(arm).join("synthetic.sqlite")).unwrap();
        store
            .resume(&frozen_suite().unwrap().seed().scope)
            .unwrap()
            .engine
    }
    fn report(&self) -> Value {
        serde_json::to_value(selected_v2::inspect_selected(&self.target).unwrap()).unwrap()
    }
}
fn binding(summary: &Value) -> &str {
    let binding = summary["binding"].as_str().unwrap();
    assert!(binding.len() == 64 && binding.bytes().all(|b| b.is_ascii_hexdigit()));
    binding
}
fn contexts(full: &Engine) -> Value {
    json!([
        full.character_context(&full.seed().player, full.scope(), full.revision())
            .unwrap(),
        full.character_context("mira", full.scope(), full.revision())
            .unwrap(),
        full.character_context("sable", full.scope(), full.revision())
            .unwrap()
    ])
}
fn no_private(value: &Value, root: &Path) {
    match value {
        Value::Object(fields) => {
            for (key, value) in fields {
                assert!(![
                    "report",
                    "request",
                    "source_inputs",
                    "source_binding",
                    "profile",
                    "source_profile",
                    "trace",
                    "capture",
                    "outputs",
                    "raw",
                    "narration",
                    "text",
                    "path"
                ]
                .contains(&key.as_str()));
                no_private(value, root);
            }
        }
        Value::Array(values) => {
            for value in values {
                no_private(value, root);
            }
        }
        Value::String(value) => {
            assert!(!value.contains("SECRET-TIDE-731") && !value.contains("amber stitch"));
            assert!(!value.contains(root.to_str().unwrap()));
        }
        _ => {}
    }
}
fn envelope(reply: &Value, snapshot: &str, cp: &Value, arm: &str, observer: &Observer) {
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["binding"], snapshot);
    assert_eq!(
        reply["row"],
        json!({"turn":cp["request"]["turn"],"arm":arm})
    );
    assert_eq!(reply["scope"], cp["request"]["scope"]);
    assert_eq!(reply["before_head"], cp["before_head"]);
    assert_eq!(reply["after_head"], cp["after_head"]);
    assert_eq!(reply["observer"], serde_json::to_value(observer).unwrap());
    assert_eq!(reply["read_only"], true);
    assert_eq!(reply["generation_grant"], false);
    assert!(serde_json::to_vec(reply).unwrap().len() <= 256 * 1024);
}

#[test]
fn selected2_safe_metadata_lock_lifecycle_and_both_version_readers_remain_distinct() {
    let fixture = Fixture::new("safe-metadata");
    let files = inventory(&fixture.root);
    let report = fixture.report();
    let cap = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&cap, true).unwrap();
    keys(
        &summary,
        &[
            "version",
            "kind",
            "source_protocol_version",
            "constructions",
            "binding",
            "selection",
            "lane",
            "arms",
            "read_only",
            "execution_available",
        ],
    );
    assert_eq!(summary["version"], 2);
    assert_eq!(summary["kind"], "selected_read");
    assert_eq!(summary["source_protocol_version"], 3);
    assert_eq!(
        summary["constructions"],
        serde_json::to_value(arm_descriptors()).unwrap()
    );
    assert_eq!(summary["selection"], report["selection"]);
    assert_eq!(summary["lane"], "scripted_selected_case");
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    assert_ne!(binding(&summary), report["binding"].as_str().unwrap());
    assert_eq!(summary["arms"].as_array().unwrap().len(), 2);
    for (index, arm) in ["left", "right"].into_iter().enumerate() {
        let metadata = &summary["arms"][index];
        let cp = value(&fixture.cp(arm));
        keys(
            metadata,
            &["arm", "scope", "before_head", "after_head", "available"],
        );
        assert_eq!(metadata["arm"], arm);
        assert_eq!(metadata["scope"], report["source_inputs"][index]["scope"]);
        assert_eq!(metadata["before_head"], cp["before_head"]);
        assert_eq!(metadata["after_head"], cp["after_head"]);
        assert_eq!(metadata["available"], true);
    }
    no_private(&summary, &fixture.root);
    assert!(serde_json::to_vec(&summary).unwrap().len() <= 16 * 1024);
    assert_eq!(
        refused(desktop_read::open_read_only(&fixture.target)),
        "RunBusy"
    );
    assert_eq!(
        refused(selected_v2::resume_selected(
            &fixture.target,
            &fixture.source,
            report["binding"].as_str().unwrap(),
            &Cancellation::default()
        )),
        "RunBusy"
    );
    drop(cap);
    assert!(inventory(&fixture.root) == files);
    let reopened = desktop_read::open_read_only(&fixture.target).unwrap();
    assert_eq!(desktop_read::summary(&reopened, true).unwrap(), summary);
    drop(reopened);
    assert!(
        read1::open_read_only(&fixture.target).is_err(),
        "old cap must not reinterpret selected2"
    );
    assert!(inventory(&fixture.root) == files);

    // Genuine old selected1 output, never relabel a protocol-3 manifest/capture.
    let legacy = root("actual-selected1");
    let source = legacy.join("source");
    comparison::run_comparison(
        &source,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let cap = common::open_read_only(&source).unwrap();
    let source_binding = common::summary(&cap, true).unwrap()["binding"]
        .as_str()
        .unwrap()
        .to_owned();
    drop(cap);
    let plan = selected1::prepare_selected(
        &source,
        &source_binding,
        &common::RowId {
            turn: frozen_suite().unwrap().steps()[INDEX].id().into(),
            arm: Arm::Left,
        },
        selected1::SelectedIntent {
            client_id: "legacy-selected-read-control".into(),
            lane: selected1::SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    )
    .unwrap();
    selected1::run_selected(plan, &legacy.join("selected"), &Cancellation::default()).unwrap();
    let legacy_files = inventory(&legacy);
    assert!(
        desktop_read::open_read_only(&legacy.join("selected")).is_err(),
        "new cap must reject selected1"
    );
    let old = read1::open_read_only(&legacy.join("selected")).unwrap();
    assert_eq!(read1::summary(&old, true).unwrap()["version"], 1);
    drop(old);
    assert!(inventory(&legacy) == legacy_files);
}

#[test]
fn query2_before_after_player_mira_sable_matches_real_store_without_changing_generation_contexts() {
    let fixture = Fixture::new("actual-observers");
    let files = inventory(&fixture.root);
    let cap = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&cap, true).unwrap();
    for (arm, name) in [(Arm::Left, "left"), (Arm::Right, "right")] {
        let cp = value(&fixture.cp(name));
        let full = fixture.full(name);
        let canon = full.canonical_bytes();
        let basis = full.accepted_history_basis().unwrap();
        let generation = contexts(&full);
        for (edge, edge_name, head) in [
            (Edge::Before, "before", "before_head"),
            (Edge::After, "after", "after_head"),
        ] {
            let cut = full.at_revision(cp[head].as_u64().unwrap()).unwrap();
            for observer in [
                Observer::Player,
                Observer::Character { id: "mira".into() },
                Observer::Character { id: "sable".into() },
            ] {
                for view in [View::History, View::Knowledge] {
                    let expected = inspection_query::query(
                        &cut,
                        &Query {
                            version: 2,
                            scope: cut.scope().clone(),
                            expected_head: cut.revision(),
                            at_revision: None,
                            observer: observer.clone(),
                            view,
                            cursor: None,
                            limit: MAX_ROWS,
                            search: String::new(),
                        },
                        true,
                    )
                    .unwrap();
                    let reply = desktop_read::evidence(
                        &cap,
                        binding(&summary),
                        arm,
                        EvidenceRequest::Query {
                            edge,
                            observer: observer.clone(),
                            view,
                        },
                        true,
                    )
                    .unwrap();
                    envelope(&reply, binding(&summary), &cp, name, &observer);
                    assert_eq!(reply["edge"], edge_name);
                    assert_eq!(reply["body"]["kind"], "query");
                    assert_eq!(
                        reply["body"]["page"],
                        serde_json::to_value(expected).unwrap()
                    );
                    if let Observer::Character { id } = &observer {
                        assert!(!reply.to_string().contains("SECRET-TIDE-731"));
                        if view == View::History {
                            assert_eq!(
                                reply["body"]["page"].to_string().contains("amber stitch"),
                                id == "mira"
                            );
                        }
                    }
                }
            }
        }
        let after = fixture.full(name);
        assert!(
            after.canonical_bytes() == canon && after.accepted_history_basis().unwrap() == basis
        );
        assert!(after.receipts() == full.receipts());
        assert_eq!(contexts(&after), generation);
    }
    drop(cap);
    assert!(inventory(&fixture.root) == files);
}

#[test]
fn omniscient_receipt_capture_outputs_and_manual_diagnostics_match_actual_selected_records() {
    let fixture = Fixture::new("actual-raw-diagnostics");
    let files = inventory(&fixture.root);
    let report = fixture.report();
    let canonical = [fixture.full("left"), fixture.full("right")];
    let generation = [contexts(&canonical[0]), contexts(&canonical[1])];
    let cap = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&cap, true).unwrap();
    for (arm, name) in [(Arm::Left, "left"), (Arm::Right, "right")] {
        let cp = value(&fixture.cp(name));
        let mut store =
            Store::open_read_only(&fixture.target.join(name).join("synthetic.sqlite")).unwrap();
        let receipt = serde_json::to_value(
            store
                .lookup_turn(
                    &frozen_suite().unwrap().seed().scope,
                    cp["request"]["turn"].as_str().unwrap(),
                )
                .unwrap()
                .receipt
                .unwrap(),
        )
        .unwrap();
        drop(store);
        let capture = value(
            &fixture
                .target
                .join(name)
                .join(cp["capture_file"].as_str().unwrap()),
        );
        let recording = value(
            &fixture
                .target
                .join(name)
                .join(cp["recording_file"].as_str().unwrap()),
        );
        let outputs: Vec<Value> = recording["raw"].as_array().unwrap().iter().map(|raw| {
            let bytes = fs::read(fixture.target.join(name).join(raw["file"].as_str().unwrap())).unwrap();
            json!({"role":raw["role"],"bytes":raw["bytes"],"sha256":raw["sha256"],"text":String::from_utf8(bytes).unwrap()})
        }).collect();
        for (request, kind, expected) in [
            (
                EvidenceRequest::Receipt {
                    observer: Observer::Omniscient,
                },
                "receipt",
                receipt,
            ),
            (
                EvidenceRequest::Capture {
                    observer: Observer::Omniscient,
                },
                "capture",
                capture,
            ),
            (
                EvidenceRequest::Outputs {
                    observer: Observer::Omniscient,
                },
                "outputs",
                json!(outputs),
            ),
        ] {
            let reply =
                desktop_read::evidence(&cap, binding(&summary), arm, request, true).unwrap();
            envelope(&reply, binding(&summary), &cp, name, &Observer::Omniscient);
            assert_eq!(reply["body"]["kind"], kind);
            assert_eq!(reply["body"][kind], expected);
        }
    }
    let diagnostics =
        desktop_read::diagnostics(&cap, binding(&summary), Observer::Omniscient, true).unwrap();
    assert_eq!(diagnostics["version"], 2);
    assert_eq!(diagnostics["kind"], "selected_diagnostics");
    assert_eq!(diagnostics["source_protocol_version"], 3);
    assert_eq!(
        diagnostics["constructions"],
        serde_json::to_value(arm_descriptors()).unwrap()
    );
    assert_eq!(diagnostics["binding"], binding(&summary));
    for field in [
        "lane",
        "completed",
        "physical_setups",
        "physical_setup_ms",
        "left_charged_ms",
        "right_charged_ms",
        "left_reserved_roles",
        "right_reserved_roles",
        "human_reviewed",
        "quality_accepted",
    ] {
        assert!(diagnostics.get(field).is_some());
        assert_eq!(diagnostics[field], report[field]);
    }
    assert_eq!(diagnostics["human_reviewed"], 0);
    assert_eq!(diagnostics["quality_accepted"], false);
    assert_eq!(diagnostics["rows"].as_array().unwrap().len(), 2);
    for (index, row) in diagnostics["rows"].as_array().unwrap().iter().enumerate() {
        for field in [
            "turn",
            "arm",
            "phase",
            "error",
            "expected",
            "passed",
            "failures",
            "quality_flags",
            "roles",
            "roles_known",
            "elapsed_ms",
            "actual_receipt_sha256",
            "privacy_passed",
            "context_evidence_available",
            "construction",
            "construction_evidence_status",
            "construction_matches",
            "literal_source_units",
            "literal_selected_start",
            "literal_selected_units",
            "fallback",
        ] {
            assert!(
                row.get(field).is_some(),
                "required diagnostic field {field}"
            );
            assert_eq!(row[field], report["rows"][index][field]);
        }
        assert_eq!(
            row["construction"],
            serde_json::to_value(&arm_descriptors()[index]).unwrap()
        );
    }
    no_private(&diagnostics, &fixture.root);
    assert!(serde_json::to_vec(&diagnostics).unwrap().len() <= 256 * 1024);
    drop(cap);
    for (index, arm) in ["left", "right"].into_iter().enumerate() {
        let after = fixture.full(arm);
        assert!(after.canonical_bytes() == canonical[index].canonical_bytes());
        assert!(after.receipts() == canonical[index].receipts());
        assert!(
            after.accepted_history_basis().unwrap()
                == canonical[index].accepted_history_basis().unwrap()
        );
        assert_eq!(contexts(&after), generation[index]);
    }
    assert!(inventory(&fixture.root) == files);
}

#[test]
fn grant_and_actor_raw_denials_precede_wrong_binding_and_poisoned_manifest_probes() {
    let fixture = Fixture::new("access-priority");
    let mut expected = inventory(&fixture.root);
    let cap = desktop_read::open_read_only(&fixture.target).unwrap();
    let summary = desktop_read::summary(&cap, true).unwrap();
    let snapshot = binding(&summary).to_owned();
    for poisoned in [false, true] {
        if poisoned {
            let path = fixture.target.join("selected.json");
            let bytes = b"[".to_vec();
            fs::write(&path, &bytes).unwrap();
            expected.insert(
                path.strip_prefix(&fixture.root).unwrap().to_owned(),
                Some(bytes),
            );
        }
        assert_eq!(refused(desktop_read::summary(&cap, false)), "Forbidden");
        for supplied in [&snapshot[..], "invalid-binding"] {
            for observer in [
                Observer::Player,
                Observer::Character { id: "mira".into() },
                Observer::Character { id: "sable".into() },
            ] {
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
                            &cap,
                            supplied,
                            Arm::Left,
                            request,
                            true
                        )),
                        "Forbidden"
                    );
                }
                assert_eq!(
                    refused(desktop_read::diagnostics(&cap, supplied, observer, true)),
                    "Forbidden"
                );
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
                EvidenceRequest::Query {
                    edge: Edge::Before,
                    observer: Observer::Player,
                    view: View::History,
                },
            ] {
                assert_eq!(
                    refused(desktop_read::evidence(
                        &cap,
                        supplied,
                        Arm::Right,
                        request,
                        false
                    )),
                    "Forbidden"
                );
            }
            assert_eq!(
                refused(desktop_read::diagnostics(
                    &cap,
                    supplied,
                    Observer::Omniscient,
                    false
                )),
                "Forbidden"
            );
        }
    }
    assert!(desktop_read::summary(&cap, true).is_err());
    assert!(desktop_read::evidence(
        &cap,
        &snapshot,
        Arm::Left,
        EvidenceRequest::Receipt {
            observer: Observer::Omniscient
        },
        true
    )
    .is_err());
    assert!(desktop_read::diagnostics(&cap, &snapshot, Observer::Omniscient, true).is_err());
    drop(cap);
    assert!(inventory(&fixture.root) == expected);
}

#[test]
fn coherent_other_arm_diagnostic_drift_invalidates_all_old_cap_reads_without_touching_canon() {
    let fixture = Fixture::new("whole-cap-drift");
    let source_files = inventory(&fixture.source);
    let mut expected = inventory(&fixture.root);
    let canon = [fixture.full("left"), fixture.full("right")];
    let cap = desktop_read::open_read_only(&fixture.target).unwrap();
    let old = desktop_read::summary(&cap, true).unwrap();
    let snapshot = binding(&old).to_owned();
    let cp_path = fixture.cp("right");
    let mut cp = value(&cp_path);
    let admission = cp["row"]["admission"].as_u64().unwrap();
    let settlement_path = fixture
        .target
        .join("right")
        .join(format!("admission-{admission:02}-settled.json"));
    let mut settlement = value(&settlement_path);
    let elapsed = cp["row"]["elapsed_ms"].as_u64().unwrap();
    assert_eq!(settlement["ms"].as_u64(), Some(elapsed));
    // Hostile synthetic diagnostics only, no new measured work or history.
    // Preserve the actual checkpoint/settlement agreement to reach the seal.
    cp["row"]["elapsed_ms"] = json!(elapsed.checked_add(1).unwrap());
    settlement["ms"] = cp["row"]["elapsed_ms"].clone();
    for (path, diagnostic) in [(&cp_path, &cp), (&settlement_path, &settlement)] {
        let bytes = serde_json::to_vec(diagnostic).unwrap();
        fs::write(path, &bytes).unwrap();
        assert!(expected
            .insert(
                path.strip_prefix(&fixture.root).unwrap().to_owned(),
                Some(bytes)
            )
            .is_some());
    }
    assert_eq!(
        refused(desktop_read::summary(&cap, true)),
        "SnapshotMismatch"
    );
    assert_eq!(
        refused(desktop_read::evidence(
            &cap,
            &snapshot,
            Arm::Left,
            EvidenceRequest::Receipt {
                observer: Observer::Omniscient
            },
            true
        )),
        "SnapshotMismatch"
    );
    assert_eq!(
        refused(desktop_read::diagnostics(
            &cap,
            &snapshot,
            Observer::Omniscient,
            true
        )),
        "SnapshotMismatch"
    );
    drop(cap);
    assert!(inventory(&fixture.root) == expected);
    let fresh = desktop_read::open_read_only(&fixture.target).unwrap();
    assert_ne!(
        binding(&desktop_read::summary(&fresh, true).unwrap()),
        snapshot
    );
    drop(fresh);
    assert!(inventory(&fixture.root) == expected && inventory(&fixture.source) == source_files);
    for (index, arm) in ["left", "right"].into_iter().enumerate() {
        let after = fixture.full(arm);
        assert!(after.receipts() == canon[index].receipts());
        assert!(after.canonical_bytes() == canon[index].canonical_bytes());
        assert!(
            after.accepted_history_basis().unwrap()
                == canon[index].accepted_history_basis().unwrap()
        );
        assert_eq!(contexts(&after), contexts(&canon[index]));
    }
}
