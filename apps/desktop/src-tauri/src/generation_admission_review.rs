//! Independent D04.02 FIRST at af55d531. SOURCE AUTHOR UNCOMPILED / UNRUN.
//! Root registers this cfg(test) child in Main after the private helper exists.
//! Missing registration/helper or compilation is SETUP, not a behavioral RED.
//! Actual Host envelope types and WindowLease; fixed closures only, no inference,
//! persistence, app/window, provider, runtime adapter or native IPC qualification.
use crate::generation_admission::{dispatch, requires_generation_permit};
use crate::lease::WindowLease;
use locallore::host::Envelope;
use serde_json::{json, Value};
use std::sync::{atomic::{AtomicBool, AtomicUsize, Ordering}, mpsc, Arc};
use std::thread::{self, JoinHandle};
use std::time::Duration;

const PROBE: Duration = Duration::from_secs(2);

fn wire(command: Value) -> String {
    let envelope = json!({"version":1,"command":command});
    let typed: Envelope = serde_json::from_value(envelope).expect("typed Host fixture");
    serde_json::to_string(&typed).expect("serialize actual Host envelope")
}
fn prepare() -> String {
    wire(json!({"op":"prepare","session":"native-session-73","scope":{"story":"synthetic-admission","branch":"main"},"turn":"synthetic-turn"}))
}
fn author_generate() -> String {
    wire(json!({"op":"authoring_generate","job":"synthetic-author-job"}))
}

// Every held action has a release sender and an always-joined RAII owner.
// Work waits at most three bounded two-second channel intervals. Probes are
// individually <=2s; no sleeps or elapsed-time/performance assertions are used.
// Cleanup releases before joining, including unwinding from an unexpected panic.
struct HeldAction {
    entered: mpsc::Receiver<()>,
    release: Option<mpsc::Sender<()>>,
    worker: Option<JoinHandle<Result<&'static str, String>>>,
}
impl HeldAction {
    fn start(lease: Arc<WindowLease>, epoch: u64, generation: bool) -> Self {
        let (entered_tx, entered) = mpsc::channel();
        let (release, release_rx) = mpsc::channel();
        let worker = thread::spawn(move || dispatch(&lease, epoch, generation, || {
            entered_tx.send(()).map_err(|_| "TestObserverClosed".to_owned())?;
            for _ in 0..3 {
                match release_rx.recv_timeout(PROBE) {
                    Ok(()) => return Ok("released"),
                    Err(mpsc::RecvTimeoutError::Timeout) => {},
                    Err(mpsc::RecvTimeoutError::Disconnected) => return Err("TestReleaseClosed".to_owned()),
                }
            }
            Err("TestReleaseTimeout".to_owned())
        }));
        Self { entered, release: Some(release), worker: Some(worker) }
    }
    fn finish(mut self) -> thread::Result<Result<&'static str, String>> {
        if let Some(sender) = self.release.take() { let _ = sender.send(()); }
        self.worker.take().expect("held worker retained").join()
    }
}
impl Drop for HeldAction {
    fn drop(&mut self) {
        if let Some(sender) = self.release.take() { let _ = sender.send(()); }
        if let Some(worker) = self.worker.take() { let _ = worker.join(); }
    }
}

#[test]
fn typed_prepare_and_authoring_generate_are_long_without_native_version_policy() {
    assert!(requires_generation_permit(&prepare()));
    assert!(requires_generation_permit(&author_generate()));
    // Host, not this native classifier, rejects unsupported envelope versions.
    for version in [0, 2, u16::MAX] {
        let mut value: Value = serde_json::from_str(&prepare()).unwrap();
        value["version"] = json!(version);
        let text = serde_json::to_string(&value).unwrap();
        assert!(serde_json::from_str::<Envelope>(&text).is_ok());
        assert!(requires_generation_permit(&text), "typed Prepare version {version}");
    }
}

#[test]
fn typed_authoring_controls_and_canonical_operations_do_not_take_generation_permit() {
    let input = json!({"version":1,"premise":"Synthetic operation-looking authoring_generate and prepare text","player_name":"Rowan","player_description":"Synthetic player","cast":[],"profile":"fantasy_v1","presentation":{"version":1,"tone":"plain","excluded_phrases":[]}});
    let proposal = json!({"version":1,"locations":[],"player_location":0,"characters":[],"routes":[],"facts":[],"beliefs":[],"possessions":[]});
    let scope = json!({"story":"synthetic-admission","branch":"main"});
    for command in [
        json!({"op":"authoring_capabilities"}),
        json!({"op":"authoring_begin","input":input}),
        json!({"op":"authoring_review","job":"job","input":input,"proposal":proposal,"title":"prepare"}),
        json!({"op":"authoring_create","job":"job","review_sha256":"a".repeat(64),"creation_id":"creation"}),
        json!({"op":"authoring_cancel","job":"prepare"}),
        json!({"op":"authoring_status","job":"authoring_generate"}),
        json!({"op":"capabilities"}), json!({"op":"workspace"}),
        json!({"op":"create","seed":"authoring_generate"}),
        json!({"op":"resume","scope":scope}),
        json!({"op":"open","session":"session","scope":scope}),
        json!({"op":"close","session":"session","scope":scope}),
        json!({"op":"commit","session":"session","scope":scope,"turn":"turn"}),
        json!({"op":"cancel","session":"session","scope":scope,"turn":"turn"}),
        json!({"op":"turn_status","session":"session","scope":scope,"turn":"turn"}),
        json!({"op":"inspect","session":"session","scope":scope,"observer":"player","expected_revision":3}),
    ] {
        let text = wire(command); // Real typed decoding prerequisite, not business acceptance.
        assert!(!requires_generation_permit(&text), "{text}");
    }
}

