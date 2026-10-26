// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen private protocol-3 selected regressions; source-only, UNCOMPILED/UNRUN.
//! Base cb391224; #29 claim6410543364. Root owns registration and execution.
//! Actual Host/Store/producer/Ledger only. No canonical SQL, invented receipt,
//! cost, capture, setup, model result, or production fault hook.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --lib local_lane::comparison::literal_v3::selected_v2::review_tests -- --nocapture --test-threads=1
use super::*;
use crate::local_lane::comparison::literal_v3 as source3;
use std::{collections::BTreeMap, sync::OnceLock};

const INDEX: usize = 4;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "locallore-selected2-private-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&path).unwrap();
    path
}

// Only call with all opaque owners for this root dropped (Windows run.lock).
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(relative, None).is_none());
                visit(root, &path, depth + 1, total, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(bytes)).is_none());
            }
        }
    }
    let mut result = BTreeMap::new();
    visit(root, root, 0, &mut 0, &mut result);
    result
}

fn unchanged(path: &Path, expected: &Inventory) {
    let actual = inventory(path);
    let changed: Vec<_> = actual
        .keys()
        .chain(expected.keys())
        .filter(|key| actual.get(*key) != expected.get(*key))
        .take(24)
        .collect();
    assert!(
        changed.is_empty(),
        "synthetic inventory changed: {changed:?}"
    );
}

fn copy(snapshot: &Inventory, target: &Path) {
    assert!(!target.exists());
    fs::create_dir(target).unwrap();
    for (relative, bytes) in snapshot {
        match bytes {
            None => fs::create_dir_all(target.join(relative)).unwrap(),
            Some(bytes) => fs::write(target.join(relative), bytes).unwrap(),
        }
    }
    unchanged(target, snapshot);
}

// A genuine failed first-left attempt causes divergent accepted histories.
// Every other attempt uses the normal protocol-3 construction/provider path.
fn original_source() -> &'static PathBuf {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE.get_or_init(|| {
        let source = root("actual-divergent-source").join("rollout");
        let manifest = source3::Manifest::new(
            ComparisonKind::ContinuousRollout,
            LaneFactory::ScriptedBaseline.profile().unwrap(),
            None,
        )
        .unwrap();
        let mut session =
            source3::Session3::open(&source, false, manifest, None, Instant::now()).unwrap();
        session.begin_invocations().unwrap();
        turn_execution::record_setup(
            &mut session.ledgers,
            turn_execution::Setup {
                version: 3,
                dir: &session.dir,
                key: &session.key,
                native: false,
                physical_ms: 0,
                status: "scripted",
                load: None,
            },
        )
        .unwrap();
        let corpus = suite().unwrap();
        let cancel = Cancellation::default();
        for index in 0..6 {
            for arm in [0, 1] {
                let began = Instant::now();
                let d = source.join(ARM_NAMES[arm]);
                let path = database(&d, index, ComparisonKind::ContinuousRollout);
                ensure_database(&path, corpus.seed(), &[]).unwrap();
                let factory = if index == 0 && arm == 0 {
                    LaneFactory::TestFault(TestFault::WrongCommand)
                } else {
                    LaneFactory::ScriptedBaseline
                };
                let turn = source3::execute_turn3(
                    source3::Job3 {
                        dir: &d,
                        path: &path,
                        index,
                        arm: ARM_NAMES[arm],
                        construction: source3::CONSTRUCTIONS[arm],
                        binding: &session.key,
                        step: &corpus.steps()[index],
                        factory: &factory,
                        cancel: &cancel,
                    },
                    &mut session.ledgers[arm],
                )
                .unwrap();
                if index == 0 && arm == 0 {
                    assert_eq!(turn.row.phase, "failed");
                    assert!(!turn.row.passed);
                    assert_eq!(turn.before_head, turn.after_head);
                    assert!(engine(&path, &corpus.seed().scope)
                        .unwrap()
                        .receipts()
                        .is_empty());
                } else {
                    assert_eq!(turn.row.phase, "committed");
                    assert!(turn.row.passed);
                }
                assert_eq!(turn.row.construction, v3::arm_descriptors()[arm]);
                let checkpoint: StoredTurn3 =
                    decode(&checkpoint_path(&d, index), 256 * 1024).unwrap();
                assert!(encode(&checkpoint).unwrap() == encode(&turn).unwrap());
                session.turns[arm].push(turn);
                session.ledgers[1 - arm]
                    .exclude_measured_interval(
                        began.elapsed().as_millis().min(u64::MAX as u128) as u64
                    )
                    .unwrap();
            }
        }
        saved(
            &source.join("scene-00.json"),
            &source3::scene_data3(&source, &session.key, 0).unwrap(),
            4096,
        )
        .unwrap();
        let report = session.finish().unwrap();
        assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
        assert_eq!(report.turns.iter().filter(|row| !row.passed).count(), 1);
        assert!(!report.quality_accepted);
        assert_eq!(source3::inspect_comparison(&source).unwrap(), report);
        source
    })
}

