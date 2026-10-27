// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen BEFORE callback/pin fixes at cea16866. SOURCE ONLY / UNRUN.
//! Default Models are empty. No model/runtime process or inference is requested.
use super::*;

#[test]
fn consent_panic_before_reservation_ends_the_actual_job_without_cleanup_or_permanent_busy() {
    let f = Fixture::new();
    let started = f
        .manager
        .full_comparison_start_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            Fixture::input(&uuid().unwrap()),
            |_| -> Result<bool> { panic!("fixed pre-reservation native consent panic") },
        )
        .unwrap();
    // Fixture scheduling bound ONLY. In particular do not wait the parent's
    //180s helper when a dead worker left its active flag/cancellation latched.
    let deadline = Instant::now() + Duration::from_secs(15);
    let observed = loop {
        let status = f
            .manager
            .full_comparison_status_native(&f.lease, f.epoch, true, cap(&started))
            .unwrap();
        let evaluation_complete = f.manager.cleanup_complete();
        let models_complete = f.models.cleanup_complete();
        if (status["running"] == false && evaluation_complete && models_complete)
            || Instant::now() >= deadline
        {
            break (status, evaluation_complete, models_complete);
        }
        std::thread::sleep(Duration::from_millis(5));
    };
    // Capture this before assertions. A new denied request is allowed, but must
    // not inherit permanent EvaluationBusy from the already-ended panic thread.
    let next = f.manager.full_comparison_start_native(
        &f.lease,
        &f.models,
        f.epoch,
        true,
        Fixture::input(&uuid().unwrap()),
        |_| Ok(false),
    );
    assert_eq!(observed.0["running"], false);
    assert_eq!(observed.0["phase"], "failed");
    assert_eq!(observed.0["error"], "EvaluationInternal");
    assert_eq!(observed.0["report_ready"], false);
    assert_eq!(observed.0["cleanup_required"], false);
    assert_eq!(observed.0["cleanup_running"], false);
    assert!(
        observed.1 && observed.2,
        "actual owners complete without cleanup action"
    );
    assert_eq!(next.unwrap()["version"], 2);
    // Parent Drop drains any newly admitted denied request; on the baseline it
    // retains an unconfirmed actual manager/Job rather than inventing completion.
}

fn checked_owned_move(f: &Fixture, run: &str) -> std::io::Result<(PathBuf, PathBuf)> {
    fn unsafe_path() -> std::io::Error {
        std::io::Error::other("UnsafeOwnedFixtureMove")
    }
    fn ordinary_directory(path: &Path) -> std::io::Result<()> {
        let metadata = fs::symlink_metadata(path)?;
        if !metadata.is_dir() || metadata.file_type().is_symlink() {
            return Err(unsafe_path());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err(unsafe_path());
            }
        }
        Ok(())
    }
    if !valid_id(run) {
        return Err(unsafe_path());
    }
    let library = std::path::absolute(f.root())?;
    let parent = std::path::absolute(f.manager.root.parent().ok_or_else(unsafe_path)?)?;
    if library.parent() != Some(parent.as_path())
        || library.file_name().and_then(|s| s.to_str()) != Some("comparison-evaluations")
    {
        return Err(unsafe_path());
    }
    for ancestor in library.ancestors() {
        ordinary_directory(ancestor)?;
    }
    let source = library.join(run);
    let target = library.join(format!("{run}-pin-review-moved"));
    if source.parent() != Some(library.as_path())
        || target.parent() != Some(library.as_path())
        || source == target
    {
        return Err(unsafe_path());
    }
    ordinary_directory(&source)?;
    let canonical_library = fs::canonicalize(&library)?;
    if fs::canonicalize(&source)?.parent() != Some(canonical_library.as_path()) {
        return Err(unsafe_path());
    }
    match fs::symlink_metadata(&target) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        Err(error) => return Err(error),
        Ok(_) => return Err(unsafe_path()),
    }
    Ok((source, target))
}

#[test]
fn native_consent_keeps_the_exact_owned_uuid_directory_pinned_until_producer_returns() {
    let (f, run, client) = copied_denial();
    let value = f.lookup(&client);
    let leaf = f.root().join(&run);
    // Genuine denied native provisional prefix, not a relabelled scripted run.
    // Snapshot BEFORE resume acquires run.lock; never read/skip a locked file.
    let before = inventory(&leaf);
    let (entered, observed) = mpsc::sync_channel(1);
    let (release, wait) = mpsc::sync_channel(1);
    let started = f
        .manager
        .full_comparison_resume_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            FullComparisonNativeResume {
                run_token: cap(&value).into(),
                max_new_scenes: 1,
            },
            move |_| {
                entered.send(()).map_err(|_| "Interrupted".to_owned())?;
                wait.recv_timeout(Duration::from_secs(60))
                    .map_err(|_| "Interrupted".to_owned())?;
                Ok(false)
            },
        )
        .unwrap();
    let entry = observed.recv_timeout(Duration::from_secs(30));
    let mut paths_checked = false;
    let mut rename_refused = false;
    let mut restored = true;
    if entry.is_ok() {
        if let Ok((source, target)) = checked_owned_move(&f, &run) {
            paths_checked = true;
            match fs::rename(&source, &target) {
                Err(_) => rename_refused = true,
                // Restore immediately, BEFORE releasing consent or asserting.
                Ok(()) => restored = fs::rename(&target, &source).is_ok(),
            }
        }
    }
    // Always release and positively drain before any assertion, including a
    // failed containment check or unexpectedly successful rename/failed restore.
    let _ = release.send(());
    let stopped = f.done(cap(&started));
    f.manager.drain(f.epoch);
    assert!(entry.is_ok(), "bounded consent entry");
    assert!(
        paths_checked,
        "only absolute contained ordinary owned fixture paths may move"
    );
    assert!(
        restored,
        "unexpectedly moved leaf must be restored before release"
    );
    assert!(
        rename_refused,
        "actual native directory pin must survive held consent"
    );
    assert_eq!(stopped["error"], "Cancelled");
    assert_eq!(stopped["report_ready"], false);
    assert!(f.manager.cleanup_complete() && f.models.cleanup_complete());
    assert!(inventory(&leaf) == before);
}
