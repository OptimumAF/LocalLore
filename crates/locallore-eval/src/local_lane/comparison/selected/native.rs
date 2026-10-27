// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Native selected workflow over the same turn, Store and resource authorities.
use super::super::native_selected_workflow::save_setup_at;
use super::native_owner::{SelectedNativeFailure, SelectedNativeReservation};
use super::*;

type NativeResult<T, R> = std::result::Result<T, SelectedNativeFailure<R>>;

#[cfg(test)]
#[path = "native_accounting_review_tests.rs"]
mod accounting_review_tests;

// `remaining` is already measured at `now`. Entry preflight is not subtracted
// twice, and this absolute cap is never restarted at callback/load boundaries.
pub(super) fn preparation_deadline(
    started: Instant,
    remaining: u64,
    now: Instant,
) -> Result<Instant> {
    super::super::native_startup::preparation_deadline(started, remaining, now)
}

fn elapsed(started: Instant) -> u64 {
    started.elapsed().as_millis().min(u64::MAX as u128) as u64
}

struct Work {
    turns: [Option<StoredTurn>; 2],
    ready: [Option<StoredTurn>; 2],
    ledgers: [Ledger; 2],
    requires_provider: [bool; 2],
}
impl Work {
    fn completed(&self) -> bool {
        self.turns.iter().all(Option::is_some)
    }
    fn needs_native(&self) -> bool {
        self.requires_provider.into_iter().any(|needed| needed)
    }
    fn remaining(&self) -> u64 {
        self.ledgers
            .iter()
            .map(Ledger::remaining)
            .min()
            .unwrap_or(0)
    }
    fn preflight(&self) -> Result<()> {
        for arm in 0..2 {
            self.ledgers[arm].preflight_invocation(self.requires_provider[arm])?;
        }
        Ok(())
    }
}

// Read-only both-arm classification precedes reservation callbacks and all
// target mutation. Complete/committed/dependency work never constructs a factory.
fn inspect_work(plan: &PreparedSelectedPlan, dir: &Path, started: Instant) -> Result<Work> {
    let manifest = &plan.manifest;
    let turns = if dir.exists() {
        validate_destination(dir, manifest, Some(&plan.before))?
    } else {
        [None, None]
    };
    let mut ledgers = ledgers(dir, &manifest.binding)?;
    for ledger in &mut ledgers {
        ledger.started = started;
    }
    let mut work = Work {
        turns,
        ready: [None, None],
        ledgers,
        requires_provider: [false, false],
    };
    let corpus = suite()?;
    let index = manifest.selection.index;
    let step = &corpus.steps()[index];
    for arm in 0..2 {
        if work.turns[arm].is_some() {
            continue;
        }
        let path = database(&dir.join(ARM_NAMES[arm]), index, manifest.source_kind);
        if path.exists()
            && !Store::open_read_only(&path)
                .map_err(|_| "Workspace")?
                .stories()
                .map_err(|_| "Workspace")?
                .is_empty()
        {
            let full = engine(&path, &corpus.seed().scope)?;
            work.ready[arm] = recover_committed_turn(RecoveryJob {
                path: &path,
                full: &full,
                index,
                arm: ARM_NAMES[arm],
                policy: POLICIES[arm],
                binding: &manifest.binding,
                step,
                profile: &manifest.profile,
            })?;
        }
        if work.ready[arm].is_none() {
            work.ready[arm] = dependency_turn(DependencyJob {
                full: &plan.before[arm],
                index,
                arm: ARM_NAMES[arm],
                policy: POLICIES[arm],
                binding: &manifest.binding,
                step,
                profile: &manifest.profile,
            })?;
        }
        work.requires_provider[arm] = work.ready[arm].is_none();
    }
    Ok(work)
}

