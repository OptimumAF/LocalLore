// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Optional shared-engine provider. This adapter never validates or commits canonical outcomes.
use crate::{
    resource_metrics::Sampler, AuthorAccess, Error as RuntimeError, Generation, LocalRuntime,
    Metrics, ReplyBounds, ResourceMetrics, Role, PLAY_REPLY_BOUNDS, PROFILE,
};
use crate::{
    role_metrics::digest, AdapterError, AdapterTerminal, MetricRole, NativeTerminal, RoleMetrics,
    RoleMetricsLog,
};
use locallore::{
    contracts::Error,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
};
use serde_json::json;
use std::{
    sync::{mpsc, Arc, Mutex, TryLockError},
    task::Poll,
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

pub type SharedRuntime = Arc<Mutex<LocalRuntime>>;

#[cfg(all(test, feature = "development-worker"))]
pub(crate) enum AuthorFixtureCase {
    Completed,
    BlockedGenerationObserved,
}
#[cfg(all(test, feature = "development-worker"))]
pub(crate) fn author_fixture(
    log: Option<RoleMetricsLog>,
    case: AuthorFixtureCase,
) -> Result<(RuntimeProvider, SharedRuntime, std::path::PathBuf), crate::OwnedStartFailure> {
    let case = match case {
        AuthorFixtureCase::Completed => crate::DevelopmentFixtureCase::Completed,
        AuthorFixtureCase::BlockedGenerationObserved => {
            crate::DevelopmentFixtureCase::BlockedGenerationObserved
        }
    };
    let (mut owner, directory) = LocalRuntime::development_protocol_fixture_case(case)?;
    owner.author_access = AuthorAccess::Fixture;
    let shared = Arc::new(Mutex::new(owner));
    let mut provider = match log {
        Some(log) => RuntimeProvider::with_metrics(shared.clone(), log),
        None => RuntimeProvider::new(shared.clone()),
    };
    provider.author_access = AuthorAccess::Fixture;
    Ok((provider, shared, directory))
}

#[derive(Clone, PartialEq, Eq)]
struct Identity {
    story: String,
    branch: String,
    turn: String,
    revision: u64,
    profile: String,
    role: String,
    prompt: String,
    schema: Vec<u8>,
    full: Vec<u8>,
}
impl Identity {
    fn same_turn(&self, before: &Self) -> bool {
        self.story == before.story
            && self.branch == before.branch
            && self.turn == before.turn
            && self.revision == before.revision
            && self.profile == before.profile
    }
    fn follows(&self, before: &Self) -> bool {
        self.same_turn(before) && before.role == "director" && self.role == "narrator"
    }
    fn repairs(&self, before: &Self) -> bool {
        self.same_turn(before)
            && before.role == "director"
            && self.role == "director"
            && self.schema == before.schema
            && self.prompt != before.prompt
    }
}
#[derive(Clone, Copy, PartialEq, Eq)]
enum Lane {
    Play,
    InitialWorld,
}
struct CompiledCall {
    identity: Identity,
    generation: Generation,
    lane: Lane,
    reply: ReplyBounds,
}
fn compile(request: &GenerationRequest) -> Result<CompiledCall, Error> {
    let Input::Structured {
        role,
        prompt,
        schema,
    } = &request.input
    else {
        return Err(Error::Provider);
    };
    let native_role = match role.as_str() {
        "director" => Role::Director,
        "narrator" => Role::Narrator,
        _ => return Err(Error::Rule),
    };
    if request.version != 1
        || request.model_profile != PROFILE
        || prompt.is_empty()
        || prompt.contains('\0')
        || !schema.is_object()
        || request.budget.max_output_tokens == 0
        || request.budget.max_output_tokens > 350
        || request.budget.max_output_bytes == 0
        || request.budget.max_output_bytes > 16_384
        || request.budget.deadline_ms == 0
        || request.budget.deadline_ms > 120_000
    {
        return Err(Error::Rule);
    }
    let full=serde_json::to_vec(&json!({"version":request.version,"scope":request.scope,"turn":request.turn,"revision":request.revision,"profile":request.model_profile,"schema_id":request.schema,"budget":{"bytes":request.budget.max_output_bytes,"tokens":request.budget.max_output_tokens,"polls":request.budget.max_pending_polls,"deadline":request.budget.deadline_ms},"role":role,"prompt":prompt,"schema":schema})).map_err(|_|Error::Malformed)?;
    if full.len() > 32_000 {
        return Err(Error::TooLarge);
    }
    Ok(CompiledCall {
        identity: Identity {
            story: request.scope.story.clone(),
            branch: request.scope.branch.clone(),
            turn: request.turn.clone(),
            revision: request.revision,
            profile: request.model_profile.clone(),
            role: role.clone(),
            prompt: prompt.clone(),
            schema: serde_json::to_vec(&json!({"id":request.schema,"schema":schema}))
                .map_err(|_| Error::Malformed)?,
            full,
        },
        generation: Generation {
            role: native_role,
            prompt: prompt.clone(),
            schema: Some(schema.clone()),
            max_tokens: request.budget.max_output_tokens as u16,
        },
        lane: Lane::Play,
        reply: PLAY_REPLY_BOUNDS,
    })
}

struct Outcome {
    result: Result<Vec<u8>, Error>,
    metrics: Option<Metrics>,
    failure: Option<RuntimeError>,
    native: NativeTerminal,
    resources: Option<ResourceMetrics>,
}
impl Outcome {
    fn unavailable(failure: RuntimeError, native: NativeTerminal) -> Self {
        Self {
            result: Err(if failure == RuntimeError::Cancelled {
                Error::Cancelled
            } else {
                Error::Provider
            }),
            metrics: None,
            failure: Some(failure),
            native,
            resources: None,
        }
    }
}
fn metric_error(error: &Error) -> AdapterError {
    match error {
        Error::Cancelled => AdapterError::Cancelled,
        Error::Timeout => AdapterError::Timeout,
        Error::TooLarge => AdapterError::TooLarge,
        Error::RetryMismatch => AdapterError::RetryMismatch,
        Error::Rule | Error::Malformed => AdapterError::InvalidRequest,
        _ => AdapterError::Provider,
    }
}
fn terminal(error: Option<AdapterError>) -> AdapterTerminal {
    match error {
        None => AdapterTerminal::Completed,
        Some(AdapterError::Cancelled) => AdapterTerminal::Cancelled,
        Some(AdapterError::Timeout) => AdapterTerminal::Timeout,
        Some(_) => AdapterTerminal::Failed,
    }
}
struct Observation {
    log: RoleMetricsLog,
    turn: String,
    request: String,
    role: MetricRole,
    director_attempt: Option<u8>,
    ordinal: u8,
    started: Instant,
}
impl Observation {
    fn new(log: &RoleMetricsLog, identity: &Identity, directors: u8) -> Option<Self> {
        let Ok(turn) = serde_json::to_vec(&json!({"story":identity.story,"branch":identity.branch,
            "turn":identity.turn,"revision":identity.revision,"profile":identity.profile}))
        else {
            log.lost();
            return None;
        };
        let turn = digest(&turn);
        log.bind(&turn);
        let director = identity.role == "director";
        Some(Self {
            log: log.clone(),
            turn,
            request: digest(&identity.full),
            role: if director {
                MetricRole::Director
            } else {
                MetricRole::Narrator
            },
            director_attempt: director.then_some(directors - 1),
            ordinal: if director { directors - 1 } else { directors },
            started: Instant::now(),
        })
    }
    fn finish(
        &self,
        outcome: &Outcome,
        status: AdapterTerminal,
        error: Option<AdapterError>,
        dropped: bool,
    ) {
        self.log.record(
            &self.turn,
            RoleMetrics {
                role: self.role,
                director_attempt: self.director_attempt,
                ordinal: self.ordinal,
                request_sha256: self.request.clone(),
                parent_elapsed_ms: self.started.elapsed().as_millis().min(u64::MAX as u128) as u64,
                adapter_terminal: status,
                adapter_error: error,
                native_terminal: outcome.native,
                native_error: outcome.failure,
                worker_metrics: if outcome.native == NativeTerminal::Completed {
                    outcome.metrics.clone()
                } else {
                    None
                },
                drained_on_drop: dropped,
                resources: outcome.resources.clone(),
            },
        );
    }
}
struct Job {
    identity: Identity,
    cancel: Cancellation,
    external: Cancellation,
    receiver: mpsc::Receiver<Outcome>,
    thread: Option<JoinHandle<()>>,
    observation: Option<Observation>,
    observed_error: Option<AdapterError>,
}
/// Create one provider per turn. It accepts a director, at most one director repair, then a narrator;
/// repeated identical polls are idempotent. A new turn needs a fresh provider from the factory.
pub struct RuntimeProvider {
    runtime: SharedRuntime,
    active: Option<Job>,
    completed: Option<(Identity, Result<Vec<u8>, Error>)>,
    metrics: Option<Metrics>,
    failure: Option<RuntimeError>,
    poisoned: bool,
    directors_started: u8,
    log: Option<RoleMetricsLog>,
    sample_resources: bool,
    author_access: AuthorAccess,
}
impl RuntimeProvider {
    pub fn new(runtime: SharedRuntime) -> Self {
        Self {
            runtime,
            active: None,
            completed: None,
            metrics: None,
            failure: None,
            poisoned: false,
            directors_started: 0,
            log: None,
            sample_resources: false,
            author_access: AuthorAccess::Disabled,
        }
    }
    /// Optional passive per-turn recorder; all log loss is independent of inference results.
    pub fn with_metrics(runtime: SharedRuntime, log: RoleMetricsLog) -> Self {
        let mut provider = Self::new(runtime);
        provider.log = Some(log);
        provider
    }
    /// Opt-in private owned-worker sampling; no change to provider or canonical authority.
    pub fn with_resource_metrics(runtime: SharedRuntime, log: RoleMetricsLog) -> Self {
        let mut provider = Self::with_metrics(runtime, log);
        provider.sample_resources = true;
        provider
    }
    pub fn metrics(&self) -> Option<&Metrics> {
        self.metrics.as_ref()
    }
    pub fn last_failure(&self) -> Option<RuntimeError> {
        self.failure
    }
    fn drain(&mut self) {
        if let Some(mut job) = self.active.take() {
            job.cancel.cancel();
            if let Some(thread) = job.thread.take() {
                if thread.join().is_err() {
                    self.failure = Some(RuntimeError::Cleanup);
                    self.poisoned = true;
                    {
                        let mut owner = self
                            .runtime
                            .lock()
                            .unwrap_or_else(|poisoned| poisoned.into_inner());
                        let _ = owner.fail::<()>(RuntimeError::Cleanup);
                    }
                    if let Some(observation) = &job.observation {
                        observation.finish(
                            &Outcome::unavailable(RuntimeError::Cleanup, NativeTerminal::Unknown),
                            AdapterTerminal::Failed,
                            Some(AdapterError::Cleanup),
                            true,
                        );
                    }
                    return;
                }
            }
            if let Ok(outcome) = job.receiver.try_recv() {
                self.metrics = outcome.metrics.clone();
                self.failure = outcome.failure;
                if let Some(observation) = &job.observation {
                    let error = job.observed_error.or_else(|| {
                        job.external
                            .is_cancelled()
                            .then_some(AdapterError::Cancelled)
                    });
                    let status = error.map_or(AdapterTerminal::Dropped, |e| terminal(Some(e)));
                    observation.finish(&outcome, status, error, true);
                }
            } else if let Some(observation) = &job.observation {
                observation.finish(
                    &Outcome::unavailable(RuntimeError::Cleanup, NativeTerminal::Unknown),
                    AdapterTerminal::Failed,
                    Some(AdapterError::Cleanup),
                    true,
                );
            }
        }
    }
    fn start(
        &mut self,
        call: CompiledCall,
        request: &GenerationRequest,
        external: Cancellation,
    ) -> Result<(), Error> {
        let CompiledCall {
            identity,
            generation,
            reply,
            ..
        } = call;
        self.metrics = None;
        self.failure = None;
        let observation = self
            .log
            .as_ref()
            .and_then(|log| Observation::new(log, &identity, self.directors_started));
        let runtime = self.runtime.clone();
        let sample_resources = self.sample_resources;
        let local = Cancellation::default();
        let cancel = local.clone();
        let deadline = Duration::from_millis(request.budget.deadline_ms.min(60_000));
        let bytes = request.budget.max_output_bytes;
        let (sender, receiver) = mpsc::sync_channel(1);
        let observed_external = external.clone();
        #[cfg(all(test, feature = "development-worker"))]
        let reply_delay = crate::AFTER_REPLY_DELAY.with(|delay| delay.take());
        let worker = thread::Builder::new()
            .name("locallore-local-role".into())
            .spawn(move || {
                #[cfg(all(test, feature = "development-worker"))]
                crate::AFTER_REPLY_DELAY.with(|delay| delay.set(reply_delay));
                let mut guard = match runtime.try_lock() {
                    Ok(g) => g,
                    Err(TryLockError::WouldBlock) => {
                        let _ = sender.send(Outcome::unavailable(
                            RuntimeError::Busy,
                            NativeTerminal::NotRun,
                        ));
                        return;
                    }
                    Err(TryLockError::Poisoned(_)) => {
                        let _ = sender.send(Outcome::unavailable(
                            RuntimeError::Cleanup,
                            NativeTerminal::NotRun,
                        ));
                        return;
                    }
                };
                if local.is_cancelled() || external.is_cancelled() {
                    let _ = sender.send(Outcome::unavailable(
                        RuntimeError::Cancelled,
                        NativeTerminal::NotRun,
                    ));
                    return;
                }
                let sampler = sample_resources.then(|| Sampler::start(&guard.child));
                let previous = guard.deadline;
                guard.deadline = deadline;
                let result = guard.generate_bounded(generation, reply, || {
                    local.is_cancelled() || external.is_cancelled()
                });
                guard.deadline = previous;
                let resources = sampler.map(Sampler::finish);
                let metrics = guard.last_metrics().cloned();
                let native = match &result {
                    Ok(_) => NativeTerminal::Completed,
                    Err(RuntimeError::Cancelled) => NativeTerminal::Cancelled,
                    Err(RuntimeError::Timeout) => NativeTerminal::Timeout,
                    Err(_) => NativeTerminal::Failed,
                };
                let (result, failure) = match result {
                    Ok(r) if r.text.len() <= bytes => (Ok(r.text.into_bytes()), None),
                    Ok(_) => (Err(Error::TooLarge), None),
                    Err(e) => (
                        Err(match e {
                            RuntimeError::Cancelled => Error::Cancelled,
                            RuntimeError::Timeout => Error::Timeout,
                            RuntimeError::InvalidRequest => Error::Rule,
                            _ => Error::Provider,
                        }),
                        Some(e),
                    ),
                };
                drop(guard);
                let _ = sender.send(Outcome {
                    result,
                    metrics,
                    failure,
                    native,
                    resources,
                });
            });
        let worker = match worker {
            Ok(worker) => worker,
            Err(_) => {
                if let Some(observation) = &observation {
                    observation.finish(
                        &Outcome {
                            result: Err(Error::Provider),
                            metrics: None,
                            failure: None,
                            native: NativeTerminal::NotRun,
                            resources: None,
                        },
                        AdapterTerminal::Failed,
                        Some(AdapterError::Provider),
                        false,
                    );
                }
                return Err(Error::Provider);
            }
        };
        self.active = Some(Job {
            identity,
            cancel,
            external: observed_external,
            receiver,
            thread: Some(worker),
            observation,
            observed_error: None,
        });
        Ok(())
    }
}
impl InferenceProvider for RuntimeProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        if self.poisoned {
            self.metrics = None;
            return Poll::Ready(Err(Error::RetryMismatch));
        }
        let call = match compile(request) {
            Ok(value) => value,
            Err(error) => {
                self.metrics = None;
                self.failure = None;
                if let Some(job) = &mut self.active {
                    job.cancel.cancel();
                    job.observed_error = Some(metric_error(&error));
                    self.poisoned = true;
                }
                return Poll::Ready(Err(error));
            }
        };
        if call.lane == Lane::InitialWorld && matches!(self.author_access, AuthorAccess::Disabled) {
            self.metrics = None;
            self.failure = Some(RuntimeError::WorkerUnavailable);
            return Poll::Ready(Err(Error::Provider));
        }
        let identity = &call.identity;
        if let Some(job) = &mut self.active {
            if &job.identity != identity {
                self.metrics = None;
                job.cancel.cancel();
                job.observed_error = Some(AdapterError::RetryMismatch);
                self.poisoned = true;
                return Poll::Ready(Err(Error::RetryMismatch));
            }
        }
        if cancel.is_cancelled() {
            self.metrics = None;
            if let Some(job) = &mut self.active {
                job.cancel.cancel();
                job.observed_error = Some(AdapterError::Cancelled);
            } else {
                return Poll::Ready(Err(Error::Cancelled));
            }
        }
        if self.active.is_none() {
            if self.completed.is_none() && identity.role != "director" {
                self.metrics = None;
                return Poll::Ready(Err(Error::RetryMismatch));
            }
            if let Some((previous, result)) = &self.completed {
                if identity == previous {
                    return Poll::Ready(result.clone());
                }
                if result.is_err()
                    || !(identity.follows(previous)
                        || (self.directors_started < 2 && identity.repairs(previous)))
                {
                    self.metrics = None;
                    return Poll::Ready(Err(Error::RetryMismatch));
                }
            }
            if identity.role == "director" {
                self.directors_started += 1;
            }
            if let Err(error) = self.start(call, request, cancel.clone()) {
                return Poll::Ready(Err(error));
            }
        }
        let mut result = match self.active.as_ref().unwrap().receiver.try_recv() {
            Ok(result) => result,
            Err(mpsc::TryRecvError::Empty) => return Poll::Pending,
            Err(mpsc::TryRecvError::Disconnected) => {
                Outcome::unavailable(RuntimeError::Cleanup, NativeTerminal::Unknown)
            }
        };
        let mut job = self.active.take().unwrap();
        if let Some(thread) = job.thread.take() {
            if thread.join().is_err() {
                self.failure = Some(RuntimeError::Cleanup);
                self.poisoned = true;
                {
                    let mut owner = self
                        .runtime
                        .lock()
                        .unwrap_or_else(|poisoned| poisoned.into_inner());
                    let _ = owner.fail::<()>(RuntimeError::Cleanup);
                }
                if let Some(observation) = &job.observation {
                    observation.finish(
                        &Outcome::unavailable(RuntimeError::Cleanup, NativeTerminal::Unknown),
                        AdapterTerminal::Failed,
                        Some(AdapterError::Cleanup),
                        false,
                    );
                }
                return Poll::Ready(Err(Error::Provider));
            }
        }
        self.metrics = result.metrics.clone();
        self.failure = result.failure;
        if cancel.is_cancelled() {
            result.result = Err(Error::Cancelled);
        }
        if let Some(observation) = &job.observation {
            let error = result.result.as_ref().err().map(metric_error);
            observation.finish(&result, terminal(error), error, false);
        }
        self.completed = Some((job.identity, result.result.clone()));
        Poll::Ready(result.result)
    }
}
impl Drop for RuntimeProvider {
    fn drop(&mut self) {
        self.drain();
    }
}

