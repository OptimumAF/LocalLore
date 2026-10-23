// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic filesystem/SQLite proof; no app, model or shared resource access.
use locallore_storage::{StorageError, Store};

#[cfg(windows)]
mod windows {
    use super::*;
    use locallore::{contracts::*, engine::Engine};
    use locallore_storage::{validate_archive, ForkRequest, SCHEMA_VERSION};
    use std::{
        path::{Path, PathBuf},
        sync::{
            atomic::{AtomicUsize, Ordering},
            Arc, Barrier,
        },
    };
    static NEXT: AtomicUsize = AtomicUsize::new(0);
    struct Temp(PathBuf);
    impl Temp {
        fn new() -> Self {
            let root = std::env::temp_dir().join(format!(
                "pinned-store-{}-{}-{}",
                std::process::id(),
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_nanos(),
                NEXT.fetch_add(1, Ordering::Relaxed)
            ));
            std::fs::create_dir(&root).unwrap();
            Self(root)
        }
        fn path(&self, name: &str) -> PathBuf {
            self.0.join(name)
        }
    }
    impl Drop for Temp {
        fn drop(&mut self) {
            assert!(self.0.is_absolute());
            assert_eq!(self.0.parent(), Some(std::env::temp_dir().as_path()));
            assert!(self
                .0
                .file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("pinned-store-"));
            std::fs::remove_dir_all(&self.0).unwrap();
        }
    }
    fn seed() -> Seed {
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
    }
    fn wait(store: &mut Store, scope: &Scope, key: &str) -> Receipt {
        let e = store.resume(scope).unwrap().engine;
        let r = e.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        let p = Engine::proposal(&r).unwrap();
        let n = e.preview(&r, &p).unwrap().narration().to_owned();
        store.begin_turn(&r).unwrap();
        store.commit_turn(&r, &p, &n).unwrap()
    }
    fn outside(path: &Path) -> (Scope, Vec<u8>) {
        let seed = seed();
        let scope = seed.scope.clone();
        let mut store = Store::open(path, None).unwrap();
        store
            .create_story("Synthetic outside authority", seed)
            .unwrap();
        wait(&mut store, &scope, "outside-turn");
        let state = store.resume(&scope).unwrap().engine.canonical_bytes();
        drop(store);
        (scope, state)
    }
    fn assert_sidecars_locked(path: &Path) {
        for suffix in ["-journal", "-wal", "-shm"] {
            let mut name = path.as_os_str().to_owned();
            name.push(suffix);
            let sidecar = PathBuf::from(name);
            assert_eq!(std::fs::metadata(&sidecar).unwrap().len(), 0);
            assert!(
                std::fs::OpenOptions::new()
                    .write(true)
                    .open(&sidecar)
                    .is_err(),
                "write {suffix}"
            );
            assert!(std::fs::remove_file(&sidecar).is_err(), "delete {suffix}");
            assert!(
                std::fs::rename(&sidecar, sidecar.with_extension("stolen")).is_err(),
                "rename {suffix}"
            );
        }
    }

    #[test]
    fn existing_empty_ordinary_valid_and_hardlinked_leaves_are_never_adopted_or_changed() {
        let dir = Temp::new();
        let outside_path = dir.path("outside.sqlite");
        let (scope, state) = outside(&outside_path);
        let bytes = std::fs::read(&outside_path).unwrap();
        for (name, contents) in [
            ("empty.sqlite", &b""[..]),
            ("ordinary.sqlite", &b"foreign ordinary bytes"[..]),
        ] {
            let path = dir.path(name);
            std::fs::write(&path, contents).unwrap();
            assert_eq!(
                Store::create_new_pinned(&path).err(),
                Some(StorageError::Io)
            );
            assert_eq!(std::fs::read(&path).unwrap(), contents);
        }
        assert_eq!(
            Store::create_new_pinned(&outside_path).err(),
            Some(StorageError::Io)
        );
        let planted = dir.path("planted-hardlink.sqlite");
        std::fs::hard_link(&outside_path, &planted).unwrap();
        assert_eq!(
            Store::create_new_pinned(&planted).err(),
            Some(StorageError::Io)
        );
        assert_eq!(std::fs::read(&outside_path).unwrap(), bytes);
        assert_eq!(
            Store::open(&outside_path, None)
                .unwrap()
                .resume(&scope)
                .unwrap()
                .engine
                .canonical_bytes(),
            state
        );
        let directory = dir.path("directory.sqlite");
        std::fs::create_dir(&directory).unwrap();
        assert!(Store::create_new_pinned(&directory).is_err());
        assert!(directory.is_dir());
        assert_eq!(std::fs::read_dir(&dir.0).unwrap().count(), 5);
    }

