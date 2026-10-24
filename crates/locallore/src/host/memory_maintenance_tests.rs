// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Host admission/lifecycle guards. These ports do not emulate SQLite.
use super::*;
use crate::{
    contracts::*,
    engine::Engine,
    host::{Persistence, SavedTurn, WorkspaceSummary},
};
use serde_json::{json, Value};
use std::sync::{
    atomic::{AtomicBool, AtomicUsize, Ordering},
    mpsc, Arc,
};

macro_rules! required_port {
    () => {
        fn location(&self) -> &str {
            "synthetic-maintenance-port"
        }
        fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
            Ok(vec![])
        }
        fn create(&mut self) -> Result<Engine, String> {
            Ok(self.engine.clone())
        }
        fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
            if self.engine.scope() == scope {
                Ok(self.engine.clone())
            } else {
                Err("Scope".into())
            }
        }
        fn begin(&mut self, request: &Request) -> Result<SavedTurn, String> {
            self.last = Some(request.clone());
            Ok(SavedTurn {
                request: request.clone(),
                receipt: None,
                phase: "draft".into(),
            })
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
        fn status(&mut self, scope: &Scope, turn: &str) -> Result<SavedTurn, String> {
            let request = self
                .last
                .as_ref()
                .filter(|request| &request.scope == scope && request.turn == turn)
                .ok_or("UnknownTurn")?;
            Ok(SavedTurn {
                request: request.clone(),
                receipt: None,
                phase: "draft".into(),
            })
        }
    };
}
struct Legacy {
    engine: Engine,
    last: Option<Request>,
}
impl Persistence for Legacy {
    required_port!();
}
struct Port {
    engine: Engine,
    last: Option<Request>,
    mode: u8,
    calls: Arc<AtomicUsize>,
    entered: Option<mpsc::SyncSender<()>>,
}
impl Persistence for Port {
    required_port!();
    fn begin_bound(
        &mut self,
        request: &Request,
        basis: &crate::engine::AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        assert!(basis.matches_request(request));
        assert!(self.engine.matches_accepted_history(basis).unwrap());
        self.begin(request)
    }
    fn status_bound(
        &mut self,
        request: &Request,
        basis: &crate::engine::AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        assert!(basis.covers_request(request));
        assert!(self.engine.matches_accepted_history(basis).unwrap());
        let saved = self.status(&request.scope, &request.turn)?;
        assert_eq!(saved.request, *request);
        Ok(saved)
    }
    fn memory_maintenance(
        &mut self,
        selected: &Engine,
        head: u64,
        action: MaintenanceAction,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MaintenanceReply, MaintenanceError> {
        self.calls.fetch_add(1, Ordering::Relaxed);
        assert_eq!(selected.seed().player, self.engine.seed().player);
        match self.mode {
            1 => {
                let _ = cancel();
                let _ = cancel();
            }
            2 => panic!("synthetic persistence panic"),
            3 => {
                self.entered.take().unwrap().send(()).unwrap();
                let deadline = std::time::Instant::now() + std::time::Duration::from_secs(2);
                while !cancel() {
                    if std::time::Instant::now() >= deadline {
                        return Err(MaintenanceError::Internal);
                    }
                    std::thread::yield_now();
                }
                return Err(MaintenanceError::Cancelled);
            }
            _ => {}
        }
        Ok(MaintenanceReply {
            version: 1,
            scope: selected.scope().clone(),
            head: head + u64::from(self.mode == 4),
            action,
            job: (self.mode == 5).then_some(MaintenanceJobView {
                status: MaintenanceStatus::Stale,
                basis_revision: 1,
                next_from: 0,
                generation: 1,
                last_error: Some(MaintenanceFailure::Budget),
            }),
        })
    }
}
fn engine() -> Engine {
    Engine::new(
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap(),
    )
    .unwrap()
}
fn call(h: &Host, command: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn create(h: &Host) -> (String, Scope) {
    let v = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(v["status"], "ok", "{v}");
    (
        v["data"]["session"].as_str().unwrap().into(),
        serde_json::from_value(v["data"]["scope"].clone()).unwrap(),
    )
}
fn fixture(mode: u8, lab: bool) -> (Host, String, Scope, Arc<AtomicUsize>) {
    let calls = Arc::new(AtomicUsize::new(0));
    let host = Host::with_persistence(
        lab,
        Box::new(Port {
            engine: engine(),
            last: None,
            mode,
            calls: calls.clone(),
            entered: None,
        }),
    );
    let (session, scope) = create(&host);
    (host, session, scope, calls)
}
#[test]
fn default_port_and_ephemeral_are_explicitly_unsupported() {
    let host = Host::with_persistence(
        false,
        Box::new(Legacy {
            engine: engine(),
            last: None,
        }),
    );
    let (session, scope) = create(&host);
    assert_eq!(
        host.memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false),
        Err(MaintenanceError::Unsupported)
    );
    let host = Host::default();
    let (session, scope) = create(&host);
    assert_eq!(
        host.memory_maintenance(&session, &scope, 0, MaintenanceAction::Admit, &|| false),
        Err(MaintenanceError::Unsupported)
    );
}
#[test]
fn closed_scope_and_unknown_wire_operation_do_not_reach_port() {
    let (host, session, scope, calls) = fixture(0, false);
    assert_eq!(
        host.memory_maintenance("missing", &scope, 0, MaintenanceAction::Status, &|| false),
        Err(MaintenanceError::Closed)
    );
    let mut wrong = scope.clone();
    wrong.branch = "other".into();
    assert_eq!(
        host.memory_maintenance(&session, &wrong, 0, MaintenanceAction::Admit, &|| false),
        Err(MaintenanceError::Scope)
    );
    assert_eq!(
        call(
            &host,
            json!({"op":"memory_maintenance","session":session,"scope":scope})
        )["status"],
        "rejected"
    );
    assert_eq!(calls.load(Ordering::Relaxed), 0);
}
#[test]
fn all_selected_scope_pending_phases_block_mutations_but_not_status() {
    for phase in ["queued", "running", "ready"] {
        let (host, session, scope, calls) = fixture(0, false);
        // The fixed test port returns its one scope on both real Create
        // admissions, giving distinct cached sessions without inserting State.
        let (second, second_scope) = create(&host);
        assert_ne!(session, second);
        assert_eq!(scope, second_scope);
        let req = engine().request(
            "pending-maintenance",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        assert_eq!(
            call(
                &host,
                json!({"op":"submit","session":second,"request":req,"mode":"accepted"})
            )["data"]["phase"],
            "queued"
        );
        let work = if phase == "running" {
            Some(
                host.begin_work(&second, &scope, "pending-maintenance")
                    .ok()
                    .unwrap(),
            )
        } else {
            None
        };
        if phase == "ready" {
            assert_eq!(
                call(
                    &host,
                    json!({"op":"prepare","session":second,"scope":scope,"turn":"pending-maintenance"})
                )["data"]["phase"],
                "ready"
            );
        }
        for action in [
            MaintenanceAction::Admit,
            MaintenanceAction::Step,
            MaintenanceAction::Cancel,
            MaintenanceAction::Prune,
        ] {
            assert_eq!(
                host.memory_maintenance(&session, &scope, 0, action, &|| false),
                Err(MaintenanceError::Busy),
                "{phase}"
            );
        }
        assert!(host
            .memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false)
            .is_ok());
        assert_eq!(calls.load(Ordering::Relaxed), 1);
        drop(work);
    }
}
#[test]
fn true_or_panicking_callback_stays_cancelled_even_if_override_ignores_it() {
    for panic in [false, true] {
        let (host, session, scope, _) = fixture(1, false);
        let polls = std::cell::Cell::new(0);
        let cancel = || {
            let n = polls.get();
            polls.set(n + 1);
            if n == 2 {
                if panic {
                    panic!("synthetic cancellation");
                }
                true
            } else {
                false
            }
        };
        assert_eq!(
            host.memory_maintenance(&session, &scope, 0, MaintenanceAction::Admit, &cancel),
            Err(MaintenanceError::Cancelled)
        );
        assert!(host
            .memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false)
            .is_ok());
    }
}
#[test]
fn port_panic_and_invalid_reply_fail_closed_without_poisoning_host() {
    let (host, session, scope, _) = fixture(2, false);
    assert_eq!(
        host.memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false),
        Err(MaintenanceError::Internal)
    );
    assert!(!host.state.is_poisoned());
    let (host, session, scope, _) = fixture(4, false);
    assert_eq!(
        host.memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false),
        Err(MaintenanceError::Integrity)
    );
    assert!(!host.state.is_poisoned());
}
#[test]
fn poisoned_host_is_unavailable_not_a_new_ephemeral_owner() {
    let (host, session, scope, calls) = fixture(0, false);
    let state = host.state.clone();
    let _ = std::panic::catch_unwind(|| {
        let _held = state.lock().unwrap();
        panic!("synthetic poisoned owner");
    });
    assert_eq!(
        host.memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false),
        Err(MaintenanceError::Internal)
    );
    assert_eq!(calls.load(Ordering::Relaxed), 0);
    // Existing cleanup may recover poison for lease retirement only; gameplay
    // admission above must remain unavailable.
    drop(host);
}
#[test]
fn owner_atomic_cancellation_does_not_need_host_lock() {
    let (send, receive) = mpsc::sync_channel(1);
    let calls = Arc::new(AtomicUsize::new(0));
    let host = Arc::new(Host::with_persistence(
        false,
        Box::new(Port {
            engine: engine(),
            last: None,
            mode: 3,
            calls,
            entered: Some(send),
        }),
    ));
    let (session, scope) = create(&host);
    let cancelled = Arc::new(AtomicBool::new(false));
    let worker = {
        let host = host.clone();
        let cancelled = cancelled.clone();
        std::thread::spawn(move || {
            host.memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| {
                cancelled.load(Ordering::Acquire)
            })
        })
    };
    receive
        .recv_timeout(std::time::Duration::from_secs(2))
        .unwrap();
    cancelled.store(true, Ordering::Release);
    assert_eq!(worker.join().unwrap(), Err(MaintenanceError::Cancelled));
}
#[test]
fn lab_flag_does_not_change_player_or_grant_raw_data() {
    let (ordinary, session, scope, _) = fixture(0, false);
    let expected = ordinary
        .memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false)
        .unwrap();
    let (lab, session, scope, _) = fixture(0, true);
    assert_eq!(
        lab.memory_maintenance(&session, &scope, 0, MaintenanceAction::Status, &|| false)
            .unwrap(),
        expected
    );
    let bytes = serde_json::to_string(&expected).unwrap();
    for excluded in [
        "handle", "observer", "prompt", "packet", "location", "SECRET",
    ] {
        assert!(!bytes.contains(excluded));
    }
}

#[test]
fn passive_stale_view_preserves_historical_blocked_failure() {
    // Exactly the existing Store status shape after a Blocked job's source
    // advances. The sibling actual-Store regression establishes that shape.
    let (host, session, scope, _) = fixture(5, false);
    let reply = host
        .memory_maintenance(&session, &scope, 2, MaintenanceAction::Status, &|| false)
        .unwrap();
    let job = reply.job.unwrap();
    assert_eq!(job.status, MaintenanceStatus::Stale);
    assert_eq!(job.last_error, Some(MaintenanceFailure::Budget));
    assert_eq!(
        (job.basis_revision, job.next_from, job.generation),
        (1, 0, 1)
    );
}
