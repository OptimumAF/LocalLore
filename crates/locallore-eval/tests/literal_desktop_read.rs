// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Actual scripted V3 producer and
//! Store/Core queries; no model, native IPC, renderer or authenticated-origin claim.
use locallore::{
    inference::Cancellation,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
use locallore_eval::{
    local_lane::{
        comparison::{
            desktop_api as v2,
            literal_v3::{self, desktop_api as v3},
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
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        OnceLock,
    },
};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
static NEXT: AtomicU64 = AtomicU64::new(0);
fn root() -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "literal-desktop-read-{}-{}-{}",
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
    let mut out = Inventory::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}
fn fixture() -> PathBuf {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    let source = SOURCE.get_or_init(|| {
        let dir = root().join("run");
        let report = literal_v3::run_comparison(
            &dir,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!(report.turns.len(), 12);
        assert!(report.turns.iter().all(|row| row.passed));
        assert!(!report.completed);
        dir
    });
    let captured = inventory(source); // Producer returned; no retained reader lock.
    let copy = root().join("run");
    fs::create_dir(&copy).unwrap();
    for (path, value) in &captured {
        match value {
            None => fs::create_dir_all(copy.join(path)).unwrap(),
            Some(bytes) => fs::write(copy.join(path), bytes).unwrap(),
        }
    }
    assert!(inventory(&copy) == captured);
    copy
}
fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn row(turn: &str, arm: v2::Arm) -> v2::RowId {
    v2::RowId {
        turn: turn.into(),
        arm,
    }
}
fn binding(summary: &Value) -> &str {
    summary["binding"].as_str().unwrap()
}
fn refused<T>(result: Result<T, String>) -> String {
    match result {
        Err(error) => error,
        Ok(_) => panic!("expected closed read refusal"),
    }
}

#[test]
fn actual_v3_summary_is_versioned_read_only_and_not_a_v2_report() {
    let dir = fixture();
    let before = inventory(&dir);
    let expected = serde_json::to_value(literal_v3::inspect_comparison(&dir).unwrap()).unwrap();
    let cap = v3::open_read_only(&dir).unwrap();
    assert_eq!(refused(v3::summary(&cap, false)), "Forbidden");
    let summary = v3::summary(&cap, true).unwrap();
    assert_eq!(summary["version"], 1);
    assert_eq!(summary["protocol_version"], 3);
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    assert_eq!(summary["report"], expected);
    assert_eq!(summary["report"]["version"], 3);
    assert_eq!(
        summary["report"]["arms"],
        serde_json::to_value(arm_descriptors()).unwrap()
    );
    assert_eq!(summary["report"]["human_reviewed"], 0);
    assert_eq!(summary["report"]["quality_accepted"], false);
    assert_eq!(summary["rows"].as_array().unwrap().len(), 12);
    assert_eq!(summary["report"]["turns"].as_array().unwrap().len(), 12);
    for turn in summary["report"]["turns"].as_array().unwrap() {
        assert!(turn.get("policy").is_none());
        if turn["arm"] == "left" {
            for key in [
                "mandatory_sha256",
                "optional_detail_selected",
                "selected_context_bytes",
                "estimated_context_tokens",
                "source_fallback_reason",
                "compiler_fallback_reason",
            ] {
                assert!(
                    turn[key].is_null(),
                    "literal row invented memory metric {key}"
                );
            }
            assert!(turn["literal_source_units"].is_u64());
            assert!(turn["literal_selected_units"].is_u64());
        }
    }
    drop(cap);
    assert!(
        v2::open_read_only(&dir).is_err(),
        "V2 reader must not reinterpret protocol3"
    );
    assert!(inventory(&dir) == before);
}

#[test]
fn actual_receipt_capture_outputs_and_observer_query_edges_are_bound_to_store() {
    let dir = fixture();
    let before = inventory(&dir);
    let corpus = frozen_suite().unwrap();
    for (name, arm) in [("left", v2::Arm::Left), ("right", v2::Arm::Right)] {
        let cp = value(&dir.join(name).join("attempt-01.json"));
        let store = Store::open_read_only(&dir.join(name).join("synthetic.sqlite")).unwrap();
        let full = store.resume(&corpus.seed().scope).unwrap().engine;
        let receipt = serde_json::to_value(
            store
                .lookup_turn(&corpus.seed().scope, "courier-02")
                .unwrap()
                .receipt
                .unwrap(),
        )
        .unwrap();
        drop(store);
        let capture = value(&dir.join(name).join(cp["capture_file"].as_str().unwrap()));
        let recording = value(&dir.join(name).join(cp["recording_file"].as_str().unwrap()));
        let outputs: Vec<Value> = recording["raw"].as_array().unwrap().iter().map(|raw| {
            let bytes = fs::read(dir.join(name).join(raw["file"].as_str().unwrap())).unwrap();
            json!({"role":raw["role"],"bytes":raw["bytes"],"sha256":raw["sha256"],"text":String::from_utf8(bytes).unwrap()})
        }).collect();
        let cap = v3::open_read_only(&dir).unwrap();
        let summary = v3::summary(&cap, true).unwrap();
        let id = row("courier-02", arm);
        for (request, expected_kind, expected_value) in [
            (
                v2::EvidenceRequest::Receipt {
                    observer: Observer::Omniscient,
                },
                "receipt",
                receipt,
            ),
            (
                v2::EvidenceRequest::Capture {
                    observer: Observer::Omniscient,
                },
                "capture",
                capture,
            ),
            (
                v2::EvidenceRequest::Outputs {
                    observer: Observer::Omniscient,
                },
                "outputs",
                json!(outputs),
            ),
        ] {
            let reply = v3::evidence(&cap, binding(&summary), &id, request, true).unwrap();
            assert_eq!(reply["body"]["kind"], expected_kind);
            assert_eq!(reply["body"][expected_kind], expected_value);
            assert_eq!(reply["read_only"], true);
            assert_eq!(reply["generation_grant"], false);
        }
        for (edge, head_key) in [
            (v2::Edge::Before, "before_head"),
            (v2::Edge::After, "after_head"),
        ] {
            let cut = full.at_revision(cp[head_key].as_u64().unwrap()).unwrap();
            for observer in [
                Observer::Player,
                Observer::Character { id: "mira".into() },
                Observer::Character { id: "sable".into() },
            ] {
                let expected = inspection_query::query(
                    &cut,
                    &Query {
                        version: 2,
                        scope: cut.scope().clone(),
                        expected_head: cut.revision(),
                        at_revision: None,
                        observer: observer.clone(),
                        view: View::History,
                        cursor: None,
                        limit: MAX_ROWS,
                        search: String::new(),
                    },
                    true,
                )
                .unwrap();
                let reply = v3::evidence(
                    &cap,
                    binding(&summary),
                    &id,
                    v2::EvidenceRequest::Query {
                        edge,
                        observer: observer.clone(),
                        view: View::History,
                    },
                    true,
                )
                .unwrap();
                assert_eq!(
                    reply["body"]["page"],
                    serde_json::to_value(expected).unwrap()
                );
                let text = reply["body"]["page"].to_string();
                if let Observer::Character { id } = observer {
                    assert!(!text.contains("SECRET-TIDE-731"));
                    assert_eq!(text.contains("amber stitch"), id == "mira");
                }
            }
        }
        drop(cap);
    }
    assert!(inventory(&dir) == before);
}

#[test]
fn actor_raw_denials_precede_bad_identity_and_corrupt_manifest_probe() {
    let dir = fixture();
    let mut expected = inventory(&dir);
    let cap = v3::open_read_only(&dir).unwrap();
    // Deliberate fixture fault after valid open. Access denial must occur before
    // this corruption or deliberately invalid binding/row can become an oracle.
    let broken = b"not a manifest".to_vec();
    fs::write(dir.join("run.json"), &broken).unwrap();
    expected.insert(PathBuf::from("run.json"), Some(broken));
    let unknown = row("unknown-row", v2::Arm::Left);
    for observer in [
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Character { id: "sable".into() },
    ] {
        for request in [
            v2::EvidenceRequest::Receipt {
                observer: observer.clone(),
            },
            v2::EvidenceRequest::Capture {
                observer: observer.clone(),
            },
            v2::EvidenceRequest::Outputs { observer },
        ] {
            assert_eq!(
                refused(v3::evidence(&cap, "not-a-binding", &unknown, request, true)),
                "Forbidden"
            );
        }
    }
    assert_eq!(
        refused(v3::evidence(
            &cap,
            "not-a-binding",
            &unknown,
            v2::EvidenceRequest::Query {
                edge: v2::Edge::After,
                observer: Observer::Omniscient,
                view: View::History
            },
            false
        )),
        "Forbidden"
    );
    drop(cap);
    assert!(inventory(&dir) == expected);
}

#[test]
fn bound_manifest_or_checkpoint_mutation_is_refused_without_repair_or_writes() {
    for checkpoint in [false, true] {
        let dir = fixture();
        let mut expected = inventory(&dir);
        let cap = v3::open_read_only(&dir).unwrap();
        let summary = v3::summary(&cap, true).unwrap();
        let relative = if checkpoint {
            "left/attempt-01.json"
        } else {
            "run.json"
        };
        let mut actual = value(&dir.join(relative));
        if checkpoint {
            let elapsed = actual["row"]["elapsed_ms"].as_u64().unwrap();
            actual["row"]["elapsed_ms"] = json!(elapsed.checked_add(1).unwrap());
        } else {
            actual["order"] = json!("foreign-order");
        }
        let changed = serde_json::to_vec(&actual).unwrap();
        fs::write(dir.join(relative), &changed).unwrap();
        expected.insert(PathBuf::from(relative), Some(changed));
        let result = v3::evidence(
            &cap,
            binding(&summary),
            &row("courier-02", v2::Arm::Left),
            v2::EvidenceRequest::Query {
                edge: v2::Edge::After,
                observer: Observer::Player,
                view: View::History,
            },
            true,
        );
        assert!(
            result.is_err(),
            "changed bound evidence must not pair with old summary"
        );
        drop(cap);
        assert!(inventory(&dir) == expected);
    }
}
