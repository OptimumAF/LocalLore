// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic metadata/index boundary regressions, not an execution capability.
//! Genuine scripted preparation/start/resume remains covered by the existing
//! literal and scene selected-service tests. Historical fixtures are untouched.
use super::*;

fn prepared(version: u64, legacy: bool) -> Value {
    let mut value = json!({
        "version": version, "kind": "selected_prepared", "binding": "a".repeat(64),
        "lane": "scripted_selected_case",
        "selection": {"turn": "turn-5", "clicked_arm": "left", "index": 4},
        "arms": ["left", "right"].map(|arm| json!({
            "arm": arm, "scope": {"story": "fixture-story", "branch": arm},
            "before_head": 7, "prefix_sha256": "b".repeat(64),
            "input_semantic_sha256": "c".repeat(64)
        }))
    });
    if version == 2 {
        value["source_protocol_version"] = json!(3);
        value["constructions"] = if legacy {
            serde_json::to_value(locallore_eval::memory_comparison_v3::arm_descriptors())
        } else {
            serde_json::to_value(locallore_eval::memory_comparison_v3::current_arm_descriptors())
        }
        .unwrap();
    } else if version == 3 {
        value["source_protocol_version"] = json!(4);
        value["source_binding"] = json!("d".repeat(64));
        value["constructions"] = if legacy {
            serde_json::to_value(locallore_eval::memory_comparison_v4::arm_descriptors())
        } else {
            serde_json::to_value(locallore_eval::memory_comparison_v4::current_arm_descriptors())
        }
        .unwrap();
    }
    value
}

#[test]
fn fresh_requires_current_whole_family_while_recorded_keeps_both_exact_families() {
    for (version, policy) in [
        (2, "grounded-prose-v2.5-whole-evidence-words-v1"),
        (3, "grounded-prose-v2.7-scene-frame-whole-evidence-words-v1"),
    ] {
        let current = prepared(version, false);
        let historical = prepared(version, true);
        for arm in 0..2 {
            assert_eq!(current["constructions"][arm]["narration_policy"], policy);
        }
        assert_ne!(current["constructions"], historical["constructions"]);
        assert!(prepared_valid(&current, PreparedUse::Fresh));
        assert!(prepared_valid(&current, PreparedUse::Recorded));
        assert!(prepared_valid(&historical, PreparedUse::Recorded));
        assert!(!prepared_valid(&historical, PreparedUse::Fresh));
    }
}

#[test]
fn individually_known_mixed_arms_and_descriptor_tuple_drift_never_form_a_family() {
    for version in [2, 3] {
        let current = prepared(version, false);
        let historical = prepared(version, true);
        for replaced in 0..2 {
            let mut mixed = current.clone();
            mixed["constructions"][replaced] = historical["constructions"][replaced].clone();
            for usage in [PreparedUse::Fresh, PreparedUse::Recorded] {
                assert!(!prepared_valid(&mixed, usage));
            }
        }
        for field in ["prompt_version", "narration_policy", "literal_packing_version", "compiler_version"] {
            let mut drift = current.clone();
            drift["constructions"][0][field] = json!("unsupported");
            for usage in [PreparedUse::Fresh, PreparedUse::Recorded] {
                assert!(!prepared_valid(&drift, usage), "{version}: {field}");
            }
        }
        let mut extra = current.clone();
        extra["constructions"][1]["execution_available"] = json!(true);
        assert!(!prepared_valid(&extra, PreparedUse::Recorded));
    }
}

