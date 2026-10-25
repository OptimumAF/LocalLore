//! Frozen source-only paired-resume oracles. UNCOMPILED/UNRUN at handoff.
//! All canonical fixtures use actual Core/Store APIs and bounded synthetic Play.
//! No model, SQL writer, invented receipt, corpus change or public test hook.
use locallore::{
    contracts::{Command, Error, Intent, PlayInputKind, Proposal, VERSION},
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
};
use locallore_eval::{
    local_lane::{comparison::*, LaneFactory},
    memory_comparison::{self as protocol, Expected},
};
use locallore_storage::Store;
use serde_json::json;
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    task::Poll,
};

const NEXT_INDEX: usize = 6;
const LAST_COMPLETED_INDEX: usize = 5;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn private_root(name: &str) -> PathBuf {
    let parent = std::env::temp_dir();
    let root = parent.join(format!(
        "locallore-comparison-resume-basis-{name}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    assert_eq!(root.parent(), Some(parent.as_path()));
    fs::create_dir(&root).unwrap();
    root
}

fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, out: &mut Inventory, total: &mut usize) {
        let mut entries: Vec<_> = fs::read_dir(dir)
            .unwrap()
            .map(|entry| entry.unwrap().path())
            .collect();
        entries.sort();
        for path in entries {
            assert!(out.len() < 4096, "bounded private fixture entry inventory");
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink(), "no fixture links");
            let key = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                out.insert(key, None);
                walk(root, &path, out, total);
            } else {
                assert!(metadata.is_file(), "ordinary fixture files only");
                assert!(metadata.len() <= 4 * 1024 * 1024, "bounded fixture file");
                let bytes = fs::read(path).unwrap();
                *total += bytes.len();
                assert!(*total <= 64 * 1024 * 1024, "bounded whole fixture");
                out.insert(key, Some(bytes));
            }
        }
    }
    let mut result = BTreeMap::new();
    walk(root, root, &mut result, &mut 0);
    result
}

fn no_new_turn_work(root: &Path) -> Inventory {
    inventory(root)
        .into_iter()
        .filter(|(path, _)| {
            let name = path.file_name().unwrap().to_string_lossy();
            name.starts_with("admission-")
                || name.starts_with("raw-")
                || name.contains("-capture")
                || name.contains("-recording")
        })
        .collect()
}

fn first_scene(name: &str) -> (PathBuf, ValidatedReference) {
    let root = private_root(name);
    let reference_dir = root.join("reference");
    let prepared = prepare_reference(&reference_dir, &Cancellation::default()).unwrap();
    assert_eq!(
        (prepared.accepted, prepared.guard_only, prepared.roles),
        (21, 3, 42)
    );
    assert_eq!(prepared.turns.len(), 24);
    assert!(prepared.turns.iter().all(|row| row.passed));
    let reference = open_reference(&reference_dir).unwrap();
    let initial = run_comparison(
        &root.join("run"),
        false,
        ComparisonKind::PairedSnapshots,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        Some(&reference),
    )
    .unwrap();
    assert_eq!(initial.completed_scenes, 1);
    assert_eq!(initial.turns.len(), 12);
    assert_eq!(initial.turns.iter().map(|row| row.roles).sum::<usize>(), 24);
    assert!(initial.turns.iter().all(|row| row.passed));
    assert!(!initial.completed);
    (root, reference)
}

fn read_engine(path: &Path) -> Engine {
    let scope = protocol::frozen_suite().unwrap().seed().scope.clone();
    Store::open_read_only(path)
        .unwrap()
        .resume(&scope)
        .unwrap()
        .engine
}

fn reference_before_next(root: &Path) -> Engine {
    let corpus = protocol::frozen_suite().unwrap();
    let reference = read_engine(&root.join("reference/synthetic.sqlite"));
    let next = reference
        .receipts()
        .iter()
        .find(|receipt| receipt.request().turn == corpus.steps()[NEXT_INDEX].id())
        .unwrap();
    reference
        .at_revision(next.request().expected_revision)
        .unwrap()
}

fn fixture_profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-resume-basis-fixture".into(),
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

// Only fixture construction uses this two-role script. The tested resume uses
// the existing closed LaneFactory::ScriptedBaseline and actual public runner.
struct WaitFixtureProvider {
    narration: String,
    events: Vec<u64>,
    director: usize,
    narrator: usize,
}
impl InferenceProvider for WaitFixtureProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        if cancel.is_cancelled() {
            return Poll::Ready(Err(Error::Cancelled));
        }
        let Input::Structured { role, .. } = &request.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        let value = match role.as_str() {
            "director" => {
                self.director += 1;
                json!({"commands":[{"op":"wait","ticks":1}]})
            }
            "narrator" => {
                self.narrator += 1;
                json!({"text":self.narration,"event_ids":self.events,"speaker":"narrator"})
            }
            _ => return Poll::Ready(Err(Error::Provider)),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}

