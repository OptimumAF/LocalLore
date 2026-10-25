// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! SOURCE ONLY / UNCOMPILED / UNRUN. Child of selected::tests.
//! Actual fixed protocol child ownership, not approved inference or app exit.
use super::*;
use locallore_eval::local_lane::comparison::selected::SelectedNativeReservation;

struct FixedOwner {
    runtime: Arc<Mutex<locallore_local_runtime::LocalRuntime>>,
    directory: PathBuf,
}
impl Drop for FixedOwner {
    fn drop(&mut self) {
        let confirmed = match self.runtime.lock() {
            Ok(mut owner) => owner.terminate_and_reap().is_ok(),
            Err(poisoned) => poisoned.into_inner().terminate_and_reap().is_ok(),
        };
        if confirmed { let _ = fs::remove_dir_all(&self.directory); }
    }
}

#[test]
fn one_shutdown_drain_reconciles_actual_accepted_handoff_after_models_confirms_cleanup() {
    let f = Fixture::new();
    let (runtime, directory) = match locallore_local_runtime::LocalRuntime::development_protocol_fixture() {
        Ok(value) => value,
        Err(locallore_local_runtime::OwnedStartFailure::BeforeChild(error)) => panic!("fixed worker: {error:?}"),
        Err(locallore_local_runtime::OwnedStartFailure::AfterChild { cause, mut owner }) => {
            let cleanup = owner.terminate_and_reap();
            panic!("fixed worker: {cause:?}; cleanup {cleanup:?}");
        }
    };
    let fixed = FixedOwner { runtime: Arc::new(Mutex::new(runtime)), directory };
    let mut reservation = f.models.reserve_evaluation().unwrap();
    let witness = reservation.cleanup_witness();
    // Exercise the genuine SAME manager ticket and actual trait handoff. No
    // stale-ticket helper, fabricated witness acknowledgement or owner swap.
    let accepted = SelectedNativeReservation::retain_uncertain(&mut reservation, fixed.runtime.clone());
    assert!(accepted.is_ok());
    drop(reservation);
    assert!(!witness.confirmed());
    assert!(!f.models.cleanup_complete());
    {
        let mut parent = f.manager.state().unwrap();
        parent.next += 1;
        parent.job = Some(Job {
            kind: JobKind::Curated,
            worker_active: false,
            epoch: f.epoch,
            id: parent.next,
            run: uuid().unwrap(),
            cancel: Cancellation::default(),
            selected: Some(SelectedOwnership {
                models: f.models.clone(), witness: Some(witness.clone()),
                retained: None, cleanup_running: false,
            }),
        });
    }
    let archives = crate::archive::ArchiveBroker::default();
    let closed = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
    f.manager.retire(f.epoch);
    archives.retire(f.epoch);
    let retired = f.models.retire();
    let first = crate::shutdown::drain_owned_work(&f.manager, &archives, &f.models, None, retired, f.epoch);
    let observed = (first, witness.confirmed(), f.manager.cleanup_complete(), f.models.cleanup_complete());
    // Always perform real fallback reconciliation BEFORE assertions. The
    // original one-pass bug must not orphan the genuine protocol process.
    let _ = f.manager.selected_cleanup_retired(f.epoch);
    f.models.close(None, f.models.retire());
    let _ = f.manager.selected_cleanup_retired(f.epoch);
    f.lease.finish_close(closed, || {});
    assert_eq!(observed, (true, true, true, true),
        "one captured-epoch drain must reconcile the Job after actual Models cleanup");
    assert!(f.manager.state().unwrap().job.is_none());
    assert_eq!(fixed.runtime.lock().unwrap().status(), locallore_local_runtime::Status::Failed);
}
