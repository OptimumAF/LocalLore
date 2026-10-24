//! Independent compiler2 source-frozen review oracles; no model or Store.
use locallore::{
    author_correction::*,
    context_compiler::*,
    contracts::*,
    engine::Engine,
    inspection_query::{Row, ValueOrigin},
};

fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "OBSERVED_A".into();
    fact.known_by.insert("mira".into());
    Engine::new(seed).unwrap()
}
fn say(text: &str, audience: &str) -> Command {
    Command::Say {
        text: text.into(),
        audience: [audience.into()].into(),
    }
}
fn commit(engine: &mut Engine, key: &str, commands: Vec<Command>) -> Receipt {
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&preview).unwrap()
}
fn authored(parent: &Engine) -> Engine {
    let request = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "OBSERVED_A".into(),
            replacement: "PRIVATE_WORLD_B".into(),
        },
        reason: "PRIVATE_AUTHOR_POLICY_REASON".into(),
    };
    let plan = parent
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine
}
fn request(engine: &Engine, observer: &str) -> CompileRequest {
    CompileRequest {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: observer.into(),
        role: if observer == engine.seed().player {
            Role::Director
        } else {
            Role::Character
        },
        query: String::new(),
        referenced_ids: vec![],
        budget: Budget {
            estimated_tokens: 20000,
            reserved_tokens: 0,
            recent_events: 0,
            optional_records: 4,
            ..Budget::default()
        },
    }
}
fn run(engine: &Engine, request: &CompileRequest, policy: ContextPolicy) -> PolicyCompilation {
    compile_policy_cancelled(engine, request, policy, None, &|| false).unwrap()
}
fn units(compilation: &PolicyCompilation) -> Vec<&TranscriptUnit> {
    compilation
        .compilation
        .package
        .records
        .iter()
        .filter_map(|r| match &r.payload {
            Payload::TranscriptUnit(unit) => Some(unit.as_ref()),
            _ => None,
        })
        .collect()
}
fn mandatory(compilation: &PolicyCompilation) -> Vec<&Selected> {
    compilation
        .compilation
        .package
        .records
        .iter()
        .filter(|r| r.mandatory)
        .collect()
}

#[test]
fn mixed_private_and_public_receipt_gives_npc_only_eligible_event_subset_and_no_raw_attachment() {
    let mut engine = fixture();
    let receipt = commit(
        &mut engine,
        "mixed",
        vec![
            say("PRIVATE_SELF_ONLY_POLICY_CANARY", "player"),
            say("HEARD_PUBLIC_POLICY_WORDS", "mira"),
        ],
    );
    assert_eq!(receipt.events().len(), 2);
    let npc = run(
        &engine,
        &request(&engine, "mira"),
        ContextPolicy::StateRecentTranscriptV1,
    );
    let npc_units = units(&npc);
    assert_eq!(npc_units.len(), 1);
    assert_eq!(npc_units[0].events.len(), 1);
    assert_eq!(npc_units[0].events[0].event, receipt.events()[1]);
    assert!(npc_units[0].original_input.is_none() && npc_units[0].narration.is_none());
    let encoded = serde_json::to_string(&npc.compilation.package).unwrap();
    assert!(encoded.contains("HEARD_PUBLIC_POLICY_WORDS"));
    assert!(!encoded.contains("PRIVATE_SELF_ONLY_POLICY_CANARY"));
    let player = run(
        &engine,
        &request(&engine, "player"),
        ContextPolicy::StateRecentTranscriptV1,
    );
    let player_units = units(&player);
    assert_eq!(player_units.len(), 1);
    assert_eq!(
        player_units[0]
            .events
            .iter()
            .map(|e| &e.event)
            .collect::<Vec<_>>(),
        receipt.events().iter().collect::<Vec<_>>()
    );
    assert_eq!(
        player_units[0].narration.as_deref(),
        Some(receipt.narration())
    );
    assert_eq!(npc.construction.eligible_transcript_units, 1);
    assert_eq!(npc.construction.selected_transcript_units, 1);
}

