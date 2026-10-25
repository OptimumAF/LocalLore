//! Isolated scripted selected turns over the existing comparison execution path.
//! Native execution and renderer-constructed capabilities are not supported.
use super::*;

const LANE: &str = "scripted_selected_case";
const MANIFEST_CAP: usize = 128 * 1024;

pub enum SelectedLane {
    ScriptedBaseline,
}
pub struct SelectedIntent {
    pub client_id: String,
    pub lane: SelectedLane,
}

/// A native-owned source read lock and actual Core histories, never JSON authority.
pub struct PreparedSelectedPlan {
    _source: desktop_api::OpenedComparison,
    source_dir: PathBuf,
    manifest: SelectedManifest,
    before: [Engine; 2],
}

#[derive(Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Selection {
    turn: String,
    clicked_arm: String,
    index: usize,
}
#[derive(Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceInput {
    arm: String,
    scope: Scope,
    before_head: u64,
    request: Request,
    prefix_sha256: String,
    input_semantic_sha256: String,
}
#[derive(Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SelectedManifest {
    version: u16,
    run_type: String,
    client_id: String,
    binding: String,
    source_binding: String,
    source_kind: ComparisonKind,
    source_profile: PlayProfile,
    selection: Selection,
    lane: String,
    profile: PlayProfile,
    suite_sha256: String,
    source_sha256: String,
    #[serde(deserialize_with = "required_reference")]
    source_reference_sha256: Option<String>,
    source_inputs: [SourceInput; 2],
}

// Nullable is still a required manifest key. Plain Option deserialization
// would otherwise silently accept a missing rollout reference field.
fn required_reference<'de, D: serde::Deserializer<'de>>(
    deserializer: D,
) -> std::result::Result<Option<String>, D::Error> {
    Option::<String>::deserialize(deserializer)
}

fn client_valid(client: &str) -> bool {
    !client.is_empty() && client.len() <= 128
        && client.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
}
fn cancelled(cancel: &Cancellation) -> Result<()> {
    if cancel.is_cancelled() { Err("Interrupted".into()) } else { Ok(()) }
}
impl SelectedManifest {
    fn digest(&self) -> Result<String> {
        let mut value = serde_json::to_value(self).map_err(|_| "Encoding")?;
        value.as_object_mut().ok_or("SelectedBinding")?.remove("binding");
        Ok(digest(&encode(&value)?))
    }
    fn run_manifest(&self) -> Result<RunManifest> {
        RunManifest::new(self.source_kind, self.profile.clone(), false,
            self.source_reference_sha256.clone())
    }
    fn validate(&self) -> Result<()> {
        let corpus = suite()?;
        let step = corpus.steps().get(self.selection.index).ok_or("UnknownRow")?;
        let seed_engine = Engine::new(corpus.seed().clone()).map_err(|_| "Seed")?;
        let template = step.request(&seed_engine);
        let expected = self.run_manifest()?;
        expected.validate()?;
        self.source_profile.validate().map_err(|_| "Profile")?;
        // Validate source profile shape without pretending its target lane is
        // scripted. Its exact producer/profile identity is checked on execution.
        RunManifest::new(self.source_kind, self.source_profile.clone(), false,
            self.source_reference_sha256.clone())?.validate()?;
        if self.version != 1 || self.run_type != "selected_case" || self.lane != LANE
            || !client_valid(&self.client_id) || !hex(&self.binding)
            || self.binding != self.digest()? || !hex(&self.source_binding)
            || !hex(&self.source_sha256) || self.suite_sha256 != expected.binding.suite_sha256
            || self.profile != LaneFactory::ScriptedBaseline.profile()?
            || self.selection.turn != step.id()
            || !ARM_NAMES.contains(&self.selection.clicked_arm.as_str())
        {
            return Err("SelectedBinding".into());
        }
        match (self.source_kind, &self.source_reference_sha256) {
            (ComparisonKind::PairedSnapshots, Some(hash)) if hex(hash) => {}
            (ComparisonKind::ContinuousRollout, None) => {}
            _ => return Err("ReferenceBinding".into()),
        }
        for (arm, input) in self.source_inputs.iter().enumerate() {
            if input.arm != ARM_NAMES[arm] || input.scope != corpus.seed().scope
                || input.request.scope != input.scope || input.request.version != template.version
                || input.request.turn != self.selection.turn
                || input.request.expected_revision != input.before_head
                || input.request.intent != template.intent
                || !hex(&input.prefix_sha256) || !hex(&input.input_semantic_sha256)
            {
                return Err("SelectedInput".into());
            }
        }
        Ok(())
    }
}

