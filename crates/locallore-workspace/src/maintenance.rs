// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! One selected-player operation on the existing Store. Never an automatic loop.
use super::Repository;
use locallore::{
    engine::Engine,
    host::memory_maintenance::{
        MaintenanceAction, MaintenanceError, MaintenanceFailure, MaintenanceJobView,
        MaintenanceReply, MaintenanceStatus,
    },
};
use locallore_storage::{
    derived_memory::MemoryError,
    memory_jobs::{MemoryJobFailure, MemoryJobInfo, MemoryJobRequest, MemoryJobStatus},
};

fn error(value: MemoryError) -> MaintenanceError {
    match value {
        MemoryError::Scope => MaintenanceError::Scope,
        MemoryError::Stale => MaintenanceError::Stale,
        MemoryError::InvalidInput => MaintenanceError::Integrity,
        MemoryError::Unsupported => MaintenanceError::Unsupported,
        MemoryError::NotFound => MaintenanceError::NotFound,
        MemoryError::TooLarge => MaintenanceError::TooLarge,
        MemoryError::Cancelled => MaintenanceError::Cancelled,
        MemoryError::Integrity => MaintenanceError::Integrity,
        MemoryError::Database => MaintenanceError::Database,
        MemoryError::Busy => MaintenanceError::Busy,
        MemoryError::Full => MaintenanceError::Full,
    }
}
fn view(info: MemoryJobInfo) -> MaintenanceJobView {
    MaintenanceJobView {
        status: match info.status {
            MemoryJobStatus::Ready => MaintenanceStatus::Ready,
            MemoryJobStatus::Cancelled => MaintenanceStatus::Cancelled,
            MemoryJobStatus::Stale => MaintenanceStatus::Stale,
            MemoryJobStatus::Complete => MaintenanceStatus::Complete,
            MemoryJobStatus::Blocked => MaintenanceStatus::Blocked,
        },
        basis_revision: info.basis_revision,
        next_from: info.next_from,
        generation: info.generation,
        last_error: info.last_error.map(|failure| match failure {
            MemoryJobFailure::Budget => MaintenanceFailure::Budget,
            MemoryJobFailure::PacketLimit => MaintenanceFailure::PacketLimit,
            MemoryJobFailure::Integrity => MaintenanceFailure::Integrity,
        }),
    }
}
pub(super) fn run(
    repository: &mut Repository,
    selected: &Engine,
    expected_head: u64,
    action: MaintenanceAction,
    cancel: &dyn Fn() -> bool,
) -> Result<MaintenanceReply, MaintenanceError> {
    let request = MemoryJobRequest {
        scope: selected.scope().clone(),
        observer: selected.seed().player.clone(),
        expected_head,
    };
    let store = &mut repository.store;
    let info = if action == MaintenanceAction::Admit {
        Some(
            store
                .ensure_selected_memory_job(&request, selected, cancel)
                .map_err(error)?,
        )
    } else {
        let info = store
            .lookup_memory_job(&request, selected, cancel)
            .map_err(error)?;
        match (action, info) {
            (MaintenanceAction::Status, info) => info,
            (MaintenanceAction::Prune, None) => None,
            (_, None) => return Err(MaintenanceError::NotFound),
            (MaintenanceAction::Cancel, Some(info)) => Some(
                store
                    .cancel_memory_job(&info.handle, cancel)
                    .map_err(error)?,
            ),
            (MaintenanceAction::Prune, Some(info)) => {
                store
                    .prune_memory_job(&info.handle, cancel)
                    .map_err(error)?;
                None
            }
            (MaintenanceAction::Step, Some(info)) => match info.status {
                MemoryJobStatus::Ready => {
                    let step = store
                        .prepare_memory_job_step(&info.handle, cancel)
                        .map_err(error)?;
                    Some(store.publish_memory_job_step(step, cancel).map_err(error)?)
                }
                MemoryJobStatus::Cancelled => return Err(MaintenanceError::Cancelled),
                MemoryJobStatus::Stale => return Err(MaintenanceError::Stale),
                MemoryJobStatus::Complete | MemoryJobStatus::Blocked => Some(info),
            },
            (MaintenanceAction::Admit, _) => unreachable!("admission handled above"),
        }
    };
    Ok(MaintenanceReply {
        version: 1,
        scope: request.scope,
        head: expected_head,
        action,
        job: info.map(view),
    })
}
