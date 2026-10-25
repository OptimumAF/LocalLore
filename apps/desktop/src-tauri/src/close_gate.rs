//! Owner-free native close/exit coordination. A ticket is not cleanup proof.
//! Root owns actual manager proofs, event wiring and test execution separately.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Intent {
    Window,
    Exit(Option<i32>),
}

/// Single-app-gate coordinates only, not an owner identity or cleanup grant.
/// The caller binds epochs to its actual WindowLease; JSON cannot mint tickets.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct CloseTicket {
    epoch: u64,
    sequence: u64,
}
impl CloseTicket {
    pub(crate) fn epoch(self) -> u64 {
        self.epoch
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Decision {
    Start(CloseTicket),
    Pending,
    Continue(CloseTicket),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Continuation {
    DestroyWindow { epoch: u64 },
    Exit { code: Option<i32> },
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Phase {
    Unopened,
    Open,
    InFlight(CloseTicket),
    Uncertain(CloseTicket),
    Confirmed(CloseTicket),
    WindowContinued,
    ExitContinued,
}

/// Mutable owner-free FSM. Root wraps this in existing app-state coordination;
/// no manager, worker, resource, path, serialization or execution lives here.
pub(crate) struct CloseGate {
    epoch: u64,
    sequence: u64,
    phase: Phase,
    intent: Intent,
    exit_permit: Option<i32>,
}
impl Default for CloseGate {
    fn default() -> Self {
        Self {
            epoch: 0,
            sequence: 0,
            phase: Phase::Unopened,
            intent: Intent::Window,
            exit_permit: None,
        }
    }
}

impl CloseGate {
    pub(crate) fn current_epoch(&self) -> u64 {
        self.epoch
    }
    pub(crate) fn opened(&mut self, epoch: u64) -> Result<(), &'static str> {
        if epoch == 0
            || epoch.is_multiple_of(2)
            || epoch <= self.epoch
            || matches!(self.intent, Intent::Exit(_))
            || self.exit_permit.is_some()
            || !matches!(self.phase, Phase::Unopened | Phase::WindowContinued)
        {
            return Err("Closed");
        }
        self.epoch = epoch;
        self.phase = Phase::Open;
        self.intent = Intent::Window;
        Ok(())
    }

    fn next_ticket(&mut self) -> Result<CloseTicket, &'static str> {
        let sequence = self.sequence.checked_add(1).ok_or("Closed")?;
        self.sequence = sequence;
        Ok(CloseTicket {
            epoch: self.epoch,
            sequence,
        })
    }

    fn upgrade_intent(&mut self, requested: Intent) {
        if let Intent::Exit(code) = requested {
            match self.intent {
                Intent::Window => self.intent = requested,
                Intent::Exit(None) if code.is_some() => self.intent = requested,
                Intent::Exit(_) => {}
            }
        }
    }

    pub(crate) fn request(&mut self, epoch: u64, intent: Intent) -> Result<Decision, &'static str> {
        if epoch == 0 || epoch.is_multiple_of(2) || epoch != self.epoch {
            return Err("Closed");
        }
        match self.phase {
            Phase::Unopened => Err("Closed"),
            Phase::Open | Phase::Uncertain(_) => {
                // Counter refusal must not upgrade intent or erase uncertainty.
                let ticket = self.next_ticket()?;
                self.upgrade_intent(intent);
                self.phase = Phase::InFlight(ticket);
                Ok(Decision::Start(ticket))
            }
            Phase::InFlight(_) => {
                self.upgrade_intent(intent);
                Ok(Decision::Pending)
            }
            Phase::Confirmed(ticket) => {
                self.upgrade_intent(intent);
                Ok(Decision::Continue(ticket))
            }
            Phase::WindowContinued if matches!(intent, Intent::Exit(_)) => {
                // No new window/work was admitted since this epoch's proof.
                // A fresh continuation ticket prevents reuse of the destroy ack.
                let ticket = self.next_ticket()?;
                self.upgrade_intent(intent);
                self.phase = Phase::Confirmed(ticket);
                Ok(Decision::Continue(ticket))
            }
            Phase::WindowContinued | Phase::ExitContinued => {
                // An already issued exit/permit cannot be changed retroactively.
                Ok(Decision::Pending)
            }
        }
    }

    pub(crate) fn pause(&mut self, ticket: CloseTicket) -> bool {
        if self.phase != Phase::InFlight(ticket) || ticket.epoch != self.epoch {
            return false;
        }
        self.phase = Phase::Uncertain(ticket);
        true
    }

    /// Only the trusted native callsite may acknowledge both manager proofs.
    /// This transition performs no cleanup and does not validate that proof.
    pub(crate) fn confirm(&mut self, ticket: CloseTicket) -> bool {
        if self.phase != Phase::InFlight(ticket) || ticket.epoch != self.epoch {
            return false;
        }
        self.phase = Phase::Confirmed(ticket);
        true
    }

    pub(crate) fn take_continuation(&mut self, ticket: CloseTicket) -> Option<Continuation> {
        if self.phase != Phase::Confirmed(ticket)
            || ticket.epoch != self.epoch
            || self.exit_permit.is_some()
        {
            return None;
        }
        match self.intent {
            Intent::Window => {
                self.phase = Phase::WindowContinued;
                Some(Continuation::DestroyWindow {
                    epoch: ticket.epoch,
                })
            }
            Intent::Exit(code) => {
                self.exit_permit = Some(code.unwrap_or(0));
                self.phase = Phase::ExitContinued;
                Some(Continuation::Exit { code })
            }
        }
    }

    pub(crate) fn consume_exit(&mut self, code: Option<i32>) -> bool {
        if self.exit_permit != Some(code.unwrap_or(0)) {
            return false;
        }
        self.exit_permit = None;
        true
    }

    /// A trusted native scheduling/destroy failure can reissue only this
    /// already-proven continuation. It cannot undo a consumed exit, later
    /// continuation sequence or a newer window's lifetime.
    pub(crate) fn continuation_failed(&mut self, ticket: CloseTicket) -> bool {
        if ticket.epoch != self.epoch || ticket.sequence != self.sequence {
            return false;
        }
        if !matches!(self.phase, Phase::WindowContinued)
            && !(self.phase == Phase::ExitContinued && self.exit_permit.is_some())
        {
            return false;
        }
        self.exit_permit = None;
        self.phase = Phase::Confirmed(ticket);
        true
    }

    /// Coordination status only: false never proves that a child is terminal.
    pub(crate) fn pending(&self) -> bool {
        matches!(self.phase, Phase::InFlight(_) | Phase::Uncertain(_))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[path = "continuation_review_tests.rs"]
    mod continuation_review_tests;

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
        for intent in [
            Intent::Window,
            Intent::Exit(None),
            Intent::Exit(Some(7)),
            Intent::Exit(Some(9)),
        ] {
            assert_eq!(gate.request(1, intent), Ok(Decision::Pending));
        }
        assert!(gate.confirm(ticket)); // Synthetic trusted-callsite acknowledgment only.
        assert!(!gate.pending());
        assert!(!gate.confirm(ticket));
        assert_eq!(
            gate.take_continuation(ticket),
            Some(Continuation::Exit { code: Some(7) })
        );
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
        assert_eq!(
            gate.request(1, Intent::Exit(Some(17))),
            Ok(Decision::Continue(ticket))
        );
        assert_eq!(
            gate.request(1, Intent::Window),
            Ok(Decision::Continue(ticket))
        );
        assert_eq!(
            gate.take_continuation(ticket),
            Some(Continuation::Exit { code: Some(17) })
        );
        assert_eq!(
            gate.request(1, Intent::Exit(Some(23))),
            Ok(Decision::Pending)
        );
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
        assert_eq!(
            gate.take_continuation(retry),
            Some(Continuation::Exit { code: Some(4) })
        );
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
        assert_eq!(
            gate.take_continuation(current),
            Some(Continuation::DestroyWindow { epoch: 3 })
        );
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
        assert_eq!(
            gate.take_continuation(retry),
            Some(Continuation::DestroyWindow { epoch: 1 })
        );
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
        assert_eq!(
            gate.take_continuation(window),
            Some(Continuation::DestroyWindow { epoch: 1 })
        );
        assert_eq!(gate.request(1, Intent::Window), Ok(Decision::Pending));
        let exit = match gate.request(1, Intent::Exit(None)).unwrap() {
            Decision::Continue(ticket) => ticket,
            other => panic!("already clean window needs no second cleanup: {other:?}"),
        };
        assert_ne!(exit, window);
        assert!(!gate.pending());
        assert_eq!(gate.opened(3), Err("Closed"));
        assert_eq!(
            gate.request(1, Intent::Exit(Some(12))),
            Ok(Decision::Continue(exit))
        );
        assert_eq!(gate.take_continuation(window), None);
        assert_eq!(
            gate.take_continuation(exit),
            Some(Continuation::Exit { code: Some(12) })
        );
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
            assert!(
                !gate.consume_exit(matching),
                "confirmation alone has not issued exit"
            );
            assert!(gate.confirm(ticket));
            assert!(!gate.consume_exit(matching));
            assert_eq!(
                gate.take_continuation(ticket),
                Some(Continuation::Exit { code: requested })
            );
            assert!(
                !gate.consume_exit(wrong),
                "wrong event cannot discard the actual permit"
            );
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
        assert_eq!(
            closed.take_continuation(ticket),
            Some(Continuation::DestroyWindow { epoch: 1 })
        );
        closed.sequence = u64::MAX;
        assert_eq!(closed.request(1, Intent::Exit(Some(8))), Err("Closed"));
        // Refusing a new exit ticket must not silently latch Exit and wedge reopen.
        closed.opened(3).unwrap();
        assert_eq!(closed.request(3, Intent::Window), Err("Closed"));
        assert!(!closed.pending());
    }
}
