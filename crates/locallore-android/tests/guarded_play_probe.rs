// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#![cfg(feature = "play-probe")]
//! Original public-bridge regressions. All response bytes are synthetic, never model evidence.
use locallore::contracts::Scope;
use locallore_android::play_probe::{ProbeRegistry, PROFILE_ID};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const GIFT_TEXT: &str = "I give my last potion to Mira.";
const GIFT: &[u8] = br#"{"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]}"#;

fn profile() -> Vec<u8> {
    // Synthetic artifact identities; the actual experiment's role/context/deadline caps stay fixed.
    serde_json::to_vec(&json!({"id":PROFILE_ID,"model_sha256":"a".repeat(64),
        "runtime_revision":"b".repeat(40),"template_sha256":"c".repeat(64),
        "worker_sha256":"d".repeat(64),"profile_manifest_sha256":"e".repeat(64),
        "context_tokens":4096,"director_tokens":350,"narrator_tokens":220,
        "deadline_ms":60000,"repair_limit":1}))
    .unwrap()
}
fn decode(bytes: Vec<u8>) -> Value {
    assert!(bytes.len() <= 262_144);
    serde_json::from_slice(&bytes).unwrap()
}
fn ok(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "expected fixed native success");
    reply["data"].clone()
}
fn call(registry: &ProbeRegistry, handle: u64, command: Value) -> Value {
    decode(registry.call(
        handle,
        &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
    ))
}
struct Fixture {
    root: PathBuf,
    registry: Arc<ProbeRegistry>,
    handle: u64,
    session: Value,
}
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-guarded-bridge-{}-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        std::fs::write(
            root.join("owner-v1"),
            b"locallore-guarded-bridge-synthetic-v1",
        )
        .unwrap();
        let registry = Arc::new(ProbeRegistry::default());
        let handle = registry
            .open(&root.join("stories.sqlite3"), &profile())
            .unwrap();
        let session = ok(call(
            &registry,
            handle,
            json!({"op":"create","seed":"lantern-quay-v1"}),
        ));
        Self {
            root,
            registry,
            handle,
            session,
        }
    }
    fn call(&self, command: Value) -> Value {
        call(&self.registry, self.handle, command)
    }
    fn operation(&self, op: &str, turn: &str) -> Value {
        json!({"op":op,"session":self.session["session"],"scope":self.session["scope"],"turn":turn})
    }
    fn submit(&self, turn: &str, text: &str) -> Value {
        let request = json!({"version":1,"scope":self.session["scope"],"turn":turn,"expected_revision":0,
            "intent":{"kind":"free_text","value":{"kind":"action","text":text}}});
        assert_eq!(
            ok(self.call(
                json!({"op":"free_text","session":self.session["session"],"request":request})
            ))["phase"],
            "queued"
        );
        request
    }
    fn snapshot(&self, head: u64) -> Value {
        ok(self.call(
            json!({"op":"play_snapshot","session":self.session["session"],
            "scope":self.session["scope"],"expected_revision":head}),
        ))
    }
    fn start(&self, turn: &str) -> Running {
        let registry = self.registry.clone();
        let handle = self.handle;
        let prepare = self.operation("prepare", turn);
        Running {
            registry: self.registry.clone(),
            handle,
            cancel: self.operation("cancel", turn),
            worker: Some(thread::spawn(move || call(&registry, handle, prepare))),
        }
    }
    fn pending(&self, running: &Running) -> Value {
        let deadline = Instant::now() + Duration::from_secs(6);
        loop {
            let pending = ok(decode(self.registry.poll(self.handle)))["pending"].clone();
            if !pending.is_null() {
                return pending;
            }
            assert!(
                !running.finished(),
                "generation ended before expected request"
            );
            assert!(
                Instant::now() < deadline,
                "bounded bridge observation expired"
            );
            thread::sleep(Duration::from_millis(1));
        }
    }
    fn respond(&self, pending: &Value, bytes: &[u8]) {
        assert_eq!(
            ok(decode(self.registry.respond(
                self.handle,
                pending["ticket"].as_u64().unwrap(),
                bytes
            ))),
            json!({"accepted":true})
        );
    }
    fn reopen(&mut self) {
        self.registry.close(self.handle);
        self.handle = self
            .registry
            .open(&self.root.join("stories.sqlite3"), &profile())
            .unwrap();
        self.session = ok(self.call(json!({"op":"resume","scope":self.session["scope"]})));
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.registry.close(self.handle);
        // Preserve every synthetic database under the explicitly selected test TEMP root.
    }
}
struct Running {
    registry: Arc<ProbeRegistry>,
    handle: u64,
    cancel: Value,
    worker: Option<JoinHandle<Value>>,
}
impl Running {
    fn finished(&self) -> bool {
        self.worker.as_ref().unwrap().is_finished()
    }
    fn finish(mut self) -> Value {
        let deadline = Instant::now() + Duration::from_secs(6);
        while !self.finished() {
            assert!(
                Instant::now() < deadline,
                "bounded prepare completion expired"
            );
            thread::sleep(Duration::from_millis(1));
        }
        self.worker.take().unwrap().join().unwrap()
    }
}
impl Drop for Running {
    fn drop(&mut self) {
        if let Some(worker) = self.worker.take() {
            let _ = call(&self.registry, self.handle, self.cancel.clone());
            let _ = worker.join();
        }
    }
}

