// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Genuine synthetic Archive3 fixture: binary stdout, bounded metadata stderr.
//! Explicit fresh D scratch only; no model/provider/app-author API or cleanup.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    inspection::sha256,
    inspection_query::{self, Observer, Query, Row, Source, ValueOrigin, View},
    play::PlayProfile,
    story_authoring::{
        self, InitialGenerationV1, InitialModelConfigurationV1, InitialProviderKindV1,
        InitialStoryInputV1, InitialWorldOriginV1, InitialWorldProposalV1,
    },
};
use locallore_storage::{validate_archive, ForkRequest, Store};
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    fs,
    io::{self, Write},
    path::{Component, Path, PathBuf, Prefix},
};

const STORY: &str = "query2-ui-opaque-v1";
const OLD: &str = "The survey beacon flashes amber at the north pier.";
const NEW: &str = "The survey beacon flashes violet at the north pier.";
const NPC_NAME: &str = "PRIVATE_RECORD_UI_NPC_NAME";
const NPC_SHEET: &str = "PRIVATE_RECORD_UI_NPC_SHEET";
const NPC_BELIEF: &str = "PRIVATE_RECORD_UI_NPC_BELIEF";
const HIDDEN_FACT: &str = "PRIVATE_RECORD_UI_HIDDEN_FACT";
const AUTHOR_REASON: &str = "PRIVATE_RECORD_UI_AUTHOR_REASON";

fn physical_d(path: &Path) -> bool {
    matches!(path.components().next(), Some(Component::Prefix(prefix))
        if matches!(prefix.kind(), Prefix::Disk(b'D' | b'd') | Prefix::VerbatimDisk(b'D' | b'd')))
}

fn create_scratch(path: &Path) -> io::Result<()> {
    assert!(path.is_absolute() && physical_d(path));
    assert!(!path.components().any(|component| matches!(component, Component::ParentDir | Component::CurDir)));
    assert!(!path.try_exists()?, "scratch must be create-only");
    let parent = path.parent().expect("scratch parent");
    for ancestor in parent.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        assert!(metadata.is_dir() && !metadata.file_type().is_symlink());
        #[cfg(windows)] {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0, "scratch ancestors must be ordinary");
        }
    }
    assert!(physical_d(&parent.canonicalize()?), "scratch parent must resolve physically to D");
    fs::create_dir(path)?;
    Ok(())
}

fn seed() -> Seed {
    let input: InitialStoryInputV1 = serde_json::from_value(json!({
        "version":1,"premise":"A small pier survey needs a reliable beacon record.",
        "player_name":"Iona","player_description":"A patient surveyor.",
        "cast":[{"name":"Nia","description":"A bell keeper."},
            {"name":NPC_NAME,"description":"A distant keeper."}],
        "profile":"narrative_v1","presentation":{"version":1,"tone":"plain","excluded_phrases":[]}
    })).expect("typed synthetic author input");
    let accepted: InitialWorldProposalV1 = serde_json::from_value(json!({
        "version":1,"locations":[
            {"name":"North Pier","description":"A stone pier supports a survey bell."},
            {"name":"Upper Store","description":"A closed room stands above the quay."}],
        "player_location":0,
        "characters":[{"name":"Nia","description":NPC_SHEET,"location":0,"known_by":[1]},
            {"name":NPC_NAME,"description":NPC_SHEET,"location":1,"known_by":[2]}],
        "routes":[{"from":0,"to":1},{"from":1,"to":0}],
        "facts":[{"text":OLD,"known_by":[],"discoverable_at":0},
            {"text":HIDDEN_FACT,"known_by":[2],"discoverable_at":1}],
        "beliefs":[{"believer":2,"text":NPC_BELIEF,"confidence":"believed"}],
        "possessions":[]
    })).expect("typed synthetic world proposal");
    story_authoring::validate_proposal(&input, &accepted).expect("valid original authored world");
    let profile = PlayProfile {
        id: "record-ui-archive-synthetic-v1".into(), model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40), template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64), profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096, director_tokens: 350, narrator_tokens: 350,
        deadline_ms: 5000, repair_limit: 1,
    };
    let response = serde_json::to_string(&accepted).expect("synthetic origin encoding");
    let origin = InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(), proposal: accepted.clone(), model_profile: profile.id.clone(),
            model_configuration: InitialModelConfigurationV1::from(&profile),
            provider: InitialProviderKindV1::Scripted,
            prompt_version: story_authoring::PROMPT_VERSION.into(),
            schema_version: story_authoring::SCHEMA_VERSION.into(),
            response_sha256: sha256(response.as_bytes()), response,
        },
        reviewed: input, accepted: accepted.clone(), title: "Record UI corrected opaque fixture".into(),
    };
    let seed = story_authoring::materialize(&origin,
        Scope { story: STORY.into(), branch: "main".into() }).expect("actual authored materialization");
    story_authoring::validate_origin(&seed).expect("exact authored seed origin");
    assert!(seed.player.starts_with("a-") && seed.player != "player");
    seed
}

