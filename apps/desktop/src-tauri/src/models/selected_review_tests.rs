// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen selected-owner fence oracles; SOURCE ONLY / UNCOMPILED / UNRUN.
//! Base16919129, coordinator freeze6401731125. Root owns registration/producer.
//! Only the fixed protocol worker is used when Root runs these tests. Ticket
//! invalidation below is explicit private metadata fault injection, not evidence
//! that ordinary retirement loses its ticket. No model/asset/profile-load bypass.
//! Pre-execution contract correction: the selected trait entry owns the fence;
//! the legacy inherent retain_uncertain and its existing tests stay unchanged.
use super::*;
use locallore_eval::local_lane::comparison::selected::SelectedNativeReservation;
use locallore_local_runtime::{Generation, Role, Status};

struct FaultReset;
impl Drop for FaultReset {
    fn drop(&mut self) {
        FAIL_CLEANUP_ONCE.with(|fault| fault.set(false));
    }
}

fn manager() -> Arc<ModelManager> {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-fence-{}",
        exports::identifier().unwrap()
    ));
    assert!(!root.exists());
    Arc::new(ModelManager::new(
        root.join("models"),
        root.join("resources"),
    ))
}

struct FixedOwner {
    runtime: Option<SharedRuntime>,
    directory: PathBuf,
}
impl FixedOwner {
    fn new() -> Self {
        let (runtime, directory) = match LocalRuntime::development_protocol_fixture() {
            Ok(value) => value,
            Err(OwnedStartFailure::BeforeChild(error)) => {
                panic!("fixed protocol startup before child: {error:?}")
            }
            Err(OwnedStartFailure::AfterChild { cause, mut owner }) => {
                let cleanup = owner.terminate_and_reap();
                panic!("fixed protocol startup after child: {cause:?}; cleanup {cleanup:?}");
            }
        };
        let fixture = Self {
            runtime: Some(Arc::new(Mutex::new(runtime))),
            directory,
        };
        fixture.owner().lock().unwrap().load(|| false).unwrap();
        responding(fixture.owner());
        fixture
    }
    fn owner(&self) -> &SharedRuntime {
        self.runtime.as_ref().unwrap()
    }
}
impl Drop for FixedOwner {
    fn drop(&mut self) {
        // Cleanup-only recovery; remove only this fixture's owned paths after
        // its actual cleanup API confirms terminal state, including on panic.
        let owner = self.runtime.take().unwrap();
        let confirmed = match owner.lock() {
            Ok(mut runtime) => runtime.terminate_and_reap().is_ok(),
            Err(poisoned) => poisoned.into_inner().terminate_and_reap().is_ok(),
        };
        // Drop held model/worker file handles before removing the fixture root.
        drop(owner);
        if confirmed {
            let _ = fs::remove_dir_all(&self.directory);
        }
    }
}

fn responding(owner: &SharedRuntime) {
    let mut runtime = owner.lock().unwrap();
    assert_eq!(runtime.status(), Status::Loaded);
    let reply = runtime
        .generate(
            Generation {
                role: Role::Director,
                prompt: "fixed selected owner probe".into(),
                schema: None,
                max_tokens: 1,
            },
            || false,
        )
        .unwrap();
    assert!(reply.text.is_empty());
}

fn stale(manager: &Arc<ModelManager>) -> EvaluationReservation {
    let reservation = manager.reserve_evaluation().unwrap();
    let mut inner = manager.inner.lock().unwrap();
    assert_eq!(inner.evaluation, Some(reservation.ticket));
    // Deliberate single-field metadata fault while the actual R stays alive.
    inner.evaluation = None;
    drop(inner);
    reservation
}

fn rejected(reservation: &mut EvaluationReservation, owner: &SharedRuntime) {
    let returned = match SelectedNativeReservation::retain_uncertain(reservation, owner.clone()) {
        Err(returned) => returned,
        Ok(()) => panic!("faulted stale ticket unexpectedly accepted owner"),
    };
    assert!(Arc::ptr_eq(&returned, owner));
}