#[cfg(all(test, feature = "development-worker"))]
#[path = "adapter_author_review.rs"]
mod adapter_author_review;

#[cfg(all(test, feature = "development-worker"))]
mod tests {
    use super::*;
    use locallore::{contracts::Scope, inference::Budget};
    use std::time::Instant;
    fn request(role: &str) -> GenerationRequest {
        GenerationRequest {
            version: 1,
            scope: Scope {
                story: "synthetic-story".into(),
                branch: "root".into(),
            },
            turn: "synthetic-turn".into(),
            revision: 0,
            model_profile: PROFILE.into(),
            schema: "synthetic-schema-v1".into(),
            budget: Budget {
                max_output_bytes: 16384,
                max_output_tokens: 64,
                max_pending_polls: 1000,
                deadline_ms: 5000,
            },
            input: Input::Structured {
                role: role.into(),
                prompt: "original synthetic prompt".into(),
                schema: json!({"type":"object"}),
            },
        }
    }
    fn poll_to_ready(
        provider: &mut RuntimeProvider,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Result<Vec<u8>, Error> {
        let start = Instant::now();
        loop {
            if let Poll::Ready(result) = provider.poll(request, cancel) {
                return result;
            }
            assert!(start.elapsed() < Duration::from_secs(5));
            thread::sleep(Duration::from_millis(5));
        }
    }
    fn owner(mode: &str) -> (SharedRuntime, std::path::PathBuf) {
        let (mut runtime, dir) = crate::tests::fixture(mode);
        runtime.load(|| false).unwrap();
        (Arc::new(Mutex::new(runtime)), dir)
    }
    #[test]
    fn resource_sampling_is_opt_in_per_role_cached_and_cancellation_drains() {
        let (shared, dir) = owner("valid");
        let req = request("director");
        let cancel = Cancellation::default();
        let mut plain = RuntimeProvider::new(shared.clone());
        assert!(!plain.sample_resources);
        let expected = poll_to_ready(&mut plain, &req, &cancel);
        drop(plain);
        let log = RoleMetricsLog::new();
        let mut passive = RuntimeProvider::with_metrics(shared.clone(), log.clone());
        assert!(!passive.sample_resources);
        assert_eq!(poll_to_ready(&mut passive, &req, &cancel), expected);
        assert!(log.snapshot().records[0].resources.is_none());
        drop(passive);
        let log = RoleMetricsLog::new();
        let mut sampled = RuntimeProvider::with_resource_metrics(shared.clone(), log.clone());
        assert_eq!(poll_to_ready(&mut sampled, &req, &cancel), expected);
        assert_eq!(sampled.poll(&req, &cancel), Poll::Ready(expected));
        assert_eq!(log.snapshot().records.len(), 1);
        assert!(poll_to_ready(&mut sampled, &request("narrator"), &cancel).is_ok());
        drop(sampled);
        let snapshot = log.snapshot();
        assert_eq!(snapshot.version, 2);
        assert_eq!(snapshot.records.len(), 2);
        for record in &snapshot.records {
            let resources = record.resources.as_ref().unwrap();
            assert!(resources.successful_samples >= 1);
            assert!(resources.sampled_peak_working_set_bytes.unwrap() > 0);
            assert!(resources.sampled_peak_private_committed_bytes.unwrap() > 0);
        }
        let encoded = serde_json::to_string(&snapshot).unwrap();
        assert!(!encoded.contains("synthetic prompt"));
        assert!(!encoded.contains(dir.to_str().unwrap()));
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();

        let (shared, dir) = owner("blocked-generation");
        let log = RoleMetricsLog::new();
        let mut sampled = RuntimeProvider::with_resource_metrics(shared.clone(), log.clone());
        let cancel = Cancellation::default();
        assert!(sampled.poll(&request("director"), &cancel).is_pending());
        let started = Instant::now();
        while shared.try_lock().is_ok() {
            assert!(started.elapsed() < Duration::from_secs(5));
            thread::sleep(Duration::from_millis(5));
        }
        thread::sleep(Duration::from_millis(30));
        cancel.cancel();
        drop(sampled); // Both native cancellation cleanup and sampling are drained.
        assert!(started.elapsed() < Duration::from_secs(5));
        let snapshot = log.snapshot();
        assert_eq!(snapshot.records.len(), 1);
        assert_eq!(
            snapshot.records[0].adapter_terminal,
            AdapterTerminal::Cancelled
        );
        assert!(snapshot.records[0].drained_on_drop);
        assert!(snapshot.records[0].resources.is_some());
        assert!(shared.lock().unwrap().child.try_wait().unwrap().is_some());
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn resource_sampling_busy_admission_never_reports_prior_role_resources() {
        let (shared, dir) = owner("valid");
        let log = RoleMetricsLog::new();
        let mut provider = RuntimeProvider::with_resource_metrics(shared.clone(), log.clone());
        assert!(poll_to_ready(
            &mut provider,
            &request("director"),
            &Cancellation::default()
        )
        .is_ok());
        let held = shared.lock().unwrap();
        assert_eq!(
            poll_to_ready(
                &mut provider,
                &request("narrator"),
                &Cancellation::default()
            ),
            Err(Error::Provider)
        );
        drop(held);
        drop(provider);
        let snapshot = log.snapshot();
        assert!(snapshot.records[0].resources.is_some());
        assert_eq!(snapshot.records[1].native_terminal, NativeTerminal::NotRun);
        assert!(snapshot.records[1].resources.is_none());
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn structured_input_profile_role_and_budget_are_frozen() {
        let req = request("director");
        assert!(compile(&req).is_ok());
        let mut legacy = req.clone();
        legacy.input = Input::Narrator {
            accepted_description: "fixture".into(),
        };
        assert_eq!(compile(&legacy).err(), Some(Error::Provider));
        let mut invalid = req.clone();
        invalid.model_profile = "fake".into();
        assert_eq!(compile(&invalid).err(), Some(Error::Rule));
        let invalid = request("tool");
        assert_eq!(compile(&invalid).err(), Some(Error::Rule));
        let mut invalid = req;
        invalid.budget.max_output_tokens = 351;
        assert_eq!(compile(&invalid).err(), Some(Error::Rule));
    }
    #[test]
    fn narrator_cannot_start_a_turn_but_rejected_call_does_not_poison_director() {
        let (shared, dir) = owner("valid");
        let mut provider = RuntimeProvider::new(shared.clone());
        let cancel = Cancellation::default();
        assert_eq!(
            provider.poll(&request("narrator"), &cancel),
            Poll::Ready(Err(Error::RetryMismatch))
        );
        assert!(poll_to_ready(&mut provider, &request("director"), &cancel).is_ok());
        assert!(poll_to_ready(&mut provider, &request("narrator"), &cancel).is_ok());
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn repeated_polls_and_sequential_roles_reuse_one_owner() {
        let (shared, dir) = owner("valid");
        let mut provider = RuntimeProvider::new(shared.clone());
        let cancel = Cancellation::default();
        let director = request("director");
        let bytes = poll_to_ready(&mut provider, &director, &cancel).unwrap();
        assert_eq!(provider.poll(&director, &cancel), Poll::Ready(Ok(bytes)));
        assert!(poll_to_ready(&mut provider, &request("narrator"), &cancel).is_ok());
        let mut another = request("narrator");
        another.scope.story = "other-story".into();
        assert_eq!(
            provider.poll(&another, &cancel),
            Poll::Ready(Err(Error::RetryMismatch))
        );
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn exactly_one_completed_director_repair_then_narrator_is_permitted() {
        let (shared, dir) = owner("valid");
        let mut provider = RuntimeProvider::new(shared.clone());
        let cancel = Cancellation::default();
        let original = request("director");
        assert!(poll_to_ready(&mut provider, &original, &cancel).is_ok());
        let mut repair = original.clone();
        if let Input::Structured { prompt, .. } = &mut repair.input {
            *prompt = "bounded repair after malformed proposal".into();
        }
        assert!(poll_to_ready(&mut provider, &repair, &cancel).is_ok());
        assert_eq!(provider.directors_started, 2);
        let mut third = repair.clone();
        if let Input::Structured { prompt, .. } = &mut third.input {
            *prompt = "forbidden second repair".into();
        }
        assert_eq!(
            provider.poll(&third, &cancel),
            Poll::Ready(Err(Error::RetryMismatch))
        );
        assert!(poll_to_ready(&mut provider, &request("narrator"), &cancel).is_ok());
        assert_eq!(provider.directors_started, 2);
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn completed_director_repair_cannot_change_schema_or_scope() {
        for mutation in 0..2 {
            let (shared, dir) = owner("valid");
            let mut provider = RuntimeProvider::new(shared.clone());
            let cancel = Cancellation::default();
            let original = request("director");
            assert!(poll_to_ready(&mut provider, &original, &cancel).is_ok());
            let mut repair = original.clone();
            if let Input::Structured { prompt, schema, .. } = &mut repair.input {
                *prompt = "repair".into();
                if mutation == 0 {
                    *schema = json!({"type":"array"});
                }
            }
            if mutation == 1 {
                repair.scope.branch = "sibling".into();
            }
            assert_eq!(
                provider.poll(&repair, &cancel),
                Poll::Ready(Err(Error::RetryMismatch))
            );
            assert_eq!(provider.directors_started, 1);
            drop(provider);
            drop(shared);
            std::fs::remove_dir_all(dir).unwrap();
        }
    }
    #[test]
    fn active_identity_change_is_prompt_and_poisoned() {
        for mutation in 0..3 {
            let (shared, dir) = owner("valid");
            let mut provider = RuntimeProvider::new(shared.clone());
            let cancel = Cancellation::default();
            let original = request("director");
            assert!(provider.poll(&original, &cancel).is_pending());
            let mut changed = original.clone();
            match mutation {
                0 => changed.scope.story = "other".into(),
                1 => {
                    changed.input = Input::Structured {
                        role: "director".into(),
                        prompt: "changed".into(),
                        schema: json!({"type":"object"}),
                    }
                }
                _ => {
                    changed.input = Input::Structured {
                        role: "narrator".into(),
                        prompt: "original synthetic prompt".into(),
                        schema: json!({"type":"object"}),
                    }
                }
            }
            let start = Instant::now();
            assert_eq!(
                provider.poll(&changed, &cancel),
                Poll::Ready(Err(Error::RetryMismatch))
            );
            assert!(start.elapsed() < Duration::from_millis(50));
            assert_eq!(
                provider.poll(&original, &cancel),
                Poll::Ready(Err(Error::RetryMismatch))
            );
            drop(provider);
            drop(shared);
            std::fs::remove_dir_all(dir).unwrap();
        }
    }
    #[test]
    fn concurrent_ownership_returns_busy_without_native_call() {
        let (shared, dir) = owner("valid");
        let lock = shared.lock().unwrap();
        let mut provider = RuntimeProvider::new(shared.clone());
        let cancel = Cancellation::default();
        assert_eq!(
            poll_to_ready(&mut provider, &request("director"), &cancel),
            Err(Error::Provider)
        );
        assert_eq!(provider.last_failure(), Some(RuntimeError::Busy));
        drop(lock);
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn cancellation_poll_is_prompt_and_drop_reaps_native_owner() {
        let (shared, dir) = owner("blocked-generation-observed");
        let mut provider = RuntimeProvider::new(shared.clone());
        let cancel = Cancellation::default();
        let req = request("director");
        assert!(provider.poll(&req, &cancel).is_pending());
        // Synchronize with the synthetic child receiving generation, not a scheduler delay.
        // Cancellation before the role thread starts legitimately preserves a loaded owner.
        let marker = dir
            .join("blocked-generation-observed")
            .with_extension("generation-started");
        let waiting = Instant::now();
        while !marker.is_file() {
            assert!(waiting.elapsed() < Duration::from_secs(5));
            thread::sleep(Duration::from_millis(5));
        }
        cancel.cancel();
        let start = Instant::now();
        assert!(provider.poll(&req, &cancel).is_pending());
        assert!(start.elapsed() < Duration::from_millis(50));
        drop(provider);
        assert!(start.elapsed() < Duration::from_secs(4));
        assert_eq!(shared.lock().unwrap().status(), crate::Status::Failed);
        assert!(shared.lock().unwrap().child.try_wait().unwrap().is_some());
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn completed_role_cannot_be_reinterpreted_or_retried_as_new_turn() {
        let (shared, dir) = owner("valid");
        let mut provider = RuntimeProvider::new(shared.clone());
        let cancel = Cancellation::default();
        let req = request("director");
        assert!(poll_to_ready(&mut provider, &req, &cancel).is_ok());
        let mut changed = req.clone();
        changed.turn = "other-turn".into();
        assert_eq!(
            provider.poll(&changed, &cancel),
            Poll::Ready(Err(Error::RetryMismatch))
        );
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn role_metrics_order_repair_identity_and_cached_polls_are_bounded() {
        let (shared, dir) = owner("valid");
        let log = RoleMetricsLog::new();
        let mut provider = RuntimeProvider::with_metrics(shared.clone(), log.clone());
        let cancel = Cancellation::default();
        let director = request("director");
        let original_digest = digest(&compile(&director).unwrap().identity.full);
        let first = poll_to_ready(&mut provider, &director, &cancel).unwrap();
        assert_eq!(provider.poll(&director, &cancel), Poll::Ready(Ok(first)));
        let mut repair = director.clone();
        if let Input::Structured { prompt, .. } = &mut repair.input {
            *prompt = "one synthetic repair".into();
        }
        assert!(poll_to_ready(&mut provider, &repair, &cancel).is_ok());
        let mut wrong = repair.clone();
        wrong.scope.branch = "other".into();
        assert_eq!(
            provider.poll(&wrong, &cancel),
            Poll::Ready(Err(Error::RetryMismatch))
        );
        assert!(poll_to_ready(&mut provider, &request("narrator"), &cancel).is_ok());
        drop(provider);
        let snapshot = log.snapshot();
        assert!(snapshot.available && !snapshot.incomplete);
        assert_eq!(snapshot.records.len(), 3);
        assert_eq!(snapshot.records[0].request_sha256, original_digest);
        for (index, record) in snapshot.records.iter().enumerate() {
            assert_eq!(record.ordinal as usize, index);
            assert_eq!(record.director_attempt, (index < 2).then_some(index as u8));
            assert_eq!(
                record.role,
                if index < 2 {
                    MetricRole::Director
                } else {
                    MetricRole::Narrator
                }
            );
            assert_eq!(record.adapter_terminal, AdapterTerminal::Completed);
            assert_eq!(record.native_terminal, NativeTerminal::Completed);
            assert!(record.worker_metrics.is_some());
            assert!(!record.drained_on_drop);
        }
        let encoded = serde_json::to_string(&snapshot).unwrap();
        for private in [
            "synthetic-story",
            "synthetic-turn",
            "original synthetic prompt",
            "one synthetic repair",
        ] {
            assert!(!encoded.contains(private));
        }
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn role_metrics_busy_and_unavailable_never_reuse_prior_metrics() {
        let (shared, dir) = owner("valid");
        let cancel = Cancellation::default();
        let busy_log = RoleMetricsLog::new();
        let held = shared.lock().unwrap();
        let mut busy = RuntimeProvider::with_metrics(shared.clone(), busy_log.clone());
        assert_eq!(
            poll_to_ready(&mut busy, &request("director"), &cancel),
            Err(Error::Provider)
        );
        drop(held);
        drop(busy);
        let record = busy_log.snapshot().records.remove(0);
        assert_eq!(record.native_terminal, NativeTerminal::NotRun);
        assert_eq!(record.native_error, Some(RuntimeError::Busy));
        assert!(record.worker_metrics.is_none());
        let log = RoleMetricsLog::new();
        let mut provider = RuntimeProvider::with_metrics(shared.clone(), log.clone());
        assert!(poll_to_ready(&mut provider, &request("director"), &cancel).is_ok());
        let _ = shared.lock().unwrap().fail::<()>(RuntimeError::Runtime);
        assert_eq!(
            poll_to_ready(&mut provider, &request("narrator"), &cancel),
            Err(Error::Provider)
        );
        let snapshot = log.snapshot();
        assert!(snapshot.records[0].worker_metrics.is_some());
        assert!(snapshot.records[1].worker_metrics.is_none());
        assert_eq!(snapshot.records[1].native_terminal, NativeTerminal::Failed);
        assert_eq!(
            snapshot.records[1].native_error,
            Some(RuntimeError::WorkerUnavailable)
        );
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }

    fn await_generation(dir: &std::path::Path) {
        let marker = dir
            .join("blocked-generation-observed")
            .with_extension("generation-started");
        let start = Instant::now();
        while !marker.is_file() {
            assert!(start.elapsed() < Duration::from_secs(5));
            thread::sleep(Duration::from_millis(5));
        }
    }

    #[test]
    fn role_metrics_cancel_drop_and_active_identity_keep_original_attempt() {
        for variant in 0..3 {
            let changed_identity = variant == 1;
            let (shared, dir) = owner("blocked-generation-observed");
            let log = RoleMetricsLog::new();
            let mut provider = RuntimeProvider::with_metrics(shared.clone(), log.clone());
            let cancel = Cancellation::default();
            let original = request("director");
            assert!(provider.poll(&original, &cancel).is_pending());
            await_generation(&dir);
            if changed_identity {
                let mut changed = original.clone();
                changed.scope.story = "foreign".into();
                assert_eq!(
                    provider.poll(&changed, &cancel),
                    Poll::Ready(Err(Error::RetryMismatch))
                );
            } else {
                cancel.cancel();
                if variant == 0 {
                    assert!(provider.poll(&original, &cancel).is_pending());
                }
            }
            drop(provider);
            let snapshot = log.snapshot();
            assert_eq!(snapshot.records.len(), 1);
            let record = &snapshot.records[0];
            assert_eq!(
                record.request_sha256,
                digest(&compile(&original).unwrap().identity.full)
            );
            assert_eq!(
                record.adapter_terminal,
                if changed_identity {
                    AdapterTerminal::Failed
                } else {
                    AdapterTerminal::Cancelled
                }
            );
            assert_eq!(
                record.adapter_error,
                Some(if changed_identity {
                    AdapterError::RetryMismatch
                } else {
                    AdapterError::Cancelled
                })
            );
            assert!(record.drained_on_drop);
            assert!(record.worker_metrics.is_none());
            assert!(shared.lock().unwrap().child.try_wait().unwrap().is_some());
            drop(shared);
            std::fs::remove_dir_all(dir).unwrap();
        }
    }

    #[test]
    fn role_metrics_distinguish_native_completion_from_late_cancel_and_drop() {
        for late_cancel in [false, true] {
            let (shared, dir) = owner("valid");
            let log = RoleMetricsLog::new();
            let mut provider = RuntimeProvider::with_metrics(shared.clone(), log.clone());
            let cancel = Cancellation::default();
            let req = request("director");
            // Enter the production admission helper without receiving its terminal channel yet.
            let call = compile(&req).unwrap();
            provider.directors_started = 1;
            provider.start(call, &req, cancel.clone()).unwrap();
            let start = Instant::now();
            while !provider
                .active
                .as_ref()
                .unwrap()
                .thread
                .as_ref()
                .unwrap()
                .is_finished()
            {
                assert!(start.elapsed() < Duration::from_secs(5));
                thread::sleep(Duration::from_millis(5));
            }
            if late_cancel {
                cancel.cancel();
                assert_eq!(
                    provider.poll(&req, &cancel),
                    Poll::Ready(Err(Error::Cancelled))
                );
            }
            drop(provider);
            let record = log.snapshot().records.remove(0);
            assert_eq!(record.native_terminal, NativeTerminal::Completed);
            assert!(record.worker_metrics.is_some());
            assert_eq!(
                record.adapter_terminal,
                if late_cancel {
                    AdapterTerminal::Cancelled
                } else {
                    AdapterTerminal::Dropped
                }
            );
            assert_eq!(record.drained_on_drop, !late_cancel);
            drop(shared);
            std::fs::remove_dir_all(dir).unwrap();
        }
    }

    #[test]
    fn role_metrics_timeout_is_not_a_completed_zero_metric_sample() {
        let (shared, dir) = owner("valid");
        let log = RoleMetricsLog::new();
        let mut provider = RuntimeProvider::with_metrics(shared.clone(), log.clone());
        let mut req = request("director");
        req.budget.deadline_ms = 20;
        // Reuse the native client's existing test-only delayed-terminal hook on the role thread.
        crate::AFTER_REPLY_DELAY.with(|delay| delay.set(Some(Duration::from_millis(40))));
        assert_eq!(
            poll_to_ready(&mut provider, &req, &Cancellation::default()),
            Err(Error::Timeout)
        );
        let record = log.snapshot().records.remove(0);
        assert_eq!(record.adapter_terminal, AdapterTerminal::Timeout);
        assert_eq!(record.native_terminal, NativeTerminal::Timeout);
        assert!(record.worker_metrics.is_none());
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn role_metrics_unacknowledged_deadline_is_cleanup_failure_not_fake_timeout() {
        let (shared, dir) = owner("blocked-generation");
        let log = RoleMetricsLog::new();
        let mut provider = RuntimeProvider::with_metrics(shared.clone(), log.clone());
        let mut req = request("director");
        req.budget.deadline_ms = 40;
        assert_eq!(
            poll_to_ready(&mut provider, &req, &Cancellation::default()),
            Err(Error::Provider)
        );
        let record = log.snapshot().records.remove(0);
        assert_eq!(record.adapter_terminal, AdapterTerminal::Failed);
        assert_eq!(record.native_error, Some(RuntimeError::Cleanup));
        assert!(record.worker_metrics.is_none());
        assert!(shared.lock().unwrap().child.try_wait().unwrap().is_some());
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn disabled_enabled_and_poisoned_recorders_preserve_actual_pipeline_failure_and_canon() {
        use locallore::{
            contracts::{Intent, PlayInputKind, Seed},
            engine::Engine,
            play::{self, PlayProfile},
        };
        let seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let profile = PlayProfile {
            id: PROFILE.into(),
            model_sha256: crate::MODEL_SHA256.into(),
            runtime_revision: crate::RUNTIME_COMMIT.into(),
            template_sha256: "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361"
                .into(),
            worker_sha256: "0".repeat(64),
            profile_manifest_sha256: "0".repeat(64),
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 350,
            deadline_ms: 120_000,
            repair_limit: 1,
        };
        let (shared, dir) = owner("valid");
        let clean = RoleMetricsLog::new();
        let poisoned = RoleMetricsLog::new();
        poisoned.poison_for_test();
        let mut expected = None;
        for (log, resources) in [
            (None, false),
            (Some(clean.clone()), false),
            (Some(poisoned.clone()), false),
            (Some(RoleMetricsLog::new()), true),
        ] {
            let mut engine = Engine::new(seed.clone()).unwrap();
            let before = engine.canonical_bytes();
            let req = engine.request(
                "synthetic-metrics-golden",
                Intent::FreeText {
                    kind: PlayInputKind::Action,
                    text: "I give my last potion to Mira.".into(),
                },
            );
            let mut provider = match log {
                None => RuntimeProvider::new(shared.clone()),
                Some(log) if resources => {
                    RuntimeProvider::with_resource_metrics(shared.clone(), log)
                }
                Some(log) => RuntimeProvider::with_metrics(shared.clone(), log),
            };
            // Actual synthetic process returns empty text; the production parser/one repair rejects it.
            let result = play::execute(
                &mut engine,
                &req,
                &mut provider,
                &Cancellation::default(),
                &profile,
            )
            .err();
            assert!(result.is_some());
            assert_eq!(provider.directors_started, 2);
            if let Some(expected) = &expected {
                assert_eq!(&result, expected);
            } else {
                expected = Some(result);
            }
            drop(provider);
            assert_eq!(before, engine.canonical_bytes());
        }
        assert_eq!(clean.snapshot().records.len(), 2);
        assert!(!poisoned.snapshot().available);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn recorder_disabled_full_poison_and_foreign_turn_do_not_change_results() {
        let (shared, dir) = owner("valid");
        let cancel = Cancellation::default();
        let mut disabled = RuntimeProvider::new(shared.clone());
        assert!(disabled.log.is_none());
        let expected = poll_to_ready(&mut disabled, &request("director"), &cancel);
        drop(disabled);
        let full = RoleMetricsLog::new();
        let mut filled = RuntimeProvider::with_metrics(shared.clone(), full.clone());
        let director = request("director");
        assert_eq!(poll_to_ready(&mut filled, &director, &cancel), expected);
        let mut repair = director.clone();
        if let Input::Structured { prompt, .. } = &mut repair.input {
            *prompt = "repair".into();
        }
        assert_eq!(poll_to_ready(&mut filled, &repair, &cancel), expected);
        assert_eq!(
            poll_to_ready(&mut filled, &request("narrator"), &cancel),
            expected
        );
        drop(filled);
        let poisoned = RoleMetricsLog::new();
        poisoned.poison_for_test();
        for log in [full.clone(), poisoned.clone()] {
            let mut provider = RuntimeProvider::with_metrics(shared.clone(), log);
            assert_eq!(poll_to_ready(&mut provider, &director, &cancel), expected);
        }
        assert_eq!(full.snapshot().records.len(), 3);
        assert!(full.snapshot().incomplete);
        assert!(!poisoned.snapshot().available);
        let scoped = RoleMetricsLog::new();
        let mut provider = RuntimeProvider::with_metrics(shared.clone(), scoped.clone());
        assert_eq!(poll_to_ready(&mut provider, &director, &cancel), expected);
        drop(provider);
        let mut foreign = director;
        foreign.turn = "other-turn".into();
        let mut provider = RuntimeProvider::with_metrics(shared.clone(), scoped.clone());
        assert_eq!(poll_to_ready(&mut provider, &foreign, &cancel), expected);
        assert_eq!(scoped.snapshot().records.len(), 1);
        assert!(scoped.snapshot().incomplete);
        drop(provider);
        drop(shared);
        std::fs::remove_dir_all(dir).unwrap();
    }
}
