// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST after 988d425f: UNREGISTERED/UNCOMPILED/UNFORMATTED/UNRUN.
//! Child of selected::tests. Actual public scripted Scene4 and native manager
//! APIs only: no IPC/WebView, model, OS picker, process restart or new test hook.
//! Consent channels are synthetic decisions; discarded Start replies simulate
//! acknowledgement loss. Failed fixtures are retained without automatic cleanup.
use super::*;
use locallore::{inspection_query::{self, Query, MAX_ROWS}, contracts::Receipt};
use locallore_eval::{local_lane::comparison::scene_v4, memory_comparison::frozen_suite,
    memory_comparison_v4::arm_descriptors};
use locallore_storage::Store;
use std::{io::Write, sync::{atomic::AtomicUsize, mpsc}};

const SELECTED_INDEX: usize = 4;
const ARM_NAMES4: [&str; 2] = ["left", "right"];
const SECRET4: &str = "SECRET-TIDE-731";

fn root4(label: &str) -> PathBuf {
    // Root's local runner enforces physical D and supplies this dedicated parent.
    // Other CI remains portable; no universal Windows drive requirement.
    let parent = std::env::var_os("LOCALLORE_SELECTED_SCENE4_NATIVE_TEST_ROOT")
        .map(PathBuf::from).unwrap_or_else(std::env::temp_dir);
    assert!(parent.is_absolute() && parent.is_dir());
    let parent = fs::canonicalize(parent).unwrap();
    for ancestor in parent.ancestors() {
        let info = fs::symlink_metadata(ancestor).unwrap();
        assert!(info.is_dir() && !info.file_type().is_symlink());
        #[cfg(windows)] {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(info.file_attributes() & 0x400, 0);
        }
    }
    let path = parent.join(format!("selected-scene4-manager-{label}-{}", uuid().unwrap()));
    fs::create_dir(&path).unwrap(); path
}
fn copy4(source: &Path, target: &Path) {
    let original = inventory(source);
    fs::create_dir(target).unwrap();
    for (relative, bytes) in &original {
        let path = target.join(relative);
        match bytes {
            None => fs::create_dir_all(path).unwrap(),
            Some(bytes) => {
                let mut file = OpenOptions::new().write(true).create_new(true).open(path).unwrap();
                file.write_all(bytes).unwrap(); file.sync_all().unwrap();
            }
        }
    }
    assert_eq!(inventory(target), original);
}
fn original4(kind: producer::ComparisonKind) -> &'static Path {
    static PAIRED: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    static ROLLOUT: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    let slot = match kind { producer::ComparisonKind::PairedSnapshots => &PAIRED,
        producer::ComparisonKind::ContinuousRollout => &ROLLOUT };
    slot.get_or_init(|| std::panic::catch_unwind(|| {
        let root = root4("closed-source");
        let reference = if kind == producer::ComparisonKind::PairedSnapshots {
            let path = root.join("reference-owner");
            producer::prepare_reference(&path, &Cancellation::default()).unwrap();
            Some(producer::open_reference(&path).unwrap())
        } else { None };
        let source = root.join("source");
        let report = scene_v4::run_comparison(&source, false, kind, &Cancellation::default(),
            1, LaneFactory::ScriptedBaseline, reference.as_ref()).unwrap();
        assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
        assert_eq!(report.arms, arm_descriptors());
        assert_eq!(scene_v4::inspect_comparison(&source).unwrap(), report);
        source
    }).map_err(|_| ())).as_ref()
        .expect("original public Scene4 source failed; retain it, never generate a replacement")
        .as_path()
}
fn fixture4(kind: producer::ComparisonKind) -> Fixture {
    let root = root4("fixture"); let source = root.join("source");
    copy4(original4(kind), &source);
    let lease = Arc::new(WindowLease::default()); let epoch = lease.begin().unwrap();
    let manager = Arc::new(EvaluationManager::new(root.join("evaluations")));
    manager.catalog(&lease, epoch).unwrap();
    Fixture { manager, lease, epoch, source,
        models: Arc::new(ModelManager::new(root.join("models"), root.join("resources"))) }
}
fn join4(f: &Fixture) {
    // Preserve consumed-operation receipts; drain would remove presentation.
    let worker = { let _gate = f.manager.registration.lock().unwrap();
        f.manager.worker.lock().unwrap().take() };
    if let Some((epoch, worker)) = worker { assert_eq!(epoch, f.epoch); worker.join().unwrap(); }
    assert!(f.manager.state().unwrap().job.is_none());
}
fn read4(path: &Path) -> Value { serde_json::from_slice(&fs::read(path).unwrap()).unwrap() }
fn work4(f: &Fixture, run: &str) -> PathBuf {
    let (path, pins) = f.manager.selected_work_path(run).unwrap(); drop(pins); path
}
fn catalog4(f: &Fixture) -> Value {
    f.manager.selected_catalog(&f.lease, f.epoch, true).unwrap()
}
fn close4(f: &Fixture, client: &str) {
    f.manager.selected_close(&f.lease, f.epoch, client).unwrap(); join4(f);
}
fn source_input4(f: &Fixture, client: &str, path: &Path) -> SelectedPrepareInput {
    let reader = uuid().unwrap(); let picked = path.to_owned();
    f.manager.comparison_pick(&f.lease, f.epoch, true, &reader, move || Ok(Some(picked))).unwrap();
    let deadline = Instant::now() + Duration::from_secs(60);
    let ready = loop {
        let status = f.manager.comparison_status(&f.lease, f.epoch, true, &reader).unwrap();
        if status["running"] == false { break status; }
        assert!(Instant::now() < deadline, "bounded actual Scene4 reader: {status}");
        std::thread::sleep(Duration::from_millis(5));
    };
    join4(f); assert_eq!(ready["phase"], "ready", "{ready}");
    let token = ready["run_token"].as_str().unwrap();
    let metadata = f.manager.comparison_source(&f.lease, f.epoch, true, token).unwrap();
    assert_eq!(metadata["source"]["protocol_version"], 4);
    let turn = metadata["source"]["rows"].as_array().unwrap().iter()
        .filter(|row| row["row"]["arm"] == "left").nth(SELECTED_INDEX).unwrap()
        ["row"]["turn"].as_str().unwrap().to_owned();
    assert_eq!(turn, frozen_suite().unwrap().steps()[SELECTED_INDEX].id());
    SelectedPrepareInput { client_id: client.into(), reader_client_id: reader,
        run_token: token.into(), binding: ready["binding"].as_str().unwrap().into(),
        turn_id: turn, arm: Arm::Right, lane: SelectedInputLane::ScriptedBaseline }
}
fn duplicate_input4(input: &SelectedPrepareInput) -> SelectedPrepareInput {
    SelectedPrepareInput { client_id: input.client_id.clone(), reader_client_id: input.reader_client_id.clone(),
        run_token: input.run_token.clone(), binding: input.binding.clone(), turn_id: input.turn_id.clone(),
        arm: input.arm, lane: input.lane }
}
fn prepare4(f: &Fixture, client: &str) -> Value {
    let input = source_input4(f, client, f.source()); let binding = input.binding.clone();
    f.manager.selected_prepare(&f.lease, &f.models, f.epoch, true, input, move |m| {
        assert_eq!(m["version"], 3); assert_eq!(m["source_protocol_version"], 4);
        assert_eq!(m["source_binding"], binding); assert_eq!(m["selection"]["index"], SELECTED_INDEX);
        assert_eq!(m["selection"]["clicked_arm"], "right");
        assert_eq!(m["constructions"], serde_json::to_value(arm_descriptors()).unwrap());
        assert_eq!(m["lane"], "scripted_selected_case"); Ok(true)
    }).unwrap();
    let ready = f.done(client); join4(f); assert_eq!(ready["phase"], "prepared", "{ready}"); ready
}
fn complete4(f: &Fixture, client: &str) -> (Value, Value, Value) {
    let prepared = prepare4(f, client);
    let started = f.manager.selected_start(&f.lease, &f.models, f.epoch, true, client,
        prepared["plan_token"].as_str().unwrap()).unwrap();
    let finished = f.done(client); join4(f);
    assert_eq!(finished["phase"], "completed", "{finished}"); (prepared, started, finished)
}
fn open4(f: &Fixture, client: &str, run: &str) -> SelectedReadInput {
    f.manager.selected_open(&f.lease, &f.models, f.epoch, true, (client, run), |m| {
        assert_eq!(m["version"], 3); assert_eq!(m["source_protocol_version"], 4);
        assert_eq!(m["constructions"], serde_json::to_value(arm_descriptors()).unwrap());
        assert_eq!(m["read_only"], true); assert_eq!(m["execution_available"], false); Ok(true)
    }).unwrap();
    let ready = f.done(client); join4(f); assert_eq!(ready["phase"], "completed", "{ready}");
    SelectedReadInput { client_id: client.into(), run_token: ready["run_token"].as_str().unwrap().into(),
        binding: ready["binding"].as_str().unwrap().into() }
}
fn database4(root: &Path, arm: &str, kind: producer::ComparisonKind) -> PathBuf {
    root.join(arm).join(match kind { producer::ComparisonKind::PairedSnapshots => format!("pair-{SELECTED_INDEX:02}.sqlite"),
        producer::ComparisonKind::ContinuousRollout => "synthetic.sqlite".into() })
}
fn resume_input4(client: &str, read: &SelectedReadInput, source: SelectedPrepareInput) -> SelectedResumeInput {
    SelectedResumeInput { client_id: client.into(), run_token: read.run_token.clone(),
        reader_client_id: source.reader_client_id, source_token: source.run_token, source_binding: source.binding }
}
fn source_released4(f: &Fixture, expected: &Inventory) {
    let cap = scene_v4::desktop_api::open_read_only(f.source()).unwrap();
    assert_eq!(scene_v4::desktop_api::summary(&cap, true).unwrap()["protocol_version"], 4);
    drop(cap); assert_eq!(&inventory(f.source()), expected);
}

