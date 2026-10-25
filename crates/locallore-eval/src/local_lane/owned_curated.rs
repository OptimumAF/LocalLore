// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Additive native curated ownership. Existing Session/Host/Store own all work;
//! the caller retains this typed failure until cleanup or same-manager handoff.
use super::*;
use comparison::selected::native_owner::finish_owner;
use locallore_local_runtime::{LocalRuntime, OwnedStartFailure};
use std::panic::{catch_unwind, AssertUnwindSafe};

#[cfg(test)]
mod review_tests;

fn preparation_deadline(started: Instant, remaining: u64, now: Instant) -> Result<Instant> {
    let deadline = (started + Duration::from_millis(PREPARATION_MS))
        .min(now + Duration::from_millis(remaining.saturating_sub(CLEANUP_RESERVE_MS)));
    if now >= deadline {
        Err("PreparationDeadline".into())
    } else {
        Ok(deadline)
    }
}

fn check_preparation(cancel: &Cancellation, deadline: Instant) -> Result<()> {
    if cancel.is_cancelled() {
        Err("Interrupted".into())
    } else if Instant::now() >= deadline {
        Err("PreparationDeadline".into())
    } else {
        Ok(())
    }
}

fn known_failure<R>(mut session: Session, failure: NativeFailure<R>)
    -> std::result::Result<Report, NativeFailure<R>>
{
    // Exactly one attempt after positive no-child/cleanup confirmation. The
    // original closed failure remains primary if settlement IO also fails.
    // This API cannot carry a second diagnostic: a missing/partial settlement
    // stays unknown or may make inspection unusable; it is never called success.
    let _secondary_settlement = session.ledger.finish();
    Err(failure)
}

/// Owned native path; R is already reserved by the native caller. No new Store,
/// backend, wire authority or implicit retry. Legacy entrypoints stay unchanged.
pub fn run_native_curated_owned<R: NativeReservation>(
    directory: &Path,
    resume: bool,
    selected: Option<&str>,
    cancel: &Cancellation,
    max_new_stories: usize,
    reservation: R,
) -> std::result::Result<Report, NativeFailure<R>> {
    let entry_started = Instant::now();
    let failure = NativeFailure::<R>::from_error;
    if !(1..=6).contains(&max_new_stories) {
        return Err(failure("CaseBudget".into()));
    }
    if cancel.is_cancelled() {
        return Err(failure("Interrupted".into()));
    }
    let profile = native_profile().map_err(failure)?;
    profile.validate().map_err(|_| failure("Profile".into()))?;
    let mut session = Session::open(directory, resume, selected, true, profile.clone(), false)
        .map_err(failure)?;
    // Opening, replay/restore validation and all later cleanup are this same
    // invocation's real overhead; preparation does not get a fresh entry clock.
    session.ledger.started = entry_started;
    match session.all_saved() {
        Ok(true) => {
            // No assets/child; preserve existing curated cached-restore semantics,
            // including its actual invocation/finalize writes (not selected RO).
            return session.restore_completed().map_err(failure);
        }
        Ok(false) => {}
        Err(error) => return known_failure(session, failure(error)),
    }
    let deadline = match preparation_deadline(entry_started, session.ledger.remaining(), Instant::now()) {
        Ok(deadline) => deadline,
        Err(error) => return known_failure(session, failure(error)),
    };
    if let Err(error) = check_preparation(cancel, deadline) {
        return known_failure(session, failure(error));
    }
    let stopped = || cancel.is_cancelled() || Instant::now() >= deadline;
    let started = {
        let assets = reservation.assets();
        LocalRuntime::spawn_packaged_owned_expected_cancelled(
            assets.resource_dir, assets.model, &profile.worker_sha256, stopped,
        )
    };
    let (runtime, mut cause) = match started {
        Ok(runtime) => (Arc::new(Mutex::new(runtime)), None),
        Err(OwnedStartFailure::BeforeChild(error)) => {
            drop(reservation); // Positively no process owner was created.
            return known_failure(session, failure(format!("Runtime{error:?}")));
        }
        Err(OwnedStartFailure::AfterChild { cause, owner }) => {
            (Arc::new(Mutex::new(*owner)), Some(format!("Runtime{cause:?}")))
        }
    };
    if cause.is_none() {
        // Keep the actual Arc/R outside this unwind boundary. A failed load or
        // subsequent case error cannot implicitly drop its cleanup owner.
        let preparation = catch_unwind(AssertUnwindSafe(|| -> Result<()> {
            check_preparation(cancel, deadline)?;
            let mut owner = runtime.try_lock().map_err(|_| "RuntimeBusy")?;
            if owner.profile_manifest_sha256() != profile.profile_manifest_sha256 {
                return Err("Profile".into());
            }
            let load = owner.load(stopped).map_err(|error| format!("Runtime{error:?}"))?;
            session.report.provenance["native_load"] = serde_json::to_value(load).map_err(|_| "Encoding")?;
            check_preparation(cancel, deadline)
        }));
        cause = preparation.unwrap_or_else(|_| Err("SelectedExecution".into())).err();
    }
    if cause.is_none() {
        let factory = LaneFactory::Native { runtime: runtime.clone(), profile };
        let execution = catch_unwind(AssertUnwindSafe(|| {
            factory.profile()
                .and_then(|_| check_preparation(cancel, deadline))
                .and_then(|_| session.execute_body(&factory, cancel, max_new_stories))
        }));
        cause = execution.unwrap_or_else(|_| Err("SelectedExecution".into())).err();
        // Actual story Host/provider/watchdog scopes have returned/unwound.
        // Drop the last factory reference before the explicit owner cleanup.
        drop(factory);
    }
    let terminal = finish_owner(reservation, runtime, cause);
    match terminal {
        Ok(()) => session.finalize().map_err(failure), // The sole successful finish/publication.
        Err(error) if error.cleanup_uncertain() => {
            // Preserve real case/turn checkpoints and admission settlements,
            // but never settle this unknown preparation or publish completion.
            Err(error)
        }
        Err(error) => known_failure(session, error),
    }
}
