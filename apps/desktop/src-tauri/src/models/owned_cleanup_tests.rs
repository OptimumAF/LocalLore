//! Frozen phase1 ownership oracles against existing ModelManager APIs.
//! SOURCE ONLY / UNCOMPILED / UNRUN by this test author. No worker or model.
//! These metadata cases do not prove child termination or runtime cleanup.
use super::*;

fn metadata_manager() -> Arc<ModelManager> {
    // No directory, model, worker, or runtime is created. status() can only
    // inspect this newly named absent synthetic namespace.
    let root = std::env::temp_dir().join(format!(
        "locallore-model-pending-owner-{}",
        exports::identifier().expect("synthetic namespace")
    ));
    assert!(!root.exists());
    Arc::new(ModelManager::new(
        root.join("models"),
        root.join("resources"),
    ))
}

fn assert_metadata_owner(manager: &ModelManager, job: u64, phase: &str) {
    let status = manager.status().expect("native metadata status");
    assert_eq!(status["operation_id"], job);
    assert_eq!(status["phase"], phase);
    assert_eq!(status["resident"], false);
    assert_eq!(status["loaded"], false);
}

fn assert_replacement_busy(manager: &Arc<ModelManager>) {
    assert!(matches!(manager.begin("loading"), Err(error) if error == "Busy"));
    assert!(matches!(manager.reserve_evaluation(), Err(error) if error == "Busy"));
}

#[test]
fn retired_pending_startup_stays_unloading_until_original_cleanup_acknowledges() {
    let manager = metadata_manager();
    let (startup, cancel) = manager.begin("loading").expect("original loading job");
    assert_metadata_owner(&manager, startup, "loading");
    assert!(!cancel.load(Ordering::SeqCst));

    let retired = manager.retire().expect("retire original loading job");
    let retirement = retired.0;
    assert!(retirement > startup);
    assert!(retired.1.is_none(), "startup has not published a runtime");
    assert!(cancel.load(Ordering::SeqCst));
    assert_metadata_owner(&manager, retirement, "unloading");

    // The close worker has no runtime yet. That is not proof that the original
    // startup job has stopped or has acknowledged its prechild cleanup.
    manager.close(None, Some(retired));
    assert_metadata_owner(&manager, retirement, "unloading");
    assert_replacement_busy(&manager);

    // Only this matching original callback knows that its prechild cleanup is
    // complete. No actual child or cleanup-failure scenario is simulated here.
    manager.finish(startup, &Err("Cancelled".into()));
    let status = manager.status().expect("acknowledged metadata status");
    assert_eq!(status["phase"], "unloaded");
    assert_eq!(status["resident"], false);
    assert_eq!(status["loaded"], false);
    let reservation = manager
        .reserve_evaluation()
        .expect("matching cleanup permits evaluation reservation");
    assert_replacement_busy(&manager);
    drop(reservation);
    let (next, _) = manager.begin("loading").expect("replacement admission");
    assert!(next > retirement);
    manager.finish(next, &Err("Cancelled".into()));
}

#[test]
fn older_finish_and_close_cannot_release_newer_loading_or_retired_pending_owner() {
    let manager = metadata_manager();
    let (older, older_cancel) = manager.begin("loading").expect("older startup");
    let older_retired = manager.retire().expect("older retirement");
    assert!(older_retired.1.is_none());
    assert!(older_cancel.load(Ordering::SeqCst));
    manager.close(None, Some(older_retired.clone()));
    manager.finish(older, &Err("Cancelled".into()));
    assert_eq!(manager.status().unwrap()["phase"], "unloaded");

    let (current, current_cancel) = manager.begin("loading").expect("new startup");
    assert!(current > older_retired.0);
    assert_metadata_owner(&manager, current, "loading");
    assert!(!current_cancel.load(Ordering::SeqCst));

    // Duplicate callbacks carry only actual prior job/retirement identities;
    // they must not acknowledge the newer job or make replacement admissible.
    manager.finish(older, &Err("Cancelled".into()));
    manager.close(None, Some(older_retired));
    assert_metadata_owner(&manager, current, "loading");
    assert!(!current_cancel.load(Ordering::SeqCst));
    assert_replacement_busy(&manager);

    let current_retired = manager.retire().expect("current retirement");
    let retirement = current_retired.0;
    assert!(retirement > current);
    assert!(current_retired.1.is_none());
    manager.close(None, Some(current_retired));
    manager.finish(older, &Err("Cancelled".into()));
    assert_metadata_owner(&manager, retirement, "unloading");
    assert!(current_cancel.load(Ordering::SeqCst));
    assert_replacement_busy(&manager);

    manager.finish(current, &Err("Cancelled".into()));
    assert_eq!(manager.status().unwrap()["phase"], "unloaded");
    let reservation = manager
        .reserve_evaluation()
        .expect("only matching current cleanup releases exclusion");
    drop(reservation);
}

