// Temporarily include the pure module until the coordinator wires the shared public library.
pub use locallore::contracts;
#[path = "../src/turn_trace.rs"]
mod turn_trace;
use contracts::Scope;
use turn_trace::*;

fn scope() -> Scope {
    Scope {
        story: "synthetic-story".into(),
        branch: "root".into(),
    }
}
fn identity(attempt: u32) -> AttemptIdentity {
    AttemptIdentity {
        scope: scope(),
        base_revision: 3,
        observer: "player".into(),
        turn: "synthetic-turn".into(),
        attempt,
    }
}
fn select() -> Selection {
    Selection {
        scope: scope(),
        base_revision: 3,
        observer: "player".into(),
        turn: None,
        attempt: None,
    }
}
fn reader() -> Reader {
    Reader::scoped(scope(), "player".into())
}
fn enabled() -> TraceRing {
    let mut ring = TraceRing::default();
    ring.set_enabled(true);
    ring
}
fn begin(ring: &mut TraceRing, attempt: u32) -> AttemptHandle {
    let result = ring.begin(identity(attempt), Provenance::default());
    assert_eq!(result.status, HookStatus::Recorded);
    result.handle.unwrap()
}

#[test]
fn default_is_disabled_and_full_capture_never_claims_support() {
    let mut ring = TraceRing::default();
    let result = ring.begin(identity(0), Provenance::default());
    assert_eq!(result.status, HookStatus::Disabled);
    assert!(result.handle.is_none());
    assert_eq!(ring.request_full_capture(), HookStatus::Unsupported);
    let snapshot = ring.read(&select(), &reader()).unwrap();
    assert_eq!(snapshot.version, TRACE_VERSION);
    assert_eq!(snapshot.status, CaptureStatus::Disabled);
    assert!(snapshot.attempts.is_empty());
    assert!(!snapshot.exact_reconstruction);
}

#[test]
fn metadata_types_reject_paths_unicode_raw_errors_and_invalid_widths() {
    for value in ["", "C:\\private\\model", "file/path", "a b", "a\n", "λ"] {
        assert!(Label::new(value).is_none());
        assert!(IdentityHash::sha256(value).is_none());
        assert!(Revision::new(value).is_none());
    }
    assert!(Label::new(&"a".repeat(65)).is_none());
    assert!(IdentityHash::sha256(&"a".repeat(40)).is_none());
    assert!(Revision::new(&"a".repeat(64)).is_none());
    assert!(IdentityHash::sha256(&"g".repeat(64)).is_none());
    assert_eq!(
        serde_json::to_string(&IdentityHash::sha256(&"A".repeat(64)).unwrap()).unwrap(),
        format!("\"{}\"", "a".repeat(64))
    );
    assert!(Label::new("profile-v1.0_test").is_some());
    assert!(Revision::new(&"a".repeat(40)).is_some());
}

#[test]
fn invalid_attempt_metadata_is_dropped_without_touching_retained_attempts() {
    let mut ring = enabled();
    begin(&mut ring, 0);
    let before = ring.read(&select(), &reader()).unwrap();
    for field in 0..4 {
        let mut key = identity(1);
        match field {
            0 => key.scope.story = "private/path".into(),
            1 => key.scope.branch = "b\n".into(),
            2 => key.observer = "".into(),
            _ => key.turn = "x".repeat(65),
        }
        let result = ring.begin(key, Provenance::default());
        assert_eq!(result.status, HookStatus::InvalidMetadata);
        assert!(result.handle.is_none());
    }
    assert_eq!(before, ring.read(&select(), &reader()).unwrap());
}

#[test]
fn scope_and_observer_are_independently_authorized_even_when_disabled() {
    for mut ring in [TraceRing::default(), enabled()] {
        let result = ring.begin(identity(0), Provenance::default());
        if result.status == HookStatus::Recorded {
            assert!(result.handle.is_some());
        }
        let mut q = select();
        q.observer = "mira".into();
        assert_eq!(ring.read(&q, &reader()), Err(ReadError::Forbidden));
        let lab = Reader::story_lab(scope());
        assert!(ring.read(&q, &lab).unwrap().attempts.is_empty());
        q.scope.story = "sibling-story".into();
        assert_eq!(ring.read(&q, &lab), Err(ReadError::Scope));
        let malformed = Reader::scoped(scope(), "bad/path".into());
        q = select();
        q.observer = "bad/path".into();
        assert_eq!(ring.read(&q, &malformed), Err(ReadError::InvalidSelection));
    }
}

