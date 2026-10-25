// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Two frozen source-only selected preflight regressions, UNCOMPILED/UNRUN.
//! Exact base e0d2899b; #29 claim6395876482. Root registers this child AFTER freeze.
//! Actual producer/Store/Ledger only; no SQL, receipt/cost fabrication, new hooks,
//! checkpoint resealing or runtime/model/desktop execution by the author.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --lib local_lane::comparison::selected::preflight_review_tests -- --nocapture --test-threads=1
use super::*;
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::{
        atomic::{AtomicU64, Ordering},
        OnceLock,
    },
};

const INDEX: usize = 4; // Existing even original corpus index: left is attempted first.
static NEXT: AtomicU64 = AtomicU64::new(0);
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "locallore-selected-preflight-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&path).unwrap();
    path
}

// Read a whole inventory ONLY after that root's opaque run.lock owner drops.
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, path: &Path, depth: usize, bytes: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(path).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(relative, None).is_none());
                visit(root, &path, depth + 1, bytes, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let content = fs::read(path).unwrap();
                *bytes = bytes.checked_add(content.len()).unwrap();
                assert!(*bytes <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(content)).is_none());
            }
        }
    }
    let mut result = BTreeMap::new();
    visit(root, root, 0, &mut 0, &mut result);
    result
}

fn unchanged(actual: &Inventory, expected: &Inventory, label: &str, retained_root: &Path) {
    let paths: BTreeSet<_> = actual.keys().chain(expected.keys()).collect();
    let changed: Vec<_> = paths
        .into_iter()
        .filter(|path| actual.get(*path) != expected.get(*path))
        .collect();
    assert!(
        changed.is_empty(),
        "{label}; {} changed paths (first24 {:?}); retained synthetic fixture {}",
        changed.len(),
        changed.iter().take(24).collect::<Vec<_>>(),
        retained_root.display()
    );
}

fn copy_inventory(snapshot: &Inventory, destination: &Path) {
    assert!(!destination.exists());
    fs::create_dir(destination).unwrap();
    for (relative, content) in snapshot {
        match content {
            None => fs::create_dir_all(destination.join(relative)).unwrap(),
            Some(bytes) => fs::write(destination.join(relative), bytes).unwrap(),
        }
    }
    unchanged(
        &inventory(destination),
        snapshot,
        "copy original synthetic bytes, never relabel metadata",
        destination,
    );
}

fn original_source() -> &'static PathBuf {
    static ORIGINAL: OnceLock<PathBuf> = OnceLock::new();
    ORIGINAL.get_or_init(|| {
        let root = root("producers");
        let reference_dir = root.join("reference");
        let actual = prepare_reference(&reference_dir, &Cancellation::default()).unwrap();
        assert_eq!(
            (actual.accepted, actual.guard_only, actual.roles),
            (21, 3, 42)
        );
        let reference = open_reference(&reference_dir).unwrap();
        let source = root.join("paired");
        let report = run_comparison(
            &source,
            false,
            ComparisonKind::PairedSnapshots,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            Some(&reference),
        )
        .unwrap();
        assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
        assert!(report.turns.iter().all(|turn| turn.passed));
        source
    })
}

struct Fixture {
    root: PathBuf,
    source: PathBuf,
}
impl Fixture {
    fn new(label: &str) -> Self {
        let snapshot = inventory(original_source());
        let root = root(label);
        let source = root.join("source");
        copy_inventory(&snapshot, &source);
        Self { root, source }
    }
    fn plan(&self, client: &str) -> PreparedSelectedPlan {
        let reader = desktop_api::open_read_only(&self.source).unwrap();
        let summary = desktop_api::summary(&reader, true).unwrap();
        let binding = summary["binding"].as_str().unwrap().to_owned();
        drop(reader);
        let corpus = suite().unwrap();
        prepare_selected(
            &self.source,
            &binding,
            &desktop_api::RowId {
                turn: corpus.steps()[INDEX].id().into(),
                arm: desktop_api::Arm::Left,
            },
            SelectedIntent {
                client_id: client.into(),
                lane: SelectedLane::ScriptedBaseline,
            },
            &Cancellation::default(),
        )
        .unwrap()
    }
}

