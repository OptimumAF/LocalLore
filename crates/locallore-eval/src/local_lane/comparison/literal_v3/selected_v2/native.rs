//! Native selected2 adapter over the same retained owner as selected1.
use super::*;
use crate::local_lane::comparison::{native_selected_workflow as owned, native_startup};
use shared::{SelectedNativeFailure, SelectedNativeReservation};

type NativeResult<T, R> = std::result::Result<T, SelectedNativeFailure<R>>;
struct Workflow {
    plan: PreparedSelectedPlan,
    destination: Destination,
    work: Work,
}
impl owned::Workflow for Workflow {
    type Report = SelectedComparisonReportV2;
    fn profile(&self) -> &PlayProfile {
        &self.plan.manifest.profile
    }
    fn started(&self) -> Instant {
        self.work.ledgers[0].started
    }
    fn remaining(&self) -> u64 {
        remaining(&self.work)
    }
    fn preflight(&self) -> Result<()> {
        preflight(&self.work)
    }
    fn ledgers(&mut self) -> &mut [Ledger; 2] {
        &mut self.work.ledgers
    }
    fn save_setup(&mut self, ms: u64, status: &str, load: Option<Value>) -> Result<()> {
        owned::save_setup_at(
            &self.destination.dir,
            &self.destination.manifest.binding,
            &mut self.work.ledgers,
            ms,
            status,
            load,
        )
    }
    fn execute(&mut self, factory: Option<&LaneFactory>, cancel: &Cancellation) -> Result<()> {
        execute_work(
            &self.plan,
            &self.destination,
            &mut self.work,
            factory,
            cancel,
        )
    }
    fn finish(mut self) -> Result<Self::Report> {
        finish_workflow(&self.plan, &self.destination, &mut self.work)
    }
}
fn remaining(work: &Work) -> u64 {
    work.ledgers
        .iter()
        .map(Ledger::remaining)
        .min()
        .unwrap_or(0)
}
pub fn run_native_selected<R: SelectedNativeReservation>(
    plan: PreparedSelectedPlan,
    new_dir: &Path,
    cancel: &Cancellation,
    reserve: impl FnOnce() -> Result<R>,
) -> NativeResult<SelectedComparisonReportV2, R> {
    let started = Instant::now();
    let failure = SelectedNativeFailure::from_error;
    if !plan.manifest.native().map_err(failure)? {
        return Err(failure("SelectedLaneMismatch".into()));
    }
    plan.refresh(cancel).map_err(failure)?;
    let (target, _pins) =
        shared::destination_target_for(&plan.source_dir, new_dir).map_err(failure)?;
    let work = inspect_work(&plan, &target, started).map_err(failure)?;
    preflight(&work).map_err(failure)?;
    let mut deadline =
        native_startup::preparation_deadline(started, remaining(&work), Instant::now())
            .map_err(failure)?;
    native_startup::check_preparation(cancel, deadline).map_err(failure)?;
    let reservation = if work.needs_admission.into_iter().any(|needed| needed) {
        Some(reserve().map_err(failure)?)
    } else {
        None
    };
    deadline = deadline.min(
        native_startup::preparation_deadline(started, remaining(&work), Instant::now())
            .map_err(failure)?,
    );
    native_startup::check_preparation(cancel, deadline).map_err(failure)?;
    preflight(&work).map_err(failure)?;
    let destination = new_destination(&plan, &target).map_err(failure)?;
    owned::run(
        Workflow {
            plan,
            destination,
            work,
        },
        reservation,
        cancel,
        deadline,
    )
}
pub fn resume_native_selected<R: SelectedNativeReservation>(
    dir: &Path,
    source_dir: &Path,
    expected_binding: &str,
    cancel: &Cancellation,
    reserve: impl FnOnce() -> Result<R>,
) -> NativeResult<SelectedComparisonReportV2, R> {
    let started = Instant::now();
    let failure = SelectedNativeFailure::from_error;
    shared::cancelled(cancel).map_err(failure)?;
    if !hex(expected_binding) {
        return Err(failure("SelectedIdentity".into()));
    }
    let destination = open_destination(dir).map_err(failure)?;
    let m = &destination.manifest;
    if !m.native().map_err(failure)? {
        return Err(failure("SelectedLaneMismatch".into()));
    }
    if m.binding != expected_binding {
        return Err(failure("CheckpointMismatch".into()));
    }
    let row = shared_read::RowId {
        turn: m.selection.turn.clone(),
        arm: if m.selection.clicked_arm == "left" {
            shared_read::Arm::Left
        } else {
            shared_read::Arm::Right
        },
    };
    let plan = prepare_selected(
        source_dir,
        &m.source_binding,
        &row,
        SelectedIntent {
            client_id: m.client_id.clone(),
            lane: SelectedLane::ApprovedNative,
        },
        cancel,
    )
    .map_err(failure)?;
    shared::disjoint(&plan.source_dir, &destination.dir).map_err(failure)?;
    if plan.manifest != *m {
        return Err(failure("CheckpointMismatch".into()));
    }
    plan.refresh(cancel).map_err(failure)?;
    let work = inspect_work(&plan, &destination.dir, started).map_err(failure)?;
    if work.turns.iter().all(Option::is_some) {
        return report(&destination.dir, m, &work.turns, &work.ledgers).map_err(failure);
    }
    preflight(&work).map_err(failure)?;
    let mut deadline =
        native_startup::preparation_deadline(started, remaining(&work), Instant::now())
            .map_err(failure)?;
    native_startup::check_preparation(cancel, deadline).map_err(failure)?;
    let reservation = if work.needs_admission.into_iter().any(|needed| needed) {
        Some(reserve().map_err(failure)?)
    } else {
        None
    };
    deadline = deadline.min(
        native_startup::preparation_deadline(started, remaining(&work), Instant::now())
            .map_err(failure)?,
    );
    native_startup::check_preparation(cancel, deadline).map_err(failure)?;
    preflight(&work).map_err(failure)?;
    owned::run(
        Workflow {
            plan,
            destination,
            work,
        },
        reservation,
        cancel,
        deadline,
    )
}
