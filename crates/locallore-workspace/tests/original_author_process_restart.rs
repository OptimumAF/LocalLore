// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Real self-spawned process deaths, SQLite recovery and scripted PLAYER plumbing.
//! All synthetic databases, unacknowledged replies and captures are retained.
use locallore::{
    contracts::*,
    host::{Host, WorkspaceForkRequest},
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    inspection_query::{Observer, Query, View},
    play::PlayProfile,
    story_authoring::{InitialStoryInputV1, InitialWorldProposalV1},
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
    process::{Child, Command as ProcessCommand, Stdio},
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Mutex,
    },
    task::Poll,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

const CASE: &str = "LOCALLORE_ORIGINAL_RESTART_CASE_V1";
const ROOT: &str = "LOCALLORE_ORIGINAL_RESTART_ROOT_V1";
const ARTIFACT_BASE: &str = "LOCALLORE_ORIGINAL_RESTART_ARTIFACT_BASE_V1";
const GO: &[u8] = b"LL_ORIGINAL_AUTHOR_RESTART_V1\n";
const ASH: &str = "93739dd7d3e24ea890bd6472ab34f901";
const COPPER: &str = "094f727ef5494e7a8b7dfaf82220e2d3";
const BRANCH: &str = "sealed-alternate";
const BRANCH_CANARY: &str = "SYNTHETIC-ALTERNATE-ONLY-529";
const LIMIT: u64 = 65_536;
const SECRETS: &[&str] = &[
    "ASHGLASS-NPC-319",
    "ASHGLASS-VALVE-701",
    "ASHGLASS-RUMOR-622",
    "COPPER-NPC-263",
    "COPPER-SLUICE-468",
    "COPPER-RUMOR-853",
    BRANCH_CANARY,
];