fn source_inputs(
    dir: &Path, snapshot: &desktop_api::Snapshot, selection: &Selection,
) -> Result<[Engine; 2]> {
    let corpus = suite()?;
    let reference = if snapshot.manifest.kind == ComparisonKind::PairedSnapshots {
        let reference = open_reference(&dir.join("reference"))?;
        if !reference.manifest.source_matches()?
            || Some(reference.digest()?) != snapshot.manifest.reference_sha256
        {
            return Err("ReferenceSourceMismatch".into());
        }
        Some(reference)
    } else { None };
    let mut before = Vec::with_capacity(2);
    for arm in 0..2 {
        let stored = snapshot.turns[arm].get(selection.index).ok_or("UnknownRow")?;
        let full = engine(&database(&dir.join(ARM_NAMES[arm]), selection.index,
            snapshot.manifest.kind), &corpus.seed().scope)?;
        if full.domain_version() != 1 || full.seed() != corpus.seed() {
            return Err("SelectedInput".into());
        }
        let cut = full.at_revision(stored.before_head).map_err(|_| "Replay")?;
        let after = full.at_revision(stored.after_head).map_err(|_| "Replay")?;
        let request = corpus.steps()[selection.index].request(&cut);
        if request != stored.request || stored.row.turn != selection.turn
            || v2::semantic_input(&cut, &request)? != stored.row.input_semantic_sha256
            || v2::semantic_output(&after)? != stored.row.output_semantic_sha256
            || v2::mechanical_output(&after)? != stored.row.mechanical_sha256
        {
            return Err("SelectedInput".into());
        }
        if let Some(reference) = &reference {
            if cut.receipts() != reference.prefix(selection.index)? {
                return Err("ReferencePrefix".into());
            }
        }
        before.push(cut);
    }
    before.try_into().map_err(|_| "SelectedInput".into())
}

fn manifest_for(
    snapshot: &desktop_api::Snapshot, selection: Selection, client_id: String,
    before: &[Engine; 2],
) -> Result<SelectedManifest> {
    if !snapshot.manifest.source_matches()? { return Err("SourceMismatch".into()); }
    let corpus = suite()?;
    let make_input = |arm: usize| -> Result<SourceInput> {
        let engine = &before[arm];
        let request = corpus.steps()[selection.index].request(engine);
        Ok(SourceInput {
            arm: ARM_NAMES[arm].into(), scope: engine.scope().clone(),
            before_head: engine.revision(),
            prefix_sha256: digest(&encode(engine.receipts())?),
            input_semantic_sha256: v2::semantic_input(engine, &request)?, request,
        })
    };
    let mut manifest = SelectedManifest {
        version: 1, run_type: "selected_case".into(), client_id,
        binding: String::new(),
        source_binding: snapshot.value["binding"].as_str().ok_or("Source")?.into(),
        source_kind: snapshot.manifest.kind, source_profile: snapshot.manifest.profile.clone(),
        selection: selection.clone(), lane: LANE.into(),
        profile: LaneFactory::ScriptedBaseline.profile()?,
        suite_sha256: snapshot.manifest.binding.suite_sha256.clone(),
        source_sha256: snapshot.manifest.source_sha256.clone(),
        source_reference_sha256: snapshot.manifest.reference_sha256.clone(),
        source_inputs: [make_input(0)?, make_input(1)?],
    };
    manifest.binding = manifest.digest()?;
    manifest.validate()?;
    Ok(manifest)
}

