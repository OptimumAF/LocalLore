// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Root registers this module only
//! under protocol-owner-tests. Fixed protocol child, no model weights/inference.
use super::super::{Manifest, Session3};
use super::finish_prepared;
use crate::local_lane::comparison::{
    native_startup::Startup,
    selected::{native_owner, SelectedNativeFailure, SelectedNativeReservation},
    ComparisonKind,
};
use crate::local_lane::{native_profile, NativeAssets};
use locallore::inference::Cancellation;
use locallore_local_runtime::{Error, LocalRuntime, OwnedStartFailure, Status};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Mutex, Weak,
    },
    time::{Duration, Instant},
};

type Runtime = Arc<Mutex<LocalRuntime>>;

struct FixedOwner {
    runtime: Runtime,
    _diagnostics: PathBuf,
}
impl FixedOwner {
    fn new() -> Self {
        let (runtime, directory) = match LocalRuntime::development_protocol_fixture() {
            Ok(value) => value,
            Err(OwnedStartFailure::BeforeChild(error)) => panic!("fixture before child: {error:?}"),
            Err(OwnedStartFailure::AfterChild { cause, mut owner }) => {
                let cleanup = owner.terminate_and_reap();
                panic!("fixture startup {cause:?}; actual cleanup {cleanup:?}");
            }
        };
        let fixture = Self {
            runtime: Arc::new(Mutex::new(runtime)),
            _diagnostics: directory,
        };
        fixture
            .runtime
            .lock()
            .unwrap()
            .load(|| false)
            .expect("fixed protocol load only");
        assert_eq!(fixture.runtime.lock().unwrap().status(), Status::Loaded);
        fixture
    }
    fn cleanup(&self) {
        let mut runtime = self.runtime.lock().unwrap_or_else(|p| p.into_inner());
        runtime
            .terminate_and_reap()
            .expect("same actual fixture cleanup");
        assert_eq!(runtime.status(), Status::Failed);
        assert_eq!(runtime.load(|| false), Err(Error::WorkerUnavailable));
    }
}
impl Drop for FixedOwner {
    fn drop(&mut self) {
        // Exact helper-owned child is reaped even on assertion failure. Preserve
        // all TEMP diagnostics; no recursive filesystem deletion or other owner.
        let _ = self
            .runtime
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .terminate_and_reap();
    }
}
struct FaultReset;
impl Drop for FaultReset {
    fn drop(&mut self) {
        native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(false));
    }
}

struct Observation {
    status: Status,
    settled: bool,
    report: bool,
    same_retained: bool,
}
struct Spy {
    accept: bool,
    directory: PathBuf,
    owner: Weak<Mutex<LocalRuntime>>,
    retained: Mutex<Option<Runtime>>,
    assets: AtomicUsize,
    drops: AtomicUsize,
    observed: Mutex<Vec<Observation>>,
}
struct Reservation(Arc<Spy>);
impl SelectedNativeReservation for Reservation {
    fn assets(&self) -> NativeAssets<'_> {
        self.0.assets.fetch_add(1, Ordering::SeqCst);
        NativeAssets {
            resource_dir: Path::new("UNUSED-FIXED-RESOURCE"),
            model: Path::new("UNUSED-FIXED-MODEL"),
        }
    }
    fn retain_uncertain(&mut self, owner: Runtime) -> Result<(), Runtime> {
        assert!(Arc::ptr_eq(&owner, &self.0.owner.upgrade().unwrap()));
        if !self.0.accept {
            return Err(owner);
        }
        let mut retained = self.0.retained.lock().unwrap();
        assert!(retained.is_none(), "no owner overwrite");
        *retained = Some(owner);
        Ok(())
    }
}
impl Drop for Reservation {
    fn drop(&mut self) {
        let owner = self.0.owner.upgrade().unwrap();
        let status = owner.lock().unwrap_or_else(|p| p.into_inner()).status();
        let same_retained = self
            .0
            .retained
            .lock()
            .unwrap()
            .as_ref()
            .is_some_and(|retained| Arc::ptr_eq(retained, &owner));
        self.0.observed.lock().unwrap().push(Observation {
            status,
            settled: ["left", "right"].iter().any(|arm| {
                self.0
                    .directory
                    .join(arm)
                    .join("invocation-00-settled.json")
                    .exists()
            }),
            report: self.0.directory.join("report.json").exists()
                || self.0.directory.join("report.html").exists(),
            same_retained,
        });
        self.0.drops.fetch_add(1, Ordering::SeqCst);
    }
}

