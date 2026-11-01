// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Child of selected::tests.
//! Actual scripted V3 source and existing native manager/lease/consent APIs;
//! no model, OS picker, native IPC/WebView, accepted-history forgery or new hook.
use super::*;
use locallore::{
    inference::Cancellation,
    inspection_query::{self, Query, MAX_ROWS},
};
use locallore_eval::{
    local_lane::comparison::literal_v3, memory_comparison::frozen_suite,
    memory_comparison_v3::current_arm_descriptors as arm_descriptors,
};
use locallore_storage::Store;
use std::sync::{atomic::AtomicUsize, mpsc};

fn join(f: &Fixture) {
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
fn originals() -> &'static (PathBuf, PathBuf) {
    static SOURCES: OnceLock<(PathBuf, PathBuf)> = OnceLock::new();
    SOURCES.get_or_init(|| {
        let root =
            std::env::temp_dir().join(format!("selected2-native-consumer-{}", uuid().unwrap()));
        fs::create_dir(&root).unwrap();
        let first = root.join("first");
        let report = literal_v3::run_comparison(
            &first,
            false,
            producer::ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
        let second = root.join("second");
        copy_files(&first, &second);
        let report = literal_v3::run_comparison(
            &second,
            true,
            producer::ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!((report.completed_scenes, report.turns.len()), (2, 24));
        (first, second)
    })
}
fn copy_files(source: &Path, target: &Path) {
    let files = inventory(source);
    fs::create_dir(target).unwrap();
    for (p, b) in &files {
        match b {
            None => fs::create_dir_all(target.join(p)).unwrap(),
            Some(b) => fs::write(target.join(p), b).unwrap(),
        }
    }
    assert_eq!(inventory(target), files);
}
fn source3(second: bool) -> PathBuf {
    let p = std::env::temp_dir().join(format!("selected2-native-source-copy-{}", uuid().unwrap()));
    copy_files(
        if second {
            &originals().1
        } else {
            &originals().0
        },
        &p,
    );
    p
}
fn input3(f: &Fixture, client: &str, source: &Path) -> SelectedPrepareInput {
    let reader = uuid().unwrap();
    let picked = source.to_owned();
    f.manager
        .comparison_pick(&f.lease, f.epoch, true, &reader, move || Ok(Some(picked)))
        .unwrap();
    let until = Instant::now() + Duration::from_secs(60);
    let ready = loop {
        let status = f
            .manager
            .comparison_status(&f.lease, f.epoch, true, &reader)
            .unwrap();
        if status["running"] == false {
            break status;
        }
        assert!(Instant::now() < until);
        std::thread::sleep(Duration::from_millis(5));
    };
    join(f);
    assert_eq!(ready["phase"], "ready", "{ready}");
    SelectedPrepareInput {
        client_id: client.into(),
        reader_client_id: reader,
        run_token: ready["run_token"].as_str().unwrap().into(),
        binding: ready["binding"].as_str().unwrap().into(),
        turn_id: frozen_suite().unwrap().steps()[4].id().into(),
        arm: Arm::Left,
        lane: SelectedInputLane::ScriptedBaseline,
    }
}
fn prepare3(f: &Fixture, client: &str, source: &Path) -> Value {
    let input = input3(f, client, source);
    f.manager
        .selected_prepare(&f.lease, &f.models, f.epoch, true, input, |m| {
            assert_eq!(m["version"], 2);
            assert_eq!(m["source_protocol_version"], 3);
            assert_eq!(
                m["constructions"],
                serde_json::to_value(arm_descriptors()).unwrap()
            );
            assert!(m.get("request").is_none());
            Ok(true)
        })
        .unwrap();
    let prepared = f.done(client);
    join(f);
    assert_eq!(prepared["phase"], "prepared", "{prepared}");
    prepared
}
fn complete3(f: &Fixture, client: &str, source: &Path) -> (Value, Value, Value) {
    let prepared = prepare3(f, client, source);
    let started = f
        .manager
        .selected_start(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            client,
            prepared["plan_token"].as_str().unwrap(),
        )
        .unwrap();
    let completed = f.done(client);
    join(f);
    assert_eq!(completed["phase"], "completed", "{completed}");
    (prepared, started, completed)
}
fn work(f: &Fixture, run: &str) -> PathBuf {
    let (path, pins) = f.manager.selected_work_path(run).unwrap();
    drop(pins);
    path
}
fn open(f: &Fixture, client: &str, run: &str) -> SelectedReadInput {
    f.manager
        .selected_open(&f.lease, &f.models, f.epoch, true, (client, run), |m| {
            assert_eq!(m["version"], 2);
            assert_eq!(m["source_protocol_version"], 3);
            Ok(true)
        })
        .unwrap();
    let opened = f.done(client);
    join(f);
    assert_eq!(opened["phase"], "completed", "{opened}");
    SelectedReadInput {
        client_id: client.into(),
        run_token: opened["run_token"].as_str().unwrap().into(),
        binding: opened["binding"].as_str().unwrap().into(),
    }
}
fn close(f: &Fixture, client: &str) {
    f.manager.selected_close(&f.lease, f.epoch, client).unwrap();
    join(f);
}
fn reacquire3(path: &Path) {
    let cap = literal_v3::desktop_api::open_read_only(path).unwrap();
    literal_v3::desktop_api::summary(&cap, true).unwrap();
    drop(cap);
}
fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

#[test]
fn actual_v3_prepare2_start_index2_and_observer_reads_preserve_canon_and_source() {
    let f = Fixture::new();
    let source = source3(false);
    let source_before = inventory(&source);
    let client = uuid().unwrap();
    let (prepared, started, completed) = complete3(&f, &client, &source);
    let run = completed["run_id"].as_str().unwrap();
    let path = work(&f, run);
    let before = inventory(path.parent().unwrap());
    let index = value(&path.parent().unwrap().join("native.json"));
    assert_eq!(index["version"], 2);
    assert_eq!(index["prepared"], prepared["prepared"]);
    assert_eq!(index["prepared"]["source_protocol_version"], 3);
    for _ in 0..2 {
        let retry = f
            .manager
            .selected_start(
                &f.lease,
                &f.models,
                f.epoch,
                true,
                &client,
                prepared["plan_token"].as_str().unwrap(),
            )
            .unwrap();
        assert_eq!(retry["operation_id"], started["operation_id"]);
        assert_eq!(retry["run_id"], started["run_id"]);
    }
    assert_eq!(inventory(path.parent().unwrap()), before);
    let identity = open(&f, &client, run);
    let summary = f
        .manager
        .selected_summary(&f.lease, &f.models, f.epoch, true, identity.clone())
        .unwrap();
    join(&f);
    assert_eq!(summary["summary"]["version"], 2);
    assert_eq!(summary["summary"]["source_protocol_version"], 3);
    assert_eq!(
        summary["summary"]["constructions"],
        serde_json::to_value(arm_descriptors()).unwrap()
    );
    assert_eq!(summary["summary"]["execution_available"], false);
    let suite = frozen_suite().unwrap();
    let mut store = Store::open_read_only(&path.join("left/synthetic.sqlite")).unwrap();
    let full = store.resume(&suite.seed().scope).unwrap().engine;
    let receipt = store
        .lookup_turn(&suite.seed().scope, suite.steps()[4].id())
        .unwrap()
        .receipt
        .unwrap();
    let cut = full
        .at_revision(receipt.events().last().unwrap().sequence())
        .unwrap();
    for observer in [
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Character { id: "sable".into() },
    ] {
        let expected = inspection_query::query(
            &cut,
            &Query {
                version: 2,
                scope: cut.scope().clone(),
                expected_head: cut.revision(),
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
            .selected_evidence(
                &f.lease,
                &f.models,
                f.epoch,
                true,
                SelectedEvidenceInput {
                    identity: identity.clone(),
                    arm: Arm::Left,
                    request: EvidenceRequest::Query {
                        edge: Edge::After,
                        observer: observer.clone(),
                        view: View::History,
                    },
                },
            )
            .unwrap();
        join(&f);
        assert_eq!(
            actual["evidence"]["body"]["page"],
            serde_json::to_value(expected).unwrap()
        );
        assert_eq!(actual["evidence"]["generation_grant"], false);
        assert_eq!(
            f.manager
                .selected_evidence(
                    &f.lease,
                    &f.models,
                    f.epoch,
                    true,
                    SelectedEvidenceInput {
                        identity: identity.clone(),
                        arm: Arm::Left,
                        request: EvidenceRequest::Receipt { observer }
                    }
                )
                .unwrap_err(),
            "Forbidden"
        );
    }
    let accepted = f
        .manager
        .selected_evidence(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            SelectedEvidenceInput {
                identity: identity.clone(),
                arm: Arm::Left,
                request: EvidenceRequest::Receipt {
                    observer: Observer::Omniscient,
                },
            },
        )
        .unwrap();
    join(&f);
    assert_eq!(
        accepted["evidence"]["body"]["receipt"],
        serde_json::to_value(receipt).unwrap()
    );
    let diagnostics = f
        .manager
        .selected_diagnostics(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            identity.clone(),
            Observer::Omniscient,
        )
        .unwrap();
    join(&f);
    assert_eq!(diagnostics["diagnostics"]["version"], 2);
    assert_eq!(diagnostics["diagnostics"]["source_protocol_version"], 3);
    assert_eq!(
        diagnostics["diagnostics"]["rows"].as_array().unwrap().len(),
        2
    );
    drop(store);
    close(&f, &client);
    assert_eq!(
        f.manager
            .selected_summary(&f.lease, &f.models, f.epoch, true, identity)
            .unwrap_err(),
        "UnknownEvaluationRun"
    );
    assert_eq!(inventory(path.parent().unwrap()), before);
    reacquire3(&source);
    assert_eq!(inventory(&source), source_before);
    assert!(f.models.cleanup_complete());
}

#[test]
fn genuine_selected1_and_selected2_catalog_mix_survives_epoch_reopen_with_distinct_read_versions() {
    let mut f = Fixture::new();
    let source = source3(false);
    let before_source = inventory(&source);
    let new_client = uuid().unwrap();
    let (_, _, new) = complete3(&f, &new_client, &source);
    let new_run = new["run_id"].as_str().unwrap().to_owned();
    close(&f, &new_client);
    let old_client = uuid().unwrap();
    let prepared = f.prepare(&old_client);
    join(&f);
    f.manager
        .selected_start(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            &old_client,
            prepared["plan_token"].as_str().unwrap(),
        )
        .unwrap();
    let old = f.done(&old_client);
    join(&f);
    assert_eq!(old["phase"], "completed");
    let old_run = old["run_id"].as_str().unwrap().to_owned();
    close(&f, &old_client);
    let old_path = work(&f, &old_run);
    let new_path = work(&f, &new_run);
    assert_eq!(
        value(&old_path.parent().unwrap().join("native.json"))["version"],
        1
    );
    assert_eq!(
        value(&new_path.parent().unwrap().join("native.json"))["version"],
        2
    );
    let files = inventory(&f.manager.selected_root());
    let closed = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
    f.manager.retire(f.epoch);
    f.manager.drain(f.epoch);
    f.lease.finish_close(closed, || {});
    f.epoch = f.lease.begin().unwrap();
    let catalog = f.manager.selected_catalog(&f.lease, f.epoch, true).unwrap();
    let runs = catalog["runs"].as_array().unwrap();
    assert_eq!(runs.len(), 2);
    assert!(
        runs.iter().any(|r| r["run_id"] == new_run) && runs.iter().any(|r| r["run_id"] == old_run)
    );
    let client = uuid().unwrap();
    let identity = open(&f, &client, &new_run);
    let summary = f
        .manager
        .selected_summary(&f.lease, &f.models, f.epoch, true, identity)
        .unwrap();
    join(&f);
    assert_eq!(summary["summary"]["version"], 2);
    close(&f, &client);
    let client = uuid().unwrap();
    f.manager
        .selected_open(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            (&client, &old_run),
            |m| {
                assert_eq!(m["version"], 1);
                Ok(true)
            },
        )
        .unwrap();
    let opened = f.done(&client);
    join(&f);
    let identity = SelectedReadInput {
        client_id: client.clone(),
        run_token: opened["run_token"].as_str().unwrap().into(),
        binding: opened["binding"].as_str().unwrap().into(),
    };
    let summary = f
        .manager
        .selected_summary(&f.lease, &f.models, f.epoch, true, identity)
        .unwrap();
    join(&f);
    assert_eq!(summary["summary"]["version"], 1);
    close(&f, &client);
    assert_eq!(inventory(&f.manager.selected_root()), files);
    assert_eq!(inventory(&source), before_source);
}

#[test]
fn poisoned_index_version_protocol_or_exact_construction_refuses_before_consent_or_new_work() {
    let f = Fixture::new();
    let source = source3(false);
    let before_source = inventory(&source);
    let client = uuid().unwrap();
    let (_, _, completed) = complete3(&f, &client, &source);
    let run = completed["run_id"].as_str().unwrap();
    close(&f, &client);
    let path = work(&f, run);
    let index = path.parent().unwrap().join("native.json");
    let original = fs::read(&index).unwrap();
    for fault in 0..3 {
        let mut v: Value = serde_json::from_slice(&original).unwrap();
        match fault {
            0 => v["version"] = json!(1),
            1 => v["prepared"]["source_protocol_version"] = json!(2),
            _ => {
                v["prepared"]["constructions"][0]["prompt_version"] =
                    json!("unsupported-diagnostic-copy")
            }
        };
        fs::write(&index, serde_json::to_vec(&v).unwrap()).unwrap();
        let expected = inventory(&f.manager.selected_root());
        let calls = Arc::new(AtomicUsize::new(0));
        let seen = calls.clone();
        let opening = uuid().unwrap();
        let admitted = f.manager.selected_open(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            (&opening, run),
            move |_| {
                seen.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            },
        );
        let error = match admitted {
            Ok(_) => {
                let status = f.done(&opening);
                join(&f);
                status["error"].as_str().unwrap().to_owned()
            }
            Err(error) => error,
        };
        assert_eq!(error, "EvaluationIntegrity");
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        assert_eq!(inventory(&f.manager.selected_root()), expected);
        let _ = f.manager.selected_close(&f.lease, f.epoch, &opening);
        // Restore only the original owned diagnostic index, never canonical rows.
        fs::write(&index, &original).unwrap();
    }
    assert_eq!(
        f.manager.selected_catalog(&f.lease, f.epoch, true).unwrap()["runs"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    assert_eq!(inventory(&source), before_source);
    assert!(f.models.cleanup_complete());
}

#[test]
fn held_v3_execution_consent_cancel_or_retirement_cannot_publish_a_late_plan() {
    for retire in [false, true] {
        let mut f = Fixture::new();
        let source = source3(false);
        let before = inventory(&source);
        let client = uuid().unwrap();
        let input = input3(&f, &client, &source);
        let (entered, seen) = mpsc::sync_channel(1);
        let (release, wait) = mpsc::sync_channel(1);
        let pending = f
            .manager
            .selected_prepare(&f.lease, &f.models, f.epoch, true, input, move |m| {
                assert_eq!(m["version"], 2);
                entered.send(()).unwrap();
                wait.recv_timeout(Duration::from_secs(30)).unwrap();
                Ok(true)
            })
            .unwrap();
        seen.recv_timeout(Duration::from_secs(60)).unwrap();
        let busy = f.manager.start(&f.lease, f.epoch, None, "one");
        if retire {
            let closed = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
            f.manager.retire(f.epoch);
            release.send(()).unwrap();
            f.manager.drain(f.epoch);
            f.lease.finish_close(closed, || {});
            f.epoch = f.lease.begin().unwrap();
            assert_eq!(
                f.manager
                    .selected_status(&f.lease, f.epoch, true, &client)
                    .unwrap_err(),
                "UnknownEvaluationRun"
            );
        } else {
            let cancelled = f.manager.selected_cancel(
                &f.lease,
                f.epoch,
                true,
                &client,
                pending["operation_id"].as_u64().unwrap(),
            );
            release.send(()).unwrap();
            cancelled.unwrap();
            let result = f.done(&client);
            join(&f);
            assert_eq!(result["error"], "Cancelled");
            assert!(result["plan_token"].is_null() && result["run_id"].is_null());
            close(&f, &client);
        }
        assert_eq!(busy.unwrap_err(), "EvaluationBusy");
        reacquire3(&source);
        assert_eq!(inventory(&source), before);
        assert!(
            f.manager.selected_catalog(&f.lease, f.epoch, true).unwrap()["runs"]
                .as_array()
                .unwrap()
                .is_empty()
        );
        let fresh_client = uuid().unwrap();
        let fresh = prepare3(&f, &fresh_client, &source);
        assert_eq!(fresh["prepared"]["source_protocol_version"], 3);
        close(&f, &fresh_client);
        reacquire3(&source);
        assert_eq!(inventory(&source), before);
        drop(f.models.reserve_evaluation().unwrap());
    }
}

#[test]
fn genuine_different_v3_source_cannot_resume_completed_run_or_replace_model_reservation() {
    let f = Fixture::new();
    let source = source3(false);
    let different = source3(true);
    let before_source = inventory(&source);
    let before_different = inventory(&different);
    let client = uuid().unwrap();
    let (_, _, completed) = complete3(&f, &client, &source);
    let run = completed["run_id"].as_str().unwrap();
    let path = work(&f, run);
    let target_before = inventory(path.parent().unwrap());
    let identity = open(&f, &client, run);
    let supplied = input3(&f, &client, &different);
    let calls = Arc::new(AtomicUsize::new(0));
    let seen = calls.clone();
    let reservation = f.models.reserve_evaluation().unwrap();
    let pending = f.manager.selected_resume(
        &f.lease,
        &f.models,
        f.epoch,
        true,
        SelectedResumeInput {
            client_id: client.clone(),
            run_token: identity.run_token,
            reader_client_id: supplied.reader_client_id,
            source_token: supplied.run_token,
            source_binding: supplied.binding,
        },
        move |_| {
            seen.fetch_add(1, Ordering::SeqCst);
            Ok(true)
        },
    );
    let error = match pending {
        Ok(_) => {
            let status = f.done(&client);
            join(&f);
            status["error"].as_str().unwrap().to_owned()
        }
        Err(error) => error,
    };
    close(&f, &client);
    assert_eq!(error, "EvaluationSourceMismatch");
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert!(matches!(f.models.reserve_evaluation(), Err(error) if error == "Busy"));
    drop(reservation);
    assert!(f.models.cleanup_complete());
    assert_eq!(inventory(path.parent().unwrap()), target_before);
    reacquire3(&source);
    reacquire3(&different);
    assert_eq!(inventory(&source), before_source);
    assert_eq!(inventory(&different), before_different);
    // The replacement source is a genuine additional scripted scene, not a
    // corrupt/relabelled manifest. No native provider or asset path is invoked.
}
