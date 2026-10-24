// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen before Archive3 implementation. All new cases UNCOMPILED/UNRUN at freeze.
//! Real public Store/Core histories; no provider, forged receipt or SQL writer.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord},
    contracts::*,
    engine::Engine,
};
use locallore_storage::{
    validate_archive, ArchiveError, ForkRequest, StorageError, Store, TurnError,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    cell::Cell,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-m08-archive3-{}-{}-{}",
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
                panic!("synthetic Archive3 cleanup failed: {error}");
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
fn create(store: &mut Store, story: &str) -> Scope {
    let seed = seed(story);
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic mixed canonical history", seed)
        .unwrap();
    scope
}
fn apply(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap()
}
fn wait(store: &mut Store, scope: &Scope, key: &str) {
    apply(store, scope, key, vec![Command::Wait { ticks: 1 }]);
}
fn fork(store: &mut Store, parent: &Scope, name: &str, at: u64) -> Scope {
    let expected_parent_revision = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: name.into(),
                expected_parent_revision,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn author(
    store: &mut Store,
    parent: &Scope,
    name: &str,
    old: &str,
    new: &str,
) -> (Scope, AuthorCorrectionInputV1) {
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
        reason: format!("PRIVATE_AUTHOR_REASON_{name}"),
    };
    let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
    let result = store.apply_author_correction(&prepared, &|| false).unwrap();
    assert!(result.created);
    (result.scope, input)
}
fn retire(store: &mut Store, scope: &Scope) -> Option<u64> {
    let head = store.resume(scope).unwrap().engine.revision();
    let plan = store
        .prepare_branch_deletion(scope, head, &|| false)
        .unwrap();
    store
        .delete_branch(plan, &|| false)
        .unwrap()
        .retained_through_revision
}
fn absent(store: &mut Store, scope: &Scope) {
    assert!(matches!(
        store.resume(scope),
        Err(TurnError::Storage(StorageError::NotFound))
    ))
}
fn equal_engine(actual: &Engine, expected: &Engine) {
    assert_eq!(actual.scope(), expected.scope());
    assert_eq!(actual.seed(), expected.seed());
    assert_eq!(actual.revision(), expected.revision());
    assert_eq!(actual.domain_version(), expected.domain_version());
    assert_eq!(actual.canonical_records(), expected.canonical_records());
    assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        expected.accepted_history_basis().unwrap()
    );
    for actor in ["player", "mira", "sable"] {
        assert_eq!(
            actual
                .character_context_v2(actor, actual.scope(), actual.revision())
                .unwrap(),
            expected
                .character_context_v2(actor, expected.scope(), expected.revision())
                .unwrap()
        );
    }
}
fn foreign(store: &mut Store) -> (Scope, Engine) {
    let scope = create(store, "unrelated-foreign");
    wait(store, &scope, "keep");
    let engine = store.resume(&scope).unwrap().engine;
    (scope, engine)
}
fn no_import(store: &mut Store, control: &Scope, before: &Engine) {
    equal_engine(&store.resume(control).unwrap().engine, before);
    assert_eq!(store.stories().unwrap().len(), 1);
    assert!(matches!(
        store.resume(&Scope {
            story: "quay".into(),
            branch: "main".into()
        }),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
}

#[test]
fn full_mixed_roundtrip_preserves_sources_a_b_a_native_bases_and_original_turn_recovery() {
    let temp = Temp::new();
    let mut source = temp.open("source.sqlite");
    let root = create(&mut source, "quay");
    wait(&mut source, &root, "prefix");
    let sibling = fork(&mut source, &root, "sibling", 1);
    apply(
        &mut source,
        &sibling,
        "private-sibling",
        vec![Command::Say {
            text: "SIBLING_PRIVATE_CANARY".into(),
            audience: ["mira".into()].into(),
        }],
    );
    let (b, input_b) = author(&mut source, &root, "author-b", "OBSERVED_A", "PRIVATE_B");
    let discovery_b = apply(
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
    let (a, input_a) = author(&mut source, &b, "again-a", "PRIVATE_B", "OBSERVED_A");
    let before_rediscovery = source.resume(&a).unwrap().engine;
    assert_eq!(
        before_rediscovery.observed_facts("player", &a, 5).unwrap()["relic-location"].proposition,
        "PRIVATE_B"
    );
    let discovery_a = apply(
        &mut source,
        &a,
        "rediscover-a",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    wait(&mut source, &root, "later-parent");
    let scopes = [&root, &sibling, &b, &a];
    let originals: Vec<_> = scopes
        .iter()
        .map(|scope| source.resume(scope).unwrap().engine)
        .collect();
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(archive.preview().version, 3);
    assert_eq!(archive.preview().committed_turns, 7);
    assert!(!archive.preview().noncommitted_workflow_transferred);
    let preview = serde_json::to_value(archive.preview()).unwrap();
    assert!(preview.get("retired_branch_ids").is_none());
    let raw: Value = serde_json::from_slice(archive.bytes()).unwrap();
    assert_eq!(raw["payload"]["domain_version"], 2);
    assert_eq!(raw["payload"]["source_database_schema_version"], 5);
    assert_eq!(
        raw["payload"]["transcript"],
        "accepted_canonical_records_v2"
    );
    assert_eq!(raw["payload"]["retired_branch_ids"], json!([]));
    let bytes = archive.bytes().to_vec();
    let text = std::str::from_utf8(&bytes).unwrap();
    assert!(
        text.contains("PRIVATE_AUTHOR_REASON_author-b") && text.contains("SIBLING_PRIVATE_CANARY")
    );
    assert!(
        raw["payload"]["branches"]
            .as_array()
            .unwrap()
            .iter()
            .all(|branch| branch.get("local_receipts").is_none()
                && branch["local_records"].is_array())
    );
    let mut target = temp.open("target.sqlite");
    let (control, kept) = foreign(&mut target);
    let imported = target
        .import_archive(validate_archive(&bytes, &|| false).unwrap(), &|| false)
        .unwrap();
    assert_eq!(imported.root, root);
    assert_eq!(imported.branches, 4);
    assert_eq!(imported.committed_turns, 7);
    equal_engine(&target.resume(&control).unwrap().engine, &kept);
    for (scope, original) in scopes.iter().zip(&originals) {
        equal_engine(&target.resume(scope).unwrap().engine, original);
    }
    for input in [&input_b, &input_a] {
        assert!(
            !target
                .lookup_author_correction(input, &|| false)
                .unwrap()
                .unwrap()
                .created
        );
    }
    for (scope, receipt) in [(&b, &discovery_b), (&a, &discovery_a)] {
        assert_eq!(
            target
                .lookup_turn(scope, &receipt.request().turn)
                .unwrap()
                .receipt
                .as_ref(),
            Some(receipt)
        );
        assert_eq!(
            target
                .begin_turn(receipt.request())
                .unwrap()
                .receipt
                .as_ref(),
            Some(receipt)
        );
        assert_eq!(target.commit_prepared(receipt).unwrap(), *receipt);
    }
    let e = target.resume(&a).unwrap().engine;
    let context = e.character_context_v2("player", &a, e.revision()).unwrap();
    let observed: Vec<_> = context
        .observations
        .iter()
        .filter_map(|row| row.discovery.as_ref())
        .collect();
    assert_eq!(
        observed
            .iter()
            .map(|v| v.proposition.as_str())
            .collect::<Vec<_>>(),
        ["PRIVATE_B", "PRIVATE_B", "OBSERVED_A"]
    );
    assert_ne!(observed[0].observation, observed[1].observation);
    let actor_text =
        serde_json::to_string(&e.character_context_v2("mira", &a, e.revision()).unwrap()).unwrap();
    assert!(
        !actor_text.contains("PRIVATE_B")
            && !actor_text.contains("PRIVATE_AUTHOR_REASON")
            && !actor_text.contains("SIBLING_PRIVATE_CANARY")
    );
    assert_eq!(e.canonical_records().len(), 5);
    assert_eq!(e.receipts().len(), 3);
    assert!(matches!(
        e.canonical_records()[1],
        CanonicalRecord::AuthorV1(_)
    ));
    assert_eq!(
        target
            .export_archive(&root.story, &|| false)
            .unwrap()
            .bytes(),
        bytes
    );
    drop(target);
    let mut reopened = temp.open("target.sqlite");
    for (scope, original) in scopes.iter().zip(&originals) {
        equal_engine(&reopened.resume(scope).unwrap().engine, original);
    }
    assert_eq!(
        reopened
            .export_archive(&root.story, &|| false)
            .unwrap()
            .bytes(),
        bytes
    );
    wait(&mut reopened, &a, "continue-once");
    assert_eq!(reopened.resume(&a).unwrap().engine.revision(), 7);
    equal_engine(&reopened.resume(&control).unwrap().engine, &kept);
}

#[test]
fn equal_projection_and_head_cannot_erase_different_private_author_sources() {
    let temp = Temp::new();
    let mut left = temp.open("left.sqlite");
    let mut right = temp.open("right.sqlite");
    let root_left = create(&mut left, "quay");
    let root_right = create(&mut right, "quay");
    let (a, _) = author(
        &mut left,
        &root_left,
        "same-child",
        "OBSERVED_A",
        "PRIVATE_B",
    );
    let (b, _) = author(
        &mut right,
        &root_right,
        "same-child",
        "OBSERVED_A",
        "PRIVATE_C",
    );
    let left_engine = left.resume(&a).unwrap().engine;
    let right_engine = right.resume(&b).unwrap().engine;
    assert_eq!(a, b);
    assert_eq!(left_engine.revision(), right_engine.revision());
    assert_eq!(
        left_engine.canonical_bytes(),
        right_engine.canonical_bytes()
    );
    assert_ne!(
        left_engine.canonical_records(),
        right_engine.canonical_records()
    );
    assert_ne!(
        left_engine.accepted_history_basis().unwrap(),
        right_engine.accepted_history_basis().unwrap()
    );
    let left_archive = left.export_archive(&a.story, &|| false).unwrap();
    let right_archive = right.export_archive(&b.story, &|| false).unwrap();
    assert_ne!(
        left_archive.preview().payload_sha256,
        right_archive.preview().payload_sha256
    );
    let mut x = temp.open("x.sqlite");
    let mut y = temp.open("y.sqlite");
    x.import_archive(
        validate_archive(left_archive.bytes(), &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    y.import_archive(
        validate_archive(right_archive.bytes(), &|| false).unwrap(),
        &|| false,
    )
    .unwrap();
    equal_engine(&x.resume(&a).unwrap().engine, &left_engine);
    equal_engine(&y.resume(&b).unwrap().engine, &right_engine);
}

#[test]
fn actual_retirement_preserves_author_prefix_prebirth_rewind_and_collected_identity() {
    let temp = Temp::new();
    let mut source = temp.open("retained.sqlite");
    let root = create(&mut source, "quay");
    for n in 0..4 {
        wait(&mut source, &root, &format!("prefix-{n}"));
    }
    let (born, _) = author(
        &mut source,
        &root,
        "born-at-four",
        "OBSERVED_A",
        "REMOVED_B",
    );
    let child = fork(&mut source, &born, "rewound-to-one", 1);
    wait(&mut source, &child, "child-local");
    let (kept_author, _) = author(&mut source, &root, "kept-author", "OBSERVED_A", "KEPT_C");
    let descendant = fork(&mut source, &kept_author, "inherits-author", 5);
    wait(&mut source, &descendant, "after-author");
    let (gone, _) = author(&mut source, &root, "collected", "OBSERVED_A", "REMOVED_D");
    assert_eq!(retire(&mut source, &born), Some(4));
    assert_eq!(retire(&mut source, &kept_author), Some(5));
    assert_eq!(retire(&mut source, &gone), None);
    let originals = [
        source.resume(&root).unwrap().engine,
        source.resume(&child).unwrap().engine,
        source.resume(&descendant).unwrap().engine,
    ];
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(archive.preview().version, 3);
    assert_eq!(
        archive.preview().retired_branch_ids,
        ["born-at-four", "collected", "kept-author"]
    );
    assert_eq!(archive.preview().branch_heads.get("born-at-four"), Some(&4));
    assert_eq!(archive.preview().branch_heads.get("kept-author"), Some(&5));
    assert!(!archive.preview().branch_heads.contains_key("collected"));
    let raw: Value = serde_json::from_slice(archive.bytes()).unwrap();
    assert_eq!(
        raw["payload"]["retired_branch_ids"],
        json!(["born-at-four", "collected", "kept-author"])
    );
    assert!(!std::str::from_utf8(archive.bytes())
        .unwrap()
        .contains("REMOVED_B"));
    assert!(!std::str::from_utf8(archive.bytes())
        .unwrap()
        .contains("REMOVED_D"));
    let mut target = temp.open("retained-target.sqlite");
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    for (scope, original) in [&root, &child, &descendant].into_iter().zip(&originals) {
        equal_engine(&target.resume(scope).unwrap().engine, original);
    }
    for retired in [&born, &kept_author, &gone] {
        absent(&mut target, retired);
    }
    assert_eq!(
        target
            .export_archive(&root.story, &|| false)
            .unwrap()
            .bytes(),
        archive.bytes()
    );
    drop(target);
    let mut target = temp.open("retained-target.sqlite");
    equal_engine(&target.resume(&descendant).unwrap().engine, &originals[2]);
    for retired in [&born, &kept_author, &gone] {
        absent(&mut target, retired);
    }
}

#[test]
fn cancellation_panic_and_progressive_import_polls_leave_foreign_canon_unchanged() {
    let temp = Temp::new();
    let mut source = temp.open("cancel-source.sqlite");
    let root = create(&mut source, "quay");
    let (child, _) = author(&mut source, &root, "child", "OBSERVED_A", "PRIVATE_B");
    wait(&mut source, &child, "after");
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    assert!(matches!(
        validate_archive(archive.bytes(), &|| true),
        Err(ArchiveError::Cancelled)
    ));
    assert!(matches!(
        validate_archive(archive.bytes(), &|| panic!(
            "synthetic cancellation callback"
        )),
        Err(ArchiveError::Cancelled)
    ));
    let mut successful = temp.open("poll-count.sqlite");
    foreign(&mut successful);
    let polls = Cell::new(0usize);
    successful
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| {
                polls.set(polls.get() + 1);
                false
            },
        )
        .unwrap();
    let total = polls.get();
    assert!(total > 4, "must exercise intermediate import checks");
    let mut stops = vec![1, 2, total / 2, total - 1, total];
    stops.sort_unstable();
    stops.dedup();
    for (n, stop) in stops.into_iter().enumerate() {
        let mut target = temp.open(&format!("cancel-{n}.sqlite"));
        let (control, before) = foreign(&mut target);
        let seen = Cell::new(0usize);
        let result = target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| {
                seen.set(seen.get() + 1);
                seen.get() >= stop
            },
        );
        assert_eq!(result, Err(ArchiveError::Cancelled), "stop {stop}/{total}");
        assert_eq!(seen.get(), stop);
        no_import(&mut target, &control, &before);
    }
    let mut target = temp.open("panic-import.sqlite");
    let (control, before) = foreign(&mut target);
    let seen = Cell::new(0usize);
    assert_eq!(
        target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| {
                seen.set(seen.get() + 1);
                if seen.get() == total / 2 {
                    panic!("synthetic mid-import panic");
                }
                false
            }
        ),
        Err(ArchiveError::Cancelled)
    );
    no_import(&mut target, &control, &before);
}

#[test]
fn winning_import_reopen_and_identical_or_divergent_identity_retry_never_overwrite() {
    let temp = Temp::new();
    let mut source = temp.open("conflict-source.sqlite");
    let root = create(&mut source, "quay");
    let (child, _) = author(&mut source, &root, "child", "OBSERVED_A", "PRIVATE_B");
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let mut target = temp.open("conflict-target.sqlite");
    let (control, kept) = foreign(&mut target);
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let winning = target.resume(&child).unwrap().engine;
    drop(target);
    let mut target = temp.open("conflict-target.sqlite");
    assert_eq!(
        target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false
        ),
        Err(ArchiveError::Conflict)
    );
    wait(&mut source, &child, "source-continued");
    let divergent = source.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(
        target.import_archive(
            validate_archive(divergent.bytes(), &|| false).unwrap(),
            &|| false
        ),
        Err(ArchiveError::Conflict)
    );
    equal_engine(&target.resume(&child).unwrap().engine, &winning);
    equal_engine(&target.resume(&control).unwrap().engine, &kept);
    assert_eq!(target.stories().unwrap().len(), 2);
}

#[test]
fn immutable_archive1_and2_assets_keep_original_bytes_and_domain1_export_selection() {
    let assets: [(&[u8], &str, u16); 3] = [
        (include_bytes!("../../../apps/android/app/src/androidTest/assets/platform-roundtrip-v1/windows-origin.json"), "ac77f1144db9de68c0d01241949f85f21660da6526b241cb9e947277b3c27fbb", 1),
        (include_bytes!("../../../apps/android/app/src/androidTest/assets/platform-roundtrip-v1/windows-continued.json"), "31f7bdb6904d8759186f0586b80c79b0346d9e9d03f04c015c409a1f1670ec6a", 1),
        (include_bytes!("../../../apps/android/app/src/androidTest/assets/parent-retention-v1.json"), "5cc8eea595258669c1ebb04a15c0a8d642e43be0e534a35cd776920883d62dc7", 2),
    ];
    let temp = Temp::new();
    for (n, (bytes, expected_hash, version)) in assets.into_iter().enumerate() {
        assert_eq!(format!("{:x}", Sha256::digest(bytes)), expected_hash);
        let validated = validate_archive(bytes, &|| false).unwrap();
        assert_eq!(validated.preview().version, version);
        let expected = validated.preview().clone();
        let mut target = temp.open(&format!("old-{n}.sqlite"));
        target.import_archive(validated, &|| false).unwrap();
        let exported = target
            .export_archive(&expected.story_id, &|| false)
            .unwrap();
        assert_eq!(exported.preview().version, version);
        // Current export reports actual DB5. Do not rewrite the historical asset
        // or falsely require old source-schema metadata from the current Store.
        let raw: Value = serde_json::from_slice(exported.bytes()).unwrap();
        assert_eq!(raw["payload"]["domain_version"], 1);
        assert_eq!(raw["payload"]["source_database_schema_version"], 5);
        assert!(raw["payload"]["branches"]
            .as_array()
            .unwrap()
            .iter()
            .all(|b| b.get("local_records").is_none() && b["local_receipts"].is_array()));
        let historical: Value = serde_json::from_slice(bytes).unwrap();
        let mut normalized = raw;
        // Exactly the truthful source-schema field and its dependent payload
        // digest differ. Every receipt, lineage, projection digest and other
        // historical field must remain equal; original asset bytes stay pinned.
        normalized["payload"]["source_database_schema_version"] =
            historical["payload"]["source_database_schema_version"].clone();
        normalized["integrity"]["payload_sha256"] =
            historical["integrity"]["payload_sha256"].clone();
        assert_eq!(normalized, historical);
        for (branch, head) in &expected.branch_heads {
            let scope = Scope {
                story: expected.story_id.clone(),
                branch: branch.clone(),
            };
            if expected.retired_branch_ids.contains(branch) {
                absent(&mut target, &scope);
            } else {
                let engine = target.resume(&scope).unwrap().engine;
                assert_eq!(engine.revision(), *head);
                assert_eq!(engine.domain_version(), 1);
            }
        }
    }
}

#[test]
fn maximal_escaped_author_fields_roundtrip_full_wrapper_and_private_reason() {
    let temp = Temp::new();
    let mut source = temp.open("escaped.sqlite");
    let root = create(&mut source, "quay");
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: root.clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: "escaped".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "OBSERVED_A".into(),
            replacement: "\u{0000}".repeat(2048),
        },
        reason: "\u{0001}".repeat(2048),
    };
    let plan = source.prepare_author_correction(&input, &|| false).unwrap();
    let child = source
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .scope;
    let original = source.resume(&child).unwrap().engine;
    let encoded = serde_json::to_vec(original.canonical_records().last().unwrap()).unwrap();
    assert!(encoded.len() > 24576 && encoded.len() <= MAX_RECEIPT_BYTES);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let mut target = temp.open("escaped-target.sqlite");
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    equal_engine(&target.resume(&child).unwrap().engine, &original);
    assert!(
        !target
            .lookup_author_correction(&input, &|| false)
            .unwrap()
            .unwrap()
            .created
    );
}
