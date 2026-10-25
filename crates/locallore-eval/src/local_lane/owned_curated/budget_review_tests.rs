// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen owned-curated admission/entry-clock regressions; SOURCE UNRUN.
//! Root registers this as a child of owned_curated::review_tests. Only actual
//! Session/Ledger operations and missing-assets Reservation are used. Unknown
//! admissions are reservations, never claimed actual role calls or known work.
use super::*;

struct EntryReset;
impl Drop for EntryReset {
    fn drop(&mut self) {
        super::super::ENTRY_STARTED_OVERRIDE.with(|entry| entry.set(None));
    }
}

#[test]
fn insufficient_next_turn_budget_refuses_before_assets_after_one_known_resume_invocation() {
    let root = root("turn-budget-review");
    let directory = root.join("run");
    let mut session = Session::open(
        &directory,
        false,
        Some("gift-agency"),
        true,
        native_profile().unwrap(),
        false,
    )
    .unwrap();
    assert!(!session.all_saved().unwrap());
    for index in 0..27 {
        assert_eq!(
            session
                .ledger
                .admit("gift-agency", &format!("unknown-{index:02}"))
                .unwrap(),
            index
        );
    }
    // Finish this actual invocation's overhead only. No admission is settled,
    // no synthetic roles/times are written, and no provider has been invoked.
    session.ledger.finish().unwrap();
    drop(session);
    let original = actual_ledger(&directory);
    assert_eq!(original.invocations, 1);
    assert_eq!(original.admissions, 27);
    assert_eq!(original.charged_roles, 27 * 3);
    assert!(
        original.remaining() >= PREPARATION_MS,
        "fixture can afford preparation reservation"
    );
    assert!(
        original.remaining_after_reservation(PREPARATION_MS) < TURN_MS + CLEANUP_RESERVE_MS,
        "fixture cannot afford a turn after that already-existing preparation reserve"
    );
    let before = inventory(&directory);
    let spy = Arc::new(Spy::default());
    let error = failure(run_native_curated_owned(
        &directory,
        true,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        Reservation::new(&root, &spy),
    ));
    let code = error.code().to_owned();
    let uncertain = error.cleanup_uncertain();
    assert!(
        error.into_retained().is_err(),
        "model-free rejection has no actual child pair"
    );
    let after = inventory(&directory);
    for (name, bytes) in &before {
        assert_eq!(
            after.get(name),
            Some(bytes),
            "prior evidence changed: {name:?}"
        );
    }
    let added: Vec<_> = after
        .keys()
        .filter(|name| !before.contains_key(*name))
        .cloned()
        .collect();
    assert_eq!(
        added,
        vec![
            PathBuf::from("invocation-01-settled.json"),
            PathBuf::from("invocation-01.json")
        ]
    );
    let settlement: Settlement =
        serde_json::from_slice(&fs::read(directory.join("invocation-01-settled.json")).unwrap())
            .unwrap();
    assert_eq!((settlement.index, settlement.roles), (1, 0));
    let resumed = actual_ledger(&directory);
    assert_eq!(
        (
            resumed.invocations,
            resumed.admissions,
            resumed.charged_roles
        ),
        (2, 27, 81)
    );
    assert_eq!(
        resumed.charged_ms,
        original.charged_ms.checked_add(settlement.ms).unwrap(),
        "known opening overhead is charged once; no second preparation reserve"
    );
    for index in 0..27 {
        assert!(!directory
            .join(format!("admission-{index:02}-settled.json"))
            .exists());
    }
    assert!(!directory.join("report.json").exists() && !directory.join("report.html").exists());
    assert_eq!(
        (
            code,
            spy.assets.load(Ordering::SeqCst),
            spy.drops.load(Ordering::SeqCst),
            uncertain
        ),
        ("RunBudget".to_owned(), 0, 1, false)
    );
    assert!(!spy.busy.load(Ordering::SeqCst));
}

#[test]
fn exhausted_entry_clock_refuses_before_new_invocation_or_assets_and_preserves_inventory() {
    let _reset = EntryReset;
    let root = root("entry-budget-review");
    let directory = root.join("run");
    let mut session = Session::open(
        &directory,
        false,
        Some("gift-agency"),
        true,
        native_profile().unwrap(),
        false,
    )
    .unwrap();
    assert!(!session.all_saved().unwrap());
    session.ledger.finish().unwrap();
    drop(session);
    let original = actual_ledger(&directory);
    assert_eq!(
        (
            original.invocations,
            original.admissions,
            original.charged_roles
        ),
        (1, 0, 0)
    );
    let before = inventory(&directory);
    let spy = Arc::new(Spy::default());
    let reservation = Reservation::new(&root, &spy);
    // Fixed cfg(test)-only origin seam, consumed once at the public entry.
    // This is not measured opening work or a production clock/timeout override.
    let started = Instant::now()
        .checked_sub(Duration::from_millis(MAX_ACTIVE_MS + 1_000))
        .unwrap();
    super::super::ENTRY_STARTED_OVERRIDE.with(|entry| entry.set(Some(started)));
    let error = failure(run_native_curated_owned(
        &directory,
        true,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        reservation,
    ));
    let code = error.code().to_owned();
    assert!(!error.cleanup_uncertain());
    assert!(error.into_retained().is_err());
    assert_eq!(spy.assets.load(Ordering::SeqCst), 0);
    assert_eq!(spy.drops.load(Ordering::SeqCst), 1);
    assert!(!spy.busy.load(Ordering::SeqCst));
    assert_eq!(code, "RunBudget");
    assert_eq!(
        inventory(&directory),
        before,
        "an exhausted entry cannot create/refund/settle another invocation"
    );
    let after = actual_ledger(&directory);
    assert_eq!(
        (
            after.invocations,
            after.admissions,
            after.charged_roles,
            after.charged_ms
        ),
        (
            original.invocations,
            original.admissions,
            original.charged_roles,
            original.charged_ms
        )
    );
}
