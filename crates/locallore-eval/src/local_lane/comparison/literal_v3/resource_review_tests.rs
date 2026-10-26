// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen source-only regression oracles; UNCOMPILED / UNRUN by the author.
//! Scripted Host/Store output and real durable reservations, not native work.
use super::*;
use std::{collections::BTreeMap, sync::OnceLock};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "literal-v3-resource-review-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&path).unwrap();
    path
}

fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, bytes: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                out.insert(relative, None);
                walk(root, &path, depth + 1, bytes, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let data = fs::read(path).unwrap();
                *bytes = bytes.checked_add(data.len()).unwrap();
                assert!(*bytes <= 64 * 1024 * 1024);
                out.insert(relative, Some(data));
            }
        }
    }
    let mut result = Inventory::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}

fn copy_fixture(label: &str) -> PathBuf {
    static FIXTURE: OnceLock<PathBuf> = OnceLock::new();
    let original = FIXTURE.get_or_init(|| {
        let run = root("actual-first-scene").join("run");
        let report = run_comparison(
            &run,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert!(!report.completed);
        assert_eq!(report.turns.len(), 12);
        assert!(run.join("setup-00.json").is_file());
        run
    });
    // The producer has returned, so no retained run.lock is read under a lock.
    let original = inventory(original);
    let copy = root(label).join("run");
    fs::create_dir(&copy).unwrap();
    for (path, contents) in &original {
        match contents {
            None => fs::create_dir_all(copy.join(path)).unwrap(),
            Some(data) => fs::write(copy.join(path), data).unwrap(),
        }
    }
    assert_eq!(inventory(&copy), original);
    copy
}

#[test]
fn exhausted_right_invocations_refuse_before_new_left_reservation() {
    let dir = copy_fixture("exhausted-right");
    let manifest: Manifest = decode(&dir.join("run.json"), 128 * 1024).unwrap();
    let key = manifest.key().unwrap();
    let mut right = Ledger::load(&dir.join("right"), &key).unwrap();
    let original_invocations = right.invocations;
    let original_admissions = right.admissions;
    let mut unknown = 0;
    for _ in 0..32 {
        match right.begin_invocation() {
            Ok(()) => {
                unknown += 1;
                assert!(!dir
                    .join("right")
                    .join(format!("invocation-{:02}-settled.json", right.invocation))
                    .exists());
            }
            Err(error) => {
                assert_eq!(error, "RunBudget");
                break;
            }
        }
    }
    assert!(unknown > 0);
    assert_eq!(right.invocations, original_invocations + unknown);
    assert_eq!(right.admissions, original_admissions);
    assert_eq!(
        right.preflight_invocation(false).err().as_deref(),
        Some("RunBudget")
    );
    drop(right); // Unknown reservations are deliberately never settled/refunded.
    let before = inventory(&dir);
    let result = run_comparison(
        &dir,
        true,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    );
    let after = inventory(&dir); // Session/Store/lock owners have returned.
    assert_eq!(result.err().as_deref(), Some("RunBudget"));
    let changed: Vec<_> = before
        .keys()
        .chain(after.keys())
        .filter(|path| before.get(*path) != after.get(*path))
        .take(24)
        .collect();
    assert!(
        after == before,
        "known right refusal changed paths: {changed:?}"
    );
}

#[test]
fn setup_must_reference_an_actual_right_invocation() {
    let dir = copy_fixture("orphan-right-reference");
    assert!(!dir.join("right/invocation-31.json").exists());
    let path = dir.join("setup-00.json");
    let mut setup: serde_json::Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    assert_eq!(setup["right_invocation"], 0);
    // Only an adversarial derived setup reference changes; actual turn/Store and
    // reservation files remain byte-identical. No fabricated execution/charge.
    setup["right_invocation"] = serde_json::json!(31);
    fs::write(&path, serde_json::to_vec(&setup).unwrap()).unwrap();
    let before = inventory(&dir);
    let result = inspect_comparison(&dir);
    let after = inventory(&dir);
    assert_eq!(after, before);
    assert!(
        result.is_err(),
        "reader accepted an absent referenced invocation"
    );
}

#[test]
fn setup_filename_outside_bounded_namespace_is_not_silently_ignored() {
    let dir = copy_fixture("setup-out-of-range");
    let actual = fs::read(dir.join("setup-00.json")).unwrap();
    assert!(!dir.join("setup-32.json").exists());
    // Copy an actual producer setup verbatim; no padded/forged canonical data.
    fs::write(dir.join("setup-32.json"), actual).unwrap();
    let before = inventory(&dir);
    let result = inspect_comparison(&dir);
    let after = inventory(&dir);
    assert_eq!(after, before);
    assert!(
        result.is_err(),
        "reader ignored a setup outside indices 00..31"
    );
}
