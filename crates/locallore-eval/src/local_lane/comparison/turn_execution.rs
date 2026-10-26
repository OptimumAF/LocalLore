//! One actual Host/Store/provider/watchdog path for the closed comparison arms.
//! Checkpoint writers retain protocol-specific codecs; reservations are settled
//! only through checkpoint_and_settle after the checkpoint is durable.
use super::*;
use locallore::host::HostPlayConstructionV1;

pub(super) struct LiveTurnJob<'a> {
    pub dir: &'a Path,
    pub path: &'a Path,
    pub index: usize,
    pub step: &'a protocol::Step,
    pub factory: &'a LaneFactory,
    pub cancel: &'a Cancellation,
    pub construction: HostPlayConstructionV1,
    pub before: Engine,
    pub profile: PlayProfile,
}

pub(super) struct ActualTurn {
    pub before: Engine,
    pub after: Engine,
    pub request: Request,
    pub receipt: Option<Receipt>,
    pub phase: String,
    pub error: Option<String>,
    pub recording: RecordingFile,
    pub capture: Option<Value>,
    pub trace: Option<Value>,
    pub admission: usize,
    pub elapsed_ms: u64,
    pub first_final_response_ms: Option<u64>,
    pub commit_elapsed_ms: Option<u64>,
    pub profile: PlayProfile,
    pub capture_file: Option<String>,
    pub recording_file: String,
    owned: OwnedHost,
    session: String,
}
impl ActualTurn {
    pub(super) fn checkpoint_and_settle<T: Serialize>(
        &self,
        dir: &Path,
        index: usize,
        checkpoint: &T,
        ledger: &mut Ledger,
    ) -> Result<()> {
        saved(&checkpoint_path(dir, index), checkpoint, 256 * 1024)?;
        ledger.settle(self.admission, self.elapsed_ms, self.recording.roles)?;
        call(
            &self.owned.0,
            json!({"op":"trace_capture_revoke","session":self.session,"scope":self.before.scope()}),
        );
        self.owned.0.close_all();
        Ok(())
    }
}