fn busy(manager: &Arc<ModelManager>) {
    assert!(matches!(manager.begin("loading"), Err(error) if error == "Busy"));
    assert!(matches!(manager.reserve_evaluation(), Err(error) if error == "Busy"));
}

fn cleanup_status(manager: &ModelManager) {
    let value = manager.status().unwrap();
    assert_eq!(value["loaded"], false);
    assert_eq!(value["error"], "Cleanup");
    assert_ne!(value["phase"], "unloaded");
}

fn marked(reservation: &EvaluationReservation, owner: &SharedRuntime) {
    assert!(std::sync::Weak::ptr_eq(
        reservation
            .retained_owner
            .as_ref()
            .expect("exact retained identity"),
        &Arc::downgrade(owner),
    ));
}

#[test]
fn normal_retirement_preserves_actual_evaluation_ticket_without_external_fence() {
    let manager = manager();
    let reservation = manager.reserve_evaluation().unwrap();
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 0);
    let retired = manager.retire().unwrap();
    assert!(retired.1.is_none());
    manager.close(None, Some(retired));
    assert_eq!(
        manager.inner.lock().unwrap().evaluation,
        Some(reservation.ticket)
    );
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 0);
    busy(&manager);
    drop(reservation);
    drop(
        manager
            .reserve_evaluation()
            .expect("normal ticket released by matching Drop"),
    );
}

#[test]
fn rejected_owner_stays_excluded_and_truthful_through_retirement_and_empty_close() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let manager = manager();
    let mut reservation = stale(&manager);
    rejected(&mut reservation, fixture.owner());
    marked(&reservation, fixture.owner());
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 1);
    assert!(manager.inner.lock().unwrap().runtime.is_none());
    busy(&manager);
    {
        let _held = fixture.owner().lock().unwrap();
        cleanup_status(&manager);
    }
    let retired = manager.retire().unwrap();
    assert!(retired.1.is_none());
    manager.close(None, Some(retired));
    cleanup_status(&manager);
    busy(&manager);
    responding(fixture.owner());
    let outcome = reservation.cleanup_retained(fixture.owner());
    assert!(outcome.confirmed);
    assert!(outcome.result.is_ok());
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 0);
    assert!(reservation.retained_owner.is_none());
    drop(reservation);
    drop(
        manager
            .reserve_evaluation()
            .expect("actual terminal cleanup releases fence"),
    );
}

#[test]
fn same_arc_is_one_fence_wrong_arc_cannot_clear_or_rebind_and_slot_transfer_is_safe() {
    let _reset = FaultReset;
    let first = FixedOwner::new();
    let other = FixedOwner::new();
    let manager = manager();
    let mut reservation = stale(&manager);
    rejected(&mut reservation, first.owner());
    rejected(&mut reservation, first.owner());
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 1);
    rejected(&mut reservation, other.owner());
    marked(&reservation, first.owner());
    let wrong = reservation.cleanup_retained(other.owner());
    assert!(!wrong.confirmed && wrong.result.is_err());
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 1);
    responding(first.owner());
    responding(other.owner());
    busy(&manager);
    assert!(reservation.cleanup_retained(first.owner()).confirmed);
    drop(reservation);

    let mut current = manager.reserve_evaluation().unwrap();
    assert!(
        SelectedNativeReservation::retain_uncertain(&mut current, other.owner().clone()).is_ok()
    );
    assert!(
        SelectedNativeReservation::retain_uncertain(&mut current, other.owner().clone()).is_ok()
    );
    assert!(current.retained_owner.is_none());
    let inner = manager.inner.lock().unwrap();
    assert_eq!(inner.retained_evaluations, 0);
    assert!(Arc::ptr_eq(inner.runtime.as_ref().unwrap(), other.owner()));
    drop(inner);
    drop(current);
    assert!(matches!(manager.reserve_evaluation(), Err(error) if error == "ModelLoaded"));
    let retired = manager.retire().unwrap();
    manager.close(None, Some(retired));
    drop(
        manager
            .reserve_evaluation()
            .expect("same-slot actual cleanup releases ownership"),
    );
}

