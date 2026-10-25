/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Test

/** Pure bounded diagnostic counters; no worker, SDK, provider or Android component. */
class LiteRtWorkerTraceTest {
    private val names = listOf(
        "ADMISSION_ENTERED", "ADMISSION_RETURNED",
        "ENGINE_CREATE_ENTERED", "ENGINE_CREATE_RETURNED",
        "INITIALIZE_ADMISSION_ENTERED", "INITIALIZE_ADMISSION_RETURNED",
        "INITIALIZE_ENTERED", "INITIALIZE_RETURNED",
        "ROLE_ADMISSION_ENTERED", "ROLE_ADMISSION_RETURNED",
        "CONVERSATION_CREATE_ENTERED", "CONVERSATION_CREATE_RETURNED",
        "SEND_ADMISSION_ENTERED", "SEND_ADMISSION_RETURNED",
        "SEND_ENTERED", "SEND_RETURNED", "MESSAGE_ENTERED", "MESSAGE_RETURNED",
        "DONE_ENTERED", "DONE_RETURNED", "ERROR_ENTERED", "ERROR_RETURNED", "DRAIN_SETTLED",
        "CANCEL_ENTERED", "CANCEL_RETURNED", "CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN",
        "ENGINE_CLOSE_ENTERED", "ENGINE_CLOSE_KNOWN", "UNCERTAIN",
    )
    private fun counts(value: Int = 0) = LiteRtWorkerEvent.entries.associateWith { value }
    private fun expectedJson(values: List<Int>, saturated: List<String> = emptyList()) =
        "{\"version\":1,\"counts\":{" + names.zip(values).joinToString(",") { (name, count) ->
            "\"$name\":$count"
        } + "},\"saturated\":[" + saturated.joinToString(",") { "\"$it\"" } + "]}"

    private fun refuses(action: () -> Unit) {
        try { action(); fail("Expected invalid snapshot refusal") }
        catch (_: IllegalArgumentException) { }
    }

    private fun immutable(action: () -> Unit) {
        try { action(); fail("Snapshot collection must be immutable") }
        catch (_: UnsupportedOperationException) { }
    }

    @Test fun vocabularyOrderAndStatusEnvelopeAreExactlyClosed() {
        assertEquals(30, names.size)
        assertEquals(names, LiteRtWorkerEvent.entries.map { it.name })
        assertEquals("locallore_receipt_worker_v1", LiteRtWorkerTrace.STATUS_KEY)
        assertEquals(1337, LiteRtWorkerTrace.STATUS_CODE)
        assertEquals("INSTRUMENTATION_STATUS: locallore_receipt_worker_v1=", LiteRtWorkerTrace.WIRE_PREFIX)
        assertEquals(4096, LiteRtWorkerTrace.MAX_BYTES)
        assertEquals(1_000_000, LiteRtWorkerTrace.MAX_COUNT)
    }

    @Test fun emptySnapshotContainsEveryZeroCounterInExactWireOrder() {
        val value = LiteRtWorkerTrace().snapshot()
        assertEquals(counts(), value.counts)
        assertTrue(value.saturated.isEmpty())
        assertEquals(expectedJson(List(30) { 0 }), value.json())
        assertEquals(value.json(), value.json())
    }

