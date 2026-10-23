use locallore::{
    context_compiler::{self as compiler, Budget, CompileError, CompileRequest, Role},
    contracts::*,
    engine::Engine,
    inspection_query::{self as inspect, Observer, Query, QueryError, Row, View},
};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn commit(e: &mut Engine, key: &str, commands: Vec<Command>) -> Receipt {
    let r = e.request(key, Intent::Actions(commands));
    let p = Engine::proposal(&r).unwrap();
    let n = e.preview(&r, &p).unwrap().narration().to_owned();
    e.commit(&r, &p, &n).unwrap()
}
fn say(e: &mut Engine, key: &str, text: &str) {
    commit(
        e,
        key,
        vec![Command::Say {
            text: text.into(),
            audience: ["mira".into()].into(),
        }],
    );
}
fn compile_request(e: &Engine) -> CompileRequest {
    CompileRequest {
        version: compiler::COMPILER_VERSION,
        scope: e.scope().clone(),
        expected_head: e.revision(),
        at_revision: None,
        observer: "mira".into(),
        role: Role::Character,
        query: "INHERITED CHILD PARENT SIBLING secret".into(),
        referenced_ids: vec![],
        budget: Budget::default(),
    }
}
fn query(e: &Engine, view: View) -> Query {
    Query {
        version: inspect::QUERY_VERSION,
        scope: e.scope().clone(),
        expected_head: e.revision(),
        at_revision: None,
        observer: Observer::Character { id: "mira".into() },
        view,
        cursor: None,
        limit: inspect::MAX_ROWS,
        search: String::new(),
    }
}
fn family() -> (Engine, Engine, Engine) {
    let mut root = Engine::new(seed()).unwrap();
    say(&mut root, "inherited", "INHERITED-CANARY");
    let mut child = root.fork("child", 1).unwrap();
    let mut sibling = root.fork("sibling", 1).unwrap();
    say(&mut root, "future-parent", "PARENT-FUTURE-CANARY");
    say(&mut sibling, "sibling-private", "SIBLING-CANARY");
    say(&mut child, "child-local", "CHILD-CANARY");
    (root, child, sibling)
}

#[test]
fn historical_snapshot_preserves_original_receipts_and_child_scope_at_all_boundaries() {
    let (root, mut child, sibling) = family();
    commit(
        &mut child,
        "two-events",
        vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
    );
    let before = child.canonical_bytes();
    let history = child.receipts().to_vec();
    for at in [0, 1, 2, 4] {
        let snapshot = child.at_revision(at).unwrap();
        assert_eq!(snapshot.scope(), child.scope());
        assert_eq!(snapshot.revision(), at);
        assert_eq!(
            snapshot.receipts(),
            &history[..match at {
                0 => 0,
                1 => 1,
                2 => 2,
                _ => 3,
            }]
        );
        if at > 0 {
            assert_eq!(snapshot.receipts()[0].request().scope, *root.scope());
        }
        assert!(!serde_json::to_string(snapshot.receipts())
            .unwrap()
            .contains("PARENT-FUTURE-CANARY"));
        assert!(!serde_json::to_string(snapshot.receipts())
            .unwrap()
            .contains("SIBLING-CANARY"));
        assert_eq!(
            snapshot.at_revision(at).unwrap().canonical_bytes(),
            snapshot.canonical_bytes()
        );
    }
    for at in [3, 5, u64::MAX] {
        assert_eq!(child.at_revision(at).err(), Some(Error::Rule));
    }
    assert_eq!(child.canonical_bytes(), before);
    assert_eq!(sibling.revision(), 2);
    let mut rewind = child.fork("nested", 1).unwrap();
    say(&mut rewind, "replacement", "NESTED-REPLACEMENT");
    let past = rewind.at_revision(1).unwrap();
    assert_eq!(past.scope().branch, "nested");
    assert_eq!(past.receipts(), &history[..1]);
    assert!(
        !serde_json::to_string(&past.character_context("mira", past.scope(), 1).unwrap())
            .unwrap()
            .contains("CHILD-CANARY")
    );
    let zero = rewind.fork("zero", 0).unwrap();
    assert_eq!(
        zero.at_revision(0).unwrap().state(),
        &Engine::new(seed()).unwrap().state().clone()
    );
}

