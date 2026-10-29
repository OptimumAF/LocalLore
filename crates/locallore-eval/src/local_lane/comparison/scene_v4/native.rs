//! Native protocol4 workflow using the established retained runtime owner.
//! No assets/worker are opened before both invocations are durable. Cleanup is
//! confirmed before accounting/publication; uncertain ownership is returned.
use super::super::native_startup::{self, Startup};
use super::super::selected::{native_owner, SelectedNativeFailure, SelectedNativeReservation};
use super::*;

type NativeResult<T, R> = std::result::Result<T, SelectedNativeFailure<R>>;

fn elapsed(started: Instant) -> u64 {
    started.elapsed().as_millis().min(u64::MAX as u128) as u64
}
fn remaining(session: &Session4) -> u64 {
    session
        .ledgers
        .iter()
        .map(Ledger::remaining)
        .min()
        .unwrap_or(0)
}
fn preflight(session: &Session4) -> Result<()> {
    for ledger in &session.ledgers {
        ledger.preflight_invocation(true)?;
    }
    Ok(())
}
fn save_setup(
    session: &mut Session4,
    physical_ms: u64,
    status: &str,
    load: Option<Value>,
) -> Result<()> {
    if !matches!(status, "loaded" | "failed") || (status == "loaded" && load.is_none()) {
        return Err("SetupIntegrity".into());
    }
    if status == "loaded" && physical_ms > PREPARATION_MS {
        return Err("PreparationDeadline".into());
    }
    turn_execution::record_setup(
        &mut session.ledgers,
        turn_execution::Setup {
            version: 4,
            dir: &session.dir,
            key: &session.key,
            native: true,
            physical_ms,
            status,
            load,
        },
    )
}

pub(super) fn finish_prepared<R: SelectedNativeReservation>(
    mut session: Session4,
    reservation: R,
    startup: Startup,
    cancel: &Cancellation,
    preparation_began: Instant,
    deadline: Instant,
    max_new_scenes: usize,
) -> NativeResult<ComparisonReportV4, R> {
    let failure = SelectedNativeFailure::from_error;
    let mut initial_error = startup.error;
    let mut setup_saved = false;
    let body = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        if initial_error.is_none() {
            initial_error = native_startup::check_preparation(cancel, deadline).err();
        }
        if initial_error.is_none() {
            match save_setup(
                &mut session,
                elapsed(preparation_began),
                "loaded",
                startup.load.clone(),
            ) {
                Ok(()) => setup_saved = true,
                Err(error) => initial_error = Some(error),
            }
        }
        if initial_error.is_none() {
            if let Some(runtime) = startup.runtime.as_ref() {
                let factory = LaneFactory::Native {
                    runtime: runtime.clone(),
                    profile: session.manifest.profile.clone(),
                };
                initial_error = factory
                    .profile()
                    .and_then(|_| native_startup::check_preparation(cancel, deadline))
                    .and_then(|_| session.execute_body(cancel, max_new_scenes, &factory))
                    .err();
                drop(factory); // All synchronous Host/provider/watchdog guards drained.
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
        // Return the established actual ownership pair/retained slot. Do not
        // settle, publish success, replace the owner or refund unknown work.
        return terminal.and_then(|_| Err(failure("Cleanup".into())));
    }
    if !setup_saved {
        save_setup(
            &mut session,
            elapsed(preparation_began),
            "failed",
            startup.load,
        )
        .map_err(failure)?;
    }
    // Actual cleanup time remains inside both original live invocation clocks.
    let published = session.finish().map_err(failure);
    match terminal {
        Ok(()) => published,
        Err(error) => {
            published?;
            Err(error)
        }
    }
}

/// Trusted native lease only. Wire metadata, a preowned provider or arbitrary
/// command cannot select runtime ownership. Completed current-source resume
/// returns before reserve/assets; continuing runs retain the existing owner.
pub fn run_native_comparison<R: SelectedNativeReservation>(
    dir: &Path,
    resume: bool,
    kind: ComparisonKind,
    cancel: &Cancellation,
    max_new_scenes: usize,
    reserve: impl FnOnce() -> Result<R>,
    reference: Option<&ValidatedReference>,
) -> NativeResult<ComparisonReportV4, R> {
    run_native_comparison_inner(dir,resume,kind,cancel,max_new_scenes,reserve,(reference,false))
}
pub fn run_native_comparison_with_narration_diagnostics_v1<R:SelectedNativeReservation>(
    dir:&Path,resume:bool,kind:ComparisonKind,cancel:&Cancellation,max_new_scenes:usize,
    reserve:impl FnOnce()->Result<R>,reference:Option<&ValidatedReference>,
)->NativeResult<ComparisonReportV4,R>{
    run_native_comparison_inner(dir,resume,kind,cancel,max_new_scenes,reserve,(reference,true))
}
fn run_native_comparison_inner<R:SelectedNativeReservation>(
    dir:&Path,resume:bool,kind:ComparisonKind,cancel:&Cancellation,max_new_scenes:usize,
    reserve:impl FnOnce()->Result<R>,options:(Option<&ValidatedReference>,bool),
)->NativeResult<ComparisonReportV4,R>{
    let (reference,diagnostics)=options;
    let started = Instant::now();
    let failure = SelectedNativeFailure::from_error;
    if cancel.is_cancelled() {
        return Err(failure("Interrupted".into()));
    }
    if !(1..=4).contains(&max_new_scenes) {
        return Err(failure("SceneBudget".into()));
    }
    let expected = Manifest::new_with_lane(
        kind,
        native_profile().map_err(failure)?,
        true,
        reference_digest(dir, resume, kind, reference).map_err(failure)?,
    )
    .map_err(failure)?;
    if resume {
        let actual: Manifest = decode(&dir.join("run.json"), 128 * 1024).map_err(failure)?;
        if actual != expected || !actual.source_matches().map_err(failure)? {
            return Err(failure("CheckpointMismatch".into()));
        }
        if diagnostics {desktop_api::validate_companion_for_resume(dir).map_err(failure)?;}
        let report = inspect_comparison(dir).map_err(failure)?;
        if report.completed {
            return Ok(report);
        }
    }
    let mut session = Session4::open(dir, resume, expected, reference, started).map_err(failure)?;
    if diagnostics {
        if !resume {crate::narration_diagnostic_companion_v1::declare(dir,&session.key,&session.manifest.source_sha256).map_err(failure)?;}
        session.diagnostics=true;
    }
    preflight(&session).map_err(failure)?;
    let deadline =
        native_startup::preparation_deadline(started, remaining(&session), Instant::now())
            .map_err(failure)?;
    native_startup::check_preparation(cancel, deadline).map_err(failure)?;
    let reservation = reserve().map_err(failure)?;
    native_startup::check_preparation(cancel, deadline).map_err(failure)?;
    preflight(&session).map_err(failure)?;
    session.begin_invocations().map_err(failure)?;
    let deadline = deadline.min(
        native_startup::preparation_deadline(started, remaining(&session), Instant::now())
            .map_err(failure)?,
    );
    native_startup::check_preparation(cancel, deadline).map_err(failure)?;
    let began = Instant::now();
    let startup =
        native_startup::start_runtime(&reservation, &session.manifest.profile, cancel, deadline);
    finish_prepared(
        session,
        reservation,
        startup,
        cancel,
        began,
        deadline,
        max_new_scenes,
    )
}
