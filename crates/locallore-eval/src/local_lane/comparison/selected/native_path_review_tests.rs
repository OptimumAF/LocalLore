// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen native-selected preflight/model-free oracles; SOURCE-ONLY / UNRUN.
//! Actual scripted Host/Store sources, never native model generation evidence.
//! Root registers this module after freezing the new public interfaces.
#![cfg(feature = "local-model")]
use super::*;
use std::{cell::Cell, collections::BTreeMap, sync::OnceLock};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn owned_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-native-selected-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
    ));
    fs::create_dir(&root).unwrap();
    root
}
// Only after every opaque source/destination capability has dropped.
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
fn clone_source(original: &Path, label: &str) -> (PathBuf, PathBuf) {
    let original = inventory(original);
    let root = owned_root(label);
    let source = root.join("source");
    fs::create_dir(&source).unwrap();
    for (relative, content) in &original {
        match content {
            None => fs::create_dir_all(source.join(relative)).unwrap(),
            Some(bytes) => fs::write(source.join(relative), bytes).unwrap(),
        }
    }
    assert!(inventory(&source) == original);
    (root, source)
}
fn ordinary_source() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE
        .get_or_init(|| {
            let root = owned_root("real-scripted-source");
            let source = root.join("rollout");
            let report = run_comparison(
                &source,
                false,
                ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                2,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!((report.completed_scenes, report.turns.len()), (2, 24));
            assert!(report.turns.iter().all(|row| row.passed));
            source
        })
        .as_path()
}
fn source_binding(source: &Path) -> String {
    let opened = desktop_api::open_read_only(source).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    let binding = summary["binding"].as_str().unwrap().to_owned();
    drop(opened);
    binding
}
fn native_plan(source: &Path, index: usize, client: &str) -> PreparedSelectedPlan {
    let corpus = suite().unwrap();
    prepare_selected(
        source,
        &source_binding(source),
        &desktop_api::RowId {
            turn: corpus.steps()[index].id().into(),
            arm: desktop_api::Arm::Right,
        },
        SelectedIntent {
            client_id: client.into(),
            lane: SelectedLane::ApprovedNative,
        },
        &Cancellation::default(),
    )
    .unwrap()
}
struct ForbiddenAssets;
impl SelectedNativeReservation for ForbiddenAssets {
    fn assets(&self) -> crate::local_lane::NativeAssets<'_> {
        panic!("this preflight/model-free path must not access native assets");
    }
    fn retain_uncertain(
        &mut self,
        _owner: Arc<Mutex<locallore_local_runtime::LocalRuntime>>,
    ) -> std::result::Result<(), Arc<Mutex<locallore_local_runtime::LocalRuntime>>> {
        panic!("this path must not create a runtime needing handoff");
    }
}
fn native_error(
    result: std::result::Result<SelectedComparisonReportV1, SelectedNativeFailure<ForbiddenAssets>>,
) -> String {
    match result {
        Ok(_) => panic!("expected native-selected refusal"),
        Err(failure) => {
            assert!(!failure.cleanup_uncertain());
            let code = failure.code().to_owned();
            assert!(!code.is_empty() && code.len() <= 96);
            assert!(code
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_'));
            code
        }
    }
}

#[test]
fn native_callback_and_paths_refuse_without_assets_new_destination_or_source_mutation() {
    let (root, source) = clone_source(ordinary_source(), "callback-paths");
    let corpus = suite().unwrap();
    let accepted = 4;
    let guard = corpus
        .steps()
        .iter()
        .position(|step| matches!(step.expected(), protocol::Expected::GuardRejected(_)))
        .unwrap();
    let original = inventory(&source);
    for index in [accepted, guard] {
        let plan = native_plan(&source, index, &format!("native-callback-{index}"));
        if index == accepted {
            for before in &plan.before {
                assert!(protocol::reference_proposal(before, &corpus.steps()[index]).is_ok());
            }
        }
        let destination = root.join(format!("refused-{index}"));
        let calls = Cell::new(0);
        let code = native_error(run_native_selected(
            plan,
            &destination,
            &Cancellation::default(),
            || {
                calls.set(calls.get() + 1);
                Err::<ForbiddenAssets, _>("RunBudget".into())
            },
        ));
        assert_eq!(code, "RunBudget");
        assert_eq!(
            calls.get(),
            1,
            "viable and Core guard work both require reservation"
        );
        assert!(!destination.exists());
        assert!(inventory(&source) == original);
    }
    let raw = "C:\\synthetic-private\\secret-model.gguf\nPRIVATE-OUTPUT";
    let plan = native_plan(&source, accepted, "native-callback-redaction");
    let destination = root.join("redacted-refusal");
    let result = run_native_selected(plan, &destination, &Cancellation::default(), || {
        Err::<ForbiddenAssets, _>(raw.into())
    });
    if let Err(failure) = &result {
        assert!(!format!("{failure:?}").contains("synthetic-private"));
        assert!(failure
            .cause()
            .is_none_or(|cause| !cause.contains("PRIVATE")));
    }
    assert_eq!(native_error(result), "SelectedExecution");
    assert!(!destination.exists());
    assert!(inventory(&source) == original);

    let existing = root.join("already-exists");
    fs::create_dir(&existing).unwrap();
    fs::write(
        existing.join("owned-marker"),
        b"fixed synthetic destination",
    )
    .unwrap();
    for (destination, expected) in [
        (source.join("nested-output"), "SourceDestinationOverlap"),
        (existing, "OutputExists"),
    ] {
        let before = inventory(&root);
        let calls = Cell::new(0);
        let plan = native_plan(&source, accepted, "native-path-refusal");
        let code = native_error(run_native_selected(
            plan,
            &destination,
            &Cancellation::default(),
            || {
                calls.set(calls.get() + 1);
                Err::<ForbiddenAssets, _>("RunBudget".into())
            },
        ));
        assert_eq!(code, expected);
        assert_eq!(calls.get(), 0);
        assert!(inventory(&root) == before);
    }
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn native_fresh_source_rejects_unselected_actual_capture_drift_before_reservation() {
    let (root, source) = clone_source(ordinary_source(), "source-drift");
    let mut expected = inventory(&source);
    let plan = native_plan(&source, 4, "native-unselected-capture");
    let untouched: StoredTurn =
        decode(&checkpoint_path(&source.join("left"), 4), 256 * 1024).unwrap();
    let selected_file = checkpoint_path(&source.join("left"), 4);
    let selected_bytes = fs::read(&selected_file).unwrap();
    let unselected: StoredTurn =
        decode(&checkpoint_path(&source.join("left"), 0), 256 * 1024).unwrap();
    assert_ne!(unselected.index, untouched.index);
    let capture = source.join("left").join(unselected.capture_file.unwrap());
    let mut body: Value = decode(&capture, v2::MAX_PRIVATE_CAPTURE + 4096).unwrap();
    assert_eq!(body["status"], "ok");
    body["status"] = json!("rejected");
    fs::write(&capture, encode(&body).unwrap()).unwrap();
    // Keep the exact deliberate fault while the prepared cap owns its lock.
    // Read the complete inventory only after consuming run drops that cap.
    let faulted_capture = fs::read(&capture).unwrap();
    assert!(expected
        .insert(
            capture.strip_prefix(&source).unwrap().to_owned(),
            Some(faulted_capture.clone())
        )
        .is_some());
    let destination = root.join("must-not-exist");
    let calls = Cell::new(0);
    let code = native_error(run_native_selected(
        plan,
        &destination,
        &Cancellation::default(),
        || {
            calls.set(calls.get() + 1);
            Err::<ForbiddenAssets, _>("RunBudget".into())
        },
    ));
    assert_eq!(code, "CheckpointEvidenceMismatch");
    assert_eq!(calls.get(), 0);
    assert!(!destination.exists());
    assert_eq!(fs::read(capture).unwrap(), faulted_capture);
    assert_eq!(fs::read(selected_file).unwrap(), selected_bytes);
    // The corrupted source remains as evidence; no repair, reseal or retagging.
    assert!(inventory(&source) == expected);
}

fn dependency_source(source: &Path) {
    let corpus = suite().unwrap();
    assert_eq!(corpus.steps()[1].text(), "I learn beacon.");
    assert_eq!(corpus.steps()[3].text(), "I use beacon.");
    let manifest = RunManifest::new(
        ComparisonKind::ContinuousRollout,
        LaneFactory::ScriptedBaseline.profile().unwrap(),
        false,
        None,
    )
    .unwrap();
    let mut session =
        ComparisonSession::open_at(source, false, manifest, None, Instant::now()).unwrap();
    session.setup(false, 0, "scripted", None).unwrap();
    let cancel = Cancellation::default();
    for index in 0..6 {
        for (arm, arm_name) in ARM_NAMES.iter().enumerate() {
            let directory = source.join(arm_name);
            let path = database(&directory, index, ComparisonKind::ContinuousRollout);
            ensure_database(&path, corpus.seed(), &[]).unwrap();
            let factory = if index == 1 {
                LaneFactory::TestFault(TestFault::WrongCommand)
            } else {
                LaneFactory::ScriptedBaseline
            };
            let turn = execute_turn(
                TurnJob {
                    dir: &directory,
                    path: &path,
                    index,
                    arm: arm_name,
                    policy: POLICIES[arm],
                    binding: &session.key,
                    step: &corpus.steps()[index],
                    factory: &factory,
                    cancel: &cancel,
                },
                &mut session.ledgers[arm],
            )
            .unwrap();
            if index == 1 {
                assert_eq!(turn.row.phase, "failed");
                assert!(turn.row.actual_receipt_sha256.is_none());
            } else if index == 3 {
                assert_eq!(turn.row.phase, "not_run_dependency");
                assert_eq!(turn.before_head, turn.after_head);
            } else {
                assert_eq!(turn.row.phase, "committed");
            }
            // Some legacy direct paths return a pure row; use the same bounded
            // existing checkpoint writer as the ordinary comparison loop.
            if !checkpoint_path(&directory, index).exists() {
                saved(&checkpoint_path(&directory, index), &turn, 256 * 1024).unwrap();
            }
            session.turns[arm].push(turn);
        }
    }
    saved(
        &source.join("scene-00.json"),
        &scene_data(source, &session.key, 0).unwrap(),
        4096,
    )
    .unwrap();
    let report = session.finish_and_publish().unwrap();
    assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
    drop(session);
    assert!(inspect_comparison(source).is_ok());
}

#[test]
fn native_both_arm_dependencies_and_completed_resume_never_reserve_or_access_assets() {
    let root = owned_root("dependency-only");
    let source = root.join("actual-source");
    dependency_source(&source);
    let source_files = inventory(&source);
    let plan = native_plan(&source, 3, "native-dependency-only");
    let original_inputs = plan.manifest.source_inputs.clone();
    let before = plan.before.clone();
    let destination = root.join("isolated-native-target");
    let calls = Cell::new(0);
    let result = run_native_selected(plan, &destination, &Cancellation::default(), || {
        calls.set(calls.get() + 1);
        Err::<ForbiddenAssets, _>("RunBudget".into())
    });
    let report = match result {
        Ok(report) => report,
        Err(failure) => panic!("dependency-only refused with fixed code {}", failure.code()),
    };
    assert_eq!(calls.get(), 0);
    assert!(report.completed && !report.quality_accepted);
    assert_eq!(report.lane, "native_selected_case");
    assert!(report.profile == native_profile().unwrap());
    assert!(report.source_profile == LaneFactory::ScriptedBaseline.profile().unwrap());
    assert_eq!(report.physical_setups, 0);
    assert!(report.physical_setup_ms.is_none() && report.native_load.is_none());
    assert_eq!(report.rows.len(), 2);
    for (arm, row) in report.rows.iter().enumerate() {
        assert_eq!(row.arm, ARM_NAMES[arm]);
        assert_eq!(row.policy, POLICIES[arm]);
        assert_eq!(row.phase, "not_run_dependency");
        assert!(row.roles_known && row.roles == 0 && row.admission.is_none());
        assert!(!row.recovered_without_checkpoint && !row.passed);
        assert!(row.role_metrics.is_none() && row.actual_receipt_sha256.is_none());
        let checkpoint: StoredTurn = decode(
            &checkpoint_path(&destination.join(ARM_NAMES[arm]), 3),
            256 * 1024,
        )
        .unwrap();
        assert!(checkpoint.request == original_inputs[arm].request);
        assert_eq!(checkpoint.before_head, original_inputs[arm].before_head);
        assert_eq!(checkpoint.after_head, original_inputs[arm].before_head);
        let actual = engine(
            &database(
                &destination.join(ARM_NAMES[arm]),
                3,
                ComparisonKind::ContinuousRollout,
            ),
            before[arm].scope(),
        )
        .unwrap();
        assert!(actual.receipts() == before[arm].receipts());
        assert!(
            actual.accepted_history_basis().unwrap()
                == before[arm].accepted_history_basis().unwrap()
        );
        assert!(fs::read_dir(destination.join(ARM_NAMES[arm]))
            .unwrap()
            .all(|entry| !entry
                .unwrap()
                .file_name()
                .to_str()
                .unwrap()
                .starts_with("admission-")));
    }
    assert!(inventory(&source) == source_files);
    let destination_files = inventory(&destination);
    let original_report = serde_json::to_value(&report).unwrap();
    let resumed = resume_native_selected(
        &destination,
        &source,
        &report.binding,
        &Cancellation::default(),
        || {
            calls.set(calls.get() + 1);
            Err::<ForbiddenAssets, _>("RunBudget".into())
        },
    );
    let resumed = match resumed {
        Ok(report) => report,
        Err(failure) => panic!("completed model-free resume refused: {}", failure.code()),
    };
    assert_eq!(calls.get(), 0);
    assert!(serde_json::to_value(resumed).unwrap() == original_report);
    assert!(inventory(&destination) == destination_files);
    assert!(inventory(&source) == source_files);
    fs::remove_dir_all(root).unwrap();
}