fn apply(store: &mut Store, scope: &Scope, turn: &str, intent: Intent) -> Receipt {
    let engine = store.resume(scope).expect("actual Store source").engine;
    let request = engine.request(turn, intent);
    let proposal = Engine::proposal(&request).expect("existing mechanical proposal");
    let receipt = engine.preview(&request, &proposal).expect("valid mechanical action");
    store.begin_turn(&request).expect("actual durable turn begin");
    store.commit_prepared(&receipt).expect("actual durable commit")
}

fn branch_metadata(engine: &Engine) -> Value {
    json!({"branch":engine.scope().branch,"head":engine.revision(),"story_time":engine.state().story_time})
}

fn inspect(engine: &Engine, fact: &str, expected: &str, drill_scope: &Scope, drill_sequence: u64) {
    let before = engine.canonical_bytes();
    let records = engine.canonical_records().to_vec();
    let basis = engine.accepted_history_basis().expect("accepted history basis");
    let mut known = false;
    let mut witnessed_drill = false;
    let mut inherited_discovery = false;
    let mut marker = false;
    for view in [View::Profiles, View::Relationships, View::Knowledge, View::History, View::Promises] {
        let mut request = Query {
            version: 2, scope: engine.scope().clone(), expected_head: engine.revision(),
            at_revision: None, observer: Observer::Player, view, cursor: None, limit: 8, search: String::new(),
        };
        let mut seen = BTreeSet::new();
        let mut complete = false;
        for _ in 0..16 {
            let page = inspection_query::query(engine, &request, false).expect("actual current Player Query2");
            let encoded = serde_json::to_string(&page).expect("native page encoding");
            for private in [NPC_NAME, NPC_SHEET, NPC_BELIEF, HIDDEN_FACT, AUTHOR_REASON] {
                assert!(!encoded.contains(private), "private synthetic value reached Player inspection");
            }
            if expected == OLD { assert!(!encoded.contains(NEW), "unseen correction reached Player inspection"); }
            for row in &page.rows {
                match row {
                    Row::Knowledge { id, subject, text, sources, origin: ValueOrigin::KnownAsObserved, .. } if id == fact => {
                        assert_eq!(subject.as_deref(), Some(engine.seed().player.as_str()));
                        assert_eq!(text, expected);
                        let (observed_scope, observed_sequence) = if expected == OLD {
                            (drill_scope, drill_sequence)
                        } else {
                            (engine.scope(), engine.revision())
                        };
                        assert!(matches!(sources.as_slice(), [Source::ScopedEvent { original_scope, sequence }]
                            if original_scope == observed_scope && *sequence == observed_sequence));
                        known = true;
                    }
                    Row::Knowledge { id, text, sources, origin: ValueOrigin::RecordedDiscovery, .. } if id == fact && text == OLD => {
                        assert!(matches!(sources.as_slice(), [Source::ScopedEvent { original_scope, sequence }]
                            if original_scope == drill_scope && *sequence == drill_sequence));
                        inherited_discovery = true;
                    }
                    Row::Event { event, .. } if event.scope == *drill_scope && event.sequence == drill_sequence => {
                        assert!(event.witnesses.contains(&engine.seed().player));
                        assert!(matches!(&event.consequence, Effect::Discovered { actor, fact: actual }
                            if actor == &engine.seed().player && actual == fact));
                        witnessed_drill = true;
                    }
                    Row::AuthorCorrection { .. } => marker = true,
                    _ => {}
                }
            }
            if let Some(cursor) = page.next_cursor {
                assert!(seen.insert(cursor.clone()), "native cursors must advance");
                request.cursor = Some(cursor);
            } else { complete = true; break; }
        }
        assert!(complete, "finite fixture inspection budget exhausted");
    }
    assert!(known && witnessed_drill && inherited_discovery);
    assert_eq!(marker, engine.domain_version() == 2);
    assert!(engine.canonical_bytes() == before && engine.canonical_records() == records.as_slice());
    assert!(engine.accepted_history_basis().expect("history remains valid") == basis);
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let arguments: Vec<_> = std::env::args_os().collect();
    assert_eq!(arguments.len(), 2, "one explicit fresh D scratch directory required");
    let scratch = PathBuf::from(&arguments[1]);
    create_scratch(&scratch)?;
    let source_path = scratch.join("source.sqlite3");
    let target_path = scratch.join("roundtrip.sqlite3");
    let seed = seed();
    let root_scope = seed.scope.clone();
    let player = seed.player.clone();
    let prefix = seed.id.strip_prefix("world-").expect("materialized namespace");
    let fact = format!("f-{prefix}-world-0");
    let mentor = format!("a-{prefix}-1");
    let mut source = Store::open_application(&source_path).expect("create-only synthetic source Store");
    source.create_story("Record UI corrected opaque fixture", seed).expect("actual authored story");
    let observed = apply(&mut source, &root_scope, "observe-before",
        Intent::Actions(vec![Command::Discover { fact: fact.clone() }]));
    let sequence = observed.events()[0].sequence();
    assert_eq!(sequence, 1);
    apply(&mut source, &root_scope, "stated-survey", Intent::Dialogue {
        text: "The survey record needs another look.".into(), audience: [mentor.clone()].into(),
    });
    apply(&mut source, &root_scope, "return-survey", Intent::Actions(vec![Command::Promise {
        id: "survey-notes".into(), to: mentor, terms: "Bring the survey notes before the bell.".into(),
        deadline: 10, return_item: None,
    }]));
    apply(&mut source, &root_scope, "wait-before", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let before = source.resume(&root_scope).expect("durable root replay").engine;
    assert_eq!(before.domain_version(), 1);
    assert_eq!(before.revision(), 4);
    drop(source);

    // The existing native Host author port owns this fixture preparation only.
    // Normal Android/JNI construction gets no StoryLab operation or capability.
    let host = locallore_workspace::open(&source_path, true).expect("actual Host/Store owner");
    assert!(host.story_lab_granted());
    let resumed = host.call(&serde_json::to_vec(&json!({"version":1,
        "command":{"op":"resume","scope":root_scope}}))?);
    assert_eq!(resumed["status"], "ok");
    let session = resumed["data"]["session"].as_str().expect("actual native session");
    let input = AuthorCorrectionInputV1 {
        version: 1, parent: root_scope.clone(), expected_parent_revision: before.revision(),
        fork_revision: before.revision(), child_branch: "corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: fact.clone(), expected_proposition: OLD.into(), replacement: NEW.into(),
        }, reason: AUTHOR_REASON.into(),
    };
    let prepared = host.prepare_author_correction(session, &input, &|| false).expect("native author preparation");
    let correction = host.apply_author_correction(&prepared, &|| false).expect("native atomic author correction");
    assert!(correction.created);
    assert_eq!(correction.author_revision, 5);
    host.close_all();
    drop(prepared);
    drop(host);

    let mut source = Store::open_application(&source_path).expect("reopen actual corrected Store");
    let corrected = source.resume(&correction.scope).expect("durable corrected history").engine;
    assert_eq!(corrected.domain_version(), 2);
    assert_eq!(corrected.revision(), 5);
    assert_eq!(corrected.effective_fact(&fact)?.proposition, NEW);
    let fork = source.fork_branch(&ForkRequest {
        parent: corrected.scope().clone(), child_branch: "rediscovered".into(),
        expected_parent_revision: corrected.revision(), at_revision: corrected.revision(),
    }, &|| false).expect("actual corrected-history fork");
    apply(&mut source, &fork.scope, "observe-after", Intent::Actions(vec![Command::Discover { fact: fact.clone() }]));
    let rediscovered = source.resume(&fork.scope).expect("durable rediscovered history").engine;
    assert_eq!(rediscovered.domain_version(), 2);
    assert_eq!(rediscovered.revision(), 6);
    for (engine, expected) in [(&before, OLD), (&corrected, OLD), (&rediscovered, NEW)] {
        inspect(engine, &fact, expected, &root_scope, sequence);
        assert_eq!(engine.state().story_time, 1);
    }
    let archive = source.export_archive(STORY, &|| false).expect("production Archive3 export");
    assert_eq!(archive.preview().version, 3);
    assert_eq!(archive.preview().branch_heads.len(), 3);
    assert!(archive.bytes().len() <= 256 * 1024);
    let validated = validate_archive(archive.bytes(), &|| false).expect("production archive validation");
    let mut target = Store::open_application(&target_path).expect("fresh roundtrip Store");
    let imported = target.import_archive(validated, &|| false).expect("production archive import");
    assert_eq!(imported.root, root_scope);
    assert_eq!(imported.branches, 3);
    for (engine, expected) in [(&before, OLD), (&corrected, OLD), (&rediscovered, NEW)] {
        let actual = target.resume(engine.scope()).expect("actual imported scope").engine;
        assert!(actual.seed() == engine.seed() && actual.canonical_records() == engine.canonical_records());
        assert!(actual.canonical_bytes() == engine.canonical_bytes());
        assert!(actual.accepted_history_basis()? == engine.accepted_history_basis()?);
        inspect(&actual, &fact, expected, &root_scope, sequence);
    }
    let replay = target.export_archive(STORY, &|| false).expect("production re-export");
    assert!(replay.bytes() == archive.bytes(), "canonical archive bytes must roundtrip unchanged");
    let metadata = json!({"version":1,"archive":{"bytes":archive.bytes().len(),"sha256":sha256(archive.bytes())},
        "story":STORY,"root_branch":root_scope.branch,"player":player,"fact_id":fact,
        "old_observation":OLD,"new_observation":NEW,
        "forbidden":[NPC_NAME,NPC_SHEET,NPC_BELIEF,HIDDEN_FACT,AUTHOR_REASON],
        "correction_revision":correction.author_revision,
        "branches":{"before":branch_metadata(&before),"corrected":branch_metadata(&corrected),
            "rediscovered":branch_metadata(&rediscovered)},
        "drill":{"original_scope":root_scope,"sequence":sequence}});
    let metadata = serde_json::to_vec(&metadata)?;
    assert!(metadata.len() + 1 <= 32 * 1024);
    drop(target);
    drop(source);
    let mut stdout = io::stdout().lock();
    stdout.write_all(archive.bytes())?;
    stdout.flush()?;
    let mut stderr = io::stderr().lock();
    stderr.write_all(&metadata)?;
    stderr.write_all(b"\n")?;
    stderr.flush()?;
    Ok(())
}