#[test]
fn malformed_unknown_duplicate_extra_fields_and_op_looking_text_are_not_substring_authority() {
    for text in [
        "", "not-json", "[]", "null",
        r#"{"version":1,"command":{"op":"unknown","job":"authoring_generate"}}"#,
        r#"{"version":1,"command":{"op":"authoring_generate","job":7}}"#,
        r#"{"version":1,"command":{"op":"authoring_generate","job":"job","extra":true}}"#,
        r#"{"version":1,"version":1,"command":{"op":"authoring_generate","job":"job"}}"#,
        r#"{"version":1,"command":{"op":"authoring_generate","op":"prepare","job":"job"}}"#,
        r#"{"version":1,"command":{"op":"authoring_generate","job":"job"},"extra":0}"#,
        r#"{"command":{"op":"prepare","session":"s","scope":{"story":"s","branch":"b"},"turn":"t"}}"#,
        r#"{"version":1,"command":{"op":"prepare","session":"s","scope":{"story":"s","branch":"b"},"turn":"t","extra":0}}"#,
    ] {
        assert!(serde_json::from_str::<Envelope>(text).is_err(), "invalid fixture must really be untyped: {text}");
        assert!(!requires_generation_permit(text));
    }
    let status = wire(json!({"op":"authoring_status","job":"{\"op\":\"authoring_generate\"}"}));
    assert!(!requires_generation_permit(&status));
    assert!(requires_generation_permit(&format!(" \n{}\t", author_generate())));
}

#[test]
fn waiting_authoring_and_prepare_leave_cancel_and_status_control_dispatch_available() {
    for input in [prepare(), author_generate()] {
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let held = HeldAction::start(lease.clone(), epoch, requires_generation_permit(&input));
        let entered = held.entered.recv_timeout(PROBE);
        let controls = [wire(json!({"op":"authoring_cancel","job":"job"})), wire(json!({"op":"authoring_status","job":"job"}))];
        let (done_tx, done_rx) = mpsc::channel();
        let control = {
            let lease = lease.clone();
            thread::spawn(move || {
                let result = controls.into_iter().map(|text| dispatch(&lease, epoch, requires_generation_permit(&text), || Ok("control"))).collect::<Vec<_>>();
                let _ = done_tx.send(result.clone()); result
            })
        };
        let before_release = done_rx.recv_timeout(PROBE);
        let generation_result = held.finish();
        let control_result = control.join();
        // Every worker is joined BEFORE any observation can assert/panic.
        assert!(entered.is_ok());
        assert_eq!(generation_result.unwrap(), Ok("released"));
        assert_eq!(control_result.unwrap(), vec![Ok("control"), Ok("control")]);
        assert_eq!(before_release.unwrap(), vec![Ok("control"), Ok("control")], "controls must complete before explicit generation release");
    }
}

#[test]
fn finish_close_can_complete_while_each_generation_action_is_still_waiting() {
    for input in [prepare(), author_generate()] {
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let held = HeldAction::start(lease.clone(), epoch, requires_generation_permit(&input));
        let entered = held.entered.recv_timeout(PROBE);
        let closed = lease.invalidate(&format!("main-{epoch}"));
        let (done_tx, done_rx) = mpsc::channel();
        let cleanup = {
            let lease = lease.clone(); let closed_epoch = closed.unwrap_or(0);
            thread::spawn(move || { lease.finish_close(closed_epoch, || {}); let _ = done_tx.send(()); })
        };
        let before_release = done_rx.recv_timeout(PROBE);
        let generation_result = held.finish(); let cleanup_result = cleanup.join();
        assert!(entered.is_ok()); assert!(closed.is_some());
        assert_eq!(generation_result.unwrap(), Ok("released")); assert!(cleanup_result.is_ok());
        assert!(before_release.is_ok(), "finish_close must not await generation release");
        assert!(lease.can_open()); assert!(!lease.valid(epoch));
        assert_ne!(lease.begin().unwrap(), epoch);
    }
}