#[test]
fn newest_oversized_whole_unit_is_skipped_and_older_fitting_unit_remains_complete() {
    let mut engine = fixture();
    let older = commit(
        &mut engine,
        "older-fitting",
        vec![say("OLDER_COMPLETE_WORDS", "mira")],
    );
    let escaped = "\u{0001}".repeat(2048);
    let newest_request = engine.request(
        "newest-oversized",
        Intent::Dialogue {
            text: escaped.clone(),
            audience: ["mira".into()].into(),
        },
    );
    let newest_proposal = Engine::proposal(&newest_request).unwrap();
    let newest_preview = engine.preview(&newest_request, &newest_proposal).unwrap();
    let newest = engine.commit_prepared(&newest_preview).unwrap();
    let view = engine
        .actor_receipts_v2("player", engine.scope(), engine.revision())
        .unwrap()
        .pop()
        .unwrap();
    let expected_newest = TranscriptUnit {
        original_scope: view.original_scope,
        turn: view.turn,
        events: view.events,
        original_input: Some(escaped),
        narration: Some(newest.narration().into()),
    };
    assert!(
        serde_json::to_vec(&expected_newest).unwrap().len() > MAX_CONTEXT_BYTES,
        "fixture must exceed entire context byte bound before mandatory records"
    );
    let q = request(&engine, "player");
    let before = engine.accepted_history_basis().unwrap();
    let result = run(&engine, &q, ContextPolicy::StateRecentTranscriptV1);
    let selected = units(&result);
    assert_eq!(selected.len(), 1);
    assert_eq!(selected[0].turn, "older-fitting");
    assert_eq!(selected[0].events.len(), 1);
    assert_eq!(selected[0].events[0].event, older.events()[0]);
    assert_eq!(selected[0].narration.as_deref(), Some(older.narration()));
    assert!(result
        .compilation
        .package
        .diagnostics
        .omissions
        .iter()
        .any(|o| o.id.contains("newest-oversized") && o.reason == Reason::Budget));
    assert_eq!(result.construction.eligible_transcript_units, 2);
    assert_eq!(result.construction.selected_transcript_units, 1);
    assert!(
        serde_json::to_vec(&result.compilation.package)
            .unwrap()
            .len()
            <= q.budget.max_bytes
    );
    assert_eq!(engine.accepted_history_basis().unwrap(), before);
}

#[test]
fn author_only_interval_is_public_head_without_actor_unit_or_hidden_truth_payload() {
    let engine = authored(&fixture());
    assert_eq!(engine.revision(), 1);
    assert!(engine.receipts().is_empty());
    let q = request(&engine, "player");
    let recent = run(&engine, &q, ContextPolicy::StateRecentTranscriptV1);
    let relevant = run(&engine, &q, ContextPolicy::StateRelevantMemoryV1);
    assert_eq!(mandatory(&recent), mandatory(&relevant));
    for result in [&recent, &relevant] {
        let package = &result.compilation.package;
        assert_eq!((package.head, package.revision), (1, 1));
        assert!(units(result).is_empty());
        assert_eq!(result.compilation.coverage.mode, CoverageMode::Raw);
        assert_eq!(
            result.compilation.coverage.set_fallback_reason,
            Some(MemoryFallbackReason::Unsupported)
        );
        assert_eq!(result.compilation.coverage.raw_event_candidates, 0);
        assert_eq!(result.compilation.coverage.cached_event_candidates, 0);
        assert!(package.records.iter().any(|r| r.mandatory && matches!(&r.payload,Payload::Record(row) if matches!(row.as_ref(),Row::Knowledge{id,text,origin:ValueOrigin::KnownAsObserved,..} if id=="relic-location" && text=="OBSERVED_A"))));
        let encoded = serde_json::to_string(package).unwrap();
        assert!(
            !encoded.contains("PRIVATE_WORLD_B")
                && !encoded.contains("PRIVATE_AUTHOR_POLICY_REASON")
        );
    }
    assert_eq!(recent.construction.eligible_transcript_units, 0);
}

#[test]
fn historical_policy_snapshot_keeps_current_guard_and_original_event_scope_without_future_truth() {
    let mut root = fixture();
    let retained = commit(
        &mut root,
        "retained",
        vec![say("RETAINED_POLICY_WORDS", "mira")],
    );
    let mut engine = authored(&root);
    commit(
        &mut engine,
        "later",
        vec![say("EXCLUDED_POLICY_FUTURE", "mira")],
    );
    let mut q = request(&engine, "player");
    q.at_revision = Some(1);
    let before = engine.accepted_history_basis().unwrap();
    let recent = run(&engine, &q, ContextPolicy::StateRecentTranscriptV1);
    let relevant = run(&engine, &q, ContextPolicy::StateRelevantMemoryV1);
    assert_eq!(mandatory(&recent), mandatory(&relevant));
    let selected = units(&recent);
    assert_eq!(selected.len(), 1);
    assert_eq!(selected[0].original_scope, *root.scope());
    assert_eq!(selected[0].events[0].event, retained.events()[0]);
    for result in [&recent, &relevant] {
        assert_eq!(result.compilation.package.scope, *engine.scope());
        assert_eq!(
            (
                result.compilation.package.head,
                result.compilation.package.revision
            ),
            (3, 1)
        );
        let encoded = serde_json::to_string(&result.compilation.package).unwrap();
        for hidden in [
            "EXCLUDED_POLICY_FUTURE",
            "PRIVATE_WORLD_B",
            "PRIVATE_AUTHOR_POLICY_REASON",
        ] {
            assert!(!encoded.contains(hidden));
        }
    }
    let mut stale = q.clone();
    stale.expected_head = 1;
    assert_eq!(
        compile_policy_cancelled(
            &engine,
            &stale,
            ContextPolicy::StateRecentTranscriptV1,
            None,
            &|| false
        )
        .unwrap_err(),
        CompileError::Stale
    );
    assert_eq!(engine.accepted_history_basis().unwrap(), before);
}