pub fn prepare_selected(
    source_dir: &Path, expected_source_binding: &str, row: &desktop_api::RowId,
    intent: SelectedIntent, cancel: &Cancellation,
) -> Result<PreparedSelectedPlan> {
    cancelled(cancel)?;
    if !client_valid(&intent.client_id) || !hex(expected_source_binding) {
        return Err("SelectedIdentity".into());
    }
    let SelectedLane::ScriptedBaseline = intent.lane;
    let corpus = suite()?;
    let index = corpus.steps().iter().position(|s| s.id() == row.turn).ok_or("UnknownRow")?;
    let selection = Selection { turn: row.turn.clone(), index,
        clicked_arm: ARM_NAMES[match row.arm { desktop_api::Arm::Left => 0, desktop_api::Arm::Right => 1 }].into() };
    let source = desktop_api::open_read_only(source_dir)?;
    let directory = fs::canonicalize(source_dir).map_err(|_| "Io")?;
    let snapshot = desktop_api::snapshot(&directory)?;
    if snapshot.value["binding"].as_str() != Some(expected_source_binding) {
        return Err("SnapshotMismatch".into());
    }
    if !snapshot.manifest.source_matches()? { return Err("SourceMismatch".into()); }
    let before = source_inputs(&directory, &snapshot, &selection)?;
    let manifest = manifest_for(&snapshot, selection, intent.client_id, &before)?;
    cancelled(cancel)?;
    Ok(PreparedSelectedPlan { _source: source, source_dir: directory, manifest, before })
}

impl PreparedSelectedPlan {
    fn refresh(&self, cancel: &Cancellation) -> Result<()> {
        cancelled(cancel)?;
        let snapshot = desktop_api::snapshot(&self.source_dir)?;
        let before = source_inputs(&self.source_dir, &snapshot, &self.manifest.selection)?;
        let manifest = manifest_for(&snapshot, self.manifest.selection.clone(),
            self.manifest.client_id.clone(), &before)?;
        if manifest != self.manifest { return Err("SnapshotMismatch".into()); }
        for (actual, expected) in before.iter().zip(&self.before) {
            if actual.accepted_history_basis().map_err(|_| "Source")?
                != expected.accepted_history_basis().map_err(|_| "Source")?
            { return Err("SnapshotMismatch".into()); }
        }
        cancelled(cancel)
    }
}

struct Destination {
    dir: PathBuf,
    manifest: SelectedManifest,
    _pins: Vec<File>,
    _lock: File,
}

fn pin_selected(dir: &Path) -> Result<Vec<File>> {
    let mut pins = crate::local_lane::desktop_api::pin_directory(dir)?;
    let mut count = 0usize;
    for entry in fs::read_dir(dir).map_err(|_| "Io")? {
        count += 1;
        if count > 512 { return Err("ReportBudget".into()); }
        let entry = entry.map_err(|_| "Io")?;
        ordinary(&entry.path())?;
        let name = entry.file_name();
        if entry.file_type().map_err(|_| "Io")?.is_dir() {
            if !ARM_NAMES.iter().any(|arm| name == *arm) {
                return Err("SelectedDirectory".into());
            }
            pins.extend(crate::local_lane::desktop_api::pin_directory(&entry.path())?);
            for (n, child) in fs::read_dir(entry.path()).map_err(|_| "Io")?.enumerate() {
                if n >= 512 { return Err("ReportBudget".into()); }
                let child = child.map_err(|_| "Io")?;
                ordinary(&child.path())?;
                if !child.file_type().map_err(|_| "Io")?.is_file() {
                    return Err("SelectedDirectory".into());
                }
            }
        } else if !["selected.json", "run.lock", "report.json", "report.html"]
            .iter().any(|known| name == *known)
        {
            return Err("SelectedDirectory".into());
        }
    }
    Ok(pins)
}

fn open_destination(dir: &Path) -> Result<Destination> {
    let pins = pin_selected(dir)?;
    ordinary(&dir.join("run.lock"))?;
    let lock = OpenOptions::new().read(true).open(dir.join("run.lock"))
        .map_err(|_| "Io")?;
    lock.try_lock().map_err(|_| "RunBusy")?;
    let manifest: SelectedManifest = decode(&dir.join("selected.json"), MANIFEST_CAP)?;
    manifest.validate()?;
    Ok(Destination { dir: fs::canonicalize(dir).map_err(|_| "Io")?,
        manifest, _pins: pins, _lock: lock })
}

fn disjoint(source: &Path, destination: &Path) -> Result<()> {
    if destination.starts_with(source) || source.starts_with(destination) {
        Err("SourceDestinationOverlap".into())
    } else { Ok(()) }
}

