// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! One frozen real divergent-rollout oracle, UNCOMPILED/UNRUN at handoff.
//! Root registers this child only after source freeze. No production/test hooks.
//! Only the existing private WrongCommand fixture creates the failed source
//! attempt; every subsequent receipt comes from actual Host/Core/Store execution.
use super::*;

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn owned_root() -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-divergent-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&root).unwrap();
    root
}

fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096);
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(relative, None).is_none());
                visit(root, &path, depth + 1, total, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(path).unwrap();
                *total += bytes.len();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(bytes)).is_none());
            }
        }
    }
    let mut files = BTreeMap::new();
    visit(root, root, 0, &mut 0, &mut files);
    files
}

fn actual_divergent_scene(source: &Path) -> ComparisonReportV2 {
    let started = Instant::now();
    let manifest = RunManifest::new(
        ComparisonKind::ContinuousRollout,
        LaneFactory::ScriptedBaseline.profile().unwrap(),
        false,
        None,
    ).unwrap();
    let mut session = ComparisonSession::open_at(source, false, manifest, None, started).unwrap();
    session.setup(false, 0, "scripted", None).unwrap();
    let corpus = suite().unwrap();
    let cancel = Cancellation::default();
    for index in 0..6 {
        // The existing rollout order is scene parity, left first in scene zero.
        for arm in [0, 1] {
            let began = Instant::now();
            let d = source.join(ARM_NAMES[arm]);
            let path = database(&d, index, ComparisonKind::ContinuousRollout);
            ensure_database(&path, corpus.seed(), &[]).unwrap();
            let factory = if index == 0 && arm == 0 {
                LaneFactory::TestFault(TestFault::WrongCommand)
            } else {
                LaneFactory::ScriptedBaseline
            };
            let turn = execute_turn(TurnJob {
                dir: &d,
                path: &path,
                index,
                arm: ARM_NAMES[arm],
                policy: POLICIES[arm],
                binding: &session.key,
                step: &corpus.steps()[index],
                factory: &factory,
                cancel: &cancel,
            }, &mut session.ledgers[arm]).unwrap();
            if index == 0 && arm == 0 {
                assert_eq!(turn.row.phase, "failed");
                assert!(!turn.row.passed);
                assert_eq!(turn.before_head, turn.after_head);
                assert!(engine(&path, &corpus.seed().scope).unwrap().receipts().is_empty());
            } else {
                assert_eq!(turn.row.phase, "committed");
                assert!(turn.row.passed);
            }
            if !checkpoint_path(&d, index).exists() {
                saved(&checkpoint_path(&d, index), &turn, 256 * 1024).unwrap();
            }
            session.turns[arm].push(turn);
            session.ledgers[1 - arm].exclude_measured_interval(
                began.elapsed().as_millis().min(u64::MAX as u128) as u64,
            ).unwrap();
        }
    }
    let seal = scene_data(source, &session.key, 0).unwrap();
    saved(&source.join("scene-00.json"), &seal, 4096).unwrap();
    let report = session.finish_and_publish().unwrap();
    assert_eq!(report.completed_scenes, 1);
    assert_eq!(report.turns.len(), 12);
    assert_eq!(report.turns.iter().filter(|row| !row.passed).count(), 1);
    assert!(!report.quality_accepted);
    assert!(report.first_semantic_divergence.is_some());
    drop(session); // Release the actual source run.lock before reader/prepare.
    assert_eq!(inspect_comparison(source).unwrap(), report);
    report
}

