//! Actual Host/SQLite authoring ownership, explicit consent, recovery and isolation.
use locallore::{
    contracts::*,
    engine::Engine,
    host::{Host, Persistence, SavedTurn, WorkspaceSummary},
    inference::{Cancellation, GenerationRequest, InferenceProvider},
    play::PlayProfile,
    story_authoring::{self as core, InitialStoryInputV1, InitialWorldProposalV1},
};
use locallore_storage::{validate_archive, Store};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
        Arc,
    },
    task::Poll,
    time::{Duration, Instant},
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let base = std::env::temp_dir().canonicalize().unwrap();
        let p = base.join(format!(
            "locallore-initial-world-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&p).unwrap();
        Self(p)
    }
    fn path(&self) -> PathBuf {
        self.0.join("stories.sqlite")
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.path(), false).unwrap()
    }
    fn snapshot(&self) -> Value {
        let mut store = Store::open_application(&self.path()).unwrap();
        let rows = store.stories().unwrap();
        let archives: Vec<Value> = rows
            .iter()
            .map(|row| {
                serde_json::from_slice(
                    store
                        .export_archive(&row.scope.story, &|| false)
                        .unwrap()
                        .bytes(),
                )
                .unwrap()
            })
            .collect();
        json!({"stories":rows.iter().map(|row| json!({"scope":row.scope,"title":row.title,"revision":row.revision,"drafts":row.drafts})).collect::<Vec<_>>(),"archives":archives})
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        assert_eq!(
            self.0.parent(),
            Some(std::env::temp_dir().canonicalize().unwrap().as_path())
        );
        assert!(self
            .0
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-initial-world-"));
        for name in ["stories.sqlite", "stories.sqlite-wal", "stories.sqlite-shm"] {
            if let Err(e) = std::fs::remove_file(self.0.join(name)) {
                if e.kind() != std::io::ErrorKind::NotFound && !std::thread::panicking() {
                    panic!("owned test cleanup: {e}");
                }
            }
        }
        if let Err(e) = std::fs::remove_dir(&self.0) {
            if !std::thread::panicking() {
                panic!("owned test directory cleanup: {e}");
            }
        }
    }
}
fn call(h: &Host, c: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap())
}
fn data(v: Value) -> Value {
    assert_eq!(v["status"], "ok", "{v}");
    v["data"].clone()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "initial-world-test-v1".into(),
        model_sha256: "0".repeat(64),
        runtime_revision: "0".repeat(40),
        template_sha256: "0".repeat(64),
        worker_sha256: "0".repeat(64),
        profile_manifest_sha256: "0".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}
