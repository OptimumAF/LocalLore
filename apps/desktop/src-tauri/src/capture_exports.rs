//! Exact private trace preview. Native Host reads only; no renderer bytes or paths.
use crate::{
    exports::{self, ExportBroker},
    WorkspaceState,
};
use locallore::{contracts::Scope, host::Host};
use serde_json::{json, Value};
use std::sync::Arc;
#[cfg(feature = "dev-harness")]
use tauri::Manager;
#[derive(Default)]
pub struct CaptureBroker(ExportBroker);
impl CaptureBroker {
    pub fn invalidate(&self, epoch: u64) {
        self.0.invalidate(epoch);
    }
    fn preview(
        &self,
        host: &Host,
        epoch: u64,
        query: Value,
        current: impl FnOnce() -> bool,
    ) -> Result<Value, String> {
        let bytes = serde_json::to_vec(&json!({"version":1,"command":query}))
            .map_err(|_| "InvalidInput")?;
        let reply = host.call(&bytes);
        if reply["version"] != 1 || reply["status"] != "ok" {
            return Err(reply["error"].as_str().unwrap_or("Wire").to_owned());
        }
        let data = reply["data"].clone();
        validate(&data, &query)?;
        if !["recorded", "truncated"].contains(&data["details"]["status"].as_str().unwrap_or("")) {
            return Err("CaptureNotRetained".into());
        }
        self.0.insert_capture(epoch, data, current)
    }
}
fn keys(v: &Value, expected: &[&str]) -> bool {
    v.as_object()
        .is_some_and(|v| v.len() == expected.len() && expected.iter().all(|k| v.contains_key(*k)))
}
fn validate(v: &Value, q: &Value) -> Result<(), String> {
    let d = &v["details"];
    if !keys(
        v,
        &["scope", "head", "base_revision", "observer", "details"],
    ) || v["scope"] != q["scope"]
        || v["head"] != q["expected_head"]
        || v["base_revision"] != q["base_revision"]
        || v["observer"] != "private_player_generation_capture"
        || !keys(
            d,
            &[
                "version",
                "status",
                "identity",
                "artifacts",
                "exact_reconstruction",
                "privacy",
            ],
        )
        || d["version"] != 1
        || d["exact_reconstruction"] != false
        || d["privacy"].as_str().is_none_or(|s| s.len() > 512)
        || serde_json::to_vec(v).map_or(true, |b| b.len() > 262144)
    {
        return Err("Wire".into());
    }
    let status = d["status"].as_str().ok_or("Wire")?;
    if ![
        "disabled",
        "expired",
        "not_retained",
        "recorded",
        "truncated",
    ]
    .contains(&status)
    {
        return Err("Wire".into());
    }
    let retained = ["recorded", "truncated"].contains(&status);
    let i = &d["identity"];
    if retained {
        if !keys(
            i,
            &["scope", "base_revision", "observer", "turn", "attempt"],
        ) || i["scope"] != q["scope"]
            || i["base_revision"] != q["base_revision"]
            || i["turn"] != q["turn"]
            || i["attempt"] != q["attempt"]
            || i["observer"].as_str().is_none_or(|s| {
                s.is_empty()
                    || s.len() > 64
                    || !s
                        .bytes()
                        .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
            })
        {
            return Err("Wire".into());
        }
    } else if !i.is_null() {
        return Err("Wire".into());
    }
    let artifacts = d["artifacts"].as_array().ok_or("Wire")?;
    if artifacts.len() > 16 || (!retained && !artifacts.is_empty()) {
        return Err("Wire".into());
    }
    for (ordinal, a) in artifacts.iter().enumerate() {
        if !keys(a, &["kind", "ordinal", "value"])
            || a["ordinal"] != ordinal
            || ![
                "selected_context",
                "generation_request",
                "raw_director_output",
                "parsed_proposal",
                "validated_plan_not_durable_commit",
                "accepted_candidate_not_durable_commit",
                "raw_narrator_output",
            ]
            .contains(&a["kind"].as_str().unwrap_or(""))
            || serde_json::to_vec(a).map_or(true, |b| b.len() > 49152)
        {
            return Err("Wire".into());
        }
    }
    Ok(())
}
#[tauri::command]
pub async fn capture_preview(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<CaptureBroker>>,
    selection: Value,
) -> Result<Value, String> {
    if !keys(
        &selection,
        &[
            "session",
            "scope",
            "expected_head",
            "base_revision",
            "turn",
            "attempt",
        ],
    ) {
        return Err("InvalidInput".into());
    }
    let session = selection["session"]
        .as_str()
        .ok_or("InvalidInput")?
        .to_owned();
    let scope = selection["scope"].clone();
    let expected_head = selection["expected_head"].as_u64().ok_or("InvalidInput")?;
    let base_revision = selection["base_revision"].as_u64().ok_or("InvalidInput")?;
    let turn = selection["turn"].as_str().ok_or("InvalidInput")?.to_owned();
    let attempt = selection["attempt"].as_u64().ok_or("InvalidInput")?;
    if session.is_empty()
        || session.len() > 128
        || turn.is_empty()
        || turn.len() > 64
        || !turn
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
        || attempt > u32::MAX as u64
        || expected_head > 9_007_199_254_740_991
        || base_revision > expected_head
        || !keys(&scope, &["story", "branch"])
    {
        return Err("InvalidInput".into());
    }
    let scope: Scope = serde_json::from_value(scope).map_err(|_| "Scope")?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    tauri::async_runtime::spawn_blocking(move || lease.dispatch(epoch, || {
        broker.preview(&host, epoch, json!({"op":"trace_capture_read","session":session,"scope":scope,"expected_head":expected_head,"base_revision":base_revision,"turn":turn,"attempt":attempt}), || lease.valid(epoch))
    })).await.map_err(|_| "Transport".to_owned())?
}
#[tauri::command]
pub fn capture_revoke(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<CaptureBroker>>,
    token: Option<String>,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    workspace.lease.dispatch(epoch, || {
        if let Some(token) = token {
            broker.0.cancel(epoch, &token)?;
        } else {
            broker.invalidate(epoch);
        }
        Ok(json!({"revoked":true}))
    })
}
#[tauri::command]
pub async fn capture_save(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<CaptureBroker>>,
    token: String,
    consent: bool,
) -> Result<Value, String> {
    if !consent {
        return Err("CaptureConsentRequired".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let record = broker.0.get(epoch, &token)?;
    let lease = workspace.lease.clone();
    #[cfg(windows)]
    let owner = window.hwnd().map_err(|_| "Closed")?.0 as isize;
    #[cfg(not(windows))]
    let owner = 0;
    #[cfg(feature = "dev-harness")]
    let scenario = window
        .state::<TestCaptureState>()
        .0
        .lock()
        .map_err(|_| "Internal")?
        .clone();
    tauri::async_runtime::spawn_blocking(move || {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        #[cfg(feature = "dev-harness")]
        let destination = if crate::harness::active()
            && std::env::var("LOCALLORE_D06_CAPTURE_HARNESS").as_deref() == Ok("1")
        {
            if scenario == "export-cancel" {
                None
            } else {
                Some(std::path::PathBuf::from(
                    std::env::var_os("LOCALLORE_D06_CAPTURE_EXPORT_ROOT").ok_or("InvalidInput")?,
                ))
            }
        } else {
            exports::choose_directory(owner)?
        };
        #[cfg(not(feature = "dev-harness"))]
        let destination = exports::choose_directory(owner)?;
        let Some(destination) = destination else {
            return Ok(json!({"status":"cancelled"}));
        };
        record.save(&destination, |handle, stage, target| {
            lease.dispatch(epoch, || exports::atomic_finalize(handle, stage, target))
        })
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}

// Fixed trusted synthetic provider uses the real Host→Play/compiler/validation path.
// It is absent from normal builds and accepts no model, file or arbitrary output.
#[cfg(any(test, feature = "dev-harness"))]
static SYNTHETIC_PENDING_OBSERVED: std::sync::atomic::AtomicBool =
    std::sync::atomic::AtomicBool::new(false);
#[cfg(any(test, feature = "dev-harness"))]
fn synthetic_provider(host: &Host, case: &str) -> Result<(), String> {
    use locallore::{contracts::Error, inference::*, play::PlayProfile};
    use std::task::Poll;
    if !["give", "repair", "agency", "fallback", "wait", "pending"].contains(&case) {
        return Err("InvalidInput".into());
    }
    if case == "pending" {
        SYNTHETIC_PENDING_OBSERVED.store(false, std::sync::atomic::Ordering::SeqCst);
    }
    struct Script {
        case: String,
        directors: u8,
    }
    impl InferenceProvider for Script {
        fn poll(
            &mut self,
            r: &GenerationRequest,
            cancel: &Cancellation,
        ) -> Poll<Result<Vec<u8>, Error>> {
            if cancel.is_cancelled() {
                return Poll::Ready(Err(Error::Cancelled));
            }
            let Input::Structured { role, .. } = &r.input else {
                return Poll::Ready(Err(Error::Malformed));
            };
            if self.case == "pending" {
                SYNTHETIC_PENDING_OBSERVED.store(true, std::sync::atomic::Ordering::SeqCst);
                std::thread::sleep(std::time::Duration::from_millis(2));
                return Poll::Pending;
            }
            if role == "director" {
                self.directors += 1;
                if self.case == "repair" && self.directors == 1 {
                    return Poll::Ready(Ok(b"MALFORMED_SYNTHETIC_DIRECTOR".to_vec()));
                }
                let command = match self.case.as_str() {
                    "agency" => json!({"op":"use_ability","ability":"teleport"}),
                    "wait" => json!({"op":"wait","ticks":1}),
                    _ => json!({"op":"give","item":"potion","to":"mira","quantity":1}),
                };
                return Poll::Ready(Ok(
                    serde_json::to_vec(&json!({"commands":[command]})).unwrap()
                ));
            }
            let text = if self.case == "fallback" {
                "Mira is healed and gains a sword."
            } else if self.case == "wait" {
                "You wait as the tide turns."
            } else {
                "You hand the potion to Mira."
            };
            Poll::Ready(Ok(serde_json::to_vec(
                &json!({"text":text,"event_ids":[r.revision+1],"speaker":"narrator"}),
            )
            .unwrap()))
        }
    }
    let profile = PlayProfile {
        id: "synthetic-private-capture".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 5000,
        repair_limit: 1,
    };
    let case = case.to_owned();
    host.configure_local_provider(
        profile,
        Arc::new(move || {
            Box::new(Script {
                case: case.clone(),
                directors: 0,
            })
        }),
    )
}
#[cfg(feature = "dev-harness")]
#[derive(Default)]
pub struct TestCaptureState(std::sync::Mutex<String>);
#[cfg(feature = "dev-harness")]
#[tauri::command]
pub async fn harness_capture_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    state: tauri::State<'_, TestCaptureState>,
    case: String,
) -> Result<Value, String> {
    if !crate::harness::active()
        || std::env::var("LOCALLORE_D06_CAPTURE_HARNESS").as_deref() != Ok("1")
    {
        return Err("Forbidden".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    if case == "pending-status" {
        return Ok(
            json!({"synthetic":true,"provider_polled":SYNTHETIC_PENDING_OBSERVED.load(std::sync::atomic::Ordering::SeqCst)}),
        );
    }
    if ["export-save", "export-cancel"].contains(&case.as_str()) {
        *state.0.lock().map_err(|_| "Internal")? = case;
        return Ok(json!({"synthetic":true,"picker_double":true}));
    }
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch, || {
            synthetic_provider(&host, &case)?;
            Ok(json!({"synthetic":true,"fake_inference":true,"same_production_play":true}))
        })
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}

#[cfg(test)]
mod tests {
    use super::*;
    fn call(h: &Host, c: Value) -> Value {
        h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap())
    }
    fn staged(case: &str, enabled: bool) -> (Host, Value, Value) {
        let host = Host::new(true);
        synthetic_provider(&host, case).unwrap();
        let created = call(&host, json!({"op":"create","seed":"lantern-quay-v1"}))["data"].clone();
        let s = &created["session"];
        let scope = &created["scope"];
        if enabled {
            assert_eq!(
                call(
                    &host,
                    json!({"op":"trace_capture_configure","session":s,"scope":scope,"expected_head":0,"enabled":true,"consent":true})
                )["status"],
                "ok"
            );
        }
        let request = json!({"version":1,"scope":scope,"turn":"private-turn","expected_revision":0,"intent":{"kind":"free_text","value":{"kind":"action","text":"I give my last potion to Mira."}}});
        assert_eq!(
            call(
                &host,
                json!({"op":"free_text","session":s,"request":request})
            )["data"]["phase"],
            "queued"
        );
        let result = call(
            &host,
            json!({"op":"prepare","session":s,"scope":scope,"turn":"private-turn"}),
        );
        let metadata = call(
            &host,
            json!({"op":"trace_read","session":s,"scope":scope,"expected_head":0,"base_revision":0,"observer":{"kind":"omniscient"},"turn":"private-turn","attempt":null}),
        );
        let attempt = metadata["data"]["snapshot"]["attempts"]
            .as_array()
            .and_then(|a| a.last())
            .map(|a| a["identity"]["attempt"].clone())
            .unwrap_or(json!(1));
        let query = json!({"op":"trace_capture_read","session":s,"scope":scope,"expected_head":0,"base_revision":0,"turn":"private-turn","attempt":attempt});
        (host, query, result)
    }
    #[test]
    fn actual_play_private_preview_is_exact_and_rejects_disabled_stale_foreign_and_unretained() {
        let (host, query, result) = staged("repair", true);
        assert_eq!(result["data"]["phase"], "ready", "{result}");
        let broker = CaptureBroker::default();
        let preview = broker.preview(&host, 1, query.clone(), || true).unwrap();
        let captured: Value = serde_json::from_str(preview["text"].as_str().unwrap()).unwrap();
        assert_eq!(captured, call(&host, query.clone())["data"]);
        assert!(preview["text"]
            .as_str()
            .unwrap()
            .contains("MALFORMED_SYNTHETIC_DIRECTOR"));
        assert!(preview["text"]
            .as_str()
            .unwrap()
            .contains("validated_plan_not_durable_commit"));
        assert!(preview["text"]
            .as_str()
            .unwrap()
            .contains("accepted_candidate_not_durable_commit"));
        let mut wrong = query.clone();
        wrong["expected_head"] = json!(1);
        assert_eq!(
            broker.preview(&host, 1, wrong, || true).unwrap_err(),
            "Stale"
        );
        let mut wrong = query.clone();
        wrong["scope"]["story"] = json!("foreign");
        assert!(broker.preview(&host, 1, wrong, || true).is_err());
        let mut wrong = query.clone();
        wrong["turn"] = json!("unretained");
        assert_eq!(
            broker.preview(&host, 1, wrong, || true).unwrap_err(),
            "CaptureNotRetained"
        );
        call(
            &host,
            json!({"op":"trace_capture_revoke","session":query["session"],"scope":query["scope"]}),
        );
        assert_eq!(
            broker.preview(&host, 1, query, || true).unwrap_err(),
            "CaptureNotRetained"
        );
    }
    #[test]
    fn actual_play_capture_on_off_preserves_effects_and_proposal_and_labels_agency_fallback() {
        let (off, qoff, roff) = staged("give", false);
        let (on, qon, ron) = staged("give", true);
        assert_eq!(roff["data"]["phase"], "ready");
        assert_eq!(ron["data"]["phase"], "ready");
        let commit = |h: &Host, q: &Value| {
            call(
                h,
                json!({"op":"commit","session":q["session"],"scope":q["scope"],"turn":q["turn"]}),
            )
        };
        let a = commit(&off, &qoff);
        let b = commit(&on, &qon);
        assert_eq!(
            a["data"]["receipt"]["events"],
            b["data"]["receipt"]["events"]
        );
        assert_eq!(
            a["data"]["receipt"]["proposal"],
            b["data"]["receipt"]["proposal"]
        );
        assert_eq!(
            a["data"]["receipt"]["narration"],
            b["data"]["receipt"]["narration"]
        );
        let (agency, qa, ra) = staged("agency", true);
        assert_eq!(ra["data"]["error"], "Agency");
        let view = call(&agency, qa);
        assert!(view["data"]["details"]["artifacts"]
            .as_array()
            .unwrap()
            .iter()
            .all(|a| a["kind"] != "accepted_candidate_not_durable_commit"));
        let (fallback, qf, rf) = staged("fallback", true);
        assert_eq!(rf["data"]["phase"], "ready");
        let details = call(&fallback, qf);
        assert!(details["data"]["details"]["artifacts"]
            .as_array()
            .unwrap()
            .iter()
            .any(|a| a["kind"] == "accepted_candidate_not_durable_commit"
                && a["value"]["play"]["fallback"] == true));
    }
}
