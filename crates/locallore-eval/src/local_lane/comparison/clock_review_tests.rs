// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen source-only clock oracles. No sleep-based performance assertions.
//! open_at/turn_deadline and registration are coordinator-owned and initially
//! absent. These cases are UNCOMPILED/UNRUN, not a demonstrated RED.
//! Preparation remains the native asset phase: backdated opening work is active
//! arm cost, never fabricated physical model-load time. No execution injection.
use super::*;
use std::collections::BTreeMap;

fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "locallore-comparison-clock-review-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()
    ));
    fs::create_dir(&path).unwrap();
    path
}

fn manifest() -> RunManifest {
    RunManifest::new(
        ComparisonKind::ContinuousRollout,
        LaneFactory::ScriptedBaseline.profile().unwrap(),
        false,
        None,
    ).unwrap()
}

fn backdated(milliseconds: u64) -> Instant {
    Instant::now().checked_sub(Duration::from_millis(milliseconds)).unwrap()
}

fn assert_settled(dir: &Path, key: &str, invocation: usize, prior: u64, minimum: u64) {
    let settled: Settlement = decode(
        &dir.join(format!("invocation-{invocation:02}-settled.json")), 4096,
    ).unwrap();
    assert_eq!(settled.binding, key);
    assert_eq!(settled.index, invocation);
    assert_eq!(settled.roles, 0);
    assert!(settled.ms >= minimum, "opening work must not disappear from settlement");
    let reopened = Ledger::load(dir, key).unwrap();
    assert_eq!(reopened.invocations, invocation + 1);
    assert_eq!(reopened.charged_ms, prior.checked_add(settled.ms).unwrap());
}

#[test]
fn real_open_charges_known_opening_above_reservation_and_reopens_exact_settlement() {
    let directory = root("known").join("run");
    let expected = manifest();
    let key = expected.stable_key().unwrap();
    let opening_ms = PREPARATION_MS + 9_000;
    let started = backdated(opening_ms);
    let mut session = ComparisonSession::open_at(&directory, false, expected, None, started).unwrap();
    for ledger in &session.ledgers {
        assert_eq!(ledger.started, started, "exact invocation origin, not a new clock");
        assert_eq!(ledger.invocations, 1);
        assert_eq!(ledger.admissions, 0);
        assert_eq!(ledger.charged_ms, PREPARATION_MS);
        assert!(ledger.elapsed() >= opening_ms);
        assert!(ledger.remaining() <= MAX_ACTIVE_MS - opening_ms);
    }
    // Opening has exceeded the preparation reservation but is not native asset
    // load. It remains valid active work and must be settled at its actual cost.
    session.setup(false, 0, "scripted", None).unwrap();
    session.finish_ledgers().unwrap();
    let setup: SetupRecord = decode(&directory.join("setup-00.json"), 64 * 1024).unwrap();
    assert!(!setup.native);
    assert_eq!(setup.physical_ms, 0);
    assert_eq!(setup.status, "scripted");
    drop(session);
    for arm in ARM_NAMES {
        assert_settled(&directory.join(arm), &key, 0, 0, opening_ms);
        let ledger = Ledger::load(&directory.join(arm), &key).unwrap();
        assert!(ledger.charged_ms > PREPARATION_MS);
        assert_eq!(ledger.charged_roles, 0);
        assert_eq!(ledger.admissions, 0);
    }
}

fn retained_files(directory: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    fn visit(root: &Path, dir: &Path, files: &mut BTreeMap<PathBuf, Vec<u8>>) {
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            if metadata.is_dir() {
                visit(root, &path, files);
            } else {
                assert!(metadata.is_file());
                assert!(metadata.len() <= 2 * 1024 * 1024);
                files.insert(path.strip_prefix(root).unwrap().to_path_buf(), fs::read(path).unwrap());
                assert!(files.len() <= 512);
            }
        }
    }
    let mut files = BTreeMap::new();
    visit(directory, directory, &mut files);
    files
}

#[test]
fn continuing_actual_checkpoint_replay_uses_original_clock_and_no_new_turn_admission() {
    let directory = root("resume").join("run");
    let first = run_comparison(
        &directory, false, ComparisonKind::ContinuousRollout,
        &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None,
    ).unwrap();
    assert_eq!(first.completed_scenes, 1);
    assert_eq!(first.turns.len(), 12);
    assert!(first.turns.iter().all(|row| row.passed));
    let expected = manifest();
    let key = expected.stable_key().unwrap();
    let prior = [
        Ledger::load(&directory.join("left"), &key).unwrap(),
        Ledger::load(&directory.join("right"), &key).unwrap(),
    ];
    let immutable = retained_files(&directory);
    let opening_ms = PREPARATION_MS + 5_000;
    let started = backdated(opening_ms);
    // Actual production open revalidates saved canonical/capture checkpoints.
    // The supplied origin must survive that work, not start after replay.
    let mut session = ComparisonSession::open_at(&directory, true, expected, None, started).unwrap();
    for (arm, ledger) in session.ledgers.iter().enumerate() {
        assert_eq!(ledger.started, started);
        assert_eq!(ledger.prior_ms, prior[arm].charged_ms);
        assert_eq!(ledger.invocations, prior[arm].invocations + 1);
        assert_eq!(ledger.admissions, prior[arm].admissions);
        assert_eq!(ledger.charged_roles, prior[arm].charged_roles);
        assert!(ledger.remaining() <= MAX_ACTIVE_MS.saturating_sub(prior[arm].charged_ms + opening_ms));
    }
    session.setup(false, 0, "scripted", None).unwrap();
    session.finish_ledgers().unwrap();
    drop(session);
    for arm in 0..2 {
        assert_settled(
            &directory.join(ARM_NAMES[arm]), &key,
            prior[arm].invocations, prior[arm].charged_ms, opening_ms,
        );
    }
    // The new invocation records may be added; every existing byte remains exact.
    for (name, bytes) in immutable {
        assert!(fs::read(directory.join(name)).unwrap() == bytes);
    }
}

