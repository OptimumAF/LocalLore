//! One owned startup path shared by native comparison drivers. No settlement,
//! report publication or alternate runtime implementation lives here.
use super::selected::SelectedNativeReservation;
use super::*;
use locallore_local_runtime::{adapter::SharedRuntime, LocalRuntime, OwnedStartFailure};

// Entry origin is never reset by lease acquisition, hashing or loading.
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

pub(super) fn check_preparation(cancel: &Cancellation, deadline: Instant) -> Result<()> {
    if cancel.is_cancelled() {
        return Err("Interrupted".into());
    }
    if Instant::now() >= deadline {
        Err("PreparationDeadline".into())
    } else {
        Ok(())
    }
}

pub(super) struct Startup {
    pub(super) runtime: Option<SharedRuntime>,
    pub(super) load: Option<Value>,
    pub(super) error: Option<String>,
}
pub(super) fn start_runtime<R: SelectedNativeReservation>(
    reservation: &R,
    profile: &PlayProfile,
    cancel: &Cancellation,
    deadline: Instant,
) -> Startup {
    if let Err(error) = check_preparation(cancel, deadline) {
        return Startup {
            runtime: None,
            load: None,
            error: Some(error),
        };
    }
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

#[cfg(test)]
mod pre_asset_tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};
    struct Lease(AtomicUsize);
    impl SelectedNativeReservation for Lease {
        fn assets(&self) -> NativeAssets<'_> {
            self.0.fetch_add(1, Ordering::SeqCst);
            NativeAssets {
                resource_dir: Path::new("MISSING-STARTUP-RESOURCE"),
                model: Path::new("MISSING-STARTUP-MODEL"),
            }
        }
        fn retain_uncertain(
            &mut self,
            owner: SharedRuntime,
        ) -> std::result::Result<(), SharedRuntime> {
            Err(owner)
        }
    }
    #[test]
    fn cancelled_shared_startup_never_inspects_assets() {
        let lease = Lease(AtomicUsize::new(0));
        let cancel = Cancellation::default();
        cancel.cancel();
        let value = start_runtime(
            &lease,
            &native_profile().unwrap(),
            &cancel,
            Instant::now() + Duration::from_secs(120),
        );
        assert!(value.runtime.is_none());
        assert_eq!(lease.0.load(Ordering::SeqCst), 0);
        assert_eq!(value.error.as_deref(), Some("Interrupted"));
    }
    #[test]
    fn expired_shared_startup_never_inspects_assets() {
        let lease = Lease(AtomicUsize::new(0));
        let cancel = Cancellation::default();
        let value = start_runtime(
            &lease,
            &native_profile().unwrap(),
            &cancel,
            Instant::now() - Duration::from_millis(1),
        );
        assert!(value.runtime.is_none());
        assert_eq!(lease.0.load(Ordering::SeqCst), 0);
        assert_eq!(value.error.as_deref(), Some("PreparationDeadline"));
    }
}
