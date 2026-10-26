// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen before binding-shape correction at cea16866. UNCOMPILED / UNRUN.
//! Real current-service denied provisional prefixes, not native generation,
//! historical receipts, execution bypass or installed-model evidence.
use super::*;

fn coherent_binding_fault_refuses(fault: &str) {
    let (f, run, client) = copied_denial();
    let directory = f.root().join(&run);
    let index_path = directory.join("desktop.json");
    let manifest_path = directory.join("work/run.json");
    let mut index: Value = serde_json::from_slice(&fs::read(&index_path).unwrap()).unwrap();
    let mut manifest: Value = serde_json::from_slice(&fs::read(&manifest_path).unwrap()).unwrap();
    assert_eq!(index["version"], 2);
    assert_eq!(index["protocol_version"], 3);
    assert_eq!(manifest["version"], 3);
    assert_eq!(index["binding"], manifest["binding"]);
    match fault {
        "protocol" => index["binding"]["protocol_version"] = json!(2),
        "forwarded" => index["binding"]["forwarded_budget_version"] = json!(2),
        "roles" => {
            let actual = index["binding"]["max_roles"].as_u64().unwrap();
            index["binding"]["max_roles"] = json!(actual.checked_add(1).unwrap());
        }
        "source" => index["binding"]["source_sha256"] = json!("not-a-lowercase-sha256"),
        _ => panic!("closed fixture fault"),
    }
    manifest["binding"] = index["binding"].clone();
    manifest["source_sha256"] = index["binding"]["source_sha256"].clone();
    assert_eq!(manifest["binding"], index["binding"]);
    assert_eq!(manifest["source_sha256"], index["binding"]["source_sha256"]);
    // Explicit metadata corruption on this owned copy only. Both old outer
    // comparisons still match; no canonical Store/receipt/report is fabricated.
    fs::write(&index_path, serde_json::to_vec(&index).unwrap()).unwrap();
    fs::write(&manifest_path, serde_json::to_vec(&manifest).unwrap()).unwrap();
    let before = inventory(&f.root());

    // Exercise the native and opposite scripted catalog independently before
    // asserting, so one early assertion cannot conceal the other's response.
    let native = f
        .manager
        .full_comparison_catalog_native(&f.lease, f.epoch, true);
    let scripted = f.manager.full_comparison_catalog(&f.lease, f.epoch, true);
    let calls = Arc::new(AtomicUsize::new(0));
    let consent = calls.clone();
    let exact_retry = f.manager.full_comparison_start_native(
        &f.lease,
        &f.models,
        f.epoch,
        true,
        Fixture::input(&client),
        move |_| {
            consent.fetch_add(1, Ordering::SeqCst);
            Ok(false)
        },
    );
    assert!(inventory(&f.root()) == before);
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert!(f.manager.cleanup_complete());
    assert!(f.models.cleanup_complete());
    rejected(native, "EvaluationIntegrity");
    rejected(scripted, "EvaluationIntegrity");
    rejected(exact_retry, "EvaluationIntegrity");
}

#[test]
fn inner_protocol_two_cannot_masquerade_as_coherent_outer_protocol_three() {
    coherent_binding_fault_refuses("protocol");
}

#[test]
fn unknown_forwarded_budget_version_is_not_validated_by_matching_outer_metadata() {
    coherent_binding_fault_refuses("forwarded");
}

#[test]
fn changed_role_cap_cannot_enter_either_lane_catalog_as_known_schema() {
    coherent_binding_fault_refuses("roles");
}

#[test]
fn malformed_source_sha_remains_invalid_when_manifest_matches_it_exactly() {
    coherent_binding_fault_refuses("source");
}

#[test]
fn well_formed_stale_source_and_suite_are_metadata_only_not_execution_or_history() {
    let f = Fixture::new();
    let scripted = f.metadata(false, &uuid().unwrap());
    let native = f.metadata(true, &uuid().unwrap());
    for run in [&scripted, &native] {
        let path = f.root().join(run).join("desktop.json");
        let mut index: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        index["binding"]["source_sha256"] = json!("1".repeat(64));
        index["binding"]["suite_sha256"] = json!("2".repeat(64));
        fs::write(path, serde_json::to_vec(&index).unwrap()).unwrap();
        assert!(!f.root().join(run).join("work").exists());
    }
    // These are deliberately synthetic wrapper-metadata fixtures, not genuine
    // historical runs or hashes authenticated by a recorded native execution.
    let before = inventory(&f.root());
    let scripted_catalog = f
        .manager
        .full_comparison_catalog(&f.lease, f.epoch, true)
        .unwrap();
    let native_catalog = f
        .manager
        .full_comparison_catalog_native(&f.lease, f.epoch, true)
        .unwrap();
    assert_eq!(scripted_catalog["version"], 1);
    assert_eq!(scripted_catalog["runs"].as_array().unwrap().len(), 1);
    assert_eq!(scripted_catalog["runs"][0]["run_id"], scripted);
    assert_eq!(native_catalog["version"], 2);
    assert_eq!(native_catalog["runs"].as_array().unwrap().len(), 1);
    assert_eq!(native_catalog["runs"][0]["run_id"], native);
    assert!(inventory(&f.root()) == before);
    assert!(f.manager.cleanup_complete());
    assert!(f.models.cleanup_complete());
}
