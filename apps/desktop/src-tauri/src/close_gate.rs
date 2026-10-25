//! Owner-free native close/exit coordination. A ticket is not cleanup proof.
//! Root owns actual manager proofs, event wiring and test execution separately.

#[cfg(test)]
mod tests {
    use super::*;

    fn start(gate: &mut CloseGate, epoch: u64, intent: Intent) -> CloseTicket {
        match gate.request(epoch, intent).expect("valid native request") {
            Decision::Start(ticket) => ticket,
            other => panic!("expected single cleanup admission, got {other:?}"),
        }
    }

    #[test]
    fn one_cleanup_admission_accumulates_exit_and_keeps_first_explicit_code() {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let ticket = start(&mut gate, 1, Intent::Window);
        assert_eq!(ticket.epoch(), 1);
        assert!(gate.pending());
        for intent in [Intent::Window, Intent::Exit(None), Intent::Exit(Some(7)), Intent::Exit(Some(9))] {
            assert_eq!(gate.request(1, intent), Ok(Decision::Pending));
        }
        assert!(gate.confirm(ticket)); // Synthetic trusted-callsite acknowledgment only.
        assert!(!gate.pending());
        assert!(!gate.confirm(ticket));
        assert_eq!(gate.take_continuation(ticket), Some(Continuation::Exit { code: Some(7) }));
        assert_eq!(gate.take_continuation(ticket), None);
        assert!(!gate.consume_exit(Some(9)));
        assert!(gate.consume_exit(Some(7)));
        assert!(!gate.consume_exit(Some(7)));
        assert_eq!(gate.opened(3), Err("Closed"));
    }

    #[test]
    fn explicit_exit_code_can_arrive_after_confirmation_but_not_replace_issued_exit() {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let ticket = start(&mut gate, 1, Intent::Exit(None));
        assert!(gate.confirm(ticket));
        assert_eq!(gate.request(1, Intent::Exit(Some(17))), Ok(Decision::Continue(ticket)));
        assert_eq!(gate.request(1, Intent::Window), Ok(Decision::Continue(ticket)));
        assert_eq!(gate.take_continuation(ticket), Some(Continuation::Exit { code: Some(17) }));
        assert_eq!(gate.request(1, Intent::Exit(Some(23))), Ok(Decision::Pending));
        assert!(!gate.consume_exit(Some(23)));
        assert!(gate.consume_exit(Some(17)));
        assert_eq!(gate.opened(3), Err("Closed"));
    }

    #[test]
    fn uncertain_pause_retries_with_fresh_ticket_and_old_completion_has_no_authority() {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let old = start(&mut gate, 1, Intent::Exit(Some(4)));
        assert!(gate.pause(old));
        assert!(gate.pending());
        assert!(!gate.pause(old));
        assert!(!gate.confirm(old));
        assert_eq!(gate.take_continuation(old), None);
        assert_eq!(gate.opened(3), Err("Closed"));
        let retry = start(&mut gate, 1, Intent::Window);
        assert_ne!(retry, old);
        assert_eq!(retry.epoch(), old.epoch());
        assert!(!gate.pause(old));
        assert!(!gate.confirm(old));
        assert_eq!(gate.take_continuation(old), None);
        assert!(gate.confirm(retry));
        assert_eq!(gate.take_continuation(retry), Some(Continuation::Exit { code: Some(4) }));
    }

    #[test]
    fn stale_epochs_tickets_and_invalid_inputs_never_upgrade_current_intent() {
        let mut gate = CloseGate::default();
        assert_eq!(gate.request(1, Intent::Exit(Some(99))), Err("Closed"));
        for invalid in [0, 2, 4, u64::MAX - 1] {
            assert_eq!(gate.opened(invalid), Err("Closed"));
        }
        gate.opened(3).unwrap();
        let mut old_gate = CloseGate::default();
        old_gate.opened(1).unwrap();
        let foreign_epoch = start(&mut old_gate, 1, Intent::Window);
        let current = start(&mut gate, 3, Intent::Window);
        for invalid in [0, 1, 2, 5, u64::MAX] {
            assert_eq!(gate.request(invalid, Intent::Exit(Some(99))), Err("Closed"));
        }
        assert!(!gate.confirm(foreign_epoch));
        assert!(!gate.pause(foreign_epoch));
        assert_eq!(gate.take_continuation(foreign_epoch), None);
        assert!(gate.confirm(current));
        assert_eq!(gate.take_continuation(current), Some(Continuation::DestroyWindow { epoch: 3 }));
        assert!(!gate.consume_exit(None));
    }

