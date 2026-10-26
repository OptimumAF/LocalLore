//! Read-only protocol3 capability. No provider, execution grant or source import.
use super::{
    database, decode, inspect_comparison, load_turn3, load_turns3, Manifest, StoredTurn3, ARM_NAMES,
};
use crate::local_lane::comparison::desktop_api::{self as shared, Arm, EvidenceRequest, RowId};
use crate::{digest, encode, ordinary, Result};
use serde_json::{json, Value};
use std::{
    fs::{self, File, OpenOptions},
    path::{Path, PathBuf},
};

const MAX_SUMMARY: usize = 2 * 1024 * 1024;

/// Opaque retained native read capability; never serializable/executable.
pub struct OpenedComparison {
    directory: PathBuf,
    snapshot: Value,
    manifest: Manifest,
    key: String,
    turns: [Vec<StoredTurn3>; 2],
    _pins: Vec<File>,
    _lock: File,
}

fn snapshot(directory: &Path) -> Result<(Value, Manifest, [Vec<StoredTurn3>; 2])> {
    let manifest: Manifest = decode(&directory.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    let report = inspect_comparison(directory)?;
    let turns = load_turns3(directory, &manifest, &manifest.key()?)?;
    let mut rows = Vec::new();
    let mut reported = report.turns.iter();
    for index in 0..24 {
        for arm in 0..2 {
            let Some(turn) = turns[arm].get(index) else {
                continue;
            };
            if reported.next() != Some(&turn.row) {
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
    let value = json!({"version":1,"protocol_version":3,"binding":binding,
        "report":report,"rows":rows,"read_only":true,"execution_available":false,
        "unavailable":["selected_protocol3_rerun_not_implemented"]});
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
    // Viewing never creates, writes or truncates a lock/run/checkpoint.
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
    // Last validated immutable snapshot, not live status or execution permission.
    Ok(run.snapshot.clone())
}

pub fn evidence(
    run: &OpenedComparison,
    expected_binding: &str,
    row: &RowId,
    request: EvidenceRequest,
    native_inspection_granted: bool,
) -> Result<Value> {
    // Reuse the exact early access guard, before any identity/source probe.
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
    let current = load_turn3(&arm_dir, &path, retained.index, arm, &run.key, &manifest)?;
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
    // The shared renderer reads actual Store edges/receipt and retained raw
    // hashes again. Query2 remains the actor authority; no V2 report is forged.
    shared::render_evidence_view(&arm_dir, &path, &view, expected_binding, request)
}