#[test]
fn actual_scene4_paired_and_rollout_noninitial_prepare_start_and_observer_reads_keep_original_inputs() {
    for kind in [producer::ComparisonKind::PairedSnapshots, producer::ComparisonKind::ContinuousRollout] {
        let f = fixture4(kind); let source_before = inventory(f.source()); let client = uuid().unwrap();
        let other_owner = f.models.reserve_evaluation().unwrap();
        let prepared = prepare4(&f, &client);
        assert!(catalog4(&f)["runs"].as_array().unwrap().is_empty());
        assert!(!f.manager.selected_root().exists(), "prepare is not Start");
        let token = prepared["plan_token"].as_str().unwrap();
        let started = f.manager.selected_start(&f.lease, &f.models, f.epoch, true, &client, token).unwrap();
        let retry = f.manager.selected_start(&f.lease, &f.models, f.epoch, true, &client, token).unwrap();
        assert_eq!(retry["operation_id"], started["operation_id"]); assert_eq!(retry["run_id"], started["run_id"]);
        let finished = f.done(&client); join4(&f); assert_eq!(finished["phase"], "completed", "{finished}");
        assert!(finished["run_token"].is_null() && finished["binding"].is_null(), "execution is not inspection consent");
        let run = finished["run_id"].as_str().unwrap().to_owned(); let work = work4(&f, &run);
        let run_before = inventory(work.parent().unwrap());
        let index = read4(&work.parent().unwrap().join("native.json"));
        assert_eq!(index["version"], 3); assert_eq!(index["source_binding"], prepared["prepared"]["source_binding"]);
        assert_eq!(index["prepared"], prepared["prepared"]);
        let report = read4(&work.join("report.json"));
        assert_eq!(report["version"], 3); assert_eq!(report["source_protocol_version"], 4);
        assert_eq!(report["constructions"], Value::Null); assert_eq!(report["arms"], serde_json::to_value(arm_descriptors()).unwrap());
        for (n, arm) in ARM_NAMES4.iter().copied().enumerate() {
            let source_cp = read4(&f.source().join(arm).join(format!("attempt-{SELECTED_INDEX:02}.json")));
            let actual = read4(&work.join(arm).join(format!("attempt-{SELECTED_INDEX:02}.json")));
            assert_eq!(actual["version"], 4); assert_eq!(actual["request"], source_cp["request"]);
            assert_eq!(actual["before_head"], source_cp["before_head"]);
            assert_eq!(prepared["prepared"]["arms"][n]["before_head"], actual["before_head"]);
            assert!(!work.join(arm).join("attempt-00.json").exists());
            let mut source = Store::open_read_only(&database4(f.source(), arm, kind)).unwrap();
            let source = source.resume(&frozen_suite().unwrap().seed().scope).unwrap().engine;
            let mut target = Store::open_read_only(&database4(&work, arm, kind)).unwrap();
            let actual_engine = target.resume(source.scope()).unwrap().engine;
            let before = actual_engine.at_revision(actual["before_head"].as_u64().unwrap()).unwrap();
            assert_eq!(before.receipts(), source.at_revision(before.revision()).unwrap().receipts());
            assert_eq!(locallore_eval::digest(&serde_json::to_vec(before.receipts()).unwrap()),
                prepared["prepared"]["arms"][n]["prefix_sha256"]);
            let accepted: Receipt = target.lookup_turn(source.scope(), frozen_suite().unwrap().steps()[SELECTED_INDEX].id()).unwrap().receipt.unwrap();
            assert_eq!(serde_json::to_value(accepted.request()).unwrap(), actual["request"]);
            assert_eq!(actual["row"]["actual_receipt_sha256"], locallore_eval::digest(&serde_json::to_vec(&accepted).unwrap()));
        }
        // Discarding the returned Start value is a lost-ack simulation, not IPC.
        for _ in 0..2 {
            let retry = f.manager.selected_start(&f.lease, &f.models, f.epoch, true, &client, token).unwrap();
            assert_eq!(retry["operation_id"], started["operation_id"]); assert_eq!(retry["run_id"], started["run_id"]);
        }
        assert_eq!(inventory(work.parent().unwrap()), run_before);
        let identity = open4(&f, &client, &run);
        assert_ne!(identity.binding, prepared["prepared"]["binding"].as_str().unwrap());
        assert_ne!(identity.binding, prepared["prepared"]["source_binding"].as_str().unwrap());
        for (arm, name) in [(Arm::Left, "left"), (Arm::Right, "right")] {
            let checkpoint = read4(&work.join(name).join(format!("attempt-{SELECTED_INDEX:02}.json")));
            let mut store = Store::open_read_only(&database4(&work, name, kind)).unwrap();
            let full = store.resume(&frozen_suite().unwrap().seed().scope).unwrap().engine; drop(store);
            for (edge, field) in [(Edge::Before, "before_head"), (Edge::After, "after_head")] {
                let cut = full.at_revision(checkpoint[field].as_u64().unwrap()).unwrap();
                for observer in [Observer::Player, Observer::Character { id: "mira".into() }, Observer::Character { id: "sable".into() }] {
                    let expected = inspection_query::query(&cut, &Query { version: 2, scope: cut.scope().clone(),
                        expected_head: cut.revision(), at_revision: None, observer: observer.clone(), view: View::History,
                        cursor: None, limit: MAX_ROWS, search: String::new() }, true).unwrap();
                    let actual = f.manager.selected_evidence(&f.lease, &f.models, f.epoch, true, SelectedEvidenceInput {
                        identity: identity.clone(), arm, request: EvidenceRequest::Query { edge, observer, view: View::History } }).unwrap();
                    join4(&f); assert_eq!(actual["evidence"]["body"]["page"], serde_json::to_value(expected).unwrap());
                    assert_eq!(actual["evidence"]["generation_grant"], false);
                    assert!(!actual["evidence"].to_string().contains(SECRET4));
                }
            }
            for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
                let expected = inspection_query::query(&full, &Query { version: 2, scope: full.scope().clone(),
                    expected_head: full.revision(), at_revision: None, observer: observer.clone(), view: View::Knowledge,
                    cursor: None, limit: MAX_ROWS, search: String::new() }, true).unwrap();
                let actual = f.manager.selected_evidence(&f.lease, &f.models, f.epoch, true, SelectedEvidenceInput {
                    identity: identity.clone(), arm, request: EvidenceRequest::Query { edge: Edge::After,
                        observer: observer.clone(), view: View::Knowledge } }).unwrap();
                join4(&f); assert_eq!(actual["evidence"]["body"]["page"], serde_json::to_value(expected).unwrap());
                if matches!(observer, Observer::Player) {
                    let fact = &full.seed().facts["relic-location"];
                    assert!(fact.known_by.contains(&full.seed().player));
                    assert!(actual["evidence"]["body"]["page"]["rows"].as_array().unwrap().iter()
                        .any(|row| row["kind"] == "knowledge" && row["id"] == "relic-location"
                            && row["subject"].as_str() == Some(full.seed().player.as_str())
                            && row["text"].as_str() == Some(fact.proposition.as_str())));
                } else { assert!(!actual["evidence"].to_string().contains(SECRET4)); }
            }
            let mut store = Store::open_read_only(&database4(&work, name, kind)).unwrap();
            let receipt = store.lookup_turn(full.scope(), frozen_suite().unwrap().steps()[SELECTED_INDEX].id()).unwrap().receipt.unwrap();
            drop(store);
            let accepted = f.manager.selected_evidence(&f.lease, &f.models, f.epoch, true, SelectedEvidenceInput {
                identity: identity.clone(), arm, request: EvidenceRequest::Receipt { observer: Observer::Omniscient } }).unwrap();
            join4(&f); assert_eq!(accepted["evidence"]["body"]["receipt"], serde_json::to_value(receipt).unwrap());
        }
        let diagnostics = f.manager.selected_diagnostics(&f.lease, &f.models, f.epoch, true, identity, Observer::Omniscient).unwrap();
        join4(&f); let diagnostics = &diagnostics["diagnostics"];
        assert_eq!(diagnostics["version"], 3); assert_eq!(diagnostics["source_protocol_version"], 4);
        assert_eq!(diagnostics["constructions"], serde_json::to_value(arm_descriptors()).unwrap());
        assert_eq!(diagnostics["human_reviewed"], 0); assert_eq!(diagnostics["human_rubric"], "not_reviewed");
        assert_eq!(diagnostics["quality_accepted"], false); assert_eq!(diagnostics["rows"].as_array().unwrap().len(), 2);
        assert!(diagnostics["rows"].as_array().unwrap().iter().all(|row| row.get("privacy_passed").is_none()));
        close4(&f, &client); assert_eq!(inventory(work.parent().unwrap()), run_before);
        assert_eq!(catalog4(&f)["runs"].as_array().unwrap().len(), 1);
        assert!(matches!(f.models.reserve_evaluation(), Err(error) if error == "Busy"));
        drop(other_owner); assert!(f.models.cleanup_complete()); source_released4(&f, &source_before);
    }
}