#[test]
fn child_compiler_and_query_exclude_future_sibling_and_unwitnessed_content_before_serializing() {
    let (_, child, _) = family();
    let before = child.canonical_bytes();
    let actor_before = child
        .character_context("mira", child.scope(), child.revision())
        .unwrap();
    let request = compile_request(&child);
    let package = compiler::compile(&child, &request).unwrap();
    let text = serde_json::to_string(&package).unwrap();
    assert!(text.contains("INHERITED-CANARY") && text.contains("CHILD-CANARY"));
    for canary in ["PARENT-FUTURE-CANARY", "SIBLING-CANARY", "SECRET-TIDE-731"] {
        assert!(!text.contains(canary));
    }
    assert_eq!(package.scope, *child.scope());
    for view in [
        View::History,
        View::Knowledge,
        View::Profiles,
        View::Relationships,
        View::Promises,
        View::Provenance,
        View::TurnDiff,
    ] {
        let page = inspect::query(&child, &query(&child, view), true).unwrap();
        let text = serde_json::to_string(&page).unwrap();
        for canary in ["PARENT-FUTURE-CANARY", "SIBLING-CANARY", "SECRET-TIDE-731"] {
            assert!(!text.contains(canary), "{view:?}");
        }
        assert_eq!(page.scope, *child.scope());
    }
    let mut omniscient = query(&child, View::Knowledge);
    omniscient.observer = Observer::Omniscient;
    assert_eq!(
        inspect::query(&child, &omniscient, false),
        Err(QueryError::Forbidden)
    );
    assert!(
        serde_json::to_string(&inspect::query(&child, &omniscient, true).unwrap())
            .unwrap()
            .contains("SECRET-TIDE-731")
    );
    assert_eq!(
        actor_before,
        child
            .character_context("mira", child.scope(), child.revision())
            .unwrap()
    );
    assert_eq!(package, compiler::compile(&child, &request).unwrap());
    assert_eq!(child.canonical_bytes(), before);
    let mut sable = request.clone();
    sable.observer = "sable".into();
    let hidden = serde_json::to_string(&compiler::compile(&child, &sable).unwrap()).unwrap();
    assert!(!hidden.contains("INHERITED-CANARY") && !hidden.contains("CHILD-CANARY"));
    assert_eq!(
        compiler::compile_cancelled(&child, &request, &|| true),
        Err(CompileError::Cancelled)
    );
}

#[test]
fn historical_child_packages_and_turn_diffs_do_not_backfill_local_future() {
    let (_, child, _) = family();
    for at in [0, 1, 2] {
        let mut request = compile_request(&child);
        request.at_revision = Some(at);
        let p = compiler::compile(&child, &request).unwrap();
        assert_eq!(p.revision, at);
        assert_eq!(p.head, 2);
        assert_eq!(p.scope, *child.scope());
        let text = serde_json::to_string(&p).unwrap();
        assert_eq!(text.contains("CHILD-CANARY"), at == 2);
        assert_eq!(text.contains("INHERITED-CANARY"), at >= 1);
        let mut q = query(&child, View::History);
        q.at_revision = Some(at);
        let page = inspect::query(&child, &q, true).unwrap();
        assert_eq!(
            page.rows
                .iter()
                .filter(|r| matches!(r, Row::Event { .. }))
                .count(),
            at as usize
        );
        if at > 0 {
            q.view = View::TurnDiff;
            assert!(inspect::query(&child, &q, true).is_ok());
        }
    }
    let mut q = query(&child, View::History);
    q.at_revision = Some(3);
    assert_eq!(
        inspect::query(&child, &q, true),
        Err(QueryError::InvalidBoundary)
    );
    let mut request = compile_request(&child);
    request.at_revision = Some(3);
    assert_eq!(
        compiler::compile(&child, &request),
        Err(CompileError::Boundary)
    );
}

