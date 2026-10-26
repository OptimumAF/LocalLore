//! Read-only selected-run capability. No execution, assets, or renderer paths.
#[cfg(test)]
mod budget_review_tests;
#[cfg(test)]
mod review_tests;
use super::super::desktop_api::{
    bounded_evidence, check_access, render_evidence, Arm, EvidenceRequest, RowId,
};
use super::*;
use locallore::inspection_query::{self, Observer, Query, MAX_ROWS};

/// Retains the actual selected lock/pins and a validated immutable snapshot.
/// It is deliberately neither serializable nor constructible from JSON.
pub struct OpenedSelected {
    destination: Destination,
    binding: String,
    metadata: Value,
}

// A report's aggregate charges cannot detect offsetting settlement changes.
// Seal the actual bounded ledger/setup files too, without exposing their bytes.
pub(in crate::local_lane::comparison) fn accounting_seal(dir: &Path) -> Result<Value> {
    let mut records = Vec::new();
    for arm in ARM_NAMES {
        for (prefix, cap) in [("invocation", 32), ("admission", MAX_ADMISSIONS)] {
            for index in 0..cap {
                for suffix in ["", "-settled"] {
                    let name = format!("{arm}/{prefix}-{index:02}{suffix}.json");
                    let path = dir.join(&name);
                    if path.exists() {
                        records.push(json!([name, digest(&read(&path, 4096)?)]));
                    }
                }
            }
        }
    }
    for index in 0..32 {
        let name = format!("setup-{index:02}.json");
        let path = dir.join(&name);
        if path.exists() {
            records.push(json!([name, digest(&read(&path, 64 * 1024)?)]));
        }
    }
    Ok(json!(records))
}

struct ReadSnapshot {
    binding: String,
    metadata: Value,
    turns: [Option<StoredTurn>; 2],
    report: SelectedComparisonReportV1,
}

fn snapshot(destination: &Destination) -> Result<ReadSnapshot> {
    let dir = &destination.dir;
    // Revalidate names/link constraints too; cooperative locks do not prove that
    // an unrelated filesystem writer left the originally opened files intact.
    let _pins = pin_selected(dir)?;
    let manifest: SelectedManifest = decode(&dir.join("selected.json"), MANIFEST_CAP)?;
    manifest.validate()?;
    if manifest != destination.manifest {
        return Err("SnapshotMismatch".into());
    }
    let turns = validate_destination(dir, &manifest, None)?;
    let report = report(dir, &manifest, &turns, &ledgers(dir, &manifest.binding)?)?;
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
    let metadata = json!({"version":1,"kind":"selected_read","binding":binding,
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
        return render_evidence(&arm_dir, &path, turn, expected_binding, request);
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

// Shared unchanged missing-checkpoint Query2 transport; caller checks native grant first.
pub(in crate::local_lane::comparison) fn missing_evidence(
    path: &Path,
    input: &SourceInput,
    row: &RowId,
    expected_binding: &str,
    request: EvidenceRequest,
) -> Result<Value> {
    check_access(&request, true)?;
    // A committed Store can survive a lost checkpoint. Do not invent workflow
    // success, receipt/capture availability, or unknown historical measurements.
    // Validate an actor lens on the actual before Engine when it is available.
    let observer = match request {
        EvidenceRequest::Query { observer, view, .. } => {
            if path.exists() {
                let full = engine(path, &input.scope)?;
                let before = full.at_revision(input.before_head).map_err(|_| "Replay")?;
                inspection_query::query(
                    &before,
                    &Query {
                        version: 2,
                        scope: before.scope().clone(),
                        expected_head: before.revision(),
                        at_revision: None,
                        observer: observer.clone(),
                        view,
                        cursor: None,
                        limit: MAX_ROWS,
                        search: String::new(),
                    },
                    true,
                )
                .map_err(|error| format!("Inspection{error}"))?;
            }
            observer
        }
        EvidenceRequest::Receipt { observer }
        | EvidenceRequest::Capture { observer }
        | EvidenceRequest::Outputs { observer } => observer,
    };
    bounded_evidence(json!({"version":1,"binding":expected_binding,
        "row":row,
        "scope":input.scope,
        "before_head":input.before_head,"after_head":null,
        "observer":observer,"edge":null,"read_only":true,"generation_grant":false,
        "body":{"kind":"missing","reason":"checkpoint_unavailable"}}))
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
            "privacy_passed":row.privacy_passed,"context_evidence_available":row.context_evidence_available})
    }).collect();
    bounded_evidence(
        json!({"version":1,"kind":"selected_diagnostics","binding":expected_binding,
        "lane":report.lane,"completed":report.completed,"rows":rows,
        "physical_setups":report.physical_setups,"physical_setup_ms":report.physical_setup_ms,
        "left_charged_ms":report.left_charged_ms,"right_charged_ms":report.right_charged_ms,
        "left_reserved_roles":report.left_reserved_roles,"right_reserved_roles":report.right_reserved_roles,
        "human_reviewed":report.human_reviewed,"quality_accepted":report.quality_accepted,
        "unavailable":report.unavailable}),
    )
}
