/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import com.google.ai.edge.litertlm.LiteRtLmJniException
import java.lang.reflect.Modifier
import java.security.MessageDigest
import java.util.concurrent.CancellationException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Test

class LiteRtStatusTraceTest {
    private fun snapshot(count: Int = 0, saturated: Boolean = false) = LiteRtStatusSnapshot(
        LiteRtDeclaredStatus.entries.associateWith { count }, if (saturated) LiteRtDeclaredStatus.entries.toSet() else emptySet())
    private fun refuses(block: () -> Unit) {
        try { block(); fail("Invalid status snapshot accepted") } catch (_: IllegalArgumentException) { }
    }
    private fun immutable(block: () -> Unit) {
        try { block(); fail("Mutable status snapshot") } catch (_: UnsupportedOperationException) { }
    }
    private open class HostileFailure : Throwable() {
        var reads = 0
        override val message: String get() { reads++; error("Private message inspected") }
        override val cause: Throwable? get() { reads++; error("Private cause inspected") }
        override fun getStackTrace(): Array<StackTraceElement> { reads++; error("Private stack inspected") }
        override fun toString(): String { reads++; error("Private description inspected") }
    }

    @Test fun declaredStatusesAndWireConstantsAreClosed() {
        assertEquals((0..16).map { "CODE_$it" } + "UNRECOGNIZED", LiteRtDeclaredStatus.entries.map { it.name })
        assertEquals(1340, LiteRtStatusTrace.STATUS_CODE); assertEquals(2048, LiteRtStatusTrace.MAX_BYTES)
        assertEquals(1000000, LiteRtStatusTrace.MAX_COUNT); assertEquals("locallore_receipt_status_v1", LiteRtStatusTrace.STATUS_KEY)
        assertEquals("INSTRUMENTATION_STATUS: locallore_receipt_status_v1=", LiteRtStatusTrace.WIRE_PREFIX)
    }
    @Test fun emptySnapshotHasExactClosedOrderedWire() {
        val value = LiteRtStatusTrace().snapshot()
        assertTrue(value.counts.values.all { it == 0 }); assertTrue(value.saturated.isEmpty())
        val fields = LiteRtDeclaredStatus.entries.joinToString(",") { "\"${it.name}\":0" }
        assertEquals("{\"version\":1,\"counts\":{$fields},\"saturated\":[]}", value.json())
    }
    @Test fun recordingDoesNotReinterpretZeroOneOrUnknownAsLifecycle() {
        val trace = LiteRtStatusTrace()
        trace.record(LiteRtDeclaredStatus.CODE_0); trace.record(LiteRtDeclaredStatus.CODE_1); trace.record(LiteRtDeclaredStatus.UNRECOGNIZED)
        val old = trace.snapshot(); val wire = old.json()
        trace.record(LiteRtDeclaredStatus.CODE_13)
        assertEquals(wire, old.json())
        for (status in listOf(LiteRtDeclaredStatus.CODE_0, LiteRtDeclaredStatus.CODE_1, LiteRtDeclaredStatus.UNRECOGNIZED))
            assertEquals(1, trace.snapshot().counts.getValue(status))
        assertEquals(0, old.counts.getValue(LiteRtDeclaredStatus.CODE_13))
    }
    @Test fun nestedCollectionsAreDefensivelyCopiedAndEntriesImmutable() {
        val counts = LiteRtDeclaredStatus.entries.associateWith { 1000000 }.toMutableMap()
        val flags = LiteRtDeclaredStatus.entries.toMutableSet()
        val value = LiteRtStatusSnapshot(counts, flags); val before = value.json()
        counts.clear(); flags.clear(); assertEquals(before, value.json())
        @Suppress("UNCHECKED_CAST") val mutableCounts = value.counts as MutableMap<LiteRtDeclaredStatus, Int>
        @Suppress("UNCHECKED_CAST") val mutableFlags = value.saturated as MutableSet<LiteRtDeclaredStatus>
        immutable { mutableCounts.clear() }; immutable { mutableCounts.entries.first().setValue(0) }; immutable { mutableFlags.clear() }
    }
    @Test fun malformedKeysCountsAndSaturationRefuseBeforeEncoding() {
        refuses { LiteRtStatusSnapshot(emptyMap(), emptySet()) }
        refuses { LiteRtStatusSnapshot(snapshot().counts - LiteRtDeclaredStatus.CODE_16, emptySet()) }
        refuses { snapshot(-1) }; refuses { snapshot(1000001) }; refuses { snapshot(1, true) }
        assertNotNull(snapshot(1000000, false).json()); assertNotNull(snapshot(1000000, true).json())
    }
    @Test fun actualCounterOverflowClampsAndFlagsOnlyAfterExactCap() {
        val trace = LiteRtStatusTrace()
        repeat(LiteRtStatusTrace.MAX_COUNT) { trace.record(LiteRtDeclaredStatus.CODE_13) }
        val exact = trace.snapshot()
        assertEquals(1000000, exact.counts.getValue(LiteRtDeclaredStatus.CODE_13)); assertTrue(exact.saturated.isEmpty())
        trace.record(LiteRtDeclaredStatus.CODE_13); trace.record(LiteRtDeclaredStatus.UNRECOGNIZED)
        assertEquals(setOf(LiteRtDeclaredStatus.CODE_13), trace.snapshot().saturated)
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.UNRECOGNIZED)); assertTrue(exact.saturated.isEmpty())
    }
    @Test fun concurrentCountersAndSnapshotsRetainIndependentCountsAndValidWire() {
        val trace = LiteRtStatusTrace(); val pool = Executors.newFixedThreadPool(7); val start = CountDownLatch(1)
        try {
            val jobs = (0..5).map { number -> pool.submit {
                start.await(); repeat(5000) { trace.record(LiteRtDeclaredStatus.entries[number]) }
            } }
            val observer = pool.submit { start.await(); repeat(100) { assertTrue(trace.snapshot().json().length < 2048) } }
            start.countDown(); jobs.forEach { it.get(10, TimeUnit.SECONDS) }; observer.get(10, TimeUnit.SECONDS)
            for (index in 0..5) assertEquals(5000, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.entries[index]))
            assertEquals(0, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.CODE_16))
        } finally { pool.shutdownNow(); assertTrue(pool.awaitTermination(10, TimeUnit.SECONDS)) }
    }
    @Test fun denseWireMatchesIndependentHostFixtureAndPrefixInclusiveCap() {
        val wire = snapshot(1000000, true).json()
        assertTrue(wire.all { it.code in 32..126 }); assertEquals(wire, snapshot(1000000, true).json())
        assertEquals(532, wire.toByteArray(Charsets.US_ASCII).size)
        assertEquals(584, (LiteRtStatusTrace.WIRE_PREFIX + wire).toByteArray(Charsets.US_ASCII).size)
        assertTrue((LiteRtStatusTrace.WIRE_PREFIX + wire).toByteArray(Charsets.UTF_8).size <= LiteRtStatusTrace.MAX_BYTES)
        assertEquals("14007fc5a07f286147fdae2350af4d203b2470d7a9e674d95645dd10e1b574b3",
            MessageDigest.getInstance("SHA-256").digest(wire.toByteArray(Charsets.US_ASCII)).joinToString("") { "%02x".format(it) })
    }
    @Test fun codecSurfaceAcceptsOnlyClosedEnumsWithoutClocksOrPrivateData() {
        assertTrue(LiteRtStatusTrace::class.java.declaredConstructors.all { it.parameterCount == 0 })
        val record = LiteRtStatusTrace::class.java.getDeclaredMethod("record", LiteRtDeclaredStatus::class.java)
        assertEquals(Void.TYPE, record.returnType)
        assertTrue(LiteRtStatusTrace::class.java.declaredFields.none { Throwable::class.java.isAssignableFrom(it.type) ||
            it.type.name.startsWith("java.io.") || it.type.name.startsWith("kotlin.jvm.functions.") || it.type == java.time.Clock::class.java })
        val wire = snapshot().json()
        for (privateKey in listOf("message", "payload", "cause", "stack", "request", "time", "Status Code:")) assertFalse(wire.contains(privateKey))
    }
    @Test fun everyExactDeclaredSdkCodeMapsWithoutEngineOrNativeInitialization() {
        assertTrue(Modifier.isFinal(LiteRtLmJniException::class.java.modifiers))
        for (code in 0..16) {
            val failure = LiteRtLmJniException("Status Code: $code. Message: ")
            assertEquals(LiteRtDeclaredStatus.entries[code], liteRtDeclaredStatus(failure))
        }
    }
    @Test fun arbitraryPayloadIncludingHugePrivateUnicodeDoesNotChangeOrEnterWire() {
        val trace = LiteRtStatusTrace()
        val payloads = listOf("", "PRIVATE_STATUS_CANARY", "\n雪\u0000private", "Status Code: 2. Message: payload", "private".repeat(100000))
        for (payload in payloads) trace.record(liteRtDeclaredStatus(LiteRtLmJniException("Status Code: 13. Message: $payload")))
        assertEquals(payloads.size, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.CODE_13))
        assertEquals(0, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.UNRECOGNIZED))
        val wire = trace.snapshot().json()
        for (privateText in listOf("PRIVATE_STATUS_CANARY", "private", "雪", "Message:", "Status Code:")) assertFalse(wire.contains(privateText))
    }
    @Test fun malformedAndUnknownPrefixesNeverPromoteNearbyNumericRepresentations() {
        for (message in listOf("", "Status Code: 17. Message: private", "Status Code: -1. Message: private",
            "Status Code: +1. Message: private", "Status Code: 01. Message: private", "Status Code: 016. Message: private",
            " Status Code: 1. Message: private", "\nStatus Code: 1. Message: private", "status Code: 1. Message: private",
            "Status Code: 1.Message: private", "Status Code: 1. Message:private", "Status Code: 1. message: private",
            "Status Code: 1. Message:", "Status Code: 1x. Message: private", "Status Code: 100. Message: private",
            "Status Code: ١. Message: private", "{\"code\":13}", "Status Code: 1 . Message: private"))
            assertEquals(LiteRtDeclaredStatus.UNRECOGNIZED, liteRtDeclaredStatus(LiteRtLmJniException(message)))
    }
    @Test fun foreignThrowablesAndHostileAccessorsAreNeverInspected() {
        val hostile = HostileFailure()
        assertEquals(LiteRtDeclaredStatus.UNRECOGNIZED, liteRtDeclaredStatus(hostile)); assertEquals(0, hostile.reads)
        assertEquals(LiteRtDeclaredStatus.UNRECOGNIZED, liteRtDeclaredStatus(IllegalStateException("Status Code: 13. Message: private")))
        assertEquals(LiteRtDeclaredStatus.UNRECOGNIZED, liteRtDeclaredStatus(CancellationException("Status Code: 1. Message: private")))
    }
    @Test fun wrappedSdkCauseAndHostileCancellationRemainUnrecognizedWithoutAccess() {
        val sdk = LiteRtLmJniException("Status Code: 13. Message: private")
        assertEquals(LiteRtDeclaredStatus.UNRECOGNIZED, liteRtDeclaredStatus(RuntimeException("Status Code: 13. Message: private", sdk)))
        var accesses = 0
        val cancellation = object : CancellationException() {
            override val message: String get() { accesses++; error("Must not inspect foreign message") }
            override val cause: Throwable? get() { accesses++; return sdk }
            override fun toString(): String { accesses++; error("Must not inspect description") }
        }
        assertEquals(LiteRtDeclaredStatus.UNRECOGNIZED, liteRtDeclaredStatus(cancellation)); assertEquals(0, accesses)
    }
    @Test fun zeroAndOneAreDeclaredDataNotSuccessOrAcknowledgement() {
        assertEquals(LiteRtDeclaredStatus.CODE_0, liteRtDeclaredStatus(LiteRtLmJniException("Status Code: 0. Message: private failure")))
        assertEquals(LiteRtDeclaredStatus.CODE_1, liteRtDeclaredStatus(LiteRtLmJniException("Status Code: 1. Message: private failure")))
        assertEquals(LiteRtDeclaredStatus.UNRECOGNIZED, liteRtDeclaredStatus(LiteRtLmJniException("Message: Status Code: 0. Message: private")))
    }
}
