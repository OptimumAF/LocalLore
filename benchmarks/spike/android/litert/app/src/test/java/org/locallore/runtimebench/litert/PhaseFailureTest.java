// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import java.io.IOException;
import static org.junit.Assert.*;
import org.junit.Test;

public final class PhaseFailureTest {
    @Test public void suppressedCloseUncertaintyCannotBeHiddenByBodyFailure() {
        IOException body = new IOException("synthetic_body");
        body.addSuppressed(new PhaseJournal.OwnershipUnknown());
        assertTrue(PhaseFailure.journalOwnershipUnknown(body));
        assertTrue(PhaseFailure.journalOwnershipUnknown(new IOException("wrapper", body)));
    }
    @Test public void ordinaryErrorsAndNoErrorDoNotImplyOwnershipLoss() {
        assertFalse(PhaseFailure.journalOwnershipUnknown(null));
        IOException body = new IOException("synthetic_body"); body.addSuppressed(new IOException("ordinary"));
        assertFalse(PhaseFailure.journalOwnershipUnknown(body));
    }
    @Test public void cyclesAndExcessiveGraphsFailClosedWithinTheBound() {
        IOException one = new IOException("one"), two = new IOException("two");
        one.initCause(two); two.initCause(one);
        assertTrue(PhaseFailure.journalOwnershipUnknown(one));
        IOException root = new IOException("root");
        for (int i = 0; i < 65; i++) root.addSuppressed(new IOException("synthetic"));
        assertTrue(PhaseFailure.journalOwnershipUnknown(root));
    }
}
