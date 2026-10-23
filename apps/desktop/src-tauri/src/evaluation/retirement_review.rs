//! Independent regression over the actual manager retirement path. No worker or assets.
use super::*;

fn registered() -> (Arc<EvaluationManager>, Arc<WindowLease>, u64, Cancellation) {
    let manager = Arc::new(EvaluationManager::new(PathBuf::from(
        "unused-review-root-no-filesystem-access",
    )));
    let lease = Arc::new(WindowLease::default());
    let epoch = lease.begin().unwrap();
    let cancel = Cancellation::default();
    manager.state().unwrap().job = Some(Job {
        epoch,
        id: 1,
        run: "11111111-1111-1111-1111-111111111111".into(),
        cancel: cancel.clone(),
    });
    (manager, lease, epoch, cancel)
}

#[test]
fn retired_registered_job_is_cancelled_when_state_was_contended() {
    let (manager, lease, epoch, cancel) = registered();
    let guard = manager.state().unwrap();
    lease.invalidate("main-1").unwrap();
    let (ready_tx, ready_rx) = std::sync::mpsc::channel();
    let (done_tx, done_rx) = std::sync::mpsc::channel();
    let owner = manager.clone();
    let thread = std::thread::spawn(move || {
        ready_tx.send(()).unwrap();
        owner.retire(epoch);
        done_tx.send(()).unwrap();
    });
    ready_rx.recv_timeout(Duration::from_secs(1)).unwrap();
    // Either a nonblocking independent cancellation path returns now, or a safe
    // implementation waits for this lock. Both must cancel the registered job.
    let returned_while_held = done_rx.recv_timeout(Duration::from_millis(100)).is_ok();
    drop(guard);
    if !returned_while_held {
        done_rx.recv_timeout(Duration::from_secs(1)).unwrap();
    }
    thread.join().unwrap();
    assert!(
        cancel.is_cancelled(),
        "Destroyed retirement lost cancellation of a registered job while state was contended"
    );
}

#[test]
fn retired_registered_job_is_cancelled_when_state_was_poisoned() {
    let (manager, lease, epoch, cancel) = registered();
    let owner = manager.clone();
    let panic = std::thread::spawn(move || {
        let _guard = owner.state().unwrap();
        panic!("fixed review poison injection");
    });
    assert!(panic.join().is_err());
    lease.invalidate("main-1").unwrap();
    manager.retire(epoch);
    assert!(
        cancel.is_cancelled(),
        "Destroyed retirement lost cancellation of a registered job when state was poisoned"
    );
}
