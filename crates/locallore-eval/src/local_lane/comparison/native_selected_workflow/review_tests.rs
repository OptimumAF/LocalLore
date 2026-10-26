// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen common-owner oracles. SOURCE ONLY / UNCOMPILED / UNRUN at handoff.
//! Root registers under cfg(all(test, feature = "protocol-owner-tests")) after
//! freezing finish_prepared. Fixed real protocol child; no model or inference.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features protocol-owner-tests --lib local_lane::comparison::native_selected_workflow::review_tests -- --nocapture --test-threads=1
use super::*;
use crate::local_lane::{native_profile, NativeAssets};
use locallore_local_runtime::{Error, LocalRuntime, OwnedStartFailure, Status};
use std::{
    collections::BTreeMap,
    sync::{atomic::{AtomicUsize, Ordering}, Arc, Mutex, Weak},
    time::{Duration, Instant},
};

type Runtime = Arc<Mutex<LocalRuntime>>;

struct FixedOwner {
    runtime: Runtime,
    load: Value,
    _diagnostics: PathBuf,
}
impl FixedOwner {
    fn new() -> Self {
        let (runtime, directory) = match LocalRuntime::development_protocol_fixture() {
            Ok(value) => value,
            Err(OwnedStartFailure::BeforeChild(cause)) => panic!("fixed before child: {cause:?}"),
            Err(OwnedStartFailure::AfterChild { cause, mut owner }) => {
                let cleanup = owner.terminate_and_reap();
                panic!("fixed after child: {cause:?}; cleanup {cleanup:?}");
            }
        };
        let runtime = Arc::new(Mutex::new(runtime));
        // Install the Drop owner before load or assertions can unwind.
        let mut fixture = Self { runtime, load: Value::Null, _diagnostics: directory };
        let metrics = fixture.runtime.lock().unwrap().load(|| false)
            .expect("fixed protocol load only, no weights");
        fixture.load = serde_json::to_value(metrics).unwrap();
        assert_eq!(fixture.runtime.lock().unwrap().status(), Status::Loaded);
        fixture
    }
    fn close(&self) {
        let mut owner = self.runtime.lock().unwrap_or_else(|p| p.into_inner());
        assert_eq!(owner.terminate_and_reap(), Ok(()));
        assert_eq!(owner.status(), Status::Failed);
        assert_eq!(owner.load(|| false), Err(Error::WorkerUnavailable));
    }
}
impl Drop for FixedOwner {
    fn drop(&mut self) {
        // Only this exact fixture child; preserve its diagnostic files.
        let _ = self.runtime.lock().unwrap_or_else(|p| p.into_inner()).terminate_and_reap();
    }
}

struct DropObservation { status: Option<Status>, settled: bool, setup: bool, retained: bool }
struct Spy {
    directory: PathBuf,
    runtime: Weak<Mutex<LocalRuntime>>,
    accept: bool,
    retained: Mutex<Option<Runtime>>,
    assets: AtomicUsize,
    executions: AtomicUsize,
    finishes: AtomicUsize,
    loaded: AtomicUsize,
    failed: AtomicUsize,
    drops: AtomicUsize,
    events: Mutex<Vec<&'static str>>,
    observations: Mutex<Vec<DropObservation>>,
}
impl Spy {
    fn status(&self) -> Option<Status> {
        self.runtime.upgrade().unwrap().try_lock().ok().map(|owner| owner.status())
    }
    fn settled(&self) -> bool {
        ARM_NAMES.iter().any(|arm| self.directory.join(arm).join("invocation-00-settled.json").exists())
    }
}
struct Ticket(Arc<Spy>);
impl SelectedNativeReservation for Ticket {
    fn assets(&self) -> NativeAssets<'_> {
        self.0.assets.fetch_add(1, Ordering::SeqCst);
        panic!("direct prepared-owner seam must never inspect assets")
    }
    fn retain_uncertain(&mut self, owner: Runtime) -> std::result::Result<(), Runtime> {
        assert!(Arc::ptr_eq(&owner, &self.0.runtime.upgrade().unwrap()));
        if !self.0.accept { return Err(owner); }
        let mut retained = self.0.retained.lock().unwrap();
        assert!(retained.is_none(), "never overwrite an owned child");
        *retained = Some(owner);
        Ok(())
    }
}
impl Drop for Ticket {
    fn drop(&mut self) {
        let runtime = self.0.runtime.upgrade().unwrap();
        let retained = self.0.retained.lock().unwrap().as_ref()
            .is_some_and(|owner| Arc::ptr_eq(owner, &runtime));
        // Nonblocking: busy-owner tests deliberately retain the actual guard.
        self.0.observations.lock().unwrap().push(DropObservation {
            status: self.0.status(), settled: self.0.settled(),
            setup: self.0.directory.join("setup-00.json").exists(), retained,
        });
        self.0.events.lock().unwrap().push("reservation_drop");
        self.0.drops.fetch_add(1, Ordering::SeqCst);
    }
}

