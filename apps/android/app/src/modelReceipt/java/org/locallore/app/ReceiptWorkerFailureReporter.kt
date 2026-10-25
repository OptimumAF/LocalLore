/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.atomic.AtomicBoolean

/** Fixture-only, one emission per reporter/process. Never changes the operation's outcome. */
internal class ReceiptWorkerFailureReporter {
    private val emitted = AtomicBoolean()

    suspend fun <T> run(
        trace: LiteRtWorkerTrace,
        send: (Int, String, String) -> Unit,
        block: suspend () -> T,
    ): T {
        try {
            return block()
        } catch (original: Throwable) {
            try {
                if (emitted.compareAndSet(false, true)) {
                    send(LiteRtWorkerTrace.STATUS_CODE, LiteRtWorkerTrace.STATUS_KEY, trace.snapshot().json())
                }
            } catch (_: Throwable) { /* A failed observation cannot replace the original failure. */ }
            throw original
        }
    }
}
