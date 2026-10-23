// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! One native app adapter; no SQL/model/foreign history execution capability.
use locallore::{
    contracts::*,
    engine::Engine,
    host::{
        Host, HostGenerationSnapshot, Persistence, SavedTurn, WorkspaceBranch,
        WorkspaceBranchCatalog, WorkspaceForkOutcome, WorkspaceForkRequest, WorkspaceSummary,
    },
};
use locallore_storage::{StorageError, Store, TurnError, TurnPhase, TurnRecord};
use std::path::Path;
mod maintenance;
pub const DATABASE_SCHEMA_VERSION: u32 = locallore_storage::SCHEMA_VERSION;

struct Repository {
    store: Store,
    location: String,
}
fn storage(error: StorageError) -> String {
    error.to_string()
}
fn turn(error: TurnError) -> String {
    match error {
        TurnError::Storage(e) => storage(e),
        TurnError::Engine(e) => e.to_string(),
        TurnError::Integrity => "Integrity".into(),
        TurnError::TooLarge => "TooLarge".into(),
        TurnError::UnknownTurn => "UnknownTurn".into(),
        TurnError::RetryMismatch => "RetryMismatch".into(),
        TurnError::Stale => "Stale".into(),
        TurnError::Terminal => "Cancelled".into(),
        TurnError::Full => "Full".into(),
    }
}
fn generation_memory(error: locallore_storage::derived_memory::MemoryError) -> String {
    use locallore_storage::derived_memory::MemoryError::*;
    match error {
        Scope => "Scope",
        Stale | NotFound => "Stale",
        InvalidInput => "InvalidInput",
        Unsupported => "Unsupported",
        TooLarge => "TooLarge",
        Cancelled => "Cancelled",
        Integrity => "Integrity",
        Database => "Database",
        Busy => "Busy",
        Full => "Full",
    }
    .into()
}
fn saved(record: TurnRecord) -> SavedTurn {
    SavedTurn {
        request: record.request,
        receipt: record.receipt,
        phase: match record.phase {
            TurnPhase::Draft => "draft",
            TurnPhase::Committed => "committed",
            TurnPhase::Cancelled => "cancelled",
            TurnPhase::Failed => "failed",
            TurnPhase::Stale => "stale",
        }
        .into(),
    }
}
/// Native code chooses an application-private path and calls on its IO worker. Failure is
/// explicit; it never silently substitutes an ephemeral Host or overwrites a foreign database.
pub fn open(path: &Path, story_lab: bool) -> Result<Host, String> {
    let store = Store::open_application(path).map_err(storage)?;
    let location = std::fs::canonicalize(path)
        .map_err(|_| "Io".to_owned())?
        .to_str()
        .ok_or("InvalidInput")?
        .to_owned();
    Ok(Host::with_persistence(
        story_lab,
        Box::new(Repository { store, location }),
    ))
}
/// Trusted native-only explicit private SQLite-tool copy, including every saved story/draft.
/// Caller owns source/destination authority and staging/finalization; no renderer paths accepted.
/// Uses SQLite backup, never a live .db file copy. Returned heads are read from the actual copy.
pub fn inspection_database_copy(
    source: &Path,
    destination: &Path,
) -> Result<Vec<WorkspaceSummary>, String> {
    let source = Store::open_read_only(source).map_err(storage)?;
    source.backup_inspection_to(destination).map_err(storage)?;
    let mut copy = Store::open_read_only(destination).map_err(storage)?;
    Ok(copy
        .stories()
        .map_err(storage)?
        .into_iter()
        .map(|s| WorkspaceSummary {
            scope: s.scope,
            title: s.title,
            revision: s.revision,
            drafts: s.drafts,
        })
        .collect())
}
impl Persistence for Repository {
    fn status_bound(
        &mut self,
        request: &Request,
        basis: &locallore::engine::AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        self.store
            .turn_status_bound(request, basis)
            .map(saved)
            .map_err(turn)
    }
    fn commit_prepared_bound(
        &mut self,
        receipt: &Receipt,
        basis: &locallore::engine::AcceptedHistoryBasis,
    ) -> Result<Receipt, String> {
        self.store
            .commit_prepared_bound(receipt, basis)
            .map_err(turn)
    }
    fn finish_bound(
        &mut self,
        request: &Request,
        basis: &locallore::engine::AcceptedHistoryBasis,
        phase: locallore::host::DraftDisposition,
    ) -> Result<SavedTurn, String> {
        let phase = match phase {
            locallore::host::DraftDisposition::Cancelled => TurnPhase::Cancelled,
            locallore::host::DraftDisposition::Failed => TurnPhase::Failed,
            locallore::host::DraftDisposition::Stale => TurnPhase::Stale,
        };
        self.store
            .finish_bound(request, basis, phase)
            .map(saved)
            .map_err(turn)
    }
    fn memory_maintenance(
        &mut self,
        selected: &Engine,
        expected_head: u64,
        action: locallore::host::memory_maintenance::MaintenanceAction,
        cancel: &dyn Fn() -> bool,
    ) -> Result<
        locallore::host::memory_maintenance::MaintenanceReply,
        locallore::host::memory_maintenance::MaintenanceError,
    > {
        maintenance::run(self, selected, expected_head, action, cancel)
    }
    fn validate_scope(&mut self, scope: &Scope) -> Result<(), String> {
        if self.store.is_branch_active(scope).map_err(storage)? {
            Ok(())
        } else {
            Err("NotFound".into())
        }
    }
    fn database_schema_version(&self) -> u32 {
        DATABASE_SCHEMA_VERSION
    }
    fn commit_prepared(&mut self, receipt: &Receipt) -> Result<Receipt, String> {
        self.store.commit_prepared(receipt).map_err(turn)
    }
    fn location(&self) -> &str {
        &self.location
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Ok(self
            .store
            .stories()
            .map_err(storage)?
            .into_iter()
            .map(|s| WorkspaceSummary {
                scope: s.scope,
                title: s.title,
                revision: s.revision,
                drafts: s.drafts,
            })
            .collect())
    }
    fn branches(&mut self, story: &str) -> Result<WorkspaceBranchCatalog, String> {
        let catalog = self.store.branch_catalog(story, &|| false).map_err(turn)?;
        Ok(WorkspaceBranchCatalog {
            version: catalog.version,
            story_id: catalog.story_id,
            title: catalog.title,
            root_branch: catalog.root_branch,
            branches: catalog
                .branches
                .into_iter()
                .map(|branch| WorkspaceBranch {
                    scope: branch.scope,
                    parent_branch: branch.parent_branch,
                    fork_revision: branch.fork_revision,
                    revision: branch.revision,
                    drafts: branch.drafts,
                    retired: branch.retired,
                })
                .collect(),
        })
    }
    fn fork_branch(
        &mut self,
        request: &WorkspaceForkRequest,
        cancel: &dyn Fn() -> bool,
    ) -> Result<WorkspaceForkOutcome, String> {
        let outcome = self
            .store
            .fork_branch(
                &locallore_storage::ForkRequest {
                    parent: request.parent.clone(),
                    child_branch: request.child_branch.clone(),
                    expected_parent_revision: request.expected_parent_revision,
                    at_revision: request.at_revision,
                },
                cancel,
            )
            .map_err(turn)?;
        Ok(WorkspaceForkOutcome {
            version: 1,
            scope: outcome.scope,
            parent: outcome.parent,
            fork_revision: outcome.fork_revision,
            head_revision: outcome.head_revision,
            created: outcome.created,
        })
    }
    fn create(&mut self) -> Result<Engine, String> {
        let seed: Seed = serde_seed();
        let scope = self
            .store
            .create_workspace("Lantern Quay", seed)
            .map_err(storage)?;
        self.resume(&scope)
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        Ok(self.store.resume(scope).map_err(turn)?.engine)
    }
    fn generation_snapshot(
        &mut self,
        scope: &Scope,
        expected_head: u64,
        observer: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        let snapshot = self
            .store
            .context_snapshot(
                &locallore_storage::memory_jobs::MemoryJobRequest {
                    scope: scope.clone(),
                    expected_head,
                    observer: observer.into(),
                },
                cancel,
            )
            .map_err(generation_memory)?;
        if snapshot.engine.seed().player != observer {
            return Err("Stale".into());
        }
        Ok(HostGenerationSnapshot {
            engine: snapshot.engine,
            coverage: snapshot.coverage,
        })
    }
    fn begin(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.begin_turn(request).map(saved).map_err(turn)
    }
    fn commit(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
    ) -> Result<Receipt, String> {
        self.store
            .commit_turn(request, proposal, narration)
            .map_err(turn)
    }
    fn cancel(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.cancel_turn(request).map(saved).map_err(turn)
    }
    fn fail(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.fail_turn(request).map(saved).map_err(turn)
    }
    fn stale(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.stale_turn(request).map(saved).map_err(turn)
    }
    fn status(&mut self, scope: &Scope, id: &str) -> Result<SavedTurn, String> {
        self.store.lookup_turn(scope, id).map(saved).map_err(turn)
    }
}
fn serde_seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .expect("bundled validated fixture")
}
