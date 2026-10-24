// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import org.junit.Test;

public final class PhaseExitMatcherTest {
    private static final String RUN = "0123456789abcdef0123456789abcdef";
    @Test public void exactInstanceMatchesWithoutTreatingReasonAsCause() {
        byte[] token = PhaseExitMatcher.summary(RUN, 1234);
        assertTrue(token.length <= 128);
        assertTrue(PhaseExitMatcher.matches(321, 10234, "fixed.package", token, 321, 10234, "fixed.package", token.clone()));
    }
    @Test public void pidReuseWrongRunStartUidNameAndMissingSummaryDoNotMatch() {
        byte[] token = PhaseExitMatcher.summary(RUN, 1234);
        for (byte[] other : new byte[][] {null, new byte[0], PhaseExitMatcher.summary(RUN, 1235),
                PhaseExitMatcher.summary("ffffffffffffffffffffffffffffffff", 1234)})
            assertFalse(PhaseExitMatcher.matches(321, 10234, "fixed.package", token, 321, 10234, "fixed.package", other));
        assertFalse(PhaseExitMatcher.matches(321, 10234, "fixed.package", token, 322, 10234, "fixed.package", token));
        assertFalse(PhaseExitMatcher.matches(321, 10234, "fixed.package", token, 321, 10235, "fixed.package", token));
        assertFalse(PhaseExitMatcher.matches(321, 10234, "fixed.package", token, 321, 10234, "other.package", token));
    }
    @Test public void invalidIdentityCannotConstructSummary() {
        for (String run : new String[] {null, "", "PRIVATE", RUN.toUpperCase()}) {
            try { PhaseExitMatcher.summary(run, 0); fail(); } catch (IllegalArgumentException expected) { }
        }
        try { PhaseExitMatcher.summary(RUN, -1); fail(); } catch (IllegalArgumentException expected) { }
    }
}
