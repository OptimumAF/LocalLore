// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen private dependency extraction tests. SOURCE-ONLY / UNRUN at handoff.
//! Actual typed Core/Store history; no factory, provider, runtime, ledger or SQL.
//! Root registers this module and supplies the frozen DependencyJob/helper.
use super::*;

struct Fixture {
    directory: PathBuf,
    path: PathBuf,
    full: Engine,
}
impl Fixture {
    fn new(learn_beacon: bool) -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-dependency-review-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
        ));
        fs::create_dir(&directory).unwrap();
        let path = directory.join("actual-history.sqlite");
        let corpus = suite().unwrap();
        let mut store = Store::open_application(&path).unwrap();
        store
            .create_story("Synthetic dependency extraction", corpus.seed().clone())
            .unwrap();
        let mut full = store.resume(&corpus.seed().scope).unwrap().engine;
        let mut commands = vec![("dependency-setup-wait", Command::Wait { ticks: 1 })];
        if learn_beacon {
            commands.push((
                "dependency-setup-learn",
                Command::Learn {
                    ability: "beacon".into(),
                },
            ));
        }
        for (turn, command) in commands {
            let request = full.request(turn, Intent::Actions(vec![command]));
            let proposal = Engine::proposal(&request).unwrap();
            let preview = full.preview(&request, &proposal).unwrap();
            store.begin_turn(&request).unwrap();
            let actual = store
                .commit_turn(&request, &proposal, preview.narration())
                .unwrap();
            assert!(actual == preview);
            full = store.resume(&corpus.seed().scope).unwrap().engine;
        }
        assert_eq!(full.receipts().len(), if learn_beacon { 2 } else { 1 });
        drop(store);
        let reopened = engine(&path, full.scope()).unwrap();
        assert!(reopened.receipts() == full.receipts());
        Self {
            directory,
            path,
            full: reopened,
        }
    }
    fn inventory(&self) -> BTreeMap<String, Vec<u8>> {
        let mut files = BTreeMap::new();
        let mut total = 0;
        for entry in fs::read_dir(&self.directory).unwrap() {
            let entry = entry.unwrap();
            let metadata = fs::symlink_metadata(entry.path()).unwrap();
            assert!(metadata.is_file() && !metadata.file_type().is_symlink());
            assert!(metadata.len() <= 8 * 1024 * 1024 && files.len() < 16);
            let bytes = fs::read(entry.path()).unwrap();
            total += bytes.len();
            assert!(total <= 16 * 1024 * 1024);
            files.insert(entry.file_name().into_string().unwrap(), bytes);
        }
        files
    }
    fn unchanged(&self, files: &BTreeMap<String, Vec<u8>>, before: &Engine) {
        assert!(
            self.inventory() == *files,
            "pure helper changed actual Store files"
        );
        assert_eq!(self.full.canonical_bytes(), before.canonical_bytes());
        assert!(self.full.receipts() == before.receipts());
        assert!(
            self.full.accepted_history_basis().unwrap() == before.accepted_history_basis().unwrap()
        );
        let cold = engine(&self.path, before.scope()).unwrap();
        assert_eq!(cold.canonical_bytes(), before.canonical_bytes());
        assert!(cold.receipts() == before.receipts());
        assert!(cold.accepted_history_basis().unwrap() == before.accepted_history_basis().unwrap());
        assert!(
            self.inventory() == *files,
            "cold read changed actual Store files"
        );
    }
    fn finish(self) {
        drop(self.full);
        fs::remove_dir_all(self.directory).unwrap();
    }
}

fn index_for(corpus: &protocol::FrozenSuite, text: &str) -> usize {
    corpus
        .steps()
        .iter()
        .position(|step| step.text() == text)
        .unwrap()
}
fn read_dependency(
    full: &Engine,
    corpus: &protocol::FrozenSuite,
    index: usize,
    arm: &str,
    policy: ContextPolicy,
    binding: &str,
    profile: &PlayProfile,
) -> Result<Option<StoredTurn>> {
    // The frozen seam intentionally has no external execution/resource inputs.
    dependency_turn(DependencyJob {
        full,
        index,
        arm,
        policy,
        binding,
        step: &corpus.steps()[index],
        profile,
    })
}
fn assert_dependency(
    turn: &StoredTurn,
    full: &Engine,
    step: &protocol::Step,
    index: usize,
    arm: &str,
    policy: ContextPolicy,
    binding: &str,
) {
    assert_eq!(turn.version, 2);
    assert_eq!(turn.binding, binding);
    assert_eq!(turn.index, index);
    assert_eq!(turn.arm, arm);
    let request = step.request(full);
    assert!(turn.request == request);
    assert_eq!(turn.request.scope, *full.scope());
    assert_eq!(turn.request.turn, step.id());
    assert_eq!(turn.request.expected_revision, full.revision());
    assert!(
        matches!(&turn.request.intent, Intent::FreeText { kind, text }
        if *kind == step.kind() && text == step.text())
    );
    assert_eq!(turn.before_head, full.revision());
    assert_eq!(turn.after_head, full.revision());
    assert!(turn.capture_file.is_none() && turn.recording_file.is_none());
    let row = &turn.row;
    assert_eq!(row.turn, step.id());
    assert_eq!(row.scene, step.scene());
    assert_eq!(row.arm, arm);
    assert_eq!(row.policy, policy);
    assert_eq!(row.phase, "not_run_dependency");
    assert_eq!(
        row.expected,
        serde_json::to_string(step.expected()).unwrap()
    );
    assert!(row.error.is_none() && !row.passed && !row.policy_matches);
    assert_eq!(
        row.failures,
        ["not_run_dependency", "no_matching_current_policy_receipt"]
    );
    // Existing make_row semantics: this path explicitly did not run roles.
    // Its elapsed-zero sentinel is not a measured native/model latency.
    assert_eq!(row.roles, 0);
    assert!(row.roles_known && !row.recovered_without_checkpoint);
    assert!(row.admission.is_none());
    assert_eq!(row.elapsed_ms, 0);
    assert!(row.first_final_response_ms.is_none() && row.commit_elapsed_ms.is_none());
    assert!(row.context_evidence_available && row.privacy_passed);
    assert_eq!(row.context_requirement, "not_applicable_dependency");
    assert!(row.capture_sha256.is_none() && row.recording_sha256.is_none());
    assert!(row.raw_sha256.is_empty() && row.role_metrics.is_none() && row.trace.is_none());
    assert!(row.actual_receipt_sha256.is_none() && row.narration.is_none());
    assert!(row.fallback.is_none() && row.repairs.is_none() && row.stages.is_empty());
    assert!(row.quality_flags.is_empty());
    assert!(row.mandatory_sha256.is_none() && row.optional_detail_selected.is_none());
    assert!(row.director_private_target_present.is_none() && row.selected_context_bytes.is_none());
    assert!(row.estimated_context_tokens.is_none() && row.forwarded_director_estimates.is_none());
    assert!(row.source_fallback_reason.is_none() && row.compiler_fallback_reason.is_none());
    assert_eq!(
        row.input_semantic_sha256,
        v2::semantic_input(full, &request).unwrap()
    );
    assert_eq!(
        row.output_semantic_sha256,
        v2::semantic_output(full).unwrap()
    );
    assert_eq!(row.mechanical_sha256, v2::mechanical_output(full).unwrap());
}

