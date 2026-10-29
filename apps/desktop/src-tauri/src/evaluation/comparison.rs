//! Native-only read capability over the existing shared comparison reader.
//! No runner, provider, model reservation, renderer path or persistent journal.
use super::*;
use locallore::inspection_query::Observer;
use locallore_eval::local_lane::comparison::desktop_api as shared;
use locallore_eval::local_lane::comparison::literal_v3::desktop_api as literal;
use locallore_eval::local_lane::comparison::scene_v4::desktop_api as scene;
use std::sync::{mpsc, Weak};

const TTL: Duration = Duration::from_secs(900);
const MAX_CLIENTS: usize = 4;
const MAX_SAFE: u64 = 9_007_199_254_740_991;

pub struct ComparisonEvidenceRequest {
    pub token: String,
    pub binding: String,
    pub row: shared::RowId,
    pub request: shared::EvidenceRequest,
}
pub struct ComparisonNarrationDiagnosticRequestV1 {
    pub token: String,
    pub binding: String,
    pub row: shared::RowId,
    pub observer: Observer,
}
// Constructed only after affirmative native picker selection and shared open.
struct ReaderGrant;
// One existing reader lifecycle; the variant cannot become execution permission.
enum OpenedRead {
    V2(shared::OpenedComparison),
    V3(literal::OpenedComparison),
    V4(scene::OpenedComparison),
}
impl OpenedRead {
    fn open(path: &Path) -> Result<Self> {
        match shared::open_read_only(path) {
            Ok(opened) => Ok(Self::V2(opened)),
            Err(original) => match literal::open_read_only(path) {
                Ok(opened) => Ok(Self::V3(opened)),
                Err(_) => match scene::open_read_only(path) {
                    Ok(opened) => Ok(Self::V4(opened)),
                    // Preserve the existing V2 failure category on invalid sources.
                    Err(_) => Err(original),
                },
            },
        }
    }
    fn summary(&self) -> Result<Value> {
        match self {
            Self::V2(opened) => shared::summary(opened, true),
            Self::V3(opened) => literal::summary(opened, true),
            Self::V4(opened) => scene::summary(opened, true),
        }
    }
    fn evidence(
        &self,
        binding: &str,
        row: &shared::RowId,
        request: shared::EvidenceRequest,
    ) -> Result<Value> {
        match self {
            Self::V2(opened) => shared::evidence(opened, binding, row, request, true),
            Self::V3(opened) => literal::evidence(opened, binding, row, request, true),
            Self::V4(opened) => scene::evidence(opened, binding, row, request, true),
        }
    }
    fn narration_diagnostic_v1(
        &self,
        binding: &str,
        row: &shared::RowId,
        observer: Observer,
    ) -> Result<Value> {
        match self {
            Self::V4(opened) => {
                scene::narration_diagnostic_v1(opened, binding, row, observer, true)
            }
            Self::V2(_) | Self::V3(_) => Err("Unsupported".into()),
        }
    }
}
struct Capability {
    opened: OpenedRead,
    origin: PathBuf,
    _grant: ReaderGrant,
}

