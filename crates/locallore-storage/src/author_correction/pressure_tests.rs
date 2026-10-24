//! Private real SQLite pressure oracle. No production cap or wire control.
use super::*;
use locallore::author_correction::AuthorCorrectionOperationV1;
use locallore::contracts::Seed;
use rusqlite::types::Value;

struct Temp(std::path::PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-author-full-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        assert!(self.0.starts_with(std::env::temp_dir()));
        assert!(self
            .0
            .file_name()
            .unwrap()
            .to_string_lossy()
            .starts_with("locallore-author-full-"));
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn rows(connection: &Connection) -> Vec<Vec<Vec<Value>>> {
    [
        "stories",
        "branches",
        "entities",
        "branch_entities",
        "turns",
        "accepted_events",
        "event_witnesses",
        "branch_projections",
        "derived_memory",
        "branch_retention",
        "memory_jobs",
        "memory_job_packets",
    ]
    .into_iter()
    .map(|table| {
        let mut query = connection
            .prepare(&format!("SELECT * FROM {table} ORDER BY 1,2"))
            .unwrap();
        let columns = query.column_count();
        query
            .query_map([], |row| {
                (0..columns)
                    .map(|i| row.get(i))
                    .collect::<std::result::Result<Vec<Value>, _>>()
            })
            .unwrap()
            .collect::<std::result::Result<Vec<_>, _>>()
            .unwrap()
    })
    .collect()
}
#[test]
fn real_sqlite_full_author_creation_rolls_back_then_same_preparation_retries_once() {
    let temp = Temp::new();
    let path = temp.0.join("synthetic.sqlite");
    let mut store = Store::open(&path, None).unwrap();
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    seed.facts.get_mut("relic-location").unwrap().proposition = "OBSERVED_A".into();
    let parent = seed.scope.clone();
    store.create_story("Synthetic author Full", seed).unwrap();
    let before = store.resume(&parent).unwrap().engine;
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: "author-full-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "OBSERVED_A".into(),
            replacement: "\u{1}".repeat(2048),
        },
        reason: "\u{1}".repeat(2048),
    };
    let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
    let original_max: i64 = store
        .connection
        .pragma_query_value(None, "max_page_count", |r| r.get(0))
        .unwrap();
    let pages: i64 = store
        .connection
        .pragma_query_value(None, "page_count", |r| r.get(0))
        .unwrap();
    store
        .connection
        .pragma_update(None, "max_page_count", pages)
        .unwrap();
    let actual_cap: i64 = store
        .connection
        .pragma_query_value(None, "max_page_count", |r| r.get(0))
        .unwrap();
    assert_eq!(actual_cap, pages);
    let snapshot = rows(&store.connection);
    let result = store.apply_author_correction(&prepared, &|| false);
    assert_eq!(
        result,
        Err(TurnError::Full),
        "must observe real SQLite Full, not a synthetic ABORT or any arbitrary error"
    );
    assert_eq!(
        rows(&store.connection),
        snapshot,
        "all application rows roll back together"
    );
    assert_eq!(
        store.resume(&parent).unwrap().engine.canonical_bytes(),
        before.canonical_bytes()
    );
    assert!(store
        .lookup_author_correction(&input, &|| false)
        .unwrap()
        .is_none());
    store
        .connection
        .pragma_update(None, "max_page_count", original_max)
        .unwrap();
    let accepted = store.apply_author_correction(&prepared, &|| false).unwrap();
    assert!(accepted.created);
    assert_eq!(
        (
            accepted.fork_revision,
            accepted.author_revision,
            accepted.head_revision
        ),
        (0, 1, 1)
    );
    let replay = store.apply_author_correction(&prepared, &|| false).unwrap();
    assert!(!replay.created);
    assert_eq!(replay.scope, accepted.scope);
    let child = store.resume(&accepted.scope).unwrap().engine;
    assert_eq!(child.domain_version(), 2);
    assert_eq!(child.canonical_record_count(), 1);
    assert_eq!(
        child.effective_fact("relic-location").unwrap().proposition,
        "\u{1}".repeat(2048)
    );
    assert_eq!(child.state().story_time, before.state().story_time);
    assert_eq!(
        store.resume(&parent).unwrap().engine.canonical_bytes(),
        before.canonical_bytes()
    );
    let request = crate::memory_jobs::MemoryJobRequest {
        scope: accepted.scope.clone(),
        observer: "player".into(),
        expected_head: 1,
    };
    assert!(matches!(
        store.ensure_memory_job(&request, &|| false),
        Err(crate::derived_memory::MemoryError::Unsupported)
    ));
    let coherent = store.context_snapshot(&request, &|| false).unwrap();
    assert_eq!(
        coherent.engine.accepted_history_basis().unwrap(),
        child.accepted_history_basis().unwrap()
    );
    assert!(matches!(
        coherent.coverage,
        locallore::memory_coverage::CoverageRead::RawFallback(
            locallore::memory_coverage::FallbackReason::Unsupported
        )
    ));
    drop(store);
    let mut reopened = Store::open(&path, None).unwrap();
    let recovered = reopened
        .lookup_author_correction(&input, &|| false)
        .unwrap()
        .unwrap();
    assert!(!recovered.created);
    assert_eq!(recovered.head_revision, 1);
    assert_eq!(
        reopened
            .resume(&accepted.scope)
            .unwrap()
            .engine
            .accepted_history_basis()
            .unwrap(),
        child.accepted_history_basis().unwrap()
    );
}
