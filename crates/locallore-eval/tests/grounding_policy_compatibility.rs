// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Closed policy metadata and genuine old-history compatibility, not model quality.
use locallore::{
    contracts::Seed,
    engine::Engine,
    play::{self, scene_narration::SceneRecipeV1, PlayContextPolicy},
};
use locallore_eval::{
    digest,
    local_lane::comparison::{self, literal_v3, scene_v4},
    memory_comparison_v2 as v2,
    memory_comparison_v3 as v3,
    memory_comparison_v4 as v4,
    scene_capture_v1::{
        check_committed_scene_capture_v1, SceneCaptureErrorV1, SceneCaptureInputV1,
    },
};
use serde_json::Value;
use std::{collections::BTreeMap, fs, path::{Path, PathBuf}};

const OLD_ORDINARY: &str = "grounded-prose-v2.2";
const STRICT_ORDINARY: &str = "grounded-prose-v2.5-whole-evidence-words-v1";
const OLD_SCENE: &str = "grounded-prose-v2.4-scene-frame-v1";
const STRICT_SCENE: &str = "grounded-prose-v2.7-scene-frame-whole-evidence-words-v1";

#[test]
fn immutable_old_descriptor_apis_and_strict_current_bindings_remain_distinct() {
    assert_eq!(play::NARRATION_POLICY, STRICT_ORDINARY);
    assert_eq!(play::scene_narration::SCENE_NARRATION_POLICY_V1, OLD_SCENE);
    assert_eq!(play::scene_narration::SCENE_NARRATION_POLICY_V2, STRICT_SCENE);
    let old3 = v3::arm_descriptors();
    let new3 = v3::current_arm_descriptors();
    let old4 = v4::arm_descriptors();
    let new4 = v4::current_arm_descriptors();
    for index in 0..2 {
        assert_eq!(old3[index].narration_policy, OLD_ORDINARY);
        assert_eq!(new3[index].narration_policy, STRICT_ORDINARY);
        let mut changed3 = old3[index].clone();
        changed3.narration_policy = STRICT_ORDINARY.into();
        assert_eq!(changed3, new3[index], "no prompt/schema/packing tuple change");
        assert_eq!(old4[index].narration_policy, OLD_SCENE);
        assert_eq!(new4[index].narration_policy, STRICT_SCENE);
        let mut changed4 = old4[index].clone();
        changed4.narration_policy = STRICT_SCENE.into();
        assert_eq!(changed4, new4[index], "no scene construction tuple change");
    }
    assert_eq!(v2::current_binding(false).unwrap().narration_policy, STRICT_ORDINARY);
    assert_eq!(v3::current_binding(false).unwrap().arms, new3);
    assert_eq!(v4::current_binding(false).unwrap().arms, new4);
}

#[test]
fn complete_old_or_strict_families_pass_but_mixed_arms_and_tuple_drift_refuse() {
    let old3 = v3::arm_descriptors();
    let new3 = v3::current_arm_descriptors();
    v3::validate_arm_family(&old3).unwrap();
    v3::validate_arm_family(&new3).unwrap();
    for pair in [[old3[0].clone(), new3[1].clone()], [new3[0].clone(), old3[1].clone()]] {
        assert!(v3::validate_arm_family(&pair).is_err());
    }
    let mut changed3 = new3.clone();
    changed3[0].literal_render_version = Some(2);
    assert!(v3::validate_arm_family(&changed3).is_err());
    changed3 = new3;
    changed3[1].narration_policy = "invented-policy".into();
    assert!(v3::validate_arm_family(&changed3).is_err());

    let old4 = v4::arm_descriptors();
    let new4 = v4::current_arm_descriptors();
    v4::validate_arm_family(&old4).unwrap();
    v4::validate_arm_family(&new4).unwrap();
    for pair in [[old4[0].clone(), new4[1].clone()], [new4[0].clone(), old4[1].clone()]] {
        assert!(v4::validate_arm_family(&pair).is_err());
    }
    let mut changed4 = new4.clone();
    changed4[1].scene_frame_version = 2;
    assert!(v4::validate_arm_family(&changed4).is_err());
    changed4 = new4;
    changed4[0].narration_policy = STRICT_ORDINARY.into();
    assert!(v4::validate_arm_family(&changed4).is_err());
}

