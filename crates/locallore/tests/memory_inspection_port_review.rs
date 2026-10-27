//! Independent native-port adversaries. Actual Engine/proof/Host; no SQLite/model/UI claim.
#![cfg(feature = "host")]

use locallore::{
    contracts::*,
    engine::Engine,
    host::{Host, HostGenerationSnapshot, Persistence, SavedTurn, WorkspaceSummary,
        memory_inspection::{MemoryInspectionError as E, MemoryInspectionReplyV1 as Reply,
            MemoryInspectionRequestV1 as Read, MemoryInspectionViewV1 as View}},
    inspection_query::Observer,
    memory_coverage::{self, ChunkRequest, CoverageRead, CoverageRequest, FallbackReason},
};
use serde_json::{Value, json};
use std::{cell::Cell, sync::{Arc, Mutex, atomic::{AtomicBool, AtomicUsize, Ordering}}};

struct Port {
    initial: Engine,
    actual: Arc<Mutex<Engine>>,
    foreign_proof: Option<Engine>,
    reads: Arc<AtomicUsize>,
    panic_next: Arc<AtomicBool>,
}
impl Persistence for Port {
    fn location(&self) -> &str { "synthetic-untrusted-native-port" }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> { Ok(vec![]) }
    fn create(&mut self) -> Result<Engine, String> { Ok(self.initial.clone()) }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        panic!("reader must use one coherent generation_snapshot, never a second resume")
    }
    fn generation_snapshot(&mut self, _: &Scope, _: u64, _: &str,
        _: &dyn Fn() -> bool) -> Result<HostGenerationSnapshot, String> {
        self.reads.fetch_add(1, Ordering::SeqCst);
        assert!(!self.panic_next.swap(false, Ordering::SeqCst), "synthetic override panic");
        let coverage = if let Some(other) = &self.foreign_proof {
            let packet = memory_coverage::build_chunk(other, &ChunkRequest {
                scope: other.scope().clone(), expected_head: other.revision(),
                observer: other.seed().player.clone(), from_exclusive: 0,
            }, &|| false).unwrap().unwrap().bytes().unwrap();
            let proof = memory_coverage::verify_coverage(other, &CoverageRequest {
                scope: other.scope().clone(), expected_head: other.revision(),
                observer: other.seed().player.clone(),
            }, &[&packet], &|| false).unwrap();
            assert!(matches!(proof, CoverageRead::Verified(_)), "genuine proof for OTHER Engine");
            proof
        } else { CoverageRead::RawFallback(FallbackReason::Missing) };
        Ok(HostGenerationSnapshot { engine:self.actual.lock().unwrap().clone(), coverage })
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn,String> { panic!("no writer admission") }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt,String> { panic!("no commit") }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn,String> { panic!("no draft cancellation") }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn,String> { panic!("no draft mutation") }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn,String> { panic!("no draft mutation") }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn,String> { panic!("no status mutation port") }
}
fn base() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()).unwrap()
}
fn accepted(text: &str) -> Engine {
    let mut e=base();
    let r=e.request("same-original-turn", Intent::Actions(vec![Command::Say {
        text:text.into(), audience:["mira".into()].into(),
    }]));
    let p=Engine::proposal(&r).unwrap();
    let receipt=e.preview(&r,&p).unwrap();
    e.commit_prepared(&receipt).unwrap();
    e
}
struct Fixture {
    host:Host, session:String, request:Read,
    actual:Arc<Mutex<Engine>>, reads:Arc<AtomicUsize>, panic_next:Arc<AtomicBool>,
}
fn fixture(lab:bool, engine:Engine, foreign_proof:Option<Engine>) -> Fixture {
    let initial=base();
    let actual=Arc::new(Mutex::new(engine));
    let reads=Arc::new(AtomicUsize::new(0));
    let panic_next=Arc::new(AtomicBool::new(false));
    let host=Host::with_persistence(lab,Box::new(Port {
        initial,actual:actual.clone(),foreign_proof,reads:reads.clone(),panic_next:panic_next.clone(),
    }));
    let created=host.call(&serde_json::to_vec(&json!({"version":1,"command":{"op":"create","seed":"lantern-quay-v1"}})).unwrap());
    assert_eq!(created["status"],"ok","{created}");
    let (scope,head)={let engine=actual.lock().unwrap();(engine.scope().clone(),engine.revision())};
    let request=Read { version:1, scope,
        expected_head:head, observer:Observer::Player,
        binding:None, view:View::Packets { cursor:None,limit:64 } };
    Fixture { host, session:created["data"]["session"].as_str().unwrap().into(),request,actual,reads,panic_next }
}
fn page(reply:Reply) -> locallore::host::memory_inspection::MemoryInspectionPageV1 {
    match reply { Reply::Page(p)=>p, _=>panic!("actual packets page required") }
}