#[test]
fn changed_observer_never_relabels_a_player_attempt() {
    let mut ring = enabled();
    begin(&mut ring, 0);
    let mut q = select();
    q.observer = "mira".into();
    let mira = Reader::scoped(scope(), "mira".into());
    let result = ring.read(&q, &mira).unwrap();
    assert!(result.attempts.is_empty());
    assert!(!serde_json::to_string(&result)
        .unwrap()
        .contains("synthetic-turn"));
    let lab = Reader::story_lab(scope());
    assert!(ring.read(&q, &lab).unwrap().attempts.is_empty());
    q = select();
    assert_eq!(ring.read(&q, &mira), Err(ReadError::Forbidden));
    assert_eq!(ring.read(&q, &lab).unwrap().attempts.len(), 1);
}

#[test]
fn selection_binds_base_revision_turn_attempt_and_branch() {
    let mut ring = enabled();
    begin(&mut ring, 0);
    begin(&mut ring, 1);
    let mut q = select();
    q.attempt = Some(1);
    assert_eq!(ring.read(&q, &reader()).unwrap().attempts.len(), 1);
    q.attempt = Some(99);
    assert!(ring.read(&q, &reader()).unwrap().attempts.is_empty());
    q = select();
    q.base_revision = 4;
    assert!(ring.read(&q, &reader()).unwrap().attempts.is_empty());
    q = select();
    q.turn = Some("other-turn".into());
    assert!(ring.read(&q, &reader()).unwrap().attempts.is_empty());
    q.turn = Some("../bad".into());
    assert_eq!(ring.read(&q, &reader()), Err(ReadError::InvalidSelection));
    q = select();
    q.scope.branch = "sibling".into();
    assert_eq!(ring.read(&q, &reader()), Err(ReadError::Scope));
}

#[test]
fn hashes_and_unknowns_are_honest_fixed_provenance_not_story_payloads() {
    let mut ring = enabled();
    let provenance = Provenance {
        model_sha256: IdentityHash::sha256(&"1".repeat(64)),
        engine_revision: Revision::new(&"2".repeat(40)),
        profile_label: Label::new("synthetic-fixed-profile-v1"),
        ..Provenance::default()
    };
    ring.begin(identity(0), provenance.clone());
    let data = &ring.read(&select(), &reader()).unwrap().attempts[0];
    assert_eq!(data.provenance, provenance);
    let json = serde_json::to_value(data).unwrap();
    assert!(json["provenance"]["runtime_revision"].is_null());
    assert!(json["provenance"]["prompt_sha256"].is_null());
    for absent in [
        "prompt",
        "text",
        "output",
        "context",
        "path",
        "excluded_ids",
        "excluded_count",
    ] {
        assert!(json.get(absent).is_none());
    }
}

#[test]
fn every_stage_and_failure_outcome_remains_typed_and_monotonic() {
    let mut ring = enabled();
    let handle = begin(&mut ring, 0);
    let stages = [
        Stage::Intent,
        Stage::Retrieval,
        Stage::Context,
        Stage::Director,
        Stage::Parsing,
        Stage::Validation,
        Stage::Repair,
        Stage::AcceptedCandidate,
        Stage::Narration,
        Stage::NarrationValidation,
        Stage::AtomicCommit,
        Stage::MemoryMaintenance,
    ];
    let outcomes = [
        Outcome::Accepted,
        Outcome::NotRun,
        Outcome::Accepted,
        Outcome::Failed,
        Outcome::Rejected,
        Outcome::Rejected,
        Outcome::Accepted,
        Outcome::Accepted,
        Outcome::Cancelled,
        Outcome::Stale,
        Outcome::NotRun,
        Outcome::Truncated,
    ];
    for (stage, outcome) in stages.into_iter().zip(outcomes) {
        assert_eq!(
            ring.record(
                &handle,
                stage,
                outcome,
                Counts::default(),
                Some(ErrorCategory::Unknown)
            ),
            HookStatus::Recorded
        );
    }
    assert_eq!(ring.finish(&handle, Outcome::Failed), HookStatus::Recorded);
    let data = &ring.read(&select(), &reader()).unwrap().attempts[0];
    let mut last = 0;
    for record in &data.stages {
        assert!(record.started_us >= last);
        last = record.started_us + record.duration_us;
    }
    assert!(data.elapsed_us >= last);
    assert_eq!(data.outcome, Outcome::Failed);
}

