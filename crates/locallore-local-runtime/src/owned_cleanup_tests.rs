// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen owned-runtime cleanup oracles. Fixed protocol fixtures, never model quality.
//! Root registers this child module and the contract's private one-shot fault.
#![cfg(feature = "development-worker")]

use super::*;
use std::{path::PathBuf, sync::atomic::AtomicU64};

static OWNED_FIXTURE_SEQUENCE: AtomicU64 = AtomicU64::new(0);

struct FaultReset;
impl Drop for FaultReset {
    fn drop(&mut self) {
        FAIL_CLEANUP_ONCE.with(|fault| fault.set(false));
        #[cfg(windows)]
        {
            FAIL_PIPE_STAGE.with(|fault| fault.set(None));
            STARTED_CHILD.with(|handle| drop(handle.borrow_mut().take()));
        }
    }
}

fn owned_fixture_directory() -> PathBuf {
    let directory = std::env::temp_dir().join(format!(
        "locallore-owned-cleanup-private-{}-{}",
        std::process::id(),
        OWNED_FIXTURE_SEQUENCE.fetch_add(1, Ordering::Relaxed)
    ));
    std::fs::create_dir(&directory).unwrap();
    directory
}

#[cfg(windows)]
fn fixed_owned_start(directory: &Path) -> Result<LocalRuntime, OwnedStartFailure> {
    // Exactly the existing fixed worker lookup and tiny mode file used by tests::fixture.
    let model = directory.join("hang");
    let file = File::create(&model).unwrap();
    let mut executable = std::env::current_exe().unwrap();
    executable.pop();
    executable.pop();
    executable.push("protocol-fixture.exe");
    assert!(
        executable.is_file(),
        "build the existing protocol-fixture first"
    );
    LocalRuntime::start_owned_cancelled(&executable, &model, file, &|| false)
}

fn require_before_child(result: Result<LocalRuntime, OwnedStartFailure>, expected: Error) {
    match result {
        Err(OwnedStartFailure::BeforeChild(cause)) => assert_eq!(cause, expected),
        Err(OwnedStartFailure::AfterChild { mut owner, .. }) => {
            owner.terminate_and_reap().unwrap();
            panic!("pre-child refusal unexpectedly created an owned child");
        }
        Ok(mut owner) => {
            owner.terminate_and_reap().unwrap();
            panic!("pre-child refusal unexpectedly succeeded");
        }
    }
}

#[cfg(windows)]
fn require_after_child(result: Result<LocalRuntime, OwnedStartFailure>) -> (Error, LocalRuntime) {
    match result {
        Err(OwnedStartFailure::AfterChild { cause, owner }) => (cause, owner),
        Err(OwnedStartFailure::BeforeChild(_)) => panic!("lost partial-start child ownership"),
        Ok(mut owner) => {
            owner.terminate_and_reap().unwrap();
            panic!("requested pipe-thread failure unexpectedly succeeded");
        }
    }
}

#[cfg(windows)]
fn duplicate_child(owner: &LocalRuntime) -> std::os::windows::io::OwnedHandle {
    use std::os::windows::io::AsHandle;
    owner.child.as_handle().try_clone_to_owned().unwrap()
}

#[cfg(windows)]
fn assert_exact_child_terminal(handle: &std::os::windows::io::OwnedHandle) {
    use std::os::windows::io::AsRawHandle;
    #[link(name = "kernel32")]
    extern "system" {
        fn WaitForSingleObject(handle: *mut std::ffi::c_void, milliseconds: u32) -> u32;
    }
    // A zero-time observation of this retained handle, never PID/name enumeration.
    assert_eq!(unsafe { WaitForSingleObject(handle.as_raw_handle(), 0) }, 0);
}

fn assert_cleanup_confirmed(owner: &mut LocalRuntime) {
    assert_eq!(owner.status(), Status::Failed);
    assert!(owner.child.try_wait().unwrap().is_some());
    assert!(owner.writer.is_none());
    assert!(owner.threads.is_empty());
    assert_eq!(owner.terminate_and_reap(), Ok(()));
    assert!(owner.threads.is_empty());
    assert_eq!(owner.load(|| false), Err(Error::WorkerUnavailable));
}

#[test]
fn public_owned_start_refuses_cancel_and_invalid_expected_hash_before_any_child() {
    let _reset = FaultReset;
    let directory = owned_fixture_directory();
    let missing_model = directory.join("private missing model");
    #[cfg(windows)]
    {
        assert!(STARTED_CHILD.with(|handle| handle.borrow().is_none()));
        // If either public path actually reached process creation, retain its exact handle.
        FAIL_PIPE_STAGE.with(|fault| fault.set(Some(1)));
    }
    require_before_child(
        LocalRuntime::spawn_packaged_owned_expected_cancelled(
            &directory,
            &missing_model,
            &"0".repeat(64),
            || true,
        ),
        Error::Cancelled,
    );
    for invalid in ["", "bad", &"A".repeat(64), &"0".repeat(63)] {
        require_before_child(
            LocalRuntime::spawn_packaged_owned_expected_cancelled(
                &directory,
                &missing_model,
                invalid,
                || false,
            ),
            Error::InvalidRequest,
        );
    }
    #[cfg(windows)]
    assert!(STARTED_CHILD.with(|handle| handle.borrow().is_none()));
    assert_eq!(std::fs::read_dir(&directory).unwrap().count(), 0);
    std::fs::remove_dir(directory).unwrap();
}

