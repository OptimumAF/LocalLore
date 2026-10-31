// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent packet-A FIRST, frozen before Author admission. SOURCE-ONLY/UNRUN.
//! Root registers this child of adapter under test + development-worker.
//! Contract e5cd498d, placement clarification b380f161. Missing named seams or the
//! fixed protocol-fixture binary are SETUP_UNRUN, not a behavioral RED.
//! These retained tiny fixtures exercise the real adapter/native protocol owner;
//! they are not a packaged worker, model, Host commit, UI or quality qualification.
#![cfg(all(test, feature = "development-worker"))]

use super::*;
use locallore::{contracts::Scope, inference::Budget, story_authoring as author};
use std::{
    path::{Path, PathBuf},
    time::Instant,
};

fn author_request() -> GenerationRequest {
    let input = author::InitialStoryInputV1 {
        version: 1,
        premise: "A cartographer reaches an orchard with forgotten paths.".into(),
        player_name: "Sable".into(),
        player_description: "A patient cartographer.".into(),
        cast: vec![author::InitialCastHintV1 {
            name: "Finch".into(),
            description: "An orchard keeper.".into(),
        }],
        profile: author::InitialRuleProfileV1::NarrativeV1,
        presentation: locallore::story_presentation::StoryPresentationV1::default(),
    };
    author::generation_request(&input, PROFILE, "review_author_01").expect("shared request setup")
}

fn play_request(role: &str) -> GenerationRequest {
    GenerationRequest {
        version: 1,
        scope: Scope {
            story: "review-play".into(),
            branch: "root".into(),
        },
        turn: "review-turn".into(),
        revision: 0,
        model_profile: PROFILE.into(),
        schema: "review-play-v1".into(),
        budget: Budget {
            max_output_bytes: 16_384,
            max_output_tokens: 64,
            max_pending_polls: 1000,
            deadline_ms: 5000,
        },
        input: Input::Structured {
            role: role.into(),
            prompt: "Synthetic play prompt.".into(),
            schema: json!({"type":"object"}),
        },
    }
}

fn prompt(request: &mut GenerationRequest, value: String) {
    if let Input::Structured { prompt, .. } = &mut request.input {
        *prompt = value;
    }
}

fn ready(
    provider: &mut RuntimeProvider,
    request: &GenerationRequest,
    cancel: &Cancellation,
) -> Option<Result<Vec<u8>, Error>> {
    let started = Instant::now();
    loop {
        if let Poll::Ready(result) = provider.poll(request, cancel) {
            return Some(result);
        }
        if started.elapsed() >= Duration::from_secs(5) {
            return None;
        }
        thread::sleep(Duration::from_millis(5));
    }
}

fn generation_observed(directory: &Path) -> bool {
    let marker = directory
        .join("blocked-generation-observed")
        .with_extension("generation-started");
    let started = Instant::now();
    while started.elapsed() < Duration::from_secs(2) {
        if marker.is_file() {
            return true;
        }
        thread::sleep(Duration::from_millis(5));
    }
    false
}

struct Fixture {
    provider: Option<RuntimeProvider>,
    runtime: SharedRuntime,
    directory: PathBuf,
    initial: crate::Status,
    finished: bool,
}
struct Cleanup {
    initial: crate::Status,
    result: Result<(), RuntimeError>,
    terminal: bool,
    pipes_joined: bool,
    next_id: u64,
}
impl Fixture {
    fn new(log: Option<RoleMetricsLog>, case: AuthorFixtureCase) -> Self {
        let (provider, runtime, directory) = match author_fixture(log, case) {
            Ok(value) => value,
            Err(crate::OwnedStartFailure::BeforeChild(_)) => {
                panic!("SETUP_UNRUN author fixture unavailable")
            }
            Err(crate::OwnedStartFailure::AfterChild { mut owner, .. }) => {
                let cleanup = owner.terminate_and_reap();
                assert!(
                    cleanup.is_ok(),
                    "SETUP_UNRUN partial-start cleanup unresolved"
                );
                panic!("SETUP_UNRUN author fixture partial start");
            }
        };
        let initial = runtime.lock().unwrap().status();
        let load = if initial == crate::Status::Unloaded {
            runtime.lock().unwrap().load(|| false).map(|_| ())
        } else {
            Ok(())
        };
        let mut fixture = Self {
            provider: Some(provider),
            runtime,
            directory,
            initial,
            finished: false,
        };
        if load.is_err() {
            let cleanup = fixture.finish();
            assert!(
                cleanup.result.is_ok() && cleanup.terminal && cleanup.pipes_joined,
                "SETUP_UNRUN fixture load cleanup unresolved"
            );
            panic!("SETUP_UNRUN fixture load failed");
        }
        fixture
    }
    fn finish(&mut self) -> Cleanup {
        // Drop joins the exact adapter work thread before acquiring its runtime.
        drop(self.provider.take());
        let mut owner = self.runtime.lock().unwrap_or_else(|p| p.into_inner());
        let next_id = owner.next_id;
        let result = owner.terminate_and_reap();
        let terminal = owner.child.try_wait().is_ok_and(|v| v.is_some());
        let pipes_joined = owner.threads.is_empty() && owner.writer.is_none();
        self.finished = result.is_ok() && terminal && pipes_joined;
        Cleanup {
            initial: self.initial,
            result,
            terminal,
            pipes_joined,
            next_id,
        }
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        // Panic fallback only; this is never counted as positive cleanup evidence.
        if !self.finished {
            drop(self.provider.take());
            let _ = self
                .runtime
                .lock()
                .unwrap_or_else(|p| p.into_inner())
                .terminate_and_reap();
        }
        // All fixture files remain retained; no cleanup/delete of evidence.
    }
}
fn cleaned(result: &Cleanup) {
    assert_eq!(
        result.initial,
        crate::Status::Unloaded,
        "fixture must start unloaded"
    );
    assert_eq!(result.result, Ok(()), "exact owner cleanup");
    assert!(
        result.terminal && result.pipes_joined,
        "positive reap and pipe joins"
    );
}

