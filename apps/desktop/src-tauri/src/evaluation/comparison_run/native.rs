//! Native lane over the same comparison worker and actual retained model owner.
use super::*;
use crate::models::ModelManager;

impl EvaluationManager {
    pub fn full_comparison_catalog_native(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
    ) -> Result<Value> {
        self.full_catalog_lane(lease, epoch, granted, ComparisonLane::Native)
    }
    pub fn full_comparison_lookup_native(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        client: &str,
    ) -> Result<Value> {
        self.full_lookup_lane(lease, epoch, granted, client, ComparisonLane::Native)
    }
    pub fn full_comparison_status_native(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
    ) -> Result<Value> {
        self.full_status_lane(lease, epoch, granted, token, ComparisonLane::Native)
    }
    pub fn full_comparison_open_native(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        run_id: &str,
    ) -> Result<Value> {
        self.full_open_lane(lease, epoch, granted, run_id, ComparisonLane::Native)
    }
    pub fn full_comparison_cancel_native(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        token: &str,
        operation: u64,
    ) -> Result<Value> {
        self.full_cancel_lane(
            lease,
            epoch,
            granted,
            token,
            operation,
            ComparisonLane::Native,
        )
    }
    pub fn full_comparison_close_native(
        &self,
        lease: &WindowLease,
        epoch: u64,
        _: bool,
        token: &str,
    ) -> Result<Value> {
        self.full_close_lane(lease, epoch, token, ComparisonLane::Native)
    }
    pub fn full_comparison_pick_native(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        client: &str,
        run_id: &str,
        consent: impl FnOnce() -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        self.full_pick_lane(
            lease,
            epoch,
            granted,
            (client, run_id),
            consent,
            ComparisonLane::Native,
        )
    }
    pub fn full_comparison_start_native(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        input: FullComparisonStart,
        consent: impl FnOnce(&Value) -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        self.full_start_execution(
            lease,
            epoch,
            granted,
            input,
            Execution::Native(NativeExecution {
                models: models.clone(),
                consent: Box::new(consent),
            }),
        )
    }
    pub fn full_comparison_resume_native(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        input: FullComparisonNativeResume,
        consent: impl FnOnce(&Value) -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        self.full_resume_execution(
            lease,
            epoch,
            granted,
            (&input.run_token, input.max_new_scenes),
            Execution::Native(NativeExecution {
                models: models.clone(),
                consent: Box::new(consent),
            }),
        )
    }
    fn full_confirming(
        &self,
        lease: &WindowLease,
        epoch: u64,
        operation: u64,
        run: &str,
        cancel: &Cancellation,
    ) -> Result<()> {
        lease.dispatch(epoch, || {
            if cancel.is_cancelled() {
                return Err("Cancelled".into());
            }
            let parent = self.state()?;
            if !parent.job.as_ref().is_some_and(|j| {
                j.kind == JobKind::ComparisonRun
                    && j.epoch == epoch
                    && j.id == operation
                    && j.run == run
                    && j.worker_active
            }) {
                return Err("Closed".into());
            }
            let mut full = self.full_lock()?;
            let record = full
                .runs
                .get_mut(run)
                .filter(|r| {
                    r.epoch == epoch && r.operation == Some(operation) && r.phase != "closed"
                })
                .ok_or("Closed")?;
            record.phase = "awaiting_confirmation";
            Ok(())
        })
    }
    pub(super) fn full_work(
        &self,
        lease: &WindowLease,
        (epoch, operation): (u64, u64),
        expected: &Index,
        cancel: &Cancellation,
        (work, batch): (Work, usize),
        native: Option<NativeExecution>,
    ) -> FullOutcome {
        let prepared = match self.full_prepare_work(lease, epoch, expected, cancel, work) {
            Ok(value) => value,
            Err(error) => return FullOutcome::plain(Err(error)),
        };
        let (output, reference, _pins) = match prepared {
            PreparedWork::Inspected(report) => return FullOutcome::plain(Ok(*report)),
            PreparedWork::Execute {
                output,
                reference,
                _pins,
            } => (output, reference, _pins),
        };
        let resume = matches!(work, Work::Resume);
        let mut outcome = match native {
            None if expected.lane().ok() == Some(ComparisonLane::Scripted) => FullOutcome::plain(
                literal_v3::run_comparison(
                    &output,
                    resume,
                    expected.kind,
                    cancel,
                    batch,
                    LaneFactory::ScriptedBaseline,
                    reference.as_deref(),
                )
                .map_err(failure),
            ),
            Some(NativeExecution { models, consent })
                if expected.lane().ok() == Some(ComparisonLane::Native) =>
            {
                let metadata = json!({"version":1,"kind":"full_comparison_execution","protocol_version":3,"input_lane":"approved_native","run_id":expected.run_id,"client_id":expected.client_id,"comparison_kind":kind_name(expected.kind),"batch":batch,"max_admissions":expected.binding.max_admissions,"max_roles":expected.binding.max_roles,"max_active_ms":expected.binding.max_active_ms});
                let mut consent_error = None;
                let result = literal_v3::run_native_comparison(
                    &output,
                    resume,
                    expected.kind,
                    cancel,
                    batch,
                    || {
                        if !lease.valid(epoch) || cancel.is_cancelled() {
                            return Err("Interrupted".into());
                        }
                        self.full_confirming(lease, epoch, operation, &expected.run_id, cancel)
                            .map_err(|_| "Interrupted".to_owned())?;
                        if !lease.valid(epoch) || cancel.is_cancelled() {
                            return Err("Interrupted".into());
                        }
                        // This callback precedes any reservation/assets. Catch
                        // only this safe boundary, never the post-owner body.
                        let answer = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                            consent(&metadata)
                        }))
                        .unwrap_or_else(|_| Err("EvaluationInternal".into()));
                        let accepted = answer.map_err(|error| {
                            consent_error = Some(super::super::selected::failure(&error));
                            "Interrupted".to_owned()
                        })?;
                        if !accepted || !lease.valid(epoch) || cancel.is_cancelled() {
                            return Err("Interrupted".into());
                        }
                        self.reserve_owned(&models, JobKind::ComparisonRun, epoch, operation)
                    },
                    reference.as_deref(),
                );
                let mut outcome = match result {
                    Ok(report) => FullOutcome::plain(Ok(report)),
                    Err(error) => FullOutcome::native(error),
                };
                // Preserve the typed owner first. Only the code-owned native
                // consent diagnostic is restored after the shared error closes.
                if let Some(error) = consent_error {
                    outcome.result = Err(error.clone());
                    outcome.cause = Some(error);
                }
                outcome
            }
            _ => FullOutcome::plain(Err("EvaluationInternal".into())),
        };
        if outcome.result.is_ok() {
            if let Err(error) = self.budget(Some(output.parent().unwrap_or(&output))) {
                outcome.result = Err(error);
            }
        }
        outcome
    }
    pub(super) fn full_finish(
        &self,
        lease: &WindowLease,
        epoch: u64,
        run: &str,
        operation: u64,
        mut outcome: FullOutcome,
    ) -> Result<()> {
        // The existing single Job remains installed throughout actual execution.
        // Retire, close and generic cleanup cannot remove an active worker.
        {
            let mut parent = self.state.lock().unwrap_or_else(|p| p.into_inner());
            let job = parent
                .job
                .as_mut()
                .filter(|j| {
                    j.kind == JobKind::ComparisonRun
                        && j.epoch == epoch
                        && j.id == operation
                        && j.run == run
                })
                .ok_or("Closed")?;
            if let Some(owned) = job.selected.as_mut() {
                owned.retained = outcome.retained.take();
            }
        }
        let uncertain = outcome.uncertain;
        let mut removed = None;
        let answer = lease.dispatch(epoch, || {
            let mut parent = self.state()?;
            if !parent.job.as_ref().is_some_and(|j| {
                j.kind == JobKind::ComparisonRun
                    && j.epoch == epoch
                    && j.id == operation
                    && j.run == run
            }) {
                return Err("Closed".into());
            }
            let mut full = self.full_lock()?;
            let record = full
                .runs
                .get_mut(run)
                .filter(|r| {
                    r.epoch == epoch && r.operation == Some(operation) && r.phase != "closed"
                })
                .ok_or("Closed")?;
            record.cause = outcome.cause;
            match outcome.result {
                Ok(report) => {
                    record.report = Some((
                        report.completed_scenes,
                        report.completed,
                        report.source_matches,
                    ));
                    record.phase = if report.completed {
                        "completed"
                    } else {
                        "paused"
                    };
                    record.error = None;
                }
                Err(error) => {
                    record.report = None;
                    record.phase = if uncertain {
                        "cleanup_required"
                    } else {
                        "failed"
                    };
                    record.error = Some(error);
                }
            }
            // Publish the terminal view and transition the same actual Job in
            // one metadata critical section. A clean result never presents a
            // transient retained-cleanup requirement between those operations.
            parent.job.as_mut().ok_or("Closed")?.worker_active = false;
            if !uncertain {
                removed = parent.job.take();
            }
            Ok(())
        });
        self.clear_cancellation(epoch, operation);
        if answer.is_err() {
            let mut parent = self.state.lock().unwrap_or_else(|p| p.into_inner());
            if let Some(job) = parent.job.as_mut().filter(|j| {
                j.kind == JobKind::ComparisonRun
                    && j.epoch == epoch
                    && j.id == operation
                    && j.run == run
            }) {
                job.worker_active = false;
                if !uncertain {
                    removed = parent.job.take();
                }
            }
        }
        // Actual R/Models drops occur outside metadata and lease gates.
        drop(removed);
        answer
    }
    pub(in crate::evaluation) fn full_comparison_cleanup_confirmed(
        &self,
        epoch: u64,
        operation: u64,
        run: &str,
    ) {
        let mut full = self
            .full_comparison
            .lock()
            .unwrap_or_else(|p| p.into_inner());
        if let Some(record) = full
            .runs
            .get_mut(run)
            .filter(|r| r.epoch == epoch && r.operation == Some(operation))
        {
            if record.phase == "cleanup_required" {
                record.phase = "failed";
            }
        }
    }
}
