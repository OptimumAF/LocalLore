//! Scripted protocol3 literal/Relevant comparison over the existing owners.
//! Native entry and selected/UI execution remain explicitly unavailable.
#[cfg(test)]
mod resource_review_tests;
use super::*;
use crate::memory_comparison_v3::{
    self as v3, ArmDescriptorV3, CapturedLiteralContext, ComparisonArmV3, ComparisonReportV3,
    ConstructionEvidenceStatusV3 as Status, CurrentBindingV3, TurnReportV3,
};
use locallore::host::HostPlayConstructionV1;

const CONSTRUCTIONS: [ComparisonArmV3; 2] = [
    ComparisonArmV3::LiteralPlayerV1,
    ComparisonArmV3::RelevantMemoryV1,
];
fn descriptor(arm: ComparisonArmV3) -> ArmDescriptorV3 {
    v3::arm_descriptors()[usize::from(arm == ComparisonArmV3::RelevantMemoryV1)].clone()
}
fn host_construction(arm: ComparisonArmV3) -> HostPlayConstructionV1 {
    match arm {
        ComparisonArmV3::LiteralPlayerV1 => HostPlayConstructionV1::PlayerLiteralV1,
        ComparisonArmV3::RelevantMemoryV1 => {
            HostPlayConstructionV1::Memory(ContextPolicy::StateRelevantMemoryV1)
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    version: u16,
    source_sha256: String,
    binding: CurrentBindingV3,
    profile: PlayProfile,
    kind: ComparisonKind,
    #[serde(deserialize_with = "v3::required_nullable")]
    reference_sha256: Option<String>,
    order: String,
}
impl Manifest {
    fn new(
        kind: ComparisonKind,
        profile: PlayProfile,
        reference_sha256: Option<String>,
    ) -> Result<Self> {
        let binding = v3::current_binding(false)?;
        Ok(Self {
            version: 3,
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
        let current = v3::current_binding(false)?;
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
        let current = Self::new(
            self.kind,
            self.profile.clone(),
            self.reference_sha256.clone(),
        )?;
        if self.version != 3
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
struct StoredTurn3 {
    version: u16,
    binding: String,
    index: usize,
    arm: String,
    request: Request,
    before_head: u64,
    after_head: u64,
    row: TurnReportV3,
    #[serde(deserialize_with = "v3::required_nullable")]
    capture_file: Option<String>,
    #[serde(deserialize_with = "v3::required_nullable")]
    recording_file: Option<String>,
}
struct Observation3<'a> {
    step: &'a protocol::Step,
    arm: &'a str,
    construction: ComparisonArmV3,
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
enum Checked {
    Literal(CapturedLiteralContext),
    Relevant(CapturedContext),
}
impl Checked {
    fn director(&self) -> &[String] {
        match self {
            Self::Literal(c) => &c.director_prompts,
            Self::Relevant(c) => &c.director_prompts,
        }
    }
    fn narrator(&self) -> &[String] {
        match self {
            Self::Literal(c) => &c.narrator_prompts,
            Self::Relevant(c) => &c.narrator_prompts,
        }
    }
    fn package(&self) -> Option<&Value> {
        match self {
            Self::Literal(_) => None,
            Self::Relevant(c) => Some(&c.package),
        }
    }
    fn estimates(&self) -> Option<Vec<Value>> {
        match self {
            Self::Literal(c) => Some(c.director_estimates.clone()),
            Self::Relevant(c) => c.director_estimates.clone(),
        }
    }
}
fn make_row3(o: Observation3<'_>) -> Result<TurnReportV3> {
    let Observation3 {
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
    let assessed = turn_execution::assess_outcome(
        before,
        after,
        step,
        phase,
        error.as_deref(),
        receipt,
        roles,
    )?;
    let guard = assessed.guard;
    let expected_ok = assessed.expected_ok;
    let record = receipt.and_then(Receipt::play);
    let construction_matches = if let Some(p) = record {
        p.policy == NARRATION_POLICY
            && p.profile == *profile
            && match construction {
                ComparisonArmV3::LiteralPlayerV1 => {
                    p.prompt_version == locallore::play::LITERAL_PLAY_PROMPT_VERSION_V1
                        && p.context.is_none()
                        && p.context_policy.is_none()
                }
                ComparisonArmV3::RelevantMemoryV1 => {
                    p.prompt_version == PROMPT_VERSION
                        && p.context_policy == Some(ContextPolicy::StateRelevantMemoryV1)
                        && p.context
                            .as_ref()
                            .is_some_and(|c| c.compiler_version == 2 && c.version == 2)
                }
            }
    } else {
        guard && roles == 0
    };
    let checked = match (recording, capture) {
        (Some(recording), Some(capture)) => capture["data"]["details"]["identity"]["attempt"]
            .as_u64()
            .and_then(|n| u32::try_from(n).ok())
            .and_then(|attempt| match construction {
                ComparisonArmV3::LiteralPlayerV1 => CapturedLiteralContext::from_host_capture(
                    before,
                    &request,
                    attempt,
                    capture,
                    &recording.captures,
                    profile,
                    1,
                )
                .ok()
                .map(Checked::Literal),
                ComparisonArmV3::RelevantMemoryV1 => CapturedContext::from_host_capture(
                    before,
                    &request,
                    attempt,
                    capture,
                    &recording.captures,
                    profile,
                    Some(1),
                )
                .ok()
                .map(Checked::Relevant),
            }),
        _ => None,
    };
    // A tuple-valid diagnostic candidate must also be the actual Store receipt.
    // This comparison grants nothing; accepted history still comes from Store.
    if checked.is_some() {
        if let Some(receipt) = receipt {
            let candidates: Vec<_> = capture
                .and_then(|c| c["data"]["details"]["artifacts"].as_array())
                .into_iter()
                .flatten()
                .filter(|a| a["kind"] == "accepted_candidate_not_durable_commit")
                .collect();
            if candidates.len() != 1
                || candidates[0]["value"]
                    != serde_json::to_value(receipt).map_err(|_| "Encoding")?
            {
                return Err("CaptureCandidateBinding".into());
            }
        }
    }
    let applicable = roles > 0;
    let evidence_available = applicable && checked.is_some() && !recovered;
    let evidence_satisfied = if applicable {
        checked.is_some()
    } else {
        guard || phase == "not_run_dependency"
    };
    let status = if recovered {
        Status::Unavailable
    } else if guard && roles == 0 {
        Status::NotApplicableGuard
    } else if phase == "not_run_dependency" {
        Status::NotApplicableDependency
    } else {
        match &checked {
            Some(Checked::Literal(_)) => Status::ValidatedLiteral,
            Some(Checked::Relevant(_)) => Status::ValidatedRelevant,
            None => Status::Unavailable,
        }
    };
    let privacy = checked.as_ref().is_none_or(|c| {
        !c.director()
            .iter()
            .chain(c.narrator())
            .any(|p| EXCLUSIONS.iter().any(|x| p.contains(x)))
            && !c.narrator().iter().any(|p| p.contains("SECRET-TIDE-731"))
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
    let package = checked.as_ref().and_then(Checked::package);
    let mandatory = package.map(|p| -> Result<String> {
        let rows = p["records"].as_array().ok_or("CaptureMalformed")?;
        let selected: Vec<_> = rows.iter().filter(|r| r["mandatory"] == true).map(|r|
            json!({"kind":r["kind"],"source_revision":r["source_revision"],"sources":r["sources"],"payload":r["payload"]})).collect();
        Ok(digest(&encode(&selected)?))
    }).transpose()?;
    let optional = package.map(|p| {
        p["records"].as_array().is_some_and(|r| {
            r.iter().any(|r| {
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
    if !construction_matches && !guard {
        failures.push("no_matching_construction_receipt".into());
    }
    if !evidence_satisfied {
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
    let literal = match &checked {
        Some(Checked::Literal(c)) if !recovered => Some(c),
        _ => None,
    };
    Ok(TurnReportV3 {
        turn: step.id().into(),
        scene: step.scene(),
        arm: arm.into(),
        construction: descriptor(construction),
        phase: phase.into(),
        error,
        expected: serde_json::to_string(step.expected()).map_err(|_| "Encoding")?,
        passed: expected_ok
            && construction_matches
            && evidence_satisfied
            && privacy
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
        construction_evidence_status: status,
        literal_source_units: literal.map(|c| c.source_units),
        literal_selected_start: literal.map(|c| c.selected_start),
        literal_selected_units: literal.map(|c| c.selected_units),
        context_evidence_available: evidence_available,
        context_requirement: if guard {
            "not_applicable_guard_configured_only"
        } else if phase == "not_run_dependency" {
            "not_applicable_dependency"
        } else {
            "required_actual_capture"
        }
        .into(),
        privacy_passed: privacy && evidence_available,
        fallback: record.map(|r| r.fallback),
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
        director_private_target_present: checked
            .as_ref()
            .map(|c| c.director().iter().any(|p| p.contains("SECRET-TIDE-731"))),
        selected_context_bytes: package.map(|p| encode(p).map(|b| b.len())).transpose()?,
        estimated_context_tokens: package.and_then(|p| p["estimated_tokens"].as_u64()),
        forwarded_director_estimates: checked.as_ref().and_then(Checked::estimates),
    })
}
struct Job3<'a> {
    dir: &'a Path,
    path: &'a Path,
    index: usize,
    arm: &'a str,
    construction: ComparisonArmV3,
    binding: &'a str,
    step: &'a protocol::Step,
    factory: &'a LaneFactory,
    cancel: &'a Cancellation,
}
fn execute_turn3(job: Job3<'_>, ledger: &mut Ledger) -> Result<StoredTurn3> {
    let Job3 {
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
    let recovered = turn_execution::recover_actual(path, &full, step)?;
    if recovered.is_some() || turn_execution::dependency_missing(&full, step, &profile)? {
        let is_recovered = recovered.is_some();
        let before = recovered.as_ref().map_or(&full, |r| &r.before);
        let after = recovered.as_ref().map_or(&full, |r| &r.after);
        let row = make_row3(Observation3 {
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
            profile: &profile,
            recovered: is_recovered,
        })?;
        return Ok(StoredTurn3 {
            version: 3,
            binding: binding.into(),
            index,
            arm: arm.into(),
            request: step.request(before),
            before_head: before.revision(),
            after_head: after.revision(),
            row,
            capture_file: None,
            recording_file: None,
        });
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
    let row = make_row3(Observation3 {
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
    let result = StoredTurn3 {
        version: 3,
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
fn load_turn3(
    dir: &Path,
    path: &Path,
    index: usize,
    arm: usize,
    key: &str,
    manifest: &Manifest,
) -> Result<StoredTurn3> {
    let stored: StoredTurn3 = decode(&checkpoint_path(dir, index), 256 * 1024)?;
    if stored.version != 3
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
    let actual = make_row3(Observation3 {
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
fn load_turns3(dir: &Path, manifest: &Manifest, key: &str) -> Result<[Vec<StoredTurn3>; 2]> {
    let corpus = suite()?;
    let mut result: [Vec<StoredTurn3>; 2] = [Vec::new(), Vec::new()];
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
            let t = load_turn3(
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
fn scene_data3(dir: &Path, key: &str, scene: usize) -> Result<SceneManifest> {
    let mut value = scene_data(dir, key, scene)?;
    value.version = 3;
    Ok(value)
}
fn sealed_scenes3(dir: &Path, key: &str) -> Result<usize> {
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
        if stored != scene_data3(dir, key, scene)? {
            return Err("SceneIntegrity".into());
        }
        count += 1;
    }
    Ok(count)
}
struct Session3 {
    dir: PathBuf,
    manifest: Manifest,
    key: String,
    _lock: File,
    ledgers: [Ledger; 2],
    turns: [Vec<StoredTurn3>; 2],
    reference: Option<ValidatedReference>,
}
impl Session3 {
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
        let turns = load_turns3(dir, &expected, &key)?;
        sealed_scenes3(dir, &key)?;
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
        let ledgers = turn_execution::begin_pair(dir, &key, started)?;
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
    fn finish(mut self) -> Result<ComparisonReportV3> {
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
        publish3(&self.dir, &report)?;
        Ok(report)
    }
    fn execute(
        mut self,
        cancel: &Cancellation,
        max_new_scenes: usize,
        factory: LaneFactory,
    ) -> Result<ComparisonReportV3> {
        turn_execution::record_setup(
            &mut self.ledgers,
            turn_execution::Setup {
                version: 3,
                dir: &self.dir,
                key: &self.key,
                native: false,
                physical_ms: 0,
                status: "scripted",
                load: None,
            },
        )?;
        let corpus = suite()?;
        let first = sealed_scenes3(&self.dir, &self.key)?;
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
                    let turn = execute_turn3(
                        Job3 {
                            dir: &dir,
                            path: &path,
                            index,
                            arm: ARM_NAMES[arm],
                            construction: CONSTRUCTIONS[arm],
                            binding: &self.key,
                            step: &corpus.steps()[index],
                            factory: &factory,
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
                &scene_data3(&self.dir, &self.key, scene)?,
                4096,
            )?;
        }
        self.finish()
    }
}
fn publish3(dir: &Path, report: &ComparisonReportV3) -> Result<()> {
    let data = serde_json::to_vec_pretty(report).map_err(|_| "Encoding")?;
    let html = format!("<!doctype html><meta charset=utf-8><meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'none'\"><title>Literal and Relevant comparison</title><h1>Literal and Relevant comparison</h1><p>Scripted synthetic evaluation. Native comparison unavailable. No human quality acceptance.</p><pre>{}</pre>", escape(std::str::from_utf8(&data).map_err(|_| "Encoding")?));
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
) -> Result<ComparisonReportV3> {
    let started = Instant::now();
    if factory.native() {
        return Err("NativeComparisonV3Unavailable".into());
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
    Session3::open(dir, resume, expected, reference, started)?.execute(
        cancel,
        max_new_scenes,
        factory,
    )
}
/// Strict cold read: validates actual canonical/capture/raw/ledger evidence and
/// never opens a provider, creates an invocation or repairs a checkpoint.
pub fn inspect_comparison(dir: &Path) -> Result<ComparisonReportV3> {
    ordinary(dir)?;
    let manifest: Manifest = decode(&dir.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    let key = manifest.key()?;
    let turns = load_turns3(dir, &manifest, &key)?;
    let completed_scenes = sealed_scenes3(dir, &key)?;
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
        if let Some(suffix) = name.strip_prefix("setup-") {
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
    for index in 0..32 {
        let path = dir.join(format!("setup-{index:02}.json"));
        ordinary(&path)?;
        if !path.exists() {
            continue;
        }
        let setup: SetupRecord = decode(&path, 64 * 1024)?;
        if setup.version != 3
            || setup.binding != key
            || setup.left_invocation != index
            || setup.right_invocation >= 32
            || setup.native
            || setup.physical_ms != 0
            || setup.status != "scripted"
            || setup.load.is_some()
        {
            return Err("SetupIntegrity".into());
        }
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
            // Ledger::load above checks any settlement's binding/index/role cap.
            // Its absence retains the full unknown reservation, never a refund.
        }
    }
    append_ledger_notes(dir, &ledgers, &mut unavailable);
    Ok(ComparisonReportV3 { version:3, arms:v3::arm_descriptors(), kind:manifest.kind, lane:"scripted_literal_relevant_comparison".into(),
        source_matches:manifest.source_matches()?,completed:completed_scenes==4,completed_scenes,turns:rows,
        human_reviewed:0,human_rubric:"not_reviewed".into(),quality_accepted:false,physical_setups:0,physical_setup_ms:None,native_load:None,
        left_charged_ms:ledgers[0].charged_ms,right_charged_ms:ledgers[1].charged_ms,left_reserved_roles:ledgers[0].charged_roles,right_reserved_roles:ledgers[1].charged_roles,
        first_semantic_divergence:semantic,first_mechanical_divergence:mechanical,same_input_pairs,unavailable,
        profile:manifest.profile,suite_sha256:manifest.binding.suite_sha256,source_sha256:manifest.source_sha256,reference_sha256:manifest.reference_sha256,
        limitations:vec!["Scripted 24-attempt/21-accepted/3-guard synthetic suite; no model or prose-quality measurement.".into(),
            "Literal player history has no invented opening or memory projection; the information channels differ.".into(),
            "Narrator remains Core-grounded; finite sentinel checks are not universal semantic privacy proof.".into(),
            "Missing recovered calls/captures remain unknown. Hashes detect consistency, not authenticated evidence origin.".into(),
            "Native protocol3, selected/UI integration, human quality review and physical-phone qualification are unavailable.".into()] })
}
/// Fixed scripted grammar; no native provider, arbitrary corpus or expected
/// outcome input. The existing reference owner remains the only reference writer.
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
    let mut scenes = 4;
    let mut reference = None;
    let mut seen = BTreeSet::new();
    let mut index = 2;
    while index < args.len() {
        if index + 1 >= args.len() || !seen.insert(args[index].as_str()) {
            return Err("Usage".into());
        }
        let value = &args[index + 1];
        match args[index].as_str() {
            "--kind" => {
                kind = Some(match value.as_str() {
                    "paired" => ComparisonKind::PairedSnapshots,
                    "rollout" => ComparisonKind::ContinuousRollout,
                    _ => return Err("Usage".into()),
                })
            }
            "--lane" => lane = Some(value.as_str()),
            "--max-scenes" => {
                scenes = value.parse::<usize>().map_err(|_| "Usage")?;
                if !(1..=4).contains(&scenes) {
                    return Err("SceneBudget".into());
                }
            }
            "--reference" => reference = Some(Path::new(value)),
            _ => return Err("Usage".into()),
        }
        index += 2;
    }
    match lane {
        Some("scripted") => {}
        Some("native") => return Err("NativeComparisonV3Unavailable".into()),
        _ => return Err("Usage".into()),
    }
    let kind = kind.ok_or("Usage")?;
    let reference = reference.map(open_reference).transpose()?;
    serde_json::to_value(run_comparison(
        dir,
        args[0] == "resume",
        kind,
        &Cancellation::default(),
        scenes,
        LaneFactory::ScriptedBaseline,
        reference.as_ref(),
    )?)
    .map_err(|_| "Encoding".into())
}

#[cfg(test)]
mod lifecycle_tests {
    use super::*;
    #[test]
    fn manifest_kind_and_reference_combination_is_closed_before_any_execution() {
        let profile = LaneFactory::ScriptedBaseline.profile().unwrap();
        assert!(Manifest::new(
            ComparisonKind::ContinuousRollout,
            profile.clone(),
            Some("a".repeat(64))
        )
        .unwrap()
        .validate()
        .is_err());
        assert!(
            Manifest::new(ComparisonKind::PairedSnapshots, profile.clone(), None)
                .unwrap()
                .validate()
                .is_err()
        );
        assert!(Manifest::new(
            ComparisonKind::PairedSnapshots,
            profile.clone(),
            Some("invalid".into())
        )
        .unwrap()
        .validate()
        .is_err());
        Manifest::new(ComparisonKind::ContinuousRollout, profile.clone(), None)
            .unwrap()
            .validate()
            .unwrap();
        Manifest::new(
            ComparisonKind::PairedSnapshots,
            profile,
            Some("a".repeat(64)),
        )
        .unwrap()
        .validate()
        .unwrap();
    }
    #[test]
    fn pending_actual_director_cancels_without_canonical_commit_and_cold_read_keeps_the_failed_turn(
    ) {
        PENDING_POLLED.store(false, Ordering::Release);
        let path = std::env::temp_dir().join(format!(
            "locallore-literal-pending-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let cancel = Cancellation::default();
        let stop = cancel.clone();
        let watcher = std::thread::spawn(move || {
            let began = Instant::now();
            while !PENDING_POLLED.load(Ordering::Acquire) {
                if began.elapsed() > Duration::from_secs(15) {
                    stop.cancel();
                    panic!("actual fixed pending provider never polled");
                }
                std::thread::sleep(Duration::from_millis(1));
            }
            stop.cancel();
        });
        let outcome = run_comparison(
            &path,
            false,
            ComparisonKind::ContinuousRollout,
            &cancel,
            1,
            LaneFactory::TestFault(TestFault::Pending),
            None,
        );
        watcher.join().unwrap();
        let report = outcome.unwrap();
        assert!(!report.completed);
        assert_eq!(report.completed_scenes, 0);
        assert_eq!(report.turns.len(), 1);
        let row = &report.turns[0];
        assert_eq!(row.phase, "cancelled");
        assert!(row.roles_known);
        assert_eq!(row.roles, 1);
        assert!(!row.passed);
        assert_eq!(row.construction_evidence_status, Status::ValidatedLiteral); // Actual input was forwarded; no accepted receipt is implied.
        assert!(row.actual_receipt_sha256.is_none());
        assert!(row.narration.is_none());
        let before = read(&path.join("left/synthetic.sqlite"), 8 * 1024 * 1024).unwrap();
        let actual = engine(
            &path.join("left/synthetic.sqlite"),
            &suite().unwrap().seed().scope,
        )
        .unwrap();
        assert_eq!(actual.revision(), 0);
        assert!(actual.receipts().is_empty());
        assert_eq!(inspect_comparison(&path).unwrap(), report);
        assert_eq!(
            read(&path.join("left/synthetic.sqlite"), 8 * 1024 * 1024).unwrap(),
            before
        );
    }
}
