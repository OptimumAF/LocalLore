// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Closed native-origin codes. This module performs no filesystem or symbol operation.

pub(super) const SYMBOL_UNAVAILABLE: i32 = 5;

/// Classify only the errno observed after the single failed no-replace rename.
/// Missing-symbol classification is separate; no category authorizes a fallback.
pub(super) fn rename_failure(errno: Option<i32>) -> i32 {
    match errno {
        Some(17) => 1, // EEXIST
        Some(22) => 6, // EINVAL
        Some(38) => 7, // ENOSYS
        Some(95) => 8, // EOPNOTSUPP
        _ => 3,
    }
}

#[cfg(test)]
mod tests {
    use super::{rename_failure, SYMBOL_UNAVAILABLE};

    #[test]
    fn exact_rename_failures_preserve_distinct_closed_origins() {
        assert_eq!(rename_failure(Some(17)), 1);
        assert_eq!(rename_failure(Some(22)), 6);
        assert_eq!(rename_failure(Some(38)), 7);
        assert_eq!(rename_failure(Some(95)), 8);
    }

    #[test]
    fn missing_or_unrecognized_errno_is_io_failure_never_success() {
        assert_eq!(rename_failure(None), 3);
        for errno in -256..=256 {
            if ![17, 22, 38, 95].contains(&errno) {
                assert_eq!(rename_failure(Some(errno)), 3);
            }
        }
        assert_eq!(rename_failure(Some(i32::MIN)), 3);
        assert_eq!(rename_failure(Some(i32::MAX)), 3);
    }

    #[test]
    fn symbol_absence_is_not_an_errno_or_legacy_grouped_refusal() {
        assert_eq!(SYMBOL_UNAVAILABLE, 5);
        assert_ne!(SYMBOL_UNAVAILABLE, 2); // Legacy grouped UNSUPPORTED remains readable.
        for errno in [17, 22, 38, 95] {
            assert_ne!(rename_failure(Some(errno)), SYMBOL_UNAVAILABLE);
        }
        assert_eq!(rename_failure(Some(SYMBOL_UNAVAILABLE)), 3);
    }
}
