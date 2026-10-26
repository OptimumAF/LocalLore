// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Core receipts/forks/replay over the frozen native source contract;
//! no provider, model, Host, Store, SQL writer, literal packer or execution lane.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    context_compiler::{
        player_literal_transcript_v1_cancelled, CompileError, LiteralTranscriptSourceV1,
    },
    contracts::*,
    engine::Engine,
};
use serde_json::{json, Value};
use std::cell::Cell;

fn seed() -> Seed {
    let mut s: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    s.facts.get_mut("ancestry").unwrap().proposition =
        "ELIGIBLE_SEED_FACT_IS_NOT_AN_OPENING".into();
    s.facts.get_mut("relic-location").unwrap().proposition =
        "SECRET_SEED_VALUE_IS_NOT_TRANSCRIPT".into();
    s.actors
        .get_mut("sable")
        .unwrap()
        .goals
        .insert("NPC_PRIVATE_GOAL_IS_NOT_TRANSCRIPT".into());
    s
}
fn engine() -> Engine {
    Engine::new(seed()).unwrap()
}
fn commit(e: &mut Engine, id: &str, intent: Intent) -> Receipt {
    let request = e.request(id, intent);
    let proposal = Engine::proposal(&request).unwrap();
    let candidate = e.preview(&request, &proposal).unwrap();
    e.commit_prepared(&candidate).unwrap()
}
fn dialogue(e: &mut Engine, id: &str, text: &str) -> Receipt {
    commit(
        e,
        id,
        Intent::Dialogue {
            text: text.into(),
            audience: ["mira".into()].into(),
        },
    )
}
fn source(e: &Engine) -> LiteralTranscriptSourceV1 {
    player_literal_transcript_v1_cancelled(
        e,
        e.scope(),
        e.revision(),
        e.seed().player.as_str(),
        &|| false,
    )
    .unwrap()
}
// Recompute the FROZEN private budget shape from getters. This is NOT public
// serialization of source/unit, and intentionally excludes the opaque basis.
fn budget_shape(s: &LiteralTranscriptSourceV1) -> Value {
    let units: Vec<_> = s.units().iter().map(|u| json!({
        "original_scope":u.original_scope(),"turn":u.turn(),"through_revision":u.through_revision(),
        "original_input":u.original_input(),"narration":u.narration(),
    })).collect();
    json!({"version":s.version(),"scope":s.scope(),"head":s.head(),"observer":s.observer(),"units":units})
}
fn assert_header(e: &Engine, s: &LiteralTranscriptSourceV1) {
    assert_eq!(s.version(), 1);
    assert_eq!(s.scope(), e.scope());
    assert_eq!(s.head(), e.revision());
    assert_eq!(s.observer(), e.seed().player);
    assert_eq!(s.accepted_basis(), &e.accepted_history_basis().unwrap());
    assert_eq!(
        s.budget_bytes(),
        serde_json::to_vec(&budget_shape(s)).unwrap().len()
    );
    assert!(s.budget_bytes() <= 2 * 1024 * 1024);
    assert!(s.units().len() <= 8192);
}

#[test]
fn empty_history_has_no_synthetic_opening_current_projection_or_hidden_seed_prose() {
    let e = engine();
    let bytes = e.canonical_bytes();
    let s = source(&e);
    assert_header(&e, &s);
    assert!(s.units().is_empty());
    let text = serde_json::to_string(&budget_shape(&s)).unwrap();
    let debug = format!("{s:?}");
    for forbidden in [
        "ELIGIBLE_SEED_FACT_IS_NOT_AN_OPENING",
        "SECRET_SEED_VALUE_IS_NOT_TRANSCRIPT",
        "NPC_PRIVATE_GOAL_IS_NOT_TRANSCRIPT",
        "Your words are heard",
        "potion",
    ] {
        assert!(!text.contains(forbidden));
        assert!(!debug.contains(forbidden));
    }
    assert_eq!(source(&e), s);
    assert_eq!(s.clone(), s);
    assert_eq!(bytes, e.canonical_bytes());
}