    #[test]
    fn reopen_requires_confirmation_and_consumed_destroy_continuation() {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let first = start(&mut gate, 1, Intent::Window);
        assert_eq!(gate.opened(3), Err("Closed"));
        assert!(gate.pause(first));
        assert_eq!(gate.opened(3), Err("Closed"));
        let retry = start(&mut gate, 1, Intent::Window);
        assert!(gate.confirm(retry));
        assert_eq!(gate.opened(3), Err("Closed"));
        assert_eq!(gate.take_continuation(retry), Some(Continuation::DestroyWindow { epoch: 1 }));
        for invalid in [0, 1, 2] {
            assert_eq!(gate.opened(invalid), Err("Closed"));
        }
        gate.opened(3).unwrap();
        assert_eq!(gate.opened(3), Err("Closed"));
        assert_eq!(gate.request(1, Intent::Exit(Some(9))), Err("Closed"));
        assert!(!gate.confirm(retry));
        assert!(!gate.pause(retry));
        assert_eq!(gate.take_continuation(retry), None);
        let next = start(&mut gate, 3, Intent::Window);
        assert_ne!(next, retry);
        assert_eq!(next.epoch(), 3);
    }

    #[test]
    fn late_exit_after_destroy_uses_already_confirmed_window_and_fresh_continuation() {
        let mut gate = CloseGate::default();
        gate.opened(1).unwrap();
        let window = start(&mut gate, 1, Intent::Window);
        assert!(gate.confirm(window));
        assert_eq!(gate.take_continuation(window), Some(Continuation::DestroyWindow { epoch: 1 }));
        assert_eq!(gate.request(1, Intent::Window), Ok(Decision::Pending));
        let exit = match gate.request(1, Intent::Exit(None)).unwrap() {
            Decision::Continue(ticket) => ticket,
            other => panic!("already clean window needs no second cleanup: {other:?}"),
        };
        assert_ne!(exit, window);
        assert!(!gate.pending());
        assert_eq!(gate.opened(3), Err("Closed"));
        assert_eq!(gate.request(1, Intent::Exit(Some(12))), Ok(Decision::Continue(exit)));
        assert_eq!(gate.take_continuation(window), None);
        assert_eq!(gate.take_continuation(exit), Some(Continuation::Exit { code: Some(12) }));
        assert!(gate.consume_exit(Some(12)));
    }

    #[test]
    fn exit_permit_normalizes_none_zero_and_only_matching_event_consumes_it_once() {
        for (requested, matching, wrong) in [
            (None, Some(0), Some(7)),
            (Some(0), None, Some(1)),
            (Some(5), Some(5), None),
            (Some(-7), Some(-7), Some(7)),
        ] {
            let mut gate = CloseGate::default();
            gate.opened(1).unwrap();
            let ticket = start(&mut gate, 1, Intent::Exit(requested));
            assert!(!gate.consume_exit(matching), "confirmation alone has not issued exit");
            assert!(gate.confirm(ticket));
            assert!(!gate.consume_exit(matching));
            assert_eq!(gate.take_continuation(ticket), Some(Continuation::Exit { code: requested }));
            assert!(!gate.consume_exit(wrong), "wrong event cannot discard the actual permit");
            assert!(gate.consume_exit(matching));
            assert!(!gate.consume_exit(matching));
            assert_eq!(gate.opened(3), Err("Closed"));
        }
    }

    #[test]
    fn sequence_exhaustion_refuses_retry_and_late_exit_without_partial_intent_change() {
        let mut pending = CloseGate::default();
        pending.opened(1).unwrap();
        pending.sequence = u64::MAX - 1; // Private unit boundary, no caller/wire hook.
        let last = start(&mut pending, 1, Intent::Window);
        assert!(pending.pause(last));
        assert_eq!(pending.request(1, Intent::Exit(Some(8))), Err("Closed"));
        assert!(pending.pending());
        assert!(!pending.confirm(last));
        assert_eq!(pending.take_continuation(last), None);
        assert_eq!(pending.opened(3), Err("Closed"));

        let mut closed = CloseGate::default();
        closed.opened(1).unwrap();
        let ticket = start(&mut closed, 1, Intent::Window);
        assert!(closed.confirm(ticket));
        assert_eq!(closed.take_continuation(ticket), Some(Continuation::DestroyWindow { epoch: 1 }));
        closed.sequence = u64::MAX;
        assert_eq!(closed.request(1, Intent::Exit(Some(8))), Err("Closed"));
        // Refusing a new exit ticket must not silently latch Exit and wedge reopen.
        closed.opened(3).unwrap();
        assert_eq!(closed.request(3, Intent::Window), Err("Closed"));
        assert!(!closed.pending());
    }
}
