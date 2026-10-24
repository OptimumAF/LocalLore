// Native owner lifecycle oracles, frozen before the IPC owner implementation.
// Actual local Host/Repository and runtime executor, no window or WebView launch.
use super::*;

fn workspace() -> WorkspaceState {
    let root = std::env::temp_dir().join(format!(
        "locallore-author-ipc-{}-{}", std::process::id(), exports::identifier().unwrap()
    ));
    WorkspaceState {
        path: root.join("synthetic.sqlite"),
        lease: Arc::new(WindowLease::default()),
        host: tokio::sync::OnceCell::new(),
        preview_cleanup: Arc::new(std::sync::Mutex::new(json!({"pending":true}))),
        author: std::sync::Mutex::new(None),
    }
}

#[test]
fn one_window_reuses_its_actual_host_and_shared_worker_and_rejects_a_foreign_worker() {
    let state = workspace();
    let epoch = state.lease.begin().unwrap();
    let broker = Arc::new(archive::ArchiveBroker::default());
    let (host, first) = tauri::async_runtime::block_on(state.author_manager(epoch, &broker)).unwrap();
    let (same_host, same) = tauri::async_runtime::block_on(state.author_manager(epoch, &broker)).unwrap();
    assert!(Arc::ptr_eq(&host, &same_host));
    assert!(Arc::ptr_eq(&first, &same));
    assert_eq!(host.call(br#"{"version":1,"command":{"op":"workspace"}}"#)["data"]["stories"], json!([]));
    let foreign = Arc::new(archive::ArchiveBroker::default());
    let error = tauri::async_runtime::block_on(state.author_manager(epoch, &foreign)).err();
    assert_eq!(error.as_deref(), Some("Integrity"));
    let (_, after) = tauri::async_runtime::block_on(state.author_manager(epoch, &broker)).unwrap();
    assert!(Arc::ptr_eq(&first, &after));
}

#[test]
fn destroyed_window_cannot_reuse_an_author_manager_and_reopen_gets_a_new_owner() {
    let state = workspace();
    let epoch = state.lease.begin().unwrap();
    let broker = Arc::new(archive::ArchiveBroker::default());
    let (host, first) = tauri::async_runtime::block_on(state.author_manager(epoch, &broker)).unwrap();
    let closed = state.lease.invalidate(&format!("main-{epoch}")).unwrap();
    state.retire_author(epoch);
    assert_eq!(tauri::async_runtime::block_on(state.author_manager(epoch, &broker)).err().as_deref(), Some("Closed"));
    state.lease.finish_close(closed, || {});
    let next = state.lease.begin().unwrap();
    let (same_host, replacement) = tauri::async_runtime::block_on(state.author_manager(next, &broker)).unwrap();
    assert!(Arc::ptr_eq(&host, &same_host));
    assert!(!Arc::ptr_eq(&first, &replacement));
    assert_eq!(first.check_binding(&host, &state.lease, &broker, next).err().as_deref(), Some("Closed"));
    replacement.check_binding(&host, &state.lease, &broker, next).unwrap();
}
