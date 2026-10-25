//! Actual SQLite/Repository/Host policy construction; bounded synthetic provider only.
use locallore::{
    context_compiler::ContextPolicy, contracts::*, engine::Engine, host::Host, inference::*,
    play::PlayProfile,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{Arc, Mutex},
    task::Poll,
};
fn call(h: &Host, c: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap())
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "comparison-scripted".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 120000,
        repair_limit: 1,
    }
}
#[derive(Clone)]
struct Script(Arc<Mutex<Vec<GenerationRequest>>>);
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.0.lock().unwrap().push(r.clone());
        let Input::Structured { role, schema, .. } = &r.input else {
            panic!("actual structured input")
        };
        let v = if role == "director" {
            json!({"commands":[{"op":"wait","ticks":1}]})
        } else {
            json!({"text":"Time passes.","speaker":"narrator","event_ids":schema["properties"]["event_ids"]["const"]})
        };
        Poll::Ready(Ok(serde_json::to_vec(&v).unwrap()))
    }
}
fn setup(name: &str) -> (PathBuf, Seed) {
    let p = std::env::temp_dir().join(format!(
        "locallore-comparison-policy-{name}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&p).unwrap();
    let path = p.join("synthetic.sqlite");
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let mut store = Store::open_application(&path).unwrap();
    store
        .create_story("Synthetic policy", seed.clone())
        .unwrap();
    for i in 0..12 {
        let e = store.resume(&seed.scope).unwrap().engine;
        let r = e.request(
            &format!("history-{i}"),
            Intent::Actions(vec![Command::Say {
                text: format!("PUBLIC_OLD_HISTORY_{i}"),
                audience: ["mira".into()].into(),
            }]),
        );
        let p = Engine::proposal(&r).unwrap();
        let narration = e.preview(&r, &p).unwrap().narration().to_owned();
        store.begin_turn(&r).unwrap();
        store.commit_turn(&r, &p, &narration).unwrap();
    }
    (path, seed)
}
#[test]
fn actual_repository_both_policies_commit_and_retry_without_provider_after_restart() {
    let mut packages = Vec::new();
    for policy in [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ] {
        let (path, seed) = setup(&format!("{policy:?}"));
        let h = locallore_workspace::open(&path, true).unwrap();
        let s = call(&h, json!({"op":"resume","scope":seed.scope}))["data"]["session"]
            .as_str()
            .unwrap()
            .to_owned();
        let seen = Arc::new(Mutex::new(Vec::new()));
        let script = Script(seen.clone());
        h.configure_fixture_provider_with_policy(
            profile(),
            Arc::new(move || Box::new(script.clone())),
            policy,
        )
        .unwrap();
        let before = Store::open_application(&path)
            .unwrap()
            .resume(&seed.scope)
            .unwrap()
            .engine;
        let r = before.request(
            "current",
            Intent::FreeText {
                kind: PlayInputKind::Action,
                text: "I wait for one tide tick.".into(),
            },
        );
        assert_eq!(
            call(&h, json!({"op":"free_text","session":s,"request":r}))["data"]["phase"],
            "queued"
        );
        assert_eq!(
            call(
                &h,
                json!({"op":"prepare","session":s,"scope":seed.scope,"turn":r.turn})
            )["data"]["phase"],
            "ready"
        );
        let committed = call(
            &h,
            json!({"op":"commit","session":s,"scope":seed.scope,"turn":r.turn}),
        );
        assert_eq!(committed["data"]["phase"], "committed", "{committed}");
        let record = &committed["data"]["receipt"]["play"];
        assert_eq!(record["prompt_version"], "locallore-play-v2.5");
        assert_eq!(record["context"]["compiler_version"], 2);
        assert_eq!(
            record["context_policy"],
            serde_json::to_value(policy).unwrap()
        );
        assert_eq!(seen.lock().unwrap().len(), 2);
        let requests = seen.lock().unwrap();
        let Input::Structured {
            prompt: director, ..
        } = &requests[0].input
        else {
            panic!()
        };
        let package: Value =
            serde_json::Deserializer::from_str(director.split_once("Context data: ").unwrap().1)
                .into_iter::<Value>()
                .next()
                .unwrap()
                .unwrap();
        assert_eq!(package["context"]["compiler_version"], 2);
        assert_eq!(package["context"]["observer"], seed.player);
        assert_eq!(package["context"]["revision"], 12);
        packages.push(package["context"].clone());
        let Input::Structured {
            prompt: narrator, ..
        } = &requests[1].input
        else {
            panic!()
        };
        assert!(!narrator.contains("PUBLIC_OLD_HISTORY_"));
        assert!(!narrator.contains("SECRET-TIDE-731"));
        drop(requests);
        let mut store = Store::open_application(&path).unwrap();
        let after = store.resume(&seed.scope).unwrap().engine;
        assert_eq!(after.revision(), 13);
        assert_eq!(before.revision(), 12);
        assert_eq!(
            serde_json::to_value(
                store
                    .lookup_turn(&seed.scope, &r.turn)
                    .unwrap()
                    .receipt
                    .unwrap()
            )
            .unwrap(),
            committed["data"]["receipt"]
        );
        h.close_all();
        drop(h);
        let reopened = locallore_workspace::open(&path, true).unwrap();
        let sid = call(&reopened, json!({"op":"resume","scope":seed.scope}))["data"]["session"]
            .as_str()
            .unwrap()
            .to_owned();
        let retry = call(
            &reopened,
            json!({"op":"free_text","session":sid,"request":r}),
        );
        assert_eq!(retry["data"]["receipt"], committed["data"]["receipt"]);
        assert_eq!(seen.lock().unwrap().len(), 2);
        assert_eq!(
            store.resume(&seed.scope).unwrap().engine.canonical_bytes(),
            after.canonical_bytes()
        );
    }
    let recent = serde_json::to_string(&packages[0]).unwrap();
    let relevant = serde_json::to_string(&packages[1]).unwrap();
    assert!(recent.contains("transcript_unit"));
    assert!(!relevant.contains("transcript_unit"));
}
