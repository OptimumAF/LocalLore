// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Original black-box synthetic review tests. The coordinator compiles/runs them.
//! No real model, native provider, device or quality acceptance is exercised.

use locallore::{inference::Cancellation, inspection_query::Observer};
use locallore_eval::local_lane::{
    comparison::{self, desktop_api, ComparisonKind},
    LaneFactory,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
    sync::{
        atomic::{AtomicU64, Ordering},
        OnceLock,
    },
};

const GRANT: &str = "--allow-synthetic-author-evidence";
static NEXT: AtomicU64 = AtomicU64::new(0);

fn owned(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-role-review-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&root).unwrap();
    root
}

#[derive(Debug, PartialEq, Eq)]
struct Inventory {
    directories: BTreeSet<PathBuf>,
    files: BTreeMap<PathBuf, (u64, String)>,
}

fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, relative: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 10);
        let path = root.join(relative);
        let metadata = fs::symlink_metadata(&path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        if metadata.is_dir() {
            out.directories.insert(relative.into());
            for entry in fs::read_dir(path).unwrap() {
                walk(
                    root,
                    &relative.join(entry.unwrap().file_name()),
                    depth + 1,
                    total,
                    out,
                );
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 64 * 1024 * 1024);
            out.files
                .insert(relative.into(), (metadata.len(), hash(&bytes)));
        }
        assert!(out.files.len() + out.directories.len() <= 4096);
    }
    let mut result = Inventory {
        directories: BTreeSet::new(),
        files: BTreeMap::new(),
    };
    walk(root, Path::new(""), 0, &mut 0, &mut result);
    result
}

fn producer() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE
        .get_or_init(|| {
            let run = owned("producer").join("run");
            let report = comparison::run_comparison(
                &run,
                false,
                ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!(report.completed_scenes, 1);
            assert_eq!(report.turns.len(), 12);
            assert!(report.turns.iter().all(|row| row.passed));
            run
        })
        .as_path()
}

fn fixture(label: &str) -> (PathBuf, PathBuf) {
    let parent = owned(label);
    let run = parent.join("run");
    let source = inventory(producer());
    for relative in &source.directories {
        fs::create_dir_all(run.join(relative)).unwrap();
    }
    for relative in source.files.keys() {
        fs::copy(producer().join(relative), run.join(relative)).unwrap();
    }
    assert_eq!(inventory(&run), source);
    (parent, run)
}

fn cli(command: &str, run: &Path, review: &Path, options: &[&str], granted: bool) -> Output {
    // The caller's outer test job owns descendants. This is only the trusted
    // local CLI with finite synthetic inputs; no shell or provider is launched.
    let mut child = Command::new(env!("CARGO_BIN_EXE_quality-review"));
    child.arg(command).arg(run).arg(review).args(options);
    if granted {
        child.arg(GRANT);
    }
    let output = child.output().unwrap();
    assert!(output.stdout.len() <= 2 * 1024 * 1024 && output.stderr.len() <= 16 * 1024);
    output
}