#[test]
fn measured_and_estimated_tokens_stay_distinct() {
    let mut ring = enabled();
    let handle = begin(&mut ring, 0);
    let counts = Counts {
        eligible_records: 2,
        input_tokens: Some(TokenCount {
            value: 10,
            basis: TokenBasis::Measured,
        }),
        output_tokens: Some(TokenCount {
            value: 12,
            basis: TokenBasis::Estimated,
        }),
        operations: 1,
        repairs: 1,
    };
    ring.record(&handle, Stage::Director, Outcome::Accepted, counts, None);
    let data = &ring.read(&select(), &reader()).unwrap().attempts[0];
    assert_eq!(data.stages[0].counts, counts);
}

#[test]
fn duplicate_attempt_and_foreign_handles_cannot_corrupt_retained_trace() {
    let mut a = enabled();
    let mut b = enabled();
    let handle = begin(&mut a, 0);
    begin(&mut b, 0);
    assert_eq!(
        a.begin(identity(0), Provenance::default()).status,
        HookStatus::Dropped
    );
    let before = b.read(&select(), &reader()).unwrap();
    assert_eq!(
        b.record(
            &handle,
            Stage::Intent,
            Outcome::Accepted,
            Counts::default(),
            None
        ),
        HookStatus::Dropped
    );
    assert_eq!(b.finish(&handle, Outcome::Committed), HookStatus::Dropped);
    assert_eq!(b.read(&select(), &reader()).unwrap(), before);
}

#[test]
fn clear_and_disable_delete_data_and_invalidate_old_handles() {
    let mut ring = enabled();
    let old = begin(&mut ring, 0);
    ring.clear();
    assert!(ring.read(&select(), &reader()).unwrap().attempts.is_empty());
    let new = begin(&mut ring, 0);
    assert_eq!(ring.finish(&old, Outcome::Cancelled), HookStatus::Dropped);
    ring.set_enabled(false);
    assert!(ring.read(&select(), &reader()).unwrap().attempts.is_empty());
    assert_eq!(ring.finish(&new, Outcome::Cancelled), HookStatus::Disabled);
    assert_eq!(
        ring.record(
            &new,
            Stage::Intent,
            Outcome::Failed,
            Counts::default(),
            None
        ),
        HookStatus::Disabled
    );
    ring.set_enabled(true);
    assert_eq!(ring.finish(&new, Outcome::Cancelled), HookStatus::Dropped);
}

#[test]
fn stage_cap_marks_truncation_and_never_claims_a_commit() {
    let mut ring = TraceRing::new(Config::new(2, 1, MAX_BYTES).unwrap());
    ring.set_enabled(true);
    let handle = begin(&mut ring, 0);
    assert_eq!(
        ring.record(
            &handle,
            Stage::Intent,
            Outcome::Accepted,
            Counts::default(),
            None
        ),
        HookStatus::Recorded
    );
    assert_eq!(
        ring.record(
            &handle,
            Stage::Director,
            Outcome::Accepted,
            Counts::default(),
            None
        ),
        HookStatus::Truncated
    );
    assert_eq!(
        ring.finish(&handle, Outcome::Committed),
        HookStatus::Truncated
    );
    let snapshot = ring.read(&select(), &reader()).unwrap();
    assert_eq!(snapshot.status, CaptureStatus::BoundedMetadataWindow);
    assert!(!snapshot.exact_reconstruction);
    assert_eq!(snapshot.attempts[0].outcome, Outcome::Truncated);
    assert!(snapshot.attempts[0].truncated);
    assert_eq!(snapshot.attempts[0].stages.len(), 1);
}

