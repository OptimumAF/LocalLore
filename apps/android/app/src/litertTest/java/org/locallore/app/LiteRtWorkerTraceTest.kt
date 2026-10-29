/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.security.MessageDigest
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
    private fun snapshot(
        values: Map<LiteRtWorkerEvent, Int> = counts(),
        saturated: Set<LiteRtWorkerEvent> = emptySet(),
        last: Map<LiteRtWorkerEvent, Int?> = values.mapValues { if (it.value == 0) null else 0 },
        ms: Int = 0,
        timeSaturated: Boolean = false,
        total: Int = 0,
        creationsSaturated: Boolean = false,
        creations: List<LiteRtTraceCreation> = emptyList(),
    ) = LiteRtWorkerSnapshot(values, saturated, last, ms, timeSaturated, total, creationsSaturated, creations)

    private fun expectedJson(
        values: List<Int>,
        saturated: List<String> = emptyList(),
        last: List<Int?> = values.map { if (it == 0) null else 0 },
        ms: Int = 0,
        timeSaturated: Boolean = false,
        total: Int = 0,
        creationsSaturated: Boolean = false,
        creationsJson: String = "",
    ) = "{\"version\":2,\"counts\":{" + names.zip(values).joinToString(",") { (name, count) ->
            "\"$name\":$count"
        } + "},\"saturated\":[" + saturated.joinToString(",") { "\"$it\"" } +
        "],\"last_ms\":{" + names.zip(last).joinToString(",") { (name, time) -> "\"$name\":$time" } +
        "},\"snapshot_ms\":$ms,\"time_saturated\":$timeSaturated,\"creations_total\":$total," +
        "\"creations_saturated\":$creationsSaturated,\"creations\":[$creationsJson]}"

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
        assertEquals("locallore_receipt_worker_v2", LiteRtWorkerTrace.STATUS_KEY)
        assertEquals(1337, LiteRtWorkerTrace.STATUS_CODE)
        assertEquals("INSTRUMENTATION_STATUS: locallore_receipt_worker_v2=", LiteRtWorkerTrace.WIRE_PREFIX)
        assertEquals(4096, LiteRtWorkerTrace.MAX_BYTES)
        assertEquals(1_000_000, LiteRtWorkerTrace.MAX_COUNT)
        assertEquals(180_000, LiteRtWorkerTrace.MAX_MS)
        assertEquals(3, LiteRtWorkerTrace.MAX_CREATIONS)
        assertEquals(listOf("DIRECTOR", "NARRATOR", "AUTHOR"), LiteRtTraceRole.entries.map { it.name })
        assertEquals(listOf("NONE", "CANCELLED", "OTHER"), LiteRtTraceFailure.entries.map { it.name })
    }

    @Test fun emptySnapshotContainsEveryZeroCounterInExactWireOrder() {
        val value = LiteRtWorkerTrace().snapshot()
        assertEquals(counts(), value.counts)
        assertTrue(value.saturated.isEmpty())
        assertEquals(LiteRtWorkerEvent.entries.associateWith { null }, value.lastMs)
        assertTrue(value.snapshotMs in 0..180_000)
        assertEquals(0, value.creationsTotal)
        assertTrue(value.creations.isEmpty())
        assertEquals(expectedJson(List(30) { 0 }, ms = value.snapshotMs, timeSaturated = value.timeSaturated), value.json())
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
        assertEquals(expectedJson((1..30).toList(), last = LiteRtWorkerEvent.entries.map { value.lastMs[it] },
            ms = value.snapshotMs, timeSaturated = value.timeSaturated), value.json())
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
        val value = snapshot(counts(LiteRtWorkerTrace.MAX_COUNT), setOf(LiteRtWorkerEvent.UNCERTAIN))
        val before = value.json()
        @Suppress("UNCHECKED_CAST")
        val map = value.counts as MutableMap<LiteRtWorkerEvent, Int>
        @Suppress("UNCHECKED_CAST")
        val set = value.saturated as MutableSet<LiteRtWorkerEvent>
        @Suppress("UNCHECKED_CAST")
        val last = value.lastMs as MutableMap<LiteRtWorkerEvent, Int?>
        immutable { map[LiteRtWorkerEvent.UNCERTAIN] = 0 }
        immutable { map.clear() }
        immutable { map.entries.first().setValue(0) }
        immutable { set.clear() }
        immutable { set.add(LiteRtWorkerEvent.SEND_ENTERED) }
        immutable { last.clear() }
        immutable { last.entries.first().setValue(1) }
        assertEquals(before, value.json())
    }

    @Test fun constructorCopiesCallerOwnedCollectionsBeforeEncoding() {
        val originalCounts = counts(LiteRtWorkerTrace.MAX_COUNT).toMutableMap()
        val originalSaturated = mutableSetOf(LiteRtWorkerEvent.MESSAGE_ENTERED, LiteRtWorkerEvent.UNCERTAIN)
        val originalLast = LiteRtWorkerEvent.entries.associateWith<LiteRtWorkerEvent, Int?> { 0 }.toMutableMap()
        val originalCreations = mutableListOf(LiteRtTraceCreation(1, LiteRtTraceRole.DIRECTOR, 0, null, null, LiteRtTraceFailure.NONE))
        val value = snapshot(originalCounts, originalSaturated, originalLast, total = 1, creations = originalCreations)
        val before = value.json()
        originalCounts.clear()
        originalSaturated.clear()
        originalLast.clear()
        originalCreations.clear()
        assertEquals(counts(LiteRtWorkerTrace.MAX_COUNT), value.counts)
        assertEquals(setOf(LiteRtWorkerEvent.MESSAGE_ENTERED, LiteRtWorkerEvent.UNCERTAIN), value.saturated)
        assertEquals(30, value.lastMs.size)
        assertEquals(1, value.creations.size)
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
        refuses { snapshot(emptyMap(), emptySet()) }
        refuses { snapshot(counts().minus(LiteRtWorkerEvent.UNCERTAIN), emptySet()) }
        for (bad in listOf(-1, Int.MIN_VALUE, LiteRtWorkerTrace.MAX_COUNT + 1, Int.MAX_VALUE)) {
            refuses { snapshot(counts() + (LiteRtWorkerEvent.SEND_ENTERED to bad), emptySet()) }
        }
        refuses { snapshot(counts(), setOf(LiteRtWorkerEvent.SEND_ENTERED)) }
        val exactlyAtCap = snapshot(counts(LiteRtWorkerTrace.MAX_COUNT), emptySet())
        assertTrue(exactlyAtCap.saturated.isEmpty())
    }

    @Test fun maximalWireIsExactAsciiAndWithinPrefixInclusiveByteBound() {
        val reversed = LiteRtWorkerEvent.entries.reversed()
        val creations = (1..3).map {
            LiteRtTraceCreation(it, LiteRtTraceRole.NARRATOR, 180_000, null, 180_000, LiteRtTraceFailure.CANCELLED)
        }
        val value = snapshot(reversed.associateWith { LiteRtWorkerTrace.MAX_COUNT }, reversed.toSet(),
            reversed.associateWith { 180_000 }, 180_000, true, 1_000_000, true, creations)
        val json = value.json()
        val creationJson = (1..3).joinToString(",") {
            "{\"ordinal\":$it,\"role\":\"NARRATOR\",\"entered_ms\":180000,\"returned_ms\":null,\"failed_ms\":180000,\"failure\":\"CANCELLED\"}"
        }
        assertEquals(expectedJson(List(30) { 1_000_000 }, names, List(30) { 180_000 },
            180_000, true, 1_000_000, true, creationJson), json)
        val wire = (LiteRtWorkerTrace.WIRE_PREFIX + json).toByteArray(Charsets.UTF_8)
        assertTrue(wire.size <= 4096)
        assertEquals(2960, wire.size)
        assertEquals(2908, json.toByteArray(Charsets.UTF_8).size)
        assertEquals("bd2f1b19bc833f90227b87531da9f35037a948643ef3072c151b51d3baef2b31",
            MessageDigest.getInstance("SHA-256").digest(json.toByteArray(Charsets.UTF_8))
                .joinToString("") { "%02x".format(it.toInt() and 255) })
        assertTrue(wire.all { it.toInt() in 32..126 })
        assertEquals(wire.size, LiteRtWorkerTrace.WIRE_PREFIX.length + json.length)
        assertEquals(json, value.json())
    }

    @Test fun encodingContainsOnlyClosedTokensAndOffersNoRawInputApi() {
        val json = snapshot(counts(1), emptySet()).json()
        val tokens = Regex("\"([^\"]*)\"").findAll(json).map { it.groupValues[1] }.toList()
        assertEquals(listOf("version", "counts") + names + listOf("saturated", "last_ms") + names +
            listOf("snapshot_ms", "time_saturated", "creations_total", "creations_saturated", "creations"), tokens)
        assertFalse(json.contains("org.locallore"))
        assertFalse(json.contains("Throwable"))
        assertEquals(listOf(LiteRtWorkerEvent::class.java), LiteRtWorkerTrace::class.java
            .getDeclaredMethod("record", LiteRtWorkerEvent::class.java).parameterTypes.toList())
        assertEquals(0, LiteRtWorkerTrace::class.java.getDeclaredMethod("snapshot").parameterCount)
        assertEquals(0, LiteRtWorkerSnapshot::class.java.getDeclaredMethod("json").parameterCount)
        assertEquals(listOf(LiteRtTraceRole::class.java), LiteRtWorkerTrace::class.java
            .getDeclaredMethod("creationEntered", LiteRtTraceRole::class.java).parameterTypes.toList())
        assertEquals(listOf(Int::class.javaPrimitiveType, LiteRtTraceFailure::class.java), LiteRtWorkerTrace::class.java
            .getDeclaredMethod("creationFailed", Int::class.javaPrimitiveType, LiteRtTraceFailure::class.java).parameterTypes.toList())
        for (type in listOf(LiteRtWorkerTrace::class.java, LiteRtWorkerSnapshot::class.java, LiteRtTraceCreation::class.java)) {
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

    @Test fun elapsedMathClampsWithoutOverflowAndFlagsOnlyBeyondTheExactCap() {
        val cap = 180_000L * 1_000_000
        val cases = listOf(
            Triple(Long.MIN_VALUE, 0, false), Triple(-1L, 0, false), Triple(0L, 0, false),
            Triple(999_999L, 0, false), Triple(1_000_000L, 1, false),
            Triple(cap - 1, 179_999, false), Triple(cap, 180_000, false),
            Triple(cap + 1, 180_000, true), Triple(Long.MAX_VALUE, 180_000, true),
        )
        for ((nanos, ms, saturated) in cases) assertEquals(LiteRtTraceTime(ms, saturated), liteRtTraceTime(nanos))
    }

    @Test fun eventLastTimesAreObservedMonotonicValuesAndNotInventedCallDurations() {
        val trace = LiteRtWorkerTrace()
        trace.record(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
        val before = trace.snapshot()
        trace.record(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
        trace.record(LiteRtWorkerEvent.MESSAGE_RETURNED)
        val after = trace.snapshot()
        val first = requireNotNull(before.lastMs[LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN])
        val latest = requireNotNull(after.lastMs[LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN])
        assertTrue(first in 0..before.snapshotMs)
        assertTrue(latest in first..after.snapshotMs)
        assertTrue(after.snapshotMs >= before.snapshotMs)
        assertEquals(0, after.counts[LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED])
        assertNull(after.lastMs[LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED])
        assertEquals(first, before.lastMs[LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN])
    }

    @Test fun invalidUnissuedAndZeroCreationTokensAreNonthrowingAndFirstTerminalWins() {
        val trace = LiteRtWorkerTrace()
        for (token in listOf(Int.MIN_VALUE, -1, 0, 1, 3, 4, Int.MAX_VALUE)) {
            trace.creationReturned(token)
            trace.creationFailed(token, LiteRtTraceFailure.OTHER)
        }
        assertTrue(trace.snapshot().creations.isEmpty())
        assertEquals(0, trace.snapshot().creationsTotal)
        val token = trace.creationEntered(LiteRtTraceRole.DIRECTOR)
        assertEquals(1, token)
        trace.creationFailed(token, LiteRtTraceFailure.NONE)
        assertNull(trace.snapshot().creations.single().failedMs)
        trace.creationReturned(2) // No second entry owns this ordinal yet.
        trace.creationFailed(3, LiteRtTraceFailure.CANCELLED)
        trace.creationReturned(token)
        val completed = trace.snapshot().creations.single()
        assertNotNull(completed.returnedMs)
        assertNull(completed.failedMs)
        assertEquals(LiteRtTraceFailure.NONE, completed.failure)
        trace.creationFailed(token, LiteRtTraceFailure.CANCELLED)
        trace.creationReturned(token)
        assertEquals(completed, trace.snapshot().creations.single())

        val failed = trace.creationEntered(LiteRtTraceRole.NARRATOR)
        trace.creationFailed(failed, LiteRtTraceFailure.CANCELLED)
        val cancelled = trace.snapshot().creations[1]
        trace.creationReturned(failed)
        trace.creationFailed(failed, LiteRtTraceFailure.OTHER)
        assertEquals(cancelled, trace.snapshot().creations[1])
        assertNull(cancelled.returnedMs)
        assertNotNull(cancelled.failedMs)
        assertEquals(LiteRtTraceFailure.CANCELLED, cancelled.failure)
    }

    @Test fun threeRetainedCreationsAreIndependentFromEventCountsAndExplainLaterTruncation() {
        val trace = LiteRtWorkerTrace()
        assertEquals(1, trace.creationEntered(LiteRtTraceRole.DIRECTOR))
        trace.creationReturned(1)
        val earlier = trace.snapshot()
        assertEquals(2, trace.creationEntered(LiteRtTraceRole.DIRECTOR)) // A repair can keep the same role.
        trace.creationFailed(2, LiteRtTraceFailure.OTHER)
        assertEquals(3, trace.creationEntered(LiteRtTraceRole.NARRATOR))
        assertEquals(0, trace.creationEntered(LiteRtTraceRole.DIRECTOR))
        assertEquals(0, trace.creationEntered(LiteRtTraceRole.NARRATOR))
        trace.creationReturned(4)
        trace.creationFailed(0, LiteRtTraceFailure.OTHER)
        val value = trace.snapshot()
        assertEquals(listOf(1, 2, 3), value.creations.map { it.ordinal })
        assertEquals(listOf(LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.NARRATOR), value.creations.map { it.role })
        assertEquals(5, value.creationsTotal)
        assertFalse(value.creationsSaturated) // Truncation at three is not counter overflow.
        assertEquals(counts(), value.counts)
        assertEquals(1, earlier.creations.size)
        for (entry in value.creations) {
            assertTrue(entry.enteredMs in 0..value.snapshotMs)
            assertTrue(entry.returnedMs == null || entry.returnedMs in entry.enteredMs..value.snapshotMs)
            assertTrue(entry.failedMs == null || entry.failedMs in entry.enteredMs..value.snapshotMs)
        }
        @Suppress("UNCHECKED_CAST")
        val list = value.creations as MutableList<LiteRtTraceCreation>
        immutable { list.clear() }
        immutable { list[0] = list[1] }
        assertEquals(3, value.creations.size)
    }

    @Test fun creationCounterReachingCapIsNotOverflowAndRetainedMemoryDoesNotGrow() {
        val trace = LiteRtWorkerTrace()
        repeat(LiteRtWorkerTrace.MAX_COUNT) { trace.creationEntered(LiteRtTraceRole.DIRECTOR) }
        val atCap = trace.snapshot()
        assertEquals(1_000_000, atCap.creationsTotal)
        assertFalse(atCap.creationsSaturated)
        assertEquals(3, atCap.creations.size)
        assertEquals(0, trace.creationEntered(LiteRtTraceRole.NARRATOR))
        val beyondCap = trace.snapshot()
        assertEquals(1_000_000, beyondCap.creationsTotal)
        assertTrue(beyondCap.creationsSaturated)
        assertEquals(atCap.creations, beyondCap.creations)
        assertFalse(atCap.creationsSaturated)
    }

    @Test fun manualTimingSnapshotsRejectMissingInconsistentAndUnboundedValues() {
        for (ms in listOf(-1, 180_001, Int.MIN_VALUE, Int.MAX_VALUE)) refuses { snapshot(ms = ms) }
        refuses { snapshot(timeSaturated = true) }
        refuses { snapshot(last = emptyMap()) }
        refuses { snapshot(last = LiteRtWorkerEvent.entries.associateWith { 0 }) }
        refuses { snapshot(counts(1), last = LiteRtWorkerEvent.entries.associateWith { null }) }
        for (bad in listOf(-1, 2, Int.MIN_VALUE, Int.MAX_VALUE)) {
            refuses { snapshot(counts(1), last = LiteRtWorkerEvent.entries.associateWith { bad }, ms = 1) }
        }
        val exact = snapshot(counts(1), last = LiteRtWorkerEvent.entries.associateWith { 180_000 }, ms = 180_000)
        assertFalse(exact.timeSaturated)
        assertTrue(snapshot(counts(1), last = exact.lastMs, ms = 180_000, timeSaturated = true).timeSaturated)
    }

    @Test fun manualCreationSnapshotsRefuseBrokenTokensTerminalsFailureCategoriesAndBounds() {
        val pending = LiteRtTraceCreation(1, LiteRtTraceRole.DIRECTOR, 5, null, null, LiteRtTraceFailure.NONE)
        for (total in listOf(-1, 1_000_001, Int.MIN_VALUE, Int.MAX_VALUE)) refuses { snapshot(total = total) }
        refuses { snapshot(total = 0, creationsSaturated = true) }
        refuses { snapshot(total = 1) }
        refuses { snapshot(ms = 10, creations = listOf(pending)) }
        for (entry in listOf(
            pending.copy(ordinal = 0), pending.copy(ordinal = 2), pending.copy(enteredMs = -1),
            pending.copy(enteredMs = 11), pending.copy(returnedMs = 4), pending.copy(returnedMs = 11),
            pending.copy(failedMs = 4, failure = LiteRtTraceFailure.OTHER),
            pending.copy(failedMs = 11, failure = LiteRtTraceFailure.OTHER),
            pending.copy(returnedMs = 6, failedMs = 7, failure = LiteRtTraceFailure.OTHER),
            pending.copy(failedMs = 6), pending.copy(failure = LiteRtTraceFailure.OTHER),
            pending.copy(returnedMs = 6, failure = LiteRtTraceFailure.CANCELLED),
        )) refuses { snapshot(ms = 10, total = 1, creations = listOf(entry)) }
        refuses { snapshot(ms = 10, total = 2, creations = listOf(pending, pending)) }
        refuses { snapshot(ms = 10, total = 4, creations = (1..4).map { pending.copy(ordinal = it) }) }
        val oversized = object : AbstractList<LiteRtTraceCreation>() {
            override val size = Int.MAX_VALUE
            override fun get(index: Int): LiteRtTraceCreation = error("Refuse oversized input before copying")
        }
        refuses { snapshot(total = 1_000_000, creations = oversized) }
        assertEquals(4, snapshot(ms = 10, total = 4,
            creations = (1..3).map { pending.copy(ordinal = it) }).creationsTotal)
    }

    @Test fun creationJsonHasOnlyExactClosedFieldsIncludingPendingReturnAndFailureShapes() {
        val entries = listOf(
            LiteRtTraceCreation(1, LiteRtTraceRole.DIRECTOR, 0, 1, null, LiteRtTraceFailure.NONE),
            LiteRtTraceCreation(2, LiteRtTraceRole.DIRECTOR, 1, null, 2, LiteRtTraceFailure.OTHER),
            LiteRtTraceCreation(3, LiteRtTraceRole.NARRATOR, 2, null, null, LiteRtTraceFailure.NONE),
        )
        val value = snapshot(ms = 2, total = 3, creations = entries)
        val exact = "{\"ordinal\":1,\"role\":\"DIRECTOR\",\"entered_ms\":0,\"returned_ms\":1,\"failed_ms\":null,\"failure\":\"NONE\"}," +
            "{\"ordinal\":2,\"role\":\"DIRECTOR\",\"entered_ms\":1,\"returned_ms\":null,\"failed_ms\":2,\"failure\":\"OTHER\"}," +
            "{\"ordinal\":3,\"role\":\"NARRATOR\",\"entered_ms\":2,\"returned_ms\":null,\"failed_ms\":null,\"failure\":\"NONE\"}"
        assertEquals(expectedJson(List(30) { 0 }, ms = 2, total = 3, creationsJson = exact), value.json())
    }

    @Test fun concurrentCreationTerminalsAndSnapshotsKeepBoundedCopiedRecords() {
        val trace = LiteRtWorkerTrace()
        val executor = Executors.newFixedThreadPool(6)
        val gate = CountDownLatch(1)
        try {
            val futures = (0 until 4).map { index -> executor.submit {
                assertTrue(gate.await(5, TimeUnit.SECONDS))
                repeat(500) {
                    val token = trace.creationEntered(if (index % 2 == 0) LiteRtTraceRole.DIRECTOR else LiteRtTraceRole.NARRATOR)
                    if (index % 2 == 0) trace.creationReturned(token) else trace.creationFailed(token, LiteRtTraceFailure.OTHER)
                    trace.creationFailed(token, LiteRtTraceFailure.CANCELLED)
                    trace.creationReturned(token)
                }
            } } + (0 until 2).map { executor.submit {
                assertTrue(gate.await(5, TimeUnit.SECONDS))
                repeat(200) {
                    val value = trace.snapshot()
                    assertEquals(minOf(value.creationsTotal, 3), value.creations.size)
                    assertFalse(value.creationsSaturated)
                    assertTrue(value.creations.all { it.returnedMs == null || it.failedMs == null })
                    assertEquals(value.json(), value.json())
                }
            } }
            gate.countDown()
            futures.forEach { it.get(10, TimeUnit.SECONDS) }
            val value = trace.snapshot()
            assertEquals(2000, value.creationsTotal)
            assertEquals(3, value.creations.size)
            assertTrue(value.creations.all { it.returnedMs != null || it.failedMs != null })
            assertEquals(counts(), value.counts)
        } finally {
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS))
        }
    }
}
