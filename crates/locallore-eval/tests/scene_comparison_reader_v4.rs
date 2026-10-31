// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST independent source freeze: UNCOMPILED/UNRUN. The scene_v4::desktop_api
//! seam is proposed, not implemented at this freeze. Its absence is a build
//! prerequisite, never an executed behavior RED. Actual scripted producer and
//! retained read capabilities only; no fabricated report, engine or runtime.
use locallore::{
    inference::Cancellation,
    inspection_query::{Observer, View},
};
use locallore_eval::{
    digest,
    local_lane::{
        comparison::{
            self,
            desktop_api::{Arm, Edge, EvidenceRequest, RowId},
            scene_v4::{self, desktop_api as reader},
            ComparisonKind,
        },
        LaneFactory,
    },
    memory_comparison_v4,
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
fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "scene-reader-v4-{label}-{}-{}-{}",
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
    fn visit(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path();
            let meta = fs::symlink_metadata(&path).unwrap();
            assert!(!meta.file_type().is_symlink() && out.len() < 4096);
            let key = path.strip_prefix(root).unwrap().to_owned();
            if meta.is_dir() {
                out.insert(key, None);
                visit(root, &path, depth + 1, total, out);
            } else {
                assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(path).unwrap();
                *total += bytes.len();
                assert!(*total <= 64 * 1024 * 1024);
                out.insert(key, Some(bytes));
            }
        }
    }
    let mut out = Inventory::new();
    visit(root, root, 0, &mut 0, &mut out);
    out
}
fn source() -> &'static Path {
    static TEMPLATE: OnceLock<PathBuf> = OnceLock::new();
    TEMPLATE.get_or_init(|| {
        let path = root("closed-template").join("run");
        let report = scene_v4::run_comparison(
            &path,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!(report.turns.len(), 12);
        path
    })
}
fn fixture(label: &str) -> PathBuf {
    // The immutable closed template is NEVER opened with a retained reader.
    // Each reader/lock/mutation belongs to a distinct ordinary byte copy.
    let files = inventory(source());
    let target = root(label).join("run");
    fs::create_dir(&target).unwrap();
    for (relative, bytes) in &files {
        let path = target.join(relative);
        match bytes {
            None => fs::create_dir_all(path).unwrap(),
            Some(bytes) => {
                fs::create_dir_all(path.parent().unwrap()).unwrap();
                fs::write(path, bytes).unwrap();
            }
        }
    }
    assert_eq!(inventory(&target), files);
    target
}
fn first_row(summary: &Value) -> RowId {
    let row = &summary["rows"][0]["row"];
    assert_eq!(row["arm"], "left");
    RowId {
        turn: row["turn"].as_str().unwrap().into(),
        arm: Arm::Left,
    }
}
fn binding(summary: &Value) -> &str {
    summary["binding"].as_str().unwrap()
}
fn forbidden<T>(result: Result<T, String>) {
    assert!(matches!(result, Err(ref error) if error == "Forbidden"));
}

#[test]
fn actual_scene_report_snapshot_is_bound_read_only_and_lossless() {
    let dir = fixture("snapshot");
    let before = inventory(&dir);
    let actual_report = serde_json::to_value(scene_v4::inspect_comparison(&dir).unwrap()).unwrap();
    let cap = reader::open_read_only(&dir).unwrap();
    forbidden(reader::summary(&cap, false));
    let summary = reader::summary(&cap, true).unwrap();
    assert_eq!(summary["version"], 1);
    assert_eq!(summary["protocol_version"], 4);
    assert_eq!(summary["report"], actual_report);
    assert_eq!(
        summary["report"]["arms"],
        serde_json::to_value(memory_comparison_v4::current_arm_descriptors()).unwrap()
    );
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    assert_eq!(
        summary["unavailable"],
        json!(["selected_protocol4_native_rerun_unavailable"])
    );
    assert_eq!(summary["report"]["human_reviewed"], 0);
    assert_eq!(summary["report"]["human_rubric"], "not_reviewed");
    assert_eq!(summary["report"]["quality_accepted"], false);
    let rows = summary["rows"].as_array().unwrap();
    let turns = actual_report["turns"].as_array().unwrap();
    assert_eq!(rows.len(), 12);
    for (row, turn) in rows.iter().zip(turns) {
        assert_eq!(row["row"], json!({"turn":turn["turn"],"arm":turn["arm"]}));
        assert_eq!(row["source"]["status"], "available");
        assert_eq!(
            row["source"]["input_semantic_sha256"],
            turn["input_semantic_sha256"]
        );
        assert!(
            row["source"]["before_head"].as_u64().unwrap()
                < row["source"]["after_head"].as_u64().unwrap()
        );
        assert_eq!(row["receipt_available"], true);
        assert_eq!(row["capture_available"], true);
        assert_eq!(row["recording_available"], true);
        assert_eq!(row["unavailable"], json!([]));
    }
    let manifest: Value = serde_json::from_slice(&fs::read(dir.join("run.json")).unwrap()).unwrap();
    assert_eq!(
        binding(&summary),
        digest(
            &serde_json::to_vec(&json!({"manifest":manifest,"report":actual_report,"rows":rows}))
                .unwrap()
        )
    );
    assert!(matches!(reader::open_read_only(&dir), Err(ref error) if error == "RunBusy"));
    drop(cap); // Include every byte, including run.lock, only after releasing it.
    assert_eq!(inventory(&dir), before);
    let reopened = reader::open_read_only(&dir).unwrap();
    assert_eq!(reader::summary(&reopened, true).unwrap(), summary);
    drop(reopened);
    assert_eq!(inventory(&dir), before);
}

