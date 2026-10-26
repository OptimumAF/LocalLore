// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Core Host with static providers and
//! actual canonical Engine fixture port; no SQLite/durability/model/UI claim.
#![cfg(feature = "host")]
use locallore::{
    context_compiler::{player_literal_transcript_v1_cancelled, ContextPolicy},
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
    host::{
        DraftDisposition, Host, HostGenerationSnapshot, HostPlayConstructionV1, Persistence,
        ProviderFactory, SavedTurn, WorkspaceSummary,
    },
    inference::*,
    memory_coverage::{CoverageRead, FallbackReason},
    play::{self, DirectorPassV25, PlayProfile},
};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    sync::{
        atomic::{AtomicBool, AtomicUsize, Ordering},
        mpsc, Arc, Mutex,
    },
    task::Poll,
    time::Duration,
};

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-literal-host".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}
fn call(h: &Host, c: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap())
}
fn create(h: &Host) -> (String, Scope, u64) {
    let v = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(v["status"], "ok", "{v}");
    (
        v["data"]["session"].as_str().unwrap().into(),
        serde_json::from_value(v["data"]["scope"].clone()).unwrap(),
        v["data"]["revision"].as_u64().unwrap(),
    )
}
fn request(scope: &Scope, head: u64, key: &str, kind: PlayInputKind) -> Request {
    Request {
        version: 1,
        scope: scope.clone(),
        turn: key.into(),
        expected_revision: head,
        intent: Intent::FreeText {
            kind,
            text: if kind == PlayInputKind::Action {
                "I wait for one tide tick."
            } else {
                "CURRENT_LITERAL 雪 \"quoted\" \\"
            }
            .into(),
        },
    }
}
fn submit(h: &Host, s: &str, r: &Request) -> Value {
    call(
        h,
        json!({"op":"submit","session":s,"request":r,"mode":"accepted"}),
    )
}
fn op(h: &Host, s: &str, r: &Request, name: &str) -> Value {
    call(
        h,
        json!({"op":name,"session":s,"scope":r.scope,"turn":r.turn}),
    )
}
fn trace_on(h: &Host, s: &str, r: &Request) {
    assert_eq!(
        call(
            h,
            json!({"op":"trace_configure","session":s,"scope":r.scope,"expected_head":r.expected_revision,"enabled":true})
        )["status"],
        "ok"
    );
}
fn provenance(h: &Host, s: &str, r: &Request, head: u64) -> Value {
    let v = call(
        h,
        json!({"op":"trace_read","session":s,"scope":r.scope,"expected_head":head,"base_revision":r.expected_revision,"observer":{"kind":"player"},"turn":r.turn,"attempt":null}),
    );
    assert_eq!(v["status"], "ok", "{v}");
    v["data"]["snapshot"]["attempts"][0]["provenance"].clone()
}
fn literal_record(v: &Value) {
    assert_eq!(v["status"], "ok", "{v}");
    assert_eq!(v["data"]["phase"], "committed", "{v}");
    let p = &v["data"]["receipt"]["play"];
    assert_eq!(p["prompt_version"], play::LITERAL_PLAY_PROMPT_VERSION_V1);
    assert_eq!(p["policy"], "grounded-prose-v2.2");
    assert!(p["context"].is_null());
    assert!(p["context_policy"].is_null());
}

