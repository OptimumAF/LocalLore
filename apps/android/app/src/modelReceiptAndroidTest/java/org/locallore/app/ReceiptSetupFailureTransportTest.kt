/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Bundle
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertSame
import org.junit.Assert.fail
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

/** Separately selected negative transport oracle; an actual runner failure is required. */
@RunWith(AndroidJUnit4::class)
class ReceiptSetupFailureTransportTest {
    @Test fun preservesOriginalFailureAfterDedicatedStatus() {
        assumeTrue("Dedicated class selection is required",
            InstrumentationRegistry.getArguments().getString("class") ==
                "org.locallore.app.ReceiptSetupFailureTransportTest")
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.ACCEPT).apply {
            record(ReceiptSetupFailureEvent.CHECK_START)
            record(ReceiptSetupFailureEvent.CHECK_MISSING)
        }
        val original = AssertionError("receipt_setup_failure_transport_v1")
        try {
            ReceiptSetupFailureReporter.run<Unit>(
                claim = { ReceiptSetupFixture.claimFailureEmission() },
                snapshot = {
                    trace.snapshot(LocalModelSetupPhase.READY, LocalModelSetupPhase.MISSING,
                        ReceiptSetupSourceProgress())
                },
                send = { code, key, json ->
                    InstrumentationRegistry.getInstrumentation().sendStatus(code,
                        Bundle().apply { putString(key, json) })
                },
                block = { throw original },
            )
        } catch (caught: Throwable) {
            assertSame(original, caught)
            throw caught
        }
        fail("Negative transport reporter unexpectedly returned")
    }
}