#[test]
fn actual_edges_and_receipt_use_shared_observer_guard_before_identity_probes() {
    let dir = fixture("evidence");
    let before = inventory(&dir);
    let cap = reader::open_read_only(&dir).unwrap();
    let summary = reader::summary(&cap, true).unwrap();
    let row = first_row(&summary);
    let unknown = RowId {
        turn: "not-an-actual-row".into(),
        arm: Arm::Right,
    };
    for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
        forbidden(reader::evidence(
            &cap,
            "wrong-binding",
            &unknown,
            EvidenceRequest::Receipt {
                observer: observer.clone(),
            },
            true,
        ));
        forbidden(reader::evidence(
            &cap,
            "wrong-binding",
            &unknown,
            EvidenceRequest::Capture {
                observer: observer.clone(),
            },
            true,
        ));
        forbidden(reader::evidence(
            &cap,
            "wrong-binding",
            &unknown,
            EvidenceRequest::Outputs { observer },
            true,
        ));
    }
    forbidden(reader::evidence(
        &cap,
        "wrong-binding",
        &unknown,
        EvidenceRequest::Query {
            edge: Edge::After,
            observer: Observer::Player,
            view: View::History,
        },
        false,
    ));
    for (edge, name) in [(Edge::Before, "before"), (Edge::After, "after")] {
        let evidence = reader::evidence(
            &cap,
            binding(&summary),
            &row,
            EvidenceRequest::Query {
                edge,
                observer: Observer::Player,
                view: View::History,
            },
            true,
        )
        .unwrap();
        assert_eq!(evidence["binding"], summary["binding"]);
        assert_eq!(evidence["row"], summary["rows"][0]["row"]);
        assert_eq!(evidence["scope"], summary["rows"][0]["source"]["scope"]);
        assert_eq!(evidence["read_only"], true);
        assert_eq!(evidence["generation_grant"], false);
        assert_eq!(evidence["edge"], name);
        assert_eq!(evidence["body"]["kind"], "query");
        assert_eq!(evidence["body"]["page"]["version"], 2);
        assert_eq!(
            evidence["body"]["page"]["observer"],
            json!({"kind":"player"})
        );
        assert_eq!(
            evidence["body"]["page"]["revision"],
            summary["rows"][0]["source"][format!("{name}_head")]
        );
    }
    let evidence = reader::evidence(
        &cap,
        binding(&summary),
        &row,
        EvidenceRequest::Receipt {
            observer: Observer::Omniscient,
        },
        true,
    )
    .unwrap();
    assert_eq!(evidence["body"]["kind"], "receipt");
    let receipt = &evidence["body"]["receipt"];
    let scope = serde_json::from_value(summary["rows"][0]["source"]["scope"].clone()).unwrap();
    let actual = Store::open_read_only(&dir.join("left").join("synthetic.sqlite"))
        .unwrap()
        .lookup_turn(&scope, &row.turn)
        .unwrap()
        .receipt
        .unwrap();
    assert_eq!(*receipt, serde_json::to_value(&actual).unwrap());
    assert_eq!(
        digest(&serde_json::to_vec(&actual).unwrap()),
        summary["report"]["turns"][0]["actual_receipt_sha256"]
            .as_str()
            .unwrap()
    );
    assert_eq!(receipt["play"]["scene"]["version"], 1);
    assert_eq!(
        receipt["play"]["scene"]["frame_sha256"],
        summary["report"]["turns"][0]["scene_frame_sha256"]
    );
    drop(cap);
    assert_eq!(inventory(&dir), before);
}

#[test]
fn retained_snapshot_never_authorizes_changed_source_evidence_or_repairs_it() {
    let dir = fixture("changed-source");
    let cap = reader::open_read_only(&dir).unwrap();
    let snapshot = reader::summary(&cap, true).unwrap();
    let row = first_row(&snapshot);
    let path = dir.join("run.json");
    let original = fs::read(&path).unwrap();
    let mut changed: Value = serde_json::from_slice(&original).unwrap();
    changed["future_unrecognized_key"] = json!(true);
    fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
    // Summary is an explicitly retained snapshot, not a fresh integrity claim.
    assert_eq!(reader::summary(&cap, true).unwrap(), snapshot);
    assert!(reader::evidence(
        &cap,
        binding(&snapshot),
        &row,
        EvidenceRequest::Query {
            edge: Edge::After,
            observer: Observer::Player,
            view: View::History
        },
        true
    )
    .is_err());
    drop(cap);
    let changed_bytes = inventory(&dir);
    assert!(reader::open_read_only(&dir).is_err());
    assert_eq!(inventory(&dir), changed_bytes);
    fs::write(&path, original).unwrap();
    let restored = reader::open_read_only(&dir).unwrap();
    assert_eq!(reader::summary(&restored, true).unwrap(), snapshot);
}

#[test]
fn reader_versions_never_relabel_actual_protocol3_or_protocol4_sources() {
    let old = root("protocol3").join("run");
    comparison::literal_v3::run_comparison(
        &old,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let old_bytes = inventory(&old);
    assert!(reader::open_read_only(&old).is_err());
    let old_cap = comparison::literal_v3::desktop_api::open_read_only(&old).unwrap();
    assert_eq!(
        comparison::literal_v3::desktop_api::summary(&old_cap, true).unwrap()["protocol_version"],
        3
    );
    drop(old_cap);
    assert_eq!(inventory(&old), old_bytes);
    let new = fixture("version4");
    let new_bytes = inventory(&new);
    assert!(comparison::literal_v3::desktop_api::open_read_only(&new).is_err());
    assert_eq!(inventory(&new), new_bytes);
}