#[test]
fn oldest_attempt_eviction_is_bounded_and_stale_handle_drops() {
    let mut ring = TraceRing::new(Config::new(2, MAX_STAGES, MAX_BYTES).unwrap());
    ring.set_enabled(true);
    let old = begin(&mut ring, 0);
    begin(&mut ring, 1);
    begin(&mut ring, 2);
    assert_eq!(ring.finish(&old, Outcome::Committed), HookStatus::Dropped);
    let snapshot = ring.read(&select(), &reader()).unwrap();
    assert_eq!(snapshot.attempts.len(), 2);
    assert_eq!(snapshot.attempts[0].identity.attempt, 1);
    assert!(!snapshot.exact_reconstruction);
}

#[test]
fn whole_serialized_snapshot_including_wrapper_respects_byte_cap() {
    for bytes in [1024, 2048, MAX_BYTES] {
        let mut ring = TraceRing::new(Config::new(MAX_ATTEMPTS, MAX_STAGES, bytes).unwrap());
        ring.set_enabled(true);
        for n in 0..40 {
            let begun = ring.begin(identity(n), Provenance::default());
            if let Some(handle) = begun.handle {
                for _ in 0..MAX_STAGES + 1 {
                    ring.record(
                        &handle,
                        Stage::Director,
                        Outcome::Failed,
                        Counts {
                            eligible_records: u32::MAX,
                            input_tokens: Some(TokenCount {
                                value: u32::MAX,
                                basis: TokenBasis::Estimated,
                            }),
                            output_tokens: None,
                            operations: u16::MAX,
                            repairs: u8::MAX,
                        },
                        Some(ErrorCategory::Unavailable),
                    );
                    assert!(
                        serde_json::to_vec(&ring.read(&select(), &reader()).unwrap())
                            .unwrap()
                            .len()
                            <= bytes
                    );
                }
                ring.finish(&handle, Outcome::Failed);
            }
            assert!(
                serde_json::to_vec(&ring.read(&select(), &reader()).unwrap())
                    .unwrap()
                    .len()
                    <= bytes
            );
        }
    }
}

#[test]
fn retained_snapshot_is_detached_and_abandoned_attempt_is_honestly_running() {
    let mut ring = enabled();
    let handle = begin(&mut ring, 0);
    let before = ring.read(&select(), &reader()).unwrap();
    drop(handle);
    begin(&mut ring, 1);
    assert_eq!(before.attempts.len(), 1);
    assert_eq!(before.attempts[0].outcome, Outcome::Running);
    assert!(!before.exact_reconstruction);
}

#[test]
fn config_rejects_unbounded_or_impossible_caps() {
    assert!(Config::new(0, 1, MAX_BYTES).is_none());
    assert!(Config::new(MAX_ATTEMPTS + 1, 1, MAX_BYTES).is_none());
    assert!(Config::new(1, 0, MAX_BYTES).is_none());
    assert!(Config::new(1, MAX_STAGES + 1, MAX_BYTES).is_none());
    assert!(Config::new(1, 1, 1023).is_none());
    assert!(Config::new(1, 1, MAX_BYTES + 1).is_none());
}

#[test]
fn collector_cannot_mutate_engine_state_and_terminal_hooks_do_not_reopen_attempt() {
    let engine = locallore::engine::Engine::new(
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap(),
    )
    .unwrap();
    let before = engine.canonical_bytes();
    let mut ring = enabled();
    let handle = begin(&mut ring, 0);
    assert_eq!(ring.finish(&handle, Outcome::Running), HookStatus::Dropped);
    assert_eq!(
        ring.finish(&handle, Outcome::Cancelled),
        HookStatus::Recorded
    );
    assert_eq!(
        ring.finish(&handle, Outcome::Committed),
        HookStatus::Dropped
    );
    assert_eq!(
        ring.record(
            &handle,
            Stage::AtomicCommit,
            Outcome::Committed,
            Counts::default(),
            None
        ),
        HookStatus::Dropped
    );
    ring.clear();
    assert_eq!(before, engine.canonical_bytes());
}

