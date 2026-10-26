// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN actual Repository/Store oracles.
//! Synthetic providers even when testing the native real-model LABEL setter.
//! No model, UI/IPC/device, competing Persistence, SQL or forged receipt fixture.
use locallore::{
    contracts::{Command, Error, Intent, PlayInputKind, Request, Scope},
    engine::Engine,
    host::{Host, HostPlayConstructionV1},
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    memory_coverage::CoverageRead,
    play::{PlayProfile, LITERAL_PLAY_PROMPT_VERSION_V1},
};
use locallore_storage::{memory_jobs::{MemoryJobRequest, MemoryJobStatus}, Store};
use serde_json::{json, Value};
use std::{path::PathBuf, sync::{atomic::{AtomicBool, AtomicUsize, Ordering}, mpsc, Arc}, task::Poll, thread, time::Duration};

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!("literal-host-durable-{}-{}", std::process::id(),
            std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        std::fs::create_dir(&path).unwrap(); Self(path)
    }
    fn path(&self) -> PathBuf { self.0.join("stories.sqlite") }
    fn host(&self) -> Host { locallore_workspace::open(&self.path(), false).unwrap() }
    fn store(&self) -> Store { Store::open_application(&self.path()).unwrap() }
}
// Retain bounded synthetic artifacts in caller-owned TEMP, including on failure.
fn call(h: &Host, command: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn create(h: &Host) -> (String, Scope) {
    let value = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(value["status"], "ok");
    (value["data"]["session"].as_str().unwrap().into(), serde_json::from_value(value["data"]["scope"].clone()).unwrap())
}
fn resume(h: &Host, scope: &Scope) -> String {
    let value = call(h, json!({"op":"resume","scope":scope}));
    assert_eq!(value["status"], "ok"); value["data"]["session"].as_str().unwrap().into()
}
fn text(kind: PlayInputKind) -> &'static str {
    if kind == PlayInputKind::Action { "I wait for one tide tick." }
    else { "Mira, keep the harbor promise: café 灯 🧭." }
}
fn request(scope: &Scope, key: &str, head: u64, kind: PlayInputKind) -> Request {
    Request { version:1, scope:scope.clone(), turn:key.into(), expected_revision:head,
        intent:Intent::FreeText { kind, text:text(kind).into() } }
}
fn op(h: &Host, session: &str, r: &Request, op: &str) -> Value {
    call(h, json!({"op":op,"session":session,"scope":r.scope,"turn":r.turn}))
}
fn submit(h: &Host, session: &str, r: &Request) {
    assert_eq!(call(h,json!({"op":"free_text","session":session,"request":r}))["data"]["phase"], "queued");
}
fn profile() -> PlayProfile {
    PlayProfile { id:"synthetic-literal-host".into(), model_sha256:"a".repeat(64), runtime_revision:"b".repeat(40),
        template_sha256:"c".repeat(64), worker_sha256:"d".repeat(64), profile_manifest_sha256:"e".repeat(64),
        context_tokens:4096, director_tokens:350, narrator_tokens:350, deadline_ms:5000, repair_limit:1 }
}
#[derive(Clone, Default)]
struct Counts { factories:Arc<AtomicUsize>, polls:Arc<AtomicUsize> }
struct Script { counts:Counts, kind:PlayInputKind, hold:Option<(Arc<AtomicBool>,mpsc::SyncSender<()>)>, announced:bool }
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.counts.polls.fetch_add(1,Ordering::SeqCst);
        let Input::Structured { role, .. } = &r.input else { panic!("actual structured path required") };
        if role == "director" {
            if let Some((release, entered)) = &self.hold {
                if !self.announced { let _ = entered.try_send(()); self.announced = true; }
                if !release.load(Ordering::SeqCst) { return Poll::Pending; }
            }
        }
        let value = match role.as_str() {
            "director" if self.kind == PlayInputKind::Action => json!({"commands":[{"op":"wait","ticks":1}]}),
            "director" => json!({"commands":[{"op":"say","text":text(self.kind),"audience":["mira"]}]}),
            "narrator" => json!({"text":if self.kind == PlayInputKind::Action {"You pause as a tide tick passes."} else {"Your words are heard by the chosen listeners."},"event_ids":[r.revision+1],"speaker":"narrator"}),
            _ => panic!("unexpected role"),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
fn configure(h: &Host, counts:&Counts, kind:PlayInputKind, real_label:bool,
    hold:Option<(Arc<AtomicBool>,mpsc::SyncSender<()>)>) {
    let counts=counts.clone();
    let factory:locallore::host::ProviderFactory=Arc::new(move || {
        counts.factories.fetch_add(1,Ordering::SeqCst);
        Box::new(Script { counts:counts.clone(), kind, hold:hold.clone(), announced:false })
    });
    if real_label { h.configure_local_provider_with_construction(profile(),factory,HostPlayConstructionV1::PlayerLiteralV1) }
    else { h.configure_fixture_provider_with_construction(profile(),factory,HostPlayConstructionV1::PlayerLiteralV1) }.unwrap();
}
fn typed(store:&mut Store, scope:&Scope, key:&str, commands:Vec<Command>) {
    let e=store.resume(scope).unwrap().engine;
    let r=e.request(key,Intent::Actions(commands)); let p=Engine::proposal(&r).unwrap();
    let preview=e.preview(&r,&p).unwrap();
    store.begin_turn(&r).unwrap();
    assert_eq!(store.commit_turn(&r,&p,preview.narration()).unwrap(),preview);
}

#[test]
fn both_modes_prepare_without_canon_commit_literal_then_restart_and_exact_retry_without_factory() {
    for (kind, real_label) in [(PlayInputKind::Action,false),(PlayInputKind::Dialogue,true)] {
        let temp=Temp::new(); let h=temp.host(); let (session,scope)=create(&h); let counts=Counts::default();
        configure(&h,&counts,kind,real_label,None);
        assert_eq!(call(&h,json!({"op":"model_status"}))["data"]["real_model"],real_label);
        let r=request(&scope,"literal-original",0,kind);
        let before=temp.store().resume(&scope).unwrap().engine.accepted_history_basis().unwrap();
        submit(&h,&session,&r);
        let ready=op(&h,&session,&r,"prepare"); assert_eq!(ready["data"]["phase"],"ready");
        assert_eq!(ready["data"]["receipt"],Value::Null,"Ready does not export a fabricated receipt");
        assert_eq!(temp.store().resume(&scope).unwrap().engine.accepted_history_basis().unwrap(),before);
        let accepted=op(&h,&session,&r,"commit"); assert_eq!(accepted["data"]["phase"],"committed");
        let play=&accepted["data"]["receipt"]["play"];
        assert_eq!(play["prompt_version"],LITERAL_PLAY_PROMPT_VERSION_V1);
        assert_eq!(play["context"],Value::Null); assert_eq!(play["context_policy"],Value::Null);
        assert_eq!(accepted["data"]["receipt"]["request"],json!(r));
        assert_eq!(counts.factories.load(Ordering::SeqCst),1); assert_eq!(counts.polls.load(Ordering::SeqCst),2);
        // Native constructor selection is never deserialized through Host JSON.
        assert_eq!(call(&h,json!({"op":"configure_fixture_provider_with_construction","construction":"player_literal_v1"}))["error"],"Malformed");
        drop(h);
        let h=temp.host(); let session=resume(&h,&scope); let retry=Counts::default();
        configure(&h,&retry,kind,false,None);
        assert_eq!(op(&h,&session,&r,"turn_status"),accepted);
        assert_eq!(call(&h,json!({"op":"submit","session":session,"request":r,"mode":"accepted"})),accepted);
        assert_eq!(op(&h,&session,&r,"prepare"),accepted); assert_eq!(op(&h,&session,&r,"commit"),accepted);
        assert_eq!(retry.factories.load(Ordering::SeqCst),0); assert_eq!(retry.polls.load(Ordering::SeqCst),0);
        let e=temp.store().resume(&scope).unwrap().engine; assert_eq!(e.revision(),1); assert_eq!(e.receipts().len(),1);
    }
}

#[test]
fn reopened_intent_draft_is_queued_not_a_persisted_prepared_output_and_commit_is_not_ready() {
    let temp=Temp::new(); let h=temp.host(); let (session,scope)=create(&h); let counts=Counts::default();
    configure(&h,&counts,PlayInputKind::Action,false,None);
    let r=request(&scope,"uncommitted-literal",0,PlayInputKind::Action); submit(&h,&session,&r);
    assert_eq!(op(&h,&session,&r,"prepare")["data"]["phase"],"ready"); drop(h);
    let h=temp.host(); let session=resume(&h,&scope); let retry=Counts::default();
    configure(&h,&retry,PlayInputKind::Action,false,None);
    assert_eq!(op(&h,&session,&r,"turn_status")["data"]["phase"],"queued");
    assert_eq!(op(&h,&session,&r,"commit")["error"],"NotReady");
    assert_eq!(retry.factories.load(Ordering::SeqCst),0); assert_eq!(retry.polls.load(Ordering::SeqCst),0);
    assert_eq!(temp.store().resume(&scope).unwrap().engine.revision(),0);
}

struct Held { release:Arc<AtomicBool>, entered:mpsc::Receiver<()>, worker:Option<thread::JoinHandle<Value>> }
impl Held {
    fn start(h:Arc<Host>, counts:&Counts, session:&str, r:&Request) -> Self {
        let release=Arc::new(AtomicBool::new(false)); let (send,entered)=mpsc::sync_channel(1);
        configure(&h,counts,PlayInputKind::Action,false,Some((release.clone(),send)));
        let session=session.to_owned(); let r=r.clone();
        let worker=thread::spawn(move || op(&h,&session,&r,"prepare"));
        Self { release,entered,worker:Some(worker) }
    }
    fn finish(mut self)->Value { self.release.store(true,Ordering::SeqCst); self.worker.take().unwrap().join().unwrap() }
}
impl Drop for Held {
    fn drop(&mut self) { self.release.store(true,Ordering::SeqCst); if let Some(worker)=self.worker.take(){let _=worker.join();} }
}

#[test]
fn cancel_while_actual_literal_provider_pending_is_durable_and_never_commits() {
    let temp=Temp::new(); let h=Arc::new(temp.host()); let (session,scope)=create(&h); let counts=Counts::default();
    configure(&h,&counts,PlayInputKind::Action,false,None);
    let r=request(&scope,"cancel-held",0,PlayInputKind::Action); submit(&h,&session,&r);
    let held=Held::start(h.clone(),&counts,&session,&r); let entered=held.entered.recv_timeout(Duration::from_secs(5));
    let cancelled=if entered.is_ok(){op(&h,&session,&r,"cancel")}else{Value::Null};
    let completed=held.finish(); assert!(entered.is_ok());
    assert_eq!(cancelled["data"]["phase"],"cancelled"); assert_eq!(completed["data"]["phase"],"cancelled");
    assert_eq!(temp.store().resume(&scope).unwrap().engine.revision(),0); drop(h);
    let h=temp.host(); let session=resume(&h,&scope);
    assert_eq!(op(&h,&session,&r,"turn_status")["data"]["phase"],"cancelled");
    assert_eq!(temp.store().resume(&scope).unwrap().engine.receipts().len(),0);
}

#[test]
fn another_actual_store_writer_advances_canon_while_literal_work_is_held_and_old_work_is_stale() {
    let temp=Temp::new(); let h=Arc::new(temp.host()); let (session,scope)=create(&h); let counts=Counts::default();
    configure(&h,&counts,PlayInputKind::Action,false,None);
    let r=request(&scope,"stale-held",0,PlayInputKind::Action); submit(&h,&session,&r);
    let held=Held::start(h.clone(),&counts,&session,&r); let entered=held.entered.recv_timeout(Duration::from_secs(5));
    if entered.is_ok(){typed(&mut temp.store(),&scope,"other-owner",vec![Command::Wait{ticks:1}]);}
    let completed=held.finish(); assert!(entered.is_ok());
    assert_eq!(completed["data"]["phase"],"stale"); assert_eq!(completed["data"]["error"],"Stale");
    let e=temp.store().resume(&scope).unwrap().engine; assert_eq!(e.revision(),1);
    assert_eq!(e.receipts().len(),1); assert_eq!(e.receipts()[0].request().turn,"other-owner");
    assert_ne!(op(&h,&session,&r,"commit")["data"]["phase"],"committed");
}

#[test]
fn completed_memory_job_proof_and_missing_partition_are_unchanged_by_literal_prepare() {
    let temp=Temp::new(); let h=temp.host(); let (_,scope)=create(&h); drop(h);
    let mut store=temp.store();
    typed(&mut store,&scope,"prefix",vec![Command::Wait{ticks:1},Command::Say{text:"Actual recorded harbor dialogue.".into(),audience:["mira".into()].into()}]);
    let selected=store.resume(&scope).unwrap().engine;
    let request=MemoryJobRequest{scope:scope.clone(),observer:"player".into(),expected_head:2};
    let mut info=store.ensure_memory_job(&request,&||false).unwrap();
    for _ in 0..8 {
        if info.status==MemoryJobStatus::Complete {break}
        let prepared=store.prepare_memory_job_step(&info.handle,&||false).unwrap();
        info=store.publish_memory_job_step(prepared,&||false).unwrap();
    }
    assert_eq!(info.status,MemoryJobStatus::Complete);
    assert!(matches!(store.context_snapshot(&request,&||false).unwrap().coverage,CoverageRead::Verified(_)));
    let missing=MemoryJobRequest{scope:scope.clone(),observer:"mira".into(),expected_head:2};
    assert!(store.lookup_memory_job(&missing,&selected,&||false).unwrap().is_none());
    let h=temp.host(); let session=resume(&h,&scope); let counts=Counts::default();
    configure(&h,&counts,PlayInputKind::Action,false,None);
    let r=self::request(&scope,"cache-independent",2,PlayInputKind::Action); submit(&h,&session,&r);
    assert_eq!(op(&h,&session,&r,"prepare")["data"]["phase"],"ready");
    assert_eq!(store.resume(&scope).unwrap().engine.accepted_history_basis().unwrap(),selected.accepted_history_basis().unwrap());
    assert_eq!(store.memory_job_status(&info.handle,&||false).unwrap(),info);
    assert!(store.lookup_memory_job(&missing,&selected,&||false).unwrap().is_none());
    assert!(matches!(store.context_snapshot(&request,&||false).unwrap().coverage,CoverageRead::Verified(_)));
    assert_eq!(counts.factories.load(Ordering::SeqCst),1); assert_eq!(counts.polls.load(Ordering::SeqCst),2);
    // Known job metadata/proof and absent partition checked, not whole-table SQL
    // inventory or malformed-cache injection (no public raw connection here).
}
