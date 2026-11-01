//! Genuine synthetic SQLite/ordinary-Host presentation corpus. One fresh D:
//! scratch argument; bounded JSON stdout, no model, network, or app-author API.
use locallore::{
    contracts::*,
    engine::Engine,
    host::Host,
    inference::{Cancellation, GenerationRequest, InferenceProvider},
    inspection::sha256,
    play::{self, PlayProfile},
};
use locallore_storage::{validate_archive, Store};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, VecDeque},
    fs,
    io::{self, Write},
    path::{Component, Path, PathBuf, Prefix},
    task::Poll,
};

const ARCHIVE: &[u8] = include_bytes!(
    "../../../apps/android/app/src/androidTest/assets/query2-corrected-opaque-v1.llore"
);
const METADATA: &str = include_str!(
    "../../../apps/android/app/src/androidTest/assets/query2-corrected-opaque-v1.json"
);
const PRIVATE: &str = "PRIVATE_PRESENTATION_MIXED_NPC_BELIEF";

fn scratch(path: &Path) -> io::Result<()> {
    assert!(path.is_absolute());
    let mut components = path.components();
    assert!(
        matches!(components.next(), Some(Component::Prefix(p)) if matches!(p.kind(), Prefix::Disk(b'D') | Prefix::Disk(b'd')))
    );
    assert!(matches!(components.next(), Some(Component::RootDir)));
    assert!(components.all(|component| matches!(component, Component::Normal(_))));
    assert!(fs::symlink_metadata(path).is_err_and(|error| error.kind() == io::ErrorKind::NotFound));
    for ancestor in path.parent().unwrap().ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        assert!(metadata.is_dir() && !metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
    }
    fs::create_dir(path)
}

fn seed(story: &str) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    seed.beliefs[0].proposition = PRIVATE.into();
    seed
}

fn append(store: &mut Store, scope: &Scope, turn: &str, intent: Intent) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, intent);
    let receipt = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap()
}

struct Script(VecDeque<Vec<u8>>);
impl InferenceProvider for Script {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        Poll::Ready(self.0.pop_front().ok_or(Error::Provider))
    }
}