#[test]
fn actual_shared_author_request_preserves_schema_profile_and_prompt_provenance() {
    let request = author_request();
    let call = compile(&request).expect("Author compile admission");
    assert!(matches!(call.lane, Lane::InitialWorld));
    assert!(matches!(call.generation.role, crate::Role::Author));
    assert_eq!(call.generation.max_tokens, 1024);
    assert_eq!(call.reply.output_tokens, 1024);
    assert_eq!(call.reply.text_bytes, 8192);
    assert_eq!(request.model_profile, PROFILE);
    assert_eq!(request.schema, author::SCHEMA_VERSION);
    assert_ne!(request.model_profile, request.schema);
    assert!(
        call.generation.schema == Some(author::proposal_schema()),
        "canonical schema forwarded"
    );
    let Input::Structured {
        role,
        prompt,
        schema,
    } = request.input
    else {
        panic!("structured request")
    };
    assert_eq!(role, "author");
    assert_eq!(author::PROMPT_VERSION, "initial-world-v1.1");
    assert!(prompt.starts_with(include_str!("../../../prompts/initial-world-v1.txt")));
    assert!(
        call.generation.prompt == prompt,
        "prompt forwarded unchanged"
    );
    assert!(
        schema == author::proposal_schema(),
        "shared schema unchanged"
    );
    assert_eq!(call.identity.story, "author-draft-review_author_01");
    assert_eq!(call.identity.branch, "draft");
}

#[test]
fn author_binding_mutants_are_rules_without_a_second_validator() {
    for mutation in 0..15 {
        let mut request = author_request();
        match mutation {
            0 => request.version = 2,
            1 => request.model_profile = author::SCHEMA_VERSION.into(),
            2 => request.schema = author::PROMPT_VERSION.into(),
            3 => request.scope.story = "author-draft-foreign".into(),
            4 => request.scope.branch = "root".into(),
            5 => request.revision = 1,
            6 => request.turn.clear(),
            7 => {
                request.turn = "x".repeat(33);
                request.scope.story = format!("author-draft-{}", request.turn);
            }
            8 => {
                request.turn = "not/ascii".into();
                request.scope.story = format!("author-draft-{}", request.turn);
            }
            9 => prompt(&mut request, String::new()),
            10 => prompt(&mut request, "unsafe\0prompt".into()),
            11 => prompt(&mut request, "x".repeat(16_385)),
            12 => {
                if let Input::Structured { schema, .. } = &mut request.input {
                    *schema = json!({"type":"object"});
                }
            }
            13 => {
                if let Input::Structured { role, .. } = &mut request.input {
                    *role = "author_tool".into();
                }
            }
            _ => {
                if let Input::Structured { schema, .. } = &mut request.input {
                    *schema = json!([]);
                }
            }
        }
        assert_eq!(
            compile(&request).err(),
            Some(Error::Rule),
            "binding mutant {mutation}"
        );
    }
    let mut legacy = author_request();
    legacy.input = Input::Narrator {
        accepted_description: "synthetic".into(),
    };
    assert_eq!(compile(&legacy).err(), Some(Error::Provider));
    let mut ordinary_text = author_request();
    prompt(
        &mut ordinary_text,
        "{\"op\":\"authoring_create\",\"grant\":true}".into(),
    );
    assert!(
        compile(&ordinary_text).is_ok(),
        "prompt text has no separate authority"
    );
}