#[derive(Default)]
struct Seen {
    factories: AtomicUsize,
    requests: Mutex<Vec<GenerationRequest>>,
}
impl Seen {
    fn factory(self: &Arc<Self>) -> ProviderFactory {
        let seen = self.clone();
        Arc::new(move || {
            seen.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Script {
                seen: seen.clone(),
                dialogue: false,
            })
        })
    }
    fn count(&self) -> usize {
        self.factories.load(Ordering::SeqCst)
    }
}
struct Script {
    seen: Arc<Seen>,
    dialogue: bool,
}
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.requests.lock().unwrap().push(r.clone());
        let Input::Structured { role, prompt, .. } = &r.input else {
            panic!("structured actual role")
        };
        let value = if role == "director" {
            let marker = if prompt.contains("Literal conversation data: ") {
                "Literal conversation data: "
            } else {
                "Context data: "
            };
            let rest = prompt.split_once(marker).unwrap().1;
            let frame = serde_json::Deserializer::from_str(rest)
                .into_iter::<Value>()
                .next()
                .unwrap()
                .unwrap();
            self.dialogue = frame["kind"] == "dialogue";
            if self.dialogue {
                json!({"commands":[{"op":"say","text":frame["player_text"],"audience":["mira"]}]})
            } else {
                json!({"commands":[{"op":"wait","ticks":1}]})
            }
        } else {
            assert_eq!(role, "narrator");
            json!({"text":if self.dialogue{"Your words are heard by the chosen listeners."}else{"You pause as a tide tick passes."},"event_ids":[r.revision+1],"speaker":"narrator"})
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}