#[test]
fn child_cursor_is_bound_to_lineage_observer_revision_and_query() {
    let (_, mut child, sibling) = family();
    let mut q = query(&child, View::History);
    q.limit = 1;
    let first = inspect::query(&child, &q, true).unwrap();
    q.cursor = Some(first.next_cursor.unwrap());
    assert_eq!(inspect::query(&child, &q, true).unwrap().rows.len(), 1);
    let mut other = q.clone();
    other.scope = sibling.scope().clone();
    assert_eq!(
        inspect::query(&sibling, &other, true),
        Err(QueryError::InvalidCursor)
    );
    other = q.clone();
    other.observer = Observer::Omniscient;
    assert_eq!(
        inspect::query(&child, &other, true),
        Err(QueryError::InvalidCursor)
    );
    other = q.clone();
    other.at_revision = Some(1);
    assert_eq!(
        inspect::query(&child, &other, true),
        Err(QueryError::InvalidCursor)
    );
    say(&mut child, "next", "NEW-CANARY");
    assert_eq!(inspect::query(&child, &q, true), Err(QueryError::Stale));
}

#[test]
fn accepted_historical_play_keeps_its_recorded_policy_in_child_snapshots() {
    let f: serde_json::Value =
        serde_json::from_str(include_str!("fixtures/accepted_play_v2_1.json")).unwrap();
    let root = Engine::restore(
        serde_json::from_value(f["seed"].clone()).unwrap(),
        &[f["receipt"].to_string()],
    )
    .unwrap();
    let mut child = root.fork("historical", root.revision()).unwrap();
    let old = child.revision();
    commit(&mut child, "continue", vec![Command::Wait { ticks: 1 }]);
    let snapshot = child.at_revision(old).unwrap();
    assert_eq!(
        serde_json::to_value(&snapshot.receipts()[0]).unwrap(),
        f["receipt"]
    );
    let mut request = compile_request(&child);
    request.at_revision = Some(old);
    assert!(compiler::compile(&child, &request).is_ok());
    let mut q = query(&child, View::History);
    q.at_revision = Some(old);
    assert!(inspect::query(&child, &q, true).is_ok());
}

#[test]
fn long_child_history_retains_old_mandatory_evidence_within_budget_and_no_future_leak() {
    let mut root = Engine::new(seed()).unwrap();
    commit(
        &mut root,
        "promise",
        vec![Command::Promise {
            id: "beacon-oath".into(),
            to: "mira".into(),
            terms: "Repair beacon before tide".into(),
            deadline: 5000,
            return_item: None,
        }],
    );
    let mut child = root.fork("long-child", 1).unwrap();
    say(&mut root, "excluded", "PARENT-FUTURE-CANARY");
    for i in 0..1024 {
        commit(
            &mut child,
            &format!("wait-{i}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    let mut request = compile_request(&child);
    request.observer = "player".into();
    request.role = Role::Director;
    let p = compiler::compile(&child, &request).unwrap();
    let text = serde_json::to_string(&p).unwrap();
    assert!(p
        .records
        .iter()
        .any(|r| r.mandatory && r.sources.contains(&inspect::Source::Event(1))));
    assert!(text.contains("Repair beacon before tide"));
    assert!(!text.contains("PARENT-FUTURE-CANARY"));
    assert!(text.len() <= request.budget.max_bytes);
    assert!(p.estimated_tokens + p.reserved_tokens <= request.budget.estimated_tokens);
    request.at_revision = Some(1);
    let old = compiler::compile(&child, &request).unwrap();
    assert_eq!(old.scope, *child.scope());
    assert!(old.records.iter().all(|r| r.source_revision <= 1));
    let mut q = query(&child, View::History);
    q.search = "Repair beacon before tide".into();
    assert!(inspect::query(&child, &q, true).unwrap().total > 0);
    q.search = "PARENT-FUTURE-CANARY".into();
    assert_eq!(inspect::query(&child, &q, true).unwrap().total, 0);
}
