// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Actual scripted producers and
//! canonical Store reads, not native/model/UI or a hand-authored report oracle.
use locallore::{engine::Engine, inference::Cancellation};
use locallore_eval::{
    local_lane::{
        comparison::{self, desktop_api, literal_v3, selected, ComparisonKind},
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
fn root(label: &str) -> PathBuf {
    let p = std::env::temp_dir().join(format!(
        "literal-comparison-v3-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&p).unwrap();
    p
}
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for e in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let p = e.unwrap().path();
            let m = fs::symlink_metadata(&p).unwrap();
            assert!(!m.file_type().is_symlink());
            let key = p.strip_prefix(root).unwrap().to_owned();
            if m.is_dir() {
                out.insert(key, None);
                walk(root, &p, depth + 1, total, out);
            } else {
                assert!(m.is_file() && m.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(p).unwrap();
                *total += bytes.len();
                assert!(*total <= 64 * 1024 * 1024);
                out.insert(key, Some(bytes));
            }
        }
    }
    let mut out = Inventory::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}
fn clone_owned(source: &Path, label: &str) -> PathBuf {
    let source = inventory(source);
    let target = root(label).join("run");
    fs::create_dir(&target).unwrap();
    for (p, v) in &source {
        match v {
            None => fs::create_dir_all(target.join(p)).unwrap(),
            Some(bytes) => fs::write(target.join(p), bytes).unwrap(),
        }
    }
    assert_eq!(inventory(&target), source);
    target
}
fn value(p: &Path) -> Value {
    serde_json::from_slice(&fs::read(p).unwrap()).unwrap()
}
fn run(
    p: &Path,
    resume: bool,
    kind: ComparisonKind,
    scenes: usize,
    reference: Option<&comparison::ValidatedReference>,
) -> Value {
    serde_json::to_value(
        literal_v3::run_comparison(
            p,
            resume,
            kind,
            &Cancellation::default(),
            scenes,
            LaneFactory::ScriptedBaseline,
            reference,
        )
        .unwrap(),
    )
    .unwrap()
}
fn protected(i: &Inventory) -> Inventory {
    i.iter()
        .filter(|(p, _)| {
            p.file_name().and_then(|n| n.to_str()).is_some_and(|n| {
                n.starts_with("attempt-") || n.starts_with("raw-") || n.starts_with("admission-")
            })
        })
        .map(|(p, v)| (p.clone(), v.clone()))
        .collect()
}
fn refuse<T>(result: Result<T, String>) {
    if let Ok(_) = result {
        panic!("expected closed refusal before new work");
    }
}
struct Cohorts {
    reference: PathBuf,
    paired: PathBuf,
    paired_report: Value,
    partial: PathBuf,
    first: Value,
    middle: Value,
    full: PathBuf,
    full_report: Value,
    first_evidence: Inventory,
}
fn cohorts() -> &'static Cohorts {
    static C: OnceLock<Cohorts> = OnceLock::new();
    C.get_or_init(|| {
        let r = root("actual");
        let reference = r.join("reference");
        let report = comparison::prepare_reference(&reference, &Cancellation::default()).unwrap();
        assert_eq!(
            (report.accepted, report.guard_only, report.roles),
            (21, 3, 42)
        );
        let opened = comparison::open_reference(&reference).unwrap();
        let paired = r.join("paired");
        let paired_report = run(
            &paired,
            false,
            ComparisonKind::PairedSnapshots,
            1,
            Some(&opened),
        );
        let full = r.join("rollout");
        let first = run(&full, false, ComparisonKind::ContinuousRollout, 1, None);
        let first_evidence = protected(&inventory(&full));
        let partial = clone_owned(&full, "genuine-partial");
        let middle = run(&full, true, ComparisonKind::ContinuousRollout, 1, None);
        let after = inventory(&full);
        for (p, v) in &first_evidence {
            assert_eq!(after.get(p), Some(v));
        }
        let full_report = run(&full, true, ComparisonKind::ContinuousRollout, 4, None);
        Cohorts {
            reference,
            paired,
            paired_report,
            partial,
            first,
            middle,
            full,
            full_report,
            first_evidence,
        }
    })
}
fn row<'a>(report: &'a Value, turn: &str, arm: &str) -> &'a Value {
    report["turns"]
        .as_array()
        .unwrap()
        .iter()
        .find(|r| r["turn"] == turn && r["arm"] == arm)
        .unwrap()
}
fn assert_row_contract(row: &Value) {
    assert!(row.get("policy").is_none());
    assert!(row.get("policy_matches").is_none());
    let literal = row["arm"] == "left";
    assert_eq!(
        row["construction"],
        serde_json::to_value(&arm_descriptors()[usize::from(!literal)]).unwrap()
    );
    if literal {
        for key in [
            "mandatory_sha256",
            "optional_detail_selected",
            "selected_context_bytes",
            "estimated_context_tokens",
            "source_fallback_reason",
            "compiler_fallback_reason",
        ] {
            assert!(row[key].is_null(), "literal memory-only field {key}");
        }
    }
    if row["phase"] == "committed" && !row["recovered_without_checkpoint"].as_bool().unwrap() {
        assert_eq!(row["construction_matches"], true);
        assert_eq!(row["context_evidence_available"], true);
        assert_eq!(
            row["construction_evidence_status"],
            if literal {
                "validated_literal"
            } else {
                "validated_relevant"
            }
        );
        if literal {
            let source = row["literal_source_units"].as_u64().unwrap();
            let selected = row["literal_selected_units"].as_u64().unwrap();
            let start = row["literal_selected_start"].as_u64().unwrap();
            assert_eq!(start + selected, source);
            assert!(selected <= 128);
        } else {
            for key in [
                "literal_source_units",
                "literal_selected_start",
                "literal_selected_units",
            ] {
                assert!(row[key].is_null());
            }
        }
    }
}
fn actual_engine(path: &Path) -> Engine {
    let scope = frozen_suite().unwrap().seed().scope.clone();
    Store::open_read_only(path)
        .unwrap()
        .resume(&scope)
        .unwrap()
        .engine
}
fn paired_engine(dir: &Path, turn: &str) -> Engine {
    let mut found = None;
    for p in fs::read_dir(dir).unwrap() {
        let p = p.unwrap().path();
        if p.extension().and_then(|v| v.to_str()) == Some("sqlite") {
            let e = actual_engine(&p);
            if e.receipts()
                .last()
                .is_some_and(|r| r.request().turn == turn)
            {
                assert!(found.is_none());
                found = Some(e);
            }
        }
    }
    found.expect("actual isolated pair database")
}

