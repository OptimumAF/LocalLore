// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Child of close_gate::tests.
//! SYNTHETIC trusted manager confirmations and native-event acknowledgements;
//! no actual HWND/WebView/Chromium, process cleanup or leak evidence.
use super::*;

fn continued(result: Result<Decision, &'static str>) -> CloseTicket {
    match result {
        Ok(Decision::Continue(ticket)) => ticket,
        other => panic!("expected one proven exit continuation, got {other:?}"),
    }
}
fn no_authority(result: Result<Decision, &'static str>) {
    assert!(matches!(result, Err(_) | Ok(Decision::Pending)),
        "invalid/duplicate event acquired authority: {result:?}");
}

#[test]
fn confirmed_exit_waits_for_observed_destruction_then_issues_exact_exit_once() {
    for code in [None, Some(0), Some(7)] {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let ticket = start(&mut gate, 1, Intent::Exit(code));
        assert!(gate.confirm(ticket)); // Manager proof is not a Destroyed event.
        assert_eq!(gate.take_continuation(ticket), Some(Continuation::DestroyWindow { epoch: 1 }));
        assert!(!gate.consume_exit(code));
        assert_eq!(gate.opened(3), Err("Closed"));
        let exit = continued(gate.destroyed(1));
        assert_eq!(exit.epoch(), 1);
        assert_eq!(gate.take_continuation(exit), Some(Continuation::Exit { code }));
        assert_eq!(gate.take_continuation(exit), None);
        assert!(gate.consume_exit(code));
        assert!(!gate.consume_exit(code));
        no_authority(gate.destroyed(1));
        assert!(!gate.consume_exit(code));
    }
}

#[test]
fn invalid_epochs_and_duplicate_unexpected_destruction_cannot_mint_extra_work() {
    let mut gate = CloseGate::default();
    gate.opened(1).unwrap();
    for epoch in [0, 2, 3, 4, u64::MAX - 1] {
        no_authority(gate.destroyed(epoch));
        assert_eq!(gate.current_epoch(), 1);
        assert!(!gate.consume_exit(None));
    }
    let ticket = match gate.destroyed(1) {
        Ok(Decision::Start(ticket)) => ticket,
        other => panic!("unexpected current-window destruction must admit cleanup: {other:?}"),
    };
    assert_eq!(ticket.epoch(), 1);
    no_authority(gate.destroyed(1));
    assert_eq!(gate.take_continuation(ticket), None);
    assert!(!gate.consume_exit(None));
    assert_eq!(gate.opened(3), Err("Closed"));
}

#[test]
fn early_destroyed_event_does_not_substitute_for_inflight_manager_confirmation() {
    let mut gate = CloseGate::default();
    gate.opened(1).unwrap();
    let ticket = start(&mut gate, 1, Intent::Exit(Some(7)));
    assert_eq!(gate.destroyed(1), Ok(Decision::Pending));
    assert_eq!(gate.take_continuation(ticket), None);
    assert!(!gate.consume_exit(Some(7)));
    assert_eq!(gate.opened(3), Err("Closed"));
    assert!(gate.confirm(ticket));
    // The window is already observed gone; do not issue another destroy.
    assert_eq!(gate.take_continuation(ticket), Some(Continuation::Exit { code: Some(7) }));
    assert!(gate.consume_exit(Some(7)));
    assert!(!gate.consume_exit(Some(7)));
}

#[test]
fn destruction_during_uncertain_cleanup_requires_a_fresh_confirmed_retry() {
    let mut gate = CloseGate::default();
    gate.opened(1).unwrap();
    let old = start(&mut gate, 1, Intent::Exit(Some(7)));
    assert!(gate.pause(old));
    assert_eq!(gate.destroyed(1), Ok(Decision::Pending));
    assert!(gate.pending(), "observed destruction cannot erase uncertain ownership");
    assert!(!gate.confirm(old));
    assert_eq!(gate.take_continuation(old), None);
    assert!(!gate.consume_exit(Some(7)));
    assert_eq!(gate.opened(3), Err("Closed"));
    let retry = start(&mut gate, 1, Intent::Window);
    assert_ne!(retry, old);
    assert!(!gate.confirm(old));
    assert!(gate.confirm(retry));
    assert_eq!(gate.take_continuation(retry), Some(Continuation::Exit { code: Some(7) }));
    assert!(gate.consume_exit(Some(7)));
    assert!(!gate.consume_exit(Some(7)));
}

#[test]
fn waiting_destroy_preserves_the_first_explicit_exit_code_across_duplicate_requests() {
    for first_explicit in [0, 7] {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let ticket = start(&mut gate, 1, Intent::Window);
        assert!(gate.confirm(ticket));
        assert_eq!(gate.take_continuation(ticket), Some(Continuation::DestroyWindow { epoch: 1 }));
        for intent in [Intent::Exit(None), Intent::Exit(Some(first_explicit)), Intent::Exit(Some(9)), Intent::Window] {
            assert_eq!(gate.request(1, intent), Ok(Decision::Pending));
        }
        assert_eq!(gate.take_continuation(ticket), None);
        assert!(!gate.consume_exit(Some(first_explicit)));
        let exit = continued(gate.destroyed(1));
        assert_eq!(gate.take_continuation(exit), Some(Continuation::Exit { code: Some(first_explicit) }));
        assert!(!gate.consume_exit(Some(9)));
        assert!(gate.consume_exit(Some(first_explicit)));
    }
}

#[test]
fn observed_window_destruction_allows_reopen_but_old_ack_or_failure_cannot_touch_it() {
    let mut gate = CloseGate::default();
    gate.opened(1).unwrap();
    let old = start(&mut gate, 1, Intent::Window);
    assert!(gate.confirm(old));
    assert_eq!(gate.take_continuation(old), Some(Continuation::DestroyWindow { epoch: 1 }));
    assert_eq!(gate.destroyed(1), Ok(Decision::Pending));
    gate.opened(3).unwrap();
    no_authority(gate.destroyed(1));
    assert!(!gate.continuation_failed(old));
    assert!(!gate.confirm(old));
    assert_eq!(gate.take_continuation(old), None);
    assert_eq!(gate.request(1, Intent::Exit(Some(9))), Err("Closed"));
    assert_eq!(gate.current_epoch(), 3);
    assert!(!gate.consume_exit(Some(9)));
    let current = start(&mut gate, 3, Intent::Window);
    assert_eq!(current.epoch(), 3);
}
