// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST additive source freeze on 3c1f1146: UNCOMPILED/UNRUN. Existing public
//! manager APIs and metadata-only indices; no completed native data or runtime.
//! Root registers this child under scene_native_review and executes it unchanged.
use super::*;

fn native_protocol(version: u16) -> FullComparisonProtocol {
    match version {
        2 => FullComparisonProtocol::LiteralV3,
        3 => FullComparisonProtocol::SceneV4,
        _ => panic!("fixed native fixture mode"),
    }
}
fn lookup(f: &Fixture, lease: &WindowLease, epoch: u64, version: u16, client: &str) -> Value {
    if version == 1 {
        f.manager
            .full_comparison_lookup(lease, epoch, true, client)
            .unwrap()
    } else {
        f.manager
            .full_comparison_lookup_native_for(lease, epoch, true, native_protocol(version), client)
            .unwrap()
    }
}
fn status(f: &Fixture, lease: &WindowLease, epoch: u64, version: u16, cap: &str) -> Result<Value> {
    if version == 1 {
        f.manager.full_comparison_status(lease, epoch, true, cap)
    } else {
        f.manager.full_comparison_status_native_for(
            lease,
            epoch,
            true,
            native_protocol(version),
            cap,
        )
    }
}
fn cancel(f: &Fixture, lease: &WindowLease, epoch: u64, version: u16, cap: &str) -> Result<Value> {
    // No operation exists. Owner refusal must precede even that job lookup.
    if version == 1 {
        f.manager.full_comparison_cancel(lease, epoch, true, cap, 1)
    } else {
        f.manager.full_comparison_cancel_native_for(
            lease,
            epoch,
            true,
            native_protocol(version),
            cap,
            1,
        )
    }
}
fn resume(
    f: &Fixture,
    lease: &Arc<WindowLease>,
    epoch: u64,
    version: u16,
    cap: &str,
) -> Result<Value> {
    if version == 1 {
        f.manager.full_comparison_resume(lease, epoch, true, cap, 1)
    } else {
        f.manager.full_comparison_resume_native_for(
            lease,
            &f.models,
            epoch,
            true,
            native_protocol(version),
            FullComparisonNativeResume {
                run_token: cap.into(),
                max_new_scenes: 1,
            },
            |_| panic!("stolen token must never reach execution consent"),
        )
    }
}
fn close(f: &Fixture, lease: &WindowLease, epoch: u64, version: u16, cap: &str) -> Result<Value> {
    if version == 1 {
        f.manager.full_comparison_close(lease, epoch, false, cap)
    } else {
        f.manager.full_comparison_close_native_for(
            lease,
            epoch,
            false,
            native_protocol(version),
            cap,
        )
    }
}

