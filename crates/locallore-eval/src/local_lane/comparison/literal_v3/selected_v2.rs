//! Versioned isolated reruns of actual protocol3 inputs. No desktop/model grant.
use super::*;
use crate::local_lane::comparison::{desktop_api as shared_read, selected as shared};
use shared::{SelectedIntent, SelectedLane, Selection, SourceInput, MANIFEST_CAP};

const LANE: &str = "scripted_selected_case";
const NATIVE_LANE: &str = "native_selected_case";
#[cfg(feature = "local-model")]
mod native;
#[cfg(feature = "local-model")]
pub use native::{resume_native_selected, run_native_selected};
#[cfg(all(test, feature = "local-model"))]
mod native_review_tests;
#[cfg(test)]
mod review_tests;
#[cfg(test)]
thread_local! {
    // Fixed unit boundary only; absent from normal builds and IPC.
    static CANCEL_AFTER_ARM: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

#[derive(Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SelectedManifest2 {
    version: u16,
    run_type: String,
    source_protocol_version: u16,
    arms: [ArmDescriptorV3; 2],
    client_id: String,
    binding: String,
    source_binding: String,
    source_kind: ComparisonKind,
    source_profile: PlayProfile,
    source_native: bool,
    selection: Selection,
    lane: String,
    profile: PlayProfile,
    suite_sha256: String,
    source_sha256: String,
    #[serde(deserialize_with = "v3::required_nullable")]
    source_reference_sha256: Option<String>,
    source_inputs: [SourceInput; 2],
}
impl SelectedManifest2 {
    fn digest(&self) -> Result<String> {
        let mut value = serde_json::to_value(self).map_err(|_| "Encoding")?;
        value
            .as_object_mut()
            .ok_or("SelectedBinding")?
            .remove("binding");
        Ok(digest(&encode(&value)?))
    }
    fn lane(&self) -> Result<SelectedLane> {
        match self.lane.as_str() {
            LANE => Ok(SelectedLane::ScriptedBaseline),
            NATIVE_LANE => Ok(SelectedLane::ApprovedNative),
            _ => Err("SelectedBinding".into()),
        }
    }
    fn native(&self) -> Result<bool> {
        Ok(matches!(self.lane()?, SelectedLane::ApprovedNative))
    }
    fn execution_manifest(&self) -> Result<Manifest> {
        Manifest::new_with_lane(
            self.source_kind,
            self.profile.clone(),
            self.native()?,
            self.source_reference_sha256.clone(),
        )
    }
    fn validate(&self) -> Result<()> {
        let corpus = suite()?;
        let step = corpus
            .steps()
            .get(self.selection.index)
            .ok_or("UnknownRow")?;
        let seed = Engine::new(corpus.seed().clone()).map_err(|_| "Seed")?;
        let template = step.request(&seed);
        self.execution_manifest()?.validate()?;
        Manifest::new_with_lane(
            self.source_kind,
            self.source_profile.clone(),
            self.source_native,
            self.source_reference_sha256.clone(),
        )?
        .validate()?;
        if self.version != 2
            || self.source_protocol_version != 3
            || self.run_type != "selected_case"
            || self.arms != v3::arm_descriptors()
            || !matches!(self.lane.as_str(), LANE | NATIVE_LANE)
            || !shared::client_valid(&self.client_id)
            || !hex(&self.binding)
            || self.binding != self.digest()?
            || !hex(&self.source_binding)
            || !hex(&self.source_sha256)
            || self.suite_sha256 != v3::current_binding(false)?.suite_sha256
            || (!self.native()? && self.profile != LaneFactory::ScriptedBaseline.profile()?)
            || self.selection.turn != step.id()
            || !ARM_NAMES.contains(&self.selection.clicked_arm.as_str())
        {
            return Err("SelectedBinding".into());
        }
        for (arm, input) in self.source_inputs.iter().enumerate() {
            if input.arm != ARM_NAMES[arm]
                || input.scope != corpus.seed().scope
                || input.request.scope != input.scope
                || input.request.version != template.version
                || input.request.turn != self.selection.turn
                || input.request.expected_revision != input.before_head
                || input.request.intent != template.intent
                || !hex(&input.prefix_sha256)
                || !hex(&input.input_semantic_sha256)
            {
                return Err("SelectedInput".into());
            }
        }
        Ok(())
    }
}

