// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen service regressions; SOURCE ONLY / UNCOMPILED / UNRUN at handoff.
//! Child of selected::tests, using its genuine scripted producer and service.
//! No native inference, IPC, renderer, canonical SQL or fabricated receipts.
use super::*;
use std::sync::mpsc::{sync_channel, SyncSender};

// Presentation may finish just before the worker clears the parent job. Join
// that actual worker without drain(), which would destroy the client cache.
fn join_finished(f: &Fixture) {
    let worker = {
        let _registration = f.manager.registration.lock().unwrap();
        f.manager.worker.lock().unwrap().take()
    };
    if let Some((epoch, worker)) = worker {
        assert_eq!(epoch, f.epoch);
        worker.join().unwrap();
    }
    assert!(f.manager.state().unwrap().job.is_none());
}

struct Release(Option<SyncSender<()>>);
impl Release {
    fn now(&mut self) {
        if let Some(sender) = self.0.take() {
            let _ = sender.try_send(());
        }
    }
}
impl Drop for Release {
    fn drop(&mut self) {
        self.now();
    }
}

fn existing_run(f: &Fixture) -> String {
    let client = uuid().unwrap();
    let prepared = f.prepare(&client);
    f.manager
        .selected_start(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            &client,
            prepared["plan_token"].as_str().unwrap(),
        )
        .unwrap();
    let done = f.done(&client);
    join_finished(f);
    assert_eq!(done["phase"], "completed", "{done}");
    let run = done["run_id"].as_str().unwrap().to_owned();
    f.manager
        .selected_close(&f.lease, f.epoch, &client)
        .unwrap();
    run
}

#[test]
fn open_existing_retires_unused_plan_before_consent_and_cannot_execute_it_after_open() {
    replacement_case(0);
}

#[test]
fn denied_failed_and_cancelled_open_never_resurrect_the_replaced_execution_plan() {
    for outcome in [1, 2, 3] {
        replacement_case(outcome);
    }
}