#[test]
fn source4_native_lane_refuses_before_consent_or_target_with_another_real_model_owner() {
    for kind in [producer::ComparisonKind::PairedSnapshots, producer::ComparisonKind::ContinuousRollout] {
        let f = fixture4(kind); let before = inventory(f.source()); let client = uuid().unwrap();
        let mut input = source_input4(&f, &client, f.source()); input.lane = SelectedInputLane::ApprovedNative;
        let token = input.run_token.clone(); let reader = input.reader_client_id.clone();
        let owner = f.models.reserve_evaluation().unwrap();
        let calls = Arc::new(AtomicUsize::new(0)); let seen = calls.clone();
        f.manager.selected_prepare(&f.lease, &f.models, f.epoch, true, input, move |_| {
            seen.fetch_add(1, Ordering::SeqCst); Ok(true) }).unwrap();
        let done = f.done(&client); join4(&f);
        assert_eq!(done["error"], "NativeUnavailable"); assert_eq!(calls.load(Ordering::SeqCst), 0);
        for key in ["plan_token", "run_token", "binding", "run_id", "prepared"] { assert!(done[key].is_null()); }
        assert!(catalog4(&f)["runs"].as_array().unwrap().is_empty()); assert!(!f.manager.selected_root().exists());
        assert_eq!(f.manager.comparison_source(&f.lease, f.epoch, true, &token).unwrap_err(), "UnknownEvaluationRun");
        assert_eq!(f.manager.comparison_close(&f.lease, f.epoch, &reader, Some(&token)).unwrap()["phase"], "closed");
        assert!(matches!(f.models.reserve_evaluation(), Err(error) if error == "Busy"));
        assert!(!f.source().parent().unwrap().join("models").exists());
        drop(owner); close4(&f, &client); assert!(f.models.cleanup_complete()); source_released4(&f, &before);
    }
}

