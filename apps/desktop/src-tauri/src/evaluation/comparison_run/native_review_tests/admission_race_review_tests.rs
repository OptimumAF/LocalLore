// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen BEFORE cross-lane busy-conflict correction at d9fd9443. UNRUN.
//! Deterministic PRIVATE admission interleaving, not measured OS scheduling.
//! Real service Job/index, fixed existing hold only; no model/assets/worker process.
use super::*;

fn stale_launch(f: &Fixture, lane: ComparisonLane, client: &str, calls: &Arc<AtomicUsize>) -> Launch {
    let count = calls.clone();
    Launch {
        lane, existing: None, input: Some(Fixture::input(client)), work: Work::Start,
        native: if lane.native() { Some(NativeExecution { models: f.models.clone(), consent: Box::new(move |_| { count.fetch_add(1, Ordering::SeqCst); Ok(false) }) }) } else { None },
    }
}
fn actual_job(f: &Fixture) -> (u64, u64, String, bool, bool) {
    let parent = f.manager.state().unwrap(); let job = parent.job.as_ref().unwrap();
    (job.epoch, job.id, job.run.clone(), job.worker_active, job.selected.is_some())
}

fn assert_stale_interleaving(a_native: bool) {
        let f = Fixture::new(); let client = uuid().unwrap();
        let a_lane = if a_native { ComparisonLane::Native } else { ComparisonLane::Scripted };
        let b_lane = if a_native { ComparisonLane::Scripted } else { ComparisonLane::Native };
        let b_calls = Arc::new(AtomicUsize::new(0));
        // B has passed its outer authorization/input/catalog work while the
        // library is empty. Capture exactly the Launch sent to full_launch.
        authorize(&f.lease, f.epoch, true).unwrap(); batch(1).unwrap(); assert!(valid_id(&client));
        f.manager.full_catalog_lane(&f.lease, f.epoch, true, b_lane).unwrap();
        let b = stale_launch(&f, b_lane, &client, &b_calls);

        // A then wins admission and remains genuinely active. Holding BEFORE
        // execution avoids any native reservation, provisional work or model.
        f.manager.test_case("hold-boundary").unwrap();
        let a_calls = Arc::new(AtomicUsize::new(0)); let count = a_calls.clone();
        let admitted = if a_native {
            f.manager.full_comparison_start_native(&f.lease, &f.models, f.epoch, true, Fixture::input(&client), move |_| { count.fetch_add(1, Ordering::SeqCst); Ok(false) }).unwrap()
        } else { f.manager.full_comparison_start(&f.lease, f.epoch, true, Fixture::input(&client)).unwrap() };
        let before_job = actual_job(&f); let before = inventory(&f.root());

        // This represents B resuming AFTER catalog but BEFORE admission. The
        // existing global Job must not hide its precise same-client conflict.
        let conflict = f.manager.full_launch(&f.lease, f.epoch, b);
        let internal_same = f.manager.full_launch(&f.lease, f.epoch, stale_launch(&f, a_lane, &client, &b_calls));
        let unrelated = f.manager.full_launch(&f.lease, f.epoch, stale_launch(&f, b_lane, &uuid().unwrap(), &b_calls));
        // Same-lane exact internal Busy is intentional: the PUBLIC wrapper must
        // resolve that case to the already admitted original run/operation.
        let public_retry = if a_native { let count = b_calls.clone();
            f.manager.full_comparison_start_native(&f.lease, &f.models, f.epoch, true, Fixture::input(&client), move |_| { count.fetch_add(1, Ordering::SeqCst); Ok(false) })
        } else { f.manager.full_comparison_start(&f.lease, f.epoch, true, Fixture::input(&client)) };
        let after_job = actual_job(&f); let after = inventory(&f.root());

        // Always release/cancel/drain the actual held Job before assertions.
        let cancel = if a_native {
            f.manager.full_comparison_cancel_native(&f.lease, f.epoch, true, cap(&admitted), admitted["operation_id"].as_u64().unwrap())
        } else { f.manager.full_comparison_cancel(&f.lease, f.epoch, true, cap(&admitted), admitted["operation_id"].as_u64().unwrap()) };
        f.manager.test_case("release-boundary").unwrap(); f.manager.drain(f.epoch);

        rejected(conflict, "InvalidEvaluationInput");
        rejected(internal_same, "EvaluationBusy"); rejected(unrelated, "EvaluationBusy");
        let retry = public_retry.unwrap(); assert_eq!(retry["run_id"], admitted["run_id"]); assert_eq!(retry["operation_id"], admitted["operation_id"]);
        assert_eq!(before_job, after_job); assert!(before_job.3); assert_eq!(before_job.4, a_native);
        assert!(after == before); assert_eq!(a_calls.load(Ordering::SeqCst), 0); assert_eq!(b_calls.load(Ordering::SeqCst), 0);
        cancel.unwrap(); assert!(f.manager.cleanup_complete() && f.models.cleanup_complete());
}

#[test]
fn scripted_winner_native_stale_client_conflict_does_not_hide_behind_global_busy() { assert_stale_interleaving(false); }

#[test]
fn native_winner_scripted_stale_client_conflict_does_not_hide_behind_global_busy() { assert_stale_interleaving(true); }