fn independent_same_epoch_capabilities(version: u16) {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let run = f.metadata(version, &client); // Wrapper only; there is no work/report.
    let before = inventory(&f.root);
    let assets = f.assets();
    let first = lookup(&f, &f.lease, f.epoch, version, &client);
    let first_token = token(&first).to_owned();
    assert_eq!(
        token(&lookup(&f, &f.lease, f.epoch, version, &client)),
        first_token,
        "same owner browsing reuses its token"
    );

    let other = Arc::new(WindowLease::default());
    let other_epoch = other.begin().unwrap();
    assert_eq!(
        other_epoch, f.epoch,
        "equal epochs do not identify the same native window"
    );
    let second = lookup(&f, &other, other_epoch, version, &client); // Explicit authorized new-window lookup.
    let second_token = token(&second).to_owned();
    assert_ne!(second_token,first_token,"same run in another live lease must mint a distinct capability, never rebind the old token");
    assert_eq!(
        token(&lookup(&f, &other, other_epoch, version, &client)),
        second_token
    );
    for (lease, epoch, own, stolen) in [
        (
            &f.lease,
            f.epoch,
            first_token.as_str(),
            second_token.as_str(),
        ),
        (
            &other,
            other_epoch,
            second_token.as_str(),
            first_token.as_str(),
        ),
    ] {
        let own_status = status(&f, lease, epoch, version, own).unwrap();
        assert_eq!(own_status["run_id"], run);
        assert_eq!(own_status["run_token"], own);
        rejected(
            status(&f, lease, epoch, version, stolen),
            "UnknownEvaluationRun",
        );
        rejected(
            cancel(&f, lease, epoch, version, stolen),
            "UnknownEvaluationRun",
        );
        rejected(
            resume(&f, lease, epoch, version, stolen),
            "UnknownEvaluationRun",
        );
        rejected(
            close(&f, lease, epoch, version, stolen),
            "UnknownEvaluationRun",
        );
        assert_eq!(
            status(&f, lease, epoch, version, own).unwrap()["run_id"],
            run,
            "stolen close cannot revoke its rightful sibling"
        );
    }
    close(&f, &f.lease, f.epoch, version, &first_token).unwrap();
    rejected(
        status(&f, &f.lease, f.epoch, version, &first_token),
        "UnknownEvaluationRun",
    );
    assert_eq!(
        status(&f, &other, other_epoch, version, &second_token).unwrap()["run_id"],
        run,
        "one rightful close must not delete the other owner's handle"
    );
    let reopened = lookup(&f, &f.lease, f.epoch, version, &client);
    let fresh = token(&reopened).to_owned();
    assert_ne!(fresh, first_token);
    assert_ne!(fresh, second_token);
    assert_eq!(
        status(&f, &other, other_epoch, version, &second_token).unwrap()["run_token"],
        second_token
    );
    close(&f, &f.lease, f.epoch, version, &fresh).unwrap();
    close(&f, &other, other_epoch, version, &second_token).unwrap();
    assert_eq!(f.sequence(), 0);
    assert_eq!(f.assets(), assets);
    assert_eq!(inventory(&f.root), before);
}

#[test]
fn scripted3_same_run_has_independent_same_epoch_window_capabilities() {
    independent_same_epoch_capabilities(1);
}
#[test]
fn native3_same_run_has_independent_same_epoch_window_capabilities() {
    independent_same_epoch_capabilities(2);
}
#[test]
fn native4_same_run_has_independent_same_epoch_window_capabilities() {
    independent_same_epoch_capabilities(3);
}

#[test]
fn four_handle_bound_evicts_oldest_without_rebinding_still_live_window_capabilities() {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let run = f.metadata(3, &client);
    let before = inventory(&f.root);
    let mut owners = Vec::new();
    let mut tokens = Vec::new();
    // No sleeps or new quota: existing map ordering/touched observation fixes
    // only the old handle's LRU age after admission, using retained native state.
    for _ in 0..4 {
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        assert_eq!(epoch, f.epoch);
        let opened = lookup(&f, &lease, epoch, 3, &client);
        let cap = token(&opened).to_owned();
        assert!(
            !tokens.contains(&cap),
            "each owner must have a separate capability before LRU testing"
        );
        owners.push(lease);
        tokens.push(cap);
    }
    assert_eq!(f.manager.state().unwrap().tokens.len(), 4);
    {
        let mut state = f.manager.state().unwrap();
        state.tokens.get_mut(&tokens[0]).unwrap().touched =
            Instant::now().checked_sub(Duration::from_secs(1)).unwrap();
    }
    let fifth = Arc::new(WindowLease::default());
    let epoch = fifth.begin().unwrap();
    let newest = lookup(&f, &fifth, epoch, 3, &client);
    let fifth_token = token(&newest).to_owned();
    assert!(!tokens.contains(&fifth_token));
    assert_eq!(
        f.manager.state().unwrap().tokens.len(),
        4,
        "scope ownership must not enlarge the established token cap"
    );
    rejected(
        status(&f, &owners[0], epoch, 3, &tokens[0]),
        "UnknownEvaluationRun",
    );
    for index in 1..4 {
        assert_eq!(
            status(&f, &owners[index], epoch, 3, &tokens[index]).unwrap()["run_id"],
            run
        );
        rejected(
            status(&f, &fifth, epoch, 3, &tokens[index]),
            "UnknownEvaluationRun",
        );
    }
    for index in 1..4 {
        close(&f, &owners[index], epoch, 3, &tokens[index]).unwrap();
    }
    close(&f, &fifth, epoch, 3, &fifth_token).unwrap();
    assert_eq!(f.manager.state().unwrap().tokens.len(), 0);
    assert_eq!(f.sequence(), 0);
    assert_eq!(inventory(&f.root), before);
}
