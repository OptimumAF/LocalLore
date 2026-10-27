// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Original Host/Store assertions; no SQL, model, JNI or alternate story authority.
//! Source-only author handoff. Coordinator must compile/run this exact target.
use locallore::{
    contracts::Seed,
    host::{Host, MAX_INPUT, MAX_SESSIONS},
    inference::{FakeMode, FakeProvider},
    play::PlayProfile,
};
use locallore_storage::{validate_archive, Store};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, AtomicUsize, Ordering},
        Arc,
    },
};

const TEMPLATE: &str = "lantern-quay-v1";
static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temp {
    directory: PathBuf,
    parent: PathBuf,
}
impl Temp {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let directory = parent.join(format!(
            "locallore-story-creation-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        Self { directory, parent }
    }
    fn path(&self) -> PathBuf {
        self.directory.join("stories.sqlite")
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.path(), false).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        assert_eq!(self.directory.parent(), Some(self.parent.as_path()));
        assert!(self
            .directory
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-story-creation-"));
        if let Err(error) = std::fs::remove_dir_all(&self.directory) {
            if !std::thread::panicking() {
                panic!("owned synthetic cleanup: {error}");
            }
        }
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn fields(value: &Value, expected: &[&str]) {
    assert_eq!(
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>()
    );
}
fn preview(host: &Host) -> Value {
    data(call(
        host,
        json!({"op":"story_template","template":TEMPLATE}),
    ))
}
fn command(hash: &Value, title: &str, id: &str) -> Value {
    json!({"op":"create_named","template":TEMPLATE,"seed_sha256":hash,"title":title,"creation_id":id})
}
fn named(host: &Host, hash: &Value, title: &str, id: &str) -> Value {
    data(call(host, command(hash, title, id)))
}
fn snapshot(host: &Host, created: &Value, head: u64) -> Value {
    data(call(
        host,
        json!({"op":"play_snapshot","session":created["session"],"scope":created["scope"],"expected_revision":head}),
    ))
}
fn gift(host: &Host, created: &Value) -> Value {
    let request = json!({"version":1,"scope":created["scope"],"turn":"original-creation-gift","expected_revision":0,
        "intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}});
    assert_eq!(
        data(call(
            host,
            json!({"op":"submit","session":created["session"],"request":request,"mode":"accepted"})
        ))["phase"],
        "queued"
    );
    for (op, phase) in [("prepare", "ready"), ("commit", "committed")] {
        assert_eq!(
            data(call(
                host,
                json!({"op":op,"session":created["session"],"scope":created["scope"],"turn":"original-creation-gift"})
            ))["phase"],
            phase
        );
    }
    snapshot(host, created, 1)
}
/// Compare native canonical exports and the complete catalog, never live SQLite file bytes.
fn canonical(path: &Path) -> Value {
    let mut store = Store::open_application(path).unwrap();
    let stories = store.stories().unwrap();
    let mut archives = BTreeMap::new();
    let catalog = stories
        .iter()
        .map(|row| {
            json!({"scope":row.scope,"title":row.title,
        "revision":row.revision,"drafts":row.drafts})
        })
        .collect::<Vec<_>>();
    for row in stories {
        let archive = store.export_archive(&row.scope.story, &|| false).unwrap();
        archives.insert(
            row.scope.story,
            serde_json::from_slice::<Value>(archive.bytes()).unwrap(),
        );
    }
    json!({"stories":catalog,"archives":archives})
}
fn assert_refusal_unchanged(host: &Host, path: &Path, before: &Value, cmd: Value, error: &str) {
    let reply = call(host, cmd);
    assert_eq!(reply["status"], "rejected", "{reply}");
    assert_eq!(reply["error"], error, "{reply}");
    assert_eq!(&canonical(path), before);
}

#[test]
fn preview_is_closed_player_eligible_and_never_allocates_a_story_session_or_provider() {
    let temp = Temp::new();
    let host = temp.host();
    let factories = Arc::new(AtomicUsize::new(0));
    let observed = factories.clone();
    host.configure_fixture_provider(
        PlayProfile {
            id: "synthetic-creation-forbidden-v1".into(),
            model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40),
            template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64),
            profile_manifest_sha256: "e".repeat(64),
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 220,
            deadline_ms: 5000,
            repair_limit: 1,
        },
        Arc::new(move || {
            observed.fetch_add(1, Ordering::SeqCst);
            Box::new(FakeProvider::new(FakeMode::Failed))
        }),
    )
    .unwrap();
    let before = canonical(&temp.path());
    let first = preview(&host);
    fields(
        &first,
        &[
            "version",
            "template",
            "seed_sha256",
            "default_title",
            "description",
            "profile",
            "details",
        ],
    );
    assert_eq!(first["version"], 1);
    assert_eq!(first["template"], TEMPLATE);
    assert_eq!(first["default_title"], "Lantern Quay");
    assert_eq!(first["profile"], "fantasy_v1");
    let hash = first["seed_sha256"].as_str().unwrap();
    assert_eq!(hash.len(), 64);
    assert!(hash
        .bytes()
        .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)));
    let details = first["details"].as_array().unwrap();
    assert!(!details.is_empty() && details.len() <= 64);
    assert!(details
        .iter()
        .all(|line| line.as_str().unwrap().len() <= 2048));
    assert!(serde_json::to_vec(&first).unwrap().len() <= 16384);
    let lines = details
        .iter()
        .map(|line| line.as_str().unwrap())
        .collect::<Vec<_>>();
    assert!(lines.contains(&"Player: Rowan"));
    assert!(lines.contains(&"Inventory potion: 1"));
    assert!(lines
        .iter()
        .any(|line| line.starts_with("Known fact ancestry:")));
    assert!(lines
        .iter()
        .any(|line| line.starts_with("Known fact relic-location:")
            && line.contains("SECRET-TIDE-731")));
    let text = lines.join("\n");
    for hidden in [
        "beacon-mark",
        "An old repair mark",
        "The tideglass relic is in old-ruins.",
        "Rowan may possess the tideglass relic.",
        "respect 4, trust -3",
    ] {
        assert!(!text.contains(hidden), "NPC/unknown detail escaped");
    }
    for _ in 0..8 {
        assert_eq!(preview(&host), first);
    }
    assert_eq!(host.live_counts(), (0, 0));
    assert_eq!(factories.load(Ordering::SeqCst), 0);
    assert_eq!(canonical(&temp.path()), before);
    let ephemeral = Host::new(false);
    assert_eq!(preview(&ephemeral), first);
    assert_eq!(ephemeral.live_counts(), (0, 0));
}

#[test]
fn repeated_preview_preserves_every_existing_canonical_story_and_accepted_receipt() {
    let temp = Temp::new();
    let host = temp.host();
    let hash = preview(&host)["seed_sha256"].clone();
    let a = named(&host, &hash, "Original A", &"1".repeat(32));
    gift(&host, &a);
    named(&host, &hash, "Original B", &"2".repeat(32));
    let before = canonical(&temp.path());
    let counts = host.live_counts();
    for _ in 0..5 {
        preview(&host);
    }
    assert_refusal_unchanged(
        &host,
        &temp.path(),
        &before,
        json!({"op":"story_template","template":"foreign-starter"}),
        "UnsupportedSeed",
    );
    assert_eq!(canonical(&temp.path()), before);
    assert_eq!(host.live_counts(), counts);
    assert_eq!(
        snapshot(&host, &a, 1)["receipts"].as_array().unwrap().len(),
        1
    );
}

#[test]
fn explicit_named_unicode_creation_reopens_and_round_trips_the_actual_seed_title_and_receipt() {
    let source = Temp::new();
    let host = source.host();
    let hash = preview(&host)["seed_sha256"].clone();
    let title = "😀".repeat(80);
    assert_eq!(title.len(), 320);
    let created = named(&host, &hash, &title, &"a".repeat(32));
    fields(&created, &["session", "scope", "revision", "created"]);
    assert_eq!(
        created["scope"],
        json!({"story":format!("quay-{}", "a".repeat(32)),"branch":"main"})
    );
    assert_eq!(created["revision"], 0);
    assert_eq!(created["created"], true);
    let accepted = gift(&host, &created);
    drop(host);
    let reopened = source.host();
    let retry = named(&reopened, &hash, &title, &"a".repeat(32));
    assert_eq!(retry["created"], false);
    assert_eq!(retry["revision"], 1);
    assert_eq!(snapshot(&reopened, &retry, 1), accepted);
    let mut store = Store::open_application(&source.path()).unwrap();
    let archive = store
        .export_archive(created["scope"]["story"].as_str().unwrap(), &|| false)
        .unwrap();
    let validated = validate_archive(archive.bytes(), &|| false).unwrap();
    assert_eq!(validated.preview().title, title);
    assert_eq!(validated.preview().committed_turns, 1);
    let target = Temp::new();
    let mut imported = Store::open_application(&target.path()).unwrap();
    let outcome = imported.import_archive(validated, &|| false).unwrap();
    assert_eq!(
        serde_json::to_value(&outcome.root).unwrap(),
        created["scope"]
    );
    assert_eq!(outcome.committed_turns, 1);
    drop(imported);
    drop(store);
    let target_host = target.host();
    let resumed = data(call(
        &target_host,
        json!({"op":"resume","scope":created["scope"]}),
    ));
    assert_eq!(snapshot(&target_host, &resumed, 1), accepted);
    assert_eq!(canonical(&target.path()), canonical(&source.path()));
}

#[test]
fn matching_retries_refresh_advanced_head_and_reuse_the_attached_session_even_at_capacity() {
    let temp = Temp::new();
    let first = temp.host();
    let hash = preview(&first)["seed_sha256"].clone();
    let original = named(&first, &hash, "Stable title", &"1".repeat(32));
    let second = temp.host();
    let other = named(&second, &hash, "Stable title", &"1".repeat(32));
    let accepted = gift(&second, &other);
    for n in 2..=MAX_SESSIONS {
        named(&first, &hash, &format!("Other {n}"), &format!("{n:032x}"));
    }
    assert_eq!(first.live_counts(), (MAX_SESSIONS, 0));
    let before = canonical(&temp.path());
    for _ in 0..6 {
        let retry = named(&first, &hash, "Stable title", &"1".repeat(32));
        assert_eq!(retry["created"], false);
        assert_eq!(retry["revision"], 1);
        assert_eq!(retry["session"], original["session"]);
        assert_eq!(retry["scope"], original["scope"]);
        assert_eq!(snapshot(&first, &retry, 1), accepted);
    }
    assert_eq!(first.live_counts(), (MAX_SESSIONS, 0));
    assert_eq!(canonical(&temp.path()), before);
}

#[test]
fn session_capacity_refuses_new_attachment_before_any_persistent_creation() {
    let temp = Temp::new();
    let host = temp.host();
    let hash = preview(&host)["seed_sha256"].clone();
    for n in 1..=MAX_SESSIONS {
        named(&host, &hash, &format!("Story {n}"), &format!("{n:032x}"));
    }
    let before = canonical(&temp.path());
    assert_refusal_unchanged(
        &host,
        &temp.path(),
        &before,
        command(&hash, "No attachment", &"f".repeat(32)),
        "SessionLimit",
    );
    preview(&host);
    assert_eq!(host.live_counts(), (MAX_SESSIONS, 0));
    // A known refusal is not an uncertain commit: a separate owner can create this still-absent ID once.
    let second = temp.host();
    assert_eq!(
        named(&second, &hash, "No attachment", &"f".repeat(32))["created"],
        true
    );
}

#[test]
fn invalid_titles_ids_hashes_and_templates_preserve_prior_canon_without_normalization() {
    let temp = Temp::new();
    let host = temp.host();
    let hash = preview(&host)["seed_sha256"].clone();
    let original = named(&host, &hash, "Prior title", &"1".repeat(32));
    gift(&host, &original);
    let before = canonical(&temp.path());
    let id = "2".repeat(32);
    for title in [
        "".into(),
        " leading".into(),
        "trailing ".into(),
        "line\nfeed".into(),
        "tab\tinside".into(),
        "nul\0inside".into(),
        "separator\u{2028}here".into(),
        "paragraph\u{2029}here".into(),
        "bidi\u{202e}here".into(),
        "isolate\u{2067}here".into(),
        "a".repeat(81),
        "😀".repeat(81),
    ] {
        assert_refusal_unchanged(
            &host,
            &temp.path(),
            &before,
            command(&hash, &title, &id),
            "InvalidTitle",
        );
    }
    for bad in [
        "".into(),
        "a".repeat(31),
        "a".repeat(33),
        "A".repeat(32),
        "g".repeat(32),
        "../".repeat(11),
        "é".repeat(16),
    ] {
        assert_refusal_unchanged(
            &host,
            &temp.path(),
            &before,
            command(&hash, "Valid title", &bad),
            "InvalidInput",
        );
    }
    for bad_hash in ["".into(), "0".repeat(64), "A".repeat(64)] {
        assert_refusal_unchanged(
            &host,
            &temp.path(),
            &before,
            command(&json!(bad_hash), "Valid title", &id),
            "Stale",
        );
    }
    let mut unknown = command(&hash, "Valid title", &id);
    unknown["template"] = json!("foreign-starter");
    assert_refusal_unchanged(&host, &temp.path(), &before, unknown, "UnsupportedSeed");
    assert_eq!(host.live_counts(), (1, 0));
}

#[test]
fn closed_raw_envelopes_reject_duplicate_wrong_type_extra_and_future_input_before_writes() {
    let temp = Temp::new();
    let host = temp.host();
    let hash = preview(&host)["seed_sha256"].clone();
    named(&host, &hash, "Prior", &"1".repeat(32));
    let before = canonical(&temp.path());
    assert_refusal_unchanged(
        &host,
        &temp.path(),
        &before,
        json!({"op":"story_template"}),
        "Malformed",
    );
    assert_refusal_unchanged(
        &host,
        &temp.path(),
        &before,
        json!({"op":"story_template","template":TEMPLATE,"private":"original-hostile-canary"}),
        "Malformed",
    );
    for wrong in [Value::Null, json!(true), json!(2), json!([]), json!({})] {
        assert_refusal_unchanged(
            &host,
            &temp.path(),
            &before,
            json!({"op":"story_template","template":wrong}),
            "Malformed",
        );
    }
    assert_eq!(host.call(br#"{"version":1,"command":{"op":"story_template","template":"lantern-quay-v1","template":"lantern-quay-v1"}}"#)["error"], "Malformed");
    let original = command(&hash, "Valid", &"2".repeat(32));
    for key in ["template", "seed_sha256", "title", "creation_id"] {
        let mut missing = original.clone();
        missing.as_object_mut().unwrap().remove(key);
        assert_refusal_unchanged(&host, &temp.path(), &before, missing, "Malformed");
        for wrong in [Value::Null, json!(true), json!(2), json!([]), json!({})] {
            let mut wrong_type = original.clone();
            wrong_type[key] = wrong;
            assert_refusal_unchanged(&host, &temp.path(), &before, wrong_type, "Malformed");
        }
    }
    let mut extra = original.clone();
    extra["private"] = json!("original-hostile-canary");
    assert_refusal_unchanged(&host, &temp.path(), &before, extra, "Malformed");
    let valid = serde_json::to_string(&json!({"version":1,"command":original})).unwrap();
    let malformed = [
        valid.replacen(
            "\"title\":\"Valid\"",
            "\"title\":\"Valid\",\"title\":\"Other\"",
            1,
        ),
        valid.replacen("\"version\":1", "\"version\":1,\"version\":1", 1),
        format!("{valid}{{}}"),
        valid.replace("\"Valid\"", "\"\\ud800\""),
    ];
    for raw in malformed {
        assert_ne!(raw, valid);
        assert_eq!(host.call(raw.as_bytes())["error"], "Malformed");
    }
    assert_eq!(host.call(&[0xff])["error"], "Malformed");
    assert_eq!(host.call(&vec![b' '; MAX_INPUT + 1])["error"], "TooLarge");
    let mut future: Value = serde_json::from_str(&valid).unwrap();
    future["version"] = json!(2);
    assert_eq!(
        host.call(&serde_json::to_vec(&future).unwrap())["error"],
        "Version"
    );
    assert_eq!(canonical(&temp.path()), before);
    assert_eq!(host.live_counts(), (1, 0));
}

#[test]
fn title_and_foreign_seed_or_root_collisions_never_adopt_or_overwrite_existing_rows() {
    let temp = Temp::new();
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    {
        let mut store = Store::open_application(&temp.path()).unwrap();
        let mut foreign = seed.clone();
        foreign.scope.story = format!("quay-{}", "b".repeat(32));
        foreign.actors.get_mut("player").unwrap().name = "Another original player".into();
        store.create_story("Collision", foreign).unwrap();
        let mut other_root = seed;
        other_root.scope.story = format!("quay-{}", "c".repeat(32));
        other_root.scope.branch = "other-root".into();
        store.create_story("Collision", other_root).unwrap();
    }
    let host = temp.host();
    let hash = preview(&host)["seed_sha256"].clone();
    let created = named(&host, &hash, "Original title", &"a".repeat(32));
    gift(&host, &created);
    let before = canonical(&temp.path());
    for (title, id) in [
        ("Changed title", "a"),
        ("Collision", "b"),
        ("Collision", "c"),
    ] {
        assert_refusal_unchanged(
            &host,
            &temp.path(),
            &before,
            command(&hash, title, &id.repeat(32)),
            "DuplicateStory",
        );
    }
    assert_eq!(host.live_counts(), (1, 0));
}

#[test]
fn nonpersistent_named_creation_refuses_without_breaking_legacy_create_or_preview() {
    let host = Host::new(false);
    let first = preview(&host);
    assert_eq!(
        call(
            &host,
            command(&first["seed_sha256"], "No persistence", &"a".repeat(32))
        )["error"],
        "Unsupported"
    );
    assert_eq!(host.live_counts(), (0, 0));
    let legacy = data(call(&host, json!({"op":"create","seed":TEMPLATE})));
    fields(&legacy, &["session", "scope", "revision"]);
    assert_eq!(legacy["revision"], 0);
    assert_eq!(preview(&host), first);
    assert_eq!(host.live_counts(), (1, 0));
}
