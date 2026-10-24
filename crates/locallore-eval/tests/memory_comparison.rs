//! Frozen model-free protocol vectors. No existing runner, model, files or native app.
#[allow(dead_code)]
#[path = "../src/memory_comparison.rs"]
mod protocol;
use locallore::{
    context_compiler::ContextPackage,
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
    turn_capture::Artifact,
    turn_trace::{StageMeasurement, TraceSink},
};
use protocol::*;
use serde_json::json;
use std::task::Poll;

fn profile() -> PlayProfile {
    PlayProfile {
        id: "comparison-scripted".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 120_000,
        repair_limit: 1,
    }
}
#[derive(Default)]
struct Capture {
    context: Option<ContextPackage>,
}
impl TraceSink for Capture {
    fn matches(&mut self, _: &Scope, _: u64, _: &str, _: &str) -> bool {
        true
    }
    fn record(&mut self, _: StageMeasurement) {}
    fn capture(&mut self, a: Artifact<'_>) {
        if let Artifact::Context(value) = a {
            self.context = Some(value.clone());
        }
    }
}
struct Script {
    command: Command,
    narration: String,
    calls: Vec<GenerationRequest>,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        r: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<std::result::Result<Vec<u8>, Error>> {
        self.calls.push(r.clone());
        let Input::Structured { role, .. } = &r.input else {
            panic!("same production structured request required")
        };
        let output = if role == "director" {
            json!({"commands":[self.command]})
        } else {
            assert_eq!(role, "narrator");
            json!({"text":self.narration,"event_ids":[r.revision+1],"speaker":"narrator"})
        };
        Poll::Ready(Ok(serde_json::to_vec(&output).unwrap()))
    }
}
fn actual_step(
    suite: &FrozenSuite,
    index: usize,
    engine: &mut Engine,
    wrong: bool,
    html: bool,
) -> TurnEvidence {
    let step = &suite.steps()[index];
    let before = engine.clone();
    let reference = reference_proposal(&before, step);
    if matches!(step.expected(), Expected::Accepted(_)) && reference.is_err() {
        return check_observation(
            suite,
            index,
            &before,
            engine,
            ActualOutcome::NotRunDependency,
            &[],
            None,
        )
        .unwrap();
    }
    let (command, narration) = reference
        .map(|p| {
            let text = before
                .preview(&step.request(&before), &p)
                .unwrap()
                .narration()
                .to_owned();
            (p.commands[0].clone(), text)
        })
        .unwrap_or((Command::Wait { ticks: 1 }, "Time passes.".into()));
    let mut provider = Script {
        command: if wrong {
            Command::Wait { ticks: 1 }
        } else {
            command
        },
        narration: if html {
            "Your words are heard <script>alert(1)</script>.".into()
        } else {
            narration
        },
        calls: vec![],
    };
    let mut captured = Capture::default();
    let result = play::execute_traced(
        engine,
        &step.request(&before),
        &mut provider,
        &Cancellation::default(),
        &profile(),
        Some(&mut captured),
    );
    let observed = match &result {
        Ok(r) => ActualOutcome::Accepted(r),
        Err(e) => ActualOutcome::Rejected(e.clone()),
    };
    check_observation(
        suite,
        index,
        &before,
        engine,
        observed,
        &provider.calls,
        captured.context.as_ref(),
    )
    .unwrap()
}
fn rollout(wrong: Option<usize>) -> (Vec<TurnEvidence>, Engine) {
    let suite = frozen_suite().unwrap();
    let mut engine = Engine::new(suite.seed().clone()).unwrap();
    let rows = (0..ATTEMPTS)
        .map(|i| actual_step(&suite, i, &mut engine, wrong == Some(i), false))
        .collect();
    (rows, engine)
}
fn binding(id: &str, source: &str, kind: ExperimentKind, policy: HistoryPolicy) -> Binding {
    Binding::new(
        id,
        source,
        &frozen_suite().unwrap(),
        &profile(),
        ProviderLane::Scripted,
        kind,
        policy,
    )
    .unwrap()
}
fn zero() -> Charges {
    Charges {
        admissions: 0,
        roles: 0,
        active_ms: 0,
        invocations: 0,
        unknown_roles: 0,
    }
}