#[test]
fn real_paired_inputs_and_reference_prefixes_keep_distinct_construction_evidence() {
    let c = cohorts();
    let reference_before = inventory(&c.reference);
    let paired_before = inventory(&c.paired);
    let r = &c.paired_report;
    assert_eq!(r["version"], 3);
    assert_eq!(r["arms"], serde_json::to_value(arm_descriptors()).unwrap());
    assert_eq!(r["turns"].as_array().unwrap().len(), 12);
    assert_eq!(r["completed_scenes"], 1);
    assert_eq!(r["completed"], false);
    assert_eq!(r["human_reviewed"], 0);
    assert_eq!(r["quality_accepted"], false);
    let suite = frozen_suite().unwrap();
    assert_eq!(r["suite_sha256"], suite.sha256().unwrap());
    for step in &suite.steps()[..6] {
        let a = row(r, step.id(), "left");
        let b = row(r, step.id(), "right");
        assert_eq!(a["input_semantic_sha256"], b["input_semantic_sha256"]);
        assert_eq!(a["passed"], true);
        assert_eq!(b["passed"], true);
        assert_row_contract(a);
        assert_row_contract(b);
    }
    let key = suite.steps()[4].id();
    let reference = actual_engine(&c.reference.join("synthetic.sqlite"));
    for arm in ["left", "right"] {
        let e = paired_engine(&c.paired.join(arm), key);
        let actual = e.receipts().last().unwrap();
        let before = e.at_revision(actual.request().expected_revision).unwrap();
        let prefix: Vec<_> = reference
            .receipts()
            .iter()
            .filter(|r| r.events().last().unwrap().sequence() <= before.revision())
            .cloned()
            .collect();
        assert_eq!(before.receipts(), prefix);
        assert_eq!(actual.request(), &suite.steps()[4].request(&before));
        assert_eq!(
            actual.play().unwrap().prompt_version,
            if arm == "left" {
                "locallore-play-v2.6-literal-director-v1"
            } else {
                "locallore-play-v2.5"
            }
        );
    }
    assert_eq!(inventory(&c.reference), reference_before);
    assert_eq!(inventory(&c.paired), paired_before);
}