#[derive(Clone, Copy)]
enum SnapshotFault {
    Good,
    Error,
    Panic,
}
struct Draft {
    request: Request,
    phase: String,
    receipt: Option<Receipt>,
}
struct Data {
    engine: Engine,
    drafts: BTreeMap<String, Draft>,
    resumes: usize,
    snapshots: usize,
    snapshot_fault: SnapshotFault,
    panic_resume: bool,
}
type Shared = Arc<Mutex<Data>>;
struct Spy(Shared);
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn wait(e: &mut Engine, id: &str) {
    let r = e.request(id, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let p = Engine::proposal(&r).unwrap();
    let v = e.preview(&r, &p).unwrap();
    e.commit_prepared(&v).unwrap();
}
fn selected() -> Engine {
    let mut e = Engine::new(seed()).unwrap().fork("selected", 0).unwrap();
    wait(&mut e, "prefix-original");
    e
}
fn port(e: Engine, fault: SnapshotFault) -> (Host, Shared) {
    let data = Arc::new(Mutex::new(Data {
        engine: e,
        drafts: BTreeMap::new(),
        resumes: 0,
        snapshots: 0,
        snapshot_fault: fault,
        panic_resume: false,
    }));
    (
        Host::with_persistence(false, Box::new(Spy(data.clone()))),
        data,
    )
}
fn verify(d: &Data, b: &AcceptedHistoryBasis) -> Result<(), String> {
    if d.engine
        .matches_accepted_history(b)
        .map_err(|e| e.to_string())?
    {
        Ok(())
    } else {
        Err("Stale".into())
    }
}
fn saved(d: &Data, scope: &Scope, turn: &str) -> Result<SavedTurn, String> {
    if d.engine.scope() != scope {
        return Err("Scope".into());
    }
    let t = d.drafts.get(turn).ok_or("UnknownTurn")?;
    Ok(SavedTurn {
        request: t.request.clone(),
        phase: t.phase.clone(),
        receipt: t.receipt.clone(),
    })
}
impl Persistence for Spy {
    fn location(&self) -> &str {
        "synthetic-canonical-port"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Ok(vec![])
    }
    fn create(&mut self) -> Result<Engine, String> {
        Ok(self.0.lock().unwrap().engine.clone())
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        let (e, panic) = {
            let mut d = self.0.lock().unwrap();
            d.resumes += 1;
            let panic = std::mem::take(&mut d.panic_resume);
            (d.engine.clone(), panic)
        };
        // Deliberate native-port fault occurs AFTER releasing the fixture lock;
        // only the Host's panic containment/owner lock is under test.
        if panic {
            panic!("fixed canonical resume fault");
        }
        if e.scope() != scope {
            return Err("Scope".into());
        }
        Ok(e)
    }
    fn generation_snapshot(
        &mut self,
        scope: &Scope,
        head: u64,
        observer: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        let fault = {
            let mut d = self.0.lock().unwrap();
            d.snapshots += 1;
            d.snapshot_fault
        };
        match fault {
            SnapshotFault::Error => return Err("Integrity".into()),
            SnapshotFault::Panic => panic!("fixed memory snapshot fault"),
            SnapshotFault::Good => {}
        }
        if cancel() {
            return Err("Cancelled".into());
        }
        let e = self.resume(scope)?;
        if e.revision() != head || e.seed().player != observer {
            return Err("Stale".into());
        }
        if cancel() {
            return Err("Cancelled".into());
        }
        Ok(HostGenerationSnapshot {
            engine: e,
            coverage: CoverageRead::RawFallback(FallbackReason::Missing),
        })
    }
    fn begin_bound(&mut self, r: &Request, b: &AcceptedHistoryBasis) -> Result<SavedTurn, String> {
        let mut d = self.0.lock().unwrap();
        verify(&d, b)?;
        d.engine.preflight(r).map_err(|e| e.to_string())?;
        if let Some(t) = d.drafts.get(&r.turn) {
            if t.request != *r {
                return Err("RetryMismatch".into());
            }
        } else {
            d.drafts.insert(
                r.turn.clone(),
                Draft {
                    request: r.clone(),
                    phase: "draft".into(),
                    receipt: None,
                },
            );
        }
        saved(&d, &r.scope, &r.turn)
    }
    fn status_bound(&mut self, r: &Request, b: &AcceptedHistoryBasis) -> Result<SavedTurn, String> {
        let d = self.0.lock().unwrap();
        verify(&d, b)?;
        let s = saved(&d, &r.scope, &r.turn)?;
        if s.request != *r {
            return Err("RetryMismatch".into());
        }
        Ok(s)
    }
    fn commit_prepared_bound(
        &mut self,
        r: &Receipt,
        b: &AcceptedHistoryBasis,
    ) -> Result<Receipt, String> {
        let mut d = self.0.lock().unwrap();
        verify(&d, b)?;
        if d.drafts.get(&r.request().turn).map(|t| &t.request) != Some(r.request()) {
            return Err("RetryMismatch".into());
        }
        let actual = d.engine.commit_prepared(r).map_err(|e| e.to_string())?;
        let t = d.drafts.get_mut(&r.request().turn).unwrap();
        t.phase = "committed".into();
        t.receipt = Some(actual.clone());
        Ok(actual)
    }
    fn finish_bound(
        &mut self,
        r: &Request,
        b: &AcceptedHistoryBasis,
        p: DraftDisposition,
    ) -> Result<SavedTurn, String> {
        let mut d = self.0.lock().unwrap();
        verify(&d, b)?;
        let t = d.drafts.get_mut(&r.turn).ok_or("UnknownTurn")?;
        if t.request != *r {
            return Err("RetryMismatch".into());
        }
        if t.phase == "draft" {
            t.phase = match p {
                DraftDisposition::Cancelled => "cancelled",
                DraftDisposition::Failed => "failed",
                DraftDisposition::Stale => "stale",
            }
            .into();
        }
        saved(&d, &r.scope, &r.turn)
    }
    fn status(&mut self, s: &Scope, t: &str) -> Result<SavedTurn, String> {
        saved(&self.0.lock().unwrap(), s, t)
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
}

#[test]
fn native_construction_both_modes_preserves_actual_renderer_fixture_labels_and_literal_trace() {
    for real_label in [false, true] {
        for kind in [PlayInputKind::Action, PlayInputKind::Dialogue] {
            let h = Host::new(true);
            let seen = Arc::new(Seen::default());
            if real_label {
                h.configure_local_provider_with_construction(
                    profile(),
                    seen.factory(),
                    HostPlayConstructionV1::PlayerLiteralV1,
                )
                .unwrap();
            } else {
                h.configure_fixture_provider_with_construction(
                    profile(),
                    seen.factory(),
                    HostPlayConstructionV1::PlayerLiteralV1,
                )
                .unwrap();
            }
            let (s, scope, head) = create(&h);
            let r = request(&scope, head, "literal", kind);
            trace_on(&h, &s, &r);
            let before = h
                .generation_snapshot(&s, &scope, head, &|| false)
                .unwrap()
                .engine;
            let source =
                player_literal_transcript_v1_cancelled(&before, &scope, head, "player", &|| false)
                    .unwrap();
            let expected = play::render_player_literal_director_v1_cancelled(
                &before,
                &r,
                &source,
                &profile(),
                DirectorPassV25::Initial,
                &|| false,
            )
            .unwrap();
            assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
            let ready = op(&h, &s, &r, "prepare");
            assert_eq!(ready["data"]["phase"], "ready", "{ready}");
            assert!(ready["data"]["receipt"].is_null());
            let done = op(&h, &s, &r, "commit");
            literal_record(&done);
            let requests = seen.requests.lock().unwrap();
            assert_eq!(requests.len(), 2);
            assert_eq!(requests[0].schema, "locallore-director-literal-v1");
            let Input::Structured { prompt, schema, .. } = &requests[0].input else {
                panic!("structured role")
            };
            assert_eq!(prompt, expected.prompt());
            assert_eq!(schema, expected.schema());
            drop(requests);
            let provenance = provenance(&h, &s, &r, head + 1);
            assert_eq!(
                provenance["prompt_label"],
                play::LITERAL_PLAY_PROMPT_VERSION_V1
            );
            assert_eq!(provenance["schema_label"], "locallore-director-literal-v1");
            assert_eq!(provenance["model_sha256"].is_null(), !real_label);
            let status = call(&h, json!({"op":"model_status"}));
            assert_eq!(status["data"]["real_model"], real_label);
            if !real_label {
                assert_eq!(status["data"]["loaded"], false);
                assert_eq!(status["data"]["status"], "configured_fixture_owner");
            }
        }
    } // real_label=true is still this same static fake provider, not a model.
}

#[test]
fn no_lab_is_needed_for_player_literal_but_json_selector_and_observer_privilege_are_denied() {
    fn native_traits<T: Clone + Copy + std::fmt::Debug + Eq>(_: T) {}
    native_traits(HostPlayConstructionV1::PlayerLiteralV1);
    let h = Host::new(false);
    let seen = Arc::new(Seen::default());
    h.configure_fixture_provider_with_construction(
        profile(),
        seen.factory(),
        HostPlayConstructionV1::PlayerLiteralV1,
    )
    .unwrap();
    let (s, scope, head) = create(&h);
    let r = request(&scope, head, "literal", PlayInputKind::Action);
    for command in [
        json!({"op":"configure_fixture_provider_with_construction","construction":"player_literal_v1"}),
        json!({"op":"submit","session":s,"request":r,"mode":"accepted","construction":"player_literal_v1"}),
        json!({"op":"prepare","session":s,"scope":scope,"turn":r.turn,"observer":"mira"}),
    ] {
        assert_eq!(call(&h, command)["error"], "Malformed");
    }
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_capture_configure","session":s,"scope":scope,"expected_head":head,"enabled":true,"consent":true})
        )["error"],
        "Forbidden"
    );
    assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
    assert_eq!(op(&h, &s, &r, "prepare")["data"]["phase"], "ready");
    literal_record(&op(&h, &s, &r, "commit"));
    assert_eq!(seen.count(), 1);
}

