//! Native-owned verified model lifecycle. No renderer-supplied file or executable paths.
use crate::{exports, lease::WindowLease};
use locallore::{host::Host, play::PlayProfile};
use locallore_local_runtime::{
    LocalRuntime, OwnedStartFailure, MODEL_BYTES, MODEL_SHA256, PROFILE, RUNTIME_COMMIT,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs::{self, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex, TryLockError, Weak,
    },
};
type SharedRuntime = Arc<Mutex<LocalRuntime>>;

/// Native-only acknowledgement, never a renderer value or a cleanup request.
/// A clone observes the same actual cleanup even after the slot is replaced.
#[derive(Clone)]
pub(crate) struct CleanupWitness(Arc<AtomicBool>);
impl CleanupWitness {
    pub(crate) fn confirmed(&self) -> bool {
        self.0.load(Ordering::Acquire)
    }
    fn confirm(&self) {
        self.0.store(true, Ordering::Release);
    }
    fn same(&self, other: &Self) -> bool {
        Arc::ptr_eq(&self.0, &other.0)
    }
}
#[cfg(test)]
thread_local! {
    static FAIL_CLEANUP_ONCE: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
    static CLOSE_REVOKE_PAUSE: std::cell::RefCell<Option<(std::sync::mpsc::SyncSender<()>, std::sync::mpsc::Receiver<()>)>> = const { std::cell::RefCell::new(None) };
}
// The worker staged with this application, verified on the held file before
// process creation. A renderer or editable profile cannot select this identity.
const APPROVED_WORKER_SHA256: &str =
    "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434";
fn owner_failed<T>(owner: &Mutex<T>, failed: impl FnOnce(&T) -> bool) -> bool {
    match owner.try_lock() {
        Ok(runtime) => failed(&runtime),
        Err(TryLockError::WouldBlock) => false,
        Err(TryLockError::Poisoned(_)) => true,
    }
}
pub(crate) struct CleanupOutcome {
    pub(crate) confirmed: bool,
    pub(crate) result: Result<(), String>,
}
fn cleanup_owner<T>(
    owner: &Mutex<T>,
    shutdown: impl FnOnce(&mut T) -> Result<(), String>,
) -> CleanupOutcome {
    #[cfg(test)]
    if FAIL_CLEANUP_ONCE.with(|fault| fault.replace(false)) {
        return CleanupOutcome {
            confirmed: false,
            result: Err("Cleanup".into()),
        };
    }
    match owner.lock() {
        Ok(mut runtime) => {
            let result = shutdown(&mut runtime);
            CleanupOutcome {
                confirmed: result.is_ok(),
                result,
            }
        }
        Err(poisoned) => {
            // Recover only to drain/reap the failed owner, never to resume inference.
            let result = shutdown(&mut poisoned.into_inner());
            CleanupOutcome {
                confirmed: result.is_ok(),
                result: Err("Cleanup".into()),
            }
        }
    }
}

fn try_cleanup_owner<T>(
    owner: &Mutex<T>,
    shutdown: impl FnOnce(&mut T) -> Result<(), String>,
) -> CleanupOutcome {
    #[cfg(test)]
    if FAIL_CLEANUP_ONCE.with(|fault| fault.replace(false)) {
        return CleanupOutcome {
            confirmed: false,
            result: Err("Cleanup".into()),
        };
    }
    let (mut runtime, poisoned) = match owner.try_lock() {
        Ok(runtime) => (runtime, false),
        Err(TryLockError::Poisoned(poisoned)) => (poisoned.into_inner(), true),
        Err(TryLockError::WouldBlock) => {
            return CleanupOutcome {
                confirmed: false,
                result: Err("Cleanup".into()),
            }
        }
    };
    // Keep this same guard through actual cleanup: dropping it and relocking
    // would reintroduce an unbounded wait on a newly occupied runtime mutex.
    let result = shutdown(&mut runtime);
    CleanupOutcome {
        confirmed: result.is_ok(),
        result: if poisoned {
            Err("Cleanup".into())
        } else {
            result
        },
    }
}
#[cfg(test)]
fn shutdown_owner<T>(
    owner: &Mutex<T>,
    shutdown: impl FnOnce(&mut T) -> Result<(), String>,
) -> Result<(), String> {
    cleanup_owner(owner, shutdown).result
}
struct Inner {
    evaluation: Option<u64>,
    evaluation_sequence: u64,
    retained_evaluations: usize,
    runtime_cleanup_witness: Option<(Weak<Mutex<LocalRuntime>>, CleanupWitness)>,
    starting: Option<u64>,
    closing: Option<u64>,
    cleanup_uncertain: bool,
    cleanup_cause: Option<String>,
    phase: &'static str,
    percent: u64,
    error: Option<String>,
    job: u64,
    cancel: Arc<AtomicBool>,
    runtime: Option<SharedRuntime>,
    profile: Option<PlayProfile>,
}
pub struct ModelManager {
    root: PathBuf,
    resource: PathBuf,
    inner: Mutex<Inner>,
    close_worker: Mutex<()>,
}
pub struct EvaluationReservation {
    owner: Arc<ModelManager>,
    ticket: u64,
    retained_owner: Option<Weak<Mutex<LocalRuntime>>>,
    selected_identity: Option<Weak<Mutex<LocalRuntime>>>,
    cleanup_witness: CleanupWitness,
    pub resource: PathBuf,
    pub model: PathBuf,
}
impl EvaluationReservation {
    pub(crate) fn retain_uncertain(&mut self, runtime: SharedRuntime) -> Result<(), SharedRuntime> {
        let mut s = self.owner.inner.lock().unwrap_or_else(|p| p.into_inner());
        if s.evaluation != Some(self.ticket)
            || s.runtime
                .as_ref()
                .is_some_and(|current| !Arc::ptr_eq(current, &runtime))
        {
            return Err(runtime);
        }
        s.runtime = Some(runtime);
        s.profile = None;
        s.cleanup_uncertain = true;
        s.phase = "failed";
        s.percent = 0;
        s.error = Some("Cleanup".into());
        Ok(())
    }

