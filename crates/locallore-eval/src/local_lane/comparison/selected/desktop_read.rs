//! Read-only selected-run capability. No execution, assets, or renderer paths.
#[cfg(test)]
mod budget_review_tests;
#[cfg(test)]
mod review_tests;
use super::super::desktop_api::{
    bounded_evidence, check_access, render_evidence, Arm, EvidenceRequest,
};
use super::*;
use locallore::inspection_query::{self, Query, MAX_ROWS};

/// Retains the actual selected lock/pins and a validated immutable snapshot.
/// It is deliberately neither serializable nor constructible from JSON.
pub struct OpenedSelected {
    destination: Destination,
    binding: String,
    metadata: Value,
}

// A report's aggregate charges cannot detect offsetting settlement changes.
// Seal the actual bounded ledger/setup files too, without exposing their bytes.
fn accounting_seal(dir: &Path) -> Result<Value> {
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

fn snapshot(destination: &Destination) -> Result<(String, Value, [Option<StoredTurn>; 2])> {
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
    Ok((binding, metadata, turns))
}

pub fn open_read_only(dir: &Path) -> Result<OpenedSelected> {
    let destination = open_destination(dir)?;
    let (binding, metadata, _) = snapshot(&destination)?;
    Ok(OpenedSelected {
        destination,
        binding,
        metadata,
    })
}

fn fresh(run: &OpenedSelected) -> Result<[Option<StoredTurn>; 2]> {
    let (binding, metadata, turns) = snapshot(&run.destination)?;
    if binding != run.binding || metadata != run.metadata {
        return Err("SnapshotMismatch".into());
    }
    Ok(turns)
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
    let turns = fresh(run)?;
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
    // A committed Store can survive a lost checkpoint. Do not invent workflow
    // success, receipt/capture availability, or unknown historical measurements.
    // Validate an actor lens on the actual before Engine when it is available.
    let observer = match request {
        EvidenceRequest::Query { observer, view, .. } => {
            if path.exists() {
                let input = &manifest.source_inputs[index];
                let full = engine(&path, &input.scope)?;
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
        "row":{"turn":manifest.selection.turn,"arm":ARM_NAMES[index]},
        "scope":manifest.source_inputs[index].scope,
        "before_head":manifest.source_inputs[index].before_head,"after_head":null,
        "observer":observer,"edge":null,"read_only":true,"generation_grant":false,
        "body":{"kind":"missing","reason":"checkpoint_unavailable"}}))
}