struct Held {
    script: Script,
    release: Arc<AtomicBool>,
    entered: Option<mpsc::Sender<()>>,
}
impl InferenceProvider for Held {
    fn poll(&mut self, r: &GenerationRequest, c: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        if let Some(s) = self.entered.take() {
            let _ = s.send(());
        }
        if !self.release.load(Ordering::SeqCst) {
            Poll::Pending
        } else {
            self.script.poll(r, c)
        }
    }
}
struct Release(Arc<AtomicBool>);
impl Drop for Release {
    fn drop(&mut self) {
        self.0.store(true, Ordering::SeqCst);
    }
}
#[test]
fn held_literal_work_captures_provider_construction_and_trace_before_memory_reconfiguration() {
    let h = Arc::new(Host::new(true));
    let old = Arc::new(Seen::default());
    let release = Arc::new(AtomicBool::new(false));
    let guard = Release(release.clone());
    let (tx, rx) = mpsc::channel();
    let factory: ProviderFactory = {
        let old = old.clone();
        Arc::new(move || {
            old.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Held {
                script: Script {
                    seen: old.clone(),
                    dialogue: false,
                },
                release: release.clone(),
                entered: Some(tx.clone()),
            })
        })
    };
    h.configure_fixture_provider_with_construction(
        profile(),
        factory,
        HostPlayConstructionV1::PlayerLiteralV1,
    )
    .unwrap();
    let (s, scope, head) = create(&h);
    let r = request(&scope, head, "held", PlayInputKind::Action);
    trace_on(&h, &s, &r);
    assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
    let worker = {
        let h = h.clone();
        let s = s.clone();
        let r = r.clone();
        std::thread::spawn(move || op(&h, &s, &r, "prepare"))
    };
    rx.recv_timeout(Duration::from_secs(2))
        .expect("actual provider entered");
    let next = Arc::new(Seen::default());
    h.configure_fixture_provider_with_construction(
        profile(),
        next.factory(),
        HostPlayConstructionV1::Memory(ContextPolicy::StateRelevantMemoryV1),
    )
    .unwrap();
    drop(guard);
    let ready = worker.join().unwrap();
    assert_eq!(ready["data"]["phase"], "ready", "{ready}");
    literal_record(&op(&h, &s, &r, "commit"));
    let captured = provenance(&h, &s, &r, head + 1);
    assert_eq!(
        captured["prompt_label"],
        play::LITERAL_PLAY_PROMPT_VERSION_V1
    );
    assert_eq!(captured["schema_label"], "locallore-director-literal-v1");
    assert_eq!(old.count(), 1);
    assert_eq!(next.count(), 0);
    let future = request(&scope, head + 1, "memory", PlayInputKind::Action);
    assert_eq!(submit(&h, &s, &future)["data"]["phase"], "queued");
    assert_eq!(op(&h, &s, &future, "prepare")["data"]["phase"], "ready");
    let committed = op(&h, &s, &future, "commit");
    assert_eq!(
        committed["data"]["receipt"]["play"]["prompt_version"],
        play::PROMPT_VERSION
    );
    assert!(!committed["data"]["receipt"]["play"]["context"].is_null());
    assert_eq!(next.count(), 1);
    assert_eq!(old.requests.lock().unwrap().len(), 2);
}