#[test]
fn actual_missing_learn_dependency_keeps_full_identity_honest_row_and_durable_history() {
    let fixture = Fixture::new(false);
    let corpus = suite().unwrap();
    let index = index_for(&corpus, "I use beacon.");
    let step = &corpus.steps()[index];
    assert!(matches!(step.expected(), protocol::Expected::Accepted(_)));
    assert!(protocol::reference_proposal(&fixture.full, step).is_err());
    let before = fixture.full.clone();
    let files = fixture.inventory();
    let binding = "a".repeat(64);
    let profile = LaneFactory::ScriptedBaseline.profile().unwrap();
    for (arm, policy) in ARM_NAMES.into_iter().zip(POLICIES) {
        let turn = read_dependency(
            &fixture.full,
            &corpus,
            index,
            arm,
            policy,
            &binding,
            &profile,
        )
        .unwrap()
        .expect("actual missing prerequisite must produce dependency row");
        assert_dependency(&turn, &before, step, index, arm, policy, &binding);
    }
    fixture.unchanged(&files, &before);
    fixture.finish();
}

#[test]
fn actual_learned_accepted_step_and_actual_core_guard_are_not_dependency_rows() {
    let fixture = Fixture::new(true);
    let corpus = suite().unwrap();
    let accepted = index_for(&corpus, "I use beacon.");
    assert!(protocol::reference_proposal(&fixture.full, &corpus.steps()[accepted]).is_ok());
    let guard = index_for(&corpus, "I use blink.");
    assert!(matches!(
        corpus.steps()[guard].expected(),
        protocol::Expected::GuardRejected(protocol::GuardRejection::Ability)
    ));
    assert!(matches!(
        protocol::reference_proposal(&fixture.full, &corpus.steps()[guard]),
        Err(locallore::contracts::Error::Ability)
    ));
    let before = fixture.full.clone();
    let files = fixture.inventory();
    let profile = LaneFactory::ScriptedBaseline.profile().unwrap();
    for index in [accepted, guard] {
        assert!(read_dependency(
            &fixture.full,
            &corpus,
            index,
            "left",
            POLICIES[0],
            &"b".repeat(64),
            &profile
        )
        .unwrap()
        .is_none());
    }
    fixture.unchanged(&files, &before);
    fixture.finish();
}

#[test]
fn invalid_profile_is_fixed_profile_error_without_mutating_dependency_or_guard_history() {
    let fixture = Fixture::new(false);
    let corpus = suite().unwrap();
    let before = fixture.full.clone();
    let files = fixture.inventory();
    let mut profile = LaneFactory::ScriptedBaseline.profile().unwrap();
    profile.context_tokens = 0;
    assert!(profile.validate().is_err());
    for text in ["I use beacon.", "I learn beacon.", "I use blink."] {
        let result = read_dependency(
            &fixture.full,
            &corpus,
            index_for(&corpus, text),
            "right",
            POLICIES[1],
            &"c".repeat(64),
            &profile,
        );
        assert!(matches!(result, Err(ref error) if error == "Profile"));
    }
    fixture.unchanged(&files, &before);
    fixture.finish();
}

#[cfg(feature = "local-model")]
#[test]
fn approved_native_profile_can_describe_pure_dependency_without_runtime_or_assets() {
    let fixture = Fixture::new(false);
    let corpus = suite().unwrap();
    let index = index_for(&corpus, "I use beacon.");
    let before = fixture.full.clone();
    let files = fixture.inventory();
    let profile = native_profile().unwrap();
    assert!(profile.validate().is_ok());
    assert_eq!(profile.id, locallore_local_runtime::PROFILE);
    let binding = "d".repeat(64);
    let turn = read_dependency(
        &fixture.full,
        &corpus,
        index,
        "right",
        POLICIES[1],
        &binding,
        &profile,
    )
    .unwrap()
    .expect("model-free native-profile dependency");
    assert_dependency(
        &turn,
        &before,
        &corpus.steps()[index],
        index,
        "right",
        POLICIES[1],
        &binding,
    );
    fixture.unchanged(&files, &before);
    fixture.finish();
}