    #[test]
    fn actual_sqlite_store_works_while_leaf_rename_delete_and_replacement_are_denied() {
        let dir = Temp::new();
        let path = dir.path("stage.sqlite");
        let replacement = dir.path("outside.sqlite");
        outside(&replacement);
        let outside_bytes = std::fs::read(&replacement).unwrap();
        let mut store = Store::create_new_pinned(&path).unwrap();
        assert_sidecars_locked(&path);
        assert_eq!(store.info().unwrap().schema_version, SCHEMA_VERSION);
        let seed = seed();
        let scope = seed.scope.clone();
        store.create_story("Reserved authority", seed).unwrap();
        let receipt = wait(&mut store, &scope, "live-turn");
        assert!(std::fs::rename(&path, dir.path("stolen.sqlite")).is_err());
        assert!(std::fs::remove_file(&path).is_err());
        assert!(std::fs::rename(&replacement, &path).is_err());
        assert_eq!(std::fs::read(&replacement).unwrap(), outside_bytes);
        assert_eq!(
            store.resume(&scope).unwrap().engine.receipts(),
            std::slice::from_ref(&receipt)
        );
        assert_sidecars_locked(&path);
        drop(store);
        let moved = dir.path("released.sqlite");
        std::fs::rename(&path, &moved).unwrap();
        std::fs::rename(&moved, &path).unwrap();
        assert_eq!(
            Store::open(&path, None)
                .unwrap()
                .resume(&scope)
                .unwrap()
                .engine
                .receipts(),
            std::slice::from_ref(&receipt)
        );
    }

    #[test]
    fn shared_archive_import_fork_exact_retry_and_reopen_use_the_reserved_database() {
        let dir = Temp::new();
        let source = dir.path("source.sqlite");
        let (root, _) = outside(&source);
        let mut source = Store::open(&source, None).unwrap();
        let child = source
            .fork_branch(
                &ForkRequest {
                    parent: root.clone(),
                    child_branch: "child".into(),
                    expected_parent_revision: 1,
                    at_revision: 1,
                },
                &|| false,
            )
            .unwrap()
            .scope;
        wait(&mut source, &child, "child-turn");
        let archive = source.export_archive(&root.story, &|| false).unwrap();
        let expected = source.resume(&child).unwrap().engine;
        let destination = dir.path("stage.sqlite");
        let mut target = Store::create_new_pinned(&destination).unwrap();
        target
            .import_archive(
                validate_archive(archive.bytes(), &|| false).unwrap(),
                &|| false,
            )
            .unwrap();
        assert_sidecars_locked(&destination);
        let loaded = target.resume(&child).unwrap().engine;
        assert_eq!(loaded.canonical_bytes(), expected.canonical_bytes());
        assert_eq!(loaded.receipts(), expected.receipts());
        let receipt = loaded.receipts().last().unwrap();
        assert_eq!(
            target
                .commit_turn(receipt.request(), receipt.proposal(), receipt.narration())
                .unwrap(),
            *receipt
        );
        assert!(std::fs::rename(&destination, dir.path("stolen.sqlite")).is_err());
        drop(target);
        let mut reopened = Store::open(&destination, None).unwrap();
        assert_eq!(
            reopened.resume(&child).unwrap().engine.canonical_bytes(),
            expected.canonical_bytes()
        );
        wait(&mut reopened, &child, "continued");
        assert_eq!(reopened.resume(&child).unwrap().engine.revision(), 3);
        assert_eq!(source.resume(&child).unwrap().engine.revision(), 2);
    }

    #[test]
    fn competing_creators_get_exactly_one_new_store_and_release_its_guard_on_drop() {
        let dir = Temp::new();
        let path = dir.path("race.sqlite");
        let barrier = Arc::new(Barrier::new(2));
        let other_path = path.clone();
        let gate = barrier.clone();
        let other = std::thread::spawn(move || {
            gate.wait();
            Store::create_new_pinned(&other_path)
        });
        barrier.wait();
        let first = Store::create_new_pinned(&path);
        let second = other.join().unwrap();
        assert_eq!(usize::from(first.is_ok()) + usize::from(second.is_ok()), 1);
        let winner = first.or(second).unwrap();
        assert_eq!(winner.info().unwrap().schema_version, SCHEMA_VERSION);
        assert!(std::fs::remove_file(&path).is_err());
        drop(winner);
        std::fs::remove_file(&path).unwrap();
        assert!(!path.exists());
    }