fn plain(path: &Path) {
    for part in path.ancestors() {
        let metadata = fs::symlink_metadata(part).unwrap();
        assert!(
            !metadata.file_type().is_symlink(),
            "reparse/symlink: {part:?}"
        );
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0, "reparse: {part:?}");
        }
    }
}
fn temp_base() -> PathBuf {
    // The local runner selects physical D explicitly. Other platforms/CI may
    // use their normal supported TEMP without imposing a product drive policy.
    let base = std::env::var_os(ARTIFACT_BASE)
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    assert!(base.is_absolute());
    plain(&base);
    base.canonicalize().unwrap()
}
fn saved(root: &Path, name: &str, value: &Value) {
    assert!(name.ends_with(".json") && !name.contains(['/', '\\']));
    let bytes = serde_json::to_vec(value).unwrap();
    assert!(bytes.len() <= 2 * 1024 * 1024);
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(root.join(name))
        .unwrap();
    file.write_all(&bytes).unwrap();
    file.sync_all().unwrap();
}
fn read(root: &Path, name: &str) -> Value {
    let path = root.join(name);
    plain(&path);
    let file = File::open(&path).unwrap();
    assert!(file.metadata().unwrap().len() <= 2 * 1024 * 1024);
    serde_json::from_reader(file).unwrap()
}
fn scope(id: &str, branch: &str) -> Scope {
    Scope {
        story: format!("original-{id}"),
        branch: branch.into(),
    }
}
fn database(root: &Path) -> PathBuf {
    root.join("stories.sqlite")
}
fn host(root: &Path) -> Host {
    locallore_workspace::open(&database(root), true).unwrap()
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "scripted-process-restart-v1".into(),
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
    let (input, proposal) = if copper {
        (
            include_str!("../../../fixtures/initial_world/copper-input.json"),
            include_str!("../../../fixtures/initial_world/copper-proposal.json"),
        )
    } else {
        (
            include_str!("../../../fixtures/initial_world/ashglass-input.json"),
            include_str!("../../../fixtures/initial_world/ashglass-proposal.json"),
        )
    };
    (
        serde_json::from_str(input).unwrap(),
        serde_json::from_str(proposal).unwrap(),
    )
}
#[derive(Default)]
struct Counts {
    factories: AtomicUsize,
    requests: Mutex<Vec<Value>>,
}
impl Counts {
    fn value(&self) -> Value {
        let requests = self.requests.lock().unwrap();
        json!({"factories":self.factories.load(Ordering::SeqCst),
            "author":requests.iter().filter(|r|r["role"]=="author").count(),
            "director":requests.iter().filter(|r|r["role"]=="director").count(),
            "narrator":requests.iter().filter(|r|r["role"]=="narrator").count(),"requests":*requests})
    }
}
struct Script {
    counts: Arc<Counts>,
    author: Option<InitialWorldProposalV1>,
    forbid: bool,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        assert!(
            !self.forbid,
            "recovery/retry must not poll an inference provider"
        );
        let Input::Structured { role, prompt, .. } = &request.input else {
            panic!("structured role required")
        };
        self.counts
            .requests
            .lock()
            .unwrap()
            .push(json!({"role":role,"prompt":prompt,
            "scope":request.scope,"turn":request.turn,"revision":request.revision}));
        let output = match role.as_str() {
            "author" => {
                serde_json::to_value(self.author.as_ref().expect("explicit author fixture"))
                    .unwrap()
            }
            "director" => {
                for secret in SECRETS {
                    assert!(!prompt.contains(secret), "director leaked {secret}");
                }
                assert_eq!(request.scope, scope(ASH, "main"));
                json!({"commands":[{"op":"wait","ticks":1}]})
            }
            "narrator" => {
                for secret in SECRETS {
                    assert!(!prompt.contains(secret), "narrator leaked {secret}");
                }
                assert_eq!(request.scope, scope(ASH, "main"));
                json!({"text":"Time passes.","event_ids":[request.revision+1],"speaker":"narrator"})
            }
            other => panic!("unexpected scripted role {other}"),
        };
        Poll::Ready(Ok(serde_json::to_vec(&output).unwrap()))
    }
}
fn configure(
    host: &Host,
    counts: &Arc<Counts>,
    author: Option<InitialWorldProposalV1>,
    forbid: bool,
) {
    let counts = counts.clone();
    host.configure_fixture_provider(
        profile(),
        Arc::new(move || {
            counts.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Script {
                counts: counts.clone(),
                author: author.clone(),
                forbid,
            })
        }),
    )
    .unwrap();
}
fn creation(host: &Host, id: &str, job: &str, hash: &str) -> Value {
    call(
        host,
        json!({"op":"authoring_create","job":job,"review_sha256":hash,"creation_id":id}),
    )
}
fn authored(host: &Host, root: &Path, copper: bool, counts: &Arc<Counts>) -> Value {
    let (input, proposal) = fixture(copper);
    configure(host, counts, Some(proposal.clone()), false);
    let job = data(call(host, json!({"op":"authoring_begin","input":input})))["job"]
        .as_str()
        .unwrap()
        .to_owned();
    let generated = data(call(host, json!({"op":"authoring_generate","job":job})));
    assert_eq!(generated["proposal"], json!(proposal));
    assert_eq!(generated["provider"], "scripted");
    let review = data(call(
        host,
        json!({"op":"authoring_review","job":job,"input":input,
        "proposal":proposal,"title":if copper {"Copper restart control"} else {"Ashglass restart target"}}),
    ));
    let consent = json!({"job":job,"review_sha256":review["review_sha256"]});
    saved(
        root,
        if copper {
            "copper-consent.json"
        } else {
            "ash-consent.json"
        },
        &consent,
    );
    let created = data(creation(
        host,
        if copper { COPPER } else { ASH },
        &job,
        review["review_sha256"].as_str().unwrap(),
    ));
    assert_eq!(created["created"], true);
    created
}
fn engine(root: &Path, scope: &Scope) -> locallore::engine::Engine {
    Store::open_read_only(&database(root))
        .unwrap()
        .resume(scope)
        .unwrap()
        .engine
}
fn snapshot(root: &Path) -> Value {
    let rows = [
        scope(ASH, "main"),
        scope(ASH, BRANCH),
        scope(COPPER, "main"),
    ]
    .map(|scope| {
        let engine = engine(root, &scope);
        json!({"scope":scope,"seed":engine.seed(),"revision":engine.revision(),
            "canonical":engine.canonical_bytes(),"receipts":engine.receipts()})
    });
    let stories = Store::open_read_only(&database(root))
        .unwrap()
        .stories()
        .unwrap();
    json!({"stories":stories.iter().map(|s|json!({"scope":s.scope,"title":s.title,"revision":s.revision,"drafts":s.drafts})).collect::<Vec<_>>(),"scopes":rows})
}
fn turn(host: &Host, session: &str, request: &Request, op: &str) -> Value {
    call(
        host,
        json!({"op":op,"session":session,"scope":request.scope,"turn":request.turn}),
    )
}
fn player_request() -> Request {
    Request {
        version: 1,
        scope: scope(ASH, "main"),
        turn: "first-original-player-message".into(),
        expected_revision: 0,
        intent: Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tick.".into(),
        },
    }
}
fn free_text(host: &Host, session: &str, request: &Request) -> Value {
    call(
        host,
        json!({"op":"free_text","session":session,"request":request}),
    )
}
fn query(scope: Scope, observer: Observer, search: &str, head: u64) -> Query {
    Query {
        version: 1,
        scope,
        expected_head: head,
        at_revision: None,
        observer,
        view: View::Knowledge,
        cursor: None,
        limit: 64,
        search: search.into(),
    }
}
fn recover(host: &Host, root: &Path, revision: u64) -> String {
    let consent = read(root, "ash-consent.json");
    let before = snapshot(root);
    let reply = data(creation(
        host,
        ASH,
        "lost-process-job",
        consent["review_sha256"].as_str().unwrap(),
    ));
    assert_eq!(reply["created"], false);
    assert_eq!(reply["scope"], json!(scope(ASH, "main")));
    assert_eq!(reply["revision"], revision);
    assert_eq!(
        snapshot(root),
        before,
        "exact-key lookup may not insert or change canonical state"
    );
    for (id, hash, expected) in [
        (ASH, "0".repeat(64), "Conflict"),
        (
            "cccccccccccccccccccccccccccccccc",
            consent["review_sha256"].as_str().unwrap().into(),
            "NotFound",
        ),
        (
            ASH,
            read(root, "copper-consent.json")["review_sha256"]
                .as_str()
                .unwrap()
                .into(),
            "Conflict",
        ),
    ] {
        assert_eq!(
            creation(host, id, "dead-or-stale-job", &hash)["error"],
            expected
        );
        assert_eq!(
            snapshot(root),
            before,
            "wrong/stale consent cannot insert or overwrite"
        );
    }
    reply["session"].as_str().unwrap().into()
}
fn barrier(root: &Path, phase: &str, host: &Host, counts: &Counts) -> ! {
    saved(root, &format!("{phase}-generation.json"), &counts.value());
    let pending = format!("{phase}-ready.pending.json");
    saved(
        root,
        &pending,
        &json!({"version":1,"stage":phase,"committed_before_ack":true}),
    );
    fs::rename(root.join(pending), root.join(format!("{phase}-ready.json"))).unwrap();
    loop {
        std::hint::black_box(host.live_counts());
        std::thread::sleep(Duration::from_millis(20));
    }
}