#[test]
fn real_rollout_advances_12_24_48_rows_only_missing_work_then_cold_complete_resume_is_read_only() {
    let c = cohorts();
    assert_eq!(c.first["turns"].as_array().unwrap().len(), 12);
    assert_eq!(c.middle["turns"].as_array().unwrap().len(), 24);
    let done = &c.full_report;
    assert_eq!(done["turns"].as_array().unwrap().len(), 48);
    assert_eq!(done["completed"], true);
    assert_eq!(done["completed_scenes"], 4);
    for original in c.first["turns"].as_array().unwrap() {
        assert_eq!(
            row(
                &c.middle,
                original["turn"].as_str().unwrap(),
                original["arm"].as_str().unwrap()
            ),
            original
        );
        assert_eq!(
            row(
                done,
                original["turn"].as_str().unwrap(),
                original["arm"].as_str().unwrap()
            ),
            original
        );
    }
    let mut roles = 0;
    let mut guards = 0;
    for r in done["turns"].as_array().unwrap() {
        assert_eq!(r["passed"], true);
        assert_row_contract(r);
        roles += r["roles"].as_u64().unwrap();
        if r["roles"] == 0 {
            guards += 1;
            assert_eq!(r["construction_evidence_status"], "not_applicable_guard");
            assert_eq!(r["context_evidence_available"], false);
            for k in [
                "literal_source_units",
                "literal_selected_start",
                "literal_selected_units",
            ] {
                assert!(r[k].is_null());
            }
        }
    }
    assert_eq!(roles, 84);
    assert_eq!(guards, 6);
    let before = inventory(&c.full);
    for (p, v) in &c.first_evidence {
        assert_eq!(before.get(p), Some(v));
    }
    let inspected = serde_json::to_value(literal_v3::inspect_comparison(&c.full).unwrap()).unwrap();
    assert_eq!(inspected, *done);
    assert_eq!(inventory(&c.full), before);
    assert_eq!(
        run(&c.full, true, ComparisonKind::ContinuousRollout, 4, None),
        *done
    );
    assert_eq!(inventory(&c.full), before);
    // Public factory is a closed enum: unchanged full ledger/raw/database/report
    // inventory is measured here, not an invented counting-provider callback.
}

#[test]
fn committed_lost_checkpoint_uses_actual_store_and_reports_unknown_unavailable_not_validated_literal(
) {
    let p = clone_owned(&cohorts().partial, "lost-checkpoint");
    fs::remove_file(p.join("left/attempt-05.json")).unwrap();
    fs::remove_file(p.join("scene-00.json")).unwrap();
    let db = fs::read(p.join("left/synthetic.sqlite")).unwrap();
    let before = protected(&inventory(&p));
    let report = run(&p, true, ComparisonKind::ContinuousRollout, 1, None);
    let recovered = row(&report, "courier-06", "left");
    assert_eq!(recovered["phase"], "committed");
    assert_eq!(recovered["recovered_without_checkpoint"], true);
    assert_eq!(recovered["roles_known"], false);
    assert_eq!(recovered["passed"], false);
    assert_eq!(recovered["context_evidence_available"], false);
    assert_eq!(recovered["construction_evidence_status"], "unavailable");
    for k in [
        "literal_source_units",
        "literal_selected_start",
        "literal_selected_units",
    ] {
        assert!(recovered[k].is_null());
    }
    assert_eq!(fs::read(p.join("left/synthetic.sqlite")).unwrap(), db);
    let after = inventory(&p);
    for (path, bytes) in before {
        assert_eq!(after.get(&path), Some(&bytes));
    }
}

fn corrupt_descriptor(v: &mut Value) -> bool {
    match v {
        Value::Object(o) => {
            if o.get("arm").is_some_and(|v| v == "literal_player_v1") {
                assert!(o.contains_key("literal_source_version"));
                o.insert("prompt_version".into(), json!("unsupported-copy"));
                true
            } else {
                o.values_mut().any(corrupt_descriptor)
            }
        }
        Value::Array(a) => a.iter_mut().any(corrupt_descriptor),
        _ => false,
    }
}
#[test]
fn mutated_manifest_version_arm_profile_and_source_are_refused_before_any_new_admission() {
    for fault in 0..4 {
        let p = clone_owned(&cohorts().partial, "manifest-copy");
        let file = p.join("run.json");
        let mut v = value(&file);
        match fault {
            0 => v["version"] = json!(2),
            1 => v["profile"]["context_tokens"] = json!(0),
            2 => assert!(corrupt_descriptor(&mut v)),
            _ => v["source_sha256"] = json!("0".repeat(64)),
        }
        fs::write(&file, serde_json::to_vec(&v).unwrap()).unwrap();
        let expected = inventory(&p);
        refuse(literal_v3::run_comparison(
            &p,
            true,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        ));
        assert_eq!(inventory(&p), expected);
        // This is an explicitly mutated synthetic metadata copy, NOT a genuine
        // historical cohort. If read-only source drift is displayable it must
        // remain visibly mismatched, never repair the bytes or allow resume.
        if fault == 3 {
            if let Ok(report) = literal_v3::inspect_comparison(&p) {
                assert_eq!(
                    serde_json::to_value(report).unwrap()["source_matches"],
                    false
                );
            }
            assert_eq!(inventory(&p), expected);
        }
    }
}

