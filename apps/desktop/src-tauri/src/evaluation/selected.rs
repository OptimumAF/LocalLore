//! Native selected workflow over the existing single evaluation job/worker.
//! Paths, grants, prepared plans and runtime owners never come from renderer JSON.
use super::*;
use crate::models::{self, ModelManager};
use locallore::inspection_query::Observer;
use locallore_eval::local_lane::comparison::{desktop_api as source_reader, selected as producer};
use producer::desktop_read as shared;
#[cfg(test)]
use source_reader::Edge;
use source_reader::{Arm, EvidenceRequest};
use std::io::Read;
use std::sync::{mpsc, Weak};
mod versioned;

const TTL: Duration = Duration::from_secs(300);
const CLIENTS: usize = 4;
const SAFE: u64 = 9_007_199_254_740_991;
const INDEX_CAP: usize = 32 * 1024;
#[cfg(test)]
type StartPrecheckPause = (
    std::sync::mpsc::SyncSender<()>,
    std::sync::mpsc::Receiver<()>,
);
#[cfg(test)]
thread_local! {
    static SELECTED_START_PRECHECK_PAUSE: std::cell::RefCell<Option<StartPrecheckPause>> = const { std::cell::RefCell::new(None) };
}
type Runtime = Arc<Mutex<locallore_local_runtime::LocalRuntime>>;
type Consent = Box<dyn FnOnce(&Value) -> Result<bool> + Send>;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum SelectedInputLane {
    ScriptedBaseline,
    ApprovedNative,
}
impl SelectedInputLane {
    fn input(self) -> &'static str {
        match self {
            Self::ScriptedBaseline => "scripted_baseline",
            Self::ApprovedNative => "approved_native",
        }
    }
    fn stored(self) -> &'static str {
        match self {
            Self::ScriptedBaseline => "scripted_selected_case",
            Self::ApprovedNative => "native_selected_case",
        }
    }
    fn shared(self) -> producer::SelectedLane {
        match self {
            Self::ScriptedBaseline => producer::SelectedLane::ScriptedBaseline,
            Self::ApprovedNative => producer::SelectedLane::ApprovedNative,
        }
    }
    fn parse(value: &str) -> Result<Self> {
        match value {
            "scripted_baseline" => Ok(Self::ScriptedBaseline),
            "approved_native" => Ok(Self::ApprovedNative),
            _ => Err("EvaluationIntegrity".into()),
        }
    }
}
pub struct SelectedPrepareInput {
    pub client_id: String,
    pub reader_client_id: String,
    pub run_token: String,
    pub binding: String,
    pub turn_id: String,
    pub arm: Arm,
    pub lane: SelectedInputLane,
}
pub struct SelectedResumeInput {
    pub client_id: String,
    pub run_token: String,
    pub reader_client_id: String,
    pub source_token: String,
    pub source_binding: String,
}
#[derive(Clone)]
pub struct SelectedReadInput {
    pub client_id: String,
    pub run_token: String,
    pub binding: String,
}
pub struct SelectedEvidenceInput {
    pub identity: SelectedReadInput,
    pub arm: Arm,
    pub request: EvidenceRequest,
}

// The only runtime ownership payload lives in the existing parent Job. It is
// never placed in expiring presentation records or a second owner registry.
pub(super) struct SelectedOwnership {
    pub(super) models: Arc<ModelManager>,
    pub(super) witness: Option<models::CleanupWitness>,
    pub(super) retained: Option<(models::EvaluationReservation, Runtime)>,
    pub(super) cleanup_running: bool,
}
struct ExecutionGrant;
struct ReadGrant;
struct Prepared {
    plan: versioned::Plan,
    metadata: Value,
    source_binding: String,
    _grant: ExecutionGrant,
}
struct ReadCap {
    opened: versioned::Opened,
    _grant: ReadGrant,
}
struct Record {
    lease: Weak<WindowLease>,
    models: Weak<ModelManager>,
    epoch: u64,
    client: String,
    operation: Option<u64>,
    phase: &'static str,
    running: bool,
    revoked: bool,
    lane: Option<SelectedInputLane>,
    plan_token: Option<String>,
    run_id: Option<String>,
    run_token: Option<String>,
    binding: Option<String>,
    metadata: Option<Value>,
    plan: Option<Box<Prepared>>,
    cap: Option<Box<ReadCap>>,
    consumed: Option<(String, Value)>,
    error: Option<String>,
    cause: Option<String>,
    cleanup_required: bool,
    cancel: Cancellation,
    touched: Instant,
}
impl Record {
    fn cache_execution_status(&mut self, operation: u64, status: &Value) {
        // Read/resume operations cannot rebind the admitted start receipt or
        // promote their later private read grant into an execution response.
        if let Some((_, cached)) = self
            .consumed
            .as_mut()
            .filter(|(_, cached)| cached["operation_id"].as_u64() == Some(operation))
        {
            *cached = status.clone();
        }
    }
    fn owns(&self, lease: &WindowLease, epoch: u64) -> bool {
        self.epoch == epoch && std::ptr::eq(self.lease.as_ptr(), lease)
    }
    fn status(&self) -> Result<Value> {
        let visible = !self.revoked;
        bounded(
            json!({"version":1,"kind":"selected_evaluation","client_id":self.client,
            "operation_id":if visible {self.operation}else{None},"phase":if visible{self.phase}else{"closed"},
            "running":self.running,"lane":if visible{self.lane.map(SelectedInputLane::input)}else{None},
            "plan_token":if visible{self.plan_token.as_ref()}else{None},"run_id":if visible{self.run_id.as_ref()}else{None},
            "run_token":if visible{self.run_token.as_ref()}else{None},"binding":if visible{self.binding.as_ref()}else{None},
            "prepared":if visible{self.metadata.as_ref()}else{None},"error":if visible{self.error.as_ref()}else{None},
            "cause":if visible{self.cause.as_ref()}else{None},"cleanup_required":self.cleanup_required}),
            24 * 1024,
        )
    }
    fn revoke(&mut self, discard: &mut Vec<Discard>) {
        self.revoked = true;
        self.cancel.cancel();
        self.plan_token = None;
        self.run_token = None;
        self.binding = None;
        self.metadata = None;
        self.run_id = None;
        self.lane = None;
        self.consumed = None;
        if let Some(plan) = self.plan.take() {
            discard.push(Discard::Plan(plan));
        }
        if let Some(cap) = self.cap.take() {
            discard.push(Discard::Cap(cap));
        }
    }
}
enum Discard {
    Plan(Box<Prepared>),
    Cap(Box<ReadCap>),
}
fn dispose(discard: Vec<Discard>) {
    for value in discard {
        match value {
            Discard::Plan(plan) => drop(plan),
            Discard::Cap(cap) => drop(cap),
        }
    }
}
#[derive(Default)]
pub(super) struct SelectedState {
    records: BTreeMap<String, Record>,
    cleanup_error: Option<String>,
}

