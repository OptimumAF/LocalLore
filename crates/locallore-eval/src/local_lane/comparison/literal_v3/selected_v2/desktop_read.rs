//! Read-only selected2 capability over actual Store/Query2 and V3 evidence.
//! No provider, source import, model assets or generation grant.
use super::*;
use crate::local_lane::comparison::{
    desktop_api::{
        bounded_evidence, check_access, render_evidence_view, Arm, EvidenceRequest, EvidenceTurn,
        RowId,
    },
    selected::desktop_read::{accounting_seal, missing_evidence},
};
use locallore::inspection_query::Observer;

/// Retains the actual selected lock/pins and a validated immutable snapshot.
/// It is deliberately neither serializable nor constructible from JSON.
pub struct OpenedSelected {
    destination: Destination,
    binding: String,
    metadata: Value,
}

struct ReadSnapshot {
    binding: String,
    metadata: Value,
    turns: [Option<StoredTurn3>; 2],
    report: SelectedComparisonReportV2,
}

fn snapshot(destination: &Destination) -> Result<ReadSnapshot> {
    let dir = &destination.dir;
    // Revalidate names/link constraints too; cooperative locks do not prove that
    // an unrelated filesystem writer left the originally opened files intact.
    let _pins = shared::pin_selected(dir)?;
    let manifest: SelectedManifest2 = decode(&dir.join("selected.json"), MANIFEST_CAP)?;
    manifest.validate()?;
    if manifest != destination.manifest {
        return Err("SnapshotMismatch".into());
    }
    let turns = validate_destination(dir, &manifest, None)?;
    let report = report(
        dir,
        &manifest,
        &turns,
        &shared::ledgers(dir, &manifest.binding)?,
    )?;
    // Full Requests and diagnostic fields contribute only to a private digest;
    // they must never become an actor-facing summary through Serde.
    let accounting = accounting_seal(dir)?;
    let binding = digest(&encode(&json!({"manifest":manifest,"turns":turns,
        "report":report,"accounting":accounting}))?);
    let arms: Vec<Value> = (0..2)
        .map(|arm| {
            let input = &manifest.source_inputs[arm];
            json!({"arm":ARM_NAMES[arm],"scope":input.scope,
            "before_head":input.before_head,
            "after_head":turns[arm].as_ref().map(|turn| turn.after_head),
            "available":turns[arm].is_some()})
        })
        .collect();
    let metadata = json!({"version":2,"kind":"selected_read","source_protocol_version":3,
        "constructions":manifest.arms,"binding":binding,
        "selection":manifest.selection,"lane":manifest.lane,"arms":arms,
        "read_only":true,"execution_available":false});
    if encode(&metadata)?.len() > 16 * 1024 {
        return Err("ReportBudget".into());
    }
    Ok(ReadSnapshot {
        binding,
        metadata,
        turns,
        report,
    })
}

pub fn open_read_only(dir: &Path) -> Result<OpenedSelected> {
    let destination = open_destination(dir)?;
    let snapshot = snapshot(&destination)?;
    Ok(OpenedSelected {
        destination,
        binding: snapshot.binding,
        metadata: snapshot.metadata,
    })
}

fn fresh(run: &OpenedSelected) -> Result<ReadSnapshot> {
    let snapshot = snapshot(&run.destination)?;
    if snapshot.binding != run.binding || snapshot.metadata != run.metadata {
        return Err("SnapshotMismatch".into());
    }
    Ok(snapshot)
}

/// Small source/edge metadata, identical for all inspection lenses. Outcomes,
/// Requests, model inputs, diagnostic prose and the private report are omitted.
pub fn summary(run: &OpenedSelected, native_inspection_granted: bool) -> Result<Value> {
    if !native_inspection_granted {
        return Err("Forbidden".into());
    }
    fresh(run)?;
    Ok(run.metadata.clone())
}