fn success(output: Output) -> Output {
    assert!(
        output.status.success(),
        "CLI failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    output
}

fn refused(output: Output) {
    assert!(!output.status.success(), "Unexpected CLI acceptance");
    for bytes in [&output.stdout, &output.stderr] {
        assert!(!String::from_utf8_lossy(bytes).contains("PRIVATE_PATH_CANARY"));
    }
}

fn read_json(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn write_json(path: &Path, value: &Value) {
    fs::write(path, serde_json::to_vec_pretty(value).unwrap()).unwrap();
}

fn summary(run: &Path, review: &Path) -> Value {
    let output = success(cli("summarize", run, review, &[], true));
    serde_json::from_slice(&output.stdout).unwrap()
}

fn snapshot(run: &Path) -> Value {
    let opened = desktop_api::open_read_only(run).unwrap();
    desktop_api::summary(&opened, true).unwrap()
}

fn exact_keys(value: &Value, names: &[&str]) {
    assert_eq!(
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        names.iter().copied().collect::<BTreeSet<_>>()
    );
}

fn check_packet(run: &Path, packet: &Value, selected: usize) {
    exact_keys(
        packet,
        &[
            "version",
            "scope",
            "rubric",
            "source",
            "reviewer",
            "quality_accepted",
            "entries",
            "limitations",
        ],
    );
    assert_eq!(packet["version"], 1);
    assert_eq!(packet["scope"], "locallore_role_review");
    assert_eq!(packet["rubric"], "role-quality-v1");
    assert!(packet["reviewer"].is_null());
    assert_eq!(packet["quality_accepted"], false);
    let opened = desktop_api::open_read_only(run).unwrap();
    let source = desktop_api::summary(&opened, true).unwrap();
    assert_eq!(packet["source"]["snapshot_binding"], source["binding"]);
    assert_eq!(
        packet["source"]["lane"],
        "scripted_current_policy_comparison"
    );
    assert_eq!(
        packet["source"]["source_matches"],
        source["report"]["source_matches"]
    );
    assert_eq!(packet["source"]["total_turns"], 12);
    assert_eq!(packet["source"]["selected_turns"], selected);
    assert_eq!(packet["source"]["sampling"], "first_n_report_rows");
    assert_eq!(
        packet["source"]["report_sha256"].as_str().unwrap().len(),
        64
    );
    let rows = source["report"]["turns"].as_array().unwrap();
    let entries = packet["entries"].as_array().unwrap();
    assert_eq!(entries.len(), rows.len());
    for (index, (entry, row)) in entries.iter().zip(rows).enumerate() {
        exact_keys(
            entry,
            &[
                "turn",
                "arm",
                "selected",
                "source_row",
                "capture",
                "outputs",
                "assessments",
            ],
        );
        assert_eq!(entry["turn"], row["turn"]);
        assert_eq!(entry["arm"], row["arm"]);
        assert_eq!(entry["source_row"], *row);
        assert_eq!(entry["selected"], index < selected);
        if index >= selected {
            assert!(entry["capture"].is_null() && entry["outputs"].is_null());
            assert_eq!(entry["assessments"], json!([]));
            continue;
        }
        let id = desktop_api::RowId {
            turn: row["turn"].as_str().unwrap().into(),
            arm: match row["arm"].as_str().unwrap() {
                "left" => desktop_api::Arm::Left,
                "right" => desktop_api::Arm::Right,
                _ => panic!("unknown source arm"),
            },
        };
        for (key, request) in [
            (
                "capture",
                desktop_api::EvidenceRequest::Capture {
                    observer: Observer::Omniscient,
                },
            ),
            (
                "outputs",
                desktop_api::EvidenceRequest::Outputs {
                    observer: Observer::Omniscient,
                },
            ),
        ] {
            let actual = desktop_api::evidence(
                &opened,
                source["binding"].as_str().unwrap(),
                &id,
                request,
                true,
            )
            .unwrap();
            assert_eq!(entry[key], actual);
        }
        let outputs = entry["outputs"]["body"]["outputs"].as_array().unwrap();
        let assessments = entry["assessments"].as_array().unwrap();
        assert_eq!(assessments.len(), outputs.len());
        for (ordinal, (assessment, output)) in assessments.iter().zip(outputs).enumerate() {
            assert_eq!(assessment["ordinal"], ordinal);
            for key in ["role", "bytes", "sha256"] {
                assert_eq!(assessment[key], output[key]);
            }
            assert!(assessment["rationale"].is_null());
            let dimensions: &[&str] = match output["role"].as_str().unwrap() {
                "director" => &["intent_fidelity", "scope_attribution"],
                "narrator" => &[
                    "outcome_fidelity",
                    "player_agency",
                    "voice",
                    "readability",
                    "repetition_pacing",
                    "enjoyment",
                ],
                _ => panic!("unknown original role"),
            };
            exact_keys(&assessment["judgments"], dimensions);
            assert!(assessment["judgments"]
                .as_object()
                .unwrap()
                .values()
                .all(|v| v == "not_assessed"));
        }
    }
}

fn check_pending_summary(summary: &Value, packet: &Value) {
    exact_keys(
        summary,
        &[
            "version",
            "scope",
            "rubric",
            "source",
            "review_sha256",
            "review_origin",
            "quality_accepted",
            "coverage",
            "original_outcomes",
            "roles",
            "limitations",
        ],
    );
    assert_eq!(summary["scope"], "locallore_role_review_summary");
    assert_eq!(summary["source"], packet["source"]);
    assert_eq!(summary["review_origin"], "reviewer_declared");
    assert_eq!(summary["quality_accepted"], false);
    let selected = packet["source"]["selected_turns"].as_u64().unwrap();
    assert_eq!(
        summary["coverage"],
        json!({"total_turns":12,"selected_turns":selected,"unselected_turns":12-selected,
        "selected_missing_capture":0,"selected_missing_outputs":0,"selected_without_outputs":0})
    );
    let entries = packet["entries"].as_array().unwrap();
    for (role, dimensions) in [("director", 2), ("narrator", 6)] {
        let attempts = entries
            .iter()
            .flat_map(|e| e["assessments"].as_array().unwrap())
            .filter(|a| a["role"] == role)
            .count();
        assert_eq!(
            summary["roles"][role],
            json!({"attempts":attempts,"reviewed_attempts":0,"dimensions":attempts*dimensions,
            "satisfactory":0,"concern":0,"not_assessed":attempts*dimensions})
        );
    }
    // Outcome denominators include unselected rows, not merely displayed prose.
    let mut phases = BTreeMap::<String, usize>::new();
    for entry in entries {
        *phases
            .entry(entry["source_row"]["phase"].as_str().unwrap().into())
            .or_default() += 1;
    }
    assert_eq!(
        summary["original_outcomes"]["phases"],
        serde_json::to_value(phases).unwrap()
    );
    assert_eq!(summary["original_outcomes"]["passed"], 12);
    assert_eq!(summary["original_outcomes"]["failed"], 0);
    assert_eq!(summary["original_outcomes"]["fallback"], 0);
}

#[test]
fn pending_template_and_summary_preserve_all_source_rows_and_deterministic_sample() {
    let (parent, run) = fixture("pending");
    let before = inventory(&run);
    for (name, options, selected) in [
        ("default", vec![], 4),
        ("one", vec!["--max-turns", "1"], 1),
        ("eight", vec!["--max-turns", "8"], 8),
    ] {
        let review = parent.join(format!("{name}.json"));
        success(cli("template", &run, &review, &options, true));
        let packet = read_json(&review);
        check_packet(&run, &packet, selected);
        let result = summary(&run, &review);
        check_pending_summary(&result, &packet);
        assert_eq!(result["review_sha256"], hash(&fs::read(&review).unwrap()));
        assert_eq!(inventory(&run), before);
    }
}

#[test]
fn partial_self_declared_ratings_are_counts_not_acceptance_or_published_notes() {
    let (parent, run) = fixture("ratings");
    let before = inventory(&run);
    let path = parent.join("review.json");
    success(cli("template", &run, &path, &[], true));
    let mut packet = read_json(&path);
    packet["reviewer"] = json!("PRIVATE_REVIEWER_CANARY");
    let mut roles = BTreeSet::new();
    for entry in packet["entries"].as_array_mut().unwrap() {
        for assessment in entry["assessments"].as_array_mut().unwrap() {
            let role = assessment["role"].as_str().unwrap().to_owned();
            if roles.insert(role.clone()) {
                let dimension = if role == "director" {
                    "intent_fidelity"
                } else {
                    "enjoyment"
                };
                assessment["judgments"][dimension] = json!("concern");
                assessment["rationale"] = json!("PRIVATE_RATIONALE_CANARY");
            }
        }
    }
    assert_eq!(
        roles,
        BTreeSet::from(["director".to_string(), "narrator".to_string()])
    );
    write_json(&path, &packet);
    let result = summary(&run, &path);
    for role in ["director", "narrator"] {
        assert_eq!(result["roles"][role]["reviewed_attempts"], 1);
        assert_eq!(result["roles"][role]["concern"], 1);
    }
    assert_eq!(result["quality_accepted"], false);
    let public = result.to_string();
    assert!(
        !public.contains("PRIVATE_REVIEWER_CANARY") && !public.contains("PRIVATE_RATIONALE_CANARY")
    );
    assert!(
        result.get("reviewer").is_none()
            && result.get("entries").is_none()
            && result.get("score").is_none()
    );
    // A note alone is not a rated attempt, even with a declared reviewer.
    for entry in packet["entries"].as_array_mut().unwrap() {
        for assessment in entry["assessments"].as_array_mut().unwrap() {
            for judgment in assessment["judgments"]
                .as_object_mut()
                .unwrap()
                .values_mut()
            {
                *judgment = json!("not_assessed");
            }
        }
    }
    write_json(&path, &packet);
    let notes_only = summary(&run, &path);
    for role in ["director", "narrator"] {
        assert_eq!(notes_only["roles"][role]["reviewed_attempts"], 0);
    }
    assert_eq!(inventory(&run), before);
}

#[test]
fn immutable_bindings_rows_output_order_and_payloads_cannot_be_relabelled() {
    let (parent, run) = fixture("binding");
    let before = inventory(&run);
    let template = parent.join("template.json");
    success(cli("template", &run, &template, &[], true));
    let original = read_json(&template);
    let mut variants = Vec::new();
    for (pointer, replacement) in [
        ("/source/snapshot_binding", json!("0".repeat(64))),
        ("/source/report_sha256", json!("0".repeat(64))),
        ("/source/lane", json!("native_current_policy_comparison")),
        ("/source/selected_turns", json!(1)),
        ("/entries/0/source_row/passed", json!(false)),
        ("/entries/0/turn", json!("foreign-turn")),
        ("/entries/0/assessments/0/role", json!("narrator")),
        ("/entries/0/assessments/0/ordinal", json!(1)),
        ("/entries/0/assessments/0/sha256", json!("0".repeat(64))),
        (
            "/entries/0/outputs/body/outputs/0/text",
            json!("fabricated output"),
        ),
        ("/quality_accepted", json!(true)),
    ] {
        let mut changed = original.clone();
        *changed.pointer_mut(pointer).expect("actual template field") = replacement;
        variants.push(changed);
    }
    let mut reordered = original.clone();
    reordered["entries"].as_array_mut().unwrap().swap(0, 1);
    variants.push(reordered);
    let mut raw_reordered = original.clone();
    raw_reordered["entries"][0]["assessments"]
        .as_array_mut()
        .unwrap()
        .swap(0, 1);
    variants.push(raw_reordered);
    for (index, changed) in variants.iter().enumerate() {
        let path = parent.join(format!("changed-{index}.json"));
        write_json(&path, changed);
        refused(cli("summarize", &run, &path, &[], true));
        assert_eq!(inventory(&run), before);
    }
}

#[test]
fn unknown_duplicate_judgments_and_unattributed_edits_refuse_without_source_changes() {
    let (parent, run) = fixture("schema");
    let before = inventory(&run);
    let template = parent.join("template.json");
    success(cli("template", &run, &template, &[], true));
    let original = read_json(&template);
    let mut variants = Vec::new();
    let mut unknown = original.clone();
    unknown["extra"] = json!("private");
    variants.push(unknown);
    for rating in [json!("excellent"), json!(true), json!(1), Value::Null] {
        let mut edited = original.clone();
        edited["reviewer"] = json!("reviewer");
        edited["entries"][0]["assessments"][0]["judgments"]["intent_fidelity"] = rating;
        variants.push(edited);
    }
    for reviewer in [
        Value::Null,
        json!(""),
        json!("x".repeat(49)),
        json!("非ASCII"),
        json!(true),
    ] {
        let mut edited = original.clone();
        edited["reviewer"] = reviewer;
        edited["entries"][0]["assessments"][0]["rationale"] =
            json!("a changed note requires attribution");
        variants.push(edited);
    }
    let mut dimension = original.clone();
    dimension["reviewer"] = json!("reviewer");
    dimension["entries"][0]["assessments"][0]["judgments"]["authority_to_commit"] =
        json!("satisfactory");
    variants.push(dimension);
    for (index, value) in variants.iter().enumerate() {
        let path = parent.join(format!("invalid-{index}.json"));
        write_json(&path, value);
        refused(cli("summarize", &run, &path, &[], true));
    }
    let serialized = serde_json::to_string(&original).unwrap();
    let duplicate = serialized.replacen("\"version\":1", "\"version\":1,\"version\":1", 1);
    assert_ne!(duplicate, serialized);
    let path = parent.join("duplicate.json");
    fs::write(&path, duplicate).unwrap();
    refused(cli("summarize", &run, &path, &[], true));
    assert_eq!(inventory(&run), before);
}

#[test]
fn consent_and_output_create_only_outside_source_rules_precede_review_authority() {
    let (parent, run) = fixture("consent");
    let before = inventory(&run);
    let missing = parent.join("PRIVATE_PATH_CANARY_missing");
    let output = parent.join("new.json");
    for command in ["template", "summarize"] {
        let denied_existing = cli(command, &run, &output, &[], false);
        let denied_missing = cli(command, &missing, &output, &[], false);
        assert_eq!(denied_existing.stdout, denied_missing.stdout);
        assert_eq!(denied_existing.stderr, denied_missing.stderr);
        refused(denied_existing);
        refused(denied_missing);
        assert!(!output.exists());
    }
    fs::write(&output, b"existing file must survive").unwrap();
    refused(cli("template", &run, &output, &[], true));
    assert_eq!(fs::read(&output).unwrap(), b"existing file must survive");
    let inside = run.join("forbidden-review.json");
    refused(cli("template", &run, &inside, &[], true));
    assert!(!inside.exists());
    for invalid in ["0", "9", "-1", "true", "1.5"] {
        refused(cli(
            "template",
            &run,
            &parent.join(format!("bad-{invalid}.json")),
            &["--max-turns", invalid],
            true,
        ));
    }
    assert_eq!(inventory(&run), before);
}

#[test]
fn corrupted_actual_recording_is_retained_but_never_exported_or_regenerated() {
    let (parent, run) = fixture("corrupt");
    let files = inventory(&run);
    let raw = files
        .files
        .keys()
        .find(|p| {
            p.extension().is_some_and(|s| s == "bin")
                && p.file_name().unwrap().to_string_lossy().starts_with("raw-")
        })
        .unwrap();
    let path = run.join(raw);
    let mut bytes = fs::read(&path).unwrap();
    bytes.extend_from_slice(b"CORRUPTED_CAPTURE_CANARY");
    fs::write(&path, bytes).unwrap();
    let corrupted = inventory(&run);
    let output = parent.join("refused.json");
    refused(cli("template", &run, &output, &[], true));
    assert!(!output.exists());
    assert_eq!(inventory(&run), corrupted);
    // The original public producer remains available and was never the mutation target.
    assert_eq!(
        snapshot(producer())["report"]["turns"]
            .as_array()
            .unwrap()
            .len(),
        12
    );
}

#[cfg(unix)]
#[test]
fn linked_source_and_output_parent_refuse_instead_of_following_them() {
    let (parent, run) = fixture("links");
    let before = inventory(&run);
    let alias = parent.join("run-alias");
    std::os::unix::fs::symlink(&run, &alias).unwrap();
    let output = parent.join("aliased.json");
    refused(cli("template", &alias, &output, &[], true));
    assert!(!output.exists());
    let actual_output_parent = parent.join("output");
    fs::create_dir(&actual_output_parent).unwrap();
    let output_alias = parent.join("output-alias");
    std::os::unix::fs::symlink(&actual_output_parent, &output_alias).unwrap();
    refused(cli(
        "template",
        &run,
        &output_alias.join("review.json"),
        &[],
        true,
    ));
    assert_eq!(fs::read_dir(actual_output_parent).unwrap().count(), 0);
    assert_eq!(inventory(&run), before);
}

#[cfg(windows)]
#[test]
fn dos_devices_and_ads_are_not_review_output_files() {
    let (parent, run) = fixture("windows-paths");
    let before = inventory(&run);
    // Merely pass these names to the trusted CLI. The test itself never opens
    // a Windows device/stream and never probes a network or UNC destination.
    for leaf in ["NUL", "NUL.txt", "COM1.txt", "review.json:stream"] {
        refused(cli("template", &run, &parent.join(leaf), &[], true));
    }
    assert_eq!(inventory(&run), before);
}