    @Test fun eachEventIncrementsOnlyItsCounterWithoutInventedLifecycleRules() {
        val trace = LiteRtWorkerTrace()
        for ((index, event) in LiteRtWorkerEvent.entries.withIndex()) {
            repeat(index + 1) { trace.record(event) }
        }
        val value = trace.snapshot()
        assertEquals(LiteRtWorkerEvent.entries.associateWith { it.ordinal + 1 }, value.counts)
        assertTrue(value.saturated.isEmpty())
        assertEquals(expectedJson((1..30).toList()), value.json())
        val observations = LiteRtWorkerTrace()
        observations.record(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
        observations.record(LiteRtWorkerEvent.MESSAGE_RETURNED)
        observations.record(LiteRtWorkerEvent.UNCERTAIN)
        assertEquals(1, observations.snapshot().counts[LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN])
        assertEquals(0, observations.snapshot().counts[LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED])
    }

    @Test fun snapshotsRemainIndependentOfFutureRecords() {
        val trace = LiteRtWorkerTrace()
        trace.record(LiteRtWorkerEvent.SEND_ENTERED)
        val before = trace.snapshot()
        val beforeJson = before.json()
        trace.record(LiteRtWorkerEvent.SEND_ENTERED)
        trace.record(LiteRtWorkerEvent.SEND_RETURNED)
        assertEquals(beforeJson, before.json())
        assertEquals(1, before.counts[LiteRtWorkerEvent.SEND_ENTERED])
        assertEquals(0, before.counts[LiteRtWorkerEvent.SEND_RETURNED])
        assertEquals(2, trace.snapshot().counts[LiteRtWorkerEvent.SEND_ENTERED])
    }

    @Test fun snapshotMapsSetsAndEntriesRejectCallerMutation() {
        val value = LiteRtWorkerSnapshot(counts(LiteRtWorkerTrace.MAX_COUNT), setOf(LiteRtWorkerEvent.UNCERTAIN))
        val before = value.json()
        @Suppress("UNCHECKED_CAST")
        val map = value.counts as MutableMap<LiteRtWorkerEvent, Int>
        @Suppress("UNCHECKED_CAST")
        val set = value.saturated as MutableSet<LiteRtWorkerEvent>
        immutable { map[LiteRtWorkerEvent.UNCERTAIN] = 0 }
        immutable { map.clear() }
        immutable { map.entries.first().setValue(0) }
        immutable { set.clear() }
        immutable { set.add(LiteRtWorkerEvent.SEND_ENTERED) }
        assertEquals(before, value.json())
    }

    @Test fun constructorCopiesCallerOwnedCollectionsBeforeEncoding() {
        val originalCounts = counts(LiteRtWorkerTrace.MAX_COUNT).toMutableMap()
        val originalSaturated = mutableSetOf(LiteRtWorkerEvent.MESSAGE_ENTERED, LiteRtWorkerEvent.UNCERTAIN)
        val value = LiteRtWorkerSnapshot(originalCounts, originalSaturated)
        val before = value.json()
        originalCounts.clear()
        originalSaturated.clear()
        assertEquals(counts(LiteRtWorkerTrace.MAX_COUNT), value.counts)
        assertEquals(setOf(LiteRtWorkerEvent.MESSAGE_ENTERED, LiteRtWorkerEvent.UNCERTAIN), value.saturated)
        assertEquals(before, value.json())
    }

    @Test fun reachingCapDoesNotClaimOverflowUntilNextObservation() {
        val trace = LiteRtWorkerTrace()
        val event = LiteRtWorkerEvent.MESSAGE_ENTERED
        repeat(LiteRtWorkerTrace.MAX_COUNT) { trace.record(event) }
        val atLimit = trace.snapshot()
        assertEquals(LiteRtWorkerTrace.MAX_COUNT, atLimit.counts[event])
        assertTrue(atLimit.saturated.isEmpty())
        trace.record(event)
        repeat(17) { trace.record(event) }
        val overflowed = trace.snapshot()
        assertEquals(LiteRtWorkerTrace.MAX_COUNT, overflowed.counts[event])
        assertEquals(setOf(event), overflowed.saturated)
        assertTrue(atLimit.saturated.isEmpty())
        for (other in LiteRtWorkerEvent.entries.filter { it != event }) assertEquals(0, overflowed.counts[other])
    }

    @Test fun invalidCounterSetsAndUnjustifiedSaturationCannotBeSerialized() {
        refuses { LiteRtWorkerSnapshot(emptyMap(), emptySet()) }
        refuses { LiteRtWorkerSnapshot(counts().minus(LiteRtWorkerEvent.UNCERTAIN), emptySet()) }
        for (bad in listOf(-1, Int.MIN_VALUE, LiteRtWorkerTrace.MAX_COUNT + 1, Int.MAX_VALUE)) {
            refuses { LiteRtWorkerSnapshot(counts() + (LiteRtWorkerEvent.SEND_ENTERED to bad), emptySet()) }
        }
        refuses { LiteRtWorkerSnapshot(counts(), setOf(LiteRtWorkerEvent.SEND_ENTERED)) }
        val exactlyAtCap = LiteRtWorkerSnapshot(counts(LiteRtWorkerTrace.MAX_COUNT), emptySet())
        assertTrue(exactlyAtCap.saturated.isEmpty())
    }

    @Test fun maximalWireIsExactAsciiAndWithinPrefixInclusiveByteBound() {
        val reversed = LiteRtWorkerEvent.entries.reversed()
        val value = LiteRtWorkerSnapshot(reversed.associateWith { LiteRtWorkerTrace.MAX_COUNT }, reversed.toSet())
        val json = value.json()
        assertEquals(expectedJson(List(30) { 1_000_000 }, names), json)
        val wire = (LiteRtWorkerTrace.WIRE_PREFIX + json).toByteArray(Charsets.UTF_8)
        assertTrue(wire.size <= 4096)
        assertTrue(wire.all { it.toInt() in 32..126 })
        assertEquals(wire.size, LiteRtWorkerTrace.WIRE_PREFIX.length + json.length)
        assertEquals(json, value.json())
    }

    @Test fun encodingContainsOnlyClosedTokensAndOffersNoRawInputApi() {
        val json = LiteRtWorkerSnapshot(counts(1), emptySet()).json()
        val tokens = Regex("\"([^\"]*)\"").findAll(json).map { it.groupValues[1] }.toList()
        assertEquals(listOf("version", "counts") + names + "saturated", tokens)
        assertFalse(json.contains("org.locallore"))
        assertFalse(json.contains("Throwable"))
        assertEquals(listOf(LiteRtWorkerEvent::class.java), LiteRtWorkerTrace::class.java
            .getDeclaredMethod("record", LiteRtWorkerEvent::class.java).parameterTypes.toList())
        assertEquals(0, LiteRtWorkerTrace::class.java.getDeclaredMethod("snapshot").parameterCount)
        assertEquals(0, LiteRtWorkerSnapshot::class.java.getDeclaredMethod("json").parameterCount)
        for (type in listOf(LiteRtWorkerTrace::class.java, LiteRtWorkerSnapshot::class.java)) {
            assertFalse(type.declaredConstructors.any { constructor -> constructor.parameterTypes.any {
                it == String::class.java || Throwable::class.java.isAssignableFrom(it) ||
                    it.name.startsWith("java.io.") || it.name.startsWith("kotlin.jvm.functions.")
            } })
        }
    }

    @Test fun concurrentRecordAndSnapshotKeepExactTotalsAndImmutableBoundedValues() {
        val trace = LiteRtWorkerTrace()
        val executor = Executors.newFixedThreadPool(6)
        val gate = CountDownLatch(1)
        try {
            val writers = (0 until 4).map { index -> executor.submit {
                assertTrue(gate.await(5, TimeUnit.SECONDS))
                repeat(2000) { trace.record(LiteRtWorkerEvent.entries[index]) }
            } }
            val readers = (0 until 2).map { executor.submit {
                assertTrue(gate.await(5, TimeUnit.SECONDS))
                var previous = counts()
                repeat(250) {
                    val value = trace.snapshot()
                    val encoded = value.json()
                    assertEquals(30, value.counts.size)
                    assertTrue(value.saturated.isEmpty())
                    assertTrue(value.counts.all { (event, count) -> count >= previous.getValue(event) })
                    assertTrue((LiteRtWorkerTrace.WIRE_PREFIX + encoded).toByteArray(Charsets.UTF_8).size <= 4096)
                    assertEquals(encoded, value.json())
                    previous = value.counts
                }
            } }
            gate.countDown()
            (writers + readers).forEach { it.get(10, TimeUnit.SECONDS) }
            val value = trace.snapshot()
            assertEquals(8000, value.counts.values.sum())
            for (event in LiteRtWorkerEvent.entries) assertEquals(if (event.ordinal < 4) 2000 else 0, value.counts[event])
            assertTrue(value.saturated.isEmpty())
        } finally {
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS))
        }
    }
}
