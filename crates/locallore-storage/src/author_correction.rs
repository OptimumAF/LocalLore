// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Store-owned atomic author correction. All canonical validation stays in Core.
use crate::{branches, turns, Store, TurnError};
use locallore::{
    author_correction::{
        AuthorCorrectionInputV1, AuthorCorrectionPreviewV1, CanonicalRecord,
        PreparedAuthorCorrection, AUTHOR_TURN_KEY,
    },
    contracts::{Error, Scope, MAX_RECEIPT_BYTES},
    engine::AcceptedHistoryBasis,
};
use rusqlite::{params, Connection, TransactionBehavior};
use sha2::{Digest, Sha256};
use std::sync::Arc;
type Result<T> = std::result::Result<T, TurnError>;
#[cfg(test)]
mod pressure_tests;

#[derive(Clone, Debug)]
pub struct PreparedStoreAuthorCorrection {
    owner: Arc<()>,
    parent: AcceptedHistoryBasis,
    core: PreparedAuthorCorrection,
    preview_bytes: Vec<u8>,
}
impl PreparedStoreAuthorCorrection {
    pub fn preview(&self) -> &AuthorCorrectionPreviewV1 {
        self.core.preview()
    }
    pub fn preview_bytes(&self) -> &[u8] {
        &self.preview_bytes
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AuthorCorrectionOutcome {
    pub scope: Scope,
    pub parent: Scope,
    pub fork_revision: u64,
    pub author_revision: u64,
    pub head_revision: u64,
    pub created: bool,
}
fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(TurnError::Engine(Error::Cancelled))
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
pub(crate) fn request_index(record: &CanonicalRecord) -> Result<serde_json::Value> {
    let CanonicalRecord::AuthorV1(author) = record else {
        return Err(TurnError::Integrity);
    };
    let bytes = serde_json::to_vec(record).map_err(|_| TurnError::Integrity)?;
    Ok(
        serde_json::json!({"version":1,"kind":"author_correction","scope":author.scope(),
        "turn":AUTHOR_TURN_KEY,"expected_revision":author.input().fork_revision,
        "record_sha256":format!("{:x}",Sha256::digest(bytes))}),
    )
}
/// Normalize one actual native author record inside the caller's transaction.
/// Shared by author application and accepted-history import; no witness grant.
pub(crate) fn insert_author_record(
    connection: &Connection,
    record: &CanonicalRecord,
) -> Result<()> {
    let CanonicalRecord::AuthorV1(author) = record else {
        return Err(TurnError::Integrity);
    };
    let scope = author.scope();
    let response = serde_json::to_string(record).map_err(|_| TurnError::Integrity)?;
    let index = serde_json::to_string(&request_index(record)?).map_err(|_| TurnError::Integrity)?;
    if response.len() > MAX_RECEIPT_BYTES {
        return Err(TurnError::TooLarge);
    }
    let fork = i64::try_from(author.input().fork_revision).map_err(|_| TurnError::TooLarge)?;
    let sequence = i64::try_from(author.sequence()).map_err(|_| TurnError::TooLarge)?;
    connection.execute("INSERT INTO turns(story_id,branch_id,turn_id,expected_revision,status,request_json,response_json,canonical_kind) VALUES(?1,?2,?3,?4,'committed',?5,?6,'author_v1')",
        params![scope.story,scope.branch,AUTHOR_TURN_KEY,fork,index,response])?;
    connection.execute("INSERT INTO accepted_events(story_id,branch_id,sequence,turn_id,event_version,envelope_json,record_kind) VALUES(?1,?2,?3,?4,1,?5,'author_correction')",
        params![scope.story,scope.branch,sequence,AUTHOR_TURN_KEY,serde_json::to_string(author).map_err(|_|TurnError::Integrity)?])?;
    Ok(())
}
fn lookup(
    connection: &Connection,
    input: &AuthorCorrectionInputV1,
    cancel: &dyn Fn() -> bool,
) -> Result<Option<AuthorCorrectionOutcome>> {
    check(cancel)?;
    input.validate().map_err(TurnError::Engine)?;
    let scope = child(input);
    crate::retention_state::admit(connection, &scope)?;
    let exists: bool = connection.query_row(
        "SELECT EXISTS(SELECT 1 FROM branches WHERE story_id=?1 AND branch_id=?2)",
        params![scope.story, scope.branch],
        |r| r.get(0),
    )?;
    if !exists {
        return Ok(None);
    }
    // Replays the child's actual retained ancestry, not the parent's current H.
    let engine = turns::read_engine(connection, &scope)?.engine;
    let author = engine
        .canonical_records()
        .iter()
        .find_map(|record| match record {
            CanonicalRecord::AuthorV1(author) if author.scope() == &scope => Some(author),
            _ => None,
        })
        .ok_or(TurnError::RetryMismatch)?;
    if author.input() != input {
        return Err(TurnError::RetryMismatch);
    }
    check(cancel)?;
    Ok(Some(AuthorCorrectionOutcome {
        scope,
        parent: input.parent.clone(),
        fork_revision: input.fork_revision,
        author_revision: author.sequence(),
        head_revision: engine.revision(),
        created: false,
    }))
}
fn map_core(error: Error) -> TurnError {
    if error == Error::Stale {
        TurnError::Stale
    } else {
        TurnError::Engine(error)
    }
}
impl Store {
    pub fn lookup_author_correction(
        &mut self,
        input: &AuthorCorrectionInputV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Option<AuthorCorrectionOutcome>> {
        let tx = self.connection.transaction()?;
        let outcome = lookup(&tx, input, cancel)?;
        tx.commit()?;
        Ok(outcome)
    }
    pub fn prepare_author_correction(
        &mut self,
        input: &AuthorCorrectionInputV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<PreparedStoreAuthorCorrection> {
        check(cancel)?;
        input.validate().map_err(TurnError::Engine)?;
        let tx = self.connection.transaction()?;
        crate::retention_state::admit(&tx, &child(input))?;
        if lookup(&tx, input, cancel)?.is_some() {
            return Err(TurnError::RetryMismatch);
        }
        branches::check_child_capacity(&tx, &input.parent)?;
        let parent = turns::read_engine(&tx, &input.parent)?.engine;
        let basis = parent.accepted_history_basis().map_err(TurnError::Engine)?;
        let core = parent
            .prepare_author_correction(input, cancel)
            .map_err(map_core)?;
        let preview_bytes = serde_json::to_vec(core.preview()).map_err(|_| TurnError::Integrity)?;
        if preview_bytes.len() > MAX_RECEIPT_BYTES {
            return Err(TurnError::TooLarge);
        }
        check(cancel)?;
        tx.commit()?;
        Ok(PreparedStoreAuthorCorrection {
            owner: self.memory_job_owner.clone(),
            parent: basis,
            core,
            preview_bytes,
        })
    }
    pub fn apply_author_correction(
        &mut self,
        prepared: &PreparedStoreAuthorCorrection,
        cancel: &dyn Fn() -> bool,
    ) -> Result<AuthorCorrectionOutcome> {
        check(cancel)?;
        if !Arc::ptr_eq(&self.memory_job_owner, &prepared.owner) {
            return Err(TurnError::Integrity);
        }
        let input = prepared.core.input();
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        if let Some(outcome) = lookup(&tx, input, cancel)? {
            tx.commit()?;
            return Ok(outcome);
        }
        let parent = turns::read_engine(&tx, &input.parent)?.engine;
        if parent.accepted_history_basis().map_err(TurnError::Engine)? != prepared.parent {
            return Err(TurnError::Stale);
        }
        let actual = parent
            .prepare_author_correction(input, cancel)
            .map_err(map_core)?;
        if serde_json::to_vec(actual.preview()).map_err(|_| TurnError::Integrity)?
            != prepared.preview_bytes
        {
            return Err(TurnError::Stale);
        }
        let applied = parent
            .apply_author_correction(&prepared.core, cancel)
            .map_err(map_core)?;
        let scope = applied.engine.scope().clone();
        branches::insert_child(
            &tx,
            &input.parent,
            &applied.engine,
            input.fork_revision,
            cancel,
        )?;
        let record = applied
            .engine
            .canonical_records()
            .last()
            .ok_or(TurnError::Integrity)?;
        insert_author_record(&tx, record)?;
        // Revalidate actual transaction bytes and accounting before publication.
        let verified = turns::read_engine(&tx, &scope)?.engine;
        if verified
            .accepted_history_basis()
            .map_err(TurnError::Engine)?
            != applied
                .engine
                .accepted_history_basis()
                .map_err(TurnError::Engine)?
        {
            return Err(TurnError::Integrity);
        }
        check(cancel)?;
        tx.commit()?;
        Ok(AuthorCorrectionOutcome {
            scope,
            parent: input.parent.clone(),
            fork_revision: input.fork_revision,
            author_revision: applied.receipt.sequence(),
            head_revision: verified.revision(),
            created: true,
        })
    }
}