fn fixture(copper: bool) -> (InitialStoryInputV1, InitialWorldProposalV1) {
    if copper {
        (
            serde_json::from_str(include_str!(
                "../../../fixtures/initial_world/copper-input.json"
            ))
            .unwrap(),
            serde_json::from_str(include_str!(
                "../../../fixtures/initial_world/copper-proposal.json"
            ))
            .unwrap(),
        )
    } else {
        (
            serde_json::from_str(include_str!(
                "../../../fixtures/initial_world/ashglass-input.json"
            ))
            .unwrap(),
            serde_json::from_str(include_str!(
                "../../../fixtures/initial_world/ashglass-proposal.json"
            ))
            .unwrap(),
        )
    }
}
struct Output {
    bytes: Vec<u8>,
    calls: Arc<AtomicUsize>,
}
impl InferenceProvider for Output {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        assert!(
            matches!(&r.input,locallore::inference::Input::Structured{role,..} if role=="author")
        );
        self.calls.fetch_add(1, Ordering::SeqCst);
        Poll::Ready(Ok(self.bytes.clone()))
    }
}
fn configure(h: &Host, p: &InitialWorldProposalV1) -> Arc<AtomicUsize> {
    configure_bytes(h, serde_json::to_vec(p).unwrap())
}
fn configure_bytes(h: &Host, bytes: Vec<u8>) -> Arc<AtomicUsize> {
    let calls = Arc::new(AtomicUsize::new(0));
    let counter = calls.clone();
    h.configure_fixture_provider(
        profile(),
        Arc::new(move || {
            Box::new(Output {
                bytes: bytes.clone(),
                calls: counter.clone(),
            })
        }),
    )
    .unwrap();
    calls
}
fn begin(h: &Host, input: &InitialStoryInputV1) -> String {
    data(call(h, json!({"op":"authoring_begin","input":input})))["job"]
        .as_str()
        .unwrap()
        .into()
}
fn ready(
    h: &Host,
    input: &InitialStoryInputV1,
    proposal: &InitialWorldProposalV1,
    title: &str,
) -> (String, String) {
    let job = begin(h, input);
    let generated = data(call(h, json!({"op":"authoring_generate","job":job})));
    assert_eq!(generated["proposal"], json!(proposal));
    assert_eq!(generated["provider"], "scripted");
    let review = data(call(
        h,
        json!({"op":"authoring_review","job":job,"input":input,"proposal":proposal,"title":title}),
    ));
    (job, review["review_sha256"].as_str().unwrap().into())
}
fn create(h: &Host, job: &str, hash: &str, id: &str) -> Value {
    call(
        h,
        json!({"op":"authoring_create","job":job,"review_sha256":hash,"creation_id":id}),
    )
}
fn scope(created: &Value) -> Scope {
    serde_json::from_value(created["scope"].clone()).unwrap()
}
fn wait_turn(h: &Host, created: &Value) {
    let request = Request {
        version: 1,
        scope: scope(created),
        turn: "original-wait".into(),
        expected_revision: 0,
        intent: Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    };
    assert_eq!(
        data(call(
            h,
            json!({"op":"submit","session":created["session"],"request":request,"mode":"accepted"})
        ))["phase"],
        "queued"
    );
    for (op, phase) in [("prepare", "ready"), ("commit", "committed")] {
        assert_eq!(
            data(call(
                h,
                json!({"op":op,"session":created["session"],"scope":created["scope"],"turn":"original-wait"})
            ))["phase"],
            phase
        );
    }
}

#[test]
fn original_generation_is_noncanonical_until_reviewed_create_and_two_worlds_stay_distinct() {
    let temp = Temp::new();
    let h = temp.host();
    let before = temp.snapshot();
    let (a, pa) = fixture(false);
    let calls = configure(&h, &pa);
    let (job, hash) = ready(&h, &a, &pa, "Ashglass");
    assert_eq!(temp.snapshot(), before);
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    let first = data(create(&h, &job, &hash, &"1".repeat(32)));
    assert_eq!(first["created"], true);
    let old = Store::open_read_only(&temp.path())
        .unwrap()
        .load_seed(&scope(&first))
        .unwrap();
    assert_eq!(old.initial_world.as_ref().unwrap().reviewed, a);
    let generation = &old.initial_world.as_ref().unwrap().generation;
    assert_eq!(generation.prompt_version, core::PROMPT_VERSION);
    assert_eq!(generation.prompt_version, "initial-world-v1.1");
    assert_eq!(generation.schema_version, core::SCHEMA_VERSION);
    assert_eq!(
        old.initial_world
            .as_ref()
            .unwrap()
            .generation
            .model_configuration,
        (&profile()).into()
    );
    let (b, pb) = fixture(true);
    configure(&h, &pb);
    let (job, hash) = ready(&h, &b, &pb, "Copper");
    let second = data(create(&h, &job, &hash, &"2".repeat(32)));
    assert_ne!(first["scope"], second["scope"]);
    let store = Store::open_read_only(&temp.path()).unwrap();
    let new = store.load_seed(&scope(&second)).unwrap();
    assert_ne!(old.actors, new.actors);
    assert_ne!(old.routes, new.routes);
    assert_ne!(old.facts, new.facts);
    assert_eq!(store.load_seed(&scope(&first)).unwrap(), old);
}