fn prepared(fixture: &FixedOwner, accept: bool) -> (Session3, Arc<Spy>) {
    let root = std::env::temp_dir().join(format!(
        "literal-v3-owner-review-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&root).unwrap();
    let directory = root.join("run");
    let started = Instant::now();
    let manifest = Manifest::new_with_lane(
        ComparisonKind::ContinuousRollout,
        native_profile().unwrap(),
        true,
        None,
    )
    .unwrap();
    let mut session = Session3::open(&directory, false, manifest, None, started).unwrap();
    session.begin_invocations().unwrap();
    for arm in ["left", "right"] {
        assert!(directory.join(arm).join("invocation-00.json").is_file());
        assert!(!directory
            .join(arm)
            .join("invocation-00-settled.json")
            .exists());
    }
    let spy = Arc::new(Spy {
        accept,
        directory,
        owner: Arc::downgrade(&fixture.runtime),
        retained: Mutex::new(None),
        assets: AtomicUsize::new(0),
        drops: AtomicUsize::new(0),
        observed: Mutex::new(Vec::new()),
    });
    (session, spy)
}
fn finish(
    session: Session3,
    spy: &Arc<Spy>,
    fixture: &FixedOwner,
) -> SelectedNativeFailure<Reservation> {
    let began = Instant::now();
    let startup = Startup {
        runtime: Some(fixture.runtime.clone()),
        load: None,
        error: Some("RuntimeProtocol".into()),
    };
    match finish_prepared(
        session,
        Reservation(spy.clone()),
        startup,
        &Cancellation::default(),
        began,
        began + Duration::from_secs(120),
        1,
    ) {
        Err(failure) => failure,
        Ok(_) => panic!("synthetic startup failure must not become successful model execution"),
    }
}
fn assert_unsettled(spy: &Spy) {
    for arm in ["left", "right"] {
        assert!(!spy
            .directory
            .join(arm)
            .join("invocation-00-settled.json")
            .exists());
    }
    assert!(!spy.directory.join("report.json").exists());
    assert!(!spy.directory.join("report.html").exists());
    assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
}

#[test]
fn confirmed_owner_cleanup_precedes_reservation_drop_then_accounting_and_publication() {
    let fixture = FixedOwner::new();
    let (session, spy) = prepared(&fixture, false);
    let failure = finish(session, &spy, &fixture);
    assert_eq!(failure.code(), "RuntimeProtocol");
    assert!(!failure.cleanup_uncertain());
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    let observations = spy.observed.lock().unwrap();
    assert_eq!(observations.len(), 1);
    assert_eq!(observations[0].status, Status::Failed);
    assert!(!observations[0].settled && !observations[0].report);
    drop(observations);
    for arm in ["left", "right"] {
        assert!(spy
            .directory
            .join(arm)
            .join("invocation-00-settled.json")
            .is_file());
    }
    assert!(spy.directory.join("report.json").is_file());
    assert!(spy.directory.join("report.html").is_file());
    assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
    assert!(failure.into_retained().is_err());
    fixture.cleanup();
}

#[test]
fn uncertain_cleanup_installs_same_arc_before_drop_without_settling_or_publishing() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let (session, spy) = prepared(&fixture, true);
    native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let failure = finish(session, &spy, &fixture);
    assert!(failure.cleanup_uncertain());
    assert_eq!(failure.code(), "Cleanup");
    assert_eq!(failure.cause(), Some("RuntimeProtocol"));
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert_unsettled(&spy);
    let observations = spy.observed.lock().unwrap();
    assert_eq!(observations.len(), 1);
    assert_eq!(observations[0].status, Status::Loaded);
    assert!(observations[0].same_retained);
    assert!(!observations[0].settled && !observations[0].report);
    drop(observations);
    let retained = spy.retained.lock().unwrap().take().unwrap();
    assert!(Arc::ptr_eq(&retained, &fixture.runtime));
    assert!(failure.into_retained().is_err());
    fixture.cleanup();
    drop(retained);
}

#[test]
fn rejected_uncertain_handoff_returns_undropped_reservation_and_same_actual_owner() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let (session, spy) = prepared(&fixture, false);
    native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let failure = finish(session, &spy, &fixture);
    assert!(failure.cleanup_uncertain());
    assert_eq!(failure.cause(), Some("RuntimeProtocol"));
    assert_eq!(spy.drops.load(Ordering::SeqCst), 0);
    assert!(spy.observed.lock().unwrap().is_empty());
    assert_unsettled(&spy);
    let (reservation, runtime) = match failure.into_retained() {
        Ok(pair) => pair,
        Err(_) => panic!("rejected handoff lost actual ownership pair"),
    };
    assert!(Arc::ptr_eq(&runtime, &fixture.runtime));
    assert_eq!(runtime.lock().unwrap().status(), Status::Loaded);
    fixture.cleanup();
    drop(runtime);
    drop(reservation);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert_unsettled(&spy);
}

