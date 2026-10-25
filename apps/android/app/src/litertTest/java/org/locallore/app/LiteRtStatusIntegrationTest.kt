/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import com.google.ai.edge.litertlm.LiteRtLmJniException
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.CancellationException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Tiny original files, fake SDK-neutral resources and synthetic errors only. No SDK engine. */
class LiteRtStatusIntegrationTest {
    @get:Rule val temporary = TemporaryFolder()
    private val request = LocalInferenceRequest(1, "director", "original synthetic prompt", 350, 4096, 4, "{}")
    private class PrivateFailure : RuntimeException() {
        override val message: String get() = error("Private getter must not run")
        override val cause: Throwable get() = error("Private cause must not run")
        override fun toString(): String = error("Private rendering must not run")
    }
    private fun sdk(code: Int) = LiteRtLmJniException("Status Code: $code. Message: original private test payload")
    private fun assertZero(trace: LiteRtStatusTrace) = assertTrue(trace.snapshot().counts.values.all { it == 0 })

    @Test fun booleanAndOldCategoryPrecedeStatusAndOriginalFailureIdentitySurvives() {
        val trace = LiteRtStatusTrace(); val original = PrivateFailure(); val order = mutableListOf<String>()
        val callbacks = object : LiteRtCallbacks {
            override fun message(read: () -> LiteRtChunk) = error("Unused")
            override fun done() = error("Unused")
            override fun error(cancelled: Boolean) { assertFalse(cancelled); assertZero(trace); order += "fence"; throw original }
            override fun errorCategory(category: LiteRtCallbackError) {
                assertEquals(listOf("fence"), order); assertZero(trace)
                assertEquals(LiteRtCallbackError.SDK_JNI, category); order += "category"; throw PrivateFailure()
            }
        }
        try { observedLiteRtError(sdk(13), callbacks, trace); fail("Original callback must throw") }
        catch (caught: Throwable) { assertSame(original, caught) }
        assertEquals(listOf("fence", "category"), order)
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.CODE_13))
        assertEquals(1, trace.snapshot().counts.values.sum())
    }
    @Test fun disabledTracePreservesOriginalCallbackAndForeignAccessorsStayUnread() {
        for (trace in listOf(null, LiteRtStatusTrace())) {
            var calls = 0
            val callbacks = object : LiteRtCallbacks {
                override fun message(read: () -> LiteRtChunk) = error("Unused")
                override fun done() = error("Unused")
                override fun error(cancelled: Boolean) { assertFalse(cancelled); calls++ }
            }
            observedLiteRtError(PrivateFailure(), callbacks, trace); assertEquals(1, calls)
            if (trace != null) assertEquals(1, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.UNRECOGNIZED))
        }
    }
    private class Resources : LiteRtResources {
        var send: (LiteRtCallbacks) -> Unit = {}
        var cancel: (LiteRtCallbacks) -> Unit = {}
        lateinit var callbacks: LiteRtCallbacks
        val creates = AtomicInteger(); val childCloses = AtomicInteger(); val parentCloses = AtomicInteger()
        override fun engine(paths: LiteRtPaths): LiteRtEngineResource {
            creates.incrementAndGet()
            return object : LiteRtEngineResource {
                override fun initialize() = Unit
                override fun conversation(request: LocalInferenceRequest): LiteRtConversationResource = object : LiteRtConversationResource {
                    override fun send(request: LocalInferenceRequest, callbacks: LiteRtCallbacks) {
                        this@Resources.callbacks = callbacks; this@Resources.send(callbacks)
                    }
                    override fun cancel() = this@Resources.cancel(callbacks)
                    override fun close(): Boolean { childCloses.incrementAndGet(); return true }
                }
                override fun close(): Boolean { parentCloses.incrementAndGet(); return true }
            }
        }
    }
    private fun config(): LiteRtWorkerConfig {
        val root = temporary.newFolder()
        val model = File(root, "original-four-byte.litertlm").also { it.writeBytes(byteArrayOf(1, 2, 3, 4)) }
        val cache = File(root, "scratch").also { check(it.mkdir()) }
        val hash = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
        return LiteRtWorkerConfig(root, model, cache, 4, hash, "a".repeat(64), "b".repeat(64), "c".repeat(64), deadlineMs = 500)
    }
    private class Port(request: LocalInferenceRequest) : LocalInferenceNativePort {
        private val pending = AtomicReference<LocalInferencePending?>(LocalInferencePending(1, request))
        private val terminal = CountDownLatch(1)
        val deliveries = AtomicInteger(); val commits = AtomicInteger()
        override fun call(input: ByteArray): ByteArray = when (input.toString(Charsets.UTF_8)) {
            "prepare" -> { check(terminal.await(2, TimeUnit.SECONDS)); "cancelled".toByteArray() }
            "cancel" -> { close(); "cancelled".toByteArray() }
            "commit" -> { commits.incrementAndGet(); "committed".toByteArray() }
            else -> error("Unexpected synthetic operation")
        }
        override fun poll(): LocalInferencePending? = pending.get()
        override fun respond(ticket: Long, response: ByteArray): Boolean { deliveries.incrementAndGet(); close(); return true }
        override fun close() { pending.set(null); terminal.countDown() }
    }
    private suspend fun uncertain(block: suspend () -> Unit) {
        try { block(); fail("An uncertain owner must refuse") } catch (_: LocalInferenceUncertain) { }
    }
    @Test fun everyDeclaredCodeAndUnknownRetainTheRealWorkerOwnerFence() = runBlocking {
        val cases = (0..16).map { sdk(it) to LiteRtDeclaredStatus.valueOf("CODE_$it") } + listOf(
            sdk(17) to LiteRtDeclaredStatus.UNRECOGNIZED,
            CancellationException("Status Code: 13. Message: private") to LiteRtDeclaredStatus.UNRECOGNIZED,
            PrivateFailure() to LiteRtDeclaredStatus.UNRECOGNIZED,
        )
        for ((failure, expected) in cases) {
            val trace = LiteRtStatusTrace(); val resources = Resources(); val port = Port(request)
            lateinit var owner: LocalInferenceOwner
            resources.send = { callbacks -> observedLiteRtError(failure, object : LiteRtCallbacks {
                override fun message(read: () -> LiteRtChunk) = callbacks.message(read)
                override fun done() = callbacks.done()
                override fun error(cancelled: Boolean) = callbacks.error(cancelled)
                override fun errorCategory(category: LiteRtCallbackError) {
                    try { owner.assertBorrowable(); fail("Original fence must precede metadata") } catch (_: LocalInferenceUncertain) { }
                    assertZero(trace); callbacks.errorCategory(category)
                }
            }, trace) }
            owner = config().createOwner(LocalInferenceLimits(500, 200, 2), resources, statusTrace = trace)
            try {
                uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
                assertTrue(owner.quarantined); assertTrue(owner.nativeInvalidatedKnown)
                assertEquals(1, trace.snapshot().counts.getValue(expected)); assertEquals(1, trace.snapshot().counts.values.sum())
                uncertain { owner.execute(port, "commit", "commit".toByteArray()) }
                uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
                assertEquals(0, port.deliveries.get()); assertEquals(0, port.commits.get()); assertEquals(1, resources.creates.get())
            } finally { owner.close() }
            assertEquals(0, resources.childCloses.get()); assertEquals(0, resources.parentCloses.get())
        }
    }
    @Test fun requestedCancellationStillDrainsAndClosesWithoutClaimingPrefixCodeOne() = runBlocking {
        val trace = LiteRtStatusTrace(); val resources = Resources()
        resources.cancel = { observedLiteRtError(CancellationException("synthetic cancellation"), it, trace) }
        val engine = LiteRtRoleWorker(config(), resources).open()
        val call = engine.start(request); call.cancel()
        assertTrue(call.await().terminal); assertTrue(call.drain()); assertTrue(call.close()); assertTrue(engine.close())
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.UNRECOGNIZED))
        assertEquals(0, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.CODE_1))
    }
    @Test fun normalDoneAndLateErrorCannotTurnADeclaredOkIntoReleaseAuthority() = runBlocking {
        val trace = LiteRtStatusTrace(); val resources = Resources()
        resources.send = { it.message { LiteRtChunk(text = listOf("ok")) }; it.done() }
        val engine = LiteRtRoleWorker(config(), resources).open()
        val call = engine.start(request); assertTrue(call.await().terminal)
        assertTrue(call.drain()); assertTrue(call.close()); assertTrue(engine.close()); assertZero(trace)
        observedLiteRtError(sdk(0), resources.callbacks, trace)
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtDeclaredStatus.CODE_0))
        uncertain { call.await() }; assertFalse(call.close()); assertFalse(engine.close())
    }
}
