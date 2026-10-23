// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Narrow Host trust/locking checks; durable behavior is tested in workspace/fork_host.
use super::*;
use std::sync::atomic::{AtomicBool, Ordering};

struct Port {
    committed: Arc<AtomicBool>,
}
impl Persistence for Port {
    fn location(&self) -> &str {
        "synthetic"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        unreachable!()
    }
    fn create(&mut self) -> Result<Engine, String> {
        unreachable!()
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        unreachable!("Host must not pre-read or check head")
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
    fn fork_branch(
        &mut self,
        r: &WorkspaceForkRequest,
        cancel: &dyn Fn() -> bool,
    ) -> Result<WorkspaceForkOutcome, String> {
        assert!(!cancel());
        self.committed.store(true, Ordering::SeqCst);
        Ok(WorkspaceForkOutcome {
            version: 1,
            scope: Scope {
                story: r.parent.story.clone(),
                branch: r.child_branch.clone(),
            },
            parent: r.parent.clone(),
            fork_revision: r.at_revision,
            head_revision: 7,
            created: false,
        })
    }
}
fn attached(host: &Host) -> (String, WorkspaceForkRequest) {
    let seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    let parent = seed.scope.clone();
    let reply = attach_engine(&mut host.state.lock().unwrap(), Engine::new(seed).unwrap());
    (
        reply["data"]["session"].as_str().unwrap().into(),
        WorkspaceForkRequest {
            parent,
            child_branch: "fixed".into(),
            expected_parent_revision: 999,
            at_revision: 0,
        },
    )
}
#[test]
fn committed_port_outcome_wins_over_late_cancellation_without_host_head_read() {
    let committed = Arc::new(AtomicBool::new(false));
    let host = Host::with_persistence(
        false,
        Box::new(Port {
            committed: committed.clone(),
        }),
    );
    let (session, r) = attached(&host);
    let outcome = host
        .fork_branch(&session, &r, &|| committed.load(Ordering::SeqCst))
        .unwrap();
    assert!(committed.load(Ordering::SeqCst));
    assert_eq!(outcome.head_revision, 7);
    assert!(!outcome.created);
    assert_eq!(
        host.state.lock().unwrap().sessions[&session]
            .engine
            .revision(),
        0
    );
}
#[test]
fn poisoned_host_fails_closed_without_fork_dispatch() {
    let committed = Arc::new(AtomicBool::new(false));
    let host = Host::with_persistence(
        false,
        Box::new(Port {
            committed: committed.clone(),
        }),
    );
    let (session, r) = attached(&host);
    let state = host.state.clone();
    assert!(std::thread::spawn(move || {
        let _held = state.lock().unwrap();
        panic!("synthetic poison");
    })
    .join()
    .is_err());
    assert_eq!(
        host.fork_branch(&session, &r, &|| false).unwrap_err(),
        "Internal"
    );
    assert!(!committed.load(Ordering::SeqCst));
}
