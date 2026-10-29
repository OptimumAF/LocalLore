//! Native-owned built-in synthetic evaluations; never accepts a renderer filesystem path.
use crate::lease::WindowLease;
use locallore::inference::Cancellation;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs::{self, File, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
    thread::JoinHandle,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};
const RUN_BYTES: u64 = 32 * 1024 * 1024;
const ROOT_BYTES: u64 = 256 * 1024 * 1024;
const REPORT_BYTES: usize = locallore_eval::MAX_REPORT;
type Result<T> = std::result::Result<T, String>;
fn uuid() -> Result<String> {
    #[cfg(windows)]
    {
        unsafe { windows::Win32::System::Com::CoCreateGuid() }
            .map(|g| format!("{g:?}").trim_matches(['{', '}']).to_lowercase())
            .map_err(|_| "EvaluationIo".into())
    }
    #[cfg(not(windows))]
    {
        Err("UnsupportedPlatform".into())
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn setup() -> (Arc<EvaluationManager>, Arc<WindowLease>, u64, PathBuf) {
        let path = std::env::temp_dir().join(format!("evaluation-unit-{}", uuid().unwrap()));
        fs::create_dir(&path).unwrap();
        let manager = Arc::new(EvaluationManager::new(path.join("runs")));
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        manager.catalog(&lease, epoch).unwrap();
        (manager, lease, epoch, path)
    }
    #[test]
    fn late_cancellation_registration_and_old_cleanup_cannot_escape_retirement() {
        let (m, l, e, path) = setup();
        l.invalidate(&format!("main-{e}")).unwrap();
        m.retire(e); // retirement observes no registered job
        let late = Cancellation::default();
        m.register_cancellation(&l, e, 1, &late);
        assert!(late.is_cancelled());

        let next_lease = WindowLease::default();
        let next_epoch = next_lease.begin().unwrap();
        let current = Cancellation::default();
        m.register_cancellation(&next_lease, next_epoch, 2, &current);
        m.clear_cancellation(e, 1);
        assert!(!current.is_cancelled());
        m.retire(next_epoch);
        assert!(current.is_cancelled());
        m.clear_cancellation(next_epoch, 2);
        assert!(m.cancellation.lock().unwrap().is_none());
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    fn done(m: &EvaluationManager, l: &WindowLease, e: u64, t: &str) -> Value {
        // This is a fixture scheduling bound, not the native operation budget.
        // The twelve real SQLite cases can exceed five seconds on Windows.
        let deadline = Instant::now() + Duration::from_secs(30);
        loop {
            let status = m.status(l, e, t).unwrap();
            if status["running"] == false {
                return status;
            }
            assert!(
                Instant::now() < deadline,
                "native evaluation did not reach boundary; last status: {status}"
            );
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    #[test]
    fn retirement_between_admission_and_registration_drains_without_running() {
        let (m, l, e, path) = setup();
        let entered = Arc::new(std::sync::Barrier::new(2));
        let release = Arc::new(std::sync::Barrier::new(2));
        *m.before_spawn.lock().unwrap() = Some((entered.clone(), release.clone()));
        let worker = {
            let m = m.clone();
            let l = l.clone();
            std::thread::spawn(move || m.start(&l, e, None, "all"))
        };
        entered.wait();
        assert!(m.registration.try_lock().is_err());
        let closed = l.invalidate(&format!("main-{e}")).unwrap();
        m.retire(e);
        let close = {
            let m = m.clone();
            std::thread::spawn(move || m.drain(e))
        };
        release.wait();
        assert_eq!(worker.join().unwrap().unwrap_err(), "Closed");
        close.join().unwrap();
        assert!(m.state().unwrap().job.is_none());
        assert!(m.state().unwrap().runs.values().all(|r| r.report.is_none()));
        for dir in fs::read_dir(&m.root).unwrap() {
            assert!(!dir.unwrap().path().join("work").exists())
        }
        l.finish_close(closed, || {});
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn retired_worker_cannot_publish_a_snapshot() {
        let (m, l, e, path) = setup();
        let entered = Arc::new(std::sync::Barrier::new(2));
        let release = Arc::new(std::sync::Barrier::new(2));
        *m.before_publish.lock().unwrap() = Some((entered.clone(), release.clone()));
        m.start(&l, e, None, "one").unwrap();
        entered.wait();
        let closed = l.invalidate(&format!("main-{e}")).unwrap();
        m.retire(e);
        release.wait();
        m.drain(e);
        assert!(m.state().unwrap().runs.values().all(|r| r.report.is_none()));
        assert!(m.state().unwrap().job.is_none());
        l.finish_close(closed, || {});
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn spawn_failure_and_worker_panic_leave_no_busy_job() {
        let (m, l, e, path) = setup();
        m.fail_spawn
            .store(true, std::sync::atomic::Ordering::SeqCst);
        assert_eq!(
            m.start(&l, e, None, "one").unwrap_err(),
            "EvaluationInternal"
        );
        assert!(m.state().unwrap().job.is_none());
        assert!(m.state().unwrap().tokens.is_empty());
        m.panic_worker
            .store(true, std::sync::atomic::Ordering::SeqCst);
        let run = m.start(&l, e, None, "one").unwrap();
        let token = run["run_token"].as_str().unwrap();
        assert_eq!(done(&m, &l, e, token)["error"], "EvaluationInternal");
        assert!(m.state().unwrap().job.is_none());
        let next = m
            .start(&l, e, Some("portable-archive".into()), "one")
            .unwrap();
        assert_eq!(
            done(&m, &l, e, next["run_token"].as_str().unwrap())["phase"],
            "completed"
        );
        m.retire(e);
        m.drain(e);
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn pinned_chain_prevents_ancestor_replacement_and_malformed_ids_do_no_work() {
        let (m, l, e, path) = setup();
        let nested = path.join("ancestor");
        fs::create_dir(&nested).unwrap();
        let leaf = nested.join("leaf");
        fs::write(&leaf, b"synthetic").unwrap();
        let pins = pin(&leaf).unwrap();
        assert!(fs::rename(&nested, path.join("moved")).is_err());
        drop(pins);
        fs::rename(&nested, path.join("moved")).unwrap();
        assert_eq!(
            m.open(&l, e, "../other").unwrap_err(),
            "InvalidEvaluationInput"
        );
        assert_eq!(
            m.status(&l, e, &"x".repeat(200)).unwrap_err(),
            "InvalidEvaluationInput"
        );
        assert_eq!(
            m.start(&l, e, Some("x".repeat(200)), "one").unwrap_err(),
            "InvalidEvaluationInput"
        );
        assert_eq!(fs::read_dir(&m.root).unwrap().count(), 0);
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn boundary_cancel_resume_old_operation_and_retired_lease_are_fenced() {
        let (m, l, e, path) = setup();
        m.test_case("hold-boundary").unwrap();
        let job = m.start(&l, e, None, "all").unwrap();
        let token = job["run_token"].as_str().unwrap();
        let operation = job["operation_id"].as_u64().unwrap();
        for _ in 0..1000 {
            if m.status(&l, e, token).unwrap()["completed_cases"] == 1 {
                break;
            }
            std::thread::sleep(Duration::from_millis(5))
        }
        assert_eq!(
            m.cancel(&l, e, token, operation + 1).unwrap_err(),
            "StaleEvaluationOperation"
        );
        m.cancel(&l, e, token, operation).unwrap();
        assert_eq!(done(&m, &l, e, token)["completed_cases"], 1);
        m.test_case("release-boundary").unwrap();
        m.resume(&l, e, token, "all").unwrap();
        assert_eq!(
            m.cancel(&l, e, token, operation).unwrap_err(),
            "StaleEvaluationOperation"
        );
        assert_eq!(done(&m, &l, e, token)["completed_cases"], 12);
        let report = m.read(&l, e, token, None).unwrap();
        assert_eq!(report["report"]["cases"].as_array().unwrap().len(), 12);
        let closed = l.invalidate(&format!("main-{e}")).unwrap();
        m.retire(e);
        m.drain(e);
        assert_eq!(m.status(&l, e, token).unwrap_err(), "Closed");
        l.finish_close(closed, || {});
        let fresh = l.begin().unwrap();
        assert_eq!(
            m.status(&l, fresh, token).unwrap_err(),
            "UnknownEvaluationRun"
        );
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn explicit_recovery_validates_checkpoint_and_does_not_execute_another_case() {
        let (m, l, e, path) = setup();
        let first = m.start(&l, e, None, "one").unwrap();
        let token = first["run_token"].as_str().unwrap();
        done(&m, &l, e, token);
        let run = first["run_id"].as_str().unwrap();
        let file = m.root.join(run).join("work/case-00.json");
        let original = fs::read(&file).unwrap();
        m.open(&l, e, run).unwrap();
        assert_eq!(done(&m, &l, e, token)["completed_cases"], 1);
        assert_eq!(fs::read(&file).unwrap(), original);
        let mut changed = original.clone();
        changed[0] = b'!';
        fs::write(&file, changed).unwrap();
        m.open(&l, e, run).unwrap();
        assert_eq!(done(&m, &l, e, token)["error"], "EvaluationIntegrity");
        fs::write(&file, &original).unwrap();
        fs::write(m.root.join(run).join("work/run.json"), b"changed binding").unwrap();
        m.open(&l, e, run).unwrap();
        assert_eq!(done(&m, &l, e, token)["error"], "EvaluationSourceMismatch");
        assert_eq!(fs::read(&file).unwrap(), original);
        m.retire(e);
        m.drain(e);
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn unknown_case_and_unsafe_catalog_fail_before_creating_a_run() {
        let (m, l, e, path) = setup();
        assert_eq!(
            m.start(&l, e, Some("../../story".into()), "one")
                .unwrap_err(),
            "InvalidEvaluationInput"
        );
        assert_eq!(fs::read_dir(&m.root).unwrap().count(), 0);
        fs::create_dir(m.root.join("not-a-run")).unwrap();
        assert_eq!(m.catalog(&l, e).unwrap_err(), "UnsafeEvaluationPath");
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn token_reaping_retains_four_handles_and_never_deletes_reports() {
        let (m, l, e, path) = setup();
        let mut first = String::new();
        for i in 0..5 {
            let run = m
                .start(&l, e, Some("portable-archive".into()), "all")
                .unwrap();
            let token = run["run_token"].as_str().unwrap();
            done(&m, &l, e, token);
            if i == 0 {
                first = token.into()
            }
        }
        assert_eq!(m.state().unwrap().tokens.len(), 4);
        assert_eq!(m.state().unwrap().runs.len(), 5);
        assert_eq!(m.status(&l, e, &first).unwrap_err(), "UnknownEvaluationRun");
        assert_eq!(fs::read_dir(&m.root).unwrap().count(), 5);
        m.retire(e);
        m.drain(e);
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn boundary_budget_refuses_next_execution_and_keeps_checkpoint() {
        let (m, l, e, path) = setup();
        let run = m.start(&l, e, None, "one").unwrap();
        let token = run["run_token"].as_str().unwrap();
        done(&m, &l, e, token);
        let dir = m.root.join(run["run_id"].as_str().unwrap());
        let checkpoint = dir.join("work/case-00.json");
        let before = fs::read(&checkpoint).unwrap();
        File::create(dir.join("budget-fixture"))
            .unwrap()
            .set_len(RUN_BYTES + 1)
            .unwrap();
        m.resume(&l, e, token, "all").unwrap();
        assert_eq!(done(&m, &l, e, token)["error"], "EvaluationBudget");
        assert_eq!(fs::read(checkpoint).unwrap(), before);
        assert!(!dir.join("work/case-01.json").exists());
        m.retire(e);
        m.drain(e);
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
    #[test]
    fn retained_run_cap_refuses_new_directory() {
        let (m, l, e, path) = setup();
        for _ in 0..32 {
            let id = uuid().unwrap();
            let dir = m.root.join(&id);
            fs::create_dir(&dir).unwrap();
            fs::write(
                dir.join("native.json"),
                serde_json::to_vec(&json!({"version":1,"run_id":id,"selection":null,"created":1}))
                    .unwrap(),
            )
            .unwrap();
        }
        assert_eq!(
            m.start(&l, e, None, "all").unwrap_err(),
            "EvaluationRunLimit"
        );
        assert_eq!(fs::read_dir(&m.root).unwrap().count(), 32);
        drop(m);
        fs::remove_dir_all(path).unwrap();
    }
}
fn valid_id(s: &str) -> bool {
    s.len() == 36
        && s.bytes().enumerate().all(|(i, b)| {
            if [8, 13, 18, 23].contains(&i) {
                b == b'-'
            } else {
                b.is_ascii_hexdigit()
            }
        })
}
fn pin(path: &Path) -> Result<Vec<File>> {
    let absolute = std::path::absolute(path).map_err(|_| "UnsafeEvaluationPath")?;
    let mut paths: Vec<_> = absolute.ancestors().collect();
    paths.reverse();
    let mut pins = Vec::new();
    for p in paths {
        #[cfg(windows)]
        {
            use std::os::windows::fs::{MetadataExt, OpenOptionsExt};
            // Parent handles remain pinned before every descendant lookup; reject the
            // opened handle's reparse metadata, not a pre-open path observation.
            let handle = OpenOptions::new()
                .read(true)
                .share_mode(3)
                .custom_flags(0x0220_0000)
                .open(p)
                .map_err(|_| "EvaluationIo")?;
            let metadata = handle.metadata().map_err(|_| "EvaluationIo")?;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("UnsafeEvaluationPath".into());
            }
            pins.push(handle);
        }
        #[cfg(not(windows))]
        {
            if fs::symlink_metadata(p)
                .map_err(|_| "EvaluationIo")?
                .file_type()
                .is_symlink()
            {
                return Err("UnsafeEvaluationPath".into());
            }
        }
    }
    Ok(pins)
}
fn bytes(path: &Path, entries: &mut usize) -> Result<u64> {
    walk_bytes(path, entries, 0)
}
fn walk_bytes(path: &Path, entries: &mut usize, depth: usize) -> Result<u64> {
    if depth > 6 {
        return Err("EvaluationBudget".into());
    }
    let _pins = pin(path)?;
    let m = fs::symlink_metadata(path).map_err(|_| "EvaluationIo")?;
    *entries += 1;
    if *entries > 8192 {
        return Err("EvaluationBudget".into());
    }
    if m.is_file() {
        return Ok(m.len());
    }
    let mut total = 0u64;
    for item in fs::read_dir(path).map_err(|_| "EvaluationIo")? {
        total = total
            .checked_add(walk_bytes(
                &item.map_err(|_| "EvaluationIo")?.path(),
                entries,
                depth + 1,
            )?)
            .ok_or("EvaluationBudget")?;
    }
    Ok(total)
}
fn free_space(path: &Path) -> Result<u64> {
    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        use windows::{core::PCWSTR, Win32::Storage::FileSystem::GetDiskFreeSpaceExW};
        let wide: Vec<u16> = path.as_os_str().encode_wide().chain(Some(0)).collect();
        let mut free = 0;
        unsafe { GetDiskFreeSpaceExW(PCWSTR(wide.as_ptr()), Some(&mut free), None, None) }
            .map_err(|_| "EvaluationIo")?;
        Ok(free)
    }
    #[cfg(not(windows))]
    {
        let _ = path;
        Err("UnsupportedPlatform".into())
    }
}
fn builtin_id(case: Option<&str>) -> Result<()> {
    if let Some(id) = case {
        if id.is_empty()
            || id.len() > 48
            || !id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
        {
            return Err("InvalidEvaluationInput".into());
        }
        if !locallore_eval::builtin()?
            .scenarios
            .iter()
            .any(|s| s.id == id)
        {
            return Err("UnknownEvaluationCase".into());
        }
    }
    Ok(())
}
fn category(error: String) -> String {
    match error.as_str() {
        "CheckpointMismatch" => "EvaluationSourceMismatch",
        "CheckpointIntegrity" => "EvaluationIntegrity",
        "Reparse" => "UnsafeEvaluationPath",
        "RunBusy" => "EvaluationBusy",
        "ReportBudget" | "CaseBudget" | "OutputBudget" | "AttemptLimit" => "EvaluationBudget",
        _ => "EvaluationIo",
    }
    .into()
}
struct Token {
    epoch: u64,
    run: String,
    touched: Instant,
}
struct Run {
    selection: Option<String>,
    created: u64,
    report: Option<Value>,
    phase: String,
    error: Option<String>,
}
#[derive(Clone, Copy, PartialEq, Eq)]
enum JobKind {
    Builtin,
    Curated,
    ComparisonRead,
    Selected,
    ComparisonRun,
}
struct Job {
    kind: JobKind,
    epoch: u64,
    id: u64,
    run: String,
    cancel: Cancellation,
    selected: Option<selected::SelectedOwnership>,
    // Remains true while drain temporarily owns the JoinHandle. It is cleared
    // only by actual worker completion, never by presentation retirement.
    worker_active: bool,
}
struct JobCancellation {
    epoch: u64,
    operation: u64,
    cancel: Cancellation,
}
#[derive(Default)]
struct State {
    runs: BTreeMap<String, Run>,
    tokens: BTreeMap<String, Token>,
    job: Option<Job>,
    next: u64,
}
pub struct EvaluationManager {
    full_comparison: Mutex<comparison_run::FullComparisonState>,
    comparison: Mutex<comparison::ComparisonState>,
    curated: Mutex<curated::CuratedState>,
    selected: Mutex<selected::SelectedState>,
    root: PathBuf,
    state: Mutex<State>,
    // Only clone/cancel/replace under this lock; never IO, joins, or another
    // manager/lease lock. Destroyed can cancel even if presentation state is busy.
    cancellation: Mutex<Option<JobCancellation>>,
    worker: Mutex<Option<(u64, JoinHandle<()>)>>,
    registration: Mutex<()>,
    #[cfg(test)]
    fail_spawn: std::sync::atomic::AtomicBool,
    #[cfg(test)]
    panic_worker: std::sync::atomic::AtomicBool,
    #[cfg(test)]
    before_spawn: Mutex<Option<(Arc<std::sync::Barrier>, Arc<std::sync::Barrier>)>>,
    #[cfg(test)]
    before_publish: Mutex<Option<(Arc<std::sync::Barrier>, Arc<std::sync::Barrier>)>>,
    #[cfg(any(test, feature = "dev-harness"))]
    hold: std::sync::atomic::AtomicBool,
    #[cfg(any(test, feature = "dev-harness"))]
    curated_lost_ack: std::sync::atomic::AtomicBool,
    #[cfg(any(test, feature = "dev-harness"))]
    full_lost_ack: std::sync::atomic::AtomicBool,
    #[cfg(any(test, feature = "dev-harness"))]
    full_read_denied: std::sync::atomic::AtomicBool,
}
impl EvaluationManager {
    pub fn new(root: PathBuf) -> Self {
        Self {
            full_comparison: Mutex::new(comparison_run::FullComparisonState::default()),
            comparison: Mutex::new(comparison::ComparisonState::default()),
            curated: Mutex::new(curated::CuratedState::default()),
            selected: Mutex::new(selected::SelectedState::default()),
            root,
            state: Mutex::new(State::default()),
            cancellation: Mutex::new(None),
            worker: Mutex::new(None),
            registration: Mutex::new(()),
            #[cfg(test)]
            fail_spawn: std::sync::atomic::AtomicBool::new(false),
            #[cfg(test)]
            panic_worker: std::sync::atomic::AtomicBool::new(false),
            #[cfg(test)]
            before_spawn: Mutex::new(None),
            #[cfg(test)]
            before_publish: Mutex::new(None),
            #[cfg(any(test, feature = "dev-harness"))]
            hold: std::sync::atomic::AtomicBool::new(false),
            #[cfg(any(test, feature = "dev-harness"))]
            curated_lost_ack: std::sync::atomic::AtomicBool::new(false),
            #[cfg(any(test, feature = "dev-harness"))]
            full_lost_ack: std::sync::atomic::AtomicBool::new(false),
            #[cfg(any(test, feature = "dev-harness"))]
            full_read_denied: std::sync::atomic::AtomicBool::new(false),
        }
    }
    fn state(&self) -> Result<std::sync::MutexGuard<'_, State>> {
        self.state.lock().map_err(|_| "EvaluationInternal".into())
    }
    /// Registry readiness only. Whole-app acknowledgement also requires the
    /// actual model/Host owners' confirmation; finished presentation is no proof.
    pub(crate) fn cleanup_complete(&self) -> bool {
        self.state
            .try_lock()
            .map(|s| s.job.is_none())
            .unwrap_or(false)
            && self
                .worker
                .try_lock()
                .map(|slot| slot.as_ref().is_none_or(|(_, worker)| worker.is_finished()))
                .unwrap_or(false)
            && self
                .cancellation
                .try_lock()
                .map(|slot| slot.is_none())
                .unwrap_or(false)
    }
    fn register_cancellation(
        &self,
        lease: &WindowLease,
        epoch: u64,
        operation: u64,
        cancel: &Cancellation,
    ) {
        {
            let mut slot = self.cancellation.lock().unwrap_or_else(|p| p.into_inner());
            *slot = Some(JobCancellation {
                epoch,
                operation,
                cancel: cancel.clone(),
            });
        }
        // Invalidation is atomic and need not wait for lease.dispatch's gate.
        // Retirement may have observed an empty slot just before registration.
        if !lease.valid(epoch) {
            cancel.cancel();
        }
    }
    fn clear_cancellation(&self, epoch: u64, operation: u64) {
        let mut slot = self.cancellation.lock().unwrap_or_else(|p| p.into_inner());
        if slot
            .as_ref()
            .is_some_and(|j| j.epoch == epoch && j.operation == operation)
        {
            *slot = None;
        }
    }
    fn budget(&self, run: Option<&Path>) -> Result<()> {
        let parent = self.root.parent().ok_or("EvaluationIo")?;
        let _pins = pin(parent)?;
        let builtin_bytes = if self.root.exists() {
            bytes(&self.root, &mut 0)?
        } else {
            0
        };
        let curated = self.curated_root();
        let extra = if curated.exists() {
            bytes(&curated, &mut 0)?
        } else {
            0
        };
        let selected = self.selected_root();
        let selected_bytes = if selected.exists() {
            bytes(&selected, &mut 0)?
        } else {
            0
        };
        let full = self.full_comparison_root();
        let full_bytes = if full.exists() {
            bytes(&full, &mut 0)?
        } else {
            0
        };
        if free_space(parent)? < 64 * 1024 * 1024
            || builtin_bytes
                .saturating_add(extra)
                .saturating_add(selected_bytes)
                .saturating_add(full_bytes)
                > ROOT_BYTES
        {
            return Err("EvaluationBudget".into());
        }
        if let Some(p) = run {
            if p.exists() && bytes(p, &mut 0)? > RUN_BYTES {
                return Err("EvaluationBudget".into());
            }
        }
        Ok(())
    }
    pub fn catalog(&self, lease: &WindowLease, epoch: u64) -> Result<Value> {
        let _registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        let _parent_pins = pin(self.root.parent().ok_or("EvaluationIo")?)?;
        fs::create_dir_all(&self.root).map_err(|_| "EvaluationIo")?;
        let _pins = pin(&self.root)?;
        let suite = locallore_eval::builtin()?;
        let mut found = Vec::new();
        for item in fs::read_dir(&self.root).map_err(|_| "EvaluationIo")? {
            let entry = item.map_err(|_| "EvaluationIo")?;
            let id = entry.file_name().to_string_lossy().into_owned();
            if !valid_id(&id) {
                return Err("UnsafeEvaluationPath".into());
            }
            if found.len() >= 32 {
                return Err("EvaluationRunLimit".into());
            }
            let path = entry.path();
            let _pins = pin(&path)?;
            let metadata = path.join("native.json");
            let pins = pin(&metadata)?;
            let file = pins.last().ok_or("EvaluationIo")?;
            let info = file.metadata().map_err(|_| "EvaluationIo")?;
            if !info.is_file() || info.len() > 4096 {
                return Err("EvaluationIntegrity".into());
            }
            use std::io::Read;
            let mut data = Vec::new();
            file.take(4097)
                .read_to_end(&mut data)
                .map_err(|_| "EvaluationIo")?;
            if data.len() > 4096 {
                return Err("EvaluationIntegrity".into());
            }
            let v: Value = serde_json::from_slice(&data).map_err(|_| "EvaluationIntegrity")?;
            let selected = match &v["selection"] {
                Value::Null => None,
                Value::String(s) => Some(s.clone()),
                _ => return Err("EvaluationIntegrity".into()),
            };
            builtin_id(selected.as_deref())?;
            if v["version"] != 1 || v["run_id"] != id {
                return Err("EvaluationIntegrity".into());
            }
            found.push((
                id,
                selected,
                v["created"].as_u64().ok_or("EvaluationIntegrity")?,
            ));
        }
        lease.dispatch(epoch,||{let mut s=self.state()?;for(id,selection,created)in found{s.runs.entry(id).or_insert(Run{selection,created,report:None,phase:"retained".into(),error:None});}
            Ok(json!({"version":1,"cases":suite.scenarios.iter().map(|x|json!({"id":x.id,"unsupported":x.unsupported})).collect::<Vec<_>>(),"runs":s.runs.iter().map(|(id,r)|json!({"run_id":id,"selection":r.selection,"created":r.created,"phase":r.phase})).collect::<Vec<_>>(),"location":self.root,"caps":{"runs":32,"tokens":4,"workers":1,"report_bytes":REPORT_BYTES,"run_boundary_bytes":RUN_BYTES,"library_boundary_bytes":ROOT_BYTES},"retention":"Private run files remain locally; no automatic expiry. Quota blocks new runs. Outside copies and OS backups are separate."}))})
    }
    fn token(s: &mut State, epoch: u64, id: &str) -> Result<String> {
        if !valid_id(id) {
            return Err("InvalidEvaluationInput".into());
        }
        let active = s.job.as_ref().map(|job| job.run.clone());
        let t = s.tokens.get_mut(id).ok_or("UnknownEvaluationRun")?;
        if t.epoch != epoch
            || (t.touched.elapsed() > Duration::from_secs(900) && active.as_ref() != Some(&t.run))
        {
            return Err("UnknownEvaluationRun".into());
        }
        t.touched = Instant::now();
        Ok(t.run.clone())
    }
    fn mint(s: &mut State, epoch: u64, run: String) -> Result<String> {
        Self::mint_reusing(s, epoch, run, |_| true)
    }
    fn mint_reusing(s: &mut State, epoch: u64, run: String, can_reuse: impl Fn(&str) -> bool) -> Result<String> {
        let active = s.job.as_ref().map(|j| j.run.clone());
        s.tokens.retain(|_, t| {
            t.touched.elapsed() < Duration::from_secs(900) || active.as_ref() == Some(&t.run)
        });
        // Opening the same run reuses its lease; no token churn during ordinary browsing.
        if let Some((id, t)) = s
            .tokens
            .iter_mut()
            .find(|(id, t)| t.epoch == epoch && t.run == run && can_reuse(id))
        {
            t.touched = Instant::now();
            return Ok(id.clone());
        }
        if s.tokens.values().filter(|t| t.epoch == epoch).count() >= 4 {
            // Admission has established no active job. Reap one idle handle, never files.
            let oldest = s
                .tokens
                .iter()
                .filter(|(_, t)| t.epoch == epoch)
                .filter(|(_, t)| active.as_ref() != Some(&t.run))
                .min_by_key(|(_, t)| t.touched)
                .map(|(id, _)| id.clone())
                .ok_or("EvaluationTokenLimit")?;
            s.tokens.remove(&oldest);
        }
        let id = uuid()?;
        s.tokens.insert(
            id.clone(),
            Token {
                epoch,
                run,
                touched: Instant::now(),
            },
        );
        Ok(id)
    }
    fn snapshot(s: &State, run: &str, token: &str) -> Result<Value> {
        let r = s.runs.get(run).ok_or("UnknownEvaluationRun")?;
        let job = s.job.as_ref().filter(|j| j.run == run);
        Ok(
            json!({"version":1,"run_token":token,"run_id":run,"operation_id":job.map(|j|j.id),"running":job.is_some(),"phase":r.phase,"error":r.error,"completed_cases":r.report.as_ref().and_then(|r|r["cases"].as_array()).map_or(0,Vec::len),"completed":r.report.as_ref().is_some_and(|r|r["completed"]==true)}),
        )
    }
    pub fn status(&self, lease: &WindowLease, epoch: u64, token: &str) -> Result<Value> {
        lease.dispatch(epoch, || {
            let mut s = self.state()?;
            let run = Self::token(&mut s, epoch, token)?;
            Self::snapshot(&s, &run, token)
        })
    }
    pub fn read(
        &self,
        lease: &WindowLease,
        epoch: u64,
        token: &str,
        case: Option<&str>,
    ) -> Result<Value> {
        builtin_id(case)?;
        lease.dispatch(epoch, || {
            let mut s = self.state()?;
            let run = Self::token(&mut s, epoch, token)?;
            let r = s
                .runs
                .get(&run)
                .and_then(|r| r.report.as_ref())
                .ok_or("EvaluationNotReady")?;
            let value = if let Some(case) = case {
                r["cases"]
                    .as_array()
                    .and_then(|a| a.iter().find(|c| c["id"] == case))
                    .cloned()
                    .ok_or("UnknownEvaluationCase")?
            } else {
                r.clone()
            };
            Ok(json!({"version":1,"run_token":token,"run_id":run,"case_id":case,"report":value}))
        })
    }
    pub fn cancel(
        &self,
        lease: &WindowLease,
        epoch: u64,
        token: &str,
        operation: u64,
    ) -> Result<Value> {
        if operation == 0 || operation > 9_007_199_254_740_991 {
            return Err("InvalidEvaluationInput".into());
        }
        lease.dispatch(epoch, || {
            let mut s = self.state()?;
            let run = Self::token(&mut s, epoch, token)?;
            let j = s
                .job
                .as_ref()
                .filter(|j| {
                    j.epoch == epoch
                        && j.id == operation
                        && j.run == run
                        && matches!(j.kind, JobKind::Builtin | JobKind::Curated)
                })
                .ok_or("StaleEvaluationOperation")?;
            j.cancel.cancel();
            if let Some(retained) = s.runs.get_mut(&run) {
                retained.phase = "stopping_at_boundary".into();
            } else if let Some(retained) = self
                .curated
                .lock()
                .map_err(|_| "EvaluationInternal")?
                .runs
                .get_mut(&run)
            {
                retained.phase = "stopping_at_boundary".into();
            }
            if !s.runs.contains_key(&run) {
                drop(s);
                return self.curated_snapshot(epoch, &run, token);
            }
            Self::snapshot(&s, &run, token)
        })
    }
    pub fn start(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        selection: Option<String>,
        batch: &str,
    ) -> Result<Value> {
        builtin_id(selection.as_deref())?;
        self.catalog(lease, epoch)?;
        self.admit(lease, epoch, None, selection, batch, false)
    }
    pub fn open(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        run: &str,
    ) -> Result<Value> {
        if !valid_id(run) {
            return Err("InvalidEvaluationInput".into());
        }
        self.catalog(lease, epoch)?;
        self.admit(lease, epoch, Some(run.to_owned()), None, "one", true)
    }
    pub fn resume(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        token: &str,
        batch: &str,
    ) -> Result<Value> {
        let run = lease.dispatch(epoch, || {
            let mut state = self.state()?;
            Self::token(&mut state, epoch, token)
        })?;
        self.admit(lease, epoch, Some(run), None, batch, false)
    }
    pub fn rerun(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        token: &str,
        case: &str,
    ) -> Result<Value> {
        self.read(lease, epoch, token, Some(case))?;
        self.start(lease, epoch, Some(case.to_owned()), "all")
    }
    fn admit(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        existing: Option<String>,
        selection: Option<String>,
        batch: &str,
        recover: bool,
    ) -> Result<Value> {
        if !["one", "all"].contains(&batch) {
            return Err("InvalidEvaluationInput".into());
        }
        let all = batch == "all";
        self.budget(None)?;
        // Drain old finished handles without holding any admission/lease/state/worker
        // lock. Reacquire registration and recheck admission after every such join.
        loop {
            let registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
            if self.state()?.job.is_some() {
                return Err("EvaluationBusy".into());
            }
            let previous = self.worker.lock().map_err(|_| "EvaluationInternal")?.take();
            if let Some((_, handle)) = previous {
                drop(registration);
                handle.join().map_err(|_| "EvaluationInternal")?;
                continue;
            }
            let answer=lease.dispatch(epoch,||{
                let (run,token,id,cancel,resume,selection)={
                    let mut s=self.state()?;
                    if s.job.is_some(){return Err("EvaluationBusy".into())}
                    let resume=existing.is_some();
                    let run=if let Some(id)=existing.clone(){if !valid_id(&id)||!s.runs.contains_key(&id){return Err("UnknownEvaluationRun".into())}id}else{
                        if s.runs.len()>=32{return Err("EvaluationRunLimit".into())}
                        let id=uuid()?;let directory=self.root.join(&id);let _parent=pin(&self.root)?;
                        fs::create_dir(&directory).map_err(|_|"EvaluationIo")?;let _pins=pin(&directory)?;
                        let created=SystemTime::now().duration_since(UNIX_EPOCH).map_err(|_|"EvaluationIo")?.as_millis() as u64;
                        let data=serde_json::to_vec(&json!({"version":1,"run_id":id,"selection":selection,"created":created})).map_err(|_|"EvaluationInternal")?;
                        OpenOptions::new().write(true).create_new(true).open(directory.join("native.json")).and_then(|mut f|f.write_all(&data).and_then(|_|f.sync_all())).map_err(|_|"EvaluationIo")?;
                        s.runs.insert(id.clone(),Run{selection:selection.clone(),created,report:None,phase:"starting".into(),error:None});id
                    };
                    let token=Self::mint(&mut s,epoch,run.clone())?;s.next+=1;let id=s.next;
                    if id>9_007_199_254_740_991{return Err("EvaluationBudget".into())}
                    let cancel=Cancellation::default();if recover{cancel.cancel()}
                    let r=s.runs.get_mut(&run).ok_or("EvaluationInternal")?;r.phase=if recover{"validating_checkpoints"}else{"running"}.into();r.error=None;let selected=r.selection.clone();
                    s.job=Some(Job{kind:JobKind::Builtin,epoch,id,run:run.clone(),cancel:cancel.clone(),selected:None,worker_active:true});
                    self.register_cancellation(lease,epoch,id,&cancel);
                    (run,token,id,cancel,resume,selected)
                };
                #[cfg(test)]
                if let Some((entered,release))=self.before_spawn.lock().unwrap().take(){entered.wait();release.wait();}
                let (start,registered)=std::sync::mpsc::channel();let manager=self.clone();let lease_copy=lease.clone();let run_copy=run.clone();
                let work=move||{
                    if registered.recv().is_err(){return}
                    let result=std::panic::catch_unwind(std::panic::AssertUnwindSafe(||->Result<()> {
                        #[cfg(test)] if manager.panic_worker.swap(false,std::sync::atomic::Ordering::SeqCst){panic!("fixed synthetic worker panic")}
                        if !lease_copy.valid(epoch){return Err("Closed".into())}
                        let path=manager.root.join(&run_copy);let _pins=pin(&path)?;let directory=path.join("work");let mut resume=resume;
                        loop{
                            if !lease_copy.valid(epoch){break}
                            manager.budget(Some(&path))?;
                            let report=locallore_eval::run_builtin(&directory,resume,selection.as_deref(),&cancel,1).map_err(category)?;
                            let data=serde_json::to_value(report).map_err(|_|"EvaluationInternal")?;
                            if serde_json::to_vec(&data).map_err(|_|"EvaluationInternal")?.len()>REPORT_BYTES{return Err("EvaluationBudget".into())}
                            let complete=data["completed"]==true;
                            #[cfg(test)] if let Some((entered,release))=manager.before_publish.lock().unwrap().take(){entered.wait();release.wait();}
                            // The same control gate used by window retirement rejects every
                            // late snapshot. Checkpoints may finish; revoked UI data may not.
                            lease_copy.dispatch(epoch,||{let mut s=manager.state()?;if s.job.as_ref().is_some_and(|j|j.id==id&&j.epoch==epoch){s.runs.get_mut(&run_copy).ok_or("EvaluationInternal")?.report=Some(data);Ok(())}else{Err("Closed".into())}})?;
                            manager.budget(Some(&path))?;
                            #[cfg(any(test,feature="dev-harness"))] while manager.hold.load(std::sync::atomic::Ordering::SeqCst)&&!cancel.is_cancelled()&&lease_copy.valid(epoch){std::thread::sleep(Duration::from_millis(10));}
                            if complete||!all||recover||cancel.is_cancelled()||!lease_copy.valid(epoch){break}resume=true;
                        }Ok(())
                    })).unwrap_or_else(|_|Err("EvaluationInternal".into()));
                    let _=lease_copy.dispatch(epoch,||{let mut s=manager.state()?;if s.job.as_ref().is_some_and(|j|j.id==id&&j.epoch==epoch){let r=s.runs.get_mut(&run_copy).ok_or("EvaluationInternal")?;r.phase=if result.is_err(){"error"}else if r.report.as_ref().is_some_and(|r|r["completed"]==true){"completed"}else{"paused"}.into();r.error=result.clone().err();}Ok(())});
                    // Terminal ownership cleanup also works after lease retirement and
                    // poisoned-state panics. It never publishes a new report.
                    manager.clear_cancellation(epoch,id);
                    let mut s=manager.state.lock().unwrap_or_else(|poison|poison.into_inner());
                    if s.job.as_ref().is_some_and(|j|j.id==id&&j.epoch==epoch){if !lease_copy.valid(epoch){if let Some(r)=s.runs.get_mut(&run_copy){r.phase="retained".into()}}s.job=None;}
                };
                #[cfg(test)] let failed=self.fail_spawn.swap(false,std::sync::atomic::Ordering::SeqCst);
                #[cfg(not(test))] let failed=false;
                let spawned=if failed{Err(std::io::Error::other("fixed synthetic spawn refusal"))}else{std::thread::Builder::new().name("locallore-evaluation".into()).spawn(work)};
                match spawned {
                    Ok(handle)=>{*self.worker.lock().unwrap_or_else(|p|p.into_inner())=Some((epoch,handle));let _=start.send(());}
                    Err(_)=>{self.clear_cancellation(epoch,id);let mut s=self.state()?;if s.job.as_ref().is_some_and(|j|j.id==id&&j.epoch==epoch){s.job=None;s.tokens.remove(&token);if let Some(r)=s.runs.get_mut(&run){r.phase="error".into();r.error=Some("EvaluationInternal".into())}}return Err("EvaluationInternal".into())}
                }
                let s=self.state()?;Self::snapshot(&s,&run,&token)
            });
            drop(registration);
            return if lease.valid(epoch) {
                answer
            } else {
                Err("Closed".into())
            };
        }
    }
    pub fn retire(&self, epoch: u64) {
        self.full_comparison_retire(epoch);
        self.selected_retire(epoch);
        self.comparison_retire(epoch);
        // No IO/state/lease/worker locks are acquired while holding this slot.
        // Cleanup recovers poison; ordinary presentation calls still fail closed.
        {
            let slot = self.cancellation.lock().unwrap_or_else(|p| p.into_inner());
            if let Some(job) = slot.as_ref().filter(|job| job.epoch == epoch) {
                job.cancel.cancel();
            }
        }
        // Destroyed never waits for admission IO or a worker.
        if let Ok(mut s) = self.state.try_lock() {
            s.tokens.retain(|_, t| t.epoch != epoch);
            if let Some(j) = s.job.as_ref().filter(|j| j.epoch == epoch) {
                j.cancel.cancel()
            }
        }
    }
    pub fn drain(&self, epoch: u64) {
        let old = {
            let _registration = self.registration.lock().unwrap_or_else(|p| p.into_inner());
            let mut slot = self.worker.lock().unwrap_or_else(|p| p.into_inner());
            if slot.as_ref().is_some_and(|(e, _)| *e == epoch) {
                slot.take()
            } else {
                None
            }
        };
        if let Some((_, handle)) = old {
            let _ = handle.join();
        }
        self.comparison_drain(epoch);
        self.selected_drain(epoch);
        let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
        state.tokens.retain(|_, t| t.epoch != epoch);
    }
    #[cfg(any(test, feature = "dev-harness"))]
    pub fn test_case(&self, case: &str) -> Result<Value> {
        use std::sync::atomic::Ordering;
        match case {
            "hold-boundary" => self.hold.store(true, Ordering::SeqCst),
            "release-boundary" => self.hold.store(false, Ordering::SeqCst),
            "lose-curated-start-ack" => self.curated_lost_ack.store(true, Ordering::SeqCst),
            "lose-comparison-start-ack" => self.full_lost_ack.store(true, Ordering::SeqCst),
            "deny-comparison-read" => self.full_read_denied.store(true, Ordering::SeqCst),
            _ => return Err("InvalidEvaluationInput".into()),
        }
        Ok(json!({"synthetic":true}))
    }
    #[cfg(feature = "dev-harness")]
    pub fn take_curated_lost_ack(&self) -> bool {
        self.curated_lost_ack
            .swap(false, std::sync::atomic::Ordering::SeqCst)
    }
    #[cfg(feature = "dev-harness")]
    pub fn take_full_lost_ack(&self) -> bool {
        self.full_lost_ack
            .swap(false, std::sync::atomic::Ordering::SeqCst)
    }
    #[cfg(feature = "dev-harness")]
    pub fn take_full_read_denial(&self) -> bool {
        self.full_read_denied
            .swap(false, std::sync::atomic::Ordering::SeqCst)
    }
}
mod comparison;
mod comparison_run;
mod curated;
#[cfg(test)]
mod fresh_budget_review;
mod selected;

pub use comparison::ComparisonEvidenceRequest;
pub use comparison_run::{FullComparisonNativeResume, FullComparisonStart};
#[cfg(test)]
#[path = "evaluation/retirement_review.rs"]
mod retirement_review;
pub use curated::{CuratedEvidenceRequest, CuratedStart};

pub use selected::{
    SelectedEvidenceInput, SelectedInputLane, SelectedPrepareInput, SelectedReadInput,
    SelectedResumeInput,
};
