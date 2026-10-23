//! Fixed native fork adapter. Canonical authority remains in Host/Store.
//! Uses the existing archive worker/registration/lifetime owner; no new Store.
use crate::{archive::ArchiveBroker, WorkspaceState};
use locallore::{
    contracts::Scope,
    host::{Host, WorkspaceForkRequest},
};
use serde_json::{json, Value};
use std::sync::Arc;

const MAX_SAFE: u64 = 9_007_199_254_740_991;
fn id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}
pub fn request(value: &Value) -> Result<WorkspaceForkRequest, String> {
    let object = value.as_object().ok_or("InvalidForkInput")?;
    let keys = [
        "parent",
        "child_branch",
        "expected_parent_revision",
        "at_revision",
    ];
    if object.len() != keys.len() || object.keys().any(|k| !keys.contains(&k.as_str())) {
        return Err("InvalidForkInput".into());
    }
    // Borrow/validate bounded IDs before copying any renderer-owned strings.
    let parent_object = value["parent"].as_object().ok_or("InvalidForkInput")?;
    if parent_object.len() != 2
        || parent_object
            .keys()
            .any(|k| !["story", "branch"].contains(&k.as_str()))
    {
        return Err("InvalidForkInput".into());
    }
    let story = value["parent"]["story"]
        .as_str()
        .filter(|v| id(v))
        .ok_or("InvalidForkInput")?;
    let branch = value["parent"]["branch"]
        .as_str()
        .filter(|v| id(v))
        .ok_or("InvalidForkInput")?;
    let child = value["child_branch"].as_str().ok_or("InvalidForkInput")?;
    let expected = value["expected_parent_revision"]
        .as_u64()
        .filter(|v| *v <= MAX_SAFE)
        .ok_or("InvalidForkInput")?;
    let at = value["at_revision"]
        .as_u64()
        .filter(|v| *v <= expected)
        .ok_or("InvalidForkInput")?;
    if !id(child) || child == branch {
        return Err("InvalidForkInput".into());
    }
    Ok(WorkspaceForkRequest {
        parent: Scope {
            story: story.to_owned(),
            branch: branch.to_owned(),
        },
        child_branch: child.into(),
        expected_parent_revision: expected,
        at_revision: at,
    })
}
pub fn execute(
    host: &Host,
    session: &str,
    input: &WorkspaceForkRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<Value, String> {
    if session.is_empty() || session.len() > 128 {
        return Err("InvalidForkInput".into());
    }
    // Store's committed return wins a late cancel; never replace it with Cancelled.
    let outcome = host.fork_branch(session, input, cancel)?;
    Ok(json!({"kind":"fork", "outcome":outcome}))
}
pub fn lookup(host: &Host, input: &WorkspaceForkRequest) -> Result<Value, String> {
    // Read-only public catalog. This path never calls fork_branch, even if absent.
    // Parent head may have advanced; immutable parent/fork/child identity is enough.
    let reply = host.call(
        &serde_json::to_vec(
            &json!({"version":1,"command":{"op":"branches","story":input.parent.story}}),
        )
        .map_err(|_| "Internal")?,
    );
    if reply["status"] != "ok" {
        return Err(reply["error"].as_str().unwrap_or("Internal").to_owned());
    }
    let row = reply["data"]["branches"]
        .as_array()
        .ok_or("Internal")?
        .iter()
        .find(|row| row["scope"]["branch"] == input.child_branch);
    match row {
        None => Ok(json!({"version":1,"kind":"fork_lookup","found":false,"outcome":null})),
        Some(row) => {
            if row["parent_branch"] != input.parent.branch
                || row["fork_revision"].as_u64() != Some(input.at_revision)
            {
                return Err("Mismatch".into());
            }
            if row["retired"] != false {
                return Err("Closed".into());
            }
            let head = row["revision"].as_u64().ok_or("Internal")?;
            Ok(
                json!({"version":1,"kind":"fork_lookup","found":true,"outcome":{"version":1,"scope":{"story":input.parent.story,"branch":input.child_branch},"parent":input.parent,"fork_revision":input.at_revision,"head_revision":head,"created":false}}),
            )
        }
    }
}
#[tauri::command]
pub async fn fork_start(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    session: String,
    input: Value,
    consent: bool,
) -> Result<Value, String> {
    if !consent {
        return Err("ForkConsentRequired".into());
    }
    let input = request(&input)?;
    if session.is_empty() || session.len() > 128 {
        return Err("InvalidForkInput".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    #[cfg(feature = "dev-harness")]
    let fixture = {
        use tauri::Manager;
        crate::fork_harness::active().then(|| {
            window
                .state::<Arc<crate::fork_harness::ForkHarnessState>>()
                .inner()
                .clone()
        })
    };
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        #[cfg(feature = "dev-harness")]
        let lose_ack = fixture
            .as_ref()
            .is_some_and(|s| s.lose_ack.swap(false, std::sync::atomic::Ordering::SeqCst));
        #[cfg(feature = "dev-harness")]
        let status_lease = lease.clone();
        let result = broker.start(lease, epoch, move |work| {
            work.phase("forking")?;
            #[cfg(feature = "dev-harness")]
            if let Some(fixture) = fixture {
                let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
                while fixture.hold.load(std::sync::atomic::Ordering::SeqCst) {
                    work.check()?;
                    if std::time::Instant::now() >= deadline {
                        return Err("Transport".into());
                    }
                    std::thread::sleep(std::time::Duration::from_millis(5));
                }
            }
            execute(&host, &session, &input, &|| work.cancelled())
        });
        #[cfg(feature = "dev-harness")]
        if lose_ack {
            let id = result
                .as_ref()
                .ok()
                .and_then(|v| v["operation_id"].as_u64())
                .ok_or("SyntheticStart")?;
            for _ in 0..1000 {
                let status = broker.status(&status_lease, epoch, id)?;
                if status["running"] == false {
                    if status["error"] != Value::Null {
                        return Err("SyntheticForkFailed".into());
                    }
                    return Err("Transport".into());
                }
                std::thread::sleep(std::time::Duration::from_millis(5));
            }
            return Err("SyntheticTimeout".into());
        }
        result
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}
#[tauri::command]
pub async fn fork_lookup(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    input: Value,
) -> Result<Value, String> {
    let input = request(&input)?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || lease.dispatch(epoch, || lookup(&host, &input)))
        .await
        .map_err(|_| "Transport".to_owned())?
}
// Status/cancel reuse archive_status/archive_cancel with the returned operation_id.
// The root integration must register only these two closed commands.

#[cfg(test)]
mod fork_adapter_tests {
    use super::*;
    use crate::lease::WindowLease;
    use std::sync::{
        atomic::{AtomicU64, Ordering},
        mpsc,
    };
    use std::time::{Duration, Instant};
    static NEXT: AtomicU64 = AtomicU64::new(0);
    fn database() -> std::path::PathBuf {
        // Bounded synthetic test evidence, retained under caller-owned TEMP.
        let root = std::env::temp_dir().join(format!(
            "locallore-desktop-fork-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        root.join("synthetic.sqlite")
    }
    fn call(host: &Host, command: Value) -> Value {
        host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
    }
    fn create(host: &Host) -> (String, Scope) {
        let value = call(host, json!({"op":"create","seed":"lantern-quay-v1"}));
        assert_eq!(value["status"], "ok", "{value}");
        (
            value["data"]["session"].as_str().unwrap().to_owned(),
            serde_json::from_value(value["data"]["scope"].clone()).unwrap(),
        )
    }
    fn fork(parent: &Scope, expected: u64, at: u64) -> WorkspaceForkRequest {
        request(&json!({"parent":parent,"child_branch":"fixed-child","expected_parent_revision":expected,"at_revision":at})).unwrap()
    }
    fn wait(host: &Host, session: &str, scope: &Scope, head: u64, turn: &str) {
        let value = call(
            host,
            json!({"op":"submit","session":session,"request":{"version":1,"scope":scope,"turn":turn,"expected_revision":head,"intent":{"kind":"actions","value":[{"op":"wait","ticks":1}]}},"mode":"accepted"}),
        );
        assert_eq!(value["data"]["phase"], "queued", "{value}");
        for (op, phase) in [("prepare", "ready"), ("commit", "committed")] {
            let value = call(
                host,
                json!({"op":op,"session":session,"scope":scope,"turn":turn}),
            );
            assert_eq!(value["data"]["phase"], phase, "{value}");
        }
    }
    fn settled(broker: &ArchiveBroker, lease: &WindowLease, epoch: u64, operation: u64) -> Value {
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            let value = broker.status(lease, epoch, operation).unwrap();
            if value["running"] == false {
                return value;
            }
            assert!(Instant::now() < deadline, "fork test worker did not settle");
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn input() -> Value {
        json!({"parent":{"story":"s","branch":"main"},"child_branch":"fixed-child","expected_parent_revision":2,"at_revision":1})
    }
    #[test]
    fn closed_input_and_no_json_author_fields() {
        let good = input();
        assert_eq!(request(&good).unwrap().child_branch, "fixed-child");
        for (key, value) in [
            ("observer", json!("omniscient")),
            ("author", json!(true)),
            ("path", json!("x")),
        ] {
            let mut bad = input();
            bad[key] = value;
            assert!(request(&bad).is_err());
        }
        for (key, value) in [
            ("child_branch", json!("main")),
            ("child_branch", json!("../x")),
            ("at_revision", json!(3)),
            ("expected_parent_revision", json!(9_007_199_254_740_992u64)),
        ] {
            let mut bad = input();
            bad[key] = value;
            assert!(request(&bad).is_err());
        }
        let mut bad = input();
        bad["parent"]["observer"] = json!("player");
        assert!(request(&bad).is_err());
        let mut bad = input();
        bad["parent"]["story"] = json!("s".repeat(65));
        assert!(request(&bad).is_err());
        let mut bad = input();
        bad["parent"]["branch"] = json!("b".repeat(65));
        assert!(request(&bad).is_err());
    }
    #[test]
    fn ephemeral_caller_does_not_gain_fork_or_inspection_authority() {
        let host = Host::new(false);
        let input = request(&input()).unwrap();
        assert_eq!(
            execute(&host, "missing", &input, &|| false),
            Err("Closed".into())
        );
        assert_eq!(lookup(&host, &input), Err("Unsupported".into()));
    }
    #[test]
    fn actual_store_discarded_ack_restart_lookup_and_exact_retry_current_head() {
        let path = database();
        let host = locallore_workspace::open(&path, false).unwrap();
        let (session, parent) = create(&host);
        let input = fork(&parent, 0, 0);
        assert_eq!(lookup(&host, &input).unwrap()["found"], false);
        assert_eq!(
            call(&host, json!({"op":"branches","story":parent.story}))["data"]["branches"]
                .as_array()
                .unwrap()
                .len(),
            1
        );
        let answer = execute(&host, &session, &input, &|| false).unwrap();
        assert_eq!(answer["outcome"]["created"], true);
        // Drop the actual outcome and actual owner, simulating lost acknowledgement.
        drop(answer);
        drop(host);
        let host = locallore_workspace::open(&path, false).unwrap();
        let found = lookup(&host, &input).unwrap();
        assert_eq!(found["found"], true);
        assert_eq!(found["outcome"]["created"], false);
        let child: Scope = serde_json::from_value(found["outcome"]["scope"].clone()).unwrap();
        let child_session = call(&host, json!({"op":"resume","scope":child}))["data"]["session"]
            .as_str()
            .unwrap()
            .to_owned();
        wait(&host, &child_session, &child, 0, "child-after-restart");
        let parent_session = call(&host, json!({"op":"resume","scope":parent}))["data"]["session"]
            .as_str()
            .unwrap()
            .to_owned();
        wait(&host, &parent_session, &parent, 0, "parent-after-restart");
        let retry = execute(&host, &parent_session, &input, &|| false).unwrap();
        assert_eq!(retry["outcome"]["head_revision"], 1);
        assert_eq!(retry["outcome"]["created"], false);
        assert_eq!(
            lookup(&host, &input).unwrap()["outcome"]["head_revision"],
            1
        );
        let mut store = locallore_storage::Store::open_read_only(&path).unwrap();
        let child_engine = store.resume(&child).unwrap().engine;
        let parent_engine = store.resume(&parent).unwrap().engine;
        assert_eq!(child_engine.receipts().len(), 1);
        assert_eq!(parent_engine.receipts().len(), 1);
        assert_ne!(
            child_engine.receipts()[0].request().turn,
            parent_engine.receipts()[0].request().turn
        );
        let mut mismatch = input.clone();
        mismatch.at_revision = 1;
        assert_eq!(lookup(&host, &mismatch), Err("Mismatch".into()));
        assert_eq!(
            call(&host, json!({"op":"branches","story":parent.story}))["data"]["branches"]
                .as_array()
                .unwrap()
                .len(),
            2
        );
    }
    #[test]
    fn actual_store_closed_session_stale_and_cancel_do_not_create_child() {
        let path = database();
        let host = locallore_workspace::open(&path, false).unwrap();
        let (session, parent) = create(&host);
        assert_eq!(
            execute(&host, "foreign-session", &fork(&parent, 0, 0), &|| false),
            Err("Closed".into())
        );
        assert_eq!(
            execute(&host, &session, &fork(&parent, 1, 0), &|| false),
            Err("Stale".into())
        );
        assert_eq!(
            execute(&host, &session, &fork(&parent, 0, 0), &|| true),
            Err("Cancelled".into())
        );
        assert_eq!(lookup(&host, &fork(&parent, 0, 0)).unwrap()["found"], false);
        assert_eq!(
            locallore_storage::Store::open_read_only(&path)
                .unwrap()
                .resume(&parent)
                .unwrap()
                .engine
                .revision(),
            0
        );
    }
    #[test]
    fn existing_broker_pending_cancel_and_commit_wins_late_cancel() {
        let path = database();
        let host = Arc::new(locallore_workspace::open(&path, false).unwrap());
        let (session, parent) = create(&host);
        let input = fork(&parent, 0, 0);
        let broker = Arc::new(ArchiveBroker::default());
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let (entered_tx, entered_rx) = mpsc::channel();
        let (release_tx, release_rx) = mpsc::channel();
        let copy = host.clone();
        let selected = session.clone();
        let first = input.clone();
        let value = broker
            .start(lease.clone(), epoch, move |work| {
                entered_tx.send(()).unwrap();
                release_rx.recv_timeout(Duration::from_secs(5)).unwrap();
                execute(&copy, &selected, &first, &|| work.cancelled())
            })
            .unwrap();
        let operation = value["operation_id"].as_u64().unwrap();
        entered_rx.recv_timeout(Duration::from_secs(5)).unwrap();
        assert_eq!(
            broker.start(lease.clone(), epoch, |_| Ok(json!({}))),
            Err("ArchiveBusy".into())
        );
        broker.cancel(&lease, epoch, operation).unwrap();
        release_tx.send(()).unwrap();
        assert_eq!(
            settled(&broker, &lease, epoch, operation)["error"],
            "Cancelled"
        );
        assert_eq!(lookup(&host, &input).unwrap()["found"], false);
        let copy = host.clone();
        let selected = session.clone();
        let next = input.clone();
        let value = broker
            .start(lease.clone(), epoch, move |work| {
                execute(&copy, &selected, &next, &|| work.cancelled())
            })
            .unwrap();
        let operation = value["operation_id"].as_u64().unwrap();
        let committed = settled(&broker, &lease, epoch, operation);
        assert_eq!(committed["result"]["outcome"]["created"], true);
        assert_eq!(
            broker.cancel(&lease, epoch, operation).unwrap()["result"],
            committed["result"]
        );
        broker.drain(epoch);
        assert_eq!(lookup(&host, &input).unwrap()["found"], true);
    }
    #[test]
    fn existing_broker_window_retirement_cancels_queued_actual_store_fork() {
        let path = database();
        let host = Arc::new(locallore_workspace::open(&path, false).unwrap());
        let (session, parent) = create(&host);
        let input = fork(&parent, 0, 0);
        let broker = Arc::new(ArchiveBroker::default());
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let (entered_tx, entered_rx) = mpsc::channel();
        let (release_tx, release_rx) = mpsc::channel();
        let copy = host.clone();
        let selected = session.clone();
        let first = input.clone();
        let value = broker
            .start(lease.clone(), epoch, move |work| {
                entered_tx.send(()).unwrap();
                release_rx.recv_timeout(Duration::from_secs(5)).unwrap();
                execute(&copy, &selected, &first, &|| work.cancelled())
            })
            .unwrap();
        let operation = value["operation_id"].as_u64().unwrap();
        entered_rx.recv_timeout(Duration::from_secs(5)).unwrap();
        let closed = lease.invalidate(&format!("main-{epoch}")).unwrap();
        broker.retire(epoch);
        release_tx.send(()).unwrap();
        broker.drain(epoch);
        assert_eq!(
            broker.status(&lease, epoch, operation),
            Err("Closed".into())
        );
        lease.finish_close(closed, || host.close_all());
        assert_eq!(lookup(&host, &input).unwrap()["found"], false);
        assert!(lease.begin().is_ok());
    }
}
