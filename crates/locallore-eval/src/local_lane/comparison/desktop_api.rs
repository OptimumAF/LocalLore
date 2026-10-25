//! Data-only inspection of actual comparison checkpoints. Never starts execution.
use super::{
    database, decode, inspect_comparison, load_turn, load_turns, validate_recording, RecordingFile,
    RunManifest, StoredTurn, ARM_NAMES, POLICIES,
};
use crate::{digest, encode, engine, ordinary, read, Result};
use locallore::engine::Engine;
use locallore::inspection_query::{self, Observer, Query, View, MAX_ROWS};
use serde_json::{json, Value};
use std::{
    fs::{self, File, OpenOptions},
    path::{Path, PathBuf},
};

const MAX_SUMMARY: usize = 2 * 1024 * 1024;
const MAX_EVIDENCE: usize = 256 * 1024;

#[cfg(test)]
mod tests;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Arm {
    Left,
    Right,
}
pub struct RowId {
    pub turn: String,
    pub arm: Arm,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Edge {
    Before,
    After,
}
pub enum EvidenceRequest {
    Query {
        edge: Edge,
        observer: Observer,
        view: View,
    },
    Receipt {
        observer: Observer,
    },
    Capture {
        observer: Observer,
    },
    Outputs {
        observer: Observer,
    },
}

/// Native read capability, not a renderer-constructible history or execution grant.
pub struct OpenedComparison {
    directory: PathBuf,
    snapshot: Value,
    manifest: RunManifest,
    key: String,
    turns: [Vec<StoredTurn>; 2],
    _pins: Vec<File>,
    _lock: File,
}
pub(super) struct Snapshot {
    pub(super) value: Value,
    pub(super) turns: [Vec<StoredTurn>; 2],
    pub(super) manifest: RunManifest,
}

pub(super) fn snapshot(directory: &Path) -> Result<Snapshot> {
    let manifest: RunManifest = decode(&directory.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    let report = inspect_comparison(directory)?;
    let turns = load_turns(directory, &manifest, &manifest.stable_key()?)?;
    let mut rows = Vec::new();
    let mut reported = report.turns.iter();
    for index in 0..24 {
        for arm in 0..2 {
            let Some(turn) = turns[arm].get(index) else {
                continue;
            };
            // The public report and source metadata must describe one snapshot.
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
    let value = json!({"version":1,"protocol_version":2,"binding":binding,
        "report":report,"rows":rows,"read_only":true,"execution_available":false,
        "unavailable":["selected_rerun_not_implemented","full_comparison_gui_not_implemented"]});
    if encode(&value)?.len() > MAX_SUMMARY {
        return Err("ReportBudget".into());
    }
    Ok(Snapshot {
        value,
        turns,
        manifest,
    })
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
    // No create/write/truncate flag: merely viewing never creates a lock/run.
    let lock = OpenOptions::new()
        .read(true)
        .open(lock_path)
        .map_err(|_| "Io")?;
    lock.try_lock().map_err(|_| "RunBusy")?;
    let data = snapshot(&directory)?;
    let key = data.manifest.stable_key()?;
    Ok(OpenedComparison {
        directory,
        snapshot: data.value,
        manifest: data.manifest,
        key,
        turns: data.turns,
        _pins: pins,
        _lock: lock,
    })
}

pub fn summary(run: &OpenedComparison, native_inspection_granted: bool) -> Result<Value> {
    if !native_inspection_granted {
        return Err("Forbidden".into());
    }
    Ok(run.snapshot.clone())
}

fn missing(reason: &str) -> Value {
    json!({"kind":"missing","reason":reason})
}

/// Bind the actual immutable engines used by Query2, including its separate
/// Store read after checkpoint validation. Play diagnostics intentionally are
/// not actor context authority; selected full receipts have their own hash.
fn checked_edges(full: &Engine, turn: &StoredTurn) -> Result<(Engine, Engine)> {
    let before = full.at_revision(turn.before_head).map_err(|_| "Replay")?;
    let after = full.at_revision(turn.after_head).map_err(|_| "Replay")?;
    if crate::memory_comparison_v2::semantic_input(&before, &turn.request)?
        != turn.row.input_semantic_sha256
        || crate::memory_comparison_v2::semantic_output(&after)? != turn.row.output_semantic_sha256
        || crate::memory_comparison_v2::mechanical_output(&after)? != turn.row.mechanical_sha256
    {
        return Err("SnapshotMismatch".into());
    }
    Ok((before, after))
}
pub fn evidence(
    run: &OpenedComparison,
    expected_binding: &str,
    row: &RowId,
    request: EvidenceRequest,
    native_inspection_granted: bool,
) -> Result<Value> {
    if !native_inspection_granted {
        return Err("Forbidden".into());
    }
    // Deny an actor's raw-artifact request before even probing identities or
    // source integrity. Those errors must not expose private artifact state.
    let raw_forbidden = match &request {
        EvidenceRequest::Query { .. } => false,
        EvidenceRequest::Receipt { observer }
        | EvidenceRequest::Capture { observer }
        | EvidenceRequest::Outputs { observer } => !matches!(observer, Observer::Omniscient),
    };
    if raw_forbidden {
        return Err("Forbidden".into());
    }
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
    // The entire cohort was validated at open under the retained cooperative
    // writer lock. This is selected evidence for that immutable summary, not
    // a live whole-report health check or permission to resume execution.
    let manifest: RunManifest = decode(&run.directory.join("run.json"), 128 * 1024)?;
    manifest.validate()?;
    if manifest != run.manifest {
        return Err("SnapshotMismatch".into());
    }
    let arm_dir = run.directory.join(ARM_NAMES[arm]);
    let path = database(&arm_dir, retained.index, manifest.kind);
    let current = load_turn(
        &arm_dir,
        &path,
        retained.index,
        ARM_NAMES[arm],
        POLICIES[arm],
        &run.key,
        &manifest,
    )?;
    // A currently valid but changed checkpoint must not be paired with the old
    // binding. Compare every checkpoint field, including diagnostics/timings.
    if encode(&current)? != encode(retained)? {
        return Err("SnapshotMismatch".into());
    }
    let turn = &current;
    let (observer, edge, body) = match request {
        EvidenceRequest::Query {
            edge,
            observer,
            view,
        } => {
            let full = engine(&path, &turn.request.scope)?;
            let (before, after) = checked_edges(&full, turn)?;
            let cut = match edge {
                Edge::Before => before,
                Edge::After => after,
            };
            let head = cut.revision();
            let page = inspection_query::query(
                &cut,
                &Query {
                    version: 2,
                    scope: cut.scope().clone(),
                    expected_head: head,
                    at_revision: None,
                    observer: observer.clone(),
                    view,
                    cursor: None,
                    limit: MAX_ROWS,
                    search: String::new(),
                },
                true,
            )
            .map_err(|e| format!("Inspection{e}"))?;
            (
                observer,
                json!(match edge {
                    Edge::Before => "before",
                    Edge::After => "after",
                }),
                json!({"kind":"query","page":page}),
            )
        }
        EvidenceRequest::Receipt { observer } => {
            let body = if turn.row.phase != "committed" {
                missing("no_accepted_receipt")
            } else {
                let receipt = locallore_storage::Store::open_read_only(&path)
                    .map_err(|_| "Workspace")?
                    .lookup_turn(&turn.request.scope, &row.turn)
                    .map_err(|_| "Lookup")?
                    .receipt
                    .ok_or("Lookup")?;
                if turn.row.actual_receipt_sha256.as_deref()
                    != Some(digest(&encode(&receipt)?).as_str())
                {
                    return Err("CheckpointEvidenceMismatch".into());
                }
                json!({"kind":"receipt","receipt":receipt})
            };
            (observer, json!("after"), body)
        }
        EvidenceRequest::Capture { observer } => {
            let body = match &turn.capture_file {
                None => missing("capture_unavailable"),
                Some(name) => {
                    let capture: Value = decode(
                        &arm_dir.join(name),
                        crate::memory_comparison_v2::MAX_PRIVATE_CAPTURE + 4096,
                    )?;
                    let bytes = encode(&capture)?;
                    if turn.row.capture_sha256.as_deref() != Some(digest(&bytes).as_str()) {
                        return Err("CaptureBinding".into());
                    }
                    if bytes.len() > crate::memory_comparison_v2::MAX_PRIVATE_CAPTURE {
                        return Err("EvidenceBudget".into());
                    }
                    json!({"kind":"capture","capture":capture})
                }
            };
            (observer, Value::Null, body)
        }
        EvidenceRequest::Outputs { observer } => {
            let body = match &turn.recording_file {
                None => missing("recording_unavailable"),
                Some(name) => {
                    let recording: RecordingFile = decode(&arm_dir.join(name), 64 * 1024)?;
                    validate_recording(
                        &arm_dir,
                        turn.row.admission.ok_or("RecordingIntegrity")?,
                        &recording,
                    )?;
                    if turn.row.recording_sha256.as_deref()
                        != Some(digest(&encode(&recording)?).as_str())
                    {
                        return Err("RecordingIntegrity".into());
                    }
                    let mut outputs = Vec::new();
                    for raw in recording.raw {
                        let bytes = read(&arm_dir.join(&raw.file), 16384)?;
                        if bytes.len() != raw.bytes || digest(&bytes) != raw.sha256 {
                            return Err("RawIntegrity".into());
                        }
                        outputs.push(
                            json!({"role":raw.role,"bytes":raw.bytes,"sha256":raw.sha256,
                            "text":String::from_utf8(bytes).map_err(|_| "RawIntegrity")?}),
                        );
                    }
                    json!({"kind":"outputs","outputs":outputs})
                }
            };
            (observer, Value::Null, body)
        }
    };
    let result = json!({"version":1,"binding":expected_binding,
        "row":{"turn":row.turn,"arm":ARM_NAMES[arm]},"scope":turn.request.scope,
        "before_head":turn.before_head,"after_head":turn.after_head,"observer":observer,
        "edge":edge,"read_only":true,"generation_grant":false,"body":body});
    if encode(&result)?.len() > MAX_EVIDENCE {
        return Err("EvidenceBudget".into());
    }
    Ok(result)
}