pub fn evidence(
    run: &OpenedSelected,
    expected_binding: &str,
    arm: Arm,
    request: EvidenceRequest,
    native_inspection_granted: bool,
) -> Result<Value> {
    // This must precede binding, manifest, checkpoint and artifact probes.
    check_access(&request, native_inspection_granted)?;
    if expected_binding != run.binding {
        return Err("SnapshotMismatch".into());
    }
    let turns = fresh(run)?.turns;
    let index = match arm {
        Arm::Left => 0,
        Arm::Right => 1,
    };
    let destination = &run.destination;
    let manifest = &destination.manifest;
    let arm_dir = destination.dir.join(ARM_NAMES[index]);
    let path = database(&arm_dir, manifest.selection.index, manifest.source_kind);
    if let Some(turn) = &turns[index] {
        let view = EvidenceTurn {
            request: &turn.request,
            before_head: turn.before_head,
            after_head: turn.after_head,
            turn: &turn.row.turn,
            arm: &turn.row.arm,
            phase: &turn.row.phase,
            input_semantic_sha256: &turn.row.input_semantic_sha256,
            output_semantic_sha256: &turn.row.output_semantic_sha256,
            mechanical_sha256: &turn.row.mechanical_sha256,
            actual_receipt_sha256: turn.row.actual_receipt_sha256.as_deref(),
            capture_file: turn.capture_file.as_deref(),
            recording_file: turn.recording_file.as_deref(),
            capture_sha256: turn.row.capture_sha256.as_deref(),
            recording_sha256: turn.row.recording_sha256.as_deref(),
            admission: turn.row.admission,
        };
        return render_evidence_view(&arm_dir, &path, &view, expected_binding, request);
    }
    missing_evidence(
        &path,
        &manifest.source_inputs[index],
        &RowId {
            turn: manifest.selection.turn.clone(),
            arm,
        },
        expected_binding,
        request,
    )
}

/// Explicit spoiler diagnostics, separate from actor-safe metadata and Query2.
/// Even omniscient callers receive a manual bounded view, never the full report.
pub fn diagnostics(
    run: &OpenedSelected,
    expected_binding: &str,
    observer: Observer,
    native_inspection_granted: bool,
) -> Result<Value> {
    check_access(
        &EvidenceRequest::Receipt { observer },
        native_inspection_granted,
    )?;
    if expected_binding != run.binding {
        return Err("SnapshotMismatch".into());
    }
    let report = fresh(run)?.report;
    let rows: Vec<Value> = report.rows.iter().map(|row| {
        json!({"turn":row.turn,"arm":row.arm,"phase":row.phase,"error":row.error,
            "expected":row.expected,"passed":row.passed,"failures":row.failures,
            "quality_flags":row.quality_flags,"roles":row.roles,"roles_known":row.roles_known,
            "elapsed_ms":row.elapsed_ms,"actual_receipt_sha256":row.actual_receipt_sha256,
            "privacy_passed":row.privacy_passed,"context_evidence_available":row.context_evidence_available,
            "construction":row.construction,"construction_evidence_status":row.construction_evidence_status,
            "construction_matches":row.construction_matches,"literal_source_units":row.literal_source_units,
            "literal_selected_start":row.literal_selected_start,"literal_selected_units":row.literal_selected_units,
            "fallback":row.fallback})
    }).collect();
    bounded_evidence(
        json!({"version":2,"kind":"selected_diagnostics","source_protocol_version":3,
        "constructions":report.identity.arms,"binding":expected_binding,
        "lane":report.identity.lane,"completed":report.completed,"rows":rows,
        "physical_setups":report.physical_setups,"physical_setup_ms":report.physical_setup_ms,
        "left_charged_ms":report.left_charged_ms,"right_charged_ms":report.right_charged_ms,
        "left_reserved_roles":report.left_reserved_roles,"right_reserved_roles":report.right_reserved_roles,
        "human_reviewed":report.human_reviewed,"quality_accepted":report.quality_accepted,
        "unavailable":report.unavailable}),
    )
}