// Phase2 below is separately frozen, UNCOMPILED/UNRUN by this author. Root must
// supply the approved zero-argument fixed-protocol helper, dev dependency and
// private one-shot manager fault. These cases launch only that tiny fixture
// when Root executes them, never inference/model weights. Direct OS child and
// pipe-thread proofs belong to the runtime's private unit tests, not this file.
mod actual_owned_cleanup {
    use super::*;
    use locallore_local_runtime::{Generation, OwnedStartFailure, Role, Status};

    struct FaultReset;
    impl Drop for FaultReset {
        fn drop(&mut self) {
            FAIL_CLEANUP_ONCE.with(|fault| fault.set(false));
        }
    }

    struct FixedOwner {
        owner: Option<SharedRuntime>,
        directory: PathBuf,
    }
    impl FixedOwner {
        fn new() -> Self {
            let (owner, directory) = match LocalRuntime::development_protocol_fixture() {
                Ok(fixture) => fixture,
                Err(OwnedStartFailure::BeforeChild(cause)) => {
                    panic!("fixed protocol fixture failed before child: {cause:?}");
                }
                Err(OwnedStartFailure::AfterChild { cause, mut owner }) => {
                    let cleanup = owner.terminate_and_reap();
                    panic!("fixed protocol fixture failed: {cause:?}; cleanup {cleanup:?}");
                }
            };
            let fixture = Self {
                owner: Some(Arc::new(Mutex::new(owner))),
                directory,
            };
            fixture
                .arc()
                .lock()
                .unwrap()
                .load(|| false)
                .expect("fixed valid worker loads without weights");
            assert_responding(&fixture.arc());
            fixture
        }
        fn arc(&self) -> SharedRuntime {
            self.owner.as_ref().unwrap().clone()
        }
    }
    impl Drop for FixedOwner {
        fn drop(&mut self) {
            let owner = self.owner.take().unwrap();
            // Recovery of a poisoned runtime is cleanup-only, never inference.
            let confirmed = match owner.lock() {
                Ok(mut runtime) => runtime.terminate_and_reap().is_ok(),
                Err(poisoned) => poisoned.into_inner().terminate_and_reap().is_ok(),
            };
            drop(owner);
            // Helpers are declared before their managers/guards so those Arcs
            // drop first. Never delete fixture paths before terminal cleanup.
            if confirmed {
                let _ = fs::remove_dir_all(&self.directory);
            }
        }
    }

    fn assert_responding(owner: &SharedRuntime) {
        // Private fixed-worker liveness probe only; never re-enable a Host
        // supplier or infer that quarantined model execution is permitted.
        let mut runtime = owner.lock().expect("unpoisoned fixed fixture");
        assert_eq!(runtime.status(), Status::Loaded);
        let reply = runtime
            .generate(
                Generation {
                    role: Role::Director,
                    prompt: "fixed owner lifecycle probe".into(),
                    schema: None,
                    max_tokens: 1,
                },
                || false,
            )
            .expect("same tiny protocol worker is still responding");
        assert!(reply.text.is_empty());
    }

    fn retained_same_owner(manager: &ModelManager, owner: &SharedRuntime) {
        let inner = manager.inner.lock().unwrap();
        assert!(Arc::ptr_eq(inner.runtime.as_ref().unwrap(), owner));
        drop(inner);
        let status = manager.status().unwrap();
        assert_eq!(status["resident"], true);
        assert_eq!(status["loaded"], false);
        assert_eq!(status["phase"], "failed");
        assert_eq!(status["error"], "Cleanup");
    }

