/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class ReceiptWorkerFailureReporterTest {
    @Test fun successDoesNotEmitOrConsumeFailureSlot() = runBlocking {
        val reporter = ReceiptWorkerFailureReporter()
        val trace = LiteRtWorkerTrace()
        var sends = 0
        val send: (Int, String, String) -> Unit = { code, key, json ->
            assertEquals(1337, code); assertEquals("locallore_receipt_worker_v1", key)
            assertEquals(trace.snapshot().json(), json); sends++
        }
        assertEquals(42, reporter.run(trace, send) { 42 })
        assertEquals(0, sends)
        val original = AssertionError("private story/path/native cause")
        try { reporter.run(trace, send) { throw original }; fail() }
        catch (failure: Throwable) { assertSame(original, failure) }
        assertEquals(1, sends)
    }

    @Test fun failedSendPreservesOriginalAndStillConsumesSingleSlot() = runBlocking {
        val reporter = ReceiptWorkerFailureReporter()
        val trace = LiteRtWorkerTrace()
        var sends = 0
        var sentJson: String? = null
        val original = AssertionError("private exception must not be serialized")
        repeat(2) {
            try {
                reporter.run(trace, send = { _, _, json ->
                    sends++; sentJson = json; throw AssertionError("reporter failure")
                }) { throw original }
                fail()
            } catch (failure: Throwable) { assertSame(original, failure) }
        }
        assertEquals(1, sends)
        assertNotNull(sentJson)
        assertFalse(requireNotNull(sentJson).contains("private"))
    }
}