#[test]
fn lost_ack_reopen_and_archive_retry_preserve_accepted_history_without_provider() {
    let temp = Temp::new();
    let h = temp.host();
    let (input, proposal) = fixture(false);
    let calls = configure(&h, &proposal);
    let (job, hash) = ready(&h, &input, &proposal, "Ashglass");
    let id = "3".repeat(32);
    let created = data(create(&h, &job, &hash, &id));
    wait_turn(&h, &created);
    let before = temp.snapshot();
    h.close_all();
    drop(h);
    let reopened = temp.host();
    assert_eq!(
        data(call(&reopened, json!({"op":"authoring_capabilities"})))["available"],
        false
    );
    let retry = data(create(&reopened, "lost-process-job", &hash, &id));
    assert_eq!(retry["created"], false);
    assert_eq!(retry["revision"], 1);
    assert_eq!(temp.snapshot(), before);
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    let mut store = Store::open_application(&temp.path()).unwrap();
    let archive = store
        .export_archive(&scope(&created).story, &|| false)
        .unwrap();
    let target = Temp::new();
    Store::open_application(&target.path())
        .unwrap()
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let imported = target.host();
    let imported_before = target.snapshot();
    let recovered = data(create(&imported, "no-generation-job", &hash, &id));
    assert_eq!(recovered["created"], false);
    assert_eq!(recovered["revision"], 1);
    assert_eq!(target.snapshot(), imported_before);
}

#[test]
fn recovered_creation_consumes_matching_live_review_but_preserves_unrelated_draft() {
    let temp = Temp::new();
    let live = temp.host();
    let other = temp.host();
    let (input, proposal) = fixture(false);
    let calls = configure(&live, &proposal);
    configure(&other, &proposal);
    let (job, hash) = ready(&live, &input, &proposal, "Ashglass");
    let (other_job, other_hash) = ready(&other, &input, &proposal, "Ashglass");
    assert_eq!(hash, other_hash);
    let id = "a".repeat(32);
    assert_eq!(
        data(create(&other, &other_job, &hash, &id))["created"],
        true
    );
    let (duplicate_job, duplicate_hash) = ready(&other, &input, &proposal, "Ashglass");
    assert_eq!(duplicate_hash, hash);
    assert_eq!(
        data(create(&other, &duplicate_job, &hash, &"b".repeat(32)))["created"],
        true
    );
    let before = temp.snapshot();

    assert_eq!(data(create(&live, &job, &hash, &id))["created"], false);
    assert_eq!(
        data(call(&live, json!({"op":"authoring_status","job":job})))["phase"],
        "created"
    );
    assert_eq!(
        create(&live, &job, &hash, &"b".repeat(32))["error"],
        "Stale"
    );
    assert_eq!(
        create(&live, &job, &hash, &"d".repeat(32))["error"],
        "Stale"
    );
    assert_eq!(
        call(
            &live,
            json!({"op":"authoring_review","job":job,"input":input,"proposal":proposal,"title":"Changed"})
        )["error"],
        "Stale"
    );
    assert_eq!(
        create(&live, &job, &hash, &"b".repeat(32))["error"],
        "Stale"
    );
    assert_eq!(data(create(&live, &job, &hash, &id))["created"], false);
    assert_eq!(
        data(call(&live, json!({"op":"authoring_cancel","job":job})))["cancelled"],
        false
    );
    assert_eq!(temp.snapshot(), before);
    assert_eq!(calls.load(Ordering::SeqCst), 1);

    let (new_job, new_hash) = ready(&live, &input, &proposal, "Another review");
    assert_ne!(new_hash, hash);
    assert_eq!(
        data(create(&live, "foreign-job", &hash, &id))["created"],
        false
    );
    assert_eq!(
        data(call(&live, json!({"op":"authoring_status","job":new_job})))["phase"],
        "reviewed"
    );
    assert_eq!(
        data(create(&live, &new_job, &new_hash, &"c".repeat(32)))["created"],
        true
    );
    assert_eq!(calls.load(Ordering::SeqCst), 2);
}