pub(super) fn execute(job: LiveTurnJob<'_>, ledger: &mut Ledger) -> Result<ActualTurn> {
    let LiveTurnJob {
        dir,
        path,
        index,
        step,
        factory,
        cancel,
        construction,
        before,
        profile,
    } = job;
    if cancel.is_cancelled() {
        return Err("Interrupted".into());
    }
    let admission = ledger.admit(&format!("scene-{}", step.scene()), step.id())?;
    let started = Instant::now();
    let host = Arc::new(locallore_workspace::open(path, true).map_err(|_| "Workspace")?);
    let _owned = OwnedHost(host.clone());
    let session = resume_session(&host, before.scope())?;
    for command in [
        json!({"op":"trace_configure","session":session,"scope":before.scope(),"expected_head":before.revision(),"enabled":true}),
        json!({"op":"trace_capture_configure","session":session,"scope":before.scope(),"expected_head":before.revision(),"enabled":true,"consent":true}),
    ] {
        if call(&host, command)["status"] != "ok" {
            return Err("CaptureConsent".into());
        }
    }
    let proposal = protocol::reference_proposal(&before, step).ok();
    let commands = match step.expected() {
        protocol::Expected::Accepted(command) => vec![command.clone()],
        protocol::Expected::GuardRejected(_) => vec![],
    };
    let narration = proposal
        .as_ref()
        .and_then(|p| before.preview(&request, p).ok())
        .map_or_else(|| "No outcome.".into(), |p| p.narration().to_owned());
    let spec = LocalStep {
        id: step.id().into(),
        branch: before.scope().branch.clone(),
        kind: step.kind(),
        text: step.text().into(),
        error: None,
        commands,
        narration,
        prohibited_narration: vec!["SECRET-TIDE-731".into()],
        cancel: false,
        prompt_targets: vec![],
        assertions: vec![],
    };
    let recording = Arc::new(Recording::default());
    let make = factory.clone();
    let observed = recording.clone();
    let director = EXCLUSIONS.iter().map(|s| (*s).into()).collect::<Vec<_>>();
    let mut narrator = director.clone();
    narrator.push("SECRET-TIDE-731".into());
    let forbidden = ForbiddenByRole { director, narrator };
    let provider = Arc::new(move || make.provider(&spec, observed.clone(), forbidden.clone()));
    if factory.native() {
        host.configure_local_provider_with_construction(profile.clone(), provider, construction)
    } else {
        host.configure_fixture_provider_with_construction(profile.clone(), provider, construction)
    }
    .map_err(|_| "Profile")?;
    let mut reply = call(
        &host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    let active_remaining = MAX_ACTIVE_MS.saturating_sub(
        ledger
            .charged_ms
            .saturating_sub(TURN_MS)
            .max(ledger.prior_ms.saturating_add(ledger.elapsed())),
    );
    let deadline = turn_deadline(started, Instant::now(), active_remaining);
    let (stop, stopped) = std::sync::mpsc::sync_channel(1);
    let watch_host = host.clone();
    let sid = session.clone();
    let watch = request.clone();
    let external = cancel.clone();
    let watchdog = DeadlineGuard {
        stop,
        worker: Some(
            std::thread::Builder::new()
                .name("locallore-comparison-deadline".into())
                .spawn(move || loop {
                    if external.is_cancelled() || Instant::now() >= deadline {
                        op(&watch_host, &sid, &watch.scope, &watch.turn, "cancel");
                        break;
                    }
                    match stopped.recv_timeout(Duration::from_millis(5)) {
                        Ok(()) | Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => break,
                        Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
                    }
                })
                .map_err(|_| "Watchdog")?,
        ),
    };
    if reply["data"]["phase"] == "queued" {
        // A slow prelude cannot admit a model role after the absolute deadline.
        reply = op(
            &host,
            &session,
            before.scope(),
            step.id(),
            if cancel.is_cancelled() || Instant::now() >= deadline {
                "cancel"
            } else {
                "prepare"
            },
        );
    }
    if cancel.is_cancelled() || Instant::now() >= deadline {
        reply = op(&host, &session, before.scope(), step.id(), "cancel");
    }
    let (capture, trace) = private_read(&host, &session, &before, &request);
    let recorded = captured_recording(dir, admission, &recording)?;
    validate_recording(dir, admission, &recorded)?;
    let capture_file = capture
        .as_ref()
        .map(|capture| -> Result<String> {
            let name = evidence_name(index, admission, "capture");
            saved(&dir.join(&name), capture, v2::MAX_PRIVATE_CAPTURE + 4096)?;
            Ok(name)
        })
        .transpose()?;
    let recording_file = evidence_name(index, admission, "recording");
    saved(&dir.join(&recording_file), &recorded, 64 * 1024)?;
    if cancel.is_cancelled() || Instant::now() >= deadline {
        reply = op(&host, &session, before.scope(), step.id(), "cancel");
    }
    let mut commit_elapsed_ms = None;
    if reply["data"]["phase"] == "ready" {
        let committed = Instant::now();
        reply = op(&host, &session, before.scope(), step.id(), "commit");
        commit_elapsed_ms = Some(committed.elapsed().as_millis().min(u64::MAX as u128) as u64);
    }
    let response_ms = started.elapsed().as_millis().min(u64::MAX as u128) as u64;
    watchdog.finish()?;
    // Exact durable outcome wins over an acknowledgment error or late cancel.
    let mut actual = Store::open_read_only(path).map_err(|_| "Workspace")?;
    let stored = actual.lookup_turn(before.scope(), step.id()).ok();
    let receipt = stored.as_ref().and_then(|s| s.receipt.as_ref());
    let after = actual.resume(before.scope()).map_err(|_| "Replay")?.engine;
    let phase = if receipt.is_some() {
        "committed".to_owned()
    } else if reply["status"] == "rejected" {
        "rejected".into()
    } else {
        reply["data"]["phase"]
            .as_str()
            .ok_or("TransportUnknown")?
            .to_owned()
    };
    let error = if receipt.is_some() {
        None
    } else if reply["status"] == "rejected" {
        reply["error"].as_str().map(str::to_owned)
    } else {
        reply["data"]["error"].as_str().map(str::to_owned)
    };
    if !matches!(
        phase.as_str(),
        "committed" | "failed" | "cancelled" | "rejected" | "stale"
    ) {
        return Err("TransportUnknown".into());
    }
    let first_final_response_ms = Some(
        if reply["data"]["phase"] == "committed"
            || reply["status"] == "rejected"
            || matches!(
                reply["data"]["phase"].as_str(),
                Some("failed" | "cancelled" | "stale")
            )
        {
            response_ms
        } else {
            started.elapsed().as_millis().min(u64::MAX as u128) as u64
        },
    );
    let committed_trace = call(
        &host,
        json!({"op":"trace_read","session":session,"scope":request.scope,"expected_head":after.revision(),"base_revision":request.expected_revision,"observer":{"kind":"player"},"turn":request.turn,"attempt":null}),
    );
    let trace = if committed_trace["status"] == "ok" {
        Some(committed_trace["data"]["snapshot"].clone())
    } else {
        trace
    };
    let elapsed = started.elapsed().as_millis().min(u64::MAX as u128) as u64;
    Ok(ActualTurn {
        receipt: receipt.cloned(),
        before,
        after,
        request,
        phase,
        error,
        recording: recorded,
        capture,
        trace,
        admission,
        elapsed_ms: elapsed,
        first_final_response_ms,
        commit_elapsed_ms,
        profile,
        capture_file,
        recording_file,
        owned: _owned,
        session,
    })
}

// Closed native facts extracted from a protocol-specific decoded checkpoint.
// Shared validation retains actual Store outcome/request/receipt edges, ledger
// reservations and raw-file integrity before either version rebuilds its row.
pub(super) struct CheckpointMeta {
    pub request: Request,
    pub before_head: u64,
    pub after_head: u64,
    pub capture_file: Option<String>,
    pub recording_file: Option<String>,
    pub row: CheckpointRowMeta,
}
pub(super) struct CheckpointRowMeta {
    pub admission: Option<usize>,
    pub elapsed_ms: u64,
    pub roles_known: bool,
    pub roles: usize,
    pub phase: String,
}
pub(super) struct CheckpointEvidence {
    pub before: Engine,
    pub after: Engine,
    pub receipt: Option<Receipt>,
    pub recording: Option<RecordingFile>,
    pub capture: Option<Value>,
}
pub(super) fn load_evidence(
    dir: &Path,
    path: &Path,
    index: usize,
    key: &str,
    stored: &CheckpointMeta,
) -> Result<CheckpointEvidence> {
    let corpus = suite()?;
    let step = &corpus.steps()[index];
    let full = engine(path, &corpus.seed().scope)?;
    let before = full.at_revision(stored.before_head).map_err(|_| "Replay")?;
    let after = full.at_revision(stored.after_head).map_err(|_| "Replay")?;
    if stored.request != step.request(&before) {
        return Err("CheckpointMismatch".into());
    }
    if let Some(admission) = stored.row.admission {
        if admission >= MAX_ADMISSIONS {
            return Err("LedgerIntegrity".into());
        }
        let reservation: Reservation =
            decode(&dir.join(format!("admission-{admission:02}.json")), 4096)?;
        if reservation.version != 1
            || reservation.binding != key
            || reservation.index != admission
            || reservation.story != format!("scene-{}", step.scene())
            || reservation.turn != step.id()
            || reservation.ms != TURN_MS
            || reservation.roles != 3
        {
            return Err("LedgerIntegrity".into());
        }
        let path = dir.join(format!("admission-{admission:02}-settled.json"));
        ordinary(&path)?;
        if path.exists() {
            let settled: Settlement = decode(&path, 4096)?;
            if settled.version != 1
                || settled.binding != key
                || settled.index != admission
                || settled.ms != stored.row.elapsed_ms
                || !stored.row.roles_known
                || settled.roles != stored.row.roles
            {
                return Err("LedgerIntegrity".into());
            }
        }
    } else if stored.recording_file.is_some() || stored.capture_file.is_some() {
        return Err("LedgerIntegrity".into());
    }
    // A diagnostic checkpoint cannot hide a real commit or relabel the Store's
    // terminal result. This validator is shared by source and selected readers.
    let actual = match Store::open_read_only(path)
        .map_err(|_| "Workspace")?
        .lookup_turn(before.scope(), step.id())
    {
        Ok(record) => Some(record),
        Err(locallore_storage::TurnError::UnknownTurn) => None,
        Err(_) => return Err("Lookup".into()),
    };
    let phase_agrees = match actual.as_ref().map(|record| record.phase) {
        Some(locallore_storage::TurnPhase::Committed) => stored.row.phase == "committed",
        Some(locallore_storage::TurnPhase::Failed) => {
            matches!(stored.row.phase.as_str(), "failed" | "rejected")
        }
        Some(locallore_storage::TurnPhase::Cancelled) => stored.row.phase == "cancelled",
        Some(locallore_storage::TurnPhase::Stale) => stored.row.phase == "stale",
        Some(locallore_storage::TurnPhase::Draft) => false,
        None => matches!(
            stored.row.phase.as_str(),
            "failed" | "rejected" | "cancelled" | "stale" | "not_run_dependency"
        ),
    };
    if !phase_agrees
        || actual
            .as_ref()
            .is_some_and(|record| record.request != stored.request)
        || (stored.row.phase != "committed" && stored.before_head != stored.after_head)
    {
        return Err("CheckpointOutcomeMismatch".into());
    }
    let receipt = actual.and_then(|record| record.receipt);
    if stored.row.phase == "committed" {
        let receipt = receipt.as_ref().ok_or("Lookup")?;
        if receipt.request().expected_revision != stored.before_head
            || receipt.events().last().map(|event| event.sequence()) != Some(stored.after_head)
        {
            return Err("CheckpointOutcomeMismatch".into());
        }
    } else if receipt.is_some() {
        return Err("CheckpointOutcomeMismatch".into());
    }
    let recording = stored
        .recording_file
        .as_ref()
        .map(|name| -> Result<RecordingFile> {
            let a = stored.row.admission.ok_or("RecordingIntegrity")?;
            if a >= MAX_ADMISSIONS || *name != evidence_name(index, a, "recording") {
                return Err("RecordingIntegrity".into());
            }
            let r: RecordingFile = decode(&dir.join(name), 64 * 1024)?;
            validate_recording(dir, a, &r)?;
            Ok(r)
        })
        .transpose()?;
    let capture = stored
        .capture_file
        .as_ref()
        .map(|name| -> Result<Value> {
            let a = stored.row.admission.ok_or("CaptureBinding")?;
            if a >= MAX_ADMISSIONS || *name != evidence_name(index, a, "capture") {
                return Err("CaptureBinding".into());
            }
            decode(&dir.join(name), v2::MAX_PRIVATE_CAPTURE + 4096)
        })
        .transpose()?;
    Ok(CheckpointEvidence {
        before,
        after,
        receipt,
        recording,
        capture,
    })
}