#[test]
fn two_induced_stale_owners_release_only_their_own_count_after_actual_cleanup() {
    let _reset = FaultReset;
    let first = FixedOwner::new();
    let second = FixedOwner::new();
    let manager = manager();
    // Obtain both actual guards before either failure installs its fence.
    let mut left = stale(&manager);
    let mut right = stale(&manager);
    assert_ne!(left.ticket, right.ticket);
    rejected(&mut left, first.owner());
    rejected(&mut right, second.owner());
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 2);
    let retired = manager.retire().unwrap();
    manager.close(None, Some(retired));
    assert!(left.cleanup_retained(first.owner()).confirmed);
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 1);
    drop(left);
    marked(&right, second.owner());
    cleanup_status(&manager);
    busy(&manager);
    responding(second.owner());
    assert!(right.cleanup_retained(second.owner()).confirmed);
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 0);
    drop(right);
    drop(
        manager
            .reserve_evaluation()
            .expect("both actual owners acknowledged terminal"),
    );
}

#[test]
fn precleanup_fault_poison_confirmation_and_unacknowledged_drop_are_distinct() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let drop_fixture = FixedOwner::new();
    let manager = manager();
    let mut reservation = stale(&manager);
    rejected(&mut reservation, fixture.owner());
    FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let first = reservation.cleanup_retained(fixture.owner());
    assert!(!first.confirmed && first.result.is_err());
    assert!(!FAIL_CLEANUP_ONCE.with(|fault| fault.get()));
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 1);
    responding(fixture.owner());
    assert!(std::panic::catch_unwind(|| {
        let _held = fixture.owner().lock().unwrap();
        panic!("synthetic fixed-owner mutex poison");
    })
    .is_err());
    FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let uncertain = reservation.cleanup_retained(fixture.owner());
    assert!(!uncertain.confirmed && uncertain.result.is_err());
    busy(&manager);
    cleanup_status(&manager);
    let confirmed = reservation.cleanup_retained(fixture.owner());
    assert!(
        confirmed.confirmed,
        "actual reap proof survives poison diagnostic"
    );
    assert_eq!(confirmed.result.err().as_deref(), Some("Cleanup"));
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 0);
    drop(reservation);

    let mut unacknowledged = stale(&manager);
    rejected(&mut unacknowledged, drop_fixture.owner());
    // Fixture hygiene: actually clean this child FIRST, but intentionally do
    // not submit R's proof. Dropping R must not manufacture acknowledgement.
    drop_fixture
        .owner()
        .lock()
        .unwrap()
        .terminate_and_reap()
        .unwrap();
    drop(unacknowledged);
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 1);
    busy(&manager);
    cleanup_status(&manager);
}