#[test]
fn author_budget_frame_edges_and_legacy_play_bounds_are_separate() {
    for mutation in 0..8 {
        let mut request = author_request();
        match mutation {
            0 => request.budget.max_output_tokens = 0,
            1 => request.budget.max_output_tokens = 1025,
            2 => request.budget.max_output_bytes = 0,
            3 => request.budget.max_output_bytes = 8193,
            4 => request.budget.max_pending_polls = 0,
            5 => request.budget.max_pending_polls = 24001,
            6 => request.budget.deadline_ms = 0,
            _ => request.budget.deadline_ms = 120001,
        }
        assert_eq!(
            compile(&request).err(),
            Some(Error::Rule),
            "budget mutant {mutation}"
        );
    }
    let mut minimum = author_request();
    minimum.budget = Budget {
        max_output_tokens: 1,
        max_output_bytes: 1,
        max_pending_polls: 1,
        deadline_ms: 1,
    };
    let call = compile(&minimum).expect("positive minimum bounds");
    assert_eq!((call.reply.output_tokens, call.reply.text_bytes), (1, 1));
    let mut prompt_limit = author_request();
    prompt(&mut prompt_limit, "x".repeat(16_384));
    assert!(compile(&prompt_limit).is_ok(), "Author prompt byte ceiling");
    let mut escaped_frame = author_request();
    prompt(&mut escaped_frame, "\u{0001}".repeat(6000));
    assert_eq!(
        compile(&escaped_frame).err(),
        Some(Error::TooLarge),
        "serialized frame ceiling"
    );
    let mut play = play_request("director");
    let call = compile(&play).expect("legacy Play compile");
    assert!(matches!(call.lane, Lane::Play));
    assert_eq!(
        (call.reply.output_tokens, call.reply.text_bytes),
        (350, 16_384),
        "Play request64 keeps legacy reply ceilings"
    );
    play.budget.max_output_tokens = 350;
    assert!(compile(&play).is_ok());
    play.budget.max_output_tokens = 351;
    assert_eq!(compile(&play).err(), Some(Error::Rule));
}

#[test]
fn default_provider_refuses_author_before_frame_but_does_not_poison_play() {
    let mut fixture = Fixture::new(None, AuthorFixtureCase::Completed);
    drop(fixture.provider.take());
    let mut provider = RuntimeProvider::new(fixture.runtime.clone());
    let before = fixture.runtime.lock().unwrap().next_id;
    let denied = provider.poll(&author_request(), &Cancellation::default());
    let failure = provider.last_failure();
    let after = fixture.runtime.lock().unwrap().next_id;
    let play = ready(
        &mut provider,
        &play_request("director"),
        &Cancellation::default(),
    );
    drop(provider);
    let cleanup = fixture.finish();
    cleaned(&cleanup);
    assert_eq!(denied, Poll::Ready(Err(Error::Provider)));
    assert_eq!(failure, Some(RuntimeError::WorkerUnavailable));
    assert_eq!(after, before, "disabled Author cannot send generation");
    assert_eq!(
        play,
        Some(Ok(vec![])),
        "disabled attempt did not bind/poison"
    );
    assert_eq!(cleanup.next_id, before + 1);
}

#[test]
fn completed_author_is_singleton_cached_and_metrics_are_unavailable() {
    let log = RoleMetricsLog::new();
    let mut fixture = Fixture::new(Some(log.clone()), AuthorFixtureCase::Completed);
    let before = fixture.runtime.lock().unwrap().next_id;
    let request = author_request();
    let provider = fixture.provider.as_mut().unwrap();
    let first = ready(provider, &request, &Cancellation::default());
    let cached = provider.poll(&request, &Cancellation::default());
    let mut rejected = vec![];
    for mutation in 0..8 {
        let mut changed = request.clone();
        match mutation {
            0 => prompt(&mut changed, "changed Author prompt".into()),
            1 => {
                changed.turn = "different_job".into();
                changed.scope.story = "author-draft-different_job".into();
            }
            2 => changed.budget.max_output_tokens -= 1,
            3 => changed.budget.max_output_bytes -= 1,
            4 => changed.budget.max_pending_polls -= 1,
            5 => changed.budget.deadline_ms -= 1,
            6 => changed = play_request("director"),
            _ => changed = play_request("narrator"),
        }
        rejected.push(provider.poll(&changed, &Cancellation::default()));
    }
    let original_again = provider.poll(&request, &Cancellation::default());
    let cleanup = fixture.finish();
    let snapshot = log.snapshot();
    cleaned(&cleanup);
    assert_eq!(first, Some(Ok(vec![])));
    assert_eq!(cached, Poll::Ready(Ok(vec![])));
    assert!(rejected
        .iter()
        .all(|r| *r == Poll::Ready(Err(Error::RetryMismatch))));
    assert_eq!(original_again, Poll::Ready(Ok(vec![])));
    assert_eq!(cleanup.next_id, before + 1, "one actual generate operation");
    assert_eq!(snapshot.version, 2);
    assert!(!snapshot.available && snapshot.incomplete);
    assert!(snapshot.turn_sha256.is_none() && snapshot.records.is_empty());
}