#[test]
fn fixed_error_categories_never_accept_a_free_form_exception() {
    let categories = [
        ErrorCategory::Malformed,
        ErrorCategory::Version,
        ErrorCategory::Scope,
        ErrorCategory::Rule,
        ErrorCategory::Agency,
        ErrorCategory::Narration,
        ErrorCategory::Storage,
        ErrorCategory::Unavailable,
        ErrorCategory::Busy,
        ErrorCategory::Deadline,
        ErrorCategory::Cancelled,
        ErrorCategory::Stale,
        ErrorCategory::Internal,
        ErrorCategory::Unknown,
    ];
    for category in categories {
        let bytes = serde_json::to_string(&category).unwrap();
        assert!(bytes
            .bytes()
            .all(|c| c.is_ascii_lowercase() || c == b'"' || c == b'_'));
    }
}

#[test]
fn core_error_mapping_preserves_existing_diagnostic_categories_without_display_text() {
    use contracts::Error;
    let cases = [
        (Error::Version, ErrorCategory::Version),
        (Error::Scope, ErrorCategory::Scope),
        (Error::Stale, ErrorCategory::Stale),
        (Error::RetryMismatch, ErrorCategory::RetryMismatch),
        (Error::Malformed, ErrorCategory::Malformed),
        (Error::TooLarge, ErrorCategory::TooLarge),
        (Error::Agency, ErrorCategory::Agency),
        (Error::AuthorUiRequired, ErrorCategory::AuthorUiRequired),
        (
            Error::ClarificationRequired,
            ErrorCategory::ClarificationRequired,
        ),
        (Error::UnknownReference, ErrorCategory::UnknownReference),
        (Error::DeadActor, ErrorCategory::DeadActor),
        (Error::Location, ErrorCategory::Location),
        (Error::Inventory, ErrorCategory::Inventory),
        (Error::Resource, ErrorCategory::Resource),
        (Error::Ability, ErrorCategory::Ability),
        (Error::Knowledge, ErrorCategory::Knowledge),
        (Error::Rule, ErrorCategory::Rule),
        (Error::Cancelled, ErrorCategory::Cancelled),
        (Error::Provider, ErrorCategory::Provider),
        (Error::Timeout, ErrorCategory::Deadline),
        (Error::Narration, ErrorCategory::Narration),
        (Error::CorruptHistory, ErrorCategory::CorruptHistory),
    ];
    for (source, category) in cases {
        assert_eq!(ErrorCategory::from_engine(&source), category);
    }
}

#[test]
fn explicit_truncated_terminal_and_maximum_metadata_fit_or_drop_honestly() {
    let mut ring = enabled();
    let mut key = identity(u32::MAX);
    key.scope.story = "s".repeat(64);
    key.scope.branch = "b".repeat(64);
    key.observer = "p".repeat(64);
    key.turn = "t".repeat(64);
    key.base_revision = u64::MAX;
    let hash = IdentityHash::sha256(&"f".repeat(64));
    let revision = Revision::new(&"e".repeat(40));
    let label = Label::new(&"L".repeat(64));
    let provenance = Provenance {
        model_sha256: hash.clone(),
        worker_sha256: hash.clone(),
        profile_sha256: hash.clone(),
        config_sha256: hash.clone(),
        prompt_sha256: hash.clone(),
        schema_sha256: hash,
        runtime_revision: revision.clone(),
        engine_revision: revision,
        profile_label: label.clone(),
        prompt_label: label.clone(),
        schema_label: label,
    };
    let handle = ring.begin(key.clone(), provenance).handle.unwrap();
    assert_eq!(
        ring.finish(&handle, Outcome::Truncated),
        HookStatus::Recorded
    );
    let selection = Selection {
        scope: key.scope.clone(),
        base_revision: key.base_revision,
        observer: key.observer.clone(),
        turn: Some(key.turn),
        attempt: Some(key.attempt),
    };
    let snapshot = ring
        .read(&selection, &Reader::scoped(key.scope, key.observer))
        .unwrap();
    assert!(snapshot.attempts[0].truncated);
    assert!(serde_json::to_vec(&snapshot).unwrap().len() <= MAX_BYTES);
}