struct Release4(Option<mpsc::SyncSender<()>>);
impl Release4 { fn now(&mut self) { if let Some(sender) = self.0.take() { let _ = sender.try_send(()); } } }
impl Drop for Release4 { fn drop(&mut self) { self.now(); } }

#[test]
fn actual_consent_deny_error_cancel_close_and_epoch_retire_never_publish_a_late_scene_plan() {
    // Fixed native-consent boundary; no claim of inference/arm interruption.
    for outcome in 0..5 {
        let mut f = fixture4(producer::ComparisonKind::ContinuousRollout);
        let before = inventory(f.source()); let client = uuid().unwrap();
        let input = source_input4(&f, &client, f.source());
        let (entered, arrived) = mpsc::sync_channel(1); let (sender, wait) = mpsc::sync_channel(1);
        let mut release = Release4(Some(sender));
        let pending = f.manager.selected_prepare(&f.lease, &f.models, f.epoch, true, input, move |m| {
            assert_eq!(m["version"], 3); entered.send(()).map_err(|_| "EvaluationInternal".to_owned())?;
            wait.recv_timeout(Duration::from_secs(60)).map_err(|_| "EvaluationInternal".to_owned())?;
            match outcome { 0 => Ok(false), 1 => Err("EvaluationIo".into()), _ => Ok(true) }
        }).unwrap();
        let reached = arrived.recv_timeout(Duration::from_secs(60));
        let busy = f.manager.start(&f.lease, f.epoch, None, "one");
        let gates_free = f.manager.registration.try_lock().is_ok() && f.manager.state.try_lock().is_ok()
            && f.manager.selected.try_lock().is_ok();
        let operation = pending["operation_id"].as_u64().unwrap();
        let stale_cancel = f.manager.selected_cancel(&f.lease, f.epoch, true, &client, operation + 1);
        let retirement = if outcome == 4 {
            let closed = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
            f.manager.retire(f.epoch); Some(closed)
        } else { None };
        if outcome == 2 { f.manager.selected_cancel(&f.lease, f.epoch, true, &client, operation).unwrap(); }
        if outcome == 3 { f.manager.selected_close(&f.lease, f.epoch, &client).unwrap(); }
        release.now();
        let result = if let Some(closed) = retirement {
            let old_epoch = f.epoch; f.manager.drain(old_epoch); f.lease.finish_close(closed, || {});
            f.epoch = f.lease.begin().unwrap();
            assert_eq!(f.manager.selected_status(&f.lease, old_epoch, true, &client).unwrap_err(), "Closed");
            assert_eq!(f.manager.selected_status(&f.lease, f.epoch, true, &client).unwrap_err(), "UnknownEvaluationRun");
            None
        } else { let result = f.done(&client); join4(&f); Some(result) };
        assert!(reached.is_ok(), "actual V3 preparation must reach native consent");
        assert_eq!(busy.unwrap_err(), "EvaluationBusy"); assert_eq!(stale_cancel.unwrap_err(), "UnknownEvaluationRun");
        assert!(gates_free);
        if let Some(result) = result {
            assert!(result["plan_token"].is_null() && result["run_id"].is_null());
            if outcome == 3 { assert_eq!(result["phase"], "closed"); }
            else { assert_eq!(result["error"], if outcome == 1 { "EvaluationIo" } else { "Cancelled" }); }
            close4(&f, &client);
        }
        assert!(catalog4(&f)["runs"].as_array().unwrap().is_empty());
        assert!(f.models.cleanup_complete()); source_released4(&f, &before);
    }
}