#[test]
fn literal_reads_canonical_resume_without_loading_or_dropping_memory_snapshot_even_if_it_would_panic(
) {
    for fault in [SnapshotFault::Error, SnapshotFault::Panic] {
        let before = selected();
        let (h, data) = port(before.clone(), fault);
        let seen = Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(
            profile(),
            seen.factory(),
            HostPlayConstructionV1::PlayerLiteralV1,
        )
        .unwrap();
        let (s, scope, head) = create(&h);
        let r = request(&scope, head, "literal", PlayInputKind::Action);
        assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
        let reads = data.lock().unwrap().resumes;
        let ready = op(&h, &s, &r, "prepare");
        assert_eq!(ready["data"]["phase"], "ready", "{ready}");
        {
            let d = data.lock().unwrap();
            assert_eq!(d.snapshots, 0);
            assert!(d.resumes > reads);
            assert_eq!(d.engine.canonical_records(), before.canonical_records());
        }
        literal_record(&op(&h, &s, &r, "commit"));
        assert_eq!(seen.count(), 1);
        assert_eq!(
            data.lock().unwrap().engine.canonical_record_count(),
            before.canonical_record_count() + 1
        );
    }
    for fault in [SnapshotFault::Good, SnapshotFault::Error] {
        let (h, data) = port(selected(), fault);
        let seen = Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(
            profile(),
            seen.factory(),
            HostPlayConstructionV1::Memory(ContextPolicy::StateRelevantMemoryV1),
        )
        .unwrap();
        let (s, scope, head) = create(&h);
        let r = request(&scope, head, "memory", PlayInputKind::Action);
        assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
        let ready = op(&h, &s, &r, "prepare");
        assert_eq!(data.lock().unwrap().snapshots, 1);
        if matches!(fault, SnapshotFault::Good) {
            assert_eq!(ready["data"]["phase"], "ready", "{ready}");
            assert_eq!(seen.count(), 1);
        } else {
            assert_ne!(ready["data"]["phase"], "ready");
            assert_eq!(seen.count(), 0);
            assert!(seen.requests.lock().unwrap().is_empty());
        }
    }
}