fn new_destination(plan: &PreparedSelectedPlan, dir: &Path) -> Result<Destination> {
    let absolute = std::path::absolute(dir).map_err(|_| "Io")?;
    if absolute.components().any(|part| matches!(part, std::path::Component::ParentDir)) {
        return Err("SelectedDirectory".into());
    }
    let parent = absolute.parent().ok_or("SelectedDirectory")?;
    let parent_pins = crate::local_lane::desktop_api::pin_directory(parent)?;
    let canonical = fs::canonicalize(parent).map_err(|_| "Io")?
        .join(absolute.file_name().ok_or("SelectedDirectory")?);
    disjoint(&plan.source_dir, &canonical)?;
    ordinary(&canonical)?;
    if canonical.exists() { return Err("OutputExists".into()); }
    fs::create_dir(&canonical).map_err(|_| "OutputExists")?;
    let lock = take_lock(&canonical)?;
    saved(&canonical.join("selected.json"), &plan.manifest, MANIFEST_CAP)?;
    for arm in ARM_NAMES {
        fs::create_dir(canonical.join(arm)).map_err(|_| "Io")?;
    }
    let mut pins = parent_pins;
    pins.extend(pin_selected(&canonical)?);
    Ok(Destination { dir: canonical, manifest: plan.manifest.clone(),
        _pins: pins, _lock: lock })
}

/// Reconstruct a before engine from actual canonical records, never a JSON
/// engine. A source-owned prefix additionally proves interrupted bootstraps.
fn validate_destination(
    dir: &Path, manifest: &SelectedManifest, source: Option<&[Engine; 2]>,
) -> Result<[Option<StoredTurn>; 2]> {
    let corpus = suite()?;
    let index = manifest.selection.index;
    let step = &corpus.steps()[index];
    let run = manifest.run_manifest()?;
    let mut turns = [None, None];
    for arm in 0..2 {
        let d = dir.join(ARM_NAMES[arm]);
        ordinary(&d)?;
        if !d.is_dir() { return Err("SelectedDirectory".into()); }
        let path = database(&d, index, manifest.source_kind);
        let checkpoint = checkpoint_path(&d, index);
        ordinary(&path)?;
        ordinary(&checkpoint)?;
        for entry in fs::read_dir(&d).map_err(|_| "Io")? {
            let entry = entry.map_err(|_| "Io")?;
            let name = entry.file_name();
            let name = name.to_str().ok_or("SelectedDirectory")?;
            if let Some(number) = name.strip_prefix("attempt-")
                .and_then(|s| s.strip_suffix(".json"))
                .filter(|s| s.bytes().all(|b| b.is_ascii_digit()))
            {
                if number != format!("{index:02}") { return Err("CheckpointMismatch".into()); }
            }
            if name.ends_with(".sqlite") && entry.path() != path {
                return Err("SelectedDirectory".into());
            }
        }
        if let Some(before) = source {
            validate_pair_source(&path, corpus.seed(), before[arm].receipts(), step)?;
        }
        if !path.exists() {
            if checkpoint.exists() { return Err("CheckpointMismatch".into()); }
            continue;
        }
        let input = &manifest.source_inputs[arm];
        let mut store = Store::open_read_only(&path).map_err(|_| "Workspace")?;
        if store.stories().map_err(|_| "Workspace")?.is_empty() {
            if checkpoint.exists() || source.is_none() {
                return Err("BootstrapIncomplete".into());
            }
            continue;
        }
        let full = store.resume(&input.scope).map_err(|_| "Replay")?.engine;
        match store.lookup_turn(&input.scope, &input.request.turn) {
            Ok(record) => {
                if record.request != input.request { return Err("ReferencePrefix".into()); }
                if !checkpoint.exists() && matches!(record.phase,
                    locallore_storage::TurnPhase::Cancelled | locallore_storage::TurnPhase::Failed
                        | locallore_storage::TurnPhase::Stale)
                {
                    // No recorded failure cause can be invented from canonical
                    // history. Do not clear a terminal key and regenerate it.
                    return Err("TerminalCheckpointMissing".into());
                }
            }
            Err(locallore_storage::TurnError::UnknownTurn) => {}
            Err(_) => return Err("Lookup".into()),
        }
        drop(store);
        if full.domain_version() != 1 || full.seed() != corpus.seed() {
            return Err("ReferencePrefix".into());
        }
        if full.revision() < input.before_head {
            if checkpoint.exists() || source.is_none() {
                return Err("BootstrapIncomplete".into());
            }
            continue;
        }
        let before = full.at_revision(input.before_head).map_err(|_| "ReferencePrefix")?;
        validate_rollout_source(&before, &corpus)?;
        if before.receipts().iter().any(|receipt|
            corpus.steps().iter().position(|s| s.id() == receipt.request().turn)
                .is_none_or(|n| n >= index))
            || digest(&encode(before.receipts())?) != input.prefix_sha256
            || step.request(&before) != input.request
            || v2::semantic_input(&before, &input.request)? != input.input_semantic_sha256
        {
            return Err("ReferencePrefix".into());
        }
        if let Some(expected) = source {
            if before.accepted_history_basis().map_err(|_| "Source")?
                != expected[arm].accepted_history_basis().map_err(|_| "Source")?
            { return Err("ReferencePrefix".into()); }
        }
        validate_pair_source(&path, corpus.seed(), before.receipts(), step)?;
        if checkpoint.exists() {
            let turn = load_turn(&d, &path, index, ARM_NAMES[arm], POLICIES[arm],
                &manifest.binding, &run)?;
            if turn.request != input.request || turn.before_head != input.before_head
                || turn.row.input_semantic_sha256 != input.input_semantic_sha256
            { return Err("CheckpointMismatch".into()); }
            turns[arm] = Some(turn);
        }
    }
    // Read both ledgers before a caller can reserve either one. Loading does
    // not settle/refund unknown invocations or admissions.
    Ledger::load(&dir.join("left"), &manifest.binding)?;
    Ledger::load(&dir.join("right"), &manifest.binding)?;
    Ok(turns)
}

