// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen before Archive3 implementation. All new cases UNCOMPILED/UNRUN.
//! Mutations edit genuine public-API archive bytes, not accepted native authority.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
};
use locallore_storage::{
    playable_archive::{MAX_ARCHIVE_BRANCHES, MAX_ARCHIVE_BYTES},
    validate_archive, ArchiveError, Store,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-m08-archive3-hostile-{}-{}-{}",
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
    fn open(&self, name: &str) -> Store {
        Store::open(&self.0.join(name), None).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        if let Err(error) = std::fs::remove_dir_all(&self.0) {
            if !std::thread::panicking() {
                panic!("synthetic hostile fixture cleanup failed: {error}");
            }
        }
    }
}
fn seed(story: &str) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "OBSERVED_A".into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    seed
}
fn apply(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
}
fn author(store: &mut Store, parent: &Scope, name: &str, old: &str, new: &str) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: head,
        fork_revision: head,
        child_branch: name.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old.into(),
            replacement: new.into(),
        },
        reason: "PRIVATE_REASON".into(),
    };
    let plan = store.prepare_author_correction(&input, &|| false).unwrap();
    store
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .scope
}
fn fixture(temp: &Temp) -> Value {
    let mut source = temp.open("source.sqlite");
    let seed = seed("quay");
    let root = seed.scope.clone();
    source
        .create_story("Synthetic hostile archive source", seed)
        .unwrap();
    apply(
        &mut source,
        &root,
        "prefix",
        vec![Command::Wait { ticks: 1 }],
    );
    let b = author(&mut source, &root, "author-b", "OBSERVED_A", "PRIVATE_B");
    apply(
        &mut source,
        &b,
        "twice",
        vec![
            Command::Discover {
                fact: "relic-location".into(),
            },
            Command::Discover {
                fact: "relic-location".into(),
            },
        ],
    );
    let a = author(&mut source, &b, "again-a", "PRIVATE_B", "OBSERVED_A");
    apply(&mut source, &a, "after", vec![Command::Wait { ticks: 1 }]);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(archive.preview().version, 3);
    serde_json::from_slice(archive.bytes()).unwrap()
}

// Independent checksum editing only: no Core semantics, parser, import or
// observer validator is reproduced here. A hostile sender can recompute hashes.
fn canonical(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort_unstable();
            let mut out = serde_json::Map::new();
            for key in keys {
                out.insert(key.clone(), canonical(&map[key]));
            }
            Value::Object(out)
        }
        Value::Array(values) => Value::Array(values.iter().map(canonical).collect()),
        value => value.clone(),
    }
}
fn hash(value: &Value) -> String {
    format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&canonical(value)).unwrap())
    )
}
fn rehash(value: &mut Value) {
    let previous = value["integrity"]["branches"].clone();
    let rows: Vec<_> = value["payload"]["branches"].as_array().unwrap().iter().map(|branch| {
        let state = previous.as_array().unwrap().iter().find(|row| row["id"] == branch["id"])
            .map(|row| row["canonical_state_sha256"].clone()).unwrap_or(json!("0".repeat(64)));
        json!({"id":branch["id"], "records_sha256":hash(&branch["local_records"]), "canonical_state_sha256":state})
    }).collect();
    value["integrity"]["branches"] = json!(rows);
    value["integrity"]["seed_sha256"] = json!(hash(&value["payload"]["story"]["seed"]));
    value["integrity"]["payload_sha256"] = json!(hash(&value["payload"]));
}
fn branch<'a>(value: &'a mut Value, id: &str) -> &'a mut Value {
    value["payload"]["branches"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|branch| branch["id"] == id)
        .unwrap()
}
fn record<'a>(value: &'a mut Value, id: &str, index: usize) -> &'a mut Value {
    &mut branch(value, id)["local_records"][index]
}
fn reject(temp: &Temp, bytes: &[u8], allowed: &[ArchiveError], case: &str, serial: usize) {
    let mut target = temp.open(&format!("target-{serial}.sqlite"));
    let seed = seed("foreign-control");
    let scope = seed.scope.clone();
    target.create_story("Unrelated destination", seed).unwrap();
    apply(
        &mut target,
        &scope,
        "keep",
        vec![Command::Wait { ticks: 1 }],
    );
    let before = target.resume(&scope).unwrap().engine;
    match validate_archive(bytes, &|| false) {
        Err(error) => assert!(
            allowed.contains(&error),
            "{case}: unexpected closed category {error:?}"
        ),
        Ok(validated) => {
            let result = target.import_archive(validated, &|| false);
            panic!("{case}: hostile bytes obtained an import capability; target result {result:?}");
        }
    }
    let after = target.resume(&scope).unwrap().engine;
    assert_eq!(
        after.canonical_records(),
        before.canonical_records(),
        "{case}"
    );
    assert_eq!(after.canonical_bytes(), before.canonical_bytes(), "{case}");
    assert_eq!(
        after.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap(),
        "{case}"
    );
    assert_eq!(target.stories().unwrap().len(), 1, "{case}");
}
fn mutated_cases(cases: Vec<(&str, Value)>, temp: &Temp, allowed: &[ArchiveError]) {
    for (serial, (case, mut value)) in cases.into_iter().enumerate() {
        rehash(&mut value);
        reject(
            temp,
            &serde_json::to_vec(&canonical(&value)).unwrap(),
            allowed,
            case,
            serial,
        );
    }
}

