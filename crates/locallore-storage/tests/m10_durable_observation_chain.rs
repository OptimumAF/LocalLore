// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Original SQLite/Query2 composition oracle.
//! Uses public Store mutation/resume and public Core query; no SQL writer/model.
use locallore::{author_correction::*, contracts::*, engine::Engine, inspection_query::*};
use locallore_storage::{ForkRequest, Store, TurnPhase};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

const A: &str = "B96_A_SEED_KNOWN";
const B: &str = "B96_B_OBSERVED_AFTER_CORRECTION";
const C: &str = "B96_C_UNOBSERVED_PRIVATE_WORLD";
const PARENT_FUTURE: &str = "B96_PARENT_ONLY_AFTER_SELECTED_FORK";
const SIBLING_FUTURE: &str = "B96_SIBLING_ONLY_AFTER_SELECTED_FORK";
const REASON: &str = "B96_PRIVATE_AUTHOR_EXPLANATION";
static NEXT: AtomicU64 = AtomicU64::new(0);

struct RetainedDatabase(PathBuf);
impl RetainedDatabase {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let path = parent.join(format!(
            "locallore-m10-durable-observation-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn open(&self) -> Store {
        Store::open(&self.path(), None).unwrap()
    }
}
// Deliberately no Drop/cleanup: unique synthetic DB and any failure evidence stay.

fn reopened(temp: &RetainedDatabase, scope: &Scope, expected: &Engine) -> Engine {
    let mut store = temp.open();
    let resumed = store.resume(scope).unwrap();
    assert!(!resumed.projection_needs_rebuild);
    assert_eq!(resumed.engine.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(
        resumed.engine.canonical_records(),
        expected.canonical_records()
    );
    assert_eq!(
        resumed.engine.accepted_history_basis().unwrap(),
        expected.accepted_history_basis().unwrap()
    );
    resumed.engine
}

fn amend(
    temp: &RetainedDatabase,
    parent: &Scope,
    child: &str,
    old: &str,
    new: &str,
) -> (Scope, Engine) {
    let mut store = temp.open();
    let engine = store.resume(parent).unwrap().engine;
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: engine.revision(),
        fork_revision: engine.revision(),
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old.into(),
            replacement: new.into(),
        },
        reason: REASON.into(),
    };
    let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
    let result = store.apply_author_correction(&prepared, &|| false).unwrap();
    assert!(result.created);
    assert_eq!(result.author_revision, engine.revision() + 1);
    let child_engine = store.resume(&result.scope).unwrap().engine;
    (result.scope, child_engine)
}

fn append(
    temp: &RetainedDatabase,
    scope: &Scope,
    turn: &str,
    command: Command,
) -> (Receipt, Engine) {
    let mut store = temp.open();
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(vec![command]));
    let prepared = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    let receipt = store.commit_prepared(&prepared).unwrap();
    let after = store.resume(scope).unwrap().engine;
    (receipt, after)
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
        limit: MAX_ROWS,
        search: String::new(),
    }
}

fn remembered(page: &Page) -> (&str, &[Source]) {
    page.rows
        .iter()
        .find_map(|row| match row {
            Row::Knowledge {
                id,
                text,
                sources,
                origin: ValueOrigin::KnownAsObserved,
                ..
            } if id == "relic-location" => Some((text.as_str(), sources.as_slice())),
            _ => None,
        })
        .unwrap()
}

fn known(engine: &Engine, observer: Observer, grant: bool) -> String {
    let page = query(engine, &request(engine, observer, View::Knowledge), grant).unwrap();
    remembered(&page).0.into()
}