fn refusal<T>(result: Result<T>) -> Option<String> {
    result.err().map(|error| {
        assert!(!error.is_empty() && error.len() <= 96);
        assert!(error
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_'));
        error
    })
}

#[test]
fn missing_right_turn_capacity_refuses_before_either_invocation_or_missing_left_work() {
    let fixture = Fixture::new("both-budgets");
    let source_before = inventory(&fixture.source);
    let plan = fixture.plan("preflight-both-budgets");
    let destination_path = fixture.root.join("selected");
    let destination = new_destination(&plan, &destination_path).unwrap();
    assert_eq!(destination.manifest.selection.index, INDEX);
    let binding = destination.manifest.binding.clone();
    let right = destination_path.join("right");
    let corpus = suite().unwrap();
    let step = &corpus.steps()[INDEX];
    let mut ledger = Ledger::load(&right, &binding).unwrap();
    ledger.begin_invocation().unwrap();
    for admission in 0..27 {
        assert_eq!(
            ledger
                .admit(&format!("scene-{}", step.scene()), step.id())
                .unwrap(),
            admission
        );
        assert!(!right
            .join(format!("admission-{admission:02}-settled.json"))
            .exists());
    }
    // Finish records ACTUAL measured invocation overhead; no invented zero cost
    // or provider-role count. All27 turn reservations deliberately remain unknown.
    ledger.finish().unwrap();
    let known: Settlement = decode(&right.join("invocation-00-settled.json"), 4096).unwrap();
    assert_eq!((known.index, known.roles), (0, 0));
    assert_eq!(known.binding, binding);
    drop(ledger);
    let persisted = Ledger::load(&right, &binding).unwrap();
    assert_eq!(
        (
            persisted.invocations,
            persisted.admissions,
            persisted.charged_roles
        ),
        (1, 27, 81)
    );
    assert_eq!(persisted.charged_ms, 27 * TURN_MS + known.ms);
    let remaining = persisted.remaining();
    assert!(
        remaining >= PREPARATION_MS,
        "fixture can reserve preparation, actual remaining {remaining}"
    );
    assert!(
        remaining.saturating_sub(PREPARATION_MS) < TURN_MS + CLEANUP_RESERVE_MS,
        "fixture cannot reserve the required turn+cleanup after preparation: {remaining}"
    );
    for arm in ARM_NAMES {
        assert!(!database(
            &destination_path.join(arm),
            INDEX,
            destination.manifest.source_kind
        )
        .exists());
        assert!(!checkpoint_path(&destination_path.join(arm), INDEX).exists());
    }
    drop(persisted);
    drop(destination);
    assert!(inventory(&destination_path.join("left")).is_empty());
    let destination_before = inventory(&destination_path);
    let reopened = open_destination(&destination_path).unwrap();
    // Existing private entry origin; no new execution/clock injection hook.
    let outcome = execute_selected(&plan, &reopened, &Cancellation::default(), Instant::now());
    drop(reopened);
    drop(plan);
    let error = refusal(outcome);
    eprintln!(
        "both-arm budget outcome {error:?}; retained {}",
        fixture.root.display()
    );
    unchanged(
        &inventory(&fixture.source),
        &source_before,
        "source immutable",
        &fixture.root,
    );
    unchanged(&inventory(&destination_path), &destination_before,
        "known insufficient missing-right capacity must precede BOTH invocation/Store/provider writes", &fixture.root);
    assert_eq!(error.as_deref(), Some("RunBudget"));
    assert!(!destination_path.join("left/admission-00.json").exists());
}

#[test]
fn actual_failed_checkpoint_cannot_hide_an_actual_committed_store_during_inspect_or_resume() {
    let fixture = Fixture::new("outcome-conflict");
    let source_before = inventory(&fixture.source);
    let plan = fixture.plan("preflight-outcome-conflict");
    let destination_path = fixture.root.join("failed-original");
    let destination = new_destination(&plan, &destination_path).unwrap();
    let binding = destination.manifest.binding.clone();
    let kind = destination.manifest.source_kind;
    let corpus = suite().unwrap();
    let step = &corpus.steps()[INDEX];
    let left = destination_path.join("left");
    let path = database(&left, INDEX, kind);
    ensure_database(&path, corpus.seed(), plan.before[0].receipts()).unwrap();
    let mut ledger = Ledger::load(&left, &binding).unwrap();
    ledger.begin_invocation().unwrap();
    let failed = execute_turn(
        TurnJob {
            dir: &left,
            path: &path,
            index: INDEX,
            arm: ARM_NAMES[0],
            policy: POLICIES[0],
            binding: &binding,
            step,
            factory: &LaneFactory::TestFault(TestFault::WrongCommand),
            cancel: &Cancellation::default(),
        },
        &mut ledger,
    )
    .unwrap();
    assert_eq!(failed.row.phase, "failed");
    assert!(!failed.row.passed);
    assert_eq!(failed.before_head, failed.after_head);
    assert_eq!(failed.request, plan.manifest.source_inputs[0].request);
    assert!(failed.recording_file.is_some());
    let checkpoint = checkpoint_path(&left, INDEX);
    let original_checkpoint = fs::read(&checkpoint).unwrap();
    let actual_checkpoint: StoredTurn = decode(&checkpoint, 256 * 1024).unwrap();
    assert_eq!(
        encode(&actual_checkpoint).unwrap(),
        encode(&failed).unwrap()
    );
    let before_basis = plan.before[0].accepted_history_basis().unwrap();
    assert_eq!(
        engine(&path, plan.before[0].scope())
            .unwrap()
            .accepted_history_basis()
            .unwrap(),
        before_basis
    );
    ledger.finish().unwrap(); // execute_turn already settled its real admission.
    drop(ledger);
    let committed_source = database(&fixture.source.join("left"), INDEX, kind);
    let committed_engine = engine(&committed_source, &corpus.seed().scope).unwrap();
    assert_eq!(
        committed_engine
            .at_revision(failed.before_head)
            .unwrap()
            .accepted_history_basis()
            .unwrap(),
        before_basis
    );
    assert!(committed_engine.revision() > failed.after_head);
    {
        let mut store = Store::open_read_only(&committed_source).unwrap();
        let actual = store
            .lookup_turn(&failed.request.scope, &failed.request.turn)
            .unwrap();
        assert_eq!(actual.phase, locallore_storage::TurnPhase::Committed);
        assert_eq!(actual.request, failed.request);
        assert!(actual.receipt.is_some());
    }
    assert!(!database(&destination_path.join("right"), INDEX, kind).exists());
    drop(destination);
    drop(plan);
    // Sole intentional inconsistency: COPY a genuinely committed Store over our
    // own failed destination Store, after handles drop. No SQL/reset/receipt or
    // checkpoint rewrite; the source remains byte-identical and not hardlinked.
    single_link_file(&committed_source).unwrap();
    fs::copy(&committed_source, &path).unwrap();
    single_link_file(&path).unwrap();
    single_link_file(&committed_source).unwrap();
    assert_eq!(fs::read(&checkpoint).unwrap(), original_checkpoint);
    let retained: StoredTurn = decode(&checkpoint, 256 * 1024).unwrap();
    assert_eq!(retained.row.phase, "failed");
    assert_eq!(retained.before_head, retained.after_head);
    {
        let mut store = Store::open_read_only(&path).unwrap();
        let actual = store
            .lookup_turn(&failed.request.scope, &failed.request.turn)
            .unwrap();
        assert_eq!(actual.phase, locallore_storage::TurnPhase::Committed);
        assert_eq!(actual.request, failed.request);
        assert!(actual.receipt.is_some());
    }
    unchanged(
        &inventory(&fixture.source),
        &source_before,
        "setup only read actual source",
        &fixture.root,
    );
    let after_setup = inventory(&destination_path);
    // Independent byte-exact copies let BOTH public calls be observed even if
    // the first has an unexpected mutation; no failure is silently repaired.
    let inspect_path = fixture.root.join("inspect-conflict");
    let resume_path = fixture.root.join("resume-conflict");
    copy_inventory(&after_setup, &inspect_path);
    copy_inventory(&after_setup, &resume_path);
    let inspect_before = inventory(&inspect_path);
    let resume_before = inventory(&resume_path);
    let inspect_result = refusal(inspect_selected(&inspect_path));
    let inspect_after = inventory(&inspect_path);
    let resume_result = refusal(resume_selected(
        &resume_path,
        &fixture.source,
        &binding,
        &Cancellation::default(),
    ));
    let resume_after = inventory(&resume_path);
    eprintln!(
        "outcome contradiction inspect={inspect_result:?} resume={resume_result:?}; retained {}",
        fixture.root.display()
    );
    unchanged(
        &inventory(&fixture.source),
        &source_before,
        "source immutable",
        &fixture.root,
    );
    unchanged(
        &inventory(&destination_path),
        &after_setup,
        "original contradictory fixture retained",
        &fixture.root,
    );
    unchanged(
        &inspect_after,
        &inspect_before,
        "inspect is read-only even on refusal",
        &fixture.root,
    );
    unchanged(
        &resume_after,
        &resume_before,
        "contradictory Store/checkpoint must precede either ledger or output",
        &fixture.root,
    );
    assert!(
        inspect_result.is_some(),
        "inspect must refuse an actual committed Store hidden by a failed checkpoint"
    );
    assert!(
        resume_result.is_some(),
        "resume must refuse actual outcome disagreement before missing-arm generation"
    );
}