#[test]
fn genuine_old_receipts_restore_exactly_but_cannot_qualify_a_fresh_scene_capture() {
    let bytes = include_bytes!("../../../fixtures/narrator_source_words_legacy_v1.json");
    assert_eq!(digest(bytes), "58b56d456220ef07b16721f31d0b2fddc125bc67e54fcfd366a9ff685e354b07");
    let fixture: Value = serde_json::from_slice(bytes).unwrap();
    let cases = fixture["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 18);
    let mut scene_cases = 0;
    for case in cases {
        let seed: Seed = serde_json::from_str(case["seed_json"].as_str().unwrap()).unwrap();
        let receipt_json = case["receipt_json"].as_str().unwrap().to_owned();
        let before = Engine::new(seed.clone()).unwrap();
        let after = Engine::restore(seed, std::slice::from_ref(&receipt_json)).unwrap();
        assert_eq!(serde_json::to_string(&after.receipts()[0]).unwrap(), receipt_json);
        let expected: Vec<u8> = serde_json::from_value(case["canonical_after"].clone()).unwrap();
        assert_eq!(after.canonical_bytes(), expected);
        let family = case["family"].as_str().unwrap();
        if !family.contains("Scene") {
            continue;
        }
        scene_cases += 1;
        let receipt = &after.receipts()[0];
        let record = receipt.play().unwrap();
        assert_eq!(record.policy, OLD_SCENE);
        let recipe = if family.ends_with("Literal") {
            SceneRecipeV1::LiteralV1
        } else {
            SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1)
        };
        // The genuine old receipt is not retagged. The fresh gate must reject
        // its policy before a missing recording could be mistaken for proof.
        let missing = Value::Null;
        let checked = check_committed_scene_capture_v1(SceneCaptureInputV1 {
            before: &before,
            after: &after,
            request: receipt.request(),
            expected_recipe: recipe,
            expected_profile: &record.profile,
            attempt: 0,
            details_reply: &missing,
            recordings: &[],
        });
        assert!(matches!(checked, Err(SceneCaptureErrorV1::RecipeBinding)));
        assert_eq!(after.canonical_bytes(), expected);
    }
    assert_eq!(scene_cases, 8);
}

type Inventory = BTreeMap<PathBuf, (u64, String)>;
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, path: &Path, depth: usize, total: &mut u64, result: &mut Inventory) {
        assert!(depth <= 12 && result.len() < 4096);
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)] {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
        if metadata.is_dir() {
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), depth + 1, total, result);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            *total += metadata.len();
            assert!(*total <= 32 * 1024 * 1024);
            let raw = fs::read(path).unwrap();
            assert_eq!(raw.len() as u64, metadata.len());
            assert!(result.insert(path.strip_prefix(root).unwrap().to_owned(),
                (metadata.len(), digest(&raw))).is_none());
        }
    }
    let mut result = Inventory::new();
    visit(root, root, 0, &mut 0, &mut result);
    result
}

#[test]
#[ignore = "requires genuine pre-change captures; never fabricates or regenerates historical evidence"]
fn genuine_old_eval_committed_rows_remain_readable_without_relabel_or_mutation() {
    let root = PathBuf::from(std::env::var_os("LOCALLORE_LEGACY_COMPARISON_FIXTURES")
        .expect("explicit genuine old comparison fixtures required"));
    assert!(root.is_absolute() && root.is_dir());
    let before = inventory(&root);
    assert!(!before.is_empty());
    let old2 = comparison::inspect_comparison(&root.join("v2")).unwrap();
    let old3 = literal_v3::inspect_comparison(&root.join("v3")).unwrap();
    let old4 = scene_v4::inspect_comparison(&root.join("v4")).unwrap();
    assert!(!old2.source_matches && !old3.source_matches && !old4.source_matches);
    assert!(!old2.quality_accepted && !old3.quality_accepted && !old4.quality_accepted);
    assert_eq!(old2.completed_scenes, 1);
    assert_eq!(old3.completed_scenes, 1);
    assert_eq!(old4.completed_scenes, 1);
    assert!(old2.turns.iter().any(|row| row.phase == "committed" && row.policy_matches));
    assert!(old3.turns.iter().any(|row| row.phase == "committed" && row.construction_matches));
    assert!(old4.turns.iter().any(|row| row.phase == "committed" && row.construction_matches));
    assert_eq!(old3.arms, v3::arm_descriptors());
    assert_eq!(old4.arms, v4::arm_descriptors());
    assert_ne!(old3.arms, v3::current_arm_descriptors());
    assert_ne!(old4.arms, v4::current_arm_descriptors());
    assert!(old2.limitations.iter().any(|line| line.contains(OLD_ORDINARY)));
    assert_eq!(inventory(&root), before, "no old capture file may be rewritten or added");
}
