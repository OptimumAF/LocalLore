//! Frozen actual Core/compiler policy oracles before production changes. No model.
use locallore::{
    author_correction::*,
    context_compiler::*,
    contracts::*,
    engine::Engine,
    inspection_query::{self, Observer, Query, Row, Source, ValueOrigin, View},
    memory_coverage::*,
};
fn engine() -> Engine {
    let mut s: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let f = s.facts.get_mut("relic-location").unwrap();
    f.proposition = "KNOWN_A".into();
    f.discoverable_at = Some("quay".into());
    f.known_by.insert("mira".into());
    s.facts.get_mut("ancestry").unwrap().proposition = "PLAYER_SECRET".into();
    Engine::new(s).unwrap()
}
fn commit(e: &mut Engine, key: &str, commands: Vec<Command>) {
    let r = e.request(key, Intent::Actions(commands));
    let p = e.preview(&r, &Engine::proposal(&r).unwrap()).unwrap();
    e.commit_prepared(&p).unwrap();
}
fn say(text: &str, audience: &str) -> Command {
    Command::Say {
        text: text.into(),
        audience: [audience.into()].into(),
    }
}
fn author(e: &Engine) -> Engine {
    let i = AuthorCorrectionInputV1 {
        version: 1,
        parent: e.scope().clone(),
        expected_parent_revision: e.revision(),
        fork_revision: e.revision(),
        child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "KNOWN_A".into(),
            replacement: "PRIVATE_B".into(),
        },
        reason: "PRIVATE_REASON".into(),
    };
    e.apply_author_correction(
        &e.prepare_author_correction(&i, &|| false).unwrap(),
        &|| false,
    )
    .unwrap()
    .engine
}
fn request(e: &Engine, observer: &str) -> CompileRequest {
    CompileRequest {
        version: 2,
        scope: e.scope().clone(),
        expected_head: e.revision(),
        at_revision: None,
        observer: observer.into(),
        role: if observer == "player" {
            Role::Director
        } else {
            Role::Character
        },
        query: String::new(),
        referenced_ids: vec![],
        budget: Budget {
            recent_events: 0,
            optional_records: 2,
            ..Budget::default()
        },
    }
}
fn run(e: &Engine, q: &CompileRequest, p: ContextPolicy) -> PolicyCompilation {
    compile_policy_cancelled(e, q, p, None, &|| false).unwrap()
}
fn units(p: &PolicyCompilation) -> Vec<&TranscriptUnit> {
    p.compilation
        .package
        .records
        .iter()
        .filter_map(|s| match &s.payload {
            Payload::TranscriptUnit(u) => Some(u.as_ref()),
            _ => None,
        })
        .collect()
}
fn mandatory(p: &PolicyCompilation) -> Vec<&Selected> {
    p.compilation
        .package
        .records
        .iter()
        .filter(|s| s.mandatory)
        .collect()
}
fn encoded(v: impl serde::Serialize) -> String {
    serde_json::to_string(&v).unwrap()
}
fn proof(e: &Engine, observer: &str) -> VerifiedCoverage {
    let packet = build_chunk(
        e,
        &ChunkRequest {
            scope: e.scope().clone(),
            expected_head: e.revision(),
            observer: observer.into(),
            from_exclusive: 0,
        },
        &|| false,
    )
    .unwrap()
    .unwrap();
    let bytes = packet.bytes().unwrap();
    match verify_coverage(
        e,
        &CoverageRequest {
            scope: e.scope().clone(),
            expected_head: e.revision(),
            observer: observer.into(),
        },
        &[bytes.as_slice()],
        &|| false,
    )
    .unwrap()
    {
        CoverageRead::Verified(p) => p,
        _ => panic!("actual proof unavailable"),
    }
}

