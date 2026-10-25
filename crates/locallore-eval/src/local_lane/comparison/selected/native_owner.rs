// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Retained native cleanup ownership, independent of execution/accounting policy.
use crate::local_lane::NativeAssets;
use locallore_local_runtime::LocalRuntime;
use std::{
    fmt,
    panic::{catch_unwind, AssertUnwindSafe},
    sync::{Arc, Mutex, TryLockError},
};

pub(super) type SharedRuntime = Arc<Mutex<LocalRuntime>>;

pub trait SelectedNativeReservation {
    fn assets(&self) -> NativeAssets<'_>;
    fn retain_uncertain(
        &mut self,
        owner: SharedRuntime,
    ) -> std::result::Result<(), SharedRuntime>;
}

/// Fixed diagnostics plus, only after a rejected transfer, the actual owner pair.
/// Neither the reservation nor runtime is inspected by Debug or made wire data.
pub struct SelectedNativeFailure<R> {
    code: &'static str,
    cause: Option<&'static str>,
    cleanup_uncertain: bool,
    retained: Option<Box<(R, SharedRuntime)>>,
}

impl<R> SelectedNativeFailure<R> {
    pub fn code(&self) -> &str {
        self.code
    }
    pub fn cause(&self) -> Option<&str> {
        self.cause
    }
    pub fn cleanup_uncertain(&self) -> bool {
        self.cleanup_uncertain
    }
    pub fn into_retained(mut self) -> std::result::Result<(R, SharedRuntime), Self> {
        match self.retained.take() {
            Some(owner) => Ok(*owner),
            None => Err(self),
        }
    }
    pub(super) fn from_error(error: String) -> Self {
        let code = closed_code(&error);
        Self {
            code,
            cause: Some(code),
            cleanup_uncertain: false,
            retained: None,
        }
    }
}

impl<R> fmt::Debug for SelectedNativeFailure<R> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SelectedNativeFailure")
            .field("code", &self.code)
            .field("cause", &self.cause)
            .field("cleanup_uncertain", &self.cleanup_uncertain)
            .field("retains_owner", &self.retained.is_some())
            .finish_non_exhaustive()
    }
}

// Exact fixed source/driver/runtime categories only. Never retain an arbitrary
// callback string or accept a private suffix merely because its prefix is known.
fn closed_code(error: &str) -> &'static str {
    const CODES: &[&str] = &[
        "Agency", "AliasedDestination", "AttemptLimit", "Binding", "BindingBudget",
        "BootstrapIncomplete", "CaptureBinding", "CaptureConsent", "CaptureForwardedBudget",
        "CaptureMalformed", "CaptureRepairMismatch", "CaseBudget", "CheckpointBudget",
        "CheckpointEvidenceMismatch", "CheckpointIntegrity", "CheckpointMalformed",
        "CheckpointMismatch", "CheckpointOrder", "CheckpointOutcomeMismatch", "Cleanup",
        "ClockIntegrity", "ComparisonBinding", "ComparisonDirectory", "Create", "DependencyOracle", "Encoding", "EvidenceBudget", "Forbidden", "Fork",
        "Interrupted", "InvalidSeed", "InvalidStep", "InvalidSuite", "Io", "LedgerIntegrity",
        "Lookup", "Malformed", "NativeFeatureUnavailable", "OutputExists", "PreparationDeadline",
        "OutputBudget", "Profile", "Provider", "RawBudget", "RawIntegrity", "ReceiptBinding", "ReceiptReplay", "Reparse",
        "Recording", "RecordingIntegrity", "RecordingLost", "ReferenceBinding", "ReferenceChanged",
        "ReferenceFailed", "ReferenceInputMismatch", "ReferenceIntegrity", "ReferenceNotApplicable",
        "ReferenceOracle", "ReferenceOrder", "ReferencePrefix", "ReferenceReplay", "ReferenceRequired",
        "ReferenceSourceMismatch", "Replay", "ReportBudget", "Resume", "RoleBudget", "RoleOrder",
        "RolloutContinuity", "RolloutSource", "RunBudget", "RunBusy", "RuntimeInvalidRequest",
        "RuntimeModelInvalid", "RuntimeWorkerUnavailable", "RuntimeProtocol", "RuntimeBusy",
        "RuntimeCancelled", "RuntimeTimeout", "RuntimeCleanup", "RuntimeRuntime", "SceneBudget",
        "SceneIntegrity", "SceneOrder", "Scope", "Seed", "SelectedBinding", "SelectedDirectory",
        "SelectedExecution", "SelectedIdentity", "SelectedInput", "SelectedLaneMismatch", "SetupBegin",
        "SetupCommit", "SetupIntegrity", "SetupProposal", "SetupReplay", "SetupValidation",
        "SnapshotMismatch", "Source", "SourceDestinationOverlap", "SourceMismatch", "Stale",
        "Storage", "Suite", "SuiteBudget", "TerminalCheckpointMissing", "TooLarge", "TransportUnknown",
        "UnknownCase", "UnknownRow", "UnsupportedDomain", "UnsupportedPlatform", "Usage",
        "UseNativeComparisonEntry", "Watchdog", "Workspace",
    ];
    CODES
        .iter()
        .copied()
        .find(|candidate| *candidate == error)
        .unwrap_or("SelectedExecution")
}

