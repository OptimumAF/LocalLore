// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Gate1 frozen reader oracles, source-only UNCOMPILED/UNRUN by this author.
//! Contract ac9966f58c017642323efe4b7144616c5cccc21a, query clarification from Root:
//! cut actual Engine at edge, Query2 expected_head=edge, at_revision=None, limit64.
//! Claim #29 6393149922. No production/old-test edits or private authority grants.
//! Actual scripted producer fixtures are generated only when Root executes tests;
//! this is not model quality, native IPC, WebView, device or zero-role measurement.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_desktop_review -- --nocapture --test-threads=1
//! Separate explicit historical opt-in uses LOCALLORE_D07_HISTORICAL_COHORT.

use locallore::{
    contracts::Request,
    engine::Engine,
    inference::Cancellation,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
use locallore_eval::{
    local_lane::{
        comparison::{self, desktop_api, ComparisonKind},
        LaneFactory,
    },
    memory_comparison::frozen_suite,
    memory_comparison_v2::semantic_input,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        OnceLock,
    },
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const SECRET: &str = "SECRET-TIDE-731";

fn owned_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-comparison-reader-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&root).unwrap();
    // Caller-owned synthetic files are retained for first-failure inspection.
    root
}

#[derive(PartialEq, Eq)]
struct Inventory {
    directories: BTreeSet<PathBuf>,
    files: BTreeMap<PathBuf, Vec<u8>>,
}
fn inventory(root: &Path) -> Inventory {
    fn visit(
        root: &Path,
        relative: &Path,
        depth: usize,
        result: &mut Inventory,
        total: &mut usize,
    ) {
        assert!(depth <= 8);
        let path = root.join(relative);
        let metadata = fs::symlink_metadata(&path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        if metadata.is_dir() {
            result.directories.insert(relative.into());
            for entry in fs::read_dir(path).unwrap() {
                visit(
                    root,
                    &relative.join(entry.unwrap().file_name()),
                    depth + 1,
                    result,
                    total,
                );
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 64 * 1024 * 1024);
            assert!(result.files.insert(relative.into(), bytes).is_none());
        }
        assert!(result.files.len() + result.directories.len() <= 4096);
    }
    let mut result = Inventory {
        directories: BTreeSet::new(),
        files: BTreeMap::new(),
    };
    visit(root, Path::new(""), 0, &mut result, &mut 0);
    result
}
fn clone_owned(source: &Path, label: &str) -> PathBuf {
    let captured = inventory(source);
    let target = owned_root(label).join("run");
    fs::create_dir(&target).unwrap();
    for relative in &captured.directories {
        if !relative.as_os_str().is_empty() {
            fs::create_dir_all(target.join(relative)).unwrap();
        }
    }
    for (relative, bytes) in &captured.files {
        fs::write(target.join(relative), bytes).unwrap();
    }
    assert!(inventory(&target) == captured);
    target
}
fn read_json(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
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
fn ordinary_error<T>(result: Result<T, String>) -> String {
    // OpenedComparison deliberately has no Debug; do not require unwrap_err().
    result.err().expect("closed reader refusal")
}
fn fixed_error<T>(result: Result<T, String>) {
    let error = ordinary_error(result);
    assert!(!error.is_empty() && error.len() <= 96);
    assert!(error
        .bytes()
        .all(|b| b.is_ascii_alphanumeric() || b == b'_'));
    assert!(!error.contains(SECRET));
}

struct Producers {
    paired: PathBuf,
    rollout: PathBuf,
}
fn producers() -> &'static Producers {
    static PRODUCERS: OnceLock<Producers> = OnceLock::new();
    PRODUCERS.get_or_init(|| {
        let root = owned_root("producer");
        let reference_path = root.join("reference");
        let reference_report =
            comparison::prepare_reference(&reference_path, &Cancellation::default()).unwrap();
        assert_eq!(reference_report.turns.len(), 24);
        let reference = comparison::open_reference(&reference_path).unwrap();
        let paired = root.join("paired");
        let paired_report = comparison::run_comparison(
            &paired,
            false,
            ComparisonKind::PairedSnapshots,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            Some(&reference),
        )
        .unwrap();
        assert_eq!(paired_report.turns.len(), 12);
        assert_eq!(paired_report.completed_scenes, 1);
        let rollout = root.join("rollout");
        let rollout_report = comparison::run_comparison(
            &rollout,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            2,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!(rollout_report.turns.len(), 24);
        assert_eq!(rollout_report.completed_scenes, 2);
        assert!(paired_report
            .turns
            .iter()
            .chain(&rollout_report.turns)
            .all(|row| row.passed));
        Producers { paired, rollout }
    })
}
fn index(turn: &str) -> usize {
    frozen_suite()
        .unwrap()
        .steps()
        .iter()
        .position(|step| step.id() == turn)
        .unwrap()
}
fn arm_name(arm: desktop_api::Arm) -> &'static str {
    match arm {
        desktop_api::Arm::Left => "left",
        desktop_api::Arm::Right => "right",
    }
}
fn row(turn: &str, arm: desktop_api::Arm) -> desktop_api::RowId {
    desktop_api::RowId {
        turn: turn.into(),
        arm,
    }
}
fn checkpoint(dir: &Path, turn: &str, arm: desktop_api::Arm) -> Value {
    read_json(
        &dir.join(arm_name(arm))
            .join(format!("attempt-{:02}.json", index(turn))),
    )
}
fn source_engine(dir: &Path, turn: &str, arm: desktop_api::Arm) -> Engine {
    let manifest = read_json(&dir.join("run.json"));
    let database = if manifest["kind"] == "paired_snapshots" {
        format!("pair-{:02}.sqlite", index(turn))
    } else {
        "synthetic.sqlite".into()
    };
    Store::open_read_only(&dir.join(arm_name(arm)).join(database))
        .unwrap()
        .resume(&frozen_suite().unwrap().seed().scope)
        .unwrap()
        .engine
}
fn expected_query(full: &Engine, edge: u64, observer: Observer, view: View) -> Value {
    let cut = full.at_revision(edge).unwrap();
    serde_json::to_value(
        inspection_query::query(
            &cut,
            &Query {
                version: 2,
                scope: cut.scope().clone(),
                expected_head: edge,
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
fn binding(summary: &Value) -> &str {
    let binding = summary["binding"].as_str().unwrap();
    assert!(binding.len() == 64 && binding.bytes().all(|b| b.is_ascii_hexdigit()));
    binding
}
fn envelope(
    reply: &Value,
    binding: &str,
    id: &desktop_api::RowId,
    cp: &Value,
    observer: Observer,
    edge: Value,
) {
    keys(
        reply,
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
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["binding"], binding);
    assert_eq!(reply["row"], json!({"turn":id.turn,"arm":arm_name(id.arm)}));
    assert_eq!(reply["scope"], cp["request"]["scope"]);
    assert_eq!(reply["before_head"], cp["before_head"]);
    assert_eq!(reply["after_head"], cp["after_head"]);
    assert_eq!(reply["observer"], serde_json::to_value(observer).unwrap());
    assert_eq!(reply["edge"], edge);
    assert_eq!(reply["read_only"], true);
    assert_eq!(reply["generation_grant"], false);
    assert!(serde_json::to_vec(reply).unwrap().len() <= 256 * 1024);
}

#[test]
fn paired_and_rollout_summaries_equal_inspection_and_derive_actual_scope_heads_without_writes() {
    for source in [&producers().paired, &producers().rollout] {
        let directory = clone_owned(source, "summary");
        let before = inventory(&directory);
        let report = comparison::inspect_comparison(&directory).unwrap();
        let opened = desktop_api::open_read_only(&directory).unwrap();
        let summary = desktop_api::summary(&opened, true).unwrap();
        keys(
            &summary,
            &[
                "version",
                "protocol_version",
                "binding",
                "report",
                "rows",
                "read_only",
                "execution_available",
                "unavailable",
            ],
        );
        assert_eq!(summary["version"], 1);
        assert_eq!(summary["protocol_version"], 2);
        let original_binding = binding(&summary).to_owned();
        assert_eq!(summary["report"], serde_json::to_value(&report).unwrap());
        assert_eq!(summary["read_only"], true);
        assert_eq!(summary["execution_available"], false);
        let unavailable: BTreeSet<_> = summary["unavailable"]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_str().unwrap())
            .collect();
        assert!(unavailable.contains("selected_rerun_not_implemented"));
        assert!(unavailable.contains("full_comparison_gui_not_implemented"));
        let rows = summary["rows"].as_array().unwrap();
        assert_eq!(rows.len(), report.turns.len());
        assert!(rows.len() <= 48 && serde_json::to_vec(&summary).unwrap().len() <= 2 * 1024 * 1024);
        for (actual, reported) in rows.iter().zip(&report.turns) {
            keys(
                actual,
                &[
                    "row",
                    "source",
                    "capture_available",
                    "receipt_available",
                    "recording_available",
                    "unavailable",
                ],
            );
            keys(&actual["row"], &["turn", "arm"]);
            keys(
                &actual["source"],
                &[
                    "status",
                    "scope",
                    "before_head",
                    "after_head",
                    "input_semantic_sha256",
                ],
            );
            let arm = if reported.arm == "left" {
                desktop_api::Arm::Left
            } else {
                assert_eq!(reported.arm, "right");
                desktop_api::Arm::Right
            };
            let cp = checkpoint(&directory, &reported.turn, arm);
            let full = source_engine(&directory, &reported.turn, arm);
            let before = full
                .at_revision(cp["before_head"].as_u64().unwrap())
                .unwrap();
            let after = full
                .at_revision(cp["after_head"].as_u64().unwrap())
                .unwrap();
            let request: Request = serde_json::from_value(cp["request"].clone()).unwrap();
            assert_eq!(request.scope, *before.scope());
            assert_eq!(
                actual["row"],
                json!({"turn":reported.turn,"arm":reported.arm})
            );
            assert_eq!(
                actual["source"],
                json!({"status":"available","scope":before.scope(),"before_head":before.revision(),"after_head":after.revision(),"input_semantic_sha256":semantic_input(&before,&request).unwrap()})
            );
            assert_eq!(actual["capture_available"], cp["capture_file"].is_string());
            assert_eq!(
                actual["recording_available"],
                cp["recording_file"].is_string()
            );
            assert_eq!(actual["receipt_available"], reported.phase == "committed");
            assert!(actual["unavailable"].is_array());
        }
        assert_eq!(desktop_api::summary(&opened, true).unwrap(), summary);
        drop(opened);
        let reopened = desktop_api::open_read_only(&directory).unwrap();
        assert_eq!(
            binding(&desktop_api::summary(&reopened, true).unwrap()),
            original_binding
        );
        drop(reopened);
        assert!(
            inventory(&directory) == before,
            "all files/directories, including ledgers, unchanged"
        );
    }
}

#[test]
fn query_edges_are_actual_cut_query2_pages_and_actor_privacy_is_not_raw_artifact_access() {
    let detail = frozen_suite().unwrap().steps()[0].text().to_owned();
    for source in [&producers().paired, &producers().rollout] {
        let directory = clone_owned(source, "query");
        let before = inventory(&directory);
        let opened = desktop_api::open_read_only(&directory).unwrap();
        let summary = desktop_api::summary(&opened, true).unwrap();
        let turn = frozen_suite().unwrap().steps()[0].id().to_owned();
        for arm in [desktop_api::Arm::Left, desktop_api::Arm::Right] {
            let id = row(&turn, arm);
            let cp = checkpoint(&directory, &turn, arm);
            let full = source_engine(&directory, &turn, arm);
            for (edge, name, head) in [
                (
                    desktop_api::Edge::Before,
                    "before",
                    cp["before_head"].as_u64().unwrap(),
                ),
                (
                    desktop_api::Edge::After,
                    "after",
                    cp["after_head"].as_u64().unwrap(),
                ),
            ] {
                for observer in [
                    Observer::Player,
                    Observer::Character { id: "mira".into() },
                    Observer::Character { id: "sable".into() },
                    Observer::Omniscient,
                ] {
                    for view in [View::Knowledge, View::History] {
                        let reply = desktop_api::evidence(
                            &opened,
                            binding(&summary),
                            &id,
                            desktop_api::EvidenceRequest::Query {
                                edge,
                                observer: observer.clone(),
                                view,
                            },
                            true,
                        )
                        .unwrap();
                        envelope(
                            &reply,
                            binding(&summary),
                            &id,
                            &cp,
                            observer.clone(),
                            json!(name),
                        );
                        keys(&reply["body"], &["kind", "page"]);
                        assert_eq!(reply["body"]["kind"], "query");
                        assert_eq!(
                            reply["body"]["page"],
                            expected_query(&full, head, observer.clone(), view)
                        );
                        assert_eq!(reply["body"]["page"]["head"], head);
                        assert_eq!(reply["body"]["page"]["revision"], head);
                        assert!(
                            serde_json::to_vec(&reply["body"]["page"]).unwrap().len() <= 65_536
                        );
                        if matches!(&observer, Observer::Character{id} if id=="mira" || id=="sable")
                        {
                            assert!(!reply.to_string().contains(SECRET));
                            assert!(
                                reply.get("receipt").is_none()
                                    && reply.get("capture").is_none()
                                    && reply.get("outputs").is_none()
                            );
                        }
                        if view == View::History
                            && matches!(&observer, Observer::Character{id} if id=="mira")
                        {
                            assert_eq!(
                                reply["body"]["page"].to_string().contains(detail.as_str()),
                                name == "after"
                            );
                        }
                        if view == View::History
                            && matches!(&observer, Observer::Character{id} if id=="sable")
                        {
                            assert!(!reply["body"]["page"].to_string().contains(detail.as_str()));
                        }
                    }
                }
            }
            for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
                for request in [
                    desktop_api::EvidenceRequest::Receipt {
                        observer: observer.clone(),
                    },
                    desktop_api::EvidenceRequest::Capture {
                        observer: observer.clone(),
                    },
                    desktop_api::EvidenceRequest::Outputs {
                        observer: observer.clone(),
                    },
                ] {
                    assert_eq!(
                        ordinary_error(desktop_api::evidence(
                            &opened,
                            binding(&summary),
                            &id,
                            request,
                            true
                        )),
                        "Forbidden"
                    );
                }
            }
        }
        drop(opened);
        assert!(inventory(&directory) == before);
    }
}

#[test]
fn omniscient_receipt_capture_and_outputs_are_exact_validated_producer_bytes() {
    let directory = clone_owned(&producers().rollout, "private");
    let before = inventory(&directory);
    let opened = desktop_api::open_read_only(&directory).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    let turn = frozen_suite().unwrap().steps()[0].id().to_owned();
    for arm in [desktop_api::Arm::Left, desktop_api::Arm::Right] {
        let id = row(&turn, arm);
        let cp = checkpoint(&directory, &turn, arm);
        let arm_dir = directory.join(arm_name(arm));
        let receipt = Store::open_read_only(&arm_dir.join("synthetic.sqlite"))
            .unwrap()
            .lookup_turn(source_engine(&directory, &turn, arm).scope(), &turn)
            .unwrap()
            .receipt
            .unwrap();
        let reply = desktop_api::evidence(
            &opened,
            binding(&summary),
            &id,
            desktop_api::EvidenceRequest::Receipt {
                observer: Observer::Omniscient,
            },
            true,
        )
        .unwrap();
        envelope(
            &reply,
            binding(&summary),
            &id,
            &cp,
            Observer::Omniscient,
            json!("after"),
        );
        assert_eq!(reply["body"], json!({"kind":"receipt","receipt":receipt}));
        let capture = read_json(&arm_dir.join(cp["capture_file"].as_str().unwrap()));
        let reply = desktop_api::evidence(
            &opened,
            binding(&summary),
            &id,
            desktop_api::EvidenceRequest::Capture {
                observer: Observer::Omniscient,
            },
            true,
        )
        .unwrap();
        envelope(
            &reply,
            binding(&summary),
            &id,
            &cp,
            Observer::Omniscient,
            Value::Null,
        );
        assert_eq!(reply["body"], json!({"kind":"capture","capture":capture}));
        assert!(serde_json::to_vec(&reply["body"]["capture"]).unwrap().len() <= 196_608);
        let recording = read_json(&arm_dir.join(cp["recording_file"].as_str().unwrap()));
        let outputs:Vec<_> = recording["raw"].as_array().unwrap().iter().map(|raw| {
            let bytes = fs::read(arm_dir.join(raw["file"].as_str().unwrap())).unwrap();
            assert_eq!(bytes.len() as u64,raw["bytes"].as_u64().unwrap());
            assert_eq!(hash(&bytes),raw["sha256"].as_str().unwrap());
            json!({"role":raw["role"],"bytes":bytes.len(),"sha256":hash(&bytes),"text":String::from_utf8(bytes).unwrap()})
        }).collect();
        let reply = desktop_api::evidence(
            &opened,
            binding(&summary),
            &id,
            desktop_api::EvidenceRequest::Outputs {
                observer: Observer::Omniscient,
            },
            true,
        )
        .unwrap();
        envelope(
            &reply,
            binding(&summary),
            &id,
            &cp,
            Observer::Omniscient,
            Value::Null,
        );
        assert_eq!(reply["body"], json!({"kind":"outputs","outputs":outputs}));
        for output in reply["body"]["outputs"].as_array().unwrap() {
            keys(output, &["role", "bytes", "sha256", "text"]);
        }
    }
    drop(opened);
    assert!(inventory(&directory) == before);
}

#[test]
fn native_grant_snapshot_binding_and_known_row_are_required_without_mutation() {
    let directory = clone_owned(&producers().rollout, "fences");
    let other = desktop_api::open_read_only(&producers().paired).unwrap();
    let foreign = desktop_api::summary(&other, true).unwrap();
    drop(other);
    let before = inventory(&directory);
    let opened = desktop_api::open_read_only(&directory).unwrap();
    assert_eq!(
        ordinary_error(desktop_api::summary(&opened, false)),
        "Forbidden"
    );
    let summary = desktop_api::summary(&opened, true).unwrap();
    assert_ne!(binding(&summary), binding(&foreign));
    let turn = frozen_suite().unwrap().steps()[0].id().to_owned();
    let id = row(&turn, desktop_api::Arm::Left);
    let query = || desktop_api::EvidenceRequest::Query {
        edge: desktop_api::Edge::Before,
        observer: Observer::Player,
        view: View::Knowledge,
    };
    assert_eq!(
        ordinary_error(desktop_api::evidence(
            &opened,
            binding(&summary),
            &id,
            query(),
            false
        )),
        "Forbidden"
    );
    for observer in [
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Omniscient,
    ] {
        for request in [
            desktop_api::EvidenceRequest::Receipt {
                observer: observer.clone(),
            },
            desktop_api::EvidenceRequest::Capture {
                observer: observer.clone(),
            },
            desktop_api::EvidenceRequest::Outputs {
                observer: observer.clone(),
            },
        ] {
            assert_eq!(
                ordinary_error(desktop_api::evidence(
                    &opened,
                    binding(&summary),
                    &id,
                    request,
                    false
                )),
                "Forbidden"
            );
        }
    }
    for bad in ["", "not-a-binding", &"0".repeat(64), binding(&foreign)] {
        assert_eq!(
            ordinary_error(desktop_api::evidence(&opened, bad, &id, query(), true)),
            "SnapshotMismatch"
        );
    }
    let unknown = row("not-a-frozen-turn", desktop_api::Arm::Right);
    assert_eq!(
        ordinary_error(desktop_api::evidence(
            &opened,
            binding(&summary),
            &unknown,
            query(),
            true
        )),
        "UnknownRow"
    );
    // A real frozen turn beyond this partial run is still absent, not guessed.
    let absent = row(
        frozen_suite().unwrap().steps()[23].id(),
        desktop_api::Arm::Left,
    );
    assert_eq!(
        ordinary_error(desktop_api::evidence(
            &opened,
            binding(&summary),
            &absent,
            query(),
            true
        )),
        "UnknownRow"
    );
    fixed_error(desktop_api::evidence(
        &opened,
        binding(&summary),
        &id,
        desktop_api::EvidenceRequest::Query {
            edge: desktop_api::Edge::After,
            observer: Observer::Character {
                id: "missing-actor".into(),
            },
            view: View::Knowledge,
        },
        true,
    ));
    drop(opened);
    assert!(inventory(&directory) == before);
}

#[test]
fn guard_only_rows_have_real_equal_edges_and_honest_optional_missing_evidence() {
    let directory = clone_owned(&producers().rollout, "guards");
    let before = inventory(&directory);
    let opened = desktop_api::open_read_only(&directory).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    let suite = frozen_suite().unwrap();
    for index in [8, 9] {
        for arm in [desktop_api::Arm::Left, desktop_api::Arm::Right] {
            let id = row(suite.steps()[index].id(), arm);
            let cp = checkpoint(&directory, &id.turn, arm);
            assert_ne!(cp["row"]["phase"], "committed");
            assert_eq!(cp["before_head"], cp["after_head"]);
            let found = summary["rows"]
                .as_array()
                .unwrap()
                .iter()
                .find(|r| r["row"] == json!({"turn":id.turn,"arm":arm_name(arm)}))
                .unwrap();
            assert_eq!(found["receipt_available"], false);
            for (request, reason, edge) in [
                (
                    desktop_api::EvidenceRequest::Receipt {
                        observer: Observer::Omniscient,
                    },
                    "no_accepted_receipt",
                    json!("after"),
                ),
                (
                    desktop_api::EvidenceRequest::Capture {
                        observer: Observer::Omniscient,
                    },
                    "capture_unavailable",
                    Value::Null,
                ),
            ] {
                let reply =
                    desktop_api::evidence(&opened, binding(&summary), &id, request, true).unwrap();
                envelope(
                    &reply,
                    binding(&summary),
                    &id,
                    &cp,
                    Observer::Omniscient,
                    edge,
                );
                assert_eq!(reply["body"], json!({"kind":"missing","reason":reason}));
            }
            let reply = desktop_api::evidence(
                &opened,
                binding(&summary),
                &id,
                desktop_api::EvidenceRequest::Query {
                    edge: desktop_api::Edge::After,
                    observer: Observer::Player,
                    view: View::Knowledge,
                },
                true,
            )
            .unwrap();
            assert_eq!(
                reply["body"]["page"],
                expected_query(
                    &source_engine(&directory, &id.turn, arm),
                    cp["after_head"].as_u64().unwrap(),
                    Observer::Player,
                    View::Knowledge
                )
            );
        }
    }
    drop(opened);
    assert!(inventory(&directory) == before);
}

#[test]
fn actual_lost_checkpoint_recovery_keeps_unknown_roles_and_missing_capture_recording_honest() {
    let directory = clone_owned(&producers().rollout, "recovered");
    // Existing real producer recovery boundary: the accepted DB is durable but
    // final left checkpoint and scene acknowledgement were lost. No relabelled
    // report/source or forged recovered row is written by this fixture.
    fs::remove_file(directory.join("left/attempt-11.json")).unwrap();
    fs::remove_file(directory.join("scene-01.json")).unwrap();
    comparison::run_comparison(
        &directory,
        true,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let turn = frozen_suite().unwrap().steps()[11].id().to_owned();
    let cp = checkpoint(&directory, &turn, desktop_api::Arm::Left);
    assert_eq!(cp["row"]["recovered_without_checkpoint"], true);
    assert_eq!(cp["row"]["roles_known"], false);
    assert!(cp["capture_file"].is_null() && cp["recording_file"].is_null());
    let before = inventory(&directory);
    let report = comparison::inspect_comparison(&directory).unwrap();
    let opened = desktop_api::open_read_only(&directory).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    assert_eq!(summary["report"], serde_json::to_value(&report).unwrap());
    let id = row(&turn, desktop_api::Arm::Left);
    for (request, reason) in [
        (
            desktop_api::EvidenceRequest::Capture {
                observer: Observer::Omniscient,
            },
            "capture_unavailable",
        ),
        (
            desktop_api::EvidenceRequest::Outputs {
                observer: Observer::Omniscient,
            },
            "recording_unavailable",
        ),
    ] {
        let reply = desktop_api::evidence(&opened, binding(&summary), &id, request, true).unwrap();
        envelope(
            &reply,
            binding(&summary),
            &id,
            &cp,
            Observer::Omniscient,
            Value::Null,
        );
        assert_eq!(reply["body"], json!({"kind":"missing","reason":reason}));
    }
    let receipt = desktop_api::evidence(
        &opened,
        binding(&summary),
        &id,
        desktop_api::EvidenceRequest::Receipt {
            observer: Observer::Omniscient,
        },
        true,
    )
    .unwrap();
    assert_eq!(receipt["body"]["kind"], "receipt");
    assert_eq!(receipt["body"]["receipt"]["request"]["turn"], turn);
    drop(opened);
    assert!(
        inventory(&directory) == before,
        "reader must not repair lost-ack metadata or settle/admit roles"
    );
}

#[test]
fn corrupt_or_missing_required_source_checkpoint_capture_recording_and_raw_output_are_refused() {
    let first_turn = frozen_suite().unwrap().steps()[0].id().to_owned();
    for (label, relative, remove) in [
        ("db-missing", "left/synthetic.sqlite", true),
        ("db-corrupt", "left/synthetic.sqlite", false),
        ("checkpoint-missing", "left/attempt-00.json", true),
        ("checkpoint-corrupt", "left/attempt-00.json", false),
        ("capture-missing", "left/attempt-00-capture.json", true),
        ("capture-corrupt", "left/attempt-00-capture.json", false),
        ("recording-missing", "left/attempt-00-recording.json", true),
        ("recording-corrupt", "left/attempt-00-recording.json", false),
        ("raw-missing", "left/raw-00-00.bin", true),
        ("raw-corrupt", "left/raw-00-00.bin", false),
    ] {
        let directory = clone_owned(&producers().rollout, label);
        let cp = checkpoint(&directory, &first_turn, desktop_api::Arm::Left);
        assert_eq!(cp["capture_file"], "attempt-00-capture.json");
        assert_eq!(cp["recording_file"], "attempt-00-recording.json");
        assert!(directory.join(relative).is_file());
        if remove {
            fs::remove_file(directory.join(relative)).unwrap();
        } else {
            fs::write(
                directory.join(relative),
                b"SYNTHETIC_CORRUPT_REQUIRED_EVIDENCE",
            )
            .unwrap();
        }
        let before = inventory(&directory);
        fixed_error(desktop_api::open_read_only(&directory));
        assert!(
            inventory(&directory) == before,
            "required corruption must not be repaired or hidden as optional"
        );
    }
}

#[test]
fn opening_requires_existing_unheld_lock_and_never_creates_a_missing_run_or_lock() {
    let directory = clone_owned(&producers().paired, "locks");
    let before = inventory(&directory);
    let lock = OpenOptions::new()
        .read(true)
        .write(true)
        .open(directory.join("run.lock"))
        .unwrap();
    lock.try_lock().unwrap();
    assert_eq!(
        ordinary_error(desktop_api::open_read_only(&directory)),
        "RunBusy"
    );
    assert!(inventory(&directory) == before);
    drop(lock);
    let opened = desktop_api::open_read_only(&directory).unwrap();
    assert_eq!(
        ordinary_error(desktop_api::open_read_only(&directory)),
        "RunBusy"
    );
    desktop_api::summary(&opened, true).unwrap();
    drop(opened);
    assert!(inventory(&directory) == before);
    fs::remove_file(directory.join("run.lock")).unwrap();
    let missing_lock = inventory(&directory);
    fixed_error(desktop_api::open_read_only(&directory));
    assert!(inventory(&directory) == missing_lock);
    assert!(!directory.join("run.lock").exists());
    let parent = owned_root("missing");
    let missing = parent.join("not-created");
    let before = inventory(&parent);
    fixed_error(desktop_api::open_read_only(&missing));
    assert!(!missing.exists());
    assert!(inventory(&parent) == before);
}

#[test]
#[ignore = "requires explicit LOCALLORE_D07_HISTORICAL_COHORT genuine retained 33356 rollout; never generated or relabelled"]
fn genuine_historical_summary_preserves_original_report_and_every_byte_without_execution_permission(
) {
    let directory = PathBuf::from(
        std::env::var_os("LOCALLORE_D07_HISTORICAL_COHORT").expect("explicit historical cohort"),
    );
    assert!(directory.is_absolute());
    // Same immutable sentinel packet as comparison_historical_readonly.rs.
    for (name, sha) in [
        (
            "run.json",
            "3e6ff45d65582ff9b65e550210dc0b14ff8a9fbf7d538a878d7f35014b0d668b",
        ),
        (
            "report.json",
            "4167a78bb84ea5cad983d7eb8ff83fb0be1c4e93d4deb019bfac1be05f785a2d",
        ),
        (
            "left/synthetic.sqlite",
            "0a810374ef2c2f94ef890899a2377a70a90b9d63a83bdf6adc5f87c57e230fa1",
        ),
        (
            "right/synthetic.sqlite",
            "8b749d981bd8b1806c6e6a11e2b4b943926344b98f01f9033cfa44fca71e6576",
        ),
    ] {
        let path = directory.join(name);
        let metadata = fs::symlink_metadata(&path).unwrap();
        assert!(
            metadata.is_file()
                && !metadata.file_type().is_symlink()
                && metadata.len() <= 1024 * 1024
        );
        assert_eq!(hash(&fs::read(path).unwrap()), sha);
    }
    let before = inventory(&directory);
    let inspected = comparison::inspect_comparison(&directory).unwrap();
    assert!(!inspected.source_matches);
    assert_eq!(inspected.turns.len(), 48);
    let opened = desktop_api::open_read_only(&directory).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    assert_eq!(summary["report"], serde_json::to_value(&inspected).unwrap());
    assert_eq!(summary["execution_available"], false);
    assert_eq!(summary["read_only"], true);
    assert!(summary["report"]["turns"]
        .as_array()
        .unwrap()
        .iter()
        .all(|r| r.get("forwarded_director_estimates").is_none()));
    drop(opened);
    assert!(inventory(&directory) == before);
}
