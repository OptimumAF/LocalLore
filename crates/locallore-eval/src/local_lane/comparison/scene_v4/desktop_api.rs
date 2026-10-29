// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Read-only protocol4 adapter over the strict scene loader and shared evidence
//! renderer. Retaining a report conveys no provider or execution grant.
use super::{
    database, decode, inspect_comparison, load_turn4, load_turns4, Manifest, StoredTurn4, ARM_NAMES,
};
use crate::local_lane::comparison::desktop_api::{self as shared, Arm, EvidenceRequest, RowId};
use crate::{digest, encode, ordinary, Result};
use serde_json::{json, Value};
use std::{
    fs::{self, File, OpenOptions},
    path::{Path, PathBuf},
};

const MAX_SUMMARY: usize = 2 * 1024 * 1024;

/// Opaque retained read capability, without serialization or execution methods.
pub struct OpenedComparison {
    directory: PathBuf,
    snapshot: Value,
    manifest: Manifest,
    key: String,
    turns: [Vec<StoredTurn4>; 2],
    _pins: Vec<File>,
    _lock: File,
}

fn snapshot(directory: &Path) -> Result<(Value, Manifest, [Vec<StoredTurn4>; 2])> {
    let manifest: Manifest = decode(&directory.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    let report = inspect_comparison(directory)?;
    let turns = load_turns4(directory, &manifest, &manifest.key()?)?;
    let mut rows = Vec::new();
    let mut seen = std::collections::BTreeSet::new();
    let mut reported = report.turns.iter();
    for index in 0..24 {
        for arm in 0..2 {
            let Some(turn) = turns[arm].get(index) else {
                continue;
            };
            // Pair the actual loaded checkpoint with this exact inspector row.
            if !seen.insert((arm, turn.row.turn.clone())) || reported.next() != Some(&turn.row) {
                return Err("SnapshotMismatch".into());
            }
            let mut unavailable = Vec::new();
            if turn.capture_file.is_none() {
                unavailable.push("capture_unavailable");
            }
            if turn.recording_file.is_none() {
                unavailable.push("recording_unavailable");
            }
            if turn.row.phase != "committed" {
                unavailable.push("no_accepted_receipt");
            }
            rows.push(json!({"row":{"turn":turn.row.turn,"arm":ARM_NAMES[arm]},
                "source":{"status":"available","scope":turn.request.scope,
                "before_head":turn.before_head,"after_head":turn.after_head,
                "input_semantic_sha256":turn.row.input_semantic_sha256},
                "capture_available":turn.capture_file.is_some(),
                "receipt_available":turn.row.phase=="committed",
                "recording_available":turn.recording_file.is_some(),"unavailable":unavailable}));
        }
    }
    if reported.next().is_some() || rows.len() > 48 {
        return Err("SnapshotMismatch".into());
    }
    let binding = digest(&encode(
        &json!({"manifest":&manifest,"report":&report,"rows":&rows}),
    )?);
    let value = json!({"version":1,"protocol_version":4,"binding":binding,
        "report":report,"rows":rows,"read_only":true,"execution_available":false,
        "unavailable":["selected_protocol4_rerun_not_implemented"]});
    if encode(&value)?.len() > MAX_SUMMARY {
        return Err("ReportBudget".into());
    }
    Ok((value, manifest, turns))
}

pub fn open_read_only(dir: &Path) -> Result<OpenedComparison> {
    let directory = std::path::absolute(dir).map_err(|_| "Io")?;
    let mut pins = crate::local_lane::desktop_api::pin_directory(&directory)?;
    let mut count = 0usize;
    for entry in fs::read_dir(&directory).map_err(|_| "Io")? {
        count += 1;
        if count > 512 {
            return Err("ReportBudget".into());
        }
        let entry = entry.map_err(|_| "Io")?;
        ordinary(&entry.path())?;
        if entry.file_type().map_err(|_| "Io")?.is_dir() {
            let name = entry.file_name();
            if !["left", "right", "reference"]
                .iter()
                .any(|known| name == *known)
            {
                return Err("ComparisonDirectory".into());
            }
            pins.extend(crate::local_lane::desktop_api::pin_directory(
                &entry.path(),
            )?);
        }
    }
    let lock_path = directory.join("run.lock");
    ordinary(&lock_path)?;
    // Existing lock only: opening a reader cannot create or repair a run.
    let lock = OpenOptions::new()
        .read(true)
        .open(lock_path)
        .map_err(|_| "Io")?;
    lock.try_lock().map_err(|_| "RunBusy")?;
    let (snapshot, manifest, turns) = snapshot(&directory)?;
    let key = manifest.key()?;
    Ok(OpenedComparison {
        directory,
        snapshot,
        manifest,
        key,
        turns,
        _pins: pins,
        _lock: lock,
    })
}

pub fn summary(run: &OpenedComparison, native_inspection_granted: bool) -> Result<Value> {
    if !native_inspection_granted {
        return Err("Forbidden".into());
    }
    // Immutable last-validated snapshot, not live status or fresh integrity.
    Ok(run.snapshot.clone())
}

pub fn evidence(
    run: &OpenedComparison,
    expected_binding: &str,
    row: &RowId,
    request: EvidenceRequest,
    native_inspection_granted: bool,
) -> Result<Value> {
    // Keep raw observer/grant refusal ahead of binding, row and source probes.
    shared::check_access(&request, native_inspection_granted)?;
    if run.snapshot["binding"].as_str() != Some(expected_binding) {
        return Err("SnapshotMismatch".into());
    }
    let arm = match row.arm {
        Arm::Left => 0,
        Arm::Right => 1,
    };
    let retained = run.turns[arm]
        .iter()
        .find(|turn| turn.row.turn == row.turn)
        .ok_or("UnknownRow")?;
    let manifest: Manifest = decode(&run.directory.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    if manifest != run.manifest {
        return Err("SnapshotMismatch".into());
    }
    let arm_dir = run.directory.join(ARM_NAMES[arm]);
    let path = database(&arm_dir, retained.index, manifest.kind);
    let current = load_turn4(&arm_dir, &path, retained.index, arm, &run.key, &manifest)?;
    if encode(&current)? != encode(retained)? {
        return Err("SnapshotMismatch".into());
    }
    let view = shared::EvidenceTurn {
        request: &current.request,
        before_head: current.before_head,
        after_head: current.after_head,
        turn: &current.row.turn,
        arm: &current.row.arm,
        phase: &current.row.phase,
        input_semantic_sha256: &current.row.input_semantic_sha256,
        output_semantic_sha256: &current.row.output_semantic_sha256,
        mechanical_sha256: &current.row.mechanical_sha256,
        actual_receipt_sha256: current.row.actual_receipt_sha256.as_deref(),
        capture_file: current.capture_file.as_deref(),
        recording_file: current.recording_file.as_deref(),
        capture_sha256: current.row.capture_sha256.as_deref(),
        recording_sha256: current.row.recording_sha256.as_deref(),
        admission: current.row.admission,
    };
    // Actual Store prefixes/receipt and observer-filtered Query2 remain shared;
    // a retained metadata report is never converted into an Engine or Receipt.
    shared::render_evidence_view(&arm_dir, &path, &view, expected_binding, request)
}

// The source capability supplies the existing immutable snapshot and lock.
// Companion files are held through parsing/hash/binding validation, never used
// to reconstruct a Host owner or an Engine.
fn validated_companion(
    run: &OpenedComparison,
) -> Result<crate::narration_diagnostic_companion_v1::Loaded> {
    let (fresh, manifest, turns) = snapshot(&run.directory)?;
    if fresh != run.snapshot || manifest != run.manifest {
        return Err("SnapshotMismatch".into());
    }
    let mut loaded = crate::narration_diagnostic_companion_v1::load(
        &run.directory,
        &run.key,
        &manifest.source_sha256,
    )?;
    // Iterate a bounded metadata copy so pins can be retained on the same owner.
    for observation in loaded.observations.clone() {
        let arm = match observation.arm() {
            "left" => 0,
            "right" => 1,
            _ => return Err("DiagnosticBinding".into()),
        };
        let retained = turns[arm]
            .iter()
            .find(|t| t.index == observation.index())
            .ok_or("DiagnosticBinding")?;
        let arm_dir = run.directory.join(ARM_NAMES[arm]);
        let (file, bytes) = super::super::read_narration_diagnostic_file_v1(
            &super::checkpoint_path(&arm_dir, retained.index),
            256 * 1024,
        )?;
        let current: StoredTurn4 =
            serde_json::from_slice(&bytes).map_err(|_| "DiagnosticBinding")?;
        if encode(&current)? != encode(retained)? {
            return Err("SnapshotMismatch".into());
        }
        let source = crate::engine(
            &database(&arm_dir, retained.index, manifest.kind),
            &current.request.scope,
        )?;
        observation.bind_checkpoint(
            &serde_json::to_value(&current).map_err(|_| "DiagnosticWire")?,
            &bytes,
            &source.seed().player,
        )?;
        let admission = observation.admission();
        let (reservation_file, bytes) = super::super::read_narration_diagnostic_file_v1(
            &arm_dir.join(format!("admission-{admission:02}.json")),
            4096,
        )?;
        let reservation: crate::local_lane::Reservation =
            serde_json::from_slice(&bytes).map_err(|_| "DiagnosticBinding")?;
        let (settlement_file, bytes) = super::super::read_narration_diagnostic_file_v1(
            &arm_dir.join(format!("admission-{admission:02}-settled.json")),
            4096,
        )?;
        let settlement: crate::local_lane::Settlement =
            serde_json::from_slice(&bytes).map_err(|_| "DiagnosticBinding")?;
        if reservation.version != 1
            || reservation.binding != run.key
            || reservation.index != admission
            || reservation.turn != current.request.turn
            || reservation.story != format!("scene-{}", current.row.scene)
            || reservation.roles != 3
            || settlement.version != 1
            || settlement.binding != run.key
            || settlement.index != admission
            || settlement.ms != current.row.elapsed_ms
            || !current.row.roles_known
            || settlement.roles != current.row.roles
        {
            return Err("DiagnosticBinding".into());
        }
        loaded.retain_pin(file);
        loaded.retain_pin(reservation_file);
        loaded.retain_pin(settlement_file);
    }
    Ok(loaded)
}

pub(super) fn validate_companion_for_resume(dir: &Path) -> Result<()> {
    let run = open_read_only(dir)?;
    if !validated_companion(&run)?.declared() {
        return Err("DiagnosticNotDeclared".into());
    }
    Ok(())
}

pub fn narration_diagnostic_v1(
    run: &OpenedComparison,
    expected_binding: &str,
    row: &RowId,
    observer: locallore::inspection_query::Observer,
    native_inspection_granted: bool,
) -> Result<Value> {
    shared::check_access(
        &EvidenceRequest::Outputs { observer },
        native_inspection_granted,
    )?;
    if run.snapshot["binding"].as_str() != Some(expected_binding) {
        return Err("SnapshotMismatch".into());
    }
    let arm = match row.arm {
        Arm::Left => 0,
        Arm::Right => 1,
    };
    let retained = run.turns[arm]
        .iter()
        .find(|t| t.row.turn == row.turn)
        .ok_or("UnknownRow")?;
    if retained.index >= 24 {
        return Err("DiagnosticBinding".into());
    }
    let loaded = validated_companion(run)?;
    let observation = loaded.observations.iter().find(|o| {
        o.arm() == ARM_NAMES[arm]
            && o.index() == retained.index
            && retained.row.admission == Some(o.admission())
    });
    let status = if !loaded.declared() {
        "no_declaration"
    } else {
        observation.map_or("no_observation", |o| o.status())
    };
    let mut result = json!({"version":1,"protocol_version":4,"kind":"narration_diagnostic_v1","binding":expected_binding,
        "row":{"turn":retained.row.turn,"arm":ARM_NAMES[arm]},"generation_grant":false,"status":status});
    if let Some(observation) = observation {
        result["observation"] = observation.value()?;
    }
    Ok(result)
}
