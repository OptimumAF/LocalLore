// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit manual producer for genuine pre-whole-word synthetic Eval captures.
//! Run only on the old production source; never retag current receipts.
use locallore::{inference::Cancellation, play};
use locallore_eval::local_lane::{
    comparison::{self, literal_v3, scene_v4, ComparisonKind},
    LaneFactory,
};
use std::{fs, path::PathBuf};

#[test]
#[ignore = "manual old-source fixture generation; requires a fresh explicitly selected directory"]
fn produce_genuine_pre_whole_word_comparisons() {
    assert_eq!(play::NARRATION_POLICY, "grounded-prose-v2.2");
    assert_eq!(
        play::scene_narration::SCENE_NARRATION_POLICY_V1,
        "grounded-prose-v2.4-scene-frame-v1"
    );
    let output = PathBuf::from(
        std::env::var_os("LOCALLORE_LEGACY_COMPARISON_OUTPUT")
            .expect("explicit create-only fixture output"),
    );
    assert!(output.is_absolute() && !output.exists());
    fs::create_dir(&output).unwrap();
    let cancel = Cancellation::default();
    let v2 = comparison::run_comparison(
        &output.join("v2"),
        false,
        ComparisonKind::ContinuousRollout,
        &cancel,
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let v3 = literal_v3::run_comparison(
        &output.join("v3"),
        false,
        ComparisonKind::ContinuousRollout,
        &cancel,
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let v4 = scene_v4::run_comparison(
        &output.join("v4"),
        false,
        ComparisonKind::ContinuousRollout,
        &cancel,
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    assert!(v2.turns.iter().any(|row| row.phase == "committed"));
    assert!(v3.turns.iter().any(|row| row.phase == "committed"));
    assert!(v4.turns.iter().any(|row| row.phase == "committed"));
    assert!(v3
        .arms
        .iter()
        .all(|arm| arm.narration_policy == "grounded-prose-v2.2"));
    assert!(v4
        .arms
        .iter()
        .all(|arm| arm.narration_policy == "grounded-prose-v2.4-scene-frame-v1"));
    println!(
        "genuine old synthetic comparison fixtures: {}",
        output.display()
    );
}