#[derive(Serialize)]
struct Progress { arm: String, state: String }

/// Bounded data-only diagnostics. No deserialization or public authority fields.
#[derive(Serialize)]
pub struct SelectedComparisonReportV1 {
    version: u16,
    run_type: String,
    source_protocol_version: u16,
    binding: String,
    source_binding: String,
    source_kind: ComparisonKind,
    source_profile: PlayProfile,
    selection: Selection,
    lane: String,
    profile: PlayProfile,
    suite_sha256: String,
    source_sha256: String,
    source_reference_sha256: Option<String>,
    source_inputs: [SourceInput; 2],
    rows: Vec<TurnReportV2>,
    completed: bool,
    per_arm_progress: [Progress; 2],
    physical_setups: usize,
    physical_setup_ms: Option<u64>,
    native_load: Option<Value>,
    left_charged_ms: u64,
    right_charged_ms: u64,
    left_reserved_roles: usize,
    right_reserved_roles: usize,
    human_reviewed: usize,
    human_rubric: String,
    quality_accepted: bool,
    unavailable: Vec<String>,
    limitations: Vec<String>,
}

fn ledgers(dir: &Path, binding: &str) -> Result<[Ledger; 2]> {
    Ok([Ledger::load(&dir.join("left"), binding)?,
        Ledger::load(&dir.join("right"), binding)?])
}

