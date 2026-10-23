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
    let parent: Scope =
        serde_json::from_value(value["parent"].clone()).map_err(|_| "InvalidForkInput")?;
    let child = value["child_branch"].as_str().ok_or("InvalidForkInput")?;
    let expected = value["expected_parent_revision"]
        .as_u64()
        .filter(|v| *v <= MAX_SAFE)
        .ok_or("InvalidForkInput")?;
    let at = value["at_revision"]
        .as_u64()
        .filter(|v| *v <= expected)
        .ok_or("InvalidForkInput")?;
    if !id(&parent.story) || !id(&parent.branch) || !id(child) || child == parent.branch {
        return Err("InvalidForkInput".into());
    }
    Ok(WorkspaceForkRequest {
        parent,
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
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        broker.start(lease, epoch, move |work| {
            work.phase("forking")?;
            execute(&host, &session, &input, &|| work.cancelled())
        })
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
}
