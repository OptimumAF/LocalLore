// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen source-only owner-port oracles; Root registers this module separately.
//! UNCOMPILED/UNRUN by this author. Dedicated execution additionally enables
//! locallore-local-runtime/development-worker and builds its fixed protocol fixture.
//! Real tiny child ownership, synthetic reservation port; no weights/native UI.
#![cfg(feature = "local-model")]

use super::native_owner::{self, SelectedNativeFailure, SelectedNativeReservation, SharedRuntime};
use crate::local_lane::NativeAssets;
use locallore_local_runtime::{Error, LocalRuntime, OwnedStartFailure, Status};
use std::{
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicUsize, Ordering},
        mpsc, Arc, Mutex,
    },
    time::Duration,
};

struct FaultReset;
impl Drop for FaultReset {
    fn drop(&mut self) {
        native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(false));
    }
}

struct FixedOwner {
    runtime: SharedRuntime,
    directory: PathBuf,
}
impl FixedOwner {
    fn new() -> Self {
        let (runtime, directory) = match LocalRuntime::development_protocol_fixture() {
            Ok(fixture) => fixture,
            Err(OwnedStartFailure::BeforeChild(cause)) => {
                panic!("fixed fixture unavailable before child: {cause:?}");
            }
            Err(OwnedStartFailure::AfterChild { cause, mut owner }) => {
                let cleanup = owner.terminate_and_reap();
                panic!("fixed fixture failed: {cause:?}; cleanup {cleanup:?}");
            }
        };
        let fixture = Self {
            runtime: Arc::new(Mutex::new(runtime)),
            directory,
        };
        fixture
            .runtime
            .lock()
            .unwrap()
            .load(|| false)
            .expect("fixed protocol load, no weights");
        assert_eq!(fixture.runtime.lock().unwrap().status(), Status::Loaded);
        fixture
    }
    fn assert_confirmed(&self) {
        let mut runtime = self
            .runtime
            .lock()
            .unwrap_or_else(|poison| poison.into_inner());
        assert_eq!(runtime.status(), Status::Failed);
        assert_eq!(
            runtime.terminate_and_reap(),
            Ok(()),
            "same actual owner cleanup is idempotent"
        );
        assert_eq!(runtime.load(|| false), Err(Error::WorkerUnavailable));
    }
}
impl Drop for FixedOwner {
    fn drop(&mut self) {
        let confirmed = self
            .runtime
            .lock()
            .unwrap_or_else(|poison| poison.into_inner())
            .terminate_and_reap()
            .is_ok();
        // Only the zero-argument helper's own resolved, immediate TEMP child.
        // Never remove local diagnostics while the actual child is uncertain.
        if confirmed {
            if let (Ok(directory), Ok(temp)) = (
                self.directory.canonicalize(),
                std::env::temp_dir().canonicalize(),
            ) {
                let prefix = format!("locallore-protocol-fixture-{}-", std::process::id());
                if directory.parent() == Some(temp.as_path())
                    && directory
                        .file_name()
                        .and_then(|name| name.to_str())
                        .is_some_and(|name| name.starts_with(&prefix))
                {
                    let _ = std::fs::remove_dir_all(directory);
                }
            }
        }
    }
}

// This spy tests the shared reservation interface and Drop ordering only.
// Actual ModelManager ownership/native wire evidence belongs to its own tests.
struct ReservationState {
    accept: bool,
    retained: Mutex<Option<SharedRuntime>>,
    events: Mutex<Vec<&'static str>>,
    assets: AtomicUsize,
    drops: AtomicUsize,
    drop_observed_retained: AtomicBool,
}
impl ReservationState {
    fn new(accept: bool) -> Arc<Self> {
        Arc::new(Self {
            accept,
            retained: Mutex::new(None),
            events: Mutex::new(Vec::new()),
            assets: AtomicUsize::new(0),
            drops: AtomicUsize::new(0),
            drop_observed_retained: AtomicBool::new(false),
        })
    }
    fn assert_events(&self, expected: &[&str]) {
        assert_eq!(self.events.lock().unwrap().as_slice(), expected);
        assert_eq!(
            self.assets.load(Ordering::SeqCst),
            0,
            "cleanup must not inspect assets"
        );
    }
}
struct Reservation {
    state: Arc<ReservationState>,
    private_marker: &'static str,
}
impl Reservation {
    fn new(state: &Arc<ReservationState>) -> Self {
        Self {
            state: state.clone(),
            private_marker: "PRIVATE-RESERVATION-NOT-DEBUG",
        }
    }
}
impl SelectedNativeReservation for Reservation {
    fn assets(&self) -> NativeAssets<'_> {
        self.state.assets.fetch_add(1, Ordering::SeqCst);
        NativeAssets {
            resource_dir: Path::new(self.private_marker),
            model: Path::new("UNUSED-PRIVATE-MODEL"),
        }
    }
    fn retain_uncertain(
        &mut self,
        runtime: SharedRuntime,
    ) -> std::result::Result<(), SharedRuntime> {
        self.state.events.lock().unwrap().push("handoff");
        if !self.state.accept {
            return Err(runtime);
        }
        let mut retained = self.state.retained.lock().unwrap();
        assert!(retained.is_none(), "one transfer, no overwritten owner");
        *retained = Some(runtime);
        Ok(())
    }
}
impl Drop for Reservation {
    fn drop(&mut self) {
        self.state.drop_observed_retained.store(
            self.state.retained.lock().unwrap().is_some(),
            Ordering::SeqCst,
        );
        self.state.events.lock().unwrap().push("drop");
        self.state.drops.fetch_add(1, Ordering::SeqCst);
    }
}

