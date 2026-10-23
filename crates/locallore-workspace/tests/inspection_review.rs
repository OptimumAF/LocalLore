// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent privacy and snapshot-ownership checks with synthetic real SQLite stories.
use locallore::{
    contracts::{Belief, Confidence, Evidence, Fact, Scope, Seed},
    host::Host,
    inspection::{ExportMode, InspectionBundle},
};
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::PathBuf};

const HIDDEN_FACT: &str = "PRIVATE-NPC-FACT-CANARY-483";
const HIDDEN_BELIEF: &str = "PRIVATE-NPC-BELIEF-CANARY-702";
const HIDDEN_SHEET: &str = "PRIVATE-NPC-SHEET-CANARY-963";
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-inspection-review-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn host(&self, lab: bool) -> Host {
        locallore_workspace::open(&self.0.join("synthetic.sqlite"), lab).unwrap()
    }
    fn seed(&self) -> Scope {
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope.story = "synthetic-review-story".into();
        seed.facts.insert(
            "private-review-fact".into(),
            Fact {
                proposition: HIDDEN_FACT.into(),
                discoverable_at: None,
                known_by: BTreeSet::from(["mira".into()]),
            },
        );
        seed.beliefs.push(Belief {
            believer: "mira".into(),
            proposition: HIDDEN_BELIEF.into(),
            source_claim: None,
            source: Evidence::Seed(seed.id.clone()),
            confidence: Confidence::Believed,
        });
        seed.actors.get_mut("sable").unwrap().name = HIDDEN_SHEET.into();
        let scope = seed.scope.clone();
        let mut store =
            locallore_storage::Store::open(&self.0.join("synthetic.sqlite"), None).unwrap();
        store.create_story("Synthetic review", seed).unwrap();
        scope
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn call(h: &Host, command: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn resume(h: &Host, scope: &Scope) -> String {
    let v = call(h, json!({"op":"resume","scope":scope}));
    assert_eq!(v["status"], "ok", "{v}");
    v["data"]["session"].as_str().unwrap().into()
}
fn joined(bundle: &InspectionBundle) -> String {
    let mut text = serde_json::to_string(&bundle.manifest).unwrap();
    for (name, bytes) in &bundle.files {
        text.push_str(name);
        text.push_str(std::str::from_utf8(bytes).unwrap());
    }
    text
}
fn give(h: &Host, id: &str, scope: &Scope, turn: &str) -> Value {
    let req = json!({"version":1,"scope":scope,"turn":turn,"expected_revision":0,"intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}});
    assert_eq!(
        call(
            h,
            json!({"op":"submit","session":id,"request":req,"mode":"accepted"})
        )["data"]["phase"],
        "queued"
    );
    assert_eq!(
        call(
            h,
            json!({"op":"prepare","session":id,"scope":scope,"turn":turn})
        )["data"]["phase"],
        "ready"
    );
    let v = call(
        h,
        json!({"op":"commit","session":id,"scope":scope,"turn":turn}),
    );
    assert_eq!(v["data"]["phase"], "committed", "{v}");
    v
}

#[test]
fn player_export_filters_every_file_and_manifest_without_erasing_known_player_facts() {
    let dir = Temp::new();
    let scope = dir.seed();
    let h = dir.host(true);
    let id = resume(&h, &scope);
    give(&h, &id, &scope, "gift");
    let bundle = h
        .inspection_snapshot(&id, &scope, 1, ExportMode::Player)
        .unwrap();
    let text = joined(&bundle);
    for secret in [HIDDEN_FACT, HIDDEN_BELIEF, HIDDEN_SHEET] {
        assert!(!text.contains(secret), "player export leaked {secret}");
    }
    assert!(
        text.contains("SECRET-TIDE-731"),
        "this fixture fact is actually player-known"
    );
    assert!(
        !text.contains(dir.0.to_str().unwrap()),
        "native workspace path is not story inspection data"
    );
    assert_eq!(bundle.manifest["revision"], 1);
}

#[test]
fn full_export_requires_native_lab_authority_and_keeps_explicit_hidden_inspection() {
    let dir = Temp::new();
    let scope = dir.seed();
    let play = dir.host(false);
    let id = resume(&play, &scope);
    assert_eq!(
        play.inspection_snapshot(&id, &scope, 0, ExportMode::Full)
            .err()
            .unwrap(),
        "Forbidden"
    );
    let lab = dir.host(true);
    let id = resume(&lab, &scope);
    let full = lab
        .inspection_snapshot(&id, &scope, 0, ExportMode::Full)
        .unwrap();
    let text = joined(&full);
    for secret in [HIDDEN_FACT, HIDDEN_BELIEF, HIDDEN_SHEET] {
        assert!(
            text.contains(secret),
            "full inspection omitted implemented {secret}"
        );
    }
    assert!(!text.contains(dir.0.to_str().unwrap()));
}

#[test]
fn export_is_not_a_wire_path_or_a_way_to_select_foreign_scope() {
    let dir = Temp::new();
    let scope = dir.seed();
    let h = dir.host(true);
    let id = resume(&h, &scope);
    let reply = call(
        &h,
        json!({"op":"inspection_snapshot","session":id,"scope":scope,"expected_revision":0,"mode":"full","path":"../outside"}),
    );
    assert_eq!(reply["error"], "Malformed");
    let mut wrong = scope.clone();
    wrong.story = "foreign-story".into();
    assert_eq!(
        h.inspection_snapshot(&id, &wrong, 0, ExportMode::Player)
            .err()
            .unwrap(),
        "Scope"
    );
    assert_eq!(
        h.inspection_snapshot("closed-session", &scope, 0, ExportMode::Player)
            .err()
            .unwrap(),
        "Closed"
    );
    assert_eq!(
        h.inspection_snapshot(&id, &scope, 99, ExportMode::Player)
            .err()
            .unwrap(),
        "Stale"
    );
}

#[test]
fn external_commit_invalidates_expected_head_while_captured_bundle_stays_immutable() {
    let dir = Temp::new();
    let scope = dir.seed();
    let first = dir.host(true);
    let a = resume(&first, &scope);
    let captured = first
        .inspection_snapshot(&a, &scope, 0, ExportMode::Full)
        .unwrap();
    let before = joined(&captured);
    let second = dir.host(false);
    let b = resume(&second, &scope);
    give(&second, &b, &scope, "external");
    assert_eq!(
        first
            .inspection_snapshot(&a, &scope, 0, ExportMode::Full)
            .err()
            .unwrap(),
        "Stale"
    );
    let next = first
        .inspection_snapshot(&a, &scope, 1, ExportMode::Full)
        .unwrap();
    assert_eq!(captured.manifest["revision"], 0);
    assert_eq!(joined(&captured), before);
    assert_eq!(next.manifest["revision"], 1);
    let unchanged = call(
        &second,
        json!({"op":"turn_status","session":b,"scope":scope,"turn":"external"}),
    );
    assert_eq!(unchanged["data"]["phase"], "committed");
    assert_eq!(
        call(
            &second,
            json!({"op":"play_snapshot","session":b,"scope":scope,"expected_revision":1})
        )["data"]["receipts"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn default_diagnostics_are_structural_and_do_not_include_seed_or_story_prose() {
    let dir = Temp::new();
    let scope = dir.seed();
    let h = dir.host(false);
    let id = resume(&h, &scope);
    give(&h, &id, &scope, "gift");
    let bundle = h
        .inspection_snapshot(&id, &scope, 1, ExportMode::default())
        .unwrap();
    assert_eq!(bundle.manifest["mode"], "diagnostics");
    assert_eq!(bundle.manifest["privacy"], "structural_metadata_only");
    assert_eq!(
        bundle.files.keys().map(String::as_str).collect::<Vec<_>>(),
        vec!["diagnostics.json"]
    );
    let text = joined(&bundle);
    for prose in [
        HIDDEN_FACT,
        HIDDEN_BELIEF,
        HIDDEN_SHEET,
        "SECRET-TIDE-731",
        "Rowan",
        "You give",
        "lantern-quay-v1",
    ] {
        assert!(
            !text.contains(prose),
            "structural diagnostics leaked story/seed prose: {prose}"
        );
    }
    assert!(!text.contains(dir.0.to_str().unwrap()));
    assert!(bundle.manifest["views"]
        .as_array()
        .unwrap()
        .iter()
        .all(|v| v["status"] == "omitted_privacy" || v["status"] == "unsupported"));
}

#[test]
fn manifest_inventory_hashes_and_canonical_views_are_one_explicit_head() {
    let dir = Temp::new();
    let scope = dir.seed();
    let h = dir.host(true);
    let id = resume(&h, &scope);
    give(&h, &id, &scope, "gift");
    let bundle = h
        .inspection_snapshot(&id, &scope, 1, ExportMode::Full)
        .unwrap();
    bundle.validate().unwrap();
    assert_eq!(bundle.manifest["portable_playable"], false);
    assert_eq!(
        bundle.manifest["scope"],
        serde_json::to_value(&scope).unwrap()
    );
    assert_eq!(bundle.manifest["schema_version"], 1);
    assert!(bundle.manifest["created_at_unix_ms"].as_u64().unwrap() > 0);
    assert_eq!(
        bundle.manifest["files"].as_array().unwrap().len(),
        bundle.files.len()
    );
    for row in bundle.manifest["files"].as_array().unwrap() {
        let name = row["path"].as_str().unwrap();
        assert!(!name.contains(['/', '\\']));
        let bytes = bundle.files.get(name).unwrap();
        assert_eq!(row["bytes"].as_u64().unwrap(), bytes.len() as u64);
        assert_eq!(row["sha256"], locallore::inspection::sha256(bytes));
    }
    for view in bundle.manifest["views"].as_array().unwrap() {
        if view["status"] == "unsupported" {
            assert!(view["source_revision"].is_null());
        } else {
            assert_eq!(view["source_revision"], 1);
        }
    }
    let events = std::str::from_utf8(&bundle.files["events.jsonl"])
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str::<Value>(line).unwrap())
        .collect::<Vec<_>>();
    assert_eq!(events.len(), 1);
    assert_eq!(events[0]["sequence"], 1);
    assert_eq!(events[0]["scope"], serde_json::to_value(&scope).unwrap());
    let state: Value = serde_json::from_slice(&bundle.files["state.json"]).unwrap();
    assert_eq!(state["items"]["potion"]["owner"], "mira");
    let transcript: Value = serde_json::from_slice(
        std::str::from_utf8(&bundle.files["transcript.jsonl"])
            .unwrap()
            .lines()
            .next()
            .unwrap()
            .as_bytes(),
    )
    .unwrap();
    assert_eq!(transcript["event_ids"], json!([1]));
    assert!(transcript.get("request").is_none() && transcript.get("proposal").is_none());
}

#[test]
fn changed_export_bytes_traversal_or_budget_excess_cannot_pass_write_boundary_validation() {
    let dir = Temp::new();
    let scope = dir.seed();
    let h = dir.host(true);
    let id = resume(&h, &scope);
    let original = h
        .inspection_snapshot(&id, &scope, 0, ExportMode::Player)
        .unwrap();
    let mut changed = original.clone();
    changed.files.get_mut("state.json").unwrap().push(b' ');
    assert_eq!(changed.validate().unwrap_err(), "Integrity");
    let mut traversal = original.clone();
    traversal.manifest["files"][0]["path"] = json!("../outside.json");
    assert_eq!(traversal.validate().unwrap_err(), "Integrity");
    let mut too_large = original;
    too_large.files.insert(
        "state.json".into(),
        vec![b' '; locallore::inspection::MAX_BUNDLE_BYTES + 1],
    );
    assert_eq!(too_large.validate().unwrap_err(), "TooLarge");
    assert_eq!(
        call(&h, json!({"op":"open","session":id,"scope":scope}))["data"]["revision"],
        0
    );
}

#[test]
fn spoiler_bundle_cannot_be_relabelled_as_structural_diagnostics_or_playable_archive() {
    let dir = Temp::new();
    let scope = dir.seed();
    let h = dir.host(true);
    let id = resume(&h, &scope);
    let full = h
        .inspection_snapshot(&id, &scope, 0, ExportMode::Full)
        .unwrap();
    let mut diagnostic_label = full.clone();
    diagnostic_label.manifest["mode"] = json!("diagnostics");
    diagnostic_label.manifest["privacy"] = json!("structural_metadata_only");
    assert_eq!(
        diagnostic_label.validate().unwrap_err(),
        "Integrity",
        "spoiler files are not structural diagnostics"
    );
    let mut playable_label = full;
    playable_label.manifest["portable_playable"] = json!(true);
    assert_eq!(
        playable_label.validate().unwrap_err(),
        "Integrity",
        "inspection cannot advertise a playable archive"
    );
}