    fn replacement_refused(manager: &Arc<ModelManager>) {
        assert!(matches!(
            manager.reserve_evaluation(),
            Err(error) if error == "Busy" || error == "ModelLoaded"
        ));
        let lease = WindowLease::default();
        let epoch = lease.begin().unwrap();
        assert!(matches!(
            manager.load(&Host::new(true), &lease, epoch),
            Err(error) if error == "Busy" || error == "ModelLoaded"
        ));
    }

    fn handoff(manager: &Arc<ModelManager>, owner: &SharedRuntime) {
        let mut reservation = manager.reserve_evaluation().unwrap();
        assert!(reservation.retain_uncertain(owner.clone()).is_ok());
        drop(reservation);
    }

    fn unload(manager: &ModelManager) -> Result<Value, String> {
        let lease = WindowLease::default();
        let epoch = lease.begin().unwrap();
        manager.unload(&Host::new(true), &lease, epoch)
    }

    fn assert_released(manager: &Arc<ModelManager>, owner: &SharedRuntime) {
        let status = manager.status().unwrap();
        assert_eq!(status["resident"], false);
        assert_eq!(status["loaded"], false);
        assert_eq!(owner.lock().unwrap().status(), Status::Failed);
        assert_eq!(owner.lock().unwrap().terminate_and_reap(), Ok(()));
        let reservation = manager.reserve_evaluation().unwrap();
        drop(reservation);
    }

    #[test]
    fn handoff_before_drop_preserves_cleanup_latch_even_while_runtime_mutex_is_held() {
        let _reset = FaultReset;
        let fixture = FixedOwner::new();
        let manager = metadata_manager();
        let owner = fixture.arc();
        let mut reservation = manager.reserve_evaluation().unwrap();
        assert!(reservation.retain_uncertain(owner.clone()).is_ok());
        retained_same_owner(&manager, &owner);
        replacement_refused(&manager);
        {
            let _held = owner.lock().unwrap();
            retained_same_owner(&manager, &owner);
            replacement_refused(&manager);
        }
        drop(reservation);
        retained_same_owner(&manager, &owner);
        replacement_refused(&manager);

        // Metadata completion alone has not cleaned the actual fixture owner.
        let (job, _) = manager.begin("unloading").unwrap();
        manager.finish(job, &Ok(()));
        retained_same_owner(&manager, &owner);
        assert_responding(&owner);
        unload(&manager).unwrap();
        assert_released(&manager, &owner);
    }

    #[test]
    fn same_ticket_same_arc_is_idempotent_and_other_owner_is_returned_unchanged() {
        let _reset = FaultReset;
        let first = FixedOwner::new();
        let other = FixedOwner::new();
        let manager = metadata_manager();
        let owner = first.arc();
        let other_owner = other.arc();
        let mut reservation = manager.reserve_evaluation().unwrap();
        assert!(reservation.retain_uncertain(owner.clone()).is_ok());
        assert!(reservation.retain_uncertain(owner.clone()).is_ok());
        let returned = match reservation.retain_uncertain(other_owner.clone()) {
            Err(owner) => owner,
            Ok(()) => panic!("different live owner overwrote original slot"),
        };
        assert!(Arc::ptr_eq(&returned, &other_owner));
        retained_same_owner(&manager, &owner);
        assert_responding(&returned);
        drop(returned);
        drop(reservation);
        unload(&manager).unwrap();
        assert_released(&manager, &owner);
        assert_responding(&other_owner);
    }

