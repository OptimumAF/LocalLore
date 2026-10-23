// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Fixed original model-free M07.06 corpus. All events are accepted by typed
//! Engine/Store APIs; no SQL fixture history, provider or production mutation.
use locallore::{
    context_compiler::{
        compile, compile_cancelled, Budget, CompileError, CompileRequest, ContextPackage, Payload,
        Role, COMPILER_VERSION,
    },
    contracts::*,
    engine::Engine,
    inspection_query::{
        query, FieldValue, Observer, Query, Row, Source, ValueOrigin, View, MAX_ROWS, QUERY_VERSION,
    },
};
use locallore_storage::{
    derived_memory::{EntityKind, MemoryError, PrepareRequest, SearchRequest, Target},
    ForkRequest, Store,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, path::PathBuf, time::Instant};

const ROOT_HEAD: u64 = 1032;
const CHILD_HEAD: u64 = 1034;
const OLD: &str = "SPINDLE-ORCHARD-ANCHOR";
const PRIVATE: &str = "PLAYER-ONLY-GLASS-ANCHOR";
const CHILD_PRIVATE: &str = "CHILD-ONLY-GLASS-ANCHOR";
const FORBIDDEN: [&str; 3] = ["PARENT-FUTURE-ANCHOR", "SIBLING-ANCHOR", "FOREIGN-ANCHOR"];