#[test]
fn actual_raw_or_capture_corruption_is_never_repaired_or_promoted_into_a_valid_input() {
    for fault in 0..2 {
        let p = clone_owned(&cohorts().partial, "evidence-copy");
        let checkpoint = value(&p.join("left/attempt-00.json"));
        let capture = p
            .join("left")
            .join(checkpoint["capture_file"].as_str().unwrap());
        if fault == 0 {
            let recording = value(
                &p.join("left")
                    .join(checkpoint["recording_file"].as_str().unwrap()),
            );
            let raw = p
                .join("left")
                .join(recording["raw"][0]["file"].as_str().unwrap());
            let mut bytes = fs::read(&raw).unwrap();
            assert!(!bytes.is_empty());
            bytes[0] ^= 1;
            fs::write(raw, bytes).unwrap();
        } else {
            let mut v = value(&capture);
            v["data"]["details"]["identity"]["observer"] = json!("sable");
            fs::write(capture, serde_json::to_vec(&v).unwrap()).unwrap();
        }
        let expected = inventory(&p);
        refuse(literal_v3::inspect_comparison(&p));
        assert_eq!(inventory(&p), expected);
        refuse(literal_v3::run_comparison(
            &p,
            true,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        ));
        assert_eq!(inventory(&p), expected);
    }
}

#[test]
fn pre_cancel_and_scene_bounds_create_no_run_and_existing_v2_selected_reader_remains_closed_to_v3()
{
    let parent = root("refusal");
    for scenes in [0, 5] {
        let p = parent.join(format!("scene-{scenes}"));
        refuse(literal_v3::run_comparison(
            &p,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            scenes,
            LaneFactory::ScriptedBaseline,
            None,
        ));
        assert!(!p.exists());
    }
    let p = parent.join("cancelled");
    let cancel = Cancellation::default();
    cancel.cancel();
    refuse(literal_v3::run_comparison(
        &p,
        false,
        ComparisonKind::ContinuousRollout,
        &cancel,
        1,
        LaneFactory::ScriptedBaseline,
        None,
    ));
    assert!(!p.exists());
    let c = cohorts();
    let before = inventory(&c.partial);
    refuse(comparison::inspect_comparison(&c.partial));
    refuse(desktop_api::open_read_only(&c.partial));
    refuse(selected::prepare_selected(
        &c.partial,
        &"0".repeat(64),
        &desktop_api::RowId {
            turn: "courier-01".into(),
            arm: desktop_api::Arm::Left,
        },
        selected::SelectedIntent {
            client_id: "11111111-1111-4111-8111-111111111111".into(),
            lane: selected::SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    ));
    assert_eq!(inventory(&c.partial), before);
}

#[test]
fn actual_cli_scripted_run_and_read_are_closed_bounded_and_do_not_control_a_desktop() {
    let parent = root("actual-cli");
    let path = parent.join("run");
    fn owned_cli() -> std::process::Command {
        let command = std::process::Command::new(env!("CARGO_BIN_EXE_locallore-eval"));
        #[cfg(windows)]
        let command = {
            use std::os::windows::process::CommandExt;
            let mut command = command;
            command.creation_flags(0x08000000); // CREATE_NO_WINDOW for this fixed owned CLI.
            command
        };
        command
    }
    let output = owned_cli()
        .args(["literal-comparison", "run"])
        .arg(&path)
        .args([
            "--kind",
            "rollout",
            "--lane",
            "scripted",
            "--max-scenes",
            "1",
        ])
        .output()
        .unwrap();
    assert!(output.stdout.len() <= 2 * 1024 * 1024 + 1 && output.stderr.len() <= 16384);
    assert!(
        output.status.success(),
        "fixed scripted CLI failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["version"], 3);
    assert_eq!(report["turns"].as_array().unwrap().len(), 12);
    assert_eq!(report["quality_accepted"], false);
    let before = inventory(&path);
    let inspected = owned_cli()
        .args(["literal-comparison", "inspect"])
        .arg(&path)
        .output()
        .unwrap();
    assert!(inspected.status.success());
    assert!(inspected.stdout.len() <= 2 * 1024 * 1024 + 1 && inspected.stderr.len() <= 16384);
    assert_eq!(
        serde_json::from_slice::<Value>(&inspected.stdout).unwrap(),
        report
    );
    assert_eq!(inventory(&path), before);
    let unavailable = parent.join("native-unavailable");
    let refused = owned_cli()
        .args(["literal-comparison", "run"])
        .arg(&unavailable)
        .args(["--kind", "rollout", "--lane", "native"])
        .output()
        .unwrap();
    assert_eq!(refused.status.code(), Some(2));
    assert!(!unavailable.exists());
    assert!(refused.stdout.is_empty() && refused.stderr.len() <= 16384);
    assert!(String::from_utf8_lossy(&refused.stderr).contains("NativeComparisonV3Unavailable"));
    assert_eq!(inventory(&path), before);
}
