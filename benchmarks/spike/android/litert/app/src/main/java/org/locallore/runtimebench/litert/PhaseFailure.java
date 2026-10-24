// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import java.util.ArrayDeque;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** A try-with-resources body failure must not hide uncertain journal closure. */
final class PhaseFailure {
    private PhaseFailure() {}
    static boolean journalOwnershipUnknown(Throwable failure) {
        if (failure == null) return false;
        ArrayDeque<Throwable> pending = new ArrayDeque<>(); pending.add(failure);
        Set<Throwable> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        while (!pending.isEmpty()) {
            Throwable current = pending.removeFirst();
            if (current instanceof PhaseJournal.OwnershipUnknown) return true;
            if (!seen.add(current) || seen.size() > 64) return true;
            Throwable cause = current.getCause();
            if (cause != null) pending.addLast(cause);
            for (Throwable suppressed : current.getSuppressed()) {
                if (pending.size() >= 64) return true;
                pending.addLast(suppressed);
            }
        }
        return false;
    }
}