/// Only the same admitted native selected worker can consume this source.
/// The old read grant is revoked before transfer; it grants no execution.
pub(super) struct SelectedSource {
    opened: OpenedRead,
    origin: PathBuf,
    binding: String,
}
impl SelectedSource {
    pub(super) fn protocol_version(&self) -> u16 {
        match &self.opened {
            OpenedRead::V2(_) => 2,
            OpenedRead::V3(_) => 3,
            OpenedRead::V4(_) => 4,
        }
    }
    pub(super) fn into_origin(self) -> (PathBuf, String) {
        let Self {
            opened,
            origin,
            binding,
        } = self;
        // The caller executes this in its registered worker, outside metadata,
        // window-lease and admission gates. Releasing the File lock can do IO.
        drop(opened);
        (origin, binding)
    }
}
struct Record {
    window: Weak<WindowLease>,
    epoch: u64,
    client: String,
    token: Option<String>,
    snapshot: Option<Value>,
    cap: Option<Capability>,
    granted: bool,
    expired: bool,
    phase: &'static str,
    running: bool,
    operation: Option<u64>,
    error: Option<String>,
    cancel: Cancellation,
    touched: Instant,
}
impl Record {
    fn owns(&self, lease: &WindowLease, epoch: u64) -> bool {
        self.epoch == epoch && std::ptr::eq(self.window.as_ptr(), lease)
    }
    fn status(&self) -> Result<Value> {
        let usable = self.granted && !self.expired && matches!(self.phase, "ready" | "reading");
        bounded(
            json!({"version":1,"kind":"comparison_reader","client_id":self.client,
            "operation_id":self.operation,"phase":self.phase,"running":self.running,
            "run_token":if usable{self.token.clone()}else{None},
            "binding":if usable{self.snapshot.as_ref().and_then(|s|s["binding"].as_str())}else{None},
            "error":self.error,"read_only":true,"execution_available":false}),
            4096,
        )
    }
    fn close(&mut self, discard: &mut Vec<Capability>) {
        self.cancel.cancel();
        self.granted = false;
        self.snapshot = None;
        self.error = None;
        if let Some(cap) = self.cap.take() {
            discard.push(cap)
        }
        self.phase = if self.running { "closing" } else { "closed" };
        if !self.running {
            self.operation = None;
        }
    }
}
#[derive(Default)]
pub(super) struct ComparisonState {
    records: BTreeMap<String, Record>,
}
enum WorkResult {
    Picked(Option<(Capability, Value, String)>),
    Read(Capability, Result<Value>),
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
fn failure(error: String) -> String {
    match error.as_str() {
        "EvaluationIntegrity"
        | "EvaluationSourceMismatch"
        | "EvaluationBudget"
        | "EvaluationIo"
        | "UnsafeEvaluationPath"
        | "InvalidEvaluationInput"
        | "UnknownEvaluationRun"
        | "EvaluationTokenLimit" => return error,
        "Forbidden" | "InspectionForbidden" => "Forbidden",
        "Closed" => "Closed",
        "PickerUnavailable" => "PickerUnavailable",
        "Unsupported" | "UnsupportedPlatform" | "UnsupportedDomain" => "Unsupported",
        "EvaluationInternal" => "EvaluationInternal",
        "RunBusy" | "EvaluationBusy" => "EvaluationBusy",
        "Reparse" | "ComparisonDirectory" => "UnsafeEvaluationPath",
        "UnknownRow" | "InspectionUnknownObserver" | "InspectionInvalidRequest" => {
            "InvalidEvaluationInput"
        }
        e if e.ends_with("Budget") || e == "TooLarge" || e == "InspectionTooLarge" => {
            "EvaluationBudget"
        }
        e if e == "SnapshotMismatch"
            || e == "Replay"
            || e == "Lookup"
            || e == "InputBinding"
            || e == "Profile"
            || e.starts_with("Checkpoint")
            || e.starts_with("Recording")
            || e.starts_with("Capture")
            || e.starts_with("Raw")
            || e.starts_with("Ledger")
            || e.starts_with("Reference")
            || e.starts_with("Scene")
            || e == "ComparisonBinding"
            || e == "RolloutContinuity" =>
        {
            "EvaluationIntegrity"
        }
        _ => "EvaluationIo",
    }
    .into()
}
fn actor_raw(request: &shared::EvidenceRequest) -> bool {
    match request {
        shared::EvidenceRequest::Query { .. } => false,
        shared::EvidenceRequest::Receipt { observer }
        | shared::EvidenceRequest::Capture { observer }
        | shared::EvidenceRequest::Outputs { observer } => {
            !matches!(observer, Observer::Omniscient)
        }
    }
}
// Only the new read uses these additional fixed categories. Existing actions
// retain their original projection and no companion failure text is forwarded.
fn narration_diagnostic_failure(error: String) -> String {
    match error.as_str() {
        "DiagnosticWire" | "DiagnosticBinding" => "EvaluationIntegrity".into(),
        "DiagnosticBudget" => "EvaluationBudget".into(),
        "DiagnosticIo" | "Io" => "EvaluationIo".into(),
        "Reparse" | "AliasedDestination" => "UnsafeEvaluationPath".into(),
        _ => failure(error),
    }
}
fn valid_narration_diagnostic(input: &ComparisonNarrationDiagnosticRequestV1) -> bool {
    valid_id(&input.token)
        && !input.token.bytes().any(|b| b.is_ascii_uppercase())
        && input.binding.len() == 64
        && input
            .binding
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        && !input.row.turn.is_empty()
        && input.row.turn.len() <= 64
        && input
            .row
            .turn
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn valid_evidence(input: &ComparisonEvidenceRequest) -> bool {
    let actor = match &input.request {
        shared::EvidenceRequest::Query { observer, .. }
        | shared::EvidenceRequest::Receipt { observer }
        | shared::EvidenceRequest::Capture { observer }
        | shared::EvidenceRequest::Outputs { observer } => observer,
    };
    valid_id(&input.token)
        && input.binding.len() == 64
        && input
            .binding
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        && !input.row.turn.is_empty()
        && input.row.turn.len() <= 64
        && input
            .row
            .turn
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
        && match actor {
            Observer::Character { id } => {
                !id.is_empty()
                    && id.len() <= 64
                    && id
                        .bytes()
                        .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
            }
            _ => true,
        }
}
impl EvaluationManager {
    /// Caller holds the existing lease/parent-job admission gates. No IO or
    /// source-lock Drop occurs here; the opaque payload moves into that worker.
    pub(super) fn comparison_take_source_in_gate(
        &self,
        lease: &WindowLease,
        epoch: u64,
        client: &str,
        token: &str,
        binding: &str,
    ) -> Result<SelectedSource> {
        let mut state = self.comparison_lock()?;
        let record = state
            .records
            .get_mut(client)
            .filter(|record| {
                record.owns(lease, epoch)
                    && record.granted
                    && !record.expired
                    && !record.running
                    && record.phase == "ready"
                    && record.touched.elapsed() <= TTL
                    && record.token.as_deref() == Some(token)
            })
            .ok_or("UnknownEvaluationRun")?;
        if record
            .snapshot
            .as_ref()
            .and_then(|value| value["binding"].as_str())
            != Some(binding)
        {
            return Err("EvaluationSourceMismatch".into());
        }
        let Capability {
            opened,
            origin,
            _grant,
        } = record.cap.take().ok_or("UnknownEvaluationRun")?;
        record.cancel.cancel();
        record.granted = false;
        record.token = None;
        record.snapshot = None;
        record.phase = "closed";
        record.operation = None;
        record.error = None;
        Ok(SelectedSource {
            opened,
            origin,
            binding: binding.into(),
        })
    }
    fn comparison_lock(&self) -> Result<std::sync::MutexGuard<'_, ComparisonState>> {
        self.comparison
            .lock()
            .map_err(|_| "EvaluationInternal".into())
    }
    // Access-time expiry: detach under lock and DROP handles after all gates.
    fn comparison_expire(&self, lease: &WindowLease, epoch: u64) -> Result<()> {
        let mut discard = vec![];
        let result = lease.dispatch(epoch, || {
            let mut state = self.comparison_lock()?;
            for record in state.records.values_mut() {
                if record.owns(lease, epoch)
                    && !record.running
                    && !record.expired
                    && record.touched.elapsed() > TTL
                {
                    record.expired = true;
                    record.close(&mut discard);
                }
            }
            Ok(())
        });
        drop(discard);
        result
    }
    pub fn comparison_status(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        client: &str,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !valid_id(client) {
            return Err("InvalidEvaluationInput".into());
        }
        self.comparison_expire(lease, epoch)?;
        lease.dispatch(epoch, || {
            let mut state = self.comparison_lock()?;
            let r = state
                .records
                .get_mut(client)
                .filter(|r| r.owns(lease, epoch) && !r.expired)
                .ok_or("UnknownEvaluationRun")?;
            r.touched = Instant::now();
            r.status()
        })
    }
    fn comparison_cached(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
        source: bool,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !valid_id(token) {
            return Err("InvalidEvaluationInput".into());
        }
        self.comparison_expire(lease, epoch)?;
        lease.dispatch(epoch,||{let mut state=self.comparison_lock()?;
            let r=state.records.values_mut().find(|r|r.owns(lease,epoch)&&!r.expired&&r.granted&&r.token.as_deref()==Some(token)).ok_or("UnknownEvaluationRun")?;
            r.touched=Instant::now();let snapshot=r.snapshot.as_ref().ok_or("UnknownEvaluationRun")?;
            if source {bounded(json!({"version":1,"kind":"comparison_reader","run_token":token,
                "source":{"binding":snapshot["binding"],"protocol_version":snapshot["protocol_version"],"rows":snapshot["rows"],"read_only":true,"execution_available":false}}),65536)}
            else {bounded(json!({"version":1,"kind":"comparison_reader","run_token":token,"snapshot":snapshot}),2*1024*1024+4096)}
        })
    }
    pub fn comparison_source(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
    ) -> Result<Value> {
        self.comparison_cached(lease, epoch, granted, token, true)
    }
    pub fn comparison_summary(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
    ) -> Result<Value> {
        self.comparison_cached(lease, epoch, granted, token, false)
    }

    pub fn comparison_close(
        &self,
        lease: &WindowLease,
        epoch: u64,
        client: &str,
        token: Option<&str>,
    ) -> Result<Value> {
        if !valid_id(client) || token.is_some_and(|t| !valid_id(t)) {
            return Err("InvalidEvaluationInput".into());
        }
        let mut discard = vec![];
        let result = lease.dispatch(epoch, || {
            let mut state = self.comparison_lock()?;
            let r = state
                .records
                .get_mut(client)
                .filter(|r| r.owns(lease, epoch))
                .ok_or("UnknownEvaluationRun")?;
            // A transferred/released record has no capability left to close.
            // Acknowledging that empty owner is idempotent; a replacement ready
            // capability still requires its exact token and native epoch.
            let empty_closed = r.phase == "closed"
                && !r.running
                && !r.granted
                && r.token.is_none()
                && r.cap.is_none()
                && r.snapshot.is_none()
                && r.operation.is_none();
            if token.is_some() && r.token.as_deref() != token && !empty_closed {
                return Err("UnknownEvaluationRun".into());
            }
            r.close(&mut discard);
            r.touched = Instant::now();
            r.status()
        });
        drop(discard);
        result
    }
    pub(super) fn comparison_retire(&self, epoch: u64) {
        // Invalidation already revoked the lease. Never wait for an IO worker or
        // acquire another manager lock; drain handles outside this callback.
        if let Ok(mut state) = self.comparison.try_lock() {
            for r in state.records.values_mut().filter(|r| r.epoch == epoch) {
                r.cancel.cancel();
                r.granted = false;
                r.phase = "closing";
            }
        }
    }
    pub(super) fn comparison_drain(&self, epoch: u64) {
        let discarded = {
            let mut state = self.comparison.lock().unwrap_or_else(|p| p.into_inner());
            let ids = state
                .records
                .iter()
                .filter(|(_, r)| r.epoch == epoch)
                .map(|(id, _)| id.clone())
                .collect::<Vec<_>>();
            ids.into_iter()
                .filter_map(|id| state.records.remove(&id))
                .collect::<Vec<_>>()
        };
        drop(discarded);
    }

    pub fn comparison_pick(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        client: &str,
        picker: impl FnOnce() -> Result<Option<PathBuf>> + Send + 'static,
    ) -> Result<Value> {
        if !granted {
            return Err("Forbidden".into());
        }
        if !valid_id(client) {
            return Err("InvalidEvaluationInput".into());
        }
        self.comparison_expire(lease, epoch)?;
        let existing = lease.dispatch(epoch, || {
            let mut state = self.comparison_lock()?;
            if let Some(r) = state.records.get_mut(client) {
                if !r.owns(lease, epoch) || r.expired {
                    return Err("UnknownEvaluationRun".into());
                }
                r.touched = Instant::now();
                return Ok(Some(r.status()?));
            }
            Ok(None)
        })?;
        if let Some(existing) = existing {
            return Ok(existing);
        }
        let client = client.to_owned();
        let owner = Arc::downgrade(lease);
        let prepare_client = client.clone();
        self.comparison_launch(
            lease,
            epoch,
            client,
            move |state, operation, cancel| {
                if state
                    .records
                    .values()
                    .any(|r| r.epoch == epoch && !matches!(r.phase, "closed"))
                {
                    return Err("EvaluationBusy".into());
                }
                if state.records.contains_key(&prepare_client) {
                    return Err("EvaluationBusy".into());
                }
                if state.records.len() >= MAX_CLIENTS {
                    let oldest = state
                        .records
                        .iter()
                        .filter(|(_, r)| r.phase == "closed" && !r.running)
                        .min_by_key(|(_, r)| r.touched)
                        .map(|(id, _)| id.clone())
                        .ok_or("EvaluationTokenLimit")?;
                    // Closed records contain no capability/ReaderGrant.
                    state.records.remove(&oldest);
                }
                state.records.insert(
                    prepare_client.clone(),
                    Record {
                        window: owner,
                        epoch,
                        client: prepare_client,
                        token: None,
                        snapshot: None,
                        cap: None,
                        granted: false,
                        expired: false,
                        phase: "choosing",
                        running: true,
                        operation: Some(operation),
                        error: None,
                        cancel: cancel.clone(),
                        touched: Instant::now(),
                    },
                );
                Ok(())
            },
            None,
            move |(), manager, owner, epoch, client, operation, cancel| {
                if cancel.is_cancelled() || !owner.valid(epoch) {
                    return Err("Closed".into());
                }
                let Some(path) = picker().map_err(failure)? else {
                    return Ok(WorkResult::Picked(None));
                };
                if cancel.is_cancelled() || !owner.valid(epoch) {
                    return Err("Closed".into());
                }
                owner.dispatch(epoch, || {
                    let mut state = manager.comparison_lock()?;
                    let r = state
                        .records
                        .get_mut(&client)
                        .filter(|r| r.operation == Some(operation) && r.phase == "choosing")
                        .ok_or("Closed")?;
                    r.phase = "opening";
                    Ok(())
                })?;
                let token = uuid()?;
                let opened = OpenedRead::open(&path).map_err(failure)?;
                let snapshot = opened.summary().map_err(failure)?;
                // Permission originated in the native affirmative picker, not JSON.
                Ok(WorkResult::Picked(Some((
                    Capability {
                        opened,
                        origin: path,
                        _grant: ReaderGrant,
                    },
                    snapshot,
                    token,
                ))))
            },
        )
    }

    pub fn comparison_evidence(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        input: ComparisonEvidenceRequest,
    ) -> Result<Value> {
        if !granted || actor_raw(&input.request) {
            return Err("Forbidden".into());
        }
        if !valid_evidence(&input) {
            return Err("InvalidEvaluationInput".into());
        }
        self.comparison_expire(lease, epoch)?;
        let client = lease.dispatch(epoch, || {
            let state = self.comparison_lock()?;
            state
                .records
                .values()
                .find(|r| {
                    r.owns(lease, epoch)
                        && !r.expired
                        && r.granted
                        && r.token.as_deref() == Some(input.token.as_str())
                })
                .map(|r| r.client.clone())
                .ok_or_else(|| "UnknownEvaluationRun".into())
        })?;
        let token = input.token.clone();
        let prepare_client = client.clone();
        let (send, receive) = mpsc::sync_channel(1);
        self.comparison_launch(lease,epoch,client,move|state,operation,cancel|{
            let r=state.records.get_mut(&prepare_client).filter(|r|r.owns(lease,epoch)&&!r.expired&&r.granted&&r.token.as_deref()==Some(token.as_str())).ok_or("UnknownEvaluationRun")?;
            if r.running{return Err("EvaluationBusy".into())}
            let cap=r.cap.take().ok_or("UnknownEvaluationRun")?;
            r.running=true;r.phase="reading";r.operation=Some(operation);r.cancel=cancel.clone();r.touched=Instant::now();Ok(cap)
        },Some(send),move|cap:Capability,_manager,_owner,_epoch,_client,_operation,_cancel|{
            let result=cap.opened.evidence(&input.binding,&input.row,input.request).map_err(failure)
                .and_then(|evidence|bounded(json!({"version":1,"kind":"comparison_reader","run_token":input.token,"evidence":evidence}),256*1024+4096));
            Ok(WorkResult::Read(cap,result))
        })?;
        // A response timeout does not pretend to stop native IO. Status/close
        // retain the exact admitted operation until this same worker finishes.
        receive
            .recv_timeout(Duration::from_secs(30))
            .map_err(|_| "EvaluationIo".to_owned())?
    }

    pub fn comparison_narration_diagnostic_v1(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        input: ComparisonNarrationDiagnosticRequestV1,
    ) -> Result<Value> {
        // The requested lens grants nothing. Refuse before scalar validation,
        // expiry, lease/token/source lookup or any new filesystem work.
        if !granted || !matches!(&input.observer, Observer::Omniscient) {
            return Err("Forbidden".into());
        }
        if !valid_narration_diagnostic(&input) {
            return Err("InvalidEvaluationInput".into());
        }
        self.comparison_expire(lease, epoch)?;
        let client = lease.dispatch(epoch, || {
            let state = self.comparison_lock()?;
            state
                .records
                .values()
                .find(|r| {
                    r.owns(lease, epoch)
                        && !r.expired
                        && r.granted
                        && r.token.as_deref() == Some(input.token.as_str())
                })
                .map(|r| r.client.clone())
                .ok_or_else(|| "UnknownEvaluationRun".into())
        })?;
        let token = input.token.clone();
        let prepare_client = client.clone();
        let (send, receive) = mpsc::sync_channel(1);
        self.comparison_launch(
            lease,
            epoch,
            client,
            move |state, operation, cancel| {
                let r = state
                    .records
                    .get_mut(&prepare_client)
                    .filter(|r| {
                        r.owns(lease, epoch)
                            && !r.expired
                            && r.granted
                            && r.token.as_deref() == Some(token.as_str())
                    })
                    .ok_or("UnknownEvaluationRun")?;
                if r.running {
                    return Err("EvaluationBusy".into());
                }
                let cap = r.cap.take().ok_or("UnknownEvaluationRun")?;
                r.running = true;
                r.phase = "reading";
                r.operation = Some(operation);
                r.cancel = cancel.clone();
                r.touched = Instant::now();
                Ok(cap)
            },
            Some(send),
            move |cap: Capability, _manager, _owner, _epoch, _client, _operation, _cancel| {
                let result = cap
                    .opened
                    .narration_diagnostic_v1(&input.binding, &input.row, input.observer)
                    .map_err(narration_diagnostic_failure)
                    .and_then(|diagnostic| {
                        bounded(
                            json!({"version":1,"kind":"comparison_reader_narration_diagnostic_v1",
                                "run_token":input.token,"diagnostic":diagnostic}),
                            8192,
                        )
                    });
                Ok(WorkResult::Read(cap, result))
            },
        )?;
        // A timeout does not cancel the same still-owned worker or filesystem
        // operation. Existing status/close/drain remain authoritative.
        receive
            .recv_timeout(Duration::from_secs(30))
            .map_err(|_| "EvaluationIo".to_owned())?
    }

    fn comparison_launch<T: Send + 'static, P, F>(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        client: String,
        prepare: P,
        reply: Option<mpsc::SyncSender<Result<Value>>>,
        work: F,
    ) -> Result<Value>
    where
        P: FnOnce(&mut ComparisonState, u64, &Cancellation) -> Result<T>,
        F: FnOnce(
                T,
                Arc<Self>,
                Arc<WindowLease>,
                u64,
                String,
                u64,
                Cancellation,
            ) -> Result<WorkResult>
            + Send
            + 'static,
    {
        let mut prepare = Some(prepare);
        let mut work = Some(work);
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
                    .filter(|n| *n <= MAX_SAFE)
                    .ok_or("EvaluationBudget")?;
                let cancel = Cancellation::default();
                let mut state = self.comparison_lock()?;
                let payload =
                    prepare.take().ok_or("EvaluationInternal")?(&mut state, operation, &cancel)?;
                parent.next = operation;
                parent.job = Some(Job {
                    epoch,
                    id: operation,
                    run: client.clone(),
                    cancel: cancel.clone(),
                    kind: JobKind::ComparisonRead,
                    selected: None,
                    worker_active: true,
                });
                let initial = state
                    .records
                    .get(&client)
                    .ok_or("EvaluationInternal")?
                    .status()?;
                Ok((operation, cancel, payload, initial))
            })?;
            self.register_cancellation(lease, epoch, operation, &cancel);
            #[cfg(test)]
            if let Some((entered, release)) = self.before_spawn.lock().unwrap().take() {
                entered.wait();
                release.wait();
            }
            let payload = Arc::new(Mutex::new(Some(payload)));
            let held = payload.clone();
            let manager = self.clone();
            let owner = lease.clone();
            let client_copy = client.clone();
            let cancel_copy = cancel.clone();
            let work = work.take().ok_or("EvaluationInternal")?;
            let (start, registered) = mpsc::channel();
            let worker = move || {
                if registered.recv().is_err() {
                    return;
                }
                let payload = held.lock().unwrap_or_else(|p| p.into_inner()).take();
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    #[cfg(test)]
                    if manager
                        .panic_worker
                        .swap(false, std::sync::atomic::Ordering::SeqCst)
                    {
                        panic!("fixed comparison reader worker panic")
                    }
                    if !owner.valid(epoch) || cancel_copy.is_cancelled() {
                        return Err("Closed".into());
                    }
                    work(
                        payload.ok_or("EvaluationInternal")?,
                        manager.clone(),
                        owner.clone(),
                        epoch,
                        client_copy.clone(),
                        operation,
                        cancel_copy.clone(),
                    )
                }))
                .unwrap_or_else(|_| Err("EvaluationInternal".into()));
                #[cfg(test)]
                if let Some((entered, release)) = manager.before_publish.lock().unwrap().take() {
                    entered.wait();
                    release.wait();
                }
                let delivered = manager.comparison_finish(
                    &owner,
                    epoch,
                    &client_copy,
                    operation,
                    &cancel_copy,
                    result,
                );
                if let Some(reply) = reply {
                    let _ = reply.send(delivered);
                }
            };
            #[cfg(test)]
            let failed = self
                .fail_spawn
                .swap(false, std::sync::atomic::Ordering::SeqCst);
            #[cfg(not(test))]
            let failed = false;
            let spawned = if failed {
                Err(std::io::Error::other("fixed comparison spawn refusal"))
            } else {
                std::thread::Builder::new()
                    .name("locallore-evaluation".into())
                    .spawn(worker)
            };
            match spawned {
                Ok(handle) => {
                    *self.worker.lock().unwrap_or_else(|p| p.into_inner()) = Some((epoch, handle));
                    let _ = start.send(());
                }
                Err(_) => {
                    drop(registration);
                    let _ = self.comparison_finish(
                        lease,
                        epoch,
                        &client,
                        operation,
                        &cancel,
                        Err("EvaluationInternal".into()),
                    );
                    let discarded = payload.lock().unwrap_or_else(|p| p.into_inner()).take();
                    drop(discarded);
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

    fn comparison_finish(
        &self,
        lease: &WindowLease,
        epoch: u64,
        client: &str,
        operation: u64,
        cancel: &Cancellation,
        outcome: Result<WorkResult>,
    ) -> Result<Value> {
        let mut outcome = Some(outcome);
        let mut discard = vec![];
        let answer = lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            if !parent.job.as_ref().is_some_and(|j| {
                j.kind == JobKind::ComparisonRead
                    && j.epoch == epoch
                    && j.id == operation
                    && j.run == client
            }) {
                return Err("Closed".into());
            }
            let mut state = self.comparison_lock()?;
            let r = state
                .records
                .get_mut(client)
                .filter(|r| r.owns(lease, epoch) && r.operation == Some(operation))
                .ok_or("Closed")?;
            let reading = r.phase == "reading";
            let closed = cancel.is_cancelled() || r.phase == "closing";
            r.running = false;
            let result = if closed {
                r.close(&mut discard);
                Err("Closed".into())
            } else {
                match outcome.take().ok_or("EvaluationInternal")? {
                    Ok(WorkResult::Picked(None)) => {
                        r.phase = "cancelled";
                        r.error = None;
                        r.status()
                    }
                    Ok(WorkResult::Picked(Some((cap, snapshot, token)))) => {
                        r.token = Some(token);
                        r.snapshot = Some(snapshot);
                        r.cap = Some(cap);
                        r.granted = true;
                        r.phase = "ready";
                        r.error = None;
                        r.touched = Instant::now();
                        r.status()
                    }
                    Ok(WorkResult::Read(cap, result)) => {
                        r.cap = Some(cap);
                        r.phase = "ready";
                        r.error = None;
                        r.touched = Instant::now();
                        result
                    }
                    Err(error) => {
                        r.close(&mut discard);
                        r.phase = "failed";
                        r.operation = Some(operation);
                        let error = failure(error);
                        r.error = Some(error.clone());
                        if reading {
                            Err(error)
                        } else {
                            r.status()
                        }
                    }
                }
            };
            parent.job = None;
            result
        });
        self.clear_cancellation(epoch, operation);
        // Terminal cleanup after retirement/poison never publishes private data.
        {
            let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
            if state.job.as_ref().is_some_and(|j| {
                j.kind == JobKind::ComparisonRead && j.epoch == epoch && j.id == operation
            }) {
                state.job = None;
            }
        }
        if !lease.valid(epoch) {
            let mut state = self.comparison.lock().unwrap_or_else(|p| p.into_inner());
            if let Some(r) = state
                .records
                .get_mut(client)
                .filter(|r| r.epoch == epoch && r.operation == Some(operation))
            {
                r.running = false;
                r.close(&mut discard);
            }
        }
        drop(outcome);
        drop(discard);
        answer
    }
}

#[cfg(test)]
mod literal_read_review;
#[cfg(test)]
mod scene_read_review;
#[cfg(test)]
mod tests;
