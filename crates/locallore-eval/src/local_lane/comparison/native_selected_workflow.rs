//! One private native selected workflow over the existing actual runtime owner.
//! Versioned plans, histories, checkpoints and reports stay with their codecs.
use super::native_startup::{self, check_preparation, start_runtime};
use super::selected::{native_owner, SelectedNativeFailure, SelectedNativeReservation};
use super::*;
#[cfg(all(test, feature = "protocol-owner-tests"))]
mod review_tests;

pub(super) trait Workflow {
    type Report;
    fn profile(&self) -> &PlayProfile;
    fn started(&self) -> Instant;
    fn remaining(&self) -> u64;
    fn preflight(&self) -> Result<()>;
    fn ledgers(&mut self) -> &mut [Ledger; 2];
    fn save_setup(&mut self, ms: u64, status: &str, load: Option<Value>) -> Result<()>;
    fn execute(&mut self, factory: Option<&LaneFactory>, cancel: &Cancellation) -> Result<()>;
    fn finish(self) -> Result<Self::Report>;
}
fn elapsed(started: Instant) -> u64 {
    started.elapsed().as_millis().min(u64::MAX as u128) as u64
}
pub(super) fn save_setup_at(
    dir: &Path,
    binding: &str,
    ledgers: &mut [Ledger; 2],
    physical_ms: u64,
    status: &str,
    load: Option<Value>,
) -> Result<()> {
    // Only this native-private workflow reaches here: either actual load is
    // observed, or startup has ended with confirmed cleanup/BeforeChild.
    // Unknown cleanup never calls it as a failed/settled terminal measurement.
    if !matches!(status, "loaded" | "failed") || (status == "loaded" && load.is_none()) {
        return Err("SetupIntegrity".into());
    }
    if status == "loaded" && physical_ms > PREPARATION_MS {
        return Err("PreparationDeadline".into());
    }
    if ledgers.iter().any(|ledger| ledger.shared_setup.is_some()) {
        return Err("ClockIntegrity".into());
    }
    let record = SetupRecord {
        version: 2,
        binding: binding.into(),
        left_invocation: ledgers[0].invocation,
        right_invocation: ledgers[1].invocation,
        native: true,
        physical_ms,
        status: status.into(),
        load,
    };
    saved(
        &dir.join(format!("setup-{:02}.json", record.left_invocation)),
        &record,
        64 * 1024,
    )?;
    let (left, right) = shared_setup_shares(physical_ms);
    for (ledger, share) in ledgers.iter_mut().zip([left, right]) {
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

pub(super) fn run<W: Workflow, R: SelectedNativeReservation>(
    mut workflow: W,
    reservation: Option<R>,
    cancel: &Cancellation,
    deadline: Instant,
) -> std::result::Result<W::Report, SelectedNativeFailure<R>> {
    let failure = SelectedNativeFailure::from_error;
    workflow.preflight().map_err(failure)?;
    workflow.ledgers()[0].begin_invocation().map_err(failure)?;
    workflow.ledgers()[1].begin_invocation().map_err(failure)?;
    let Some(reservation) = reservation else {
        workflow.execute(None, cancel).map_err(failure)?;
        return workflow.finish().map_err(failure);
    };
    let deadline = deadline.min(
        native_startup::preparation_deadline(
            workflow.started(),
            workflow.remaining(),
            Instant::now(),
        )
        .map_err(failure)?,
    );
    check_preparation(cancel, deadline).map_err(failure)?;
    let began = Instant::now();
    let startup = start_runtime(&reservation, workflow.profile(), cancel, deadline);
    finish_prepared(workflow, reservation, startup, cancel, began, deadline)
}

pub(super) fn finish_prepared<W: Workflow, R: SelectedNativeReservation>(
    mut workflow: W,
    reservation: R,
    startup: native_startup::Startup,
    cancel: &Cancellation,
    began: Instant,
    deadline: Instant,
) -> std::result::Result<W::Report, SelectedNativeFailure<R>> {
    let failure = SelectedNativeFailure::from_error;
    let mut initial_error = startup.error;
    let mut setup_saved = false;
    // The actual reservation/runtime remain outside this unwind boundary. A
    // synchronous Host/factory unwinds before the established cleanup owner runs.
    let body = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        if initial_error.is_none() {
            initial_error = check_preparation(cancel, deadline).err();
        }
        if initial_error.is_none() {
            match workflow.save_setup(elapsed(began), "loaded", startup.load.clone()) {
                Ok(()) => setup_saved = true,
                Err(error) => initial_error = Some(error),
            }
        }
        if initial_error.is_none() {
            if let Some(runtime) = startup.runtime.as_ref() {
                let factory = LaneFactory::Native {
                    runtime: runtime.clone(),
                    profile: workflow.profile().clone(),
                };
                initial_error = factory
                    .profile()
                    .and_then(|_| check_preparation(cancel, deadline))
                    .and_then(|_| workflow.execute(Some(&factory), cancel))
                    .err();
                drop(factory);
            } else {
                initial_error = Some("Provider".into());
            }
        }
    }));
    if body.is_err() {
        initial_error = Some("SelectedExecution".into());
    }
    let terminal = match startup.runtime {
        Some(runtime) => native_owner::finish_owner(reservation, runtime, initial_error),
        None => {
            drop(reservation);
            Err(failure(initial_error.unwrap_or_else(|| "Provider".into())))
        }
    };
    if terminal
        .as_ref()
        .is_err_and(|error| error.cleanup_uncertain())
    {
        // No finish/settlement/publication under uncertain cleanup. The failure
        // retains the actual rejected owner pair, or the reservation retains it.
        return terminal.and_then(|_| Err(failure("Cleanup".into())));
    }
    if !setup_saved {
        workflow
            .save_setup(elapsed(began), "failed", startup.load)
            .map_err(failure)?;
    }
    let published = workflow.finish().map_err(failure);
    match terminal {
        Ok(()) => published,
        Err(error) => {
            published?;
            Err(error)
        }
    }
}
