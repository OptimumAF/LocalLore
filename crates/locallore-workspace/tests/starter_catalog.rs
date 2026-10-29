// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent original catalog/creation adversaries through the real Host and Store.
//! No fixture provider, SQL manipulation, arbitrary seed import, JNI or model inference.
use locallore::{
    contracts::{Profile, Scope, Seed},
    engine::Engine,
    host::Host,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

const FANTASY: &str = "lantern-quay-v1";
const NARRATIVE: &str = "bracken-harbor-v1";
const NARRATIVE_SHA: &str = "df58fc298372389f1366cdee767bac81740e56d5ee0c4ea4cec1d322f0e17347";
static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let base = std::env::temp_dir().canonicalize().unwrap();
        let path = base.join(format!(
            "locallore-catalog-adversary-{}-{}-{}",
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
        self.0.join("stories.sqlite")
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.path(), false).unwrap()
    }
    /// Complete public archive and catalog state, not a comparison of live DB bytes.
    fn canonical(&self) -> Value {
        let mut store = Store::open_application(&self.path()).unwrap();
        let stories = store.stories().unwrap();
        let mut exports = BTreeMap::new();
        let mut catalog = Vec::new();
        for row in stories {
            let archive = store.export_archive(&row.scope.story, &|| false).unwrap();
            exports.insert(
                row.scope.story.clone(),
                serde_json::from_slice::<Value>(archive.bytes()).unwrap(),
            );
            catalog.push(json!({"scope":row.scope,"title":row.title,
                "revision":row.revision,"drafts":row.drafts}));
        }
        json!({"catalog":catalog,"archives":exports})
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        assert_eq!(
            self.0.parent(),
            Some(std::env::temp_dir().canonicalize().unwrap().as_path())
        );
        assert!(self
            .0
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-catalog-adversary-"));
        if let Err(error) = std::fs::remove_dir_all(&self.0) {
            if !std::thread::panicking() {
                panic!("owned synthetic test cleanup: {error}");
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
    let mut keys = value
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect::<Vec<_>>();
    let mut wanted = expected.to_vec();
    keys.sort_unstable();
    wanted.sort_unstable();
    assert_eq!(keys, wanted);
}
fn catalog(host: &Host) -> Value {
    data(call(host, json!({"op":"story_templates"})))
}
fn preview(host: &Host, template: &str) -> Value {
    data(call(
        host,
        json!({"op":"story_template","template":template}),
    ))
}
fn creation(template: &str, hash: &Value, title: &str, id: &str) -> Value {
    json!({"op":"create_named","template":template,"seed_sha256":hash,
        "title":title,"creation_id":id})
}
fn create(host: &Host, template: &str, title: &str, id: &str) -> Value {
    data(call(
        host,
        creation(template, &preview(host, template)["seed_sha256"], title, id),
    ))
}
fn snapshot(host: &Host, created: &Value, head: u64) -> Value {
    data(call(
        host,
        json!({"op":"play_snapshot","session":created["session"],
        "scope":created["scope"],"expected_revision":head}),
    ))
}
fn gift(host: &Host, created: &Value, item: &str, to: &str) -> Value {
    assert_eq!(
        data(call(
            host,
            json!({"op":"submit","session":created["session"],
        "mode":"accepted","request":{"version":1,"scope":created["scope"],
            "turn":"original-catalog-gift","expected_revision":0,
            "intent":{"kind":"actions","value":[{"op":"give","item":item,"to":to,"quantity":1}]}}})
        ))["phase"],
        "queued"
    );
    for (op, phase) in [("prepare", "ready"), ("commit", "committed")] {
        assert_eq!(
            data(call(
                host,
                json!({"op":op,"session":created["session"],
            "scope":created["scope"],"turn":"original-catalog-gift"})
            ))["phase"],
            phase
        );
    }
    snapshot(host, created, 1)
}
fn fixture(template: &str) -> Seed {
    serde_json::from_slice(match template {
        FANTASY => include_bytes!("../../../fixtures/lantern_quay.json"),
        NARRATIVE => include_bytes!("../../../fixtures/bracken_harbor.json"),
        _ => panic!("not a fixed test fixture"),
    })
    .unwrap()
}
fn rejected_without_change(temp: &Temp, host: &Host, before: &Value, cmd: Value, expected: &str) {
    let counts = host.live_counts();
    let reply = call(host, cmd);
    assert_eq!(reply["status"], "rejected", "{reply}");
    assert_eq!(reply["error"], expected, "{reply}");
    assert_eq!(host.live_counts(), counts);
    assert_eq!(&temp.canonical(), before);
}

#[test]
fn catalog_and_both_previews_are_read_only_before_and_after_accepted_history() {
    let temp = Temp::new();
    let host = temp.host();
    let empty = temp.canonical();
    let options = catalog(&host);
    fields(&options, &["version", "templates"]);
    assert_eq!(options["version"], 1);
    assert_eq!(options["templates"].as_array().unwrap().len(), 2);
    for (row, (template, profile)) in options["templates"]
        .as_array()
        .unwrap()
        .iter()
        .zip([(FANTASY, "fantasy_v1"), (NARRATIVE, "narrative_v1")])
    {
        fields(
            row,
            &["template", "default_title", "description", "profile"],
        );
        assert_eq!(row["template"], template);
        assert_eq!(row["profile"], profile);
        let reviewed = preview(&host, template);
        for key in ["template", "default_title", "description", "profile"] {
            assert_eq!(reviewed[key], row[key]);
        }
        assert!(!row["description"].as_str().unwrap().is_empty());
    }
    assert_eq!(host.live_counts(), (0, 0));
    assert_eq!(temp.canonical(), empty);

    let existing = create(&host, FANTASY, "Already played", &"1".repeat(32));
    let accepted = gift(&host, &existing, "potion", "mira");
    let before = temp.canonical();
    let counts = host.live_counts();
    for _ in 0..4 {
        assert_eq!(catalog(&host), options);
        preview(&host, FANTASY);
        preview(&host, NARRATIVE);
    }
    assert_eq!(host.live_counts(), counts);
    assert_eq!(snapshot(&host, &existing, 1), accepted);
    assert_eq!(temp.canonical(), before);
    let ephemeral = Host::new(false);
    assert_eq!(catalog(&ephemeral), options);
    assert_eq!(ephemeral.live_counts(), (0, 0));
}

#[test]
fn narrative_preview_exposes_player_truth_without_disclosing_npc_secret_or_belief() {
    let host = Host::new(false);
    let reviewed = preview(&host, NARRATIVE);
    assert_eq!(reviewed["seed_sha256"], NARRATIVE_SHA);
    assert_ne!(
        reviewed["seed_sha256"],
        preview(&host, FANTASY)["seed_sha256"]
    );
    fields(
        &reviewed,
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
    assert_eq!(reviewed["profile"], "narrative_v1");
    let text = reviewed["details"]
        .as_array()
        .unwrap()
        .iter()
        .map(|line| line.as_str().unwrap())
        .collect::<Vec<_>>()
        .join("\n");
    for visible in [
        "Player: Aster",
        "Inventory borrowed-lantern: 1; return to nessa",
        "Inventory sail-thread: 1",
        "Known fact ferry-schedule:",
        "Commitment return-lantern to nessa:",
    ] {
        assert!(text.contains(visible), "missing visible detail {visible}");
    }
    for hidden in [
        "ledger-location",
        "BRACKEN-CHEST-482",
        "BRACKEN-RUMOR-619",
        "Nessa placed the ferry ledger",
        "may have washed into the reedway",
    ] {
        assert!(
            !serde_json::to_string(&reviewed).unwrap().contains(hidden),
            "hidden detail {hidden}"
        );
        assert!(!serde_json::to_string(&catalog(&host))
            .unwrap()
            .contains(hidden));
    }
    let seed = fixture(NARRATIVE);
    assert_eq!(seed.profile, Profile::NarrativeV1);
    assert!(seed.abilities.is_empty());
    assert!(seed.actors.values().all(|actor| actor.energy == 0
        && actor.abilities.is_empty()
        && actor.attributes.is_empty()));
    let engine = Engine::new(seed.clone()).unwrap();
    let player = engine
        .character_context("player", engine.scope(), 0)
        .unwrap();
    assert!(!player.facts.contains_key("ledger-location"));
    assert!(player.beliefs.is_empty());
    let cal = engine.character_context("cal", engine.scope(), 0).unwrap();
    assert_eq!(cal.beliefs.len(), 1);
    assert!(cal.beliefs[0].proposition.contains("BRACKEN-RUMOR-619"));
    assert!(!cal
        .facts
        .values()
        .any(|text| text.contains("BRACKEN-RUMOR-619")));
    assert!(engine
        .character_context("nessa", engine.scope(), 0)
        .unwrap()
        .facts["ledger-location"]
        .contains("BRACKEN-CHEST-482"));
    Engine::new(fixture(FANTASY)).unwrap();
}

#[test]
fn both_selections_persist_exact_distinct_bundled_seeds_and_keep_accepted_stories_isolated() {
    let temp = Temp::new();
    let host = temp.host();
    let fantasy = create(&host, FANTASY, "Quay choice", &"a".repeat(32));
    let narrative = create(&host, NARRATIVE, "Harbor choice", &"b".repeat(32));
    let fantasy_before = snapshot(&host, &fantasy, 0);
    assert_eq!(fantasy_before["rules"], "fantasy_v1");
    assert_eq!(snapshot(&host, &narrative, 0)["rules"], "narrative_v1");
    assert_ne!(fantasy["scope"], narrative["scope"]);
    let store = Store::open_application(&temp.path()).unwrap();
    for (created, template) in [(&fantasy, FANTASY), (&narrative, NARRATIVE)] {
        let scope: Scope = serde_json::from_value(created["scope"].clone()).unwrap();
        let actual = store.load_seed(&scope).unwrap();
        let mut expected = fixture(template);
        expected.scope = scope;
        assert_eq!(actual, expected);
    }
    drop(store);
    let accepted = gift(&host, &narrative, "borrowed-lantern", "nessa");
    assert!(accepted["inventory"].get("borrowed-lantern").is_none());
    assert_eq!(accepted["inventory"]["sail-thread"]["quantity"], 1);
    assert_eq!(accepted["receipts"].as_array().unwrap().len(), 1);
    assert_eq!(snapshot(&host, &fantasy, 0), fantasy_before);
    drop(host);
    let reopened = temp.host();
    let resumed_fantasy = data(call(
        &reopened,
        json!({"op":"resume","scope":fantasy["scope"]}),
    ));
    let resumed_narrative = data(call(
        &reopened,
        json!({"op":"resume","scope":narrative["scope"]}),
    ));
    assert_eq!(snapshot(&reopened, &resumed_fantasy, 0), fantasy_before);
    assert_eq!(snapshot(&reopened, &resumed_narrative, 1), accepted);
}

#[test]
fn narrative_retry_after_committed_transfer_and_reopen_never_replenishes_or_duplicates_history() {
    let temp = Temp::new();
    let host = temp.host();
    let id = "c".repeat(32);
    let original = create(&host, NARRATIVE, "A deliberate choice", &id);
    let accepted = gift(&host, &original, "sail-thread", "nessa");
    let before = temp.canonical();
    drop(host);
    let reopened = temp.host();
    for _ in 0..3 {
        let retry = create(&reopened, NARRATIVE, "A deliberate choice", &id);
        assert_eq!(retry["created"], false);
        assert_eq!(retry["revision"], 1);
        assert_eq!(snapshot(&reopened, &retry, 1), accepted);
        assert_eq!(temp.canonical(), before);
    }
    assert_eq!(accepted["rules"], "narrative_v1");
    assert!(accepted["inventory"].get("sail-thread").is_none());
    assert_eq!(accepted["receipts"].as_array().unwrap().len(), 1);
    assert_eq!(reopened.live_counts().0, 1);
}

#[test]
fn identical_creation_id_cannot_retarget_a_played_story_to_another_template_in_either_direction() {
    for (first, second, item, recipient) in [
        (FANTASY, NARRATIVE, "potion", "mira"),
        (NARRATIVE, FANTASY, "sail-thread", "nessa"),
    ] {
        let temp = Temp::new();
        let host = temp.host();
        let id = "d".repeat(32);
        let original = create(&host, first, "Same title", &id);
        let accepted = gift(&host, &original, item, recipient);
        let before = temp.canonical();
        rejected_without_change(
            &temp,
            &host,
            &before,
            creation(
                second,
                &preview(&host, second)["seed_sha256"],
                "Same title",
                &id,
            ),
            "DuplicateStory",
        );
        rejected_without_change(
            &temp,
            &host,
            &before,
            creation(
                first,
                &preview(&host, first)["seed_sha256"],
                "Different title",
                &id,
            ),
            "DuplicateStory",
        );
        let matching = create(&host, first, "Same title", &id);
        assert_eq!(matching["created"], false);
        assert_eq!(snapshot(&host, &matching, 1), accepted);
        assert_eq!(temp.canonical(), before);
    }
}

#[test]
fn selected_hash_title_and_closed_catalog_envelope_refuse_without_any_canonical_change() {
    let temp = Temp::new();
    let host = temp.host();
    let original = create(&host, NARRATIVE, "Original harbor", &"e".repeat(32));
    gift(&host, &original, "sail-thread", "nessa");
    let before = temp.canonical();
    let id = "f".repeat(32);
    for (template, foreign) in [(FANTASY, NARRATIVE), (NARRATIVE, FANTASY)] {
        rejected_without_change(
            &temp,
            &host,
            &before,
            creation(
                template,
                &preview(&host, foreign)["seed_sha256"],
                "Hash from other choice",
                &id,
            ),
            "Stale",
        );
    }
    for title in ["", " leading", "line\nbreak", "hidden\u{202e}order"] {
        rejected_without_change(
            &temp,
            &host,
            &before,
            creation(
                NARRATIVE,
                &preview(&host, NARRATIVE)["seed_sha256"],
                title,
                &id,
            ),
            "InvalidTitle",
        );
    }
    for bad in [
        json!({"op":"story_templates","template":NARRATIVE}),
        json!({"op":"story_templates","seed":fixture(NARRATIVE)}),
        json!({"op":"story_templates","version":1}),
        json!({"op":"story_templates","private":"original-catalog-canary"}),
    ] {
        rejected_without_change(&temp, &host, &before, bad, "Malformed");
    }
    for wrong in [Value::Null, json!(true), json!(7), json!([]), json!({})] {
        rejected_without_change(
            &temp,
            &host,
            &before,
            json!({"op":"story_template","template":wrong}),
            "Malformed",
        );
    }
    for raw in [
        br#"{"version":1,"command":{"op":"story_templates","op":"story_templates"}}"#.as_slice(),
        br#"{"version":1,"version":1,"command":{"op":"story_templates"}}"#.as_slice(),
        br#"{"version":1,"command":{"op":"story_templates"}}{}"#.as_slice(),
    ] {
        assert_eq!(host.call(raw)["error"], "Malformed");
        assert_eq!(temp.canonical(), before);
    }
    rejected_without_change(
        &temp,
        &host,
        &before,
        json!({"op":"story_template","template":"arbitrary-seed-canary"}),
        "UnsupportedSeed",
    );
    let ephemeral = Host::new(false);
    let unsupported = call(
        &ephemeral,
        creation(
            NARRATIVE,
            &preview(&ephemeral, NARRATIVE)["seed_sha256"],
            "Read only host",
            &id,
        ),
    );
    assert_eq!(unsupported["error"], "Unsupported");
    assert_eq!(ephemeral.live_counts(), (0, 0));
    assert_eq!(temp.canonical(), before);
}