    #[test]
    fn every_existing_sidecar_empty_ordinary_or_hardlink_refuses_before_sqlite() {
        for suffix in ["-journal", "-wal", "-shm"] {
            for kind in ["empty", "ordinary", "hardlink"] {
                let dir = Temp::new();
                let outside_path = dir.path("outside.sqlite");
                let (scope, state) = outside(&outside_path);
                let before = std::fs::read(&outside_path).unwrap();
                let path = dir.path("stage.sqlite");
                let sidecar = dir.path(&format!("stage.sqlite{suffix}"));
                match kind {
                    "empty" => std::fs::write(&sidecar, b"").unwrap(),
                    "ordinary" => std::fs::write(&sidecar, b"foreign sidecar bytes").unwrap(),
                    _ => std::fs::hard_link(&outside_path, &sidecar).unwrap(),
                };
                let sidecar_before = std::fs::read(&sidecar).unwrap();
                assert_eq!(
                    Store::create_new_pinned(&path).err(),
                    Some(StorageError::Io),
                    "{suffix}/{kind}"
                );
                assert_eq!(std::fs::read(&sidecar).unwrap(), sidecar_before);
                assert_eq!(std::fs::read(&outside_path).unwrap(), before);
                assert_eq!(
                    Store::open(&outside_path, None)
                        .unwrap()
                        .resume(&scope)
                        .unwrap()
                        .engine
                        .canonical_bytes(),
                    state
                );
            }
        }
    }

    #[test]
    #[ignore = "Requires Windows file-symlink privilege or Developer Mode; run explicitly."]
    fn planted_sidecar_reparse_never_recovers_or_overwrites_another_valid_store() {
        for suffix in ["-journal", "-wal", "-shm"] {
            let dir = Temp::new();
            let outside_path = dir.path("outside.sqlite");
            let (scope, state) = outside(&outside_path);
            let before = std::fs::read(&outside_path).unwrap();
            let path = dir.path("stage.sqlite");
            let sidecar = dir.path(&format!("stage.sqlite{suffix}"));
            std::os::windows::fs::symlink_file(&outside_path, &sidecar).unwrap();
            let result = Store::create_new_pinned(&path);
            let accepted = result.is_ok();
            drop(result);
            let changed = std::fs::read(&outside_path).unwrap() != before;
            assert!(
                !accepted && !changed,
                "sidecar={suffix}, accepted={accepted}, outside_bytes_changed={changed}"
            );
            assert_eq!(
                Store::open(&outside_path, None)
                    .unwrap()
                    .resume(&scope)
                    .unwrap()
                    .engine
                    .canonical_bytes(),
                state
            );
            // Dangling reparses are also existing entries and must not create
            // or inspect the named target during pragma/schema initialization.
            let other_dir = Temp::new();
            let missing = other_dir.path("must-not-create.sqlite");
            let path = other_dir.path("stage.sqlite");
            std::os::windows::fs::symlink_file(
                &missing,
                other_dir.path(&format!("stage.sqlite{suffix}")),
            )
            .unwrap();
            assert_eq!(
                Store::create_new_pinned(&path).err(),
                Some(StorageError::Io)
            );
            assert!(!missing.exists());
        }
    }

    #[test]
    #[ignore = "Requires Windows file-symlink privilege or Developer Mode; run explicitly."]
    fn planted_file_reparse_and_dangling_reparse_never_touch_outside_store() {
        let dir = Temp::new();
        let outside_path = dir.path("outside.sqlite");
        let (scope, state) = outside(&outside_path);
        let bytes = std::fs::read(&outside_path).unwrap();
        let planted = dir.path("planted.sqlite");
        std::os::windows::fs::symlink_file(&outside_path, &planted).unwrap();
        assert_eq!(
            Store::create_new_pinned(&planted).err(),
            Some(StorageError::Io)
        );
        let dangling = dir.path("dangling.sqlite");
        let nonexistent = dir.path("must-not-create.sqlite");
        std::os::windows::fs::symlink_file(&nonexistent, &dangling).unwrap();
        assert_eq!(
            Store::create_new_pinned(&dangling).err(),
            Some(StorageError::Io)
        );
        assert!(!nonexistent.exists());
        assert_eq!(std::fs::read(&outside_path).unwrap(), bytes);
        assert_eq!(
            Store::open(&outside_path, None)
                .unwrap()
                .resume(&scope)
                .unwrap()
                .engine
                .canonical_bytes(),
            state
        );
    }

    #[test]
    fn relative_and_ambiguous_leaf_names_fail_before_creation() {
        let dir = Temp::new();
        for path in [
            PathBuf::from("relative-stage.sqlite"),
            dir.path("new.sqlite:stream"),
            dir.path("new.sqlite."),
            dir.path("new.sqlite "),
            dir.path("..\\new.sqlite"),
        ] {
            assert_eq!(
                Store::create_new_pinned(&path).err(),
                Some(StorageError::InvalidInput)
            );
        }
        assert_eq!(std::fs::read_dir(&dir.0).unwrap().count(), 0);
    }
}

#[cfg(not(windows))]
#[test]
fn unsupported_platform_fails_closed_without_creating_any_leaf() {
    let path =
        std::env::temp_dir().join(format!("unsupported-pinned-store-{}", std::process::id()));
    assert_eq!(
        Store::create_new_pinned(&path).err(),
        Some(StorageError::InvalidInput)
    );
    assert!(!path.exists());
}
