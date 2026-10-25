// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Native selected workflow over the same turn, Store and resource authorities.
use super::{native_owner, *};
use locallore_local_runtime::{LocalRuntime, OwnedStartFailure};
use native_owner::{SelectedNativeFailure, SelectedNativeReservation, SharedRuntime};

type NativeResult<T, R> = std::result::Result<T, SelectedNativeFailure<R>>;

// `remaining` is already measured at `now`. Entry preflight is not subtracted
// twice, and this absolute cap is never restarted at callback/load boundaries.
pub(super) fn preparation_deadline(
    started: Instant,
    remaining: u64,
    now: Instant,
) -> Result<Instant> {
    let deadline = (started + Duration::from_millis(PREPARATION_MS))
        .min(now + Duration::from_millis(remaining.saturating_sub(CLEANUP_RESERVE_MS)));
    if now >= deadline {
        Err("PreparationDeadline".into())
    } else {
        Ok(deadline)
    }
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
    // Only this native-private workflow reaches here: either actual load is
    // observed, or startup has ended with confirmed cleanup/BeforeChild.
    // Unknown cleanup never calls it as a failed/settled terminal measurement.
    let record = SetupRecord {
        version: 2,
        binding: destination.manifest.binding.clone(),
        left_invocation: work.ledgers[0].invocation,
        right_invocation: work.ledgers[1].invocation,
        native: true,
        physical_ms,
        status: status.into(),
        load,
    };
    saved(
        &destination
            .dir
            .join(format!("setup-{:02}.json", record.left_invocation)),
        &record,
        64 * 1024,
    )?;
    let (left, right) = shared_setup_shares(physical_ms);
    for (ledger, share) in work.ledgers.iter_mut().zip([left, right]) {
        if physical_ms <= PREPARATION_MS {
            ledger.record_shared_setup(physical_ms, share)?;
        } else {
            // A known terminal OS overrun is charged in full, never clamped to
            // the cooperative deadline. Legacy full-run validation is unchanged.
            if ledger.shared_setup.is_some() || share > physical_ms {
                return Err("ClockIntegrity".into());
            }
            ledger.shared_setup = Some((physical_ms, share));
        }
    }
    Ok(())
}

fn check_preparation(cancel: &Cancellation, deadline: Instant) -> Result<()> {
    cancelled(cancel)?;
    if Instant::now() >= deadline {
        Err("PreparationDeadline".into())
    } else {
        Ok(())
    }
}

struct Startup {
    runtime: Option<SharedRuntime>,
    load: Option<Value>,
    error: Option<String>,
}
fn start_runtime<R: SelectedNativeReservation>(
    reservation: &R,
    profile: &PlayProfile,
    cancel: &Cancellation,
    deadline: Instant,
) -> Startup {
    let assets = reservation.assets();
    let stopped = || cancel.is_cancelled() || Instant::now() >= deadline;
    let runtime = match LocalRuntime::spawn_packaged_owned_expected_cancelled(
        assets.resource_dir,
        assets.model,
        &profile.worker_sha256,
        stopped,
    ) {
        Ok(runtime) => runtime,
        Err(OwnedStartFailure::BeforeChild(cause)) => {
            return Startup {
                runtime: None,
                load: None,
                error: Some(format!("Runtime{cause:?}")),
            };
        }
        Err(OwnedStartFailure::AfterChild { cause, owner }) => {
            return Startup {
                runtime: Some(Arc::new(Mutex::new(*owner))),
                load: None,
                error: Some(format!("Runtime{cause:?}")),
            };
        }
    };
    let runtime = Arc::new(Mutex::new(runtime));
    let mut load = None;
    let result = (|| {
        check_preparation(cancel, deadline)?;
        let mut owner = runtime.try_lock().map_err(|_| "RuntimeBusy")?;
        if owner.profile_manifest_sha256() != profile.profile_manifest_sha256 {
            return Err("Profile".into());
        }
        let observed = owner
            .load(stopped)
            .map_err(|cause| format!("Runtime{cause:?}"))?;
        load = Some(serde_json::to_value(observed).map_err(|_| "Encoding")?);
        check_preparation(cancel, deadline)?;
        Ok::<(), String>(())
    })();
    Startup {
        runtime: Some(runtime),
        load,
        error: result.err(),
    }
}

fn run_prepared<R: SelectedNativeReservation>(
    plan: PreparedSelectedPlan,
    destination: Destination,
    mut work: Work,
    reservation: Option<R>,
    cancel: &Cancellation,
    deadline: Instant,
) -> NativeResult<SelectedComparisonReportV1, R> {
    let failure = SelectedNativeFailure::from_error;
    // Both preparations precede assets, hashing, worker creation and load.
    work.ledgers[0].begin_invocation().map_err(failure)?;
    work.ledgers[1].begin_invocation().map_err(failure)?;
    let Some(reservation) = reservation else {
        execute_work(&plan, &destination, &mut work, None, cancel).map_err(failure)?;
        return finish_workflow(&plan, &destination, &mut work).map_err(failure);
    };
    let mut deadline = deadline;
    deadline = deadline.min(
        preparation_deadline(work.ledgers[0].started, work.remaining(), Instant::now())
            .map_err(failure)?,
    );
    check_preparation(cancel, deadline).map_err(failure)?;
    let began = Instant::now();
    let startup = start_runtime(&reservation, &plan.manifest.profile, cancel, deadline);
    let mut initial_error = startup.error;
    let mut setup_saved = false;
    if initial_error.is_none() {
        initial_error = check_preparation(cancel, deadline).err();
    }
    if initial_error.is_none() {
        if let Err(error) = save_setup(
            &destination,
            &mut work,
            elapsed(began),
            "loaded",
            startup.load.clone(),
        ) {
            initial_error = Some(error);
        } else {
            setup_saved = true;
        }
    }
    if initial_error.is_none() {
        if let Some(runtime) = startup.runtime.as_ref() {
            let factory = LaneFactory::Native {
                runtime: runtime.clone(),
                profile: plan.manifest.profile.clone(),
            };
            // Check the same approved identities as every production native factory.
            initial_error = factory
                .profile()
                .and_then(|_| check_preparation(cancel, deadline))
                .and_then(|_| execute_work(&plan, &destination, &mut work, Some(&factory), cancel))
                .err();
            drop(factory); // All synchronous execute_turn Host/provider guards drained.
        } else {
            initial_error = Some("Provider".into());
        }
    }
    let terminal = match startup.runtime {
        Some(runtime) => native_owner::finish_owner(reservation, runtime, initial_error),
        None => {
            drop(reservation); // BeforeChild positively has no process owner.
            Err(failure(initial_error.unwrap_or_else(|| "Provider".into())))
        }
    };
    if terminal
        .as_ref()
        .is_err_and(|failure| failure.cleanup_uncertain())
    {
        // Keep both preparation reserves outstanding; admission settlements and
        // committed rows remain actual. The failure retains any rejected handoff.
        return terminal.and_then(|_| Err(failure("Cleanup".into())));
    }
    // Confirmed cleanup cost is still inside both live invocation clocks.
    // A late failed setup may exceed 120s: retain the actual physical duration.
    if !setup_saved {
        save_setup(
            &destination,
            &mut work,
            elapsed(began),
            "failed",
            startup.load,
        )
        .map_err(failure)?;
    }
    let published = finish_workflow(&plan, &destination, &mut work).map_err(failure);
    match terminal {
        Ok(()) => published,
        Err(error) => {
            published?;
            Err(error)
        }
    }
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
