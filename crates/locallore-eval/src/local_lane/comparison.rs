//! Current-policy comparison over the existing Host, Store, provider and ledger.
use super::*;
pub use crate::memory_comparison_v2::{ComparisonKind, ComparisonReportV2};
use crate::{
    memory_comparison as protocol,
    memory_comparison_v2::{
        self as v2, CapturedContext, CurrentBinding, ReferenceReportV2, TurnReportV2,
    },
};
use locallore::context_compiler::ContextPolicy;

const ARM_NAMES: [&str; 2] = ["left", "right"];
const POLICIES: [ContextPolicy; 2] = [
    ContextPolicy::StateRecentTranscriptV1,
    ContextPolicy::StateRelevantMemoryV1,
];
const EXCLUSIONS: [&str; 3] = [
    "FOREIGN-COMPARISON",
    "SIBLING-COMPARISON",
    "PARENT-FUTURE-COMPARISON",
];

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RunManifest {
    version: u16,
    source_sha256: String,
    binding: CurrentBinding,
    profile: PlayProfile,
    kind: ComparisonKind,
    reference_sha256: Option<String>,
    order: String,
}
impl RunManifest {
    fn new(
        kind: ComparisonKind,
        profile: PlayProfile,
        native: bool,
        reference_sha256: Option<String>,
    ) -> Result<Self> {
        let binding = v2::current_binding(native)?;
        Ok(Self {
            version: 2,
            source_sha256: binding.source_sha256.clone(),
            binding,
            profile,
            kind,
            reference_sha256,
            order: "alternate-first-v1".into(),
        })
    }
    fn stable_key(&self) -> Result<String> {
        // A historical source label is display-only. It cannot authorize resume.
        let mut value = serde_json::to_value(self).map_err(|_| "Encoding")?;
        value
            .as_object_mut()
            .ok_or("Binding")?
            .remove("source_sha256");
        value["binding"]
            .as_object_mut()
            .ok_or("Binding")?
            .remove("source_sha256");
        Ok(digest(&encode(&value)?))
    }
    fn source_matches(&self) -> Result<bool> {
        let current = v2::current_binding(self.binding.native)?;
        Ok(self.source_sha256 == current.source_sha256 && self.binding == current)
    }
    fn validate(&self) -> Result<()> {
        let mut current = Self::new(
            self.kind,
            self.profile.clone(),
            self.binding.native,
            self.reference_sha256.clone(),
        )?;
        // Historical absent estimates remain viewable under their original
        // stable key. source_matches still refuses executing that old source.
        match self.binding.forwarded_budget_version {
            None => current.binding.forwarded_budget_version = None,
            Some(1) => {}
            Some(_) => return Err("ComparisonBinding".into()),
        }
        if self.version != 2
            || self.stable_key() != current.stable_key()
            || !hex(&self.source_sha256)
            || !hex(&self.binding.source_sha256)
        {
            return Err("ComparisonBinding".into());
        }
        self.profile.validate().map_err(|_| "Profile")?;
        if self.profile.context_tokens != 4096
            || self.profile.director_tokens != 350
            || self.profile.narrator_tokens != 350
            || self.profile.deadline_ms != 120000
            || self.profile.repair_limit != 1
        {
            return Err("Profile".into());
        }
        Ok(())
    }
}
fn hex(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
}
fn suite() -> Result<protocol::FrozenSuite> {
    protocol::frozen_suite().map_err(|_| "Suite".into())
}
fn decode<T: serde::de::DeserializeOwned>(p: &Path, cap: usize) -> Result<T> {
    serde_json::from_slice(&read(p, cap)?).map_err(|_| "CheckpointMalformed".into())
}
fn saved<T: Serialize>(p: &Path, value: &T, cap: usize) -> Result<()> {
    ordinary(p)?;
    let bytes = encode(value)?;
    if bytes.len() > cap {
        return Err("CheckpointBudget".into());
    }
    write_new(p, &bytes)
}
fn take_lock(dir: &Path) -> Result<File> {
    ordinary(&dir.join("run.lock"))?;
    let lock = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(dir.join("run.lock"))
        .map_err(|_| "Io")?;
    lock.try_lock().map_err(|_| "RunBusy")?;
    Ok(lock)
}
fn database(dir: &Path, index: usize, kind: ComparisonKind) -> PathBuf {
    dir.join(match kind {
        ComparisonKind::ContinuousRollout => "synthetic.sqlite".into(),
        ComparisonKind::PairedSnapshots => format!("pair-{index:02}.sqlite"),
    })
}
fn ensure_database(path: &Path, seed: &Seed, prefix: &[Receipt]) -> Result<()> {
    ordinary(path)?;
    let mut store = Store::open_application(path).map_err(|_| "Workspace")?;
    if store.stories().map_err(|_| "Workspace")?.is_empty() {
        store
            .create_story("Synthetic comparison", seed.clone())
            .map_err(|_| "Workspace")?;
    }
    let engine = store.resume(&seed.scope).map_err(|_| "Replay")?.engine;
    if engine.domain_version() != 1 || engine.seed() != seed {
        return Err("ComparisonBinding".into());
    }
    if engine.receipts().len() < prefix.len() {
        if engine.receipts() != &prefix[..engine.receipts().len()] {
            return Err("ReferencePrefix".into());
        }
        for receipt in &prefix[engine.receipts().len()..] {
            store
                .begin_turn(receipt.request())
                .map_err(|_| "ReferencePrefix")?;
            store
                .commit_prepared(receipt)
                .map_err(|_| "ReferencePrefix")?;
        }
    }
    let engine = store.resume(&seed.scope).map_err(|_| "Replay")?.engine;
    if engine.receipts().len() < prefix.len() || &engine.receipts()[..prefix.len()] != prefix {
        return Err("ReferencePrefix".into());
    }
    Ok(())
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RecordingFile {
    version: u16,
    captures: Vec<Capture>,
    raw: Vec<RawRef>,
    role_metrics: Option<Value>,
    roles: usize,
    lost: bool,
    forbidden_director_prompt: bool,
    forbidden_narrator_prompt: bool,
    forbidden_narrator_output: bool,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct StoredTurn {
    version: u16,
    binding: String,
    index: usize,
    arm: String,
    request: Request,
    before_head: u64,
    after_head: u64,
    row: TurnReportV2,
    capture_file: Option<String>,
    recording_file: Option<String>,
}
fn checkpoint_path(dir: &Path, index: usize) -> PathBuf {
    dir.join(format!("attempt-{index:02}.json"))
}
fn evidence_name(index: usize, admission: usize, suffix: &str) -> String {
    if index == admission {
        format!("attempt-{index:02}-{suffix}.json")
    } else {
        format!("attempt-{index:02}-{suffix}-retry-{admission:02}.json")
    }
}
fn raw_name(admission: usize, index: usize) -> String {
    format!("raw-{admission:02}-{index:02}.bin")
}
fn captured_recording(
    dir: &Path,
    admission: usize,
    recording: &Recording,
) -> Result<RecordingFile> {
    let r = recording.state.lock().map_err(|_| "RecordingLost")?;
    let mut raw = Vec::new();
    for (i, (role, bytes)) in r.outputs.iter().enumerate() {
        if i >= 3 || bytes.len() > 16384 || !matches!(role.as_str(), "director" | "narrator") {
            return Err("RawBudget".into());
        }
        let file = raw_name(admission, i);
        ordinary(&dir.join(&file))?;
        write_new(&dir.join(&file), bytes)?;
        raw.push(RawRef {
            file,
            sha256: digest(bytes),
            bytes: bytes.len(),
            role: role.clone(),
        });
    }
    Ok(RecordingFile {
        version: 2,
        captures: r.captures.clone(),
        raw,
        role_metrics: r.role_metrics.clone(),
        roles: recording.roles.load(Ordering::Relaxed),
        lost: recording.lost.load(Ordering::Relaxed),
        forbidden_director_prompt: r.forbidden_director_prompt,
        forbidden_narrator_prompt: r.forbidden_narrator_prompt,
        forbidden_narrator_output: r.forbidden_narrator_output,
    })
}
fn validate_recording(dir: &Path, admission: usize, r: &RecordingFile) -> Result<()> {
    if r.version != 2
        || r.roles > 3
        || r.captures.len() > 3
        || r.raw.len() > 3
        || (!r.lost && r.roles != r.captures.len())
    {
        return Err("RecordingIntegrity".into());
    }
    let order: Vec<_> = r.captures.iter().map(|c| c.role.as_str()).collect();
    if !matches!(
        order.as_slice(),
        [] | ["director"]
            | ["director", "director"]
            | ["director", "narrator"]
            | ["director", "director", "narrator"]
    ) {
        return Err("RoleOrder".into());
    }
    for (i, raw) in r.raw.iter().enumerate() {
        if raw.file != raw_name(admission, i)
            || !hex(&raw.sha256)
            || raw.bytes > 16384
            || !matches!(raw.role.as_str(), "director" | "narrator")
        {
            return Err("RawIntegrity".into());
        }
        let bytes = read(&dir.join(&raw.file), 16384)?;
        if bytes.len() != raw.bytes || digest(&bytes) != raw.sha256 {
            return Err("RawIntegrity".into());
        }
    }
    Ok(())
}
fn private_read(
    host: &Host,
    session: &str,
    before: &Engine,
    r: &Request,
) -> (Option<Value>, Option<Value>) {
    let trace = call(
        host,
        json!({"op":"trace_read","session":session,"scope":r.scope,"expected_head":before.revision(),"base_revision":r.expected_revision,"observer":{"kind":"player"},"turn":r.turn,"attempt":null}),
    );
    let attempt = trace["data"]["snapshot"]["attempts"]
        .as_array()
        .and_then(|a| a.last())
        .and_then(|a| a["identity"]["attempt"].as_u64());
    let capture=attempt.map(|attempt|call(host,json!({"op":"trace_capture_read","session":session,"scope":r.scope,"expected_head":before.revision(),"base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt})));
    (
        capture,
        if trace["status"] == "ok" {
            Some(trace["data"]["snapshot"].clone())
        } else {
            None
        },
    )
}
struct Observation<'a> {
    step: &'a protocol::Step,
    arm: &'a str,
    policy: ContextPolicy,
    before: &'a Engine,
    after: &'a Engine,
    phase: &'a str,
    error: Option<String>,
    receipt: Option<&'a Receipt>,
    recording: Option<&'a RecordingFile>,
    capture: Option<&'a Value>,
    trace: Option<Value>,
    admission: Option<usize>,
    elapsed_ms: u64,
    first_final_response_ms: Option<u64>,
    commit_elapsed_ms: Option<u64>,
    profile: &'a PlayProfile,
    recovered: bool,
    forwarded_budget_version: Option<u16>,
}
fn make_row(observation: Observation<'_>) -> Result<TurnReportV2> {
    let Observation {
        step,
        arm,
        policy,
        before,
        after,
        phase,
        error,
        receipt,
        recording,
        capture,
        trace,
        admission,
        elapsed_ms,
        first_final_response_ms,
        commit_elapsed_ms,
        profile,
        recovered,
        forwarded_budget_version,
    } = observation;
    let request = step.request(before);
    let same = before.accepted_history_basis().map_err(|_| "Source")?
        == after.accepted_history_basis().map_err(|_| "Source")?;
    let roles = recording.map_or(0, |r| r.roles);
    let guard = matches!(step.expected(), protocol::Expected::GuardRejected(_));
    let mut expected_ok = false;
    let mut policy_matches = guard && roles == 0;
    if let Some(receipt) = receipt {
        if receipt.request() != &request {
            return Err("ReceiptBinding".into());
        }
        let mut replay = before.clone();
        replay
            .commit_prepared(receipt)
            .map_err(|_| "ReceiptReplay")?;
        if replay.accepted_history_basis().map_err(|_| "Source")?
            != after.accepted_history_basis().map_err(|_| "Source")?
        {
            return Err("ReceiptReplay".into());
        }
        expected_ok = matches!(step.expected(),protocol::Expected::Accepted(c) if receipt.proposal().commands.as_slice()==std::slice::from_ref(c));
        policy_matches = receipt.play().is_some_and(|p| {
            p.prompt_version == PROMPT_VERSION
                && p.policy == NARRATION_POLICY
                && p.context_policy == Some(policy)
                && p.profile == *profile
                && p.context
                    .as_ref()
                    .is_some_and(|c| c.compiler_version == 2 && c.version == 2)
        });
    } else if let protocol::Expected::GuardRejected(g) = step.expected() {
        expected_ok = error.as_deref() == Some(format!("{g:?}").as_str()) && same && roles == 0;
    }
    if phase == "not_run_dependency"
        && (!same
            || !matches!(step.expected(), protocol::Expected::Accepted(_))
            || protocol::reference_proposal(before, step).is_ok()
            || roles != 0)
    {
        return Err("DependencyOracle".into());
    }
    let applicable = roles > 0;
    let checked = match (recording, capture) {
        (Some(recording), Some(capture)) => {
            let attempt = capture["data"]["details"]["identity"]["attempt"]
                .as_u64()
                .and_then(|n| u32::try_from(n).ok());
            attempt.and_then(|attempt| {
                CapturedContext::from_host_capture(
                    before,
                    &request,
                    attempt,
                    capture,
                    &recording.captures,
                    profile,
                    forwarded_budget_version,
                )
                .ok()
            })
        }
        _ => None,
    };
    let evidence_available = if applicable {
        checked.is_some()
    } else {
        guard || phase == "not_run_dependency"
    };
    let privacy = checked.as_ref().is_none_or(|c| {
        !c.director_prompts
            .iter()
            .chain(&c.narrator_prompts)
            .any(|p| EXCLUSIONS.iter().any(|x| p.contains(x)))
            && !c
                .narrator_prompts
                .iter()
                .any(|p| p.contains("SECRET-TIDE-731"))
    }) && recording.is_none_or(|r| {
        !r.lost
            && !r.forbidden_director_prompt
            && !r.forbidden_narrator_prompt
            && !r.forbidden_narrator_output
    }) && receipt.is_none_or(|r| {
        !EXCLUSIONS
            .iter()
            .chain(std::iter::once(&"SECRET-TIDE-731"))
            .any(|x| r.narration().contains(x))
    });
    let record = receipt.and_then(Receipt::play);
    let mandatory=checked.as_ref().map(|c|->Result<String>{
        let rows=c.package["records"].as_array().ok_or("CaptureMalformed")?;
        let m:Vec<_>=rows.iter().filter(|r|r["mandatory"]==true).map(|r|json!({"kind":r["kind"],"source_revision":r["source_revision"],"sources":r["sources"],"payload":r["payload"]})).collect();Ok(digest(&encode(&m)?))
    }).transpose()?;
    let optional = checked.as_ref().map(|c| {
        c.package["records"].as_array().is_some_and(|rows| {
            rows.iter().any(|r| {
                r["mandatory"] == false
                    && r.to_string()
                        .contains("The pennant I carry has an amber stitch.")
            })
        })
    });
    let sf = record
        .and_then(|r| r.context.as_ref())
        .and_then(|c| serde_json::to_value(c.source_fallback_reason).ok())
        .and_then(|v| v.as_str().map(str::to_owned));
    let cf = record
        .and_then(|r| r.context.as_ref())
        .and_then(|c| serde_json::to_value(c.coverage.set_fallback_reason).ok())
        .and_then(|v| v.as_str().map(str::to_owned));
    let mut failures = Vec::new();
    if !expected_ok {
        failures.push(
            match error.as_deref() {
                Some("Agency") => "player_agency",
                Some("Stale" | "Scope") => "stale_source",
                Some("Malformed" | "Provider" | "TooLarge") => "provider_or_parse",
                _ if phase == "not_run_dependency" => "not_run_dependency",
                _ => "scenario_outcome",
            }
            .into(),
        );
    }
    if !policy_matches && !guard {
        failures.push("no_matching_current_policy_receipt".into());
    }
    if !evidence_available {
        failures.push("context_evidence_unavailable".into());
    }
    if !privacy {
        failures.push("observer_or_output_privacy".into());
    }
    if recovered {
        failures.push("unknown_historical_calls_and_checkpoint".into());
    }
    if recording.is_some_and(|r| r.lost) {
        failures.push("recording_loss".into());
    }
    let quality_flags = if record.is_some_and(|r| r.fallback) {
        vec!["narration_fallback_no_quality_acceptance".into()]
    } else {
        vec![]
    };
    Ok(TurnReportV2 {
        turn: step.id().into(),
        scene: step.scene(),
        arm: arm.into(),
        policy,
        phase: phase.into(),
        error,
        expected: serde_json::to_string(step.expected()).map_err(|_| "Encoding")?,
        passed: expected_ok
            && policy_matches
            && evidence_available
            && privacy
            && !recovered
            && recording.is_none_or(|r| !r.lost),
        failures,
        quality_flags,
        roles,
        roles_known: !recovered,
        recovered_without_checkpoint: recovered,
        admission,
        elapsed_ms,
        first_final_response_ms,
        commit_elapsed_ms,
        input_semantic_sha256: v2::semantic_input(before, &request)?,
        output_semantic_sha256: v2::semantic_output(after)?,
        mechanical_sha256: v2::mechanical_output(after)?,
        policy_matches,
        context_evidence_available: evidence_available && !recovered,
        context_requirement: if guard {
            "not_applicable_guard_configured_only"
        } else if phase == "not_run_dependency" {
            "not_applicable_dependency"
        } else {
            "required_actual_capture"
        }
        .into(),
        privacy_passed: privacy && evidence_available && !recovered,
        fallback: record.map(|p| p.fallback),
        capture_sha256: capture.map(|c| encode(c).map(|b| digest(&b))).transpose()?,
        recording_sha256: recording
            .map(|r| encode(r).map(|b| digest(&b)))
            .transpose()?,
        raw_sha256: recording.map_or_else(Vec::new, |r| {
            r.raw.iter().map(|r| r.sha256.clone()).collect()
        }),
        role_metrics: recording.and_then(|r| r.role_metrics.clone()),
        trace,
        actual_receipt_sha256: receipt.map(|r| encode(r).map(|b| digest(&b))).transpose()?,
        source_fallback_reason: sf,
        compiler_fallback_reason: cf,
        narration: receipt.map(|r| r.narration().to_owned()),
        repairs: record.map(|r| r.repairs),
        stages: record.map_or_else(Vec::new, |r| {
            r.stages
                .iter()
                .filter_map(|s| serde_json::to_value(s).ok())
                .collect()
        }),
        mandatory_sha256: mandatory,
        optional_detail_selected: optional,
        director_private_target_present: checked.as_ref().map(|c| {
            c.director_prompts
                .iter()
                .any(|p| p.contains("SECRET-TIDE-731"))
        }),
        selected_context_bytes: checked
            .as_ref()
            .map(|c| encode(&c.package).map(|b| b.len()))
            .transpose()?,
        estimated_context_tokens: checked
            .as_ref()
            .and_then(|c| c.package["estimated_tokens"].as_u64()),
        forwarded_director_estimates: checked.as_ref().and_then(|c| c.director_estimates.clone()),
    })
}

struct TurnJob<'a> {
    dir: &'a Path,
    path: &'a Path,
    index: usize,
    arm: &'a str,
    policy: ContextPolicy,
    binding: &'a str,
    step: &'a protocol::Step,
    factory: &'a LaneFactory,
    cancel: &'a Cancellation,
}
struct OwnedHost(Arc<Host>);
impl Drop for OwnedHost {
    fn drop(&mut self) {
        self.0.close_all();
    }
}
fn execute_turn(job: TurnJob<'_>, ledger: &mut Ledger) -> Result<StoredTurn> {
    let TurnJob {
        dir,
        path,
        index,
        arm,
        policy,
        binding,
        step,
        factory,
        cancel,
    } = job;
    let full = engine(path, &suite()?.seed().scope)?;
    if full.domain_version() != 1 {
        return Err("UnsupportedDomain".into());
    }
    if full
        .receipts()
        .iter()
        .any(|r| r.request().turn == step.id())
    {
        // Actual durable lookup, before admission/provider construction. Unknown
        // historical roles/capture are never manufactured from the receipt.
        let actual = Store::open_read_only(path)
            .map_err(|_| "Workspace")?
            .lookup_turn(full.scope(), step.id())
            .map_err(|_| "Lookup")?;
        let receipt = actual.receipt.ok_or("Lookup")?;
        let before = full
            .at_revision(receipt.request().expected_revision)
            .map_err(|_| "Replay")?;
        let after = full
            .at_revision(receipt.events().last().ok_or("ReceiptBinding")?.sequence())
            .map_err(|_| "Replay")?;
        let row = make_row(Observation {
            step,
            arm,
            policy,
            before: &before,
            after: &after,
            phase: "committed",
            error: None,
            receipt: Some(&receipt),
            recording: None,
            capture: None,
            trace: None,
            admission: None,
            elapsed_ms: 0,
            first_final_response_ms: None,
            commit_elapsed_ms: None,
            profile: &factory.profile()?,
            recovered: true,
            forwarded_budget_version: Some(1),
        })?;
        return Ok(StoredTurn {
            version: 2,
            binding: binding.into(),
            index,
            arm: arm.into(),
            request: step.request(&before),
            before_head: before.revision(),
            after_head: after.revision(),
            row,
            capture_file: None,
            recording_file: None,
        });
    }
    let before = full;
    let request = step.request(&before);
    let profile = factory.profile()?;
    if matches!(step.expected(), protocol::Expected::Accepted(_))
        && protocol::reference_proposal(&before, step).is_err()
    {
        let row = make_row(Observation {
            step,
            arm,
            policy,
            before: &before,
            after: &before,
            phase: "not_run_dependency",
            error: None,
            receipt: None,
            recording: None,
            capture: None,
            trace: None,
            admission: None,
            elapsed_ms: 0,
            first_final_response_ms: None,
            commit_elapsed_ms: None,
            profile: &profile,
            recovered: false,
            forwarded_budget_version: Some(1),
        })?;
        return Ok(StoredTurn {
            version: 2,
            binding: binding.into(),
            index,
            arm: arm.into(),
            request,
            before_head: before.revision(),
            after_head: before.revision(),
            row,
            capture_file: None,
            recording_file: None,
        });
    }
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
        host.configure_local_provider_with_policy(profile.clone(), provider, policy)
    } else {
        host.configure_fixture_provider_with_policy(profile.clone(), provider, policy)
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
    let limit = TURN_MS.min(active_remaining.saturating_sub(CLEANUP_RESERVE_MS));
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
                .spawn(move || {
                    let began = Instant::now();
                    loop {
                        match stopped.recv_timeout(Duration::from_millis(5)) {
                            Ok(()) | Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => break,
                            Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
                        }
                        if external.is_cancelled()
                            || began.elapsed() >= Duration::from_millis(limit)
                        {
                            op(&watch_host, &sid, &watch.scope, &watch.turn, "cancel");
                            break;
                        }
                    }
                })
                .map_err(|_| "Watchdog")?,
        ),
    };
    if reply["data"]["phase"] == "queued" {
        reply = op(&host, &session, before.scope(), step.id(), "prepare");
    }
    if cancel.is_cancelled() || started.elapsed() >= Duration::from_millis(limit) {
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
    if cancel.is_cancelled() || started.elapsed() >= Duration::from_millis(limit) {
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
    let row = make_row(Observation {
        step,
        arm,
        policy,
        before: &before,
        after: &after,
        phase: &phase,
        error,
        receipt,
        recording: Some(&recorded),
        capture: capture.as_ref(),
        trace,
        admission: Some(admission),
        elapsed_ms: elapsed,
        first_final_response_ms,
        commit_elapsed_ms,
        profile: &profile,
        recovered: false,
        forwarded_budget_version: Some(1),
    })?;
    let result = StoredTurn {
        version: 2,
        binding: binding.into(),
        index,
        arm: arm.into(),
        request,
        before_head: before.revision(),
        after_head: after.revision(),
        row,
        capture_file,
        recording_file: Some(recording_file),
    };
    // The canonical/known-terminal checkpoint is durable before reducing reservations.
    saved(&checkpoint_path(dir, index), &result, 256 * 1024)?;
    if matches!(
        phase.as_str(),
        "committed" | "failed" | "cancelled" | "rejected" | "stale"
    ) {
        ledger.settle(admission, elapsed, recorded.roles)?;
    }
    call(
        &host,
        json!({"op":"trace_capture_revoke","session":session,"scope":before.scope()}),
    );
    host.close_all();
    Ok(result)
}

fn load_turn(
    dir: &Path,
    path: &Path,
    index: usize,
    arm: &str,
    policy: ContextPolicy,
    key: &str,
    manifest: &RunManifest,
) -> Result<StoredTurn> {
    let profile = &manifest.profile;
    let stored: StoredTurn = decode(&checkpoint_path(dir, index), 256 * 1024)?;
    let corpus = suite()?;
    let step = &corpus.steps()[index];
    if stored.version != 2 || stored.index != index || stored.arm != arm || stored.binding != key {
        return Err("CheckpointMismatch".into());
    }
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
    let receipt = if stored.row.phase == "committed" {
        Some(
            Store::open_read_only(path)
                .map_err(|_| "Workspace")?
                .lookup_turn(before.scope(), step.id())
                .map_err(|_| "Lookup")?
                .receipt
                .ok_or("Lookup")?,
        )
    } else {
        None
    };
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
    let actual = make_row(Observation {
        step,
        arm,
        policy,
        before: &before,
        after: &after,
        phase: &stored.row.phase,
        error: stored.row.error.clone(),
        receipt: receipt.as_ref(),
        recording: recording.as_ref(),
        capture: capture.as_ref(),
        trace: stored.row.trace.clone(),
        admission: stored.row.admission,
        elapsed_ms: stored.row.elapsed_ms,
        first_final_response_ms: stored.row.first_final_response_ms,
        commit_elapsed_ms: stored.row.commit_elapsed_ms,
        profile,
        recovered: stored.row.recovered_without_checkpoint,
        forwarded_budget_version: manifest.binding.forwarded_budget_version,
    })?;
    if actual != stored.row {
        return Err("CheckpointEvidenceMismatch".into());
    }
    Ok(stored)
}

/// Validated actual reference. No Deserialize and no caller-supplied expected receipt.
pub struct ValidatedReference {
    directory: PathBuf,
    report: ReferenceReportV2,
    engine: Engine,
    turns: Vec<StoredTurn>,
    manifest: RunManifest,
}
impl ValidatedReference {
    pub fn report(&self) -> &ReferenceReportV2 {
        &self.report
    }
    fn digest(&self) -> Result<String> {
        Ok(digest(&encode(&self.report)?))
    }
    fn prefix(&self, index: usize) -> Result<&[Receipt]> {
        let head = self.turns.get(index).ok_or("ReferenceOrder")?.before_head;
        let count = self
            .engine
            .receipts()
            .iter()
            .take_while(|r| r.events().last().is_some_and(|e| e.sequence() <= head))
            .count();
        Ok(&self.engine.receipts()[..count])
    }
}
pub fn prepare_reference(dir: &Path, cancel: &Cancellation) -> Result<ReferenceReportV2> {
    if cancel.is_cancelled() {
        return Err("Interrupted".into());
    }
    ordinary(dir)?;
    fs::create_dir(dir).map_err(|_| "OutputExists")?;
    let _lock = take_lock(dir)?;
    let corpus = suite()?;
    let factory = LaneFactory::ScriptedBaseline;
    let profile = factory.profile()?;
    let manifest = RunManifest::new(
        ComparisonKind::ContinuousRollout,
        profile.clone(),
        false,
        None,
    )?;
    saved(&dir.join("reference-binding.json"), &manifest, 128 * 1024)?;
    let key = manifest.stable_key()?;
    let path = dir.join("synthetic.sqlite");
    ensure_database(&path, corpus.seed(), &[])?;
    let mut ledger = Ledger::load(dir, &key)?;
    ledger.begin_invocation()?;
    let mut turns = Vec::new();
    for (index, step) in corpus.steps().iter().enumerate() {
        if cancel.is_cancelled() {
            ledger.finish()?;
            return Err("Interrupted".into());
        }
        let t = execute_turn(
            TurnJob {
                dir,
                path: &path,
                index,
                arm: "reference",
                policy: ContextPolicy::StateRelevantMemoryV1,
                binding: &key,
                step,
                factory: &factory,
                cancel,
            },
            &mut ledger,
        )?;
        if !checkpoint_path(dir, index).exists() {
            saved(&checkpoint_path(dir, index), &t, 256 * 1024)?;
        }
        turns.push(t.row);
    }
    ledger.finish()?;
    let report = ReferenceReportV2 {
        version: 2,
        source_sha256: manifest.source_sha256,
        suite_sha256: manifest.binding.suite_sha256,
        accepted: turns.iter().filter(|t| t.phase == "committed").count(),
        guard_only: turns.iter().filter(|t| t.roles == 0 && t.passed).count(),
        roles: turns.iter().map(|t| t.roles).sum(),
        turns,
    };
    saved(&dir.join("reference.json"), &report, crate::MAX_REPORT)?;
    if report.accepted != 21
        || report.guard_only != 3
        || report.roles != 42
        || report.turns.iter().any(|t| !t.passed)
    {
        return Err("ReferenceFailed".into());
    }
    Ok(report)
}
pub fn open_reference(dir: &Path) -> Result<ValidatedReference> {
    ordinary(dir)?;
    let manifest: RunManifest = decode(&dir.join("reference-binding.json"), 128 * 1024)?;
    manifest.validate()?;
    if manifest.binding.native
        || manifest.reference_sha256.is_some()
        || manifest.kind != ComparisonKind::ContinuousRollout
    {
        return Err("ReferenceBinding".into());
    }
    let report: ReferenceReportV2 = decode(&dir.join("reference.json"), crate::MAX_REPORT)?;
    let corpus = suite()?;
    let path = dir.join("synthetic.sqlite");
    let engine = engine(&path, &corpus.seed().scope)?;
    let key = manifest.stable_key()?;
    let mut turns = Vec::new();
    for index in 0..24 {
        let t = load_turn(
            dir,
            &path,
            index,
            "reference",
            ContextPolicy::StateRelevantMemoryV1,
            &key,
            &manifest,
        )?;
        let before = engine
            .at_revision(t.before_head)
            .map_err(|_| "ReferenceReplay")?;
        match corpus.steps()[index].expected() {
            protocol::Expected::Accepted(command) => {
                let p = protocol::reference_proposal(&before, &corpus.steps()[index])
                    .map_err(|_| "ReferenceOracle")?;
                if p.commands.as_slice() != std::slice::from_ref(command) {
                    return Err("ReferenceOracle".into());
                }
            }
            protocol::Expected::GuardRejected(expected) => {
                if protocol::reference_proposal(&before, &corpus.steps()[index])
                    .err()
                    .map(|e| format!("{e:?}"))
                    != Some(format!("{expected:?}"))
                {
                    return Err("ReferenceOracle".into());
                }
            }
        }
        turns.push(t);
    }
    let rebuilt = ReferenceReportV2 {
        version: 2,
        source_sha256: manifest.source_sha256.clone(),
        suite_sha256: manifest.binding.suite_sha256.clone(),
        accepted: turns.iter().filter(|t| t.row.phase == "committed").count(),
        guard_only: turns
            .iter()
            .filter(|t| t.row.roles == 0 && t.row.passed)
            .count(),
        roles: turns.iter().map(|t| t.row.roles).sum(),
        turns: turns.iter().map(|t| t.row.clone()).collect(),
    };
    if rebuilt != report
        || report.accepted != 21
        || report.guard_only != 3
        || report.roles != 42
        || turns.iter().any(|t| !t.row.passed)
    {
        return Err("ReferenceIntegrity".into());
    }
    Ok(ValidatedReference {
        directory: dir.into(),
        report,
        engine,
        turns,
        manifest,
    })
}

fn copy_reference(reference: &ValidatedReference, dest: &Path) -> Result<()> {
    let fresh = open_reference(&reference.directory)?;
    if fresh.digest()? != reference.digest()? {
        return Err("ReferenceChanged".into());
    }
    ordinary(dest)?;
    if !dest.exists() {
        fs::create_dir(dest).map_err(|_| "Io")?;
    }
    ensure_database(
        &dest.join("synthetic.sqlite"),
        fresh.engine.seed(),
        fresh.engine.receipts(),
    )?;
    let mut files = vec![
        ("reference-binding.json".to_owned(), 128 * 1024),
        ("reference.json".to_owned(), crate::MAX_REPORT),
    ];
    for t in &fresh.turns {
        files.push((format!("attempt-{:02}.json", t.index), 256 * 1024));
        if let Some(admission) = t.row.admission {
            files.push((format!("admission-{admission:02}.json"), 4096));
            let settled = format!("admission-{admission:02}-settled.json");
            if fresh.directory.join(&settled).exists() {
                files.push((settled, 4096));
            }
        }
        if let Some(name) = &t.capture_file {
            files.push((name.clone(), v2::MAX_PRIVATE_CAPTURE + 4096));
        }
        if let Some(name) = &t.recording_file {
            files.push((name.clone(), 64 * 1024));
            let r: RecordingFile = decode(&fresh.directory.join(name), 64 * 1024)?;
            files.extend(r.raw.iter().map(|r| (r.file.clone(), 16384)));
        }
    }
    for index in 0..32 {
        for name in [
            format!("invocation-{index:02}.json"),
            format!("invocation-{index:02}-settled.json"),
        ] {
            if fresh.directory.join(&name).exists() {
                files.push((name, 4096));
            }
        }
    }
    for (name, cap) in files {
        let bytes = read(&fresh.directory.join(&name), cap)?;
        let target = dest.join(name);
        ordinary(&target)?;
        if target.exists() {
            if read(&target, cap)? != bytes {
                return Err("ReferenceChanged".into());
            }
        } else {
            write_new(&target, &bytes)?;
        }
    }
    open_reference(dest)?;
    Ok(())
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SceneManifest {
    version: u16,
    binding: String,
    scene: usize,
    checkpoints: Vec<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SetupRecord {
    version: u16,
    binding: String,
    left_invocation: usize,
    right_invocation: usize,
    native: bool,
    physical_ms: u64,
    status: String,
    load: Option<Value>,
}
struct ComparisonSession {
    dir: PathBuf,
    manifest: RunManifest,
    key: String,
    _lock: File,
    ledgers: [Ledger; 2],
    turns: [Vec<StoredTurn>; 2],
    reference: Option<ValidatedReference>,
}
fn scene_data(dir: &Path, key: &str, scene: usize) -> Result<SceneManifest> {
    let mut checkpoints = Vec::new();
    for index in scene * 6..scene * 6 + 6 {
        for arm in ARM_NAMES {
            checkpoints.push(digest(&read(
                &checkpoint_path(&dir.join(arm), index),
                256 * 1024,
            )?));
        }
    }
    Ok(SceneManifest {
        version: 2,
        binding: key.into(),
        scene,
        checkpoints,
    })
}
fn sealed_scenes(dir: &Path, key: &str) -> Result<usize> {
    let mut count = 0;
    let mut gap = false;
    for scene in 0..4 {
        let path = dir.join(format!("scene-{scene:02}.json"));
        ordinary(&path)?;
        if !path.exists() {
            gap = true;
            continue;
        }
        if gap {
            return Err("SceneOrder".into());
        }
        let stored: SceneManifest = decode(&path, 4096)?;
        if stored != scene_data(dir, key, scene)? {
            return Err("SceneIntegrity".into());
        }
        count += 1;
    }
    Ok(count)
}
fn load_turns(dir: &Path, manifest: &RunManifest, key: &str) -> Result<[Vec<StoredTurn>; 2]> {
    let corpus = suite()?;
    let mut result: [Vec<StoredTurn>; 2] = [Vec::new(), Vec::new()];
    for arm in 0..2 {
        let d = dir.join(ARM_NAMES[arm]);
        ordinary(&d)?;
        let mut gap = false;
        for index in 0..24 {
            let cp = checkpoint_path(&d, index);
            ordinary(&cp)?;
            if !cp.exists() {
                gap = true;
                continue;
            }
            if gap {
                return Err("CheckpointOrder".into());
            }
            let path = database(&d, index, manifest.kind);
            let t = load_turn(
                &d,
                &path,
                index,
                ARM_NAMES[arm],
                POLICIES[arm],
                key,
                manifest,
            )?;
            if manifest.kind == ComparisonKind::ContinuousRollout {
                let expected = result[arm].last().map_or(0, |t| t.after_head);
                if t.before_head != expected {
                    return Err("RolloutContinuity".into());
                }
            }
            result[arm].push(t);
        }
        let db = database(&d, 0, manifest.kind);
        if manifest.kind == ComparisonKind::ContinuousRollout && db.exists() {
            let engine = engine(&db, &corpus.seed().scope)?;
            validate_rollout_source(&engine, &corpus)?;
        }
    }
    Ok(result)
}
fn validate_rollout_source(engine: &Engine, corpus: &protocol::FrozenSuite) -> Result<()> {
    if engine.domain_version() != 1 || engine.seed() != corpus.seed() {
        return Err("RolloutSource".into());
    }
    let mut last = None;
    for r in engine.receipts() {
        let index = corpus
            .steps()
            .iter()
            .position(|s| s.id() == r.request().turn)
            .ok_or("RolloutSource")?;
        if last.is_some_and(|last| index <= last) {
            return Err("RolloutSource".into());
        }
        let before = engine
            .at_revision(r.request().expected_revision)
            .map_err(|_| "RolloutSource")?;
        if corpus.steps()[index].request(&before) != *r.request() {
            return Err("RolloutSource".into());
        }
        last = Some(index);
    }
    Ok(())
}
impl ComparisonSession {
    fn finish_and_publish(&mut self) -> Result<ComparisonReportV2> {
        // Strict final canonical/capture replay is real own work, before settlement.
        let mut report = inspect_comparison(&self.dir)?;
        self.finish_ledgers()?;
        report.left_charged_ms = self.ledgers[0].charged_ms;
        report.right_charged_ms = self.ledgers[1].charged_ms;
        report.left_reserved_roles = self.ledgers[0].charged_roles;
        report.right_reserved_roles = self.ledgers[1].charged_roles;
        report.unavailable.retain(|note| {
            !ARM_NAMES.iter().any(|arm| {
                note.starts_with(&format!("{arm}:unknown_invocations:"))
                    || note == &format!("{arm}:resource_cap_exceeded")
            })
        });
        append_ledger_notes(&self.dir, &self.ledgers, &mut report.unavailable);
        publish(&self.dir, &report)?;
        Ok(report)
    }
    fn finish_ledgers(&mut self) -> Result<()> {
        for arm in 0..2 {
            let began = Instant::now();
            self.ledgers[arm].finish()?;
            self.ledgers[1 - arm].exclude_measured_interval(
                began.elapsed().as_millis().min(u64::MAX as u128) as u64,
            )?;
        }
        Ok(())
    }
    fn open(
        dir: &Path,
        resume: bool,
        expected: RunManifest,
        reference: Option<&ValidatedReference>,
    ) -> Result<Self> {
        expected.validate()?;
        ordinary(dir)?;
        if resume {
            let actual: RunManifest = decode(&dir.join("run.json"), 128 * 1024)?;
            if actual != expected || !actual.source_matches()? {
                return Err("CheckpointMismatch".into());
            }
        } else {
            fs::create_dir(dir).map_err(|_| "OutputExists")?;
            saved(&dir.join("run.json"), &expected, 128 * 1024)?;
        }
        let lock = take_lock(dir)?;
        for arm in ARM_NAMES {
            let path = dir.join(arm);
            ordinary(&path)?;
            if !path.exists() {
                fs::create_dir(path).map_err(|_| "Io")?;
            }
        }
        if expected.kind == ComparisonKind::PairedSnapshots {
            if let Some(reference) = reference {
                copy_reference(reference, &dir.join("reference"))?;
            }
        }
        let reference = if expected.kind == ComparisonKind::PairedSnapshots {
            let r = open_reference(&dir.join("reference"))?;
            if Some(r.digest()?) != expected.reference_sha256 || !r.manifest.source_matches()? {
                return Err("ReferenceBinding".into());
            }
            Some(r)
        } else {
            None
        };
        let key = expected.stable_key()?;
        let turns = load_turns(dir, &expected, &key)?;
        sealed_scenes(dir, &key)?;
        let mut ledgers = [
            Ledger::load(&dir.join("left"), &key)?,
            Ledger::load(&dir.join("right"), &key)?,
        ];
        // Both reservations are durable before any asset/provider initialization.
        ledgers[0].begin_invocation()?;
        ledgers[1].begin_invocation()?;
        Ok(Self {
            dir: dir.into(),
            manifest: expected,
            key,
            _lock: lock,
            ledgers,
            turns,
            reference,
        })
    }
    fn setup(
        &mut self,
        native: bool,
        physical_ms: u64,
        status: &str,
        load: Option<Value>,
    ) -> Result<()> {
        let record = SetupRecord {
            version: 2,
            binding: self.key.clone(),
            left_invocation: self.ledgers[0].invocation,
            right_invocation: self.ledgers[1].invocation,
            native,
            physical_ms,
            status: status.into(),
            load,
        };
        saved(
            &self
                .dir
                .join(format!("setup-{:02}.json", record.left_invocation)),
            &record,
            64 * 1024,
        )?;
        let (left, right) = shared_setup_shares(physical_ms);
        self.ledgers[0].record_shared_setup(physical_ms, left)?;
        self.ledgers[1].record_shared_setup(physical_ms, right)?;
        Ok(())
    }
    fn execute(
        mut self,
        cancel: &Cancellation,
        max_new_scenes: usize,
        factory: LaneFactory,
    ) -> Result<ComparisonReportV2> {
        let corpus = suite()?;
        let first = sealed_scenes(&self.dir, &self.key)?;
        'scenes: for scene in first..(first + max_new_scenes).min(4) {
            for index in scene * 6..scene * 6 + 6 {
                let first_arm = match self.manifest.kind {
                    ComparisonKind::PairedSnapshots => index % 2,
                    ComparisonKind::ContinuousRollout => scene % 2,
                };
                for arm in [first_arm, 1 - first_arm] {
                    if index < self.turns[arm].len() {
                        continue;
                    }
                    if cancel.is_cancelled() {
                        break 'scenes;
                    }
                    let began = Instant::now();
                    let d = self.dir.join(ARM_NAMES[arm]);
                    let path = database(&d, index, self.manifest.kind);
                    let prefix = match &self.reference {
                        Some(reference) => reference.prefix(index)?,
                        None => &[],
                    };
                    ensure_database(&path, corpus.seed(), prefix)?;
                    if self.manifest.kind == ComparisonKind::PairedSnapshots {
                        let current = engine(&path, &corpus.seed().scope)?;
                        if current.receipts().len() > prefix.len() + 1 {
                            return Err("ReferencePrefix".into());
                        }
                    }
                    let t = execute_turn(
                        TurnJob {
                            dir: &d,
                            path: &path,
                            index,
                            arm: ARM_NAMES[arm],
                            policy: POLICIES[arm],
                            binding: &self.key,
                            step: &corpus.steps()[index],
                            factory: &factory,
                            cancel,
                        },
                        &mut self.ledgers[arm],
                    )?;
                    if !checkpoint_path(&d, index).exists() {
                        saved(&checkpoint_path(&d, index), &t, 256 * 1024)?;
                    }
                    self.turns[arm].push(t);
                    self.ledgers[1 - arm].exclude_measured_interval(
                        began.elapsed().as_millis().min(u64::MAX as u128) as u64,
                    )?;
                }
            }
            let sealed = scene_data(&self.dir, &self.key, scene)?;
            saved(
                &self.dir.join(format!("scene-{scene:02}.json")),
                &sealed,
                4096,
            )?;
        }
        self.finish_and_publish()
    }
}
fn publish(dir: &Path, report: &ComparisonReportV2) -> Result<()> {
    let data = serde_json::to_vec_pretty(report).map_err(|_| "Encoding")?;
    let html=format!("<!doctype html><meta charset=utf-8><meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'none'\"><title>Current policy comparison</title><h1>Current policy comparison</h1><p>Synthetic evaluation. No human quality acceptance.</p><pre>{}</pre>",escape(std::str::from_utf8(&data).map_err(|_|"Encoding")?));
    if data.len() > crate::MAX_REPORT || html.len() > crate::MAX_REPORT {
        return Err("ReportBudget".into());
    }
    for (name, bytes) in [
        ("report.json", data.as_slice()),
        ("report.html", html.as_bytes()),
    ] {
        let path = dir.join(name);
        ordinary(&path)?;
        fs::write(path, bytes).map_err(|_| "Io")?;
    }
    Ok(())
}
fn append_ledger_notes(dir: &Path, ledgers: &[Ledger; 2], unavailable: &mut Vec<String>) {
    for (arm, ledger) in ledgers.iter().enumerate() {
        if ledger.admissions > MAX_ADMISSIONS
            || ledger.charged_roles > MAX_ROLES
            || ledger.charged_ms > MAX_ACTIVE_MS
        {
            unavailable.push(format!("{}:resource_cap_exceeded", ARM_NAMES[arm]));
        }
        let d = dir.join(ARM_NAMES[arm]);
        let unknown = (0..ledger.invocations)
            .filter(|i| !d.join(format!("invocation-{i:02}-settled.json")).exists())
            .count();
        if unknown > 0 {
            unavailable.push(format!("{}:unknown_invocations:{unknown}", ARM_NAMES[arm]));
        }
    }
}
/// Pure report opening: no invocation/provider/assets, checkpoint mutation or replay calls to a model.
pub fn inspect_comparison(dir: &Path) -> Result<ComparisonReportV2> {
    ordinary(dir)?;
    let manifest: RunManifest = decode(&dir.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    let key = manifest.stable_key()?;
    let turns = load_turns(dir, &manifest, &key)?;
    let completed_scenes = sealed_scenes(dir, &key)?;
    let reference = if manifest.kind == ComparisonKind::PairedSnapshots {
        let reference = open_reference(&dir.join("reference"))?;
        if Some(reference.digest()?) != manifest.reference_sha256 {
            return Err("ReferenceBinding".into());
        }
        Some(reference)
    } else {
        None
    };
    let mut rows = Vec::new();
    let mut same_input_pairs = 0;
    let mut semantic = None;
    let mut mechanical = None;
    let mut unavailable = Vec::new();
    for index in 0..24 {
        let left = turns[0].get(index);
        let right = turns[1].get(index);
        for (arm, turn) in [left, right].into_iter().enumerate() {
            if let Some(turn) = turn {
                if let Some(reference) = &reference {
                    if turn.row.input_semantic_sha256
                        != reference.turns[index].row.input_semantic_sha256
                    {
                        return Err("ReferenceInputMismatch".into());
                    }
                }
                if !turn.row.context_evidence_available {
                    unavailable.push(format!(
                        "{}:{}:context_unavailable",
                        ARM_NAMES[arm], turn.row.turn
                    ));
                }
                if !turn.row.roles_known {
                    unavailable.push(format!(
                        "{}:{}:unknown_historical_roles",
                        ARM_NAMES[arm], turn.row.turn
                    ));
                }
                rows.push(turn.row.clone());
            }
        }
        if let (Some(l), Some(r)) = (left, right) {
            if l.row.input_semantic_sha256 == r.row.input_semantic_sha256 {
                same_input_pairs += 1;
            }
            if semantic.is_none() && l.row.output_semantic_sha256 != r.row.output_semantic_sha256 {
                semantic = Some(l.row.turn.clone());
            }
            if mechanical.is_none() && l.row.mechanical_sha256 != r.row.mechanical_sha256 {
                mechanical = Some(l.row.turn.clone());
            }
            if manifest.kind == ComparisonKind::PairedSnapshots
                && l.row.mandatory_sha256 != r.row.mandatory_sha256
            {
                unavailable.push(format!("{}:mandatory_fingerprint_mismatch", l.row.turn));
            }
        }
    }
    let ledgers = [
        Ledger::load(&dir.join("left"), &key)?,
        Ledger::load(&dir.join("right"), &key)?,
    ];
    let mut setups = Vec::new();
    for index in 0..32 {
        let path = dir.join(format!("setup-{index:02}.json"));
        ordinary(&path)?;
        if !path.exists() {
            continue;
        }
        let setup: SetupRecord = decode(&path, 64 * 1024)?;
        if setup.version != 2
            || setup.binding != key
            || setup.left_invocation != index
            || setup.right_invocation >= 32
            || setup.native != manifest.binding.native
            || !matches!(setup.status.as_str(), "loaded" | "scripted" | "failed")
        {
            return Err("SetupIntegrity".into());
        }
        setups.push(setup);
    }
    for setup in &setups {
        if setup.status == "failed" {
            unavailable.push(format!(
                "native_setup_failed_invocation:{}",
                setup.left_invocation
            ));
        }
    }
    let native: Vec<_> = setups.iter().filter(|s| s.native).collect();
    let physical_setup_ms = if native.is_empty() {
        None
    } else {
        Some(native.iter().try_fold(0u64, |sum, s| {
            sum.checked_add(s.physical_ms).ok_or("SetupIntegrity")
        })?)
    };
    append_ledger_notes(dir, &ledgers, &mut unavailable);
    Ok(ComparisonReportV2 {
        version: 2,
        kind: manifest.kind,
        lane: if manifest.binding.native {
            "native_current_policy_comparison"
        } else {
            "scripted_current_policy_comparison"
        }
        .into(),
        source_matches: manifest.source_matches()?,
        completed: completed_scenes == 4,
        completed_scenes,
        turns: rows,
        human_reviewed: 0,
        human_rubric: "not_reviewed".into(),
        quality_accepted: false,
        physical_setups: native.len(),
        physical_setup_ms,
        native_load: if native.is_empty() {
            None
        } else {
            Some(json!(native.iter().map(|s| &s.load).collect::<Vec<_>>()))
        },
        left_charged_ms: ledgers[0].charged_ms,
        right_charged_ms: ledgers[1].charged_ms,
        left_reserved_roles: ledgers[0].charged_roles,
        right_reserved_roles: ledgers[1].charged_roles,
        first_semantic_divergence: semantic,
        first_mechanical_divergence: mechanical,
        same_input_pairs,
        unavailable,
        profile: manifest.profile,
        suite_sha256: manifest.binding.suite_sha256,
        source_sha256: manifest.source_sha256,
        reference_sha256: manifest.reference_sha256,
        limitations:vec!["Synthetic 24-attempt finite-intent suite, not general prose comprehension.".into(),"Both selectors feed Director; narrator deliberately receives only Core-grounded outcomes/observations, no optional history.".into(),"Diagnostic capture/checkpoint overhead is included in observed desktop turn cost; this is not a phone measurement.".into(),"Hashes detect drift and bind retained data; they do not authenticate adversarially rewritten evaluation evidence.".into(),"No human enjoyment/distinctiveness/repetition review has been performed.".into()],
    })
}
fn reference_digest(
    dir: &Path,
    resume: bool,
    kind: ComparisonKind,
    reference: Option<&ValidatedReference>,
) -> Result<Option<String>> {
    match (kind, reference) {
        (ComparisonKind::ContinuousRollout, None) => Ok(None),
        (ComparisonKind::ContinuousRollout, Some(_)) => Err("ReferenceNotApplicable".into()),
        (ComparisonKind::PairedSnapshots, Some(reference)) => {
            if !reference.manifest.source_matches()? {
                return Err("ReferenceSourceMismatch".into());
            }
            Ok(Some(reference.digest()?))
        }
        (ComparisonKind::PairedSnapshots, None) if resume => {
            Ok(Some(open_reference(&dir.join("reference"))?.digest()?))
        }
        _ => Err("ReferenceRequired".into()),
    }
}
pub fn run_comparison(
    dir: &Path,
    resume: bool,
    kind: ComparisonKind,
    cancel: &Cancellation,
    max_new_scenes: usize,
    factory: LaneFactory,
    reference: Option<&ValidatedReference>,
) -> Result<ComparisonReportV2> {
    if factory.native() {
        return Err("UseNativeComparisonEntry".into());
    }
    if cancel.is_cancelled() {
        return Err("Interrupted".into());
    }
    if !(1..=4).contains(&max_new_scenes) {
        return Err("SceneBudget".into());
    }
    let expected = RunManifest::new(
        kind,
        factory.profile()?,
        factory.native(),
        reference_digest(dir, resume, kind, reference)?,
    )?;
    if resume {
        let actual: RunManifest = decode(&dir.join("run.json"), 128 * 1024)?;
        if actual != expected || !actual.source_matches()? {
            return Err("CheckpointMismatch".into());
        }
        let report = inspect_comparison(dir)?;
        if report.completed {
            return Ok(report);
        }
    }
    let mut session = ComparisonSession::open(dir, resume, expected, reference)?;
    // Pre-owned runtime construction remains native; setup was not measured here.
    // Only the native entry below may claim a physical asset setup measurement.
    session.setup(false, 0, "scripted", None)?;
    session.execute(cancel, max_new_scenes, factory)
}

/// Reserve BOTH preparations before touching native assets. One existing runtime
/// is then shared sequentially by both arms; no separate provider/evaluator.
#[cfg(feature = "local-model")]
pub fn run_native_comparison(
    dir: &Path,
    resume: bool,
    kind: ComparisonKind,
    cancel: &Cancellation,
    max_new_scenes: usize,
    assets: NativeAssets<'_>,
    reference: Option<&ValidatedReference>,
) -> Result<ComparisonReportV2> {
    use locallore_local_runtime::LocalRuntime;
    if cancel.is_cancelled() {
        return Err("Interrupted".into());
    }
    if !(1..=4).contains(&max_new_scenes) {
        return Err("SceneBudget".into());
    }
    let profile = native_profile()?;
    let expected = RunManifest::new(
        kind,
        profile.clone(),
        true,
        reference_digest(dir, resume, kind, reference)?,
    )?;
    if resume {
        let actual: RunManifest = decode(&dir.join("run.json"), 128 * 1024)?;
        if actual != expected || !actual.source_matches()? {
            return Err("CheckpointMismatch".into());
        }
        let report = inspect_comparison(dir)?;
        if report.completed {
            return Ok(report);
        }
    }
    let mut session = ComparisonSession::open(dir, resume, expected, reference)?;
    let began = Instant::now();
    let limit = session
        .ledgers
        .iter()
        .map(Ledger::remaining)
        .min()
        .ok_or("RunBudget")?
        .saturating_sub(CLEANUP_RESERVE_MS)
        .min(PREPARATION_MS);
    let stopped = || cancel.is_cancelled() || began.elapsed() >= Duration::from_millis(limit);
    let prepared = (|| {
        let mut runtime = LocalRuntime::spawn_packaged_expected_cancelled(
            assets.resource_dir,
            assets.model,
            &profile.worker_sha256,
            stopped,
        )
        .map_err(|e| format!("Runtime{e:?}"))?;
        if runtime.profile_manifest_sha256() != profile.profile_manifest_sha256 {
            return Err("Profile".into());
        }
        let load = runtime.load(stopped).map_err(|e| format!("Runtime{e:?}"))?;
        Ok((runtime, serde_json::to_value(load).map_err(|_| "Encoding")?))
    })();
    let measured = began.elapsed().as_millis().min(u64::MAX as u128) as u64;
    match prepared {
        Ok((runtime, load)) => {
            session.setup(true, measured, "loaded", Some(load))?;
            session.execute(
                cancel,
                max_new_scenes,
                LaneFactory::Native {
                    runtime: Arc::new(Mutex::new(runtime)),
                    profile,
                },
            )
        }
        Err(error) => {
            // A known terminal setup may settle actual measured cost. A crash or
            // uncompleted setup never reaches this branch and keeps both full reserves.
            session.setup(true, measured, "failed", None)?;
            session.finish_and_publish()?;
            Err(error)
        }
    }
}

/// Fixed grammar only; no provider/corpus/expected JSON/policy/hash/SQL/shell input.
pub fn cli(args: &[String]) -> Result<Value> {
    if args.len() < 2 {
        return Err("Usage".into());
    }
    let dir = Path::new(&args[1]);
    match args[0].as_str() {
        "reference" if args.len() == 2 => {
            return serde_json::to_value(prepare_reference(dir, &Cancellation::default())?)
                .map_err(|_| "Encoding".into())
        }
        "inspect" if args.len() == 2 => {
            return serde_json::to_value(inspect_comparison(dir)?).map_err(|_| "Encoding".into())
        }
        "run" | "resume" => {}
        _ => return Err("Usage".into()),
    }
    let mut kind = None;
    let mut lane = None;
    let mut max = 4;
    let mut reference = None;
    let mut resource = None;
    let mut model = None;
    let mut i = 2;
    let mut seen = BTreeSet::new();
    while i < args.len() {
        if i + 1 >= args.len() || !seen.insert(args[i].as_str()) {
            return Err("Usage".into());
        }
        let value = &args[i + 1];
        match args[i].as_str() {
            "--kind" => {
                kind = Some(match value.as_str() {
                    "paired" => ComparisonKind::PairedSnapshots,
                    "rollout" => ComparisonKind::ContinuousRollout,
                    _ => return Err("Usage".into()),
                })
            }
            "--lane" => lane = Some(value.as_str()),
            "--max-scenes" => {
                max = value.parse::<usize>().map_err(|_| "Usage")?;
                if !(1..=4).contains(&max) {
                    return Err("SceneBudget".into());
                }
            }
            "--reference" => reference = Some(Path::new(value)),
            "--resource-dir" => resource = Some(Path::new(value)),
            "--model" => model = Some(Path::new(value)),
            _ => return Err("Usage".into()),
        }
        i += 2;
    }
    let kind = kind.ok_or("Usage")?;
    let reference = reference.map(open_reference).transpose()?;
    let cancel = Cancellation::default();
    let report = match lane {
        Some("scripted") if resource.is_none() && model.is_none() => run_comparison(
            dir,
            args[0] == "resume",
            kind,
            &cancel,
            max,
            LaneFactory::ScriptedBaseline,
            reference.as_ref(),
        )?,
        Some("native") => {
            #[cfg(feature = "local-model")]
            {
                run_native_comparison(
                    dir,
                    args[0] == "resume",
                    kind,
                    &cancel,
                    max,
                    NativeAssets {
                        resource_dir: resource.ok_or("Usage")?,
                        model: model.ok_or("Usage")?,
                    },
                    reference.as_ref(),
                )?
            }
            #[cfg(not(feature = "local-model"))]
            {
                return Err("NativeFeatureUnavailable".into());
            }
        }
        _ => return Err("Usage".into()),
    };
    serde_json::to_value(report).map_err(|_| "Encoding".into())
}

#[cfg(test)]
mod clock_review_tests;

#[cfg(test)]
mod clock_tests {
    use super::super::*;

    fn directory(name: &str) -> PathBuf {
        let p = std::env::temp_dir().join(format!(
            "locallore-comparison-clock-{name}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&p).unwrap();
        p
    }

    #[test]
    fn zero_adjustment_is_exact_legacy_wall_clock() {
        let p = directory("legacy");
        let l = Ledger::load(&p, "frozen-binding").unwrap();
        for wall in [0, 1, 60_000, 1_800_000, u64::MAX] {
            assert_eq!(l.active_elapsed(wall), wall);
        }
    }

    #[test]
    fn excludes_only_explicitly_measured_other_arm_and_splits_known_setup_once() {
        let p = directory("measured");
        let mut l = Ledger::load(&p, "frozen-binding").unwrap();
        assert_eq!(shared_setup_shares(101), (51, 50));
        assert_eq!(shared_setup_shares(120_000), (60_000, 60_000));
        l.exclude_measured_interval(70).unwrap();
        l.record_shared_setup(101, 51).unwrap();
        // Physical 101 + own 9 + other 70 + own checkpoint 3. Own charge is 63.
        assert_eq!(l.active_elapsed(183), 63);
        assert!(l.record_shared_setup(101, 51).is_err());
        assert_eq!(l.active_elapsed(183), 63);
    }

    #[test]
    fn invalid_setup_and_exclusion_overflow_do_not_mutate_accounting() {
        let p = directory("invalid");
        let mut l = Ledger::load(&p, "frozen-binding").unwrap();
        assert!(l.record_shared_setup(120_001, 1).is_err());
        assert!(l.record_shared_setup(10, 11).is_err());
        assert_eq!(l.active_elapsed(120_001), 120_001);
        l.exclude_measured_interval(u64::MAX).unwrap();
        assert!(l.exclude_measured_interval(1).is_err());
        assert_eq!(l.active_elapsed(u64::MAX), 0);
    }

    #[test]
    fn crash_or_cancel_before_known_terminal_keeps_both_full_setup_reservations() {
        let left = directory("unknown-left");
        let right = directory("unknown-right");
        for p in [&left, &right] {
            let mut l = Ledger::load(p, "frozen-binding").unwrap();
            l.begin_invocation().unwrap();
            // Drop models an interrupted owner; no invented terminal settlement.
        }
        for p in [&left, &right] {
            let l = Ledger::load(p, "frozen-binding").unwrap();
            assert_eq!(l.charged_ms, 120_000);
            assert_eq!(l.invocations, 1);
            assert_eq!(l.charged_roles, 0);
            assert!(!p.join("invocation-00-settled.json").exists());
        }
    }

    #[test]
    fn unknown_turn_reserves_full_roles_and_time_across_reopen() {
        let p = directory("unknown-turn");
        {
            let mut l = Ledger::load(&p, "frozen-binding").unwrap();
            l.begin_invocation().unwrap();
            l.admit("scene-1", "attempt-1").unwrap();
            l.exclude_measured_interval(9_999).unwrap();
        }
        let l = Ledger::load(&p, "frozen-binding").unwrap();
        assert_eq!(l.charged_ms, 180_000);
        assert_eq!(l.charged_roles, 3);
        assert_eq!(l.admissions, 1);
        // Volatile measured exclusions cannot refund previous unknown work.
        assert_eq!(l.active_elapsed(20), 20);
    }

    #[test]
    fn known_terminal_turn_zero_roles_has_exact_durable_charge() {
        let p = directory("guard-terminal");
        {
            let mut l = Ledger::load(&p, "frozen-binding").unwrap();
            l.begin_invocation().unwrap();
            let index = l.admit("scene-1", "guard-1").unwrap();
            l.settle(index, 7, 0).unwrap();
        }
        let l = Ledger::load(&p, "frozen-binding").unwrap();
        assert_eq!(l.charged_ms, 120_007);
        assert_eq!(l.charged_roles, 0);
        assert_eq!(l.admissions, 1);
    }

    #[test]
    fn actual_pending_role_cancel_retains_checkpoint_and_no_canonical_commit() {
        // Run serially with the existing local-lane Pending fixture: its existing
        // polled signal observes an actual production provider poll, not a timer.
        PENDING_POLLED.store(false, Ordering::Release);
        let dir = directory("pending-cancel").join("run");
        let target = dir.clone();
        let cancel = Cancellation::default();
        let other = cancel.clone();
        let worker = std::thread::spawn(move || {
            super::run_comparison(
                &target,
                false,
                super::ComparisonKind::ContinuousRollout,
                &other,
                1,
                LaneFactory::TestFault(TestFault::Pending),
                None,
            )
        });
        let began = Instant::now();
        while !PENDING_POLLED.load(Ordering::Acquire) {
            assert!(
                began.elapsed() < Duration::from_secs(10),
                "actual provider did not become pending"
            );
            std::thread::sleep(Duration::from_millis(2));
        }
        cancel.cancel();
        let report = worker.join().unwrap().unwrap();
        assert!(!report.completed);
        assert_eq!(report.completed_scenes, 0);
        let row = &report.turns[0];
        assert_eq!(row.phase, "cancelled");
        assert_eq!(row.roles, 1);
        assert!(row.roles_known);
        assert!(!row.passed);
        let corpus = crate::memory_comparison::frozen_suite().unwrap();
        assert_eq!(
            engine(&dir.join("left/synthetic.sqlite"), &corpus.seed().scope)
                .unwrap()
                .revision(),
            0
        );
        assert!(dir.join("left/attempt-00.json").exists());
        assert!(dir.join("left/admission-00-settled.json").exists());
    }

    // Source-frozen only. This needs explicitly approved, already installed assets
    // to construct a REAL native owner; it performs no load/generation and remains
    // ignored in ordinary/default/all-feature qualification.
    #[cfg(feature = "local-model")]
    #[test]
    #[ignore = "requires explicit approved local assets; no inference; opt-in ownership gate"]
    fn public_comparison_rejects_a_real_preowned_native_before_admission() {
        use locallore_local_runtime::LocalRuntime;
        let resource = PathBuf::from(
            std::env::var_os("LOCALLORE_COMPARISON_TEST_RESOURCES")
                .expect("explicit approved resources"),
        );
        let model = PathBuf::from(
            std::env::var_os("LOCALLORE_COMPARISON_TEST_MODEL").expect("explicit approved model"),
        );
        let profile = native_profile().unwrap();
        let runtime = LocalRuntime::spawn_packaged_expected_cancelled(
            &resource,
            &model,
            &profile.worker_sha256,
            || false,
        )
        .unwrap();
        let dir = directory("preowned").join("must-not-exist");
        let result = super::run_comparison(
            &dir,
            false,
            super::ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::Native {
                runtime: Arc::new(Mutex::new(runtime)),
                profile,
            },
            None,
        );
        assert!(matches!(result,Err(ref e) if e=="UseNativeComparisonEntry"));
        assert!(!dir.exists());
    }
}

#[cfg(test)]
mod forwarded_budget_tests {
    use super::*;

    #[test]
    fn historical_binding_is_viewable_under_its_original_key_but_never_resumable() {
        // Pure transport compatibility fixture, not relabelled old execution.
        let current = RunManifest::new(
            ComparisonKind::ContinuousRollout,
            LaneFactory::ScriptedBaseline.profile().unwrap(),
            false,
            None,
        )
        .unwrap();
        let mut historical = current.clone();
        historical.binding.forwarded_budget_version = None;
        let mut old_shape = serde_json::to_value(&current).unwrap();
        old_shape["binding"]
            .as_object_mut()
            .unwrap()
            .remove("forwarded_budget_version");
        assert_eq!(serde_json::to_value(&historical).unwrap(), old_shape);
        let decoded: RunManifest = serde_json::from_value(old_shape).unwrap();
        assert_eq!(
            decoded.stable_key().unwrap(),
            historical.stable_key().unwrap()
        );
        assert_ne!(decoded.stable_key().unwrap(), current.stable_key().unwrap());
        decoded.validate().unwrap();
        assert!(!decoded.source_matches().unwrap());
        let mut unknown = historical;
        unknown.binding.forwarded_budget_version = Some(2);
        assert!(unknown.validate().is_err());
    }

    #[test]
    fn actual_host_capture_requires_unchanged_current_forwarded_estimates() {
        let root = std::env::temp_dir().join(format!(
            "locallore-forwarded-evidence-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&root).unwrap();
        let run = root.join("run");
        let report = run_comparison(
            &run,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!(report.turns.len(), 12);
        assert!(report.turns.iter().all(|r| r.passed));
        for row in &report.turns {
            let estimates = row.forwarded_director_estimates.as_ref().unwrap();
            assert_eq!(estimates.len(), 1);
            assert_eq!(estimates[0]["version"], 1);
            assert_eq!(estimates[0]["output_tokens"], 350);
            assert!(estimates[0]["estimated_total_tokens"].as_u64().unwrap() <= 4096);
        }
        assert_eq!(inspect_comparison(&run).unwrap(), report);
        // Existing own synthetic checkpoint only. Never edit a historical report.
        let checkpoint = checkpoint_path(&run.join("left"), 0);
        let original = fs::read(&checkpoint).unwrap();
        let mut altered: Value = serde_json::from_slice(&original).unwrap();
        altered["row"]
            .as_object_mut()
            .unwrap()
            .remove("forwarded_director_estimates");
        fs::write(&checkpoint, encode(&altered).unwrap()).unwrap();
        assert!(inspect_comparison(&run).is_err());
        let mut altered: Value = serde_json::from_slice(&original).unwrap();
        altered["row"]["forwarded_director_estimates"][0]["estimated_total_tokens"] = json!(0);
        fs::write(&checkpoint, encode(&altered).unwrap()).unwrap();
        assert!(inspect_comparison(&run).is_err());
        fs::write(&checkpoint, original).unwrap();
        assert_eq!(inspect_comparison(&run).unwrap(), report);
        // Missing optional old transport field stays omitted, not invented.
        let mut old_row = serde_json::to_value(&report.turns[0]).unwrap();
        old_row
            .as_object_mut()
            .unwrap()
            .remove("forwarded_director_estimates");
        let decoded: TurnReportV2 = serde_json::from_value(old_row.clone()).unwrap();
        assert!(decoded.forwarded_director_estimates.is_none());
        assert_eq!(serde_json::to_value(decoded).unwrap(), old_row);
    }

    // These fixtures originate in ONE actual existing Host/Store operation.
    // Mutations affect only copied diagnostic values and their paired recording
    // hashes, never canonical records, budgets, expected commands or providers.
    struct ValidHostCaptureFixture {
        before: Engine,
        request: Request,
        reply: Value,
        captures: Vec<crate::Capture>,
        profile: PlayProfile,
        attempt: u32,
    }
    impl ValidHostCaptureFixture {
        fn new(factory: LaneFactory) -> Self {
            let directory = std::env::temp_dir().join(format!(
                "locallore-forwarded-rehash-{}-{}",
                std::process::id(),
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_nanos()
            ));
            fs::create_dir(&directory).unwrap();
            let corpus = suite().unwrap();
            let before = Engine::new(corpus.seed().clone()).unwrap();
            let step = &corpus.steps()[0];
            let request = step.request(&before);
            let profile = factory.profile().unwrap();
            let manifest = RunManifest::new(
                ComparisonKind::ContinuousRollout,
                profile.clone(),
                false,
                None,
            )
            .unwrap();
            let binding = manifest.stable_key().unwrap();
            let path = directory.join("synthetic.sqlite");
            ensure_database(&path, corpus.seed(), &[]).unwrap();
            let mut ledger = Ledger::load(&directory, &binding).unwrap();
            ledger.begin_invocation().unwrap();
            let turn = execute_turn(
                TurnJob {
                    dir: &directory,
                    path: &path,
                    index: 0,
                    arm: "left",
                    policy: ContextPolicy::StateRelevantMemoryV1,
                    binding: &binding,
                    step,
                    factory: &factory,
                    cancel: &Cancellation::default(),
                },
                &mut ledger,
            )
            .unwrap();
            ledger.finish().unwrap();
            assert_eq!(turn.row.phase, "committed");
            assert!(turn.row.passed);
            let reply: Value = decode(
                &directory.join(turn.capture_file.as_ref().unwrap()),
                v2::MAX_PRIVATE_CAPTURE + 4096,
            )
            .unwrap();
            let recording: RecordingFile = decode(
                &directory.join(turn.recording_file.as_ref().unwrap()),
                64 * 1024,
            )
            .unwrap();
            let attempt = u32::try_from(
                reply["data"]["details"]["identity"]["attempt"]
                    .as_u64()
                    .unwrap(),
            )
            .unwrap();
            let fixture = Self {
                before,
                request,
                reply,
                captures: recording.captures,
                profile,
                attempt,
            };
            fixture.assert_transport_bounds_and_recording_hashes();
            assert!(
                fixture.checked().is_ok(),
                "actual original capture must be valid"
            );
            fixture
        }
        fn checked(&self) -> Result<CapturedContext> {
            CapturedContext::from_host_capture(
                &self.before,
                &self.request,
                self.attempt,
                &self.reply,
                &self.captures,
                &self.profile,
                Some(1),
            )
        }
        fn rejection(&self) -> String {
            match self.checked() {
                Err(error) => error,
                Ok(_) => panic!("mutated current capture unexpectedly passed"),
            }
        }
        fn director(&self, ordinal: usize) -> &Value {
            self.reply["data"]["details"]["artifacts"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|a| {
                    a["kind"] == "generation_request" && a["value"]["input"]["role"] == "director"
                })
                .nth(ordinal)
                .map(|a| &a["value"])
                .unwrap()
        }
        fn director_mut(&mut self, ordinal: usize) -> &mut Value {
            self.reply["data"]["details"]["artifacts"]
                .as_array_mut()
                .unwrap()
                .iter_mut()
                .filter(|a| {
                    a["kind"] == "generation_request" && a["value"]["input"]["role"] == "director"
                })
                .nth(ordinal)
                .map(|a| &mut a["value"])
                .unwrap()
        }
        fn change_prompt_with_matching_recording_hash(&mut self, ordinal: usize, prompt: String) {
            let value = self.director(ordinal);
            let old_prompt = digest(value["input"]["prompt"].as_str().unwrap().as_bytes());
            let schema = digest(&encode(&value["input"]["schema"]).unwrap());
            let index = self
                .captures
                .iter()
                .position(|c| {
                    c.role == "director"
                        && c.prompt_sha256 == old_prompt
                        && c.schema_sha256 == schema
                })
                .unwrap();
            self.captures[index].prompt_sha256 = digest(prompt.as_bytes());
            self.director_mut(ordinal)["input"]["prompt"] = json!(prompt);
        }
        fn change_schema_with_matching_recording_hash(&mut self, ordinal: usize, schema: Value) {
            let value = self.director(ordinal);
            let prompt = digest(value["input"]["prompt"].as_str().unwrap().as_bytes());
            let old_schema = digest(&encode(&value["input"]["schema"]).unwrap());
            let index = self
                .captures
                .iter()
                .position(|c| {
                    c.role == "director"
                        && c.prompt_sha256 == prompt
                        && c.schema_sha256 == old_schema
                })
                .unwrap();
            self.captures[index].schema_sha256 = digest(&encode(&schema).unwrap());
            self.director_mut(ordinal)["input"]["schema"] = schema;
        }
        fn assert_transport_bounds_and_recording_hashes(&self) {
            assert!(encode(&self.reply).unwrap().len() <= v2::MAX_PRIVATE_CAPTURE + 4096);
            let artifacts = self.reply["data"]["details"]["artifacts"]
                .as_array()
                .unwrap();
            assert!(artifacts.len() <= 16);
            assert!(encode(artifacts).unwrap().len() <= v2::MAX_PRIVATE_CAPTURE);
            for artifact in artifacts {
                assert!(encode(artifact).unwrap().len() <= 49_152 + 128);
                if artifact["kind"] != "generation_request" {
                    continue;
                }
                let value = &artifact["value"];
                let prompt = value["input"]["prompt"].as_str().unwrap();
                let schema = encode(&value["input"]["schema"]).unwrap();
                assert!(prompt.len() <= 32000);
                assert!(schema.len() <= MAX_PROPOSAL_BYTES);
                assert!(
                    self.captures.iter().any(|capture| {
                        capture.turn == self.request.turn
                            && capture.role == value["input"]["role"].as_str().unwrap()
                            && capture.prompt_sha256 == digest(prompt.as_bytes())
                            && capture.schema_sha256 == digest(&schema)
                    }),
                    "every actual role must retain matching recording hashes"
                );
            }
        }
    }

    #[test]
    fn rehashed_actual_prompt_suffix_outside_context_json_is_rejected_by_combined_budget() {
        let mut fixture = ValidHostCaptureFixture::new(LaneFactory::ScriptedBaseline);
        let original = fixture.director(0)["input"]["prompt"]
            .as_str()
            .unwrap()
            .to_owned();
        let expanded = format!("{original}{}", "x".repeat(12000));
        let schema_bytes = encode(&fixture.director(0)["input"]["schema"])
            .unwrap()
            .len();
        assert!(expanded.len() <= 32000);
        assert!((expanded.len() + schema_bytes + 114).div_ceil(4) + 350 + 162 > 4096);
        // Padding is after the original prompt, so its embedded ContextJSON and
        // actual eligible selected-record projection remain unchanged.
        fixture.change_prompt_with_matching_recording_hash(0, expanded);
        fixture.assert_transport_bounds_and_recording_hashes();
        assert_eq!(fixture.rejection(), "CaptureForwardedBudget");
    }

    #[test]
    fn rehashed_actual_schema_below_byte_cap_is_rejected_by_combined_budget() {
        let mut fixture = ValidHostCaptureFixture::new(LaneFactory::ScriptedBaseline);
        let mut schema = fixture.director(0)["input"]["schema"].clone();
        schema["x-budget-padding"] = json!("");
        let unpadded = encode(&schema).unwrap().len();
        assert!(unpadded < 15000);
        schema["x-budget-padding"] = json!("s".repeat(15000 - unpadded));
        let padded_bytes = encode(&schema).unwrap().len();
        assert_eq!(padded_bytes, 15000);
        assert!(padded_bytes < MAX_PROPOSAL_BYTES);
        let prompt_bytes = fixture.director(0)["input"]["prompt"]
            .as_str()
            .unwrap()
            .len();
        assert!((prompt_bytes + 15000 + 114).div_ceil(4) + 350 + 162 > 4096);
        fixture.change_schema_with_matching_recording_hash(0, schema);
        fixture.assert_transport_bounds_and_recording_hashes();
        assert_eq!(fixture.rejection(), "CaptureForwardedBudget");
    }

    #[test]
    fn actual_request_output351_is_rejected_before_estimate_metadata() {
        let mut fixture = ValidHostCaptureFixture::new(LaneFactory::ScriptedBaseline);
        fixture.director_mut(0)["budget"]["max_output_tokens"] = json!(351);
        fixture.assert_transport_bounds_and_recording_hashes();
        assert_eq!(fixture.rejection(), "CaptureBinding");
    }

    #[test]
    fn rehashed_actual_second_director_extra_whitespace_is_rejected_as_invalid_repair() {
        let mut fixture =
            ValidHostCaptureFixture::new(LaneFactory::TestFault(TestFault::MalformedRepair));
        assert_eq!(
            fixture
                .captures
                .iter()
                .filter(|c| c.role == "director")
                .count(),
            2
        );
        assert_eq!(fixture.captures.len(), 3);
        let initial = fixture.director(0)["input"]["prompt"].as_str().unwrap();
        let repair = fixture.director(1)["input"]["prompt"].as_str().unwrap();
        assert!(locallore::play::director_repair_matches_v25(
            initial, repair
        ));
        let expanded = format!("{repair} ");
        assert!(!locallore::play::director_repair_matches_v25(
            initial, &expanded
        ));
        fixture.change_prompt_with_matching_recording_hash(1, expanded);
        fixture.assert_transport_bounds_and_recording_hashes();
        assert_eq!(fixture.rejection(), "CaptureRepairMismatch");
    }
}
