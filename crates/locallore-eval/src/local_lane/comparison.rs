//! Current-policy comparison runner. Frozen tests precede implementation.

#[cfg(test)]
mod clock_tests {
    use super::super::*;

    fn directory(name: &str) -> PathBuf {
        let p = std::env::temp_dir().join(format!(
            "locallore-comparison-clock-{name}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()
        ));
        fs::create_dir(&p).unwrap();
        p
    }

    #[test]
    fn zero_adjustment_is_exact_legacy_wall_clock() {
        let p = directory("legacy");
        let l = Ledger::load(&p, "frozen-binding").unwrap();
        for wall in [0, 1, 60_000, 1_800_000, u64::MAX] {
            assert_eq!(l.active_elapsed(wall), wall);
        }
    }

    #[test]
    fn excludes_only_explicitly_measured_other_arm_and_splits_known_setup_once() {
        let p = directory("measured");
        let mut l = Ledger::load(&p, "frozen-binding").unwrap();
        assert_eq!(shared_setup_shares(101), (51, 50));
        assert_eq!(shared_setup_shares(120_000), (60_000, 60_000));
        l.exclude_measured_interval(70).unwrap();
        l.record_shared_setup(101, 51).unwrap();
        // Physical 101 + own 9 + other 70 + own checkpoint 3. Own charge is 63.
        assert_eq!(l.active_elapsed(183), 63);
        assert!(l.record_shared_setup(101, 51).is_err());
        assert_eq!(l.active_elapsed(183), 63);
    }

    #[test]
    fn invalid_setup_and_exclusion_overflow_do_not_mutate_accounting() {
        let p = directory("invalid");
        let mut l = Ledger::load(&p, "frozen-binding").unwrap();
        assert!(l.record_shared_setup(120_001, 1).is_err());
        assert!(l.record_shared_setup(10, 11).is_err());
        assert_eq!(l.active_elapsed(120_001), 120_001);
        l.exclude_measured_interval(u64::MAX).unwrap();
        assert!(l.exclude_measured_interval(1).is_err());
        assert_eq!(l.active_elapsed(u64::MAX), 0);
    }

    #[test]
    fn crash_or_cancel_before_known_terminal_keeps_both_full_setup_reservations() {
        let left = directory("unknown-left");
        let right = directory("unknown-right");
        for p in [&left, &right] {
            let mut l = Ledger::load(p, "frozen-binding").unwrap();
            l.begin_invocation().unwrap();
            // Drop models an interrupted owner; no invented terminal settlement.
        }
        for p in [&left, &right] {
            let l = Ledger::load(p, "frozen-binding").unwrap();
            assert_eq!(l.charged_ms, 120_000);
            assert_eq!(l.invocations, 1);
            assert_eq!(l.charged_roles, 0);
            assert!(!p.join("invocation-00-settled.json").exists());
        }
    }

    #[test]
    fn unknown_turn_reserves_full_roles_and_time_across_reopen() {
        let p = directory("unknown-turn");
        {
            let mut l = Ledger::load(&p, "frozen-binding").unwrap();
            l.begin_invocation().unwrap();
            l.admit("scene-1", "attempt-1").unwrap();
            l.exclude_measured_interval(9_999).unwrap();
        }
        let l = Ledger::load(&p, "frozen-binding").unwrap();
        assert_eq!(l.charged_ms, 180_000);
        assert_eq!(l.charged_roles, 3);
        assert_eq!(l.admissions, 1);
        // Volatile measured exclusions cannot refund previous unknown work.
        assert_eq!(l.active_elapsed(20), 20);
    }

    #[test]
    fn known_terminal_turn_zero_roles_has_exact_durable_charge() {
        let p = directory("guard-terminal");
        {
            let mut l = Ledger::load(&p, "frozen-binding").unwrap();
            l.begin_invocation().unwrap();
            let index = l.admit("scene-1", "guard-1").unwrap();
            l.settle(index, 7, 0).unwrap();
        }
        let l = Ledger::load(&p, "frozen-binding").unwrap();
        assert_eq!(l.charged_ms, 120_007);
        assert_eq!(l.charged_roles, 0);
        assert_eq!(l.admissions, 1);
    }
}
