// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit approved-installed-asset gates; SOURCE-ONLY / UNRUN at handoff.
//! Run ONLY after Root approval, with both named asset environment variables.
//! Actual scripted sources and separate real native targets, never model quality.
#![cfg(feature = "local-model")]
use super::*;
use locallore_local_runtime::LocalRuntime;
use std::sync::{
    atomic::{AtomicBool, AtomicUsize, Ordering}, Arc, Mutex, OnceLock, Weak,
};

type Runtime = Arc<Mutex<LocalRuntime>>;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
// EXACT failed asset-test pair only. No production manager, wire or public hook.
// If real OS cleanup remains unconfirmed, retain it and block later asset tests.
static BLOCKED: AtomicBool = AtomicBool::new(false);
static RETAINED: Mutex<Option<(Reservation, Runtime)>> = Mutex::new(None);

#[derive(Clone)]
struct Assets { resources: PathBuf, model: PathBuf }
impl Assets {
    fn required() -> Self {
        assert!(!BLOCKED.load(Ordering::SeqCst), "prior asset test cleanup is unresolved; Root inspection required");
        let resources = std::env::var_os("LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES")
            .expect("explicit LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES is required");
        let model = std::env::var_os("LOCALLORE_SELECTED_NATIVE_TEST_MODEL")
            .expect("explicit LOCALLORE_SELECTED_NATIVE_TEST_MODEL is required");
        Self { resources: resources.into(), model: model.into() }
    }
}
#[derive(Default)]
struct Spy {
    callbacks: AtomicUsize, assets: AtomicUsize, drops: AtomicUsize,
    handoff: Mutex<Option<Weak<Mutex<LocalRuntime>>>>,
}
struct Reservation { assets: Assets, spy: Arc<Spy> }
impl Reservation {
    fn reserve(assets: &Assets, spy: &Arc<Spy>) -> Result<Self> {
        if BLOCKED.load(Ordering::SeqCst) { return Err("Cleanup".into()); }
        spy.callbacks.fetch_add(1, Ordering::SeqCst);
        Ok(Self { assets: assets.clone(), spy: spy.clone() })
    }
}
impl Drop for Reservation {
    fn drop(&mut self) { self.spy.drops.fetch_add(1, Ordering::SeqCst); }
}
impl SelectedNativeReservation for Reservation {
    fn assets(&self) -> crate::local_lane::NativeAssets<'_> {
        assert!(!BLOCKED.load(Ordering::SeqCst), "unresolved test owner blocks assets");
        self.spy.assets.fetch_add(1, Ordering::SeqCst);
        crate::local_lane::NativeAssets { resource_dir: &self.assets.resources, model: &self.assets.model }
    }
    fn retain_uncertain(&mut self, owner: Runtime) -> std::result::Result<(), Runtime> {
        *self.spy.handoff.lock().unwrap_or_else(|p| p.into_inner()) = Some(Arc::downgrade(&owner));
        Err(owner) // The typed failure must retain BOTH actual values.
    }
}
fn cleanup_pair(reservation: Reservation, runtime: Runtime) {
    for _ in 0..2 {
        let cleaned = runtime.lock().unwrap_or_else(|p| p.into_inner()).terminate_and_reap().is_ok();
        if cleaned { drop(runtime); drop(reservation); return; }
    }
    // Do not drop an uncertain owner merely because this test must fail.
    BLOCKED.store(true, Ordering::SeqCst);
    let mut slot = RETAINED.lock().unwrap_or_else(|p| p.into_inner());
    if slot.is_none() { *slot = Some((reservation, runtime)); }
    else { std::mem::forget((reservation, runtime)); }
    panic!("asset test cleanup remains unconfirmed; exact owner retained; Root inspection required");
}
fn dispose_failure(failure: SelectedNativeFailure<Reservation>) -> String {
    let code = failure.code().to_owned();
    let uncertain = failure.cleanup_uncertain();
    match failure.into_retained() {
        Ok((reservation, runtime)) => cleanup_pair(reservation, runtime),
        Err(_) => assert!(!uncertain, "rejected test handoff lost the retained owner pair"),
    }
    code
}
fn success(result: std::result::Result<SelectedComparisonReportV1, SelectedNativeFailure<Reservation>>)
    -> SelectedComparisonReportV1
{
    match result {
        Ok(report) => report,
        Err(failure) => panic!("native selected opt-in failed with fixed code {}", dispose_failure(failure)),
    }
}
fn forbidden(spy: &Spy) -> Result<Reservation> {
    spy.callbacks.fetch_add(1, Ordering::SeqCst);
    panic!("model-free path attempted native reservation");
}
struct ResetFaults;
impl Drop for ResetFaults {
    fn drop(&mut self) {
        CANCEL_AFTER_ARM.with(|flag| flag.set(false));
        native_owner::FAIL_CLEANUP_ONCE.with(|flag| flag.set(false));
    }
}
fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!("locallore-selected-assets-{label}-{}-{}",
        std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
    fs::create_dir(&path).unwrap();
    path
}
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let meta = fs::symlink_metadata(&path).unwrap();
            assert!(!meta.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if meta.is_dir() { out.insert(relative, None); walk(root, &path, depth + 1, total, out); }
            else {
                assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(&path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                out.insert(relative, Some(bytes));
            }
        }
    }
    let mut files = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut files);
    files
}
fn actual_source() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE.get_or_init(|| {
        let source = root("scripted-source").join("rollout");
        let report = run_comparison(&source, false, ComparisonKind::ContinuousRollout,
            &Cancellation::default(), 2, LaneFactory::ScriptedBaseline, None).unwrap();
        assert_eq!((report.completed_scenes, report.turns.len()), (2, 24));
        assert!(report.turns.iter().all(|row| row.passed));
        source
    }).as_path()
}
struct Fixture { root: PathBuf, source: PathBuf, destination: PathBuf }
impl Fixture {
    fn new(label: &str) -> Self {
        let original = inventory(actual_source());
        let root = root(label);
        let source = root.join("source");
        fs::create_dir(&source).unwrap();
        for (relative, bytes) in &original {
            match bytes {
                None => fs::create_dir_all(source.join(relative)).unwrap(),
                Some(bytes) => fs::write(source.join(relative), bytes).unwrap(),
            }
        }
        assert!(inventory(&source) == original);
        let fixture = Self { destination: root.join("native-target"), root, source };
        // Owned synthetic artifacts only; never log approved model/resource paths.
        println!("LOCALLORE_SELECTED_NATIVE_TEST_ARTIFACT={}", fixture.root.display());
        fixture
    }
    fn plan(&self, index: usize, client: &str) -> PreparedSelectedPlan {
        let opened = desktop_api::open_read_only(&self.source).unwrap();
        let binding = desktop_api::summary(&opened, true).unwrap()["binding"].as_str().unwrap().to_owned();
        drop(opened);
        prepare_selected(&self.source, &binding, &desktop_api::RowId {
            turn: suite().unwrap().steps()[index].id().into(), arm: desktop_api::Arm::Left,
        }, SelectedIntent { client_id: client.into(), lane: SelectedLane::ApprovedNative },
            &Cancellation::default()).unwrap()
    }
    fn database(&self, arm: usize, index: usize) -> PathBuf {
        database(&self.destination.join(ARM_NAMES[arm]), index, ComparisonKind::ContinuousRollout)
    }
}
fn first_guard() -> usize {
    suite().unwrap().steps().iter().position(|step| matches!(step.expected(),
        protocol::Expected::GuardRejected(_))).unwrap()
}
fn assert_setup(report: &SelectedComparisonReportV1, dir: &Path, expected: usize) {
    assert_eq!(report.lane, "native_selected_case");
    assert!(report.profile == native_profile().unwrap());
    assert!(!report.quality_accepted && report.human_reviewed == 0);
    assert_eq!(report.physical_setups, expected);
    assert!(report.physical_setup_ms.is_some() && report.native_load.is_some());
    let setups = setup::read_setups(dir, &report.binding, true).unwrap();
    assert_eq!(setups.len(), expected);
    for setup in setups {
        assert_eq!(setup.status, "loaded");
        let metrics = setup.load.expect("actual successful load measurement");
        assert_eq!(metrics["model_loads"], 1);
        assert!(metrics["load_ms"].as_f64().is_some_and(|ms| ms.is_finite() && ms >= 0.0));
    }
}
fn assert_guard_rows(fixture: &Fixture, report: &SelectedComparisonReportV1, index: usize) {
    assert!(report.completed);
    assert_eq!(report.rows.len(), 2);
    for (arm, row) in report.rows.iter().enumerate() {
        assert_eq!(row.arm, ARM_NAMES[arm]);
        assert_eq!(row.policy, POLICIES[arm]);
        assert!(matches!(row.phase.as_str(), "failed" | "rejected"));
        assert_eq!(row.error.as_deref(), Some("Inventory"));
        assert!(row.passed && row.roles_known && row.roles == 0);
        assert_eq!(row.context_requirement, "not_applicable_guard_configured_only");
        let cp: StoredTurn = decode(&checkpoint_path(&fixture.destination.join(ARM_NAMES[arm]), index), 256 * 1024).unwrap();
        let mut store = Store::open_read_only(&fixture.database(arm, index)).unwrap();
        let actual = store.lookup_turn(&cp.request.scope, &cp.request.turn).unwrap();
        assert!(actual.request == cp.request);
        assert_eq!(actual.phase, locallore_storage::TurnPhase::Failed);
        assert!(actual.receipt.is_none());
        assert_eq!(cp.before_head, cp.after_head);
        let recording: RecordingFile = decode(&fixture.destination.join(ARM_NAMES[arm])
            .join(cp.recording_file.expect("actual guard recording")), 64 * 1024).unwrap();
        assert_eq!(recording.roles, 0);
        assert!(recording.captures.is_empty() && recording.raw.is_empty());
        assert!(!recording.lost);
    }
}
fn assert_committed(fixture: &Fixture, report: &SelectedComparisonReportV1, index: usize) {
    assert!(report.completed && report.rows.len() == 2);
    for arm in 0..2 {
        let row = &report.rows[arm];
        assert_eq!(row.phase, "committed");
        assert!(row.passed && row.policy_matches && row.context_evidence_available);
        assert!(row.roles_known && (2..=3).contains(&row.roles));
        assert!(row.actual_receipt_sha256.is_some() && row.role_metrics.is_some());
        let cp: StoredTurn = decode(&checkpoint_path(&fixture.destination.join(ARM_NAMES[arm]), index), 256 * 1024).unwrap();
        let full = engine(&fixture.database(arm, index), &cp.request.scope).unwrap();
        let receipt = full.receipts().last().unwrap();
        assert!(receipt.request() == &cp.request && receipt.request() == &report.source_inputs[arm].request);
        let play = receipt.play().expect("actual native current Play metadata");
        assert!(play.profile == report.profile);
        assert_eq!(play.context_policy, Some(POLICIES[arm]));
        assert_eq!(play.prompt_version, PROMPT_VERSION);
        assert!(play.context.as_ref().is_some_and(|context| context.version == 2 && context.compiler_version == 2));
        assert!(full.recorded(&report.source_inputs[arm].request).unwrap().as_ref() == Some(receipt));
    }
    // The public inspector revalidates real receipts/capture/recordings/ledgers.
    assert!(serde_json::to_value(inspect_selected(&fixture.destination).unwrap()).unwrap()
        == serde_json::to_value(report).unwrap());
}
fn readonly_resume(fixture: &Fixture, binding: &str) {
    let source = inventory(&fixture.source);
    let target = inventory(&fixture.destination);
    let spy = Spy::default();
    success(resume_native_selected(&fixture.destination, &fixture.source, binding,
        &Cancellation::default(), || forbidden(&spy)));
    assert_eq!(spy.callbacks.load(Ordering::SeqCst), 0);
    assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
    assert!(inventory(&fixture.source) == source && inventory(&fixture.destination) == target);
}

