// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST source: UNREGISTERED/UNCOMPILED/UNRUN. Actual scripted
//! Core/Host producer -> native manager; no IPC, WebView, picker, model or OS probe.
//! Stored unavailable/rejected controls do not authenticate historical origin.
use super::*;
use crate::evaluation::ComparisonNarrationDiagnosticRequestV1;
use serde_json::json;

const HEADER: &str = "narration-diagnostics-v1.json";
const PRIVATE_DIAGNOSTIC: &str = "SYNTHETIC-DIAGNOSTIC-PRIVATE-814";

fn diagnostic_template() -> &'static Path {
    static TEMPLATE: OnceLock<PathBuf> = OnceLock::new();
    TEMPLATE
        .get_or_init(|| {
            let dir = root("diagnostic-actual-host").join("run");
            let report = scene_v4::run_comparison_with_narration_diagnostics_v1(
                &dir,
                false,
                producer::ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
            assert_eq!(report.physical_setups, 0);
            assert!(!report.quality_accepted && report.human_reviewed == 0);
            assert!(dir.join(HEADER).is_file());
            dir
        })
        .as_path()
}
fn diagnostic_copy() -> PathBuf {
    let original = inventory(diagnostic_template());
    let target = root("diagnostic-copy");
    for (relative, bytes) in &original {
        let path = target.join(relative);
        match bytes {
            None => fs::create_dir_all(path).unwrap(),
            Some(bytes) => {
                fs::create_dir_all(path.parent().unwrap()).unwrap();
                let mut file = OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(path)
                    .unwrap();
                file.write_all(bytes).unwrap();
            }
        }
    }
    assert_eq!(inventory(&target), original);
    target
}
fn json_file(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn observation_file(path: &Path, arm: &str) -> PathBuf {
    let checkpoint = json_file(&path.join(arm).join("attempt-00.json"));
    let admission = checkpoint["row"]["admission"].as_u64().unwrap();
    path.join(arm)
        .join(format!("narration-diagnostic-v1-{admission:02}.json"))
}
fn diagnostic_input(
    token: &str,
    binding: &str,
    arm: shared::Arm,
    observer: Observer,
) -> ComparisonNarrationDiagnosticRequestV1 {
    ComparisonNarrationDiagnosticRequestV1 {
        token: token.into(),
        binding: binding.into(),
        row: shared::RowId {
            turn: "courier-01".into(),
            arm,
        },
        observer,
    }
}
fn read(f: &Fixture, token: &str, binding: &str, arm: shared::Arm) -> Result<Value> {
    f.manager.comparison_narration_diagnostic_v1(
        &f.lease,
        f.epoch,
        true,
        diagnostic_input(token, binding, arm, Observer::Omniscient),
    )
}
fn exact_keys(value: &Value, names: &[&str]) {
    let mut actual: Vec<_> = value
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    let mut expected = names.to_vec();
    actual.sort_unstable();
    expected.sort_unstable();
    assert_eq!(actual, expected);
}
fn response(value: &Value, token: &str, binding: &str, arm: &str, status: &str) {
    assert!(serde_json::to_vec(value).unwrap().len() <= 8192);
    exact_keys(value, &["version", "kind", "run_token", "diagnostic"]);
    assert_eq!(value["version"], 1);
    assert_eq!(value["kind"], "comparison_reader_narration_diagnostic_v1");
    assert_eq!(value["run_token"], token);
    let diagnostic = &value["diagnostic"];
    let observed = !matches!(status, "no_declaration" | "no_observation");
    let mut keys = vec![
        "version",
        "protocol_version",
        "kind",
        "binding",
        "row",
        "generation_grant",
        "status",
    ];
    if observed {
        keys.push("observation");
    }
    exact_keys(diagnostic, &keys);
    assert_eq!(diagnostic["version"], 1);
    assert_eq!(diagnostic["protocol_version"], 4);
    assert_eq!(diagnostic["kind"], "narration_diagnostic_v1");
    assert_eq!(diagnostic["binding"], binding);
    assert_eq!(diagnostic["row"], json!({"turn":"courier-01","arm":arm}));
    assert_eq!(diagnostic["generation_grant"], false);
    assert_eq!(diagnostic["status"], status);
    assert_eq!(diagnostic.get("observation").is_some(), observed);
}
fn release_and_inventory(f: &Fixture, client: &str, token: &str, path: &Path, before: Inventory) {
    f.close(client, Some(token));
    assert_eq!(f.done(client)["phase"], "closed");
    f.manager.drain(f.epoch);
    reacquire4(path);
    assert_eq!(inventory(path), before);
}

#[test]
fn actual_opted_in_both_recipe_reads_match_unchanged_core_and_release_all_source_bytes() {
    let path = diagnostic_copy();
    let before = inventory(&path); // Never inventory while run.lock is held.
    let f = Fixture::new();
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    let token = ready["run_token"].as_str().unwrap();
    let binding = ready["binding"].as_str().unwrap();
    let old_summary = f
        .manager
        .comparison_summary(&f.lease, f.epoch, true, token)
        .unwrap();
    for (arm, name) in [(shared::Arm::Left, "left"), (shared::Arm::Right, "right")] {
        let stored = json_file(&observation_file(&path, name));
        let got = read(&f, token, binding, arm).unwrap();
        response(&got, token, binding, name, "recorded");
        assert_eq!(got["diagnostic"]["observation"], stored);
        assert_eq!(stored["generation_grant"], false);
        assert_eq!(
            stored["host_query"]["command"]["op"],
            "trace_narration_validation_read_v1"
        );
        assert_ne!(
            got["diagnostic"]["binding"], stored["run_binding_sha256"],
            "snapshot binding and run key are distinct, not substituted"
        );
    }
    assert_eq!(
        f.manager
            .comparison_summary(&f.lease, f.epoch, true, token)
            .unwrap(),
        old_summary
    );
    let status = f.done(&client);
    assert_eq!(status["phase"], "ready");
    assert_eq!(status["execution_available"], false);
    release_and_inventory(&f, &client, token, &path, before);
}

#[test]
fn five_statuses_keep_actual_legacy_absence_separate_from_trusted_stored_host_controls() {
    for mode in [
        "no_declaration",
        "no_observation",
        "host_unavailable",
        "host_rejected",
    ] {
        let path = if mode == "no_declaration" {
            copied(4)
        } else {
            diagnostic_copy()
        };
        if mode != "no_declaration" {
            let file = observation_file(&path, "left");
            let mut stored = json_file(&file);
            match mode {
                "no_observation" => fs::rename(
                    &file,
                    path.parent()
                        .unwrap()
                        .join(format!("retained-{}.bytes", uuid().unwrap())),
                )
                .unwrap(),
                "host_unavailable" => {
                    stored["host_reply"]["data"]["status"] = json!("unavailable");
                    stored["host_reply"]["data"]
                        .as_object_mut()
                        .unwrap()
                        .remove("decision");
                    fs::write(&file, serde_json::to_vec(&stored).unwrap()).unwrap();
                }
                "host_rejected" => {
                    stored["host_reply"] =
                        json!({"version":1,"status":"rejected","error":"Closed"});
                    fs::write(&file, serde_json::to_vec(&stored).unwrap()).unwrap();
                }
                _ => unreachable!(),
            }
        }
        let before = inventory(&path);
        let f = Fixture::new();
        let client = uuid().unwrap();
        let ready = f.pick(&client, &path);
        let token = ready["run_token"].as_str().unwrap();
        let binding = ready["binding"].as_str().unwrap();
        response(
            &read(&f, token, binding, shared::Arm::Left).unwrap(),
            token,
            binding,
            "left",
            mode,
        );
        release_and_inventory(&f, &client, token, &path, before);
    }
}

#[test]
fn permission_precedes_scalars_retired_lease_token_expiry_and_corrupt_source_work() {
    let path = diagnostic_copy();
    let before = inventory(&path);
    let f = Fixture::new();
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    let token = ready["run_token"].as_str().unwrap();
    let binding = ready["binding"].as_str().unwrap();
    f.manager
        .comparison_lock()
        .unwrap()
        .records
        .get_mut(&client)
        .unwrap()
        .touched = Instant::now() - Duration::from_secs(901);
    let original = fs::read(path.join("run.json")).unwrap();
    fs::write(path.join("run.json"), PRIVATE_DIAGNOSTIC).unwrap();
    for (granted, observer) in [
        (false, Observer::Omniscient),
        (true, Observer::Player),
        (true, Observer::Character { id: "mira".into() }),
    ] {
        let mut input =
            diagnostic_input("invalid-token", "bad-binding", shared::Arm::Left, observer);
        input.row.turn = "../private".into();
        assert_eq!(
            err(f.manager.comparison_narration_diagnostic_v1(
                &f.lease,
                f.epoch + 1,
                granted,
                input
            )),
            "Forbidden"
        );
        let state = f.manager.comparison_lock().unwrap();
        let r = &state.records[&client];
        assert!(!r.expired && !r.running && r.granted && r.cap.is_some());
    }
    fs::write(path.join("run.json"), original).unwrap();
    assert_eq!(
        err(read(&f, token, binding, shared::Arm::Left)),
        "UnknownEvaluationRun"
    );
    f.manager.drain(f.epoch);
    f.close(&client, Some(token));
    reacquire4(&path);
    assert_eq!(inventory(&path), before);
}

#[test]
fn wrong_protocol_foreign_owner_bad_scalars_row_binding_and_present_corruption_are_fixed_refusals()
{
    for version in [2, 3] {
        let path = copied(version);
        let mut expected = inventory(&path);
        let f = Fixture::new();
        let client = uuid().unwrap();
        let ready = f.pick(&client, &path);
        let token = ready["run_token"].as_str().unwrap();
        let binding = ready["binding"].as_str().unwrap();
        fs::write(path.join(HEADER), PRIVATE_DIAGNOSTIC).unwrap();
        expected.insert(
            PathBuf::from(HEADER),
            Some(PRIVATE_DIAGNOSTIC.as_bytes().to_vec()),
        );
        assert_eq!(
            err(read(&f, token, binding, shared::Arm::Left)),
            "Unsupported"
        );
        f.close(&client, Some(token));
        f.done(&client);
        f.manager.drain(f.epoch);
        assert_eq!(inventory(&path), expected);
    }
    let path = diagnostic_copy();
    let original = inventory(&path);
    let f = Fixture::new();
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    let token = ready["run_token"].as_str().unwrap();
    let binding = ready["binding"].as_str().unwrap();
    let other = Arc::new(WindowLease::default());
    let epoch = other.begin().unwrap();
    assert_eq!(
        err(f.manager.comparison_narration_diagnostic_v1(
            &other,
            epoch,
            true,
            diagnostic_input(token, binding, shared::Arm::Left, Observer::Omniscient)
        )),
        "UnknownEvaluationRun"
    );
    assert_eq!(
        err(f.manager.comparison_narration_diagnostic_v1(
            &f.lease,
            f.epoch + 1,
            true,
            diagnostic_input(token, binding, shared::Arm::Left, Observer::Omniscient)
        )),
        "Closed"
    );
    assert_eq!(
        err(read(&f, &uuid().unwrap(), binding, shared::Arm::Left)),
        "UnknownEvaluationRun"
    );
    assert_eq!(
        err(f.manager.comparison_narration_diagnostic_v1(
            &f.lease,
            f.epoch,
            true,
            diagnostic_input("bad", binding, shared::Arm::Left, Observer::Omniscient)
        )),
        "InvalidEvaluationInput"
    );
    let mut unknown = diagnostic_input(token, binding, shared::Arm::Left, Observer::Omniscient);
    unknown.row.turn = "not-a-retained-row".into();
    assert_eq!(
        err(f
            .manager
            .comparison_narration_diagnostic_v1(&f.lease, f.epoch, true, unknown)),
        "InvalidEvaluationInput"
    );
    assert_eq!(
        err(read(&f, token, &"0".repeat(64), shared::Arm::Left)),
        "EvaluationIntegrity"
    );
    let file = observation_file(&path, "left");
    let bytes = fs::read(&file).unwrap();
    for (bad, expected) in [
        (b"{".to_vec(), "EvaluationIntegrity"),
        (vec![b' '; 7169], "EvaluationBudget"),
    ] {
        fs::write(&file, bad).unwrap();
        assert_eq!(err(read(&f, token, binding, shared::Arm::Left)), expected);
        assert_eq!(f.done(&client)["phase"], "ready");
    }
    fs::write(&file, bytes).unwrap();
    release_and_inventory(&f, &client, token, &path, original);
}

#[test]
fn existing_worker_busy_close_and_retirement_never_publish_held_private_completion() {
    for retire in [false, true] {
        let path = diagnostic_copy();
        let before = inventory(&path);
        let mut f = Fixture::new();
        let client = uuid().unwrap();
        let ready = f.pick(&client, &path);
        let token = ready["run_token"].as_str().unwrap().to_owned();
        let binding = ready["binding"].as_str().unwrap().to_owned();
        let entered = Arc::new(Barrier::new(2));
        let release = Arc::new(Barrier::new(2));
        *f.manager.before_publish.lock().unwrap() = Some((entered.clone(), release.clone()));
        let manager = f.manager.clone();
        let lease = f.lease.clone();
        let epoch = f.epoch;
        let input = diagnostic_input(&token, &binding, shared::Arm::Left, Observer::Omniscient);
        let caller = std::thread::spawn(move || {
            manager.comparison_narration_diagnostic_v1(&lease, epoch, true, input)
        });
        entered.wait();
        let busy = read(&f, &token, &binding, shared::Arm::Right);
        assert_eq!(
            f.manager
                .comparison_status(&f.lease, f.epoch, true, &client)
                .unwrap()["phase"],
            "reading"
        );
        if retire {
            let closing = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
            f.manager.retire(f.epoch);
            release.wait();
            assert_eq!(err(caller.join().unwrap()), "Closed");
            f.manager.drain(f.epoch);
            f.lease.finish_close(closing, || {});
            f.epoch = f.lease.begin().unwrap();
            assert_eq!(
                err(read(&f, &token, &binding, shared::Arm::Left)),
                "UnknownEvaluationRun"
            );
        } else {
            assert_eq!(f.close(&client, Some(&token))["phase"], "closing");
            release.wait();
            assert_eq!(err(caller.join().unwrap()), "Closed");
            assert_eq!(f.done(&client)["phase"], "closed");
            f.manager.drain(f.epoch);
        }
        assert_eq!(err(busy), "EvaluationBusy");
        reacquire4(&path);
        assert_eq!(inventory(&path), before);
    }
}

#[test]
fn actual_thirty_second_response_timeout_retains_worker_until_explicit_close_and_drain() {
    let path = diagnostic_copy();
    let before = inventory(&path);
    let f = Fixture::new();
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    let token = ready["run_token"].as_str().unwrap().to_owned();
    let binding = ready["binding"].as_str().unwrap().to_owned();
    let entered = Arc::new(Barrier::new(2));
    let release = Arc::new(Barrier::new(2));
    *f.manager.before_publish.lock().unwrap() = Some((entered.clone(), release.clone()));
    let manager = f.manager.clone();
    let lease = f.lease.clone();
    let epoch = f.epoch;
    let input = diagnostic_input(&token, &binding, shared::Arm::Left, Observer::Omniscient);
    let started = Instant::now();
    let caller = std::thread::spawn(move || {
        manager.comparison_narration_diagnostic_v1(&lease, epoch, true, input)
    });
    entered.wait();
    // No shortened-timeout seam. Existing manager waits its actual thirty seconds.
    let result = caller.join().unwrap();
    let elapsed = started.elapsed();
    let status = f
        .manager
        .comparison_status(&f.lease, f.epoch, true, &client)
        .unwrap();
    let closing = f.close(&client, Some(&token));
    release.wait();
    f.done(&client);
    f.manager.drain(f.epoch);
    assert_eq!(err(result), "EvaluationIo");
    assert!(elapsed >= Duration::from_secs(30));
    assert_eq!(status["phase"], "reading");
    assert_eq!(status["running"], true);
    assert_eq!(closing["phase"], "closing");
    reacquire4(&path);
    assert_eq!(inventory(&path), before);
}
