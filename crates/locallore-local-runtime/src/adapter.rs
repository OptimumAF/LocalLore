// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Optional shared-engine provider. This adapter never validates or commits canonical outcomes.
use crate::{Error as RuntimeError, Generation, LocalRuntime, Metrics, Role, PROFILE};
use locallore::{
    contracts::Error,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
};
use serde_json::json;
use std::{
    sync::{mpsc, Arc, Mutex, TryLockError},
    task::Poll,
    thread::{self, JoinHandle},
    time::Duration,
};

pub type SharedRuntime = Arc<Mutex<LocalRuntime>>;

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
fn compile(request: &GenerationRequest) -> Result<(Identity, Generation), Error> {
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
    Ok((
        Identity {
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
        Generation {
            role: native_role,
            prompt: prompt.clone(),
            schema: Some(schema.clone()),
            max_tokens: request.budget.max_output_tokens as u16,
        },
    ))
}

type Outcome = (
    Result<Vec<u8>, Error>,
    Option<Metrics>,
    Option<RuntimeError>,
);
struct Job {
    identity: Identity,
    cancel: Cancellation,
    receiver: mpsc::Receiver<Outcome>,
    thread: Option<JoinHandle<()>>,
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
        }
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
                    let mut owner = self
                        .runtime
                        .lock()
                        .unwrap_or_else(|poisoned| poisoned.into_inner());
                    let _ = owner.fail::<()>(RuntimeError::Cleanup);
                    return;
                }
            }
            if let Ok((_, metrics, failure)) = job.receiver.try_recv() {
                self.metrics = metrics;
                self.failure = failure;
            }
        }
    }
    fn start(
        &mut self,
        identity: Identity,
        generation: Generation,
        request: &GenerationRequest,
        external: Cancellation,
    ) -> Result<(), Error> {
        self.metrics = None;
        self.failure = None;
        let runtime = self.runtime.clone();
        let local = Cancellation::default();
        let cancel = local.clone();
        let deadline = Duration::from_millis(request.budget.deadline_ms.min(60_000));
        let bytes = request.budget.max_output_bytes;
        let (sender, receiver) = mpsc::sync_channel(1);
        let worker = thread::Builder::new()
            .name("locallore-local-role".into())
            .spawn(move || {
                let mut guard = match runtime.try_lock() {
                    Ok(g) => g,
                    Err(TryLockError::WouldBlock) => {
                        let _ = sender.send((Err(Error::Provider), None, Some(RuntimeError::Busy)));
                        return;
                    }
                    Err(TryLockError::Poisoned(_)) => {
                        let _ =
                            sender.send((Err(Error::Provider), None, Some(RuntimeError::Cleanup)));
                        return;
                    }
                };
                if local.is_cancelled() || external.is_cancelled() {
                    let _ =
                        sender.send((Err(Error::Cancelled), None, Some(RuntimeError::Cancelled)));
                    return;
                }
                let previous = guard.deadline;
                guard.deadline = deadline;
                let result = guard.generate(generation, || {
                    local.is_cancelled() || external.is_cancelled()
                });
                guard.deadline = previous;
                let metrics = guard.last_metrics().cloned();
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
                let _ = sender.send((result, metrics, failure));
            })
            .map_err(|_| Error::Provider)?;
        self.active = Some(Job {
            identity,
            cancel,
            receiver,
            thread: Some(worker),
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
        let (identity, generation) = match compile(request) {
            Ok(value) => value,
            Err(error) => {
                self.metrics = None;
                self.failure = None;
                if let Some(job) = &self.active {
                    job.cancel.cancel();
                    self.poisoned = true;
                }
                return Poll::Ready(Err(error));
            }
        };
        if let Some(job) = &self.active {
            if job.identity != identity {
                self.metrics = None;
                job.cancel.cancel();
                self.poisoned = true;
                return Poll::Ready(Err(Error::RetryMismatch));
            }
        }
        if cancel.is_cancelled() {
            self.metrics = None;
            if let Some(job) = &self.active {
                job.cancel.cancel();
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
                if identity == *previous {
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
            if let Err(error) = self.start(identity, generation, request, cancel.clone()) {
                return Poll::Ready(Err(error));
            }
        }
        let mut result = match self.active.as_ref().unwrap().receiver.try_recv() {
            Ok(result) => result,
            Err(mpsc::TryRecvError::Empty) => return Poll::Pending,
            Err(mpsc::TryRecvError::Disconnected) => {
                (Err(Error::Provider), None, Some(RuntimeError::Cleanup))
            }
        };
        let mut job = self.active.take().unwrap();
        if let Some(thread) = job.thread.take() {
            if thread.join().is_err() {
                self.failure = Some(RuntimeError::Cleanup);
                self.poisoned = true;
                let mut owner = self
                    .runtime
                    .lock()
                    .unwrap_or_else(|poisoned| poisoned.into_inner());
                let _ = owner.fail::<()>(RuntimeError::Cleanup);
                return Poll::Ready(Err(Error::Provider));
            }
        }
        self.metrics = result.1;
        self.failure = result.2;
        if cancel.is_cancelled() {
            result.0 = Err(Error::Cancelled);
        }
        self.completed = Some((job.identity, result.0.clone()));
        Poll::Ready(result.0)
    }
}
impl Drop for RuntimeProvider {
    fn drop(&mut self) {
        self.drain();
    }
}

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
        let (shared, dir) = owner("blocked-generation");
        let mut provider = RuntimeProvider::new(shared.clone());
        let cancel = Cancellation::default();
        let req = request("director");
        assert!(provider.poll(&req, &cancel).is_pending());
        thread::sleep(Duration::from_millis(30));
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
}
