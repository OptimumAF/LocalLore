/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CancellationException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import org.junit.Assert.*
import org.junit.Test

/** Pure closed diagnostic values. Does not construct a model, provider, or Android component. */
class ReceiptSetupFailureTraceTest {
    private fun assertSameOriginal(action: (Throwable) -> Unit) {
        val originalCause = IllegalArgumentException("Original cause")
        val original = IllegalStateException("Original block failure", originalCause)
        val priorSuppressed = IllegalArgumentException("Original suppressed failure")
        original.addSuppressed(priorSuppressed)
        val caught = try {
            action(original)
            null
        } catch (failure: Throwable) {
            failure
        }
        assertSame(original, caught)
        assertSame(originalCause, original.cause)
        assertArrayEquals(arrayOf<Throwable>(priorSuppressed), original.suppressed)
    }

    private fun snapshot(trace: ReceiptSetupFailureTrace,
        source: ReceiptSetupSourceProgress = ReceiptSetupSourceProgress(),
    ) = trace.snapshot(LocalModelSetupPhase.READY, LocalModelSetupPhase.FAILED, source)

    private fun refuses(action: () -> Unit) {
        try {
            action()
            fail("Expected a bounded-value refusal")
        } catch (_: IllegalArgumentException) {
            // A malformed observation cannot be serialized as an ordinary snapshot.
        }
    }

    private class HostileFailure : Throwable(null, null, false, false) {
        override val message: String get() = error("PRIVATE message accessor was touched")
        override fun getLocalizedMessage(): String = error("PRIVATE localized accessor was touched")
        override val cause: Throwable get() = error("PRIVATE cause accessor was touched")
        override fun getStackTrace(): Array<StackTraceElement> = error("PRIVATE stack accessor was touched")
        override fun toString(): String = error("PRIVATE toString was touched")
    }

    private class HostileCancellation : CancellationException() {
        override val message: String get() = error("PRIVATE cancellation message was touched")
        override val cause: Throwable get() = error("PRIVATE cancellation cause was touched")
        override fun getStackTrace(): Array<StackTraceElement> = error("PRIVATE cancellation stack was touched")
        override fun toString(): String = error("PRIVATE cancellation toString was touched")
    }

    @Test fun closedVocabularyAndInstrumentationEnvelopeAreStable() {
        assertEquals(setOf("ACCEPT", "CANCEL_BEFORE", "CANCEL_AFTER", "DRAIN"),
            ReceiptSetupFailureCase.entries.map { it.name }.toSet())
        assertEquals(setOf("CREATE", "START", "RESUME", "PAUSE", "STOP", "DESTROY",
            "CHECK_START", "CHECK_PRESENT", "CHECK_MISSING", "CHECK_CANCELLED", "CHECK_FAILED",
            "IMPORT_START", "IMPORT_RETURNED", "IMPORT_CANCELLED", "IMPORT_FAILED"),
            ReceiptSetupFailureEvent.entries.map { it.name }.toSet())
        assertEquals(setOf("NONE", "CANCELLED", "BUSY", "NO_SPACE", "INVALID_MODEL", "UNSAFE_PATH", "STORAGE", "OTHER"),
            ReceiptSetupFailureCode.entries.map { it.name }.toSet())
        assertEquals("locallore_receipt_failure_v1", ReceiptSetupFailureTrace.STATUS_KEY)
        assertEquals(1337, ReceiptSetupFailureTrace.STATUS_CODE)
        assertEquals("INSTRUMENTATION_STATUS: locallore_receipt_failure_v1=", ReceiptSetupFailureTrace.WIRE_PREFIX)
        assertEquals(16, ReceiptSetupFailureTrace.EVENT_LIMIT)
        assertEquals(2048, ReceiptSetupFailureTrace.MAX_BYTES)
    }

