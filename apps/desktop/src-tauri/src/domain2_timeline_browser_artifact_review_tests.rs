// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent D08 FIRST. SOURCE ONLY / UNREGISTERED / UNCOMPILED / UNRUN.
//! Child of harness.rs; actual private budget/label helpers and create-new writer.
//! Root executes this filter separately with D02=1, D05 fixture=1, D08 browser=1.
//! Tests NEVER mutate environment or launch a child/app/qualifier. Missing mode or
//! new API is SETUP_UNRUN, not a behavioral result. All tiny roots remain retained.
//! Eight-MiB boundaries preload private counters; actual payloads are <=9 bytes.
//! No actual malformed-flag/IPC/WebView/image/model/SDK/OS-isolation qualification.
use super::*;
use std::{fs, sync::atomic::{AtomicU64, Ordering}, time::{SystemTime, UNIX_EPOCH}};

const BROWSER_LABELS: [&str; 7] = [
    "d08-browser-catalog", "d08-browser-root", "d08-browser-child",
    "d08-browser-observer", "d08-browser-enlarged-wide",
    "d08-browser-enlarged-narrow", "d08-browser-failure",
];

fn owned_state() -> HarnessState {
    assert!(timeline_browser_active(), "SETUP_UNRUN: Root must admit the exact closed browser flags for this test filter");
    // Commanding TEMP/TMP is D:/Dev/_Temp on Root's machine. Portable test source
    // does not impose a machine-wide drive policy on unrelated developer CI.
    let parent = std::env::temp_dir();
    assert!(parent.is_absolute() && parent.is_dir(), "SETUP_UNRUN: existing temporary parent");
    let parent = fs::canonicalize(parent).unwrap();
    for ancestor in parent.ancestors() {
        let metadata = fs::symlink_metadata(ancestor).unwrap();
        assert!(metadata.is_dir() && !metadata.file_type().is_symlink());
        #[cfg(windows)] {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
    }
    static NEXT: AtomicU64 = AtomicU64::new(0);
    let stamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
    HarnessState::create(parent.join(format!("d08-browser-writer-{stamp}-{}-{}",
        std::process::id(), NEXT.fetch_add(1, Ordering::SeqCst)))).unwrap()
}

#[test]
fn fixed_browser_labels_are_exact_and_never_enabled_for_old_modes() {
    for label in BROWSER_LABELS {
        assert!(timeline_browser_label(label, true));
        assert!(!timeline_browser_label(label, false));
    }
    for label in ["initial", "d05-page-first", "d05-page-final", "d05-page-failure",
        "selected-scene-prepared", "d08-browser-root/../child", "d08-browser-catalog.json",
        "d08-browser-Catalog", "d08-browser-unknown", "", "../escape"] {
        assert!(!timeline_browser_label(label, true), "{label}");
        assert!(!timeline_browser_label(label, false), "{label}");
    }
}

