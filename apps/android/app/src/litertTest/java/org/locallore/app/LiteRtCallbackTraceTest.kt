/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Test

class LiteRtCallbackTraceTest {
    private fun begin(trace: LiteRtCallbackTrace, role: LiteRtCallbackRole = LiteRtCallbackRole.DIRECTOR) =
        requireNotNull(trace.begin(role, 4096, 350, 100, 200))
    private fun call(ordinal: Int = 1, role: LiteRtCallbackRole = LiteRtCallbackRole.NARRATOR,
        context: Int = 4096, output: Int = 350, prompt: Int = 16384, schema: Int = 16384,
        count: Int = 0, saturated: Boolean = false): LiteRtCallbackCallSnapshot =
        LiteRtCallbackCallSnapshot(ordinal, role, context, output, prompt, schema,
            LiteRtCallbackCounter.entries.associateWith { count }, if (saturated) LiteRtCallbackCounter.entries.toSet() else emptySet())
    private fun refuses(block: () -> Unit) {
        try { block(); fail("Invalid callback observation accepted") } catch (_: IllegalArgumentException) { }
    }
    private fun immutable(block: () -> Unit) {
        try { block(); fail("Mutable callback snapshot") } catch (_: UnsupportedOperationException) { }
    }

    @Test fun enumsWireAndConfiguredConstantsAreClosedAndSeparate() {
        assertEquals(listOf("DIRECTOR", "NARRATOR", "AUTHOR"), LiteRtCallbackRole.entries.map { it.name })
        assertEquals(listOf("OUTPUT_CHUNKS", "OUTPUT_BYTES", "DONE", "CANCELLED", "SDK_JNI", "OTHER"), LiteRtCallbackCounter.entries.map { it.name })
        assertEquals(listOf("CANCELLED", "SDK_JNI", "OTHER"), LiteRtCallbackError.entries.map { it.name })
        assertEquals(3, LiteRtCallbackTrace.MAX_CALLS); assertEquals(1000000, LiteRtCallbackTrace.MAX_COUNT)
        assertEquals(4096, LiteRtCallbackTrace.MAX_BYTES); assertEquals(1339, LiteRtCallbackTrace.STATUS_CODE)
        assertEquals("locallore_receipt_callback_v1", LiteRtCallbackTrace.STATUS_KEY)
        assertEquals("INSTRUMENTATION_STATUS: locallore_receipt_callback_v1=", LiteRtCallbackTrace.WIRE_PREFIX)
    }
    @Test fun emptyTraceHasExactWireAndNoImplicitCalls() {
        val trace = LiteRtCallbackTrace()
        assertEquals("{\"version\":1,\"requests\":0,\"requests_saturated\":false,\"calls\":[]}", trace.snapshot().json())
        assertTrue(trace.snapshot().calls.isEmpty())
    }
    @Test fun firstThreeMetadataSlotsNeverReplaceAndOmissionsStayExplicit() {
        val trace = LiteRtCallbackTrace()
        val first = begin(trace); begin(trace); begin(trace, LiteRtCallbackRole.NARRATOR)
        val before = trace.snapshot()
        assertNull(trace.begin(LiteRtCallbackRole.DIRECTOR, 512, 1, 0, 2))
        assertEquals(4, trace.snapshot().requests); assertFalse(trace.snapshot().requestsSaturated)
        assertEquals(listOf(1, 2, 3), trace.snapshot().calls.map { it.ordinal })
        assertEquals(listOf(LiteRtCallbackRole.DIRECTOR, LiteRtCallbackRole.DIRECTOR, LiteRtCallbackRole.NARRATOR), trace.snapshot().calls.map { it.role })
        assertEquals(listOf(100, 100, 100), trace.snapshot().calls.map { it.promptBytes })
        first.done(); assertEquals(1, trace.snapshot().calls[0].counts.getValue(LiteRtCallbackCounter.DONE))
        assertEquals(0, before.calls[0].counts.getValue(LiteRtCallbackCounter.DONE))
    }
    @Test fun configuredBoundaryValuesAreAcceptedWithoutTokenUsageInference() {
        val trace = LiteRtCallbackTrace()
        assertNotNull(trace.begin(LiteRtCallbackRole.DIRECTOR, 512, 1, 0, 2))
        assertNotNull(trace.begin(LiteRtCallbackRole.NARRATOR, 4096, 350, 32766, 2))
        assertNotNull(trace.begin(LiteRtCallbackRole.DIRECTOR, 4096, 350, 0, 32768))
        assertEquals(32768, trace.snapshot().calls[2].schemaBytes)
    }
    @Test fun invalidMetadataRefusesBeforeCountersIncludingAfterOmission() {
        val trace = LiteRtCallbackTrace()
        fun invalids() {
            for (args in listOf(listOf(511, 1, 0, 2), listOf(4097, 1, 0, 2), listOf(4096, 0, 0, 2),
                listOf(4096, 351, 0, 2), listOf(4096, 350, -1, 2), listOf(4096, 350, 32769, 2),
                listOf(4096, 350, 0, 1), listOf(4096, 350, 0, 32769), listOf(4096, 350, 32767, 2),
                listOf(4096, 350, Int.MAX_VALUE, Int.MAX_VALUE))) {
                val before = trace.snapshot().json()
                refuses { trace.begin(LiteRtCallbackRole.DIRECTOR, args[0], args[1], args[2], args[3]) }
                assertEquals(before, trace.snapshot().json())
            }
        }
        invalids(); repeat(4) { trace.begin(LiteRtCallbackRole.DIRECTOR, 4096, 350, 1, 2) }; invalids()
    }
    @Test fun outputAcceptsZeroAndMaxAndInvalidInputCannotPartiallyIncrement() {
        val trace = LiteRtCallbackTrace(); val handle = begin(trace)
        handle.output(0); handle.output(16384)
        val value = trace.snapshot().calls.single()
        assertEquals(2, value.counts.getValue(LiteRtCallbackCounter.OUTPUT_CHUNKS))
        assertEquals(16384, value.counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
        for (bad in listOf(-1, 16385, Int.MIN_VALUE, Int.MAX_VALUE)) {
            val before = trace.snapshot().json(); refuses { handle.output(bad) }; assertEquals(before, trace.snapshot().json())
        }
    }
    @Test fun byteAdditionIsOverflowOnlyAndZeroAtExactCapDoesNotSaturateBytes() {
        val trace = LiteRtCallbackTrace(); val handle = begin(trace)
        repeat(61) { handle.output(16384) }; handle.output(576)
        assertEquals(1000000, trace.snapshot().calls.single().counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
        assertTrue(trace.snapshot().calls.single().saturated.isEmpty())
        handle.output(0); assertTrue(trace.snapshot().calls.single().saturated.isEmpty())
        handle.output(1)
        val value = trace.snapshot().calls.single()
        assertEquals(1000000, value.counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
        assertEquals(setOf(LiteRtCallbackCounter.OUTPUT_BYTES), value.saturated)
    }
    @Test fun duplicateLateAndMixedTerminalsRemainRepresentable() {
        val trace = LiteRtCallbackTrace(); val handle = begin(trace)
        handle.done(); handle.done(); handle.error(LiteRtCallbackError.CANCELLED); handle.output(4)
        handle.error(LiteRtCallbackError.SDK_JNI); handle.error(LiteRtCallbackError.OTHER)
        val counts = trace.snapshot().calls.single().counts
        assertEquals(2, counts.getValue(LiteRtCallbackCounter.DONE)); assertEquals(1, counts.getValue(LiteRtCallbackCounter.OUTPUT_CHUNKS))
        for (counter in listOf(LiteRtCallbackCounter.CANCELLED, LiteRtCallbackCounter.SDK_JNI, LiteRtCallbackCounter.OTHER)) assertEquals(1, counts.getValue(counter))
    }
    @Test fun actualTerminalAndRequestCountersClampOnlyAfterStrictOverflow() {
        val trace = LiteRtCallbackTrace(); val handle = begin(trace)
        repeat(LiteRtCallbackTrace.MAX_COUNT) { handle.done() }
        assertTrue(trace.snapshot().calls.single().saturated.isEmpty())
        handle.done(); assertEquals(setOf(LiteRtCallbackCounter.DONE), trace.snapshot().calls.single().saturated)
        repeat(LiteRtCallbackTrace.MAX_COUNT - 1) { trace.begin(LiteRtCallbackRole.DIRECTOR, 512, 1, 0, 2) }
        assertEquals(1000000, trace.snapshot().requests); assertFalse(trace.snapshot().requestsSaturated)
        assertNull(trace.begin(LiteRtCallbackRole.NARRATOR, 512, 1, 0, 2))
        assertTrue(trace.snapshot().requestsSaturated); assertEquals(1000000, trace.snapshot().requests)
        assertEquals(3, trace.snapshot().calls.size)
    }
    @Test fun handleCannotAttributeOutputToAnotherTraceOrUnretainedSlot() {
        val first = LiteRtCallbackTrace(); val second = LiteRtCallbackTrace()
        val handle = begin(first); begin(second)
        val orphan = LiteRtCallbackCall(first)
        orphan.done(); orphan.output(9); second.output(handle, 10)
        assertTrue(first.snapshot().calls.single().counts.values.all { it == 0 })
        assertTrue(second.snapshot().calls.single().counts.values.all { it == 0 })
        handle.output(1); assertEquals(1, first.snapshot().calls.single().counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
    }
    @Test fun snapshotCollectionsAndNestedEntriesAreDefensiveAndImmutable() {
        val counts = LiteRtCallbackCounter.entries.associateWith { 1000000 }.toMutableMap()
        val flags = LiteRtCallbackCounter.entries.toMutableSet()
        val record = LiteRtCallbackCallSnapshot(1, LiteRtCallbackRole.DIRECTOR, 4096, 350, 1, 2, counts, flags)
        val list = mutableListOf(record); val value = LiteRtCallbackSnapshot(1, false, list); val wire = value.json()
        counts.clear(); flags.clear(); list.clear(); assertEquals(wire, value.json())
        @Suppress("UNCHECKED_CAST") val mutableCounts = record.counts as MutableMap<LiteRtCallbackCounter, Int>
        @Suppress("UNCHECKED_CAST") val mutableFlags = record.saturated as MutableSet<LiteRtCallbackCounter>
        @Suppress("UNCHECKED_CAST") val mutableList = value.calls as MutableList<LiteRtCallbackCallSnapshot>
        immutable { mutableCounts.clear() }; immutable { mutableCounts.entries.first().setValue(0) }
        immutable { mutableFlags.clear() }; immutable { mutableList.clear() }
    }
    @Test fun manualSnapshotsRefuseWrongKeysCountsOrdinalsFlagsAndLengths() {
        refuses { call(count = -1) }; refuses { call(count = 1000001) }; refuses { call(count = 1, saturated = true) }
        refuses { call(ordinal = 0) }; refuses { call(ordinal = 4) }; refuses { call(prompt = 32768, schema = 2) }
        refuses { LiteRtCallbackCallSnapshot(1, LiteRtCallbackRole.DIRECTOR, 4096, 350, 0, 2, emptyMap(), emptySet()) }
        refuses { LiteRtCallbackSnapshot(-1, false, emptyList()) }; refuses { LiteRtCallbackSnapshot(1000001, false, emptyList()) }
        refuses { LiteRtCallbackSnapshot(1, true, listOf(call())) }; refuses { LiteRtCallbackSnapshot(0, false, listOf(call())) }
        refuses { LiteRtCallbackSnapshot(2, false, listOf(call())) }; refuses { LiteRtCallbackSnapshot(1, false, listOf(call(ordinal = 2))) }
        refuses { LiteRtCallbackSnapshot(4, false, List(4) { call() }) }
        assertNotNull(LiteRtCallbackSnapshot(1000000, false, List(3) { call(it + 1) }).json())
    }
    @Test fun concurrentHandlesAndSnapshotsNeverMixRequestsOrExposePartialOutputAccounting() {
        val trace = LiteRtCallbackTrace(); val handles = List(3) { begin(trace, if (it == 2) LiteRtCallbackRole.NARRATOR else LiteRtCallbackRole.DIRECTOR) }
        val pool = Executors.newFixedThreadPool(4); val start = CountDownLatch(1)
        try {
            val jobs = handles.map { handle -> pool.submit { start.await(); repeat(5000) { handle.output(2); handle.done() } } }
            val observer = pool.submit {
                start.await(); repeat(100) {
                    val value = trace.snapshot()
                    assertEquals(3, value.requests)
                    for (call in value.calls) assertEquals(call.counts.getValue(LiteRtCallbackCounter.OUTPUT_CHUNKS) * 2,
                        call.counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES)) // One actual output mutation holds the parent monitor.
                    assertTrue(value.json().length < 4096)
                }
            }
            start.countDown(); jobs.forEach { it.get(10, TimeUnit.SECONDS) }; observer.get(10, TimeUnit.SECONDS)
            for (call in trace.snapshot().calls) { assertEquals(5000, call.counts.getValue(LiteRtCallbackCounter.DONE)); assertEquals(10000, call.counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES)) }
        } finally { pool.shutdownNow(); assertTrue(pool.awaitTermination(10, TimeUnit.SECONDS)) }
    }
    @Test fun denseCanonicalWireMatchesIndependentParserFixture() {
        val value = LiteRtCallbackSnapshot(1000000, true, List(3) { call(it + 1, count = 1000000, saturated = true) })
        val wire = value.json()
        assertTrue(wire.all { it.code in 32..126 }); assertEquals(wire, value.json())
        assertEquals(1055, wire.toByteArray(Charsets.US_ASCII).size)
        assertEquals(1109, (LiteRtCallbackTrace.WIRE_PREFIX + wire).toByteArray(Charsets.US_ASCII).size)
        assertTrue((LiteRtCallbackTrace.WIRE_PREFIX + wire).toByteArray(Charsets.UTF_8).size <= LiteRtCallbackTrace.MAX_BYTES)
        assertEquals("754c4eef06b6ea5fa2bd395ec449be37779c875799f8a71cce5115e368d754b3",
            MessageDigest.getInstance("SHA-256").digest(wire.toByteArray(Charsets.US_ASCII)).joinToString("") { "%02x".format(it) })
    }
    @Test fun signaturesCannotInspectContentThrowableCallbackClockOrFilesystem() {
        assertTrue(LiteRtCallbackTrace::class.java.declaredConstructors.all { it.parameterCount == 0 })
        for (type in listOf(LiteRtCallbackTrace::class.java, LiteRtCallbackCall::class.java)) {
            for (method in type.declaredMethods) assertFalse(method.parameterTypes.any {
                it == String::class.java || Throwable::class.java.isAssignableFrom(it) || it.name.startsWith("java.io.") || it.name.startsWith("kotlin.jvm.functions.")
            })
            assertTrue(type.declaredFields.none { it.type == java.time.Clock::class.java })
        }
        val wire = LiteRtCallbackSnapshot(1, false, listOf(call())).json()
        for (privateKey in listOf("prompt\":", "schema\":", "message", "cause", "stack", "clock", "timestamp")) assertFalse(wire.contains(privateKey))
    }
}