// Actual turn implementation stays in comparison::execute_turn. This driver
// only owns ordering and retains the live ledgers until worker cleanup finishes.
fn execute_work(
    plan: &PreparedSelectedPlan,
    destination: &Destination,
    work: &mut Work,
    factory: Option<&LaneFactory>,
    cancel: &Cancellation,
) -> Result<()> {
    let manifest = &destination.manifest;
    let index = manifest.selection.index;
    let corpus = suite()?;
    let step = &corpus.steps()[index];
    let first = match manifest.source_kind {
        ComparisonKind::PairedSnapshots => index % 2,
        ComparisonKind::ContinuousRollout => (index / 6) % 2,
    };
    for arm in [first, 1 - first] {
        if work.turns[arm].is_some() {
            continue;
        }
        let began = Instant::now();
        let dir = destination.dir.join(ARM_NAMES[arm]);
        let path = database(&dir, index, manifest.source_kind);
        let recovered = work.ready[arm]
            .as_ref()
            .is_some_and(|turn| turn.row.recovered_without_checkpoint);
        // An already proven commit wins over late cancellation. Dependency
        // checkpoints are pure rows, but still need their actual before Store.
        if !recovered {
            cancelled(cancel)?;
            ensure_database(&path, corpus.seed(), plan.before[arm].receipts())?;
            validate_pair_source(&path, corpus.seed(), plan.before[arm].receipts(), step)?;
            cancelled(cancel)?;
        }
        let turn = match work.ready[arm].take() {
            Some(turn) => turn,
            None => execute_turn(
                TurnJob {
                    dir: &dir,
                    path: &path,
                    index,
                    arm: ARM_NAMES[arm],
                    policy: POLICIES[arm],
                    binding: &manifest.binding,
                    step,
                    factory: factory.ok_or("Provider")?,
                    cancel,
                },
                &mut work.ledgers[arm],
            )?,
        };
        if !checkpoint_path(&dir, index).exists() {
            saved(&checkpoint_path(&dir, index), &turn, 256 * 1024)?;
        }
        work.turns[arm] = Some(turn);
        #[cfg(test)]
        if CANCEL_AFTER_ARM.with(std::cell::Cell::get) {
            cancel.cancel();
        }
        work.ledgers[1 - arm].exclude_measured_interval(elapsed(began))?;
    }
    // Replay/phase/capture checks are included in the invocation's real cost.
    work.turns = validate_destination(&destination.dir, manifest, Some(&plan.before))?;
    Ok(())
}

fn finish_workflow(
    plan: &PreparedSelectedPlan,
    destination: &Destination,
    work: &mut Work,
) -> Result<SelectedComparisonReportV1> {
    work.turns = validate_destination(&destination.dir, &destination.manifest, Some(&plan.before))?;
    report(
        &destination.dir,
        &destination.manifest,
        &work.turns,
        &work.ledgers,
    )?;
    for arm in 0..2 {
        let began = Instant::now();
        work.ledgers[arm].finish()?;
        work.ledgers[1 - arm].exclude_measured_interval(elapsed(began))?;
    }
    let result = report(
        &destination.dir,
        &destination.manifest,
        &work.turns,
        &work.ledgers,
    )?;
    publish_selected(&destination.dir, &result)?;
    Ok(result)
}

fn save_setup(
    destination: &Destination,
    work: &mut Work,
    physical_ms: u64,
    status: &str,
    load: Option<Value>,
) -> Result<()> {
    save_setup_at(
        &destination.dir,
        &destination.manifest.binding,
        &mut work.ledgers,
        physical_ms,
        status,
        load,
    )
}

struct Workflow {
    plan: PreparedSelectedPlan,
    destination: Destination,
    work: Work,
}
impl super::super::native_selected_workflow::Workflow for Workflow {
    type Report = SelectedComparisonReportV1;
    fn profile(&self) -> &PlayProfile {
        &self.plan.manifest.profile
    }
    fn started(&self) -> Instant {
        self.work.ledgers[0].started
    }
    fn remaining(&self) -> u64 {
        self.work.remaining()
    }
    fn preflight(&self) -> Result<()> {
        self.work.preflight()
    }
    fn ledgers(&mut self) -> &mut [Ledger; 2] {
        &mut self.work.ledgers
    }
    fn save_setup(&mut self, ms: u64, status: &str, load: Option<Value>) -> Result<()> {
        save_setup(&self.destination, &mut self.work, ms, status, load)
    }
    fn execute(&mut self, factory: Option<&LaneFactory>, cancel: &Cancellation) -> Result<()> {
        execute_work(
            &self.plan,
            &self.destination,
            &mut self.work,
            factory,
            cancel,
        )
    }
    fn finish(mut self) -> Result<Self::Report> {
        finish_workflow(&self.plan, &self.destination, &mut self.work)
    }
}
fn run_prepared<R: SelectedNativeReservation>(
    plan: PreparedSelectedPlan,
    destination: Destination,
    work: Work,
    reservation: Option<R>,
    cancel: &Cancellation,
    deadline: Instant,
) -> NativeResult<SelectedComparisonReportV1, R> {
    super::super::native_selected_workflow::run(
        Workflow {
            plan,
            destination,
            work,
        },
        reservation,
        cancel,
        deadline,
    )
}