    #[test]
    fn stale_ticket_returns_its_owner_and_old_drop_cannot_clear_new_actual_ticket() {
        let _reset = FaultReset;
        let stale_fixture = FixedOwner::new();
        let current_fixture = FixedOwner::new();
        let manager = metadata_manager();
        let stale_owner = stale_fixture.arc();
        let current_owner = current_fixture.arc();
        let mut old = manager.reserve_evaluation().unwrap();
        {
            // Deliberate metadata fault, not a claim of real concurrency. Keep
            // the old actual guard, invalidate only its existing ticket, then
            // obtain the replacement identity through the actual public API.
            let mut inner = manager.inner.lock().unwrap();
            assert_eq!(inner.evaluation, Some(old.ticket));
            inner.evaluation = None;
        }
        let mut current = manager.reserve_evaluation().unwrap();
        assert_ne!(old.ticket, current.ticket);
        let returned = match old.retain_uncertain(stale_owner.clone()) {
            Err(owner) => owner,
            Ok(()) => panic!("stale ticket accepted an owner"),
        };
        assert!(Arc::ptr_eq(&returned, &stale_owner));
        assert!(manager.inner.lock().unwrap().runtime.is_none());
        assert!(current.retain_uncertain(current_owner.clone()).is_ok());
        drop(old);
        assert_eq!(
            manager.inner.lock().unwrap().evaluation,
            Some(current.ticket)
        );
        retained_same_owner(&manager, &current_owner);
        assert_responding(&returned);
        drop(returned);
        drop(current);
        replacement_refused(&manager);
        unload(&manager).unwrap();
        assert_released(&manager, &current_owner);
    }

    #[test]
    fn preterminate_unload_fault_retains_same_live_owner_until_explicit_retry() {
        let _reset = FaultReset;
        let fixture = FixedOwner::new();
        let manager = metadata_manager();
        let owner = fixture.arc();
        handoff(&manager, &owner);
        FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
        assert_eq!(unload(&manager).err().as_deref(), Some("Cleanup"));
        assert!(!FAIL_CLEANUP_ONCE.with(|fault| fault.get()));
        retained_same_owner(&manager, &owner);
        replacement_refused(&manager);
        assert_responding(&owner);
        unload(&manager).unwrap();
        assert_released(&manager, &owner);
    }

    #[test]
    fn failed_retired_close_retains_owner_and_old_close_cannot_clear_replacement() {
        let _reset = FaultReset;
        let first_fixture = FixedOwner::new();
        let next_fixture = FixedOwner::new();
        let manager = metadata_manager();
        let first = first_fixture.arc();
        let next = next_fixture.arc();
        handoff(&manager, &first);
        let retired = manager.retire().unwrap();
        assert!(Arc::ptr_eq(retired.1.as_ref().unwrap(), &first));
        FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
        manager.close(None, Some(retired.clone()));
        assert!(!FAIL_CLEANUP_ONCE.with(|fault| fault.get()));
        retained_same_owner(&manager, &first);
        replacement_refused(&manager);
        assert_responding(&first);
        unload(&manager).unwrap();
        assert_released(&manager, &first);

        handoff(&manager, &next);
        manager.close(None, Some(retired));
        retained_same_owner(&manager, &next);
        replacement_refused(&manager);
        assert_responding(&next);
        unload(&manager).unwrap();
        assert_released(&manager, &next);
    }

    #[test]
    fn poisoned_owner_is_retained_on_precleanup_fault_then_released_when_reap_is_known() {
        let _reset = FaultReset;
        let fixture = FixedOwner::new();
        let manager = metadata_manager();
        let owner = fixture.arc();
        handoff(&manager, &owner);
        assert_responding(&owner);
        assert!(std::panic::catch_unwind(|| {
            let _held = owner.lock().unwrap();
            panic!("fixed synthetic runtime mutex poison");
        })
        .is_err());
        retained_same_owner(&manager, &owner);
        FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
        assert_eq!(unload(&manager).err().as_deref(), Some("Cleanup"));
        assert!(!FAIL_CLEANUP_ONCE.with(|fault| fault.get()));
        retained_same_owner(&manager, &owner);
        replacement_refused(&manager);

        // No inference after poison: recovery is cleanup-only. A known reap
        // can release exclusion even if the poison diagnostic remains Cleanup.
        if let Err(error) = unload(&manager) {
            assert_eq!(error, "Cleanup");
        }
        let status = manager.status().unwrap();
        assert_eq!(status["resident"], false);
        assert_eq!(status["loaded"], false);
        {
            let mut runtime = match owner.lock() {
                Err(poisoned) => poisoned.into_inner(),
                Ok(_) => panic!("fixture poison unexpectedly cleared"),
            };
            assert_eq!(runtime.status(), Status::Failed);
            assert_eq!(runtime.terminate_and_reap(), Ok(()));
        }
        let reservation = manager.reserve_evaluation().unwrap();
        drop(reservation);
    }
}