#[test]
fn unicode_quoted_backslash_input_and_actual_narration_survive_whole_typed_units_exactly() {
    let mut e = engine();
    let text = "雪 café \"quoted\" \\ harbor\nsecond line 🕯";
    let first = dialogue(&mut e, "literal-unicode", text);
    let typed = commit(
        &mut e,
        "typed-multi",
        Intent::Actions(vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 2 }]),
    );
    let canonical = e.canonical_bytes();
    let s = source(&e);
    assert_header(&e, &s);
    assert_eq!(
        s.units().len(),
        2,
        "one unit per whole receipt, not per event"
    );
    let a = &s.units()[0];
    assert_eq!(a.original_scope(), &first.request().scope);
    assert_eq!(a.turn(), first.request().turn);
    assert_eq!(
        a.through_revision(),
        first.events().last().unwrap().sequence()
    );
    assert_eq!(a.original_input(), Some(text));
    assert_eq!(a.narration(), Some(first.narration()));
    let b = &s.units()[1];
    assert_eq!(b.original_scope(), &typed.request().scope);
    assert_eq!(b.turn(), typed.request().turn);
    assert_eq!(
        b.through_revision(),
        typed.events().last().unwrap().sequence()
    );
    assert_eq!(b.original_input(), None);
    assert_eq!(b.narration(), Some(typed.narration()));
    assert_eq!(budget_shape(&s)["units"][1]["original_input"], Value::Null);
    assert!(budget_shape(&s)["units"][1]
        .as_object()
        .unwrap()
        .contains_key("original_input"));
    assert!(budget_shape(&s)["units"][1]
        .as_object()
        .unwrap()
        .contains_key("narration"));
    // No structured events, state, source dictionaries or fabricated input are
    // included by the source getters' exact budget/provenance representation.
    let encoded = serde_json::to_string(&budget_shape(&s)).unwrap();
    for forbidden in [
        "ELIGIBLE_SEED_FACT_IS_NOT_AN_OPENING",
        "NPC_PRIVATE_GOAL_IS_NOT_TRANSCRIPT",
        "SECRET_SEED_VALUE_IS_NOT_TRANSCRIPT",
        "canonical_truth",
        "witnesses",
        "claim_event",
    ] {
        assert!(!encoded.contains(forbidden));
    }
    assert_eq!(canonical, e.canonical_bytes());
}

