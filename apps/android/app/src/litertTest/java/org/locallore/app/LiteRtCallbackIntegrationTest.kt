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

/** Original tiny files and fake resources only. No SDK engine, native library or real model. */
class LiteRtCallbackIntegrationTest {
    @get:Rule val temporary = TemporaryFolder()
    private val request = LocalInferenceRequest(1, "director", "original café", 350, 4096, 4, "{\"type\":\"object\"}")
    private class PrivateFailure : RuntimeException() {
        override val message: String get() = error("Private message accessor must not run")
        override val cause: Throwable get() = error("Private cause accessor must not run")
        override fun toString(): String = error("Private rendering must not run")
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
        val model = File(root, "original-four-bytes.litertlm").also { it.writeBytes(byteArrayOf(1, 2, 3, 4)) }
        val cache = File(root, "scratch").also { check(it.mkdir()) }
        val hash = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
        return LiteRtWorkerConfig(root, model, cache, 4, hash, "a".repeat(64), "b".repeat(64), "c".repeat(64), deadlineMs = 500)
    }
    private suspend fun uncertain(block: suspend () -> Unit) {
        try { block(); fail("Unknown resources must refuse") } catch (_: LocalInferenceUncertain) { }
    }
    @Test fun closedTypeClassificationNeverReadsPrivateAccessors() {
        assertEquals(LiteRtCallbackError.OTHER, liteRtCallbackError(PrivateFailure()))
        assertEquals(LiteRtCallbackError.CANCELLED, liteRtCallbackError(CancellationException("original private cancellation")))
        assertEquals(LiteRtCallbackError.SDK_JNI, liteRtCallbackError(LiteRtLmJniException("original private native error")))
    }
    @Test fun originalErrorRunsFirstAndItsExactFailureSurvivesDiagnosticFailure() {
        val original = PrivateFailure(); val order = mutableListOf<String>()
        val callbacks = object : LiteRtCallbacks {
            override fun message(read: () -> LiteRtChunk) = error("Unused")
            override fun done() = error("Unused")
            override fun error(cancelled: Boolean) { assertFalse(cancelled); order += "fence"; throw original }
            override fun errorCategory(category: LiteRtCallbackError) {
                assertEquals(listOf("fence"), order); assertEquals(LiteRtCallbackError.SDK_JNI, category)
                order += "observation"; throw PrivateFailure()
            }
        }
        try { observedLiteRtError(LiteRtLmJniException("synthetic"), callbacks); fail("Original must throw") }
        catch (caught: Throwable) { assertSame(original, caught) }
        assertEquals(listOf("fence", "observation"), order)
    }
    @Test fun configuredLengthsAndAcceptedUtf8BytesFollowTheActualWorker() = runBlocking {
        val trace = LiteRtCallbackTrace(); val resources = Resources()
        resources.send = { it.message { LiteRtChunk(text = listOf("é", "🌊")) }; it.message { LiteRtChunk() }; it.done() }
        val engine = LiteRtRoleWorker(config(), resources, callbackTrace = trace).open()
        val call = engine.start(request)
        assertArrayEquals(localUtf8("é🌊"), call.await().response())
        assertTrue(call.drain()); assertTrue(call.close()); assertTrue(engine.close())
        val value = trace.snapshot().calls.single()
        assertEquals(LiteRtCallbackRole.DIRECTOR, value.role)
        assertEquals(4096, value.contextTokens); assertEquals(350, value.maxOutputTokens)
        assertEquals(localUtf8(request.prompt).size, value.promptBytes)
        assertEquals(localUtf8(request.schemaJson).size, value.schemaBytes)
        assertEquals(2, value.counts.getValue(LiteRtCallbackCounter.OUTPUT_CHUNKS))
        assertEquals(6, value.counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
        assertEquals(1, value.counts.getValue(LiteRtCallbackCounter.DONE))
        assertEquals(1, resources.childCloses.get()); assertEquals(1, resources.parentCloses.get())
    }
    @Test fun invalidChunkPathsNeverInflateAcceptedOutputOrReleaseUnknownResources() = runBlocking {
        val invalid = listOf(
            LiteRtChunk(nonText = true, text = listOf("private")), LiteRtChunk(tools = true),
            LiteRtChunk(channels = true), LiteRtChunk(modelRole = false),
            LiteRtChunk(text = listOf("\uD800")), LiteRtChunk(text = listOf("<think>private</think>")),
            LiteRtChunk(text = listOf("x".repeat(16_385))),
        )
        for (chunk in invalid) {
            val trace = LiteRtCallbackTrace(); val resources = Resources()
            resources.send = { it.message { LiteRtChunk(text = listOf("ok")) }; it.message { chunk }; it.done() }
            val engine = LiteRtRoleWorker(config(), resources, callbackTrace = trace).open()
            val call = engine.start(request)
            uncertain { call.await() }; assertFalse(call.drain()); assertFalse(call.close()); assertFalse(engine.close())
            val counts = trace.snapshot().calls.single().counts
            assertEquals(1, counts.getValue(LiteRtCallbackCounter.OUTPUT_CHUNKS))
            assertEquals(2, counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
            assertEquals(0, resources.childCloses.get()); assertEquals(0, resources.parentCloses.get())
        }
    }
    @Test fun requestedCancellationKeepsTheExistingKnownDrainAndCloseContract() = runBlocking {
        val trace = LiteRtCallbackTrace(); val resources = Resources()
        resources.cancel = { observedLiteRtError(CancellationException("synthetic cancellation"), it) }
        val engine = LiteRtRoleWorker(config(), resources, callbackTrace = trace).open()
        val call = engine.start(request); call.cancel()
        assertTrue(call.await().terminal); assertTrue(call.drain()); assertTrue(call.close()); assertTrue(engine.close())
        val counts = trace.snapshot().calls.single().counts
        assertEquals(1, counts.getValue(LiteRtCallbackCounter.CANCELLED))
        assertEquals(0, counts.getValue(LiteRtCallbackCounter.SDK_JNI)); assertEquals(0, counts.getValue(LiteRtCallbackCounter.DONE))
    }
    @Test fun lateMessageCannotEnterAcceptedCountsOrRecoverAClosedCall() = runBlocking {
        val trace = LiteRtCallbackTrace(); val resources = Resources()
        resources.send = { it.message { LiteRtChunk(text = listOf("ok")) }; it.done() }
        val engine = LiteRtRoleWorker(config(), resources, callbackTrace = trace).open()
        val call = engine.start(request)
        assertTrue(call.await().terminal); assertTrue(call.drain()); assertTrue(call.close()); assertTrue(engine.close())
        resources.callbacks.message { fail("Late content must never be inspected"); LiteRtChunk() }
        val counts = trace.snapshot().calls.single().counts
        assertEquals(1, counts.getValue(LiteRtCallbackCounter.OUTPUT_CHUNKS))
        assertEquals(2, counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES))
        assertFalse(call.close()); assertFalse(engine.close())
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
    @Test fun sdkErrorsFenceTheSameOwnerBeforeCategoryAndCannotDeliverCommitOrReuse() = runBlocking {
        for (failure in listOf(LiteRtLmJniException("synthetic native failure"), CancellationException("unrequested"), PrivateFailure())) {
            val trace = LiteRtCallbackTrace(); val resources = Resources(); val port = Port(request)
            lateinit var owner: LocalInferenceOwner
            resources.send = { callbacks ->
                observedLiteRtError(failure, object : LiteRtCallbacks {
                    override fun message(read: () -> LiteRtChunk) = callbacks.message(read)
                    override fun done() = callbacks.done()
                    override fun error(cancelled: Boolean) = callbacks.error(cancelled)
                    override fun errorCategory(category: LiteRtCallbackError) {
                        try { owner.assertBorrowable(); fail("Fence must precede diagnostic") } catch (_: LocalInferenceUncertain) { }
                        callbacks.errorCategory(category)
                    }
                })
            }
            owner = config().createOwner(LocalInferenceLimits(500, 200, 2), resources, callbackTrace = trace)
            try {
                uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
                assertTrue(owner.quarantined); assertTrue(owner.nativeInvalidatedKnown)
                uncertain { owner.execute(port, "commit", "commit".toByteArray()) }
                uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
                assertEquals(0, port.deliveries.get()); assertEquals(0, port.commits.get()); assertEquals(1, resources.creates.get())
                val counts = trace.snapshot().calls.single().counts
                assertEquals(1, counts.getValue(LiteRtCallbackCounter.valueOf(liteRtCallbackError(failure).name)))
            } finally { owner.close() }
            assertEquals(0, resources.childCloses.get()); assertEquals(0, resources.parentCloses.get())
        }
    }
}
