//! Frozen phase1 ownership oracles against existing ModelManager APIs.
//! SOURCE ONLY / UNCOMPILED / UNRUN by this test author. No worker or model.
//! These metadata cases do not prove child termination or runtime cleanup.
use super::*;

fn metadata_manager() -> Arc<ModelManager> {
    // No directory, model, worker, or runtime is created. status() can only
    // inspect this newly named absent synthetic namespace.
    let root = std::env::temp_dir().join(format!(
        "locallore-model-pending-owner-{}",
        exports::identifier().expect("synthetic namespace")
    ));
    assert!(!root.exists());
    Arc::new(ModelManager::new(
        root.join("models"),
        root.join("resources"),
    ))
}

fn assert_metadata_owner(manager: &ModelManager, job: u64, phase: &str) {
    let status = manager.status().expect("native metadata status");
    assert_eq!(status["operation_id"], job);
    assert_eq!(status["phase"], phase);
    assert_eq!(status["resident"], false);
    assert_eq!(status["loaded"], false);
}

fn assert_replacement_busy(manager: &Arc<ModelManager>) {
    assert!(matches!(manager.begin("loading"), Err(error) if error == "Busy"));
    assert!(matches!(manager.reserve_evaluation(), Err(error) if error == "Busy"));
}

#[test]
fn retired_pending_startup_stays_unloading_until_original_cleanup_acknowledges() {
    let manager = metadata_manager();
    let (startup, cancel) = manager.begin("loading").expect("original loading job");
    assert_metadata_owner(&manager, startup, "loading");
    assert!(!cancel.load(Ordering::SeqCst));

    let retired = manager.retire().expect("retire original loading job");
    let retirement = retired.0;
    assert!(retirement > startup);
    assert!(retired.1.is_none(), "startup has not published a runtime");
    assert!(cancel.load(Ordering::SeqCst));
    assert_metadata_owner(&manager, retirement, "unloading");

    // The close worker has no runtime yet. That is not proof that the original
    // startup job has stopped or has acknowledged its prechild cleanup.
    manager.close(None, Some(retired));
    assert_metadata_owner(&manager, retirement, "unloading");
    assert_replacement_busy(&manager);

    // Only this matching original callback knows that its prechild cleanup is
    // complete. No actual child or cleanup-failure scenario is simulated here.
    manager.finish(startup, &Err("Cancelled".into()));
    let status = manager.status().expect("acknowledged metadata status");
    assert_eq!(status["phase"], "unloaded");
    assert_eq!(status["resident"], false);
    assert_eq!(status["loaded"], false);
    let reservation = manager
        .reserve_evaluation()
        .expect("matching cleanup permits evaluation reservation");
    assert_replacement_busy(&manager);
    drop(reservation);
    let (next, _) = manager.begin("loading").expect("replacement admission");
    assert!(next > retirement);
    manager.finish(next, &Err("Cancelled".into()));
}

#[test]
fn older_finish_and_close_cannot_release_newer_loading_or_retired_pending_owner() {
    let manager = metadata_manager();
    let (older, older_cancel) = manager.begin("loading").expect("older startup");
    let older_retired = manager.retire().expect("older retirement");
    assert!(older_retired.1.is_none());
    assert!(older_cancel.load(Ordering::SeqCst));
    manager.close(None, Some(older_retired.clone()));
    manager.finish(older, &Err("Cancelled".into()));
    assert_eq!(manager.status().unwrap()["phase"], "unloaded");

    let (current, current_cancel) = manager.begin("loading").expect("new startup");
    assert!(current > older_retired.0);
    assert_metadata_owner(&manager, current, "loading");
    assert!(!current_cancel.load(Ordering::SeqCst));

    // Duplicate callbacks carry only actual prior job/retirement identities;
    // they must not acknowledge the newer job or make replacement admissible.
    manager.finish(older, &Err("Cancelled".into()));
    manager.close(None, Some(older_retired));
    assert_metadata_owner(&manager, current, "loading");
    assert!(!current_cancel.load(Ordering::SeqCst));
    assert_replacement_busy(&manager);

    let current_retired = manager.retire().expect("current retirement");
    let retirement = current_retired.0;
    assert!(retirement > current);
    assert!(current_retired.1.is_none());
    manager.close(None, Some(current_retired));
    manager.finish(older, &Err("Cancelled".into()));
    assert_metadata_owner(&manager, retirement, "unloading");
    assert!(current_cancel.load(Ordering::SeqCst));
    assert_replacement_busy(&manager);

    manager.finish(current, &Err("Cancelled".into()));
    assert_eq!(manager.status().unwrap()["phase"], "unloaded");
    let reservation = manager
        .reserve_evaluation()
        .expect("only matching current cleanup releases exclusion");
    drop(reservation);
}