fn plant_actual_wait(root: &Path, arm: &str, use_current_turn_id: bool) -> PathBuf {
    let corpus = protocol::frozen_suite().unwrap();
    let before = reference_before_next(root);
    let next = &corpus.steps()[NEXT_INDEX];
    let wait = corpus
        .steps()
        .iter()
        .find(|step| {
            matches!(
                step.expected(),
                Expected::Accepted(Command::Wait { ticks: 1 })
            )
        })
        .unwrap();
    assert_ne!(
        wait.text(),
        next.text(),
        "fixture changes the full current input"
    );
    let path = root.join("run").join(arm).join("pair-06.sqlite");
    assert!(!path.exists(), "this pair has not started");
    let mut store = Store::open_application(&path).unwrap();
    store
        .create_story("Synthetic paired basis fixture", before.seed().clone())
        .unwrap();
    for receipt in before.receipts() {
        store.begin_turn(receipt.request()).unwrap();
        store.commit_prepared(receipt).unwrap();
    }
    let mut candidate = store.resume(before.scope()).unwrap().engine;
    assert!(
        candidate.canonical_bytes() == before.canonical_bytes(),
        "exact actual reference prefix"
    );
    let turn = if use_current_turn_id {
        next.id()
    } else {
        "off-reference-wait"
    };
    let request = candidate.request(
        turn,
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: wait.text().to_owned(),
        },
    );
    assert!(
        request != next.request(&before),
        "not the exact current-step request"
    );
    let proposal = Proposal {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        expected_revision: request.expected_revision,
        commands: vec![Command::Wait { ticks: 1 }],
    };
    let approved = candidate.preview(&request, &proposal).unwrap();
    let mut provider = WaitFixtureProvider {
        narration: approved.narration().to_owned(),
        events: approved
            .events()
            .iter()
            .map(|event| event.sequence())
            .collect(),
        director: 0,
        narrator: 0,
    };
    let actual = play::execute(
        &mut candidate,
        &request,
        &mut provider,
        &Cancellation::default(),
        &fixture_profile(),
    )
    .unwrap();
    assert_eq!((provider.director, provider.narrator), (1, 1));
    assert!(
        actual.play().is_some(),
        "actual current Play record, not a forged receipt"
    );
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&actual).unwrap();
    let planted = store.resume(before.scope()).unwrap().engine;
    assert!(planted.canonical_bytes() == candidate.canonical_bytes());
    assert_eq!(planted.receipts().len(), before.receipts().len() + 1);
    drop(store);
    path
}

fn rejects_off_reference_basis(arm: &str, same_turn: bool) {
    let (root, reference) = first_scene(&format!("{arm}-{same_turn}"));
    let pair = plant_actual_wait(&root, arm, same_turn);
    let original = read_engine(&pair).canonical_bytes();
    let before = inventory(&root);
    let outcome = run_comparison(
        &root.join("run"),
        true,
        ComparisonKind::PairedSnapshots,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        Some(&reference),
    );
    assert!(outcome.is_err(), "off-reference resume must refuse");
    assert!(
        read_engine(&pair).canonical_bytes() == original,
        "refusal must precede any new canonical work on the invalid pair"
    );
    // There is no public counting factory/poll hook. An invocation/admission is
    // the earlier durable boundary in the actual runner; assert it, setup, all
    // raw/capture files and every retained entry/byte are unchanged. This does
    // not pretend to be an independently measured provider-construction count.
    assert!(
        inventory(&root) == before,
        "refuse before new invocation/admission/setup/provider evidence or any retained mutation"
    );
}

#[test]
fn left_unstarted_pair_with_distinct_accepted_turn_refuses_before_new_work() {
    rejects_off_reference_basis("left", false);
}
#[test]
fn right_unstarted_pair_with_distinct_accepted_turn_refuses_before_new_work() {
    rejects_off_reference_basis("right", false);
}
#[test]
fn left_current_turn_with_wrong_full_free_text_refuses_before_new_work() {
    rejects_off_reference_basis("left", true);
}
#[test]
fn right_current_turn_with_wrong_full_free_text_refuses_before_new_work() {
    rejects_off_reference_basis("right", true);
}

#[test]
fn both_current_steps_with_lost_checkpoints_recover_actual_commits_without_new_roles() {
    let (root, reference) = first_scene("exact-lost-checkpoints");
    let run = root.join("run");
    let mut canonical = Vec::new();
    for arm in ["left", "right"] {
        let path = run.join(arm).join("pair-05.sqlite");
        canonical.push((path.clone(), read_engine(&path).canonical_bytes()));
        fs::remove_file(
            run.join(arm)
                .join(format!("attempt-{LAST_COMPLETED_INDEX:02}.json")),
        )
        .unwrap();
    }
    fs::remove_file(run.join("scene-00.json")).unwrap();
    let work_before = no_new_turn_work(&run);
    let result = run_comparison(
        &run,
        true,
        ComparisonKind::PairedSnapshots,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        Some(&reference),
    )
    .unwrap();
    assert_eq!(result.completed_scenes, 1);
    assert_eq!(result.turns.len(), 12);
    let recovered: Vec<_> = result
        .turns
        .iter()
        .filter(|row| row.turn == "courier-06")
        .collect();
    assert_eq!(recovered.len(), 2);
    for row in recovered {
        assert_eq!(row.phase, "committed");
        assert!(row.recovered_without_checkpoint);
        assert!(!row.roles_known);
        assert_eq!(
            row.roles, 0,
            "no regenerated calls are reported for exact lookup"
        );
        assert!(!row.context_evidence_available);
        assert!(!row.privacy_passed);
        assert!(
            !row.passed,
            "unknown original calls/capture cannot become a pass"
        );
        assert!(row.actual_receipt_sha256.is_some());
        assert!(row.capture_sha256.is_none());
        assert!(row.recording_sha256.is_none());
    }
    for (path, bytes) in canonical {
        assert!(
            read_engine(&path).canonical_bytes() == bytes,
            "actual commit preserved exactly"
        );
    }
    assert!(
        no_new_turn_work(&run) == work_before,
        "exact committed lookup creates no turn admission, raw output, capture or recording"
    );
}