fn author_process(root: &Path) {
    let host = host(root);
    let counts = Arc::new(Counts::default());
    let ash = authored(&host, root, false, &counts);
    authored(&host, root, true, &counts);
    let session = ash["session"].as_str().unwrap();
    let fork = host
        .fork_branch(
            session,
            &WorkspaceForkRequest {
                parent: scope(ASH, "main"),
                child_branch: BRANCH.into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap();
    let sibling = data(call(&host, json!({"op":"resume","scope":fork.scope})))["session"]
        .as_str()
        .unwrap()
        .to_owned();
    let player = engine(root, &fork.scope).seed().player.clone();
    let request = Request {
        version: 1,
        scope: fork.scope,
        turn: "sealed-sibling-statement".into(),
        expected_revision: 0,
        intent: Intent::Actions(vec![Command::Say {
            text: BRANCH_CANARY.into(),
            audience: [player].into(),
        }]),
    };
    assert_eq!(
        data(call(
            &host,
            json!({"op":"submit","session":sibling,"request":request,"mode":"accepted"})
        ))["phase"],
        "queued"
    );
    assert_eq!(
        data(turn(&host, &sibling, &request, "prepare"))["phase"],
        "ready"
    );
    assert_eq!(
        data(turn(&host, &sibling, &request, "commit"))["phase"],
        "committed"
    );
    assert_eq!(counts.value()["author"], 2);
    assert_eq!(counts.value()["director"], 0);
    saved(root, "author-canonical.json", &snapshot(root));
    // The reply exists only in the doomed child's private file. The parent
    // reads only the ready signal, kills/waits, then starts a new process.
    saved(root, "unacknowledged-create.json", &ash);
    barrier(root, "author", &host, &counts);
}
fn player_process(root: &Path) {
    let host = host(root);
    assert_eq!(
        data(call(&host, json!({"op":"authoring_capabilities"})))["available"],
        false
    );
    let session = recover(&host, root, 0);
    assert_eq!(snapshot(root), read(root, "author-canonical.json"));
    let initial = engine(root, &scope(ASH, "main"));
    let sel = initial
        .seed()
        .actors
        .iter()
        .find(|(_, actor)| actor.name == "Sel")
        .unwrap()
        .0;
    let npc = host
        .inspection_query(
            &session,
            &query(
                scope(ASH, "main"),
                Observer::Character { id: sel.clone() },
                "ASHGLASS-VALVE-701",
                0,
            ),
        )
        .unwrap();
    assert_eq!(npc.total, 1);
    let player = serde_json::to_string(
        &initial
            .character_context(&initial.seed().player, &scope(ASH, "main"), 0)
            .unwrap(),
    )
    .unwrap();
    for secret in SECRETS {
        assert!(!player.contains(secret), "player context leaked {secret}");
    }
    assert_eq!(
        host.inspection_query(
            &session,
            &query(scope(COPPER, "main"), Observer::Player, "", 0)
        )
        .unwrap_err(),
        "Scope"
    );
    assert_eq!(
        host.generation_snapshot(&session, &scope(ASH, BRANCH), 1, &|| false)
            .err()
            .unwrap(),
        "Scope"
    );
    let counts = Arc::new(Counts::default());
    configure(&host, &counts, None, false);
    // Preserve the original actual failure as a negative Host case. The finite
    // supported-English grammar deliberately clarifies this unsupported phrase;
    // the process-death positive case uses its documented one-tick form.
    let before_negative = snapshot(root);
    let mut unsupported = player_request();
    unsupported.turn = "unsupported-original-player-phrase".into();
    unsupported.intent = Intent::FreeText {
        kind: PlayInputKind::Action,
        text: "I wait for the next station clock tick.".into(),
    };
    assert_eq!(
        data(free_text(&host, &session, &unsupported))["phase"],
        "queued"
    );
    let refused = data(turn(&host, &session, &unsupported, "prepare"));
    assert_eq!(refused["phase"], "failed");
    assert_eq!(refused["error"], "ClarificationRequired");
    assert_eq!(snapshot(root), before_negative);
    assert!(counts.requests.lock().unwrap().is_empty());
    saved(root, "unsupported-player-input.json", &json!(unsupported));
    saved(root, "unsupported-player-result.json", &refused);
    saved(root, "unsupported-player-generation.json", &counts.value());
    let request = player_request();
    saved(root, "supported-player-input.json", &json!(request));
    assert_eq!(
        data(free_text(&host, &session, &request))["phase"],
        "queued"
    );
    let prepared = turn(&host, &session, &request, "prepare");
    saved(root, "player-prepare.json", &prepared);
    saved(root, "player-prepare-generation.json", &counts.value());
    assert_eq!(data(prepared)["phase"], "ready");
    let committed = turn(&host, &session, &request, "commit");
    assert_eq!(data(committed.clone())["phase"], "committed");
    let after = snapshot(root);
    assert_eq!(engine(root, &request.scope).revision(), 1);
    assert_eq!(engine(root, &request.scope).receipts().len(), 1);
    let initial_snapshot = read(root, "author-canonical.json");
    assert_eq!(after["scopes"][1], initial_snapshot["scopes"][1]);
    assert_eq!(after["scopes"][2], initial_snapshot["scopes"][2]);
    for op in ["prepare", "commit", "turn_status"] {
        assert_eq!(turn(&host, &session, &request, op), committed);
    }
    assert_eq!(free_text(&host, &session, &request), committed);
    let mut changed = request.clone();
    changed.intent = Intent::FreeText {
        kind: PlayInputKind::Action,
        text: "A different request under the same turn key.".into(),
    };
    assert_eq!(
        free_text(&host, &session, &changed)["error"],
        "RetryMismatch"
    );
    assert_eq!(counts.value()["author"], 0);
    assert_eq!(counts.value()["director"], 1);
    assert_eq!(counts.value()["narrator"], 1);
    assert_eq!(snapshot(root), after);
    saved(root, "player-canonical.json", &after);
    saved(root, "unacknowledged-player-commit.json", &committed);
    barrier(root, "player", &host, &counts);
}
fn reopened_process(root: &Path) {
    let host = host(root);
    assert_eq!(
        data(call(&host, json!({"op":"authoring_capabilities"})))["available"],
        false
    );
    let session = recover(&host, root, 1);
    let before = read(root, "player-canonical.json");
    assert_eq!(snapshot(root), before);
    let request = player_request();
    let expected = read(root, "unacknowledged-player-commit.json");
    assert_eq!(free_text(&host, &session, &request), expected);
    let counts = Arc::new(Counts::default());
    configure(&host, &counts, None, true);
    for op in ["prepare", "commit", "turn_status"] {
        assert_eq!(turn(&host, &session, &request, op), expected);
    }
    assert_eq!(free_text(&host, &session, &request), expected);
    assert_eq!(
        counts.value()["factories"],
        0,
        "retry must not even construct a provider"
    );
    assert_eq!(snapshot(root), before);
    saved(root, "reopened-generation.json", &counts.value());
    saved(
        root,
        "reopened-result.json",
        &json!({"version":1,"recovered":true,"revision":1,
        "receipts":1,"duplicate_conserved":true,"inference":"scripted only; recovery invoked none"}),
    );
}

#[test]
fn original_author_process_child_entry() {
    let Ok(case) = std::env::var(CASE) else {
        return;
    };
    assert!(matches!(case.as_str(), "author" | "player" | "reopen"));
    let root = PathBuf::from(std::env::var(ROOT).unwrap());
    plain(&root);
    assert_eq!(root.parent(), Some(temp_base().as_path()));
    assert!(root
        .file_name()
        .unwrap()
        .to_str()
        .unwrap()
        .starts_with("locallore-original-author-process-restart-"));
    let mut go = Vec::new();
    std::io::stdin()
        .take(GO.len() as u64 + 1)
        .read_to_end(&mut go)
        .unwrap();
    assert_eq!(go, GO);
    match case.as_str() {
        "author" => author_process(&root),
        "player" => player_process(&root),
        _ => reopened_process(&root),
    }
}

struct OwnedChild {
    child: Child,
    root: PathBuf,
    phase: &'static str,
}
impl OwnedChild {
    fn start(root: &Path, phase: &'static str) -> Self {
        let capture = |suffix| {
            OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(root.join(format!("{phase}-{suffix}.bin")))
                .unwrap()
        };
        let mut child = ProcessCommand::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "original_author_process_child_entry",
                "--nocapture",
                "--test-threads=1",
            ])
            .current_dir(root)
            .env(CASE, phase)
            .env(ROOT, root)
            .env(ARTIFACT_BASE, temp_base())
            .env("TEMP", temp_base())
            .env("TMP", temp_base())
            .stdin(Stdio::piped())
            .stdout(Stdio::from(capture("stdout")))
            .stderr(Stdio::from(capture("stderr")))
            .spawn()
            .unwrap();
        let mut input = child.stdin.take().unwrap();
        input.write_all(GO).unwrap();
        drop(input);
        Self {
            child,
            root: root.into(),
            phase,
        }
    }
    fn bounded(&self, start: Instant) {
        assert!(
            start.elapsed() < Duration::from_secs(15),
            "child deadline; retained {:?}",
            self.root
        );
        for suffix in ["stdout", "stderr"] {
            assert!(
                fs::metadata(self.root.join(format!("{}-{suffix}.bin", self.phase)))
                    .unwrap()
                    .len()
                    <= LIMIT,
                "child capture cap; retained {:?}",
                self.root
            );
        }
    }
    fn kill_after_ready(&mut self) {
        let start = Instant::now();
        let path = self.root.join(format!("{}-ready.json", self.phase));
        while !path.exists() {
            self.bounded(start);
            assert!(
                self.child.try_wait().unwrap().is_none(),
                "child exited before barrier; retained {:?}",
                self.root
            );
            std::thread::sleep(Duration::from_millis(10));
        }
        let ready = read(&self.root, &format!("{}-ready.json", self.phase));
        assert_eq!(
            ready,
            json!({"version":1,"stage":self.phase,"committed_before_ack":true})
        );
        assert!(self.child.try_wait().unwrap().is_none());
        let pid = self.child.id();
        self.child.kill().unwrap();
        let status = self.child.wait().unwrap();
        assert!(
            !status.success(),
            "must measure actual killed process, not Host.close"
        );
        self.bounded(start);
        saved(
            &self.root,
            &format!("{}-death.json", self.phase),
            &json!({"pid":pid,"kill_called":true,
            "wait_completed":true,"success":status.success(),"code":status.code(),"status":status.to_string()}),
        );
    }
    fn finish(&mut self) {
        let start = Instant::now();
        loop {
            self.bounded(start);
            if let Some(status) = self.child.try_wait().unwrap() {
                assert!(status.success(), "reopen failed; retained {:?}", self.root);
                return;
            }
            std::thread::sleep(Duration::from_millis(10));
        }
    }
}
impl Drop for OwnedChild {
    fn drop(&mut self) {
        if matches!(self.child.try_wait(), Ok(None)) {
            let _ = self.child.kill();
        }
        let _ = self.child.wait();
    }
}
#[test]
fn original_author_lost_ack_then_player_commit_survive_two_actual_process_deaths() {
    assert!(
        std::env::var_os(CASE).is_none(),
        "parent cannot be recursively selected"
    );
    let root = temp_base().join(format!(
        "locallore-original-author-process-restart-{}-{}",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&root).unwrap();
    println!(
        "retained synthetic process-death evidence: {}",
        root.display()
    );
    OwnedChild::start(&root, "author").kill_after_ready();
    OwnedChild::start(&root, "player").kill_after_ready();
    OwnedChild::start(&root, "reopen").finish();
    assert_eq!(read(&root, "author-generation.json")["author"], 2);
    assert_eq!(read(&root, "player-generation.json")["director"], 1);
    assert_eq!(read(&root, "player-generation.json")["narrator"], 1);
    assert_eq!(read(&root, "reopened-generation.json")["factories"], 0);
    assert_eq!(
        read(&root, "reopened-result.json")["duplicate_conserved"],
        true
    );
    // No Drop removes these captures, SQLite/WAL state, consent or failed runs.
}