fn refused_opening(label: &str, opening_ms: u64) {
    let directory = root(label).join("run");
    let expected = manifest();
    let key = expected.stable_key().unwrap();
    let started = backdated(opening_ms);
    match ComparisonSession::open_at(&directory, false, expected, None, started) {
        Err(error) => assert_eq!(error, "RunBudget"),
        Ok(_) => panic!("exhausted opening work must not admit another invocation"),
    }
    // This is the actual admission gate used before native construction. No
    // fake provider counter or preowned runtime stands in for asset execution.
    let files = if directory.exists() { retained_files(&directory) } else { BTreeMap::new() };
    for name in files.keys() {
        let leaf = name.file_name().unwrap().to_str().unwrap();
        assert!(!leaf.starts_with("invocation-"));
        assert!(!leaf.starts_with("admission-"));
        assert!(!leaf.starts_with("setup-"));
        assert!(!leaf.ends_with(".sqlite"));
    }
    for arm in ARM_NAMES {
        let path = directory.join(arm);
        if !path.exists() { continue; }
        let ledger = Ledger::load(&path, &key).unwrap();
        assert_eq!((ledger.invocations, ledger.admissions, ledger.charged_roles, ledger.charged_ms), (0, 0, 0, 0));
    }
}

#[test]
fn exhausted_invocation_origin_refuses_before_any_durable_reservation_or_provider() {
    refused_opening("exhausted", MAX_ACTIVE_MS + PREPARATION_MS);
}

#[test]
fn positive_remaining_below_full_preparation_reserve_cannot_admit_an_invocation() {
    // Positive active budget is insufficient if it cannot retain the unchanged
    // full120s reservation. A check of charged_ms alone wrongly admits this.
    refused_opening("insufficient-reserve", MAX_ACTIVE_MS - PREPARATION_MS + 1);
}

#[test]
fn interrupted_original_clock_preserves_both_full_unknown_preparation_reservations() {
    let directory = root("unknown").join("run");
    let expected = manifest();
    let key = expected.stable_key().unwrap();
    let started = backdated(PREPARATION_MS + 9_000);
    let session = ComparisonSession::open_at(&directory, false, expected, None, started).unwrap();
    assert!(session.ledgers.iter().all(|ledger| ledger.started == started));
    drop(session); // Synthetic lost owner only, not an OS process kill.
    assert!(!directory.join("setup-00.json").exists());
    for arm in ARM_NAMES {
        let dir = directory.join(arm);
        assert!(!dir.join("invocation-00-settled.json").exists());
        let ledger = Ledger::load(&dir, &key).unwrap();
        assert_eq!(ledger.invocations, 1);
        assert_eq!(ledger.admissions, 0);
        assert_eq!(ledger.charged_roles, 0);
        assert_eq!(ledger.charged_ms, PREPARATION_MS);
        assert_eq!(ledger.prior_ms, PREPARATION_MS);
    }
}

#[test]
fn absolute_turn_deadline_charges_prelude_without_double_subtracting_active_remaining() {
    let started = Instant::now();
    let now = started + Duration::from_millis(25_000);
    let ordinary = turn_deadline(started, now, MAX_ACTIVE_MS);
    assert_eq!(ordinary, started + Duration::from_millis(TURN_MS));
    assert_eq!(ordinary.duration_since(now), Duration::from_millis(TURN_MS - 25_000));
    let tight = turn_deadline(started, now, 10_000);
    assert_eq!(tight, now + Duration::from_millis(10_000 - CLEANUP_RESERVE_MS));
    // Active remaining is already measured at now. Subtracting the prelude a
    // second time would cancel this genuinely remaining seven-second allowance.
    assert_eq!(tight.duration_since(now), Duration::from_millis(7_000));
    assert!(tight < ordinary);
}

#[test]
fn expired_prelude_and_cleanup_exhaustion_produce_no_dispatch_window() {
    let started = Instant::now();
    let expired_now = started + Duration::from_millis(TURN_MS + 1);
    let expired = turn_deadline(started, expired_now, MAX_ACTIVE_MS);
    assert_eq!(expired, started + Duration::from_millis(TURN_MS));
    assert!(expired < expired_now);
    let now = started + Duration::from_millis(1);
    for remaining in [0, 1, CLEANUP_RESERVE_MS] {
        assert_eq!(turn_deadline(started, now, remaining), now);
    }
    assert_eq!(
        turn_deadline(started, now, CLEANUP_RESERVE_MS + 1),
        now + Duration::from_millis(1),
    );
    // Pure absolute deadline semantics. Actual dispatch/watchdog call-site use
    // is separately coordinator-owned; no simulated provider execution is claimed.
}
