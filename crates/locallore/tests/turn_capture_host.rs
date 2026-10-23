#![cfg(feature = "host")]
use locallore::{contracts::*, host::Host, inference::*, play::PlayProfile};
use serde_json::{json, Value};
use std::{sync::Arc, task::Poll};
fn call(h: &Host, c: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap())
}
fn create(h: &Host) -> (String, Value) {
    let v = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
    (
        v["data"]["session"].as_str().unwrap().into(),
        v["data"]["scope"].clone(),
    )
}
fn config(h: &Host, s: &str, scope: &Value, head: u64, on: bool, consent: bool) -> Value {
    call(
        h,
        json!({"op":"trace_capture_configure","session":s,"scope":scope,"expected_head":head,"enabled":on,"consent":consent}),
    )
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-capture".into(),
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
    }
}
struct Script;
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        let Input::Structured { role, .. } = &r.input else {
            panic!("structured")
        };
        Poll::Ready(Ok(serde_json::to_vec(&if role == "director" {
            json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
        } else {
            json!({"text":"Mira is healed.","event_ids":[1],"speaker":"narrator"})
        })
        .unwrap()))
    }
}
#[test]
fn wire_requires_native_lab_consent_scope_fresh_head_and_exact_private_attempt() {
    let h = Host::new(false);
    let (s, scope) = create(&h);
    assert_eq!(config(&h, &s, &scope, 0, true, true)["error"], "Forbidden");
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_capture_revoke","session":s,"scope":scope})
        )["error"],
        "Forbidden"
    );
    let h = Host::new(true);
    let (s, scope) = create(&h);
    h.configure_local_provider(profile(), Arc::new(|| Box::new(Script)))
        .unwrap();
    assert_eq!(
        config(&h, &s, &scope, 0, true, false)["error"],
        "CaptureConsentRequired"
    );
    assert_eq!(config(&h, &s, &scope, 1, true, true)["error"], "Stale");
    assert_eq!(config(&h, &s, &scope, 0, true, true)["status"], "ok");
    let r = json!({"version":1,"scope":scope,"turn":"captured","expected_revision":0,"intent":{"kind":"free_text","value":{"kind":"action","text":"I give my last potion to Mira."}}});
    let submit = call(
        &h,
        json!({"op":"submit","session":s,"request":r,"mode":"accepted"}),
    );
    assert_eq!(submit["status"], "ok", "{submit}");
    assert_eq!(
        call(
            &h,
            json!({"op":"prepare","session":s,"scope":scope,"turn":"captured"})
        )["data"]["phase"],
        "ready"
    );
    let meta = call(
        &h,
        json!({"op":"trace_read","session":s,"scope":scope,"expected_head":0,"base_revision":0,"observer":{"kind":"player"},"turn":"captured","attempt":null}),
    );
    let attempt = meta["data"]["snapshot"]["attempts"][0]["identity"]["attempt"]
        .as_u64()
        .unwrap();
    let read = |head: u64, turn: &str| {
        call(
            &h,
            json!({"op":"trace_capture_read","session":s,"scope":scope,"expected_head":head,"base_revision":0,"turn":turn,"attempt":attempt}),
        )
    };
    let captured = read(0, "captured");
    assert_eq!(
        captured["data"]["details"]["status"], "recorded",
        "{captured}"
    );
    assert!(
        captured["data"]["details"]["artifacts"]
            .as_array()
            .unwrap()
            .len()
            >= 8
    );
    assert!(!serde_json::to_string(&meta)
        .unwrap()
        .contains("Mira is healed"));
    assert_eq!(
        read(0, "other")["data"]["details"]["status"],
        "not_retained"
    );
    assert_eq!(
        call(
            &h,
            json!({"op":"commit","session":s,"scope":scope,"turn":"captured"})
        )["data"]["phase"],
        "committed"
    );
    assert_eq!(read(0, "captured")["error"], "Stale");
    assert_eq!(
        read(1, "captured")["data"]["details"]["identity"]["base_revision"],
        0
    );
    let state_before = call(
        &h,
        json!({"op":"play_snapshot","session":s,"scope":scope,"expected_revision":1}),
    );
    assert_eq!(config(&h, &s, &scope, 0, false, false)["error"], "Stale");
    let revoked = call(
        &h,
        json!({"op":"trace_capture_revoke","session":s,"scope":scope}),
    );
    assert_eq!(revoked["data"]["revoked"], true, "{revoked}");
    assert_eq!(
        call(
            &h,
            json!({"op":"play_snapshot","session":s,"scope":scope,"expected_revision":1})
        ),
        state_before
    );
    assert!(read(1, "captured")["data"]["details"]["artifacts"]
        .as_array()
        .unwrap()
        .is_empty());
    let metadata = call(
        &h,
        json!({"op":"trace_read","session":s,"scope":scope,"expected_head":1,"base_revision":0,"observer":{"kind":"player"},"turn":"captured","attempt":attempt}),
    );
    assert_eq!(
        metadata["data"]["snapshot"]["attempts"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    assert_eq!(config(&h, &s, &scope, 1, false, false)["status"], "ok");
    assert_eq!(
        call(&h, json!({"op":"close","session":s,"scope":scope}))["status"],
        "ok"
    );
    assert_eq!(read(1, "captured")["error"], "Closed");
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_capture_revoke","session":s,"scope":scope})
        )["error"],
        "Closed"
    );
}