#[test]
fn source_binding_reader_client_window_and_grant_are_independent_prepare_authorities() {
    let f = fixture4(producer::ComparisonKind::ContinuousRollout); let before = inventory(f.source());
    let client = uuid().unwrap(); let input = source_input4(&f, &client, f.source());
    let mut bad = duplicate_input4(&input); bad.client_id = "../invalid".into();
    assert_eq!(f.manager.selected_prepare(&f.lease, &f.models, f.epoch, false, bad, |_| panic!("no consent")).unwrap_err(), "Forbidden");
    for fault in 0..3 {
        let mut bad = duplicate_input4(&input);
        match fault { 0 => bad.reader_client_id = uuid().unwrap(), 1 => bad.run_token = uuid().unwrap(),
            _ => bad.binding = "a".repeat(64) }
        assert_eq!(f.manager.selected_prepare(&f.lease, &f.models, f.epoch, true, bad, |_| panic!("no consent")).unwrap_err(),
            if fault == 2 { "EvaluationSourceMismatch" } else { "UnknownEvaluationRun" });
    }
    let foreign = Arc::new(WindowLease::default()); let foreign_epoch = foreign.begin().unwrap();
    assert_eq!(foreign_epoch, f.epoch);
    assert_eq!(f.manager.selected_prepare(&foreign, &f.models, foreign_epoch, true, duplicate_input4(&input),
        |_| panic!("foreign lease no consent")).unwrap_err(), "UnknownEvaluationRun");
    let stale = duplicate_input4(&input); let consumed = input.run_token.clone();
    f.manager.selected_prepare(&f.lease, &f.models, f.epoch, true, input, |_| Ok(true)).unwrap();
    let prepared = f.done(&client); join4(&f); assert_eq!(prepared["phase"], "prepared");
    let mut stale = stale; stale.client_id = uuid().unwrap();
    assert_eq!(f.manager.selected_prepare(&f.lease, &f.models, f.epoch, true, stale, |_| panic!("consumed no consent")).unwrap_err(), "UnknownEvaluationRun");
    assert_eq!(f.manager.comparison_source(&f.lease, f.epoch, true, &consumed).unwrap_err(), "UnknownEvaluationRun");
    let token = prepared["plan_token"].as_str().unwrap();
    assert_eq!(f.manager.selected_start(&f.lease, &f.models, f.epoch, false, "bad/", "bad/").unwrap_err(), "Forbidden");
    assert_eq!(f.manager.selected_start(&f.lease, &f.models, f.epoch, true, &uuid().unwrap(), token).unwrap_err(), "UnknownEvaluationRun");
    assert_eq!(f.manager.selected_start(&foreign, &f.models, foreign_epoch, true, &client, token).unwrap_err(), "UnknownEvaluationRun");
    close4(&f, &client);
    assert_eq!(f.manager.selected_start(&f.lease, &f.models, f.epoch, true, &client, token).unwrap_err(), "UnknownEvaluationRun");
    assert!(!f.manager.selected_root().exists()); source_released4(&f, &before);
}