#[test]
fn actual_root_replay_preserves_literal_source_and_opaque_basis_without_inference() {
    let mut e = engine();
    dialogue(&mut e, "one", "Original \"entry\" \\ 雪");
    commit(
        &mut e,
        "two",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let history: Vec<_> = e
        .receipts()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    let restored = Engine::restore(seed(), &history).unwrap();
    assert_eq!(restored.canonical_bytes(), e.canonical_bytes());
    let before = restored.canonical_bytes();
    assert_eq!(source(&restored), source(&e));
    assert_eq!(
        source(&restored).accepted_basis(),
        &restored.accepted_history_basis().unwrap()
    );
    assert_eq!(restored.canonical_bytes(), before);
}

#[test]
fn ordinary_forks_keep_original_scope_with_repeated_bare_ids_and_exclude_future_siblings() {
    let mut parent = engine();
    let inherited = dialogue(&mut parent, "same-id", "ROOT_LITERAL");
    let fork_at = parent.revision();
    let mut child = parent.fork("literal-child", fork_at).unwrap();
    let mut sibling = parent.fork("literal-sibling", fork_at).unwrap();
    dialogue(&mut parent, "future", "PARENT_FUTURE_MUST_NOT_APPEAR");
    dialogue(&mut sibling, "same-id", "SIBLING_MUST_NOT_APPEAR");
    let local = dialogue(&mut child, "same-id", "CHILD_LITERAL");
    let before = child.canonical_bytes();
    let s = source(&child);
    assert_header(&child, &s);
    assert_eq!(s.units().len(), 2);
    assert_eq!(s.units()[0].turn(), "same-id");
    assert_eq!(s.units()[1].turn(), "same-id");
    assert_eq!(s.units()[0].original_scope(), &inherited.request().scope);
    assert_eq!(s.units()[1].original_scope(), &local.request().scope);
    assert_ne!(s.units()[0].original_scope(), s.units()[1].original_scope());
    assert_eq!(s.units()[0].original_input(), Some("ROOT_LITERAL"));
    assert_eq!(s.units()[1].original_input(), Some("CHILD_LITERAL"));
    let encoded = serde_json::to_string(&budget_shape(&s)).unwrap();
    assert!(!encoded.contains("PARENT_FUTURE_MUST_NOT_APPEAR"));
    assert!(!encoded.contains("SIBLING_MUST_NOT_APPEAR"));
    let prefix = child.at_revision(fork_at).unwrap();
    let prefix_source = source(&prefix);
    assert_eq!(prefix_source.units().len(), 1);
    assert_eq!(prefix_source.units()[0].original_scope(), parent.scope());
    let nested = child.fork("literal-nested", fork_at).unwrap();
    let nested_source = source(&nested);
    assert_header(&nested, &nested_source);
    assert_eq!(nested_source.units().len(), 1);
    assert_eq!(
        nested_source.units()[0].original_input(),
        Some("ROOT_LITERAL")
    );
    let local_history = vec![serde_json::to_string(&local).unwrap()];
    let replayed = parent
        .at_revision(fork_at)
        .unwrap()
        .fork("literal-child", fork_at)
        .unwrap()
        .restore_continuation(&local_history)
        .unwrap();
    assert_eq!(source(&replayed), s);
    assert_eq!(child.canonical_bytes(), before);
}

#[test]
fn scope_head_player_and_domain_are_exact_closed_native_inputs() {
    let mut e = engine();
    dialogue(&mut e, "visible", "ACTUAL_LITERAL");
    let before = e.canonical_bytes();
    let mut foreign = e.scope().clone();
    foreign.story = "different-story".into();
    assert_eq!(
        player_literal_transcript_v1_cancelled(&e, &foreign, e.revision(), "player", &|| false)
            .unwrap_err(),
        CompileError::Scope
    );
    let mut wrong_branch = e.scope().clone();
    wrong_branch.branch = "different-branch".into();
    assert_eq!(
        player_literal_transcript_v1_cancelled(&e, &wrong_branch, e.revision(), "player", &|| {
            false
        })
        .unwrap_err(),
        CompileError::Scope
    );
    for head in [0, e.revision() + 1] {
        assert_eq!(
            player_literal_transcript_v1_cancelled(&e, e.scope(), head, "player", &|| false)
                .unwrap_err(),
            CompileError::Stale
        );
    }
    for observer in ["mira", "sable", "never-existed", ""] {
        assert_eq!(
            player_literal_transcript_v1_cancelled(&e, e.scope(), e.revision(), observer, &|| {
                false
            })
            .unwrap_err(),
            CompileError::Observer
        );
    }
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: e.scope().clone(),
        expected_parent_revision: e.revision(),
        fork_revision: e.revision(),
        child_branch: "literal-author-refused".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "ancestry".into(),
            expected_proposition: "ELIGIBLE_SEED_FACT_IS_NOT_AN_OPENING".into(),
            replacement: "PRIVATE_AUTHOR_WORLD".into(),
        },
        reason: "PRIVATE_AUTHOR_REASON".into(),
    };
    let prepared = e.prepare_author_correction(&input, &|| false).unwrap();
    let d2 = e
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .engine;
    assert_eq!(d2.domain_version(), 2);
    let d2_before = d2.canonical_bytes();
    assert_eq!(
        player_literal_transcript_v1_cancelled(&d2, d2.scope(), d2.revision(), "player", &|| false)
            .unwrap_err(),
        CompileError::UnsupportedPolicy
    );
    assert_eq!(e.canonical_bytes(), before);
    assert_eq!(d2.canonical_bytes(), d2_before);
}

#[test]
fn cancellation_panic_and_midvisit_cancellation_return_no_partial_source_or_mutation() {
    let mut e = engine();
    for n in 0..16 {
        dialogue(&mut e, &format!("cancel-{n}"), "RECORDED");
    }
    let bytes = e.canonical_bytes();
    let basis = e.accepted_history_basis().unwrap();
    assert_eq!(
        player_literal_transcript_v1_cancelled(&e, e.scope(), e.revision(), "player", &|| true)
            .unwrap_err(),
        CompileError::Cancelled
    );
    assert_eq!(
        player_literal_transcript_v1_cancelled(&e, e.scope(), e.revision(), "player", &|| panic!(
            "fixed cancellation callback panic"
        ))
        .unwrap_err(),
        CompileError::Cancelled
    );
    let calls = Cell::new(0);
    let cancel = || {
        let n = calls.get() + 1;
        calls.set(n);
        n >= 3
    };
    assert_eq!(
        player_literal_transcript_v1_cancelled(&e, e.scope(), e.revision(), "player", &cancel)
            .unwrap_err(),
        CompileError::Cancelled
    );
    assert!(calls.get() >= 3);
    let mut wrong = e.scope().clone();
    wrong.story = "wrong".into();
    // Cancellation is checked first and panic means cancellation, not a grant
    // to inspect even the otherwise-invalid caller's source.
    assert_eq!(
        player_literal_transcript_v1_cancelled(&e, &wrong, 0, "mira", &|| true).unwrap_err(),
        CompileError::Cancelled
    );
    assert_eq!(e.canonical_bytes(), bytes);
    assert_eq!(e.accepted_history_basis().unwrap(), basis);
    assert_eq!(source(&e).units().len(), 16);
}

