// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST frozen accounting oracles; UNCOMPILED/UNRUN by this source-only author.
//! Child of selected::native. Actual Ledger methods/files, deliberately synthetic
//! clocks and load metrics. No child, model, Play, terminal-cleanup proof or timing
//! qualification. Root alone registers/runs/fixes the absent save_setup_at seam.
use super::*;
use std::{collections::BTreeMap, sync::atomic::{AtomicU64, Ordering}};

const BINDING: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
static NEXT: AtomicU64 = AtomicU64::new(0);
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn fixture(label: &str, prior_unknown: bool) -> (PathBuf, [Ledger; 2]) {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-native-accounting-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed),
    ));
    fs::create_dir(&root).unwrap();
    let make = |arm: &str| {
        let dir = root.join(arm);
        fs::create_dir(&dir).unwrap();
        if prior_unknown {
            // Real emitted reservation with no terminal settlement: a previous
            // interrupted invocation. No owner/process or measured work invented.
            let mut previous = Ledger::load(&dir, BINDING).unwrap();
            previous.begin_invocation().unwrap();
        }
        let mut current = Ledger::load(&dir, BINDING).unwrap();
        current.begin_invocation().unwrap();
        current
    };
    let ledgers = [make("left"), make("right")];
    (root, ledgers)
}

// Small owned fixture, including every directory and byte; no locked run.lock
// exists in these Ledger-only cases. Retain failed fixtures for Root diagnosis.
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 2);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 64);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let key = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(key, None).is_none());
                walk(root, &path, depth + 1, total, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 64 * 1024);
                let bytes = fs::read(path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 512 * 1024);
                assert!(out.insert(key, Some(bytes)).is_none());
            }
        }
    }
    let mut result = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}

#[derive(Debug, PartialEq, Eq)]
struct LedgerState {
    directory: PathBuf,
    binding: String,
    admissions: usize,
    invocations: usize,
    charged_ms: u64,
    charged_roles: usize,
    prior_ms: u64,
    started: Instant,
    turn_ms: u64,
    invocation: usize,
    excluded_ms: u64,
    shared_setup: Option<(u64, u64)>,
}
fn state(ledger: &Ledger) -> LedgerState {
    LedgerState {
        directory: ledger.directory.clone(), binding: ledger.binding.clone(),
        admissions: ledger.admissions, invocations: ledger.invocations,
        charged_ms: ledger.charged_ms, charged_roles: ledger.charged_roles,
        prior_ms: ledger.prior_ms, started: ledger.started, turn_ms: ledger.turn_ms,
        invocation: ledger.invocation, excluded_ms: ledger.excluded_ms,
        shared_setup: ledger.shared_setup,
    }
}
fn states(ledgers: &[Ledger; 2]) -> [LedgerState; 2] {
    [state(&ledgers[0]), state(&ledgers[1])]
}
fn synthetic_load() -> Value {
    // Valid fixed shape only; never claim this is an observed native model load.
    serde_json::to_value(locallore_local_runtime::Metrics {
        load_ms: 1.0, total_ms: 1.0, model_loads: 1,
        ..Default::default()
    }).unwrap()
}
fn setup_record(root: &Path, invocation: usize) -> SetupRecord {
    let bytes = fs::read(root.join(format!("setup-{invocation:02}.json"))).unwrap();
    let json: Value = serde_json::from_slice(&bytes).unwrap();
    let keys: Vec<&str> = json.as_object().unwrap().keys().map(String::as_str).collect();
    assert_eq!(keys, ["binding", "left_invocation", "load", "native", "physical_ms", "right_invocation", "status", "version"]);
    let record: SetupRecord = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(record.version, 2);
    assert_eq!(record.binding, BINDING);
    assert_eq!(record.left_invocation, invocation);
    assert_eq!(record.right_invocation, invocation);
    assert!(record.native);
    record
}

#[test]
fn late_loaded_setup_refuses_before_any_write_or_ledger_change_but_valid_load_splits_once() {
    let (root, mut ledgers) = fixture("loaded", false);
    let before_files = inventory(&root);
    let before_state = states(&ledgers);
    assert_eq!(save_setup_at(&root, BINDING, &mut ledgers, 120_001, "loaded", Some(synthetic_load())), Err("PreparationDeadline".into()));
    assert_eq!(inventory(&root), before_files);
    assert_eq!(states(&ledgers), before_state);

    save_setup_at(&root, BINDING, &mut ledgers, 101, "loaded", Some(synthetic_load())).unwrap();
    assert_eq!(ledgers[0].shared_setup, Some((101, 51)));
    assert_eq!(ledgers[1].shared_setup, Some((101, 50)));
    let record = setup_record(&root, 0);
    assert_eq!(record.physical_ms, 101);
    assert_eq!(record.status, "loaded");
    assert_eq!(record.load, Some(synthetic_load()));
    // Recording setup changes only each ledger's known shared-setup adjustment.
    for (arm, before) in ledgers.iter().zip(before_state) {
        let mut expected = before;
        expected.shared_setup = arm.shared_setup;
        assert_eq!(state(arm), expected);
    }
}