#[test]
fn sqlite_reopens_preserve_query2_observation_history_and_same_head_branch_isolation() {
    let temp = RetainedDatabase::new();
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let player = seed.player.clone();
    let seed_id = seed.id.clone();
    let root = seed.scope.clone();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert(player.clone());
    fact.known_by.insert("mira".into());
    let initial = {
        let mut store = temp.open();
        store
            .create_story("Synthetic durable epistemic boundaries", seed)
            .unwrap();
        store.resume(&root).unwrap().engine
    };
    let initial = reopened(&temp, &root, &initial);
    assert_eq!(known(&initial, Observer::Player, false), A);

    let (first_scope, first_before_close) = amend(&temp, &root, "first-correction", A, B);
    let first = reopened(&temp, &first_scope, &first_before_close);
    assert_eq!(first.revision(), 1);
    assert_eq!(known(&first, Observer::Player, false), A);
    assert_eq!(
        known(&first, Observer::Character { id: "mira".into() }, true),
        A
    );
    let private_b = query(
        &first,
        &request(&first, Observer::Omniscient, View::Knowledge),
        true,
    )
    .unwrap();
    assert!(private_b.rows.iter().any(|r| matches!(r,
        Row::Knowledge { id, text, origin: ValueOrigin::CanonicalTruth, .. }
        if id == "relic-location" && text == B)));

    let (discovery, observed_before_close) = append(
        &temp,
        &first_scope,
        "observed-B",
        Command::Discover {
            fact: "relic-location".into(),
        },
    );
    let observed = reopened(&temp, &first_scope, &observed_before_close);
    assert_eq!(observed.revision(), 2);
    assert_eq!(known(&observed, Observer::Player, false), B);
    assert_eq!(
        known(&observed, Observer::Character { id: "mira".into() }, true),
        A
    );
    {
        let mut store = temp.open();
        let durable_turn = store.lookup_turn(&first_scope, "observed-B").unwrap();
        assert_eq!(durable_turn.phase, TurnPhase::Committed);
        assert_eq!(durable_turn.receipt, Some(discovery.clone()));
    }

    let (sibling_scope, sibling_before_close) = {
        let mut store = temp.open();
        let result = store
            .fork_branch(
                &ForkRequest {
                    parent: first_scope.clone(),
                    child_branch: "sibling".into(),
                    expected_parent_revision: 2,
                    at_revision: 2,
                },
                &|| false,
            )
            .unwrap();
        let engine = store.resume(&result.scope).unwrap().engine;
        (result.scope, engine)
    };
    let sibling = reopened(&temp, &sibling_scope, &sibling_before_close);
    assert_eq!(known(&sibling, Observer::Player, false), B);

    let (selected_scope, selected_before_close) =
        amend(&temp, &first_scope, "second-correction", B, C);
    let selected = reopened(&temp, &selected_scope, &selected_before_close);
    assert_eq!(selected.revision(), 3);
    assert_eq!(known(&selected, Observer::Player, false), B);
    assert_eq!(
        known(&selected, Observer::Character { id: "mira".into() }, true),
        A
    );

    let (_, parent_before_close) = append(
        &temp,
        &first_scope,
        "parent-future",
        Command::Say {
            text: PARENT_FUTURE.into(),
            audience: [player.clone()].into(),
        },
    );
    let parent = reopened(&temp, &first_scope, &parent_before_close);
    let (_, sibling_before_close) = append(
        &temp,
        &sibling_scope,
        "sibling-future",
        Command::Say {
            text: SIBLING_FUTURE.into(),
            audience: [player].into(),
        },
    );
    let sibling = reopened(&temp, &sibling_scope, &sibling_before_close);
    let selected = reopened(&temp, &selected_scope, &selected);
    assert_eq!(
        (parent.revision(), sibling.revision(), selected.revision()),
        (3, 3, 3)
    );
    // Positive controls: each excluded future is actually query-visible on
    // its own reopened branch, so empty selected-branch results are meaningful.
    for (engine, canary) in [(&parent, PARENT_FUTURE), (&sibling, SIBLING_FUTURE)] {
        let mut own = request(engine, Observer::Player, View::History);
        own.search = canary.into();
        let page = query(engine, &own, false).unwrap();
        assert_eq!((page.total, page.rows.len()), (1, 1));
        assert!(matches!(&page.rows[0], Row::Event { event, .. }
            if matches!(&event.consequence, Effect::Said(claim) if claim.text == canary)));
    }
    let source = Source::ScopedEvent {
        original_scope: first_scope.clone(),
        sequence: discovery.events()[0].sequence(),
    };
    assert_eq!(discovery.events()[0].sequence(), 2);
    let selected_before_reads = selected.canonical_bytes();
    let selected_records = selected.canonical_records().to_vec();

    let current = query(
        &selected,
        &request(&selected, Observer::Player, View::Knowledge),
        false,
    )
    .unwrap();
    assert_eq!(remembered(&current), (B, std::slice::from_ref(&source)));
    assert!(current.rows.iter().any(|r| matches!(r,
        Row::Knowledge { text, sources, origin: ValueOrigin::RecordedDiscovery, .. }
        if text == B && sources == &vec![source.clone()])));
    for view in [
        View::Knowledge,
        View::History,
        View::Provenance,
        View::TurnDiff,
    ] {
        for hidden in [C, PARENT_FUTURE, SIBLING_FUTURE, REASON] {
            let mut q = request(&selected, Observer::Player, view);
            q.search = hidden.into();
            q.limit = 1;
            let page = query(&selected, &q, false).unwrap();
            assert_eq!(page.total, 0, "{view:?} must not count {hidden}");
            assert!(page.rows.is_empty() && page.next_cursor.is_none());
        }
    }
    for (revision, expected) in [(1, A), (2, B)] {
        let mut q = request(&selected, Observer::Player, View::Knowledge);
        q.at_revision = Some(revision);
        let page = query(&selected, &q, false).unwrap();
        assert_eq!((page.head, page.revision), (3, revision));
        assert_eq!(remembered(&page).0, expected);
        if revision == 1 {
            assert_eq!(remembered(&page).1, &[Source::Seed(seed_id.clone())]);
            assert!(!page.rows.iter().any(|r| matches!(
                r,
                Row::Knowledge {
                    origin: ValueOrigin::RecordedDiscovery,
                    ..
                }
            )));
        } else {
            assert_eq!(remembered(&page).1, std::slice::from_ref(&source));
        }
    }
    let mut q = request(&selected, Observer::Player, View::Knowledge);
    q.search = B.into();
    q.limit = 1;
    let first = query(&selected, &q, false).unwrap();
    assert_eq!((first.total, first.rows.len()), (2, 1));
    q.cursor = first.next_cursor.clone();
    assert!(q.cursor.is_some());
    let second = query(&selected, &q, false).unwrap();
    assert_eq!((second.total, second.rows.len()), (2, 1));
    assert!(second.next_cursor.is_none());
    assert_ne!(first.rows[0].key(), second.rows[0].key());
    let mut historical = q.clone();
    historical.at_revision = Some(2);
    assert_eq!(
        query(&selected, &historical, false).unwrap_err(),
        QueryError::InvalidCursor
    );
    let mut cross_branch = q;
    cross_branch.scope = sibling_scope.clone();
    assert_eq!(
        query(&sibling, &cross_branch, false).unwrap_err(),
        QueryError::InvalidCursor
    );

    let omni_request = request(&selected, Observer::Omniscient, View::Knowledge);
    assert_eq!(
        query(&selected, &omni_request, false).unwrap_err(),
        QueryError::Forbidden
    );
    let omni = query(&selected, &omni_request, true).unwrap();
    assert!(omni.rows.iter().any(|r| matches!(r,
        Row::Knowledge { id, text, origin: ValueOrigin::CanonicalTruth, .. }
        if id == "relic-location" && text == C)));
    let npc_request = request(
        &selected,
        Observer::Character { id: "mira".into() },
        View::Knowledge,
    );
    assert_eq!(
        query(&selected, &npc_request, false).unwrap_err(),
        QueryError::Forbidden
    );
    assert_eq!(
        remembered(&query(&selected, &npc_request, true).unwrap()).0,
        A
    );
    assert_eq!(selected.canonical_bytes(), selected_before_reads);
    assert_eq!(selected.canonical_records(), selected_records.as_slice());

    // Actual read-only SQLite reopen, not just repeated queries on one Engine.
    // Canonical replay and this synthetic main DB must remain unchanged.
    assert!(std::fs::metadata(temp.path()).unwrap().len() <= 2 * 1024 * 1024);
    let before_read_only = std::fs::read(temp.path()).unwrap();
    {
        let mut read_only = Store::open_read_only(&temp.path()).unwrap();
        for (scope, expected) in [
            (&root, &initial),
            (&first_scope, &parent),
            (&sibling_scope, &sibling),
            (&selected_scope, &selected),
        ] {
            let loaded = read_only.resume(scope).unwrap();
            assert!(!loaded.projection_needs_rebuild);
            assert_eq!(loaded.engine.canonical_bytes(), expected.canonical_bytes());
            assert_eq!(
                loaded.engine.canonical_records(),
                expected.canonical_records()
            );
        }
        let loaded = read_only.resume(&selected_scope).unwrap().engine;
        assert_eq!(known(&loaded, Observer::Player, false), B);
        assert_eq!(
            known(&loaded, Observer::Character { id: "mira".into() }, true),
            A
        );
    }
    assert_eq!(std::fs::read(temp.path()).unwrap(), before_read_only);
    assert_eq!(
        reopened(&temp, &selected_scope, &selected).canonical_bytes(),
        selected_before_reads
    );
    assert!(temp.0.is_dir() && temp.path().is_file()); // Kept; never deleted.
}