// 0 accepts read consent; 1 denies; 2 actual consent callback fails; 3 native
// cancellation arrives while consent is held. All use real existing run B.
fn replacement_case(outcome: u8) {
    let f = Fixture::new();
    let source_before = inventory(source());
    let run = existing_run(&f);
    let (target, pins) = f.manager.selected_work_path(&run).unwrap();
    drop(pins);
    let target_before = inventory(&target);
    let client = uuid().unwrap();
    let prepared = f.prepare(&client);
    join_finished(&f);
    let old_token = prepared["plan_token"].as_str().unwrap().to_owned();
    let (entered_tx, entered_rx) = sync_channel(1);
    let (release_tx, release_rx) = sync_channel(1);
    let mut release = Release(Some(release_tx));
    let opening = f
        .manager
        .selected_open(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            &client,
            &run,
            move |_| {
                entered_tx
                    .send(())
                    .map_err(|_| "EvaluationInternal".to_owned())?;
                release_rx
                    .recv_timeout(Duration::from_secs(60))
                    .map_err(|_| "EvaluationInternal".to_owned())?;
                match outcome {
                    1 => Ok(false),
                    2 => Err("EvaluationIo".into()),
                    _ => Ok(true),
                }
            },
        )
        .unwrap();
    let entered = entered_rx.recv_timeout(Duration::from_secs(60));
    // Collect observations before releasing the actual consent callback, but
    // never panic while it is waiting. Its native gates must be available.
    let pending = f.status(&client);
    let registration_free = f.manager.registration.try_lock().is_ok();
    let parent_free = f.manager.state.try_lock().is_ok();
    let selected_free = f.manager.selected.try_lock().is_ok();
    let source_reopened = source_reader::open_read_only(source()).is_ok();
    let cancellation = if outcome == 3 {
        Some(f.manager.selected_cancel(
            &f.lease,
            f.epoch,
            true,
            &client,
            opening["operation_id"].as_u64().unwrap(),
        ))
    } else {
        None
    };
    release.now();
    let done = f.done(&client);
    join_finished(&f);
    // A baseline can admit the stale token only in the successful-open case.
    // Check it even after denial/failure/cancel to prohibit resurrection.
    let stale = f
        .manager
        .selected_start(&f.lease, &f.models, f.epoch, true, &client, &old_token);
    if stale.is_ok() {
        let _ = f.done(&client);
        join_finished(&f);
    }
    f.manager
        .selected_close(&f.lease, f.epoch, &client)
        .unwrap();
    let source_after = inventory(source());
    let target_after = inventory(&target);
    assert!(entered.is_ok(), "read consent was actually entered");
    assert!(
        registration_free && parent_free && selected_free,
        "source-cap release and native consent must not hold manager gates"
    );
    assert!(
        source_reopened,
        "unused plan A must release its real source lock before B consent"
    );
    assert_eq!(pending["plan_token"], Value::Null);
    assert_eq!(pending["prepared"], Value::Null);
    assert!(
        matches!(stale, Err(ref error) if error == "UnknownEvaluationRun"),
        "replaced A must never start, got {stale:?}"
    );
    if outcome == 0 {
        assert_eq!(done["phase"], "completed", "{done}");
        assert_eq!(done["run_id"], run);
        assert!(done["run_token"].is_string());
        assert!(done["binding"].is_string());
    } else {
        assert_eq!(done["phase"], "failed", "{done}");
        assert_eq!(
            done["error"],
            if outcome == 2 {
                "EvaluationIo"
            } else {
                "Cancelled"
            }
        );
        assert_eq!(done["run_token"], Value::Null);
        assert_eq!(done["plan_token"], Value::Null);
    }
    if let Some(cancellation) = cancellation {
        assert!(cancellation.is_ok());
    }
    assert_eq!(source_after, source_before);
    assert_eq!(target_after, target_before);
    assert_eq!(
        f.manager.selected_catalog(&f.lease, f.epoch, true).unwrap()["runs"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn concurrent_exact_start_rechecks_consumed_identity_after_first_execution_finishes() {
    let f = Fixture::new();
    let source_before = inventory(source());
    let client = uuid().unwrap();
    let prepared = f.prepare(&client);
    join_finished(&f);
    let token = prepared["plan_token"].as_str().unwrap().to_owned();
    let (entered_tx, entered_rx) = sync_channel(1);
    let (release_tx, release_rx) = sync_channel(1);
    let mut release = Release(Some(release_tx));
    let manager = f.manager.clone();
    let lease = f.lease.clone();
    let models = f.models.clone();
    let epoch = f.epoch;
    let b_client = client.clone();
    let b_token = token.clone();
    let b = std::thread::spawn(move || {
        // Root's fixed test-only hook takes this pair after duplicate=None,
        // before registration. No production/provider hook or fake reply.
        super::super::SELECTED_START_PRECHECK_PAUSE.with(|hook| {
            *hook.borrow_mut() = Some((entered_tx, release_rx));
        });
        let result = manager.selected_start(&lease, &models, epoch, true, &b_client, &b_token);
        super::super::SELECTED_START_PRECHECK_PAUSE.with(|hook| {
            hook.borrow_mut().take();
        });
        result
    });
    let entered = entered_rx.recv_timeout(Duration::from_secs(60));
    // Always release and join B, including a failed genuine A, before any
    // assertion can unwind. Only A uses the manager's registered worker.
    let attempt = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let a = if entered.is_ok() {
            f.manager
                .selected_start(&f.lease, &f.models, f.epoch, true, &client, &token)
        } else {
            Err("FixturePauseNotEntered".into())
        };
        let finished = if a.is_ok() {
            Some(f.done(&client))
        } else {
            None
        };
        if finished.is_some() {
            join_finished(&f);
        }
        (a, finished)
    }));
    release.now();
    let duplicate = b.join();
    let (a, finished) = match attempt {
        Ok(value) => value,
        Err(panic) => std::panic::resume_unwind(panic),
    };
    // Release all retained caps before complete Windows file inventory reads.
    f.manager
        .selected_close(&f.lease, f.epoch, &client)
        .unwrap();
    let source_after = inventory(source());
    let catalog = f.manager.selected_catalog(&f.lease, f.epoch, true).unwrap();
    assert!(entered.is_ok());
    let admitted = a.unwrap();
    let completed = finished.unwrap();
    assert_eq!(completed["phase"], "completed", "{completed}");
    let duplicate = duplicate
        .unwrap()
        .expect("completed exact duplicate must recover original identity, not Busy/Unknown");
    assert_eq!(duplicate["operation_id"], admitted["operation_id"]);
    assert_eq!(duplicate["run_id"], admitted["run_id"]);
    assert_eq!(duplicate["operation_id"], completed["operation_id"]);
    assert_eq!(duplicate["run_id"], completed["run_id"]);
    assert_eq!(duplicate["phase"], "completed");
    assert_eq!(catalog["runs"].as_array().unwrap().len(), 1);
    assert_eq!(source_after, source_before);
}