struct Fixture {
    root: PathBuf,
    source: PathBuf,
}
impl Fixture {
    fn new(label: &str) -> Self {
        let snapshot = inventory(original_source());
        let root = root(label);
        let source = root.join("source");
        copy(&snapshot, &source);
        Self { root, source }
    }
    fn plan(&self, client: &str) -> PreparedSelectedPlan {
        let reader = source3::desktop_api::open_read_only(&self.source).unwrap();
        let summary = source3::desktop_api::summary(&reader, true).unwrap();
        let binding = summary["binding"].as_str().unwrap().to_owned();
        drop(reader);
        prepare_selected(
            &self.source,
            &binding,
            &shared_read::RowId {
                turn: suite().unwrap().steps()[INDEX].id().into(),
                arm: shared_read::Arm::Left,
            },
            SelectedIntent {
                client_id: client.into(),
                lane: SelectedLane::ScriptedBaseline,
            },
            &Cancellation::default(),
        )
        .unwrap()
    }
}

#[test]
fn second_arm_real_unknown_reservations_refuse_before_either_arm_starts_or_bootstraps() {
    let fixture = Fixture::new("both-arm-budget");
    let source_before = inventory(&fixture.source);
    let plan = fixture.plan("selected2-private-both-budget");
    let initial = fixture.root.join("initial");
    let destination = new_destination(&plan, &initial).unwrap();
    let binding = destination.manifest.binding.clone();
    let right = initial.join("right");
    let corpus = suite().unwrap();
    let step = &corpus.steps()[INDEX];
    let mut ledger = Ledger::load(&right, &binding).unwrap();
    ledger.begin_invocation().unwrap();
    for admission in 0..27 {
        assert_eq!(
            ledger
                .admit(&format!("scene-{}", step.scene()), step.id())
                .unwrap(),
            admission
        );
        assert!(!right
            .join(format!("admission-{admission:02}-settled.json"))
            .exists());
    }
    ledger.finish().unwrap();
    let known: Settlement = decode(&right.join("invocation-00-settled.json"), 4096).unwrap();
    assert_eq!((known.index, known.roles), (0, 0));
    assert_eq!(known.binding, binding);
    drop(ledger);
    let persisted = Ledger::load(&right, &binding).unwrap();
    assert_eq!(
        (
            persisted.invocations,
            persisted.admissions,
            persisted.charged_roles
        ),
        (1, 27, 81)
    );
    assert_eq!(persisted.charged_ms, 27 * TURN_MS + known.ms);
    assert!(persisted.remaining() >= PREPARATION_MS);
    assert!(persisted.remaining().saturating_sub(PREPARATION_MS) < TURN_MS + CLEANUP_RESERVE_MS);
    drop(persisted);
    drop(destination);
    drop(plan);
    let before = inventory(&initial);
    assert!(inventory(&initial.join("left")).is_empty());
    let common = fixture.root.join("common-execute");
    let resumed = fixture.root.join("public-resume");
    copy(&before, &common);
    copy(&before, &resumed);

    // Public run_selected rejects any existing output first. Exercise its common
    // execution entry on the retained destination, plus public resume separately.
    let plan = fixture.plan("selected2-private-both-budget");
    let destination = open_destination(&common).unwrap();
    let work = inspect_work(&plan, &common, Instant::now()).unwrap();
    let common_error = execute(&plan, &destination, work, &Cancellation::default()).err();
    drop(destination);
    drop(plan);
    let resume_error = resume_selected(
        &resumed,
        &fixture.source,
        &binding,
        &Cancellation::default(),
    )
    .err();
    // Record both paths before asserting error kinds; neither may mutate first.
    unchanged(&fixture.source, &source_before);
    unchanged(&initial, &before);
    unchanged(&common, &before);
    unchanged(&resumed, &before);
    assert_eq!(common_error.as_deref(), Some("RunBudget"));
    assert_eq!(resume_error.as_deref(), Some("RunBudget"));
    for d in [&common, &resumed] {
        assert!(inventory(&d.join("left")).is_empty());
        for arm in ARM_NAMES {
            assert!(!database(&d.join(arm), INDEX, ComparisonKind::ContinuousRollout).exists());
            assert!(!checkpoint_path(&d.join(arm), INDEX).exists());
        }
    }
}