    fn mark_selected_owner(&mut self, runtime: &SharedRuntime) -> Result<(), ()> {
        let identity = Arc::downgrade(runtime);
        if self
            .selected_identity
            .as_ref()
            .is_some_and(|bound| !Weak::ptr_eq(bound, &identity))
        {
            return Err(());
        }
        if let Some(bound) = &self.retained_owner {
            return if Weak::ptr_eq(bound, &identity) {
                Ok(())
            } else {
                Err(())
            };
        }
        let mut s = self.owner.inner.lock().unwrap_or_else(|p| p.into_inner());
        // Overflow cannot wrap admission open. The existing nonzero count stays
        // fail-closed and the shared failure still retains the actual R + Arc.
        s.retained_evaluations = s.retained_evaluations.checked_add(1).ok_or(())?;
        self.selected_identity = Some(identity.clone());
        self.retained_owner = Some(identity);
        Ok(())
    }

    pub(crate) fn cleanup_witness(&self) -> CleanupWitness {
        self.cleanup_witness.clone()
    }

    fn release_selected_owner(&mut self) -> bool {
        if self.retained_owner.is_none() {
            return false;
        }
        let mut s = self.owner.inner.lock().unwrap_or_else(|p| p.into_inner());
        let Some(remaining) = s.retained_evaluations.checked_sub(1) else {
            // An inconsistent private count is never an acknowledgement.
            s.retained_evaluations = 1;
            return false;
        };
        s.retained_evaluations = remaining;
        self.retained_owner = None;
        true
    }

    /// Native-only cleanup of this exact external owner. No Host revocation or
    /// old model-job completion may affect another current slot/supplier.
    pub(crate) fn cleanup_retained(&mut self, runtime: &SharedRuntime) -> CleanupOutcome {
        if !self
            .retained_owner
            .as_ref()
            .is_some_and(|bound| Weak::ptr_eq(bound, &Arc::downgrade(runtime)))
        {
            return CleanupOutcome {
                confirmed: false,
                result: Err("Cleanup".into()),
            };
        }
        // No manager metadata lock is held during actual kill/wait/pipe drain.
        let mut outcome = cleanup_owner(runtime, |runtime| {
            runtime.terminate_and_reap().map_err(runtime_error)
        });
        if outcome.confirmed && !self.release_selected_owner() {
            outcome.confirmed = false;
            outcome.result = Err("Cleanup".into());
        }
        if outcome.confirmed {
            self.cleanup_witness.confirm();
        }
        outcome
    }
}

impl locallore_eval::local_lane::comparison::selected::SelectedNativeReservation
    for EvaluationReservation
{
    fn assets(&self) -> locallore_eval::local_lane::NativeAssets<'_> {
        locallore_eval::local_lane::NativeAssets {
            resource_dir: &self.resource,
            model: &self.model,
        }
    }

    fn retain_uncertain(&mut self, runtime: SharedRuntime) -> Result<(), SharedRuntime> {
        // Only the selected consumer opts into this additional external fence.
        // Latch before a stale ticket, busy slot or panic can reject transfer.
        if self.mark_selected_owner(&runtime).is_err() {
            return Err(runtime);
        }
        let original = runtime.clone();
        EvaluationReservation::retain_uncertain(self, runtime)?;
        {
            let mut s = self.owner.inner.lock().unwrap_or_else(|p| p.into_inner());
            if s.evaluation != Some(self.ticket)
                || !s
                    .runtime
                    .as_ref()
                    .is_some_and(|owner| Arc::ptr_eq(owner, &original))
            {
                return Err(original);
            }
            s.runtime_cleanup_witness =
                Some((Arc::downgrade(&original), self.cleanup_witness.clone()));
        }
        // The exact actual owner is now in the same manager's Cleanup slot.
        // Either this count or that slot excludes admission throughout handoff.
        if self.release_selected_owner() {
            Ok(())
        } else {
            Err(original)
        }
    }
}
impl Drop for EvaluationReservation {
    fn drop(&mut self) {
        let mut s = self.owner.inner.lock().unwrap_or_else(|p| p.into_inner());
        if s.evaluation == Some(self.ticket) {
            s.evaluation = None;
        }
    }
}
impl ModelManager {
    #[cfg(test)]
    pub(crate) fn selected_rejected_for_test(
        self: &Arc<Self>,
        owner: SharedRuntime,
    ) -> (EvaluationReservation, SharedRuntime) {
        let mut reservation = self
            .reserve_evaluation()
            .expect("isolated selected fixture");
        {
            let mut s = self.inner.lock().unwrap();
            assert_eq!(s.evaluation, Some(reservation.ticket));
            // Fixed native-unit fault only. No child, file/path, IPC or
            // development-app endpoint can be selected through this helper.
            s.evaluation = None;
        }
        let returned = match locallore_eval::local_lane::comparison::selected::SelectedNativeReservation::retain_uncertain(
            &mut reservation, owner.clone(),
        ) {
            Err(returned) => returned,
            Ok(()) => panic!("isolated stale selected ticket accepted a handoff"),
        };
        assert!(Arc::ptr_eq(&returned, &owner));
        (reservation, returned)
    }

    /// This manager's tracked ownership only; callers must independently drain
    /// evaluation/Host owners before acknowledging a whole-app close.
    pub(crate) fn cleanup_complete(&self) -> bool {
        self.inner
            .try_lock()
            .map(|s| {
                s.runtime.is_none()
                    && s.runtime_cleanup_witness.is_none()
                    && s.evaluation.is_none()
                    && s.retained_evaluations == 0
                    && s.starting.is_none()
                    && s.closing.is_none()
                    && !s.cleanup_uncertain
            })
            .unwrap_or(false)
    }

