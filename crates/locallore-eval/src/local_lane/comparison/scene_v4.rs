//! Protocol4 scene narration comparison over the existing owners.
//! Native execution requires its trusted lease entry; selected/UI and CLI
//! native execution remain unavailable pending their separate integration.
use super::*;
#[cfg(feature = "local-model")]
mod native;
#[cfg(test)]
mod noncommit_privacy_review_tests;
use crate::memory_comparison_v4::{
    self as v4, ArmDescriptorV4, ComparisonArmV4, ComparisonReportV4,
    ConstructionEvidenceStatusV4 as Status, CurrentBindingV4, TurnReportV4,
};
use locallore::host::HostPlayConstructionV1;
#[cfg(feature = "local-model")]
pub use native::run_native_comparison;

const CONSTRUCTIONS: [ComparisonArmV4; 2] = [
    ComparisonArmV4::LiteralSceneV1,
    ComparisonArmV4::RelevantMemorySceneV1,
];
fn descriptor(arm: ComparisonArmV4) -> ArmDescriptorV4 {
    v4::arm_descriptors()[usize::from(arm == ComparisonArmV4::RelevantMemorySceneV1)].clone()
}
fn host_construction(arm: ComparisonArmV4) -> HostPlayConstructionV1 {
    match arm {
        ComparisonArmV4::LiteralSceneV1 => HostPlayConstructionV1::PlayerLiteralSceneV1,
        ComparisonArmV4::RelevantMemorySceneV1 => {
            HostPlayConstructionV1::MemorySceneV1(ContextPolicy::StateRelevantMemoryV1)
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    version: u16,
    source_sha256: String,
    binding: CurrentBindingV4,
    profile: PlayProfile,
    kind: ComparisonKind,
    #[serde(deserialize_with = "v4::required_nullable")]
    reference_sha256: Option<String>,
    order: String,
}
// V4 closes all eight writer keys, including an explicit null load. Keep the
// historical V2 setup decoder unchanged. This is diagnostic metadata only.
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Setup4 {
    version: u16,
    binding: String,
    left_invocation: usize,
    right_invocation: usize,
    native: bool,
    physical_ms: u64,
    status: String,
    #[serde(deserialize_with = "v4::required_nullable")]
    load: Option<Value>,
}
impl Manifest {
    fn new(
        kind: ComparisonKind,
        profile: PlayProfile,
        reference_sha256: Option<String>,
    ) -> Result<Self> {
        Self::new_with_lane(kind, profile, false, reference_sha256)
    }
    fn new_with_lane(
        kind: ComparisonKind,
        profile: PlayProfile,
        native: bool,
        reference_sha256: Option<String>,
    ) -> Result<Self> {
        let binding = v4::current_binding(native)?;
        Ok(Self {
            version: 4,
            source_sha256: binding.source_sha256.clone(),
            binding,
            profile,
            kind,
            reference_sha256,
            order: "alternate-first-v1".into(),
        })
    }
    fn key(&self) -> Result<String> {
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
        let current = v4::current_binding(self.binding.native)?;
        Ok(self.source_sha256 == current.source_sha256 && self.binding == current)
    }
    fn validate(&self) -> Result<()> {
        match (self.kind, self.reference_sha256.as_deref()) {
            (ComparisonKind::ContinuousRollout, None) => {}
            (ComparisonKind::PairedSnapshots, Some(hash)) if hex(hash) => {}
            _ => return Err("ReferenceBinding".into()),
        }
        for arm in &self.binding.arms {
            arm.validate()?;
        }
        let current = Self::new_with_lane(
            self.kind,
            self.profile.clone(),
            self.binding.native,
            self.reference_sha256.clone(),
        )?;
        if self.version != 4
            || self.key()? != current.key()?
            || !hex(&self.source_sha256)
            || !hex(&self.binding.source_sha256)
        {
            return Err("ComparisonBinding".into());
        }
        self.profile.validate().map_err(|_| "Profile")?;
        if self.profile.context_tokens != 4096
            || self.profile.director_tokens != 350
            || self.profile.narrator_tokens != 350
            || self.profile.deadline_ms != 120_000
            || self.profile.repair_limit != 1
        {
            return Err("Profile".into());
        }
        Ok(())
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct StoredTurn4 {
    version: u16,
    binding: String,
    index: usize,
    arm: String,
    request: Request,
    before_head: u64,
    after_head: u64,
    row: TurnReportV4,
    #[serde(deserialize_with = "v4::required_nullable")]
    capture_file: Option<String>,
    #[serde(deserialize_with = "v4::required_nullable")]
    recording_file: Option<String>,
}
struct Observation4<'a> {
    dir: &'a Path,
    step: &'a protocol::Step,
    arm: &'a str,
    construction: ComparisonArmV4,
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
}
fn expected_recipe(arm: ComparisonArmV4) -> locallore::play::scene_narration::SceneRecipeV1 {
    use locallore::play::scene_narration::SceneRecipeV1;
    match arm {
        ComparisonArmV4::LiteralSceneV1 => SceneRecipeV1::LiteralV1,
        ComparisonArmV4::RelevantMemorySceneV1 => {
            SceneRecipeV1::Memory(ContextPolicy::StateRelevantMemoryV1)
        }
    }
}
// Finite sentinel checks require actual available calls and output. An absent
// diagnostic cannot turn into a privacy success through a vacuous all().
#[derive(Clone, Copy, PartialEq, Eq)]
enum FinitePrivacy {
    Checked,
    Unavailable,
    Violation,
}
fn finite_privacy(
    dir: &Path,
    recording: &RecordingFile,
    capture: &Value,
    receipt: &Receipt,
) -> FinitePrivacy {
    let forbidden = |text: &str, narrator: bool| {
        EXCLUSIONS.iter().any(|sentinel| text.contains(sentinel))
            || (narrator && text.contains("SECRET-TIDE-731"))
    };
    if recording.forbidden_director_prompt
        || recording.forbidden_narrator_prompt
        || recording.forbidden_narrator_output
        || forbidden(receipt.narration(), true)
    {
        return FinitePrivacy::Violation;
    }
    let Some(artifacts) = capture["data"]["details"]["artifacts"].as_array() else {
        return FinitePrivacy::Unavailable;
    };
    let requests = artifacts
        .iter()
        .filter(|a| a["kind"] == "generation_request");
    let count = requests.clone().count();
    let mut unavailable = recording.lost || count == 0 || count != recording.captures.len();
    for artifact in requests {
        let input = &artifact["value"]["input"];
        let (Some(prompt), Some(role)) = (input["prompt"].as_str(), input["role"].as_str()) else {
            unavailable = true;
            continue;
        };
        if !matches!(role, "director" | "narrator") || prompt.is_empty() {
            unavailable = true;
            continue;
        }
        if forbidden(prompt, role == "narrator") {
            return FinitePrivacy::Violation;
        }
    }
    // These are retained diagnostic observations, not proof of output origin.
    // Empty, unreadable, malformed or inconsistent bytes cannot complete a check.
    let mut narrator_seen = false;
    for raw in recording.raw.iter().filter(|raw| raw.role == "narrator") {
        narrator_seen = true;
        let Ok(bytes) = read(&dir.join(&raw.file), 16_384) else {
            unavailable = true;
            continue;
        };
        if bytes.is_empty() || bytes.len() != raw.bytes || digest(&bytes) != raw.sha256 {
            unavailable = true;
            continue;
        }
        let Ok(text) = std::str::from_utf8(&bytes) else {
            unavailable = true;
            continue;
        };
        if forbidden(text, true) {
            return FinitePrivacy::Violation;
        }
    }
    if unavailable || !narrator_seen {
        FinitePrivacy::Unavailable
    } else {
        FinitePrivacy::Checked
    }
}
fn make_row4(o: Observation4<'_>) -> Result<TurnReportV4> {
    use crate::memory_comparison_v4::PrivacyEvidenceStatusV4 as Privacy;
    use crate::scene_capture_v1::{check_committed_scene_capture_v1, SceneCaptureInputV1};
    use locallore::play::scene_narration::SCENE_NARRATION_POLICY_V1;
    let Observation4 {
        dir,
        step,
        arm,
        construction,
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
    } = o;
    let request = step.request(before);
    let roles = recording.map_or(0, |r| r.roles);
    let assessment = turn_execution::assess_outcome(
        before,
        after,
        step,
        phase,
        error.as_deref(),
        receipt,
        roles,
    )?;
    let guard_ok = assessment.guard && assessment.expected_ok && roles == 0 && !recovered;
    let record = receipt.and_then(Receipt::play);
    let construction_matches = record.map_or(guard_ok, |p| {
        p.version == locallore::play::PLAY_VERSION
            && p.policy == SCENE_NARRATION_POLICY_V1
            && p.profile == *profile
            && p.prompt_version == descriptor(construction).prompt_version
            && p.scene
                .as_ref()
                .is_some_and(|s| s.version == 1 && hex(&s.frame_sha256))
            && match construction {
                ComparisonArmV4::LiteralSceneV1 => {
                    p.context.is_none() && p.context_policy.is_none()
                }
                ComparisonArmV4::RelevantMemorySceneV1 => {
                    p.context_policy == Some(ContextPolicy::StateRelevantMemoryV1)
                        && p.context
                            .as_ref()
                            .is_some_and(|c| c.version == 2 && c.compiler_version == 2)
                }
            }
    });
    let (checked, reason) = if recovered {
        (
            None,
            Some("recovered_without_original_checkpoint_and_calls".into()),
        )
    } else if guard_ok || phase == "not_run_dependency" {
        (None, None)
    } else if phase != "committed" || receipt.is_none() {
        (None, Some("non_committed_turn".into()))
    } else if recording.is_some_and(|r| r.lost) {
        (None, Some("recording_loss".into()))
    } else if let (Some(recording), Some(capture)) = (recording, capture) {
        if let Some(attempt) = capture["data"]["details"]["identity"]["attempt"]
            .as_u64()
            .and_then(|n| u32::try_from(n).ok())
        {
            match check_committed_scene_capture_v1(SceneCaptureInputV1 {
                before,
                after,
                request: &request,
                expected_recipe: expected_recipe(construction),
                expected_profile: profile,
                attempt,
                details_reply: capture,
                recordings: &recording.captures,
            }) {
                Ok(value) => (Some(value), None),
                Err(error) => (None, Some(format!("scene_capture:{error:?}"))),
            }
        } else {
            (None, Some("capture_attempt_unavailable".into()))
        }
    } else {
        (None, Some("capture_or_recording_unavailable".into()))
    };
    let actual_receipt_sha256 = receipt
        .map(|r| encode(r).map(|bytes| digest(&bytes)))
        .transpose()?;
    if checked
        .as_ref()
        .is_some_and(|value| Some(value.receipt_sha256()) != actual_receipt_sha256.as_deref())
    {
        return Err("CaptureReceiptBinding".into());
    }
    let evidence_status = if recovered {
        Status::Unavailable
    } else if guard_ok {
        Status::NotApplicableGuard
    } else if phase == "not_run_dependency" {
        Status::NotApplicableDependency
    } else if checked.is_some() {
        Status::ValidatedCommittedSceneNarratorV1
    } else {
        Status::Unavailable
    };
    let privacy_observation = match (recording, capture, receipt) {
        (Some(recording), Some(capture), Some(receipt)) => {
            finite_privacy(dir, recording, capture, receipt)
        }
        _ => FinitePrivacy::Unavailable,
    };
    let privacy_checked = checked.is_some() && privacy_observation == FinitePrivacy::Checked;
    let privacy_status = if guard_ok {
        Privacy::NotApplicableGuard
    } else if privacy_checked {
        Privacy::CheckedFiniteSentinels
    } else {
        Privacy::Unavailable
    };
    let evidence_ok = guard_ok || checked.is_some();
    let mut failures = Vec::new();
    if !assessment.expected_ok {
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
    if !construction_matches && !guard_ok {
        failures.push("no_matching_construction_receipt".into());
    }
    if !evidence_ok {
        failures.push("scene_capture_unavailable".into());
    }
    if !guard_ok && !privacy_checked {
        failures.push(
            match privacy_observation {
                FinitePrivacy::Violation => "observer_or_output_privacy_violation",
                _ => "observer_or_output_privacy_evidence_unavailable",
            }
            .into(),
        );
    }
    if recovered {
        failures.push("unknown_historical_calls_and_checkpoint".into());
    }
    if recording.is_some_and(|r| r.lost) {
        failures.push("recording_loss".into());
    }
    let source_fallback_reason = record
        .and_then(|r| r.context.as_ref())
        .and_then(|c| serde_json::to_value(c.source_fallback_reason).ok())
        .and_then(|v| v.as_str().map(str::to_owned));
    let compiler_fallback_reason = record
        .and_then(|r| r.context.as_ref())
        .and_then(|c| serde_json::to_value(c.coverage.set_fallback_reason).ok())
        .and_then(|v| v.as_str().map(str::to_owned));
    Ok(TurnReportV4 {
        turn: step.id().into(),
        scene: step.scene(),
        arm: arm.into(),
        construction: descriptor(construction),
        phase: phase.into(),
        error,
        expected: serde_json::to_string(step.expected()).map_err(|_| "Encoding")?,
        passed: assessment.expected_ok
            && construction_matches
            && evidence_ok
            && (guard_ok || privacy_checked)
            && !recovered
            && recording.is_none_or(|r| !r.lost),
        failures,
        quality_flags: if record.is_some_and(|r| r.fallback) {
            vec!["narration_fallback_no_quality_acceptance".into()]
        } else {
            vec![]
        },
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
        construction_matches,
        construction_evidence_status: evidence_status,
        construction_evidence_reason: reason,
        narrator_prompt_sha256: checked.as_ref().map(|c| c.narrator_prompt_sha256().into()),
        narrator_schema_sha256: checked.as_ref().map(|c| c.narrator_schema_sha256().into()),
        scene_frame_sha256: checked
            .as_ref()
            .and_then(|_| record.and_then(|r| r.scene.as_ref()))
            .map(|s| s.frame_sha256.clone()),
        actual_receipt_sha256,
        privacy_evidence_status: privacy_status,
        fallback: record.map(|r| r.fallback),
        repairs: record.map(|r| r.repairs),
        narration: receipt.map(|r| r.narration().to_owned()),
        capture_sha256: capture
            .map(|c| encode(c).map(|bytes| digest(&bytes)))
            .transpose()?,
        recording_sha256: recording
            .map(|r| encode(r).map(|bytes| digest(&bytes)))
            .transpose()?,
        raw_sha256: recording.map_or_else(Vec::new, |r| {
            r.raw.iter().map(|r| r.sha256.clone()).collect()
        }),
        role_metrics: recording.and_then(|r| r.role_metrics.clone()),
        trace,
        stages: record.map_or_else(Vec::new, |r| {
            r.stages
                .iter()
                .filter_map(|s| serde_json::to_value(s).ok())
                .collect()
        }),
        source_fallback_reason,
        compiler_fallback_reason,
    })
}
struct ReadyJob4<'a> {
    path: &'a Path,
    full: &'a Engine,
    index: usize,
    arm: &'a str,
    construction: ComparisonArmV4,
    binding: &'a str,
    step: &'a protocol::Step,
    profile: &'a PlayProfile,
}
fn ready_turn4(job: ReadyJob4<'_>) -> Result<Option<StoredTurn4>> {
    let ReadyJob4 {
        path,
        full,
        index,
        arm,
        construction,
        binding,
        step,
        profile,
    } = job;
    let recovered = turn_execution::recover_actual(path, full, step)?;
    if recovered.is_some() || turn_execution::dependency_missing(full, step, profile)? {
        let is_recovered = recovered.is_some();
        let before = recovered.as_ref().map_or(full, |r| &r.before);
        let after = recovered.as_ref().map_or(full, |r| &r.after);
        let row = make_row4(Observation4 {
            dir: path.parent().ok_or("Workspace")?,
            step,
            arm,
            construction,
            before,
            after,
            phase: if is_recovered {
                "committed"
            } else {
                "not_run_dependency"
            },
            error: None,
            receipt: recovered.as_ref().map(|r| &r.receipt),
            recording: None,
            capture: None,
            trace: None,
            admission: None,
            elapsed_ms: 0,
            first_final_response_ms: None,
            commit_elapsed_ms: None,
            profile,
            recovered: is_recovered,
        })?;
        return Ok(Some(StoredTurn4 {
            version: 4,
            binding: binding.into(),
            index,
            arm: arm.into(),
            request: step.request(before),
            before_head: before.revision(),
            after_head: after.revision(),
            row,
            capture_file: None,
            recording_file: None,
        }));
    }
    Ok(None)
}
struct Job4<'a> {
    dir: &'a Path,
    path: &'a Path,
    index: usize,
    arm: &'a str,
    construction: ComparisonArmV4,
    binding: &'a str,
    step: &'a protocol::Step,
    factory: &'a LaneFactory,
    cancel: &'a Cancellation,
}
fn execute_turn4(job: Job4<'_>, ledger: &mut Ledger) -> Result<StoredTurn4> {
    let Job4 {
        dir,
        path,
        index,
        arm,
        construction,
        binding,
        step,
        factory,
        cancel,
    } = job;
    let full = engine(path, &suite()?.seed().scope)?;
    if full.domain_version() != 1 {
        return Err("UnsupportedDomain".into());
    }
    let profile = factory.profile()?;
    if let Some(turn) = ready_turn4(ReadyJob4 {
        path,
        full: &full,
        index,
        arm,
        construction,
        binding,
        step,
        profile: &profile,
    })? {
        return Ok(turn);
    }
    let actual = turn_execution::execute(
        turn_execution::LiveTurnJob {
            dir,
            path,
            index,
            step,
            factory,
            cancel,
            construction: host_construction(construction),
            before: full,
            profile,
        },
        ledger,
    )?;
    let row = make_row4(Observation4 {
        dir,
        step,
        arm,
        construction,
        before: &actual.before,
        after: &actual.after,
        phase: &actual.phase,
        error: actual.error.clone(),
        receipt: actual.receipt.as_ref(),
        recording: Some(&actual.recording),
        capture: actual.capture.as_ref(),
        trace: actual.trace.clone(),
        admission: Some(actual.admission),
        elapsed_ms: actual.elapsed_ms,
        first_final_response_ms: actual.first_final_response_ms,
        commit_elapsed_ms: actual.commit_elapsed_ms,
        profile: &actual.profile,
        recovered: false,
    })?;
    let result = StoredTurn4 {
        version: 4,
        binding: binding.into(),
        index,
        arm: arm.into(),
        request: actual.request.clone(),
        before_head: actual.before.revision(),
        after_head: actual.after.revision(),
        row,
        capture_file: actual.capture_file.clone(),
        recording_file: Some(actual.recording_file.clone()),
    };
    actual.checkpoint_and_settle(dir, index, &result, ledger)?;
    Ok(result)
}
fn load_turn4(
    dir: &Path,
    path: &Path,
    index: usize,
    arm: usize,
    key: &str,
    manifest: &Manifest,
) -> Result<StoredTurn4> {
    let stored: StoredTurn4 = decode(&checkpoint_path(dir, index), 256 * 1024)?;
    if stored.version != 4
        || stored.index != index
        || stored.arm != ARM_NAMES[arm]
        || stored.binding != key
    {
        return Err("CheckpointMismatch".into());
    }
    let evidence = turn_execution::load_evidence(
        dir,
        path,
        index,
        key,
        &turn_execution::CheckpointMeta {
            request: stored.request.clone(),
            before_head: stored.before_head,
            after_head: stored.after_head,
            capture_file: stored.capture_file.clone(),
            recording_file: stored.recording_file.clone(),
            row: turn_execution::CheckpointRowMeta {
                admission: stored.row.admission,
                elapsed_ms: stored.row.elapsed_ms,
                roles_known: stored.row.roles_known,
                roles: stored.row.roles,
                phase: stored.row.phase.clone(),
            },
        },
    )?;
    let corpus = suite()?;
    let actual = make_row4(Observation4 {
        dir,
        step: &corpus.steps()[index],
        arm: ARM_NAMES[arm],
        construction: CONSTRUCTIONS[arm],
        before: &evidence.before,
        after: &evidence.after,
        phase: &stored.row.phase,
        error: stored.row.error.clone(),
        receipt: evidence.receipt.as_ref(),
        recording: evidence.recording.as_ref(),
        capture: evidence.capture.as_ref(),
        trace: stored.row.trace.clone(),
        admission: stored.row.admission,
        elapsed_ms: stored.row.elapsed_ms,
        first_final_response_ms: stored.row.first_final_response_ms,
        commit_elapsed_ms: stored.row.commit_elapsed_ms,
        profile: &manifest.profile,
        recovered: stored.row.recovered_without_checkpoint,
    })?;
    if actual != stored.row {
        return Err("CheckpointEvidenceMismatch".into());
    }
    Ok(stored)
}
fn load_turns4(dir: &Path, manifest: &Manifest, key: &str) -> Result<[Vec<StoredTurn4>; 2]> {
    let corpus = suite()?;
    let mut result: [Vec<StoredTurn4>; 2] = [Vec::new(), Vec::new()];
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
            let t = load_turn4(
                &d,
                &database(&d, index, manifest.kind),
                index,
                arm,
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
            validate_rollout_source(&engine(&db, &corpus.seed().scope)?, &corpus)?;
        }
    }
    Ok(result)
}
fn scene_data4(dir: &Path, key: &str, scene: usize) -> Result<SceneManifest> {
    let mut value = scene_data(dir, key, scene)?;
    value.version = 4;
    Ok(value)
}
fn sealed_scenes4(dir: &Path, key: &str) -> Result<usize> {
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
        if stored != scene_data4(dir, key, scene)? {
            return Err("SceneIntegrity".into());
        }
        count += 1;
    }
    Ok(count)
}
struct Session4 {
    dir: PathBuf,
    manifest: Manifest,
    key: String,
    _lock: File,
    ledgers: [Ledger; 2],
    turns: [Vec<StoredTurn4>; 2],
    reference: Option<ValidatedReference>,
}
impl Session4 {
    fn open(
        dir: &Path,
        resume: bool,
        expected: Manifest,
        reference: Option<&ValidatedReference>,
        started: Instant,
    ) -> Result<Self> {
        expected.validate()?;
        ordinary(dir)?;
        if resume {
            let actual: Manifest = decode(&dir.join("run.json"), 128 * 1024)?;
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
        let key = expected.key()?;
        let turns = load_turns4(dir, &expected, &key)?;
        sealed_scenes4(dir, &key)?;
        if let Some(reference) = &reference {
            let corpus = suite()?;
            for arm in 0..2 {
                for index in turns[arm].len()..corpus.steps().len() {
                    validate_pair_source(
                        &database(&dir.join(ARM_NAMES[arm]), index, expected.kind),
                        corpus.seed(),
                        reference.prefix(index)?,
                        &corpus.steps()[index],
                    )?;
                }
            }
        }
        let ledgers = turn_execution::load_pair(dir, &key, started)?;
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
    fn begin_invocations(&mut self) -> Result<()> {
        turn_execution::begin_loaded_pair(&mut self.ledgers)
    }
    fn finish(mut self) -> Result<ComparisonReportV4> {
        let mut report = inspect_comparison(&self.dir)?;
        turn_execution::finish_pair(&mut self.ledgers)?;
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
        publish4(&self.dir, &report)?;
        Ok(report)
    }
    fn execute(
        mut self,
        cancel: &Cancellation,
        max_new_scenes: usize,
        factory: LaneFactory,
    ) -> Result<ComparisonReportV4> {
        self.begin_invocations()?;
        turn_execution::record_setup(
            &mut self.ledgers,
            turn_execution::Setup {
                version: 4,
                dir: &self.dir,
                key: &self.key,
                native: false,
                physical_ms: 0,
                status: "scripted",
                load: None,
            },
        )?;
        self.execute_body(cancel, max_new_scenes, &factory)?;
        drop(factory);
        self.finish()
    }
    fn execute_body(
        &mut self,
        cancel: &Cancellation,
        max_new_scenes: usize,
        factory: &LaneFactory,
    ) -> Result<()> {
        let corpus = suite()?;
        let first = sealed_scenes4(&self.dir, &self.key)?;
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
                    let dir = self.dir.join(ARM_NAMES[arm]);
                    let path = database(&dir, index, self.manifest.kind);
                    let prefix = match &self.reference {
                        Some(r) => r.prefix(index)?,
                        None => &[],
                    };
                    ensure_database(&path, corpus.seed(), prefix)?;
                    if self.manifest.kind == ComparisonKind::PairedSnapshots {
                        validate_pair_source(&path, corpus.seed(), prefix, &corpus.steps()[index])?;
                    }
                    let turn = execute_turn4(
                        Job4 {
                            dir: &dir,
                            path: &path,
                            index,
                            arm: ARM_NAMES[arm],
                            construction: CONSTRUCTIONS[arm],
                            binding: &self.key,
                            step: &corpus.steps()[index],
                            factory,
                            cancel,
                        },
                        &mut self.ledgers[arm],
                    )?;
                    if !checkpoint_path(&dir, index).exists() {
                        saved(&checkpoint_path(&dir, index), &turn, 256 * 1024)?;
                    }
                    self.turns[arm].push(turn);
                    self.ledgers[1 - arm].exclude_measured_interval(
                        began.elapsed().as_millis().min(u64::MAX as u128) as u64,
                    )?;
                }
            }
            saved(
                &self.dir.join(format!("scene-{scene:02}.json")),
                &scene_data4(&self.dir, &self.key, scene)?,
                4096,
            )?;
        }
        Ok(())
    }
}
fn publish4(dir: &Path, report: &ComparisonReportV4) -> Result<()> {
    let data = serde_json::to_vec_pretty(report).map_err(|_| "Encoding")?;
    let label = if report.lane == "native_scene_literal_relevant_comparison" {
        "Native configured lane; inspect actual load and availability evidence. No human quality acceptance."
    } else {
        "Scripted synthetic evaluation. No human quality acceptance."
    };
    let html = format!("<!doctype html><meta charset=utf-8><meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'none'\"><title>Scene Literal and Relevant comparison</title><h1>Scene Literal and Relevant comparison</h1><p>{label}</p><pre>{}</pre>", escape(std::str::from_utf8(&data).map_err(|_| "Encoding")?));
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
/// Actual scripted run; native factories cannot enter via this API.
pub fn run_comparison(
    dir: &Path,
    resume: bool,
    kind: ComparisonKind,
    cancel: &Cancellation,
    max_new_scenes: usize,
    factory: LaneFactory,
    reference: Option<&ValidatedReference>,
) -> Result<ComparisonReportV4> {
    let started = Instant::now();
    if factory.native() {
        return Err("NativeSceneComparisonRequiresReservation".into());
    }
    if cancel.is_cancelled() {
        return Err("Interrupted".into());
    }
    if !(1..=4).contains(&max_new_scenes) {
        return Err("SceneBudget".into());
    }
    let expected = Manifest::new(
        kind,
        factory.profile()?,
        reference_digest(dir, resume, kind, reference)?,
    )?;
    if resume {
        let actual: Manifest = decode(&dir.join("run.json"), 128 * 1024)?;
        if actual != expected || !actual.source_matches()? {
            return Err("CheckpointMismatch".into());
        }
        let report = inspect_comparison(dir)?;
        if report.completed {
            return Ok(report);
        }
    }
    Session4::open(dir, resume, expected, reference, started)?.execute(
        cancel,
        max_new_scenes,
        factory,
    )
}
/// Strict cold read: validates actual canonical/capture/raw/ledger evidence and
/// never opens a provider, creates an invocation or repairs a checkpoint.
pub fn inspect_comparison(dir: &Path) -> Result<ComparisonReportV4> {
    ordinary(dir)?;
    let manifest: Manifest = decode(&dir.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    let key = manifest.key()?;
    let turns = load_turns4(dir, &manifest, &key)?;
    let completed_scenes = sealed_scenes4(dir, &key)?;
    let reference = if manifest.kind == ComparisonKind::PairedSnapshots {
        let r = open_reference(&dir.join("reference"))?;
        if Some(r.digest()?) != manifest.reference_sha256 {
            return Err("ReferenceBinding".into());
        }
        Some(r)
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
                if let Some(r) = &reference {
                    if turn.row.input_semantic_sha256 != r.turns[index].row.input_semantic_sha256 {
                        return Err("ReferenceInputMismatch".into());
                    }
                }
                if turn.row.construction_evidence_status == Status::Unavailable {
                    unavailable.push(format!(
                        "{}:{}:scene_capture_unavailable",
                        ARM_NAMES[arm], turn.row.turn
                    ));
                }
                if turn.row.privacy_evidence_status == v4::PrivacyEvidenceStatusV4::Unavailable {
                    unavailable.push(format!(
                        "{}:{}:finite_privacy_unavailable",
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
            // Literal intentionally has no mandatory-memory fingerprint. Its
            // absence is not a failed equality test or a fabricated zero.
        }
    }
    let ledgers = [
        Ledger::load(&dir.join("left"), &key)?,
        Ledger::load(&dir.join("right"), &key)?,
    ];
    // Control filenames outside the finite namespace must not silently vanish
    // from inspection. Bound enumeration before decoding any setup data.
    for (count, entry) in fs::read_dir(dir).map_err(|_| "Io")?.enumerate() {
        if count >= 256 {
            return Err("EvidenceBudget".into());
        }
        let entry = entry.map_err(|_| "Io")?;
        let name = entry.file_name();
        let Some(name) = name.to_str() else {
            return Err("SetupIntegrity".into());
        };
        if name.to_ascii_lowercase().starts_with("setup") {
            let suffix = name.strip_prefix("setup-").ok_or("SetupIntegrity")?;
            let index = suffix
                .strip_suffix(".json")
                .and_then(|s| s.parse::<usize>().ok())
                .ok_or("SetupIntegrity")?;
            if index >= 32 || name != format!("setup-{index:02}.json") {
                return Err("SetupIntegrity".into());
            }
            ordinary(&entry.path())?;
        }
    }
    let mut prior_right: Option<usize> = None;
    let mut native_preparation_ms: Option<u64> = None;
    let mut native_loads = Vec::new();
    for index in 0..32 {
        let path = dir.join(format!("setup-{index:02}.json"));
        ordinary(&path)?;
        if !path.exists() {
            continue;
        }
        let setup = if manifest.binding.native {
            selected::setup::decode_native(&read(&path, 64 * 1024)?, &key, index, 4)?
        } else {
            let value: Setup4 = decode(&path, 64 * 1024)?;
            SetupRecord {
                version: value.version,
                binding: value.binding,
                left_invocation: value.left_invocation,
                right_invocation: value.right_invocation,
                native: value.native,
                physical_ms: value.physical_ms,
                status: value.status,
                load: value.load,
            }
        };
        if setup.version != 4
            || setup.binding != key
            || setup.left_invocation != index
            || setup.right_invocation >= 32
            || setup.native != manifest.binding.native
            || prior_right.is_some_and(|prior| setup.right_invocation <= prior)
        {
            return Err("SetupIntegrity".into());
        }
        if setup.native {
            if !matches!(setup.status.as_str(), "loaded" | "failed")
                || (setup.status == "loaded"
                    && (setup.load.is_none() || setup.physical_ms > PREPARATION_MS))
            {
                return Err("SetupIntegrity".into());
            }
            native_preparation_ms = Some(
                native_preparation_ms
                    .unwrap_or(0)
                    .checked_add(setup.physical_ms)
                    .ok_or("SetupIntegrity")?,
            );
            if let Some(load) = &setup.load {
                native_loads.push(load.clone());
            }
            if setup.status == "failed" {
                unavailable.push(format!("native_setup_failed_invocation:{index}"));
            }
        } else if setup.physical_ms != 0 || setup.status != "scripted" || setup.load.is_some() {
            return Err("SetupIntegrity".into());
        }
        // Each actual invocation advances the right ledger. Gaps can retain
        // unknown work; reuse or reordered pair references cannot be actual.
        prior_right = Some(setup.right_invocation);
        for (arm, invocation) in [setup.left_invocation, setup.right_invocation]
            .into_iter()
            .enumerate()
        {
            if invocation >= ledgers[arm].invocations {
                return Err("SetupIntegrity".into());
            }
            let reservation: Reservation = decode(
                &dir.join(ARM_NAMES[arm])
                    .join(format!("invocation-{invocation:02}.json")),
                4096,
            )?;
            if reservation.version != 1
                || reservation.binding != key
                || reservation.index != invocation
                || reservation.story != "preparation"
                || reservation.turn != "preparation"
                || reservation.ms != PREPARATION_MS
                || reservation.roles != 0
            {
                return Err("SetupIntegrity".into());
            }
            if setup.native {
                let shares = shared_setup_shares(setup.physical_ms);
                selected::setup::invocation(
                    &dir.join(ARM_NAMES[arm]),
                    &key,
                    invocation,
                    if arm == 0 { shares.0 } else { shares.1 },
                )?;
            }
            // Missing settlements retain the full unknown reservation; the
            // shared validator checks each known settlement's setup share.
        }
    }
    append_ledger_notes(dir, &ledgers, &mut unavailable);
    let lane = if manifest.binding.native {
        "native_scene_literal_relevant_comparison"
    } else {
        "scripted_scene_literal_relevant_comparison"
    };
    let source_bound_committed_rows = rows
        .iter()
        .filter(|row| {
            row.phase == "committed"
                && row.construction_evidence_status == Status::ValidatedCommittedSceneNarratorV1
        })
        .count();
    Ok(ComparisonReportV4 { version:4, arms:v4::arm_descriptors(), kind:manifest.kind, lane:lane.into(),
        source_matches:manifest.source_matches()?,completed:completed_scenes==4,completed_scenes,turns:rows,
        human_reviewed:0,human_rubric:"not_reviewed".into(),quality_accepted:false,physical_setups:native_loads.len(),physical_setup_ms:native_preparation_ms,native_load:if native_loads.is_empty() {None} else {Some(json!(native_loads))},
        left_charged_ms:ledgers[0].charged_ms,right_charged_ms:ledgers[1].charged_ms,left_reserved_roles:ledgers[0].charged_roles,right_reserved_roles:ledgers[1].charged_roles,
        first_semantic_divergence:semantic,first_mechanical_divergence:mechanical,same_input_pairs,source_bound_committed_rows,unavailable,
        profile:manifest.profile,suite_sha256:manifest.binding.suite_sha256,source_sha256:manifest.source_sha256,reference_sha256:manifest.reference_sha256,
        limitations:vec![if manifest.binding.native {"Native configured 24-attempt/21-accepted/3-guard suite; load/turn evidence may be failed or unavailable. No human quality acceptance.".into()} else {"Scripted 24-attempt/21-accepted/3-guard synthetic suite; no model or prose-quality measurement.".into()},
            "Literal player history has no invented opening or memory projection; the information channels differ.".into(),
            "Fresh committed Domain1 narrator inputs are regenerated against actual Store prefix/receipt; this is not provider/output-origin or Director/compiler execution authentication.".into(),
            "Finite sentinel checks are not universal semantic privacy or prose-quality proof; unavailable evidence is never a privacy pass.".into(),
            "Missing recovered calls/captures remain unknown. Hashes detect consistency, not authenticated evidence origin.".into(),
            "Original eight-sample human assessment remains needs improvement; no new human samples or quality acceptance.".into(),
            "Selected/UI and native CLI integration, human quality review and physical-phone qualification remain separate gates.".into()] })
}