#[test]
#[ignore = "requires explicit approved installed native assets; starts real worker/model; Root approval only"]
fn approved_guard_has_one_real_setup_and_actual_host_rejections_without_generation_roles() {
    let assets = Assets::required();
    let fixture = Fixture::new("guard");
    let source = inventory(&fixture.source);
    let spy = Arc::new(Spy::default());
    let index = first_guard();
    let report = success(run_native_selected(fixture.plan(index, "asset-guard"), &fixture.destination,
        &Cancellation::default(), || Reservation::reserve(&assets, &spy)));
    assert_eq!(spy.callbacks.load(Ordering::SeqCst), 1);
    assert_eq!(spy.assets.load(Ordering::SeqCst), 1);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert_setup(&report, &fixture.destination, 1);
    assert_guard_rows(&fixture, &report, index);
    assert!(inventory(&fixture.source) == source);
    readonly_resume(&fixture, &report.binding);
}

#[test]
#[ignore = "requires explicit approved installed native assets; actual native commits and lost-checkpoint recovery"]
fn approved_move_commits_then_actual_lost_checkpoint_recovers_without_assets_or_new_calls() {
    let assets = Assets::required();
    let fixture = Fixture::new("move-recovery");
    let source = inventory(&fixture.source);
    let spy = Arc::new(Spy::default());
    let report = success(run_native_selected(fixture.plan(4, "asset-move"), &fixture.destination,
        &Cancellation::default(), || Reservation::reserve(&assets, &spy)));
    assert_setup(&report, &fixture.destination, 1);
    assert_committed(&fixture, &report, 4);
    assert_eq!(spy.callbacks.load(Ordering::SeqCst), 1);
    assert_eq!(spy.assets.load(Ordering::SeqCst), 1);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    let mut expected = inventory(&fixture.destination);
    let lost = checkpoint_path(&fixture.destination.join("left"), 4);
    assert!(lost.is_file());
    assert!(expected.remove(lost.strip_prefix(&fixture.destination).unwrap()).is_some());
    fs::remove_file(&lost).unwrap();
    assert!(inventory(&fixture.destination) == expected, "only actual left checkpoint removed");
    let before: Vec<_> = (0..2).map(|arm| engine(&fixture.database(arm, 4), &report.source_inputs[arm].scope).unwrap()).collect();
    let no_assets = Spy::default();
    let recovered = success(resume_native_selected(&fixture.destination, &fixture.source, &report.binding,
        &Cancellation::default(), || forbidden(&no_assets)));
    assert_eq!(no_assets.callbacks.load(Ordering::SeqCst), 0);
    assert_eq!(no_assets.assets.load(Ordering::SeqCst), 0);
    assert!(recovered.completed);
    let row = &recovered.rows[0];
    assert_eq!(row.phase, "committed");
    assert!(row.recovered_without_checkpoint && !row.roles_known && !row.passed);
    assert!(row.admission.is_none() && row.capture_sha256.is_none() && row.recording_sha256.is_none());
    assert!(row.role_metrics.is_none() && row.first_final_response_ms.is_none());
    assert!(row.actual_receipt_sha256.is_some());
    for arm in 0..2 {
        let after = engine(&fixture.database(arm, 4), before[arm].scope()).unwrap();
        assert!(after.receipts() == before[arm].receipts());
        assert!(after.accepted_history_basis().unwrap() == before[arm].accepted_history_basis().unwrap());
    }
    assert_eq!(recovered.physical_setups, 1);
    assert!(inventory(&fixture.source) == source);
    readonly_resume(&fixture, &report.binding);
}

