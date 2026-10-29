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
mod versioned;
pub(crate) use versioned::FullComparisonProtocol;
use versioned::{Index, Report};

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
pub struct FullComparisonNativeResume {
    pub run_token: String,
    pub max_new_scenes: usize,
}
#[derive(Clone, Copy, PartialEq, Eq)]
enum ComparisonLane {
    Scripted,
    Native,
    SceneNative,
}
impl ComparisonLane {
    fn native(self) -> bool {
        matches!(self, Self::Native | Self::SceneNative)
    }
    fn version(self) -> u16 {
        if self == Self::SceneNative {
            3
        } else if self.native() {
            2
        } else {
            1
        }
    }
    fn name(self) -> &'static str {
        if self.native() {
            "approved_native"
        } else {
            "scripted_baseline"
        }
    }
    fn protocol_version(self) -> u16 {
        if self == Self::SceneNative {
            4
        } else {
            3
        }
    }
}
type ExecutionConsent = Box<dyn FnOnce(&Value) -> Result<bool> + Send + 'static>;
struct NativeExecution {
    models: Arc<crate::models::ModelManager>,
    consent: ExecutionConsent,
}
enum Execution {
    Scripted,
    Native(NativeExecution),
    SceneNative(NativeExecution),
}
impl Execution {
    fn lane(&self) -> ComparisonLane {
        match self {
            Self::Scripted => ComparisonLane::Scripted,
            Self::Native(_) => ComparisonLane::Native,
            Self::SceneNative(_) => ComparisonLane::SceneNative,
        }
    }
    fn native(self) -> Option<NativeExecution> {
        match self {
            Self::Scripted => None,
            Self::Native(native) | Self::SceneNative(native) => Some(native),
        }
    }
}
fn kind_name(kind: core::ComparisonKind) -> &'static str {
    match kind {
        core::ComparisonKind::PairedSnapshots => "paired",
        core::ComparisonKind::ContinuousRollout => "rollout",
    }
}
struct Record {
    index: Index,
    epoch: u64,
    operation: Option<u64>,
    batch: usize,
    phase: &'static str,
    error: Option<String>,
    cause: Option<String>,
    report: Option<(usize, bool, bool)>,
}
impl Record {
    fn retained(index: Index) -> Self {
        let batch = index.initial_batch();
        Self {
            index,
            epoch: 0,
            operation: None,
            batch,
            phase: "retained",
            error: None,
            cause: None,
            report: None,
        }
    }
    fn status(&self, epoch: u64, token: &str, job: Option<&Job>) -> Result<Value> {
        let lane = self.index.lane()?;
        let visible = self.epoch == epoch;
        let report = self.report.filter(|_| visible && self.phase != "closed");
        let owned =
            job.filter(|j| j.kind == JobKind::ComparisonRun && j.run == self.index.run_id());
        let running = owned.is_some_and(|j| j.worker_active && (lane.native() || j.epoch == epoch));
        let cleanup_running = lane.native()
            && owned
                .and_then(|j| j.selected.as_ref())
                .is_some_and(|o| o.cleanup_running);
        let cleanup_required = lane.native()
            && owned.is_some_and(|j| j.selected.is_some() && (!j.worker_active || cleanup_running));
        let mut value = json!({"version":lane.version(),"kind":"comparison_run","protocol_version":lane.protocol_version(),"input_lane":lane.name(),
            "client_id":self.index.client_id(),"run_id":self.index.run_id(),"run_token":token,
            "operation_id":if visible{self.operation}else{None},"comparison_kind":kind_name(self.index.kind()),"batch":self.batch,
            "phase":if visible{self.phase}else{"retained"},"running":running,"error":if visible{self.error.as_ref()}else{None},
            "completed_scenes":report.map_or(0,|r|r.0),"completed":report.is_some_and(|r|r.1),"report_ready":report.is_some() && !running && !cleanup_required && !cleanup_running,
            "source_matches":report.map(|r|r.2)});
        if lane.native() {
            value["cleanup_required"] = json!(cleanup_required);
            value["cleanup_running"] = json!(cleanup_running);
            value["cause"] = json!(if visible { self.cause.as_ref() } else { None });
        }
        bounded(value, 32 * 1024)
    }
}
#[derive(Default)]
pub(super) struct FullComparisonState {
    runs: BTreeMap<String, Record>,
    token_leases: BTreeMap<String, (u64, std::sync::Weak<()>)>,
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
    if manifest["version"] != index.protocol_version()
        || manifest["kind"]
            != serde_json::to_value(index.kind()).map_err(|_| "EvaluationInternal")?
        || manifest["binding"] != index.binding_value()?
        || manifest["source_sha256"] != index.source_sha256()
    {
        return Err("EvaluationIntegrity".into());
    }
    Ok(())
}
fn read_index(directory: &Path, manifest: bool) -> Result<Index> {
    let value = read_json(&directory.join("desktop.json"), 32 * 1024)?;
    let index = Index::decode(value)?;
    index.validate_shape()?;
    if !valid_id(index.run_id())
        || !valid_id(index.client_id())
        || directory.file_name().and_then(|x| x.to_str()) != Some(index.run_id())
        || !(1..=4).contains(&index.initial_batch())
        || index.created_ms() > SAFE
    {
        return Err("EvaluationIntegrity".into());
    }
    if manifest {
        validate_manifest(directory, &index)?;
    }
    Ok(index)
}
#[derive(Clone, Copy)]
enum Work {
    Start,
    Resume,
    Open,
}
struct Launch {
    lane: ComparisonLane,
    existing: Option<(String, usize)>,
    input: Option<FullComparisonStart>,
    work: Work,
    native: Option<NativeExecution>,
}
enum PreparedWork {
    Inspected(Box<Report>),
    Execute {
        output: PathBuf,
        reference: Option<Box<core::ValidatedReference>>,
        _pins: Vec<File>,
    },
}
struct FullOutcome {
    result: Result<Report>,
    retained: Option<(
        crate::models::EvaluationReservation,
        Arc<Mutex<locallore_local_runtime::LocalRuntime>>,
    )>,
    uncertain: bool,
    cause: Option<String>,
}
impl FullOutcome {
    fn plain(result: Result<Report>) -> Self {
        Self {
            result,
            retained: None,
            uncertain: false,
            cause: None,
        }
    }
    fn native(
        error: core::selected::SelectedNativeFailure<crate::models::EvaluationReservation>,
    ) -> Self {
        let code = super::selected::failure(error.code());
        let cause = error.cause().map(super::selected::failure);
        let uncertain = error.cleanup_uncertain();
        let retained = error.into_retained().ok();
        Self {
            result: Err(code),
            retained,
            uncertain,
            cause,
        }
    }
}
impl EvaluationManager {
    #[cfg(feature = "dev-harness")]
    pub fn full_comparison_fixture_inventory(&self) -> Result<Value> {
        use sha2::{Digest, Sha256};
        fn visit(
            root: &Path,
            path: &Path,
            depth: usize,
            total: &mut u64,
            entries: &mut usize,
            files: &mut BTreeMap<String, String>,
        ) -> Result<()> {
            if depth > 12 || files.len() > 8192 {
                return Err("EvaluationBudget".into());
            }
            let _pins = pin(path)?;
            for entry in fs::read_dir(path).map_err(|_| "EvaluationIo")? {
                *entries = entries.checked_add(1).ok_or("EvaluationBudget")?;
                if *entries > 8192 {
                    return Err("EvaluationBudget".into());
                }
                let entry = entry.map_err(|_| "EvaluationIo")?;
                let path = entry.path();
                let pins = pin(&path)?;
                let file = pins.last().ok_or("EvaluationIo")?;
                let meta = file.metadata().map_err(|_| "EvaluationIo")?;
                if meta.is_dir() {
                    visit(root, &path, depth + 1, total, entries, files)?;
                } else {
                    if !meta.is_file() || meta.len() > 8 * 1024 * 1024 || files.len() >= 8192 {
                        return Err("EvaluationBudget".into());
                    }
                    *total = total.checked_add(meta.len()).ok_or("EvaluationBudget")?;
                    if *total > 128 * 1024 * 1024 {
                        return Err("EvaluationBudget".into());
                    }
                    let mut bytes = vec![];
                    file.take(8 * 1024 * 1024 + 1)
                        .read_to_end(&mut bytes)
                        .map_err(|_| "EvaluationIo")?;
                    if bytes.len() > 8 * 1024 * 1024 {
                        return Err("EvaluationBudget".into());
                    }
                    let relative = path
                        .strip_prefix(root)
                        .map_err(|_| "UnsafeEvaluationPath")?
                        .to_str()
                        .ok_or("UnsafeEvaluationPath")?
                        .replace('\\', "/");
                    files.insert(relative, format!("{:x}", Sha256::digest(&bytes)));
                }
            }
            Ok(())
        }
        if !crate::harness::active()
            || std::env::var("LOCALLORE_D07_FULL_COMPARISON_HARNESS").as_deref() != Ok("1")
        {
            return Err("Forbidden".into());
        }
        let root = self.full_comparison_root();
        let mut files = BTreeMap::new();
        if root.exists() {
            visit(&root, &root, 0, &mut 0, &mut 0, &mut files)?;
        }
        let encoded = serde_json::to_vec(&files).map_err(|_| "EvaluationInternal")?;
        bounded(
            json!({"version":1,"kind":"full_comparison_fixture","synthetic":true,"digest":format!("{:x}",Sha256::digest(&encoded)),"file_count":files.len(),"inventory":files}),
            2 * 1024 * 1024,
        )
    }
    pub(super) fn full_comparison_root(&self) -> PathBuf {
        self.root.with_file_name("comparison-evaluations")
    }
    fn full_lock(&self) -> Result<std::sync::MutexGuard<'_, FullComparisonState>> {
        self.full_comparison
            .lock()
            .map_err(|_| "EvaluationInternal".into())
    }
    fn full_token_lane(
        &self,
        parent: &mut State,
        lease: &WindowLease,
        epoch: u64,
        token: &str,
        lane: ComparisonLane,
    ) -> Result<String> {
        let id = parent
            .tokens
            .get(token)
            .filter(|t| t.epoch == epoch)
            .map(|t| t.run.clone())
            .ok_or("UnknownEvaluationRun")?;
        let mut full = self.full_lock()?;
        full.token_leases
            .retain(|key, _| parent.tokens.contains_key(key));
        let matches = full
            .token_leases
            .get(token)
            .is_some_and(|(owner_epoch, owner)| {
                *owner_epoch == epoch && lease.owns_identity(owner)
            })
            && full
                .runs
                .get(&id)
                .is_some_and(|r| r.index.lane().ok() == Some(lane));
        drop(full);
        if !matches {
            return Err("UnknownEvaluationRun".into());
        }
        Self::token(parent, epoch, token)
    }
    fn full_mint(
        parent: &mut State,
        full: &mut FullComparisonState,
        lease: &WindowLease,
        epoch: u64,
        run: String,
    ) -> Result<String> {
        let token = Self::mint_reusing(parent, epoch, run, |id| {
            full.token_leases
                .get(id)
                .is_some_and(|(owner_epoch, owner)| {
                    *owner_epoch == epoch && lease.owns_identity(owner)
                })
        })?;
        full.token_leases
            .retain(|id, _| parent.tokens.contains_key(id));
        full.token_leases
            .insert(token.clone(), (epoch, lease.identity()));
        Ok(token)
    }
    pub fn full_comparison_catalog(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
    ) -> Result<Value> {
        self.full_catalog_lane(lease, epoch, granted, ComparisonLane::Scripted)
    }
    fn full_catalog_lane(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        lane: ComparisonLane,
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
            if !clients.insert(index.client_id().to_owned()) {
                return Err("EvaluationIntegrity".into());
            }
            found.push(index);
        }
        lease.dispatch(epoch,|| {
            let mut state=self.full_lock()?;
            for index in &found {
                if state.runs.get(index.run_id()).is_some_and(|r|r.index!=*index) { return Err("EvaluationIntegrity".into()); }
            }
            // Cache contains no read grant or canonical Store. Missing durable
            // metadata never becomes an invented retained run.
            let ids:BTreeSet<_>=found.iter().map(|x|x.run_id().to_owned()).collect();
            state.runs.retain(|id,_|ids.contains(id));
            for index in found { state.runs.entry(index.run_id().to_owned()).or_insert_with(||Record::retained(index)); }
            bounded(json!({"version":lane.version(),"kind":"comparison_run_catalog","protocol_version":lane.protocol_version(),"input_lane":lane.name(),
                "runs":state.runs.values().filter(|r|r.index.lane().ok()==Some(lane)).map(|r|r.index.metadata()).collect::<Vec<_>>(),"max_new_scenes":4}),64*1024)
        })
    }
    pub fn full_comparison_pick(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        client: &str,
        run_id: &str,
        consent: impl FnOnce() -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        self.full_pick_lane(
            lease,
            epoch,
            granted,
            (client, run_id),
            consent,
            ComparisonLane::Scripted,
        )
    }
    fn full_pick_lane(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        (client, run_id): (&str, &str),
        consent: impl FnOnce() -> Result<bool> + Send + 'static,
        lane: ComparisonLane,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        if !valid_id(client) || !valid_id(run_id) {
            return Err("InvalidEvaluationInput".into());
        }
        self.full_catalog_lane(lease, epoch, granted, lane)?;
        let expected = self
            .full_lock()?
            .runs
            .get(run_id)
            .ok_or("UnknownEvaluationRun")?
            .index
            .clone();
        let directory = self.full_comparison_root().join(run_id);
        if expected.lane()? != lane {
            return Err("UnknownEvaluationRun".into());
        }
        // Renderer UUIDs never become paths, read grants or a substitute for
        // independent native spoiler confirmation.
        self.comparison_pick(lease, epoch, granted, client, move || {
            let _pins = pin(&directory)?;
            if read_index(&directory, true)? != expected {
                return Err("EvaluationIntegrity".into());
            }
            if !consent()? {
                return Ok(None);
            }
            if read_index(&directory, true)? != expected {
                return Err("EvaluationIntegrity".into());
            }
            Ok(Some(directory.join("work")))
        })
    }
    fn full_open_metadata(
        &self,
        lease: &WindowLease,
        epoch: u64,
        id: &str,
        lane: ComparisonLane,
    ) -> Result<Value> {
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let mut state = self.full_lock()?;
            let run = state.runs.get(id).ok_or("UnknownEvaluationRun")?;
            if run.index.lane()? != lane {
                return Err("UnknownEvaluationRun".into());
            }
            let token = Self::full_mint(&mut parent, &mut state, lease, epoch, id.to_owned())?;
            let run = state.runs.get(id).ok_or("UnknownEvaluationRun")?;
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
        self.full_lookup_lane(lease, epoch, granted, client, ComparisonLane::Scripted)
    }
    fn full_lookup_lane(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        client: &str,
        lane: ComparisonLane,
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
            .find(|r| r.index.client_id() == client)
            .map(|r| r.index.run_id().to_owned());
        let id = if let Some(id) = cached {
            id
        } else {
            self.full_catalog_lane(lease, epoch, granted, lane)?;
            self.full_lock()?
                .runs
                .values()
                .find(|r| r.index.client_id() == client)
                .map(|r| r.index.run_id().to_owned())
                .ok_or("UnknownEvaluationRun")?
        };
        self.full_open_metadata(lease, epoch, &id, lane)
    }
    pub fn full_comparison_status(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
    ) -> Result<Value> {
        self.full_status_lane(lease, epoch, granted, token, ComparisonLane::Scripted)
    }
    fn full_status_lane(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
        lane: ComparisonLane,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let id = self.full_token_lane(&mut parent, lease, epoch, token, lane)?;
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
        self.full_start_execution(lease, epoch, granted, input, Execution::Scripted)
    }
    fn full_start_execution(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        input: FullComparisonStart,
        execution: Execution,
    ) -> Result<Value> {
        let lane = execution.lane();
        authorize(lease, epoch, granted)?;
        batch(input.max_new_scenes)?;
        if !valid_id(&input.client_id) {
            return Err("InvalidEvaluationInput".into());
        }
        if let Ok(existing) = self.full_lookup_lane(lease, epoch, granted, &input.client_id, lane) {
            if existing["comparison_kind"] != kind_name(input.kind)
                || self
                    .full_lock()?
                    .runs
                    .get(existing["run_id"].as_str().ok_or("EvaluationInternal")?)
                    .ok_or("EvaluationInternal")?
                    .index
                    .initial_batch()
                    != input.max_new_scenes
            {
                return Err("InvalidEvaluationInput".into());
            }
            return Ok(existing);
        }
        // A failed catalog is not an unknown request and must not be bypassed.
        self.full_catalog_lane(lease, epoch, granted, lane)?;
        if self
            .full_lock()?
            .runs
            .values()
            .any(|r| r.index.client_id() == input.client_id && r.index.lane().ok() != Some(lane))
        {
            return Err("InvalidEvaluationInput".into());
        }
        let identity = (input.client_id.clone(), input.kind, input.max_new_scenes);
        let admitted = self.full_launch(
            lease,
            epoch,
            Launch {
                lane,
                existing: None,
                input: Some(input),
                work: Work::Start,
                native: execution.native(),
            },
        );
        if admitted
            .as_ref()
            .err()
            .is_some_and(|error| error == "EvaluationBusy")
        {
            // The original client may have been admitted while this caller was
            // loading the catalog or joining an older worker. Return that exact
            // durable identity rather than treating the retry as a new request.
            if let Ok(existing) = self.full_lookup_lane(lease, epoch, granted, &identity.0, lane) {
                let same = self
                    .full_lock()?
                    .runs
                    .get(existing["run_id"].as_str().ok_or("EvaluationInternal")?)
                    .is_some_and(|r| {
                        r.index.kind() == identity.1
                            && r.index.initial_batch() == identity.2
                            && r.index.lane().ok() == Some(lane)
                    });
                return if same {
                    Ok(existing)
                } else {
                    Err("InvalidEvaluationInput".into())
                };
            }
        }
        admitted
    }
    pub fn full_comparison_open(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        id: &str,
    ) -> Result<Value> {
        self.full_open_lane(lease, epoch, granted, id, ComparisonLane::Scripted)
    }
    fn full_open_lane(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        id: &str,
        lane: ComparisonLane,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        if !valid_id(id) {
            return Err("InvalidEvaluationInput".into());
        }
        self.full_catalog_lane(lease, epoch, granted, lane)?;
        if !self
            .full_lock()?
            .runs
            .get(id)
            .is_some_and(|r| r.index.lane().ok() == Some(lane))
        {
            return Err("UnknownEvaluationRun".into());
        }
        self.full_launch(
            lease,
            epoch,
            Launch {
                lane,
                existing: Some((id.to_owned(), 1)),
                input: None,
                work: Work::Open,
                native: None,
            },
        )
    }
    pub fn full_comparison_resume(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        token: &str,
        max_new_scenes: usize,
    ) -> Result<Value> {
        self.full_resume_execution(
            lease,
            epoch,
            granted,
            (token, max_new_scenes),
            Execution::Scripted,
        )
    }
    fn full_resume_execution(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        (token, max_new_scenes): (&str, usize),
        execution: Execution,
    ) -> Result<Value> {
        let lane = execution.lane();
        authorize(lease, epoch, granted)?;
        batch(max_new_scenes)?;
        let id = lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            self.full_token_lane(&mut parent, lease, epoch, token, lane)
        })?;
        self.full_catalog_lane(lease, epoch, granted, lane)?;
        self.full_launch(
            lease,
            epoch,
            Launch {
                lane,
                existing: Some((id, max_new_scenes)),
                input: None,
                work: Work::Resume,
                native: execution.native(),
            },
        )
    }
    pub fn full_comparison_cancel(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
        operation: u64,
    ) -> Result<Value> {
        self.full_cancel_lane(
            lease,
            epoch,
            granted,
            token,
            operation,
            ComparisonLane::Scripted,
        )
    }
    fn full_cancel_lane(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
        operation: u64,
        lane: ComparisonLane,
    ) -> Result<Value> {
        authorize(lease, epoch, granted)?;
        if operation == 0 || operation > SAFE {
            return Err("InvalidEvaluationInput".into());
        }
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let id = self.full_token_lane(&mut parent, lease, epoch, token, lane)?;
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
        self.full_close_lane(lease, epoch, token, ComparisonLane::Scripted)
    }
    fn full_close_lane(
        &self,
        lease: &WindowLease,
        epoch: u64,
        token: &str,
        lane: ComparisonLane,
    ) -> Result<Value> {
        lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            let id = self.full_token_lane(&mut parent, lease, epoch, token, lane)?;
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
            r.cause = None;
            r.report = None;
            let status = r.status(epoch, token, parent.job.as_ref())?;
            parent.tokens.remove(token);
            state.token_leases.remove(token);
            Ok(status)
        })
    }
    pub(super) fn full_comparison_retire(&self, epoch: u64) {
        if let Ok(mut state) = self.full_comparison.try_lock() {
            state
                .token_leases
                .retain(|_, (owner_epoch, _)| *owner_epoch != epoch);
            for r in state.runs.values_mut().filter(|r| r.epoch == epoch) {
                r.epoch = 0;
                r.report = None;
                r.error = None;
                r.cause = None;
                r.operation = None;
                r.phase = "retained";
            }
        }
    }
    fn full_launch(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        launch: Launch,
    ) -> Result<Value> {
        let Launch {
            lane,
            existing,
            mut input,
            work,
            native,
        } = launch;
        loop {
            let registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
            // Another start may win after this caller's outer catalog read.
            // Keep a conflicting durable client distinct from global Busy,
            // even while that winning worker remains active.
            if let Some(input) = input.as_ref() {
                let full = self.full_lock()?;
                if let Some(record) = full
                    .runs
                    .values()
                    .find(|record| record.index.client_id() == input.client_id)
                {
                    if record.index.kind() != input.kind
                        || record.index.initial_batch() != input.max_new_scenes
                        || record.index.lane()? != lane
                    {
                        return Err("InvalidEvaluationInput".into());
                    }
                }
            }
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
            let (id, _token, operation, cancel, index, initial) = lease.dispatch(epoch, || {
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
                        .find(|r| r.index.client_id() == input.client_id)
                    {
                        // Another caller admitted this durable client while we
                        // joined a previous worker. Never allocate a duplicate.
                        if r.index.kind() != input.kind
                            || r.index.initial_batch() != input.max_new_scenes
                            || r.index.lane()? != lane
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
                    let chosen_batch = input.max_new_scenes;
                    let index = Index::new(lane, id.clone(), input, created_ms)?;
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
                    full.runs.insert(id.clone(), Record::retained(index));
                    (id, chosen_batch)
                };
                let operation = parent
                    .next
                    .checked_add(1)
                    .filter(|n| *n <= SAFE)
                    .ok_or("EvaluationBudget")?;
                let token = Self::full_mint(&mut parent, &mut full, lease, epoch, id.clone())?;
                let cancel = Cancellation::default();
                let r = full.runs.get_mut(&id).ok_or("UnknownEvaluationRun")?;
                if r.index.lane()? != lane {
                    return Err("UnknownEvaluationRun".into());
                }
                if r.epoch != epoch || !matches!(work, Work::Resume) {
                    r.report = None;
                }
                r.epoch = epoch;
                r.operation = Some(operation);
                r.batch = chosen_batch;
                r.error = None;
                r.cause = None;
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
                    selected: native.as_ref().map(|n| super::selected::SelectedOwnership {
                        models: n.models.clone(),
                        witness: None,
                        retained: None,
                        cleanup_running: false,
                    }),
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
                // The fixed panic is before execution only. Actual native
                // ownership is returned by the shared typed boundary, never
                // erased by a blanket catch/unconditional Job clear.
                #[cfg(test)]
                let injected = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    if manager
                        .panic_worker
                        .swap(false, std::sync::atomic::Ordering::SeqCst)
                    {
                        panic!("fixed pre-execution comparison worker fault");
                    }
                }))
                .is_err();
                #[cfg(not(test))]
                let injected = false;
                let execute = || {
                    #[cfg(any(test, feature = "dev-harness"))]
                    while manager.hold.load(std::sync::atomic::Ordering::SeqCst)
                        && !worker_cancel.is_cancelled()
                        && owner.valid(epoch)
                    {
                        std::thread::sleep(Duration::from_millis(5));
                    }
                    manager.full_work(
                        &owner,
                        (epoch, operation),
                        &index,
                        &worker_cancel,
                        (work, chosen_batch),
                        native,
                    )
                };
                let outcome = if injected {
                    FullOutcome::plain(Err("EvaluationInternal".into()))
                } else if lane.native() {
                    execute()
                } else {
                    std::panic::catch_unwind(std::panic::AssertUnwindSafe(execute))
                        .unwrap_or_else(|_| FullOutcome::plain(Err("EvaluationInternal".into())))
                };
                let _ = manager.full_finish(&owner, epoch, &run, operation, outcome);
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
    fn full_prepare_work(
        &self,
        lease: &WindowLease,
        epoch: u64,
        expected: &Index,
        cancel: &Cancellation,
        work: Work,
    ) -> Result<PreparedWork> {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        if cancel.is_cancelled() {
            return Err("Cancelled".into());
        }
        let directory = self.full_comparison_root().join(expected.run_id());
        let _pins = pin(&directory)?;
        let index = read_index(&directory, true)?;
        if index != *expected {
            return Err("EvaluationIntegrity".into());
        }
        let output = directory.join("work");
        if matches!(work, Work::Open) {
            return index
                .inspect(&output)
                .map(|report| PreparedWork::Inspected(Box::new(report)));
        }
        if !index.matches_current()? {
            return Err("EvaluationSourceMismatch".into());
        }
        let resume = matches!(work, Work::Resume);
        if resume {
            if !output.join("run.json").exists() {
                return Err("EvaluationNotReady".into());
            }
            let report = index.inspect(&output)?;
            if report.completed() {
                return Ok(PreparedWork::Inspected(Box::new(report)));
            }
        }
        // A boundary quota must refuse before invoking the shared runner or
        // preparing a reference, not after a new canonical scene is committed.
        // Completed resume above remains a read-only verification.
        self.budget(Some(&directory))?;
        let reference = if index.kind() == core::ComparisonKind::PairedSnapshots {
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
        Ok(PreparedWork::Execute {
            output,
            reference: reference.map(Box::new),
            _pins,
        })
    }
}
mod native;
mod native_for;
#[cfg(test)]
mod native_review_tests;
#[cfg(test)]
mod review_tests;
#[cfg(test)]
mod scene_native_review;
#[cfg(test)]
mod window_identity_review;
