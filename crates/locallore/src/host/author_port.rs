// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Native-only author capabilities. No serialized operation or renderer grant.
use super::*;
use crate::author_correction::{AuthorCorrectionInputV1, AuthorCorrectionPreviewV1};
use std::{any::Any, cell::Cell, sync::Weak};

pub trait NativeAuthorPreparation: Any + Send {
    fn preview(&self) -> &AuthorCorrectionPreviewV1;
    fn preview_bytes(&self) -> &[u8];
    fn matches_parent_basis(&self, basis: &AcceptedHistoryBasis) -> bool;
    fn as_any(&self) -> &dyn Any;
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct WorkspaceAuthorOutcomeV1 {
    pub version: u16,
    pub scope: Scope,
    pub parent: Scope,
    pub fork_revision: u64,
    pub author_revision: u64,
    pub head_revision: u64,
    pub created: bool,
}

/// Native owner capability. Neither serializable nor cloneable; preview is private.
pub struct HostAuthorPreparation {
    owner: Weak<Mutex<State>>,
    session: String,
    work_owner: Arc<()>,
    input: AuthorCorrectionInputV1,
    basis: AcceptedHistoryBasis,
    plan: Box<dyn NativeAuthorPreparation>,
    preview: AuthorCorrectionPreviewV1,
    preview_bytes: Vec<u8>,
}
impl HostAuthorPreparation {
    pub fn preview(&self) -> &AuthorCorrectionPreviewV1 {
        &self.preview
    }
    pub fn preview_bytes(&self) -> &[u8] {
        &self.preview_bytes
    }
}
fn check(cancel: &dyn Fn() -> bool) -> Result<(), String> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err("Cancelled".into())
    } else {
        Ok(())
    }
}
fn child(input: &AuthorCorrectionInputV1) -> Scope {
    Scope {
        story: input.parent.story.clone(),
        branch: input.child_branch.clone(),
    }
}
fn port_panic<T>(operation: impl FnOnce() -> Result<T, String>) -> Result<T, String> {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(operation))
        .map_err(|_| "Internal".to_owned())?
}
fn reply_error(reply: Value) -> String {
    reply["error"].as_str().unwrap_or("Internal").to_owned()
}
fn no_pending(state: &State, scope: &Scope) -> Result<(), String> {
    if state.sessions.values().any(|session| {
        session.engine.scope() == scope && session.turns.values().any(|turn| turn.phase.active())
    }) {
        Err("Busy".into())
    } else {
        Ok(())
    }
}
fn valid_outcome(outcome: &WorkspaceAuthorOutcomeV1, input: &AuthorCorrectionInputV1) -> bool {
    outcome.version == 1
        && outcome.scope == child(input)
        && outcome.parent == input.parent
        && outcome.fork_revision == input.fork_revision
        && input.fork_revision.checked_add(1) == Some(outcome.author_revision)
        && outcome.head_revision >= outcome.author_revision
        && outcome.head_revision <= i64::MAX as u64
}
fn validate_outcome(
    outcome: WorkspaceAuthorOutcomeV1,
    input: &AuthorCorrectionInputV1,
) -> Result<WorkspaceAuthorOutcomeV1, String> {
    if valid_outcome(&outcome, input) {
        Ok(outcome)
    } else {
        Err("Integrity".into())
    }
}
impl Host {
    /// Native capability metadata only; a renderer value cannot change this grant.
    pub fn story_lab_granted(&self) -> bool {
        self.story_lab
    }
    /// IO-owner only. Callbacks must be bounded and may not reenter Host/Store.
    pub fn prepare_author_correction(
        &self,
        session: &str,
        input: &AuthorCorrectionInputV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostAuthorPreparation, String> {
        if !self.story_lab {
            return Err("Forbidden".into());
        }
        let observed = Cell::new(false);
        let safe_cancel = || {
            if !observed.get() {
                observed.set(check(cancel).is_err());
            }
            observed.get()
        };
        check(&safe_cancel)?;
        input.validate().map_err(|error| error.to_string())?;
        let mut state = self.state.lock().map_err(|_| "Internal".to_owned())?;
        // Catch inside the lock, including faulty native overrides, to preserve owner usability.
        port_panic(|| {
            get_session(&mut state, session, &input.parent).map_err(reply_error)?;
            if state.persistence.is_none() {
                return Err("Unsupported".into());
            }
            no_pending(&state, &input.parent)?;
            refresh_session(&mut state, session, &input.parent).map_err(reply_error)?;
            let selected = state.sessions.get(session).ok_or("Closed")?;
            if selected.engine.revision() != input.expected_parent_revision {
                return Err("Stale".into());
            }
            let basis = selected
                .engine
                .accepted_history_basis()
                .map_err(|error| error.to_string())?;
            let work_owner = selected.work_owner.clone();
            check(&safe_cancel)?;
            let plan = state
                .persistence
                .as_mut()
                .ok_or("Unsupported")?
                .prepare_author_correction(input, &safe_cancel)?;
            if !plan.matches_parent_basis(&basis) {
                return Err("Stale".into());
            }
            let preview = plan.preview().clone();
            let preview_bytes = plan.preview_bytes().to_vec();
            if preview.version != 1
                || preview.input != *input
                || preview.child != child(input)
                || input.fork_revision.checked_add(1) != Some(preview.creation_revision)
                || preview_bytes.len() > MAX_RECEIPT_BYTES
                || serde_json::to_vec(&preview).map_err(|_| "Integrity".to_owned())?
                    != preview_bytes
            {
                return Err("Integrity".into());
            }
            check(&safe_cancel)?;
            Ok(HostAuthorPreparation {
                owner: Arc::downgrade(&self.state),
                session: session.into(),
                work_owner,
                input: input.clone(),
                basis,
                plan,
                preview,
                preview_bytes,
            })
        })
    }

    pub fn apply_author_correction(
        &self,
        prepared: &HostAuthorPreparation,
        cancel: &dyn Fn() -> bool,
    ) -> Result<WorkspaceAuthorOutcomeV1, String> {
        if !self.story_lab {
            return Err("Forbidden".into());
        }
        if !Weak::ptr_eq(&prepared.owner, &Arc::downgrade(&self.state)) {
            return Err("Integrity".into());
        }
        let mut state = self.state.lock().map_err(|_| "Internal".to_owned())?;
        port_panic(|| {
            // Identity only: do not require a surviving live parent before exact replay.
            let selected = state.sessions.get(&prepared.session).ok_or("Closed")?;
            if !Arc::ptr_eq(&prepared.work_owner, &selected.work_owner) {
                return Err("Stale".into());
            }
            if selected.engine.scope() != &prepared.input.parent {
                return Err("Scope".into());
            }
            let port = state.persistence.as_mut().ok_or("Unsupported")?;
            // Bounded existing-result inspection cannot write. Recorded success wins late cancellation.
            if let Some(outcome) = port.lookup_author_correction(&prepared.input, &|| false)? {
                if outcome.created {
                    return Err("Integrity".into());
                }
                return validate_outcome(outcome, &prepared.input);
            }
            let observed = Cell::new(false);
            let safe_cancel = || {
                if !observed.get() {
                    observed.set(check(cancel).is_err());
                }
                observed.get()
            };
            check(&safe_cancel)?;
            no_pending(&state, &prepared.input.parent)?;
            refresh_session(&mut state, &prepared.session, &prepared.input.parent)
                .map_err(reply_error)?;
            let selected = state.sessions.get(&prepared.session).ok_or("Closed")?;
            if !Arc::ptr_eq(&prepared.work_owner, &selected.work_owner)
                || selected.engine.revision() != prepared.input.expected_parent_revision
                || selected
                    .engine
                    .accepted_history_basis()
                    .map_err(|error| error.to_string())?
                    != prepared.basis
            {
                return Err("Stale".into());
            }
            check(&safe_cancel)?;
            let outcome = state
                .persistence
                .as_mut()
                .ok_or("Unsupported")?
                .apply_author_correction(prepared.plan.as_ref(), &safe_cancel)?;
            // Do not post-check cancellation: the Store return is already committed.
            validate_outcome(outcome, &prepared.input)
        })
    }

    /// Explicit privileged readonly recovery; no parent/session admission or new write.
    pub fn lookup_author_correction(
        &self,
        input: &AuthorCorrectionInputV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Option<WorkspaceAuthorOutcomeV1>, String> {
        if !self.story_lab {
            return Err("Forbidden".into());
        }
        let observed = Cell::new(false);
        let safe_cancel = || {
            if !observed.get() {
                observed.set(check(cancel).is_err());
            }
            observed.get()
        };
        check(&safe_cancel)?;
        input.validate().map_err(|error| error.to_string())?;
        let mut state = self.state.lock().map_err(|_| "Internal".to_owned())?;
        port_panic(|| {
            let outcome = state
                .persistence
                .as_mut()
                .ok_or("Unsupported")?
                .lookup_author_correction(input, &safe_cancel)?;
            check(&safe_cancel)?;
            outcome
                .map(|outcome| {
                    if outcome.created {
                        return Err("Integrity".into());
                    }
                    validate_outcome(outcome, input)
                })
                .transpose()
        })
    }
}
