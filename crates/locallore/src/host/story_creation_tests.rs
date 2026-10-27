// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use super::*;
use std::sync::atomic::{AtomicUsize, Ordering};

struct NoCreation(Arc<AtomicUsize>);
impl Persistence for NoCreation {
    fn location(&self) -> &str {
        "synthetic-prewrite-guard"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        unreachable!()
    }
    fn create(&mut self) -> Result<Engine, String> {
        unreachable!()
    }
    fn create_named(
        &mut self,
        _: &crate::story_setup::NamedStarter,
    ) -> Result<(Engine, bool), String> {
        self.0.fetch_add(1, Ordering::SeqCst);
        panic!("attachment failure reached persistent creation")
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        unreachable!()
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        unreachable!()
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        unreachable!()
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        unreachable!()
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        unreachable!()
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        unreachable!()
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        unreachable!()
    }
}

#[test]
fn named_creation_checks_exhausted_attachment_id_before_persistence() {
    let calls = Arc::new(AtomicUsize::new(0));
    let host = Host::with_persistence(false, Box::new(NoCreation(calls.clone())));
    host.state.lock().unwrap().next = u64::MAX;
    let preview = crate::story_setup::template_preview("lantern-quay-v1").unwrap();
    let request = json!({"version":1,"command":{"op":"create_named","template":preview.template,
        "seed_sha256":preview.seed_sha256,"title":"Original synthetic story","creation_id":"1".repeat(32)}});
    assert_eq!(
        host.call(&serde_json::to_vec(&request).unwrap())["error"],
        "IdExhausted"
    );
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert!(host.state.lock().unwrap().sessions.is_empty());
}

#[test]
fn title_limits_use_unicode_scalars_and_never_silently_normalize() {
    use crate::story_setup::valid_title;
    for value in [
        "雪".repeat(80),
        "🌊".repeat(80),
        "A real name — café".into(),
    ] {
        assert!(valid_title(&value));
    }
    for value in [
        String::new(),
        " ".into(),
        " leading".into(),
        "trailing\n".into(),
        "🌊".repeat(81),
        "x".repeat(81),
        "a\0b".into(),
        "a\u{2028}b".into(),
        "a\u{202e}b".into(),
        "a\u{2067}b".into(),
        "a\u{0085}b".into(),
    ] {
        assert!(!valid_title(&value), "invalid title was accepted");
    }
}

/// Fault port only: all unrelated operations retain NoCreation's fail-fast
/// behavior. This proves Host admission, not an executed Store replacement race.
struct ChangedOriginalSeed(NoCreation);
impl Persistence for ChangedOriginalSeed {
    fn location(&self) -> &str {
        self.0.location()
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        self.0.list()
    }
    fn create(&mut self) -> Result<Engine, String> {
        self.0.create()
    }
    fn create_named(
        &mut self,
        starter: &crate::story_setup::NamedStarter,
    ) -> Result<(Engine, bool), String> {
        let NoCreation(calls) = &self.0;
        calls.fetch_add(1, Ordering::SeqCst);
        let original = starter.seed();
        let mut replacement = original.clone();
        replacement.actors.get_mut("player").unwrap().name = "Different original player".into();
        let engine = Engine::new(replacement).unwrap();
        assert_eq!(engine.scope(), &original.scope);
        assert_ne!(engine.seed(), original);
        Ok((engine, true))
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        self.0.resume(scope)
    }
    fn begin(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.0.begin(request)
    }
    fn commit(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
    ) -> Result<Receipt, String> {
        self.0.commit(request, proposal, narration)
    }
    fn cancel(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.0.cancel(request)
    }
    fn fail(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.0.fail(request)
    }
    fn stale(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.0.stale(request)
    }
    fn status(&mut self, scope: &Scope, turn: &str) -> Result<SavedTurn, String> {
        self.0.status(scope, turn)
    }
}

#[test]
fn named_creation_refuses_a_valid_returned_engine_with_different_original_seed() {
    let calls = Arc::new(AtomicUsize::new(0));
    let host = Host::with_persistence(
        false,
        Box::new(ChangedOriginalSeed(NoCreation(calls.clone()))),
    );
    let preview = crate::story_setup::template_preview("lantern-quay-v1").unwrap();
    let request = json!({"version":1,"command":{"op":"create_named","template":preview.template,
        "seed_sha256":preview.seed_sha256,"title":"Original synthetic story","creation_id":"2".repeat(32)}});
    let reply = host.call(&serde_json::to_vec(&request).unwrap());
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    assert_eq!(reply["status"], "rejected");
    assert_eq!(reply["error"], "Stale");
    assert!(host.state.lock().unwrap().sessions.is_empty());
}
