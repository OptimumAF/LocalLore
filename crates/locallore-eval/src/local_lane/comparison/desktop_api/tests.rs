// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Four frozen private checked_edges guards, UNCOMPILED/UNRUN by the author.
//! Based on ddcecbbc81c08f2340b9076aa063160652df1c49; #29 claim6393757495.
//! Root registers only #[cfg(test)] mod tests; in desktop_api.rs.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --lib local_lane::comparison::desktop_api::tests:: -- --nocapture --test-threads=1
//! Existing public scripted producer is fake plumbing, not a real-model claim.
//! Alternative histories use actual Core previews/commits, never deserialized
//! accepted receipts or canonical SQL. Changed expected hashes are deliberately
//! untrusted cloned checkpoint diagnostics, not fabricated accepted authority.

use super::*;
use crate::{
    local_lane::{
        comparison::{run_comparison, ComparisonKind},
        LaneFactory,
    },
    memory_comparison::frozen_suite,
    memory_comparison_v2::{mechanical_output, semantic_input, semantic_output},
};
use locallore::{
    contracts::{Command, Intent},
    inference::Cancellation,
    inspection_query::{Observer, View},
};
use locallore_storage::Store;
use std::sync::OnceLock;

fn actual_turn() -> (Engine, StoredTurn) {
    static PRODUCER: OnceLock<PathBuf> = OnceLock::new();
    let directory = PRODUCER.get_or_init(|| {
        let parent = std::env::temp_dir().join(format!(
            "locallore-reader-edge-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&parent).unwrap();
        let run = parent.join("run");
        let report = run_comparison(
            &run,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!(report.turns.len(), 12);
        assert!(report.turns.iter().all(|row| row.passed));
        // Only these newly owned synthetic files are retained for Root diagnosis.
        run
    });
    let turn: StoredTurn = decode(&directory.join("left/attempt-01.json"), 256 * 1024).unwrap();
    assert_eq!(turn.row.turn, frozen_suite().unwrap().steps()[1].id());
    assert_eq!(turn.row.phase, "committed");
    assert_eq!(turn.before_head, 1);
    assert_eq!(turn.after_head, 2);
    let full = Store::open_read_only(&directory.join("left/synthetic.sqlite"))
        .unwrap()
        .resume(&frozen_suite().unwrap().seed().scope)
        .unwrap()
        .engine;
    (full, turn)
}

fn accepted_after(before: &Engine, turn: &str, command: Command) -> Engine {
    let mut after = before.clone();
    let request = after.request(turn, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = after.preview(&request, &proposal).unwrap();
    after.commit_prepared(&receipt).unwrap();
    after
}

fn mismatch(full: &Engine, turn: &StoredTurn) {
    // Engine's existing debug traits are not required for failure extraction.
    let error = match checked_edges(full, turn) {
        Ok(_) => panic!("must reject different bound edges"),
        Err(error) => error,
    };
    assert_eq!(error, "SnapshotMismatch");
}

#[test]
fn actual_producer_edges_pass_and_are_the_actual_immutable_query2_engines() {
    let (full, turn) = actual_turn();
    let original_records = full.canonical_records().to_vec();
    let original_projection = full.canonical_bytes();
    let (before, after) = checked_edges(&full, &turn).unwrap();
    assert_eq!(before.scope(), &turn.request.scope);
    assert_eq!(after.scope(), &turn.request.scope);
    assert_eq!(before.revision(), turn.before_head);
    assert_eq!(after.revision(), turn.after_head);
    assert_eq!(before.seed(), full.seed());
    assert_eq!(after.seed(), full.seed());
    assert_eq!(
        semantic_input(&before, &turn.request).unwrap(),
        turn.row.input_semantic_sha256
    );
    assert_eq!(
        semantic_output(&after).unwrap(),
        turn.row.output_semantic_sha256
    );
    assert_eq!(
        mechanical_output(&after).unwrap(),
        turn.row.mechanical_sha256
    );
    for (cut, head) in [(&before, turn.before_head), (&after, turn.after_head)] {
        let expected = full.at_revision(head).unwrap();
        assert_eq!(cut.canonical_records(), expected.canonical_records());
        assert_eq!(cut.canonical_bytes(), expected.canonical_bytes());
        assert!(
            cut.accepted_history_basis().unwrap() == expected.accepted_history_basis().unwrap()
        );
        for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
            let request = Query {
                version: 2,
                scope: cut.scope().clone(),
                expected_head: head,
                at_revision: None,
                observer,
                view: View::Knowledge,
                cursor: None,
                limit: MAX_ROWS,
                search: String::new(),
            };
            let actual = inspection_query::query(cut, &request, true).unwrap();
            let original = inspection_query::query(&expected, &request, true).unwrap();
            assert_eq!(actual, original);
            assert_eq!(actual.head, head);
            assert_eq!(actual.revision, head);
        }
    }
    assert_eq!(full.canonical_records(), original_records);
    assert_eq!(full.canonical_bytes(), original_projection);
}

#[test]
fn same_seed_scope_and_heads_with_valid_different_prefix_refuses_input_binding() {
    let (full, mut turn) = actual_turn();
    let original_before = full.at_revision(turn.before_head).unwrap();
    let original_after = full.at_revision(turn.after_head).unwrap();
    let empty = Engine::new(full.seed().clone()).unwrap();
    let other_before = accepted_after(
        &empty,
        "other-valid-prefix",
        Command::Say {
            text: "SYNTHETIC_DIFFERENT_ACCEPTED_PREFIX".into(),
            audience: ["mira".into()].into(),
        },
    );
    let other_after = accepted_after(
        &other_before,
        &turn.request.turn,
        Command::Learn {
            ability: "beacon".into(),
        },
    );
    assert_eq!(other_before.seed(), original_before.seed());
    assert_eq!(other_before.scope(), original_before.scope());
    assert_eq!(other_before.revision(), original_before.revision());
    assert_eq!(other_after.revision(), original_after.revision());
    assert_ne!(
        other_before.canonical_records(),
        original_before.canonical_records()
    );
    assert_ne!(
        semantic_input(&other_before, &turn.request).unwrap(),
        turn.row.input_semantic_sha256
    );
    // Make both after expectations correct for the alternative actual Core
    // history. Only the retained ORIGINAL input-prefix expectation is wrong.
    turn.row.output_semantic_sha256 = semantic_output(&other_after).unwrap();
    turn.row.mechanical_sha256 = mechanical_output(&other_after).unwrap();
    mismatch(&other_after, &turn);
}

#[test]
fn same_valid_input_prefix_but_different_actual_core_after_refuses_output_semantics() {
    let (full, mut turn) = actual_turn();
    let before = full.at_revision(turn.before_head).unwrap();
    let actual_after = full.at_revision(turn.after_head).unwrap();
    let other_after = accepted_after(&before, &turn.request.turn, Command::Wait { ticks: 1 });
    assert_eq!(other_after.seed(), actual_after.seed());
    assert_eq!(other_after.scope(), actual_after.scope());
    assert_eq!(other_after.revision(), actual_after.revision());
    assert_eq!(
        semantic_input(
            &other_after.at_revision(turn.before_head).unwrap(),
            &turn.request
        )
        .unwrap(),
        turn.row.input_semantic_sha256
    );
    assert_ne!(
        semantic_output(&other_after).unwrap(),
        turn.row.output_semantic_sha256
    );
    // Bind the mechanical expectation to the actual alternate Core result,
    // isolating the retained semantic-output mismatch from the other guards.
    turn.row.mechanical_sha256 = mechanical_output(&other_after).unwrap();
    mismatch(&other_after, &turn);
}

#[test]
fn correct_actual_input_and_semantic_edges_refuse_another_valid_mechanical_expectation() {
    let (full, mut turn) = actual_turn();
    let before = full.at_revision(turn.before_head).unwrap();
    let after = full.at_revision(turn.after_head).unwrap();
    let other_after = accepted_after(&before, &turn.request.turn, Command::Wait { ticks: 1 });
    let other_mechanical = mechanical_output(&other_after).unwrap();
    assert_ne!(other_mechanical, turn.row.mechanical_sha256);
    assert_eq!(
        semantic_input(&before, &turn.request).unwrap(),
        turn.row.input_semantic_sha256
    );
    assert_eq!(
        semantic_output(&after).unwrap(),
        turn.row.output_semantic_sha256
    );
    // Expected diagnostic comes from another genuinely accepted Core history,
    // while both actual selected engines and their semantic hashes remain valid.
    turn.row.mechanical_sha256 = other_mechanical;
    mismatch(&full, &turn);
}