#[test]
fn genuine_foreign_proof_is_rechecked_against_actual_engine_before_any_payload_is_returned() {
    let f=fixture(true,accepted("ACTUAL_PLAYER_B"),Some(accepted("FOREIGN_PACKET_A")));
    let before=f.actual.lock().unwrap().canonical_bytes();
    let p=page(f.host.memory_inspection(&f.session,&f.request,&||false).unwrap());
    assert_eq!(p.coverage.status,locallore::host::memory_inspection::MemoryCoverageStatusV1::RawFallback);
    assert!(p.coverage.fallback.is_some());
    assert!(p.rows.is_empty());
    let encoded=serde_json::to_string(&p).unwrap();
    assert!(!encoded.contains("FOREIGN_PACKET_A"));
    assert!(!encoded.contains("ACTUAL_PLAYER_B"),"no rejected cache or complete canonical source serialized");
    assert_eq!(f.reads.load(Ordering::SeqCst),1);
    assert_eq!(f.actual.lock().unwrap().canonical_bytes(),before);
}

#[test]
fn same_seed_head_scope_and_missing_cache_still_bind_complete_accepted_history() {
    let f=fixture(true,accepted("BASIS_A"),None);
    let a=page(f.host.memory_inspection(&f.session,&f.request,&||false).unwrap());
    *f.actual.lock().unwrap()=accepted("BASIS_B");
    let b=page(f.host.memory_inspection(&f.session,&f.request,&||false).unwrap());
    assert_eq!(a.head,b.head);
    assert_eq!(a.scope,b.scope);
    assert_eq!(a.coverage,b.coverage);
    assert_ne!(a.binding,b.binding,"empty cache/identical scope and head cannot identify accepted history");
    let mut old=f.request.clone(); old.binding=Some(a.binding);
    assert_eq!(f.host.memory_inspection(&f.session,&old,&||false).unwrap_err(),E::Binding);
    assert_eq!(f.reads.load(Ordering::SeqCst),3);
}

#[test]
fn forbidden_lenses_and_missing_lab_grant_never_probe_native_snapshot() {
    for lab in [false,true] {
        let f=fixture(lab,accepted("NATIVE_SOURCE"),None);
        for observer in [Observer::Omniscient,Observer::Character { id:base().seed().player.clone() }] {
            let mut request=f.request.clone(); request.observer=observer;
            assert_eq!(f.host.memory_inspection(&f.session,&request,&||false).unwrap_err(),E::Forbidden);
        }
        if !lab { assert_eq!(f.host.memory_inspection(&f.session,&f.request,&||false).unwrap_err(),E::Forbidden); }
        assert_eq!(f.reads.load(Ordering::SeqCst),0);
    }
}

#[test]
fn override_panic_is_contained_and_same_host_remains_usable() {
    let f=fixture(true,accepted("NATIVE_SOURCE"),None);
    f.panic_next.store(true,Ordering::SeqCst);
    assert_eq!(f.host.memory_inspection(&f.session,&f.request,&||false).unwrap_err(),E::Internal);
    assert!(f.host.memory_inspection(&f.session,&f.request,&||false).is_ok());
    assert_eq!(f.reads.load(Ordering::SeqCst),2);
}

#[test]
fn cancellation_during_source_hash_and_callback_panic_cannot_publish_or_poison_host() {
    let f=fixture(true,accepted("NATIVE_SOURCE"),None);
    let calls=Cell::new(0);
    let cancel=|| { calls.set(calls.get()+1); calls.get()>24 };
    assert_eq!(f.host.memory_inspection(&f.session,&f.request,&cancel).unwrap_err(),E::Cancelled);
    assert!(calls.get()>24,"cancellation reaches source serialization rather than initial refusal");
    assert_eq!(f.reads.load(Ordering::SeqCst),1);
    assert_eq!(f.host.memory_inspection(&f.session,&f.request,&||panic!("synthetic cancel panic")).unwrap_err(),E::Cancelled);
    let p=page(f.host.memory_inspection(&f.session,&f.request,&||false).unwrap());
    let json=serde_json::to_value(p).unwrap();
    assert_eq!(json["privacy"],Value::String("player_visible".into()));
}
