// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST frozen owned-curated oracles, SOURCE ONLY / UNCOMPILED / UNRUN.
//! Missing-assets/clock tests do not spawn. Protocol fixture is ownership-only,
//! never an approved inference profile. Two ignored cases require real approved
//! installed assets and Root approval. No fabricated receipt/source fingerprint.
use super::*;
use std::{
    collections::BTreeMap,
    sync::atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
};

type Runtime = Arc<Mutex<LocalRuntime>>;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
static NEXT: AtomicU64 = AtomicU64::new(0);
// Test containment only: one unresolved actual pair blocks further asset tests.
// This is not a production manager or a way to discard an uncertain child.
static BLOCKED: AtomicBool = AtomicBool::new(false);
static RETAINED: Mutex<Option<(Reservation, Runtime)>> = Mutex::new(None);

#[derive(Default)]
struct Spy {
    assets: AtomicUsize,
    drops: AtomicUsize,
    busy: AtomicBool,
    offered: Mutex<Option<std::sync::Weak<Mutex<LocalRuntime>>>>,
}
struct Reservation {
    resources: PathBuf,
    model: PathBuf,
    spy: Arc<Spy>,
}
impl Reservation {
    fn new(root: &Path, spy: &Arc<Spy>) -> Self {
        assert!(!BLOCKED.load(Ordering::SeqCst));
        assert!(!spy.busy.swap(true, Ordering::SeqCst));
        Self {
            resources: root.join("missing-resources"),
            model: root.join("missing-model"),
            spy: spy.clone(),
        }
    }
    fn approved(spy: &Arc<Spy>) -> Self {
        assert!(
            !BLOCKED.load(Ordering::SeqCst),
            "earlier actual cleanup is unresolved"
        );
        let resources = std::env::var_os("LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES")
            .expect("explicit approved resources required");
        let model = std::env::var_os("LOCALLORE_SELECTED_NATIVE_TEST_MODEL")
            .expect("explicit approved model required");
        assert!(!spy.busy.swap(true, Ordering::SeqCst));
        Self {
            resources: resources.into(),
            model: model.into(),
            spy: spy.clone(),
        }
    }
}
impl NativeReservation for Reservation {
    fn assets(&self) -> NativeAssets<'_> {
        self.spy.assets.fetch_add(1, Ordering::SeqCst);
        NativeAssets {
            resource_dir: &self.resources,
            model: &self.model,
        }
    }
    fn retain_uncertain(&mut self, runtime: Runtime) -> std::result::Result<(), Runtime> {
        *self.spy.offered.lock().unwrap() = Some(Arc::downgrade(&runtime));
        Err(runtime) // The returned failure must retain BOTH actual values.
    }
}
impl Drop for Reservation {
    fn drop(&mut self) {
        self.spy.drops.fetch_add(1, Ordering::SeqCst);
        self.spy.busy.store(false, Ordering::SeqCst);
    }
}
struct FaultReset;
impl Drop for FaultReset {
    fn drop(&mut self) {
        comparison::selected::native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(false));
    }
}
fn cleanup_pair(reservation: Reservation, runtime: Runtime) {
    for _ in 0..2 {
        let confirmed = runtime
            .lock()
            .unwrap_or_else(|poison| poison.into_inner())
            .terminate_and_reap()
            .is_ok();
        if confirmed {
            drop(runtime);
            drop(reservation);
            return;
        }
    }
    BLOCKED.store(true, Ordering::SeqCst);
    let mut retained = RETAINED.lock().unwrap_or_else(|poison| poison.into_inner());
    assert!(
        retained.is_none(),
        "serial test fixture has one unresolved owner"
    );
    *retained = Some((reservation, runtime));
    panic!("actual cleanup unconfirmed; retained pair blocks later asset cases");
}
fn failure(
    result: std::result::Result<Report, NativeFailure<Reservation>>,
) -> NativeFailure<Reservation> {
    match result {
        Err(error) => error,
        Ok(_) => panic!("expected fixed failure, not a completed report"),
    }
}
fn success(result: std::result::Result<Report, NativeFailure<Reservation>>) -> Report {
    match result {
        Ok(report) => report,
        Err(error) => {
            let code = error.code().to_owned();
            if let Ok((reservation, runtime)) = error.into_retained() {
                cleanup_pair(reservation, runtime);
            }
            panic!("owned native fixture failed with closed code {code}");
        }
    }
}
fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "locallore-owned-curated-{label}-{}-{}-{}",
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
    fn visit(root: &Path, path: &Path, depth: usize, bytes: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 1024);
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
        let relative = path.strip_prefix(root).unwrap().to_owned();
        if metadata.is_dir() {
            assert!(out.insert(relative, None).is_none());
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), depth + 1, bytes, out);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            let data = fs::read(path).unwrap();
            *bytes = bytes.checked_add(data.len()).unwrap();
            assert!(*bytes <= 64 * 1024 * 1024);
            assert!(out.insert(relative, Some(data)).is_none());
        }
    }
    let mut out = BTreeMap::new();
    visit(root, root, 0, &mut 0, &mut out);
    out
}
fn actual_ledger(directory: &Path) -> Ledger {
    let manifest = read(&directory.join("run.json"), 128 * 1024).unwrap();
    Ledger::load(directory, &digest(&manifest)).unwrap()
}

