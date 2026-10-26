// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Post-implementation independent source oracles at c3b31e4a. UNCOMPILED / UNRUN.
//! Actual service/shared scripted fixtures with native consent doubles only;
//! no OS dialog, IPC, WebView, native inference or model-quality evidence.
use super::*;
use crate::evaluation::ComparisonEvidenceRequest;
use locallore::inspection_query::{self, Observer, Query, View, MAX_ROWS};
use locallore_eval::{
    local_lane::comparison::desktop_api::{Arm, Edge, EvidenceRequest, RowId},
    memory_comparison::frozen_suite,
};
use locallore_storage::Store;
use std::sync::{
    atomic::{AtomicUsize, Ordering},
    mpsc,
};

fn read_done(f: &Fixture, client: &str) -> Value {
    let deadline = Instant::now() + Duration::from_secs(180);
    loop {
        let status = f
            .manager
            .comparison_status(&f.lease, f.epoch, true, client)
            .unwrap();
        if status["running"] == false {
            return status;
        }
        assert!(
            Instant::now() < deadline,
            "bounded managed-reader fixture wait"
        );
        std::thread::sleep(Duration::from_millis(5));
    }
}
fn managed(f: &Fixture, client: &str, run: &str) -> Value {
    f.manager
        .full_comparison_pick(&f.lease, f.epoch, true, client, run, || Ok(true))
        .unwrap();
    let status = read_done(f, client);
    assert_eq!(status["phase"], "ready", "{status}");
    status
}
fn close_read(f: &Fixture, client: &str, cap: Option<&str>) {
    let closed = f
        .manager
        .comparison_close(&f.lease, f.epoch, client, cap)
        .unwrap();
    assert_eq!(closed["phase"], "closed");
    assert!(closed["run_token"].is_null());
}
fn evidence(cap: &str, binding: &str, request: EvidenceRequest) -> ComparisonEvidenceRequest {
    ComparisonEvidenceRequest {
        token: cap.into(),
        binding: binding.into(),
        row: RowId {
            turn: "courier-01".into(),
            arm: Arm::Left,
        },
        request,
    }
}

#[test]
fn execution_capability_and_denied_or_closed_consent_never_become_reader_grants() {
    let (f, run, _) = copied();
    let opened = f.opened(&run);
    let execution = token(&opened).to_owned();
    let before = inventory(&f.root());
    refusal(
        f.manager
            .comparison_summary(&f.lease, f.epoch, true, &execution),
        "UnknownEvaluationRun",
    );

    let denied = uuid().unwrap();
    let calls = Arc::new(AtomicUsize::new(0));
    let count = calls.clone();
    f.manager
        .full_comparison_pick(&f.lease, f.epoch, true, &denied, &run, move || {
            count.fetch_add(1, Ordering::SeqCst);
            Ok(false)
        })
        .unwrap();
    let stopped = read_done(&f, &denied);
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    assert_eq!(stopped["phase"], "cancelled");
    assert!(stopped["run_token"].is_null());
    assert!(stopped["binding"].is_null());
    close_read(&f, &denied, None);

    let held = uuid().unwrap();
    let (entered, seen) = mpsc::sync_channel(1);
    let (release, wait) = mpsc::sync_channel(1);
    struct Release(Option<mpsc::SyncSender<()>>);
    impl Drop for Release {
        fn drop(&mut self) {
            if let Some(sender) = self.0.take() {
                let _ = sender.try_send(());
            }
        }
    }
    let release = Release(Some(release));
    f.manager
        .full_comparison_pick(&f.lease, f.epoch, true, &held, &run, move || {
            entered
                .send(())
                .map_err(|_| "EvaluationInternal".to_owned())?;
            wait.recv_timeout(Duration::from_secs(30))
                .map_err(|_| "EvaluationInternal".to_owned())?;
            Ok(true)
        })
        .unwrap();
    seen.recv_timeout(Duration::from_secs(5)).unwrap();
    let closing = f
        .manager
        .comparison_close(&f.lease, f.epoch, &held, None)
        .unwrap();
    drop(release);
    let closed = read_done(&f, &held);
    assert_eq!(closing["phase"], "closing");
    assert_eq!(closed["phase"], "closed");
    assert!(closed["run_token"].is_null());
    assert!(closed["binding"].is_null());
    refusal(
        f.manager
            .comparison_source(&f.lease, f.epoch, true, &execution),
        "UnknownEvaluationRun",
    );
    f.close(&execution);
    assert!(inventory(&f.root()) == before);
}

