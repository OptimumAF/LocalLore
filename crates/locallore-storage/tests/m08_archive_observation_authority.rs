// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Original same-value, existing-source Archive3 adversary.
//! Public Store histories generate both complete wrappers; only hostile archive
//! bytes are substituted. No accepted native type, SQL row or capability forged.
use locallore::{author_correction::*, contracts::*, engine::Engine};
use locallore_storage::{validate_archive, ArchiveError, ForkRequest, Store};
use rusqlite::{types::Value as SqlValue, Connection, OpenFlags};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    io::Write,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

const A: &str = "B97_A_ORIGINAL_OBSERVATION";
const B: &str = "B97_B_IDENTICAL_VALUE_DIFFERENT_AUTHORITY";
const C: &str = "B97_C_LATER_UNOBSERVED_WORLD";
static NEXT: AtomicU64 = AtomicU64::new(0);

struct Retained(PathBuf);
impl Retained {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let directory = parent.join(format!(
            "locallore-m08-observation-authority-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        Self(directory)
    }
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
    fn open(&self, name: &str) -> Store {
        Store::open(&self.path(name), None).unwrap()
    }
}
// Retain all unique synthetic DBs. Root's local runner owns the physical D gate.

fn seed(story: &str) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    let player = seed.player.clone();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert(player);
    fact.known_by.insert("mira".into());
    seed
}

fn append(store: &mut Store, scope: &Scope, turn: &str, command: Command) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(vec![command]));
    let receipt = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
}

fn author(store: &mut Store, parent: &Scope, child: &str, old: &str, new: &str) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: head,
        fork_revision: head,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old.into(),
            replacement: new.into(),
        },
        reason: format!("B97_PRIVATE_REASON_{child}"),
    };
    let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
    store
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .scope
}

fn canonical(value: &Value) -> Value {
    match value {
        Value::Object(values) => {
            let mut names: Vec<_> = values.keys().collect();
            names.sort_unstable();
            let mut result = serde_json::Map::new();
            for name in names {
                result.insert(name.clone(), canonical(&values[name]));
            }
            Value::Object(result)
        }
        Value::Array(values) => Value::Array(values.iter().map(canonical).collect()),
        value => value.clone(),
    }
}
fn digest(value: &Value) -> String {
    format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&canonical(value)).unwrap())
    )
}
fn branch<'a>(value: &'a Value, id: &str) -> &'a Value {
    value["payload"]["branches"]
        .as_array()
        .unwrap()
        .iter()
        .find(|v| v["id"] == id)
        .unwrap()
}
fn wrapper(value: &Value) -> &Value {
    &branch(value, "observer")["local_records"][0]
}

struct Scenario {
    archive: Value,
    bytes: Vec<u8>,
    parent: Engine,
    observed: Engine,
    selected: Engine,
    states: BTreeMap<String, String>,
}