#[derive(serde::Serialize, serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct Index {
    version: u16,
    run_id: String,
    created: u64,
    client_id: String,
    lane: String,
    source_binding: String,
    prepared: Value,
}
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
fn hex(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn id(value: &str) -> bool {
    valid_id(value) && value.bytes().all(|b| !b.is_ascii_uppercase())
}
fn word(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn keys(value: &Value, expected: &[&str]) -> bool {
    value.as_object().is_some_and(|o| {
        o.len() == expected.len() && expected.iter().all(|key| o.contains_key(*key))
    })
}
#[derive(Clone, Copy, PartialEq, Eq)]
enum PreparedUse {
    Fresh,
    Recorded,
}
fn construction_family_matches<T: serde::Serialize>(
    value: &Value,
    current: T,
    legacy: T,
    usage: PreparedUse,
) -> bool {
    serde_json::to_value(current).is_ok_and(|expected| *value == expected)
        || (usage == PreparedUse::Recorded
            && serde_json::to_value(legacy).is_ok_and(|expected| *value == expected))
}
fn prepared_valid(value: &Value, usage: PreparedUse) -> bool {
    let version_valid = match versioned::prepared_protocol(value) {
        Some(versioned::Protocol::V1) => keys(
            value,
            &["version", "kind", "binding", "lane", "selection", "arms"],
        ),
        Some(versioned::Protocol::V2) => {
            keys(
                value,
                &[
                    "version",
                    "kind",
                    "binding",
                    "lane",
                    "selection",
                    "arms",
                    "source_protocol_version",
                    "constructions",
                ],
            ) && construction_family_matches(
                &value["constructions"],
                locallore_eval::memory_comparison_v3::current_arm_descriptors(),
                locallore_eval::memory_comparison_v3::arm_descriptors(),
                usage,
            )
        }
        Some(versioned::Protocol::V3) => {
            keys(
                value,
                &[
                    "version",
                    "kind",
                    "binding",
                    "source_binding",
                    "lane",
                    "selection",
                    "arms",
                    "source_protocol_version",
                    "constructions",
                ],
            ) && value["lane"] == "scripted_selected_case"
                && value["source_binding"].as_str().is_some_and(hex)
                && construction_family_matches(
                    &value["constructions"],
                    locallore_eval::memory_comparison_v4::current_arm_descriptors(),
                    locallore_eval::memory_comparison_v4::arm_descriptors(),
                    usage,
                )
        }
        None => false,
    };
    version_valid
        && value["kind"] == "selected_prepared"
        && value["binding"].as_str().is_some_and(hex)
        && matches!(
            value["lane"].as_str(),
            Some("scripted_selected_case" | "native_selected_case")
        )
        && keys(&value["selection"], &["turn", "clicked_arm", "index"])
        && value["selection"]["turn"].as_str().is_some_and(word)
        && matches!(
            value["selection"]["clicked_arm"].as_str(),
            Some("left" | "right")
        )
        && value["selection"]["index"].as_u64().is_some_and(|n| n < 24)
        && value["arms"].as_array().is_some_and(|arms| {
            arms.len() == 2
                && arms.iter().enumerate().all(|(n, a)| {
                    keys(
                        a,
                        &[
                            "arm",
                            "scope",
                            "before_head",
                            "prefix_sha256",
                            "input_semantic_sha256",
                        ],
                    ) && a["arm"] == ["left", "right"][n]
                        && keys(&a["scope"], &["story", "branch"])
                        && a["scope"]["story"].as_str().is_some_and(word)
                        && a["scope"]["branch"].as_str().is_some_and(word)
                        && a["before_head"].as_u64().is_some_and(|head| head <= SAFE)
                        && a["prefix_sha256"].as_str().is_some_and(hex)
                        && a["input_semantic_sha256"].as_str().is_some_and(hex)
                })
        })
}
pub(super) fn failure(error: &str) -> String {
    match error {
        "InvalidEvaluationInput"
        | "EvaluationBusy"
        | "EvaluationModelBusy"
        | "EvaluationIo"
        | "EvaluationInternal"
        | "EvaluationBudget"
        | "EvaluationRunLimit"
        | "EvaluationSourceMismatch"
        | "EvaluationIntegrity"
        | "EvaluationTokenLimit"
        | "UnknownEvaluationRun"
        | "Closed"
        | "Forbidden"
        | "PickerUnavailable"
        | "Cancelled"
        | "Cleanup"
        | "NativeUnavailable" => error,
        "Busy" | "ModelLoaded" | "RuntimeBusy" => "EvaluationModelBusy",
        "RunBusy" => "EvaluationBusy",
        "Interrupted" | "RuntimeCancelled" => "Cancelled",
        "RuntimeTimeout" | "Watchdog" | "PreparationDeadline" | "InspectionTooLarge" => {
            "EvaluationBudget"
        }
        "InspectionForbidden" => "Forbidden",
        "InspectionUnknownObserver" | "InspectionInvalidRequest" | "UnknownRow" => {
            "InvalidEvaluationInput"
        }
        "NativeFeatureUnavailable"
        | "SelectedNativeUnavailable"
        | "UnsupportedPlatform"
        | "RuntimeWorkerUnavailable"
        | "RuntimeModelInvalid" => "NativeUnavailable",
        "RuntimeCleanup" => "Cleanup",
        "SourceMismatch" | "SnapshotMismatch" | "CheckpointMismatch" => "EvaluationSourceMismatch",
        value if value.ends_with("Budget") || value == "TooLarge" || value.ends_with("Limit") => {
            "EvaluationBudget"
        }
        value
            if value.starts_with("Checkpoint")
                || value.starts_with("Reference")
                || value.starts_with("Ledger")
                || value.starts_with("Setup")
                || value.starts_with("Capture")
                || value.starts_with("Recording")
                || value.starts_with("Raw")
                || value.starts_with("Selected")
                || value == "Replay"
                || value == "Lookup"
                || value == "Reparse"
                || value == "Encoding"
                || value == "Scope"
                || value.starts_with("Inspection") =>
        {
            "EvaluationIntegrity"
        }
        _ => "EvaluationIo",
    }
    .into()
}
fn check(cancel: &Cancellation, lease: &WindowLease, epoch: u64) -> Result<()> {
    if !lease.valid(epoch) {
        Err("Closed".into())
    } else if cancel.is_cancelled() {
        Err("Cancelled".into())
    } else {
        Ok(())
    }
}
fn actor_raw(request: &EvidenceRequest) -> bool {
    match request {
        EvidenceRequest::Query { .. } => false,
        EvidenceRequest::Receipt { observer }
        | EvidenceRequest::Capture { observer }
        | EvidenceRequest::Outputs { observer } => !matches!(observer, Observer::Omniscient),
    }
}
fn read_valid(input: &SelectedReadInput) -> bool {
    id(&input.client_id) && id(&input.run_token) && hex(&input.binding)
}

enum Work {
    Prepare {
        source: Box<super::comparison::SelectedSource>,
        input: SelectedPrepareInput,
        consent: Consent,
    },
    Start {
        prepared: Box<Prepared>,
        run_id: String,
    },
    Open {
        run_id: String,
        consent: Consent,
        discard: Vec<Discard>,
    },
    Resume {
        source: Box<super::comparison::SelectedSource>,
        cap: Box<ReadCap>,
        run_id: String,
        consent: Consent,
    },
    Read {
        cap: Box<ReadCap>,
        identity: SelectedReadInput,
        kind: ReadKind,
        idle_phase: &'static str,
    },
}
enum ReadKind {
    Summary,
    Evidence(Arm, EvidenceRequest),
    Diagnostics(Observer),
}
enum Publication {
    Prepared(Box<Prepared>, String),
    Opened(Box<ReadCap>, String, Value, Index),
    Executed {
        run_id: String,
        metadata: Value,
        completed: bool,
        reopened: Option<(Box<ReadCap>, String, Value)>,
    },
    Read(Box<ReadCap>, Result<Value>, &'static str),
}
struct Outcome {
    result: Result<Publication>,
    retained: Option<(models::EvaluationReservation, Runtime)>,
    uncertain: bool,
    cause: Option<String>,
}
impl Outcome {
    fn plain(result: Result<Publication>) -> Self {
        Self {
            result,
            retained: None,
            uncertain: false,
            cause: None,
        }
    }
    fn native(error: producer::SelectedNativeFailure<models::EvaluationReservation>) -> Self {
        let code = failure(error.code());
        let cause = error.cause().map(failure);
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
    pub(super) fn selected_root(&self) -> PathBuf {
        self.root.with_file_name("selected-evaluations")
    }
    fn selected_lock(&self) -> Result<std::sync::MutexGuard<'_, SelectedState>> {
        self.selected
            .lock()
            .map_err(|_| "EvaluationInternal".into())
    }
    fn selected_expire(&self, lease: &WindowLease, epoch: u64) -> Result<()> {
        let mut discard = vec![];
        let result = lease.dispatch(epoch, || {
            let mut selected = self.selected_lock()?;
            for r in selected
                .records
                .values_mut()
                .filter(|r| r.owns(lease, epoch) && !r.running && r.touched.elapsed() > TTL)
            {
                r.revoke(&mut discard);
            }
            Ok(())
        });
        dispose(discard);
        result
    }
    pub fn selected_status(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        client: &str,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !id(client) {
            return Err("InvalidEvaluationInput".into());
        }
        self.selected_expire(lease, epoch)?;
        lease.dispatch(epoch, || {
            let mut state = self.selected_lock()?;
            let r = state
                .records
                .get_mut(client)
                .filter(|r| r.owns(lease, epoch))
                .ok_or("UnknownEvaluationRun")?;
            r.touched = Instant::now();
            r.status()
        })
    }
    pub fn selected_close(&self, lease: &WindowLease, epoch: u64, client: &str) -> Result<Value> {
        if !id(client) {
            return Err("InvalidEvaluationInput".into());
        }
        let mut discard = vec![];
        let result = lease.dispatch(epoch, || {
            let mut state = self.selected_lock()?;
            let r = state
                .records
                .get_mut(client)
                .filter(|r| r.owns(lease, epoch))
                .ok_or("UnknownEvaluationRun")?;
            r.revoke(&mut discard);
            r.status()
        });
        dispose(discard);
        result
    }
    pub fn selected_cancel(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        client: &str,
        operation: u64,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !id(client) || operation == 0 || operation > SAFE {
            return Err("InvalidEvaluationInput".into());
        }
        lease.dispatch(epoch, || {
            let mut state = self.selected_lock()?;
            let r = state
                .records
                .get_mut(client)
                .filter(|r| r.owns(lease, epoch) && r.operation == Some(operation))
                .ok_or("UnknownEvaluationRun")?;
            if r.running {
                r.cancel.cancel();
                r.phase = "cancelling";
            }
            r.status()
        })
    }
    pub(super) fn selected_retire(&self, epoch: u64) {
        if let Ok(mut state) = self.selected.try_lock() {
            for r in state.records.values_mut().filter(|r| r.epoch == epoch) {
                r.cancel.cancel();
                r.revoked = true;
                r.phase = "closed";
            }
        }
    }
    pub(super) fn selected_drain(&self, epoch: u64) {
        // Parent has already joined this epoch's worker. Never remove Job's
        // actual runtime payload here; presentation objects drop outside gates.
        let removed = {
            let mut state = self.selected.lock().unwrap_or_else(|p| p.into_inner());
            let ids: Vec<_> = state
                .records
                .iter()
                .filter(|(_, r)| r.epoch == epoch)
                .map(|(id, _)| id.clone())
                .collect();
            ids.into_iter()
                .filter_map(|id| state.records.remove(&id))
                .collect::<Vec<_>>()
        };
        drop(removed);
    }
    fn selected_index(&self, run: &str) -> Result<Index> {
        if !id(run) {
            return Err("InvalidEvaluationInput".into());
        }
        let path = self.selected_root().join(run).join("native.json");
        let _pins = pin(&path)?;
        let info = fs::metadata(&path).map_err(|_| "EvaluationIntegrity")?;
        if !info.is_file() || info.len() > INDEX_CAP as u64 {
            return Err("EvaluationIntegrity".into());
        }
        let file = File::open(&path).map_err(|_| "EvaluationIo")?;
        let mut bytes = Vec::new();
        file.take(INDEX_CAP as u64 + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| "EvaluationIo")?;
        if bytes.len() > INDEX_CAP {
            return Err("EvaluationBudget".into());
        }
        let index: Index = serde_json::from_slice(&bytes).map_err(|_| "EvaluationIntegrity")?;
        if versioned::prepared_protocol(&index.prepared)
            .is_none_or(|protocol| index.version != protocol.selected_version())
            || index.run_id != run
            || !id(&index.client_id)
            || index.created > SAFE
            || !hex(&index.source_binding)
            // Historical readability supplies no execution grant. Resume below
            // still requires an exact match to newly prepared current metadata.
            || !prepared_valid(&index.prepared, PreparedUse::Recorded)
            || (versioned::prepared_protocol(&index.prepared) == Some(versioned::Protocol::V3)
                && index.prepared["source_binding"].as_str() != Some(index.source_binding.as_str()))
            || index.prepared["lane"].as_str()
                != Some(SelectedInputLane::parse(&index.lane)?.stored())
        {
            return Err("EvaluationIntegrity".into());
        }
        Ok(index)
    }
    fn selected_work_path(&self, run: &str) -> Result<(PathBuf, Vec<File>)> {
        let index = self.selected_index(run)?;
        let path = self.selected_root().join(&index.run_id).join("work");
        if !path.is_dir() {
            return Err("EvaluationIntegrity".into());
        }
        let pins = pin(&path)?;
        Ok((path, pins))
    }
    fn selected_make_index(&self, client: &str, run: &str, prepared: &Prepared) -> Result<Index> {
        if !prepared_valid(&prepared.metadata, PreparedUse::Fresh)
            || versioned::prepared_protocol(&prepared.metadata) != Some(prepared.plan.protocol())
            || (prepared.plan.protocol() == versioned::Protocol::V3
                && prepared.metadata["source_binding"].as_str()
                    != Some(prepared.source_binding.as_str()))
        {
            return Err("EvaluationIntegrity".into());
        }
        let root = self.selected_root();
        let _parent = pin(root.parent().ok_or("EvaluationIo")?)?;
        fs::create_dir_all(&root).map_err(|_| "EvaluationIo")?;
        let _pins = pin(&root)?;
        let entries: Vec<_> = fs::read_dir(&root)
            .map_err(|_| "EvaluationIo")?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(|_| "EvaluationIo")?;
        if entries.len() >= 32 {
            return Err("EvaluationRunLimit".into());
        }
        self.budget(None)?;
        let path = root.join(run);
        fs::create_dir(&path).map_err(|_| "EvaluationIo")?;
        let _run = pin(&path)?;
        let lane = if prepared.metadata["lane"] == "native_selected_case" {
            SelectedInputLane::ApprovedNative
        } else {
            SelectedInputLane::ScriptedBaseline
        };
        let index = Index {
            version: prepared.plan.protocol().selected_version(),
            run_id: run.into(),
            created: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map_err(|_| "EvaluationIo")?
                .as_millis()
                .try_into()
                .map_err(|_| "EvaluationBudget")?,
            client_id: client.into(),
            lane: lane.input().into(),
            source_binding: prepared.source_binding.clone(),
            prepared: prepared.metadata.clone(),
        };
        let bytes = serde_json::to_vec(&index).map_err(|_| "EvaluationInternal")?;
        if bytes.len() > INDEX_CAP {
            return Err("EvaluationBudget".into());
        }
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path.join("native.json"))
            .map_err(|_| "EvaluationIo")?;
        file.write_all(&bytes).map_err(|_| "EvaluationIo")?;
        file.sync_all().map_err(|_| "EvaluationIo")?;
        Ok(index)
    }
    pub fn selected_catalog(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        (||{
        let _registration=self.registration.lock().map_err(|_|"EvaluationInternal")?;let root=self.selected_root();let mut runs=vec![];
        if root.exists(){let _pins=pin(&root)?;for entry in fs::read_dir(&root).map_err(|_|"EvaluationIo")?{if runs.len()>=32{return Err("EvaluationRunLimit".into())}let entry=entry.map_err(|_|"EvaluationIo")?;let name=entry.file_name().into_string().map_err(|_|"EvaluationIntegrity")?;let index=self.selected_index(&name)?;runs.push(json!({"run_id":name,"created":index.created,"lane":index.lane,"selection":index.prepared["selection"]}));}}
        if !lease.valid(epoch){return Err("Closed".into())} bounded(json!({"version":1,"kind":"selected_catalog","runs":runs}),64*1024)
        })().map_err(|error:String|failure(&error))
    }
    fn selected_new_record(
        state: &mut SelectedState,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        client: &str,
        operation: u64,
        cancel: &Cancellation,
    ) -> Result<()> {
        if state.records.contains_key(client) {
            return Err("EvaluationBusy".into());
        }
        if state.records.len() >= CLIENTS {
            let oldest = state
                .records
                .iter()
                .filter(|(_, r)| r.revoked && !r.running && r.plan.is_none() && r.cap.is_none())
                .min_by_key(|(_, r)| r.touched)
                .map(|(id, _)| id.clone())
                .ok_or("EvaluationTokenLimit")?;
            state.records.remove(&oldest);
        }
        state.records.insert(
            client.into(),
            Record {
                lease: Arc::downgrade(lease),
                models: Arc::downgrade(models),
                epoch,
                client: client.into(),
                operation: Some(operation),
                phase: "preparing",
                running: true,
                revoked: false,
                lane: None,
                plan_token: None,
                run_id: None,
                run_token: None,
                binding: None,
                metadata: None,
                plan: None,
                cap: None,
                consumed: None,
                error: None,
                cause: None,
                cleanup_required: false,
                cancel: cancel.clone(),
                touched: Instant::now(),
            },
        );
        Ok(())
    }
    pub fn selected_prepare(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        input: SelectedPrepareInput,
        consent: impl FnOnce(&Value) -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !id(&input.client_id)
            || !id(&input.reader_client_id)
            || !id(&input.run_token)
            || !hex(&input.binding)
            || !word(&input.turn_id)
        {
            return Err("InvalidEvaluationInput".into());
        }
        self.selected_expire(lease, epoch)?;
        let client = input.client_id.clone();
        let owned_lease = lease.clone();
        let owned_models = models.clone();
        self.selected_launch(
            lease,
            models,
            epoch,
            client.clone(),
            move |state, operation, cancel| {
                Self::selected_new_record(
                    state,
                    &owned_lease,
                    &owned_models,
                    epoch,
                    &client,
                    operation,
                    cancel,
                )?;
                let source = match self.comparison_take_source_in_gate(
                    lease,
                    epoch,
                    &input.reader_client_id,
                    &input.run_token,
                    &input.binding,
                ) {
                    Ok(source) => source,
                    Err(error) => {
                        state.records.remove(&client);
                        return Err(error);
                    }
                };
                state
                    .records
                    .get_mut(&client)
                    .ok_or("EvaluationInternal")?
                    .lane = Some(input.lane);
                Ok(Work::Prepare {
                    source: Box::new(source),
                    input,
                    consent: Box::new(consent),
                })
            },
            None,
        )
    }
    pub fn selected_start(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        client: &str,
        token: &str,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !id(client) || !id(token) {
            return Err("InvalidEvaluationInput".into());
        }
        self.selected_expire(lease, epoch)?;
        let duplicate = lease.dispatch(epoch, || {
            let state = self.selected_lock()?;
            let r = state
                .records
                .get(client)
                .filter(|r| {
                    r.owns(lease, epoch)
                        && Weak::ptr_eq(&r.models, &Arc::downgrade(models))
                        && !r.revoked
                })
                .ok_or("UnknownEvaluationRun")?;
            Ok(r.consumed
                .as_ref()
                .filter(|(used, _)| used == token)
                .map(|(_, value)| value.clone()))
        })?;
        if let Some(value) = duplicate {
            return Ok(value);
        }
        #[cfg(test)]
        if let Some((entered, release)) =
            SELECTED_START_PRECHECK_PAUSE.with(|hook| hook.borrow_mut().take())
        {
            entered.send(()).map_err(|_| "EvaluationInternal")?;
            release
                .recv_timeout(Duration::from_secs(60))
                .map_err(|_| "EvaluationInternal")?;
        }
        let client = client.to_owned();
        let token = token.to_owned();
        let lookup_client = client.clone();
        let lookup_token = token.clone();
        let new_run = uuid()?;
        let result = self.selected_launch(
            lease,
            models,
            epoch,
            client.clone(),
            move |state, operation, cancel| {
                let r = state
                    .records
                    .get_mut(&client)
                    .filter(|r| {
                        r.owns(lease, epoch)
                            && Weak::ptr_eq(&r.models, &Arc::downgrade(models))
                            && !r.revoked
                            && r.plan_token.as_deref() == Some(&token)
                    })
                    .ok_or("UnknownEvaluationRun")?;
                let prepared = r.plan.take().ok_or("UnknownEvaluationRun")?;
                r.running = true;
                r.phase = "running";
                r.operation = Some(operation);
                r.cancel = cancel.clone();
                r.plan_token = None;
                r.run_id = Some(new_run.clone());
                r.error = None;
                r.consumed = Some((token, r.status()?));
                Ok(Work::Start {
                    prepared,
                    run_id: new_run,
                })
            },
            None,
        );
        // Another exact caller can consume and finish between the optimistic
        // cache read and registration. Recover only the actual bound receipt;
        // never retry execution, override an IO failure, or relax lease/model
        // identity. This also returns the original pending identity if busy.
        if matches!(&result, Err(error) if matches!(error.as_str(), "EvaluationBusy" | "UnknownEvaluationRun"))
        {
            let cached = lease.dispatch(epoch, || {
                let state = self.selected_lock()?;
                Ok(state
                    .records
                    .get(&lookup_client)
                    .filter(|r| {
                        r.owns(lease, epoch)
                            && Weak::ptr_eq(&r.models, &Arc::downgrade(models))
                            && !r.revoked
                    })
                    .and_then(|r| r.consumed.as_ref())
                    .filter(|(used, _)| used == &lookup_token)
                    .map(|(_, value)| value.clone()))
            });
            if let Ok(Some(value)) = cached {
                return Ok(value);
            }
        }
        result
    }
    pub fn selected_open(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        (client, run): (&str, &str),
        consent: impl FnOnce(&Value) -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !id(client) || !id(run) {
            return Err("InvalidEvaluationInput".into());
        }
        self.selected_expire(lease, epoch)?;
        let client = client.to_owned();
        let run = run.to_owned();
        let owner = lease.clone();
        let model = models.clone();
        self.selected_launch(
            lease,
            models,
            epoch,
            client.clone(),
            move |state, operation, cancel| {
                if !state.records.contains_key(&client) {
                    Self::selected_new_record(
                        state, &owner, &model, epoch, &client, operation, cancel,
                    )?;
                }
                let r = state
                    .records
                    .get_mut(&client)
                    .filter(|r| {
                        r.owns(lease, epoch)
                            && Weak::ptr_eq(&r.models, &Arc::downgrade(models))
                            && !r.revoked
                            && (!r.running || r.operation == Some(operation))
                    })
                    .ok_or("UnknownEvaluationRun")?;
                r.running = true;
                r.phase = "preparing";
                r.operation = Some(operation);
                r.cancel = cancel.clone();
                let mut discard = Vec::new();
                if let Some(cap) = r.cap.take() {
                    discard.push(Discard::Cap(cap));
                }
                if let Some(plan) = r.plan.take() {
                    discard.push(Discard::Plan(plan));
                }
                r.plan_token = None;
                r.metadata = None;
                r.lane = None;
                r.error = None;
                r.cause = None;
                r.run_token = None;
                r.run_id = None;
                r.binding = None;
                Ok(Work::Open {
                    run_id: run,
                    consent: Box::new(consent),
                    discard,
                })
            },
            None,
        )
    }
    pub fn selected_resume(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        input: SelectedResumeInput,
        consent: impl FnOnce(&Value) -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !id(&input.client_id)
            || !id(&input.run_token)
            || !id(&input.reader_client_id)
            || !id(&input.source_token)
            || !hex(&input.source_binding)
        {
            return Err("InvalidEvaluationInput".into());
        }
        self.selected_expire(lease, epoch)?;
        let client = input.client_id.clone();
        self.selected_launch(
            lease,
            models,
            epoch,
            client.clone(),
            move |state, operation, cancel| {
                let r = state
                    .records
                    .get_mut(&client)
                    .filter(|r| {
                        r.owns(lease, epoch)
                            && !r.revoked
                            && !r.running
                            && r.run_token.as_deref() == Some(input.run_token.as_str())
                            && Weak::ptr_eq(&r.models, &Arc::downgrade(models))
                    })
                    .ok_or("UnknownEvaluationRun")?;
                let source = self.comparison_take_source_in_gate(
                    lease,
                    epoch,
                    &input.reader_client_id,
                    &input.source_token,
                    &input.source_binding,
                )?;
                let cap = r.cap.take().ok_or("UnknownEvaluationRun")?;
                let run_id = r.run_id.clone().ok_or("UnknownEvaluationRun")?;
                r.running = true;
                r.phase = "preparing";
                r.operation = Some(operation);
                r.cancel = cancel.clone();
                r.run_token = None;
                r.binding = None;
                Ok(Work::Resume {
                    source: Box::new(source),
                    cap,
                    run_id,
                    consent: Box::new(consent),
                })
            },
            None,
        )
    }
    fn selected_read(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        identity: SelectedReadInput,
        kind: ReadKind,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !read_valid(&identity) {
            return Err("InvalidEvaluationInput".into());
        }
        self.selected_expire(lease, epoch)?;
        let client = identity.client_id.clone();
        let (send, receive) = mpsc::sync_channel(1);
        self.selected_launch(
            lease,
            models,
            epoch,
            client.clone(),
            move |state, operation, cancel| {
                let r = state
                    .records
                    .get_mut(&client)
                    .filter(|r| {
                        r.owns(lease, epoch)
                            && !r.revoked
                            && !r.running
                            && r.run_token.as_deref() == Some(&identity.run_token)
                            && r.binding.as_deref() == Some(&identity.binding)
                            && Weak::ptr_eq(&r.models, &Arc::downgrade(models))
                    })
                    .ok_or("UnknownEvaluationRun")?;
                let cap = r.cap.take().ok_or("UnknownEvaluationRun")?;
                let idle_phase = r.phase;
                r.running = true;
                r.phase = "running";
                r.operation = Some(operation);
                r.cancel = cancel.clone();
                r.error = None;
                r.cause = None;
                Ok(Work::Read {
                    cap,
                    identity,
                    kind,
                    idle_phase,
                })
            },
            Some(send),
        )?;
        receive
            .recv_timeout(Duration::from_secs(30))
            .map_err(|_| "EvaluationIo".to_owned())?
    }
    pub fn selected_summary(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        input: SelectedReadInput,
    ) -> Result<Value> {
        self.selected_read(lease, models, epoch, granted, input, ReadKind::Summary)
    }
    pub fn selected_evidence(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        input: SelectedEvidenceInput,
    ) -> Result<Value> {
        if actor_raw(&input.request) {
            return Err("Forbidden".into());
        }
        self.selected_read(
            lease,
            models,
            epoch,
            granted,
            input.identity,
            ReadKind::Evidence(input.arm, input.request),
        )
    }
    pub fn selected_diagnostics(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        input: SelectedReadInput,
        observer: Observer,
    ) -> Result<Value> {
        if !matches!(observer, Observer::Omniscient) {
            return Err("Forbidden".into());
        }
        self.selected_read(
            lease,
            models,
            epoch,
            granted,
            input,
            ReadKind::Diagnostics(observer),
        )
    }
}

impl EvaluationManager {
    fn selected_launch<P>(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        client: String,
        prepare: P,
        reply: Option<mpsc::SyncSender<Result<Value>>>,
    ) -> Result<Value>
    where
        P: FnOnce(&mut SelectedState, u64, &Cancellation) -> Result<Work>,
    {
        let mut prepare = Some(prepare);
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
            let (operation, cancel, payload, initial) = lease.dispatch(epoch, || {
                let mut parent = self.state()?;
                if parent.job.is_some() {
                    return Err("EvaluationBusy".into());
                }
                let operation = parent
                    .next
                    .checked_add(1)
                    .filter(|n| *n <= SAFE)
                    .ok_or("EvaluationBudget")?;
                let cancel = Cancellation::default();
                let mut state = self.selected_lock()?;
                let payload =
                    prepare.take().ok_or("EvaluationInternal")?(&mut state, operation, &cancel)?;
                parent.next = operation;
                parent.job = Some(Job {
                    kind: JobKind::Selected,
                    worker_active: true,
                    epoch,
                    id: operation,
                    run: client.clone(),
                    cancel: cancel.clone(),
                    selected: Some(SelectedOwnership {
                        models: models.clone(),
                        witness: None,
                        retained: None,
                        cleanup_running: false,
                    }),
                });
                let initial = state
                    .records
                    .get(&client)
                    .ok_or("EvaluationInternal")?
                    .status()?;
                Ok((operation, cancel, payload, initial))
            })?;
            self.register_cancellation(lease, epoch, operation, &cancel);
            let payload = Arc::new(Mutex::new(Some(payload)));
            let held = payload.clone();
            let manager = self.clone();
            let owner = lease.clone();
            let model = models.clone();
            let worker_client = client.clone();
            let worker_cancel = cancel.clone();
            let (send, registered) = mpsc::channel();
            let worker = move || {
                if registered.recv().is_err() {
                    return;
                }
                let payload = held.lock().unwrap_or_else(|p| p.into_inner()).take();
                // The fixed injected panic is ONLY before execution. Do not
                // wrap actual native execution and claim universal panic cleanup.
                #[cfg(test)]
                let injected = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    if manager
                        .panic_worker
                        .swap(false, std::sync::atomic::Ordering::SeqCst)
                    {
                        panic!("fixed pre-execution selected worker fault")
                    }
                }))
                .is_err();
                #[cfg(not(test))]
                let injected = false;
                let outcome = if injected {
                    drop(payload);
                    Outcome::plain(Err("EvaluationInternal".into()))
                } else {
                    match payload {
                        Some(payload) => manager.selected_work(
                            &owner,
                            &model,
                            (epoch, operation),
                            &worker_client,
                            &worker_cancel,
                            payload,
                        ),
                        None => Outcome::plain(Err("EvaluationInternal".into())),
                    }
                };
                let result =
                    manager.selected_finish(&owner, epoch, &worker_client, operation, outcome);
                if let Some(reply) = reply {
                    let _ = reply.send(result);
                }
            };
            #[cfg(test)]
            let failed = self
                .fail_spawn
                .swap(false, std::sync::atomic::Ordering::SeqCst);
            #[cfg(not(test))]
            let failed = false;
            let spawned = if failed {
                Err(std::io::Error::other("fixed selected spawn refusal"))
            } else {
                std::thread::Builder::new()
                    .name("locallore-evaluation".into())
                    .spawn(worker)
            };
            match spawned {
                Ok(handle) => {
                    *self.worker.lock().unwrap_or_else(|p| p.into_inner()) = Some((epoch, handle));
                    let _ = send.send(());
                }
                Err(_) => {
                    drop(registration);
                    let discarded = payload.lock().unwrap_or_else(|p| p.into_inner()).take();
                    drop(discarded);
                    let _ = self.selected_finish(
                        lease,
                        epoch,
                        &client,
                        operation,
                        Outcome::plain(Err("EvaluationInternal".into())),
                    );
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
    fn selected_reserve(
        &self,
        models: &Arc<ModelManager>,
        epoch: u64,
        operation: u64,
    ) -> Result<models::EvaluationReservation> {
        self.reserve_owned(models, JobKind::Selected, epoch, operation)
    }
    pub(super) fn reserve_owned(
        &self,
        models: &Arc<ModelManager>,
        expected_kind: JobKind,
        epoch: u64,
        operation: u64,
    ) -> Result<models::EvaluationReservation> {
        // The shared owned-failure boundary accepts its own fixed runtime
        // categories, not desktop-only strings which would become unknown.
        let reservation = models.reserve_evaluation().map_err(|error| {
            match error.as_str() {
                "Busy" | "ModelLoaded" => "RuntimeBusy",
                "TooLarge" => "TooLarge",
                _ => "RuntimeRuntime",
            }
            .to_owned()
        })?;
        let witness = reservation.cleanup_witness();
        let installed: Result<()> = (|| {
            let mut parent = self.state().map_err(|_| "RuntimeRuntime")?;
            let job = parent
                .job
                .as_mut()
                .filter(|job| {
                    job.kind == expected_kind && job.epoch == epoch && job.id == operation
                })
                .ok_or("Interrupted")?;
            let ownership = job.selected.as_mut().ok_or("RuntimeRuntime")?;
            if !Arc::ptr_eq(&ownership.models, models) {
                return Err("RuntimeBusy".into());
            }
            ownership.witness = Some(witness);
            Ok(())
        })();
        match installed {
            Ok(()) => Ok(reservation),
            Err(error) => {
                drop(reservation);
                Err(error)
            }
        }
    }
    fn selected_work(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        (epoch, operation): (u64, u64),
        client: &str,
        cancel: &Cancellation,
        work: Work,
    ) -> Outcome {
        if let Err(error) = check(cancel, lease, epoch) {
            drop(work);
            return Outcome::plain(Err(error));
        }
        match work {
            Work::Prepare {
                source,
                input,
                consent,
            } => Outcome::plain((|| {
                let protocol = versioned::Protocol::from_source(source.protocol_version())
                    .ok_or("NativeUnavailable")?;
                let (origin, source_binding) = (*source).into_origin();
                let plan = versioned::Plan::prepare(
                    protocol,
                    &origin,
                    &source_binding,
                    &source_reader::RowId {
                        turn: input.turn_id,
                        arm: input.arm,
                    },
                    producer::SelectedIntent {
                        client_id: client.into(),
                        lane: input.lane.shared(),
                    },
                    cancel,
                )
                .map_err(|error| failure(&error))?;
                let metadata = plan.metadata().map_err(|error| failure(&error))?;
                check(cancel, lease, epoch)?;
                if !consent(&metadata).map_err(|error| failure(&error))? {
                    return Err("Cancelled".into());
                }
                check(cancel, lease, epoch)?;
                Ok(Publication::Prepared(
                    Box::new(Prepared {
                        plan,
                        metadata,
                        source_binding,
                        _grant: ExecutionGrant,
                    }),
                    uuid()?,
                ))
            })()),
            Work::Open {
                run_id,
                consent,
                discard,
            } => Outcome::plain((|| {
                dispose(discard);
                let index = self.selected_index(&run_id)?;
                let protocol =
                    versioned::prepared_protocol(&index.prepared).ok_or("EvaluationIntegrity")?;
                let (path, _pins) = self.selected_work_path(&run_id)?;
                self.budget(Some(path.parent().ok_or("EvaluationIo")?))?;
                let opened =
                    versioned::Opened::open(protocol, &path).map_err(|error| failure(&error))?;
                let summary = opened.summary().map_err(|error| failure(&error))?;
                if summary["version"] != index.prepared["version"]
                    || summary.get("source_protocol_version")
                        != index.prepared.get("source_protocol_version")
                    || summary.get("constructions") != index.prepared.get("constructions")
                    || summary["selection"] != index.prepared["selection"]
                    || summary["lane"] != SelectedInputLane::parse(&index.lane)?.stored()
                    || summary["arms"].as_array().is_none_or(|arms| {
                        arms.len() != 2
                            || arms.iter().enumerate().any(|(n, arm)| {
                                arm["scope"] != index.prepared["arms"][n]["scope"]
                                    || arm["before_head"]
                                        != index.prepared["arms"][n]["before_head"]
                            })
                    })
                {
                    return Err("EvaluationIntegrity".into());
                }
                check(cancel, lease, epoch)?;
                if !consent(&summary).map_err(|error| failure(&error))? {
                    return Err("Cancelled".into());
                }
                check(cancel, lease, epoch)?;
                Ok(Publication::Opened(
                    Box::new(ReadCap {
                        opened,
                        _grant: ReadGrant,
                    }),
                    uuid()?,
                    summary,
                    index,
                ))
            })()),
            Work::Read {
                cap,
                identity,
                kind,
                idle_phase,
            } => {
                let read = (|| {
                    let (key, body) = match kind {
                        ReadKind::Summary => ("summary", cap.opened.summary()),
                        ReadKind::Evidence(arm, request) => (
                            "evidence",
                            cap.opened.evidence(&identity.binding, arm, request),
                        ),
                        ReadKind::Diagnostics(observer) => (
                            "diagnostics",
                            cap.opened.diagnostics(&identity.binding, observer),
                        ),
                    };
                    let body = body.map_err(|error| failure(&error))?;
                    check(cancel, lease, epoch)?;
                    let kind = match key {
                        "summary" => "selected_summary",
                        "evidence" => "selected_evidence",
                        _ => "selected_diagnostics_result",
                    };
                    let mut value = json!({"version":1,"kind":kind,"run_token":identity.run_token});
                    value[key] = body;
                    bounded(value, 256 * 1024 + 4096)
                })();
                Outcome::plain(Ok(Publication::Read(cap, read, idle_phase)))
            }
            Work::Start { prepared, run_id } => {
                let setup = (|| {
                    check(cancel, lease, epoch)?;
                    let index = self.selected_make_index(client, &run_id, &prepared)?;
                    let path = self.selected_root().join(&run_id).join("work");
                    Ok((index, path))
                })();
                let (index, path) = match setup {
                    Ok(value) => value,
                    Err(error) => return Outcome::plain(Err(error)),
                };
                let metadata = prepared.metadata.clone();
                let protocol = prepared.plan.protocol();
                let lane = match SelectedInputLane::parse(&index.lane) {
                    Ok(lane) => lane,
                    Err(error) => return Outcome::plain(Err(error)),
                };
                let result = match lane {
                    SelectedInputLane::ScriptedBaseline => match prepared.plan.run(&path, cancel) {
                        Ok(_) => Ok(()),
                        Err(error) => return Outcome::plain(Err(failure(&error))),
                    },
                    SelectedInputLane::ApprovedNative => {
                        match prepared.plan.run_native(&path, cancel, || {
                            self.selected_reserve(models, epoch, operation)
                        }) {
                            Ok(_) => Ok(()),
                            Err(versioned::NativeDispatchFailure::Unavailable) => {
                                return Outcome::plain(Err("NativeUnavailable".into()));
                            }
                            Err(versioned::NativeDispatchFailure::Owned(error)) => {
                                return Outcome::native(error);
                            }
                        }
                    }
                };
                Outcome::plain(result.and_then(|()| {
                    self.budget(Some(path.parent().ok_or("EvaluationIo")?))?;
                    let cap = versioned::Opened::open(protocol, &path)
                        .map_err(|error| failure(&error))?;
                    let summary = cap.summary().map_err(|error| failure(&error))?;
                    let completed = summary["arms"]
                        .as_array()
                        .is_some_and(|arms| arms.iter().all(|arm| arm["available"] == true));
                    drop(cap);
                    Ok(Publication::Executed {
                        run_id,
                        metadata,
                        completed,
                        reopened: None,
                    })
                }))
            }
            Work::Resume {
                source,
                cap,
                run_id,
                consent,
            } => {
                let ReadCap { opened, _grant } = *cap;
                drop(opened);
                let source_version = source.protocol_version();
                let (origin, source_binding) = (*source).into_origin();
                let setup = (|| {
                    let index = self.selected_index(&run_id)?;
                    let protocol = versioned::prepared_protocol(&index.prepared)
                        .ok_or("EvaluationIntegrity")?;
                    let (path, pins) = self.selected_work_path(&run_id)?;
                    if index.source_binding != source_binding
                        || source_version != protocol.source_version()
                    {
                        return Err("EvaluationSourceMismatch".into());
                    }
                    let lane = SelectedInputLane::parse(&index.lane)?;
                    let selection = &index.prepared["selection"];
                    let arm = if selection["clicked_arm"] == "left" {
                        Arm::Left
                    } else {
                        Arm::Right
                    };
                    let plan = versioned::Plan::prepare(
                        protocol,
                        &origin,
                        &source_binding,
                        &source_reader::RowId {
                            turn: selection["turn"]
                                .as_str()
                                .ok_or("EvaluationIntegrity")?
                                .into(),
                            arm,
                        },
                        producer::SelectedIntent {
                            client_id: index.client_id.clone(),
                            lane: lane.shared(),
                        },
                        cancel,
                    )
                    .map_err(|error| failure(&error))?;
                    let fresh = plan.metadata().map_err(|error| failure(&error))?;
                    if fresh != index.prepared {
                        return Err("EvaluationSourceMismatch".into());
                    }
                    drop(plan);
                    check(cancel, lease, epoch)?;
                    if !consent(&fresh).map_err(|error| failure(&error))? {
                        return Err("Cancelled".into());
                    }
                    check(cancel, lease, epoch)?;
                    Ok((index, path, pins, lane, protocol, ExecutionGrant))
                })();
                let (index, path, _pins, lane, protocol, _execution) = match setup {
                    Ok(value) => value,
                    Err(error) => return Outcome::plain(Err(error)),
                };
                let binding = match index.prepared["binding"].as_str() {
                    Some(binding) => binding,
                    None => return Outcome::plain(Err("EvaluationIntegrity".into())),
                };
                match lane {
                    SelectedInputLane::ScriptedBaseline => {
                        if let Err(error) =
                            versioned::Plan::resume(protocol, &path, &origin, binding, cancel)
                        {
                            return Outcome::plain(Err(failure(&error)));
                        }
                    }
                    SelectedInputLane::ApprovedNative => {
                        if let Err(error) = versioned::Plan::resume_native(
                            protocol,
                            &path,
                            &origin,
                            binding,
                            cancel,
                            || self.selected_reserve(models, epoch, operation),
                        ) {
                            return match error {
                                versioned::NativeDispatchFailure::Unavailable => {
                                    Outcome::plain(Err("NativeUnavailable".into()))
                                }
                                versioned::NativeDispatchFailure::Owned(error) => {
                                    Outcome::native(error)
                                }
                            };
                        }
                    }
                }
                Outcome::plain((|| {
                    self.budget(Some(path.parent().ok_or("EvaluationIo")?))?;
                    let opened = versioned::Opened::open(protocol, &path)
                        .map_err(|error| failure(&error))?;
                    let summary = opened.summary().map_err(|error| failure(&error))?;
                    let completed = summary["arms"]
                        .as_array()
                        .is_some_and(|arms| arms.iter().all(|arm| arm["available"] == true));
                    Ok(Publication::Executed {
                        run_id,
                        metadata: index.prepared,
                        completed,
                        reopened: Some((Box::new(ReadCap { opened, _grant }), uuid()?, summary)),
                    })
                })())
            }
        }
    }
    fn selected_finish(
        &self,
        lease: &WindowLease,
        epoch: u64,
        client: &str,
        operation: u64,
        mut outcome: Outcome,
    ) -> Result<Value> {
        // Keep actual ownership even when the originating lease was destroyed.
        // No lease gate is acquired while holding the parent metadata mutex.
        {
            let mut parent = self.state.lock().unwrap_or_else(|p| p.into_inner());
            let job = parent
                .job
                .as_mut()
                .filter(|job| {
                    job.kind == JobKind::Selected
                        && job.epoch == epoch
                        && job.id == operation
                        && job.run == client
                })
                .ok_or("Closed")?;
            let ownership = job.selected.as_mut().ok_or("EvaluationInternal")?;
            ownership.retained = outcome.retained.take();
            // Actual shared execution has returned, including its owned cleanup
            // result. Retirement/TTL/drain never manufacture this acknowledgement.
            job.worker_active = false;
        }
        let mut publication = Some(outcome.result);
        let mut discard = vec![];
        let answer = lease.dispatch(epoch, || {
            let mut state = self.selected_lock()?;
            let r = state
                .records
                .get_mut(client)
                .filter(|r| r.owns(lease, epoch) && r.operation == Some(operation))
                .ok_or("Closed")?;
            r.running = false;
            r.cleanup_required = outcome.uncertain;
            if r.revoked {
                return Err("Closed".into());
            }
            match publication.take().ok_or("EvaluationInternal")? {
                Ok(Publication::Prepared(plan, token)) => {
                    r.metadata = Some(plan.metadata.clone());
                    r.plan = Some(plan);
                    r.plan_token = Some(token);
                    r.phase = "prepared";
                    r.error = None;
                    r.cause = None;
                    r.status()
                }
                Ok(Publication::Opened(cap, token, summary, index)) => {
                    r.cap = Some(cap);
                    r.run_token = Some(token);
                    r.binding = summary["binding"].as_str().map(str::to_owned);
                    r.metadata = None;
                    r.lane = Some(SelectedInputLane::parse(&index.lane)?);
                    r.run_id = Some(index.run_id);
                    r.phase = if summary["arms"]
                        .as_array()
                        .is_some_and(|arms| arms.iter().all(|arm| arm["available"] == true))
                    {
                        "completed"
                    } else {
                        "paused"
                    };
                    r.error = None;
                    r.cause = None;
                    r.status()
                }
                Ok(Publication::Executed {
                    run_id,
                    metadata,
                    completed,
                    reopened,
                }) => {
                    r.run_id = Some(run_id);
                    r.metadata = Some(metadata);
                    r.phase = if completed { "completed" } else { "paused" };
                    r.error = None;
                    r.cause = None;
                    if let Some((cap, token, summary)) = reopened {
                        r.cap = Some(cap);
                        r.run_token = Some(token);
                        r.binding = summary["binding"].as_str().map(str::to_owned);
                    }
                    let status = r.status()?;
                    r.cache_execution_status(operation, &status);
                    Ok(status)
                }
                Ok(Publication::Read(cap, result, idle_phase)) => {
                    r.cap = Some(cap);
                    r.phase = idle_phase;
                    r.touched = Instant::now();
                    r.error = result.as_ref().err().cloned();
                    result
                }
                Err(error) => {
                    let error = failure(&error);
                    r.phase = if outcome.uncertain {
                        "cleanup_required"
                    } else {
                        "failed"
                    };
                    r.error = Some(error);
                    r.cause = outcome.cause.take();
                    r.plan_token = None;
                    if let Some(plan) = r.plan.take() {
                        discard.push(Discard::Plan(plan));
                    }
                    let status = r.status()?;
                    r.cache_execution_status(operation, &status);
                    Ok(status)
                }
            }
        });
        let retired_job = {
            let mut parent = self.state.lock().unwrap_or_else(|p| p.into_inner());
            if !outcome.uncertain
                && parent.job.as_ref().is_some_and(|job| {
                    job.kind == JobKind::Selected && job.epoch == epoch && job.id == operation
                })
            {
                parent.job.take()
            } else {
                None
            }
        };
        self.clear_cancellation(epoch, operation);
        if !lease.valid(epoch) {
            let mut state = self.selected.lock().unwrap_or_else(|p| p.into_inner());
            if let Some(r) = state
                .records
                .get_mut(client)
                .filter(|r| r.epoch == epoch && r.operation == Some(operation))
            {
                r.running = false;
                r.cleanup_required = outcome.uncertain;
                r.revoke(&mut discard);
            }
        }
        drop(publication);
        dispose(discard);
        drop(retired_job);
        answer
    }
}

struct CleanupWork {
    kind: JobKind,
    epoch: u64,
    operation: u64,
    models: Arc<ModelManager>,
    witness: Option<models::CleanupWitness>,
    pair: Option<(models::EvaluationReservation, Runtime)>,
}
fn cleanup_envelope(required: bool, running: bool, error: Option<String>) -> Value {
    json!({"version":1,"kind":"selected_cleanup","cleanup_required":required,"running":running,"error":error})
}
impl EvaluationManager {
    fn selected_worker_active(&self) -> bool {
        let handle_running = self
            .worker
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .as_ref()
            .is_some_and(|(_, worker)| !worker.is_finished());
        // Parent drain temporarily takes the handle before joining outside its
        // gate. The same authoritative Job flag also covers owned NativeCurated;
        // presentation records are not a second worker registry or an ack.
        handle_running
            || self
                .state
                .lock()
                .unwrap_or_else(|p| p.into_inner())
                .job
                .as_ref()
                .is_some_and(|job| job.worker_active)
    }
    fn selected_cleanup_snapshot(
        &self,
        expected_epoch: Option<u64>,
    ) -> Result<(Value, Option<Job>)> {
        let active = self.selected_worker_active();
        let mut removed = None;
        let (required, running) = {
            let mut parent = self.state()?;
            match parent.job.as_ref().filter(|job| {
                job.selected.is_some() && expected_epoch.is_none_or(|epoch| job.epoch == epoch)
            }) {
                None => (false, false),
                Some(job) => {
                    let ownership = job.selected.as_ref().ok_or("EvaluationInternal")?;
                    if !active
                        && !ownership.cleanup_running
                        && ownership.retained.is_none()
                        && ownership
                            .witness
                            .as_ref()
                            .is_some_and(models::CleanupWitness::confirmed)
                    {
                        removed = parent.job.take();
                        (false, false)
                    } else {
                        (
                            !active || ownership.cleanup_running,
                            active || ownership.cleanup_running,
                        )
                    }
                }
            }
        };
        let mut selected = self.selected_lock()?;
        if let Some(job) = removed.as_ref().filter(|job| job.kind == JobKind::Selected) {
            for record in selected
                .records
                .values_mut()
                .filter(|r| r.epoch == job.epoch && r.operation == Some(job.id))
            {
                record.cleanup_required = false;
                if record.phase == "cleanup_required" {
                    record.phase = "failed";
                }
                let value = record.status()?;
                record.cache_execution_status(job.id, &value);
            }
        }
        let error = selected.cleanup_error.clone();
        drop(selected);
        if let Some(job) = removed
            .as_ref()
            .filter(|j| j.kind == JobKind::ComparisonRun)
        {
            self.full_comparison_cleanup_confirmed(job.epoch, job.id, &job.run);
        }
        Ok((cleanup_envelope(required, running, error), removed))
    }
    pub fn selected_cleanup_status(&self, lease: &WindowLease, epoch: u64) -> Result<Value> {
        let registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
        let (value, removed) = lease.dispatch(epoch, || self.selected_cleanup_snapshot(None))?;
        drop(registration);
        drop(removed);
        Ok(value)
    }
    fn selected_take_cleanup(
        &self,
        expected_epoch: Option<u64>,
        models: Option<&Arc<ModelManager>>,
    ) -> Result<Option<CleanupWork>> {
        if self.selected_worker_active() {
            return Ok(None);
        }
        let mut parent = self.state()?;
        let Some(job) = parent.job.as_mut().filter(|job| {
            job.selected.is_some() && expected_epoch.is_none_or(|epoch| job.epoch == epoch)
        }) else {
            return Ok(None);
        };
        let ownership = job.selected.as_mut().ok_or("EvaluationInternal")?;
        if models.is_some_and(|models| !Arc::ptr_eq(models, &ownership.models)) {
            return Err("EvaluationModelBusy".into());
        }
        if ownership.cleanup_running {
            return Ok(None);
        }
        ownership.cleanup_running = true;
        Ok(Some(CleanupWork {
            kind: job.kind,
            epoch: job.epoch,
            operation: job.id,
            models: ownership.models.clone(),
            witness: ownership.witness.clone(),
            pair: ownership.retained.take(),
        }))
    }
    fn selected_do_cleanup(&self, mut work: CleanupWork) -> Value {
        let outcome = if let Some((reservation, owner)) = work.pair.as_mut() {
            reservation.cleanup_retained(owner)
        } else if let Some(witness) = &work.witness {
            work.models.cleanup_selected(witness)
        } else {
            models::CleanupOutcome {
                confirmed: false,
                result: Err("Cleanup".into()),
            }
        };
        let diagnostic = outcome.result.as_ref().err().map(|_| "Cleanup".to_owned());
        let mut removed = None;
        {
            let mut parent = self.state.lock().unwrap_or_else(|p| p.into_inner());
            if let Some(job) = parent.job.as_mut().filter(|job| {
                job.kind == work.kind && job.epoch == work.epoch && job.id == work.operation
            }) {
                if let Some(ownership) = job
                    .selected
                    .as_mut()
                    .filter(|owned| Arc::ptr_eq(&owned.models, &work.models))
                {
                    ownership.cleanup_running = false;
                    if !outcome.confirmed {
                        ownership.retained = work.pair.take();
                    } else {
                        removed = parent.job.take();
                    }
                }
            }
        }
        {
            let mut state = self.selected.lock().unwrap_or_else(|p| p.into_inner());
            state.cleanup_error = diagnostic.clone();
            if work.kind == JobKind::Selected {
                for record in state
                    .records
                    .values_mut()
                    .filter(|r| r.epoch == work.epoch && r.operation == Some(work.operation))
                {
                    record.cleanup_required = !outcome.confirmed;
                    if outcome.confirmed && record.phase == "cleanup_required" {
                        record.phase = "failed";
                    }
                    if let Ok(value) = record.status() {
                        record.cache_execution_status(work.operation, &value);
                    }
                }
            }
        }
        // Actual R Drop/model ownership drops happen only after metadata gates.
        if let Some(job) = removed
            .as_ref()
            .filter(|j| j.kind == JobKind::ComparisonRun)
        {
            self.full_comparison_cleanup_confirmed(job.epoch, job.id, &job.run);
        }
        drop(removed);
        drop(work);
        cleanup_envelope(!outcome.confirmed, false, diagnostic)
    }
    pub fn selected_retry_cleanup(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
    ) -> Result<Value> {
        loop {
            let registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
            if !lease.valid(epoch) {
                return Err("Closed".into());
            }
            if self.selected_worker_active() {
                let (value, removed) =
                    lease.dispatch(epoch, || self.selected_cleanup_snapshot(None))?;
                drop(registration);
                drop(removed);
                return Ok(value);
            }
            let previous = self.worker.lock().unwrap_or_else(|p| p.into_inner()).take();
            if let Some((_, handle)) = previous {
                drop(registration);
                handle.join().map_err(|_| "EvaluationInternal")?;
                continue;
            }
            let payload =
                lease.dispatch(epoch, || self.selected_take_cleanup(None, Some(models)))?;
            let Some(payload) = payload else {
                let (value, removed) =
                    lease.dispatch(epoch, || self.selected_cleanup_snapshot(None))?;
                drop(registration);
                drop(removed);
                return Ok(value);
            };
            let expected_kind = payload.kind;
            let expected_epoch = payload.epoch;
            let operation = payload.operation;
            let held = Arc::new(Mutex::new(Some(payload)));
            let worker_held = held.clone();
            let manager = self.clone();
            let (send, registered) = mpsc::channel();
            let worker = move || {
                if registered.recv().is_err() {
                    return;
                }
                let work = { worker_held.lock().unwrap_or_else(|p| p.into_inner()).take() };
                if let Some(work) = work {
                    manager.selected_do_cleanup(work);
                }
            };
            match std::thread::Builder::new()
                .name("locallore-evaluation".into())
                .spawn(worker)
            {
                Ok(handle) => {
                    *self.worker.lock().unwrap_or_else(|p| p.into_inner()) =
                        Some((expected_epoch, handle));
                    let _ = send.send(());
                    drop(registration);
                    return Ok(cleanup_envelope(true, true, None));
                }
                Err(_) => {
                    let mut payload = held
                        .lock()
                        .unwrap_or_else(|p| p.into_inner())
                        .take()
                        .ok_or("EvaluationInternal")?;
                    {
                        let mut parent = self.state.lock().unwrap_or_else(|p| p.into_inner());
                        let job = parent
                            .job
                            .as_mut()
                            .filter(|j| {
                                j.kind == expected_kind
                                    && j.epoch == expected_epoch
                                    && j.id == operation
                            })
                            .ok_or("EvaluationInternal")?;
                        let ownership = job.selected.as_mut().ok_or("EvaluationInternal")?;
                        ownership.cleanup_running = false;
                        ownership.retained = payload.pair.take();
                    }
                    drop(registration);
                    drop(payload);
                    return Err("EvaluationInternal".into());
                }
            }
        }
    }
    /// CloseGate's captured native epoch only. No renderer can manufacture this
    /// call; it never selects a newer epoch or drains an arbitrary active job.
    pub(crate) fn selected_cleanup_retired(&self, epoch: u64) -> Result<Value> {
        let registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
        let work = self.selected_take_cleanup(Some(epoch), None)?;
        drop(registration);
        match work {
            Some(work) => Ok(self.selected_do_cleanup(work)),
            None => {
                let (value, removed) = self.selected_cleanup_snapshot(Some(epoch))?;
                drop(removed);
                Ok(value)
            }
        }
    }
}

#[cfg(test)]
mod tests;
#[cfg(test)]
#[path = "selected/prepared_policy_review_tests.rs"]
mod prepared_policy_review_tests;