    @Test fun emptySnapshotHasExactDeterministicClosedJson() {
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.ACCEPT)
        val value = snapshot(trace)
        val expected = "{\"version\":1,\"case\":\"ACCEPT\",\"expected\":\"READY\",\"actual\":\"FAILED\"," +
            "\"error\":\"NONE\",\"events_total\":0,\"events_saturated\":false,\"events\":[]," +
            "\"source\":{\"opened\":0,\"closed\":0,\"active\":0,\"reads\":0,\"bytes\":0," +
            "\"reads_saturated\":false,\"bytes_saturated\":false}}"
        assertEquals(expected, value.json())
        assertEquals(expected, value.json())
        assertEquals(expected, snapshot(trace).json())
        assertEquals(emptyList<ReceiptSetupFailureEvent>(), value.events)
        assertEquals(ReceiptSetupFailureCode.NONE, value.error)
    }

    @Test fun typedFailuresMapOnlyTheirFiniteCategory() {
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)
        for (failure in LocalModelFailure.entries) {
            trace.error(LocalModelException(failure).apply { initCause(HostileFailure()) })
            assertEquals(ReceiptSetupFailureCode.valueOf(failure.name), snapshot(trace).error)
            assertFalse(snapshot(trace).json().contains("Local model unavailable"))
        }
        trace.error(CancellationException("secret-uri:/provider/private"))
        assertEquals(ReceiptSetupFailureCode.CANCELLED, snapshot(trace).error)
        trace.error(IllegalStateException("secret-path", LocalModelException(LocalModelFailure.BUSY)))
        assertEquals(ReceiptSetupFailureCode.OTHER, snapshot(trace).error)
        assertFalse(snapshot(trace).json().contains("secret"))
    }

    @Test fun hostileThrowableAndCancellationAccessorsAreNeverInspected() {
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.CANCEL_AFTER)
        trace.error(HostileFailure())
        val other = snapshot(trace)
        assertEquals(ReceiptSetupFailureCode.OTHER, other.error)
        assertFalse(other.json().contains("PRIVATE"))
        assertFalse(other.json().contains("Hostile"))
        trace.error(HostileCancellation())
        val cancelled = snapshot(trace)
        assertEquals(ReceiptSetupFailureCode.CANCELLED, cancelled.error)
        assertFalse(cancelled.json().contains("PRIVATE"))
        assertFalse(cancelled.json().contains("Hostile"))
        assertEquals(ReceiptSetupFailureCode.OTHER, other.error)
    }

    @Test fun onlyNewestSixteenEventsRemainInInsertionOrder() {
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.CANCEL_BEFORE)
        val recorded = List(43) { ReceiptSetupFailureEvent.entries[it % ReceiptSetupFailureEvent.entries.size] }
        recorded.forEach(trace::record)
        val value = snapshot(trace)
        assertEquals(43, value.eventsTotal)
        assertFalse(value.eventsSaturated)
        assertEquals(recorded.takeLast(16), value.events)
        assertEquals(16, value.events.size)
    }

    @Test fun snapshotsDoNotAliasFutureEventsOrErrorChanges() {
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.ACCEPT)
        trace.record(ReceiptSetupFailureEvent.CREATE)
        val before = snapshot(trace)
        val beforeJson = before.json()
        trace.record(ReceiptSetupFailureEvent.IMPORT_FAILED)
        trace.error(LocalModelException(LocalModelFailure.NO_SPACE))
        assertEquals(beforeJson, before.json())
        assertEquals(listOf(ReceiptSetupFailureEvent.CREATE), before.events)
        assertEquals(ReceiptSetupFailureCode.NONE, before.error)
        // A diagnostic consumer's mutable view must not change the trace ring.
        @Suppress("UNCHECKED_CAST")
        try { (before.events as MutableList<ReceiptSetupFailureEvent>).clear() }
        catch (_: UnsupportedOperationException) { /* A read-only copy is also acceptable. */ }
        catch (_: ClassCastException) { /* A Kotlin immutable list is also acceptable. */ }
        assertEquals(listOf(ReceiptSetupFailureEvent.CREATE, ReceiptSetupFailureEvent.IMPORT_FAILED), snapshot(trace).events)
    }

    @Test fun independentSourceObservationsHaveNoInventedCausalConstraints() {
        val source = ReceiptSetupSourceProgress(opened = 0, closed = 21, active = 12, readCalls = 0, bytesRead = 999)
        val value = snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN), source)
        assertEquals(source, value.source)
        assertTrue(value.json().contains("\"opened\":0,\"closed\":21,\"active\":12,\"reads\":0,\"bytes\":999"))
        // These are independent observations, not an assertion of leaked resources.
        assertFalse(value.json().contains("leak"))
    }

    @Test fun progressCountersRefuseNegativeOverflowAndInvalidSaturationFlags() {
        val max = ReceiptSetupFailureTrace.MAX_PROGRESS
        val valid = ReceiptSetupSourceProgress(max, max, max, max, max, true, true)
        assertTrue(snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.ACCEPT), valid).json().contains("1000000"))
        for (invalid in listOf(-1, Int.MIN_VALUE, max + 1, Int.MAX_VALUE)) {
            refuses { ReceiptSetupSourceProgress(opened = invalid) }
            refuses { ReceiptSetupSourceProgress(closed = invalid) }
            refuses { ReceiptSetupSourceProgress(active = invalid) }
            refuses { ReceiptSetupSourceProgress(readCalls = invalid) }
            refuses { ReceiptSetupSourceProgress(bytesRead = invalid) }
        }
        refuses { ReceiptSetupSourceProgress(readCalls = max - 1, readsSaturated = true) }
        refuses { ReceiptSetupSourceProgress(bytesRead = max - 1, bytesSaturated = true) }
        // Reaching the limit is distinct from a producer reporting truncation.
        assertFalse(ReceiptSetupSourceProgress(readCalls = max, bytesRead = max).readsSaturated)
        assertFalse(ReceiptSetupSourceProgress(readCalls = max, bytesRead = max).bytesSaturated)
    }

    @Test fun snapshotBoundsRefuseImpossibleRingAndTotalValues() {
        fun candidate(eventsTotal: Int = 0, eventsSaturated: Boolean = false,
                      events: List<ReceiptSetupFailureEvent> = emptyList()) = ReceiptSetupFailureSnapshot(
            ReceiptSetupFailureCase.ACCEPT, LocalModelSetupPhase.READY, LocalModelSetupPhase.FAILED,
            ReceiptSetupFailureCode.NONE, eventsTotal, eventsSaturated, events, ReceiptSetupSourceProgress())
        refuses { candidate(events = List(17) { ReceiptSetupFailureEvent.CREATE }, eventsTotal = 17) }
        refuses { candidate(events = listOf(ReceiptSetupFailureEvent.CREATE), eventsTotal = 0) }
        refuses { candidate(eventsTotal = -1) }
        refuses { candidate(eventsTotal = ReceiptSetupFailureTrace.MAX_PROGRESS + 1) }
        refuses { candidate(eventsSaturated = true) }
        assertTrue(candidate(eventsTotal = ReceiptSetupFailureTrace.MAX_PROGRESS, eventsSaturated = true).eventsSaturated)
    }

    @Test fun callerAndPublishedListsCannotChangeAnExistingReceipt() {
        val caller = mutableListOf(ReceiptSetupFailureEvent.CREATE, ReceiptSetupFailureEvent.START)
        val value = ReceiptSetupFailureSnapshot(ReceiptSetupFailureCase.ACCEPT,
            LocalModelSetupPhase.READY, LocalModelSetupPhase.IMPORTING, ReceiptSetupFailureCode.NONE,
            2, false, caller, ReceiptSetupSourceProgress())
        val before = value.json()
        repeat(32) { caller.add(ReceiptSetupFailureEvent.IMPORT_FAILED) }
        (value.events as MutableList<ReceiptSetupFailureEvent>).clear()
        assertEquals(before, value.json())
        assertEquals(listOf(ReceiptSetupFailureEvent.CREATE, ReceiptSetupFailureEvent.START), value.events)
    }

    @Test fun eventCountSaturatesWithoutOverflowWhileRingContinues() {
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)
        repeat(ReceiptSetupFailureTrace.MAX_PROGRESS) { trace.record(ReceiptSetupFailureEvent.CHECK_START) }
        assertEquals(ReceiptSetupFailureTrace.MAX_PROGRESS, snapshot(trace).eventsTotal)
        assertFalse(snapshot(trace).eventsSaturated)
        repeat(16) { trace.record(ReceiptSetupFailureEvent.IMPORT_CANCELLED) }
        val value = snapshot(trace)
        assertEquals(ReceiptSetupFailureTrace.MAX_PROGRESS, value.eventsTotal)
        assertTrue(value.eventsSaturated)
        assertEquals(List(16) { ReceiptSetupFailureEvent.IMPORT_CANCELLED }, value.events)
    }

    @Test fun largestVocabularyWireIsAsciiBoundedAndHasOnlyClosedKeys() {
        val longestEvent = ReceiptSetupFailureEvent.entries.maxBy { it.name.length }
        val longestPhase = LocalModelSetupPhase.entries.maxBy { it.name.length }
        val progress = ReceiptSetupSourceProgress(1_000_000, 1_000_000, 1_000_000, 1_000_000, 1_000_000, true, true)
        val keys = setOf("version", "case", "expected", "actual", "error", "events_total", "events_saturated",
            "events", "source", "opened", "closed", "active", "reads", "bytes", "reads_saturated", "bytes_saturated")
        for (case in ReceiptSetupFailureCase.entries) {
            for (code in ReceiptSetupFailureCode.entries) {
                val value = ReceiptSetupFailureSnapshot(case, longestPhase, longestPhase, code, 1_000_000,
                    true, List(16) { longestEvent }, progress)
                val json = value.json()
                val wire = (ReceiptSetupFailureTrace.WIRE_PREFIX + json).toByteArray(Charsets.UTF_8)
                assertTrue(wire.size <= 2048)
                assertTrue(wire.all { it.toInt() in 32..126 })
                val foundKeys = Regex("\"([a-z_]+)\":").findAll(json).map { it.groupValues[1] }.toList()
                assertEquals(keys, foundKeys.toSet())
                assertEquals(keys.size, foundKeys.size)
                assertEquals(json, value.json())
            }
        }
        // The encoder and trace constructors have no arbitrary String input.
        for (type in listOf(ReceiptSetupFailureTrace::class.java, ReceiptSetupFailureSnapshot::class.java,
            ReceiptSetupSourceProgress::class.java)) {
            assertFalse(type.declaredConstructors.any { String::class.java in it.parameterTypes })
        }
    }

    @Test fun concurrentRecordingAndSnapshotsStayBoundedWithoutCrossFieldAtomicityClaim() {
        val trace = ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)
        val executor = Executors.newFixedThreadPool(5)
        val gate = CountDownLatch(1)
        val opened = AtomicInteger()
        val closed = AtomicInteger()
        try {
            val writers = (0 until 3).map { writer -> executor.submit {
                assertTrue(gate.await(5, TimeUnit.SECONDS))
                repeat(2000) {
                    closed.incrementAndGet()
                    trace.record(ReceiptSetupFailureEvent.entries[writer])
                    opened.incrementAndGet()
                }
            } }
            val readers = (0 until 2).map { executor.submit {
                assertTrue(gate.await(5, TimeUnit.SECONDS))
                var prior = 0
                repeat(500) {
                    val source = ReceiptSetupSourceProgress(opened = opened.get(), closed = closed.get())
                    val value = snapshot(trace, source)
                    assertTrue(value.eventsTotal >= prior)
                    prior = value.eventsTotal
                    assertTrue(value.events.size <= 16)
                    assertEquals(source, value.source)
                    assertTrue((ReceiptSetupFailureTrace.WIRE_PREFIX + value.json()).toByteArray(Charsets.UTF_8).size <= 2048)
                }
            } }
            gate.countDown()
            (writers + readers).forEach { it.get(10, TimeUnit.SECONDS) }
            val value = snapshot(trace)
            assertEquals(6000, value.eventsTotal)
            assertEquals(16, value.events.size)
            assertFalse(value.eventsSaturated)
        } finally {
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS))
        }
    }

    @Test fun reporterSuccessReturnsOriginalValueWithoutTouchingAnyDiagnosticClosure() {
        val expected = Any()
        val returned = ReceiptSetupFailureReporter.run(
            claim = { error("Success must not claim a diagnostic") },
            snapshot = { error("Success must not create a snapshot") },
            send = { _, _, _ -> error("Success must not send status") },
        ) { expected }
        assertSame(expected, returned)
        val absent: Any? = ReceiptSetupFailureReporter.run(
            claim = { error("Null success must not claim") },
            snapshot = { error("Null success must not snapshot") },
            send = { _, _, _ -> error("Null success must not send") },
        ) { null }
        assertNull(absent)
    }

    @Test fun reporterFailureEmitsExactStatusOnceInOrderAndRethrowsOriginal() {
        val order = mutableListOf<String>()
        val value = snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.ACCEPT))
        val sent = mutableListOf<Triple<Int, String, String>>()
        assertSameOriginal { original ->
            ReceiptSetupFailureReporter.run(
                claim = { order.add("claim"); true },
                snapshot = { order.add("snapshot"); value },
                send = { code, key, json -> order.add("send"); sent.add(Triple(code, key, json)) },
            ) { order.add("block"); throw original }
        }
        assertEquals(listOf("block", "claim", "snapshot", "send"), order)
        assertEquals(listOf(Triple(1337, "locallore_receipt_failure_v1", value.json())), sent)
        assertFalse(sent.single().third.startsWith(ReceiptSetupFailureTrace.WIRE_PREFIX))
    }

    @Test fun reporterBlockErrorsCancellationAndHostileOriginalKeepExactIdentity() {
        for (original in listOf(AssertionError("Original assertion"), CancellationException("Original cancellation"), HostileFailure())) {
            var sent = 0
            val caught = try {
                ReceiptSetupFailureReporter.run(
                    claim = { true },
                    snapshot = { snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)) },
                    send = { _, _, _ -> sent++ },
                ) { throw original }
            } catch (failure: Throwable) {
                failure
            }
            assertSame(original, caught)
            assertEquals(1, sent)
        }
    }

    @Test fun reporterDeclinedClaimNeverConstructsSnapshotOrSends() {
        val claims = AtomicInteger()
        assertSameOriginal { original ->
            ReceiptSetupFailureReporter.run(
                claim = { claims.incrementAndGet(); false },
                snapshot = { error("Declined claim must not construct a snapshot") },
                send = { _, _, _ -> error("Declined claim must not send") },
            ) { throw original }
        }
        assertEquals(1, claims.get())
    }

    @Test fun reporterClaimFailuresIncludingErrorsNeverReplaceOrSuppressOriginal() {
        for (diagnostic in listOf(AssertionError("Claim error"), CancellationException("Claim cancelled"), HostileFailure())) {
            var snapshotCalls = 0
            var sendCalls = 0
            assertSameOriginal { original ->
                ReceiptSetupFailureReporter.run(
                    claim = { throw diagnostic },
                    snapshot = { snapshotCalls++; snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)) },
                    send = { _, _, _ -> sendCalls++ },
                ) { throw original }
            }
            assertEquals(0, snapshotCalls)
            assertEquals(0, sendCalls)
        }
    }

    @Test fun reporterSnapshotOrBoundedValueConstructionFailurePreservesOriginal() {
        val failedSnapshots: List<() -> ReceiptSetupFailureSnapshot> = listOf(
            { throw AssertionError("Snapshot error") },
            { throw HostileFailure() },
            { throw CancellationException("Snapshot cancelled") },
            { snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN),
                ReceiptSetupSourceProgress(readCalls = -1)) },
        )
        for (failedSnapshot in failedSnapshots) {
            var sendCalls = 0
            assertSameOriginal { original ->
                ReceiptSetupFailureReporter.run(
                    claim = { true }, snapshot = failedSnapshot,
                    send = { _, _, _ -> sendCalls++ },
                ) { throw original }
            }
            assertEquals(0, sendCalls)
        }
    }

    @Test fun reporterSendFailuresIncludingErrorsPreserveOriginalWithoutRetry() {
        for (diagnostic in listOf(AssertionError("Send error"), CancellationException("Send cancelled"), HostileFailure())) {
            var sendCalls = 0
            assertSameOriginal { original ->
                ReceiptSetupFailureReporter.run(
                    claim = { true },
                    snapshot = { snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)) },
                    send = { _, _, _ -> sendCalls++; throw diagnostic },
                ) { throw original }
            }
            assertEquals(1, sendCalls)
        }
    }

    @Test fun reporterAtomicClaimEmitsOnceAcrossSeparateOriginalFailures() {
        val claimed = AtomicBoolean()
        var snapshots = 0
        var sends = 0
        repeat(2) {
            assertSameOriginal { original ->
                ReceiptSetupFailureReporter.run(
                    claim = { claimed.compareAndSet(false, true) },
                    snapshot = { snapshots++; snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)) },
                    send = { _, _, _ -> sends++ },
                ) { throw original }
            }
        }
        assertTrue(claimed.get())
        assertEquals(1, snapshots)
        assertEquals(1, sends)
    }

    @Test fun reporterFailedSendStillConsumesOneShotClaimAndCannotResurrectIt() {
        val claimed = AtomicBoolean()
        var snapshots = 0
        var sends = 0
        repeat(2) {
            assertSameOriginal { original ->
                ReceiptSetupFailureReporter.run(
                    claim = { claimed.compareAndSet(false, true) },
                    snapshot = { snapshots++; snapshot(ReceiptSetupFailureTrace(ReceiptSetupFailureCase.DRAIN)) },
                    send = { _, _, _ -> sends++; throw HostileFailure() },
                ) { throw original }
            }
        }
        assertTrue(claimed.get())
        assertEquals(1, snapshots)
        assertEquals(1, sends)
    }
}
