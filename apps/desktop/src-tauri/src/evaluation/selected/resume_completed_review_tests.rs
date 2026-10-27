// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen real scripted service resume; SOURCE ONLY / UNCOMPILED / UNRUN.
//! Child of selected::tests. No fake checkpoint/profile/native inference/IPC.
use super::*;
use std::sync::atomic::AtomicUsize;

// Joining the actual admitted worker preserves the client/execution cache;
// drain() would revoke its capabilities. Never inventory an owned run.lock.
fn join(f: &Fixture) {
    let worker = {
        let _gate = f.manager.registration.lock().unwrap();
        f.manager.worker.lock().unwrap().take()
    };
    if let Some((epoch, worker)) = worker {
        assert_eq!(epoch, f.epoch);
        worker.join().unwrap();
    }
    assert!(f.manager.state().unwrap().job.is_none());
}
fn identity(client: &str, status: &Value) -> SelectedReadInput {
    SelectedReadInput {
        client_id: client.into(),
        run_token: status["run_token"].as_str().unwrap().into(),
        binding: status["binding"].as_str().unwrap().into(),
    }
}
fn inspect(f: &Fixture, client: &str, status: &Value) -> (Value, Value) {
    let input = identity(client, status);
    let summary = f
        .manager
        .selected_summary(&f.lease, &f.models, f.epoch, true, input.clone())
        .unwrap();
    join(f);
    let diagnostics = f
        .manager
        .selected_diagnostics(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            input,
            Observer::Omniscient,
        )
        .unwrap();
    join(f);
    (
        summary["summary"].clone(),
        diagnostics["diagnostics"].clone(),
    )
}

