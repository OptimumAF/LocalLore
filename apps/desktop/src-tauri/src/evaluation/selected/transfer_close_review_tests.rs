// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen source-transfer close/epoch collision oracle; SOURCE UNRUN.
//! Root registers as child of selected::tests. No ordinary same-client repick
//! contract is changed: only a genuine native window retirement permits reuse.
use super::*;
use std::sync::atomic::AtomicBool;

fn reader_done(fixture: &Fixture, client: &str) -> Value {
    let until = Instant::now() + Duration::from_secs(60);
    loop {
        let value = fixture
            .manager
            .comparison_status(&fixture.lease, fixture.epoch, true, client)
            .unwrap();
        if value["running"] == false {
            return value;
        }
        assert!(Instant::now() < until, "bounded actual reader fixture");
        std::thread::sleep(Duration::from_millis(5));
    }
}

#[test]
fn transferred_empty_reader_close_is_harmless_but_old_token_cannot_close_new_epoch_capability() {
    let mut fixture = Fixture::new();
    let before = inventory(fixture.source());
    let selected_client = uuid().unwrap();
    let input = fixture.input(&selected_client);
    let reader = input.reader_client_id.clone();
    let old_token = input.run_token.clone();
    fixture
        .manager
        .selected_prepare(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            input,
            |_| Ok(true),
        )
        .unwrap();
    let prepared = fixture.done(&selected_client);
    // Collect the behavior under review before asserting it, so its baseline
    // failure cannot skip native retirement, pin release or the final inventory.
    let transferred_close =
        fixture
            .manager
            .comparison_close(&fixture.lease, fixture.epoch, &reader, Some(&old_token));
    let selected_after = fixture.status(&selected_client);
    let old_source =
        fixture
            .manager
            .comparison_source(&fixture.lease, fixture.epoch, true, &old_token);
    let catalog = fixture
        .manager
        .selected_catalog(&fixture.lease, fixture.epoch, true)
        .unwrap();
    let invoked = Arc::new(AtomicBool::new(false));
    let observed = invoked.clone();
    let source_path = fixture.source().to_path_buf();
    let same_epoch_pick =
        fixture
            .manager
            .comparison_pick(&fixture.lease, fixture.epoch, true, &reader, move || {
                observed.store(true, Ordering::SeqCst);
                Ok(Some(source_path))
            });
    let same_epoch_invoked = invoked.load(Ordering::SeqCst);

    // Actual native lifecycle, not a renderer-supplied epoch or fabricated cap.
    // This releases the selected plan/source lock before reopening that source.
    let old_epoch = fixture.epoch;
    let closed = fixture
        .lease
        .invalidate(&format!("main-{old_epoch}"))
        .unwrap();
    fixture.manager.retire(old_epoch);
    fixture.manager.drain(old_epoch);
    assert!(
        fixture.models.cleanup_complete(),
        "model-free fixture has no child/startup/owner"
    );
    fixture.lease.finish_close(closed, || {});
    fixture.epoch = fixture.lease.begin().unwrap();
    let source_path = fixture.source().to_path_buf();
    fixture
        .manager
        .comparison_pick(&fixture.lease, fixture.epoch, true, &reader, move || {
            Ok(Some(source_path))
        })
        .unwrap();
    let fresh = reader_done(&fixture, &reader);
    let fresh_token = fresh["run_token"]
        .as_str()
        .expect("genuine fresh reader capability")
        .to_owned();
    let stale_close =
        fixture
            .manager
            .comparison_close(&fixture.lease, fixture.epoch, &reader, Some(&old_token));
    let fresh_after_stale = fixture
        .manager
        .comparison_status(&fixture.lease, fixture.epoch, true, &reader)
        .unwrap();
    let fresh_source =
        fixture
            .manager
            .comparison_source(&fixture.lease, fixture.epoch, true, &fresh_token);
    let query = if let Ok(metadata) = &fresh_source {
        let turn = metadata["source"]["rows"][0]["row"]["turn"]
            .as_str()
            .unwrap()
            .to_owned();
        Some(fixture.manager.comparison_evidence(
            &fixture.lease,
            fixture.epoch,
            true,
            crate::evaluation::ComparisonEvidenceRequest {
                token: fresh_token.clone(),
                binding: fresh["binding"].as_str().unwrap().into(),
                row: source_reader::RowId {
                    turn,
                    arm: Arm::Left,
                },
                request: EvidenceRequest::Query {
                    edge: Edge::Before,
                    observer: Observer::Player,
                    view: View::History,
                },
            },
        ))
    } else {
        None
    };
    let old_epoch_close =
        fixture
            .manager
            .comparison_close(&fixture.lease, old_epoch, &reader, Some(&old_token));
    let correct_close = fixture.manager.comparison_close(
        &fixture.lease,
        fixture.epoch,
        &reader,
        Some(&fresh_token),
    );
    fixture.manager.drain(fixture.epoch);
    let after = inventory(fixture.source());
    drop(fixture);

    assert_eq!(
        after, before,
        "actual source files/directories remain byte-identical"
    );
    let closed = transferred_close
        .expect("transferred empty closed reader accepts old close token harmlessly");
    assert_eq!(closed["phase"], "closed");
    assert_eq!(closed["run_token"], Value::Null);
    assert_eq!(closed["binding"], Value::Null);
    assert_eq!(closed["running"], false);
    assert_eq!(prepared["phase"], "prepared");
    assert_eq!(selected_after["phase"], "prepared");
    assert_eq!(selected_after["plan_token"], prepared["plan_token"]);
    assert_ne!(selected_after["plan_token"], Value::Null);
    assert_eq!(selected_after["prepared"], prepared["prepared"]);
    assert_eq!(selected_after["run_id"], Value::Null);
    assert_eq!(
        catalog["runs"].as_array().unwrap().len(),
        0,
        "no selected start/target was admitted"
    );
    assert!(matches!(old_source,Err(error) if error=="UnknownEvaluationRun"));
    let repeated = same_epoch_pick.unwrap();
    assert_eq!(repeated["phase"], "closed");
    assert_eq!(repeated["run_token"], Value::Null);
    assert!(!same_epoch_invoked);
    assert_ne!(fresh_token, old_token);
    assert!(matches!(stale_close,Err(error) if error=="UnknownEvaluationRun"));
    assert_eq!(fresh_after_stale["phase"], "ready");
    assert_eq!(fresh_after_stale["run_token"], fresh_token);
    assert!(fresh_source.is_ok());
    let query = query
        .expect("fresh source row exists")
        .expect("actual observer query remains usable");
    assert_eq!(query["evidence"]["body"]["kind"], "query");
    assert!(matches!(old_epoch_close,Err(error) if error=="Closed"));
    let closed = correct_close.unwrap();
    assert_eq!(closed["phase"], "closed");
    assert_eq!(closed["run_token"], Value::Null);
}