struct Artifacts {
    directory: PathBuf,
    retain: bool,
}
impl Artifacts {
    fn new() -> Self {
        let configured = std::env::var_os("LOCALLORE_LONG_HISTORY_ARTIFACT_ROOT");
        let root = configured
            .clone()
            .map(PathBuf::from)
            .unwrap_or_else(std::env::temp_dir);
        assert!(
            root.is_absolute(),
            "Artifact root must be an absolute task path"
        );
        std::fs::create_dir_all(&root).unwrap();
        let directory = root.join(format!(
            "long-history-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&directory).unwrap();
        Self {
            directory,
            retain: configured.is_some(),
        }
    }
    fn database(&self) -> PathBuf {
        self.directory.join("stress.sqlite")
    }
}
impl Drop for Artifacts {
    fn drop(&mut self) {
        if !self.retain {
            // Only these literal generated files inside our newly created directory.
            for leaf in [
                "stress.sqlite",
                "stress.sqlite-wal",
                "stress.sqlite-shm",
                "metrics.json",
            ] {
                let _ = std::fs::remove_file(self.directory.join(leaf));
            }
            let _ = std::fs::remove_dir(&self.directory);
        }
    }
}

fn seed(story: &str) -> Seed {
    let actor = |name: &str| {
        json!({"name":name,"location":"orchard","alive":true,
        "energy":3,"abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]})
    };
    serde_json::from_value(json!({
        "version":1,"id":format!("seed-{story}"),"scope":{"story":story,"branch":"main"},
        "profile":"fantasy_v1","player":"player","locations":["orchard"],"routes":[],
        "actors":{"player":actor("Ada Vale"),"courier":actor("Lark Reed"),"rival":actor("Lark Reed")},
        "items":{"amber-compass":{"owner":"player","quantity":1,"return_to":null,"healing":true}},
        "abilities":{},
        "facts":{
            "public-ledger":{"proposition":"The orchard ledger is bronze. PUBLIC-LEDGER-ANCHOR","discoverable_at":null,"known_by":["player","courier"]},
            "player-vault":{"proposition":"PLAYER-SEED-VAULT-ANCHOR","discoverable_at":null,"known_by":["player"]},
            "courier-vault":{"proposition":"COURIER-SEED-VAULT-ANCHOR","discoverable_at":null,"known_by":["courier"]}
        },
        "relationships":[{"from":"courier","to":"player","respect":-2,"trust":-4,"obligation":0}],
        "story_time":100,
        "beliefs":[{"believer":"courier","proposition":"The orchard ledger is silver. BELIEF-LEDGER-ANCHOR",
            "source_claim":null,"source":{"kind":"seed","value":format!("seed-{story}")},"confidence":"believed"}],
        "commitments":{}
    })).unwrap()
}
fn say(text: &str, audience: &[&str]) -> Command {
    Command::Say {
        text: text.into(),
        audience: audience.iter().map(|s| (*s).into()).collect(),
    }
}
fn apply(store: &mut Store, engine: &mut Engine, key: &str, commands: Vec<Command>) -> Receipt {
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    let receipt = store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap();
    assert_eq!(receipt, preview);
    assert_eq!(
        engine
            .commit(&request, &proposal, preview.narration())
            .unwrap(),
        receipt
    );
    receipt
}
fn fork(store: &mut Store, engine: &Engine, branch: &str, at: u64) -> Scope {
    store
        .fork_branch(
            &ForkRequest {
                parent: engine.scope().clone(),
                child_branch: branch.into(),
                expected_parent_revision: engine.revision(),
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn request(engine: &Engine, observer: &str, text: &str) -> CompileRequest {
    CompileRequest {
        version: COMPILER_VERSION,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: observer.into(),
        role: Role::Character,
        query: text.into(),
        referenced_ids: vec![],
        budget: Budget::default(),
    }
}
fn history(engine: &Engine, observer: Observer, text: &str) -> locallore::inspection_query::Page {
    query(
        engine,
        &Query {
            version: QUERY_VERSION,
            scope: engine.scope().clone(),
            expected_head: engine.revision(),
            at_revision: None,
            observer,
            view: View::History,
            cursor: None,
            limit: MAX_ROWS,
            search: text.into(),
        },
        true,
    )
    .unwrap()
}
fn has_event(package: &ContextPackage, scope: &Scope, sequence: u64) -> bool {
    package.records.iter().any(|r| {
        matches!(&r.payload,
        Payload::Record(row) if matches!(&**row,Row::Event{event,..}
            if event.scope==*scope && event.sequence==sequence))
    })
}
fn has_origin(package: &ContextPackage, origin: ValueOrigin, marker: &str) -> bool {
    package.records.iter().any(|r| {
        matches!(&r.payload,
        Payload::Record(row) if matches!(&**row,Row::Knowledge{origin:o,text,..}
            if *o==origin && text.contains(marker)))
    })
}
fn record(cases: &mut Vec<Value>, name: &str, pass: bool, observed: Value) {
    cases.push(json!({"case":name,"pass":pass,"observed":observed}));
}
fn micros(start: Instant) -> u64 {
    u64::try_from(start.elapsed().as_micros()).unwrap()
}
fn prepare(scope: &Scope, head: u64, observer: &str, after: u64, target: Target) -> PrepareRequest {
    PrepareRequest {
        scope: scope.clone(),
        expected_revision: head,
        observer: observer.into(),
        from_exclusive: after,
        through_revision: head,
        target,
    }
}
fn publish(store: &mut Store, request: &PrepareRequest) {
    let prepared = store.prepare_memory(request, &|| false).unwrap();
    store.publish_memory(prepared, &|| false).unwrap();
}
fn search(store: &mut Store, scope: &Scope, head: u64, observer: &str, text: &str) -> Vec<Value> {
    store
        .search_memory(
            &SearchRequest {
                scope: scope.clone(),
                expected_revision: head,
                observer: observer.into(),
                text: text.into(),
                limit: 16,
            },
            &|| false,
        )
        .unwrap()
        .into_iter()
        .map(|h| h.packet.json().clone())
        .collect()
}

#[test]
fn accepted_thousand_event_retrieval_and_interference_baseline() {
    let artifacts = Artifacts::new();
    let mut store = Store::open(&artifacts.database(), None).unwrap();
    let original = seed("spindle-orchard");
    let root = original.scope.clone();
    store
        .create_story("Original synthetic spindle orchard", original.clone())
        .unwrap();
    let mut engine = Engine::new(original).unwrap();
    let generation = Instant::now();
    apply(
        &mut store,
        &mut engine,
        "opening",
        vec![
            say(
                &format!("Return the spindle sketch at dusk. {OLD}"),
                &["courier"],
            ),
            Command::Promise {
                id: "restore-orchard".into(),
                to: "courier".into(),
                terms: "Return the amber compass to the orchard ledger.".into(),
                deadline: 7000,
                return_item: None,
            },
            Command::Give {
                item: "amber-compass".into(),
                to: "courier".into(),
                quantity: 1,
            },
            say(
                "The ridge signal is violet. CLAIM-RIDGE-ANCHOR",
                &["courier"],
            ),
            Command::Believe { claim_event: 4 },
            say(PRIVATE, &["player"]),
            Command::Wait { ticks: 1 },
            say(
                "Two Lark Reed couriers heard the bell.",
                &["courier", "rival"],
            ),
        ],
    );
    for batch in 0..128 {
        let commands = (0..8)
            .map(|slot| {
                say(
                    &format!(
                        "Routine ledger slate number {} records pebbles and clouds.",
                        batch * 8 + slot
                    ),
                    &["courier"],
                )
            })
            .collect();
        apply(
            &mut store,
            &mut engine,
            &format!("distractors-{batch:03}"),
            commands,
        );
    }
    assert_eq!(engine.revision(), ROOT_HEAD);
    assert_eq!(engine.receipts().len(), 129);
    assert_eq!(
        engine
            .receipts()
            .iter()
            .map(|r| r.events().len())
            .sum::<usize>(),
        1032
    );
    let generation_us = micros(generation);
    let child = fork(&mut store, &engine, "child", ROOT_HEAD);
    let sibling = fork(&mut store, &engine, "sibling", ROOT_HEAD);
    let mut child_engine = store.resume(&child).unwrap().engine;
    apply(
        &mut store,
        &mut child_engine,
        "child-local",
        vec![
            say("CHILD-LOCAL-ANCHOR", &["courier"]),
            say(CHILD_PRIVATE, &["player"]),
        ],
    );
    assert_eq!(child_engine.revision(), CHILD_HEAD);
    let mut sibling_engine = store.resume(&sibling).unwrap().engine;
    apply(
        &mut store,
        &mut sibling_engine,
        "sibling-local",
        vec![say(FORBIDDEN[1], &["courier"])],
    );
    apply(
        &mut store,
        &mut engine,
        "parent-future",
        vec![say(FORBIDDEN[0], &["courier"])],
    );
    let foreign_seed = seed("foreign-orchard");
    let foreign = foreign_seed.scope.clone();
    store
        .create_story("Separate synthetic orchard", foreign_seed.clone())
        .unwrap();
    let mut foreign_engine = Engine::new(foreign_seed).unwrap();
    apply(
        &mut store,
        &mut foreign_engine,
        "foreign-local",
        vec![say(FORBIDDEN[2], &["courier"])],
    );
    // A descendant deliberately forks before its parent's birth. Original root
    // sources remain root-scoped; the selected lineage must apply the earlier cap.
    let prebirth = fork(&mut store, &child_engine, "prebirth", 8);
    drop(store);
    let reopen = Instant::now();
    let mut store = Store::open(&artifacts.database(), None).unwrap();
    let child_engine = store.resume(&child).unwrap().engine;
    let prebirth_engine = store.resume(&prebirth).unwrap().engine;
    let replay_us = micros(reopen);
    let before = child_engine.canonical_bytes();
    let fingerprint = format!("{:x}", Sha256::digest(&before));
    let mut cases = vec![];
    let mut exact_sources = vec![];
    let exact = Instant::now();
    child_engine
        .visit_actor_observations(
            "courier",
            &child,
            CHILD_HEAD,
            0,
            CHILD_HEAD,
            &|| false,
            &mut |e| {
                if e.sequence() == 1 {
                    exact_sources.push((e.scope().clone(), e.sequence()));
                }
                true
            },
        )
        .unwrap();
    record(
        &mut cases,
        "exact-old-observation-original-scope",
        exact_sources == vec![(root.clone(), 1)],
        json!({"source_count":exact_sources.len(),"elapsed_us":micros(exact)}),
    );
    let lexical = Instant::now();
    let page = history(
        &child_engine,
        Observer::Character {
            id: "courier".into(),
        },
        OLD,
    );
    record(
        &mut cases,
        "literal-old-history-amid-1024-distractors",
        page.rows
            .iter()
            .any(|r| matches!(r,Row::Event{event,..} if event.sequence==1 && event.scope==root)),
        json!({"matching_rows":page.total,"elapsed_us":micros(lexical)}),
    );
    let compiler = Instant::now();
    let base = compile(&child_engine, &request(&child_engine, "courier", OLD));
    let compiler_us = micros(compiler);
    record(
        &mut cases,
        "compiler-old-lexical-event",
        base.as_ref().is_ok_and(|p| has_event(p, &root, 1)),
        json!({"error":base.as_ref().err().map(|e|format!("{e:?}")),"elapsed_us":compiler_us}),
    );
    if let Ok(package) = &base {
        let text = serde_json::to_string(package).unwrap();
        record(
            &mut cases,
            "current-truth-and-belief-remain-distinct",
            has_origin(package, ValueOrigin::CanonicalTruth, "PUBLIC-LEDGER-ANCHOR")
                && has_origin(
                    package,
                    ValueOrigin::SubjectiveBelief,
                    "BELIEF-LEDGER-ANCHOR",
                ),
            json!({"selected":package.records.len()}),
        );
        record(&mut cases,"old-open-promise-and-supporting-event",
            package.records.iter().any(|r| matches!(&r.payload,Payload::Record(row) if
                matches!(&**row,Row::Promise{id,status,sources,..} if id=="restore-orchard" && status=="open" && sources.contains(&Source::Event(2))))) && has_event(package,&root,2),
            json!({"expected_source_event":2,"selected_original_event":has_event(package,&root,2)}));
        let relationship=package.records.iter().any(|r| matches!(&r.payload,Payload::Record(row) if
            matches!(&**row,Row::Relationship{from,to,dimension,value,source,..} if from=="courier" && to=="player" &&
                dimension=="obligation" && *value==1 && *source==Source::Event(3))));
        let inventory=package.records.iter().any(|r|matches!(&r.payload,Payload::Record(row) if
            matches!(&**row,Row::Field{actor,field,value:FieldValue::Item(item),source,..} if actor=="courier" &&
                field=="item/amber-compass" && item.owner=="courier" && item.quantity==1 && *source==Source::Event(3))));
        record(
            &mut cases,
            "current-inventory-and-directed-relationship",
            inventory
                && relationship
                && child_engine.state().items["amber-compass"].owner == "courier"
                && child_engine.state().relationships[0].trust == -4
                && child_engine.state().relationships[0].obligation == 1,
            json!({"owner":child_engine.state().items["amber-compass"].owner,"trust":child_engine.state().relationships[0].trust,
                "obligation":child_engine.state().relationships[0].obligation,"selected_inventory":inventory,"selected_relationship":relationship}),
        );
        let prohibited = [
            PRIVATE,
            CHILD_PRIVATE,
            "PLAYER-SEED-VAULT-ANCHOR",
            "player-vault",
            "event:00000000000000000006",
            FORBIDDEN[0],
            FORBIDDEN[1],
            FORBIDDEN[2],
        ];
        let leaks: Vec<_> = prohibited
            .iter()
            .filter(|m| text.contains(**m))
            .copied()
            .collect();
        record(
            &mut cases,
            "actor-secret-and-cross-scope-serialization-fences",
            leaks.is_empty() && text.contains("COURIER-SEED-VAULT-ANCHOR"),
            json!({"forbidden_markers":prohibited.len(),"leaked_markers":leaks}),
        );
        record(
            &mut cases,
            "complete-package-budget-accounting",
            package.serialized_bytes == text.len()
                && text.len() <= 24576
                && package.estimated_tokens + package.reserved_tokens <= 4096
                && package.token_accounting == "estimate_utf8_bytes_div_4_not_measured",
            json!({"bytes":text.len(),"estimated_tokens":package.estimated_tokens,"reserved":package.reserved_tokens,
                "eligible_candidates":package.diagnostics.eligible_candidates,"selected":package.records.len(),
                "omitted":package.diagnostics.omitted_eligible}),
        );
    } else {
        for name in [
            "current-truth-and-belief-remain-distinct",
            "old-open-promise-and-supporting-event",
            "current-inventory-and-directed-relationship",
            "actor-secret-and-cross-scope-serialization-fences",
            "complete-package-budget-accounting",
        ] {
            record(
                &mut cases,
                name,
                false,
                json!({"not_run":"compiler prerequisite failed"}),
            );
        }
    }
    let mut excluded_queries = vec![];
    for marker in FORBIDDEN {
        let result = compile(&child_engine, &request(&child_engine, "courier", marker));
        excluded_queries.push(
            result
                .as_ref()
                .is_ok_and(|p| !serde_json::to_string(p).unwrap().contains(marker)),
        );
    }
    record(
        &mut cases,
        "compiler-targeted-forbidden-queries-stay-excluded",
        excluded_queries == vec![true, true, true],
        json!({"excluded":excluded_queries}),
    );
    let mut wrong_scope = request(&child_engine, "courier", OLD);
    wrong_scope.scope = foreign.clone();
    record(
        &mut cases,
        "compiler-foreign-request-scope-refuses",
        matches!(
            compile(&child_engine, &wrong_scope),
            Err(CompileError::Scope)
        ),
        json!({}),
    );
    let mut director_request = request(&child_engine, "player", PRIVATE);
    director_request.role = Role::Director;
    let director = compile(&child_engine, &director_request);
    record(
        &mut cases,
        "director-player-secret-is-legitimate-courier-secret-is-not",
        director.as_ref().is_ok_and(|p| {
            let text = serde_json::to_string(p).unwrap();
            has_event(p, &root, 6)
                && has_event(p, &child, CHILD_HEAD)
                && text.contains("PLAYER-SEED-VAULT-ANCHOR")
                && !text.contains("COURIER-SEED-VAULT-ANCHOR")
                && FORBIDDEN.iter().all(|m| !text.contains(m))
        }),
        json!({"error":director.as_ref().err().map(|e|format!("{e:?}")),
            "selected":director.as_ref().ok().map(|p|p.records.len()),
            "bytes":director.as_ref().ok().map(|p|p.serialized_bytes)}),
    );
    director_request.observer = "courier".into();
    record(
        &mut cases,
        "director-cannot-assume-another-actor-observer",
        matches!(
            compile(&child_engine, &director_request),
            Err(CompileError::Observer)
        ),
        json!({}),
    );
    let mut alias = request(&child_engine, "courier", "Lark Reed spindle");
    record(
        &mut cases,
        "ambiguous-display-alias-refuses",
        matches!(
            compile(&child_engine, &alias),
            Err(CompileError::AmbiguousAlias)
        ),
        json!({}),
    );
    alias.referenced_ids = vec!["courier".into()];
    let disambiguated = compile(&child_engine, &alias);
    record(
        &mut cases,
        "explicit-id-resolves-alias-and-old-event",
        disambiguated.as_ref().is_ok_and(|p| {
            p.records
                .iter()
                .any(|r| matches!(&r.payload,Payload::Alias{actor,..} if actor=="courier"))
                && has_event(p, &root, 1)
        }),
        json!({"error":disambiguated.err().map(|e|format!("{e:?}"))}),
    );
    let mut old = request(&child_engine, "courier", OLD);
    old.at_revision = Some(8);
    let historical = compile(&child_engine, &old);
    record(
        &mut cases,
        "historical-completed-boundary-excludes-child-and-later-data",
        historical.as_ref().is_ok_and(|p| {
            let s = serde_json::to_string(p).unwrap();
            p.revision == 8
                && has_event(p, &root, 1)
                && !s.contains("CHILD-LOCAL-ANCHOR")
                && FORBIDDEN.iter().all(|m| !s.contains(m))
        }),
        json!({"error":historical.err().map(|e|format!("{e:?}"))}),
    );
    let prebirth_result = compile(&prebirth_engine, &request(&prebirth_engine, "courier", OLD));
    record(
        &mut cases,
        "prebirth-descendant-preserves-ancestor-scope-and-cap",
        prebirth_result.as_ref().is_ok_and(|p| {
            let s = serde_json::to_string(p).unwrap();
            p.revision == 8
                && has_event(p, &root, 1)
                && !s.contains("CHILD-LOCAL-ANCHOR")
                && FORBIDDEN.iter().all(|m| !s.contains(m))
        }),
        json!({"head":prebirth_engine.revision(),"error":prebirth_result.err().map(|e|format!("{e:?}"))}),
    );
    old.at_revision = Some(1031);
    record(
        &mut cases,
        "mid-turn-revision-refuses",
        matches!(compile(&child_engine, &old), Err(CompileError::Boundary)),
        json!({"requested":1031}),
    );
    let mut stale = request(&child_engine, "courier", OLD);
    stale.expected_head -= 1;
    record(
        &mut cases,
        "stale-head-refuses",
        matches!(compile(&child_engine, &stale), Err(CompileError::Stale)),
        json!({}),
    );
    let mut tiny = request(&child_engine, "courier", OLD);
    tiny.budget = Budget {
        max_bytes: 1024,
        estimated_tokens: 64,
        reserved_tokens: 1,
        ..Budget::default()
    };
    record(
        &mut cases,
        "mandatory-context-cannot-fit-refuses",
        matches!(
            compile(&child_engine, &tiny),
            Err(CompileError::MandatoryBudget)
        ),
        json!({"bytes":1024,"estimated_tokens":64}),
    );
    record(
        &mut cases,
        "cancelled-compile-refuses",
        matches!(
            compile_cancelled(
                &child_engine,
                &request(&child_engine, "courier", OLD),
                &|| true
            ),
            Err(CompileError::Cancelled)
        ),
        json!({}),
    );
    let omni = history(&child_engine, Observer::Omniscient, PRIVATE);
    let after_inspection = compile(&child_engine, &request(&child_engine, "courier", PRIVATE));
    record(
        &mut cases,
        "omniscient-inspection-never-grants-character-knowledge",
        omni.total > 0
            && after_inspection
                .as_ref()
                .is_ok_and(|p| !serde_json::to_string(p).unwrap().contains(PRIVATE)),
        json!({"omniscient_rows":omni.total,"compile_error":after_inspection.err().map(|e|format!("{e:?}"))}),
    );
    // Whole unchunked scene is deliberately too large for the accepted v1 cache.
    // Structured entity and short-tail packets below exercise its actual verified
    // FTS API, not an invented long-history cache consumer.
    let full = prepare(&child, CHILD_HEAD, "courier", 0, Target::SceneWindow);
    record(
        &mut cases,
        "unchunked-v1-cache-refuses-over-256-events",
        matches!(
            store.prepare_memory(&full, &|| false),
            Err(MemoryError::TooLarge)
        ),
        json!({"cap":256}),
    );
    let promise = prepare(
        &child,
        CHILD_HEAD,
        "courier",
        0,
        Target::Entity {
            kind: EntityKind::Commitment,
            id: "restore-orchard".into(),
        },
    );
    publish(&mut store, &promise);
    for (scope, head, observer, after) in [
        (&child, CHILD_HEAD, "courier", ROOT_HEAD),
        (&child, CHILD_HEAD, "player", ROOT_HEAD),
        (&root, 1033, "courier", ROOT_HEAD),
        (&sibling, 1033, "courier", ROOT_HEAD),
        (&foreign, 1, "courier", 0),
    ] {
        publish(
            &mut store,
            &prepare(scope, head, observer, after, Target::SceneWindow),
        );
    }
    let fts = Instant::now();
    let hits = search(&mut store, &child, CHILD_HEAD, "courier", "amber compass");
    record(
        &mut cases,
        "verified-v1-FTS-old-structured-promise",
        hits.len() == 1 && hits[0]["source_events"] == json!([2]),
        json!({"hits":hits.len(),"elapsed_us":micros(fts),"source_events":hits.iter().map(|h|h["source_events"].clone()).collect::<Vec<_>>()}),
    );
    let private_player = search(&mut store, &child, CHILD_HEAD, "player", CHILD_PRIVATE);
    let private_actor = search(&mut store, &child, CHILD_HEAD, "courier", CHILD_PRIVATE);
    record(
        &mut cases,
        "FTS-actor-partition-before-search",
        private_player.len() == 1 && private_actor.is_empty(),
        json!({"player_hits":private_player.len(),"courier_hits":private_actor.len()}),
    );
    let mut forbidden_hits = vec![];
    for marker in FORBIDDEN {
        forbidden_hits.push(search(&mut store, &child, CHILD_HEAD, "courier", marker).len());
    }
    record(
        &mut cases,
        "FTS-wrong-story-sibling-parent-future-excluded",
        forbidden_hits == vec![0, 0, 0],
        json!({"hits":forbidden_hits}),
    );
    let canonical_after = store.resume(&child).unwrap().engine.canonical_bytes();
    record(
        &mut cases,
        "compiler-inspection-and-derived-cache-never-mutate-canon",
        canonical_after == before,
        json!({"canonical_sha256":fingerprint}),
    );
    let mut unique_events = BTreeSet::new();
    let mut unique_receipts = BTreeSet::new();
    for e in [
        &engine,
        &child_engine,
        &sibling_engine,
        &foreign_engine,
        &prebirth_engine,
    ] {
        for receipt in e.receipts() {
            unique_receipts.insert((
                receipt.request().scope.clone(),
                receipt.request().turn.clone(),
            ));
            unique_events.extend(
                receipt
                    .events()
                    .iter()
                    .map(|v| (v.scope().clone(), v.sequence())),
            );
        }
    }
    assert_eq!(unique_events.len(), 1037);
    assert_eq!(unique_receipts.len(), 133);
    let failures: Vec<_> = cases
        .iter()
        .filter(|c| c["pass"] != true)
        .map(|c| c["case"].clone())
        .collect();
    let info = store.info().unwrap();
    let generator = format!(
        "{:x}",
        Sha256::digest(include_bytes!("long_history_stress.rs"))
    );
    let metrics = json!({"synthetic":true,"provider_calls":0,"production_memory_consumer":false,
        "generator_sha256":generator,"development_fixtures_feature":cfg!(feature="development-fixtures"),
        "sqlite_version":info.sqlite_version,"schema_version":info.schema_version,
        "source_base":"a13b80b8f7e37c1fb2aad714f5ba931f7bf37941","root_events_at_fork":ROOT_HEAD,"root_receipts_at_fork":129,
        "root_final_head":engine.revision(),"accepted_unique_events_all_scopes":unique_events.len(),"accepted_unique_receipts_all_scopes":unique_receipts.len(),
        "child_head":CHILD_HEAD,"child_receipts_including_inherited":child_engine.receipts().len(),
        "generated_us":generation_us,"reopen_and_two_strict_replays_us":replay_us,"cases":cases,"failures":failures,
        "timing_policy":"single observations; no wallclock pass threshold; debug0 test build; no model-use or quality measurement"});
    std::fs::write(
        artifacts.directory.join("metrics.json"),
        serde_json::to_vec_pretty(&metrics).unwrap(),
    )
    .unwrap();
    println!("LONG_HISTORY_METRICS {}", metrics);
    assert!(
        failures.is_empty(),
        "Fixed long-history cases failed: {failures:?}"
    );
}