#[cfg(test)]
thread_local! {
    pub(super) static FAIL_CLEANUP_ONCE: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

enum Cleanup {
    Confirmed { poisoned: bool },
    Uncertain,
}

fn cleanup(runtime: &SharedRuntime) -> Cleanup {
    #[cfg(test)]
    if FAIL_CLEANUP_ONCE.with(|fault| fault.replace(false)) {
        return Cleanup::Uncertain;
    }
    match runtime.try_lock() {
        Ok(mut owner) => match owner.terminate_and_reap() {
            Ok(()) => Cleanup::Confirmed { poisoned: false },
            Err(_) => Cleanup::Uncertain,
        },
        Err(TryLockError::Poisoned(poison)) => {
            // Recover poisoning only for direct cleanup, never inference.
            match poison.into_inner().terminate_and_reap() {
                Ok(()) => Cleanup::Confirmed { poisoned: true },
                Err(_) => Cleanup::Uncertain,
            }
        }
        Err(TryLockError::WouldBlock) => Cleanup::Uncertain,
    }
}

/// The caller has already drained Host/provider use and still owns its ledgers.
/// This function does not settle reservations, publish reports or inspect assets.
pub(super) fn finish_owner<R: SelectedNativeReservation>(
    reservation: R,
    runtime: SharedRuntime,
    cause: Option<String>,
) -> std::result::Result<(), SelectedNativeFailure<R>> {
    // Fixed-sized failure representation for any reservation type. The pair
    // already owns this exact runtime before a cleanup or transfer can fail.
    let mut owned = Box::new((reservation, runtime));
    match cleanup(&owned.1) {
        Cleanup::Confirmed { poisoned } => {
            drop(owned);
            if poisoned {
                Err(SelectedNativeFailure::from_error("Cleanup".into()))
            } else {
                match cause {
                    Some(error) => Err(SelectedNativeFailure::from_error(error)),
                    None => Ok(()),
                }
            }
        }
        Cleanup::Uncertain => {
            let cause = Some(closed_code(cause.as_deref().unwrap_or("Cleanup")));
            // Keep our original Arc even if a faulty native adapter panics or
            // returns the wrong Arc. A rejected handoff cannot release this pair.
            let transfer = owned.1.clone();
            let accepted = match catch_unwind(AssertUnwindSafe(|| owned.0.retain_uncertain(transfer))) {
                Ok(Ok(())) => true,
                Ok(Err(returned)) => {
                    drop(returned);
                    false
                }
                Err(_) => false,
            };
            let retained = if accepted {
                // The same actual Arc was installed before the ticket drops.
                drop(owned);
                None
            } else {
                Some(owned)
            };
            Err(SelectedNativeFailure {
                code: "Cleanup",
                cause,
                cleanup_uncertain: true,
                retained,
            })
        }
    }
}