#[test]
fn legacy_entries_refuse_domain2_before_accepting_any_old_proof() {
    let mut root = engine();
    commit(&mut root, "old", vec![say("old", "mira")]);
    let p = proof(&root, "player");
    let e = author(&root);
    let mut q = request(&e, "player");
    q.version = 1;
    assert_eq!(compile(&e, &q).unwrap_err(), CompileError::Version);
    assert_eq!(
        compile_cancelled(&e, &q, &|| false).unwrap_err(),
        CompileError::Version
    );
    assert_eq!(
        compile_verified_cancelled(&e, &q, Some(&p), &|| false).unwrap_err(),
        CompileError::Version
    );
}
#[test]
fn both_actual_policies_share_mandatory_observed_state_and_private_truth_is_absent() {
    let e = author(&engine());
    let q = request(&e, "player");
    let a = run(&e, &q, ContextPolicy::StateRecentTranscriptV1);
    let b = run(&e, &q, ContextPolicy::StateRelevantMemoryV1);
    assert_eq!(mandatory(&a), mandatory(&b));
    assert_eq!(a.compilation.package.version, 2);
    assert_eq!(a.policy, ContextPolicy::StateRecentTranscriptV1);
    assert_eq!(b.policy, ContextPolicy::StateRelevantMemoryV1);
    for p in [&a, &b] {
        assert!(p.compilation.package.records.iter().any(|s|s.kind==Kind::KnownAsObserved&&s.reason==Reason::KnownAsObserved&&matches!(&s.payload,Payload::Record(r) if matches!(r.as_ref(),Row::Knowledge{id,text,origin:ValueOrigin::KnownAsObserved,..} if id=="relic-location" && text=="KNOWN_A"))));
        for canary in ["PRIVATE_B", "PRIVATE_REASON", "truth_source"] {
            assert!(!encoded(&p.compilation.package).contains(canary));
        }
        assert_eq!(p.compilation.coverage.mode, CoverageMode::Raw);
        assert_eq!(
            p.compilation.coverage.set_fallback_reason,
            Some(MemoryFallbackReason::Unsupported)
        );
    }
}
#[test]
fn actual_discovery_changes_player_value_but_not_npc_memory() {
    let mut e = author(&engine());
    commit(
        &mut e,
        "discover",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    for policy in [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ] {
        let player = run(&e, &request(&e, "player"), policy);
        let npc = run(&e, &request(&e, "mira"), policy);
        assert!(mandatory(&player).iter().any(|r|matches!(&r.payload,Payload::Record(v) if matches!(v.as_ref(),Row::Knowledge{id,text,sources,..} if id=="relic-location" && text=="PRIVATE_B" && sources==&vec![Source::ScopedEvent{original_scope:e.scope().clone(),sequence:2}]))));
        assert!(!encoded(&npc.compilation.package).contains("PRIVATE_B"));
        assert!(encoded(&npc.compilation.package).contains("KNOWN_A"));
    }
}
#[test]
fn relevant_old_detail_and_real_recent_whole_units_are_distinct_optional_choices() {
    let mut e = engine();
    commit(
        &mut e,
        "old-detail",
        vec![say("AMBER_ARCHIVE_TOKEN", "mira")],
    );
    for n in 0..8 {
        commit(
            &mut e,
            &format!("recent-{n}"),
            vec![say(&format!("new words {n}"), "mira")],
        );
    }
    let mut q = request(&e, "player");
    q.query = "AMBER_ARCHIVE_TOKEN".into();
    let recent = run(&e, &q, ContextPolicy::StateRecentTranscriptV1);
    let relevant = run(&e, &q, ContextPolicy::StateRelevantMemoryV1);
    assert_eq!(mandatory(&recent), mandatory(&relevant));
    assert!(encoded(&relevant.compilation.package).contains("AMBER_ARCHIVE_TOKEN"));
    assert!(!encoded(&recent.compilation.package).contains("AMBER_ARCHIVE_TOKEN"));
    assert_eq!(
        units(&recent)
            .iter()
            .map(|u| u.turn.as_str())
            .collect::<Vec<_>>(),
        vec!["recent-6", "recent-7"]
    );
    assert!(units(&relevant).is_empty());
    assert_eq!(recent.construction.selected_transcript_units, 2);
    assert_eq!(relevant.construction.selected_transcript_units, 0);
}
#[test]
fn mandatory_recent_floor_excludes_entire_overlapping_multi_event_unit() {
    let mut e = engine();
    commit(
        &mut e,
        "older",
        vec![say("first", "mira"), say("second", "mira")],
    );
    commit(
        &mut e,
        "newer",
        vec![say("third", "mira"), say("fourth", "mira")],
    );
    let mut q = request(&e, "player");
    q.budget.recent_events = 1;
    let p = run(&e, &q, ContextPolicy::StateRecentTranscriptV1);
    let us = units(&p);
    assert_eq!(us.len(), 1);
    assert_eq!(us[0].turn, "older");
    assert_eq!(us[0].events.len(), 2);
    assert_eq!(p.construction.eligible_transcript_units, 2);
    assert_eq!(p.construction.overlap_transcript_units, 1);
    assert_eq!(p.construction.selected_transcript_units, 1);
    let selected = mandatory(&p)
        .iter()
        .flat_map(|s| s.sources.iter())
        .filter_map(|s| match s {
            Source::ScopedEvent {
                original_scope,
                sequence,
            } => Some((original_scope.clone(), *sequence)),
            _ => None,
        })
        .collect::<std::collections::BTreeSet<_>>();
    for event in &us[0].events {
        assert!(!selected.contains(&(event.event.scope().clone(), event.event.sequence())));
    }
}
#[test]
fn query2_whole_player_eligibility_and_npc_event_only_units_match_actual_core() {
    let mut e = author(&engine());
    for n in 0..2 {
        let r = e.request(
            &format!("dialogue-{n}"),
            Intent::Dialogue {
                text: format!("ACTUAL_INPUT_{n}"),
                audience: ["mira".into()].into(),
            },
        );
        let v = e.preview(&r, &Engine::proposal(&r).unwrap()).unwrap();
        e.commit_prepared(&v).unwrap();
    }
    commit(
        &mut e,
        "private",
        vec![say("PRIVATE_PLAYER_INPUT", "player")],
    );
    let mut q = request(&e, "player");
    q.budget.optional_records = 8;
    let p = run(&e, &q, ContextPolicy::StateRecentTranscriptV1);
    let page = inspection_query::query(
        &e,
        &Query {
            version: 2,
            scope: e.scope().clone(),
            expected_head: e.revision(),
            at_revision: None,
            observer: Observer::Player,
            view: View::History,
            cursor: None,
            limit: 64,
            search: String::new(),
        },
        false,
    )
    .unwrap();
    for unit in units(&p) {
        let actual = e
            .canonical_records()
            .iter()
            .filter_map(|r| r.receipt())
            .find(|r| r.request().scope == unit.original_scope && r.request().turn == unit.turn)
            .unwrap();
        assert_eq!(
            unit.events
                .iter()
                .map(|v| (v.event.scope(), v.event.sequence()))
                .collect::<Vec<_>>(),
            actual
                .events()
                .iter()
                .map(|v| (v.scope(), v.sequence()))
                .collect::<Vec<_>>()
        );
        assert_eq!(unit.narration.as_deref(), Some(actual.narration()));
        if let Some(text) = &unit.original_input {
            assert!(page.rows.iter().any(|r|matches!(r,Row::Message{turn,text:t,message_kind,..} if turn==&unit.turn && text==t && message_kind=="original_input")));
        }
    }
    q.observer = "mira".into();
    q.role = Role::Character;
    let npc = run(&e, &q, ContextPolicy::StateRecentTranscriptV1);
    assert_eq!(npc.construction.eligible_transcript_units, 2);
    for unit in units(&npc) {
        assert!(unit.original_input.is_none());
        assert!(unit.narration.is_none());
        assert!(unit
            .events
            .iter()
            .all(|v| v.event.witnesses().contains("mira")));
    }
    for secret in [
        "PRIVATE_PLAYER_INPUT",
        "PLAYER_SECRET",
        "PRIVATE_B",
        "PRIVATE_REASON",
        "ACTUAL_INPUT",
    ] {
        assert!(!encoded(&npc.compilation.package).contains(secret));
    }
}
#[test]
fn relevant_raw_and_actual_verified_inputs_keep_identical_package2_payloads() {
    let mut e = engine();
    for n in 0..8 {
        commit(
            &mut e,
            &format!("say-{n}"),
            vec![say(&format!("ledger token {n}"), "mira")],
        );
    }
    let p = proof(&e, "mira");
    let mut q = request(&e, "mira");
    q.query = "ledger".into();
    let raw = run(&e, &q, ContextPolicy::StateRelevantMemoryV1);
    let cached = compile_policy_cancelled(
        &e,
        &q,
        ContextPolicy::StateRelevantMemoryV1,
        Some(&p),
        &|| false,
    )
    .unwrap();
    assert_eq!(raw.compilation.package, cached.compilation.package);
    assert_eq!(cached.compilation.coverage.mode, CoverageMode::Verified);
    assert!(cached.compilation.coverage.cached_event_candidates > 0);
    assert_eq!(cached.construction.selected_transcript_units, 0);
}
#[test]
fn recent_and_domain2_do_not_relabel_old_proofs_as_transcript_or_new_observed_coverage() {
    let mut root = engine();
    commit(&mut root, "old", vec![say("old", "mira")]);
    let p = proof(&root, "player");
    let recent = compile_policy_cancelled(
        &root,
        &request(&root, "player"),
        ContextPolicy::StateRecentTranscriptV1,
        Some(&p),
        &|| false,
    )
    .unwrap();
    let e = author(&root);
    for value in [
        recent,
        compile_policy_cancelled(
            &e,
            &request(&e, "player"),
            ContextPolicy::StateRelevantMemoryV1,
            Some(&p),
            &|| false,
        )
        .unwrap(),
    ] {
        assert_eq!(value.compilation.coverage.mode, CoverageMode::Raw);
        assert_eq!(
            value.compilation.coverage.set_fallback_reason,
            Some(MemoryFallbackReason::Unsupported)
        );
        assert_eq!(value.compilation.coverage.cached_event_candidates, 0);
        assert_eq!(value.compilation.coverage.packets_used, 0);
    }
}
#[test]
fn branch_sources_future_sibling_and_prebirth_are_filtered_before_policy_units() {
    let mut parent = author(&engine());
    commit(&mut parent, "retained", vec![say("RETAINED_WORDS", "mira")]);
    let mut child = parent.fork("child", 2).unwrap();
    let mut sibling = parent.fork("sibling", 2).unwrap();
    commit(&mut parent, "future", vec![say("PARENT_FUTURE", "mira")]);
    commit(&mut sibling, "sibling", vec![say("SIBLING_ONLY", "mira")]);
    commit(&mut child, "local", vec![say("LOCAL_WORDS", "mira")]);
    let p = run(
        &child,
        &request(&child, "mira"),
        ContextPolicy::StateRecentTranscriptV1,
    );
    assert!(units(&p)
        .iter()
        .any(|u| u.original_scope.branch == "authored"));
    for canary in ["PARENT_FUTURE", "SIBLING_ONLY", "PRIVATE_REASON"] {
        assert!(!encoded(&p.compilation.package).contains(canary));
    }
    let prebirth = child.fork("prebirth", 0).unwrap();
    let p = run(
        &prebirth,
        &request(&prebirth, "player"),
        ContextPolicy::StateRecentTranscriptV1,
    );
    assert_eq!(p.construction.eligible_transcript_units, 0);
    assert!(encoded(&p.compilation.package).contains("KNOWN_A"));
}
#[test]
fn policy_versions_bounds_alias_and_panicking_cancel_fail_without_mutation() {
    let e = author(&engine());
    let basis = e.accepted_history_basis().unwrap();
    let q = request(&e, "player");
    for policy in [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ] {
        let mut bad = q.clone();
        bad.version = 1;
        assert_eq!(
            compile_policy_cancelled(&e, &bad, policy, None, &|| false).unwrap_err(),
            CompileError::Version
        );
        let mut bad = q.clone();
        bad.expected_head += 1;
        assert_eq!(
            compile_policy_cancelled(&e, &bad, policy, None, &|| false).unwrap_err(),
            CompileError::Stale
        );
        let mut bad = q.clone();
        bad.scope.branch = "wrong".into();
        assert_eq!(
            compile_policy_cancelled(&e, &bad, policy, None, &|| false).unwrap_err(),
            CompileError::Scope
        );
        let mut bad = q.clone();
        bad.referenced_ids = vec!["unknown".into()];
        assert_eq!(
            compile_policy_cancelled(&e, &bad, policy, None, &|| false).unwrap_err(),
            CompileError::UnknownReference
        );
        assert_eq!(
            compile_policy_cancelled(&e, &q, policy, None, &|| panic!("synthetic cancellation"))
                .unwrap_err(),
            CompileError::Cancelled
        );
    }
    assert_eq!(basis, e.accepted_history_basis().unwrap());
}
#[test]
fn mandatory_and_whole_unit_budgets_never_silently_truncate_or_change_canon() {
    let mut e = engine();
    commit(
        &mut e,
        "escaped",
        vec![say(&"\u{0001}".repeat(2048), "mira")],
    );
    let before = e.accepted_history_basis().unwrap();
    let mut q = request(&e, "player");
    q.budget.estimated_tokens = 1;
    q.budget.reserved_tokens = 0;
    q.budget.max_bytes = 1024;
    for policy in [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ] {
        assert_eq!(
            compile_policy_cancelled(&e, &q, policy, None, &|| false).unwrap_err(),
            CompileError::MandatoryBudget
        );
    }
    q.budget = Budget {
        recent_events: 0,
        optional_records: 1,
        ..Budget::default()
    };
    let p = run(&e, &q, ContextPolicy::StateRecentTranscriptV1);
    for unit in units(&p) {
        assert_eq!(unit.events.len(), 1);
        assert_eq!(unit.narration.as_deref(), Some(e.receipts()[0].narration()));
    }
    assert!(serde_json::to_vec(&p.compilation.package).unwrap().len() <= q.budget.max_bytes);
    assert_eq!(before, e.accepted_history_basis().unwrap());
}
#[test]
fn requested_policy_labels_are_closed_and_coverage_is_a_separate_result() {
    assert_eq!(
        encoded(ContextPolicy::StateRecentTranscriptV1),
        "\"state_recent_transcript_v1\""
    );
    assert_eq!(
        encoded(ContextPolicy::StateRelevantMemoryV1),
        "\"state_relevant_memory_v1\""
    );
    assert!(serde_json::from_str::<ContextPolicy>("\"verified_enabled\"").is_err());
    let e = engine();
    let p = run(
        &e,
        &request(&e, "player"),
        ContextPolicy::StateRecentTranscriptV1,
    );
    assert_eq!(p.policy, ContextPolicy::StateRecentTranscriptV1);
    assert_eq!(p.compilation.coverage.mode, CoverageMode::Raw);
    assert_eq!(p.construction.eligible_transcript_units, 0);
}