#[test]
fn cold_epoch_catalog_open_and_completed_resume_reuse_exact_saved_v3_without_new_work() {
    let mut f = fixture4(producer::ComparisonKind::ContinuousRollout); let before_source = inventory(f.source());
    let client = uuid().unwrap(); let (prepared, _, complete) = complete4(&f, &client);
    let run = complete["run_id"].as_str().unwrap().to_owned();
    close4(&f, &client); let before = inventory(&f.manager.selected_root()); let catalog_before = catalog4(&f);
    let old_epoch = f.epoch; let closed = f.lease.invalidate(&format!("main-{old_epoch}")).unwrap();
    f.manager.retire(old_epoch); f.manager.drain(old_epoch); f.lease.finish_close(closed, || {});
    f.epoch = f.lease.begin().unwrap();
    // Actual epoch/capability cold open, expressly not executable-process restart.
    assert_eq!(catalog4(&f), catalog_before); let new_client = uuid().unwrap();
    let identity = open4(&f, &new_client, &run);
    let read_before = f.manager.selected_summary(&f.lease, &f.models, f.epoch, true, identity.clone()).unwrap(); join4(&f);
    let source = source_input4(&f, &new_client, f.source());
    let reservation = f.models.reserve_evaluation().unwrap();
    f.manager.selected_resume(&f.lease, &f.models, f.epoch, true, resume_input4(&new_client, &identity, source), |m| {
        assert_eq!(m["version"], 3); assert_eq!(m["source_protocol_version"], 4); Ok(true)
    }).unwrap();
    let resumed = f.done(&new_client); join4(&f); assert_eq!(resumed["phase"], "completed", "{resumed}");
    assert_eq!(resumed["run_id"], run);
    let after_read = SelectedReadInput { client_id: new_client.clone(), run_token: resumed["run_token"].as_str().unwrap().into(),
        binding: resumed["binding"].as_str().unwrap().into() };
    let read_after = f.manager.selected_summary(&f.lease, &f.models, f.epoch, true, after_read.clone()).unwrap(); join4(&f);
    assert_eq!(read_before["summary"], read_after["summary"]);
    // Fresh resume denial must not use the private read grant as execution consent.
    let fresh = source_input4(&f, &new_client, f.source());
    f.manager.selected_resume(&f.lease, &f.models, f.epoch, true, resume_input4(&new_client, &after_read, fresh), |_| Ok(false)).unwrap();
    let denied = f.done(&new_client); join4(&f); assert_eq!(denied["error"], "Cancelled");
    assert_eq!(f.manager.selected_start(&f.lease, &f.models, f.epoch, true, &new_client,
        prepared["plan_token"].as_str().unwrap()).unwrap_err(), "UnknownEvaluationRun");
    close4(&f, &new_client); assert_eq!(inventory(&f.manager.selected_root()), before);
    assert_eq!(catalog4(&f), catalog_before);
    assert!(matches!(f.models.reserve_evaluation(), Err(error) if error == "Busy")); drop(reservation);
    assert!(f.models.cleanup_complete()); source_released4(&f, &before_source);
}

