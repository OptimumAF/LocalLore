// Actual Store/Archive3/Query2 journey; the local runner supplies D: TEMP.
// Retained synthetic DBs have no Drop/delete cleanup.
// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    inspection_query::{query, Observer, Page, Query, QueryError, Row, Source, ValueOrigin, View},
};
use locallore_storage::{validate_archive, ForkRequest, Store};
use std::{
    collections::BTreeSet,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
fn retained_directory() -> PathBuf {
    let dir = std::env::temp_dir().join(format!(
        "locallore-archive-query-journey-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    std::fs::create_dir(&dir).unwrap();
    dir
}
fn create(store: &mut Store, story: &str) -> Scope {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "JOURNEY_OBSERVED_A".into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic Archive3 Query2 journey", seed)
        .unwrap();
    scope
}
fn apply(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&preview).unwrap()
}
fn authored(store: &mut Store, parent: &Scope, child: &str, from: &str, to: &str) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: head,
        fork_revision: head,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: from.into(),
            replacement: to.into(),
        },
        reason: format!("JOURNEY_PRIVATE_AUTHOR_REASON_{child}"),
    };
    let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
    store
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .scope
}
fn request(engine: &Engine, observer: Observer, view: View) -> Query {
    Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer,
        view,
        cursor: None,
        limit: 1,
        search: String::new(),
    }
}
fn pages(engine: &Engine, mut q: Query, grant: bool) -> Vec<Page> {
    let mut result = vec![];
    let mut seen = BTreeSet::new();
    let mut rows = 0;
    loop {
        let page = query(engine, &q, grant).unwrap();
        assert!(page.rows.len() <= usize::from(q.limit));
        rows += page.rows.len();
        let next = page.next_cursor.clone();
        let total = page.total;
        result.push(page);
        match next {
            None => {
                assert_eq!(rows, total);
                return result;
            }
            Some(cursor) => {
                assert!(seen.insert(cursor.clone()));
                q.cursor = Some(cursor);
            }
        }
        assert!(
            result.len() < 128,
            "Bounded real Query2 traversal must terminate"
        );
    }
}
fn full(engine: &Engine, observer: Observer, view: View, grant: bool) -> Page {
    let mut q = request(engine, observer, view);
    q.limit = 64;
    query(engine, &q, grant).unwrap()
}
fn observed(page: &Page, text: &str, expected: Source) {
    let row = page
        .rows
        .iter()
        .find(|row| {
            matches!(row,
        Row::Knowledge { id, origin: ValueOrigin::KnownAsObserved, .. } if id == "relic-location")
        })
        .unwrap();
    assert!(matches!(row, Row::Knowledge { text: actual, sources, .. }
        if actual == text && sources == &vec![expected]));
}
fn unchanged(actual: &Engine, expected: &Engine) {
    assert_eq!(actual.scope(), expected.scope());
    assert_eq!(actual.revision(), expected.revision());
    assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(actual.canonical_records(), expected.canonical_records());
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        expected.accepted_history_basis().unwrap()
    );
}