    pub fn new(root: PathBuf, resource: PathBuf) -> Self {
        Self {
            root,
            resource,
            close_worker: Mutex::new(()),
            inner: Mutex::new(Inner {
                evaluation: None,
                evaluation_sequence: 0,
                retained_evaluations: 0,
                runtime_cleanup_witness: None,
                starting: None,
                closing: None,
                cleanup_uncertain: false,
                cleanup_cause: None,
                phase: "unloaded",
                percent: 0,
                error: None,
                job: 0,
                cancel: Arc::new(AtomicBool::new(false)),
                runtime: None,
                profile: None,
            }),
        }
    }
    fn path(&self) -> PathBuf {
        self.root.join("Qwen3-0.6B-Q8_0.gguf")
    }
    pub fn status(&self) -> Result<Value, String> {
        let imported = self.path().is_file();
        let mut s = self.inner.lock().map_err(|_| "Internal")?;
        let failed = s.runtime.as_ref().is_some_and(|owner| {
            owner_failed(owner, |runtime| {
                matches!(runtime.status(), locallore_local_runtime::Status::Failed)
            })
        });
        if s.cleanup_uncertain {
            if s.phase != "unloading" {
                s.phase = "failed";
            }
            s.error = Some("Cleanup".into());
        } else if failed && s.phase != "unloading" {
            s.phase = "failed";
            s.error = Some("Runtime".into());
        }
        let external = s.retained_evaluations > 0;
        let phase = if external && s.phase != "unloading" {
            "failed"
        } else {
            s.phase
        };
        let error = if external {
            Some("Cleanup".to_owned())
        } else {
            s.error.clone()
        };
        Ok(
            json!({"operation_id":s.job,"resident":s.runtime.is_some(),"phase":phase,"percent":s.percent,"error":error,"loaded":s.runtime.is_some()&&s.profile.is_some()&&!failed&&!s.cleanup_uncertain&&!external,"imported":imported,"profile":s.profile,"available_profile":{"id":PROFILE,"model_bytes":MODEL_BYTES,"model_sha256":MODEL_SHA256,"runtime_revision":RUNTIME_COMMIT,"device":"CPU: experimental Windows x64","qualification":"Experimental. Narrative quality and offline qualification remain pending."}}),
        )
    }
    fn begin(&self, phase: &'static str) -> Result<(u64, Arc<AtomicBool>), String> {
        let mut s = self.inner.lock().map_err(|_| "Internal")?;
        if s.evaluation.is_some()
            || s.retained_evaluations > 0
            || s.starting.is_some()
            || s.closing.is_some()
        {
            return Err("Busy".into());
        }
        if matches!(
            s.phase,
            "choosing" | "checking" | "copying" | "loading" | "unloading"
        ) {
            return Err("Busy".into());
        }
        if s.runtime.is_some() && phase != "unloading" {
            return Err("ModelLoaded".into());
        }
        if s.job >= 9_007_199_254_740_991 {
            return Err("TooLarge".into());
        }
        s.job += 1;
        s.cancel = Arc::new(AtomicBool::new(false));
        s.phase = phase;
        s.percent = 0;
        s.error = None;
        if phase == "loading" {
            s.starting = Some(s.job);
        } else if phase == "unloading" {
            s.closing = Some(s.job);
        }
        Ok((s.job, s.cancel.clone()))
    }
    /// Atomic exclusion with ordinary model ownership. Trusted paths stay native-only;
    /// the existing curated runner reserves startup and verifies actual assets itself.
    pub fn reserve_evaluation(self: &Arc<Self>) -> Result<EvaluationReservation, String> {
        let mut s = self.inner.lock().map_err(|_| "Internal")?;
        if s.evaluation.is_some()
            || s.retained_evaluations > 0
            || s.starting.is_some()
            || s.closing.is_some()
            || matches!(
                s.phase,
                "choosing" | "checking" | "copying" | "loading" | "unloading"
            )
        {
            return Err("Busy".into());
        }
        if s.runtime.is_some() {
            return Err("ModelLoaded".into());
        }
        s.evaluation_sequence = s.evaluation_sequence.checked_add(1).ok_or("TooLarge")?;
        let ticket = s.evaluation_sequence;
        s.evaluation = Some(ticket);
        Ok(EvaluationReservation {
            owner: self.clone(),
            ticket,
            retained_owner: None,
            selected_identity: None,
            cleanup_witness: CleanupWitness(Arc::new(AtomicBool::new(false))),
            resource: self.resource.clone(),
            model: self.path(),
        })
    }
    /// Read the existing ownership sequence for independent no-reservation tests.
    /// No counter, runtime hook, file access or renderer command is introduced.
    #[cfg(test)]
    pub(crate) fn evaluation_sequence_for_tests(&self) -> Result<u64, String> {
        self.inner
            .lock()
            .map(|state| state.evaluation_sequence)
            .map_err(|_| "Internal".into())
    }
    #[cfg(feature = "dev-harness")]
    pub(crate) fn evaluation_observation_for_harness(&self) -> Result<(u64, bool, usize), String> {
        self.inner
            .lock()
            .map(|state| {
                (
                    state.evaluation_sequence,
                    state.evaluation.is_some(),
                    state.retained_evaluations,
                )
            })
            .map_err(|_| "Internal".into())
    }
    fn progress(&self, job: u64, phase: &'static str, percent: u64) {
        if let Ok(mut s) = self.inner.lock() {
            if s.job == job {
                s.phase = phase;
                s.percent = percent.min(100);
            }
        }
    }
    fn finish(&self, job: u64, result: &Result<(), String>) {
        if let Ok(mut s) = self.inner.lock() {
            let finished_startup = s.starting == Some(job);
            if finished_startup {
                s.starting = None;
            }
            if s.closing == Some(job) {
                s.closing = None;
            }
            if s.job == job {
                if s.cleanup_uncertain {
                    s.phase = "failed";
                    s.error = Some("Cleanup".into());
                    s.percent = 0;
                    return;
                }
                s.phase = if s.runtime.is_some() {
                    "loaded"
                } else if result
                    .as_ref()
                    .err()
                    .is_some_and(|e| e != "Cancelled" && e != "Closed")
                {
                    "failed"
                } else {
                    "unloaded"
                };
                s.error = result
                    .as_ref()
                    .err()
                    .filter(|e| *e != "Cancelled" && *e != "Closed")
                    .cloned();
                s.percent = if result.is_ok() { 100 } else { 0 };
            } else if finished_startup
                && s.phase == "unloading"
                && s.runtime.is_none()
                && s.closing.is_none()
            {
                // Retirement cannot acknowledge cleanup for the still-running
                // loader. Only its matching completion releases this exclusion.
                s.phase = "unloaded";
                s.error = None;
            }
        }
    }
    pub fn cancel(&self, operation_id: u64) -> Result<Value, String> {
        let s = self.inner.lock().map_err(|_| "Internal")?;
        if s.job != operation_id {
            return Err("StaleModelOperation".into());
        }
        if s.phase == "unloading" {
            return Ok(json!({"status":"finishing_cleanup"}));
        }
        if !matches!(
            s.phase,
            "choosing" | "checking" | "copying" | "loading" | "unloading"
        ) {
            return Ok(json!({"status":"finished"}));
        }
        s.cancel.store(true, Ordering::SeqCst);
        Ok(json!({"status":"cancelling"}))
    }
    pub fn import(
        &self,
        lease: &WindowLease,
        epoch: u64,
        pick: impl FnOnce() -> Result<Option<PathBuf>, String>,
    ) -> Result<Value, String> {
        let (job, cancel) = lease.dispatch(epoch, || self.begin("choosing"))?;
        let result = (|| {
            reap_imports(&self.root)?;
            if cancel.load(Ordering::SeqCst) || !lease.valid(epoch) {
                return Err("Closed".into());
            }
            let Some(source) = pick()? else {
                return Err("Cancelled".into());
            };
            let cancelled = || cancel.load(Ordering::SeqCst) || !lease.valid(epoch);
            copy_model(
                &source,
                &self.root,
                cancelled,
                |phase, n| self.progress(job, phase, n),
                |handle, staging, target| {
                    lease.dispatch(epoch, || {
                        if cancel.load(Ordering::SeqCst) {
                            return Err("Cancelled".into());
                        }
                        exports::atomic_finalize(handle, staging, target).map_err(|e| {
                            if e == "ExportExists" {
                                "ModelExists".into()
                            } else {
                                e
                            }
                        })
                    })
                },
            )
        })();
        self.finish(job, &result);
        match result {
            Ok(()) => self.status(),
            Err(e) if e == "Cancelled" => self.status(),
            Err(e) => Err(e),
        }
    }
    pub fn load(&self, host: &Host, lease: &WindowLease, epoch: u64) -> Result<Value, String> {
        let (job, cancel) = lease.dispatch(epoch, || self.begin("loading"))?;
        let mut owned = None;
        let mut configured = false;
        let mut result = (|| {
            if !lease.valid(epoch) {
                return Err("Closed".into());
            }
            reap_imports(&self.root)?;
            let (runtime, startup_error) =
                match LocalRuntime::spawn_packaged_owned_expected_cancelled(
                    &self.resource,
                    &self.path(),
                    APPROVED_WORKER_SHA256,
                    || cancel.load(Ordering::SeqCst) || !lease.valid(epoch),
                ) {
                    Ok(runtime) => (runtime, None),
                    Err(OwnedStartFailure::BeforeChild(cause)) => return Err(runtime_error(cause)),
                    Err(OwnedStartFailure::AfterChild { cause, owner }) => {
                        (*owner, Some(runtime_error(cause)))
                    }
                };
            let shared = Arc::new(Mutex::new(runtime));
            {
                let mut s = self.inner.lock().unwrap_or_else(|p| p.into_inner());
                // Starting remains reserved through retirement until this exact
                // callback finishes. No other loader/evaluation can own the slot.
                assert_eq!(s.starting, Some(job));
                assert!(s.runtime.is_none());
                s.runtime = Some(shared.clone());
            }
            owned = Some(shared.clone());
            if let Some(error) = startup_error {
                return Err(error);
            }
            let profile = {
                let mut runtime = shared.lock().map_err(|_| "Cleanup")?;
                runtime
                    .load(|| cancel.load(Ordering::SeqCst) || !lease.valid(epoch))
                    .map_err(runtime_error)?;
                PlayProfile {
                    id: PROFILE.into(),
                    model_sha256: MODEL_SHA256.into(),
                    runtime_revision: RUNTIME_COMMIT.into(),
                    template_sha256:
                        "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361".into(),
                    worker_sha256: runtime.worker_sha256().into(),
                    profile_manifest_sha256: locallore_local_runtime::profile_manifest_sha256(),
                    context_tokens: 4096,
                    director_tokens: 350,
                    narrator_tokens: 350,
                    deadline_ms: 120000,
                    repair_limit: 1,
                }
            };
            profile.validate().map_err(|e| e.to_string())?;
            lease.dispatch(epoch, || {
                {
                    let s = self.inner.lock().map_err(|_| "Internal")?;
                    if s.job != job || cancel.load(Ordering::SeqCst) {
                        return Err("Cancelled".into());
                    }
                }
                // Never hold metadata needed by synchronous Destroyed retirement while
                // waiting on the Host state mutex (which may be doing blocking storage I/O).
                let owner = shared.clone();
                host.configure_local_provider(
                    profile.clone(),
                    Arc::new(move || {
                        Box::new(locallore_local_runtime::adapter::RuntimeProvider::new(
                            owner.clone(),
                        ))
                    }),
                )?;
                configured = true;
                let mut s = self.inner.lock().map_err(|_| "Internal")?;
                if s.job != job || cancel.load(Ordering::SeqCst) {
                    drop(s);
                    host.disable_local_provider();
                    return Err("Cancelled".into());
                }
                s.profile = Some(profile);
                Ok(())
            })
        })();
        if let (Err(cause), Some(owner)) = (&result, owned.as_ref()) {
            let initial_cause = cause.clone();
            if configured {
                host.disable_local_provider();
            }
            let outcome = cleanup_owner(owner, |runtime| {
                runtime.terminate_and_reap().map_err(runtime_error)
            });
            {
                let mut s = self.inner.lock().unwrap_or_else(|p| p.into_inner());
                if s.starting == Some(job)
                    && s.runtime
                        .as_ref()
                        .is_some_and(|current| Arc::ptr_eq(current, owner))
                {
                    s.profile = None;
                    if outcome.confirmed {
                        s.runtime = None;
                        s.cleanup_uncertain = false;
                        s.cleanup_cause = None;
                    } else {
                        s.cleanup_uncertain = true;
                        s.cleanup_cause = Some(initial_cause);
                        s.phase = "failed";
                        s.error = Some("Cleanup".into());
                    }
                }
            }
            if outcome.result.is_err() {
                result = Err("Cleanup".into());
            }
        }
        self.finish(job, &result);
        result?;
        self.status()
    }
    pub fn unload(&self, host: &Host, lease: &WindowLease, epoch: u64) -> Result<Value, String> {
        let (job, runtime) = lease.dispatch(epoch, || {
            let (job, _) = self.begin("unloading")?;
            host.disable_local_provider();
            let mut s = self.inner.lock().map_err(|_| "Internal")?;
            s.profile = None;
            Ok((job, s.runtime.clone()))
        })?;
        let outcome = if let Some(owner) = &runtime {
            cleanup_owner(owner, |runtime| {
                runtime.terminate_and_reap().map_err(runtime_error)
            })
        } else {
            CleanupOutcome {
                confirmed: true,
                result: Ok(()),
            }
        };
        self.finish_cleanup(job, runtime.as_ref(), outcome)
    }

