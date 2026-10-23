// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use super::*;
use crate::archive_capacity_fixture::{run, with_local_cap};
use locallore::{contracts::*, engine::Engine};
use std::{
    fs,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
    time::{SystemTime, UNIX_EPOCH},
};
static NEXT: AtomicU64 = AtomicU64::new(0);
fn root() -> PathBuf {
    let base = std::env::temp_dir().canonicalize().unwrap().join(format!(
        "locallore-archive-full-{}-{}",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::SeqCst)
    ));
    fs::create_dir(&base).unwrap();
    let parent = base.join("archive-capacity");
    fs::create_dir(&parent).unwrap();
    parent.join("synthetic-run")
}
fn open_test(root: &std::path::Path, native: bool) -> Store {
    let store = Store::open(&root.join("workspace-v1/stories.sqlite3"), None).unwrap();
    if !native {
        let cap: u32 = store
            .connection
            .query_row("PRAGMA max_page_count=96", [], |row| row.get(0))
            .unwrap();
        assert_eq!(cap, 96);
    }
    assert_eq!(
        store
            .connection
            .pragma_query_value::<u32, _>(None, "max_page_count", |row| row.get(0))
            .unwrap(),
        96
    );
    store
}
fn exercise(native: bool) {
    let root = root();
    let setup = run(&root, "setup").unwrap();
    eprintln!(
        "capacity calibration pages={} caches={} control_head={}",
        setup["page_count"], setup["cache_count"], setup["control_revision"]
    );
    let bytes = fs::read(root.join("archive.json")).unwrap();
    let mut store = open_test(&root, native);
    for _ in 0..2 {
        assert_eq!(
            store.import_archive(validate_archive(&bytes, &|| false).unwrap(), &|| false),
            Err(ArchiveError::Full)
        );
    }
    drop(store);
    assert_eq!(
        run(&root, "check-full").unwrap()["cache_count"],
        setup["cache_count"]
    );
    assert_eq!(run(&root, "relieve").unwrap()["cache_count"], 1);
    let mut store = open_test(&root, native);
    store
        .import_archive(validate_archive(&bytes, &|| false).unwrap(), &|| false)
        .unwrap();
    drop(store);
    assert_eq!(run(&root, "check-imported").unwrap()["archive_exact"], true);
    let mut store = open_test(&root, native);
    assert_eq!(
        store.import_archive(validate_archive(&bytes, &|| false).unwrap(), &|| false),
        Err(ArchiveError::Conflict)
    );
    let scope = Scope {
        story: "archive-capacity-source-v1".into(),
        branch: "main".into(),
    };
    let engine = store.resume(&scope).unwrap().engine;
    let request = engine.request(
        "after-relief-gift",
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    let committed = store
        .commit_turn(&request, &proposal, receipt.narration())
        .unwrap();
    assert_eq!(
        store
            .commit_turn(&request, &proposal, receipt.narration())
            .unwrap(),
        committed
    );
    assert_eq!(store.resume(&scope).unwrap().engine.revision(), 3);
    let engine = store.resume(&scope).unwrap().engine;
    let canonical = engine.canonical_bytes();
    let duplicate = engine.request("rejected-second-gift", request.intent.clone());
    let duplicate_proposal = Engine::proposal(&duplicate).unwrap();
    store.begin_turn(&duplicate).unwrap();
    assert_eq!(
        store.commit_turn(&duplicate, &duplicate_proposal, "No accepted outcome"),
        Err(TurnError::Engine(Error::Inventory))
    );
    assert!(store.resume(&scope).unwrap().engine.canonical_bytes() == canonical);
    drop(store);
    let mut reopened = open_test(&root, native);
    assert!(reopened.resume(&scope).unwrap().engine.canonical_bytes() == canonical);
    assert!(
        reopened
            .commit_turn(&request, &proposal, receipt.narration())
            .unwrap()
            == committed
    );
    assert!(
        reopened
            .export_archive("archive-capacity-control-v1", &|| false)
            .unwrap()
            .bytes()
            == fs::read(root.join("control-baseline.json")).unwrap()
    );
}
#[test]
fn actual_full_import_rolls_back_then_cache_only_relief_imports_and_continues() {
    with_local_cap(|| exercise(false));
}
#[test]
fn full_after_drop_reopen_stays_atomic_until_scoped_cache_relief() {
    with_local_cap(|| {
        let root = root();
        let setup = run(&root, "setup").unwrap();
        let bytes = fs::read(root.join("archive.json")).unwrap();
        for _ in 0..2 {
            let mut store = open_test(&root, false);
            assert_eq!(
                store.import_archive(validate_archive(&bytes, &|| false).unwrap(), &|| false),
                Err(ArchiveError::Full)
            );
            drop(store);
            let checked = run(&root, "check-full").unwrap();
            assert_eq!(checked["cache_count"], setup["cache_count"]);
            assert_eq!(checked["max_page_count"], 96);
        }
        assert_eq!(run(&root, "relieve").unwrap()["cache_count"], 1);
        let mut reopened = open_test(&root, false);
        reopened
            .import_archive(validate_archive(&bytes, &|| false).unwrap(), &|| false)
            .unwrap();
        drop(reopened);
        let checked = run(&root, "check-imported").unwrap();
        assert_eq!(checked["cache_count"], 1);
        assert_eq!(checked["max_page_count"], 96);
        assert_eq!(checked["canonical_unchanged"], true);
        assert_eq!(checked["archive_exact"], true);
    });
}
#[test]
fn fixture_refuses_unknown_modes_existing_roots_and_wrong_ownership_without_adoption() {
    let unused = root();
    assert_eq!(run(&unused, "unknown").unwrap_err(), "Mode");
    assert!(!unused.exists());
    fs::create_dir(&unused).unwrap();
    fs::write(unused.join("sentinel"), b"SYNTHETIC_RETAINED_SENTINEL").unwrap();
    assert_eq!(run(&unused, "setup").unwrap_err(), "Exists");
    assert!(fs::read(unused.join("sentinel")).unwrap() == b"SYNTHETIC_RETAINED_SENTINEL");
    assert_eq!(fs::read_dir(&unused).unwrap().count(), 1);
    with_local_cap(|| {
        let owned = root();
        run(&owned, "setup").unwrap();
        let bytes = fs::read(owned.join("control-baseline.json")).unwrap();
        let owner = fs::read(owned.join("owner-v1")).unwrap();
        fs::write(owned.join("owner-v1"), vec![b'x'; owner.len()]).unwrap();
        assert_eq!(run(&owned, "check-full").unwrap_err(), "Integrity");
        let mut store = open_test(&owned, false);
        assert!(
            store
                .export_archive("archive-capacity-control-v1", &|| false)
                .unwrap()
                .bytes()
                == bytes
        );
        assert_eq!(store.stories().unwrap().len(), 1);
    });
}
#[test]
#[ignore = "explicit qualifier requires LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=96 and development-fixtures"]
fn native_compiled_page_profile_runs_the_unmodified_feature_boundary() {
    assert_eq!(
        option_env!("LIBSQLITE3_FLAGS"),
        Some("-DSQLITE_MAX_PAGE_COUNT=96")
    );
    exercise(true);
}