#[test]
#[ignore = "requires explicit approved installed native assets; deterministic postcommit cancel and new-worker resume"]
fn approved_postcommit_cancel_preserves_first_commit_and_only_missing_arm_runs_on_resume() {
    let _reset = ResetFaults;
    let assets = Assets::required();
    let fixture = Fixture::new("postcommit-cancel");
    let source = inventory(&fixture.source);
    let spy = Arc::new(Spy::default());
    let cancel = Cancellation::default();
    CANCEL_AFTER_ARM.with(|flag| flag.set(true));
    let result = run_native_selected(fixture.plan(4, "asset-postcommit"), &fixture.destination,
        &cancel, || Reservation::reserve(&assets, &spy));
    CANCEL_AFTER_ARM.with(|flag| flag.set(false));
    let failure = match result { Err(failure) => failure, Ok(_) => panic!("postcommit boundary did not interrupt missing arm") };
    assert_eq!(dispose_failure(failure), "Interrupted");
    assert!(cancel.is_cancelled());
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    let partial = inspect_selected(&fixture.destination).unwrap();
    assert!(!partial.completed && partial.rows.len() == 1);
    assert_eq!(partial.rows[0].arm, "left");
    assert_eq!(partial.rows[0].phase, "committed");
    assert!(partial.rows[0].passed);
    assert!(!fixture.database(1, 4).exists());
    assert!(!checkpoint_path(&fixture.destination.join("right"), 4).exists());
    let first = engine(&fixture.database(0, 4), &partial.source_inputs[0].scope).unwrap();
    let first_files = inventory(&fixture.destination.join("left"));
    let resume_spy = Arc::new(Spy::default());
    let report = success(resume_native_selected(&fixture.destination, &fixture.source, &partial.binding,
        &Cancellation::default(), || Reservation::reserve(&assets, &resume_spy)));
    assert_setup(&report, &fixture.destination, 2);
    assert_committed(&fixture, &report, 4);
    assert_eq!(resume_spy.callbacks.load(Ordering::SeqCst), 1);
    assert_eq!(resume_spy.assets.load(Ordering::SeqCst), 1);
    assert_eq!(resume_spy.drops.load(Ordering::SeqCst), 1);
    let after = engine(&fixture.database(0, 4), first.scope()).unwrap();
    assert!(after.receipts() == first.receipts());
    let later_files = inventory(&fixture.destination.join("left"));
    assert!(first_files.iter().all(|(path, bytes)| later_files.get(path) == Some(bytes)));
    assert!(inventory(&fixture.source) == source);
    readonly_resume(&fixture, &report.binding);
}