struct TestWorkflow {
    profile: PlayProfile,
    started: Instant,
    binding: String,
    ledgers: [Ledger; 2],
    spy: Arc<Spy>,
    panic_loaded_once: bool,
}
impl Workflow for TestWorkflow {
    type Report = ();
    fn profile(&self) -> &PlayProfile { &self.profile }
    fn started(&self) -> Instant { self.started }
    fn remaining(&self) -> u64 { self.ledgers.iter().map(Ledger::remaining).min().unwrap() }
    fn preflight(&self) -> Result<()> { Ok(()) }
    fn ledgers(&mut self) -> &mut [Ledger; 2] { &mut self.ledgers }
    fn save_setup(&mut self, ms: u64, status: &str, load: Option<Value>) -> Result<()> {
        match status {
            "loaded" => {
                self.spy.loaded.fetch_add(1, Ordering::SeqCst);
                self.spy.events.lock().unwrap().push("loaded_attempt");
                if self.panic_loaded_once {
                    self.panic_loaded_once = false;
                    panic!("fixed test Workflow save_setup unwind");
                }
            }
            "failed" => {
                assert_eq!(self.spy.status(), Some(Status::Failed), "cleanup before failed setup");
                self.spy.failed.fetch_add(1, Ordering::SeqCst);
                self.spy.events.lock().unwrap().push("failed_setup");
            }
            _ => panic!("unexpected setup status"),
        }
        save_setup_at(&self.spy.directory, &self.binding, &mut self.ledgers, ms, status, load)
    }
    fn execute(&mut self, _: Option<&LaneFactory>, _: &Cancellation) -> Result<()> {
        self.spy.executions.fetch_add(1, Ordering::SeqCst);
        panic!("these startup/cleanup cases must not execute inference")
    }
    fn finish(mut self) -> Result<()> {
        assert_eq!(self.spy.status(), Some(Status::Failed), "cleanup before finish");
        self.spy.finishes.fetch_add(1, Ordering::SeqCst);
        self.spy.events.lock().unwrap().push("finish");
        // Real measured settlements, no fabricated cost or report publication.
        turn_execution::finish_pair(&mut self.ledgers)
    }
}

