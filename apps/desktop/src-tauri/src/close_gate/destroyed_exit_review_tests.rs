// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Child of close_gate::tests.
//! SYNTHETIC trusted-manager confirmation, not actual native Destroyed/SDK,
//! Chromium teardown, child-process, leak or clean-OS-shutdown evidence.
//! Uses only the existing API: no future acknowledgement method is assumed.
use super::*;

#[test]
fn confirmed_coded_exit_first_requires_destroy_and_cannot_yet_consume_exit() {
    let mut observed = Vec::new();
    for code in [None, Some(0), Some(7)] {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let ticket = start(&mut gate, 1, Intent::Exit(code));
        assert!(gate.confirm(ticket)); // Synthetic app-owned manager proof only.
        let continuation = gate.take_continuation(ticket);
        let premature_exit = gate.consume_exit(code);
        observed.push((code, continuation, premature_exit));
    }
    for (code, continuation, premature_exit) in observed {
        assert_eq!(continuation, Some(Continuation::DestroyWindow { epoch: 1 }),
            "manager confirmation for {code:?} must first request native destruction");
        assert!(!premature_exit,
            "no native Destroyed acknowledgement exists for {code:?}");
    }
}

#[test]
fn duplicate_coded_events_cannot_upgrade_destroy_issuance_into_exit_permission() {
    let mut gate = CloseGate::default();
    gate.opened(1).unwrap();
    let ticket = start(&mut gate, 1, Intent::Window);
    assert!(gate.confirm(ticket)); // Actual native destruction has NOT occurred.
    assert_eq!(gate.take_continuation(ticket), Some(Continuation::DestroyWindow { epoch: 1 }));
    let mut issued_exits = Vec::new();
    for intent in [Intent::Exit(None), Intent::Exit(Some(0)), Intent::Exit(Some(7)), Intent::Window] {
        let decision = gate.request(1, intent).unwrap();
        if let Decision::Continue(next) = decision {
            if let Some(continuation @ Continuation::Exit { .. }) = gate.take_continuation(next) {
                issued_exits.push(continuation);
            }
        }
    }
    let permits = [None, Some(0), Some(7)].map(|code| (code, gate.consume_exit(code)));
    assert!(issued_exits.is_empty(),
        "duplicates minted exit before native Destroyed: {issued_exits:?}");
    assert!(permits.iter().all(|(_, accepted)| !accepted),
        "duplicates minted a consumable pre-destruction permit: {permits:?}");
}

#[test]
fn window_destroy_issuance_alone_does_not_allow_a_new_live_epoch() {
    let mut gate = CloseGate::default();
    gate.opened(1).unwrap();
    let ticket = start(&mut gate, 1, Intent::Window);
    assert!(gate.confirm(ticket)); // Synthetic manager cleanup, no native event.
    assert_eq!(gate.take_continuation(ticket), Some(Continuation::DestroyWindow { epoch: 1 }));
    // Issuing destroy can be queued or fail; it is not an observation that the
    // old native window/WebView is gone. Do not admit another window yet.
    assert_eq!(gate.opened(3), Err("Closed"));
    assert_eq!(gate.current_epoch(), 1);
    assert!(!gate.consume_exit(None));
    assert!(!gate.consume_exit(Some(0)));
}