fn packet<'a>(pending: &'a Value, role: &str) -> &'a Value {
    assert!(pending["ticket"]
        .as_u64()
        .is_some_and(|ticket| ticket > 0 && ticket <= i64::MAX as u64));
    let request = &pending["request"];
    let fields: Vec<_> = request
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    assert_eq!(
        fields,
        [
            "context_tokens",
            "max_tokens",
            "prompt",
            "role",
            "schema",
            "threads",
            "version"
        ]
    );
    assert_eq!(request["version"], 1);
    assert_eq!(request["role"], role);
    assert_eq!(request["threads"], 4);
    assert_eq!(request["context_tokens"], 4096);
    assert_eq!(
        request["max_tokens"],
        if role == "director" { 350 } else { 220 }
    );
    assert!(request["prompt"]
        .as_str()
        .is_some_and(|prompt| !prompt.is_empty()));
    for private_belief in [
        "The tideglass relic is in old-ruins.",
        "Rowan may possess the tideglass relic.",
    ] {
        assert!(!serde_json::to_string(request)
            .unwrap()
            .contains(private_belief));
    }
    assert!(serde_json::to_vec(request).unwrap().len() <= 32768);
    &request["schema"]
}
fn bound(pending: &Value, expected: Value) {
    let schema = packet(pending, "director");
    assert_eq!(schema["additionalProperties"], false);
    let commands = &schema["properties"]["commands"];
    assert_eq!(commands["minItems"], 1);
    assert_eq!(commands["maxItems"], 1);
    let variants = commands["items"]["oneOf"].as_array().unwrap();
    assert_eq!(variants.len(), 1);
    let variant = &variants[0];
    assert_eq!(variant["additionalProperties"], false);
    let fields = expected.as_object().unwrap();
    assert_eq!(
        variant["required"],
        json!(fields.keys().collect::<Vec<_>>())
    );
    assert_eq!(
        variant["properties"].as_object().unwrap().len(),
        fields.len()
    );
    for (name, value) in fields {
        assert_eq!(variant["properties"][name], json!({"const":value}));
    }
}
fn gift_command() -> Value {
    json!({"op":"give","item":"potion","to":"mira","quantity":1})
}
fn narration(pending: &Value) -> Vec<u8> {
    let schema = packet(pending, "narrator");
    assert_eq!(schema["properties"]["event_ids"]["const"], json!([1]));
    serde_json::to_vec(
        &json!({"text":"You pass the potion to Mira.","event_ids":[1],"speaker":"narrator"}),
    )
    .unwrap()
}

#[test]
fn supported_actions_reach_public_sdk_packets_with_only_the_preflighted_arguments() {
    for (text, expected) in [
        (GIFT_TEXT, gift_command()),
        ("drink potion", json!({"op":"consume","item":"potion"})),
        (
            "use ability steady",
            json!({"op":"use_ability","ability":"steady"}),
        ),
        ("learn beacon", json!({"op":"learn","ability":"beacon"})),
        ("go to pier", json!({"op":"move","to":"pier"})),
        ("wait 100 ticks", json!({"op":"wait","ticks":100})),
    ] {
        let fixture = Fixture::new();
        let before = fixture.snapshot(0);
        fixture.submit("schema-only", text);
        let running = fixture.start("schema-only");
        let pending = fixture.pending(&running);
        bound(&pending, expected);
        assert_eq!(
            ok(decode(fixture.registry.poll(fixture.handle)))["pending"],
            pending
        );
        assert_eq!(
            fixture.snapshot(0),
            before,
            "emitting a grammar is not canonical application"
        );
        assert_eq!(
            ok(fixture.call(fixture.operation("cancel", "schema-only")))["phase"],
            "cancelled"
        );
        assert_eq!(ok(running.finish())["phase"], "cancelled");
        assert_eq!(fixture.snapshot(0), before);
    }
}