#[test]
#[ignore = "requires explicit approved installed native assets; actual cleanup uncertainty and retained preparation reserves"]
fn approved_guard_cleanup_uncertainty_retains_owner_and_both_unknown_preparation_charges() {
    let _reset = ResetFaults;
    let assets = Assets::required();
    let fixture = Fixture::new("uncertain-cleanup");
    let source = inventory(&fixture.source);
    let spy = Arc::new(Spy::default());
    let index = first_guard();
    native_owner::FAIL_CLEANUP_ONCE.with(|flag| flag.set(true));
    let result = run_native_selected(fixture.plan(index, "asset-uncertain"), &fixture.destination,
        &Cancellation::default(), || Reservation::reserve(&assets, &spy));
    native_owner::FAIL_CLEANUP_ONCE.with(|flag| flag.set(false));
    let failure = match result { Err(failure) => failure, Ok(_) => panic!("forced cleanup uncertainty was hidden") };
    let code = failure.code().to_owned();
    let uncertain = failure.cleanup_uncertain();
    let drops_before = spy.drops.load(Ordering::SeqCst);
    let (reservation, runtime) = match failure.into_retained() {
        Ok(pair) => pair,
        Err(failure) => panic!("uncertain cleanup lost typed retained owner: {}", dispose_failure(failure)),
    };
    let same_arc = spy.handoff.lock().unwrap_or_else(|p| p.into_inner())
        .as_ref().and_then(Weak::upgrade).is_some_and(|handed| Arc::ptr_eq(&runtime, &handed));
    // Actual same-owner retry BEFORE assertions that could otherwise drop it.
    cleanup_pair(reservation, runtime);
    assert_eq!(code, "Cleanup");
    assert!(uncertain && same_arc && drops_before == 0);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert_eq!(spy.callbacks.load(Ordering::SeqCst), 1);
    assert_eq!(spy.assets.load(Ordering::SeqCst), 1);
    let report = inspect_selected(&fixture.destination).unwrap();
    assert_setup(&report, &fixture.destination, 1);
    assert_guard_rows(&fixture, &report, index);
    for arm in 0..2 {
        let directory = fixture.destination.join(ARM_NAMES[arm]);
        assert!(!directory.join("invocation-00-settled.json").exists());
        let known: Settlement = decode(&directory.join("admission-00-settled.json"), 4096).unwrap();
        assert_eq!(known.roles, 0);
        let ledger = Ledger::load(&directory, &report.binding).unwrap();
        assert_eq!((ledger.invocations, ledger.admissions, ledger.charged_roles), (1, 1, 0));
        assert_eq!(ledger.charged_ms, PREPARATION_MS + known.ms);
    }
    assert!(inventory(&fixture.source) == source);
    readonly_resume(&fixture, &report.binding);
}