fn mixed(store: &mut Store) -> Scope {
    let seed = seed("presentation-mixed");
    let scope = seed.scope.clone();
    store
        .create_story("Presentation accepted mixed inputs", seed)
        .unwrap();
    for i in 0..21 {
        append(
            store,
            &scope,
            &format!("window-wait-{i}"),
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
    }
    append(
        store,
        &scope,
        "original-actions",
        Intent::Actions(vec![Command::Wait { ticks: 2 }]),
    );
    append(
        store,
        &scope,
        "original-dialogue",
        Intent::Dialogue {
            text: "I will check the quay survey myself.".into(),
            audience: ["mira".into()].into(),
        },
    );
    let mut engine = store.resume(&scope).unwrap().engine;
    let request = engine.request(
        "original-free-text",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let sequence = engine.revision() + 1;
    let mut provider = Script([
        json!({"commands":[{"op":"wait","ticks":1}]}),
        json!({"text":"You pause as a tide tick passes.","event_ids":[sequence],"speaker":"narrator"}),
    ].into_iter().map(|value| serde_json::to_vec(&value).unwrap()).collect());
    let profile = PlayProfile {
        id: "presentation-corpus-script".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 5000,
        repair_limit: 1,
    };
    let receipt = play::execute(
        &mut engine,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile,
    )
    .unwrap();
    assert_eq!(receipt.request(), &request);
    store.begin_turn(&request).unwrap();
    let accepted = store.commit_prepared(&receipt).unwrap();
    assert_eq!(accepted, receipt);
    assert_eq!(
        store.resume(&scope).unwrap().engine.canonical_bytes(),
        engine.canonical_bytes()
    );
    scope
}

fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn good(reply: &Value) {
    assert_eq!(reply["status"], "ok", "{reply}");
}

// These expectations come from accepted native records, independently of the
// new presentation operation. This fixture has only genuine player receipts.
fn expected(engine: &Engine) -> (Value, Value) {
    let receipts = engine.receipts();
    let start = receipts.len().saturating_sub(20);
    let mut turns = Vec::new();
    let mut messages = Vec::new();
    for (offset, receipt) in receipts[start..].iter().enumerate() {
        assert!(!receipt.events().is_empty());
        assert!(receipt
            .events()
            .iter()
            .all(|event| event.witnesses().contains(&engine.seed().player)));
        let request = receipt.request();
        let text = match &request.intent {
            Intent::Actions(commands) => serde_json::to_string(commands).unwrap(),
            Intent::Dialogue { text, .. } | Intent::FreeText { text, .. } => text.clone(),
            _ => panic!("fixture must contain accepted player intent"),
        };
        let id = (start + offset) * 2 + 1;
        messages.push(json!({"id":id,"text":text,"player":true}));
        messages.push(json!({"id":id+1,"text":receipt.narration(),"player":false}));
        // Independent expectation over the original canonical numeric JSON,
        // rather than invoking or copying the new native projection helper.
        let mut expected_intent = json!(request.intent);
        if let Some(actions) = expected_intent["value"].as_array_mut() {
            for action in actions {
                let field = match action["op"].as_str() {
                    Some("promise") => "deadline",
                    Some("believe") => "claim_event",
                    _ => continue,
                };
                let original_number = action[field].as_u64().unwrap();
                action[field] = json!(original_number.to_string());
            }
        }
        turns.push(json!({"original_scope":request.scope,"turn":request.turn,
            "event_ids":receipt.events().iter().map(AcceptedEvent::sequence).collect::<Vec<_>>(),
            "intent":expected_intent,"narration":receipt.narration()}));
    }
    (json!(turns), json!(messages))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = std::env::args_os().collect::<Vec<_>>();
    assert_eq!(arguments.len(), 2, "one explicit fresh D scratch directory");
    let directory = PathBuf::from(&arguments[1]);
    scratch(&directory)?;
    assert_eq!(ARCHIVE.len(), 14_497);
    assert_eq!(
        sha256(ARCHIVE),
        "904c725e6bae3e87b9bb42d2f91b956b6044af747fc27ea2695dd3f5c078e94c"
    );
    let metadata: Value = serde_json::from_str(METADATA)?;
    let database = directory.join("presentation.sqlite3");
    let mut store = Store::open_application(&database)?;
    let validated = validate_archive(ARCHIVE, &|| false).expect("genuine Archive3");
    let imported = store
        .import_archive(validated, &|| false)
        .expect("actual import");
    assert_eq!(imported.branches, 3);
    let empty_seed = seed("presentation-empty");
    let empty_scope = empty_seed.scope.clone();
    store.create_story("Presentation empty control", empty_seed)?;
    let mixed_scope = mixed(&mut store);
    let slash_seed = seed("presentation-slashes");
    let slash_scope = slash_seed.scope.clone();
    store.create_story("Presentation slash escaping control", slash_seed)?;
    for i in 0..20 {
        append(
            &mut store,
            &slash_scope,
            &format!("slashes-{i}"),
            Intent::Actions(vec![Command::Say {
                text: "/".repeat(1800),
                audience: ["mira".into()].into(),
            }]),
        );
    }
    let u64_seed = seed("presentation-u64");
    let u64_scope = u64_seed.scope.clone();
    store.create_story("Presentation exact unsigned action values", u64_seed)?;
    let promise = append(
        &mut store,
        &u64_scope,
        "maximum-deadline",
        Intent::Actions(vec![Command::Promise {
            id: "survey-later".into(),
            to: "mira".into(),
            terms: "Compare the survey notes after the next tide.".into(),
            deadline: u64::MAX,
            return_item: None,
        }]),
    );
    assert_eq!(
        json!(promise.request().intent)["value"][0]["deadline"].as_u64(),
        Some(u64::MAX)
    );
    let stated = append(
        &mut store,
        &u64_scope,
        "statement-to-consider",
        Intent::Dialogue {
            text: "I heard the harbor bell.".into(),
            audience: ["mira".into()].into(),
        },
    );
    let claim_event = stated.events()[0].sequence();
    assert!(claim_event > 0);
    append(
        &mut store,
        &u64_scope,
        "consider-statement",
        Intent::Actions(vec![Command::Believe { claim_event }]),
    );
    let mut selections = Vec::new();
    for (id, role) in [
        ("main", "before"),
        ("corrected", "corrected"),
        ("rediscovered", "rediscovered"),
    ] {
        let mut scope = imported.root.clone();
        scope.branch = metadata["branches"][role]["branch"]
            .as_str()
            .unwrap()
            .into();
        let engine = store.resume(&scope)?.engine;
        assert_eq!(engine.seed().player, metadata["player"]);
        assert_eq!(
            engine.revision(),
            metadata["branches"][role]["head"].as_u64().unwrap()
        );
        let forbidden = metadata["forbidden"].clone();
        selections.push((id, engine, forbidden));
    }
    selections.push((
        "empty",
        store.resume(&empty_scope)?.engine,
        json!([PRIVATE, "SECRET-TIDE-731"]),
    ));
    selections.push((
        "mixed",
        store.resume(&mixed_scope)?.engine,
        json!([PRIVATE, "SECRET-TIDE-731"]),
    ));
    selections.push((
        "slashes",
        store.resume(&slash_scope)?.engine,
        json!([PRIVATE, "SECRET-TIDE-731"]),
    ));
    selections.push((
        "u64",
        store.resume(&u64_scope)?.engine,
        json!([PRIVATE, "SECRET-TIDE-731"]),
    ));
    let mut archives = BTreeMap::new();
    for story in [
        &imported.root.story,
        &empty_scope.story,
        &mixed_scope.story,
        &slash_scope.story,
        &u64_scope.story,
    ] {
        archives.insert(
            story.clone(),
            store
                .export_archive(story, &|| false)
                .expect("before read archive")
                .bytes()
                .to_vec(),
        );
    }
    assert_eq!(archives[&imported.root.story], ARCHIVE);
    let source_bases = selections
        .iter()
        .map(|(_, engine, _)| engine.accepted_history_basis().unwrap())
        .collect::<Vec<_>>();
    drop(store);

    let host = locallore_workspace::open(&database, false)?;
    assert!(!host.story_lab_granted());
    let mut cases = Vec::new();
    for (id, engine, forbidden) in &selections {
        let scope = engine.scope();
        let resumed = call(&host, json!({"op":"resume","scope":scope}));
        good(&resumed);
        let session = resumed["data"]["session"].as_str().unwrap();
        let opened = call(&host, json!({"op":"open","session":session,"scope":scope}));
        good(&opened);
        let workspace = call(&host, json!({"op":"workspace"}));
        good(&workspace);
        let branches = call(&host, json!({"op":"branches","story":scope.story}));
        good(&branches);
        let capabilities = call(&host, json!({"op":"capabilities"}));
        good(&capabilities);
        assert_eq!(
            capabilities["data"]["free_text"], false,
            "ordinary read owner has no provider"
        );
        let reply = call(
            &host,
            json!({"op":"play_presentation_v2","session":session,"scope":scope,"expected_revision":engine.revision()}),
        );
        good(&reply);
        assert_eq!(reply["data"]["scope"], json!(scope));
        assert_eq!(reply["data"]["revision"], engine.revision());
        assert_eq!(reply["data"]["player"]["observer"], engine.seed().player);
        let (expected_turns, expected_messages) = expected(engine);
        assert_eq!(reply["data"]["turns"], expected_turns);
        if *id == "mixed" {
            assert_eq!(
                reply["data"]["window"],
                json!({"total":24,"start":4,"end":24})
            );
            assert_eq!(expected_messages.as_array().unwrap().len(), 40);
        }
        if *id == "slashes" {
            assert!(
                serde_json::to_vec(&reply)?.len() <= 65_536,
                "actual JNI raw response cap"
            );
            let android_slash_escaped_data =
                serde_json::to_string(&reply["data"])?.replace('/', "\\/");
            assert!(
                android_slash_escaped_data.len() > 65_536,
                "AOSP slash escaping counterexample must be nonvacuous"
            );
        }
        let encoded = serde_json::to_string(&reply)?;
        let raw_reply_utf8_bytes = encoded.len();
        for canary in forbidden.as_array().unwrap() {
            assert!(!encoded.contains(canary.as_str().unwrap()));
        }
        cases.push(json!({"id":id,"scope":scope,"revision":engine.revision(),"observer":engine.seed().player,
            "reply":reply,"expected_messages":expected_messages,"expected_turns":expected_turns,
            "workspace":workspace,"branches":branches,"opened":opened,"resumed":resumed,
            "capabilities":capabilities,"forbidden":forbidden,"raw_reply_utf8_bytes":raw_reply_utf8_bytes}));
        good(&call(
            &host,
            json!({"op":"close","session":session,"scope":scope}),
        ));
    }
    drop(host);

    let mut store = Store::open_application(&database)?;
    for (index, (_, engine, _)) in selections.iter().enumerate() {
        let after = store.resume(engine.scope())?.engine;
        assert_eq!(after.canonical_bytes(), engine.canonical_bytes());
        assert_eq!(after.accepted_history_basis()?, source_bases[index]);
    }
    for (story, bytes) in archives {
        assert_eq!(
            store
                .export_archive(&story, &|| false)
                .expect("after read archive")
                .bytes(),
            bytes
        );
    }
    drop(store);
    let output = serde_json::to_vec(&json!({"version":1,"cases":cases}))?;
    assert!(output.len() <= 256 * 1024, "finite native corpus cap");
    io::stdout().lock().write_all(&output)?;
    Ok(())
}
