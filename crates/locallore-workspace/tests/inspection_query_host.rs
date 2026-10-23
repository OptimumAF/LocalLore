//! Real Host wire and SQLite integration; no UI rendering or model execution.
use locallore::host::Host;
use serde_json::{json, Value};
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
static TEMP_SEQUENCE: AtomicUsize = AtomicUsize::new(0);

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-query-host-{}-{}-{}",
            std::process::id(),
            TEMP_SEQUENCE.fetch_add(1, Ordering::Relaxed),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn host(&self, lab: bool) -> Host {
        locallore_workspace::open(&self.0.join("synthetic.sqlite"), lab).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn create(host: &Host) -> (String, Value) {
    let result = call(host, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(result["status"], "ok", "{result}");
    (
        result["data"]["session"].as_str().unwrap().into(),
        result["data"]["scope"].clone(),
    )
}
fn query(
    host: &Host,
    session: &str,
    scope: &Value,
    head: u64,
    at: Option<u64>,
    observer: Value,
    view: &str,
) -> Value {
    call(
        host,
        json!({"op":"inspection_query","session":session,"query":{"version":1,"scope":scope,"expected_head":head,"at_revision":at,"observer":observer,"view":view,"cursor":null,"limit":4,"search":""}}),
    )
}
fn commit_gift(host: &Host, session: &str, scope: &Value) {
    let request = json!({"version":1,"scope":scope,"turn":"gift","expected_revision":0,"intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}});
    assert_eq!(
        call(
            host,
            json!({"op":"submit","session":session,"request":request,"mode":"accepted"})
        )["data"]["phase"],
        "queued"
    );
    for op in ["prepare", "commit"] {
        assert_eq!(
            call(
                host,
                json!({"op":op,"session":session,"scope":scope,"turn":"gift"})
            )["status"],
            "ok"
        );
    }
}

#[test]
fn private_query_grants_cannot_arrive_from_renderer_json_and_browsing_is_read_only() {
    let temp = Temp::new();
    let host = temp.host(false);
    let (session, scope) = create(&host);
    let snapshot = || {
        call(
            &host,
            json!({"op":"play_snapshot","session":session,"scope":scope,"expected_revision":0}),
        )
    };
    let before = snapshot();
    for observer in [
        json!({"kind":"omniscient"}),
        json!({"kind":"character","id":"mira"}),
    ] {
        assert_eq!(
            query(&host, &session, &scope, 0, None, observer, "knowledge")["error"],
            "Forbidden"
        );
    }
    let page = query(
        &host,
        &session,
        &scope,
        0,
        None,
        json!({"kind":"player"}),
        "knowledge",
    );
    assert_eq!(page["status"], "ok", "{page}");
    assert_eq!(page["data"]["privacy"], "player_visible");
    assert!(
        !page.to_string().contains("old-ruins"),
        "Mira's private mistaken belief must not reach Play"
    );
    let unsupported = query(
        &host,
        &session,
        &scope,
        0,
        None,
        json!({"kind":"player"}),
        "summaries",
    );
    assert_eq!(unsupported["data"]["status"], "unsupported");
    let mut command = json!({"op":"inspection_query","session":session,"query":{"version":1,"scope":scope,"expected_head":0,"at_revision":null,"observer":{"kind":"omniscient"},"view":"knowledge","cursor":null,"limit":4,"search":""}});
    command["query"]["story_lab_granted"] = json!(true);
    assert_eq!(call(&host, command)["error"], "Malformed");
    assert_eq!(snapshot(), before);
    assert_eq!(host.live_counts(), (1, 0));
    assert_eq!(
        call(&host, json!({"op":"close","session":session,"scope":scope}))["status"],
        "ok"
    );
    assert_eq!(
        query(
            &host,
            &session,
            &scope,
            0,
            None,
            json!({"kind":"player"}),
            "history"
        )["error"],
        "Closed"
    );
}

#[test]
fn durable_query_reloads_actual_head_and_rebuilds_historical_completed_boundary() {
    let temp = Temp::new();
    let host = temp.host(true);
    let (session, scope) = create(&host);
    let writer = temp.host(false);
    let resumed = call(&writer, json!({"op":"resume","scope":scope}));
    let writer_session = resumed["data"]["session"].as_str().unwrap();
    commit_gift(&writer, writer_session, &scope);
    assert_eq!(
        query(
            &host,
            &session,
            &scope,
            0,
            None,
            json!({"kind":"player"}),
            "profiles"
        )["error"],
        "Stale"
    );
    let historical = query(
        &host,
        &session,
        &scope,
        1,
        Some(0),
        json!({"kind":"omniscient"}),
        "history",
    );
    assert_eq!(historical["status"], "ok", "{historical}");
    assert_eq!(historical["data"]["head"], 1);
    assert_eq!(historical["data"]["revision"], 0);
    assert_eq!(historical["data"]["rows"], json!([]));
    let current = query(
        &host,
        &session,
        &scope,
        1,
        None,
        json!({"kind":"omniscient"}),
        "history",
    );
    assert_eq!(current["status"], "ok", "{current}");
    assert!(current["data"]["total"].as_u64().unwrap() > 0);
    let npc = query(
        &host,
        &session,
        &scope,
        1,
        None,
        json!({"kind":"character","id":"mira"}),
        "knowledge",
    );
    assert!(npc.to_string().contains("old-ruins"));
    assert!(!npc.to_string().contains("SECRET-TIDE-731"));
    let mut foreign = scope.clone();
    foreign["story"] = json!("another-story");
    assert_eq!(
        query(
            &host,
            &session,
            &foreign,
            1,
            None,
            json!({"kind":"player"}),
            "history"
        )["error"],
        "Scope"
    );
    assert_eq!(host.live_counts(), (1, 0));
    assert_eq!(writer.live_counts(), (1, 0));
}