#[test]
fn archive3_preserves_query2_pages_and_sources_then_only_imported_future_observes_c() {
    let dir = retained_directory();
    let mut source = Store::open(&dir.join("source.sqlite"), None).unwrap();
    let root = create(&mut source, "archive-query-journey");
    apply(
        &mut source,
        &root,
        "prefix",
        vec![Command::Wait { ticks: 1 }],
    );
    let sibling = source
        .fork_branch(
            &ForkRequest {
                parent: root.clone(),
                child_branch: "sibling".into(),
                expected_parent_revision: 1,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    let b = authored(
        &mut source,
        &root,
        "private-b",
        "JOURNEY_OBSERVED_A",
        "JOURNEY_PRIVATE_B",
    );
    let gift = apply(
        &mut source,
        &b,
        "observe-and-gift",
        vec![
            Command::Discover {
                fact: "relic-location".into(),
            },
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        ],
    );
    let c = authored(
        &mut source,
        &b,
        "private-c",
        "JOURNEY_PRIVATE_B",
        "JOURNEY_PRIVATE_C",
    );
    apply(
        &mut source,
        &c,
        "before-export",
        vec![Command::Wait { ticks: 1 }],
    );
    // Equal heads and overlapping sequence numbers cannot blend future parent/sibling evidence.
    for (scope, text) in [
        (&root, "JOURNEY_PARENT_CANARY"),
        (&sibling, "JOURNEY_SIBLING_CANARY"),
    ] {
        let mut commands = vec![Command::Say {
            text: text.into(),
            audience: ["mira".into()].into(),
        }];
        commands.extend((0..4).map(|_| Command::Wait { ticks: 1 }));
        apply(&mut source, scope, "equal-head-future", commands);
    }
    let scopes = [&root, &sibling, &b, &c];
    let originals: Vec<_> = scopes
        .iter()
        .map(|scope| source.resume(scope).unwrap().engine)
        .collect();
    assert_eq!(originals[0].revision(), 6);
    assert_eq!(originals[1].revision(), 6);
    let current = &originals[3];
    assert_eq!(current.revision(), 6);
    let b_source = Source::ScopedEvent {
        original_scope: b.clone(),
        sequence: 3,
    };
    observed(
        &full(current, Observer::Player, View::Knowledge, false),
        "JOURNEY_PRIVATE_B",
        b_source.clone(),
    );
    observed(
        &full(
            current,
            Observer::Character { id: "mira".into() },
            View::Knowledge,
            true,
        ),
        "JOURNEY_OBSERVED_A",
        Source::Seed(current.seed().id.clone()),
    );
    let omni = full(current, Observer::Omniscient, View::Knowledge, true);
    assert!(omni.rows.iter().any(|row| matches!(row, Row::Knowledge { id, text, origin: ValueOrigin::CanonicalTruth, sources, .. }
        if id == "relic-location" && text == "JOURNEY_PRIVATE_C" && sources == &vec![Source::Withheld])));

    let archive = source.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(archive.preview().version, 3);
    let original_archive = archive.bytes().to_vec();
    let mut target = Store::open(&dir.join("target.sqlite"), None).unwrap();
    let control = create(&mut target, "target-foreign-control");
    apply(
        &mut target,
        &control,
        "foreign-only",
        vec![Command::Wait { ticks: 1 }],
    );
    let control_before = target.resume(&control).unwrap().engine;
    let imported = target
        .import_archive(
            validate_archive(&original_archive, &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert_eq!(imported.root, root);
    assert_eq!(imported.branches, 4);
    drop(target);
    let mut target = Store::open(&dir.join("target.sqlite"), None).unwrap();
    for (scope, expected) in scopes.iter().zip(&originals) {
        unchanged(&target.resume(scope).unwrap().engine, expected);
    }
    unchanged(&target.resume(&control).unwrap().engine, &control_before);
    let imported_c = target.resume(&c).unwrap().engine;

    // Each excluded canary is a real query-visible statement on its own branch,
    // both before and after transport, rather than absent from all histories.
    for (engine, canary) in [
        (&originals[0], "JOURNEY_PARENT_CANARY"),
        (&originals[1], "JOURNEY_SIBLING_CANARY"),
    ] {
        let mut q = request(engine, Observer::Player, View::History);
        q.search = canary.into();
        let positive = query(engine, &q, false).unwrap();
        assert_eq!((positive.total, positive.rows.len()), (1, 1));
        assert!(matches!(&positive.rows[0], Row::Event { event, .. }
            if matches!(&event.consequence, Effect::Said(claim) if claim.text == canary)));
        let imported_branch = target.resume(engine.scope()).unwrap().engine;
        assert_eq!(query(&imported_branch, &q, false).unwrap(), positive);
    }

    // Exact pages include privacy, matching totals, row origins/scoped sources,
    // next-cursor bytes and historical boundary metadata, not only canonical projection parity.
    for at in [None, Some(2), Some(4), Some(5)] {
        for (observer, grant) in [
            (Observer::Player, false),
            (Observer::Character { id: "mira".into() }, true),
            (Observer::Omniscient, true),
        ] {
            for view in [View::Knowledge, View::History] {
                let mut q = request(current, observer.clone(), view);
                q.at_revision = at;
                assert_eq!(
                    pages(&imported_c, q.clone(), grant),
                    pages(current, q, grant)
                );
            }
        }
    }
    let mut historical = request(current, Observer::Player, View::Knowledge);
    historical.limit = 64;
    historical.at_revision = Some(2);
    observed(
        &query(&imported_c, &historical, false).unwrap(),
        "JOURNEY_OBSERVED_A",
        Source::Seed(current.seed().id.clone()),
    );
    for revision in [4, 5, 6] {
        historical.at_revision = Some(revision);
        observed(
            &query(&imported_c, &historical, false).unwrap(),
            "JOURNEY_PRIVATE_B",
            b_source.clone(),
        );
    }
    historical.at_revision = Some(3); // Inside two-command discovery/gift receipt, not a completed turn.
    assert_eq!(
        query(&imported_c, &historical, false),
        Err(QueryError::InvalidBoundary)
    );

    for observer in [
        Observer::Character { id: "mira".into() },
        Observer::Omniscient,
    ] {
        let q = request(current, observer, View::Knowledge);
        assert_eq!(query(current, &q, false), Err(QueryError::Forbidden));
        assert_eq!(query(&imported_c, &q, false), Err(QueryError::Forbidden));
    }
    for canary in [
        "JOURNEY_PRIVATE_C",
        "JOURNEY_PRIVATE_AUTHOR_REASON",
        "JOURNEY_PARENT_CANARY",
        "JOURNEY_SIBLING_CANARY",
    ] {
        for view in [View::Knowledge, View::History] {
            let mut q = request(current, Observer::Player, view);
            q.search = canary.into();
            let before = query(current, &q, false).unwrap();
            assert_eq!(before.total, 0);
            assert!(before.rows.is_empty() && before.next_cursor.is_none());
            assert_eq!(query(&imported_c, &q, false).unwrap(), before);
        }
    }
    let first = query(
        current,
        &request(current, Observer::Player, View::History),
        false,
    )
    .unwrap();
    let source_cursor = first.next_cursor.unwrap();
    let mut continuation = request(current, Observer::Player, View::History);
    continuation.cursor = Some(source_cursor.clone());
    assert_eq!(
        query(&imported_c, &continuation, false),
        query(current, &continuation, false)
    );
    for equal_head_other in [&originals[0], &originals[1]] {
        let mut wrong_scope = continuation.clone();
        wrong_scope.scope = equal_head_other.scope().clone();
        assert_eq!(
            query(equal_head_other, &wrong_scope, false),
            Err(QueryError::InvalidCursor)
        );
    }

    // Import transports the original turn identity. Its retry cannot spend the inherited potion again.
    assert_eq!(
        target
            .lookup_turn(&b, &gift.request().turn)
            .unwrap()
            .receipt,
        Some(gift.clone())
    );
    assert_eq!(
        target.begin_turn(gift.request()).unwrap().receipt,
        Some(gift.clone())
    );
    assert_eq!(target.commit_prepared(&gift).unwrap(), gift);
    unchanged(&target.resume(&b).unwrap().engine, &originals[2]);
    unchanged(&target.resume(&c).unwrap().engine, current);
    assert_eq!(
        target
            .export_archive(&root.story, &|| false)
            .unwrap()
            .bytes(),
        original_archive
    );

    // Only deliberate new target gameplay makes C actor-known. Canonical C already
    // existed privately; importing or retrying the gift must not reveal it.
    let future = apply(
        &mut target,
        &c,
        "target-only-observe-c",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    assert_eq!(future.events()[0].sequence(), 7);
    let target_future = target.resume(&c).unwrap().engine;
    observed(
        &full(&target_future, Observer::Player, View::Knowledge, false),
        "JOURNEY_PRIVATE_C",
        Source::ScopedEvent {
            original_scope: c.clone(),
            sequence: 7,
        },
    );
    observed(
        &full(
            &target_future,
            Observer::Character { id: "mira".into() },
            View::Knowledge,
            true,
        ),
        "JOURNEY_OBSERVED_A",
        Source::Seed(current.seed().id.clone()),
    );
    assert_eq!(target_future.state().items["potion"].owner, "mira");
    assert_eq!(target_future.state().item_transfers["potion"].sequence, 4);
    assert_eq!(
        query(&target_future, &continuation, false),
        Err(QueryError::Stale)
    );
    continuation.expected_head = 7;
    assert_eq!(
        query(&target_future, &continuation, false),
        Err(QueryError::InvalidCursor)
    );
    historical.at_revision = Some(6);
    historical.expected_head = 7;
    observed(
        &query(&target_future, &historical, false).unwrap(),
        "JOURNEY_PRIVATE_B",
        b_source.clone(),
    );
    drop(target);
    let mut reopened = Store::open(&dir.join("target.sqlite"), None).unwrap();
    let final_engine = reopened.resume(&c).unwrap().engine;
    unchanged(&final_engine, &target_future);
    assert_eq!(
        pages(
            &final_engine,
            request(&final_engine, Observer::Player, View::Knowledge),
            false
        ),
        pages(
            &target_future,
            request(&target_future, Observer::Player, View::Knowledge),
            false
        )
    );
    unchanged(&reopened.resume(&control).unwrap().engine, &control_before);
    for (scope, expected) in scopes.iter().zip(&originals) {
        unchanged(&source.resume(scope).unwrap().engine, expected);
    }
    assert_eq!(
        source
            .export_archive(&root.story, &|| false)
            .unwrap()
            .bytes(),
        original_archive
    );
    let bytes: u64 = std::fs::read_dir(&dir)
        .unwrap()
        .map(|entry| entry.unwrap().metadata().unwrap().len())
        .sum();
    assert!(
        bytes < 2 * 1024 * 1024,
        "Retained source/target fixtures exceeded 2 MiB"
    );
    // No Drop/delete: keep both original and continued target evidence.
}