#[test]
fn detached_source_remains_bound_to_exact_prefix_after_engine_advances() {
    let mut e = engine();
    dialogue(&mut e, "old", "OLD_LITERAL");
    let old = source(&e);
    let old_head = e.revision();
    let old_clone = old.clone();
    dialogue(&mut e, "new", "NEW_LITERAL");
    let current = source(&e);
    assert_eq!(old, old_clone);
    assert_eq!(old.units().len(), 1);
    assert_eq!(old.head(), old_head);
    assert_eq!(current.units().len(), 2);
    assert_ne!(old.accepted_basis(), current.accepted_basis());
    let prefix = e.at_revision(old_head).unwrap();
    assert_eq!(source(&prefix), old);
    assert_eq!(
        old.accepted_basis(),
        &prefix.accepted_history_basis().unwrap()
    );
    let mut other = engine();
    dialogue(&mut other, "old", "DIFFERENT_REAL_LITERAL");
    assert_eq!(other.scope(), prefix.scope());
    assert_eq!(other.revision(), prefix.revision());
    assert_ne!(source(&other).accepted_basis(), old.accepted_basis());
}

#[test]
fn actual_accepted_whole_units_cross_two_mib_and_fail_without_truncation() {
    // Dialogue accumulates state claims and reaches the existing 256KiB state
    // cap first. Use actual typed Wait receipts instead: constant projection,
    // long valid scope/turn IDs and actual 20-digit story-time narration.
    let mut seed = seed();
    seed.scope.story = "s".repeat(64);
    seed.scope.branch = "b".repeat(64);
    seed.story_time = u64::MAX - 4_000_000;
    let mut e = Engine::new(seed).unwrap();
    let mut budget = source(&e).budget_bytes();
    let mut previous_budget = budget;
    let mut previous_head = 0;
    let mut count = 0;
    for n in 0..3000 {
        previous_budget = budget;
        previous_head = e.revision();
        let receipt = commit(
            &mut e,
            &format!("large-{n:058}"),
            Intent::Actions(vec![Command::Wait { ticks: 1 }; MAX_COMMANDS]),
        );
        let encoded = json!({
            "original_scope":receipt.request().scope,"turn":receipt.request().turn,
            "through_revision":receipt.events().last().unwrap().sequence(),
            "original_input":null,"narration":receipt.narration(),
        });
        budget += serde_json::to_vec(&encoded).unwrap().len()
            + usize::from(n != 0)
            + e.revision().to_string().len()
            - previous_head.to_string().len();
        count += 1;
        if budget > 2 * 1024 * 1024 {
            break;
        }
    }
    assert!(
        budget > 2 * 1024 * 1024,
        "genuine accepted fixture must reach source cap"
    );
    let prefix = e.at_revision(previous_head).unwrap();
    let before_limit = source(&prefix);
    assert_eq!(before_limit.units().len(), count - 1);
    assert_eq!(before_limit.budget_bytes(), previous_budget);
    assert!(previous_budget <= 2 * 1024 * 1024);
    assert_header(&prefix, &before_limit);
    let bytes = e.canonical_bytes();
    assert!(bytes.len() <= MAX_HISTORY_BYTES);
    eprintln!("LITERAL_SOURCE_CAP actual_units={count} previous_bytes={previous_budget} rejected_bytes={budget} canonical_bytes={}", bytes.len());
    let basis = e.accepted_history_basis().unwrap();
    assert_eq!(
        player_literal_transcript_v1_cancelled(&e, e.scope(), e.revision(), "player", &|| false)
            .unwrap_err(),
        CompileError::TooLarge
    );
    assert_eq!(e.canonical_bytes(), bytes);
    assert_eq!(e.accepted_history_basis().unwrap(), basis);
    // Count8192 is not claimed executed: Core's own4096 receipt cap and this
    // earlier byte cap prevent a genuine 8193-unit fixture via current APIs.
}
