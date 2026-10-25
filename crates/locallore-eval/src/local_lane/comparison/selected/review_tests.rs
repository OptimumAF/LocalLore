// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Four frozen private selected-state groups, source-only UNCOMPILED/UNRUN.
//! Base f1377ea7; #29 claim6395224217. Root owns module registration and execution.
//! Actual Core/Store/scripted producers and existing private fault/clock seams;
//! no public fault port, fabricated receipt, SQL writer or changed corpus/budget.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --lib local_lane::comparison::selected::review_tests -- --nocapture --test-threads=1
use super::*;
use std::{collections::BTreeMap, sync::{atomic::{AtomicU64, Ordering}, OnceLock}};

const SELECTED_INDEX: usize = 4;
static NEXT: AtomicU64 = AtomicU64::new(0);
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn owned_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-state-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&root).unwrap();
    root
}

// Only call after all source/destination run.lock owners have dropped. Capture
// empty directories too, so an early write cannot hide behind identical files.
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, current: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(current).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let meta = fs::symlink_metadata(&path).unwrap();
            assert!(!meta.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if meta.is_dir() {
                assert!(out.insert(relative, None).is_none());
                walk(root, &path, depth + 1, total, out);
            } else {
                assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(&path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(bytes)).is_none());
            }
        }
    }
    let mut result = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}

fn shared_paired_source() -> &'static PathBuf {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE.get_or_init(|| {
        let root = owned_root("actual-producers");
        let reference_dir = root.join("reference");
        let original = prepare_reference(&reference_dir, &Cancellation::default()).unwrap();
        assert_eq!((original.accepted, original.guard_only, original.roles), (21, 3, 42));
        let reference = open_reference(&reference_dir).unwrap();
        let paired = root.join("paired");
        let actual = run_comparison(&paired, false, ComparisonKind::PairedSnapshots,
            &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, Some(&reference)).unwrap();
        assert_eq!(actual.completed_scenes, 1);
        assert_eq!(actual.turns.len(), 12);
        assert!(actual.turns.iter().all(|row| row.passed));
        paired
    })
}

struct Fixture { root: PathBuf, source: PathBuf }
impl Fixture {
    fn new(label: &str) -> Self {
        let original = inventory(shared_paired_source());
        let root = owned_root(label);
        let source = root.join("source");
        fs::create_dir(&source).unwrap();
        for (path, bytes) in &original {
            match bytes {
                None => fs::create_dir_all(source.join(path)).unwrap(),
                Some(bytes) => fs::write(source.join(path), bytes).unwrap(),
            }
        }
        assert_eq!(inventory(&source), original, "copied actual producer bytes, no relabelling");
        Self { root, source }
    }
    fn prepare(&self, client: &str) -> PreparedSelectedPlan {
        let opened = desktop_api::open_read_only(&self.source).unwrap();
        let summary = desktop_api::summary(&opened, true).unwrap();
        let binding = summary["binding"].as_str().unwrap().to_owned();
        drop(opened);
        let corpus = suite().unwrap();
        prepare_selected(&self.source, &binding, &desktop_api::RowId {
            turn: corpus.steps()[SELECTED_INDEX].id().into(), arm: desktop_api::Arm::Right,
        }, SelectedIntent { client_id: client.into(), lane: SelectedLane::ScriptedBaseline },
            &Cancellation::default()).unwrap()
    }
}

