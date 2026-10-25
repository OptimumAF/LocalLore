// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! One frozen common-reader source-outcome contradiction. SOURCE-ONLY, UNRUN.
//! Base e0d2899b; Root registers cfg(test) mod outcome_review_tests after freeze.
//! Real Host/Store/scripted outcomes, no SQL, forged receipt or checkpoint rewrite.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --lib local_lane::comparison::outcome_review_tests -- --nocapture --test-threads=1
use super::*;
use std::collections::BTreeMap;

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, bytes: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(path).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(relative, None).is_none());
                walk(root, &path, depth + 1, bytes, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let value = fs::read(&path).unwrap();
                *bytes = bytes.checked_add(value.len()).unwrap();
                assert!(*bytes <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(value)).is_none());
            }
        }
    }
    let mut files = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut files);
    files
}

#[test]
fn failed_source_checkpoint_cannot_hide_actual_committed_store_from_either_reader() {
    let root = std::env::temp_dir().join(format!(
        "locallore-source-outcome-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
    ));
    fs::create_dir(&root).unwrap();
    let source = root.join("source");
    let corpus = suite().unwrap();
    let step = &corpus.steps()[0];
    let manifest = RunManifest::new(
        ComparisonKind::ContinuousRollout,
        LaneFactory::ScriptedBaseline.profile().unwrap(),
        false,
        None,
    )
    .unwrap();
    let mut session =
        ComparisonSession::open_at(&source, false, manifest, None, Instant::now()).unwrap();
    session.setup(false, 0, "scripted", None).unwrap();
    let key = session.key.clone();
    for arm in 0..2 {
        let directory = source.join(ARM_NAMES[arm]);
        let path = database(&directory, 0, ComparisonKind::ContinuousRollout);
        ensure_database(&path, corpus.seed(), &[]).unwrap();
        let factory = if arm == 0 {
            LaneFactory::TestFault(TestFault::WrongCommand)
        } else {
            LaneFactory::ScriptedBaseline
        };
        let turn = execute_turn(
            TurnJob {
                dir: &directory,
                path: &path,
                index: 0,
                arm: ARM_NAMES[arm],
                policy: POLICIES[arm],
                binding: &key,
                step,
                factory: &factory,
                cancel: &Cancellation::default(),
            },
            &mut session.ledgers[arm],
        )
        .unwrap();
        assert!(
            checkpoint_path(&directory, 0).is_file(),
            "actual producer checkpoint"
        );
        session.turns[arm].push(turn);
    }
    let left = &session.turns[0][0];
    let right = &session.turns[1][0];
    assert_eq!(left.row.phase, "failed");
    assert!(left.row.error.is_some());
    assert!(left.row.actual_receipt_sha256.is_none());
    assert_eq!(left.before_head, 0);
    assert_eq!(left.after_head, 0);
    assert_eq!(right.row.phase, "committed");
    assert!(right.row.passed && right.row.actual_receipt_sha256.is_some());
    assert_eq!(right.before_head, 0);
    assert!(right.after_head > 0);
    assert!(
        left.request == right.request,
        "actual complete requests share the seed boundary"
    );
    let request = left.request.clone();
    let published = session.finish_and_publish().unwrap();
    assert!(!published.completed);
    assert_eq!(published.completed_scenes, 0);
    assert_eq!(published.turns.len(), 2);
    drop(session);
    assert!(
        !source.join("scene-00.json").exists(),
        "genuine unsealed partial source"
    );
    let original = inspect_comparison(&source).unwrap();
    assert_eq!(original.turns[0].phase, "failed");
    assert_eq!(original.turns[1].phase, "committed");
    let opened = desktop_api::open_read_only(&source).unwrap();
    assert_eq!(
        desktop_api::summary(&opened, true).unwrap()["rows"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    drop(opened);

    let left_path = database(&source.join("left"), 0, ComparisonKind::ContinuousRollout);
    let right_path = database(&source.join("right"), 0, ComparisonKind::ContinuousRollout);
    let original_right = engine(&right_path, &corpus.seed().scope).unwrap();
    assert!(engine(&left_path, &corpus.seed().scope)
        .unwrap()
        .receipts()
        .is_empty());
    assert_eq!(original_right.receipts().len(), 1);
    assert!(original_right.receipts()[0].request() == &request);
    let original_files = inventory(&source);
    // A single ordinary-file copy supplies a real accepted Store outcome. Keep
    // the failed LEFT checkpoint/recordings/raw files and report byte-exact.
    fs::copy(&right_path, &left_path).unwrap();
    let mut faulted_expected = original_files;
    let left_relative = left_path.strip_prefix(&source).unwrap().to_owned();
    assert!(faulted_expected
        .insert(left_relative, Some(fs::read(&right_path).unwrap()))
        .is_some());
    assert!(
        inventory(&source) == faulted_expected,
        "only the actual left SQLite bytes changed"
    );
    let saved = {
        let mut store = Store::open_read_only(&left_path).unwrap();
        store.lookup_turn(&corpus.seed().scope, step.id()).unwrap()
    };
    let receipt = saved
        .receipt
        .expect("actual copied Store is committed for this exact request");
    assert!(receipt.request() == &request);
    let copied = engine(&left_path, &corpus.seed().scope).unwrap();
    assert!(copied.receipts() == original_right.receipts());
    assert!(copied.canonical_bytes() == original_right.canonical_bytes());
    assert!(copied.receipts().last() == Some(&receipt));
    let before_readers = inventory(&source);

    // Collect BOTH old-reader outcomes before assertions. In particular, drop a
    // successful old capability before reading mandatory-locked run.lock bytes.
    let inspect_error = inspect_comparison(&source).err();
    let open_error = match desktop_api::open_read_only(&source) {
        Ok(capability) => {
            drop(capability);
            None
        }
        Err(error) => Some(error),
    };
    assert!(
        inventory(&source) == before_readers,
        "readers never normalize or repair the faulted source"
    );
    assert!(inspect_error.is_some() && open_error.is_some(),
        "both readers must refuse committed Store hidden by failed checkpoint; inspect error {:?}, open error {:?}; retained owned fixture {:?}",
        inspect_error, open_error, root);
    for error in [inspect_error, open_error].into_iter().flatten() {
        assert!(!error.is_empty() && error.len() <= 96);
        assert!(error
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_'));
    }
    assert!(inventory(&source) == faulted_expected);
}