#[cfg(windows)]
#[test]
fn each_partial_pipe_failure_returns_the_exact_owner_until_confirmed_reap_and_join() {
    let _reset = FaultReset;
    for stage in 1..=3 {
        let directory = owned_fixture_directory();
        FAIL_PIPE_STAGE.with(|fault| fault.set(Some(stage)));
        let result = fixed_owned_start(&directory);
        FAIL_PIPE_STAGE.with(|fault| fault.set(None));
        let exact_child = STARTED_CHILD.with(|handle| handle.borrow_mut().take().unwrap());
        let (cause, mut owner) = require_after_child(result);
        assert_eq!(cause, Error::WorkerUnavailable);
        assert_eq!(owner.threads.len(), stage - 1);
        owner.terminate_and_reap().unwrap();
        assert_exact_child_terminal(&exact_child);
        assert_cleanup_confirmed(&mut owner);
        // Cleanup must not rewrite the original fixed startup error.
        assert_eq!(cause, Error::WorkerUnavailable);
        drop(exact_child);
        drop(owner);
        std::fs::remove_dir_all(directory).unwrap();
    }
}

#[test]
fn failed_protocol_load_still_allows_direct_cleanup_without_the_protocol_gate() {
    let _reset = FaultReset;
    let (mut owner, directory) = tests::fixture("wrong-id");
    #[cfg(windows)]
    let exact_child = duplicate_child(&owner);
    let initial_error = owner.load(|| false).unwrap_err();
    assert_eq!(initial_error, Error::Protocol);
    assert_eq!(owner.status(), Status::Failed);
    // The protocol shutdown entry refuses Failed; that refusal is not cleanup proof.
    assert_eq!(owner.shutdown(), Err(Error::WorkerUnavailable));
    owner.terminate_and_reap().unwrap();
    #[cfg(windows)]
    assert_exact_child_terminal(&exact_child);
    assert_cleanup_confirmed(&mut owner);
    assert_eq!(initial_error, Error::Protocol);
    #[cfg(windows)]
    drop(exact_child);
    drop(owner);
    std::fs::remove_dir_all(directory).unwrap();
}

#[test]
fn one_shot_cleanup_failure_retains_live_child_pipes_threads_for_explicit_retry() {
    let _reset = FaultReset;
    let (mut owner, directory) = tests::fixture("valid");
    owner.load(|| false).unwrap();
    assert_eq!(owner.status(), Status::Loaded);
    let child_id = owner.child.id();
    #[cfg(windows)]
    let exact_child = duplicate_child(&owner);
    assert!(owner.child.try_wait().unwrap().is_none());
    assert!(owner.writer.is_some());
    assert_eq!(owner.threads.len(), 3);
    let thread_ids: Vec<_> = owner.threads.iter().map(|thread| thread.thread().id()).collect();
    FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    assert_eq!(owner.terminate_and_reap(), Err(Error::Cleanup));
    assert!(!FAIL_CLEANUP_ONCE.with(|fault| fault.get()));
    assert_eq!(owner.child.id(), child_id);
    assert_eq!(owner.status(), Status::Failed);
    assert!(owner.child.try_wait().unwrap().is_none());
    assert!(owner.writer.is_some());
    assert_eq!(owner.threads.len(), 3);
    assert_eq!(
        owner.threads.iter().map(|thread| thread.thread().id()).collect::<Vec<_>>(),
        thread_ids
    );
    assert_eq!(owner.load(|| false), Err(Error::WorkerUnavailable));
    owner.terminate_and_reap().unwrap();
    #[cfg(windows)]
    assert_exact_child_terminal(&exact_child);
    assert_cleanup_confirmed(&mut owner);
    #[cfg(windows)]
    drop(exact_child);
    drop(owner);
    std::fs::remove_dir_all(directory).unwrap();
}