fn fixed_error<T>(result: Result<T>) -> String {
    let error = match result { Ok(_) => panic!("expected fixed refusal"), Err(error) => error };
    assert!(!error.is_empty() && error.len() <= 96);
    assert!(error.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_'));
    error
}

#[test]
fn unselected_required_capture_drift_refuses_before_destination_and_never_repairs_source() {
    let fixture = Fixture::new("unselected-capture");
    let before = inventory(&fixture.source);
    let plan = fixture.prepare("state-whole-source");
    assert_eq!(plan.manifest.selection.index, SELECTED_INDEX);
    let selected_cp = checkpoint_path(&fixture.source.join("left"), SELECTED_INDEX);
    let selected_bytes = fs::read(&selected_cp).unwrap();
    let untouched_selected: StoredTurn = decode(&selected_cp, 256 * 1024).unwrap();
    let selected_capture = fixture.source.join("left")
        .join(untouched_selected.capture_file.as_ref().expect("selected actual capture"));
    let selected_capture_bytes = fs::read(&selected_capture).unwrap();
    let unselected: StoredTurn = decode(&checkpoint_path(&fixture.source.join("left"), 0), 256 * 1024).unwrap();
    assert_eq!(unselected.index, 0);
    assert_ne!(unselected.index, plan.manifest.selection.index);
    let capture = fixture.source.join("left")
        .join(unselected.capture_file.as_ref().expect("unselected required actual capture"));
    let mut changed: Value = decode(&capture, v2::MAX_PRIVATE_CAPTURE + 4096).unwrap();
    assert_eq!(changed["status"], "ok");
    // Valid JSON but invalid actual retained capture; do not reseal the source
    // checkpoint/report/hash or repair anything to make inspection succeed.
    changed["status"] = json!("rejected");
    let corrupted = encode(&changed).unwrap();
    assert!(corrupted.len() <= v2::MAX_PRIVATE_CAPTURE + 4096);
    fs::write(&capture, &corrupted).unwrap();
    assert_eq!(fs::read(&selected_cp).unwrap(), selected_bytes);
    assert_eq!(fs::read(&selected_capture).unwrap(), selected_capture_bytes);
    let mut faulted_expected = before;
    let relative = capture.strip_prefix(&fixture.source).unwrap().to_owned();
    assert!(faulted_expected.insert(relative, Some(corrupted.clone())).is_some());
    let destination = fixture.root.join("must-not-exist");
    let result = run_selected(plan, &destination, &Cancellation::default());
    // Public run consumed/dropped the opaque source lock even on refusal.
    assert!(!destination.exists(), "whole-source fresh preflight precedes destination creation");
    assert_eq!(inventory(&fixture.source), faulted_expected, "retain exactly the faulted owned source");
    assert_eq!(fs::read(&capture).unwrap(), corrupted);
    assert_eq!(fixed_error(result), "CheckpointEvidenceMismatch");
}

#[test]
fn exhausted_entry_origin_refuses_before_invocations_admissions_or_provider_work() {
    let fixture = Fixture::new("entry-clock");
    let source_before = inventory(&fixture.source);
    let plan = fixture.prepare("state-entry-clock");
    let destination_path = fixture.root.join("selected");
    let destination = new_destination(&plan, &destination_path).unwrap();
    drop(destination);
    let destination_before = inventory(&destination_path);
    assert!(inventory(&destination_path.join("left")).is_empty());
    assert!(inventory(&destination_path.join("right")).is_empty());
    let reopened = open_destination(&destination_path).unwrap();
    let expired = Instant::now().checked_sub(Duration::from_millis(MAX_ACTIVE_MS.checked_add(1).unwrap())).unwrap();
    let result = execute_selected(&plan, &reopened, &Cancellation::default(), expired);
    drop(reopened);
    drop(plan);
    assert_eq!(inventory(&destination_path), destination_before,
        "no invocation/admission/raw/checkpoint/Store creation after an exhausted entry origin");
    assert_eq!(inventory(&fixture.source), source_before);
    assert_eq!(fixed_error(result), "RunBudget");
}

#[test]
fn unknown_preparation_reservations_survive_refusal_without_other_arm_ledger_mutation() {
    let fixture = Fixture::new("unknown-preparation");
    let source_before = inventory(&fixture.source);
    let plan = fixture.prepare("state-unknown-preparation");
    let destination_path = fixture.root.join("selected");
    let destination = new_destination(&plan, &destination_path).unwrap();
    let binding = destination.manifest.binding.clone();
    let left = destination_path.join("left");
    let mut reservations = 0;
    // Each actual begin is deliberately left unknown, like interrupted native
    // workflow setup. No invented settlement/cost/role files and no fake clock.
    loop {
        let mut ledger = Ledger::load(&left, &binding).unwrap();
        match ledger.begin_invocation() {
            Ok(()) => {
                reservations += 1;
                assert!(reservations <= 32, "bounded actual invocation limit");
                assert!(!left.join(format!("invocation-{:02}-settled.json", reservations - 1)).exists());
            }
            Err(error) => { assert_eq!(error, "RunBudget"); break; }
        }
    }
    assert!(reservations > 0);
    let exhausted = Ledger::load(&left, &binding).unwrap();
    assert_eq!(exhausted.invocations, reservations);
    assert_eq!(exhausted.charged_ms, PREPARATION_MS * u64::try_from(reservations).unwrap());
    assert_eq!((exhausted.admissions, exhausted.charged_roles), (0, 0));
    assert!(exhausted.remaining() < PREPARATION_MS);
    drop(exhausted);
    drop(destination);
    drop(plan);
    let before = inventory(&destination_path);
    assert!(inventory(&destination_path.join("right")).is_empty());
    let result = resume_selected(&destination_path, &fixture.source, &binding, &Cancellation::default());
    assert_eq!(inventory(&destination_path), before, "unknown charges cannot be refunded or move the right ledger");
    assert_eq!(inventory(&fixture.source), source_before);
    assert_eq!(fixed_error(result), "RunBudget");
    let after = Ledger::load(&left, &binding).unwrap();
    assert_eq!(after.invocations, reservations);
    assert_eq!(after.charged_ms, PREPARATION_MS * u64::try_from(reservations).unwrap());
}

fn turn_work_inventory(arm: &Path) -> Inventory {
    inventory(arm).into_iter().filter(|(path, _)| {
        // Exclude only legal root-level invocation reservation/settlement
        // names, not arbitrary new files sharing an invocation- prefix.
        !(0..32).any(|index| path == &PathBuf::from(format!("invocation-{index:02}.json"))
            || path == &PathBuf::from(format!("invocation-{index:02}-settled.json")))
    }).collect()
}

fn terminal(path: &Path, request: &Request) -> (Request, locallore_storage::TurnPhase, Option<Vec<u8>>) {
    let mut store = Store::open_read_only(path).unwrap();
    let actual = store.lookup_turn(&request.scope, &request.turn).unwrap();
    (actual.request, actual.phase, actual.receipt.map(|receipt| encode(&receipt).unwrap()))
}

#[test]
fn failed_finished_left_is_preserved_while_only_missing_right_runs_and_completed_retry_is_read_only() {
    let fixture = Fixture::new("failed-half");
    let source_before = inventory(&fixture.source);
    let plan = fixture.prepare("state-failed-half");
    let destination_path = fixture.root.join("selected");
    let destination = new_destination(&plan, &destination_path).unwrap();
    let binding = destination.manifest.binding.clone();
    let left = destination_path.join("left");
    let index = destination.manifest.selection.index;
    assert_eq!(index, SELECTED_INDEX);
    let corpus = suite().unwrap();
    let step = &corpus.steps()[index];
    let right_request = destination.manifest.source_inputs[1].request.clone();
    let left_database = database(&left, index, destination.manifest.source_kind);
    ensure_database(&left_database, corpus.seed(), plan.before[0].receipts()).unwrap();
    let mut ledger = Ledger::load(&left, &binding).unwrap();
    ledger.begin_invocation().unwrap();
    let failed = execute_turn(TurnJob {
        dir: &left, path: &left_database, index, arm: ARM_NAMES[0], policy: POLICIES[0],
        binding: &binding, step, factory: &LaneFactory::TestFault(TestFault::WrongCommand),
        cancel: &Cancellation::default(),
    }, &mut ledger).unwrap();
    assert_eq!(failed.row.phase, "failed", "actual wrong-command Host/Store outcome, no invented failure cause");
    assert!(!failed.row.passed);
    assert_eq!(failed.request, plan.manifest.source_inputs[0].request);
    assert_eq!(failed.row.admission, Some(0));
    assert!(failed.row.roles_known && failed.row.roles > 0);
    let recording_name = failed.recording_file.as_ref().expect("actual failed-attempt recording");
    let recording: RecordingFile = decode(&left.join(recording_name), 64 * 1024).unwrap();
    assert_eq!(recording.roles, failed.row.roles);
    assert!(!recording.raw.is_empty() && !recording.captures.is_empty());
    assert_eq!(recording.roles, recording.raw.len());
    let checkpoint = checkpoint_path(&left, index);
    assert!(checkpoint.is_file(), "execute_turn emitted the actual failed checkpoint");
    assert!(left.join("admission-00-settled.json").is_file(), "execute_turn already settled its actual admission");
    let failed_engine = engine(&left_database, plan.before[0].scope()).unwrap();
    assert_eq!(failed_engine.accepted_history_basis().unwrap(), plan.before[0].accepted_history_basis().unwrap(),
        "actual failed attempt cannot advance canonical history");
    ledger.finish().unwrap(); // Finish invocation only; never double-settle the turn.
    let left_admissions = ledger.admissions;
    let left_roles = ledger.charged_roles;
    drop(ledger);
    let terminal_before = terminal(&left_database, &failed.request);
    assert_eq!(terminal_before.0, failed.request);
    assert_eq!(terminal_before.1, locallore_storage::TurnPhase::Failed);
    assert!(terminal_before.2.is_none());
    let known: StoredTurn = decode(&checkpoint, 256 * 1024).unwrap();
    assert_eq!(encode(&known).unwrap(), encode(&failed).unwrap());
    let right_database = database(&destination_path.join("right"), index, destination.manifest.source_kind);
    assert!(!right_database.exists());
    assert!(!checkpoint_path(&destination_path.join("right"), index).exists());
    drop(destination);
    drop(plan);
    let left_work_before = turn_work_inventory(&left);
    let before_checkpoint = fs::read(&checkpoint).unwrap();
    let report = resume_selected(&destination_path, &fixture.source, &binding, &Cancellation::default()).unwrap();
    assert!(report.completed, "completed counts finished attempts, not a successful left proposal");
    assert_eq!(report.rows.len(), 2);
    assert_eq!(report.rows[0], failed.row);
    assert_eq!(report.rows[1].arm, "right");
    assert_eq!(report.rows[1].phase, "committed");
    assert!(report.rows[1].passed && report.rows[1].roles_known && report.rows[1].roles > 0);
    assert_eq!(report.rows[1].admission, Some(0));
    assert!(!report.quality_accepted && report.human_reviewed == 0);
    assert_eq!(fs::read(&checkpoint).unwrap(), before_checkpoint);
    assert_eq!(turn_work_inventory(&left), left_work_before,
        "only known invocation overhead may change on the already finished arm");
    assert_eq!(terminal(&left_database, &failed.request), terminal_before);
    let final_left = Ledger::load(&left, &binding).unwrap();
    assert_eq!((final_left.admissions, final_left.charged_roles), (left_admissions, left_roles));
    let final_right = Ledger::load(&destination_path.join("right"), &binding).unwrap();
    assert_eq!(final_right.admissions, 1);
    assert_eq!(final_right.charged_roles, report.rows[1].roles);
    let actual_right = terminal(&right_database, &right_request);
    assert_eq!(actual_right.0, right_request);
    assert_eq!(actual_right.1, locallore_storage::TurnPhase::Committed);
    assert!(actual_right.2.is_some());
    assert_eq!(inventory(&fixture.source), source_before);
    let completed = inventory(&destination_path);
    let first_report = encode(&report).unwrap();
    let repeated = resume_selected(&destination_path, &fixture.source, &binding, &Cancellation::default()).unwrap();
    assert_eq!(encode(&repeated).unwrap(), first_report);
    assert_eq!(inventory(&destination_path), completed, "completed retry cannot reserve, rewrite reports or clear the failure");
    assert_eq!(inventory(&fixture.source), source_before);
}
