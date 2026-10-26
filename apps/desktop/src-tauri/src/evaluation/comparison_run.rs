//! Ordinary desktop adapter over the shared protocol3 scripted producer.
//! This owns bounded presentation/index metadata, never canonical story state.
use super::*;
use locallore_eval::{
    local_lane::{
        comparison::{self as core, literal_v3},
        LaneFactory,
    },
    memory_comparison_v3::{self as wire, ComparisonReportV3, CurrentBindingV3},
};
use serde::{Deserialize, Serialize};
use std::{collections::BTreeSet, io::Read};

const SAFE: u64 = 9_007_199_254_740_991;
fn bounded(value: Value, cap: usize) -> Result<Value> {
    if serde_json::to_vec(&value)
        .map_err(|_| "EvaluationInternal")?
        .len()
        > cap
    {
        Err("EvaluationBudget".into())
    } else {
        Ok(value)
    }
}
fn valid_id(value: &str) -> bool {
    super::valid_id(value) && !value.bytes().any(|byte| byte.is_ascii_uppercase())
}
pub struct FullComparisonStart {
    pub client_id: String,
    pub kind: core::ComparisonKind,
    pub max_new_scenes: usize,
}
#[derive(Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Index {
    version: u16,
    protocol_version: u16,
    input_lane: String,
    run_id: String,
    client_id: String,
    kind: core::ComparisonKind,
    initial_batch: usize,
    created_ms: u64,
    binding: CurrentBindingV3,
}
fn kind_name(kind: core::ComparisonKind) -> &'static str {
    match kind {
        core::ComparisonKind::PairedSnapshots => "paired",
        core::ComparisonKind::ContinuousRollout => "rollout",
    }
}
impl Index {
    fn metadata(&self) -> Value {
        json!({"run_id":self.run_id,"client_id":self.client_id,"comparison_kind":kind_name(self.kind),"initial_batch":self.initial_batch,"created_ms":self.created_ms,"protocol_version":3,"input_lane":"scripted_baseline"})
    }
}
struct Record {
    index: Index,
    epoch: u64,
    operation: Option<u64>,
    batch: usize,
    phase: &'static str,
    error: Option<String>,
    report: Option<(usize, bool, bool)>,
}
impl Record {
    fn retained(index: Index) -> Self {
        let batch = index.initial_batch;
        Self {
            index,
            epoch: 0,
            operation: None,
            batch,
            phase: "retained",
            error: None,
            report: None,
        }
    }
    fn status(&self, epoch: u64, token: &str, job: Option<&Job>) -> Result<Value> {
        let visible = self.epoch == epoch;
        let report = self.report.filter(|_| visible && self.phase != "closed");
        let running = job.is_some_and(|j| {
            j.kind == JobKind::ComparisonRun
                && j.epoch == epoch
                && j.run == self.index.run_id
                && j.worker_active
        });
        bounded(
            json!({"version":1,"kind":"comparison_run","protocol_version":3,"input_lane":"scripted_baseline",
            "client_id":self.index.client_id,"run_id":self.index.run_id,"run_token":token,
            "operation_id":if visible{self.operation}else{None},"comparison_kind":kind_name(self.index.kind),"batch":self.batch,
            "phase":if visible{self.phase}else{"retained"},"running":running,"error":if visible{self.error.as_ref()}else{None},
            "completed_scenes":report.map_or(0,|r|r.0),"completed":report.is_some_and(|r|r.1),"report_ready":report.is_some(),
            "source_matches":report.map(|r|r.2)}),
            32 * 1024,
        )
    }
}
#[derive(Default)]
pub(super) struct FullComparisonState {
    runs: BTreeMap<String, Record>,
}
fn batch(value: usize) -> Result<()> {
    if (1..=4).contains(&value) {
        Ok(())
    } else {
        Err("InvalidEvaluationInput".into())
    }
}
fn authorize(lease: &WindowLease, epoch: u64, granted: bool) -> Result<()> {
    if !granted {
        return Err("Forbidden".into());
    }
    if !lease.valid(epoch) {
        return Err("Closed".into());
    }
    Ok(())
}
fn failure(error: String) -> String {
    match error.as_str() {
        "Interrupted" | "Cancelled" => "Cancelled",
        "CheckpointMismatch" => "EvaluationSourceMismatch",
        "RunBusy" => "EvaluationBusy",
        "Reparse" => "UnsafeEvaluationPath",
        "SceneBudget" | "RunBudget" | "ReportBudget" | "OutputBudget" | "CaseBudget"
        | "AttemptLimit" => "EvaluationBudget",
        "Closed" => "Closed",
        "EvaluationInternal" => "EvaluationInternal",
        "NotFound" | "Io" => "EvaluationIo",
        "EvaluationBudget" => "EvaluationBudget",
        "EvaluationSourceMismatch" => "EvaluationSourceMismatch",
        "EvaluationNotReady" => "EvaluationNotReady",
        // Core validation errors stay bounded; no path or raw diagnostic escapes.
        _ => "EvaluationIntegrity",
    }
    .into()
}
fn read_json(path: &Path, cap: u64) -> Result<Value> {
    let pins = pin(path)?;
    let file = pins.last().ok_or("EvaluationIo")?;
    let info = file.metadata().map_err(|_| "EvaluationIo")?;
    if !info.is_file() || info.len() > cap {
        return Err("EvaluationIntegrity".into());
    }
    let mut data = vec![];
    file.take(cap + 1)
        .read_to_end(&mut data)
        .map_err(|_| "EvaluationIo")?;
    if data.len() as u64 > cap {
        return Err("EvaluationIntegrity".into());
    }
    serde_json::from_slice(&data).map_err(|_| "EvaluationIntegrity".into())
}
fn validate_manifest(directory: &Path, index: &Index) -> Result<()> {
    let path = directory.join("work/run.json");
    if !path.exists() {
        return Ok(());
    }
    let manifest = read_json(&path, 128 * 1024)?;
    if manifest["version"] != 3
        || manifest["kind"] != serde_json::to_value(index.kind).map_err(|_| "EvaluationInternal")?
        || manifest["binding"]
            != serde_json::to_value(&index.binding).map_err(|_| "EvaluationInternal")?
        || manifest["source_sha256"] != index.binding.source_sha256
    {
        return Err("EvaluationIntegrity".into());
    }
    Ok(())
}
fn read_index(directory: &Path, manifest: bool) -> Result<Index> {
    let value = read_json(&directory.join("desktop.json"), 32 * 1024)?;
    let index: Index = serde_json::from_value(value).map_err(|_| "EvaluationIntegrity")?;
    if index.version != 1
        || index.protocol_version != 3
        || index.input_lane != "scripted_baseline"
        || !valid_id(&index.run_id)
        || !valid_id(&index.client_id)
        || directory.file_name().and_then(|x| x.to_str()) != Some(index.run_id.as_str())
        || !(1..=4).contains(&index.initial_batch)
        || index.created_ms > SAFE
        || index.binding.native
    {
        return Err("EvaluationIntegrity".into());
    }
    if manifest {
        validate_manifest(directory, &index)?;
    }
    Ok(index)
}
enum Work {
    Start,
    Resume,
    Open,
}
impl EvaluationManager {
    pub(super) fn full_comparison_root(&self) -> PathBuf {
        self.root.with_file_name("comparison-evaluations")
    }
    fn full_lock(&self) -> Result<std::sync::MutexGuard<'_, FullComparisonState>> {
        self.full_comparison
            .lock()
            .map_err(|_| "EvaluationInternal".into())
    }
    pub fn full_comparison_catalog(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        let _registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
        let root = self.full_comparison_root();
        let _parent = pin(root.parent().ok_or("EvaluationIo")?)?;
        if !root.exists() {
            fs::create_dir(&root).map_err(|_| "EvaluationIo")?;
        }
        let _pins = pin(&root)?;
        let active = self
            .state()?
            .job
            .as_ref()
            .filter(|j| j.kind == JobKind::ComparisonRun && j.worker_active)
            .map(|j| j.run.clone());
        let mut found = vec![];
        let mut clients = BTreeSet::new();
        for entry in fs::read_dir(&root).map_err(|_| "EvaluationIo")? {
            let entry = entry.map_err(|_| "EvaluationIo")?;
            let id = entry.file_name().to_string_lossy().into_owned();
            if !valid_id(&id) {
                return Err("UnsafeEvaluationPath".into());
            }
            if found.len() >= 32 {
                return Err("EvaluationRunLimit".into());
            }
            let _pins = pin(&entry.path())?;
            let index = read_index(&entry.path(), active.as_deref() != Some(&id))?;
            if !clients.insert(index.client_id.clone()) {
                return Err("EvaluationIntegrity".into());
            }
            found.push(index);
        }
        lease.dispatch(epoch,|| {
            let mut state=self.full_lock()?;
            for index in &found {
                if state.runs.get(&index.run_id).is_some_and(|r|r.index!=*index) { return Err("EvaluationIntegrity".into()); }
            }
            // Cache contains no read grant or canonical Store. Missing durable
            // metadata never becomes an invented retained run.
            let ids:BTreeSet<_>=found.iter().map(|x|x.run_id.clone()).collect();
            state.runs.retain(|id,_|ids.contains(id));
            for index in found { state.runs.entry(index.run_id.clone()).or_insert_with(||Record::retained(index)); }
            bounded(json!({"version":1,"kind":"comparison_run_catalog","protocol_version":3,"input_lane":"scripted_baseline",
                "runs":state.runs.values().map(|r|r.index.metadata()).collect::<Vec<_>>(),"max_new_scenes":4}),64*1024)
        })
    }
    fn full_open_metadata(&self, lease: &WindowLease, epoch: u64, id: &str) -> Result<Value> {
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let state = self.full_lock()?;
            let run = state.runs.get(id).ok_or("UnknownEvaluationRun")?;
            let token = Self::mint(&mut parent, epoch, id.to_owned())?;
            run.status(epoch, &token, parent.job.as_ref())
        })
    }
    pub fn full_comparison_lookup(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        client: &str,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        if !valid_id(client) {
            return Err("InvalidEvaluationInput".into());
        }
        // An acknowledged active request is lookup-only; do not read a manifest
        // which its original worker may still be creating.
        let cached = self
            .full_lock()?
            .runs
            .values()
            .find(|r| r.index.client_id == client)
            .map(|r| r.index.run_id.clone());
        let id = if let Some(id) = cached {
            id
        } else {
            self.full_comparison_catalog(lease, epoch, granted)?;
            self.full_lock()?
                .runs
                .values()
                .find(|r| r.index.client_id == client)
                .map(|r| r.index.run_id.clone())
                .ok_or("UnknownEvaluationRun")?
        };
        self.full_open_metadata(lease, epoch, &id)
    }
    pub fn full_comparison_status(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let id = Self::token(&mut parent, epoch, token)?;
            self.full_lock()?
                .runs
                .get(&id)
                .ok_or("UnknownEvaluationRun")?
                .status(epoch, token, parent.job.as_ref())
        })
    }
    pub fn full_comparison_start(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        input: FullComparisonStart,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        batch(input.max_new_scenes)?;
        if !valid_id(&input.client_id) {
            return Err("InvalidEvaluationInput".into());
        }
        if let Ok(existing) = self.full_comparison_lookup(lease, epoch, granted, &input.client_id) {
            if existing["comparison_kind"] != kind_name(input.kind)
                || self
                    .full_lock()?
                    .runs
                    .get(existing["run_id"].as_str().ok_or("EvaluationInternal")?)
                    .ok_or("EvaluationInternal")?
                    .index
                    .initial_batch
                    != input.max_new_scenes
            {
                return Err("InvalidEvaluationInput".into());
            }
            return Ok(existing);
        }
        // A failed catalog is not an unknown request and must not be bypassed.
        self.full_comparison_catalog(lease, epoch, granted)?;
        self.full_launch(lease, epoch, None, Some(input), Work::Start)
    }
    pub fn full_comparison_open(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        id: &str,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        if !valid_id(id) {
            return Err("InvalidEvaluationInput".into());
        }
        self.full_comparison_catalog(lease, epoch, granted)?;
        if !self.full_lock()?.runs.contains_key(id) {
            return Err("UnknownEvaluationRun".into());
        }
        self.full_launch(lease, epoch, Some((id.to_owned(), 1)), None, Work::Open)
    }
    pub fn full_comparison_resume(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        token: &str,
        max_new_scenes: usize,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        batch(max_new_scenes)?;
        let id = lease.dispatch(epoch, || Self::token(&mut self.state()?, epoch, token))?;
        self.full_comparison_catalog(lease, epoch, granted)?;
        self.full_launch(lease, epoch, Some((id, max_new_scenes)), None, Work::Resume)
    }
    pub fn full_comparison_cancel(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
        operation: u64,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        if operation == 0 || operation > SAFE {
            return Err("InvalidEvaluationInput".into());
        }
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let id = Self::token(&mut parent, epoch, token)?;
            let job = parent
                .job
                .as_ref()
                .filter(|j| {
                    j.kind == JobKind::ComparisonRun
                        && j.epoch == epoch
                        && j.id == operation
                        && j.run == id
                })
                .ok_or("StaleEvaluationOperation")?;
            job.cancel.cancel();
            let mut full = self.full_lock()?;
            let r = full.runs.get_mut(&id).ok_or("UnknownEvaluationRun")?;
            r.phase = "stopping_at_boundary";
            r.status(epoch, token, parent.job.as_ref())
        })
    }
    pub fn full_comparison_close(
        &self,
        lease: &WindowLease,
        epoch: u64,
        _: bool,
        token: &str,
    ) -> Result<Value> {
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let id = Self::token(&mut parent, epoch, token)?;
            if let Some(job) = parent
                .job
                .as_ref()
                .filter(|j| j.kind == JobKind::ComparisonRun && j.epoch == epoch && j.run == id)
            {
                job.cancel.cancel();
            }
            let mut state = self.full_lock()?;
            let r = state.runs.get_mut(&id).ok_or("UnknownEvaluationRun")?;
            r.epoch = epoch;
            r.phase = "closed";
            r.error = None;
            r.report = None;
            let status = r.status(epoch, token, parent.job.as_ref())?;
            parent.tokens.remove(token);
            Ok(status)
        })
    }
    pub(super) fn full_comparison_retire(&self, epoch: u64) {
        if let Ok(mut state) = self.full_comparison.try_lock() {
            for r in state.runs.values_mut().filter(|r| r.epoch == epoch) {
                r.epoch = 0;
                r.report = None;
                r.error = None;
                r.operation = None;
                r.phase = "retained";
            }
        }
    }
    fn full_launch(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        existing: Option<(String, usize)>,
        mut input: Option<FullComparisonStart>,
        work: Work,
    ) -> Result<Value> {
        loop {
            let registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
            if self.state()?.job.is_some() {
                return Err("EvaluationBusy".into());
            }
            let old = self.worker.lock().map_err(|_| "EvaluationInternal")?.take();
            if let Some((_, handle)) = old {
                drop(registration);
                handle.join().map_err(|_| "EvaluationInternal")?;
                continue;
            }
            self.budget(None)?;
            let (id, token, operation, cancel, index, initial) = lease.dispatch(epoch, || {
                let mut parent = self.state()?;
                if parent.job.is_some() {
                    return Err("EvaluationBusy".into());
                }
                let mut full = self.full_lock()?;
                let (id, chosen_batch) = if let Some((id, batch)) = &existing {
                    (id.clone(), *batch)
                } else {
                    let input = input.take().ok_or("EvaluationInternal")?;
                    if let Some(r) = full
                        .runs
                        .values()
                        .find(|r| r.index.client_id == input.client_id)
                    {
                        // Another caller admitted this durable client while we
                        // joined a previous worker. Never allocate a duplicate.
                        if r.index.kind != input.kind
                            || r.index.initial_batch != input.max_new_scenes
                        {
                            return Err("InvalidEvaluationInput".into());
                        }
                        return Err("EvaluationBusy".into());
                    }
                    if full.runs.len() >= 32 {
                        return Err("EvaluationRunLimit".into());
                    }
                    let id = uuid()?;
                    let path = self.full_comparison_root().join(&id);
                    let _parent = pin(&self.full_comparison_root())?;
                    fs::create_dir(&path).map_err(|_| "EvaluationIo")?;
                    let _pins = pin(&path)?;
                    let created_ms = u64::try_from(
                        SystemTime::now()
                            .duration_since(UNIX_EPOCH)
                            .map_err(|_| "EvaluationIo")?
                            .as_millis(),
                    )
                    .map_err(|_| "EvaluationBudget")?;
                    let index = Index {
                        version: 1,
                        protocol_version: 3,
                        input_lane: "scripted_baseline".into(),
                        run_id: id.clone(),
                        client_id: input.client_id,
                        kind: input.kind,
                        initial_batch: input.max_new_scenes,
                        created_ms,
                        binding: wire::current_binding(false).map_err(failure)?,
                    };
                    let data = serde_json::to_vec(&index).map_err(|_| "EvaluationInternal")?;
                    if data.len() > 32 * 1024 {
                        return Err("EvaluationBudget".into());
                    }
                    let mut file = OpenOptions::new()
                        .create_new(true)
                        .write(true)
                        .open(path.join("desktop.json"))
                        .map_err(|_| "EvaluationIo")?;
                    file.write_all(&data)
                        .and_then(|_| file.sync_all())
                        .map_err(|_| "EvaluationIo")?;
                    let chosen_batch = input.max_new_scenes;
                    full.runs.insert(id.clone(), Record::retained(index));
                    (id, chosen_batch)
                };
                let operation = parent
                    .next
                    .checked_add(1)
                    .filter(|n| *n <= SAFE)
                    .ok_or("EvaluationBudget")?;
                let token = Self::mint(&mut parent, epoch, id.clone())?;
                let cancel = Cancellation::default();
                let r = full.runs.get_mut(&id).ok_or("UnknownEvaluationRun")?;
                r.epoch = epoch;
                r.operation = Some(operation);
                r.batch = chosen_batch;
                r.error = None;
                r.report = None;
                r.phase = if matches!(work, Work::Open) {
                    "opening"
                } else {
                    "running"
                };
                let index = r.index.clone();
                parent.next = operation;
                parent.job = Some(Job {
                    kind: JobKind::ComparisonRun,
                    epoch,
                    id: operation,
                    run: id.clone(),
                    cancel: cancel.clone(),
                    selected: None,
                    worker_active: true,
                });
                let initial = r.status(epoch, &token, parent.job.as_ref())?;
                Ok((id, token, operation, cancel, index, initial))
            })?;
            self.register_cancellation(lease, epoch, operation, &cancel);
            let manager = self.clone();
            let owner = lease.clone();
            let run = id.clone();
            let worker_cancel = cancel.clone();
            let chosen_batch = initial["batch"].as_u64().ok_or("EvaluationInternal")? as usize;
            let (send, registered) = std::sync::mpsc::channel();
            let worker = move || {
                if registered.recv().is_err() {
                    return;
                }
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    #[cfg(test)]
                    if manager
                        .panic_worker
                        .swap(false, std::sync::atomic::Ordering::SeqCst)
                    {
                        panic!("fixed scripted comparison worker fault");
                    }
                    #[cfg(any(test, feature = "dev-harness"))]
                    while manager.hold.load(std::sync::atomic::Ordering::SeqCst)
                        && !worker_cancel.is_cancelled()
                        && owner.valid(epoch)
                    {
                        std::thread::sleep(Duration::from_millis(5));
                    }
                    manager.full_work(&owner, epoch, &index, &worker_cancel, work, chosen_batch)
                }))
                .unwrap_or_else(|_| Err("EvaluationInternal".into()));
                let _ = owner.dispatch(epoch, || {
                    let parent = manager.state()?;
                    if !parent.job.as_ref().is_some_and(|j| {
                        j.kind == JobKind::ComparisonRun
                            && j.epoch == epoch
                            && j.id == operation
                            && j.run == run
                    }) {
                        return Err("Closed".into());
                    }
                    let mut state = manager.full_lock()?;
                    let r = state
                        .runs
                        .get_mut(&run)
                        .filter(|r| {
                            r.epoch == epoch
                                && r.operation == Some(operation)
                                && r.phase != "closed"
                        })
                        .ok_or("Closed")?;
                    match result {
                        Ok(report) => {
                            r.report = Some((
                                report.completed_scenes,
                                report.completed,
                                report.source_matches,
                            ));
                            r.phase = if report.completed {
                                "completed"
                            } else {
                                "paused"
                            };
                            r.error = None;
                        }
                        Err(error) => {
                            r.phase = "failed";
                            r.error = Some(error);
                            r.report = None;
                        }
                    }
                    Ok(())
                });
                manager.clear_cancellation(epoch, operation);
                let mut parent = manager.state.lock().unwrap_or_else(|p| p.into_inner());
                if parent.job.as_ref().is_some_and(|j| {
                    j.kind == JobKind::ComparisonRun
                        && j.epoch == epoch
                        && j.id == operation
                        && j.run == run
                }) {
                    parent.job = None;
                }
            };
            #[cfg(test)]
            let fail = self
                .fail_spawn
                .swap(false, std::sync::atomic::Ordering::SeqCst);
            #[cfg(not(test))]
            let fail = false;
            let spawned = if fail {
                Err(std::io::Error::other(
                    "fixed scripted comparison spawn refusal",
                ))
            } else {
                std::thread::Builder::new()
                    .name("locallore-comparison".into())
                    .spawn(worker)
            };
            match spawned {
                Ok(handle) => {
                    *self.worker.lock().unwrap_or_else(|p| p.into_inner()) = Some((epoch, handle));
                    let _ = send.send(());
                }
                Err(_) => {
                    self.clear_cancellation(epoch, operation);
                    let mut parent = self.state.lock().unwrap_or_else(|p| p.into_inner());
                    if parent.job.as_ref().is_some_and(|j| {
                        j.kind == JobKind::ComparisonRun && j.epoch == epoch && j.id == operation
                    }) {
                        parent.job = None;
                    }
                    let mut state = self.full_lock()?;
                    if let Some(r) = state.runs.get_mut(&id) {
                        r.phase = "failed";
                        r.error = Some("EvaluationInternal".into());
                    }
                    return Err("EvaluationInternal".into());
                }
            }
            drop(registration);
            return if lease.valid(epoch) {
                Ok(initial)
            } else {
                Err("Closed".into())
            };
        }
    }
    fn full_work(
        &self,
        lease: &WindowLease,
        epoch: u64,
        expected: &Index,
        cancel: &Cancellation,
        work: Work,
        chosen_batch: usize,
    ) -> Result<ComparisonReportV3> {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        if cancel.is_cancelled() {
            return Err("Cancelled".into());
        }
        let directory = self.full_comparison_root().join(&expected.run_id);
        let _pins = pin(&directory)?;
        let index = read_index(&directory, true)?;
        if index != *expected {
            return Err("EvaluationIntegrity".into());
        }
        let output = directory.join("work");
        if matches!(work, Work::Open) {
            return literal_v3::inspect_comparison(&output).map_err(failure);
        }
        if index.binding != wire::current_binding(false).map_err(failure)? {
            return Err("EvaluationSourceMismatch".into());
        }
        let resume = matches!(work, Work::Resume);
        if resume {
            if !output.join("run.json").exists() {
                return Err("EvaluationNotReady".into());
            }
            let report = literal_v3::inspect_comparison(&output).map_err(failure)?;
            if report.completed {
                return Ok(report);
            }
        }
        let reference = if index.kind == core::ComparisonKind::PairedSnapshots {
            let path = directory.join("reference-source");
            if !resume {
                core::prepare_reference(&path, cancel).map_err(failure)?;
            }
            Some(core::open_reference(&path).map_err(failure)?)
        } else {
            None
        };
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        if cancel.is_cancelled() {
            return Err("Cancelled".into());
        }
        let report = literal_v3::run_comparison(
            &output,
            resume,
            index.kind,
            cancel,
            chosen_batch,
            LaneFactory::ScriptedBaseline,
            reference.as_ref(),
        )
        .map_err(failure)?;
        self.budget(Some(&directory))?;
        Ok(report)
    }
}
#[cfg(test)]
mod review_tests;