#[test]
fn edits_invalid_reviews_cancel_and_configuration_changes_revoke_old_creation_consent() {
    let temp = Temp::new();
    let h = temp.host();
    let (mut input, proposal) = fixture(false);
    configure(&h, &proposal);
    let (job, old) = ready(&h, &input, &proposal, "Ashglass");
    let before = temp.snapshot();
    input.player_name = "Neri".into();
    let review = data(call(
        &h,
        json!({"op":"authoring_review","job":job,"input":input,"proposal":proposal,"title":"Edited"}),
    ));
    let latest = review["review_sha256"].as_str().unwrap();
    assert_ne!(latest, old);
    assert_eq!(create(&h, &job, &old, &"4".repeat(32))["error"], "Stale");
    assert_eq!(
        call(
            &h,
            json!({"op":"authoring_review","job":job,"input":input,"proposal":proposal,"title":" invalid"})
        )["status"],
        "rejected"
    );
    assert_eq!(create(&h, &job, latest, &"4".repeat(32))["error"], "Stale");
    assert_eq!(
        data(call(&h, json!({"op":"authoring_cancel","job":job})))["cancelled"],
        true
    );
    assert_eq!(
        create(&h, &job, latest, &"4".repeat(32))["error"],
        "Cancelled"
    );
    configure(&h, &proposal);
    let (job, hash) = ready(&h, &input, &proposal, "Again");
    let mut changed = profile();
    changed.model_sha256 = "a".repeat(64);
    h.configure_fixture_provider(
        changed,
        Arc::new(|| panic!("changing configuration must not generate")),
    )
    .unwrap();
    assert_eq!(
        create(&h, &job, &hash, &"4".repeat(32))["error"],
        "Cancelled"
    );
    assert_eq!(temp.snapshot(), before);
}

#[test]
fn malformed_and_impossible_generated_worlds_never_reach_create_or_change_prior_canon() {
    for bytes in [
        b"{\"version\":1,\"version\":1}".to_vec(),
        vec![b' '; 8193],
        {
            let (_, p) = fixture(false);
            let mut p = json!(p);
            p["characters"][0]["location"] = json!(999);
            serde_json::to_vec(&p).unwrap()
        },
    ] {
        let temp = Temp::new();
        let h = temp.host();
        data(call(&h, json!({"op":"create","seed":"lantern-quay-v1"})));
        let before = temp.snapshot();
        let (input, proposal) = fixture(false);
        configure_bytes(&h, bytes);
        let job = begin(&h, &input);
        assert_eq!(
            call(&h, json!({"op":"authoring_generate","job":job}))["status"],
            "rejected"
        );
        assert_eq!(
            call(
                &h,
                json!({"op":"authoring_review","job":job,"input":input,"proposal":proposal,"title":"No"})
            )["error"],
            "Stale"
        );
        assert_eq!(temp.snapshot(), before);
        assert_eq!(h.live_counts().1, 0);
    }
}

struct Pending {
    started: Arc<AtomicBool>,
    dropped: Arc<AtomicUsize>,
}
impl InferenceProvider for Pending {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.started.store(true, Ordering::SeqCst);
        Poll::Pending
    }
}
impl Drop for Pending {
    fn drop(&mut self) {
        self.dropped.fetch_add(1, Ordering::SeqCst);
    }
}
#[test]
fn generation_cancel_and_host_close_release_exact_worker_and_leave_no_story() {
    for close in [false, true] {
        let temp = Temp::new();
        let h = Arc::new(temp.host());
        let (input, _) = fixture(false);
        let started = Arc::new(AtomicBool::new(false));
        let dropped = Arc::new(AtomicUsize::new(0));
        let s = started.clone();
        let d = dropped.clone();
        h.configure_fixture_provider(
            profile(),
            Arc::new(move || {
                Box::new(Pending {
                    started: s.clone(),
                    dropped: d.clone(),
                })
            }),
        )
        .unwrap();
        let job = begin(&h, &input);
        let run = h.clone();
        let id = job.clone();
        let thread =
            std::thread::spawn(move || call(&run, json!({"op":"authoring_generate","job":id})));
        let began = Instant::now();
        while !started.load(Ordering::SeqCst) && began.elapsed() < Duration::from_secs(3) {
            std::thread::sleep(Duration::from_millis(1));
        }
        if close || !started.load(Ordering::SeqCst) {
            h.close_all();
        } else {
            assert_eq!(
                data(call(&h, json!({"op":"authoring_cancel","job":job})))["cancelled"],
                true
            );
        }
        assert_eq!(thread.join().unwrap()["error"], "Cancelled");
        assert!(started.load(Ordering::SeqCst));
        assert_eq!(dropped.load(Ordering::SeqCst), 1);
        assert_eq!(h.live_counts().1, 0);
        assert_eq!(
            data(call(&h, json!({"op":"workspace"})))["stories"],
            json!([])
        );
        assert_ne!(begin(&h, &input), job);
    }
}