fn scenario(temp: &Retained, file: &str, parent_id: &str) -> Scenario {
    let mut store = temp.open(file);
    let seed = seed("archive-authority");
    let root = seed.scope.clone();
    store
        .create_story("Synthetic existing-source authority", seed)
        .unwrap();
    let a = author(&mut store, &root, "source-a", A, B);
    let b = author(&mut store, &root, "source-b", A, B);
    let chosen = if parent_id == "source-a" { &a } else { &b };
    let parent = store.resume(chosen).unwrap().engine;
    let observer = store
        .fork_branch(
            &ForkRequest {
                parent: chosen.clone(),
                child_branch: "observer".into(),
                expected_parent_revision: 1,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    append(
        &mut store,
        &observer,
        "same-discovery",
        Command::Discover {
            fact: "relic-location".into(),
        },
    );
    let observed = store.resume(&observer).unwrap().engine;
    let selected_scope = author(&mut store, &observer, "selected", B, C);
    let selected = store.resume(&selected_scope).unwrap().engine;
    let mut states = BTreeMap::new();
    for scope in [&root, &a, &b, &observer, &selected_scope] {
        let engine = store.resume(scope).unwrap().engine;
        states.insert(
            scope.branch.clone(),
            format!("{:x}", Sha256::digest(engine.canonical_bytes())),
        );
    }
    let exported = store.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(exported.preview().version, 3);
    let archive: Value = serde_json::from_slice(exported.bytes()).unwrap();
    for row in archive["integrity"]["branches"].as_array().unwrap() {
        assert_eq!(
            row["canonical_state_sha256"].as_str().unwrap(),
            states[row["id"].as_str().unwrap()]
        );
    }
    let bytes = exported.bytes().to_vec();
    Scenario {
        archive,
        bytes,
        parent,
        observed,
        selected,
        states,
    }
}

fn retain(path: &Path, bytes: &[u8]) {
    assert!(
        bytes.len() <= 512 * 1024,
        "bounded synthetic archive fixture"
    );
    let mut output = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    output.write_all(bytes).unwrap();
    output.sync_all().unwrap();
}

fn rehash_structural(value: &mut Value) {
    let mut rows = value["integrity"]["branches"].as_array().unwrap().clone();
    for row in &mut rows {
        let id = row["id"].as_str().unwrap().to_owned();
        row["records_sha256"] = json!(digest(&branch(value, &id)["local_records"]));
    }
    value["integrity"]["branches"] = json!(rows);
    value["integrity"]["seed_sha256"] = json!(digest(&value["payload"]["story"]["seed"]));
    value["integrity"]["payload_sha256"] = json!(digest(&value["payload"]));
}
fn assert_structural_hashes(value: &Value) {
    assert_eq!(
        value["integrity"]["payload_sha256"],
        digest(&value["payload"])
    );
    assert_eq!(
        value["integrity"]["seed_sha256"],
        digest(&value["payload"]["story"]["seed"])
    );
    for row in value["integrity"]["branches"].as_array().unwrap() {
        assert_eq!(
            row["records_sha256"],
            digest(&branch(value, row["id"].as_str().unwrap())["local_records"])
        );
    }
}

// Reads every application table and every column; no SQL writes or hand-made
// canonical rows. Snapshot includes the unrelated story AND its pending draft.
fn all_rows(path: &Path) -> Vec<(String, Vec<Vec<SqlValue>>)> {
    let db = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
    let names: Vec<String> = db.prepare("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        .unwrap().query_map([], |r| r.get(0)).unwrap().map(Result::unwrap).collect();
    names
        .into_iter()
        .map(|name| {
            let quoted = name.replace('"', "\"\"");
            let mut statement = db.prepare(&format!("SELECT * FROM \"{quoted}\"")).unwrap();
            let width = statement.column_count();
            let mut rows: Vec<Vec<SqlValue>> = statement
                .query_map([], |r| (0..width).map(|n| r.get(n)).collect())
                .unwrap()
                .map(Result::unwrap)
                .collect();
            rows.sort_by_key(|r| format!("{r:?}"));
            (name, rows)
        })
        .collect()
}

#[test]
fn genuine_wrapper_from_existing_same_value_sibling_cannot_authorize_a_recipient_observation() {
    let temp = Retained::new();
    let recipient = scenario(&temp, "recipient.sqlite", "source-a");
    let donor = scenario(&temp, "donor.sqlite", "source-b");
    // Both histories, including both sibling B-author sources, are genuinely
    // valid. Final C projections coincide, while accepted evidence differs.
    assert_eq!(recipient.selected.revision(), 3);
    assert_eq!(
        recipient.selected.canonical_bytes(),
        donor.selected.canonical_bytes()
    );
    assert_ne!(
        recipient.selected.canonical_records(),
        donor.selected.canonical_records()
    );
    for (scenario, filename, archive_name) in [
        (
            &recipient,
            "positive-recipient.sqlite",
            "valid-recipient.archive3.json",
        ),
        (&donor, "positive-donor.sqlite", "valid-donor.archive3.json"),
    ] {
        assert_structural_hashes(&scenario.archive);
        let bytes = serde_json::to_vec(&canonical(&scenario.archive)).unwrap();
        assert_eq!(bytes, scenario.bytes);
        retain(&temp.path(archive_name), &bytes);
        let validated = validate_archive(&bytes, &|| false).unwrap();
        let mut target = temp.open(filename);
        target.import_archive(validated, &|| false).unwrap();
        let loaded = target.resume(scenario.selected.scope()).unwrap().engine;
        assert_eq!(
            loaded.canonical_records(),
            scenario.selected.canonical_records()
        );
        assert_eq!(
            loaded.canonical_bytes(),
            scenario.selected.canonical_bytes()
        );
    }
    let left = wrapper(&recipient.archive);
    let right = wrapper(&donor.archive);
    assert_eq!(left["receipt"], right["receipt"]); // Scope/turn/seq/outcome all agree.
    assert_eq!(left["observations"].as_array().unwrap().len(), 1);
    assert_eq!(right["observations"].as_array().unwrap().len(), 1);
    let lobs = &left["observations"][0];
    let robs = &right["observations"][0];
    for field in ["event", "actor", "fact"] {
        assert_eq!(lobs[field], robs[field]);
    }
    assert_eq!(lobs["truth"]["source"]["sequence"], 1);
    assert_eq!(robs["truth"]["source"]["sequence"], 1);
    assert_eq!(
        lobs["truth"]["source"]["original_scope"]["branch"],
        "source-a"
    );
    assert_eq!(
        robs["truth"]["source"]["original_scope"]["branch"],
        "source-b"
    );
    assert_ne!(left, right);
    assert_eq!(
        branch(&recipient.archive, "source-b")["local_records"],
        branch(&donor.archive, "source-b")["local_records"]
    );
    assert_eq!(
        recipient
            .parent
            .effective_fact("relic-location")
            .unwrap()
            .proposition,
        B
    );
    assert_eq!(
        donor
            .parent
            .effective_fact("relic-location")
            .unwrap()
            .proposition,
        B
    );

    let prefix = recipient.parent.fork("observer", 1).unwrap();
    let restored = prefix
        .restore_continuation(&[serde_json::to_string(left).unwrap()])
        .unwrap();
    assert_eq!(
        restored.canonical_records(),
        recipient.observed.canonical_records()
    );
    // Core replay has no archive checksum comparison: this isolates semantic
    // observation authority before the later canonical-state checksum gate.
    assert!(matches!(
        prefix.restore_continuation(&[serde_json::to_string(right).unwrap()]),
        Err(Error::CorruptHistory)
    ));
    assert_eq!(prefix.revision(), 1); // Failed restore returns no partial engine.

    let mut forged = recipient.archive.clone();
    forged["payload"]["branches"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|v| v["id"] == "observer")
        .unwrap()["local_records"][0] = right.clone();
    rehash_structural(&mut forged);
    assert_structural_hashes(&forged);
    for row in forged["integrity"]["branches"].as_array().unwrap() {
        // These are authentic original projection checksums, deliberately not
        // claimed to be a computed valid state for the impossible history.
        assert_eq!(
            row["canonical_state_sha256"].as_str().unwrap(),
            recipient.states[row["id"].as_str().unwrap()]
        );
    }
    let bytes = serde_json::to_vec(&canonical(&forged)).unwrap();
    retain(&temp.path("grafted-existing-source.archive3.json"), &bytes);
    let mut destination = temp.open("existing-destination.sqlite");
    let control_seed = seed("unrelated-control");
    let control = control_seed.scope.clone();
    destination
        .create_story("Retain unrelated destination", control_seed)
        .unwrap();
    append(
        &mut destination,
        &control,
        "keep",
        Command::Wait { ticks: 1 },
    );
    let before_engine = destination.resume(&control).unwrap().engine;
    let pending = before_engine.request(
        "preserved-pending",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    destination.begin_turn(&pending).unwrap();
    let before_rows = all_rows(&temp.path("existing-destination.sqlite"));
    match validate_archive(&bytes, &|| false) {
        Err(error) => assert_eq!(error, ArchiveError::Integrity),
        Ok(_) => panic!("impossible observation obtained a validated import capability"),
    }
    assert_eq!(
        all_rows(&temp.path("existing-destination.sqlite")),
        before_rows
    );
    let after = destination.resume(&control).unwrap().engine;
    assert_eq!(after.canonical_records(), before_engine.canonical_records());
    assert_eq!(after.canonical_bytes(), before_engine.canonical_bytes());
    assert_eq!(destination.stories().unwrap().len(), 1);
    // Validation refused before import: this is no-write admission evidence,
    // NOT an exercised SQLite mid-write rollback or crash-recovery claim.
    assert!(temp.0.is_dir());
}