#[test]
fn frozen_24_attempts_use_actual_play_and_preserve_explicit_capability_gaps() {
    let suite = frozen_suite().unwrap();
    assert_eq!(
        suite.sha256().unwrap(),
        frozen_suite().unwrap().sha256().unwrap()
    );
    assert_eq!(suite.steps().len(), 24);
    assert_eq!(
        suite.steps().iter().map(Step::scene).collect::<Vec<_>>(),
        (0..24).map(|i| i / 6 + 1).collect::<Vec<_>>()
    );
    let (rows, after) = rollout(None);
    assert_eq!(
        rows.iter()
            .filter(|r| r.row().outcome == Outcome::Passed)
            .count(),
        21
    );
    assert_eq!(
        rows.iter()
            .filter(|r| r.row().outcome == Outcome::GuardOnly)
            .count(),
        3
    );
    assert_eq!(rows.iter().map(|r| r.row().roles).sum::<usize>(), 42);
    for (index, error) in [
        (8, "Inventory"),
        (9, "Ability"),
        (23, "ClarificationRequired"),
    ] {
        let row = rows[index].row();
        assert_eq!(row.roles, 0);
        assert_eq!(serde_json::to_value(row).unwrap()["error"], error);
        assert_eq!(row.before_state_sha256, row.after_state_sha256);
    }
    assert_eq!(after.state().items["brass-key"].owner, "oren");
    assert_eq!(after.state().items["brass-key"].return_to, None);
    assert_eq!(after.state().items["pennant"].owner, "oren");
    assert!(!after.state().items.contains_key("potion"));
    assert_eq!(after.state().actors["player"].energy, 1);
    assert!(
        after.state().commitments["return-key"]
            .completed_by
            .is_none(),
        "unsupported free-text completion remains unmet, never teacher forced"
    );
    assert!(
        after
            .state()
            .beliefs
            .iter()
            .any(|b| b.believer == "mira" && b.proposition.contains("old-ruins")),
        "attributed belief never rewritten as fact"
    );
    assert!(!after
        .character_context("sable", after.scope(), after.revision())
        .unwrap()
        .facts
        .contains_key("relic-location"));
    let restored = Engine::replay(suite.seed().clone(), after.receipts()).unwrap();
    assert_eq!(restored.canonical_bytes(), after.canonical_bytes());
    assert_eq!(restored.receipts(), after.receipts());
}
#[test]
fn actual_context_capture_and_actual_role_requests_keep_distinct_denominators() {
    let (rows, _) = rollout(None);
    assert!(rows.iter().all(|r| r.row().envelope_privacy_passed));
    assert_eq!(
        rows[0].row().director_private_target_present,
        Some(true),
        "player's legitimate secret is permitted in actual director envelope"
    );
    assert!(
        rows.iter()
            .all(|r| r.row().raw_output_privacy_passed.is_none()),
        "unretained raw role output cannot be marked checked"
    );
    assert_eq!(
        rows[21].row().optional_detail_selected,
        Some(true),
        "old Said detail must be optional in actual lexical reference capture"
    );
    assert_eq!(
        rows[21].row().director_detail_present,
        Some(true),
        "actual director envelope must contain the optional detail, not just standalone compiler"
    );
    assert!(rows
        .iter()
        .filter(|r| r.row().outcome == Outcome::GuardOnly)
        .all(|r| r.row().director_detail_present.is_none() && r.row().mandatory_sha256.is_none()));
    assert!(rows
        .iter()
        .filter(|r| r.row().outcome == Outcome::Passed)
        .all(|r| r.row().receipt_context.is_some()
            && r.row().prompt_sha256.len() == 2
            && r.row().schema_sha256.len() == 2));
}
#[test]
fn policy_omitted_current_reference_cannot_be_relabelled_either_future_policy() {
    for policy in [
        HistoryPolicy::StateRecentTranscriptV1,
        HistoryPolicy::StateRelevantMemoryV1,
    ] {
        assert_eq!(
            require_execution(policy),
            Err(ProtocolError::UnsupportedPolicy)
        );
    }
    let left = binding(
        "left",
        &"f".repeat(64),
        ExperimentKind::ContinuousRollout,
        HistoryPolicy::StateRecentTranscriptV1,
    );
    let right = binding(
        "right",
        &"f".repeat(64),
        ExperimentKind::ContinuousRollout,
        HistoryPolicy::StateRelevantMemoryV1,
    );
    let report = validate_pair(&left, &right, &[], &[], zero(), zero()).unwrap();
    assert_eq!(report.planned_attempts_per_arm, 24);
    assert_eq!(report.observed_left, 0);
    assert!(!report.quality_passed);
    assert_eq!(report.human_review, "not_reviewed");
    let (rows, _) = rollout(None);
    let charges = Charges {
        admissions: 24,
        roles: 42,
        active_ms: 1,
        invocations: 1,
        unknown_roles: 0,
    };
    assert!(matches!(
        validate_pair(&left, &right, &[], &rows, zero(), charges),
        Err(ProtocolError::UnsupportedPolicy)
    ));
    assert!(matches!(
        validate_pair(&left, &right, &rows, &[], charges, zero()),
        Err(ProtocolError::UnsupportedPolicy)
    ));
}
#[test]
fn wrong_generated_command_stays_failed_and_dependency_skip_is_not_expected_state() {
    let (reference, _) = rollout(None);
    let (wrong, after) = rollout(Some(4));
    assert_eq!(wrong[4].row().outcome, Outcome::Failed);
    assert_eq!(
        wrong[4].row().before_state_sha256,
        wrong[4].row().after_state_sha256
    );
    assert_eq!(wrong[5].row().outcome, Outcome::NotRunDependency);
    assert_eq!(wrong[5].row().roles, 0);
    let comparison =
        compare_sequences(ExperimentKind::ContinuousRollout, &reference, &wrong).unwrap();
    assert_eq!(comparison.first_divergence, Some(5));
    assert_eq!(comparison.same_snapshot_pairs, 5);
    assert_ne!(after.canonical_bytes(), rollout(None).1.canonical_bytes());
    assert!(matches!(
        compare_sequences(ExperimentKind::PairedSnapshots, &reference, &wrong),
        Err(ProtocolError::Binding)
    ));
}
#[test]
fn timing_diagnostics_do_not_manufacture_semantic_rollout_divergence() {
    let (left, _) = rollout(None);
    let (right, _) = rollout(None);
    let comparison = compare_sequences(ExperimentKind::ContinuousRollout, &left, &right).unwrap();
    assert_eq!(comparison.first_divergence, None);
    assert_eq!(comparison.same_snapshot_pairs, 24);
    assert_eq!(
        compare_sequences(ExperimentKind::PairedSnapshots, &left, &left)
            .unwrap()
            .exact_source_pairs,
        24
    );
}
#[test]
fn tiny_mandatory_budget_stops_actual_play_before_provider() {
    let suite = frozen_suite().unwrap();
    let mut engine = Engine::new(suite.seed().clone()).unwrap();
    let before = engine.canonical_bytes();
    let mut p = profile();
    p.context_tokens = 512;
    let mut provider = Script {
        command: Command::Wait { ticks: 1 },
        narration: "Time passes.".into(),
        calls: vec![],
    };
    let request = suite.steps()[0].request(&engine);
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut provider,
            &Cancellation::default(),
            &p
        ),
        Err(Error::TooLarge)
    );
    assert!(provider.calls.is_empty());
    assert_eq!(engine.canonical_bytes(), before);
}
#[test]
fn source_profile_and_plan_drift_refuse_before_any_policy_claim() {
    let source = "f".repeat(64);
    let left = binding(
        "left",
        &source,
        ExperimentKind::PairedSnapshots,
        HistoryPolicy::StateRecentTranscriptV1,
    );
    let wrong_source = binding(
        "right",
        &"a".repeat(64),
        ExperimentKind::PairedSnapshots,
        HistoryPolicy::StateRelevantMemoryV1,
    );
    assert!(matches!(
        validate_pair(&left, &wrong_source, &[], &[], zero(), zero()),
        Err(ProtocolError::Binding)
    ));
    let mut p = profile();
    p.template_sha256 = "9".repeat(64);
    let wrong_profile = Binding::new(
        "right",
        &source,
        &frozen_suite().unwrap(),
        &p,
        ProviderLane::Scripted,
        ExperimentKind::PairedSnapshots,
        HistoryPolicy::StateRelevantMemoryV1,
    )
    .unwrap();
    assert!(matches!(
        validate_pair(&left, &wrong_profile, &[], &[], zero(), zero()),
        Err(ProtocolError::Binding)
    ));
    let wrong_kind = binding(
        "right",
        &source,
        ExperimentKind::ContinuousRollout,
        HistoryPolicy::StateRelevantMemoryV1,
    );
    assert!(matches!(
        validate_pair(&left, &wrong_kind, &[], &[], zero(), zero()),
        Err(ProtocolError::Binding)
    ));
    assert!(Binding::new(
        "../path",
        &source,
        &frozen_suite().unwrap(),
        &profile(),
        ProviderLane::Scripted,
        ExperimentKind::PairedSnapshots,
        HistoryPolicy::StateRecentTranscriptV1
    )
    .is_err());
}
#[test]
fn existing_ledger_counters_are_bounded_and_never_reset_unknown_charges() {
    let previous = Charges {
        admissions: 24,
        roles: 72,
        active_ms: 600_000,
        invocations: 2,
        unknown_roles: 3,
    };
    assert!(previous.validate().is_ok());
    assert!(previous.extends(previous).is_ok());
    for next in [
        Charges {
            admissions: 23,
            ..previous
        },
        Charges {
            roles: 71,
            ..previous
        },
        Charges {
            active_ms: 599_999,
            ..previous
        },
        Charges {
            invocations: 1,
            ..previous
        },
        Charges {
            unknown_roles: 2,
            ..previous
        },
        Charges {
            admissions: 33,
            ..previous
        },
        Charges {
            roles: 97,
            ..previous
        },
        Charges {
            active_ms: 1_800_001,
            ..previous
        },
        Charges {
            invocations: 33,
            ..previous
        },
        Charges {
            unknown_roles: 73,
            ..previous
        },
    ] {
        assert!(next.extends(previous).is_err());
    }
}
#[test]
fn original_scope_and_failed_canon_checks_reject_substitution() {
    let suite = frozen_suite().unwrap();
    let before = Engine::new(suite.seed().clone()).unwrap();
    let mut foreign = suite.seed().clone();
    foreign.scope.story = "foreign".into();
    let foreign = Engine::new(foreign).unwrap();
    assert!(matches!(
        check_observation(
            &suite,
            0,
            &before,
            &foreign,
            ActualOutcome::Rejected(Error::Provider),
            &[],
            None
        ),
        Err(ProtocolError::Binding)
    ));
    assert!(
        matches!(
            check_observation(
                &suite,
                0,
                &before,
                &before,
                ActualOutcome::NotRunDependency,
                &[],
                None
            ),
            Err(ProtocolError::Binding)
        ),
        "a valid next action cannot be hidden as dependency skip"
    );
    let failed = check_observation(
        &suite,
        0,
        &before,
        &before,
        ActualOutcome::Rejected(Error::Provider),
        &[],
        None,
    )
    .unwrap();
    assert_eq!(failed.row().outcome, Outcome::Failed);
    assert_eq!(failed.row().fallback, None);
}
#[test]
fn actual_displayed_prose_is_escaped_and_fallback_not_human_quality() {
    let suite = frozen_suite().unwrap();
    let mut engine = Engine::new(suite.seed().clone()).unwrap();
    let observation = actual_step(&suite, 0, &mut engine, false, true);
    assert_eq!(
        observation.row().fallback,
        Some(false),
        "synthetic markup must actually reach accepted display text for escaping check"
    );
    let html = render_human_packet(&[observation]).unwrap();
    assert!(html.contains("&lt;script&gt;alert(1)&lt;/script&gt;"));
    assert!(!html.contains("<script>"));
    assert!(
        html.contains("not reviewed")
            && html.contains("unsupported")
            && html.contains("fallback: Some(false)")
    );
    let (rows, _) = rollout(None);
    assert!(render_human_packet(&rows).unwrap().len() <= MAX_PACKET_BYTES);
}

