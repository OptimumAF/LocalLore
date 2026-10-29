//! Closed read-only comparison IPC. Paths and grants belong to native code.
use crate::{
    evaluation::{
        ComparisonEvidenceRequest, ComparisonNarrationDiagnosticRequestV1, EvaluationManager,
    },
    WorkspaceState,
};
use locallore::inspection_query::{Observer, View};
use locallore_eval::local_lane::comparison::desktop_api::{Arm, Edge, EvidenceRequest, RowId};
use serde_json::Value;
use std::sync::Arc;

type Result<T> = std::result::Result<T, String>;
enum Action {
    Pick(String),
    Managed(String, String),
    Status(String),
    Source(String),
    Summary(String),
    Evidence(ComparisonEvidenceRequest),
    NarrationDiagnosticV1(ComparisonNarrationDiagnosticRequestV1),
    Close(String, Option<String>),
}
fn invalid<T>() -> Result<T> {
    Err("InvalidEvaluationInput".into())
}
fn keys<'a>(value: &'a Value, expected: &[&str]) -> Result<&'a serde_json::Map<String, Value>> {
    let map = value.as_object().ok_or("InvalidEvaluationInput")?;
    if map.len() != expected.len() || map.keys().any(|key| !expected.contains(&key.as_str())) {
        return invalid();
    }
    Ok(map)
}
fn text(value: &Value) -> Result<String> {
    value
        .as_str()
        .map(str::to_owned)
        .ok_or_else(|| "InvalidEvaluationInput".into())
}
fn guid(value: &Value) -> Result<String> {
    let id = text(value)?;
    if id.len() != 36
        || !id.bytes().enumerate().all(|(i, b)| {
            if [8, 13, 18, 23].contains(&i) {
                b == b'-'
            } else {
                b.is_ascii_digit() || (b'a'..=b'f').contains(&b)
            }
        })
    {
        return invalid();
    }
    Ok(id)
}
fn identifier(value: &Value) -> Result<String> {
    let id = text(value)?;
    if id.is_empty()
        || id.len() > 64
        || !id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
    {
        return invalid();
    }
    Ok(id)
}
fn observer(value: &Value) -> Result<Observer> {
    match value.get("kind").and_then(Value::as_str) {
        Some("character") => {
            keys(value, &["kind", "id"])?;
            identifier(&value["id"])?;
        }
        Some("player" | "omniscient") => {
            keys(value, &["kind"])?;
        }
        _ => return invalid(),
    }
    serde_json::from_value(value.clone()).map_err(|_| "InvalidEvaluationInput".into())
}
fn request(value: &Value) -> Result<EvidenceRequest> {
    match value.get("kind").and_then(Value::as_str) {
        Some("query") => {
            keys(value, &["kind", "edge", "observer", "view"])?;
            let edge = match value["edge"].as_str() {
                Some("before") => Edge::Before,
                Some("after") => Edge::After,
                _ => return invalid(),
            };
            let view: View = serde_json::from_value(value["view"].clone())
                .map_err(|_| "InvalidEvaluationInput")?;
            Ok(EvidenceRequest::Query {
                edge,
                observer: observer(&value["observer"])?,
                view,
            })
        }
        Some(kind @ ("receipt" | "capture" | "outputs")) => {
            keys(value, &["kind", "observer"])?;
            let observer = observer(&value["observer"])?;
            Ok(match kind {
                "receipt" => EvidenceRequest::Receipt { observer },
                "capture" => EvidenceRequest::Capture { observer },
                _ => EvidenceRequest::Outputs { observer },
            })
        }
        _ => invalid(),
    }
}
fn parse(action: &str, query: &Value) -> Result<Action> {
    if serde_json::to_vec(query)
        .map_err(|_| "InvalidEvaluationInput")?
        .len()
        > 4096
    {
        return invalid();
    }
    match action {
        "managed" => {
            keys(query, &["clientId", "runId"])?;
            Ok(Action::Managed(
                guid(&query["clientId"])?,
                guid(&query["runId"])?,
            ))
        }
        "pick" | "status" => {
            keys(query, &["clientId"])?;
            let client = guid(&query["clientId"])?;
            Ok(if action == "pick" {
                Action::Pick(client)
            } else {
                Action::Status(client)
            })
        }
        "source" | "summary" => {
            keys(query, &["runToken"])?;
            let token = guid(&query["runToken"])?;
            Ok(if action == "source" {
                Action::Source(token)
            } else {
                Action::Summary(token)
            })
        }
        "close" => {
            keys(query, &["clientId", "runToken"])?;
            let token = if query["runToken"].is_null() {
                None
            } else {
                Some(guid(&query["runToken"])?)
            };
            Ok(Action::Close(guid(&query["clientId"])?, token))
        }
        "narration_diagnostic_v1" => {
            keys(query, &["runToken", "binding", "turnId", "arm", "observer"])?;
            let binding = text(&query["binding"])?;
            if binding.len() != 64
                || !binding
                    .bytes()
                    .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            {
                return invalid();
            }
            let arm = match query["arm"].as_str() {
                Some("left") => Arm::Left,
                Some("right") => Arm::Right,
                _ => return invalid(),
            };
            Ok(Action::NarrationDiagnosticV1(ComparisonNarrationDiagnosticRequestV1 {
                token: guid(&query["runToken"])?,
                binding,
                row: RowId {
                    turn: identifier(&query["turnId"])?,
                    arm,
                },
                observer: observer(&query["observer"])?,
            }))
        }
        "evidence" => {
            keys(query, &["runToken", "binding", "turnId", "arm", "request"])?;
            let binding = text(&query["binding"])?;
            if binding.len() != 64
                || !binding
                    .bytes()
                    .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            {
                return invalid();
            }
            let arm = match query["arm"].as_str() {
                Some("left") => Arm::Left,
                Some("right") => Arm::Right,
                _ => return invalid(),
            };
            Ok(Action::Evidence(ComparisonEvidenceRequest {
                token: guid(&query["runToken"])?,
                binding,
                row: RowId {
                    turn: identifier(&query["turnId"])?,
                    arm,
                },
                request: request(&query["request"])?,
            }))
        }
        _ => invalid(),
    }
}
#[tauri::command]
pub async fn evaluation_comparison(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    action: String,
    query: Value,
) -> Result<Value> {
    let action = parse(&action, &query)?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let manager = manager.inner().clone();
    // Cleanup remains possible after eligibility is revoked; it cannot read data.
    if let Action::Close(client, token) = action {
        return tauri::async_runtime::spawn_blocking(move || {
            manager.comparison_close(&lease, epoch, &client, token.as_deref())
        })
        .await
        .map_err(|_| "EvaluationInternal".to_owned())?;
    }
    let host = workspace.get(epoch).await?;
    let granted = host.story_lab_granted();
    if !granted {
        return Err("Forbidden".into());
    }
    #[cfg(windows)]
    let owner = window.hwnd().map_err(|_| "Closed")?.0 as isize;
    #[cfg(not(windows))]
    let owner = 0;
    #[cfg(feature = "dev-harness")]
    let test = {
        use tauri::Manager;
        if crate::comparison_reader_harness::active() {
            Some((
                workspace.path.clone(),
                window
                    .state::<Arc<crate::comparison_reader_harness::ComparisonReaderHarness>>()
                    .inner()
                    .clone(),
            ))
        } else {
            None
        }
    };
    #[cfg(feature = "dev-harness")]
    let lose_ack = test.as_ref().map(|(_, state)| state.clone());
    #[cfg(feature = "dev-harness")]
    let is_pick = matches!(&action, Action::Pick(_));
    let result = tauri::async_runtime::spawn_blocking(move || match action {
        Action::Managed(client, run) => {
            #[cfg(feature = "dev-harness")]
            let consent_manager = manager.clone();
            manager.full_comparison_pick(&lease, epoch, granted, &client, &run, move || {
                #[cfg(feature = "dev-harness")]
                if crate::harness::active()
                    && std::env::var("LOCALLORE_D07_FULL_COMPARISON_HARNESS").as_deref() == Ok("1")
                {
                    return Ok(!consent_manager.take_full_read_denial());
                }
                crate::exports::confirm_comparison_read(owner)
            })
        }
        Action::Pick(client) => {
            manager.comparison_pick(&lease, epoch, granted, &client, move || {
                #[cfg(feature = "dev-harness")]
                if let Some((path, state)) = test {
                    return crate::comparison_reader_harness::choose(&path, &state);
                }
                crate::exports::choose_comparison_directory(owner)
            })
        }
        Action::Status(client) => manager.comparison_status(&lease, epoch, granted, &client),
        Action::Source(token) => manager.comparison_source(&lease, epoch, granted, &token),
        Action::Summary(token) => manager.comparison_summary(&lease, epoch, granted, &token),
        Action::Evidence(input) => manager.comparison_evidence(&lease, epoch, granted, input),
        Action::NarrationDiagnosticV1(input) => {
            manager.comparison_narration_diagnostic_v1(&lease, epoch, granted, input)
        }
        Action::Close(_, _) => Err("EvaluationInternal".into()),
    })
    .await
    .map_err(|_| "EvaluationInternal".to_owned())?;
    #[cfg(feature = "dev-harness")]
    if is_pick
        && result.is_ok()
        && lose_ack
            .as_ref()
            .is_some_and(|state| crate::comparison_reader_harness::take_lost_ack(state))
    {
        return Err("EvaluationIo".into());
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    const ID: &str = "00000000-0000-0000-0000-000000000001";
    #[test]
    fn managed_read_accepts_only_native_run_identity_not_paths_or_grants() {
        assert!(parse("managed", &json!({"clientId":ID,"runId":ID})).is_ok());
        for value in [
            json!({"clientId":ID,"runId":"../outside"}),
            json!({"clientId":ID,"runId":ID,"grant":true}),
            json!({"clientId":ID,"runId":ID,"path":"synthetic"}),
            json!({"clientId":ID}),
            json!({"clientId":ID,"runId":null}),
        ] {
            assert!(parse("managed", &value).is_err());
        }
    }
    #[test]
    fn closed_requests_refuse_execution_paths_grants_and_coercion() {
        for action in ["start", "resume", "rerun", "run", "shell", "open"] {
            assert!(parse(action, &json!({"clientId":ID})).is_err());
        }
        for value in [
            json!(null),
            json!([]),
            json!({"clientId":ID,"path":"synthetic"}),
            json!({"clientId":ID,"grant":true}),
            json!({"clientId":false}),
        ] {
            assert!(parse("pick", &value).is_err());
        }
        assert!(parse("pick", &json!({"clientId":ID})).is_ok());
        assert!(parse("close", &json!({"clientId":ID,"runToken":null})).is_ok());
    }
    #[test]
    fn evidence_observer_edge_and_exact_shape_are_checked_before_work() {
        let valid = json!({"runToken":ID,"binding":"a".repeat(64),"turnId":"turn-01","arm":"left",
            "request":{"kind":"query","edge":"before","observer":{"kind":"character","id":"mira"},"view":"knowledge"}});
        assert!(parse("evidence", &valid).is_ok());
        for (key, value) in [
            ("arm", json!("LEFT")),
            ("binding", json!("A".repeat(64))),
            ("turnId", json!("../other")),
        ] {
            let mut changed = valid.clone();
            changed[key] = value;
            assert!(parse("evidence", &changed).is_err());
        }
        for value in [
            json!({"kind":"query","edge":"after","observer":{"kind":"player","grant":true},"view":"history"}),
            json!({"kind":"capture","observer":{"kind":"omniscient"},"path":"synthetic"}),
            json!({"kind":"query","edge":"before","observer":{"kind":"player"},"view":true}),
        ] {
            let mut changed = valid.clone();
            changed["request"] = value;
            assert!(parse("evidence", &changed).is_err());
        }
    }
}