#[test]
fn pure_browser_exact_cap_zero_and_legacy_default_remain_distinct() {
    assert_eq!(MAX_TIMELINE_BROWSER_ARTIFACT_BYTES, 8 * 1024 * 1024);
    assert_eq!(MAX_SELECTED_SCENE_ARTIFACT_BYTES, 64 * 1024 * 1024);
    let mut browser = ArtifactBudget::default();
    assert_eq!(browser.reserve_with_limit(0, MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Ok(()));
    assert_eq!(browser.reserve_with_limit(MAX_TIMELINE_BROWSER_ARTIFACT_BYTES - 1,
        MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Ok(()));
    assert_eq!(browser.reserve_with_limit(1, MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Ok(()));
    assert_eq!(browser.reserve_with_limit(0, MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Ok(()));
    assert_eq!((browser.reserved, browser.failed), (MAX_TIMELINE_BROWSER_ARTIFACT_BYTES, false));
    let mut legacy = ArtifactBudget::default();
    assert_eq!(legacy.reserve(MAX_TIMELINE_BROWSER_ARTIFACT_BYTES + 1), Ok(()));
    assert_eq!(legacy.reserve(MAX_SELECTED_SCENE_ARTIFACT_BYTES - MAX_TIMELINE_BROWSER_ARTIFACT_BYTES - 1), Ok(()));
    assert_eq!((legacy.reserved, legacy.failed), (MAX_SELECTED_SCENE_ARTIFACT_BYTES, false));
}

#[test]
fn pure_browser_excess_and_overflow_latch_without_refund_or_legacy_escape() {
    let mut browser = ArtifactBudget {reserved: 7, failed: false};
    assert_eq!(browser.reserve_with_limit(MAX_TIMELINE_BROWSER_ARTIFACT_BYTES,
        MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Err("ArtifactWriteBudget"));
    assert_eq!((browser.reserved, browser.failed), (7, true));
    for amount in [0, 1, usize::MAX] {
        assert_eq!(browser.reserve_with_limit(amount, MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Err("ArtifactWriteBudget"));
        assert_eq!(browser.reserve(amount), Err("ArtifactWriteBudget"));
        assert_eq!((browser.reserved, browser.failed), (7, true));
    }
    let mut overflow = ArtifactBudget {reserved: usize::MAX, failed: false};
    assert_eq!(overflow.reserve_with_limit(1, MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Err("ArtifactWriteBudget"));
    assert_eq!((overflow.reserved, overflow.failed), (usize::MAX, true));
    assert_eq!(overflow.reserve_with_limit(0, MAX_TIMELINE_BROWSER_ARTIFACT_BYTES), Err("ArtifactWriteBudget"));
}

#[test]
fn actual_browser_writer_reserves_before_open_and_keeps_failed_bytes_charged() {
    let mut state = owned_state();
    assert!(state.scene_budget.is_some(), "exact browser mode must activate the existing writer budget");
    // Trusted counter placement, not an eight-MiB disk allocation.
    state.scene_budget = Some(Mutex::new(ArtifactBudget {
        reserved: MAX_TIMELINE_BROWSER_ARTIFACT_BYTES - 2, failed: false,
    }));
    state.write("at-limit.bytes", b"ok").unwrap();
    assert_eq!(fs::read(state.directory.join("at-limit.bytes")).unwrap(), b"ok");
    assert_eq!(state.write("over-limit.bytes", b"x"), Err("ArtifactWriteBudget"));
    assert!(!state.directory.join("over-limit.bytes").try_exists().unwrap());
    assert_eq!(state.write("after-failure-empty.bytes", b""), Err("ArtifactWriteBudget"));
    assert!(!state.directory.join("after-failure-empty.bytes").try_exists().unwrap());
    assert_eq!(fs::read_dir(&state.directory).unwrap().count(), 1);
    let budget = state.scene_budget.as_ref().unwrap().lock().unwrap();
    assert_eq!((budget.reserved, budget.failed), (MAX_TIMELINE_BROWSER_ARTIFACT_BYTES, true));
}

#[test]
fn actual_browser_duplicate_create_new_latches_and_preserves_the_original() {
    let mut state = owned_state();
    state.scene_budget = Some(Mutex::new(ArtifactBudget::default()));
    state.write("original.bytes", b"old").unwrap();
    assert_eq!(state.write("original.bytes", b"change"), Err("ArtifactWriteFailed"));
    assert_eq!(fs::read(state.directory.join("original.bytes")).unwrap(), b"old");
    assert_eq!(state.scene_budget.as_ref().unwrap().lock().unwrap().reserved, 9);
    assert_eq!(state.write("later.bytes", b"x"), Err("ArtifactWriteBudget"));
    assert!(!state.directory.join("later.bytes").try_exists().unwrap());
    assert_eq!(fs::read_dir(&state.directory).unwrap().count(), 1);
}

#[test]
fn actual_browser_reservation_excludes_paging_and_generic_labels() {
    let state = owned_state();
    for label in ["initial", "d05-page-first", "d05-page-final", "d05-page-failure",
        "selected-scene-prepared", "d08-browser-unknown", "../escape"] {
        assert_eq!(state.reserve(label), Err("CheckpointInvalid"), "{label}");
    }
    for label in BROWSER_LABELS { state.reserve(label).unwrap(); }
    assert_eq!(state.reserve("d08-browser-catalog"), Err("CheckpointDuplicate"));
    assert_eq!(state.progress.lock().unwrap().labels.len(), BROWSER_LABELS.len());
    assert_eq!(fs::read_dir(&state.directory).unwrap().count(), 0);
}