#[test]
fn invalid_and_stale_epochs_never_execute_generation_or_control_actions() {
    let lease = WindowLease::default(); let writes = AtomicUsize::new(0);
    for generation in [false, true] {
        assert_eq!(dispatch(&lease, 0, generation, || { writes.fetch_add(1, Ordering::SeqCst); Ok(()) }), Err("Closed".to_owned()));
    }
    let first = lease.begin().unwrap();
    let closed = lease.invalidate(&format!("main-{first}")).unwrap(); lease.finish_close(closed, || {});
    let current = lease.begin().unwrap();
    for generation in [false, true] {
        assert_eq!(dispatch(&lease, first, generation, || { writes.fetch_add(1, Ordering::SeqCst); Ok(()) }), Err("Closed".to_owned()));
        assert_eq!(dispatch(&lease, current + 1, generation, || { writes.fetch_add(1, Ordering::SeqCst); Ok(()) }), Err("Closed".to_owned()));
    }
    assert_eq!(writes.load(Ordering::SeqCst), 0);
    assert_eq!(dispatch(&lease, current, true, || Ok(73)), Ok(73));
    assert_eq!(dispatch(&lease, current, false, || Ok(91)), Ok(91));
}

#[test]
fn a_queued_control_is_refused_after_invalidation_without_executing_its_action() {
    let lease = Arc::new(WindowLease::default()); let epoch = lease.begin().unwrap();
    let held = HeldAction::start(lease.clone(), epoch, false);
    let entered = held.entered.recv_timeout(PROBE);
    let wrote = Arc::new(AtomicBool::new(false)); let (queued_tx, queued_rx) = mpsc::channel();
    let queued = {
        let lease = lease.clone(); let wrote = wrote.clone();
        thread::spawn(move || { let _ = queued_tx.send(()); dispatch(&lease, epoch, false, || { wrote.store(true, Ordering::SeqCst); Ok("queued") }) })
    };
    let attempted = queued_rx.recv_timeout(PROBE);
    let closed = lease.invalidate(&format!("main-{epoch}"));
    let holder_result = held.finish(); let queued_result = queued.join();
    if let Some(value) = closed { lease.finish_close(value, || {}); }
    assert!(entered.is_ok()); assert!(attempted.is_ok()); assert!(closed.is_some());
    assert_eq!(holder_result.unwrap(), Ok("released")); assert_eq!(queued_result.unwrap(), Err("Closed".to_owned()));
    assert!(!wrote.load(Ordering::SeqCst)); assert!(lease.can_open());
}

#[test]
fn control_actions_stay_serialized_and_preserve_the_original_action_result() {
    let lease = Arc::new(WindowLease::default()); let epoch = lease.begin().unwrap();
    assert_eq!(dispatch::<()>(&lease, epoch, false, || Err("SyntheticControlRefusal".to_owned())), Err("SyntheticControlRefusal".to_owned()));
    assert_eq!(dispatch(&lease, epoch, true, || Err::<(), _>("SyntheticGenerationRefusal".to_owned())), Err("SyntheticGenerationRefusal".to_owned()));
    let held = HeldAction::start(lease.clone(), epoch, false);
    let entered = held.entered.recv_timeout(PROBE);
    let (queued_tx, queued_rx) = mpsc::channel(); let (action_tx, action_rx) = mpsc::channel();
    let queued = {
        let lease = lease.clone();
        thread::spawn(move || { let _ = queued_tx.send(()); dispatch(&lease, epoch, false, || { let _ = action_tx.send(()); Ok("second") }) })
    };
    let attempted = queued_rx.recv_timeout(PROBE); let before_release = action_rx.recv_timeout(PROBE);
    let holder_result = held.finish(); let queued_result = queued.join();
    assert!(entered.is_ok()); assert!(attempted.is_ok());
    assert_eq!(holder_result.unwrap(), Ok("released")); assert_eq!(queued_result.unwrap(), Ok("second"));
    assert!(matches!(before_release, Err(mpsc::RecvTimeoutError::Timeout)), "control action must wait for the existing control gate");
    assert_eq!(dispatch(&lease, epoch, false, || Ok("still usable")), Ok("still usable"));
}

#[test]
fn main_wiring_source_control_uses_one_classifier_for_permit_and_dispatch() {
    // SOURCE CONTROL ONLY: this does not execute Tauri IPC/semaphore behavior.
    let source = include_str!("main.rs");
    let start = source.find("async fn host_call(").expect("actual native caller");
    let end = source[start..].find("fn build_window(").map(|n| start + n).expect("actual caller end");
    let body = source[start..end].split_whitespace().collect::<String>();
    let call = "generation_admission::requires_generation_permit(&input)";
    assert_eq!(body.matches(call).count(), 1, "one actual classifier call");
    let position = body.find(call).unwrap();
    assert!(body.find("input.len()>locallore::host::MAX_INPUT").is_some_and(|p| p < position));
    let prefix = &body[..position]; let binding = prefix.rsplit_once("let").unwrap().1.strip_suffix('=').unwrap();
    assert!(!binding.is_empty() && binding.chars().all(|c| c.is_ascii_alphanumeric() || c == '_'));
    assert!(body.contains(&format!("letpermit=if{binding}{{")), "same value controls existing permit");
    let dispatch_call = format!("generation_admission::dispatch(&lease,epoch,{binding},");
    assert!(body.contains(&dispatch_call), "same value controls actual dispatch");
    assert!(body.find("spawn_blocking(move||").is_some_and(|p| p < body.find(&dispatch_call).unwrap()));
}