fn report(
    dir: &Path, manifest: &SelectedManifest, turns: &[Option<StoredTurn>; 2],
    ledgers: &[Ledger; 2],
) -> Result<SelectedComparisonReportV1> {
    let mut unavailable = vec!["scripted_lane_no_native_setup_measurement".into(),
        "selected_native_execution_unavailable".into(), "human_quality_not_reviewed".into()];
    for arm in 0..2 {
        if let Some(turn) = &turns[arm] {
            if !turn.row.roles_known {
                unavailable.push(format!("{}:unknown_historical_roles", ARM_NAMES[arm]));
            }
            if !turn.row.context_evidence_available {
                unavailable.push(format!("{}:context_unavailable", ARM_NAMES[arm]));
            }
        }
    }
    append_ledger_notes(dir, ledgers, &mut unavailable);
    let progress = |arm: usize| Progress {
        arm: ARM_NAMES[arm].into(),
        state: if turns[arm].is_some() { "finished" }
            else if database(&dir.join(ARM_NAMES[arm]), manifest.selection.index,
                manifest.source_kind).exists() { "interrupted" } else { "not_started" }.into(),
    };
    let result = SelectedComparisonReportV1 {
        version: 1, run_type: "selected_case".into(), source_protocol_version: 2,
        binding: manifest.binding.clone(), source_binding: manifest.source_binding.clone(),
        source_kind: manifest.source_kind, source_profile: manifest.source_profile.clone(),
        selection: manifest.selection.clone(), lane: LANE.into(), profile: manifest.profile.clone(),
        suite_sha256: manifest.suite_sha256.clone(), source_sha256: manifest.source_sha256.clone(),
        source_reference_sha256: manifest.source_reference_sha256.clone(),
        source_inputs: manifest.source_inputs.clone(),
        rows: turns.iter().flatten().map(|turn| turn.row.clone()).collect(),
        completed: turns.iter().all(Option::is_some),
        per_arm_progress: [progress(0), progress(1)],
        physical_setups: 0, physical_setup_ms: None, native_load: None,
        left_charged_ms: ledgers[0].charged_ms, right_charged_ms: ledgers[1].charged_ms,
        left_reserved_roles: ledgers[0].charged_roles, right_reserved_roles: ledgers[1].charged_roles,
        human_reviewed: 0, human_rubric: "not_reviewed".into(), quality_accepted: false,
        unavailable,
        limitations: vec![
            "Only the selected original turn is attempted in each actual policy arm; this is not a full comparison.".into(),
            "Synthetic scripted execution does not qualify native inference, prose quality, Android or phone performance.".into(),
            "Hashes bind retained diagnostics and detect drift; they do not authenticate adversarial rewrites.".into(),
            "Missing workflow evidence does not prove zero historical provider work.".into(),
        ],
    };
    if encode(&result)?.len() > crate::MAX_REPORT { return Err("ReportBudget".into()); }
    Ok(result)
}

fn publish_selected(dir: &Path, report: &SelectedComparisonReportV1) -> Result<()> {
    let data = serde_json::to_vec_pretty(report).map_err(|_| "Encoding")?;
    let html = format!("<!doctype html><meta charset=utf-8><meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'none'\"><title>Isolated selected comparison</title><h1>Isolated selected comparison</h1><p>Synthetic scripted evaluation. No human quality acceptance.</p><pre>{}</pre>",
        escape(std::str::from_utf8(&data).map_err(|_| "Encoding")?));
    if data.len() > crate::MAX_REPORT || html.len() > crate::MAX_REPORT {
        return Err("ReportBudget".into());
    }
    for (name, bytes) in [("report.json", data.as_slice()), ("report.html", html.as_bytes())] {
        let path = dir.join(name);
        ordinary(&path)?;
        fs::write(path, bytes).map_err(|_| "Io")?;
    }
    Ok(())
}

