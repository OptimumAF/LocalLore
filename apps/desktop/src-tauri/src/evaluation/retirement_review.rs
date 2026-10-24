//! Independent actual-admission retirement regression. Scripted worker only; no model/assets/GUI.
use super::*;

struct Root(PathBuf);
impl Drop for Root {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}
struct Admitted {
    _root: Root,
    manager: Arc<EvaluationManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
    cancel: Cancellation,
    release: Arc<std::sync::Barrier>,
}
fn registered() -> Admitted {
    let path =
        std::env::temp_dir().join(format!("evaluation-retirement-review-{}", uuid().unwrap()));
    fs::create_dir(&path).unwrap();
    let root = Root(path);
    let manager = Arc::new(EvaluationManager::new(root.0.join("runs")));
    let lease = Arc::new(WindowLease::default());
    let epoch = lease.begin().unwrap();
    manager.catalog(&lease, epoch).unwrap();
    // Reuse the real worker's existing pre-publication barrier so completion
    // cannot erase the actual admitted job before retirement observes it.
    let entered = Arc::new(std::sync::Barrier::new(2));
    let release = Arc::new(std::sync::Barrier::new(2));
    *manager.before_publish.lock().unwrap() = Some((entered.clone(), release.clone()));
    manager.start(&lease, epoch, None, "all").unwrap();
    entered.wait();
    let cancel = manager
        .state()
        .unwrap()
        .job
        .as_ref()
        .unwrap()
        .cancel
        .clone();
    Admitted {
        _root: root,
        manager,
        lease,
        epoch,
        cancel,
        release,
    }
}

#[test]
fn retired_registered_job_is_cancelled_when_state_was_contended() {
    let Admitted {
        _root,
        manager,
        lease,
        epoch,
        cancel,
        release,
    } = registered();
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
    release.wait();
    manager.drain(epoch);
    assert!(
        cancel.is_cancelled(),
        "Destroyed retirement lost cancellation of a registered job while state was contended"
    );
}

#[test]
fn retired_registered_job_is_cancelled_when_state_was_poisoned() {
    let Admitted {
        _root,
        manager,
        lease,
        epoch,
        cancel,
        release,
    } = registered();
    let owner = manager.clone();
    let panic = std::thread::spawn(move || {
        let _guard = owner.state().unwrap();
        panic!("fixed review poison injection");
    });
    assert!(panic.join().is_err());
    lease.invalidate("main-1").unwrap();
    manager.retire(epoch);
    release.wait();
    manager.drain(epoch);
    assert!(
        cancel.is_cancelled(),
        "Destroyed retirement lost cancellation of a registered job when state was poisoned"
    );
}