/// Own source lock and actual Core histories, never deserialized authority.
pub struct PreparedSelectedPlan {
    _source: desktop_api::OpenedComparison,
    source_dir: PathBuf,
    manifest: SelectedManifest2,
    before: [Engine; 2],
}

type SourceSnapshot = (Value, Manifest, [Vec<StoredTurn3>; 2]);
fn source_inputs(
    dir: &Path,
    snapshot: &SourceSnapshot,
    selection: &Selection,
) -> Result<[Engine; 2]> {
    let (_, manifest, turns) = snapshot;
    let corpus = suite()?;
    let reference = if manifest.kind == ComparisonKind::PairedSnapshots {
        let reference = open_reference(&dir.join("reference"))?;
        if !reference.manifest.source_matches()?
            || Some(reference.digest()?) != manifest.reference_sha256
        {
            return Err("ReferenceSourceMismatch".into());
        }
        Some(reference)
    } else {
        None
    };
    let mut before = Vec::with_capacity(2);
    for arm in 0..2 {
        let stored = turns[arm].get(selection.index).ok_or("UnknownRow")?;
        let full = engine(
            &database(&dir.join(ARM_NAMES[arm]), selection.index, manifest.kind),
            &corpus.seed().scope,
        )?;
        if full.domain_version() != 1 || full.seed() != corpus.seed() {
            return Err("SelectedInput".into());
        }
        let cut = full.at_revision(stored.before_head).map_err(|_| "Replay")?;
        let after = full.at_revision(stored.after_head).map_err(|_| "Replay")?;
        let request = corpus.steps()[selection.index].request(&cut);
        if request != stored.request
            || stored.row.turn != selection.turn
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
    snapshot: &SourceSnapshot,
    selection: Selection,
    client_id: String,
    before: &[Engine; 2],
    lane: SelectedLane,
) -> Result<SelectedManifest2> {
    let (value, source, _) = snapshot;
    if !source.source_matches()? {
        return Err("SourceMismatch".into());
    }
    let corpus = suite()?;
    let make_input = |arm: usize| -> Result<SourceInput> {
        let engine = &before[arm];
        let request = corpus.steps()[selection.index].request(engine);
        Ok(SourceInput {
            arm: ARM_NAMES[arm].into(),
            scope: engine.scope().clone(),
            before_head: engine.revision(),
            prefix_sha256: digest(&encode(engine.receipts())?),
            input_semantic_sha256: v2::semantic_input(engine, &request)?,
            request,
        })
    };
    let mut result = SelectedManifest2 {
        version: 2,
        run_type: "selected_case".into(),
        source_protocol_version: 3,
        arms: v3::arm_descriptors(),
        client_id,
        binding: String::new(),
        source_binding: value["binding"].as_str().ok_or("Source")?.into(),
        source_kind: source.kind,
        source_profile: source.profile.clone(),
        source_native: source.binding.native,
        selection: selection.clone(),
        lane: match lane {
            SelectedLane::ScriptedBaseline => LANE,
            SelectedLane::ApprovedNative => NATIVE_LANE,
        }
        .into(),
        profile: lane.profile()?,
        suite_sha256: source.binding.suite_sha256.clone(),
        source_sha256: source.source_sha256.clone(),
        source_reference_sha256: source.reference_sha256.clone(),
        source_inputs: [make_input(0)?, make_input(1)?],
    };
    result.binding = result.digest()?;
    result.validate()?;
    Ok(result)
}

pub fn prepare_selected(
    source_dir: &Path,
    expected_source_binding: &str,
    row: &shared_read::RowId,
    intent: SelectedIntent,
    cancel: &Cancellation,
) -> Result<PreparedSelectedPlan> {
    shared::cancelled(cancel)?;
    if !shared::client_valid(&intent.client_id) || !hex(expected_source_binding) {
        return Err("SelectedIdentity".into());
    }
    if matches!(intent.lane, SelectedLane::ApprovedNative) {
        #[cfg(not(feature = "local-model"))]
        return Err("SelectedNativeUnavailable".into());
    }
    intent.lane.profile()?;
    let corpus = suite()?;
    let selection = Selection {
        turn: row.turn.clone(),
        index: corpus
            .steps()
            .iter()
            .position(|s| s.id() == row.turn)
            .ok_or("UnknownRow")?,
        clicked_arm: ARM_NAMES[usize::from(matches!(row.arm, shared_read::Arm::Right))].into(),
    };
    let source = desktop_api::open_read_only(source_dir)?;
    let directory = fs::canonicalize(source_dir).map_err(|_| "Io")?;
    let snapshot = desktop_api::fresh_open_snapshot(&source);
    if snapshot.0["binding"].as_str() != Some(expected_source_binding) {
        return Err("SnapshotMismatch".into());
    }
    let before = source_inputs(&directory, &snapshot, &selection)?;
    let manifest = manifest_for(&snapshot, selection, intent.client_id, &before, intent.lane)?;
    shared::cancelled(cancel)?;
    Ok(PreparedSelectedPlan {
        _source: source,
        source_dir: directory,
        manifest,
        before,
    })
}
impl PreparedSelectedPlan {
    fn refresh(&self, cancel: &Cancellation) -> Result<()> {
        shared::cancelled(cancel)?;
        let snapshot = desktop_api::snapshot(&self.source_dir)?;
        let before = source_inputs(&self.source_dir, &snapshot, &self.manifest.selection)?;
        let manifest = manifest_for(
            &snapshot,
            self.manifest.selection.clone(),
            self.manifest.client_id.clone(),
            &before,
            self.manifest.lane()?,
        )?;
        if manifest != self.manifest {
            return Err("SnapshotMismatch".into());
        }
        for (actual, expected) in before.iter().zip(&self.before) {
            if actual.accepted_history_basis().map_err(|_| "Source")?
                != expected.accepted_history_basis().map_err(|_| "Source")?
            {
                return Err("SnapshotMismatch".into());
            }
        }
        shared::cancelled(cancel)
    }
}
pub fn prepared_metadata(plan: &PreparedSelectedPlan) -> Result<Value> {
    let m = &plan.manifest;
    let arms: Vec<Value> = m
        .source_inputs
        .iter()
        .map(|i| {
            json!({"arm":i.arm,"scope":i.scope,"before_head":i.before_head,
        "prefix_sha256":i.prefix_sha256,"input_semantic_sha256":i.input_semantic_sha256})
        })
        .collect();
    let value = json!({"version":2,"kind":"selected_prepared","source_protocol_version":3,"binding":m.binding,
        "lane":m.lane,"selection":m.selection,"arms":arms,"constructions":m.arms});
    if encode(&value)?.len() > 16 * 1024 {
        return Err("ReportBudget".into());
    }
    Ok(value)
}

struct Destination {
    dir: PathBuf,
    manifest: SelectedManifest2,
    _pins: Vec<File>,
    _lock: File,
}
fn open_destination(dir: &Path) -> Result<Destination> {
    let pins = shared::pin_selected(dir)?;
    ordinary(&dir.join("run.lock"))?;
    let lock = OpenOptions::new()
        .read(true)
        .open(dir.join("run.lock"))
        .map_err(|_| "Io")?;
    lock.try_lock().map_err(|_| "RunBusy")?;
    let manifest: SelectedManifest2 = decode(&dir.join("selected.json"), MANIFEST_CAP)?;
    manifest.validate()?;
    Ok(Destination {
        dir: fs::canonicalize(dir).map_err(|_| "Io")?,
        manifest,
        _pins: pins,
        _lock: lock,
    })
}
fn new_destination(plan: &PreparedSelectedPlan, dir: &Path) -> Result<Destination> {
    let (canonical, mut pins) = shared::destination_target_for(&plan.source_dir, dir)?;
    fs::create_dir(&canonical).map_err(|_| "OutputExists")?;
    let lock = take_lock(&canonical)?;
    saved(
        &canonical.join("selected.json"),
        &plan.manifest,
        MANIFEST_CAP,
    )?;
    for arm in ARM_NAMES {
        fs::create_dir(canonical.join(arm)).map_err(|_| "Io")?;
    }
    pins.extend(shared::pin_selected(&canonical)?);
    Ok(Destination {
        dir: canonical,
        manifest: plan.manifest.clone(),
        _pins: pins,
        _lock: lock,
    })
}
fn validate_destination(
    dir: &Path,
    manifest: &SelectedManifest2,
    source: Option<&[Engine; 2]>,
) -> Result<[Option<StoredTurn3>; 2]> {
    let index = manifest.selection.index;
    let checkpoints = shared::validate_prefixes(
        dir,
        index,
        manifest.source_kind,
        &manifest.source_inputs,
        source,
    )?;
    let execution = manifest.execution_manifest()?;
    let mut turns = [None, None];
    for arm in 0..2 {
        if checkpoints[arm] {
            let d = dir.join(ARM_NAMES[arm]);
            let turn = load_turn3(
                &d,
                &database(&d, index, manifest.source_kind),
                index,
                arm,
                &manifest.binding,
                &execution,
            )?;
            let input = &manifest.source_inputs[arm];
            if turn.request != input.request
                || turn.before_head != input.before_head
                || turn.row.input_semantic_sha256 != input.input_semantic_sha256
            {
                return Err("CheckpointMismatch".into());
            }
            turns[arm] = Some(turn);
        }
    }
    shared::ledgers(dir, &manifest.binding)?;
    shared::validate_setups(dir, &manifest.binding, manifest.native()?)?;
    Ok(turns)
}

/// Data-only version2 report. Fields are never an execution or observer grant.
#[derive(Serialize)]
pub struct SelectedComparisonReportV2 {
    #[serde(flatten)]
    identity: SelectedManifest2,
    rows: Vec<TurnReportV3>,
    completed: bool,
    per_arm_progress: [Value; 2],
    physical_setups: usize,
    physical_setup_ms: Option<u64>,
    native_load: Option<Value>,
    left_charged_ms: u64,
    right_charged_ms: u64,
    left_reserved_roles: usize,
    right_reserved_roles: usize,
    human_reviewed: usize,
    quality_accepted: bool,
    unavailable: Vec<String>,
    limitations: Vec<String>,
}
fn report(
    dir: &Path,
    manifest: &SelectedManifest2,
    turns: &[Option<StoredTurn3>; 2],
    ledgers: &[Ledger; 2],
) -> Result<SelectedComparisonReportV2> {
    let native = manifest.native()?;
    let setups = shared::setup_records(dir, &manifest.binding, native)?;
    let mut unavailable = vec![
        "selected_protocol3_gui_unavailable".into(),
        "human_quality_not_reviewed".into(),
    ];
    if !native {
        unavailable.push("scripted_lane_no_native_setup_measurement".into());
    }
    if native && setups.is_empty() {
        unavailable.push("native_setup_measurement_unavailable".into());
    }
    for setup in &setups {
        if setup.status == "failed" {
            unavailable.push(format!(
                "native_setup_failed_invocation:{}",
                setup.left_invocation
            ));
        }
    }
    append_ledger_notes(dir, ledgers, &mut unavailable);
    let progress = |arm: usize| {
        json!({"arm":ARM_NAMES[arm],"state": if turns[arm].is_some() {"finished"}
        else if database(&dir.join(ARM_NAMES[arm]),manifest.selection.index,manifest.source_kind).exists() {"interrupted"} else {"not_started"}})
    };
    let result = SelectedComparisonReportV2 { identity: manifest.clone(), rows: turns.iter().flatten().map(|t| t.row.clone()).collect(),
        completed: turns.iter().all(Option::is_some), per_arm_progress: [progress(0),progress(1)],
        physical_setups: setups.len(),
        physical_setup_ms: if setups.is_empty() { None } else { Some(setups.iter().try_fold(0u64,|total,setup| total.checked_add(setup.physical_ms).ok_or("SetupIntegrity"))?) },
        native_load: if setups.is_empty() { None } else { Some(json!(setups.iter().map(|setup| &setup.load).collect::<Vec<_>>())) },
        left_charged_ms: ledgers[0].charged_ms, right_charged_ms: ledgers[1].charged_ms,
        left_reserved_roles: ledgers[0].charged_roles, right_reserved_roles: ledgers[1].charged_roles,
        human_reviewed: 0, quality_accepted: false, unavailable,
        limitations: vec!["Only the selected original turn is attempted in each actual construction; this is not a full comparison.".into(),
            if native { "A native label does not establish measured generation, prose quality, Android or phone performance.".into() } else { "Synthetic scripted execution does not qualify native inference, prose quality, Android or phone performance.".into() },
            "Hashes detect retained-data drift; they do not authenticate adversarial rewrites.".into(),
            "Missing workflow evidence does not prove zero historical provider work.".into()] };
    if encode(&result)?.len() > crate::MAX_REPORT {
        return Err("ReportBudget".into());
    }
    Ok(result)
}

struct Work {
    turns: [Option<StoredTurn3>; 2],
    ready: [Option<StoredTurn3>; 2],
    ledgers: [Ledger; 2],
    needs_admission: [bool; 2],
}
fn inspect_work(plan: &PreparedSelectedPlan, dir: &Path, started: Instant) -> Result<Work> {
    let m = &plan.manifest;
    let turns = if dir.exists() {
        validate_destination(dir, m, Some(&plan.before))?
    } else {
        [None, None]
    };
    let mut work = Work {
        turns,
        ready: [None, None],
        ledgers: shared::ledgers(dir, &m.binding)?,
        needs_admission: [false; 2],
    };
    let corpus = suite()?;
    let step = &corpus.steps()[m.selection.index];
    for arm in 0..2 {
        work.ledgers[arm].started = started;
        if work.turns[arm].is_some() {
            continue;
        }
        let path = database(&dir.join(ARM_NAMES[arm]), m.selection.index, m.source_kind);
        let full = if path.exists()
            && !Store::open_read_only(&path)
                .map_err(|_| "Workspace")?
                .stories()
                .map_err(|_| "Workspace")?
                .is_empty()
        {
            engine(&path, &corpus.seed().scope)?
        } else {
            plan.before[arm].clone()
        };
        // A missing DB cannot have a committed receipt for the selected turn;
        // recover_actual reads Store only if the actual Engine has that receipt.
        work.ready[arm] = ready_turn3(ReadyJob3 {
            path: &path,
            full: &full,
            index: m.selection.index,
            arm: ARM_NAMES[arm],
            construction: CONSTRUCTIONS[arm],
            binding: &m.binding,
            step,
            profile: &m.profile,
        })?;
        work.needs_admission[arm] = work.ready[arm].is_none();
    }
    Ok(work)
}
fn preflight(work: &Work) -> Result<()> {
    for arm in 0..2 {
        work.ledgers[arm].preflight_invocation(work.needs_admission[arm])?;
    }
    Ok(())
}
fn execute_work(
    plan: &PreparedSelectedPlan,
    destination: &Destination,
    work: &mut Work,
    factory: Option<&LaneFactory>,
    cancel: &Cancellation,
) -> Result<()> {
    let dir = &destination.dir;
    let m = &destination.manifest;
    let corpus = suite()?;
    let index = m.selection.index;
    let step = &corpus.steps()[index];
    let first = match m.source_kind {
        ComparisonKind::PairedSnapshots => index % 2,
        ComparisonKind::ContinuousRollout => (index / 6) % 2,
    };
    for arm in [first, 1 - first] {
        if work.turns[arm].is_some() {
            continue;
        }
        let began = Instant::now();
        let d = dir.join(ARM_NAMES[arm]);
        let path = database(&d, index, m.source_kind);
        let recovered = work.ready[arm]
            .as_ref()
            .is_some_and(|t| t.row.recovered_without_checkpoint);
        if !recovered {
            if cancel.is_cancelled() {
                break;
            }
            ensure_database(&path, corpus.seed(), plan.before[arm].receipts())?;
            validate_pair_source(&path, corpus.seed(), plan.before[arm].receipts(), step)?;
            if cancel.is_cancelled() {
                break;
            }
        }
        let turn = match work.ready[arm].take() {
            Some(turn) => turn,
            None => execute_turn3(
                Job3 {
                    dir: &d,
                    path: &path,
                    index,
                    arm: ARM_NAMES[arm],
                    construction: CONSTRUCTIONS[arm],
                    binding: &m.binding,
                    step,
                    factory: factory.ok_or("Provider")?,
                    cancel,
                },
                &mut work.ledgers[arm],
            )?,
        };
        if !checkpoint_path(&d, index).exists() {
            saved(&checkpoint_path(&d, index), &turn, 256 * 1024)?;
        }
        work.turns[arm] = Some(turn);
        #[cfg(test)]
        if CANCEL_AFTER_ARM.with(std::cell::Cell::get) {
            cancel.cancel();
        }
        work.ledgers[1 - arm]
            .exclude_measured_interval(began.elapsed().as_millis().min(u64::MAX as u128) as u64)?;
    }
    Ok(())
}
fn finish_workflow(
    plan: &PreparedSelectedPlan,
    destination: &Destination,
    work: &mut Work,
) -> Result<SelectedComparisonReportV2> {
    let dir = &destination.dir;
    let m = &destination.manifest;
    let turns = validate_destination(dir, m, Some(&plan.before))?;
    report(dir, m, &turns, &work.ledgers)?;
    turn_execution::finish_pair(&mut work.ledgers)?;
    let result = report(dir, m, &turns, &work.ledgers)?;
    shared::publish_report(
        dir,
        &result,
        if m.native()? {
            "Synthetic selected evaluation. Native measurements exist only where recorded. No human quality acceptance."
        } else {
            "Synthetic scripted evaluation. No human quality acceptance."
        },
    )?;
    Ok(result)
}

fn execute(
    plan: &PreparedSelectedPlan,
    destination: &Destination,
    mut work: Work,
    cancel: &Cancellation,
) -> Result<SelectedComparisonReportV2> {
    let dir = &destination.dir;
    let m = &destination.manifest;
    if work.turns.iter().all(Option::is_some) {
        return report(dir, m, &work.turns, &work.ledgers);
    }
    shared::cancelled(cancel)?;
    preflight(&work)?;
    work.ledgers[0].begin_invocation()?;
    work.ledgers[1].begin_invocation()?;
    execute_work(
        plan,
        destination,
        &mut work,
        Some(&LaneFactory::ScriptedBaseline),
        cancel,
    )?;
    finish_workflow(plan, destination, &mut work)
}

pub fn run_selected(
    plan: PreparedSelectedPlan,
    new_dir: &Path,
    cancel: &Cancellation,
) -> Result<SelectedComparisonReportV2> {
    let started = Instant::now();
    if plan.manifest.native()? {
        return Err("SelectedLaneMismatch".into());
    }
    plan.refresh(cancel)?;
    let (_target, _pins) = shared::destination_target_for(&plan.source_dir, new_dir)?;
    let work = inspect_work(&plan, new_dir, started)?;
    preflight(&work)?;
    shared::cancelled(cancel)?;
    let destination = new_destination(&plan, new_dir)?;
    execute(&plan, &destination, work, cancel)
}
pub fn inspect_selected(dir: &Path) -> Result<SelectedComparisonReportV2> {
    let destination = open_destination(dir)?;
    let m = &destination.manifest;
    let turns = validate_destination(&destination.dir, m, None)?;
    report(
        &destination.dir,
        m,
        &turns,
        &shared::ledgers(&destination.dir, &m.binding)?,
    )
}
pub fn resume_selected(
    dir: &Path,
    source_dir: &Path,
    expected_binding: &str,
    cancel: &Cancellation,
) -> Result<SelectedComparisonReportV2> {
    let started = Instant::now();
    shared::cancelled(cancel)?;
    if !hex(expected_binding) {
        return Err("SelectedIdentity".into());
    }
    let destination = open_destination(dir)?;
    let m = &destination.manifest;
    if m.native()? {
        return Err("SelectedLaneMismatch".into());
    }
    if m.binding != expected_binding {
        return Err("CheckpointMismatch".into());
    }
    let row = shared_read::RowId {
        turn: m.selection.turn.clone(),
        arm: if m.selection.clicked_arm == "left" {
            shared_read::Arm::Left
        } else {
            shared_read::Arm::Right
        },
    };
    let plan = prepare_selected(
        source_dir,
        &m.source_binding,
        &row,
        SelectedIntent {
            client_id: m.client_id.clone(),
            lane: SelectedLane::ScriptedBaseline,
        },
        cancel,
    )?;
    shared::disjoint(&plan.source_dir, &destination.dir)?;
    if plan.manifest != *m {
        return Err("CheckpointMismatch".into());
    }
    plan.refresh(cancel)?;
    let work = inspect_work(&plan, &destination.dir, started)?;
    execute(&plan, &destination, work, cancel)
}