#[test]
fn confirmed_actual_owner_cleanup_drops_reservation_once_without_asset_access() {
    let fixture = FixedOwner::new();
    let state = ReservationState::new(true);
    native_owner::finish_owner(Reservation::new(&state), fixture.runtime.clone(), None).unwrap();
    fixture.assert_confirmed();
    state.assert_events(&["drop"]);
    assert_eq!(state.drops.load(Ordering::SeqCst), 1);
    assert!(state.retained.lock().unwrap().is_none());
}

#[test]
fn confirmed_cleanup_preserves_fixed_initial_cause_without_retained_payload() {
    let fixture = FixedOwner::new();
    let state = ReservationState::new(true);
    let failure = native_owner::finish_owner(
        Reservation::new(&state),
        fixture.runtime.clone(),
        Some("RunBudget".into()),
    )
    .unwrap_err();
    assert_eq!(failure.code(), "RunBudget");
    assert_eq!(failure.cause(), Some("RunBudget"));
    assert!(!failure.cleanup_uncertain());
    assert!(
        failure.into_retained().is_err(),
        "confirmed cleanup owns no reservation payload"
    );
    fixture.assert_confirmed();
    state.assert_events(&["drop"]);
    assert_eq!(state.drops.load(Ordering::SeqCst), 1);
}

#[test]
fn uncertain_cleanup_transfers_exact_arc_before_reservation_drop_and_stays_retryable() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let state = ReservationState::new(true);
    native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let failure = native_owner::finish_owner(
        Reservation::new(&state),
        fixture.runtime.clone(),
        Some("RunBudget".into()),
    )
    .unwrap_err();
    assert_eq!(failure.code(), "Cleanup");
    assert_eq!(failure.cause(), Some("RunBudget"));
    assert!(failure.cleanup_uncertain());
    assert!(
        !native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.get()),
        "one-shot consumed"
    );
    state.assert_events(&["handoff", "drop"]);
    assert_eq!(state.drops.load(Ordering::SeqCst), 1);
    assert!(
        state.drop_observed_retained.load(Ordering::SeqCst),
        "actual transferred Arc existed before reservation Drop"
    );
    let retained = state
        .retained
        .lock()
        .unwrap()
        .take()
        .expect("port owns actual runtime before ticket Drop");
    assert!(Arc::ptr_eq(&retained, &fixture.runtime));
    assert_eq!(
        retained.lock().unwrap().status(),
        Status::Loaded,
        "fault did not attempt cleanup"
    );
    assert!(
        failure.into_retained().is_err(),
        "successful handoff does not duplicate ownership payload"
    );
    retained.lock().unwrap().terminate_and_reap().unwrap();
    fixture.assert_confirmed();
}