#[test]
fn invalid_case_counts_and_precancel_refuse_before_assets_or_new_directory() {
    let root = root("admission");
    let directory = root.join("run");
    let original = inventory(&root);
    for count in [0, 7, usize::MAX] {
        let spy = Arc::new(Spy::default());
        let error = failure(run_native_curated_owned(
            &directory,
            false,
            Some("gift-agency"),
            &Cancellation::default(),
            count,
            Reservation::new(&root, &spy),
        ));
        assert_eq!(error.code(), "CaseBudget");
        assert!(!error.cleanup_uncertain());
        assert!(error.into_retained().is_err());
        assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
        assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
        assert!(!spy.busy.load(Ordering::SeqCst));
        assert!(inventory(&root) == original);
    }
    let spy = Arc::new(Spy::default());
    let cancel = Cancellation::default();
    cancel.cancel();
    let error = failure(run_native_curated_owned(
        &directory,
        false,
        Some("gift-agency"),
        &cancel,
        1,
        Reservation::new(&root, &spy),
    ));
    assert_eq!(error.code(), "Interrupted");
    assert!(!error.cleanup_uncertain());
    assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert!(!directory.exists() && inventory(&root) == original);
}

#[test]
fn missing_assets_return_closed_beforechild_failure_release_reservation_and_settle_once_without_report(
) {
    let root = root("missing");
    let directory = root.join("run");
    let spy = Arc::new(Spy::default());
    let error = failure(run_native_curated_owned(
        &directory,
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        Reservation::new(&root, &spy),
    ));
    assert_eq!(error.code(), "RuntimeModelInvalid");
    assert_eq!(error.cause(), Some("RuntimeModelInvalid"));
    assert!(!error.cleanup_uncertain());
    assert!(error.into_retained().is_err());
    assert_eq!(spy.assets.load(Ordering::SeqCst), 1);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert!(!spy.busy.load(Ordering::SeqCst));
    assert!(spy.offered.lock().unwrap().is_none());
    assert!(!directory.join("report.json").exists() && !directory.join("report.html").exists());
    assert!(!directory.join("case-00.json").exists());
    let settled: Settlement =
        serde_json::from_slice(&fs::read(directory.join("invocation-00-settled.json")).unwrap())
            .unwrap();
    assert_eq!(settled.index, 0);
    assert_eq!(settled.roles, 0);
    let ledger = actual_ledger(&directory);
    assert_eq!(ledger.invocations, 1);
    assert_eq!(ledger.admissions, 0);
    assert_eq!(ledger.charged_ms, settled.ms);
    assert!(!directory.join("invocation-01.json").exists());
}

#[test]
fn preparation_clock_keeps_entry_origin_and_remaining_cleanup_reserve_without_reset() {
    let entry = Instant::now();
    for delay in [0, 90_000, 119_999] {
        let now = entry + Duration::from_millis(delay);
        assert_eq!(
            preparation_deadline(entry, MAX_ACTIVE_MS, now).unwrap(),
            entry + Duration::from_millis(PREPARATION_MS)
        );
    }
    let now = entry + Duration::from_millis(90_000);
    assert_eq!(
        preparation_deadline(entry, 10_000, now).unwrap(),
        now + Duration::from_millis(7_000)
    );
    assert!(preparation_deadline(
        entry,
        MAX_ACTIVE_MS,
        entry + Duration::from_millis(PREPARATION_MS)
    )
    .is_err());
    assert!(preparation_deadline(entry, CLEANUP_RESERVE_MS, now).is_err());
}