#[test]
fn selected_move_preserves_actual_divergent_per_arm_prefix_request_and_v3_construction() {
    let fixture = Fixture::new("genuine-divergent-prefixes");
    let corpus = suite().unwrap();
    let step = &corpus.steps()[INDEX];
    let mut before = Vec::new();
    let mut requests = Vec::new();
    let mut rows = Vec::new();
    for arm in ARM_NAMES {
        let d = fixture.source.join(arm);
        let cp: StoredTurn3 = decode(&checkpoint_path(&d, INDEX), 256 * 1024).unwrap();
        assert_eq!(cp.version, 3);
        assert_eq!(cp.row.phase, "committed");
        assert!(cp.row.passed && cp.row.roles_known && cp.row.construction_matches);
        let full = engine(
            &database(&d, INDEX, ComparisonKind::ContinuousRollout),
            &corpus.seed().scope,
        )
        .unwrap();
        let cut = full.at_revision(cp.before_head).unwrap();
        let request = step.request(&cut);
        assert_eq!(request, cp.request);
        assert_eq!(
            v2::semantic_input(&cut, &request).unwrap(),
            cp.row.input_semantic_sha256
        );
        before.push(cut);
        requests.push(request);
        rows.push(cp.row);
    }
    assert_eq!(before[0].receipts().len() + 1, before[1].receipts().len());
    assert!(before[0]
        .receipts()
        .iter()
        .all(|r| r.request().turn != corpus.steps()[0].id()));
    assert!(before[1]
        .receipts()
        .iter()
        .any(|r| r.request().turn == corpus.steps()[0].id()));
    assert_ne!(before[0].revision(), before[1].revision());
    assert_ne!(requests[0], requests[1]);
    assert_ne!(rows[0].input_semantic_sha256, rows[1].input_semantic_sha256);
    assert_ne!(before[0].canonical_bytes(), before[1].canonical_bytes());
    let source_before = inventory(&fixture.source);
    let plan = fixture.plan("selected2-private-divergent");
    for arm in 0..2 {
        assert!(plan.before[arm].receipts() == before[arm].receipts());
        assert!(
            plan.before[arm].accepted_history_basis().unwrap()
                == before[arm].accepted_history_basis().unwrap()
        );
    }
    let target = fixture.root.join("selected");
    let report =
        serde_json::to_value(run_selected(plan, &target, &Cancellation::default()).unwrap())
            .unwrap();
    assert_eq!(report["version"], 2);
    assert_eq!(report["source_protocol_version"], 3);
    assert_eq!(report["source_kind"], "continuous_rollout");
    assert!(report["source_reference_sha256"].is_null());
    assert_eq!(
        report["arms"],
        serde_json::to_value(v3::arm_descriptors()).unwrap()
    );
    assert_eq!(
        report["selection"],
        json!({"turn":step.id(),"clicked_arm":"left","index":INDEX})
    );
    assert_eq!(report["rows"].as_array().unwrap().len(), 2);
    assert_eq!(report["completed"], true);
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["quality_accepted"], false);
    for arm in 0..2 {
        let input = &report["source_inputs"][arm];
        assert_eq!(input["arm"], ARM_NAMES[arm]);
        assert_eq!(
            input["scope"],
            serde_json::to_value(before[arm].scope()).unwrap()
        );
        assert_eq!(input["before_head"], before[arm].revision());
        assert_eq!(
            input["request"],
            serde_json::to_value(&requests[arm]).unwrap()
        );
        assert_eq!(
            input["prefix_sha256"],
            digest(&encode(before[arm].receipts()).unwrap())
        );
        assert_eq!(
            input["input_semantic_sha256"],
            rows[arm].input_semantic_sha256
        );
        let row: TurnReportV3 = serde_json::from_value(report["rows"][arm].clone()).unwrap();
        assert_eq!(row.construction, v3::arm_descriptors()[arm]);
        assert_eq!(row.turn, step.id());
        assert_eq!(row.arm, ARM_NAMES[arm]);
        assert_eq!(row.phase, "committed");
        assert!(row.passed && row.roles_known && !row.recovered_without_checkpoint);
        assert!(row.construction_matches);
        assert_eq!(
            row.construction_evidence_status,
            if arm == 0 {
                v3::ConstructionEvidenceStatusV3::ValidatedLiteral
            } else {
                v3::ConstructionEvidenceStatusV3::ValidatedRelevant
            }
        );
        assert_eq!(row.roles, 2);
        assert_eq!(row.input_semantic_sha256, rows[arm].input_semantic_sha256);
        let d = target.join(ARM_NAMES[arm]);
        let full = engine(
            &database(&d, INDEX, ComparisonKind::ContinuousRollout),
            &corpus.seed().scope,
        )
        .unwrap();
        let cut = full.at_revision(before[arm].revision()).unwrap();
        assert_eq!(cut.canonical_bytes(), before[arm].canonical_bytes());
        assert!(cut.receipts() == before[arm].receipts());
        assert!(
            cut.accepted_history_basis().unwrap() == before[arm].accepted_history_basis().unwrap()
        );
        assert_eq!(full.receipts().len(), before[arm].receipts().len() + 1);
        assert_eq!(full.receipts().last().unwrap().request(), &requests[arm]);
        let cp: StoredTurn3 = decode(&checkpoint_path(&d, INDEX), 256 * 1024).unwrap();
        assert_eq!(cp.version, 3);
        assert_eq!(cp.index, INDEX);
        assert_eq!(cp.before_head, before[arm].revision());
        assert_eq!(cp.request, requests[arm]);
        assert_eq!(cp.row, row);
        for earlier in 0..INDEX {
            assert!(!checkpoint_path(&d, earlier).exists());
        }
        let ledger = Ledger::load(&d, report["binding"].as_str().unwrap()).unwrap();
        assert_eq!((ledger.invocations, ledger.admissions), (1, 1));
    }
    let target_before = inventory(&target);
    assert_eq!(
        serde_json::to_value(inspect_selected(&target).unwrap()).unwrap(),
        report
    );
    unchanged(&target, &target_before);
    unchanged(&fixture.source, &source_before);
}