#[test]
fn duplicate_or_out_of_order_observations_cannot_hide_missing_attempts() {
    let (mut rows, _) = rollout(None);
    rows.swap(0, 1);
    assert!(matches!(
        compare_sequences(ExperimentKind::ContinuousRollout, &rows, &[]),
        Err(ProtocolError::Order)
    ));
    assert!(matches!(
        render_human_packet(&rows),
        Err(ProtocolError::Order)
    ));
    let left = binding(
        "left",
        &"f".repeat(64),
        ExperimentKind::ContinuousRollout,
        HistoryPolicy::StateRecentTranscriptV1,
    );
    let right = binding(
        "right",
        &"f".repeat(64),
        ExperimentKind::ContinuousRollout,
        HistoryPolicy::StateRelevantMemoryV1,
    );
    let (rows, _) = rollout(None);
    assert!(
        matches!(
            validate_pair(&left, &right, &[], &rows, zero(), zero()),
            Err(ProtocolError::Budget)
        ),
        "existing-ledger charges may not underreport actual captured roles/admissions"
    );
}

#[test]
fn actual_envelope_checker_rejects_injected_foreign_canary_without_changing_canon() {
    let suite = frozen_suite().unwrap();
    let before = Engine::new(suite.seed().clone()).unwrap();
    let step = &suite.steps()[0];
    let proposal = reference_proposal(&before, step).unwrap();
    let mut provider = Script {
        command: proposal.commands[0].clone(),
        narration: before
            .preview(&step.request(&before), &proposal)
            .unwrap()
            .narration()
            .into(),
        calls: vec![],
    };
    let mut after = before.clone();
    let mut captured = Capture::default();
    let receipt = play::execute_traced(
        &mut after,
        &step.request(&before),
        &mut provider,
        &Cancellation::default(),
        &profile(),
        Some(&mut captured),
    )
    .unwrap();
    // Deliberately corrupt the supplied captured envelope, not a claim that Core leaked.
    let Input::Structured { prompt, .. } = &mut provider.calls[0].input else {
        panic!("structured")
    };
    prompt.push_str(" FOREIGN-COMPARISON");
    let row = check_observation(
        &suite,
        0,
        &before,
        &after,
        ActualOutcome::Accepted(&receipt),
        &provider.calls,
        captured.context.as_ref(),
    )
    .unwrap();
    assert_eq!(row.row().outcome, Outcome::Failed);
    assert!(!row.row().envelope_privacy_passed);
    assert_eq!(
        row.row().after_state_sha256,
        check_observation(
            &suite,
            0,
            &before,
            &after,
            ActualOutcome::Accepted(&receipt),
            &provider.calls,
            None
        )
        .unwrap()
        .row()
        .after_state_sha256
    );
}
