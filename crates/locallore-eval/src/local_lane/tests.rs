use super::*;
#[test]
fn frozen_corpus_and_full_scripted_baseline() {
    let c = corpus().unwrap();
    assert_eq!(c.stories.len(), 6);
    assert_eq!(c.stories.iter().map(|s| s.steps.len()).sum::<usize>(), 24);
    let temp = crate::tests::Temp::new();
    let report = run_curated(
        &temp.0.join("curated"),
        false,
        None,
        &Cancellation::default(),
        6,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    for case in &report.cases {
        assert_ne!(
            case.status,
            Status::Failed,
            "{}: {:?}",
            case.id,
            case.checks
                .iter()
                .filter(|c| c.status == Status::Failed)
                .collect::<Vec<_>>()
        );
        let director_turns = case
            .provider_requests
            .iter()
            .filter(|capture| capture.role == "director")
            .map(|capture| &capture.turn)
            .collect::<BTreeSet<_>>();
        let checked_turns = case
            .checks
            .iter()
            .filter(|check| check.id.ends_with("-director-context"))
            .map(|check| check.turn.as_ref().unwrap())
            .collect::<BTreeSet<_>>();
        assert_eq!(checked_turns, director_turns);
    }
    assert!(report.completed);
    assert_eq!(report.cases.len(), 6);
    assert_eq!(report.provenance["coverage"]["executed_turn_cases"], 24);
    assert_eq!(report.provenance["coverage"]["guard_only"], 6);
    assert_eq!(report.provenance["coverage"]["cancelled"], 1);
    assert_eq!(report.provenance["coverage"]["inference_completed"], 17);
    assert!(!report.quality_accepted);
}
#[test]
fn role_exclusions_follow_actual_scope_without_hiding_player_secret_from_director() {
    for story in corpus().unwrap().stories {
        for step in &story.steps {
            let forbidden = forbidden_by_role(&story, step);
            let foreign = format!("FOREIGN-ONLY-{}", story.id);
            assert!(forbidden.director.contains(&foreign));
            assert!(forbidden.narrator.contains(&foreign));
            assert!(!forbidden.director.iter().any(|s| s == "SECRET-TIDE-731"));
            assert!(forbidden.narrator.iter().any(|s| s == "SECRET-TIDE-731"));
            for marker in ["PARENT-FUTURE-MIST", "SIBLING-ONLY-SALT"] {
                let excluded = story.lineage && step.branch == "child";
                assert_eq!(forbidden.director.iter().any(|s| s == marker), excluded);
                assert_eq!(forbidden.narrator.iter().any(|s| s == marker), excluded);
            }
        }
    }
}
#[test]
fn pause_resume_subset_and_immutable_completed_story_do_not_double_count() {
    let temp = crate::tests::Temp::new();
    let path = temp.0.join("run");
    let first = run_curated(
        &path,
        false,
        None,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    assert!(!first.completed);
    assert_eq!(first.provenance["coverage"]["executed_turn_cases"], 4);
    let checkpoint = fs::read(path.join("case-00.json")).unwrap();
    let done = run_curated(
        &path,
        true,
        None,
        &Cancellation::default(),
        6,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    assert!(done.completed);
    assert_eq!(done.provenance["budget"]["admissions_across_attempts"], 24);
    assert_eq!(fs::read(path.join("case-00.json")).unwrap(), checkpoint);
    let again = run_curated(
        &path,
        true,
        None,
        &Cancellation::default(),
        6,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    assert_eq!(again.provenance["budget"]["admissions_across_attempts"], 24);
    let subset = run_curated(
        &temp.0.join("subset"),
        false,
        Some("ability-cost"),
        &Cancellation::default(),
        6,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    assert_eq!(subset.cases.len(), 1);
    assert_eq!(subset.provenance["coverage"]["declared_turn_cases"], 4);
    assert_eq!(subset.provenance["coverage"]["guard_only"], 2);
}
#[test]
fn wrong_command_is_a_failure_not_scripted_repair_or_skipped_success() {
    let temp = crate::tests::Temp::new();
    let report = run_curated(
        &temp.0.join("fault"),
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::TestFault(TestFault::WrongCommand),
    )
    .unwrap();
    assert_eq!(report.cases[0].status, Status::Failed);
    assert_eq!(report.cases[0].turns.len(), 1);
    assert_eq!(report.provenance["coverage"]["not_run"], 3);
    assert_eq!(report.provenance["coverage"]["inference_failed"], 1);
    assert!(!report.quality_accepted);
}
#[test]
fn one_malformed_repair_and_unfaithful_fallback_keep_honest_quality_status() {
    let temp = crate::tests::Temp::new();
    let repaired = run_curated(
        &temp.0.join("repair"),
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::TestFault(TestFault::MalformedRepair),
    )
    .unwrap();
    assert_eq!(repaired.cases[0].status, Status::Passed);
    assert_eq!(repaired.cases[0].turns[0].repairs, Some(1));
    assert_eq!(repaired.provenance["budget"]["roles_charged"], 9);
    let fallback = run_curated(
        &temp.0.join("fallback"),
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::TestFault(TestFault::UnfaithfulNarrator),
    )
    .unwrap();
    assert_eq!(fallback.cases[0].status, Status::Passed);
    assert_eq!(fallback.cases[0].turns[0].fallback, Some(true));
    assert_eq!(fallback.provenance["coverage"]["quality_candidates"], 0);
    assert!(!fallback.quality_accepted);
    let leaked = run_curated(
        &temp.0.join("canary"),
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::TestFault(TestFault::SecretNarrator),
    )
    .unwrap();
    assert_eq!(leaked.cases[0].status, Status::Failed);
    assert!(leaked.cases[0]
        .checks
        .iter()
        .any(|c| c.stage == "prohibited_claim" && c.status == Status::Failed));
    assert!(!leaked.cases[0].turns[0]
        .narration
        .as_ref()
        .unwrap()
        .contains("SECRET-TIDE-731"));
}
#[test]
fn independent_pending_providers_cannot_signal_or_cancel_each_other() {
    let corpus = corpus().unwrap();
    let story = &corpus.stories[0];
    let step = &story.steps[0];
    let left_seen = Arc::new(std::sync::atomic::AtomicBool::new(false));
    let right_seen = Arc::new(std::sync::atomic::AtomicBool::new(false));
    let mut left = LaneFactory::TestFault(TestFault::Pending(left_seen.clone())).provider(
        step,
        Arc::new(Recording::default()),
        ForbiddenByRole::default(),
    );
    let mut right = LaneFactory::TestFault(TestFault::Pending(right_seen.clone())).provider(
        step,
        Arc::new(Recording::default()),
        ForbiddenByRole::default(),
    );
    let request = GenerationRequest {
        version: 1,
        scope: story.seed.scope.clone(),
        turn: step.id.clone(),
        revision: 0,
        model_profile: "eval-scripted-fake-v1".into(),
        schema: "fixture".into(),
        budget: locallore::inference::Budget::default(),
        input: Input::Structured {
            role: "director".into(),
            prompt: "SYNTHETIC-PENDING-ISOLATION".into(),
            schema: json!({"type":"object"}),
        },
    };
    let left_cancel = Cancellation::default();
    let right_cancel = Cancellation::default();
    assert!(left.poll(&request, &left_cancel).is_pending());
    assert!(left_seen.load(Ordering::Acquire));
    assert!(!right_seen.load(Ordering::Acquire));
    left_cancel.cancel();
    assert!(right.poll(&request, &right_cancel).is_pending());
    assert!(right_seen.load(Ordering::Acquire));
    assert!(!right_cancel.is_cancelled());
    assert!(matches!(
        left.poll(&request, &left_cancel),
        Poll::Ready(Err(Error::Cancelled))
    ));
    assert!(right.poll(&request, &right_cancel).is_pending());
    right_cancel.cancel();
    assert!(matches!(
        right.poll(&request, &right_cancel),
        Poll::Ready(Err(Error::Cancelled))
    ));
}

#[test]
fn active_cancellation_abandons_private_attempt_then_resume_starts_fresh() {
    let temp = crate::tests::Temp::new();
    let path = temp.0.join("cancel");
    let cancel = Cancellation::default();
    let token = cancel.clone();
    let pending = Arc::new(std::sync::atomic::AtomicBool::new(false));
    let observed = pending.clone();
    let stop = std::thread::spawn(move || {
        let started = Instant::now();
        while !observed.load(Ordering::Acquire) && started.elapsed() < Duration::from_secs(5) {
            std::thread::sleep(Duration::from_millis(5));
        }
        let polled = observed.load(Ordering::Acquire);
        token.cancel();
        polled
    });
    let report = run_curated(
        &path,
        false,
        Some("gift-agency"),
        &cancel,
        6,
        LaneFactory::TestFault(TestFault::Pending(pending)),
    )
    .unwrap();
    assert!(stop.join().unwrap());
    assert!(report.cancelled);
    assert!(!report.completed);
    assert!(report.cases.is_empty());
    assert!(path.join("case-00-attempt-00").exists());
    assert!(!path.join("case-00.json").exists());
    let resumed = run_curated(
        &path,
        true,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    assert!(resumed.completed);
    assert!(path.join("case-00-attempt-01").exists());
    assert_eq!(
        resumed.provenance["budget"]["admissions_across_attempts"],
        5
    );
}
#[test]
fn cumulative_reservations_unknown_work_caps_and_ledger_integrity_survive_resume() {
    let temp = crate::tests::Temp::new();
    let path = temp.0.join("budget");
    let session = Session::open(
        &path,
        false,
        Some("gift-agency"),
        false,
        LaneFactory::ScriptedBaseline.profile().unwrap(),
        false,
    )
    .unwrap();
    let binding = session.binding.clone();
    let mut ledger = session.ledger;
    ledger.admit("gift-agency", "gift").unwrap();
    drop(ledger);
    drop(session._lock);
    let mut recovered = Ledger::load(&path, &binding).unwrap();
    assert_eq!(recovered.charged_ms, PREPARATION_MS + TURN_MS);
    assert_eq!(recovered.charged_roles, 3);
    assert_eq!(recovered.admissions, 1);
    recovered.begin_invocation().unwrap();
    assert_eq!(recovered.charged_ms, 2 * PREPARATION_MS + TURN_MS);
    for i in 1..32 {
        let n = recovered.admit("gift-agency", "gift").unwrap();
        assert_eq!(n, i);
        recovered.settle(n, 0, 3).unwrap();
    }
    assert_eq!(
        recovered.admit("gift-agency", "gift").err().as_deref(),
        Some("RunBudget")
    );
    assert_eq!(recovered.charged_roles, 96);
    fs::remove_file(path.join("admission-01.json")).unwrap();
    assert_eq!(
        Ledger::load(&path, &binding).err().as_deref(),
        Some("LedgerIntegrity")
    );
}
#[test]
fn source_raw_checkpoint_and_path_tampering_refuse_resume() {
    let temp = crate::tests::Temp::new();
    let path = temp.0.join("integrity");
    run_curated(
        &path,
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    let raw = path.join("case-00-attempt-00/raw-00.json");
    let before = fs::read(&raw).unwrap();
    fs::write(&raw, b"tampered").unwrap();
    assert_eq!(
        run_curated(
            &path,
            true,
            Some("gift-agency"),
            &Cancellation::default(),
            6,
            LaneFactory::ScriptedBaseline
        )
        .err()
        .as_deref(),
        Some("CheckpointIntegrity")
    );
    fs::write(&raw, before).unwrap();
    let file = path.join("case-00.json");
    let mut saved: LocalStored = serde_json::from_slice(&fs::read(&file).unwrap()).unwrap();
    saved.metadata.turns[0].raw[0].file = "../../foreign".into();
    saved.result_sha256 = digest(
        &encode(&json!({"result":saved.result,"metadata":saved.metadata,"attempt":saved.attempt}))
            .unwrap(),
    );
    fs::write(&file, encode(&saved).unwrap()).unwrap();
    assert_eq!(
        run_curated(
            &path,
            true,
            Some("gift-agency"),
            &Cancellation::default(),
            6,
            LaneFactory::ScriptedBaseline
        )
        .err()
        .as_deref(),
        Some("CheckpointIntegrity")
    );
    let mut bytes = fs::read(path.join("run.json")).unwrap();
    bytes.push(b' ');
    fs::write(path.join("run.json"), bytes).unwrap();
    assert_eq!(
        run_curated(
            &path,
            true,
            Some("gift-agency"),
            &Cancellation::default(),
            6,
            LaneFactory::ScriptedBaseline
        )
        .err()
        .as_deref(),
        Some("CheckpointMismatch")
    );
}
#[test]
fn local_report_is_inert_and_owner_and_default_cli_refuse_unauthorized_options() {
    let temp = crate::tests::Temp::new();
    let path = temp.0.join("lock");
    let owner = Session::open(
        &path,
        false,
        Some("gift-agency"),
        false,
        LaneFactory::ScriptedBaseline.profile().unwrap(),
        false,
    )
    .unwrap();
    assert_eq!(
        Session::open(
            &path,
            true,
            Some("gift-agency"),
            false,
            LaneFactory::ScriptedBaseline.profile().unwrap(),
            false
        )
        .err()
        .as_deref(),
        Some("RunBusy")
    );
    drop(owner);
    let mut report = run_curated(
        &temp.0.join("html"),
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    report.provenance["synthetic_injection"] = json!("<script>window.x=1</script>");
    publish_local_report(&temp.0.join("html"), &report).unwrap();
    let html = fs::read_to_string(temp.0.join("html/report.html")).unwrap();
    assert!(!html.contains("<script>"));
    assert!(html.contains("&lt;script&gt;"));
    assert!(html.contains("default-src 'none'"));
    report.provenance["synthetic_injection"] = json!("x".repeat(MAX_REPORT));
    assert_eq!(
        publish_local_report(&temp.0.join("html"), &report)
            .err()
            .as_deref(),
        Some("ReportBudget")
    );
    assert_eq!(
        cli(&[
            "run".into(),
            "unused".into(),
            "--lane".into(),
            "scripted".into(),
            "--model".into(),
            "unused".into()
        ])
        .err()
        .as_deref(),
        Some("Usage")
    );
    #[cfg(not(feature = "local-model"))]
    assert_eq!(
        cli(&[
            "run".into(),
            "unused".into(),
            "--lane".into(),
            "native".into()
        ])
        .err()
        .as_deref(),
        Some("NativeFeatureUnavailable")
    );
}

#[test]
fn finite_prohibited_claim_regression_exposes_semantic_guard_false_negative() {
    let temp = crate::tests::Temp::new();
    let report = run_curated(
        &temp.0.join("semantic-limitation"),
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        6,
        LaneFactory::TestFault(TestFault::UnsupportedProse),
    )
    .unwrap();
    assert_eq!(report.cases[0].status, Status::Failed);
    assert_eq!(report.cases[0].turns[0].fallback, Some(false));
    assert!(report.cases[0]
        .checks
        .iter()
        .any(|c| c.stage == "prohibited_claim" && c.status == Status::Failed));
    assert_eq!(report.provenance["coverage"]["not_run"], 3);
    assert!(!report.quality_accepted);
}
#[cfg(feature = "local-model")]
#[test]
fn native_preparation_cancels_before_model_or_worker_open_without_fake_fallback() {
    let temp = crate::tests::Temp::new();
    let cancel = Cancellation::default();
    cancel.cancel();
    let path = temp.0.join("native-cancel");
    assert_eq!(
        run_native_curated(
            &path,
            false,
            Some("gift-agency"),
            &cancel,
            1,
            NativeAssets {
                resource_dir: Path::new("missing-fixed-resource"),
                model: Path::new("missing-approved-model")
            }
        )
        .err()
        .as_deref(),
        Some("RuntimeCancelled")
    );
    assert!(path.join("invocation-00-settled.json").exists());
    assert!(!path.join("admission-00.json").exists());
    assert!(!path.join("report.json").exists());
}
#[test]
fn recording_repeated_polls_role_cap_and_poison_do_not_create_authority() {
    use crate::local_recording::{Recording, RecordingProvider};
    use std::sync::atomic::AtomicUsize;
    struct Ready(Arc<AtomicUsize>);
    impl InferenceProvider for Ready {
        fn poll(
            &mut self,
            _: &GenerationRequest,
            _: &Cancellation,
        ) -> Poll<std::result::Result<Vec<u8>, Error>> {
            self.0.fetch_add(1, Ordering::Relaxed);
            Poll::Ready(Ok(b"{}".to_vec()))
        }
    }
    let calls = Arc::new(AtomicUsize::new(0));
    let state = Arc::new(Recording::default());
    let mut provider = RecordingProvider::new(
        Box::new(Ready(calls.clone())),
        state.clone(),
        vec![],
        ForbiddenByRole::default(),
    );
    let mut request = GenerationRequest {
        version: 1,
        scope: Scope {
            story: "fixture".into(),
            branch: "main".into(),
        },
        turn: "turn".into(),
        revision: 0,
        model_profile: "eval-scripted-fake-v1".into(),
        schema: "fixture".into(),
        budget: locallore::inference::Budget {
            max_output_bytes: 16_384,
            max_output_tokens: 350,
            max_pending_polls: 1,
            deadline_ms: 1000,
        },
        input: Input::Structured {
            role: "director".into(),
            prompt: "PRIVATE-SYNTHETIC-PROMPT".into(),
            schema: json!({"type":"object"}),
        },
    };
    let cancel = Cancellation::default();
    assert!(provider.poll(&request, &cancel).is_ready());
    assert!(provider.poll(&request, &cancel).is_ready());
    assert_eq!(state.roles.load(Ordering::Relaxed), 1);
    assert_eq!(state.state.lock().unwrap().outputs.len(), 1);
    for n in 0..2 {
        if let Input::Structured { prompt, .. } = &mut request.input {
            *prompt = format!("repair-{n}");
        }
        assert!(provider.poll(&request, &cancel).is_ready());
    }
    if let Input::Structured { prompt, .. } = &mut request.input {
        *prompt = "fourth".into();
    }
    let before = calls.load(Ordering::Relaxed);
    assert_eq!(
        provider.poll(&request, &cancel),
        Poll::Ready(Err(Error::TooLarge))
    );
    assert_eq!(calls.load(Ordering::Relaxed), before);
    assert_eq!(state.roles.load(Ordering::Relaxed), 3);
    assert!(
        !serde_json::to_string(&state.state.lock().unwrap().captures)
            .unwrap()
            .contains("PRIVATE-SYNTHETIC-PROMPT")
    );
    let poisoned = Arc::new(Recording::default());
    let p = poisoned.clone();
    let _ = std::panic::catch_unwind(|| {
        let _guard = p.state.lock().unwrap();
        panic!("synthetic recording poison");
    });
    let mut provider = RecordingProvider::new(
        Box::new(Ready(calls)),
        poisoned.clone(),
        vec![],
        ForbiddenByRole::default(),
    );
    assert_eq!(
        provider.poll(&request, &cancel),
        Poll::Ready(Ok(b"{}".to_vec()))
    );
    assert!(poisoned.lost.load(Ordering::Relaxed));
}