#[test]
fn actual_half_progress_cancels_then_resumes_only_the_missing_arm() {
    struct Reset;
    impl Drop for Reset {
        fn drop(&mut self) {
            CANCEL_AFTER_ARM.with(|flag| flag.set(false));
        }
    }
    let fixture = Fixture::new("cancel-half");
    let source_before = inventory(&fixture.source);
    let plan = fixture.plan("selected2-cancel-half");
    let target = fixture.root.join("selected");
    let cancel = Cancellation::default();
    CANCEL_AFTER_ARM.with(|flag| flag.set(true));
    let reset = Reset;
    let paused = serde_json::to_value(run_selected(plan, &target, &cancel).unwrap()).unwrap();
    drop(reset);
    assert!(cancel.is_cancelled());
    assert_eq!(paused["completed"], false);
    assert_eq!(paused["rows"].as_array().unwrap().len(), 1);
    assert_eq!(paused["rows"][0]["arm"], "left");
    assert_eq!(paused["rows"][0]["phase"], "committed");
    let binding = paused["binding"].as_str().unwrap();
    let left = target.join("left");
    let right = target.join("right");
    let left_before = inventory(&left);
    assert_eq!(Ledger::load(&left, binding).unwrap().admissions, 1);
    assert_eq!(Ledger::load(&right, binding).unwrap().admissions, 0);
    assert!(!database(&right, INDEX, ComparisonKind::ContinuousRollout).exists());
    assert!(!checkpoint_path(&right, INDEX).exists());
    let completed = serde_json::to_value(
        resume_selected(&target, &fixture.source, binding, &Cancellation::default()).unwrap(),
    )
    .unwrap();
    assert_eq!(completed["completed"], true);
    assert_eq!(completed["rows"].as_array().unwrap().len(), 2);
    assert_eq!(completed["rows"][0], paused["rows"][0]);
    assert_eq!(Ledger::load(&left, binding).unwrap().admissions, 1);
    assert_eq!(Ledger::load(&right, binding).unwrap().admissions, 1);
    let actual_left = inventory(&left);
    // Another invocation records measured preparation; the completed turn and
    // actual canonical/raw/admission bytes must never be rewritten or repeated.
    for (path, bytes) in &left_before {
        if !path
            .file_name()
            .unwrap()
            .to_string_lossy()
            .starts_with("invocation-")
        {
            assert_eq!(actual_left.get(path), Some(bytes));
        }
    }
    let completed_before = inventory(&target);
    assert_eq!(
        serde_json::to_value(
            resume_selected(&target, &fixture.source, binding, &Cancellation::default()).unwrap()
        )
        .unwrap(),
        completed
    );
    unchanged(&target, &completed_before);
    unchanged(&fixture.source, &source_before);
}
