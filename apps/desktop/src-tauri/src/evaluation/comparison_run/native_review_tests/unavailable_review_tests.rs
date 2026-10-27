// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Source-only unavailable-assets service oracle at a2610a49. UNCOMPILED / UNRUN.
//! True native consent with the actual empty Models fixture; no supplied worker,
//! model, test protocol runtime or scripted/native relabel. May already pass.
use super::*;

#[test]
fn affirmative_native_service_with_missing_assets_closes_unavailable_without_fallback_or_owner() {
    let f = Fixture::new();
    let fixture_root = f.root().parent().unwrap().to_owned();
    assert!(!fixture_root.join("models").exists());
    assert!(!fixture_root.join("resources").exists());
    let client = uuid().unwrap();
    let calls = Arc::new(AtomicUsize::new(0));
    let consent = calls.clone();
    let started = f
        .manager
        .full_comparison_start_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            Fixture::input(&client),
            move |_| {
                consent.fetch_add(1, Ordering::SeqCst);
                Ok(true)
            },
        )
        .unwrap();
    let stopped = f.done(cap(&started));

    // A terminal publication can precede the final thread instructions. Poll
    // actual owner state without any cleanup/retry/retire/helper invocation.
    let end = Instant::now() + Duration::from_secs(30);
    while !f.manager.cleanup_complete() || !f.models.cleanup_complete() {
        assert!(
            Instant::now() < end,
            "missing-assets return did not drain actual owners"
        );
        std::thread::sleep(Duration::from_millis(5));
    }
    assert!(f.manager.cleanup_complete());
    assert!(f.models.cleanup_complete());
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    assert_eq!(stopped["version"], 2);
    assert_eq!(stopped["input_lane"], "approved_native");
    assert_eq!(stopped["phase"], "failed");
    assert_eq!(stopped["error"], "NativeUnavailable");
    assert_eq!(stopped["running"], false);
    assert_eq!(stopped["cleanup_required"], false);
    assert_eq!(stopped["cleanup_running"], false);
    assert_eq!(stopped["report_ready"], false);
    assert_eq!(stopped["completed"], false);
    assert_eq!(stopped["completed_scenes"], 0);

    let run = stopped["run_id"].as_str().unwrap();
    let leaf = f.root().join(run);
    let index: Value =
        serde_json::from_slice(&fs::read(leaf.join("desktop.json")).unwrap()).unwrap();
    let manifest: Value =
        serde_json::from_slice(&fs::read(leaf.join("work/run.json")).unwrap()).unwrap();
    assert_eq!(index["version"], 2);
    assert_eq!(index["input_lane"], "approved_native");
    assert_eq!(index["binding"]["native"], true);
    assert_eq!(manifest["version"], 3);
    assert_eq!(manifest["binding"]["native"], true);
    assert_eq!(manifest["binding"], index["binding"]);
    assert_eq!(manifest["kind"], "continuous_rollout");
    assert_eq!(manifest["profile"]["id"], locallore_local_runtime::PROFILE);

    let files = inventory(&leaf);
    for path in files.keys() {
        if let Some(name) = path.file_name().and_then(|name| name.to_str()) {
            assert!(
                !["attempt-", "raw-", "capture-", "recording-"]
                    .iter()
                    .any(|prefix| name.starts_with(prefix)),
                "unavailable native assets must not generate turn evidence"
            );
        }
    }
    // Shared pre-child failure may legitimately finalize an empty diagnostic
    // report/setup and settle a real reservation. Neither is a generated turn.
    if leaf.join("work/report.json").exists() {
        let report: Value =
            serde_json::from_slice(&fs::read(leaf.join("work/report.json")).unwrap()).unwrap();
        assert_eq!(report["lane"], "native_literal_relevant_comparison");
        assert_eq!(report["completed"], false);
        assert_eq!(report["completed_scenes"], 0);
        assert!(report["turns"].as_array().unwrap().is_empty());
        assert_eq!(report["left_reserved_roles"], 0);
        assert_eq!(report["right_reserved_roles"], 0);
    }
    let scripted = f
        .manager
        .full_comparison_catalog(&f.lease, f.epoch, true)
        .unwrap();
    let native = f
        .manager
        .full_comparison_catalog_native(&f.lease, f.epoch, true)
        .unwrap();
    assert!(scripted["runs"].as_array().unwrap().is_empty());
    assert_eq!(native["runs"].as_array().unwrap().len(), 1);
    assert_eq!(native["runs"][0]["run_id"], run);
    assert!(inventory(&leaf) == files);
    f.manager
        .full_comparison_close_native(&f.lease, f.epoch, false, cap(&stopped))
        .unwrap();
}