#[test]
fn changed_canonical_append_seed_same_head_history_lineage_player_and_scope_refuse_before_factory()
{
    for mutation in 0..6 {
        let original = selected();
        let (h, data) = port(original.clone(), SnapshotFault::Panic);
        let seen = Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(
            profile(),
            seen.factory(),
            HostPlayConstructionV1::PlayerLiteralV1,
        )
        .unwrap();
        let (s, scope, head) = create(&h);
        let r = request(&scope, head, "pending", PlayInputKind::Action);
        assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
        let changed = match mutation {
            0 => {
                let mut e = original.clone();
                wait(&mut e, "other-append");
                e
            }
            1 => {
                let mut s = seed();
                s.facts.get_mut("beacon-mark").unwrap().proposition = "DIFFERENT_SEED".into();
                let mut e = Engine::new(s).unwrap().fork("selected", 0).unwrap();
                wait(&mut e, "prefix-original");
                e
            }
            2 => {
                let mut e = Engine::new(seed()).unwrap().fork("selected", 0).unwrap();
                wait(&mut e, "different-prefix");
                e
            }
            3 => {
                let mut e = Engine::new(seed())
                    .unwrap()
                    .fork("middle", 0)
                    .unwrap()
                    .fork("selected", 0)
                    .unwrap();
                wait(&mut e, "prefix-original");
                assert_eq!(e.canonical_records(), original.canonical_records());
                e
            }
            4 => {
                let mut s = seed();
                s.player = "mira".into();
                let mut e = Engine::new(s).unwrap().fork("selected", 0).unwrap();
                wait(&mut e, "prefix-original");
                e
            }
            _ => original.fork("foreign-scope", original.revision()).unwrap(),
        };
        let keep = changed.accepted_history_basis().unwrap();
        data.lock().unwrap().engine = changed;
        let response = op(&h, &s, &r, "prepare");
        assert!(
            response["status"] == "rejected"
                || response["data"]["phase"] == "stale"
                || response["data"]["phase"] == "failed",
            "{response}"
        );
        let error = response["error"]
            .as_str()
            .or_else(|| response["data"]["error"].as_str());
        assert!(matches!(error, Some("Stale" | "Scope")), "{response}");
        assert_eq!(seen.count(), 0);
        assert!(seen.requests.lock().unwrap().is_empty());
        let d = data.lock().unwrap();
        assert_eq!(d.snapshots, 0);
        assert_eq!(d.engine.accepted_history_basis().unwrap(), keep);
    }
}

#[test]
fn canonical_resume_panic_is_contained_and_retry_uses_same_live_host_without_factory_before_recovery(
) {
    let original = selected();
    let (h, data) = port(original.clone(), SnapshotFault::Panic);
    let seen = Arc::new(Seen::default());
    h.configure_fixture_provider_with_construction(
        profile(),
        seen.factory(),
        HostPlayConstructionV1::PlayerLiteralV1,
    )
    .unwrap();
    let (s, scope, head) = create(&h);
    let r = request(&scope, head, "read-panic", PlayInputKind::Action);
    assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
    data.lock().unwrap().panic_resume = true;
    let failed = op(&h, &s, &r, "prepare");
    assert_eq!(failed["status"], "rejected", "{failed}");
    assert_eq!(failed["error"], "Internal");
    assert_eq!(seen.count(), 0);
    assert_eq!(call(&h, json!({"op":"model_status"}))["status"], "ok");
    assert_eq!(
        data.lock()
            .unwrap()
            .engine
            .accepted_history_basis()
            .unwrap(),
        original.accepted_history_basis().unwrap()
    );
    let ready = op(&h, &s, &r, "prepare");
    assert_eq!(ready["data"]["phase"], "ready", "{ready}");
    literal_record(&op(&h, &s, &r, "commit"));
    assert_eq!(seen.count(), 1);
    assert_eq!(data.lock().unwrap().snapshots, 0);
}