    /// Cleanup only the selected slot associated with this opaque native token.
    /// An older acknowledged token never touches a newer runtime or Host.
    pub(crate) fn cleanup_selected(&self, witness: &CleanupWitness) -> CleanupOutcome {
        let admitted = (|| -> Result<(u64, SharedRuntime), String> {
            let mut s = self.inner.lock().map_err(|_| "Cleanup")?;
            if witness.confirmed() {
                return Err("AlreadyClean".into());
            }
            if s.evaluation.is_some()
                || s.retained_evaluations > 0
                || s.starting.is_some()
                || s.closing.is_some()
                || matches!(
                    s.phase,
                    "choosing" | "checking" | "copying" | "loading" | "unloading"
                )
            {
                return Err("Busy".into());
            }
            let runtime = s.runtime.clone().ok_or("Cleanup")?;
            if !s
                .runtime_cleanup_witness
                .as_ref()
                .is_some_and(|(owner, current)| {
                    current.same(witness) && Weak::ptr_eq(owner, &Arc::downgrade(&runtime))
                })
            {
                return Err("Cleanup".into());
            }
            if s.job >= 9_007_199_254_740_991 {
                return Err("TooLarge".into());
            }
            s.job += 1;
            s.closing = Some(s.job);
            s.phase = "unloading";
            s.percent = 0;
            Ok((s.job, runtime))
        })();
        let (job, runtime) = match admitted {
            Ok(admitted) => admitted,
            Err(error) => {
                return CleanupOutcome {
                    confirmed: witness.confirmed(),
                    result: if witness.confirmed() {
                        Ok(())
                    } else {
                        Err(error)
                    },
                }
            }
        };
        let outcome = try_cleanup_owner(&runtime, |runtime| {
            runtime.terminate_and_reap().map_err(runtime_error)
        });
        let result = outcome.result.clone();
        let _ = self.finish_cleanup(job, Some(&runtime), outcome);
        CleanupOutcome {
            confirmed: witness.confirmed(),
            result: if witness.confirmed() {
                result
            } else {
                Err("Cleanup".into())
            },
        }
    }
    fn finish_cleanup(
        &self,
        job: u64,
        owner: Option<&SharedRuntime>,
        outcome: CleanupOutcome,
    ) -> Result<Value, String> {
        {
            let mut s = self.inner.lock().unwrap_or_else(|p| p.into_inner());
            if s.job == job {
                if s.closing == Some(job) {
                    s.closing = None;
                }
                let same = match (owner, s.runtime.as_ref()) {
                    (Some(expected), Some(current)) => Arc::ptr_eq(expected, current),
                    (None, None) => true,
                    _ => false,
                };
                if same && outcome.confirmed {
                    if let (Some(owner), Some((bound, witness))) =
                        (owner, &s.runtime_cleanup_witness)
                    {
                        if Weak::ptr_eq(bound, &Arc::downgrade(owner)) {
                            witness.confirm();
                        }
                    }
                    s.runtime_cleanup_witness = None;
                    s.runtime = None;
                    s.profile = None;
                    s.cleanup_uncertain = false;
                    s.cleanup_cause = None;
                    if s.starting.is_none() {
                        s.phase = if outcome.result.is_ok() {
                            "unloaded"
                        } else {
                            "failed"
                        };
                        s.error = outcome.result.as_ref().err().cloned();
                        s.percent = if outcome.result.is_ok() { 100 } else { 0 };
                    }
                } else if same || s.cleanup_uncertain {
                    // Preserve the actual slot on uncertainty, including an owner
                    // arriving after retirement took its cleanup snapshot.
                    s.cleanup_uncertain = s.runtime.is_some();
                    s.phase = "failed";
                    s.error = Some("Cleanup".into());
                    s.percent = 0;
                }
            }
        }
        outcome.result?;
        self.status()
    }
    #[cfg(test)]
    fn finish_unload(&self, job: u64, result: Result<(), String>) -> Result<Value, String> {
        self.finish(job, &result);
        result?;
        self.status()
    }
    // Synchronous revocation happens before the close cleanup worker is scheduled.
    pub fn retire(&self) -> Option<(u64, Option<SharedRuntime>)> {
        let mut s = self.inner.lock().ok()?;
        s.cancel.store(true, Ordering::SeqCst);
        s.job += 1;
        s.closing = Some(s.job);
        s.phase = "unloading";
        s.profile = None;
        Some((s.job, s.runtime.clone()))
    }
    pub fn close(&self, host: Option<&Host>, retired: Option<(u64, Option<SharedRuntime>)>) {
        let Some((job, _retired_runtime)) = retired else {
            return;
        };
        // Retirement remains synchronous/nonblocking on this worker gate.
        // A superseding close cannot release replacement admission before this
        // worker's already-authorized Host side effects have finished.
        let _close_worker = self.close_worker.lock().unwrap_or_else(|p| p.into_inner());
        // The evaluation drain precedes this call. Its final selected handoff
        // may have installed the actual owner AFTER synchronous retirement.
        // Validate this retirement, then capture that current slot under the
        // same gate; the earlier None snapshot is not a cleanup acknowledgement.
        let runtime = match self.inner.lock() {
            Ok(s) if s.job == job && s.closing == Some(job) => s.runtime.clone(),
            _ => return,
        };
        #[cfg(test)]
        CLOSE_REVOKE_PAUSE.with(|hook| {
            if let Some((entered, release)) = hook.borrow_mut().take() {
                let _ = entered.try_send(());
                let _ = release.recv_timeout(std::time::Duration::from_secs(5));
            }
        });
        // The closing ticket excludes a replacement while supplier revocation
        // waits outside the metadata lock. A duplicate stale close cannot revoke it.
        if let Some(host) = host {
            host.disable_local_provider();
        }
        let outcome = if let Some(owner) = &runtime {
            cleanup_owner(owner, |runtime| {
                runtime.terminate_and_reap().map_err(runtime_error)
            })
        } else {
            CleanupOutcome {
                confirmed: true,
                result: Ok(()),
            }
        };
        let _ = self.finish_cleanup(job, runtime.as_ref(), outcome);
    }
}
fn runtime_error(error: locallore_local_runtime::Error) -> String {
    format!("{error:?}")
}
// A live import denies a second DELETE-access open. Reap only abandoned files
// in this exact app-owned GUID namespace; never recurse or resolve a file after pinning.
fn reap_imports(root: &Path) -> Result<(), String> {
    if !root.exists() {
        return Ok(());
    }
    let _pins = exports::pin_directory(root)?;
    for entry in fs::read_dir(root).map_err(|_| "Io")?.take(128) {
        let entry = entry.map_err(|_| "Io")?;
        let name = entry.file_name();
        let Some(id) = name
            .to_str()
            .and_then(|s| s.strip_prefix(".import-"))
            .and_then(|s| s.strip_suffix(".part"))
        else {
            continue;
        };
        if id.len() != 36
            || !id.bytes().enumerate().all(|(i, b)| {
                if [8, 13, 18, 23].contains(&i) {
                    b == b'-'
                } else {
                    b.is_ascii_hexdigit()
                }
            })
        {
            continue;
        }
        let _ = remove_abandoned_import(&entry.path());
    }
    Ok(())
}
fn remove_abandoned_import(path: &Path) -> Result<(), String> {
    #[cfg(windows)]
    {
        use std::os::windows::{
            fs::{MetadataExt, OpenOptionsExt},
            io::AsRawHandle,
        };
        use windows::Win32::{
            Foundation::HANDLE,
            Storage::FileSystem::{
                FileDispositionInfo, SetFileInformationByHandle, FILE_DISPOSITION_INFO,
            },
        };
        let handle = OpenOptions::new()
            .read(true)
            .access_mode(0x80000000 | 0x00010000)
            .share_mode(1)
            .custom_flags(0x00200000)
            .open(path)
            .map_err(|_| "Io")?;
        let meta = handle.metadata().map_err(|_| "Io")?;
        if !meta.is_file() || meta.file_attributes() & 0x400 != 0 || meta.len() > MODEL_BYTES {
            return Err("InvalidInput".into());
        }
        let info = FILE_DISPOSITION_INFO { DeleteFile: true };
        unsafe {
            SetFileInformationByHandle(
                HANDLE(handle.as_raw_handle()),
                FileDispositionInfo,
                (&info as *const FILE_DISPOSITION_INFO).cast(),
                std::mem::size_of::<FILE_DISPOSITION_INFO>() as u32,
            )
        }
        .map_err(|_| "Io".to_owned())
    }
    #[cfg(not(windows))]
    {
        let _ = path;
        Err("Unsupported".into())
    }
}
fn copy_model(
    source: &Path,
    root: &Path,
    cancelled: impl Fn() -> bool,
    progress: impl Fn(&'static str, u64),
    publish: impl FnOnce(&std::fs::File, &Path, &Path) -> Result<(), String>,
) -> Result<(), String> {
    progress("checking", 0);
    if cancelled() {
        return Err("Cancelled".into());
    }
    let _source_pins = exports::pin_directory(source.parent().ok_or("ModelInvalid")?)?;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.share_mode(1).custom_flags(0x00200000);
    }
    let mut input = options.open(source).map_err(|_| "ModelInvalid")?;
    let meta = input.metadata().map_err(|_| "ModelInvalid")?;
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if meta.file_attributes() & 0x400 != 0 {
            return Err("ModelInvalid".into());
        }
    }
    if !meta.is_file() || meta.len() != MODEL_BYTES {
        return Err("ModelInvalid".into());
    }
    fs::create_dir_all(root).map_err(|_| "Io")?;
    let _pins = exports::pin_directory(root)?;
    if root.join("Qwen3-0.6B-Q8_0.gguf").exists() {
        return Err("ModelExists".into());
    }
    if available(root)? < MODEL_BYTES + 64 * 1024 * 1024 {
        return Err("InsufficientSpace".into());
    }
    let staging = root.join(format!(".import-{}.part", exports::identifier()?));
    let target = root.join("Qwen3-0.6B-Q8_0.gguf");
    let result = (|| {
        let mut options = OpenOptions::new();
        options.write(true).create_new(true);
        #[cfg(windows)]
        {
            use std::os::windows::fs::OpenOptionsExt;
            options.access_mode(0x40000000 | 0x00010000).share_mode(1);
        }
        let mut output = options.open(&staging).map_err(|_| "Io")?;
        let mut digest = Sha256::new();
        let mut chunk = vec![0u8; 1024 * 1024];
        let mut count = 0;
        loop {
            if cancelled() {
                return Err("Cancelled".into());
            }
            let n = input.read(&mut chunk).map_err(|_| "Io")?;
            if n == 0 {
                break;
            }
            count += n as u64;
            if count > MODEL_BYTES {
                return Err("ModelInvalid".into());
            }
            digest.update(&chunk[..n]);
            output.write_all(&chunk[..n]).map_err(|_| "Io")?;
            progress("copying", count * 100 / MODEL_BYTES);
        }
        if count != MODEL_BYTES || format!("{:x}", digest.finalize()) != MODEL_SHA256 {
            return Err("ModelInvalid".into());
        }
        output.sync_all().map_err(|_| "Io")?;
        if cancelled() {
            return Err("Cancelled".into());
        }
        // Windows rename never replaces an existing model. Existing imported artifact is immutable.
        publish(&output, &staging, &target)?;
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_file(staging);
    }
    result
}
fn available(path: &Path) -> Result<u64, String> {
    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        use windows::{core::PCWSTR, Win32::Storage::FileSystem::GetDiskFreeSpaceExW};
        let wide = path
            .as_os_str()
            .encode_wide()
            .chain(Some(0))
            .collect::<Vec<_>>();
        let mut available = 0;
        unsafe { GetDiskFreeSpaceExW(PCWSTR(wide.as_ptr()), Some(&mut available), None, None) }
            .map_err(|_| "Io")?;
        Ok(available)
    }
    #[cfg(not(windows))]
    {
        let _ = path;
        Err("Unsupported".into())
    }
}
pub fn choose_model(owner: isize) -> Result<Option<PathBuf>, String> {
    #[cfg(windows)]
    {
        use windows::{
            core::HSTRING,
            Win32::{Foundation::HWND, System::Com::*, UI::Shell::*},
        };
        unsafe {
            CoInitializeEx(None, COINIT_APARTMENTTHREADED)
                .ok()
                .map_err(|_| "PickerUnavailable")?;
            let result = (|| {
                let dialog: IFileOpenDialog =
                    CoCreateInstance(&FileOpenDialog, None, CLSCTX_INPROC_SERVER)
                        .map_err(|_| "PickerUnavailable")?;
                dialog
                    .SetOptions(
                        FOS_FORCEFILESYSTEM
                            | FOS_FILEMUSTEXIST
                            | FOS_PATHMUSTEXIST
                            | FOS_NOCHANGEDIR
                            | FOS_DONTADDTORECENT,
                    )
                    .map_err(|_| "PickerUnavailable")?;
                dialog
                    .SetTitle(&HSTRING::from(
                        "Import the approved Qwen3-0.6B Q8_0 GGUF (local copy)",
                    ))
                    .map_err(|_| "PickerUnavailable")?;
                if let Err(e) = dialog.Show(Some(HWND(owner as *mut _))) {
                    return if e.code().0 as u32 == 0x800704c7 {
                        Ok(None)
                    } else {
                        Err("PickerUnavailable".into())
                    };
                }
                let item = dialog.GetResult().map_err(|_| "PickerUnavailable")?;
                let p = item
                    .GetDisplayName(SIGDN_FILESYSPATH)
                    .map_err(|_| "PickerUnavailable")?;
                let result = p
                    .to_string()
                    .map(|s| Some(PathBuf::from(s)))
                    .map_err(|_| "InvalidInput".into());
                CoTaskMemFree(Some(p.0.cast()));
                result
            })();
            CoUninitialize();
            result
        }
    }
    #[cfg(not(windows))]
    {
        let _ = owner;
        Err("Unsupported".into())
    }
}