#[test]
fn external_old_cleanup_preserves_newer_actual_slot_ticket_profile_job_and_host_supplier() {
    let _reset = FaultReset;
    let old_fixture = FixedOwner::new();
    let current_fixture = FixedOwner::new();
    let manager = manager();
    let mut old = stale(&manager);
    let mut current = manager.reserve_evaluation().unwrap();
    rejected(&mut old, old_fixture.owner());
    let retired = manager.retire().unwrap();
    manager.close(None, Some(retired));
    assert!(SelectedNativeReservation::retain_uncertain(
        &mut current,
        current_fixture.owner().clone()
    )
    .is_ok());
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 1);

    let host = Host::new(true);
    let constructed = Arc::new(AtomicBool::new(false));
    let observed = constructed.clone();
    let factory: locallore::host::ProviderFactory = Arc::new(move || {
        observed.store(true, Ordering::SeqCst);
        Box::new(locallore::inference::FakeProvider::new(
            locallore::inference::FakeMode::Accepted,
        ))
    });
    let profile = PlayProfile {
        id: "selected-fence-current".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 5000,
        repair_limit: 1,
    };
    host.configure_fixture_provider(profile, factory).unwrap();
    let before_host = host.call(br#"{"version":1,"command":{"op":"capabilities"}}"#);
    assert_eq!(before_host["data"]["free_text"], true);
    let (job, ticket, profile) = {
        let inner = manager.inner.lock().unwrap();
        (
            inner.job,
            inner.evaluation,
            serde_json::to_value(&inner.profile).unwrap(),
        )
    };
    let outcome = old.cleanup_retained(old_fixture.owner());
    assert!(outcome.confirmed && outcome.result.is_ok());
    drop(old);
    let inner = manager.inner.lock().unwrap();
    assert_eq!(inner.retained_evaluations, 0);
    assert_eq!(inner.job, job);
    assert_eq!(inner.evaluation, ticket);
    assert_eq!(serde_json::to_value(&inner.profile).unwrap(), profile);
    assert!(Arc::ptr_eq(
        inner.runtime.as_ref().unwrap(),
        current_fixture.owner()
    ));
    drop(inner);
    assert_eq!(
        host.call(br#"{"version":1,"command":{"op":"capabilities"}}"#),
        before_host
    );
    assert!(
        !constructed.load(Ordering::SeqCst),
        "capability checks never generate"
    );
    responding(current_fixture.owner());
    drop(current);
    let retired = manager.retire().unwrap();
    manager.close(Some(&host), Some(retired));
    drop(
        manager
            .reserve_evaluation()
            .expect("only current actual slot cleanup releases it"),
    );
}

// Separately frozen witness extension, coordinator6401959193. The original six
// groups above are unchanged. APIs below are absent at e2a154f7: SOURCE ONLY /
// UNCOMPILED / UNRUN, not behavior RED. Root owns actual execution/producer.

#[test]
fn selected_witness_survives_guard_drop_and_confirms_only_actual_cleanup_even_with_poison() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let manager = manager();
    let mut reservation = manager.reserve_evaluation().unwrap();
    let witness = reservation.cleanup_witness();
    let copied_witness = witness.clone();
    assert!(!witness.confirmed() && !copied_witness.confirmed());
    assert!(
        SelectedNativeReservation::retain_uncertain(&mut reservation, fixture.owner().clone())
            .is_ok()
    );
    drop(reservation);
    assert!(
        !witness.confirmed(),
        "handoff/guard Drop is not cleanup proof"
    );
    let retired = manager.retire().unwrap();
    assert!(Arc::ptr_eq(retired.1.as_ref().unwrap(), fixture.owner()));
    FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    manager.close(None, Some(retired));
    assert!(!FAIL_CLEANUP_ONCE.with(|fault| fault.get()));
    assert!(!witness.confirmed() && !copied_witness.confirmed());
    assert!(
        matches!(manager.reserve_evaluation(), Err(error) if error == "ModelLoaded" || error == "Busy")
    );
    responding(fixture.owner());

    // Poison is a diagnostic, not a claim that the child has disappeared.
    assert!(std::panic::catch_unwind(|| {
        let _held = fixture.owner().lock().unwrap();
        panic!("synthetic selected witness owner poison");
    })
    .is_err());
    assert!(!witness.confirmed());
    let outcome = manager.cleanup_selected(&witness);
    assert!(
        outcome.confirmed,
        "actual cleanup proof may coexist with poison diagnostic"
    );
    assert_eq!(outcome.result.err().as_deref(), Some("Cleanup"));
    assert!(witness.confirmed() && copied_witness.confirmed());
    assert_eq!(manager.status().unwrap()["resident"], false);
    assert_eq!(
        fixture
            .owner()
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .status(),
        Status::Failed
    );
    drop(
        manager
            .reserve_evaluation()
            .expect("actual terminal proof releases normal model slot"),
    );
}