#[test]
fn actual_other_scene4_source_and_actor_raw_queries_cannot_rebind_a_saved_read_or_resume() {
    let f = fixture4(producer::ComparisonKind::ContinuousRollout); let source_before = inventory(f.source());
    let client = uuid().unwrap(); let (_, _, complete) = complete4(&f, &client);
    let run = complete["run_id"].as_str().unwrap(); let path = work4(&f, run); let before = inventory(path.parent().unwrap());
    let identity = open4(&f, &client, run);
    for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
        let mut bad = identity.clone(); bad.binding = "bad".into();
        assert_eq!(f.manager.selected_evidence(&f.lease, &f.models, f.epoch, true, SelectedEvidenceInput {
            identity: bad.clone(), arm: Arm::Left, request: EvidenceRequest::Receipt { observer: observer.clone() } }).unwrap_err(), "Forbidden");
        assert_eq!(f.manager.selected_diagnostics(&f.lease, &f.models, f.epoch, true, bad, observer).unwrap_err(), "Forbidden");
    }
    let mut bad = identity.clone(); bad.binding = "a".repeat(64);
    assert_eq!(f.manager.selected_summary(&f.lease, &f.models, f.epoch, false, bad.clone()).unwrap_err(), "Forbidden");
    assert_eq!(f.manager.selected_summary(&f.lease, &f.models, f.epoch, true, bad).unwrap_err(), "UnknownEvaluationRun");
    let other = f.source().parent().unwrap().join("different-source");
    copy4(original4(producer::ComparisonKind::PairedSnapshots), &other); let other_before = inventory(&other);
    let fresh = source_input4(&f, &client, &other); let calls = Arc::new(AtomicUsize::new(0)); let seen = calls.clone();
    let reservation = f.models.reserve_evaluation().unwrap();
    f.manager.selected_resume(&f.lease, &f.models, f.epoch, true, resume_input4(&client, &identity, fresh), move |_| {
        seen.fetch_add(1, Ordering::SeqCst); Ok(true) }).unwrap();
    let failed = f.done(&client); join4(&f); assert_eq!(failed["error"], "EvaluationSourceMismatch");
    assert_eq!(calls.load(Ordering::SeqCst), 0); close4(&f, &client);
    assert_eq!(inventory(path.parent().unwrap()), before); assert_eq!(inventory(&other), other_before);
    assert!(matches!(f.models.reserve_evaluation(), Err(error) if error == "Busy")); drop(reservation);
    source_released4(&f, &source_before); assert!(f.models.cleanup_complete());
}

