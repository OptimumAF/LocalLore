/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import java.io.File
import java.security.MessageDigest
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class LiteRtSendTraceTest {
    @get:Rule val temporary = TemporaryFolder()
    private fun snapshot(count: Int = 0, last: Int? = null, time: Int = 0, overflow: Boolean = false, timeOverflow: Boolean = false) =
        LiteRtSendSnapshot(LiteRtSendEvent.entries.associateWith { count },
            if (overflow) LiteRtSendEvent.entries.toSet() else emptySet(),
            LiteRtSendEvent.entries.associateWith { last }, time, timeOverflow)
    private fun refuses(block: () -> Unit) {
        try { block(); fail("Invalid send snapshot accepted") } catch (_: IllegalArgumentException) { }
    }
    private fun immutable(block: () -> Unit) {
        try { block(); fail("Mutable send snapshot") } catch (_: UnsupportedOperationException) { }
    }
    private fun sameFailure(expected: Throwable, block: () -> Unit) {
        var observed: Throwable? = null
        try { block() } catch (failure: Throwable) { observed = failure }
        assertSame(expected, observed)
        assertTrue(expected.suppressed.isEmpty())
    }
    private class HostileFailure : Throwable() {
        override val message: String get() = error("Private message inspected")
        override val cause: Throwable? get() = error("Private cause inspected")
        override fun getStackTrace(): Array<StackTraceElement> = error("Private stack inspected")
        override fun toString(): String = error("Private description inspected")
    }

    @Test fun eventOrderAndWireConstantsAreIndependentAndClosed() {
        assertEquals(listOf("ARGUMENTS_ENTERED", "ARGUMENTS_RETURNED", "ARGUMENTS_THROWN", "ASYNC_CALL_ENTERED", "ASYNC_CALL_RETURNED", "ASYNC_CALL_THROWN"),
            LiteRtSendEvent.entries.map { it.name })
        assertEquals("locallore_receipt_send_v1", LiteRtSendTrace.STATUS_KEY)
        assertEquals(1338, LiteRtSendTrace.STATUS_CODE)
        assertEquals("INSTRUMENTATION_STATUS: locallore_receipt_send_v1=", LiteRtSendTrace.WIRE_PREFIX)
        assertEquals(2048, LiteRtSendTrace.MAX_BYTES); assertEquals(1000000, LiteRtSendTrace.MAX_COUNT); assertEquals(180000, LiteRtSendTrace.MAX_MS)
        assertFalse(LiteRtSendTrace.STATUS_KEY == LiteRtWorkerTrace.STATUS_KEY)
    }
    @Test fun emptyTraceAndManualWireHaveEveryKeyAndNullTimes() {
        val current = LiteRtSendTrace().snapshot()
        assertTrue(current.counts.values.all { it == 0 }); assertTrue(current.lastMs.values.all { it == null })
        assertTrue(current.saturated.isEmpty()); assertFalse(current.timeSaturated)
        assertTrue(current.snapshotMs in 0..LiteRtSendTrace.MAX_MS)
        val value = snapshot().json()
        val counts = LiteRtSendEvent.entries.joinToString(",") { "\"${it.name}\":0" }
        val times = LiteRtSendEvent.entries.joinToString(",") { "\"${it.name}\":null" }
        assertEquals("{\"version\":1,\"counts\":{$counts},\"saturated\":[],\"last_ms\":{$times},\"snapshot_ms\":0,\"time_saturated\":false}", value)
    }
    @Test fun traceSnapshotsAreHistoricalCopiesWithMonotonicObservationTimes() {
        val trace = LiteRtSendTrace()
        trace.record(LiteRtSendEvent.ARGUMENTS_ENTERED)
        val first = trace.snapshot(); val wire = first.json()
        trace.record(LiteRtSendEvent.ARGUMENTS_ENTERED); trace.record(LiteRtSendEvent.ARGUMENTS_RETURNED)
        val second = trace.snapshot()
        assertEquals(wire, first.json()); assertEquals(1, first.counts.getValue(LiteRtSendEvent.ARGUMENTS_ENTERED))
        assertEquals(2, second.counts.getValue(LiteRtSendEvent.ARGUMENTS_ENTERED))
        assertEquals(1, second.counts.getValue(LiteRtSendEvent.ARGUMENTS_RETURNED))
        assertTrue(second.snapshotMs >= first.snapshotMs)
        assertTrue(second.lastMs.getValue(LiteRtSendEvent.ARGUMENTS_ENTERED)!! >= first.lastMs.getValue(LiteRtSendEvent.ARGUMENTS_ENTERED)!!)
    }
    @Test fun manualSnapshotCopiesInputsAndRejectsAllCollectionMutationRoutes() {
        val counts = LiteRtSendEvent.entries.associateWith { LiteRtSendTrace.MAX_COUNT }.toMutableMap()
        val saturated = LiteRtSendEvent.entries.toMutableSet()
        val times = LiteRtSendEvent.entries.associateWith { 1 as Int? }.toMutableMap()
        val value = LiteRtSendSnapshot(counts, saturated, times, 1, false); val wire = value.json()
        counts.clear(); saturated.clear(); times.clear(); assertEquals(wire, value.json())
        @Suppress("UNCHECKED_CAST") val copiedCounts = value.counts as MutableMap<LiteRtSendEvent, Int>
        @Suppress("UNCHECKED_CAST") val copiedTimes = value.lastMs as MutableMap<LiteRtSendEvent, Int?>
        @Suppress("UNCHECKED_CAST") val copiedSet = value.saturated as MutableSet<LiteRtSendEvent>
        immutable { copiedCounts.clear() }; immutable { copiedCounts.entries.first().setValue(0) }
        immutable { copiedTimes.clear() }; immutable { copiedTimes.entries.first().setValue(null) }; immutable { copiedSet.clear() }
    }
    @Test fun snapshotRequiresExactKeysAndBoundedCountsAndSaturation() {
        val zero = LiteRtSendEvent.entries.associateWith { 0 }
        val times = LiteRtSendEvent.entries.associateWith { null as Int? }
        refuses { LiteRtSendSnapshot(emptyMap(), emptySet(), times, 0, false) }
        refuses { LiteRtSendSnapshot(zero, emptySet(), emptyMap(), 0, false) }
        refuses { LiteRtSendSnapshot(zero - LiteRtSendEvent.ARGUMENTS_ENTERED, emptySet(), times, 0, false) }
        refuses { snapshot(count = -1, last = 0) }; refuses { snapshot(count = LiteRtSendTrace.MAX_COUNT + 1, last = 0) }
        refuses { snapshot(count = 1, last = 0, overflow = true) }
        assertNotNull(snapshot(count = LiteRtSendTrace.MAX_COUNT, last = 0, overflow = false).json())
        assertNotNull(snapshot(count = LiteRtSendTrace.MAX_COUNT, last = 0, overflow = true).json())
    }
    @Test fun snapshotRequiresNullIffZeroAndBoundedTimes() {
        refuses { snapshot(count = 0, last = 0) }; refuses { snapshot(count = 1, last = null) }
        refuses { snapshot(count = 1, last = -1) }; refuses { snapshot(count = 1, last = 2, time = 1) }
        refuses { snapshot(time = -1) }; refuses { snapshot(time = LiteRtSendTrace.MAX_MS + 1) }
        refuses { snapshot(time = LiteRtSendTrace.MAX_MS - 1, timeOverflow = true) }
        assertNotNull(snapshot(1, LiteRtSendTrace.MAX_MS, LiteRtSendTrace.MAX_MS, timeOverflow = false).json())
        assertNotNull(snapshot(1, LiteRtSendTrace.MAX_MS, LiteRtSendTrace.MAX_MS, timeOverflow = true).json())
    }
    @Test fun clockMathClampsBeforeNarrowingAndFlagsOnlyStrictOverflow() {
        val cap = LiteRtSendTrace.MAX_MS.toLong() * 1000000
        assertEquals(LiteRtSendTime(0, false), liteRtSendTime(Long.MIN_VALUE))
        assertEquals(LiteRtSendTime(0, false), liteRtSendTime(-1))
        assertEquals(LiteRtSendTime(0, false), liteRtSendTime(999999))
        assertEquals(LiteRtSendTime(1, false), liteRtSendTime(1000000))
        assertEquals(LiteRtSendTime(LiteRtSendTrace.MAX_MS, false), liteRtSendTime(cap))
        assertEquals(LiteRtSendTime(LiteRtSendTrace.MAX_MS, true), liteRtSendTime(cap + 1))
        assertEquals(LiteRtSendTime(LiteRtSendTrace.MAX_MS, true), liteRtSendTime(Long.MAX_VALUE))
    }
    @Test fun actualCounterSaturatesOnlyOnOverflowAndRemainsSticky() {
        val trace = LiteRtSendTrace()
        repeat(LiteRtSendTrace.MAX_COUNT) { trace.record(LiteRtSendEvent.ARGUMENTS_THROWN) }
        val exact = trace.snapshot()
        assertEquals(LiteRtSendTrace.MAX_COUNT, exact.counts.getValue(LiteRtSendEvent.ARGUMENTS_THROWN)); assertTrue(exact.saturated.isEmpty())
        trace.record(LiteRtSendEvent.ARGUMENTS_THROWN); trace.record(LiteRtSendEvent.ASYNC_CALL_ENTERED)
        val overflow = trace.snapshot()
        assertEquals(LiteRtSendTrace.MAX_COUNT, overflow.counts.getValue(LiteRtSendEvent.ARGUMENTS_THROWN))
        assertEquals(setOf(LiteRtSendEvent.ARGUMENTS_THROWN), overflow.saturated)
        assertEquals(1, overflow.counts.getValue(LiteRtSendEvent.ASYNC_CALL_ENTERED)); assertTrue(exact.saturated.isEmpty())
    }
    @Test fun concurrentRecordsAndSnapshotsRetainExactCountsAndValidWire() {
        val trace = LiteRtSendTrace(); val pool = Executors.newFixedThreadPool(7); val start = CountDownLatch(1)
        try {
            val jobs = LiteRtSendEvent.entries.map { event -> pool.submit { start.await(); repeat(5000) { trace.record(event) } } }
            val observer = pool.submit { start.await(); repeat(100) { assertTrue(trace.snapshot().json().length < 2048) } }
            start.countDown(); jobs.forEach { it.get(10, TimeUnit.SECONDS) }; observer.get(10, TimeUnit.SECONDS)
            assertTrue(trace.snapshot().counts.values.all { it == 5000 })
        } finally { pool.shutdownNow(); assertTrue(pool.awaitTermination(10, TimeUnit.SECONDS)) }
    }
    @Test fun denseWireHasClosedOrderedKeysAndIncludesPrefixInCap() {
        val value = snapshot(LiteRtSendTrace.MAX_COUNT, LiteRtSendTrace.MAX_MS, LiteRtSendTrace.MAX_MS, true, true)
        val wire = value.json()
        assertEquals(wire, value.json()); assertTrue(wire.all { it.code in 32..126 })
        assertTrue((LiteRtSendTrace.WIRE_PREFIX + wire).toByteArray(Charsets.UTF_8).size <= LiteRtSendTrace.MAX_BYTES)
        assertEquals(552, wire.toByteArray(Charsets.US_ASCII).size)
        assertEquals(602, (LiteRtSendTrace.WIRE_PREFIX + wire).toByteArray(Charsets.US_ASCII).size)
        assertEquals("12402ccfe90b5203a3abcf569d6cee9be95112778c8668b6a3733a5318bf86a6",
            MessageDigest.getInstance("SHA-256").digest(wire.toByteArray(Charsets.US_ASCII)).joinToString("") { "%02x".format(it) })
        assertEquals(1, Regex("\"version\":").findAll(wire).count())
        val expectedSet = LiteRtSendEvent.entries.joinToString(",", "\"saturated\":[", "]") { "\"${it.name}\"" }
        assertTrue(wire.contains(expectedSet)); assertTrue(wire.endsWith("\"snapshot_ms\":180000,\"time_saturated\":true}"))
    }
    @Test fun traceSurfaceCannotInspectRawPrivateDataOrCallerClock() {
        for (constructor in LiteRtSendTrace::class.java.declaredConstructors) assertTrue(constructor.parameterTypes.isEmpty())
        val method = LiteRtSendTrace::class.java.getDeclaredMethod("record", LiteRtSendEvent::class.java)
        assertEquals(Void.TYPE, method.returnType)
        for (field in LiteRtSendTrace::class.java.declaredFields) assertFalse(field.type == Throwable::class.java ||
            field.type.name.startsWith("java.io.") || field.type.name.startsWith("kotlin.jvm.functions."))
        val wire = snapshot().json(); assertFalse(wire.contains("prompt")); assertFalse(wire.contains("message")); assertFalse(wire.contains("cause"))
    }
    @Test fun normalHelperPassesExactPreparedObjectOnceInOrder() {
        val events = mutableListOf<LiteRtSendEvent>(); val token = Any(); var prepares = 0; var dispatches = 0
        val observer = LiteRtSendObserver { events.add(it) }
        observedLiteRtSend(observer, { prepares++; token }, { assertSame(token, it); dispatches++ })
        assertEquals(1, prepares); assertEquals(1, dispatches)
        assertEquals(listOf(LiteRtSendEvent.ARGUMENTS_ENTERED, LiteRtSendEvent.ARGUMENTS_RETURNED,
            LiteRtSendEvent.ASYNC_CALL_ENTERED, LiteRtSendEvent.ASYNC_CALL_RETURNED), events)
    }
    @Test fun preparationFailureNeverDispatchesAndRethrowsIdenticalHostileOriginal() {
        val original = HostileFailure(); val events = mutableListOf<LiteRtSendEvent>(); var dispatches = 0
        sameFailure(original) { observedLiteRtSend<Any>(LiteRtSendObserver { events.add(it) }, { throw original }, { dispatches++ }) }
        assertEquals(0, dispatches); assertEquals(listOf(LiteRtSendEvent.ARGUMENTS_ENTERED, LiteRtSendEvent.ARGUMENTS_THROWN), events)
    }
    @Test fun dispatchFailureRetainsArgumentReturnAndSameOriginalWithoutCallReturn() {
        val original = CancellationException("PRIVATE_SEND_CANARY"); val events = mutableListOf<LiteRtSendEvent>()
        sameFailure(original) { observedLiteRtSend(LiteRtSendObserver { events.add(it) }, { Unit }, { throw original }) }
        assertEquals(listOf(LiteRtSendEvent.ARGUMENTS_ENTERED, LiteRtSendEvent.ARGUMENTS_RETURNED,
            LiteRtSendEvent.ASYNC_CALL_ENTERED, LiteRtSendEvent.ASYNC_CALL_THROWN), events)
    }
    @Test fun synchronousErrorNotificationWithNormalDispatchReturnIsNotCallThrow() {
        val trace = LiteRtSendTrace(); val original = HostileFailure(); var notified: Throwable? = null
        val callback: (Throwable) -> Unit = { notified = it }
        observedLiteRtSend(trace, { Unit }, { callback(original) })
        assertSame(original, notified)
        val result = trace.snapshot()
        assertEquals(1, result.counts.getValue(LiteRtSendEvent.ASYNC_CALL_RETURNED)); assertEquals(0, result.counts.getValue(LiteRtSendEvent.ASYNC_CALL_THROWN))
    }
    @Test fun laterCallbackCannotRetroactivelyChangeReturnedCallBoundary() {
        val trace = LiteRtSendTrace(); var callback: (() -> Unit)? = null; var notified = false
        observedLiteRtSend(trace, { Unit }, { callback = { notified = true } })
        val before = trace.snapshot().counts
        requireNotNull(callback).invoke()
        assertTrue(notified); assertEquals(before, trace.snapshot().counts)
    }
    @Test fun synchronousTerminalThenDispatchThrowIsStillAnIdenticalCallFailure() {
        val trace = LiteRtSendTrace(); val original = HostileFailure(); var terminal = false
        sameFailure(original) { observedLiteRtSend(trace, { Unit }, { terminal = true; throw original }) }
        assertTrue(terminal)
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtSendEvent.ASYNC_CALL_THROWN))
        assertEquals(0, trace.snapshot().counts.getValue(LiteRtSendEvent.ASYNC_CALL_RETURNED))
    }
    @Test fun observerThrowsAtEveryPointButCannotChangeNormalOrExceptionalOutcomes() {
        val observer = LiteRtSendObserver { throw HostileFailure() }; var dispatched = 0
        observedLiteRtSend(observer, { 9 }, { assertEquals(9, it); dispatched++ }); assertEquals(1, dispatched)
        val arguments = HostileFailure()
        sameFailure(arguments) { observedLiteRtSend<Any>(observer, { throw arguments }, { fail("Must not dispatch") }) }
        val call = HostileFailure()
        sameFailure(call) { observedLiteRtSend(observer, { Unit }, { throw call }) }
        var count = 0; observedLiteRtSend(null, { Unit }, { count++ }); assertEquals(1, count)
        sameFailure(arguments) { observedLiteRtSend<Any>(null, { throw arguments }, { fail("Must not dispatch") }) }
        sameFailure(call) { observedLiteRtSend(null, { Unit }, { throw call }) }
    }

    private enum class FailurePoint { ARGUMENTS, CALL, TERMINAL_THEN_CALL, CALLBACK_ERROR }
    private class SendResources(private val point: FailurePoint, private val observer: LiteRtSendObserver?) : LiteRtResources {
        val engines = AtomicInteger(); val dispatches = AtomicInteger(); val callbackCount = AtomicInteger()
        val engineCloses = AtomicInteger(); val conversationCloses = AtomicInteger()
        override fun engine(paths: LiteRtPaths): LiteRtEngineResource {
            engines.incrementAndGet()
            return object : LiteRtEngineResource {
                override fun initialize() = Unit
                override fun conversation(request: LocalInferenceRequest): LiteRtConversationResource = object : LiteRtConversationResource {
                    override fun send(request: LocalInferenceRequest, callbacks: LiteRtCallbacks) {
                        observedLiteRtSend(observer, {
                            if (point == FailurePoint.ARGUMENTS) throw HostileFailure()
                            Unit
                        }, {
                            dispatches.incrementAndGet()
                            if (point == FailurePoint.TERMINAL_THEN_CALL) { callbackCount.incrementAndGet(); callbacks.done() }
                            if (point == FailurePoint.CALLBACK_ERROR) { callbackCount.incrementAndGet(); callbacks.error(false) }
                            else throw HostileFailure()
                        })
                    }
                    override fun cancel() = Unit
                    override fun close(): Boolean { conversationCloses.incrementAndGet(); return true }
                }
                override fun close(): Boolean { engineCloses.incrementAndGet(); return true }
            }
        }
    }
    private class GuardedPort(request: LocalInferenceRequest) : LocalInferenceNativePort {
        private val pending = AtomicReference<LocalInferencePending?>(LocalInferencePending(1, request))
        private val terminal = CountDownLatch(1)
        val deliveries = AtomicInteger(); val commits = AtomicInteger(); val closes = AtomicInteger()
        override fun call(input: ByteArray): ByteArray = when (input.toString(Charsets.UTF_8)) {
            "prepare" -> { check(terminal.await(2, TimeUnit.SECONDS)); "cancelled".toByteArray() }
            "cancel" -> { invalidate(); "cancelled".toByteArray() }
            "commit" -> { commits.incrementAndGet(); "committed".toByteArray() }
            else -> error("Unexpected synthetic command")
        }
        override fun poll(): LocalInferencePending? = pending.get()
        override fun respond(ticket: Long, response: ByteArray): Boolean {
            deliveries.incrementAndGet(); invalidate(); return true
        }
        private fun invalidate() { pending.set(null); terminal.countDown() }
        override fun close() { closes.incrementAndGet(); invalidate() }
    }
    private fun config(): LiteRtWorkerConfig {
        val root = temporary.newFolder()
        val model = File(root, "original-four-byte-synthetic.litertlm").also { it.writeBytes(byteArrayOf(1, 2, 3, 4)) }
        val cache = File(root, "synthetic-cache").also { check(it.mkdir()) }
        val digest = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
        return LiteRtWorkerConfig(root, model, cache, 4, digest, "a".repeat(64), "b".repeat(64), "c".repeat(64), deadlineMs = 500)
    }
    private suspend fun uncertain(block: suspend () -> Unit) {
        try { block(); fail("Uncertainty must refuse") } catch (failure: LocalInferenceUncertain) {
            var current: Throwable? = failure
            val seen = java.util.IdentityHashMap<Throwable, Boolean>()
            var depth = 0
            while (current != null) {
                assertTrue(depth++ < 8); assertNull(seen.put(current, true))
                assertEquals(LocalInferenceUncertain::class.java, current.javaClass)
                assertEquals("Local inference ownership uncertain", current.message)
                current = current.cause
            }
        }
    }
    @Test fun realWorkerAndOwnerQuarantineHelperFailuresWithoutDeliveryCommitReuseOrUnsafeClose() = runBlocking {
        val request = LocalInferenceRequest(1, "director", "original synthetic prompt", 350, 4096, 4, "{\"type\":\"object\"}")
        for (point in FailurePoint.entries) for (hostileObserver in listOf(false, true)) {
            val trace = LiteRtSendTrace()
            val observer = if (hostileObserver) LiteRtSendObserver { trace.record(it); throw HostileFailure() } else trace
            val resources = SendResources(point, observer)
            val owner = config().createOwner(LocalInferenceLimits(turnMs = 500, cleanupMs = 200, pollMs = 2), resources)
            val port = GuardedPort(request)
            try {
                uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
                assertTrue(owner.quarantined); assertTrue(owner.nativeInvalidatedKnown)
                assertEquals(0, port.deliveries.get()); assertEquals(0, port.commits.get())
                assertEquals(1, resources.engines.get())
                assertEquals(if (point == FailurePoint.ARGUMENTS) 0 else 1, resources.dispatches.get())
                assertEquals(0, resources.conversationCloses.get()); assertEquals(0, resources.engineCloses.get())
                uncertain { owner.execute(port, "commit", "commit".toByteArray()) }
                uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
                assertEquals(0, port.commits.get()); assertEquals(0, port.deliveries.get()); assertEquals(1, resources.engines.get())
                val observed = trace.snapshot().counts
                assertEquals(if (point == FailurePoint.ARGUMENTS) 1 else 0, observed.getValue(LiteRtSendEvent.ARGUMENTS_THROWN))
                assertEquals(if (point == FailurePoint.CALLBACK_ERROR) 1 else 0, observed.getValue(LiteRtSendEvent.ASYNC_CALL_RETURNED))
                assertEquals(if (point == FailurePoint.CALL || point == FailurePoint.TERMINAL_THEN_CALL) 1 else 0,
                    observed.getValue(LiteRtSendEvent.ASYNC_CALL_THROWN))
            } finally { owner.close() }
            assertEquals(0, resources.conversationCloses.get()); assertEquals(0, resources.engineCloses.get())
        }
    }
}