#[test]
fn completed_scripted_resume_refreshes_only_read_grant_and_denial_never_restarts_or_writes() {
    let fixture = Fixture::new();
    let source_before = inventory(fixture.source());
    let client = uuid().unwrap();
    let prepared = fixture.prepare(&client);
    join(&fixture);
    let original_token = prepared["plan_token"].as_str().unwrap().to_owned();
    let admitted = fixture
        .manager
        .selected_start(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            &client,
            &original_token,
        )
        .unwrap();
    let completed = fixture.done(&client);
    join(&fixture);
    assert_eq!(
        completed["phase"], "completed",
        "real scripted fixture must finish"
    );
    let run = completed["run_id"].as_str().unwrap().to_owned();
    let (work, pins) = fixture.manager.selected_work_path(&run).unwrap();
    drop(pins);
    let run_directory = work.parent().unwrap().to_owned();
    let before = inventory(&run_directory);
    let catalog_before = fixture
        .manager
        .selected_catalog(&fixture.lease, fixture.epoch, true)
        .unwrap();
    fixture
        .manager
        .selected_open(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            (&client, &run),
            |_| Ok(true),
        )
        .unwrap();
    let opened = fixture.done(&client);
    join(&fixture);
    let (summary_before, diagnostics_before) = inspect(&fixture, &client, &opened);

    // Hold a real metadata reservation throughout resume. A cached scripted
    // workflow must not acquire/replace ModelManager ownership or need assets.
    // This is not a new native model run or a native cached-resume claim.
    let model_reservation = fixture.models.reserve_evaluation().unwrap();
    let fresh = fixture.input(&client);
    let transferred_reader = fresh.reader_client_id.clone();
    let transferred_token = fresh.run_token.clone();
    let consent_calls = Arc::new(AtomicUsize::new(0));
    let observed = consent_calls.clone();
    let pending = fixture
        .manager
        .selected_resume(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            SelectedResumeInput {
                client_id: client.clone(),
                run_token: opened["run_token"].as_str().unwrap().into(),
                reader_client_id: fresh.reader_client_id,
                source_token: fresh.run_token,
                source_binding: fresh.binding,
            },
            move |metadata| {
                assert_eq!(metadata["kind"], "selected_prepared");
                observed.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            },
        )
        .unwrap();
    let resumed = fixture.done(&client);
    join(&fixture);
    let (summary_after, diagnostics_after) = inspect(&fixture, &client, &resumed);
    let before_retry = fixture.status(&client);
    let original_retry = fixture.manager.selected_start(
        &fixture.lease,
        &fixture.models,
        fixture.epoch,
        true,
        &client,
        &original_token,
    );
    let after_retry = fixture.status(&client);
    let transferred_close = fixture.manager.comparison_close(
        &fixture.lease,
        fixture.epoch,
        &transferred_reader,
        Some(&transferred_token),
    );

    // A second fresh, genuine source cap reaches negative native consent.
    // It must not run/rewrite either completed arm or allocate another run.
    let fresh = fixture.input(&client);
    let denied_reader = fresh.reader_client_id.clone();
    let denied_token = fresh.run_token.clone();
    let denied_calls = Arc::new(AtomicUsize::new(0));
    let observed = denied_calls.clone();
    fixture
        .manager
        .selected_resume(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            SelectedResumeInput {
                client_id: client.clone(),
                run_token: resumed["run_token"].as_str().unwrap().into(),
                reader_client_id: fresh.reader_client_id,
                source_token: fresh.run_token,
                source_binding: fresh.binding,
            },
            move |metadata| {
                assert_eq!(metadata["kind"], "selected_prepared");
                observed.fetch_add(1, Ordering::SeqCst);
                Ok(false)
            },
        )
        .unwrap();
    let denied = fixture.done(&client);
    join(&fixture);
    let denied_close = fixture.manager.comparison_close(
        &fixture.lease,
        fixture.epoch,
        &denied_reader,
        Some(&denied_token),
    );
    let catalog_after = fixture
        .manager
        .selected_catalog(&fixture.lease, fixture.epoch, true)
        .unwrap();
    let model_still_owned =
        matches!(fixture.models.reserve_evaluation(),Err(error) if error=="Busy");
    drop(model_reservation);
    fixture
        .manager
        .selected_close(&fixture.lease, fixture.epoch, &client)
        .unwrap();
    join(&fixture);
    fixture.manager.drain(fixture.epoch);
    // All actual read capabilities, source plans, workers and pins are now
    // released before the complete file/empty-directory comparison.
    let after = inventory(&run_directory);
    let source_after = inventory(fixture.source());
    let models_clean = fixture.models.cleanup_complete();
    drop(fixture);

    assert_eq!(
        after, before,
        "completed resume/denial/inert retry are byte-read-only for the entire run"
    );
    assert_eq!(
        source_after, source_before,
        "genuine source remains byte-identical"
    );
    assert_eq!(
        catalog_after, catalog_before,
        "no new durable run/envelope was allocated"
    );
    assert_eq!(resumed["phase"], "completed");
    assert_eq!(resumed["run_id"], run);
    assert_eq!(resumed["operation_id"], pending["operation_id"]);
    assert_ne!(resumed["operation_id"], admitted["operation_id"]);
    assert_ne!(
        resumed["run_token"], opened["run_token"],
        "same run receives a fresh read capability"
    );
    assert_eq!(resumed["binding"], opened["binding"]);
    assert_eq!(
        summary_after, summary_before,
        "both original scopes/heads and snapshot binding stay equal"
    );
    assert_eq!(
        diagnostics_after, diagnostics_before,
        "no new roles/admissions/setup/cost or altered outcome"
    );
    assert_eq!(diagnostics_after["lane"], "scripted_selected_case");
    assert_eq!(diagnostics_after["physical_setups"], 0);
    assert_eq!(diagnostics_after["human_reviewed"], 0);
    assert_eq!(diagnostics_after["quality_accepted"], false);
    assert_eq!(consent_calls.load(Ordering::SeqCst), 1);
    let original_retry =
        original_retry.expect("original admitted start token remains inert after resume");
    assert_eq!(original_retry["operation_id"], admitted["operation_id"]);
    assert_eq!(original_retry["run_id"], admitted["run_id"]);
    assert_eq!(original_retry["run_token"], Value::Null);
    assert_eq!(original_retry["binding"], Value::Null);
    assert_eq!(
        after_retry, before_retry,
        "inert old execution receipt cannot change current read operation"
    );
    assert_eq!(denied_calls.load(Ordering::SeqCst), 1);
    assert_eq!(denied["error"], "Cancelled");
    assert_eq!(denied["run_id"], run);
    assert_eq!(denied["cleanup_required"], false);
    assert!(transferred_close.is_ok() && denied_close.is_ok());
    assert!(model_still_owned && models_clean);
}