#[test]
fn corrupted_real_v3_native_indices_refuse_before_consent_and_never_repair_saved_bytes() {
    let original = fixture4(producer::ComparisonKind::ContinuousRollout); let client = uuid().unwrap();
    let (_, _, complete) = complete4(&original, &client); let run = complete["run_id"].as_str().unwrap().to_owned();
    close4(&original, &client); let closed = inventory(&original.manager.selected_root().join(&run));
    let source_before = inventory(original.source());
    for fault in 0..6 {
        let f = fixture4(producer::ComparisonKind::ContinuousRollout);
        fs::create_dir(f.manager.selected_root()).unwrap();
        let dir = f.manager.selected_root().join(&run); fs::create_dir(&dir).unwrap();
        for (p,b) in &closed { match b { None => fs::create_dir_all(dir.join(p)).unwrap(), Some(b) => fs::write(dir.join(p), b).unwrap() } }
        let index_path = dir.join("native.json"); let mut index = read4(&index_path);
        // Trusted negative metadata corruption of an actual artifact, never a
        // fabricated positive plan, receipt, index, request or Engine authority.
        match fault {
            0 => index["source_binding"] = json!("a".repeat(64)),
            1 => index["prepared"]["source_binding"] = json!("b".repeat(64)),
            2 => index["version"] = json!(2),
            3 => index["prepared"]["source_protocol_version"] = json!(3),
            4 => { index["lane"] = json!("approved_native"); index["prepared"]["lane"] = json!("native_selected_case"); }
            _ => index["prepared"]["constructions"][0]["prompt_version"] = json!("unsupported-scene-contract"),
        }
        fs::write(&index_path, serde_json::to_vec(&index).unwrap()).unwrap(); let before = inventory(&f.manager.selected_root());
        let calls = Arc::new(AtomicUsize::new(0)); let seen = calls.clone(); let opening = uuid().unwrap();
        let admitted = f.manager.selected_open(&f.lease, &f.models, f.epoch, true, (&opening, &run), move |_| {
            seen.fetch_add(1, Ordering::SeqCst); Ok(true) });
        let error = match admitted { Ok(_) => { let status = f.done(&opening); join4(&f); status["error"].as_str().unwrap().to_owned() }, Err(e) => e };
        assert_eq!(error, "EvaluationIntegrity"); assert_eq!(calls.load(Ordering::SeqCst), 0);
        assert_eq!(inventory(&f.manager.selected_root()), before); assert!(f.models.cleanup_complete());
    }
    assert_eq!(inventory(&original.manager.selected_root().join(&run)), closed);
    source_released4(&original, &source_before);
}

#[test]
fn actual_prepared_v3_source_binding_corruption_refuses_before_new_index_or_start_work() {
    let f = fixture4(producer::ComparisonKind::ContinuousRollout); let before = inventory(f.source());
    let client = uuid().unwrap(); let prepared = prepare4(&f, &client);
    {
        // A negative control of one actual retained metadata copy. The opaque
        // plan and native retained source binding are untouched and remain real.
        let mut state = f.manager.selected_lock().unwrap();
        state.records.get_mut(&client).unwrap().plan.as_mut().unwrap().metadata["source_binding"] = json!("a".repeat(64));
    }
    f.manager.selected_start(&f.lease, &f.models, f.epoch, true, &client,
        prepared["plan_token"].as_str().unwrap()).unwrap();
    let failed = f.done(&client); join4(&f); assert_eq!(failed["error"], "EvaluationIntegrity");
    assert!(!f.manager.selected_root().exists(), "reject mismatched native metadata before index/destination writes");
    close4(&f, &client); source_released4(&f, &before); assert!(f.models.cleanup_complete());
}