#[test]
fn recomputed_hashes_do_not_admit_changed_author_or_discovery_source_wrappers() {
    let temp = Temp::new();
    let original = fixture(&temp);
    let mut cases = Vec::new();
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["record_version"] = json!(3);
    cases.push(("unknown record version", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["kind"] = json!("play");
    cases.push(("author disguised as play", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["receipt"]["input"]["reason"] = json!("CHANGED_REASON");
    // A changed reason can be internally coherent author history; make the
    // wrapper disagree with its required closed shape as well, rather than
    // pretending a checksum establishes the original author's authenticity.
    record(&mut v, "author-b", 0)["receipt"]["unrecognized"] = json!(true);
    cases.push(("extra author receipt field", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["receipt"]["input"]["operation"]["expected_proposition"] =
        json!("WRONG_BEFORE");
    cases.push(("wrong author prior value", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["receipt"]["before"] = json!({"kind":"author","source":{"original_scope":{"story":"quay","branch":"again-a"},"sequence":5}});
    cases.push(("author future before source", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["receipt"]["witnesses"] = json!(["mira"]);
    cases.push(("author grants witness knowledge", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)
        .as_object_mut()
        .unwrap()
        .remove("observations");
    cases.push(("missing private observations", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["observations"] = json!([]);
    cases.push(("discarded discovery bindings", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["observations"][0]["truth"] =
        json!({"kind":"seed_fact","seed_id":"lantern-quay-v1","fact":"relic-location"});
    cases.push(("old seed truth substituted", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["observations"][0]["truth"]["source"]["original_scope"]
        ["branch"] = json!("unrelated-sibling");
    cases.push(("sibling author source", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["observations"][0]["truth"]["source"] =
        json!({"original_scope":{"story":"quay","branch":"again-a"},"sequence":5});
    cases.push(("future author source", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["observations"][0]["event"]["sequence"] = json!(4);
    cases.push(("discovery identity conflated", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["observations"][0]["actor"] = json!("mira");
    cases.push(("observation changes actor", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["receipt"]["request"]["scope"]["story"] =
        json!("foreign-control");
    cases.push(("cross-story receipt", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 1)["receipt"]["proposal"]["commands"][0] =
        json!({"op":"wait","ticks":1});
    cases.push(("proposal disagrees with accepted discovery", v));
    let mut v = original.clone();
    let duplicate = record(&mut v, "author-b", 1).clone();
    branch(&mut v, "author-b")["local_records"]
        .as_array_mut()
        .unwrap()
        .push(duplicate);
    cases.push(("duplicate original turn", v));
    mutated_cases(cases, &temp, &[ArchiveError::Integrity]);
}

#[test]
fn recomputed_hashes_do_not_admit_broken_lineage_caps_or_retirement() {
    let temp = Temp::new();
    let original = fixture(&temp);
    let mut cases = Vec::new();
    let mut v = original.clone();
    branch(&mut v, "author-b")["parent"] = json!("author-b");
    cases.push(("cycle", v));
    let mut v = original.clone();
    branch(&mut v, "author-b")["parent"] = json!("missing");
    cases.push(("missing parent", v));
    let mut v = original.clone();
    branch(&mut v, "again-a")["fork_revision"] = json!(3);
    cases.push(("fork splits two-event discovery", v));
    let mut v = original.clone();
    branch(&mut v, "author-b")["head_revision"] = json!(3);
    cases.push(("head splits completed record", v));
    let mut v = original.clone();
    branch(&mut v, "main")["parent"] = json!("author-b");
    cases.push(("root is not root", v));
    let mut v = original.clone();
    v["payload"]["retired_branch_ids"] = json!(["main"]);
    cases.push(("retired root", v));
    let mut v = original.clone();
    v["payload"]["retired_branch_ids"] = json!(["again-a"]);
    cases.push(("unneeded physical retired leaf", v));
    let mut v = original.clone();
    v["payload"]["retired_branch_ids"] = json!(["z", "a"]);
    cases.push(("unsorted tombstones", v));
    let mut v = original.clone();
    v["payload"]["retired_branch_ids"] = json!(["gone", "gone"]);
    cases.push(("duplicate tombstones", v));
    let mut v = original.clone();
    v["payload"]["retired_branch_ids"] = json!(["../escape"]);
    cases.push(("invalid tombstone identity", v));
    let mut v = original.clone();
    v["payload"]["branches"].as_array_mut().unwrap().reverse();
    cases.push(("noncanonical branch order", v));
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["receipt"]["scope"]["branch"] = json!("again-a");
    cases.push(("rescoped author receipt", v));
    mutated_cases(cases, &temp, &[ArchiveError::Integrity]);
}

#[test]
fn exact_archive3_tuple_and_required_field_sets_are_closed() {
    let temp = Temp::new();
    let original = fixture(&temp);
    let mut cases = Vec::new();
    for (field, value) in [
        ("domain_version", json!(1)),
        ("source_database_schema_version", json!(4)),
        ("source_database_schema_version", json!(6)),
        (
            "transcript",
            json!("accepted_request_intent_and_narration_v1"),
        ),
    ] {
        let mut v = original.clone();
        v["payload"][field] = value;
        cases.push((field, v));
    }
    let mut v = original.clone();
    v["version"] = json!(4);
    cases.push(("future archive4", v));
    let mut v = original.clone();
    v["version"] = json!(1);
    cases.push(("mixed data downgraded to1", v));
    let mut v = original.clone();
    v["version"] = json!(2);
    cases.push(("mixed data downgraded to2", v));
    let mut v = original.clone();
    v["privacy"] = json!("player_only");
    cases.push(("partial-private playable claim", v));
    let mut v = original.clone();
    v["payload"]
        .as_object_mut()
        .unwrap()
        .remove("retired_branch_ids");
    cases.push(("missing required3 retirement array", v));
    let mut v = original.clone();
    v["payload"]["retired_branch_ids"] = Value::Null;
    cases.push(("null3 retirement array", v));
    let mut v = original.clone();
    v["payload"]["unexpected"] = json!({"path":"../payload"});
    cases.push(("unknown payload field", v));
    let mut v = original.clone();
    branch(&mut v, "author-b")["local_receipts"] = json!([]);
    cases.push(("ambiguous record and receipt fields", v));
    mutated_cases(
        cases,
        &temp,
        &[ArchiveError::Unsupported, ArchiveError::Malformed],
    );
}

#[test]
fn archive3_domain2_claim_requires_real_author_history_and_exact_projection_digest() {
    let temp = Temp::new();
    let mut source = temp.open("ordinary.sqlite");
    let seed = seed("quay");
    let root = seed.scope.clone();
    source.create_story("Ordinary source", seed).unwrap();
    apply(
        &mut source,
        &root,
        "ordinary",
        vec![Command::Wait { ticks: 1 }],
    );
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(archive.preview().version, 1);
    let mut value: Value = serde_json::from_slice(archive.bytes()).unwrap();
    value["version"] = json!(3);
    value["payload"]["domain_version"] = json!(2);
    value["payload"]["transcript"] = json!("accepted_canonical_records_v2");
    value["payload"]["retired_branch_ids"] = json!([]);
    for b in value["payload"]["branches"].as_array_mut().unwrap() {
        let local = b.as_object_mut().unwrap().remove("local_receipts").unwrap();
        b["local_records"] = local;
    }
    rehash(&mut value);
    reject(
        &temp,
        &serde_json::to_vec(&value).unwrap(),
        &[ArchiveError::Unsupported, ArchiveError::Integrity],
        "Domain1 relabeled3",
        0,
    );
    let mut actual = fixture(&temp);
    actual["integrity"]["branches"][0]["canonical_state_sha256"] = json!("0".repeat(64));
    reject(
        &temp,
        &serde_json::to_vec(&actual).unwrap(),
        &[ArchiveError::Integrity],
        "wrong replayed projection digest",
        1,
    );
}

#[test]
fn invalid_bytes_duplicate_keys_and_untrusted_payload_hashes_never_grant_import() {
    let temp = Temp::new();
    let value = fixture(&temp);
    let bytes = serde_json::to_vec(&canonical(&value)).unwrap();
    let duplicate = format!(
        "{{\"version\":3,{}",
        std::str::from_utf8(&bytes)
            .unwrap()
            .strip_prefix('{')
            .unwrap()
    )
    .into_bytes();
    let mut trailing = bytes.clone();
    trailing.extend_from_slice(b"{}");
    let mut wrong_hash = value;
    wrong_hash["integrity"]["payload_sha256"] = json!("0".repeat(64));
    let variants = [
        bytes[..bytes.len() - 1].to_vec(),
        vec![0xff, 0xfe],
        duplicate,
        trailing,
        serde_json::to_vec(&wrong_hash).unwrap(),
    ];
    for (serial, malformed) in variants.into_iter().enumerate() {
        reject(
            &temp,
            &malformed,
            &[ArchiveError::Malformed, ArchiveError::Integrity],
            "malformed bytes/hash",
            serial,
        );
    }
}

#[test]
fn enforced_archive3_caps_cover_complete_private_wrappers_counts_and_envelope() {
    let temp = Temp::new();
    let original = fixture(&temp);
    let mut cases = Vec::new();
    let mut v = original.clone();
    record(&mut v, "author-b", 0)["receipt"]["input"]["reason"] =
        json!("x".repeat(MAX_RECEIPT_BYTES + 1));
    cases.push(("complete author wrapper exceeds cap", v));
    let mut v = original.clone();
    let item = record(&mut v, "author-b", 0).clone();
    branch(&mut v, "author-b")["local_records"] = json!(vec![item; MAX_HISTORY_RECEIPTS + 1]);
    cases.push(("canonical count includes authors", v));
    let mut v = original.clone();
    let template = branch(&mut v, "author-b").clone();
    let mut branches = Vec::new();
    for n in 0..=MAX_ARCHIVE_BRANCHES {
        let mut b = template.clone();
        b["id"] = json!(format!("b{n:02}"));
        branches.push(b);
    }
    v["payload"]["branches"] = json!(branches);
    cases.push(("too many physical branches", v));
    let mut v = original.clone();
    v["payload"]["retired_branch_ids"] =
        json!((0..257).map(|n| format!("gone-{n:03}")).collect::<Vec<_>>());
    cases.push(("too many reserved identities", v));
    mutated_cases(cases, &temp, &[ArchiveError::TooLarge]);
    reject(
        &temp,
        &vec![b' '; MAX_ARCHIVE_BYTES + 1],
        &[ArchiveError::TooLarge],
        "wire byte cap",
        100,
    );
}
