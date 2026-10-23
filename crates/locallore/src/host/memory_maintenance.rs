// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit native-only maintenance. No serialized job capability or scheduler.
use super::{Host, Scope};
use serde::Serialize;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MaintenanceAction {
    Status,
    Admit,
    Step,
    Cancel,
    Prune,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MaintenanceStatus {
    Ready,
    Cancelled,
    Stale,
    Complete,
    Blocked,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MaintenanceFailure {
    Budget,
    PacketLimit,
    Integrity,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MaintenanceJobView {
    pub status: MaintenanceStatus,
    pub basis_revision: u64,
    pub next_from: u64,
    pub generation: u64,
    pub last_error: Option<MaintenanceFailure>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MaintenanceReply {
    pub version: u16,
    pub scope: Scope,
    pub head: u64,
    pub action: MaintenanceAction,
    pub job: Option<MaintenanceJobView>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MaintenanceError {
    Closed,
    Scope,
    Stale,
    Busy,
    Unsupported,
    Cancelled,
    NotFound,
    TooLarge,
    Integrity,
    Database,
    Full,
    Internal,
}
impl MaintenanceError {
    fn from_port(value: &str) -> Self {
        match value {
            "Closed" => Self::Closed,
            "Scope" => Self::Scope,
            "Stale" => Self::Stale,
            "Busy" => Self::Busy,
            "Unsupported" => Self::Unsupported,
            "Cancelled" => Self::Cancelled,
            "NotFound" => Self::NotFound,
            "TooLarge" => Self::TooLarge,
            "Integrity" => Self::Integrity,
            "Database" => Self::Database,
            "Full" => Self::Full,
            _ => Self::Internal,
        }
    }
}
fn check_cancel(cancel: &dyn Fn() -> bool) -> Result<(), MaintenanceError> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(MaintenanceError::Cancelled)
    } else {
        Ok(())
    }
}
fn valid_reply(
    reply: &MaintenanceReply,
    scope: &Scope,
    head: u64,
    action: MaintenanceAction,
) -> bool {
    reply.version == 1
        && &reply.scope == scope
        && reply.head == head
        && reply.action == action
        && reply.job.as_ref().is_none_or(|job| {
            job.generation > 0
                && [job.basis_revision, job.next_from, job.generation]
                    .iter()
                    .all(|value| *value <= i64::MAX as u64)
                && job.next_from <= job.basis_revision
                && (job.status != MaintenanceStatus::Complete
                    || job.next_from == job.basis_revision)
                && (job.status != MaintenanceStatus::Ready || job.next_from < job.basis_revision)
                && ((job.status == MaintenanceStatus::Blocked) == job.last_error.is_some())
        })
        && serde_json::to_vec(reply).is_ok_and(|bytes| bytes.len() <= 4096)
}
impl Host {
    /// Synchronous native IO operation. The owner changes its AtomicBool outside
    /// this lock; callbacks must be short and must not reenter Host/Store.
    /// A successful mutating return is committed, even if cancellation comes later.
    pub fn memory_maintenance(
        &self,
        session: &str,
        scope: &Scope,
        expected_head: u64,
        action: MaintenanceAction,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MaintenanceReply, MaintenanceError> {
        let observed = std::cell::Cell::new(false);
        let safe_cancel = || {
            if !observed.get() {
                observed.set(check_cancel(cancel).is_err());
            }
            observed.get()
        };
        check_cancel(&safe_cancel)?;
        let mut state = self.state.lock().map_err(|_| MaintenanceError::Internal)?;
        let selected = state
            .sessions
            .get(session)
            .ok_or(MaintenanceError::Closed)?;
        if selected.engine.scope() != scope {
            return Err(MaintenanceError::Scope);
        }
        let selected = selected.engine.clone();
        if action != MaintenanceAction::Status
            && state.sessions.values().any(|session| {
                session.engine.scope() == scope
                    && session.turns.values().any(|turn| turn.phase.active())
            })
        {
            return Err(MaintenanceError::Busy);
        }
        let port = state
            .persistence
            .as_mut()
            .ok_or(MaintenanceError::Unsupported)?;
        // Catch inside the lock: a faulty override cannot poison gameplay state.
        let reply = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            port.validate_scope(scope)
                .map_err(|error| MaintenanceError::from_port(&error))?;
            check_cancel(&safe_cancel)?;
            port.memory_maintenance(&selected, expected_head, action, &safe_cancel)
        }))
        .map_err(|_| MaintenanceError::Internal)??;
        if observed.get() {
            return Err(MaintenanceError::Cancelled);
        }
        if !valid_reply(&reply, scope, expected_head, action) {
            return Err(MaintenanceError::Integrity);
        }
        if action == MaintenanceAction::Status {
            check_cancel(&safe_cancel)?;
        }
        Ok(reply)
    }
}

#[cfg(test)]
#[path = "memory_maintenance_tests.rs"]
mod tests;