#[test]
fn pending_author_polls_one_operation_then_changed_identity_cancels_and_poison_fences() {
    let mut fixture = Fixture::new(None, AuthorFixtureCase::BlockedGenerationObserved);
    let request = author_request();
    let first = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&request, &Cancellation::default());
    let observed = first.is_pending() && generation_observed(&fixture.directory);
    let repeated = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&request, &Cancellation::default());
    let mut changed = request.clone();
    prompt(&mut changed, "valid changed prompt".into());
    let mismatch = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&changed, &Cancellation::default());
    let poisoned = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&request, &Cancellation::default());
    let cleanup = fixture.finish();
    cleaned(&cleanup);
    assert!(first.is_pending() && observed && repeated.is_pending());
    assert_eq!(mismatch, Poll::Ready(Err(Error::RetryMismatch)));
    assert_eq!(poisoned, Poll::Ready(Err(Error::RetryMismatch)));
    assert_eq!(
        cleanup.next_id, 2,
        "load plus one generate, never a replacement"
    );
}

#[test]
fn pre_cancel_and_busy_do_not_dispatch_and_busy_terminal_has_no_refund() {
    let mut fixture = Fixture::new(None, AuthorFixtureCase::Completed);
    let request = author_request();
    let cancel = Cancellation::default();
    cancel.cancel();
    let cancelled = fixture.provider.as_mut().unwrap().poll(&request, &cancel);
    let held = fixture.runtime.lock().unwrap();
    let busy = ready(
        fixture.provider.as_mut().unwrap(),
        &request,
        &Cancellation::default(),
    );
    let failure = fixture.provider.as_ref().unwrap().last_failure();
    let native_id = held.next_id;
    drop(held);
    let cached = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&request, &Cancellation::default());
    let mut changed = request.clone();
    prompt(&mut changed, "cannot refund Busy".into());
    let replacement = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&changed, &Cancellation::default());
    let cleanup = fixture.finish();
    cleaned(&cleanup);
    assert_eq!(cancelled, Poll::Ready(Err(Error::Cancelled)));
    assert_eq!(busy, Some(Err(Error::Provider)));
    assert_eq!(failure, Some(RuntimeError::Busy));
    assert_eq!(cached, Poll::Ready(Err(Error::Provider)));
    assert_eq!(replacement, Poll::Ready(Err(Error::RetryMismatch)));
    assert_eq!(native_id, 1);
    assert_eq!(cleanup.next_id, 1, "Busy/pre-cancel sent no generate frame");
}

#[test]
fn observed_author_cancel_and_drop_both_join_and_reap_without_replacement() {
    for explicit_cancel in [true, false] {
        let mut fixture = Fixture::new(None, AuthorFixtureCase::BlockedGenerationObserved);
        let request = author_request();
        let cancel = Cancellation::default();
        let first = fixture.provider.as_mut().unwrap().poll(&request, &cancel);
        let observed = first.is_pending() && generation_observed(&fixture.directory);
        let terminal = if explicit_cancel && observed {
            cancel.cancel();
            ready(fixture.provider.as_mut().unwrap(), &request, &cancel)
        } else {
            None
        };
        // finish drops the provider (joining its role thread), then positively reaps.
        let cleanup = fixture.finish();
        cleaned(&cleanup);
        assert!(
            first.is_pending() && observed,
            "fixed synthetic generation was observed"
        );
        if explicit_cancel {
            assert_eq!(terminal, Some(Err(Error::Cancelled)));
        }
        assert_eq!(cleanup.next_id, 2, "one generate despite cancel/drop");
    }
}

