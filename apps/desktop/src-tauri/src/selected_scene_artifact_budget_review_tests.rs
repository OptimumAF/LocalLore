// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST under Root6510885718. SOURCE ONLY / UNREGISTERED / UNRUN.
//! Child of harness; private fixed writer budget and actual create-new writes.
//! Missing ArtifactBudget/scene_budget interfaces are SETUP, not behavior RED.
//! No WebView, PNG, model, native IPC, OS isolation or full-size allocation proof.
use super::*;
use std::{
    fs,
    sync::atomic::{AtomicU64, Ordering},
    time::{SystemTime, UNIX_EPOCH},
};

fn owned_state() -> HarnessState {
    // Local Root admission supplies physical D; portable CI retains temp fallback.
    // No author execution, global environment mutation or automatic cleanup.
    let parent = std::env::var_os("LOCALLORE_SELECTED_SCENE4_NATIVE_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    assert!(parent.is_absolute() && parent.is_dir());
    let parent = fs::canonicalize(parent).unwrap();
    for ancestor in parent.ancestors() {
        let metadata = fs::symlink_metadata(ancestor).unwrap();
        assert!(metadata.is_dir() && !metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
    }
    static NEXT: AtomicU64 = AtomicU64::new(0);
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    HarnessState::create(parent.join(format!(
        "selected-scene-artifact-budget-{stamp}-{}",
        NEXT.fetch_add(1, Ordering::SeqCst)
    )))
    .unwrap()
}

#[test]
fn pure_default_exact_limit_and_zero_reservation_are_checked_without_allocation() {
    assert_eq!(MAX_SELECTED_SCENE_ARTIFACT_BYTES, 64 * 1024 * 1024);
    let mut budget = ArtifactBudget::default();
    assert_eq!((budget.reserved, budget.failed), (0, false));
    assert_eq!(budget.reserve(0), Ok(()));
    assert_eq!(
        budget.reserve(MAX_SELECTED_SCENE_ARTIFACT_BYTES - 1),
        Ok(())
    );
    assert_eq!(budget.reserve(1), Ok(()));
    assert_eq!(budget.reserve(0), Ok(()));
    assert_eq!(
        (budget.reserved, budget.failed),
        (MAX_SELECTED_SCENE_ARTIFACT_BYTES, false)
    );
}

#[test]
fn pure_excess_is_permanent_and_never_refunds_or_allows_zero_after_failure() {
    let mut budget = ArtifactBudget {
        reserved: 7,
        failed: false,
    };
    assert_eq!(
        budget.reserve(MAX_SELECTED_SCENE_ARTIFACT_BYTES),
        Err("ArtifactWriteBudget")
    );
    assert_eq!((budget.reserved, budget.failed), (7, true));
    for amount in [0, 1, MAX_SELECTED_SCENE_ARTIFACT_BYTES, usize::MAX] {
        assert_eq!(budget.reserve(amount), Err("ArtifactWriteBudget"));
        assert_eq!((budget.reserved, budget.failed), (7, true));
    }
}

#[test]
fn pure_checked_add_overflow_fails_closed_instead_of_wrapping() {
    // Trusted impossible ordinary-state control, not a production constructor.
    let mut budget = ArtifactBudget {
        reserved: usize::MAX,
        failed: false,
    };
    assert_eq!(budget.reserve(1), Err("ArtifactWriteBudget"));
    assert_eq!((budget.reserved, budget.failed), (usize::MAX, true));
    assert_eq!(budget.reserve(0), Err("ArtifactWriteBudget"));
    let mut fresh = ArtifactBudget::default();
    assert_eq!(fresh.reserve(usize::MAX), Err("ArtifactWriteBudget"));
    assert_eq!((fresh.reserved, fresh.failed), (0, true));
}

#[test]
fn pure_explicit_failure_is_idempotent_and_preserves_prior_reservations() {
    let mut budget = ArtifactBudget::default();
    budget.reserve(3).unwrap();
    budget.fail();
    budget.fail();
    assert_eq!((budget.reserved, budget.failed), (3, true));
    assert_eq!(budget.reserve(0), Err("ArtifactWriteBudget"));
    assert_eq!(budget.reserve(1), Err("ArtifactWriteBudget"));
    assert_eq!((budget.reserved, budget.failed), (3, true));
}

#[test]
fn actual_writer_reserves_before_open_and_stops_at_the_exact_limit() {
    let mut state = owned_state();
    state.scene_budget = Some(Mutex::new(ArtifactBudget {
        reserved: MAX_SELECTED_SCENE_ARTIFACT_BYTES - 3,
        failed: false,
    }));
    state.write("at-limit.bytes", b"abc").unwrap();
    assert_eq!(
        fs::read(state.directory.join("at-limit.bytes")).unwrap(),
        b"abc"
    );
    assert_eq!(
        state
            .scene_budget
            .as_ref()
            .unwrap()
            .lock()
            .unwrap()
            .reserved,
        MAX_SELECTED_SCENE_ARTIFACT_BYTES
    );
    assert_eq!(
        state.write("over-limit.bytes", b"x"),
        Err("ArtifactWriteBudget")
    );
    assert!(!state
        .directory
        .join("over-limit.bytes")
        .try_exists()
        .unwrap());
    assert_eq!(
        state.write("after-failure-empty.bytes", b""),
        Err("ArtifactWriteBudget")
    );
    assert!(!state
        .directory
        .join("after-failure-empty.bytes")
        .try_exists()
        .unwrap());
    assert_eq!(fs::read_dir(&state.directory).unwrap().count(), 1);
    assert_eq!(
        fs::read(state.directory.join("at-limit.bytes")).unwrap(),
        b"abc"
    );
    let budget = state.scene_budget.as_ref().unwrap().lock().unwrap();
    assert_eq!(
        (budget.reserved, budget.failed),
        (MAX_SELECTED_SCENE_ARTIFACT_BYTES, true)
    );
}

#[test]
fn actual_create_new_io_failure_preserves_original_and_permanently_blocks_later_files() {
    let mut state = owned_state();
    state.scene_budget = Some(Mutex::new(ArtifactBudget::default()));
    state.write("original.bytes", b"old").unwrap();
    assert_eq!(
        state.write("original.bytes", b"changed"),
        Err("ArtifactWriteFailed")
    );
    assert_eq!(
        fs::read(state.directory.join("original.bytes")).unwrap(),
        b"old"
    );
    {
        let budget = state.scene_budget.as_ref().unwrap().lock().unwrap();
        assert_eq!(
            (budget.reserved, budget.failed),
            (3 + 7, true),
            "failed writes are reserved, never refunded"
        );
    }
    for (name, body) in [
        ("later.bytes", b"later".as_slice()),
        ("later-empty.bytes", b"".as_slice()),
    ] {
        assert_eq!(state.write(name, body), Err("ArtifactWriteBudget"));
        assert!(!state.directory.join(name).try_exists().unwrap());
    }
    assert_eq!(fs::read_dir(&state.directory).unwrap().count(), 1);
    assert_eq!(
        fs::read(state.directory.join("original.bytes")).unwrap(),
        b"old"
    );
}

#[test]
fn actual_legacy_none_keeps_create_new_error_without_latching_other_writes() {
    let mut state = owned_state();
    state.scene_budget = None;
    state.write("original.bytes", b"old").unwrap();
    assert_eq!(
        state.write("original.bytes", b"changed"),
        Err("ArtifactWriteFailed")
    );
    state.write("later.bytes", b"later").unwrap();
    assert_eq!(
        fs::read(state.directory.join("original.bytes")).unwrap(),
        b"old"
    );
    assert_eq!(
        fs::read(state.directory.join("later.bytes")).unwrap(),
        b"later"
    );
    assert_eq!(fs::read_dir(&state.directory).unwrap().count(), 2);
    assert!(state.scene_budget.is_none());
}
