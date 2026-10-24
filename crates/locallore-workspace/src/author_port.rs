// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Same-Repository native author capability. No registry or new Store incarnation.
use super::{turn, Repository};
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionPreviewV1},
    engine::AcceptedHistoryBasis,
    host::{NativeAuthorPreparation, WorkspaceAuthorOutcomeV1},
};
use locallore_storage::{AuthorCorrectionOutcome, PreparedStoreAuthorCorrection};
use std::any::Any;

struct StorePreparation(PreparedStoreAuthorCorrection);
impl NativeAuthorPreparation for StorePreparation {
    fn preview(&self) -> &AuthorCorrectionPreviewV1 {
        self.0.preview()
    }
    fn preview_bytes(&self) -> &[u8] {
        self.0.preview_bytes()
    }
    fn matches_parent_basis(&self, basis: &AcceptedHistoryBasis) -> bool {
        self.0.matches_parent_basis(basis)
    }
    fn as_any(&self) -> &dyn Any {
        self
    }
}
fn outcome(value: AuthorCorrectionOutcome) -> WorkspaceAuthorOutcomeV1 {
    WorkspaceAuthorOutcomeV1 {
        version: 1,
        scope: value.scope,
        parent: value.parent,
        fork_revision: value.fork_revision,
        author_revision: value.author_revision,
        head_revision: value.head_revision,
        created: value.created,
    }
}
pub(super) fn prepare(
    repository: &mut Repository,
    input: &AuthorCorrectionInputV1,
    cancel: &dyn Fn() -> bool,
) -> Result<Box<dyn NativeAuthorPreparation>, String> {
    let prepared = repository
        .store
        .prepare_author_correction(input, cancel)
        .map_err(turn)?;
    Ok(Box::new(StorePreparation(prepared)))
}
pub(super) fn apply(
    repository: &mut Repository,
    prepared: &dyn NativeAuthorPreparation,
    cancel: &dyn Fn() -> bool,
) -> Result<WorkspaceAuthorOutcomeV1, String> {
    let prepared = prepared
        .as_any()
        .downcast_ref::<StorePreparation>()
        .ok_or("Integrity")?;
    repository
        .store
        .apply_author_correction(&prepared.0, cancel)
        .map(outcome)
        .map_err(turn)
}
pub(super) fn lookup(
    repository: &mut Repository,
    input: &AuthorCorrectionInputV1,
    cancel: &dyn Fn() -> bool,
) -> Result<Option<WorkspaceAuthorOutcomeV1>, String> {
    repository
        .store
        .lookup_author_correction(input, cancel)
        .map(|value| value.map(outcome))
        .map_err(turn)
}