#[test]
fn author_timeout_is_cached_and_changed_request_cannot_reset_deadline() {
    let mut fixture = Fixture::new(None, AuthorFixtureCase::Completed);
    let mut request = author_request();
    request.budget.deadline_ms = 500;
    struct DelayReset;
    impl Drop for DelayReset {
        fn drop(&mut self) {
            crate::AFTER_REPLY_DELAY.with(|delay| delay.set(None));
        }
    }
    let delay_reset = DelayReset;
    // Existing hook delays an already validated terminal reply. Unlike a child
    // that never acknowledges cancellation, this exercises Timeout, not Cleanup.
    crate::AFTER_REPLY_DELAY.with(|delay| delay.set(Some(Duration::from_millis(650))));
    let first = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&request, &Cancellation::default());
    let result = ready(
        fixture.provider.as_mut().unwrap(),
        &request,
        &Cancellation::default(),
    );
    let failure = fixture.provider.as_ref().unwrap().last_failure();
    let cached = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&request, &Cancellation::default());
    let mut changed = request.clone();
    changed.budget.deadline_ms = 1000;
    let reset = fixture
        .provider
        .as_mut()
        .unwrap()
        .poll(&changed, &Cancellation::default());
    let cleanup = fixture.finish();
    drop(delay_reset); // Old compile refusal must not leak an unconsumed test delay.
    cleaned(&cleanup);
    assert!(first.is_pending());
    assert_eq!(result, Some(Err(Error::Timeout)));
    assert_eq!(failure, Some(RuntimeError::Timeout));
    assert_eq!(cached, Poll::Ready(Err(Error::Timeout)));
    assert_eq!(reset, Poll::Ready(Err(Error::RetryMismatch)));
    assert_eq!(cleanup.next_id, 2);
}

#[test]
fn ordinary_two_three_role_metrics_stay_intact_and_author_never_relabels_them() {
    let two_log = RoleMetricsLog::new();
    let mut fixture = Fixture::new(Some(two_log.clone()), AuthorFixtureCase::Completed);
    let mut two = RuntimeProvider::with_metrics(fixture.runtime.clone(), two_log.clone());
    let director = play_request("director");
    let narrator = play_request("narrator");
    let two_results = [
        ready(&mut two, &director, &Cancellation::default()),
        ready(&mut two, &narrator, &Cancellation::default()),
    ];
    let play_to_author = two.poll(&author_request(), &Cancellation::default());
    drop(two);
    let two_snapshot = two_log.snapshot();
    let three_log = RoleMetricsLog::new();
    let mut three = RuntimeProvider::with_metrics(fixture.runtime.clone(), three_log.clone());
    let mut repair = director.clone();
    prompt(&mut repair, "one bounded synthetic repair".into());
    let three_results = [
        ready(&mut three, &director, &Cancellation::default()),
        ready(&mut three, &repair, &Cancellation::default()),
        ready(&mut three, &narrator, &Cancellation::default()),
    ];
    drop(three);
    let three_snapshot = three_log.snapshot();
    let author = ready(
        fixture.provider.as_mut().unwrap(),
        &author_request(),
        &Cancellation::default(),
    );
    let cleanup = fixture.finish();
    let hidden_old_records = two_log.snapshot();
    cleaned(&cleanup);
    assert!(two_results.iter().all(|r| *r == Some(Ok(vec![]))));
    assert!(three_results.iter().all(|r| *r == Some(Ok(vec![]))));
    assert_eq!(play_to_author, Poll::Ready(Err(Error::RetryMismatch)));
    for (snapshot, count) in [(&two_snapshot, 2), (&three_snapshot, 3)] {
        assert_eq!(snapshot.version, 2);
        assert!(snapshot.available && !snapshot.incomplete);
        assert_eq!(snapshot.records.len(), count);
        for (index, record) in snapshot.records.iter().enumerate() {
            let is_director = index + 1 < count;
            assert_eq!(
                record.role,
                if is_director {
                    MetricRole::Director
                } else {
                    MetricRole::Narrator
                }
            );
            assert_eq!(record.ordinal, index as u8);
            assert_eq!(
                record.director_attempt,
                if is_director { Some(index as u8) } else { None }
            );
            assert_eq!(record.adapter_terminal, AdapterTerminal::Completed);
            assert_eq!(record.native_terminal, NativeTerminal::Completed);
        }
    }
    assert_eq!(author, Some(Ok(vec![])));
    assert!(!hidden_old_records.available && hidden_old_records.incomplete);
    assert!(hidden_old_records.records.is_empty() && hidden_old_records.turn_sha256.is_none());
}