#[test]
fn rejected_handoff_returns_same_actual_arc_and_undropped_reservation_with_redacted_error() {
    let _reset = FaultReset;
    let fixture = FixedOwner::new();
    let state = ReservationState::new(false);
    native_owner::FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let failure = native_owner::finish_owner(
        Reservation::new(&state),
        fixture.runtime.clone(),
        Some("RunBudget".into()),
    )
    .unwrap_err();
    assert_eq!(failure.code(), "Cleanup");
    assert_eq!(failure.cause(), Some("RunBudget"));
    assert!(failure.cleanup_uncertain());
    state.assert_events(&["handoff"]);
    assert_eq!(
        state.drops.load(Ordering::SeqCst),
        0,
        "failed transfer must retain reservation"
    );
    assert!(state.retained.lock().unwrap().is_none());
    let debug = format!("{failure:?}");
    assert!(!debug.contains("PRIVATE-RESERVATION-NOT-DEBUG"));
    assert!(!debug.contains("UNUSED-PRIVATE-MODEL"));
    assert!(!debug.contains(&fixture.directory.to_string_lossy().to_string()));
    let (reservation, runtime) = match failure.into_retained() {
        Ok(retained) => retained,
        Err(_) => panic!("failed transfer lost owned cleanup payload"),
    };
    assert!(Arc::ptr_eq(&runtime, &fixture.runtime));
    assert_eq!(runtime.lock().unwrap().status(), Status::Loaded);
    assert_eq!(state.drops.load(Ordering::SeqCst), 0);
    runtime.lock().unwrap().terminate_and_reap().unwrap();
    drop(runtime);
    drop(reservation);
    fixture.assert_confirmed();
    state.assert_events(&["handoff", "drop"]);
    assert_eq!(state.drops.load(Ordering::SeqCst), 1);
}

#[test]
fn busy_actual_runtime_is_handed_off_without_waiting_for_its_mutex_or_assets() {
    let fixture = FixedOwner::new();
    let state = ReservationState::new(true);
    let held = fixture.runtime.lock().unwrap();
    let (send, receive) = mpsc::channel();
    let worker = {
        let runtime = fixture.runtime.clone();
        let reservation = Reservation::new(&state);
        std::thread::spawn(move || {
            send.send(native_owner::finish_owner(reservation, runtime, None))
                .expect("owned result receiver");
        })
    };
    // Fixture scheduling bound only, not an OS-wide cleanup deadline. Release
    // the mutex before joining even if a broken implementation waited on it.
    let result = receive.recv_timeout(Duration::from_secs(3));
    drop(held);
    worker.join().unwrap();
    let failure = result
        .expect("busy cleanup must return without taking the held mutex")
        .unwrap_err();
    assert_eq!(failure.code(), "Cleanup");
    assert_eq!(failure.cause(), Some("Cleanup"));
    assert!(failure.cleanup_uncertain());
    state.assert_events(&["handoff", "drop"]);
    let retained = state
        .retained
        .lock()
        .unwrap()
        .take()
        .expect("busy owner retained");
    assert!(Arc::ptr_eq(&retained, &fixture.runtime));
    assert_eq!(retained.lock().unwrap().status(), Status::Loaded);
    retained.lock().unwrap().terminate_and_reap().unwrap();
    fixture.assert_confirmed();
}

#[test]
fn poisoned_actual_owner_is_cleanup_only_and_confirmed_cleanup_releases_reservation() {
    let fixture = FixedOwner::new();
    let state = ReservationState::new(true);
    let runtime = fixture.runtime.clone();
    assert!(std::thread::spawn(move || {
        let _held = runtime.lock().unwrap();
        panic!("synthetic owner poison");
    })
    .join()
    .is_err());
    assert!(fixture.runtime.is_poisoned());
    let failure =
        native_owner::finish_owner(Reservation::new(&state), fixture.runtime.clone(), None)
            .unwrap_err();
    assert_eq!(failure.code(), "Cleanup");
    assert_eq!(failure.cause(), Some("Cleanup"));
    assert!(
        !failure.cleanup_uncertain(),
        "poison diagnostic differs from actual cleanup uncertainty"
    );
    assert!(failure.into_retained().is_err());
    fixture.assert_confirmed();
    state.assert_events(&["drop"]);
    assert_eq!(state.drops.load(Ordering::SeqCst), 1);
    assert!(state.retained.lock().unwrap().is_none());
}

#[test]
fn callback_error_allowlist_discards_unknown_private_text_in_code_cause_and_debug() {
    let known = SelectedNativeFailure::<Reservation>::from_error("RunBudget".into());
    assert_eq!(known.code(), "RunBudget");
    assert_eq!(known.cause(), Some("RunBudget"));
    assert!(!known.cleanup_uncertain());
    for private in [
        "PRIVATE-CALLBACK-STORY",
        "C:\\private\\model.gguf",
        "RuntimeCancelled: PRIVATE-RAW-OUTPUT",
    ] {
        let failure = SelectedNativeFailure::<Reservation>::from_error(private.into());
        assert_eq!(failure.code(), "SelectedExecution");
        assert_eq!(failure.cause(), Some("SelectedExecution"));
        assert!(!failure.cleanup_uncertain());
        assert!(!format!("{failure:?}").contains(private));
        assert!(
            failure.into_retained().is_err(),
            "plain callback error has no invented owner"
        );
    }
}