#[test]
fn explicit_fake_gift_bytes_require_both_roles_then_commit_original_request_and_reopen() {
    let mut fixture = Fixture::new();
    let before = fixture.snapshot(0);
    let request = fixture.submit("guarded-gift", GIFT_TEXT);
    let running = fixture.start("guarded-gift");
    let director = fixture.pending(&running);
    bound(&director, gift_command());
    fixture.respond(&director, GIFT); // Independent literal bytes, never synthesized from schema.
    let narrator = fixture.pending(&running);
    assert!(narrator["ticket"].as_u64().unwrap() > director["ticket"].as_u64().unwrap());
    fixture.respond(&narrator, &narration(&narrator));
    assert_eq!(ok(running.finish())["phase"], "ready");
    assert_eq!(fixture.snapshot(0), before);
    let committed = ok(fixture.call(fixture.operation("commit", "guarded-gift")));
    assert_eq!(committed["phase"], "committed");
    assert_eq!(committed["receipt"]["request"], request);
    assert_eq!(
        committed["receipt"]["proposal"]["commands"],
        json!([gift_command()])
    );
    assert_eq!(
        committed["receipt"]["play"]["profile"],
        serde_json::from_slice::<Value>(&profile()).unwrap()
    );
    assert_eq!(
        committed["receipt"]["play"]["prompt_version"],
        "locallore-play-v2.3"
    );
    assert_eq!(committed["receipt"]["play"]["repairs"], 0);
    let after = fixture.snapshot(1);
    assert!(after["inventory"].get("potion").is_none());
    assert_eq!(after["player"]["facts"], before["player"]["facts"]);
    fixture.reopen();
    assert_eq!(fixture.snapshot(1), after);
    assert_eq!(
        ok(fixture.call(
            json!({"op":"free_text","session":fixture.session["session"],"request":request})
        )),
        committed
    );
    assert_eq!(
        ok(fixture.call(fixture.operation("commit", "guarded-gift"))),
        committed
    );
    assert_eq!(
        ok(decode(fixture.registry.poll(fixture.handle)))["pending"],
        Value::Null
    );
    let scope: Scope = serde_json::from_value(fixture.session["scope"].clone()).unwrap();
    let engine = Store::open(&fixture.root.join("stories.sqlite3"), None)
        .unwrap()
        .resume(&scope)
        .unwrap()
        .engine;
    assert_eq!(engine.receipts().len(), 1);
    assert_eq!(engine.state().items["potion"].owner, "mira");
    assert_eq!(engine.state().items["potion"].quantity, 1);
    for observer in ["player", "mira", "sable"] {
        let context = engine.character_context(observer, &scope, 1).unwrap();
        assert_eq!(
            context.observations.len(),
            if observer == "sable" { 0 } else { 1 }
        );
    }
}

#[test]
fn schema_ignoring_valid_wait_and_wrong_arguments_are_agency_failures_without_narration() {
    for command in [
        json!({"op":"wait","ticks":1}),
        json!({"op":"consume","item":"potion"}),
        json!({"op":"give","item":"potion","to":"mira","quantity":2}),
        json!({"op":"give","item":"brass-key","to":"mira","quantity":1}),
        json!({"op":"give","item":"potion","to":"player","quantity":1}),
    ] {
        let mut fixture = Fixture::new();
        let before = fixture.snapshot(0);
        fixture.submit("ignored-grammar", GIFT_TEXT);
        let running = fixture.start("ignored-grammar");
        let pending = fixture.pending(&running);
        bound(&pending, gift_command());
        fixture.respond(
            &pending,
            &serde_json::to_vec(&json!({"commands":[command]})).unwrap(),
        );
        let failed = ok(running.finish());
        assert_eq!(failed["phase"], "failed");
        assert_eq!(failed["error"], "Agency");
        assert_eq!(
            ok(decode(fixture.registry.poll(fixture.handle)))["pending"],
            Value::Null
        );
        assert_eq!(fixture.snapshot(0), before);
        let commit = ok(fixture.call(fixture.operation("commit", "ignored-grammar")));
        assert_eq!(commit["phase"], "failed");
        assert_eq!(commit["receipt"], Value::Null);
        assert_eq!(commit["scope"], failed["scope"]);
        assert_eq!(commit["turn"], failed["turn"]);
        assert_eq!(commit["expected_revision"], 0);
        fixture.reopen();
        assert_eq!(fixture.snapshot(0), before);
    }
}

