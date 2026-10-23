// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Prototype only: actual bundled SQLite and accepted Engine events, no production migration.
#[path = "../src/derived_memory.rs"]
mod derived_memory;
use derived_memory::*;
use locallore::{
    contracts::*,
    engine::{render, Engine},
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{
    cell::Cell,
    path::PathBuf,
    sync::atomic::{AtomicUsize, Ordering},
};
static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let root = std::env::var_os("LOCALLORE_DERIVED_TEST_ROOT")
            .map(PathBuf::from)
            .unwrap_or_else(std::env::temp_dir);
        std::fs::create_dir_all(&root).unwrap();
        let path = root.join(format!(
            "derived-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn path(&self) -> PathBuf {
        self.0.join("prototype.sqlite")
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn apply(engine: &mut Engine, id: &str, commands: Vec<Command>) {
    let request = engine.request(id, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let narration = render(engine.preview(&request, &proposal).unwrap().events());
    engine.commit(&request, &proposal, &narration).unwrap();
}
fn say(engine: &mut Engine, id: &str, text: &str) {
    apply(
        engine,
        id,
        vec![Command::Say {
            text: text.into(),
            audience: ["mira".into()].into_iter().collect(),
        }],
    );
}
fn sample() -> Engine {
    let mut engine = Engine::new(seed()).unwrap();
    say(
        &mut engine,
        "claim",
        "The amber lighthouse is safe. ALLEGATION-ONLY",
    );
    apply(
        &mut engine,
        "belief",
        vec![Command::Believe { claim_event: 1 }],
    );
    apply(
        &mut engine,
        "gift",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    apply(
        &mut engine,
        "promise",
        vec![Command::Promise {
            id: "lantern-promise".into(),
            to: "mira".into(),
            terms: "Bring the copper lantern.".into(),
            deadline: 400,
            return_item: None,
        }],
    );
    for n in 0..6 {
        apply(
            &mut engine,
            &format!("wait-{n}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    engine
}
fn fixture(connection: &Connection, engine: &Engine) {
    connection
        .execute_batch("PRAGMA foreign_keys=ON; PRAGMA trusted_schema=OFF;")
        .unwrap();
    connection
        .execute_batch(include_str!("../migrations/001_initial.sql"))
        .unwrap();
    connection.execute_batch(DERIVED_SCHEMA_SQL).unwrap();
    let tx = connection.unchecked_transaction().unwrap();
    let seed = engine.seed();
    tx.execute(
        "INSERT INTO stories VALUES(?1,?2,'Synthetic',1,?3)",
        params![
            seed.scope.story,
            seed.scope.branch,
            serde_json::to_string(seed).unwrap()
        ],
    )
    .unwrap();
    tx.execute(
        "INSERT INTO branches VALUES(?1,?2,NULL,NULL,0)",
        params![seed.scope.story, seed.scope.branch],
    )
    .unwrap();
    for actor in seed.actors.keys() {
        tx.execute(
            "INSERT INTO entities VALUES(?1,'actor',?2)",
            params![seed.scope.story, actor],
        )
        .unwrap();
        tx.execute(
            "INSERT INTO branch_entities VALUES(?1,?2,'actor',?3)",
            params![seed.scope.story, seed.scope.branch, actor],
        )
        .unwrap();
    }
    tx.commit().unwrap();
    sync(connection, engine);
}
fn sync(connection: &Connection, engine: &Engine) {
    let tx = connection.unchecked_transaction().unwrap();
    for receipt in engine.receipts() {
        let r = receipt.request();
        tx.execute(
            "INSERT OR IGNORE INTO turns VALUES(?1,?2,?3,?4,'committed',?5,?6)",
            params![
                r.scope.story,
                r.scope.branch,
                r.turn,
                r.expected_revision as i64,
                serde_json::to_string(r).unwrap(),
                serde_json::to_string(receipt).unwrap()
            ],
        )
        .unwrap();
        for event in receipt.events() {
            tx.execute(
                "INSERT OR IGNORE INTO accepted_events VALUES(?1,?2,?3,?4,1,?5)",
                params![
                    r.scope.story,
                    r.scope.branch,
                    event.sequence() as i64,
                    r.turn,
                    serde_json::to_string(event).unwrap()
                ],
            )
            .unwrap();
            for observer in event.witnesses() {
                tx.execute(
                    "INSERT OR IGNORE INTO event_witnesses VALUES(?1,?2,?3,'actor',?4)",
                    params![
                        r.scope.story,
                        r.scope.branch,
                        event.sequence() as i64,
                        observer
                    ],
                )
                .unwrap();
            }
        }
    }
    tx.execute(
        "UPDATE branches SET head_revision=?3 WHERE story_id=?1 AND branch_id=?2",
        params![
            engine.scope().story,
            engine.scope().branch,
            engine.revision() as i64
        ],
    )
    .unwrap();
    tx.execute("INSERT INTO branch_projections VALUES(?1,?2,?3,1,?4) ON CONFLICT(story_id,branch_id) DO UPDATE SET revision=excluded.revision,projection_json=excluded.projection_json",params![engine.scope().story,engine.scope().branch,engine.revision()as i64,String::from_utf8(engine.canonical_bytes()).unwrap()]).unwrap();
    tx.commit().unwrap();
}
fn request(engine: &Engine, observer: &str) -> PrepareRequest {
    PrepareRequest {
        scope: engine.scope().clone(),
        expected_revision: engine.revision(),
        observer: observer.into(),
        from_exclusive: 0,
        through_revision: engine.revision(),
        target: Target::SceneWindow,
    }
}
fn search_request(engine: &Engine, observer: &str, text: &str) -> SearchRequest {
    SearchRequest {
        scope: engine.scope().clone(),
        expected_revision: engine.revision(),
        observer: observer.into(),
        text: text.into(),
        limit: 16,
    }
}
fn canonical_rows(connection: &Connection) -> Vec<String> {
    ["SELECT quote(story_id)||quote(branch_id)||quote(head_revision) FROM branches ORDER BY story_id,branch_id",
     "SELECT request_json||response_json FROM turns ORDER BY story_id,branch_id,turn_id",
     "SELECT envelope_json FROM accepted_events ORDER BY story_id,branch_id,sequence",
     "SELECT projection_json FROM branch_projections ORDER BY story_id,branch_id"]
    .into_iter().flat_map(|sql|connection.prepare(sql).unwrap().query_map([],|r|r.get::<_,String>(0)).unwrap().collect::<std::result::Result<Vec<_>,_>>().unwrap()).collect()
}
#[test]
fn typed_deterministic_extractives_preserve_attribution_and_compress_only_observed_time() {
    let engine = sample();
    let r = request(&engine, "player");
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    assert_eq!(
        connection
            .query_row("SELECT sqlite_version()", [], |r| r.get::<_, String>(0))
            .unwrap(),
        "3.53.2"
    );
    assert_eq!(
        connection
            .query_row("SELECT sqlite_compileoption_used('ENABLE_FTS5')", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
    let before = canonical_rows(&connection);
    let state = engine.canonical_bytes();
    assert_eq!(
        publish(
            &mut connection,
            prepare(&engine, &r, &|| false).unwrap(),
            &|| false
        )
        .unwrap(),
        PublishOutcome::Published
    );
    assert_eq!(
        publish(
            &mut connection,
            prepare(&engine, &r, &|| false).unwrap(),
            &|| false
        )
        .unwrap(),
        PublishOutcome::Unchanged
    );
    let packet = read(&connection, &engine, &r, &|| false).unwrap();
    let value = packet.json();
    assert_eq!(value["provenance"]["model"], Value::Null);
    assert_eq!(value["provenance"]["prompt"], Value::Null);
    assert_eq!(value["visibility"], "actor_observations");
    assert_eq!(value["source_revision"], engine.revision());
    let entries = value["entries"].as_array().unwrap();
    assert!(entries.iter().any(|e| e["class"] == "statement"
        && e["outcome"]["text"]
            .as_str()
            .unwrap()
            .contains("ALLEGATION-ONLY")));
    assert!(entries.iter().any(|e| e["class"] == "belief"));
    let time = entries
        .iter()
        .find(|e| e["class"] == "observed_time_span")
        .unwrap();
    assert_eq!(time["source_events"].as_array().unwrap().len(), 6);
    assert_eq!(time["to"], 106);
    assert!(entries.len() < value["source_events"].as_array().unwrap().len());
    assert_eq!(canonical_rows(&connection), before);
    assert_eq!(engine.canonical_bytes(), state);
    assert_eq!(
        search(
            &connection,
            &engine,
            &search_request(&engine, "player", "copper lantern"),
            &|| false
        )
        .unwrap()
        .len(),
        1
    );
}
#[test]
fn fts_corpus_is_partitioned_before_materializing_foreign_or_hidden_packets() {
    let engine = sample();
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    for observer in ["player", "mira"] {
        publish(
            &mut connection,
            prepare(&engine, &request(&engine, observer), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    }
    // Malformed-but-valid JSON in a different observer partition cannot reach parsing or FTS.
    connection
        .execute(
            "UPDATE derived_memory SET packet_json='{}' WHERE observer_id='player'",
            [],
        )
        .unwrap();
    let hits = search(
        &connection,
        &engine,
        &search_request(&engine, "mira", "amber lighthouse"),
        &|| false,
    )
    .unwrap();
    assert_eq!(hits.len(), 1);
    let text = hits[0].packet.json().to_string();
    for hidden in ["SECRET-TIDE-731", "belief", "source_claim"] {
        assert!(!text.contains(hidden), "{hidden}");
    }
    assert!(search(
        &connection,
        &engine,
        &search_request(&engine, "sable", "amber"),
        &|| false
    )
    .unwrap()
    .is_empty());
    let temp_count: i64 = connection
        .query_row(
            "SELECT count(*) FROM sqlite_temp_schema WHERE name='derived_memory_search'",
            [],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(temp_count, 0);
    assert_eq!(
        search(
            &connection,
            &engine,
            &search_request(&engine, "player", "amber"),
            &|| false
        )
        .unwrap_err(),
        MemoryError::Integrity
    );
}
#[test]
fn entity_sources_are_exact_and_hidden_or_nonexistent_entities_are_indistinguishable() {
    let engine = sample();
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    for (kind, id) in [
        (EntityKind::Actor, "mira"),
        (EntityKind::Item, "potion"),
        (EntityKind::Commitment, "lantern-promise"),
    ] {
        let mut r = request(&engine, "mira");
        r.target = Target::Entity {
            kind,
            id: id.into(),
        };
        publish(
            &mut connection,
            prepare(&engine, &r, &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
        let packet = read(&connection, &engine, &r, &|| false).unwrap();
        assert_eq!(packet.json()["target"]["id"], id);
    }
    for id in ["relic-location", "missing-fact"] {
        let mut r = request(&engine, "mira");
        r.target = Target::Entity {
            kind: EntityKind::Fact,
            id: id.into(),
        };
        assert_eq!(
            prepare(&engine, &r, &|| false).err(),
            Some(MemoryError::NotFound)
        );
    }
}
#[test]
fn stale_cancel_tampered_sources_and_packets_cannot_publish_or_be_read_as_fresh() {
    let mut engine = sample();
    let r = request(&engine, "player");
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    let stale = prepare(&engine, &r, &|| false).unwrap();
    publish(
        &mut connection,
        prepare(&engine, &r, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    let before = canonical_rows(&connection);
    assert_eq!(
        publish(
            &mut connection,
            prepare(&engine, &r, &|| false).unwrap(),
            &|| true
        )
        .unwrap_err(),
        MemoryError::Cancelled
    );
    connection.execute("UPDATE derived_memory SET packet_json=json_set(packet_json,'$.entries[0].outcome.text','FORGED')",[]).unwrap();
    assert_eq!(
        read(&connection, &engine, &r, &|| false).unwrap_err(),
        MemoryError::Integrity
    );
    publish(
        &mut connection,
        prepare(&engine, &r, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    connection.execute("UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.outcome.text','TAMPERED') WHERE sequence=1",[]).unwrap();
    assert_eq!(
        publish(
            &mut connection,
            prepare(&engine, &r, &|| false).unwrap(),
            &|| false
        )
        .unwrap_err(),
        MemoryError::Integrity
    );
    // Restore only our deliberately damaged synthetic fixture, never production data.
    connection
        .execute(
            "UPDATE accepted_events SET envelope_json=?1 WHERE sequence=1",
            [serde_json::to_string(&engine.receipts()[0].events()[0]).unwrap()],
        )
        .unwrap();
    assert_eq!(canonical_rows(&connection), before);
    apply(&mut engine, "new-fact", vec![Command::Wait { ticks: 1 }]);
    sync(&connection, &engine);
    assert_eq!(
        publish(&mut connection, stale, &|| false).unwrap_err(),
        MemoryError::Stale
    );
    assert_eq!(
        read(&connection, &engine, &r, &|| false).unwrap_err(),
        MemoryError::Stale
    );
    assert!(search(
        &connection,
        &engine,
        &search_request(&engine, "player", "amber"),
        &|| false
    )
    .unwrap()
    .is_empty());
    let fresh = request(&engine, "player");
    publish(
        &mut connection,
        prepare(&engine, &fresh, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    assert_eq!(
        search(
            &connection,
            &engine,
            &search_request(&engine, "player", "amber"),
            &|| false
        )
        .unwrap()
        .len(),
        1
    );
}
#[test]
fn maintenance_can_resume_after_reopen_and_explicit_invalidation_never_mutates_canon() {
    let temp = Temp::new();
    let engine = sample();
    let r = request(&engine, "player");
    let mut connection = Connection::open(temp.path()).unwrap();
    fixture(&connection, &engine);
    let before = canonical_rows(&connection);
    publish(
        &mut connection,
        prepare(&engine, &r, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    drop(connection);
    let mut connection = Connection::open(temp.path()).unwrap();
    assert!(read(&connection, &engine, &r, &|| false).is_ok());
    assert_eq!(
        invalidate(&mut connection, engine.scope(), "player", 0, &|| false).unwrap_err(),
        MemoryError::Stale
    );
    invalidate(
        &mut connection,
        engine.scope(),
        "player",
        engine.revision(),
        &|| false,
    )
    .unwrap();
    assert_eq!(
        read(&connection, &engine, &r, &|| false).unwrap_err(),
        MemoryError::NotFound
    );
    publish(
        &mut connection,
        prepare(&engine, &r, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    assert_eq!(canonical_rows(&connection), before);
}
#[test]
fn bounded_callbacks_cancel_and_panic_without_partial_replacement_or_temp_retention() {
    let engine = sample();
    let r = request(&engine, "player");
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    publish(
        &mut connection,
        prepare(&engine, &r, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    let before = read(&connection, &engine, &r, &|| false).unwrap();
    let canonical = canonical_rows(&connection);
    let checks = Cell::new(0);
    let cancel = || {
        checks.set(checks.get() + 1);
        checks.get() > 4
    };
    assert_eq!(
        prepare(&engine, &r, &cancel).err(),
        Some(MemoryError::Cancelled)
    );
    let checks = Cell::new(0);
    let cancel = || {
        checks.set(checks.get() + 1);
        checks.get() > 4
    };
    assert_eq!(
        publish(
            &mut connection,
            prepare(&engine, &r, &|| false).unwrap(),
            &cancel
        )
        .unwrap_err(),
        MemoryError::Cancelled
    );
    assert_eq!(read(&connection, &engine, &r, &|| false).unwrap(), before);
    assert_eq!(
        invalidate(
            &mut connection,
            engine.scope(),
            "player",
            engine.revision(),
            &|| panic!("synthetic cancellation callback")
        )
        .unwrap_err(),
        MemoryError::Cancelled
    );
    for threshold in 0..40 {
        let checks = Cell::new(0);
        let cancel = || {
            checks.set(checks.get() + 1);
            checks.get() > threshold
        };
        let result = search(
            &connection,
            &engine,
            &search_request(&engine, "player", "amber"),
            &cancel,
        );
        assert!(result.is_ok() || result == Err(MemoryError::Cancelled));
        assert_eq!(
            connection
                .query_row(
                    "SELECT count(*) FROM sqlite_temp_schema WHERE name='derived_memory_search'",
                    [],
                    |r| r.get::<_, i64>(0)
                )
                .unwrap(),
            0
        );
    }
    assert_eq!(canonical_rows(&connection), canonical);
}
#[test]
fn escaped_fts_literals_bounds_and_no_results_never_execute_search_grammar_or_sql() {
    let engine = sample();
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    publish(
        &mut connection,
        prepare(&engine, &request(&engine, "player"), &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    let canonical = canonical_rows(&connection);
    for text in [
        "amber OR secret",
        "\" OR *",
        "amber); DROP TABLE accepted_events; --",
        "NEAR(amber,1)",
        "",
        "missing_word",
        "***",
    ] {
        assert!(
            search(
                &connection,
                &engine,
                &search_request(&engine, "player", text),
                &|| false
            )
            .unwrap()
            .is_empty(),
            "{text}"
        );
    }
    assert_eq!(
        search(
            &connection,
            &engine,
            &search_request(&engine, "player", "amber"),
            &|| false
        )
        .unwrap()
        .len(),
        1
    );
    for text in [
        "x".repeat(MAX_QUERY_BYTES + 1),
        "a ".repeat(MAX_SEARCH_TERMS + 1),
        "line\nbreak".into(),
    ] {
        assert_eq!(
            search(
                &connection,
                &engine,
                &search_request(&engine, "player", &text),
                &|| false
            )
            .unwrap_err(),
            MemoryError::InvalidInput
        );
    }
    for limit in [0, MAX_HITS + 1] {
        let mut r = search_request(&engine, "player", "amber");
        r.limit = limit;
        assert_eq!(
            search(&connection, &engine, &r, &|| false).unwrap_err(),
            MemoryError::InvalidInput
        );
    }
    assert_eq!(canonical_rows(&connection), canonical);
}
#[test]
fn paired_hidden_histories_do_not_consume_eligible_budget_or_enter_mira_summary() {
    // Both have the SAME public head; excluded bodies differ in bytes and lexical canaries.
    let mut small = Engine::new(seed()).unwrap();
    let mut large = Engine::new(seed()).unwrap();
    say(&mut small, "visible", "The copper lantern is ready.");
    say(&mut large, "visible", "The copper lantern is ready.");
    for n in 0..1023 {
        // Wait is witnessed only by the player. Mira receives no hidden volume/count metadata.
        apply(
            &mut small,
            &format!("private-{n}"),
            vec![Command::Wait { ticks: 1 }],
        );
        apply(
            &mut large,
            &format!("private-{n}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    apply(
        &mut small,
        "private-words",
        vec![Command::Say {
            text: "PRIVATE-SMALL".into(),
            audience: ["player".into()].into_iter().collect(),
        }],
    );
    apply(
        &mut large,
        "private-words",
        vec![Command::Say {
            text: format!("PRIVATE-LARGE-{}", "z".repeat(500)),
            audience: ["player".into()].into_iter().collect(),
        }],
    );
    let mut a = Connection::open_in_memory().unwrap();
    let mut b = Connection::open_in_memory().unwrap();
    fixture(&a, &small);
    fixture(&b, &large);
    let ra = request(&small, "mira");
    let rb = request(&large, "mira");
    publish(&mut a, prepare(&small, &ra, &|| false).unwrap(), &|| false).unwrap();
    publish(&mut b, prepare(&large, &rb, &|| false).unwrap(), &|| false).unwrap();
    assert_eq!(
        read(&a, &small, &ra, &|| false).unwrap(),
        read(&b, &large, &rb, &|| false).unwrap()
    );
    assert_eq!(
        search(
            &a,
            &small,
            &search_request(&small, "mira", "copper"),
            &|| false
        )
        .unwrap(),
        search(
            &b,
            &large,
            &search_request(&large, "mira", "copper"),
            &|| false
        )
        .unwrap()
    );
    assert_eq!(
        prepare(&small, &request(&small, "player"), &|| false).err(),
        Some(MemoryError::TooLarge)
    );
    assert!(search(
        &a,
        &small,
        &search_request(&small, "mira", "PRIVATE SMALL"),
        &|| false
    )
    .unwrap()
    .is_empty());
    assert!(search(
        &b,
        &large,
        &search_request(&large, "mira", "PRIVATE LARGE"),
        &|| false
    )
    .unwrap()
    .is_empty());
    // Even >1000 excluded events fit a 1-event eligible summary; no global cap/cloning.
    let start = std::time::Instant::now();
    let prepared = prepare(&small, &ra, &|| false).unwrap();
    let prepare_us = start.elapsed().as_micros();
    assert_eq!(
        publish(&mut a, prepared, &|| false).unwrap(),
        PublishOutcome::Unchanged
    );
    let start = std::time::Instant::now();
    let hits = search(
        &a,
        &small,
        &search_request(&small, "mira", "copper"),
        &|| false,
    )
    .unwrap();
    let search_us = start.elapsed().as_micros();
    let packet = read(&a, &small, &ra, &|| false).unwrap();
    assert_eq!(packet.json()["source_events"], json!([1]));
    println!(
        "{}",
        json!({"fixture":"synthetic-paired-hidden-history","accepted_events":small.revision(),
        "eligible_sources":1,"packet_bytes":packet.json().to_string().len(),"hits":hits.len(),
        "prepare_us":prepare_us,"search_us":search_us,"tokenizer":"not_run","model":"not_run"})
    );
}
#[test]
fn range_scope_policy_and_caps_fail_closed_without_inventing_chapters_or_branches() {
    let engine = sample();
    let mut r = request(&engine, "player");
    r.scope.story = "foreign".into();
    assert_eq!(
        prepare(&engine, &r, &|| false).err(),
        Some(MemoryError::Scope)
    );
    let mut r = request(&engine, "player");
    r.expected_revision -= 1;
    assert_eq!(
        prepare(&engine, &r, &|| false).err(),
        Some(MemoryError::Stale)
    );
    let mut r = request(&engine, "player");
    r.through_revision -= 1;
    assert_eq!(
        prepare(&engine, &r, &|| false).err(),
        Some(MemoryError::Stale)
    );
    let mut r = request(&engine, "player");
    r.from_exclusive = r.through_revision + 1;
    assert_eq!(
        prepare(&engine, &r, &|| false).err(),
        Some(MemoryError::InvalidInput)
    );
    let mut r = request(&engine, "player");
    r.observer = "missing".into();
    assert_eq!(
        prepare(&engine, &r, &|| false).err(),
        Some(MemoryError::NotFound)
    );
    let fork = engine.fork("child", engine.revision()).unwrap();
    assert_eq!(
        prepare(&fork, &request(&fork, "player"), &|| false)
            .unwrap()
            .scope(),
        fork.scope()
    );
}

#[test]
fn partition_packet_cap_is_local_and_full_packet_byte_cap_is_enforced() {
    let mut engine = sample();
    for n in 0..32 {
        apply(
            &mut engine,
            &format!("more-{n}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    for n in 0..MAX_PARTITION_PACKETS {
        let mut r = request(&engine, "player");
        r.from_exclusive = n as u64;
        publish(
            &mut connection,
            prepare(&engine, &r, &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    }
    let mut overflow = request(&engine, "player");
    overflow.from_exclusive = MAX_PARTITION_PACKETS as u64;
    assert_eq!(
        publish(
            &mut connection,
            prepare(&engine, &overflow, &|| false).unwrap(),
            &|| false
        )
        .unwrap_err(),
        MemoryError::TooLarge
    );
    // Another observer's full partition cannot consume Mira's capacity.
    let r = request(&engine, "mira");
    publish(
        &mut connection,
        prepare(&engine, &r, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    assert!(read(&connection, &engine, &r, &|| false).is_ok());
    // Large eligible statements cannot bypass the complete packet bound.
    let mut text = Engine::new(seed()).unwrap();
    for n in 0..80 {
        say(&mut text, &format!("long-{n}"), &"w".repeat(MAX_TEXT_BYTES));
    }
    assert_eq!(
        prepare(&text, &request(&text, "player"), &|| false).err(),
        Some(MemoryError::TooLarge)
    );
}

#[test]
fn actual_sqlite_failure_during_cache_insert_rolls_back_without_touching_canon() {
    let engine = sample();
    let mut connection = Connection::open_in_memory().unwrap();
    fixture(&connection, &engine);
    let r = request(&engine, "player");
    publish(
        &mut connection,
        prepare(&engine, &r, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    let prior = read(&connection, &engine, &r, &|| false).unwrap();
    let canonical = canonical_rows(&connection);
    let mut entity = r.clone();
    entity.target = Target::Entity {
        kind: EntityKind::Item,
        id: "potion".into(),
    };
    connection.execute_batch("CREATE TRIGGER test_cache_failure AFTER INSERT ON derived_memory BEGIN SELECT RAISE(ABORT,'synthetic failure'); END;").unwrap();
    assert_eq!(
        publish(
            &mut connection,
            prepare(&engine, &entity, &|| false).unwrap(),
            &|| false
        )
        .unwrap_err(),
        MemoryError::Database
    );
    assert_eq!(
        read(&connection, &engine, &entity, &|| false).unwrap_err(),
        MemoryError::NotFound
    );
    assert_eq!(read(&connection, &engine, &r, &|| false).unwrap(), prior);
    assert_eq!(canonical_rows(&connection), canonical);
    connection
        .execute_batch("DROP TRIGGER test_cache_failure")
        .unwrap();
    publish(
        &mut connection,
        prepare(&engine, &entity, &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
}