#[test]
fn deleted_completed_creation_cannot_be_recreated_by_missing_job_retry() {
    let temp = Temp::new();
    let h = temp.host();
    let (input, proposal) = fixture(false);
    configure(&h, &proposal);
    let (job, hash) = ready(&h, &input, &proposal, "Ashglass");
    let id = "5".repeat(32);
    let created = data(create(&h, &job, &hash, &id));
    h.close_all();
    drop(h);
    let mut store = Store::open_application(&temp.path()).unwrap();
    let deletion = store
        .prepare_story_deletion(&scope(&created), 0, &|| false)
        .unwrap();
    store.delete_story(deletion, &|| false).unwrap();
    drop(store);
    let reopened = temp.host();
    assert_eq!(create(&reopened, &job, &hash, &id)["error"], "NotFound");
    assert_eq!(
        data(call(&reopened, json!({"op":"workspace"})))["stories"],
        json!([])
    );
}

/// Fault injection with a real second SQLite owner deleting exactly after recovery lookup.
struct DeleteDuringLookup {
    database: PathBuf,
    writes: Arc<AtomicUsize>,
}
impl Persistence for DeleteDuringLookup {
    fn location(&self) -> &str {
        "synthetic-recovery-race"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Ok(vec![])
    }
    fn create(&mut self) -> Result<Engine, String> {
        Err("Unsupported".into())
    }
    fn create_named(
        &mut self,
        s: &locallore::story_setup::NamedStarter,
    ) -> Result<(Engine, bool), String> {
        self.writes.fetch_add(1, Ordering::SeqCst);
        let mut store = Store::open_application(&self.database).unwrap();
        let (scope, created) = store
            .create_workspace_exact(s.title(), s.seed().clone())
            .unwrap();
        Ok((store.resume(&scope).unwrap().engine, created))
    }
    fn lookup_original(&mut self, id: &str, hash: &str) -> Result<Option<Engine>, String> {
        let scope = Scope {
            story: format!("original-{id}"),
            branch: "main".into(),
        };
        let mut other = Store::open_application(&self.database).unwrap();
        let captured = other.resume(&scope).unwrap().engine;
        assert_eq!(
            core::origin_hash(captured.seed().initial_world.as_ref().unwrap()).unwrap(),
            hash
        );
        let deletion = other
            .prepare_story_deletion(&scope, captured.revision(), &|| false)
            .unwrap();
        other.delete_story(deletion, &|| false).unwrap();
        Ok(Some(captured))
    }
    fn resume(&mut self, s: &Scope) -> Result<Engine, String> {
        Store::open_read_only(&self.database)
            .unwrap()
            .resume(s)
            .map(|r| r.engine)
            .map_err(|_| "NotFound".into())
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        Err("Unsupported".into())
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
}
#[test]
fn deletion_between_lookup_and_attachment_never_reinserts_or_resets_history() {
    let temp = Temp::new();
    let h = temp.host();
    let (input, proposal) = fixture(false);
    configure(&h, &proposal);
    let (job, hash) = ready(&h, &input, &proposal, "Ashglass");
    let id = "6".repeat(32);
    let created = data(create(&h, &job, &hash, &id));
    wait_turn(&h, &created);
    h.close_all();
    drop(h);
    let writes = Arc::new(AtomicUsize::new(0));
    let race = Host::with_persistence(
        false,
        Box::new(DeleteDuringLookup {
            database: temp.path(),
            writes: writes.clone(),
        }),
    );
    assert_eq!(create(&race, &job, &hash, &id)["error"], "NotFound");
    assert_eq!(writes.load(Ordering::SeqCst), 0);
    assert_eq!(
        Store::open_application(&temp.path())
            .unwrap()
            .stories()
            .unwrap()
            .len(),
        0
    );
}
