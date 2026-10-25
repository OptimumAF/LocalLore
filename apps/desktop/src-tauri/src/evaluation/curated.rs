//! Native-owned adapter over the single accepted curated runner. Never runs a CLI.
use super::*;
use crate::models::ModelManager;
use locallore_eval::local_lane::{self, desktop_api, LaneFactory, NativeAssets};
pub struct CuratedStart<'a> {
    pub client: &'a str,
    pub chosen_lane: &'a str,
    pub selection: Option<String>,
    pub batch: &'a str,
    pub consent: bool,
}
pub struct CuratedEvidenceRequest<'a> {
    pub token: &'a str,
    pub case: &'a str,
    pub turn: &'a str,
    pub binding: &'a str,
    pub observer: locallore::inspection_query::Observer,
    pub view: locallore::inspection_query::View,
}
type FreshRun = (String, String, Option<String>, String);
struct Admission {
    existing: Option<String>,
    fresh: Option<FreshRun>,
}
#[derive(Default)]
pub(super) struct CuratedState {
    pub(super) runs: BTreeMap<String, CuratedRun>,
}
pub(super) struct CuratedRun {
    metadata: Value,
    snapshot: Option<Value>,
    pub(super) phase: String,
    error: Option<String>,
}
fn lane(value: &str) -> Result<()> {
    if matches!(value, "scripted" | "native") {
        Ok(())
    } else {
        Err("InvalidEvaluationInput".into())
    }
}
fn selected(value: Option<&str>) -> Result<()> {
    if let Some(id) = value {
        if !desktop_api::catalog().map_err(category)?["cases"]
            .as_array()
            .ok_or("EvaluationInternal")?
            .iter()
            .any(|v| v["id"] == id)
        {
            return Err("UnknownEvaluationCase".into());
        }
    }
    Ok(())
}
fn failure(error: String) -> String {
    match error.as_str() {
        "CheckpointMismatch" => "EvaluationSourceMismatch",
        "CheckpointIntegrity" | "LedgerIntegrity" | "Profile" => "EvaluationIntegrity",
        "RunBusy" => "EvaluationBusy",
        "RunBudget" | "CaseBudget" | "ReportBudget" | "AttemptLimit" => "EvaluationBudget",
        "UnknownCase" => "UnknownEvaluationCase",
        "UnknownTurn" | "CheckpointNotReady" => "EvaluationNotReady",
        "Reparse" => "UnsafeEvaluationPath",
        e if e.starts_with("Runtime") => "EvaluationModelUnavailable",
        _ => "EvaluationIo",
    }
    .into()
}
impl EvaluationManager {
    pub(super) fn curated_root(&self) -> PathBuf {
        self.root.with_file_name("curated-evaluations")
    }
    fn curated_lock(&self) -> Result<std::sync::MutexGuard<'_, CuratedState>> {
        self.curated.lock().map_err(|_| "EvaluationInternal".into())
    }
    pub fn curated_catalog(&self, lease: &WindowLease, epoch: u64) -> Result<Value> {
        self.catalog(lease, epoch)?;
        let _registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
        let root = self.curated_root();
        let _parent = pin(root.parent().ok_or("EvaluationIo")?)?;
        fs::create_dir_all(&root).map_err(|_| "EvaluationIo")?;
        let _pins = pin(&root)?;
        let mut found = vec![];
        let mut clients = std::collections::BTreeSet::new();
        for item in fs::read_dir(&root).map_err(|_| "EvaluationIo")? {
            let entry = item.map_err(|_| "EvaluationIo")?;
            let id = entry.file_name().to_string_lossy().into_owned();
            if !valid_id(&id) || found.len() >= 32 {
                return Err("EvaluationIntegrity".into());
            }
            let _pins = pin(&entry.path())?;
            let pins = pin(&entry.path().join("curated.json"))?;
            let file = pins.last().ok_or("EvaluationIo")?;
            if !file.metadata().map_err(|_| "EvaluationIo")?.is_file()
                || file.metadata().map_err(|_| "EvaluationIo")?.len() > 4096
            {
                return Err("EvaluationIntegrity".into());
            }
            use std::io::Read;
            let mut data = vec![];
            file.take(4097)
                .read_to_end(&mut data)
                .map_err(|_| "EvaluationIo")?;
            let metadata: Value =
                serde_json::from_slice(&data).map_err(|_| "EvaluationIntegrity")?;
            let client = metadata["client_id"]
                .as_str()
                .filter(|s| valid_id(s))
                .ok_or("EvaluationIntegrity")?;
            if metadata["version"] != 1
                || metadata["run_id"] != id
                || !clients.insert(client.to_owned())
                || !metadata["created"].is_u64()
                || !metadata["source_binding"]
                    .as_str()
                    .is_some_and(|h| h.len() == 64 && h.bytes().all(|c| c.is_ascii_hexdigit()))
            {
                return Err("EvaluationIntegrity".into());
            }
            lane(metadata["lane"].as_str().ok_or("EvaluationIntegrity")?)?;
            let choice = metadata["selection"].as_str();
            if !metadata["selection"].is_null() && choice.is_none() {
                return Err("EvaluationIntegrity".into());
            }
            selected(choice)?;
            found.push((id, metadata));
        }
        lease.dispatch(epoch,||{let mut state=self.curated_lock()?;for(id,metadata)in found {
            if let Some(run)=state.runs.get(&id){if run.metadata!=metadata{return Err("EvaluationIntegrity".into())}}
            state.runs.entry(id).or_insert(CuratedRun{metadata,snapshot:None,phase:"retained".into(),error:None});
        }
        Ok(json!({"version":1,"cases":desktop_api::catalog().map_err(failure)?["cases"],"runs":state.runs.values().map(|r|&r.metadata).collect::<Vec<_>>(),"location":root,
            "caps":desktop_api::catalog().map_err(failure)?["limits"],"approved_profile":desktop_api::catalog().map_err(failure)?["approved_profile"],"retention":"Private immutable checkpoints/raw output remain; no automatic deletion."}))})
    }
    fn curated_run(&self, lease: &WindowLease, epoch: u64, token: &str) -> Result<String> {
        lease.dispatch(epoch, || {
            let mut state = self.state()?;
            Self::token(&mut state, epoch, token)
        })
    }
    pub(super) fn curated_snapshot(&self, epoch: u64, id: &str, token: &str) -> Result<Value> {
        let state = self.state()?;
        let job = state
            .job
            .as_ref()
            .filter(|j| j.epoch == epoch && j.run == id);
        let curated = self.curated_lock()?;
        let run = curated.runs.get(id).ok_or("UnknownEvaluationRun")?;
        Ok(
            json!({"version":1,"run_token":token,"run_id":id,"operation_id":job.map(|j|j.id),"running":job.is_some(),"phase":run.phase,"error":run.error,
            "completed_cases":run.snapshot.as_ref().map(|s|&s["checkpointed_stories"]).cloned().unwrap_or(json!(0)),"completed":run.snapshot.as_ref().is_some_and(|s|s["completed"]==true),
            "lane":run.metadata["lane"],"client_id":run.metadata["client_id"],"source_binding":run.metadata["source_binding"],"snapshot":run.snapshot}),
        )
    }
    pub fn curated_status(&self, lease: &WindowLease, epoch: u64, token: &str) -> Result<Value> {
        let id = self.curated_run(lease, epoch, token)?;
        lease.dispatch(epoch, || self.curated_snapshot(epoch, &id, token))
    }
    pub fn curated_lookup(&self, lease: &WindowLease, epoch: u64, client: &str) -> Result<Value> {
        if !valid_id(client) {
            return Err("InvalidEvaluationInput".into());
        }
        self.curated_catalog(lease, epoch)?;
        let id = self
            .curated_lock()?
            .runs
            .iter()
            .find(|(_, r)| r.metadata["client_id"] == client)
            .map(|(id, _)| id.clone())
            .ok_or("UnknownEvaluationRun")?;
        self.curated_open(lease, epoch, &id)
    }
    pub fn curated_open(&self, lease: &WindowLease, epoch: u64, id: &str) -> Result<Value> {
        if !valid_id(id) {
            return Err("InvalidEvaluationInput".into());
        }
        self.curated_catalog(lease, epoch)?;
        let token = lease.dispatch(epoch, || {
            let mut state = self.state()?;
            if !self.curated_lock()?.runs.contains_key(id) {
                return Err("UnknownEvaluationRun".into());
            }
            Self::mint(&mut state, epoch, id.to_owned())
        })?;
        let active = self.state()?.job.as_ref().is_some_and(|j| j.run == id);
        if !active {
            let path = self.curated_root().join(id);
            let _pins = pin(&path)?;
            let work = path.join("work");
            if work.join("run.json").exists() {
                let _pins = pin(&work)?;
                let snapshot = desktop_api::inspect(&work).map_err(failure)?;
                if snapshot["binding_sha256"]
                    != self
                        .curated_lock()?
                        .runs
                        .get(id)
                        .ok_or("UnknownEvaluationRun")?
                        .metadata["source_binding"]
                {
                    return Err("EvaluationIntegrity".into());
                }
                lease.dispatch(epoch, || {
                    let mut runs = self.curated_lock()?;
                    let r = runs.runs.get_mut(id).ok_or("UnknownEvaluationRun")?;
                    r.phase = if snapshot["completed"] == true {
                        "completed"
                    } else {
                        "paused"
                    }
                    .into();
                    r.snapshot = Some(snapshot);
                    Ok(())
                })?;
            }
        }
        lease.dispatch(epoch, || self.curated_snapshot(epoch, id, &token))
    }
    pub fn curated_start(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        models: Arc<ModelManager>,
        request: CuratedStart<'_>,
    ) -> Result<Value> {
        let CuratedStart {
            client,
            chosen_lane,
            selection,
            batch,
            consent,
        } = request;
        if !valid_id(client) || !matches!(batch, "one" | "all") {
            return Err("InvalidEvaluationInput".into());
        }
        lane(chosen_lane)?;
        selected(selection.as_deref())?;
        if chosen_lane == "native" && !consent {
            return Err("InvalidEvaluationInput".into());
        }
        self.curated_catalog(lease, epoch)?;
        let prior = self
            .curated_lock()?
            .runs
            .iter()
            .find(|(_, r)| r.metadata["client_id"] == client)
            .map(|(id, r)| (id.clone(), r.metadata.clone()));
        if let Some((id, metadata)) = prior {
            if metadata["lane"] != chosen_lane
                || metadata["selection"] != json!(selection)
                || metadata["batch"] != batch
            {
                return Err("InvalidEvaluationInput".into());
            }
            return self.curated_open(lease, epoch, &id);
        }
        self.curated_admit(
            lease,
            epoch,
            models,
            Admission {
                existing: None,
                fresh: Some((
                    client.to_owned(),
                    chosen_lane.to_owned(),
                    selection,
                    batch.to_owned(),
                )),
            },
            batch,
            consent,
        )
    }
    pub fn curated_resume(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        models: Arc<ModelManager>,
        token: &str,
        batch: &str,
        consent: bool,
    ) -> Result<Value> {
        if !matches!(batch, "one" | "all") {
            return Err("InvalidEvaluationInput".into());
        }
        let id = self.curated_run(lease, epoch, token)?;
        let opened = self.curated_open(lease, epoch, &id)?;
        if opened["running"] == true {
            return Err("EvaluationBusy".into());
        }
        if opened["snapshot"]["resume_compatible"] == false {
            return Err("EvaluationSourceMismatch".into());
        }
        if opened["completed"] == true {
            return Ok(opened);
        }
        self.curated_admit(
            lease,
            epoch,
            models,
            Admission {
                existing: Some(id),
                fresh: None,
            },
            batch,
            consent,
        )
    }
    fn curated_admit(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        models: Arc<ModelManager>,
        admission: Admission,
        batch: &str,
        consent: bool,
    ) -> Result<Value> {
        let Admission { existing, fresh } = admission;
        loop {
            let registration = self.registration.lock().map_err(|_| "EvaluationInternal")?;
            if self.state()?.job.is_some() {
                return Err("EvaluationBusy".into());
            }
            if let Some((client, lane, selection, original_batch)) = &fresh {
                let prior = self
                    .curated_lock()?
                    .runs
                    .iter()
                    .find(|(_, r)| r.metadata["client_id"] == *client)
                    .map(|(id, r)| (id.clone(), r.metadata.clone()));
                if let Some((id, metadata)) = prior {
                    if metadata["lane"] != *lane
                        || metadata["selection"] != json!(selection)
                        || metadata["batch"] != *original_batch
                    {
                        return Err("InvalidEvaluationInput".into());
                    }
                    drop(registration);
                    return self.curated_open(lease, epoch, &id);
                }
            }
            let old = self.worker.lock().map_err(|_| "EvaluationInternal")?.take();
            if let Some((_, handle)) = old {
                drop(registration);
                handle.join().map_err(|_| "EvaluationInternal")?;
                continue;
            }
            self.budget(None)?;
            let id = if let Some(id) = existing.clone() {
                id
            } else {
                lease.dispatch(epoch,||{let(client,lane,selection,original_batch)=fresh.clone().ok_or("InvalidEvaluationInput")?;
                let mut runs=self.curated_lock()?;if runs.runs.len()>=32{return Err("EvaluationRunLimit".into())}
                let id=uuid()?;let path=self.curated_root().join(&id);let _parent=pin(&self.curated_root())?;
                fs::create_dir(&path).map_err(|_|"EvaluationIo")?;let _pins=pin(&path)?;
                let source_binding=desktop_api::request_binding(lane=="native",selection.as_deref()).map_err(failure)?;
                let metadata=json!({"version":1,"run_id":id,"client_id":client,"lane":lane,"selection":selection,"batch":original_batch,"source_binding":source_binding,"created":SystemTime::now().duration_since(UNIX_EPOCH).map_err(|_|"EvaluationIo")?.as_millis() as u64});
                let bytes=serde_json::to_vec(&metadata).map_err(|_|"EvaluationInternal")?;
                let mut f=OpenOptions::new().create_new(true).write(true).open(path.join("curated.json")).map_err(|_|"EvaluationIo")?;f.write_all(&bytes).and_then(|_|f.sync_all()).map_err(|_|"EvaluationIo")?;
                runs.runs.insert(id.clone(),CuratedRun{metadata,snapshot:None,phase:"starting".into(),error:None});Ok(id)})?
            };
            let metadata = self
                .curated_lock()?
                .runs
                .get(&id)
                .ok_or("UnknownEvaluationRun")?
                .metadata
                .clone();
            let native = metadata["lane"] == "native";
            if metadata["source_binding"]
                != desktop_api::request_binding(native, metadata["selection"].as_str())
                    .map_err(failure)?
            {
                return Err("EvaluationSourceMismatch".into());
            }
            if native && !consent {
                return Err("InvalidEvaluationInput".into());
            }
            let reservation = if native {
                Some(models.reserve_evaluation().map_err(|e| {
                    if e == "Busy" || e == "ModelLoaded" {
                        "EvaluationModelBusy".to_owned()
                    } else {
                        "EvaluationInternal".to_owned()
                    }
                })?)
            } else {
                None
            };
            let (token, operation, cancel) = lease.dispatch(epoch, || {
                let mut state = self.state()?;
                let token = Self::mint(&mut state, epoch, id.clone())?;
                state.next = state
                    .next
                    .checked_add(1)
                    .filter(|n| *n <= 9_007_199_254_740_991)
                    .ok_or("EvaluationBudget")?;
                let operation = state.next;
                let cancel = Cancellation::default();
                state.job = Some(Job {
                    kind: JobKind::Curated,
                    epoch,
                    id: operation,
                    run: id.clone(),
                    cancel: cancel.clone(),
                });
                self.register_cancellation(lease, epoch, operation, &cancel);
                Ok((token, operation, cancel))
            })?;
            {
                let mut runs = self.curated_lock()?;
                let run = runs.runs.get_mut(&id).ok_or("UnknownEvaluationRun")?;
                run.phase = "running".into();
                run.error = None;
            }
            let manager = self.clone();
            let owner = lease.clone();
            let run_id = id.clone();
            let max = if batch == "one" { 1 } else { 6 };
            let (start, registered) = std::sync::mpsc::channel();
            let work = move || {
                if registered.recv().is_err() {
                    return;
                }
                let result =
                    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| -> Result<Value> {
                        #[cfg(test)]
                        if manager
                            .panic_worker
                            .swap(false, std::sync::atomic::Ordering::SeqCst)
                        {
                            panic!("fixed curated worker panic")
                        }
                        #[cfg(any(test, feature = "dev-harness"))]
                        while manager.hold.load(std::sync::atomic::Ordering::SeqCst)
                            && !cancel.is_cancelled()
                            && owner.valid(epoch)
                        {
                            std::thread::sleep(Duration::from_millis(5));
                        }
                        if !owner.valid(epoch) {
                            return Err("Closed".into());
                        }
                        // Preserve Windows' extended absolute prefix for SQLite/WAL paths;
                        // the run directory is native-owned and pinned before this resolution.
                        let owned = manager.curated_root().join(&run_id);
                        let _owned_pins = pin(&owned)?;
                        let path = fs::canonicalize(&owned).map_err(|_| "EvaluationIo")?;
                        let _pins = pin(&path)?;
                        manager.budget(Some(&path))?;
                        let directory = path.join("work");
                        let resume = directory.join("run.json").exists();
                        let selected = metadata["selection"].as_str();
                        if native {
                            let assets = reservation.as_ref().ok_or("EvaluationInternal")?;
                            local_lane::run_native_curated(
                                &directory,
                                resume,
                                selected,
                                &cancel,
                                max,
                                NativeAssets {
                                    resource_dir: &assets.resource,
                                    model: &assets.model,
                                },
                            )
                            .map_err(|error| {
                                #[cfg(test)]
                                eprintln!("curated native runner: {error}");
                                failure(error)
                            })?;
                        } else {
                            local_lane::run_curated(
                                &directory,
                                resume,
                                selected,
                                &cancel,
                                max,
                                LaneFactory::ScriptedBaseline,
                            )
                            .map_err(|error| {
                                #[cfg(test)]
                                eprintln!("curated scripted runner: {error}");
                                failure(error)
                            })?;
                        }
                        manager.budget(Some(&path))?;
                        desktop_api::inspect(&directory).map_err(failure)
                    }))
                    .unwrap_or_else(|_| Err("EvaluationInternal".into()));
                drop(reservation);
                let _ = owner.dispatch(epoch, || {
                    let mut runs = manager.curated_lock()?;
                    if let Some(run) = runs.runs.get_mut(&run_id) {
                        match &result {
                            Ok(snapshot) => {
                                run.phase = if snapshot["completed"] == true {
                                    "completed"
                                } else {
                                    "paused"
                                }
                                .into();
                                run.snapshot = Some(snapshot.clone());
                                run.error = None;
                            }
                            Err(e) => {
                                run.phase = "error".into();
                                run.error = Some(e.clone());
                            }
                        }
                    }
                    Ok(())
                });
                manager.clear_cancellation(epoch, operation);
                let mut state = manager.state.lock().unwrap_or_else(|p| p.into_inner());
                if state
                    .job
                    .as_ref()
                    .is_some_and(|j| j.id == operation && j.epoch == epoch)
                {
                    state.job = None;
                }
                if !owner.valid(epoch) {
                    if let Some(run) = manager
                        .curated
                        .lock()
                        .unwrap_or_else(|p| p.into_inner())
                        .runs
                        .get_mut(&run_id)
                    {
                        run.phase = "retained".into();
                    }
                }
            };
            #[cfg(test)]
            let failed = self
                .fail_spawn
                .swap(false, std::sync::atomic::Ordering::SeqCst);
            #[cfg(not(test))]
            let failed = false;
            let spawned = if failed {
                Err(std::io::Error::other("fixed curated spawn refusal"))
            } else {
                std::thread::Builder::new()
                    .name("locallore-curated-evaluation".into())
                    .spawn(work)
            };
            match spawned {
                Ok(handle) => {
                    *self.worker.lock().map_err(|_| "EvaluationInternal")? = Some((epoch, handle));
                    let _ = start.send(());
                }
                Err(_) => {
                    self.clear_cancellation(epoch, operation);
                    self.state()?.job = None;
                    let mut runs = self.curated_lock()?;
                    let run = runs.runs.get_mut(&id).ok_or("EvaluationInternal")?;
                    run.phase = "error".into();
                    run.error = Some("EvaluationInternal".into());
                    return Err("EvaluationInternal".into());
                }
            }
            drop(registration);
            return lease.dispatch(epoch, || self.curated_snapshot(epoch, &id, &token));
        }
    }
    pub fn curated_evidence(
        &self,
        lease: &WindowLease,
        epoch: u64,
        request: CuratedEvidenceRequest<'_>,
    ) -> Result<Value> {
        let CuratedEvidenceRequest {
            token,
            case,
            turn,
            binding,
            observer,
            view,
        } = request;
        let id = self.curated_run(lease, epoch, token)?;
        let path = self.curated_root().join(&id);
        let _pins = pin(&path)?;
        let _pins = pin(&path.join("work"))?;
        let result = desktop_api::evidence(&path.join("work"), binding, case, turn, observer, view)
            .map_err(failure)?;
        lease.dispatch(epoch, || {
            Ok(json!({"version":1,"run_token":token,"run_id":id,"evidence":result}))
        })
    }
}

#[cfg(test)]
mod tests;