#[test]
fn cancelled_or_foreign_captured_selection_cannot_start_canonical_generation_or_provider() {
    let (h, data) = port(selected(), SnapshotFault::Panic);
    let seen = Arc::new(Seen::default());
    h.configure_fixture_provider_with_construction(
        profile(),
        seen.factory(),
        HostPlayConstructionV1::PlayerLiteralV1,
    )
    .unwrap();
    let (s, scope, head) = create(&h);
    let r = request(&scope, head, "cancelled", PlayInputKind::Action);
    assert_eq!(submit(&h, &s, &r)["data"]["phase"], "queued");
    assert_eq!(op(&h, &s, &r, "cancel")["data"]["phase"], "cancelled");
    let reads = data.lock().unwrap().resumes;
    assert_eq!(op(&h, &s, &r, "prepare")["data"]["phase"], "cancelled");
    let missing = call(
        &h,
        json!({"op":"prepare","session":"not-a-session","scope":scope,"turn":r.turn}),
    );
    assert_eq!(missing["error"], "Closed");
    let mut foreign = scope.clone();
    foreign.branch = "unselected".into();
    assert_eq!(
        call(
            &h,
            json!({"op":"prepare","session":s,"scope":foreign,"turn":r.turn})
        )["error"],
        "Scope"
    );
    assert_eq!(data.lock().unwrap().resumes, reads);
    assert_eq!(seen.count(), 0);
    assert_eq!(data.lock().unwrap().snapshots, 0);
    // Resume carries no cancellation argument and Host has no public token for
    // this private read. Mid-read latch behavior is not forged via a new hook.
}

#[test]
fn actual_domain2_literal_work_refuses_before_constructing_a_provider() {
    let parent = selected();
    let input = locallore::author_correction::AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "literal-unsupported-domain2".into(),
        operation:
            locallore::author_correction::AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "ancestry".into(),
                expected_proposition: parent.seed().facts["ancestry"].proposition.clone(),
                replacement: "Actual author-corrected fixture value.".into(),
            },
        reason: "Synthetic Domain2 refusal fixture.".into(),
    };
    let prepared = parent.prepare_author_correction(&input, &|| false).unwrap();
    let engine = parent
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .engine;
    assert_eq!(engine.domain_version(), 2);
    let basis = engine.accepted_history_basis().unwrap();
    let (host, data) = port(engine, SnapshotFault::Panic);
    let seen = Arc::new(Seen::default());
    host.configure_fixture_provider_with_construction(
        profile(),
        seen.factory(),
        HostPlayConstructionV1::PlayerLiteralV1,
    )
    .unwrap();
    let (session, scope, head) = create(&host);
    let request = request(&scope, head, "domain2-refused", PlayInputKind::Action);
    assert_eq!(submit(&host, &session, &request)["data"]["phase"], "queued");
    let refused = op(&host, &session, &request, "prepare");
    assert_eq!(refused["data"]["phase"], "failed");
    assert_eq!(refused["data"]["error"], "Version");
    assert_eq!(seen.count(), 0);
    assert!(seen.requests.lock().unwrap().is_empty());
    let state = data.lock().unwrap();
    assert_eq!(state.snapshots, 0);
    assert_eq!(state.engine.accepted_history_basis().unwrap(), basis);
}
