// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST SOURCE FREEZE: UNCOMPILED/UNRUN; optional-input private API is future.
//! Actual existing scripted Host prepare/capture/cancel or failed Director.
//! No committed receipt, SQL edit, model/runtime, new fault or public hook.
use super::*;
use crate::local_lane::{LaneFactory, TestFault};
use crate::local_recording::{ForbiddenByRole, Recording};
use std::sync::{
    atomic::{AtomicU64, Ordering},
    Arc,
};

static NEXT_NONCOMMIT: AtomicU64 = AtomicU64::new(0);
#[derive(Clone, Copy)]
enum Attempt {
    CleanCancelled,
    SecretCancelled,
    FailedDirector,
}
struct Diagnostic {
    directory: PathBuf,
    before: Engine,
    after: Engine,
    profile: PlayProfile,
    capture: Value,
    recording: RecordingFile,
    phase: String,
    error: Option<String>,
}

fn diagnostic(kind: Attempt) -> Diagnostic {
    let directory = std::env::temp_dir().join(format!(
        "scene-v4-noncommit-privacy-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT_NONCOMMIT.fetch_add(1, Ordering::Relaxed),
    ));
    fs::create_dir(&directory).unwrap();
    let path = directory.join("synthetic.sqlite");
    let corpus = suite().unwrap();
    let step = &corpus.steps()[0];
    ensure_database(&path, corpus.seed(), &[]).unwrap();
    let before = engine(&path, &corpus.seed().scope).unwrap();
    let request = step.request(&before);
    let proposal = protocol::reference_proposal(&before, step).unwrap();
    let narration = before.preview(&request, &proposal).ok().map_or_else(
        || "No outcome.".into(),
        |approved| approved.narration().to_owned(),
    );
    let factory = match kind {
        Attempt::CleanCancelled => LaneFactory::ScriptedBaseline,
        Attempt::SecretCancelled => LaneFactory::TestFault(TestFault::SecretNarrator),
        Attempt::FailedDirector => LaneFactory::TestFault(TestFault::WrongCommand),
    };
    let profile = factory.profile().unwrap();
    let spec = LocalStep {
        id: step.id().into(),
        branch: before.scope().branch.clone(),
        kind: step.kind(),
        text: step.text().into(),
        error: None,
        commands: proposal.commands.clone(),
        narration,
        prohibited_narration: vec!["SECRET-TIDE-731".into()],
        cancel: false,
        prompt_targets: vec![],
        assertions: vec![],
    };
    let recording = Arc::new(Recording::default());
    let observed = recording.clone();
    let director = EXCLUSIONS.iter().map(|s| (*s).into()).collect::<Vec<_>>();
    let mut narrator = director.clone();
    narrator.push("SECRET-TIDE-731".into());
    let forbidden = ForbiddenByRole { director, narrator };
    let provider = Arc::new(move || factory.provider(&spec, observed.clone(), forbidden.clone()));
    let host = Arc::new(locallore_workspace::open(&path, true).unwrap());
    let owned = OwnedHost(host.clone());
    let session = resume_session(&host, before.scope()).unwrap();
    host.configure_fixture_provider_with_construction(
        profile.clone(),
        provider,
        host_construction(ComparisonArmV4::LiteralSceneV1),
    )
    .unwrap();
    for command in [
        json!({"op":"trace_configure","session":session,"scope":before.scope(),"expected_head":before.revision(),"enabled":true}),
        json!({"op":"trace_capture_configure","session":session,"scope":before.scope(),"expected_head":before.revision(),"enabled":true,"consent":true}),
    ] {
        assert_eq!(call(&host, command)["status"], "ok");
    }
    let queued = call(
        &host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    assert_eq!(queued["status"], "ok");
    assert_eq!(queued["data"]["phase"], "queued");
    let prepared = op(&host, &session, before.scope(), step.id(), "prepare");
    assert_eq!(prepared["status"], "ok");
    let should_fail = matches!(kind, Attempt::FailedDirector);
    assert_eq!(
        prepared["data"]["phase"],
        if should_fail { "failed" } else { "ready" }
    );
    // Take the real owner-authorized diagnostic copy while the actual attempt
    // is prepared/failed. A ready candidate is never sent to commit.
    let (capture, _) = private_read(&host, &session, &before, &request);
    let capture = capture.unwrap();
    assert_eq!(capture["status"], "ok");
    assert_eq!(capture["data"]["details"]["status"], "recorded");
    let recording = captured_recording(&directory, 0, &recording).unwrap();
    validate_recording(&directory, 0, &recording).unwrap();
    let terminal = if should_fail {
        prepared
    } else {
        op(&host, &session, before.scope(), step.id(), "cancel")
    };
    let mut store = Store::open_read_only(&path).unwrap();
    let turn = store.lookup_turn(before.scope(), step.id()).unwrap();
    assert!(turn.receipt.is_none());
    assert_eq!(
        turn.phase,
        if should_fail {
            locallore_storage::TurnPhase::Failed
        } else {
            locallore_storage::TurnPhase::Cancelled
        }
    );
    assert_eq!(
        terminal["data"]["phase"],
        if should_fail { "failed" } else { "cancelled" }
    );
    let after = store.resume(before.scope()).unwrap().engine;
    assert_eq!(
        before.accepted_history_basis().unwrap(),
        after.accepted_history_basis().unwrap()
    );
    assert_eq!(before.canonical_records(), after.canonical_records());
    assert_eq!(after.canonical_record_count(), 0);
    assert_eq!(before.canonical_bytes(), after.canonical_bytes());
    drop(store);
    drop(owned); // Existing Host close guard, not a new runtime/cleanup owner.
    Diagnostic {
        directory,
        before,
        after,
        profile,
        capture,
        recording,
        phase: terminal["data"]["phase"].as_str().unwrap().into(),
        error: terminal["data"]["error"].as_str().map(str::to_owned),
    }
}

fn same_kind(actual: FinitePrivacy, expected: FinitePrivacy, why: &str) {
    // Existing private FinitePrivacy intentionally need not implement Debug.
    assert!(actual == expected, "{why}");
}
fn derived_row(d: &Diagnostic, recording: &RecordingFile, capture: Option<&Value>) -> TurnReportV4 {
    let corpus = suite().unwrap();
    make_row4(Observation4 {
        dir: &d.directory,
        step: &corpus.steps()[0],
        arm: "left",
        construction: ComparisonArmV4::LiteralSceneV1,
        before: &d.before,
        after: &d.after,
        phase: &d.phase,
        error: d.error.clone(),
        receipt: None,
        recording: Some(recording),
        capture,
        trace: None,
        // Classification only: no producer ledger/invocation/timing is claimed.
        admission: None,
        elapsed_ms: 0,
        first_final_response_ms: None,
        commit_elapsed_ms: None,
        profile: &d.profile,
        recovered: false,
    })
    .unwrap()
}
fn classified_failure(row: &TurnReportV4, expected: &str, excluded: &str) {
    assert!(!row.passed);
    assert_eq!(row.construction_evidence_status, Status::Unavailable);
    assert_eq!(
        row.privacy_evidence_status,
        v4::PrivacyEvidenceStatusV4::Unavailable
    );
    assert!(row.actual_receipt_sha256.is_none());
    assert!(row.narrator_prompt_sha256.is_none());
    assert!(row.failures.iter().any(|failure| failure == expected));
    assert!(!row.failures.iter().any(|failure| failure == excluded));
}
const VIOLATION: &str = "observer_or_output_privacy_violation";
const UNAVAILABLE: &str = "observer_or_output_privacy_evidence_unavailable";

#[test]
fn actual_cancelled_secret_flags_remain_observed_without_receipt_or_capture() {
    let d = diagnostic(Attempt::SecretCancelled);
    assert!(d.recording.forbidden_narrator_output);
    same_kind(
        finite_privacy(&d.directory, &d.recording, Some(&d.capture), None),
        FinitePrivacy::Violation,
        "cancelled attempt's real recorded sentinel flag is retained",
    );
    same_kind(
        finite_privacy(&d.directory, &d.recording, None, None),
        FinitePrivacy::Violation,
        "missing optional details/receipt cannot erase an observed flag",
    );
    classified_failure(
        &derived_row(&d, &d.recording, Some(&d.capture)),
        VIOLATION,
        UNAVAILABLE,
    );
}

#[test]
fn actual_cancelled_raw_sentinel_survives_missing_capture_and_false_flag() {
    let d = diagnostic(Attempt::SecretCancelled);
    let mut recording = d.recording.clone();
    recording.forbidden_director_prompt = false;
    recording.forbidden_narrator_prompt = false;
    recording.forbidden_narrator_output = false;
    let raw = recording
        .raw
        .iter()
        .find(|raw| raw.role == "narrator")
        .unwrap();
    let bytes = read(&d.directory.join(&raw.file), 16_384).unwrap();
    assert_eq!(digest(&bytes), raw.sha256);
    assert!(std::str::from_utf8(&bytes)
        .unwrap()
        .contains("SECRET-TIDE-731"));
    // Only the diagnostic flag copy is altered. The actual provider's retained
    // raw bytes, actual cancellation and unchanged native history are genuine.
    same_kind(
        finite_privacy(&d.directory, &recording, None, None),
        FinitePrivacy::Violation,
        "actual retained bytes must still be examined when details are absent",
    );
    classified_failure(&derived_row(&d, &recording, None), VIOLATION, UNAVAILABLE);
}

#[test]
fn actual_clean_cancelled_and_failed_attempts_remain_unavailable_without_receipt() {
    for attempt in [Attempt::CleanCancelled, Attempt::FailedDirector] {
        let d = diagnostic(attempt);
        assert!(!d.recording.forbidden_director_prompt);
        assert!(!d.recording.forbidden_narrator_prompt);
        assert!(!d.recording.forbidden_narrator_output);
        same_kind(
            finite_privacy(&d.directory, &d.recording, Some(&d.capture), None),
            FinitePrivacy::Unavailable,
            "no receipt/source gate means no completed privacy qualification",
        );
        same_kind(
            finite_privacy(&d.directory, &d.recording, None, None),
            FinitePrivacy::Unavailable,
            "missing details are not a vacuous success",
        );
        classified_failure(
            &derived_row(&d, &d.recording, Some(&d.capture)),
            UNAVAILABLE,
            VIOLATION,
        );
    }
}

#[test]
fn retained_reported_violation_survives_lost_details_but_never_becomes_pass() {
    let d = diagnostic(Attempt::SecretCancelled);
    let mut lost = d.recording.clone();
    lost.lost = true;
    lost.captures.clear();
    lost.raw.clear();
    // Explicit diagnostic-loss copy, not a claim that files vanished at runtime.
    same_kind(
        finite_privacy(&d.directory, &lost, None, None),
        FinitePrivacy::Violation,
        "a retained positive report is not erased by other unknown evidence",
    );
    classified_failure(&derived_row(&d, &lost, None), VIOLATION, UNAVAILABLE);
}
