// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Instance correlation only. An OS reason is not a diagnosis of its cause. */
final class PhaseExitMatcher {
    private PhaseExitMatcher() {}
    static byte[] summary(String session, long processStartElapsedMs) {
        if (session == null || !session.matches("[a-f0-9]{32}") || processStartElapsedMs < 0)
            throw new IllegalArgumentException("invalid_identity");
        return ("LLP1:" + session + ":" + processStartElapsedMs).getBytes(StandardCharsets.US_ASCII);
    }
    static boolean matches(int pid, int uid, String processName, byte[] expectedSummary,
            int actualPid, int actualUid, String actualName, byte[] actualSummary) {
        return pid > 0 && uid > 0 && processName != null && expectedSummary != null
            && expectedSummary.length > 0 && expectedSummary.length <= 128
            && pid == actualPid && uid == actualUid && processName.equals(actualName)
            && Arrays.equals(expectedSummary, actualSummary);
    }
}