#[test]
fn malformed_repair_keeps_exact_bound_grammar_and_never_substitutes_a_correct_proposal() {
    for repair_is_correct in [false, true] {
        let fixture = Fixture::new();
        let before = fixture.snapshot(0);
        fixture.submit("repair", GIFT_TEXT);
        let running = fixture.start("repair");
        let first = fixture.pending(&running);
        bound(&first, gift_command());
        fixture.respond(&first, b"{");
        let repair = fixture.pending(&running);
        bound(&repair, gift_command());
        assert_eq!(repair["request"]["schema"], first["request"]["schema"]);
        assert_ne!(repair["request"]["prompt"], first["request"]["prompt"]);
        assert!(repair["request"]["prompt"]
            .as_str()
            .unwrap()
            .contains("Repair exactly once"));
        assert_eq!(
            decode(fixture.registry.respond(
                fixture.handle,
                first["ticket"].as_u64().unwrap(),
                GIFT
            ))["error"],
            "InvalidTicket"
        );
        fixture.respond(
            &repair,
            if repair_is_correct {
                GIFT
            } else {
                br#"{"commands":[{"op":"wait","ticks":1}]}"#
            },
        );
        if repair_is_correct {
            let narrator = fixture.pending(&running);
            fixture.respond(&narrator, &narration(&narrator));
            let ready = ok(running.finish());
            assert_eq!(ready["phase"], "ready");
        } else {
            let failed = ok(running.finish());
            assert_eq!(failed["phase"], "failed");
            assert_eq!(failed["error"], "Agency");
        }
        assert_eq!(fixture.snapshot(0), before);
        assert_eq!(
            ok(decode(fixture.registry.poll(fixture.handle)))["pending"],
            Value::Null
        );
    }
}

#[test]
fn cancellation_at_repair_and_close_at_narrator_invalidate_only_the_old_guarded_work() {
    for close_at_narrator in [false, true] {
        let mut fixture = Fixture::new();
        let before = fixture.snapshot(0);
        fixture.submit("old", GIFT_TEXT);
        let running = fixture.start("old");
        let first = fixture.pending(&running);
        bound(&first, gift_command());
        fixture.respond(&first, if close_at_narrator { GIFT } else { b"{" });
        let late = fixture.pending(&running);
        packet(
            &late,
            if close_at_narrator {
                "narrator"
            } else {
                "director"
            },
        );
        let old_handle = fixture.handle;
        if close_at_narrator {
            fixture.registry.close(old_handle);
            assert_eq!(running.finish()["error"], "Closed");
            assert_eq!(
                decode(fixture.registry.respond(
                    old_handle,
                    late["ticket"].as_u64().unwrap(),
                    GIFT
                ))["error"],
                "InvalidHandle"
            );
            fixture.reopen();
        } else {
            assert_eq!(
                ok(fixture.call(fixture.operation("cancel", "old")))["phase"],
                "cancelled"
            );
            assert_eq!(ok(running.finish())["phase"], "cancelled");
        }
        assert_eq!(fixture.snapshot(0), before);
        fixture.submit("replacement", "wait 2 ticks");
        let replacement = fixture.start("replacement");
        let current = fixture.pending(&replacement);
        bound(&current, json!({"op":"wait","ticks":2}));
        assert_eq!(
            decode(fixture.registry.respond(
                fixture.handle,
                late["ticket"].as_u64().unwrap(),
                GIFT
            ))["error"],
            "InvalidTicket"
        );
        assert_eq!(
            ok(decode(fixture.registry.poll(fixture.handle)))["pending"],
            current
        );
        assert_eq!(
            ok(fixture.call(fixture.operation("cancel", "replacement")))["phase"],
            "cancelled"
        );
        assert_eq!(ok(replacement.finish())["phase"], "cancelled");
        assert_eq!(fixture.snapshot(0), before);
    }
}
