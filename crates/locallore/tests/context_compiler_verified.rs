use locallore::{
    context_compiler::*, contracts::*, engine::Engine, inspection_query::Row, memory_coverage::*,
};
use serde_json::json;
use std::cell::Cell;

fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn commit(e: &mut Engine, turn: &str, commands: Vec<Command>) {
    let request = e.request(turn, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = e.preview(&request, &proposal).unwrap();
    e.commit(&request, &proposal, preview.narration()).unwrap();
}
fn say(text: &str, audience: &str) -> Command {
    Command::Say {
        text: text.into(),
        audience: [audience.into()].into(),
    }
}
fn long_history() -> Engine {
    let mut e = engine();
    commit(
        &mut e,
        "opening",
        vec![
            Command::Promise {
                id: "beacon".into(),
                to: "mira".into(),
                terms: "Return to repair the beacon".into(),
                deadline: 5000,
                return_item: None,
            },
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        ],
    );
    for batch in 0..75 {
        commit(
            &mut e,
            &format!("batch-{batch}"),
            (0..8)
                .map(|slot| {
                    let n = batch * 8 + slot;
                    say(
                        &if n == 300 {
                            "OLDEST-VERIFIED-SPINDLE".into()
                        } else {
                            format!("Ledger pebble number {n}")
                        },
                        "mira",
                    )
                })
                .collect(),
        );
    }
    commit(
        &mut e,
        "private",
        vec![say("PRIVATE-ACTOR-CANARY", "player")],
    );
    assert_eq!(e.revision(), 603);
    e
}
fn request(e: &Engine, text: &str) -> CompileRequest {
    CompileRequest {
        version: COMPILER_VERSION,
        scope: e.scope().clone(),
        expected_head: e.revision(),
        at_revision: None,
        observer: "mira".into(),
        role: Role::Character,
        query: text.into(),
        referenced_ids: vec![],
        budget: Budget::default(),
    }
}
fn packets(e: &Engine, observer: &str) -> Vec<TypedPacket> {
    let mut out = vec![];
    let mut after = 0;
    while let Some(p) = build_chunk(
        e,
        &ChunkRequest {
            scope: e.scope().clone(),
            expected_head: e.revision(),
            observer: observer.into(),
            from_exclusive: after,
        },
        &|| false,
    )
    .unwrap()
    {
        assert!(p.through_revision > after);
        after = p.through_revision;
        out.push(p);
        assert!(out.len() <= MAX_PACKETS);
    }
    out
}
fn proof(e: &Engine, observer: &str, ps: &[TypedPacket]) -> VerifiedCoverage {
    let bytes = ps.iter().map(|p| p.bytes().unwrap()).collect::<Vec<_>>();
    match verify_coverage(
        e,
        &CoverageRequest {
            scope: e.scope().clone(),
            expected_head: e.revision(),
            observer: observer.into(),
        },
        &bytes.iter().map(Vec::as_slice).collect::<Vec<_>>(),
        &|| false,
    )
    .unwrap()
    {
        CoverageRead::Verified(v) => v,
        CoverageRead::RawFallback(r) => panic!("unexpected proof rejection {r:?}"),
    }
}
fn parity(e: &Engine, r: &CompileRequest, v: Option<&VerifiedCoverage>) -> MemoryCompilation {
    let raw = compile(e, r).unwrap();
    let m = compile_verified_cancelled(e, r, v, &|| false).unwrap();
    assert_eq!(
        serde_json::to_vec(&raw).unwrap(),
        serde_json::to_vec(&m.package).unwrap()
    );
    assert_eq!(raw, m.package);
    let actual = e
        .at_revision(r.at_revision.unwrap_or(e.revision()))
        .unwrap()
        .character_context(
            &r.observer,
            e.scope(),
            r.at_revision.unwrap_or(e.revision()),
        )
        .unwrap()
        .observations
        .len();
    assert_eq!(
        m.coverage.cached_event_candidates + m.coverage.raw_event_candidates,
        actual
    );
    m
}
fn event(p: &ContextPackage, seq: u64, scope: &Scope) -> bool {
    p.records.iter().any(|r| {
        matches!(&r.payload,Payload::Record(row) if
        matches!(&**row,Row::Event{event,..} if event.sequence==seq && event.scope==*scope))
    })
}

#[test]
fn six_hundred_accepted_events_forward_cached_old_payload_with_exact_raw_bytes() {
    let e = long_history();
    let before = (e.canonical_bytes(), e.receipts().to_vec());
    let ps = packets(&e, "mira");
    let v = proof(&e, "mira", &ps);
    let m = parity(&e, &request(&e, "OLDEST-VERIFIED-SPINDLE"), Some(&v));
    assert_eq!(m.coverage.mode, CoverageMode::Verified);
    assert!(m.coverage.packets_used > 0);
    assert!(m.coverage.cached_event_candidates > 0);
    assert!(m.coverage.mandatory_fallback_packets > 0);
    assert_eq!(m.coverage.timespan_fallback_packets, 0);
    assert!(event(&m.package, 303, e.scope()));
    let target_packet = ps
        .iter()
        .find(|p| p.source_events.iter().any(|s| s.sequence == 303))
        .unwrap();
    assert!(!target_packet
        .source_events
        .iter()
        .any(|s| matches!(s.sequence, 1 | 2 | 599..=602)));
    assert!(!serde_json::to_string(&m)
        .unwrap()
        .contains("PRIVATE-ACTOR-CANARY"));
    assert!(!serde_json::to_string(&m.package)
        .unwrap()
        .contains("SECRET-TIDE-731"));
    for query in [
        "mira",
        "potion",
        "beacon",
        "Ledger",
        "PRIVATE-ACTOR-CANARY",
        "",
    ] {
        parity(&e, &request(&e, query), Some(&v));
    }
    assert_eq!(before, (e.canonical_bytes(), e.receipts().to_vec()));
}

#[test]
fn old_open_tail_and_sealed_prefix_keep_exact_raw_delta() {
    let mut e = long_history();
    let old_head = e.revision();
    let ps = packets(&e, "mira");
    assert!(ps.iter().any(|p| p.closure.is_sealed()));
    assert_eq!(ps.last().unwrap().closure, Closure::OpenTail);
    let v = proof(&e, "mira", &ps);
    commit(&mut e, "new", vec![say("RAW-DELTA-ANCHOR", "mira")]);
    let m = parity(&e, &request(&e, "RAW-DELTA-ANCHOR"), Some(&v));
    assert_eq!(m.coverage.covered_through, old_head);
    assert_eq!(m.coverage.raw_delta_after, old_head);
    assert!(event(&m.package, old_head + 1, e.scope()));
    assert!(m.coverage.cached_event_candidates > 0);
    let sealed = proof(&e, "mira", &ps[..ps.len() - 1]);
    let m = parity(&e, &request(&e, "OLDEST-VERIFIED-SPINDLE"), Some(&sealed));
    assert_eq!(
        m.coverage.covered_through,
        ps[ps.len() - 2].through_revision
    );
    assert!(m.coverage.raw_event_candidates > 1);
}

#[test]
fn timespan_and_mandatory_overlap_refetch_entire_packets_not_aggregate_expansion() {
    let mut e = engine();
    commit(
        &mut e,
        "promise",
        vec![Command::Promise {
            id: "signal".into(),
            to: "mira".into(),
            terms: "Keep the signal".into(),
            deadline: 5000,
            return_item: None,
        }],
    );
    for i in 0..10 {
        commit(
            &mut e,
            &format!("wait-{i}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    commit(&mut e, "speech", vec![say("TAIL-SPEECH", "mira")]);
    let ps = packets(&e, "player");
    assert_eq!(ps.len(), 1);
    assert!(ps[0]
        .entries
        .iter()
        .any(|x| matches!(x, Entry::ObservedTimeSpan { .. })));
    let v = proof(&e, "player", &ps);
    let mut r = request(&e, "TAIL-SPEECH");
    r.observer = "player".into();
    let m = parity(&e, &r, Some(&v));
    assert_eq!(m.coverage.timespan_fallback_packets, 1);
    assert_eq!(m.coverage.packets_fell_back, 1);
    assert_eq!(m.coverage.cached_event_candidates, 0);
    assert_eq!(m.coverage.raw_event_candidates, 12);
    let mut e = engine();
    commit(
        &mut e,
        "first",
        vec![
            say("MANDATORY-RECENT", "mira"),
            say("OTHER-SAME-PACKET", "mira"),
        ],
    );
    let ps = packets(&e, "mira");
    let v = proof(&e, "mira", &ps);
    let m = parity(&e, &request(&e, "OTHER-SAME-PACKET"), Some(&v));
    assert_eq!(m.coverage.mandatory_fallback_packets, 1);
    assert_eq!(m.coverage.raw_event_candidates, 2);
    assert_eq!(m.coverage.cached_event_candidates, 0);
}

#[test]
fn proof_rebinding_refuses_foreign_observer_story_lineage_and_changed_sources() {
    let mut root = engine();
    for i in 0..5 {
        commit(
            &mut root,
            &format!("r{i}"),
            vec![say(&format!("ROOT-{i}"), "mira")],
        );
    }
    let a = root.fork("a", 5).unwrap();
    let mut child = a.fork("b", 1).unwrap();
    commit(&mut child, "c", vec![say("CHILD", "mira")]);
    let v = proof(&child, "mira", &packets(&child, "mira"));
    let before = (child.canonical_bytes(), child.receipts().to_vec());
    let m = parity(&child, &request(&child, "ROOT-0"), Some(&v));
    assert!(event(&m.package, 1, root.scope()));
    assert!(!serde_json::to_string(&m.package)
        .unwrap()
        .contains("ROOT-4"));
    commit(&mut root, "future", vec![say("PARENT-FUTURE", "mira")]);
    parity(&child, &request(&child, "ROOT-0"), Some(&v));
    let mut sibling = root.fork("sibling", 1).unwrap();
    commit(&mut sibling, "c", vec![say("SIBLING-PRIVATE", "mira")]);
    let mut direct = root.fork("b", 1).unwrap();
    commit(&mut direct, "c", vec![say("CHILD", "mira")]);
    assert_eq!(direct.receipts(), child.receipts());
    let mut s: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    s.scope.story = "foreign".into();
    let mut foreign = Engine::new(s).unwrap();
    commit(
        &mut foreign,
        "a",
        vec![say("FOREIGN", "mira"), say("FOREIGN-SECOND", "mira")],
    );
    let mut changed = engine();
    commit(
        &mut changed,
        "a",
        vec![say("OTHER-FIRST", "mira"), say("OTHER-SECOND", "mira")],
    );
    let root_v = proof(&changed, "mira", &packets(&changed, "mira"));
    let mut same = engine();
    commit(
        &mut same,
        "a",
        vec![say("CHANGED-FIRST", "mira"), say("OTHER-SECOND", "mira")],
    );
    let m = parity(&same, &request(&same, "CHANGED-FIRST"), Some(&root_v));
    assert_eq!(
        m.coverage.set_fallback_reason,
        Some(MemoryFallbackReason::SourceMismatch)
    );
    for other in [&sibling, &direct, &foreign] {
        let m = parity(other, &request(other, ""), Some(&v));
        assert_eq!(m.coverage.mode, CoverageMode::Raw);
        assert_eq!(m.coverage.raw_delta_after, 0);
        assert_eq!(m.coverage.cached_event_candidates, 0);
        assert_eq!(
            m.coverage.set_fallback_reason,
            Some(MemoryFallbackReason::Binding)
        );
    }
    let mut r = request(&child, "");
    r.observer = "player".into();
    let m = parity(&child, &r, Some(&v));
    assert_eq!(
        m.coverage.set_fallback_reason,
        Some(MemoryFallbackReason::Binding)
    );
    assert_eq!(before, (child.canonical_bytes(), child.receipts().to_vec()));
}

#[test]
fn selected_historical_snapshot_is_rechecked_before_any_cache_candidate() {
    let e = long_history();
    let v = proof(&e, "mira", &packets(&e, "mira"));
    let mut r = request(&e, "Ledger");
    r.at_revision = Some(10);
    let m = parity(&e, &r, Some(&v));
    assert_eq!(m.package.revision, 10);
    assert_eq!(m.coverage.mode, CoverageMode::Raw);
    assert_eq!(m.coverage.raw_delta_after, 0);
    let historical = e.at_revision(10).unwrap();
    let v = proof(&historical, "mira", &packets(&historical, "mira"));
    let m = parity(&e, &r, Some(&v));
    assert_eq!(m.coverage.mode, CoverageMode::Verified);
    assert_eq!(m.coverage.covered_through, 10);
    assert_eq!(
        m.coverage.cached_event_candidates, 0,
        "whole packet overlaps recent floor"
    );
}

#[test]
fn malformed_gapped_and_edited_sets_never_create_a_compiler_proof() {
    let e = long_history();
    let ps = packets(&e, "mira");
    let base = CoverageRequest {
        scope: e.scope().clone(),
        expected_head: e.revision(),
        observer: "mira".into(),
    };
    let bytes = ps.iter().map(|p| p.bytes().unwrap()).collect::<Vec<_>>();
    for untrusted in [vec![b"{".to_vec()], bytes[1..].to_vec(), {
        let mut changed = serde_json::to_value(&ps[0]).unwrap();
        changed["source_sha256"] = json!("0".repeat(64));
        vec![serde_json::to_vec(&changed).unwrap()]
    }] {
        assert!(matches!(
            verify_coverage(
                &e,
                &base,
                &untrusted.iter().map(Vec::as_slice).collect::<Vec<_>>(),
                &|| false
            )
            .unwrap(),
            CoverageRead::RawFallback(_)
        ));
        let m = parity(&e, &request(&e, "OLDEST-VERIFIED-SPINDLE"), None);
        assert_eq!(m.coverage.mode, CoverageMode::Raw);
        assert_eq!(m.coverage.raw_event_candidates, 602);
    }
}

#[test]
fn request_errors_cancel_and_mandatory_budget_keep_their_original_safe_errors() {
    let e = long_history();
    let v = proof(&e, "mira", &packets(&e, "mira"));
    let original = request(&e, "");
    let mut cases = vec![];
    let mut r = original.clone();
    r.expected_head -= 1;
    cases.push((r, CompileError::Stale));
    let mut r = original.clone();
    r.scope.story = "foreign".into();
    cases.push((r, CompileError::Scope));
    let mut r = original.clone();
    r.version += 1;
    cases.push((r, CompileError::Version));
    let mut r = original.clone();
    r.observer = "unknown".into();
    cases.push((r, CompileError::Observer));
    let mut r = original.clone();
    r.at_revision = Some(3);
    cases.push((r, CompileError::Boundary));
    let mut r = original.clone();
    r.budget.max_bytes = 1024;
    r.budget.estimated_tokens = 64;
    r.budget.reserved_tokens = 1;
    cases.push((r, CompileError::MandatoryBudget));
    for (r, error) in cases {
        assert_eq!(compile(&e, &r), Err(error));
        assert_eq!(
            compile_verified_cancelled(&e, &r, Some(&v), &|| false),
            Err(error)
        );
    }
    assert_eq!(
        compile_verified_cancelled(&e, &original, Some(&v), &|| true),
        Err(CompileError::Cancelled)
    );
    let calls = Cell::new(0);
    let result = compile_verified_cancelled(&e, &original, Some(&v), &|| {
        let n = calls.get();
        calls.set(n + 1);
        n >= 100
    });
    assert_eq!(result, Err(CompileError::Cancelled));
    assert!(calls.get() > 100);
}