#[cfg(feature = "protocol-owner-tests")]
#[test]
fn actual_protocol_owner_exercises_same_cleanup_port_only_not_native_inference_identity() {
    let _reset = FaultReset;
    let root = root("protocol-only");
    let (runtime, _fixture_directory) = match LocalRuntime::development_protocol_fixture() {
        Ok(fixture) => fixture,
        Err(OwnedStartFailure::BeforeChild(error)) => {
            panic!("fixed protocol fixture missing: {error:?}")
        }
        Err(OwnedStartFailure::AfterChild { cause, mut owner }) => {
            let cleanup = owner.terminate_and_reap();
            panic!("protocol fixture failed: {cause:?}; cleanup {cleanup:?}");
        }
    };
    let runtime = Arc::new(Mutex::new(runtime));
    let spy = Arc::new(Spy::default());
    comparison::selected::native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let error = finish_owner(
        Reservation::new(&root, &spy),
        runtime.clone(),
        Some("RunBudget".into()),
    )
    .unwrap_err();
    assert!(error.cleanup_uncertain());
    assert_eq!(error.cause(), Some("RunBudget"));
    let (reservation, returned) = match error.into_retained() {
        Ok(pair) => pair,
        Err(_) => panic!("actual ownership pair lost"),
    };
    assert!(Arc::ptr_eq(&returned, &runtime));
    assert!(spy.busy.load(Ordering::SeqCst));
    assert_eq!(
        spy.assets.load(Ordering::SeqCst),
        0,
        "fixed worker never enters native profile/factory path"
    );
    assert_eq!(spy.drops.load(Ordering::SeqCst), 0);
    cleanup_pair(reservation, returned);
    drop(runtime);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
}

#[test]
#[ignore = "explicit approved installed assets and Root approval; real native curated story, never protocol fixture"]
fn approved_story_and_same_recipe_cached_resume_keep_real_checkpoint_and_skip_cached_assets() {
    let root = root("approved-cache");
    let directory = root.join("run");
    let spy = Arc::new(Spy::default());
    let report = success(run_native_curated_owned(
        &directory,
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        Reservation::approved(&spy),
    ));
    assert_eq!(report.lane, "native_curated_shared_host");
    assert!(report.completed && report.cases.len() == 1);
    assert_eq!(report.cases[0].id, "gift-agency");
    assert!(report.provenance["native_load"]["model_loads"]
        .as_u64()
        .is_some_and(|count| count > 0));
    assert_eq!(spy.assets.load(Ordering::SeqCst), 1);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert!(!spy.busy.load(Ordering::SeqCst));
    let checkpoint = fs::read(directory.join("case-00.json")).unwrap();
    let first = actual_ledger(&directory);
    assert_eq!(first.invocations, 1);
    assert!(directory.join("invocation-00-settled.json").is_file());
    let cached = Arc::new(Spy::default());
    // Missing paths deliberately prove cached workflow cannot touch assets.
    let reopened = success(run_native_curated_owned(
        &directory,
        true,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        Reservation::new(&root, &cached),
    ));
    assert!(reopened.completed && reopened.cases.len() == 1);
    assert_eq!(
        reopened.provenance["native_startup"],
        "not_run_all_checkpoints_complete"
    );
    assert_eq!(cached.assets.load(Ordering::SeqCst), 0);
    assert_eq!(cached.drops.load(Ordering::SeqCst), 1);
    assert!(fs::read(directory.join("case-00.json")).unwrap() == checkpoint);
    // Preserve existing curated semantics: cached restore may write its real
    // invocation/report; it is not the selected driver's read-only resume API.
    assert_eq!(actual_ledger(&directory).invocations, 2);
    assert!(directory.join("invocation-01-settled.json").is_file());
    // Case outcomes may fail finite narrative checks; no human quality assertion.
}

#[test]
#[ignore = "explicit approved installed assets and Root approval; real owner retained after forced cleanup uncertainty"]
fn approved_cleanup_uncertainty_keeps_actual_case_checkpoint_and_full_unknown_invocation() {
    let _reset = FaultReset;
    let root = root("approved-uncertain");
    let directory = root.join("run");
    let spy = Arc::new(Spy::default());
    comparison::selected::native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let error = failure(run_native_curated_owned(
        &directory,
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        Reservation::approved(&spy),
    ));
    assert_eq!(error.code(), "Cleanup");
    assert!(error.cleanup_uncertain());
    assert!(!directory.join("invocation-00-settled.json").exists());
    assert!(!directory.join("report.json").exists() && !directory.join("report.html").exists());
    assert!(
        directory.join("case-00.json").is_file(),
        "real body checkpoint survives later cleanup uncertainty"
    );
    let ledger = actual_ledger(&directory);
    assert_eq!(ledger.invocations, 1);
    assert!(ledger.charged_ms >= PREPARATION_MS);
    assert!(spy.busy.load(Ordering::SeqCst));
    assert_eq!(spy.drops.load(Ordering::SeqCst), 0);
    let before = inventory(&directory);
    let (reservation, runtime) = match error.into_retained() {
        Ok(pair) => pair,
        Err(_) => panic!("uncertain actual pair lost"),
    };
    assert!(spy
        .offered
        .lock()
        .unwrap()
        .as_ref()
        .unwrap()
        .ptr_eq(&Arc::downgrade(&runtime)));
    cleanup_pair(reservation, runtime);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert!(
        inventory(&directory) == before,
        "manual cleanup cannot settle/rewrite/regenerate actual story evidence"
    );
}