fn diagnostic_inventory(root: &Path) -> std::collections::BTreeMap<PathBuf, Option<Vec<u8>>> {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize,
        out: &mut std::collections::BTreeMap<PathBuf, Option<Vec<u8>>>) {
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
    let mut out = std::collections::BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}

#[test]
fn known_native_setup_shares_cannot_exceed_actual_invocation_settlements() {
    let fixture = FixedOwner::new();
    let (session, spy) = prepared(&fixture, false);
    let failure = finish(session, &spy, &fixture);
    assert_eq!(failure.code(), "RuntimeProtocol");
    assert!(!failure.cleanup_uncertain());
    fixture.cleanup();
    let mut known = Vec::new();
    for arm in ["left", "right"] {
        let settled: serde_json::Value = serde_json::from_slice(
            &fs::read(spy.directory.join(arm).join("invocation-00-settled.json")).unwrap()).unwrap();
        known.push(settled["ms"].as_u64().unwrap());
    }
    let physical = known.iter().copied().max().unwrap().checked_add(1).unwrap()
        .checked_mul(2).unwrap();
    assert!(physical <= 120_000, "fixture must leave room inside the actual setup cap");
    assert!(physical / 2 > known[0] && physical / 2 > known[1]);
    let path = spy.directory.join("setup-00.json");
    let mut actual: serde_json::Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    assert_eq!(actual["status"], "failed");
    assert!(physical > actual["physical_ms"].as_u64().unwrap());
    // Adversarial diagnostic copy of actual producer output: change ONLY this
    // measurement, preserving real canonical records/reservations/settlements.
    actual["physical_ms"] = serde_json::json!(physical);
    fs::write(path, serde_json::to_vec(&actual).unwrap()).unwrap();
    let before = diagnostic_inventory(&spy.directory);
    let result = super::super::inspect_comparison(&spy.directory);
    let after = diagnostic_inventory(&spy.directory);
    assert!(after == before, "read refusal must preserve diagnostic inventory");
    assert!(result.is_err(), "reader accepted setup shares above both known settlements");
}

struct PanicReset;
impl Drop for PanicReset {
    fn drop(&mut self) {
        super::PANIC_AFTER_OWNER.with(|fault| fault.set(false));
    }
}

#[test]
fn unwind_after_actual_owner_is_contained_before_cleanup_and_finalization() {
    let _reset = PanicReset;
    let fixture = FixedOwner::new();
    let (session, spy) = prepared(&fixture, false);
    super::PANIC_AFTER_OWNER.with(|fault| fault.set(true));
    let failure = finish(session, &spy, &fixture);
    assert_eq!(failure.code(), "SelectedExecution");
    assert!(!failure.cleanup_uncertain());
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
    let observations = spy.observed.lock().unwrap();
    assert_eq!(observations.len(), 1);
    assert_eq!(observations[0].status, Status::Failed);
    assert!(!observations[0].settled && !observations[0].report);
    drop(observations);
    for arm in ["left", "right"] {
        assert!(spy.directory.join(arm).join("invocation-00-settled.json").is_file());
    }
    assert!(spy.directory.join("report.json").is_file());
    assert!(spy.directory.join("report.html").is_file());
    assert!(failure.into_retained().is_err());
    fixture.cleanup();
}
