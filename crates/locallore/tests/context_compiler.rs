use contracts::*;
use engine::Engine;
use inspection_query::{Row, Source};
use locallore::context_compiler::*;
use locallore::{contracts, engine, inspection_query};
use std::{collections::BTreeSet, time::Instant};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn engine() -> Engine {
    Engine::new(seed()).unwrap()
}
fn request(e: &Engine) -> CompileRequest {
    CompileRequest {
        version: COMPILER_VERSION,
        scope: e.scope().clone(),
        expected_head: e.revision(),
        at_revision: None,
        observer: "player".into(),
        role: Role::Director,
        query: String::new(),
        referenced_ids: vec![],
        budget: Budget::default(),
    }
}
fn commit(e: &mut Engine, id: &str, commands: Vec<Command>) {
    let r = e.request(id, Intent::Actions(commands));
    let p = Engine::proposal(&r).unwrap();
    let approved = e.preview(&r, &p).unwrap();
    e.commit(&r, &p, approved.narration()).unwrap();
}
fn promised(e: &mut Engine) {
    commit(
        e,
        "old-promise",
        vec![Command::Promise {
            id: "keep-beacon".into(),
            to: "mira".into(),
            terms: "Remember the beacon repair and return before the tide.".into(),
            deadline: 5000,
            return_item: None,
        }],
    );
}
fn gift(e: &mut Engine) {
    commit(
        e,
        "old-gift",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
}
fn long_engine() -> Engine {
    let mut s = seed();
    s.actors.get_mut("mira").unwrap().name = "Maris".into();
    let mut e = Engine::new(s).unwrap();
    promised(&mut e);
    gift(&mut e);
    for i in 0..1024 {
        commit(
            &mut e,
            &format!("distractor-{i}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    e
}
fn contains_event(p: &ContextPackage, id: u64) -> bool {
    p.records
        .iter()
        .any(|r| matches!(&r.payload,Payload::Record(row)if matches!(row.as_ref(),Row::Event{event,..}if event.sequence==id)))
}
fn assert_bounded(p: &ContextPackage, b: Budget) {
    let bytes = serde_json::to_vec(p).unwrap();
    assert_eq!(p.serialized_bytes, bytes.len());
    assert_eq!(p.estimated_tokens, bytes.len().div_ceil(4) as u32);
    assert!(bytes.len() <= b.max_bytes);
    assert!(p.estimated_tokens + b.reserved_tokens <= b.estimated_tokens);
    assert!(p.records.len() <= 128);
    assert!(p.diagnostics.omissions.len() <= 32);
    assert_eq!(p.token_accounting, "estimate_utf8_bytes_div_4_not_measured");
}

#[test]
fn mandatory_state_rules_truth_open_promises_and_evidence_are_exact_and_read_only() {
    let mut e = engine();
    promised(&mut e);
    gift(&mut e);
    let before = e.canonical_bytes();
    let q = request(&e);
    let p = compile(&e, &q).unwrap();
    assert_bounded(&p, q.budget);
    assert!(p
        .records
        .iter()
        .any(|r| r.kind == Kind::Rules && r.mandatory));
    assert!(p
        .records
        .iter()
        .any(|r| r.kind == Kind::Truth && r.reason == Reason::KnownTruth));
    assert!(p.records.iter().any(|r|matches!(&r.payload,Payload::Record(row)if matches!(row.as_ref(),Row::Promise{id,status,..}if id=="keep-beacon"&&status=="open"))));
    assert!(contains_event(&p, 1));
    assert!(contains_event(&p, 2));
    assert_eq!(before, e.canonical_bytes());
    assert_eq!(p, compile(&e, &q).unwrap());
}

#[test]
fn compiler_preserves_truth_statement_belief_and_observation_labels() {
    let mut e = engine();
    commit(
        &mut e,
        "lie",
        vec![Command::Say {
            text: "The relic is in old-ruins".into(),
            audience: ["mira".into()].into(),
        }],
    );
    commit(&mut e, "belief", vec![Command::Believe { claim_event: 1 }]);
    let mut q = request(&e);
    q.query = "relic old-ruins statement".into();
    let p = compile(&e, &q).unwrap();
    for kind in [
        Kind::Truth,
        Kind::Statement,
        Kind::Belief,
        Kind::Observation,
    ] {
        assert!(p.records.iter().any(|r| r.kind == kind), "{kind:?}");
    }
    assert!(p
        .records
        .iter()
        .filter(|r| r.kind == Kind::Truth)
        .all(|r| !serde_json::to_string(r).unwrap().contains("old-ruins")));
    assert!(p
        .records
        .iter()
        .filter(|r| r.kind == Kind::Belief)
        .any(|r| r.sources.contains(&Source::Event(1))));
}

#[test]
fn source_scope_head_observer_and_completed_historical_boundary_precede_content() {
    let mut e = engine();
    commit(
        &mut e,
        "two-events",
        vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
    );
    let q = request(&e);
    for (mut changed, error) in [
        (q.clone(), CompileError::Version),
        (q.clone(), CompileError::Scope),
        (q.clone(), CompileError::Stale),
        (q.clone(), CompileError::Observer),
        (q.clone(), CompileError::Boundary),
    ] {
        match error {
            CompileError::Version => changed.version = 99,
            CompileError::Scope => changed.scope.story = "foreign".into(),
            CompileError::Stale => changed.expected_head = 0,
            CompileError::Observer => changed.observer = "missing".into(),
            _ => changed.at_revision = Some(1),
        }
        assert_eq!(compile(&e, &changed), Err(error));
    }
    let mut future = q.clone();
    future.at_revision = Some(e.revision() + 1);
    assert_eq!(compile(&e, &future), Err(CompileError::Boundary));
    let child = e.fork("child", e.revision()).unwrap();
    assert_eq!(
        compile(&child, &request(&child)),
        Err(CompileError::UnsupportedBranch)
    );
    let mut sibling = q.clone();
    sibling.scope.branch = "sibling".into();
    assert_eq!(compile(&e, &sibling), Err(CompileError::Scope));
    let mut npc = q;
    npc.observer = "mira".into();
    assert_eq!(compile(&e, &npc), Err(CompileError::Observer));
    npc.role = Role::Character;
    assert!(compile(&e, &npc).is_ok());
}

#[test]
fn later_discovery_and_current_fields_do_not_backfill_historical_context() {
    let mut e = engine();
    commit(
        &mut e,
        "move",
        vec![Command::Move {
            to: "dry-well".into(),
        }],
    );
    let previous = e.revision();
    commit(
        &mut e,
        "find",
        vec![Command::Discover {
            fact: "beacon-mark".into(),
        }],
    );
    let mut q = request(&e);
    q.query = "repair mark".into();
    let now = compile(&e, &q).unwrap();
    assert!(serde_json::to_string(&now)
        .unwrap()
        .contains("An old repair mark"));
    q.at_revision = Some(previous);
    let past = compile(&e, &q).unwrap();
    let text = serde_json::to_string(&past).unwrap();
    assert!(!text.contains("An old repair mark"));
    assert!(!text.contains("beacon-mark"));
    assert!(past.historical);
    assert_eq!(past.revision, previous);
    assert_eq!(past.head, e.revision());
    assert!(past.records.iter().all(|r| r.source_revision <= previous));
}

#[test]
fn hidden_record_contents_ids_names_and_counts_do_not_enter_actor_package() {
    let mut results = vec![];
    for hidden in [false, true] {
        let mut s = seed();
        if hidden {
            s.facts.insert(
                "HIDDEN-ID-731".into(),
                Fact {
                    proposition: "PRIVATE-CANARY-731".into(),
                    discoverable_at: None,
                    known_by: ["sable".into()].into(),
                },
            );
            s.beliefs.push(Belief {
                believer: "sable".into(),
                proposition: "PRIVATE-CANARY-731".into(),
                source_claim: None,
                source: Evidence::Seed(s.id.clone()),
                confidence: Confidence::Believed,
            });
            s.actors.get_mut("sable").unwrap().name = "PRIVATE-CANARY-731".into();
        }
        let e = Engine::new(s).unwrap();
        let mut q = request(&e);
        q.observer = "mira".into();
        q.role = Role::Character;
        q.query = "PRIVATE-CANARY-731 secret relic-location".into();
        let p = compile(&e, &q).unwrap();
        let json = serde_json::to_string(&p).unwrap();
        for forbidden in [
            "PRIVATE-CANARY-731",
            "HIDDEN-ID-731",
            "SECRET-TIDE-731",
            "ancestry",
            "relic-location",
        ] {
            assert!(!json.contains(forbidden), "{forbidden}");
        }
        results.push(p);
    }
    assert_eq!(results[0], results[1]);
    let e = engine();
    let mut q = request(&e);
    q.observer = "mira".into();
    q.role = Role::Character;
    for id in ["relic-location", "never-existed"] {
        q.referenced_ids = vec![id.into()];
        assert_eq!(compile(&e, &q), Err(CompileError::UnknownReference));
    }
}

#[test]
fn only_eligible_canonical_name_aliases_resolve_and_ambiguous_names_fail_safely() {
    let mut s = seed();
    s.actors.get_mut("mira").unwrap().name = "Harbor Friend".into();
    s.actors.get_mut("sable").unwrap().name = "Harbor Friend".into();
    let mut e = Engine::new(s).unwrap();
    gift(&mut e);
    let mut q = request(&e);
    q.query = "remember Harbor Friend gift".into();
    let p = compile(&e, &q).unwrap();
    assert!(p.records.iter().any(
        |r| matches!(&r.payload,Payload::Alias{actor,name}if actor=="mira"&&name=="Harbor Friend")
    ));
    assert!(!serde_json::to_string(&p).unwrap().contains("sable"));
    let mut s = seed();
    s.actors.get_mut("mira").unwrap().name = "Harbor Friend".into();
    s.actors.get_mut("oren").unwrap().name = "Harbor Friend".into();
    let e = Engine::new(s).unwrap();
    let mut q = request(&e);
    q.query = "Harbor Friend".into();
    assert_eq!(compile(&e, &q), Err(CompileError::AmbiguousAlias));
    q.referenced_ids = vec!["mira".into()];
    assert!(compile(&e, &q).is_ok());
}

#[test]
fn mandatory_budget_failure_and_invalid_requests_never_silently_drop_critical_state() {
    let e = engine();
    let mut q = request(&e);
    q.budget.max_bytes = 1024;
    assert_eq!(compile(&e, &q), Err(CompileError::MandatoryBudget));
    for invalid in 0..7 {
        let mut q = request(&e);
        match invalid {
            0 => q.query = "x".repeat(513),
            1 => q.query = "x\n".into(),
            2 => q.referenced_ids = vec!["../path".into()],
            3 => q.budget.reserved_tokens = q.budget.estimated_tokens,
            4 => q.budget.recent_events = 9,
            5 => q.budget.optional_records = 65,
            _ => q.budget.max_bytes = MAX_CONTEXT_BYTES + 1,
        }
        assert_eq!(compile(&e, &q), Err(CompileError::InvalidRequest));
    }
    let mut s = seed();
    for i in 0..160 {
        s.actors
            .get_mut("player")
            .unwrap()
            .attributes
            .insert(format!("attribute-{i}"), 1);
    }
    let large = Engine::new(s).unwrap();
    assert_eq!(
        compile(&large, &request(&large)),
        Err(CompileError::MandatoryBudget)
    );
}

#[test]
fn long_history_measurement_table_keeps_old_promise_alias_and_transfer_within_budget() {
    let built = Instant::now();
    let e = long_engine();
    let build_us = built.elapsed().as_micros();
    assert_eq!(e.revision(), 1026);
    let before = e.canonical_bytes();
    println!("M07_TABLE build_events=1026 build_us={build_us}");
    for (name, query, refs) in [
        (
            "old_promise",
            "beacon repair promise",
            vec!["keep-beacon".into()],
        ),
        ("alias_gift", "Maris gift", vec![]),
        ("exact_item", "potion", vec!["potion".into()]),
        ("lexical_only", "gift transfer", vec![]),
    ] {
        let mut q = request(&e);
        q.query = query.into();
        q.referenced_ids = refs;
        q.budget.recent_events = 2;
        let began = Instant::now();
        let p = compile(&e, &q).unwrap();
        let compile_us = began.elapsed().as_micros();
        assert_bounded(&p, q.budget);
        assert!(p.records.iter().any(
            |r| matches!(&r.payload,Payload::Record(row)if matches!(row.as_ref(),Row::Promise{id,..}if id=="keep-beacon"))
        ));
        let transfer = contains_event(&p, 2);
        if name != "old_promise" {
            assert!(transfer, "{name}");
        }
        assert!(contains_event(&p, 1));
        let selected_events = p
            .records
            .iter()
            .filter(|r| matches!(&r.payload, Payload::Record(row)if matches!(row.as_ref(),Row::Event { .. })))
            .count();
        println!("M07_TABLE case={name} accepted_events=1026 eligible={} selected={} selected_events={selected_events} bytes={} estimated_tokens={} reserve={} promise_recall=1 gift_recall={} compile_us={compile_us}",p.diagnostics.eligible_candidates,p.records.len(),p.serialized_bytes,p.estimated_tokens,p.reserved_tokens,u8::from(transfer));
        assert!(p.diagnostics.omitted_eligible >= 1000);
        assert!(p.diagnostics.omissions_truncated);
        assert!(p.unsupported.contains(&"SQLite FTS"));
        assert!(p.unsupported.contains(&"Summaries and invalidation"));
        let ids: BTreeSet<_> = p.records.iter().map(|r| &r.id).collect();
        assert_eq!(ids.len(), p.records.len());
    }
    assert_eq!(before, e.canonical_bytes());
    for cap in [1024, 8192, 12288, MAX_CONTEXT_BYTES] {
        let mut q = request(&e);
        q.query = "beacon promise".into();
        q.budget.max_bytes = cap;
        q.budget.recent_events = 2;
        let began = Instant::now();
        match compile(&e, &q) {
            Ok(package) => {
                assert_bounded(&package, q.budget);
                assert!(contains_event(&package, 1));
                assert!(package.records.iter().any(|r|matches!(&r.payload,Payload::Record(row)if matches!(row.as_ref(),Row::Promise{id,..}if id=="keep-beacon"))));
                println!("M07_BUDGET cap_bytes={cap} result=ok bytes={} estimate={} promise_recall=1 compile_us={}",package.serialized_bytes,package.estimated_tokens,began.elapsed().as_micros());
            }
            Err(error) => {
                assert_eq!(error, CompileError::MandatoryBudget);
                println!(
                    "M07_BUDGET cap_bytes={cap} result=mandatory_stop compile_us={}",
                    began.elapsed().as_micros()
                );
            }
        }
    }
    let mut stale = request(&e);
    stale.expected_head -= 1;
    assert_eq!(compile(&e, &stale), Err(CompileError::Stale));
}

#[test]
fn lexical_search_covers_long_eligible_records_and_sql_like_text_is_only_words() {
    let mut e = engine();
    commit(
        &mut e,
        "long-statement",
        vec![Command::Say {
            text: format!("{} unique-tail-needle", "ordinary ".repeat(200)),
            audience: ["mira".into()].into(),
        }],
    );
    for i in 0..12 {
        commit(
            &mut e,
            &format!("noise-{i}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    let mut q = request(&e);
    q.query = "unique-tail-needle".into();
    q.budget.recent_events = 0;
    let package = compile(&e, &q).unwrap();
    assert!(contains_event(&package, 1));
    assert!(package
        .records
        .iter()
        .any(|r| r.kind == Kind::Statement && r.reason == Reason::Lexical));
    let before = e.canonical_bytes();
    q.query = "\" OR 1=1; DROP TABLE receipts;--".into();
    assert!(compile(&e, &q).is_ok());
    assert_eq!(before, e.canonical_bytes());
}

#[test]
fn current_location_inventory_and_borrowed_owner_ids_are_known_without_global_lookup() {
    let e = engine();
    let mut q = request(&e);
    q.referenced_ids = vec!["quay".into(), "brass-key".into(), "oren".into()];
    let package = compile(&e, &q).unwrap();
    assert_bounded(&package, q.budget);
    assert!(package
        .records
        .iter()
        .any(|r| matches!(&r.payload,Payload::Alias{actor,..}if actor=="oren")));
    let mut s = seed();
    s.actors.get_mut("mira").unwrap().name = "n".repeat(257);
    let e = Engine::new(s).unwrap();
    assert_eq!(compile(&e, &request(&e)), Err(CompileError::TooLarge));
    let e = engine();
    let mut q = request(&e);
    q.query = (0..65)
        .map(|n| format!("w{n}"))
        .collect::<Vec<_>>()
        .join(" ");
    assert_eq!(compile(&e, &q), Err(CompileError::InvalidRequest));
}
