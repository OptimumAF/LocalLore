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
    fn done(m: &EvaluationManager, l: &WindowLease, e: u64, t: &str) -> Value {
        for _ in 0..1000 {
            let status = m.status(l, e, t).unwrap();
            if status["running"] == false {
                return status;
            }
            std::thread::sleep(Duration::from_millis(5));
        }
        panic!("native evaluation did not reach boundary")
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
        let mut changed = original;
        changed[0] = b'!';
        fs::write(&file, changed).unwrap();
        m.open(&l, e, run).unwrap();
        assert_eq!(done(&m, &l, e, token)["error"], "EvaluationIntegrity");
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
            "UnknownEvaluationCase"
        );
        assert_eq!(fs::read_dir(&m.root).unwrap().count(), 0);
        fs::create_dir(m.root.join("not-a-run")).unwrap();
        assert_eq!(m.catalog(&l, e).unwrap_err(), "UnsafeEvaluationPath");
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
    let mut pins = Vec::new();
    for p in path.ancestors() {
        let m = fs::symlink_metadata(p).map_err(|_| "EvaluationIo")?;
        if m.file_type().is_symlink() {
            return Err("UnsafeEvaluationPath".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::{fs::MetadataExt, fs::OpenOptionsExt};
            if m.file_attributes() & 0x400 != 0 {
                return Err("UnsafeEvaluationPath".into());
            }
            pins.push(
                OpenOptions::new()
                    .read(true)
                    .share_mode(3)
                    .custom_flags(0x02200000)
                    .open(p)
                    .map_err(|_| "EvaluationIo")?,
            );
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
struct Job {
    epoch: u64,
    id: u64,
    run: String,
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
    root: PathBuf,
    state: Mutex<State>,
    worker: Mutex<Option<(u64, JoinHandle<()>)>>,
    #[cfg(any(test, feature = "dev-harness"))]
    hold: std::sync::atomic::AtomicBool,
}
impl EvaluationManager {
    pub fn new(root: PathBuf) -> Self {
        Self {
            root,
            state: Mutex::new(State::default()),
            worker: Mutex::new(None),
            #[cfg(any(test, feature = "dev-harness"))]
            hold: std::sync::atomic::AtomicBool::new(false),
        }
    }
    fn state(&self) -> Result<std::sync::MutexGuard<'_, State>> {
        self.state.lock().map_err(|_| "EvaluationInternal".into())
    }
    fn budget(&self, run: Option<&Path>) -> Result<()> {
        if free_space(&self.root)? < 64 * 1024 * 1024 || bytes(&self.root, &mut 0)? > ROOT_BYTES {
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
            let _pins = pin(&metadata)?;
            if fs::metadata(&metadata).map_err(|_| "EvaluationIo")?.len() > 4096 {
                return Err("EvaluationIntegrity".into());
            }
            let v: Value = serde_json::from_slice(&fs::read(metadata).map_err(|_| "EvaluationIo")?)
                .map_err(|_| "EvaluationIntegrity")?;
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
        let t = s.tokens.get_mut(id).ok_or("UnknownEvaluationRun")?;
        if t.epoch != epoch || t.touched.elapsed() > Duration::from_secs(900) {
            return Err("UnknownEvaluationRun".into());
        }
        t.touched = Instant::now();
        Ok(t.run.clone())
    }
    fn mint(s: &mut State, epoch: u64, run: String) -> Result<String> {
        s.tokens
            .retain(|_, t| t.touched.elapsed() < Duration::from_secs(900));
        // Opening the same run reuses its lease; no token churn during ordinary browsing.
        if let Some((id, t)) = s
            .tokens
            .iter_mut()
            .find(|(_, t)| t.epoch == epoch && t.run == run)
        {
            t.touched = Instant::now();
            return Ok(id.clone());
        }
        if s.tokens.values().filter(|t| t.epoch == epoch).count() >= 4 {
            return Err("EvaluationTokenLimit".into());
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
        lease.dispatch(epoch, || {
            let mut s = self.state()?;
            let run = Self::token(&mut s, epoch, token)?;
            let j = s
                .job
                .as_ref()
                .filter(|j| j.epoch == epoch && j.id == operation && j.run == run)
                .ok_or("StaleEvaluationOperation")?;
            j.cancel.cancel();
            s.runs.get_mut(&run).unwrap().phase = "stopping_at_boundary".into();
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
        let (run, token, id, cancel, resume, selection) = lease.dispatch(epoch, || {
            let mut s = self.state()?;
            if s.job.is_some() {
                return Err("EvaluationBusy".into());
            }
            let resume = existing.is_some();
            let run = if let Some(id) = existing {
                if !s.runs.contains_key(&id) {
                    return Err("UnknownEvaluationRun".into());
                }
                id
            } else {
                if s.runs.len() >= 32 {
                    return Err("EvaluationRunLimit".into());
                }
                let id = uuid()?;
                let directory = self.root.join(&id);
                fs::create_dir(&directory).map_err(|_| "EvaluationIo")?;
                let _pins = pin(&directory)?;
                let created = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .map_err(|_| "EvaluationIo")?
                    .as_millis() as u64;
                let bytes = serde_json::to_vec(
                    &json!({"version":1,"run_id":id,"selection":selection,"created":created}),
                )
                .map_err(|_| "EvaluationInternal")?;
                OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(directory.join("native.json"))
                    .and_then(|mut f| f.write_all(&bytes).and_then(|_| f.sync_all()))
                    .map_err(|_| "EvaluationIo")?;
                s.runs.insert(
                    id.clone(),
                    Run {
                        selection: selection.clone(),
                        created,
                        report: None,
                        phase: "starting".into(),
                        error: None,
                    },
                );
                id
            };
            let token = Self::mint(&mut s, epoch, run.clone())?;
            s.next += 1;
            let id = s.next;
            if id > 9_007_199_254_740_991 {
                return Err("EvaluationBudget".into());
            }
            let cancel = Cancellation::default();
            if recover {
                cancel.cancel()
            }
            let r = s.runs.get_mut(&run).unwrap();
            r.phase = if recover {
                "validating_checkpoints"
            } else {
                "running"
            }
            .into();
            r.error = None;
            let selected = r.selection.clone();
            s.job = Some(Job {
                epoch,
                id,
                run: run.clone(),
                cancel: cancel.clone(),
            });
            Ok((run, token, id, cancel, resume, selected))
        })?;
        let manager = self.clone();
        let run_copy = run.clone();
        let lease_copy = lease.clone();
        let handle = std::thread::spawn(move || {
            let result = (|| -> Result<()> {
                let path = manager.root.join(&run_copy);
                let _pins = pin(&path)?;
                let work = path.join("work");
                let mut resume = resume;
                loop {
                    manager.budget(Some(&path))?;
                    let report = locallore_eval::run_builtin(
                        &work,
                        resume,
                        selection.as_deref(),
                        &cancel,
                        1,
                    )
                    .map_err(category)?;
                    let data = serde_json::to_value(report).map_err(|_| "EvaluationInternal")?;
                    if serde_json::to_vec(&data)
                        .map_err(|_| "EvaluationInternal")?
                        .len()
                        > REPORT_BYTES
                    {
                        return Err("EvaluationBudget".into());
                    }
                    let complete = data["completed"] == true;
                    {
                        let mut s = manager.state()?;
                        if s.job
                            .as_ref()
                            .is_some_and(|j| j.id == id && j.epoch == epoch)
                        {
                            s.runs.get_mut(&run_copy).unwrap().report = Some(data);
                        }
                    }
                    manager.budget(Some(&path))?;
                    #[cfg(any(test, feature = "dev-harness"))]
                    while manager.hold.load(std::sync::atomic::Ordering::SeqCst)
                        && !cancel.is_cancelled()
                    {
                        std::thread::sleep(Duration::from_millis(10));
                    }
                    if complete
                        || !all
                        || recover
                        || cancel.is_cancelled()
                        || !lease_copy.valid(epoch)
                    {
                        break;
                    }
                    resume = true;
                }
                Ok(())
            })();
            if let Ok(mut s) = manager.state() {
                if s.job
                    .as_ref()
                    .is_some_and(|j| j.id == id && j.epoch == epoch)
                {
                    let r = s.runs.get_mut(&run_copy).unwrap();
                    r.phase = if result.is_err() {
                        "error"
                    } else if r.report.as_ref().is_some_and(|r| r["completed"] == true) {
                        "completed"
                    } else {
                        "paused"
                    }
                    .into();
                    r.error = result.err();
                    s.job = None;
                }
            }
        });
        let old = self
            .worker
            .lock()
            .map_err(|_| "EvaluationInternal")?
            .replace((epoch, handle));
        if let Some((_, h)) = old {
            h.join().map_err(|_| "EvaluationInternal")?;
        }
        self.status(lease, epoch, &token)
    }
    pub fn retire(&self, epoch: u64) {
        if let Ok(mut s) = self.state() {
            s.tokens.retain(|_, t| t.epoch != epoch);
            if let Some(j) = s.job.as_ref().filter(|j| j.epoch == epoch) {
                j.cancel.cancel();
            }
        }
    }
    pub fn drain(&self, epoch: u64) {
        let old = self.worker.lock().ok().and_then(|mut h| {
            if h.as_ref().is_some_and(|(e, _)| *e == epoch) {
                h.take()
            } else {
                None
            }
        });
        if let Some((_, h)) = old {
            let _ = h.join();
        }
    }
    #[cfg(any(test, feature = "dev-harness"))]
    pub fn test_case(&self, case: &str) -> Result<Value> {
        use std::sync::atomic::Ordering;
        match case {
            "hold-boundary" => self.hold.store(true, Ordering::SeqCst),
            "release-boundary" => self.hold.store(false, Ordering::SeqCst),
            _ => return Err("InvalidEvaluationInput".into()),
        }
        Ok(json!({"synthetic":true}))
    }
}