fn execute_selected(
    plan: &PreparedSelectedPlan, destination: &Destination, cancel: &Cancellation,
    started: Instant,
) -> Result<SelectedComparisonReportV1> {
    let dir = &destination.dir;
    let manifest = &destination.manifest;
    let mut turns = validate_destination(dir, manifest, Some(&plan.before))?;
    let mut ledgers = ledgers(dir, &manifest.binding)?;
    if turns.iter().all(Option::is_some) {
        // Completed resume is a read-only result, including no report rewrite.
        return report(dir, manifest, &turns, &ledgers);
    }
    cancelled(cancel)?;
    for ledger in &mut ledgers {
        ledger.started = started;
        if ledger.invocations >= 32 || ledger.remaining() < PREPARATION_MS {
            return Err("RunBudget".into());
        }
    }
    // Both source/destination arms and both resource capacities have passed
    // preflight. Unknown reservations on any later error remain durable.
    ledgers[0].begin_invocation()?;
    ledgers[1].begin_invocation()?;
    let corpus = suite()?;
    let index = manifest.selection.index;
    let step = &corpus.steps()[index];
    let first_arm = match manifest.source_kind {
        ComparisonKind::PairedSnapshots => index % 2,
        ComparisonKind::ContinuousRollout => (index / 6) % 2,
    };
    for arm in [first_arm, 1 - first_arm] {
        if turns[arm].is_some() { continue; }
        let began = Instant::now();
        let d = dir.join(ARM_NAMES[arm]);
        let path = database(&d, index, manifest.source_kind);
        let recovered = if path.exists()
            && !Store::open_read_only(&path).map_err(|_| "Workspace")?
                .stories().map_err(|_| "Workspace")?.is_empty()
        {
            let full = engine(&path, &corpus.seed().scope)?;
            recover_committed_turn(RecoveryJob {
                path: &path, full: &full, index, arm: ARM_NAMES[arm],
                policy: POLICIES[arm], binding: &manifest.binding, step,
                profile: &manifest.profile,
            })?
        } else { None };
        let turn = if let Some(turn) = recovered {
            // A known actual commit wins over a late cancel. This branch has
            // no factory/provider/admission and does not replay a second commit.
            turn
        } else {
            if cancel.is_cancelled() { break; }
            ensure_database(&path, corpus.seed(), plan.before[arm].receipts())?;
            validate_pair_source(&path, corpus.seed(), plan.before[arm].receipts(), step)?;
            if cancel.is_cancelled() { break; }
            // Only this genuine missing attempt constructs the existing script.
            let factory = LaneFactory::ScriptedBaseline;
            execute_turn(TurnJob {
                dir: &d, path: &path, index, arm: ARM_NAMES[arm], policy: POLICIES[arm],
                binding: &manifest.binding, step, factory: &factory, cancel,
            }, &mut ledgers[arm])?
        };
        if !checkpoint_path(&d, index).exists() {
            // Normal execute_turn already wrote its checkpoint before settling.
            // Recovery/dependency-only returns can lack that workflow file.
            saved(&checkpoint_path(&d, index), &turn, 256 * 1024)?;
        }
        turns[arm] = Some(turn);
        ledgers[1 - arm].exclude_measured_interval(
            began.elapsed().as_millis().min(u64::MAX as u128) as u64)?;
    }
    // Actual replay/checkpoint/capture validation is preparation overhead, not
    // a cached row assertion. Finish only after this real work succeeds.
    let turns = validate_destination(dir, manifest, Some(&plan.before))?;
    report(dir, manifest, &turns, &ledgers)?;
    for arm in 0..2 {
        let began = Instant::now();
        ledgers[arm].finish()?;
        ledgers[1 - arm].exclude_measured_interval(
            began.elapsed().as_millis().min(u64::MAX as u128) as u64)?;
    }
    let result = report(dir, manifest, &turns, &ledgers)?;
    publish_selected(dir, &result)?;
    Ok(result)
}

pub fn run_selected(
    plan: PreparedSelectedPlan, new_dir: &Path, cancel: &Cancellation,
) -> Result<SelectedComparisonReportV1> {
    let started = Instant::now();
    plan.refresh(cancel)?;
    cancelled(cancel)?;
    let destination = new_destination(&plan, new_dir)?;
    execute_selected(&plan, &destination, cancel, started)
}

pub fn inspect_selected(dir: &Path) -> Result<SelectedComparisonReportV1> {
    let opened = open_destination(dir)?;
    let turns = validate_destination(&opened.dir, &opened.manifest, None)?;
    report(&opened.dir, &opened.manifest, &turns,
        &ledgers(&opened.dir, &opened.manifest.binding)?)
}

pub fn resume_selected(
    dir: &Path, source_dir: &Path, expected_binding: &str, cancel: &Cancellation,
) -> Result<SelectedComparisonReportV1> {
    let started = Instant::now();
    cancelled(cancel)?;
    if !hex(expected_binding) { return Err("SelectedIdentity".into()); }
    let destination = open_destination(dir)?;
    let manifest = &destination.manifest;
    if manifest.binding != expected_binding { return Err("CheckpointMismatch".into()); }
    let row = desktop_api::RowId {
        turn: manifest.selection.turn.clone(),
        arm: if manifest.selection.clicked_arm == "left" {
            desktop_api::Arm::Left
        } else { desktop_api::Arm::Right },
    };
    let plan = prepare_selected(source_dir, &manifest.source_binding, &row,
        SelectedIntent { client_id: manifest.client_id.clone(), lane: SelectedLane::ScriptedBaseline },
        cancel)?;
    disjoint(&plan.source_dir, &destination.dir)?;
    if plan.manifest != *manifest { return Err("CheckpointMismatch".into()); }
    plan.refresh(cancel)?;
    execute_selected(&plan, &destination, cancel, started)
}