#[test]
fn genuine_rollout_divergence_keeps_each_selected_actual_prefix_and_full_request() {
    const INDEX: usize = 4;
    let root = owned_root();
    let source = root.join("source");
    let destination = root.join("selected");
    let source_report = actual_divergent_scene(&source);
    let corpus = suite().unwrap();
    let step = &corpus.steps()[INDEX];
    let mut actual_before = Vec::new();
    let mut actual_requests = Vec::new();
    let mut source_rows = Vec::new();
    for arm_name in &ARM_NAMES {
        let d = source.join(arm_name);
        let cp: StoredTurn = decode(&checkpoint_path(&d, INDEX), 256 * 1024).unwrap();
        assert_eq!(cp.row.phase, "committed");
        assert!(cp.row.roles_known && cp.row.passed);
        let full = engine(&database(&d, INDEX, ComparisonKind::ContinuousRollout),
            &corpus.seed().scope).unwrap();
        let before = full.at_revision(cp.before_head).unwrap();
        let request = step.request(&before);
        assert_eq!(request, cp.request);
        assert_eq!(semantic_input_for(&before, &request), cp.row.input_semantic_sha256);
        actual_before.push(before);
        actual_requests.push(request);
        source_rows.push(cp.row);
    }
    // The left first Say was actually rejected, never erased/relabelled from
    // an accepted source. Both later source chains are valid and remain distinct.
    assert_eq!(actual_before[0].receipts().len() + 1, actual_before[1].receipts().len());
    assert!(actual_before[0].receipts().iter().all(|receipt|
        receipt.request().turn != corpus.steps()[0].id()));
    assert!(actual_before[1].receipts().iter().any(|receipt|
        receipt.request().turn == corpus.steps()[0].id()));
    assert_ne!(actual_before[0].revision(), actual_before[1].revision());
    assert_ne!(actual_requests[0], actual_requests[1]);
    assert_ne!(source_rows[0].input_semantic_sha256, source_rows[1].input_semantic_sha256);
    assert_ne!(actual_before[0].canonical_bytes(), actual_before[1].canonical_bytes());
    let original = inventory(&source);
    let opened = desktop_api::open_read_only(&source).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    let binding = summary["binding"].as_str().unwrap().to_owned();
    drop(opened);
    let plan = prepare_selected(&source, &binding,
        &desktop_api::RowId { turn: step.id().into(), arm: desktop_api::Arm::Left },
        SelectedIntent { client_id: "genuine-divergent-rollout".into(),
            lane: SelectedLane::ScriptedBaseline }, &Cancellation::default()).unwrap();
    let report = run_selected(plan, &destination, &Cancellation::default()).unwrap();
    let report = serde_json::to_value(report).unwrap();
    assert_eq!(report["source_kind"], "continuous_rollout");
    assert!(report["source_reference_sha256"].is_null());
    assert_eq!(report["selection"], json!({"turn":step.id(),"clicked_arm":"left","index":INDEX}));
    assert_eq!(report["rows"].as_array().unwrap().len(), 2);
    assert_eq!(report["completed"], true);
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["quality_accepted"], false);
    assert_ne!(report["source_inputs"][0]["input_semantic_sha256"],
        report["source_inputs"][1]["input_semantic_sha256"]);
    for arm in 0..2 {
        let before = &actual_before[arm];
        let input = &report["source_inputs"][arm];
        assert_eq!(input["arm"], ARM_NAMES[arm]);
        assert_eq!(input["scope"], serde_json::to_value(before.scope()).unwrap());
        assert_eq!(input["before_head"], before.revision());
        assert_eq!(input["request"], serde_json::to_value(&actual_requests[arm]).unwrap());
        assert_eq!(input["prefix_sha256"], digest(&encode(before.receipts()).unwrap()));
        assert_eq!(input["input_semantic_sha256"], source_rows[arm].input_semantic_sha256);
        let row: TurnReportV2 = serde_json::from_value(report["rows"][arm].clone()).unwrap();
        assert_eq!(row.turn, step.id());
        assert_eq!(row.arm, ARM_NAMES[arm]);
        assert_eq!(row.policy, POLICIES[arm]);
        assert_eq!(row.phase, "committed");
        assert!(row.passed && row.roles_known && !row.recovered_without_checkpoint);
        assert_eq!(row.roles, 2);
        assert_eq!(row.input_semantic_sha256, source_rows[arm].input_semantic_sha256);
        let d = destination.join(ARM_NAMES[arm]);
        let full = engine(&database(&d, INDEX, ComparisonKind::ContinuousRollout),
            &corpus.seed().scope).unwrap();
        let cut = full.at_revision(before.revision()).unwrap();
        assert_eq!(cut.canonical_bytes(), before.canonical_bytes());
        assert_eq!(cut.receipts(), before.receipts());
        assert!(cut.accepted_history_basis().unwrap() == before.accepted_history_basis().unwrap());
        assert_eq!(full.receipts().len(), before.receipts().len() + 1);
        assert_eq!(full.receipts().last().unwrap().request(), &actual_requests[arm]);
        let cp: StoredTurn = decode(&checkpoint_path(&d, INDEX), 256 * 1024).unwrap();
        assert_eq!(cp.index, INDEX);
        assert_eq!(cp.before_head, before.revision());
        assert_eq!(cp.request, actual_requests[arm]);
        for previous in 0..INDEX { assert!(!checkpoint_path(&d, previous).exists()); }
        let admissions = fs::read_dir(&d).unwrap().map(|entry|
            entry.unwrap().file_name().to_string_lossy().into_owned())
            .filter(|name| name.starts_with("admission-") && !name.contains("settled")).count();
        assert_eq!(admissions, 1, "only selected original-index generation per arm");
    }
    assert_eq!(serde_json::to_value(inspect_selected(&destination).unwrap()).unwrap(), report);
    assert_eq!(inventory(&source), original);
    assert_eq!(inspect_comparison(&source).unwrap(), source_report);
    assert_eq!(inventory(&source), original);
}

fn semantic_input_for(before: &Engine, request: &Request) -> String {
    v2::semantic_input(before, request).unwrap()
}