fn prepared(fixture: &FixedOwner, accept: bool, panic_loaded_once: bool) -> (TestWorkflow, Arc<Spy>) {
    let directory = std::env::temp_dir().join(format!("locallore-common-owner-{}-{}",
        std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
    fs::create_dir(&directory).unwrap();
    for arm in ARM_NAMES { fs::create_dir(directory.join(arm)).unwrap(); }
    let binding = "c".repeat(64);
    let mut ledgers = [Ledger::load(&directory.join("left"), &binding).unwrap(),
        Ledger::load(&directory.join("right"), &binding).unwrap()];
    for ledger in &mut ledgers { ledger.begin_invocation().unwrap(); }
    let spy = Arc::new(Spy {
        directory, runtime: Arc::downgrade(&fixture.runtime), accept,
        retained: Mutex::new(None), assets: AtomicUsize::new(0), executions: AtomicUsize::new(0),
        finishes: AtomicUsize::new(0), loaded: AtomicUsize::new(0), failed: AtomicUsize::new(0),
        drops: AtomicUsize::new(0), events: Mutex::new(Vec::new()), observations: Mutex::new(Vec::new()),
    });
    let workflow = TestWorkflow { profile: native_profile().unwrap(), started: Instant::now(),
        binding, ledgers, spy: spy.clone(), panic_loaded_once };
    (workflow, spy)
}
fn finish(workflow: TestWorkflow, spy: &Arc<Spy>, fixture: &FixedOwner, error: Option<&str>) -> SelectedNativeFailure<Ticket> {
    let began = Instant::now();
    let startup = native_startup::Startup { runtime: Some(fixture.runtime.clone()),
        load: Some(fixture.load.clone()), error: error.map(str::to_owned) };
    match finish_prepared(workflow, Ticket(spy.clone()), startup,
        &Cancellation::default(), began, began + Duration::from_secs(120)) {
        Err(failure) => failure,
        Ok(()) => panic!("fixed failure case must not report successful execution"),
    }
}
fn inventory(dir: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    let mut result = BTreeMap::new();
    for base in [dir.to_owned(), dir.join("left"), dir.join("right")] {
        for entry in fs::read_dir(base).unwrap() {
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            if metadata.is_dir() { continue; }
            assert!(metadata.is_file() && metadata.len() <= 64 * 1024 && result.len() < 32);
            result.insert(path.strip_prefix(dir).unwrap().to_owned(), fs::read(path).unwrap());
        }
    }
    result
}
fn assert_terminal(spy: &Spy, fixture: &FixedOwner, loaded_attempts: usize) {
    fixture.close();
    assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
    assert_eq!(spy.executions.load(Ordering::SeqCst), 0);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert_eq!(spy.loaded.load(Ordering::SeqCst), loaded_attempts);
    assert_eq!(spy.failed.load(Ordering::SeqCst), 1);
    assert_eq!(spy.finishes.load(Ordering::SeqCst), 1);
    let observations = spy.observations.lock().unwrap();
    assert_eq!(observations.len(), 1);
    assert_eq!(observations[0].status, Some(Status::Failed));
    assert!(!observations[0].settled && !observations[0].setup && !observations[0].retained);
    drop(observations);
    for arm in ARM_NAMES {
        let d = spy.directory.join(arm);
        assert!(d.join("invocation-00-settled.json").is_file());
        let ledger = Ledger::load(&d, &"c".repeat(64)).unwrap();
        assert_eq!((ledger.invocations, ledger.admissions, ledger.charged_roles), (1, 0, 0));
    }
    let setup: Value = decode(&spy.directory.join("setup-00.json"), 64 * 1024).unwrap();
    assert_eq!(setup["version"], 2);
    assert_eq!(setup["native"], true);
    assert_eq!(setup["status"], "failed");
    assert_eq!(setup["load"], fixture.load);
    assert!(!spy.directory.join("report.json").exists() && !spy.directory.join("report.html").exists());
}

#[test]
fn interrupted_actual_child_is_clean_before_ticket_drop_failed_setup_and_real_settlement() {
    let fixture = FixedOwner::new();
    let (workflow, spy) = prepared(&fixture, false, false);
    let failure = finish(workflow, &spy, &fixture, Some("Interrupted"));
    assert_terminal(&spy, &fixture, 0);
    assert_eq!(failure.code(), "Interrupted");
    assert!(!failure.cleanup_uncertain());
    assert!(failure.into_retained().is_err());
    assert_eq!(*spy.events.lock().unwrap(), ["reservation_drop", "failed_setup", "finish"]);
}

#[test]
fn save_setup_unwind_keeps_actual_owner_outside_catch_until_confirmed_cleanup() {
    let fixture = FixedOwner::new();
    let (workflow, spy) = prepared(&fixture, false, true);
    let failure = finish(workflow, &spy, &fixture, None);
    assert_terminal(&spy, &fixture, 1);
    assert_eq!(failure.code(), "SelectedExecution");
    assert!(!failure.cleanup_uncertain());
    assert!(failure.into_retained().is_err());
    assert_eq!(*spy.events.lock().unwrap(), ["loaded_attempt", "reservation_drop", "failed_setup", "finish"]);
}

#[test]
fn busy_actual_owner_accepted_and_rejected_transfers_keep_accounting_unknown_until_explicit_cleanup() {
    for accept in [true, false] {
        let fixture = FixedOwner::new();
        let (workflow, spy) = prepared(&fixture, accept, false);
        let before = inventory(&spy.directory);
        let guard = fixture.runtime.lock().unwrap();
        let failure = finish(workflow, &spy, &fixture, Some("Interrupted"));
        let code = failure.code().to_owned();
        let cause = failure.cause().map(str::to_owned);
        let uncertain = failure.cleanup_uncertain();
        let transfer = failure.into_retained();
        let drops_before_cleanup = spy.drops.load(Ordering::SeqCst);
        let unchanged = inventory(&spy.directory) == before;
        drop(guard);
        // Always close the exact child before assertions can unwind, including
        // rejected transfer. No OS-wide PID/path lookup or other owner cleanup.
        fixture.close();
        assert_eq!(code, "Cleanup");
        assert_eq!(cause.as_deref(), Some("Interrupted"));
        assert!(uncertain && unchanged);
        if accept {
            assert!(transfer.is_err(), "accepted transfer stays with the ticket adapter");
            let retained = spy.retained.lock().unwrap().take().unwrap();
            assert!(Arc::ptr_eq(&retained, &fixture.runtime));
            assert_eq!(drops_before_cleanup, 1);
            let observations = spy.observations.lock().unwrap();
            assert_eq!(observations.len(), 1);
            assert!(observations[0].retained && observations[0].status.is_none());
            assert!(!observations[0].settled && !observations[0].setup);
            drop(observations);
            drop(retained);
        } else {
            let (ticket, owner) = match transfer {
                Ok(pair) => pair,
                Err(_) => panic!("rejected transfer must preserve the exact ownership pair"),
            };
            assert!(Arc::ptr_eq(&owner, &fixture.runtime));
            assert!(Arc::ptr_eq(&ticket.0, &spy));
            assert_eq!(drops_before_cleanup, 0);
            drop(owner);
            drop(ticket);
        }
        assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
        assert_eq!(spy.executions.load(Ordering::SeqCst), 0);
        assert_eq!(spy.finishes.load(Ordering::SeqCst), 0);
        assert_eq!(spy.loaded.load(Ordering::SeqCst), 0);
        assert_eq!(spy.failed.load(Ordering::SeqCst), 0);
        assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
        assert!(!spy.settled() && !spy.directory.join("setup-00.json").exists());
        for arm in ARM_NAMES {
            let d = spy.directory.join(arm);
            assert!(d.join("invocation-00.json").is_file());
            let ledger = Ledger::load(&d, &"c".repeat(64)).unwrap();
            assert_eq!((ledger.invocations, ledger.admissions, ledger.charged_roles), (1, 0, 0));
            assert_eq!(ledger.charged_ms, PREPARATION_MS);
        }
        assert!(!spy.directory.join("report.json").exists() && !spy.directory.join("report.html").exists());
        assert!(inventory(&spy.directory) == before);
    }
}