#[test]
fn family_migration_retains_binding_protocol_selection_and_lane_guards() {
    for version in [2, 3] {
        for fault in 0..6 {
            let mut value = prepared(version, false);
            match fault {
                0 => value["binding"] = json!("not-a-binding"),
                1 => value["source_protocol_version"] = json!(99),
                2 => value["lane"] = json!("arbitrary_lane"),
                3 => value["selection"]["index"] = json!(24),
                4 => value["arms"][1]["before_head"] = json!(-1),
                _ => value["selection"]["execution_grant"] = json!(true),
            }
            for usage in [PreparedUse::Fresh, PreparedUse::Recorded] {
                assert!(!prepared_valid(&value, usage), "{version}: {fault}");
            }
        }
    }
    let mut scene = prepared(3, false);
    scene["lane"] = json!("native_selected_case");
    assert!(!prepared_valid(&scene, PreparedUse::Fresh));
    assert!(!prepared_valid(&scene, PreparedUse::Recorded));
}

#[test]
fn original_selected_v1_closed_shape_is_unchanged_in_both_uses() {
    let original = prepared(1, true);
    for usage in [PreparedUse::Fresh, PreparedUse::Recorded] {
        assert!(prepared_valid(&original, usage));
        let mut retagged = original.clone();
        retagged["constructions"] = prepared(2, false)["constructions"].clone();
        assert!(!prepared_valid(&retagged, usage));
    }
}

const RUN: &str = "11111111-1111-1111-1111-111111111111";
fn index_fixture(prepared: Value) -> (EvaluationManager, PathBuf, Vec<u8>) {
    static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let nonce = NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
    let root = std::env::temp_dir().join(format!("selected-policy-index-{time}-{nonce}"));
    fs::create_dir(&root).unwrap();
    let manager = EvaluationManager::new(root.join("evaluations"));
    let dir = manager.selected_root().join(RUN);
    fs::create_dir_all(&dir).unwrap();
    let index = Index {
        version: prepared["version"].as_u64().unwrap() as u16,
        run_id: RUN.into(), created: 1,
        client_id: "22222222-2222-2222-2222-222222222222".into(),
        lane: "scripted_baseline".into(), source_binding: "d".repeat(64), prepared,
    };
    let bytes = serde_json::to_vec(&index).unwrap();
    let path = dir.join("native.json");
    let mut file = OpenOptions::new().write(true).create_new(true).open(&path).unwrap();
    file.write_all(&bytes).unwrap();
    file.sync_all().unwrap();
    (manager, path, bytes)
}

#[test]
fn reading_old_or_current_indices_preserves_exact_bytes_without_execution_ownership() {
    for version in [2, 3] {
        for legacy in [true, false] {
            let metadata = prepared(version, legacy);
            let (manager, path, bytes) = index_fixture(metadata.clone());
            let read = manager.selected_index(RUN).unwrap();
            assert_eq!(read.prepared, metadata);
            assert_eq!(fs::read(&path).unwrap(), bytes);
            assert!(!path.parent().unwrap().join("work").exists());
            assert!(manager.state().unwrap().job.is_none());
            assert!(manager.worker.lock().unwrap().is_none());
            assert!(manager.selected_lock().unwrap().records.is_empty());
        }
    }
}

#[test]
fn recorded_family_acceptance_does_not_bypass_native_index_source_and_lane_joins() {
    for legacy in [true, false] {
        for fault in 0..4 {
            let (manager, path, original) = index_fixture(prepared(3, legacy));
            let mut index: Value = serde_json::from_slice(&original).unwrap();
            match fault {
                0 => index["source_binding"] = json!("e".repeat(64)),
                1 => index["prepared"]["source_binding"] = json!("f".repeat(64)),
                2 => index["lane"] = json!("approved_native"),
                _ => index["version"] = json!(2),
            }
            let bytes = serde_json::to_vec(&index).unwrap();
            fs::write(&path, &bytes).unwrap();
            assert!(matches!(manager.selected_index(RUN), Err(error) if error == "EvaluationIntegrity"));
            assert_eq!(fs::read(&path).unwrap(), bytes);
            assert!(manager.state().unwrap().job.is_none());
            assert!(manager.worker.lock().unwrap().is_none());
            assert!(!path.parent().unwrap().join("work").exists());
        }
    }
}