#[test]
fn managed_v3_actual_observer_queries_hold_read_lock_until_explicit_close_then_resume() {
    let (f, run, _) = copied();
    let opened = f.opened(&run);
    let execution = token(&opened).to_owned();
    let before = inventory(&f.root());
    let client = uuid().unwrap();
    let ready = managed(&f, &client, &run);
    let cap = token(&ready);
    let binding = ready["binding"].as_str().unwrap();
    assert_ne!(cap, execution);
    assert_eq!(ready["read_only"], true);
    assert_eq!(ready["execution_available"], false);
    let source = f
        .manager
        .comparison_source(&f.lease, f.epoch, true, cap)
        .unwrap();
    assert_eq!(source["source"]["protocol_version"], 3);
    assert_eq!(source["source"]["binding"], binding);
    let summary = f
        .manager
        .comparison_summary(&f.lease, f.epoch, true, cap)
        .unwrap();
    assert_eq!(summary["snapshot"]["report"]["version"], 3);
    assert_eq!(
        summary["snapshot"]["report"]["turns"]
            .as_array()
            .unwrap()
            .len(),
        12
    );

    let seed = frozen_suite().unwrap();
    let path = f.root().join(&run).join("work/left/synthetic.sqlite");
    let mut store = Store::open_read_only(&path).unwrap();
    let full = store.resume(&seed.seed().scope).unwrap().engine;
    let receipt = store
        .lookup_turn(&seed.seed().scope, "courier-01")
        .unwrap()
        .receipt
        .unwrap();
    let first = receipt.events().first().unwrap().sequence();
    let last = receipt.events().last().unwrap().sequence();
    for observer in [
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Character { id: "sable".into() },
    ] {
        for (edge, head) in [(Edge::Before, first - 1), (Edge::After, last)] {
            let cut = full.at_revision(head).unwrap();
            let expected = inspection_query::query(
                &cut,
                &Query {
                    version: 2,
                    scope: cut.scope().clone(),
                    expected_head: head,
                    at_revision: None,
                    observer: observer.clone(),
                    view: View::History,
                    cursor: None,
                    limit: MAX_ROWS,
                    search: String::new(),
                },
                true,
            )
            .unwrap();
            let actual = f
                .manager
                .comparison_evidence(
                    &f.lease,
                    f.epoch,
                    true,
                    evidence(
                        cap,
                        binding,
                        EvidenceRequest::Query {
                            edge,
                            observer: observer.clone(),
                            view: View::History,
                        },
                    ),
                )
                .unwrap();
            assert_eq!(
                actual["evidence"]["body"]["page"],
                serde_json::to_value(expected).unwrap()
            );
            assert_eq!(actual["evidence"]["generation_grant"], false);
        }
        for request in [
            EvidenceRequest::Receipt {
                observer: observer.clone(),
            },
            EvidenceRequest::Capture {
                observer: observer.clone(),
            },
            EvidenceRequest::Outputs { observer },
        ] {
            let mut invalid = evidence("not-a-private-token", "not-a-binding", request);
            invalid.row.turn = "unknown-turn".into();
            refusal(
                f.manager
                    .comparison_evidence(&f.lease, f.epoch, true, invalid),
                "Forbidden",
            );
        }
    }
    drop(store);
    // No whole-file inventory is read while the reader holds run.lock/pins.
    match f
        .manager
        .full_comparison_resume(&f.lease, f.epoch, true, &execution, 1)
    {
        Err(error) => assert_eq!(error, "EvaluationBusy"),
        Ok(start) => {
            let failed = f.done(token(&start));
            assert_eq!(failed["error"], "EvaluationBusy");
            assert_eq!(failed["running"], false);
        }
    }
    close_read(&f, &client, Some(cap));
    assert!(inventory(&f.root()) == before);
    f.manager
        .full_comparison_resume(&f.lease, f.epoch, true, &execution, 1)
        .unwrap();
    published(&f.done(&execution), 2, false);
    assert_eq!(report(&f, &run)["turns"].as_array().unwrap().len(), 24);
    f.close(&execution);
}

#[test]
fn malformed_identifiers_metadata_source_or_permission_refuse_before_native_consent() {
    for fault in ["permission", "client", "run", "index", "source"] {
        let (f, run, _) = copied();
        let client = uuid().unwrap();
        if matches!(fault, "index" | "source") {
            let path = f.root().join(&run).join(if fault == "index" {
                "desktop.json"
            } else {
                "work/run.json"
            });
            // Explicit hostile diagnostic-copy fault; no canonical state or
            // accepted receipt is authored, repaired or relabelled here.
            fs::write(path, b"{invalid owned diagnostic copy").unwrap();
        }
        let before = inventory(&f.root());
        let calls = Arc::new(AtomicUsize::new(0));
        let count = calls.clone();
        let result = f.manager.full_comparison_pick(
            &f.lease,
            f.epoch,
            fault != "permission",
            if fault == "client" {
                "../client"
            } else {
                &client
            },
            if fault == "run" { "../run" } else { &run },
            move || {
                count.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            },
        );
        refusal(
            result,
            match fault {
                "permission" => "Forbidden",
                "client" | "run" => "InvalidEvaluationInput",
                _ => "EvaluationIntegrity",
            },
        );
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        assert!(inventory(&f.root()) == before);
        assert!(f.manager.cleanup_complete());
    }
}