#[test]
fn owned_start_failure_debug_reveals_fixed_variant_and_cause_without_owner_internals() {
    let before = format!("{:?}", OwnedStartFailure::BeforeChild(Error::InvalidRequest));
    assert!(before.contains("BeforeChild"));
    assert!(before.contains("InvalidRequest"));
    #[cfg(windows)]
    {
        let _reset = FaultReset;
        let directory = owned_fixture_directory();
        FAIL_PIPE_STAGE.with(|fault| fault.set(Some(2)));
        let failure = match fixed_owned_start(&directory) {
            Err(failure) => failure,
            Ok(mut owner) => {
                owner.terminate_and_reap().unwrap();
                panic!("requested failure unexpectedly succeeded");
            }
        };
        FAIL_PIPE_STAGE.with(|fault| fault.set(None));
        let rendered = format!("{failure:?}");
        assert!(rendered.contains("AfterChild"));
        assert!(rendered.contains("WorkerUnavailable"));
        assert!(!rendered.contains(directory.to_str().unwrap()));
        for private in [
            "hang",
            "protocol-fixture",
            "LocalRuntime {",
            "writer:",
            "threads:",
            "worker_sha256:",
        ] {
            assert!(!rendered.contains(private));
        }
        let (initial_error, mut owner) = require_after_child(Err(failure));
        let exact_child = STARTED_CHILD.with(|handle| handle.borrow_mut().take().unwrap());
        FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
        assert_eq!(owner.terminate_and_reap(), Err(Error::Cleanup));
        assert_eq!(initial_error, Error::WorkerUnavailable);
        assert_eq!(owner.threads.len(), 1);
        owner.terminate_and_reap().unwrap();
        assert_exact_child_terminal(&exact_child);
        assert_cleanup_confirmed(&mut owner);
        drop(exact_child);
        drop(owner);
        std::fs::remove_dir_all(directory).unwrap();
    }
}

#[test]
fn owned_parent_thread_panic_reports_cleanup_then_explicit_retry_drains_and_stays_failed() {
    let _reset = FaultReset;
    let (mut owner, directory) = tests::fixture("valid");
    owner.load(|| false).unwrap();
    assert_eq!(owner.status(), Status::Loaded);
    #[cfg(windows)]
    let exact_child = duplicate_child(&owner);
    let original_threads: Vec<_> = owner
        .threads
        .iter()
        .map(|thread| thread.thread().id())
        .collect();
    assert_eq!(original_threads.len(), 3);
    // This is an actual parent-owned join failure, not a native worker crash.
    // No supplied production callback, additional process or test fault hook.
    let panicking_thread = std::thread::spawn(|| {
        panic!("fixed synthetic owned parent thread panic");
    });
    let panicking_id = panicking_thread.thread().id();
    owner.threads.push(panicking_thread);
    assert_eq!(owner.threads.len(), 4);

    assert_eq!(owner.terminate_and_reap(), Err(Error::Cleanup));
    assert_eq!(owner.status(), Status::Failed);
    assert!(owner.child.try_wait().unwrap().is_some());
    assert!(owner.writer.is_none());
    #[cfg(windows)]
    assert_exact_child_terminal(&exact_child);
    // A consumed panicked join is terminal. The implementation may already have
    // joined other threads, or may retain them for retry; neither front nor pop
    // processing order is part of this oracle. Remaining handles must still be
    // actual originally owned threads, and the explicit retry must drain them.
    assert!(owner.threads.len() <= original_threads.len());
    for retained in &owner.threads {
        assert_ne!(retained.thread().id(), panicking_id);
        assert!(original_threads.contains(&retained.thread().id()));
    }
    assert_eq!(owner.terminate_and_reap(), Ok(()));
    assert_cleanup_confirmed(&mut owner);
    assert_eq!(owner.generate(
        Generation {
            role: Role::Director,
            prompt: "fixed synthetic request after cleanup".into(),
            schema: None,
            max_tokens: 1,
        },
        || false,
    ).err(), Some(Error::WorkerUnavailable));
    #[cfg(windows)]
    drop(exact_child);
    drop(owner);
    std::fs::remove_dir_all(directory).unwrap();
}

#[cfg(windows)]
#[test]
fn partial_start_valid_fixture_owner_is_failed_and_cannot_load_before_cleanup() {
    let _reset = FaultReset;
    FAIL_PIPE_STAGE.with(|fault| fault.set(Some(3)));
    // The public fixed fixture uses VALID mode, so its surviving writer/reader
    // can expose accidental inference reuse after stderr-thread startup fails.
    let result = LocalRuntime::development_protocol_fixture().map(|(owner, _directory)| owner);
    FAIL_PIPE_STAGE.with(|fault| fault.set(None));
    let (initial_error, mut owner) = require_after_child(result);
    let exact_child = STARTED_CHILD.with(|handle| handle.borrow_mut().take().unwrap());
    let returned_status = owner.status();
    let before_request_id = owner.next_id;
    let first_load = owner.load(|| false);
    let after_request_id = owner.next_id;

    // Cleanup precedes assertions about the failing behavior on the old source.
    // The fixed helper retains its own synthetic directory on startup failure;
    // it does not disclose that path through OwnedStartFailure diagnostics.
    let cleanup = owner.terminate_and_reap();
    assert_eq!(cleanup, Ok(()));
    assert_exact_child_terminal(&exact_child);
    assert_cleanup_confirmed(&mut owner);
    drop(exact_child);
    drop(owner);

    assert_eq!(initial_error, Error::WorkerUnavailable);
    assert_eq!(returned_status, Status::Failed);
    assert_eq!(first_load, Err(Error::WorkerUnavailable));
    assert_eq!(after_request_id, before_request_id);
}
