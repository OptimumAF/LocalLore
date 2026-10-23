// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Native default-port/Host guard checks, separate from actual SQLite integration.
use super::*;
use crate::memory_coverage::{CoverageRead, FallbackReason};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};

struct LegacyPort {
    actual: Engine,
    reads: Arc<AtomicUsize>,
    cancel_on_read: Option<Arc<AtomicBool>>,
}
impl Persistence for LegacyPort {
    fn location(&self) -> &str {
        "synthetic-native-default"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        unreachable!()
    }
    fn create(&mut self) -> Result<Engine, String> {
        unreachable!()
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        self.reads.fetch_add(1, Ordering::SeqCst);
        if let Some(cancel) = &self.cancel_on_read {
            cancel.store(true, Ordering::SeqCst);
        }
        Ok(self.actual.clone())
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
struct OverridePort(Engine);
impl Persistence for OverridePort {
    fn location(&self) -> &str {
        "synthetic-native-override"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        unreachable!()
    }
    fn create(&mut self) -> Result<Engine, String> {
        unreachable!()
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        unreachable!("override must not use a second read")
    }
    fn generation_snapshot(
        &mut self,
        _: &Scope,
        _: u64,
        _: &str,
        _: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        Ok(HostGenerationSnapshot {
            engine: self.0.clone(),
            coverage: CoverageRead::RawFallback(FallbackReason::Missing),
        })
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
/// Deliberately invokes the supplied callback without its own panic catcher.
/// The new Host port must hand every override a safe cancellation boundary.
struct CallbackPort(Engine);
impl Persistence for CallbackPort {
    fn location(&self) -> &str {
        "synthetic-native-callback"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        unreachable!()
    }
    fn create(&mut self) -> Result<Engine, String> {
        unreachable!()
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        unreachable!()
    }
    fn generation_snapshot(
        &mut self,
        _: &Scope,
        _: u64,
        _: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        if cancel() {
            return Err("Cancelled".into());
        }
        Ok(HostGenerationSnapshot {
            engine: self.0.clone(),
            coverage: CoverageRead::RawFallback(FallbackReason::Missing),
        })
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
fn cancellation_panic_inside_override_is_cancelled_and_host_owner_remains_usable() {
    let actual = engine();
    let host = Host::with_persistence(false, Box::new(CallbackPort(actual.clone())));
    let session = attach(&host, actual.clone());
    let calls = AtomicUsize::new(0);
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        host.generation_snapshot(&session, actual.scope(), 0, &|| {
            if calls.fetch_add(1, Ordering::SeqCst) > 0 {
                panic!("synthetic callback panic inside native override");
            }
            false
        })
    }));
    assert!(
        host.generation_snapshot(&session, actual.scope(), 0, &|| false)
            .is_ok(),
        "callback rejection must leave Host owner usable"
    );
    assert!(
        result.is_ok(),
        "callback panic must not escape native override"
    );
    assert_eq!(error(result.unwrap()), "Cancelled");
    assert_eq!(calls.load(Ordering::SeqCst), 2);
}

/// An override that ignores the callback result must not erase cancellation.
struct IgnoringCallbackPort(Engine);
impl Persistence for IgnoringCallbackPort {
    fn location(&self) -> &str {
        "synthetic-native-ignoring-callback"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        unreachable!()
    }
    fn create(&mut self) -> Result<Engine, String> {
        unreachable!()
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        unreachable!()
    }
    fn generation_snapshot(
        &mut self,
        _: &Scope,
        _: u64,
        _: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        let _ignored = cancel();
        Ok(HostGenerationSnapshot {
            engine: self.0.clone(),
            coverage: CoverageRead::RawFallback(FallbackReason::Missing),
        })
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
fn ignored_one_shot_cancel_remains_cancelled(panic: bool) {
    let actual = engine();
    let host = Host::with_persistence(false, Box::new(IgnoringCallbackPort(actual.clone())));
    let session = attach(&host, actual.clone());
    let calls = AtomicUsize::new(0);
    let result = host.generation_snapshot(&session, actual.scope(), 0, &|| {
        if calls.fetch_add(1, Ordering::SeqCst) == 1 {
            assert!(!panic, "synthetic one-shot ignored callback panic");
            true
        } else {
            false
        }
    });
    assert!(host
        .generation_snapshot(&session, actual.scope(), 0, &|| false)
        .is_ok());
    assert_eq!(
        error(result),
        "Cancelled",
        "an observed one-shot cancellation cannot recover at final validation"
    );
    assert_eq!(
        calls.load(Ordering::SeqCst),
        2,
        "once cancelled, final validation must use the retained observation"
    );
}
#[test]
fn ignored_one_shot_true_stays_cancelled_at_host_return() {
    ignored_one_shot_cancel_remains_cancelled(false);
}
#[test]
fn ignored_one_shot_panic_stays_cancelled_at_host_return() {
    ignored_one_shot_cancel_remains_cancelled(true);
}
fn engine() -> Engine {
    Engine::new(
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap(),
    )
    .unwrap()
}
fn attach(host: &Host, engine: Engine) -> String {
    attach_engine(&mut host.state.lock().unwrap(), engine)["data"]["session"]
        .as_str()
        .unwrap()
        .into()
}
fn error(result: Result<HostGenerationSnapshot, String>) -> String {
    match result {
        Err(error) => error,
        Ok(_) => panic!("expected guarded snapshot refusal"),
    }
}

#[test]
fn legacy_default_resumes_actual_engine_without_fabricating_verified_coverage() {
    let cached = engine();
    let mut actual = cached.clone();
    let request = actual.request(
        "external",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let narration = actual
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    actual.commit(&request, &proposal, &narration).unwrap();
    let reads = Arc::new(AtomicUsize::new(0));
    let host = Host::with_persistence(
        false,
        Box::new(LegacyPort {
            actual: actual.clone(),
            reads: reads.clone(),
            cancel_on_read: None,
        }),
    );
    let session = attach(&host, cached.clone());
    let snapshot = host
        .generation_snapshot(&session, cached.scope(), 1, &|| false)
        .unwrap();
    assert_eq!(snapshot.engine.receipts(), actual.receipts());
    assert_eq!(snapshot.engine.canonical_bytes(), actual.canonical_bytes());
    assert!(matches!(
        snapshot.coverage,
        CoverageRead::RawFallback(FallbackReason::Missing)
    ));
    assert_eq!(reads.load(Ordering::SeqCst), 1);
    assert_eq!(
        host.state.lock().unwrap().sessions[&session]
            .engine
            .revision(),
        0
    );
}

#[test]
fn default_port_rejects_scope_head_and_nonplayer_observer() {
    let actual = engine();
    let mut port = LegacyPort {
        actual: actual.clone(),
        reads: Arc::new(AtomicUsize::new(0)),
        cancel_on_read: None,
    };
    let wrong = Scope {
        branch: "other".into(),
        ..actual.scope().clone()
    };
    assert_eq!(
        error(port.generation_snapshot(&wrong, 0, "player", &|| false)),
        "Scope"
    );
    assert_eq!(
        error(port.generation_snapshot(actual.scope(), 1, "player", &|| false)),
        "Stale"
    );
    assert_eq!(
        error(port.generation_snapshot(actual.scope(), 0, "mira", &|| false)),
        "Stale"
    );
}

#[test]
fn panicking_or_late_cancel_is_cancelled_and_does_not_poison_session_lock() {
    let actual = engine();
    let reads = Arc::new(AtomicUsize::new(0));
    let cancelled = Arc::new(AtomicBool::new(false));
    let host = Host::with_persistence(
        false,
        Box::new(LegacyPort {
            actual: actual.clone(),
            reads: reads.clone(),
            cancel_on_read: Some(cancelled.clone()),
        }),
    );
    let session = attach(&host, actual.clone());
    assert_eq!(
        error(
            host.generation_snapshot(&session, actual.scope(), 0, &|| panic!(
                "synthetic cancellation panic"
            ))
        ),
        "Cancelled"
    );
    assert_eq!(reads.load(Ordering::SeqCst), 0);
    assert_eq!(
        error(host.generation_snapshot(&session, actual.scope(), 0, &|| {
            cancelled.load(Ordering::SeqCst)
        })),
        "Cancelled"
    );
    assert_eq!(reads.load(Ordering::SeqCst), 1);
    assert!(host
        .generation_snapshot(&session, actual.scope(), 0, &|| false)
        .is_ok());
}

#[test]
fn native_override_cannot_bypass_returned_scope_head_or_entire_seed_guard() {
    let cached = engine();
    for kind in ["scope", "head", "seed", "player"] {
        let mut actual_seed = cached.seed().clone();
        if kind == "scope" {
            actual_seed.scope.branch = "other".into();
        }
        if kind == "seed" {
            actual_seed.facts.get_mut("ancestry").unwrap().proposition =
                "A different seed at the same identity and revision.".into();
        }
        if kind == "player" {
            actual_seed.player = "mira".into();
        }
        let mut actual = Engine::new(actual_seed).unwrap();
        if kind == "head" {
            let request =
                actual.request("newer", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
            let proposal = Engine::proposal(&request).unwrap();
            let narration = actual
                .preview(&request, &proposal)
                .unwrap()
                .narration()
                .to_owned();
            actual.commit(&request, &proposal, &narration).unwrap();
        }
        let host = Host::with_persistence(false, Box::new(OverridePort(actual)));
        let session = attach(&host, cached.clone());
        assert_eq!(
            error(host.generation_snapshot(&session, cached.scope(), 0, &|| false)),
            if kind == "scope" { "Scope" } else { "Stale" },
            "{kind}"
        );
        assert_eq!(
            host.state.lock().unwrap().sessions[&session].engine.seed(),
            cached.seed()
        );
    }
}

#[test]
fn poisoned_host_refuses_snapshot_before_native_dispatch() {
    let actual = engine();
    let reads = Arc::new(AtomicUsize::new(0));
    let host = Host::with_persistence(
        false,
        Box::new(LegacyPort {
            actual: actual.clone(),
            reads: reads.clone(),
            cancel_on_read: None,
        }),
    );
    let session = attach(&host, actual.clone());
    let state = host.state.clone();
    assert!(std::thread::spawn(move || {
        let _held = state.lock().unwrap();
        panic!("synthetic owner poison");
    })
    .join()
    .is_err());
    assert_eq!(
        error(host.generation_snapshot(&session, actual.scope(), 0, &|| false)),
        "Internal"
    );
    assert_eq!(reads.load(Ordering::SeqCst), 0);
}