#[test]
fn already_confirmed_old_witness_cannot_touch_newer_slot_job_profile_or_host() {
    let _reset = FaultReset;
    let old_fixture = FixedOwner::new();
    let next_fixture = FixedOwner::new();
    let manager = manager();
    let mut old = manager.reserve_evaluation().unwrap();
    let old_witness = old.cleanup_witness();
    assert!(
        SelectedNativeReservation::retain_uncertain(&mut old, old_fixture.owner().clone()).is_ok()
    );
    drop(old);
    assert!(!old_witness.confirmed());
    let cleaned = manager.cleanup_selected(&old_witness);
    assert!(cleaned.confirmed && cleaned.result.is_ok());
    assert!(old_witness.confirmed());

    let mut current = manager.reserve_evaluation().unwrap();
    let current_witness = current.cleanup_witness();
    assert!(SelectedNativeReservation::retain_uncertain(
        &mut current,
        next_fixture.owner().clone()
    )
    .is_ok());
    let host = Host::new(true);
    let constructed = Arc::new(AtomicBool::new(false));
    let observed = constructed.clone();
    let factory: locallore::host::ProviderFactory = Arc::new(move || {
        observed.store(true, Ordering::SeqCst);
        Box::new(locallore::inference::FakeProvider::new(
            locallore::inference::FakeMode::Accepted,
        ))
    });
    host.configure_fixture_provider(
        PlayProfile {
            id: "selected-witness-current".into(),
            model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40),
            template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64),
            profile_manifest_sha256: "e".repeat(64),
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 350,
            deadline_ms: 5000,
            repair_limit: 1,
        },
        factory,
    )
    .unwrap();
    let before_status = manager.status().unwrap();
    let before_host = host.call(br#"{"version":1,"command":{"op":"capabilities"}}"#);
    assert_eq!(before_host["data"]["free_text"], true);
    let before_ticket = manager.inner.lock().unwrap().evaluation;
    let result = manager.cleanup_selected(&old_witness);
    assert!(result.confirmed && result.result.is_ok());
    assert_eq!(manager.status().unwrap(), before_status);
    assert_eq!(manager.inner.lock().unwrap().evaluation, before_ticket);
    assert!(Arc::ptr_eq(
        manager.inner.lock().unwrap().runtime.as_ref().unwrap(),
        next_fixture.owner()
    ));
    assert_eq!(
        host.call(br#"{"version":1,"command":{"op":"capabilities"}}"#),
        before_host
    );
    assert!(!current_witness.confirmed());
    assert!(!constructed.load(Ordering::SeqCst));
    responding(next_fixture.owner());
    drop(current);
    let retired = manager.retire().unwrap();
    manager.close(Some(&host), Some(retired));
    assert!(current_witness.confirmed());
    drop(
        manager
            .reserve_evaluation()
            .expect("only actual current owner cleanup releases slot"),
    );
}

#[test]
fn genuine_late_selected_handoff_after_empty_retire_is_cleaned_by_matching_close() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let manager = manager();
    let mut reservation = manager.reserve_evaluation().unwrap();
    let witness = reservation.cleanup_witness();
    // No metadata fault: the real reservation ticket survives actual retire.
    let retired = manager.retire().unwrap();
    assert!(
        retired.1.is_none(),
        "retirement occurs before runtime handoff"
    );
    assert_eq!(
        manager.inner.lock().unwrap().evaluation,
        Some(reservation.ticket)
    );
    assert!(
        SelectedNativeReservation::retain_uncertain(&mut reservation, fixture.owner().clone())
            .is_ok()
    );
    drop(reservation);
    assert!(!witness.confirmed());
    assert!(Arc::ptr_eq(
        manager.inner.lock().unwrap().runtime.as_ref().unwrap(),
        fixture.owner()
    ));
    responding(fixture.owner());
    // The captured None is not a cleanup proof. Matching close must inspect
    // the actual late-installed owner, reap it, and acknowledge that witness.
    manager.close(None, Some(retired));
    assert!(
        witness.confirmed(),
        "matching close omitted genuine late current owner"
    );
    assert_eq!(fixture.owner().lock().unwrap().status(), Status::Failed);
    assert_eq!(manager.status().unwrap()["resident"], false);
    assert_eq!(manager.inner.lock().unwrap().retained_evaluations, 0);
    drop(
        manager
            .reserve_evaluation()
            .expect("late owner is actually terminal"),
    );
}