#[cfg(test)]
mod literal_native_asset_tests;
#[cfg(test)]
mod owned_cleanup_tests;
#[cfg(test)]
mod selected_review_tests;
#[cfg(test)]
mod tests {
    use super::*;
    struct Root(PathBuf);
    impl Root {
        fn new() -> Self {
            let p = std::env::temp_dir().join(format!(
                "locallore-model-unit-{}",
                exports::identifier().unwrap()
            ));
            fs::create_dir(&p).unwrap();
            Self(p)
        }
    }
    impl Drop for Root {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    #[test]
    fn evaluation_reservation_is_atomic_and_raii_released_without_asset_access() {
        let root = Root::new();
        let manager = Arc::new(ModelManager::new(
            root.0.join("models"),
            root.0.join("missing-worker"),
        ));
        let lease = WindowLease::default();
        let epoch = lease.begin().unwrap();
        let first = manager.reserve_evaluation().unwrap();
        assert!(matches!(manager.reserve_evaluation(),Err(e) if e=="Busy"));
        assert_eq!(
            manager.load(&Host::new(true), &lease, epoch).unwrap_err(),
            "Busy"
        );
        assert_eq!(
            manager.unload(&Host::new(true), &lease, epoch).unwrap_err(),
            "Busy"
        );
        drop(first);
        let second = manager.reserve_evaluation().unwrap();
        drop(second);
        assert_eq!(manager.status().unwrap()["operation_id"], 0);
    }
    #[test]
    #[cfg(windows)]
    fn abandoned_import_cleanup_preserves_active_unrelated_and_approved_files() {
        use std::os::windows::fs::OpenOptionsExt;
        let root = Root::new();
        let stale = root
            .0
            .join(format!(".import-{}.part", exports::identifier().unwrap()));
        let active = root
            .0
            .join(format!(".import-{}.part", exports::identifier().unwrap()));
        let unrelated = root.0.join(".import-not-a-guid.part");
        let approved = root.0.join("Qwen3-0.6B-Q8_0.gguf");
        for path in [&stale, &active, &unrelated, &approved] {
            fs::write(path, b"synthetic").unwrap();
        }
        let guard = OpenOptions::new()
            .write(true)
            .share_mode(1)
            .open(&active)
            .unwrap();
        reap_imports(&root.0).unwrap();
        assert!(!stale.exists());
        for path in [&active, &unrelated, &approved] {
            assert_eq!(fs::read(path).unwrap(), b"synthetic");
        }
        drop(guard);
        reap_imports(&root.0).unwrap();
        assert!(!active.exists());
        assert_eq!(fs::read(&approved).unwrap(), b"synthetic");
    }
    #[test]
    #[cfg(windows)]
    #[ignore = "requires Windows symlink privilege; run explicitly when available"]
    fn abandoned_import_reparse_file_is_preserved() {
        let root = Root::new();
        let source = root.0.join("unrelated");
        fs::write(&source, b"synthetic").unwrap();
        let link = root
            .0
            .join(format!(".import-{}.part", exports::identifier().unwrap()));
        std::os::windows::fs::symlink_file(&source, &link).unwrap();
        reap_imports(&root.0).unwrap();
        assert!(fs::symlink_metadata(&link)
            .unwrap()
            .file_type()
            .is_symlink());
        assert_eq!(fs::read(&source).unwrap(), b"synthetic");
    }
    #[test]
    fn poisoned_runtime_reports_failure_and_unload_finishes_before_error() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        // Synthetic owner exercises the same lifecycle helpers without a model.
        let owner = Mutex::new(false);
        let _ = std::panic::catch_unwind(|| {
            let _guard = owner.lock().unwrap();
            panic!("synthetic owner panic");
        });
        assert!(owner_failed(&owner, |_| false));
        let (job, _) = manager.begin("unloading").unwrap();
        let cleanup = shutdown_owner(&owner, |drained| {
            *drained = true;
            Ok(())
        });
        assert!(*owner.lock().unwrap_err().into_inner());
        assert_eq!(manager.finish_unload(job, cleanup).unwrap_err(), "Cleanup");
        let status = manager.status().unwrap();
        assert_eq!(status["phase"], "failed");
        assert_eq!(status["error"], "Cleanup");
        assert_eq!(status["loaded"], false);
        assert_eq!(status["resident"], false);
        assert!(manager.begin("loading").is_ok());
    }
    #[test]
    fn delayed_same_window_cancel_cannot_cancel_a_new_operation() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        let (old, _) = manager.begin("loading").unwrap();
        manager.finish(old, &Ok(()));
        let (current, cancel) = manager.begin("loading").unwrap();
        assert_eq!(manager.cancel(old).unwrap_err(), "StaleModelOperation");
        assert!(!cancel.load(Ordering::SeqCst));
        assert!(manager.cancel(current).is_ok());
        assert!(cancel.load(Ordering::SeqCst));
    }
    #[test]
    fn old_window_cancellation_cannot_reach_a_new_model_operation() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        let lease = WindowLease::default();
        let old = lease.begin().unwrap();
        let closed = lease.invalidate("main-1").unwrap();
        lease.finish_close(closed, || {});
        let current = lease.begin().unwrap();
        let (job, cancel) = manager.begin("loading").unwrap();
        assert_eq!(
            lease.dispatch(old, || manager.cancel(job)).unwrap_err(),
            "Closed"
        );
        assert!(!cancel.load(Ordering::SeqCst));
        assert!(lease.dispatch(current, || manager.cancel(job)).is_ok());
        assert!(cancel.load(Ordering::SeqCst));
    }
    #[test]
    fn delayed_closed_operations_cannot_start_picker_or_unload_new_window() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        let lease = WindowLease::default();
        let old = lease.begin().unwrap();
        let closed = lease.invalidate("main-1").unwrap();
        lease.finish_close(closed, || {});
        let _new = lease.begin().unwrap();
        let called = AtomicBool::new(false);
        assert_eq!(
            manager
                .import(&lease, old, || {
                    called.store(true, Ordering::SeqCst);
                    Ok(None)
                })
                .unwrap_err(),
            "Closed"
        );
        assert!(!called.load(Ordering::SeqCst));
        assert_eq!(
            manager.unload(&Host::new(true), &lease, old).unwrap_err(),
            "Closed"
        );
        assert_eq!(manager.status().unwrap()["operation_id"], 0);
    }
    #[test]
    fn invalid_sources_cancel_and_missing_worker_are_honest() {
        let root = Root::new();
        let lease = WindowLease::default();
        let epoch = lease.begin().unwrap();
        let manager = ModelManager::new(root.0.join("models"), root.0.join("missing-runtime"));
        assert_eq!(
            manager
                .import(&lease, epoch, || Ok(Some(root.0.join("missing.gguf"))))
                .unwrap_err(),
            "ModelInvalid"
        );
        let corrupt = root.0.join("corrupt model.gguf");
        fs::write(&corrupt, b"not GGUF").unwrap();
        assert_eq!(
            manager
                .import(&lease, epoch, || Ok(Some(corrupt.clone())))
                .unwrap_err(),
            "ModelInvalid"
        );
        assert_eq!(fs::read(&corrupt).unwrap(), b"not GGUF");
        assert_eq!(
            manager.import(&lease, epoch, || Ok(None)).unwrap()["phase"],
            "unloaded"
        );
        assert!(!manager.path().exists());
        let host = Host::new(true);
        assert!(manager.load(&host, &lease, epoch).is_err());
        assert_eq!(manager.status().unwrap()["loaded"], false);
    }
    #[test]
    fn retirement_fences_late_metadata_and_new_loads_until_cleanup() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        let (job, cancel) = manager.begin("checking").unwrap();
        let retired = manager.retire();
        assert!(cancel.load(Ordering::SeqCst));
        manager.progress(job, "loaded", 100);
        manager.finish(job, &Ok(()));
        assert_eq!(manager.status().unwrap()["phase"], "unloading");
        assert_eq!(manager.begin("loading").err().unwrap(), "Busy");
        manager.close(None, retired);
        assert_eq!(manager.status().unwrap()["loaded"], false);
        assert!(manager.begin("loading").is_ok());
    }
}