pub fn run_native_selected<R: SelectedNativeReservation>(
    plan: PreparedSelectedPlan,
    new_dir: &Path,
    cancel: &Cancellation,
    reserve: impl FnOnce() -> Result<R>,
) -> NativeResult<SelectedComparisonReportV1, R> {
    let started = Instant::now();
    let failure = SelectedNativeFailure::from_error;
    if !plan.manifest.native().map_err(failure)? {
        return Err(failure("SelectedLaneMismatch".into()));
    }
    plan.refresh(cancel).map_err(failure)?;
    let (target, _pins) = destination_target(&plan, new_dir).map_err(failure)?;
    let work = inspect_work(&plan, &target, started).map_err(failure)?;
    work.preflight().map_err(failure)?;
    let mut deadline =
        preparation_deadline(started, work.remaining(), Instant::now()).map_err(failure)?;
    let reservation = if work.needs_native() {
        Some(reserve().map_err(failure)?)
    } else {
        None
    };
    deadline = deadline
        .min(preparation_deadline(started, work.remaining(), Instant::now()).map_err(failure)?);
    cancelled(cancel).map_err(failure)?;
    work.preflight().map_err(failure)?;
    let destination = new_destination(&plan, &target).map_err(failure)?;
    run_prepared(plan, destination, work, reservation, cancel, deadline)
}

pub fn resume_native_selected<R: SelectedNativeReservation>(
    dir: &Path,
    source_dir: &Path,
    expected_binding: &str,
    cancel: &Cancellation,
    reserve: impl FnOnce() -> Result<R>,
) -> NativeResult<SelectedComparisonReportV1, R> {
    let started = Instant::now();
    let failure = SelectedNativeFailure::from_error;
    cancelled(cancel).map_err(failure)?;
    if !hex(expected_binding) {
        return Err(failure("SelectedIdentity".into()));
    }
    let destination = open_destination(dir).map_err(failure)?;
    let manifest = &destination.manifest;
    if !manifest.native().map_err(failure)? {
        return Err(failure("SelectedLaneMismatch".into()));
    }
    if manifest.binding != expected_binding {
        return Err(failure("CheckpointMismatch".into()));
    }
    let row = desktop_api::RowId {
        turn: manifest.selection.turn.clone(),
        arm: if manifest.selection.clicked_arm == "left" {
            desktop_api::Arm::Left
        } else {
            desktop_api::Arm::Right
        },
    };
    let plan = prepare_selected(
        source_dir,
        &manifest.source_binding,
        &row,
        SelectedIntent {
            client_id: manifest.client_id.clone(),
            lane: SelectedLane::ApprovedNative,
        },
        cancel,
    )
    .map_err(failure)?;
    disjoint(&plan.source_dir, &destination.dir).map_err(failure)?;
    if plan.manifest != *manifest {
        return Err(failure("CheckpointMismatch".into()));
    }
    plan.refresh(cancel).map_err(failure)?;
    let work = inspect_work(&plan, &destination.dir, started).map_err(failure)?;
    if work.completed() {
        return report(&destination.dir, manifest, &work.turns, &work.ledgers).map_err(failure);
    }
    work.preflight().map_err(failure)?;
    let mut deadline =
        preparation_deadline(started, work.remaining(), Instant::now()).map_err(failure)?;
    let reservation = if work.needs_native() {
        Some(reserve().map_err(failure)?)
    } else {
        None
    };
    deadline = deadline
        .min(preparation_deadline(started, work.remaining(), Instant::now()).map_err(failure)?);
    cancelled(cancel).map_err(failure)?;
    work.preflight().map_err(failure)?;
    run_prepared(plan, destination, work, reservation, cancel, deadline)
}
