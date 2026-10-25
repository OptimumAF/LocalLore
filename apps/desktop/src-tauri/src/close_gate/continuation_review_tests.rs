// SOURCE ONLY / UNCOMPILED / UNRUN. Child of close_gate::tests.
// Owner-free native coordination only: confirm() below is synthetic and does
// not attest to child cleanup, actual Tauri scheduling, destroy or process exit.
use super::*;

#[test]
fn failed_issued_window_continuation_can_retry_same_proven_ticket_once() {
    let mut gate = CloseGate::default(); gate.opened(1).unwrap();
    let ticket = start(&mut gate, 1, Intent::Window);
    assert!(!gate.continuation_failed(ticket));
    assert!(gate.confirm(ticket));
    assert!(!gate.continuation_failed(ticket), "not issued yet");
    assert_eq!(gate.take_continuation(ticket), Some(Continuation::DestroyWindow { epoch: 1 }));
    assert!(gate.continuation_failed(ticket));
    assert!(!gate.continuation_failed(ticket), "same failure cannot be acknowledged twice");
    assert_eq!(gate.opened(3), Err("Closed"));
    assert_eq!(gate.request(1, Intent::Window), Ok(Decision::Continue(ticket)));
    assert_eq!(gate.take_continuation(ticket), Some(Continuation::DestroyWindow { epoch: 1 }));
    assert_eq!(gate.take_continuation(ticket), None);
}

#[test]
fn failed_unconsumed_exit_preserves_first_explicit_code_and_reissues_one_permit() {
    for code in [None, Some(0), Some(17), Some(-2)] {
        let mut gate = CloseGate::default(); gate.opened(1).unwrap();
        let ticket = start(&mut gate, 1, Intent::Exit(code)); assert!(gate.confirm(ticket));
        assert_eq!(gate.take_continuation(ticket), Some(Continuation::Exit { code }));
        assert!(gate.continuation_failed(ticket));
        assert!(!gate.consume_exit(code), "failed scheduling revoked its unconsumed permit");
        assert_eq!(gate.request(1, Intent::Window), Ok(Decision::Continue(ticket)));
        assert_eq!(gate.take_continuation(ticket), Some(Continuation::Exit { code }));
        assert!(gate.consume_exit(code));
        assert!(!gate.consume_exit(code));
        assert!(!gate.continuation_failed(ticket), "actual permitted exit cannot be undone");
        assert_eq!(gate.take_continuation(ticket), None);
    }
}

#[test]
fn old_window_failure_cannot_undo_late_exit_new_sequence_or_new_window_epoch() {
    let mut gate = CloseGate::default(); gate.opened(1).unwrap();
    let window = start(&mut gate, 1, Intent::Window); assert!(gate.confirm(window));
    gate.take_continuation(window).unwrap();
    let exit = match gate.request(1, Intent::Exit(Some(9))).unwrap() {
        Decision::Continue(ticket) => ticket, other => panic!("expected proven clean exit {other:?}"),
    };
    assert_ne!(exit, window); assert!(!gate.continuation_failed(window));
    assert_eq!(gate.take_continuation(exit), Some(Continuation::Exit { code: Some(9) }));
    assert!(!gate.continuation_failed(window)); assert!(gate.consume_exit(Some(9)));
    assert!(!gate.continuation_failed(exit));

    let mut gate = CloseGate::default(); gate.opened(1).unwrap();
    let old = start(&mut gate, 1, Intent::Window); assert!(gate.confirm(old));
    gate.take_continuation(old).unwrap(); gate.opened(3).unwrap();
    assert!(!gate.continuation_failed(old));
    let current = start(&mut gate, 3, Intent::Window);
    assert!(!gate.continuation_failed(old)); assert!(!gate.continuation_failed(current));
    assert!(gate.confirm(current));
    assert_eq!(gate.take_continuation(current), Some(Continuation::DestroyWindow { epoch: 3 }));
    assert!(!gate.continuation_failed(old)); assert!(gate.continuation_failed(current));
}