#[test]
fn terminal_failed_overrun_is_unclamped_across_finish_reload_and_prior_unknown_reservations() {
    for physical in [120_001_u64, 240_001] {
        let (root, mut ledgers) = fixture(&format!("failed-{physical}"), true);
        let prior: [Vec<u8>; 2] = std::array::from_fn(|arm| fs::read(ledgers[arm].directory.join("invocation-00.json")).unwrap());
        assert_eq!(ledgers[0].invocation, 1);
        assert_eq!(ledgers[1].invocation, 1);
        save_setup_at(&root, BINDING, &mut ledgers, physical, "failed", None).unwrap();
        let left = physical / 2 + physical % 2;
        let right = physical / 2;
        assert_eq!(ledgers[0].shared_setup, Some((physical, left)));
        assert_eq!(ledgers[1].shared_setup, Some((physical, right)));
        let record = setup_record(&root, 1);
        assert_eq!(record.physical_ms, physical);
        assert_eq!(record.status, "failed");
        assert!(record.load.is_none());

        // Synthetic clock injection only, no sleep/worker/model measurement.
        // It makes actual Ledger::finish account the entire supplied duration.
        let started = Instant::now().checked_sub(Duration::from_millis(physical + 20)).unwrap();
        let mut settled_sum = 0_u64;
        for (arm, ledger) in ledgers.iter_mut().enumerate() {
            ledger.started = started;
            ledger.finish().unwrap();
            let settled: Settlement = serde_json::from_slice(&fs::read(ledger.directory.join("invocation-01-settled.json")).unwrap()).unwrap();
            assert_eq!(settled.version, 1);
            assert_eq!(settled.binding, BINDING);
            assert_eq!(settled.index, 1);
            assert_eq!(settled.roles, 0);
            assert!(settled.ms >= [left, right][arm]);
            settled_sum = settled_sum.checked_add(settled.ms).unwrap();
            assert_eq!(fs::read(ledger.directory.join("invocation-00.json")).unwrap(), prior[arm]);
            assert!(!ledger.directory.join("invocation-00-settled.json").exists());
            let reloaded = Ledger::load(&ledger.directory, BINDING).unwrap();
            assert_eq!(reloaded.invocations, 2);
            assert_eq!(reloaded.admissions, 0);
            assert_eq!(reloaded.charged_roles, 0);
            assert_eq!(reloaded.charged_ms, PREPARATION_MS + settled.ms, "prior unknown keeps FULL120000 in addition to actual terminal charge");
            assert_eq!(ledger.charged_ms, reloaded.charged_ms);
        }
        assert!(settled_sum >= physical, "overrun must not be clamped to reservation120000");

        // The general/full-run guard stays strict. Loading this ledger does not
        // recreate its volatile shared-setup adjustment, so overrun is the cause.
        let mut legacy = Ledger::load(&ledgers[0].directory, BINDING).unwrap();
        assert!(legacy.shared_setup.is_none());
        let before_state = state(&legacy);
        let before_files = inventory(&root);
        assert_eq!(legacy.record_shared_setup(physical, left), Err("ClockIntegrity".into()));
        assert_eq!(state(&legacy), before_state);
        assert_eq!(inventory(&root), before_files);
    }
}

#[test]
fn either_arm_existing_setup_or_invalid_status_refuses_before_record_or_other_arm_mutation() {
    for contaminated in [0, 1] {
        let (root, mut ledgers) = fixture(&format!("duplicate-{contaminated}"), false);
        ledgers[contaminated].record_shared_setup(20, 10).unwrap();
        let before_state = states(&ledgers);
        let before_files = inventory(&root);
        assert_eq!(save_setup_at(&root, BINDING, &mut ledgers, 101, "loaded", Some(synthetic_load())), Err("ClockIntegrity".into()));
        assert_eq!(states(&ledgers), before_state, "neither arm mutates after either-arm preflight refusal");
        assert_eq!(inventory(&root), before_files, "no dangling setup record before refused ledger update");
    }
    let (root, mut ledgers) = fixture("status", false);
    let before_state = states(&ledgers);
    let before_files = inventory(&root);
    assert_eq!(save_setup_at(&root, BINDING, &mut ledgers, 101, "pretend_loaded", None), Err("SetupIntegrity".into()));
    assert_eq!(states(&ledgers), before_state);
    assert_eq!(inventory(&root), before_files);
}
