/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Test

/** Pure ownership controls, never native/model execution or canonical acceptance evidence. */
class AuthorResponseOwnerTest {
    private val author = LocalInferenceRequest(1, "author", "SYNTHETIC author request", 1024, 4096, 4, "{}")
    private class Port(request: LocalInferenceRequest) : LocalInferenceNativePort {
        val pending = AtomicReference<LocalInferencePending?>(LocalInferencePending(7, request))
        val terminal = CountDownLatch(1)
        val deliveries = AtomicInteger()
        val cancellations = AtomicInteger()
        val closes = AtomicInteger()
        var accepted: ByteArray? = null
        var acknowledge = true
        var reply = "native-rejected-proposal"
        var onRespond: (() -> Unit)? = null
        override fun call(input: ByteArray): ByteArray = when (input.toString(Charsets.UTF_8)) {
            "generate" -> { check(terminal.await(4, TimeUnit.SECONDS)); reply.toByteArray() }
            "cancel" -> { cancellations.incrementAndGet(); invalidate(); "cancelled".toByteArray() }
            else -> "read".toByteArray()
        }
        fun invalidate() { pending.set(null); terminal.countDown() }
        override fun poll() = pending.get()
        override fun respond(ticket: Long, response: ByteArray): Boolean {
            check(ticket == 7L)
            deliveries.incrementAndGet()
            if (acknowledge) accepted = response.copyOf()
            response.fill(0) // The port's argument cannot mutate the observed original response.
            onRespond?.invoke()
            invalidate()
            return acknowledge
        }
        override fun close() { closes.incrementAndGet(); invalidate() }
    }
    private class Call : LocalRoleCall {
        val entered = CompletableDeferred<Unit>()
        val output = CompletableDeferred<LocalRoleResult>()
        val closeGate = CompletableDeferred<Boolean>().also { it.complete(true) }
        val drains = AtomicInteger()
        val closes = AtomicInteger()
        var drained = true
        override suspend fun await(): LocalRoleResult { entered.complete(Unit); return output.await() }
        override fun cancel() { output.complete(LocalRoleResult(true, byteArrayOf())) }
        override suspend fun drain(): Boolean { drains.incrementAndGet(); return drained }
        override suspend fun close(): Boolean { closes.incrementAndGet(); return closeGate.await() }
    }
    private class Engine(val call: Call) : LocalRoleEngine {
        val closes = AtomicInteger()
        var closedKnown = true
        override suspend fun start(request: LocalInferenceRequest): LocalRoleCall = call
        override suspend fun close(): Boolean { closes.incrementAndGet(); return closedKnown }
    }
    private fun newOwner(engine: LocalRoleEngine) = LocalInferenceOwner("{}".toByteArray(), LocalRoleWorker { engine }, Dispatchers.Default,
        LocalInferenceLimits(turnMs = 2_000, cleanupMs = 500, pollMs = 2, authorMs = 2_000))
    private suspend fun generate(owner: LocalInferenceOwner, port: Port, author: Boolean = true) =
        owner.execute(port, if (author) "authoring_generate" else "prepare", "generate".toByteArray(), "cancel".toByteArray())
    private fun unavailable(block: () -> Unit) {
        try { block(); fail("Capture installation must be refused") }
        catch (_: IllegalStateException) { }
    }
    private fun empty(capture: AuthorResponseCapture) {
        assertEquals(AuthorResponseCaptureState.EMPTY, capture.snapshot().state)
        assertEquals(0, capture.snapshot().calls)
        assertNull(capture.snapshot().responseBytes())
    }
    private suspend fun eventually(test: () -> Boolean) = withTimeout(2_000) { while (!test()) delay(2) }

    @Test fun explicitOptInPreservesNativeReplyAndRecordsExactAcknowledgedProposal() = runBlocking {
        for (enabled in listOf(false, true)) {
            val call = Call(); val engine = Engine(call); val port = Port(author); val owner = newOwner(engine)
            val capture = if (enabled) owner.installAuthorResponseCapture() else null
            val bytes = "SYNTHETIC not JSON; Rust may reject this unchanged".toByteArray()
            call.output.complete(LocalRoleResult(true, bytes))
            assertEquals("native-rejected-proposal", generate(owner, port).toString(Charsets.UTF_8))
            assertArrayEquals(bytes, port.accepted)
            assertEquals(1, port.deliveries.get()); assertEquals(1, call.drains.get()); assertEquals(1, call.closes.get()); assertEquals(1, engine.closes.get())
            assertFalse(owner.quarantined)
            capture?.let {
                assertEquals(AuthorResponseCaptureState.RECORDED, it.snapshot().state)
                assertEquals(1, it.snapshot().calls)
                assertArrayEquals(bytes, it.snapshot().responseBytes())
                port.accepted!!.fill(1); it.snapshot().responseBytes()!!.fill(2)
                assertArrayEquals(bytes, it.snapshot().responseBytes())
            }
            unavailable { owner.installAuthorResponseCapture() }
            owner.close()
        }
    }

    @Test fun installationIsSingleAndRequiresAnUnattachedOpenOwner() = runBlocking {
        val fresh = newOwner(Engine(Call()))
        fresh.installAuthorResponseCapture(); unavailable { fresh.installAuthorResponseCapture() }; fresh.close()
        val closed = newOwner(Engine(Call())); closed.close(); unavailable { closed.installAuthorResponseCapture() }
        val claimed = newOwner(Engine(Call())); claimed.claimTransport(Any()); unavailable { claimed.installAuthorResponseCapture() }; claimed.close()
        val attached = newOwner(Engine(Call())); attached.attach(Port(author)); unavailable { attached.installAuthorResponseCapture() }; attached.close()
        val bound = newOwner(Engine(Call())); val port = Port(author)
        assertEquals("read", bound.execute(port, "workspace", "read".toByteArray()).toString(Charsets.UTF_8))
        unavailable { bound.installAuthorResponseCapture() }; bound.close()
    }

    @Test fun activeOrQuarantinedOwnersCannotInstallAnotherCollector() = runBlocking {
        val call = Call(); val port = Port(author); val owner = newOwner(Engine(call))
        val running = async { generate(owner, port) }
        call.entered.await(); unavailable { owner.installAuthorResponseCapture() }
        port.invalidate(); running.await(); owner.close()
        val badCall = Call().also { it.output.complete(LocalRoleResult(true, ByteArray(8193))) }
        val poisoned = newOwner(Engine(badCall)); val badPort = Port(author)
        try { generate(poisoned, badPort); fail() } catch (_: LocalInferenceUncertain) { }
        assertTrue(poisoned.quarantined); unavailable { poisoned.installAuthorResponseCapture() }; poisoned.close()
    }

    @Test fun directorAndNarratorRepliesDoNotReachTheAuthorCollector() = runBlocking {
        for (role in listOf("director", "narrator")) {
            val call = Call().also { it.output.complete(LocalRoleResult(true, "SYNTHETIC play reply".toByteArray())) }
            val owner = newOwner(Engine(call)); val port = Port(author.copy(role = role, maxTokens = 220))
            val capture = owner.installAuthorResponseCapture()
            generate(owner, port, author = false)
            empty(capture); assertEquals(1, port.deliveries.get()); assertFalse(owner.quarantined); owner.close()
        }
    }

    @Test fun falseBridgeAcknowledgementAndStaleTicketCaptureNothing() = runBlocking {
        val call = Call().also { it.output.complete(LocalRoleResult(true, "SYNTHETIC response".toByteArray())) }
        val owner = newOwner(Engine(call)); val capture = owner.installAuthorResponseCapture(); val port = Port(author).also { it.acknowledge = false }
        generate(owner, port); empty(capture); assertEquals(1, port.deliveries.get()); assertFalse(owner.quarantined); owner.close()
        val staleCall = Call(); val staleOwner = newOwner(Engine(staleCall)); val staleCapture = staleOwner.installAuthorResponseCapture(); val stalePort = Port(author)
        val running = async { generate(staleOwner, stalePort) }
        staleCall.entered.await(); stalePort.invalidate(); running.await()
        empty(staleCapture); assertEquals(0, stalePort.deliveries.get()); staleOwner.close()
    }

    @Test fun explicitCancellationBeforeAResponseLeavesTheCaptureEmpty() = runBlocking {
        val call = Call(); val owner = newOwner(Engine(call)); val capture = owner.installAuthorResponseCapture(); val port = Port(author)
        val running = async { generate(owner, port) }
        call.entered.await()
        val cancelled = async { owner.execute(port, "authoring_cancel", "cancel".toByteArray()) }
        running.await(); cancelled.await()
        empty(capture); assertEquals(0, port.deliveries.get()); assertTrue(port.cancellations.get() > 0)
        assertFalse(owner.quarantined); owner.close()
    }

    @Test fun invalidDiagnosticStateCannotChangeTheSubmittedBytesOrNativeOutcome() = runBlocking {
        val bytes = "SYNTHETIC unchanged proposed bytes".toByteArray()
        val call = Call().also { it.output.complete(LocalRoleResult(true, bytes)) }
        val owner = newOwner(Engine(call)); val capture = owner.installAuthorResponseCapture(); val port = Port(author)
        capture.observe("author", ByteArray(8193))
        assertEquals("native-rejected-proposal", generate(owner, port).toString(Charsets.UTF_8))
        assertArrayEquals(bytes, port.accepted); assertFalse(owner.quarantined)
        assertEquals(AuthorResponseCaptureState.DUPLICATE, capture.snapshot().state)
        assertEquals(2, capture.snapshot().calls); assertNull(capture.snapshot().responseBytes()); owner.close()
    }

    @Test fun malformedOversizedNonterminalOrUndrainedRepliesAreNeverObserved() = runBlocking {
        for (result in listOf(LocalRoleResult(true, byteArrayOf(0xc3.toByte(), 0x28)), LocalRoleResult(true, ByteArray(8193)),
            LocalRoleResult(false, "SYNTHETIC partial".toByteArray()))) {
            val call = Call().also { it.output.complete(result) }; val owner = newOwner(Engine(call)); val capture = owner.installAuthorResponseCapture(); val port = Port(author)
            try { generate(owner, port); fail() } catch (_: LocalInferenceUncertain) { }
            empty(capture); assertEquals(0, port.deliveries.get()); assertTrue(owner.quarantined); owner.close()
        }
        val undrained = Call().also { it.drained = false; it.output.complete(LocalRoleResult(true, "SYNTHETIC complete".toByteArray())) }
        val owner = newOwner(Engine(undrained)); val capture = owner.installAuthorResponseCapture(); val port = Port(author)
        try { generate(owner, port); fail() } catch (_: LocalInferenceUncertain) { }
        empty(capture); assertEquals(0, port.deliveries.get()); assertTrue(owner.quarantined); owner.close()
    }

    @Test fun captureWaitsForKnownRoleCloseAndCloseBeforeTheHookPreventsObservation() = runBlocking {
        val call = Call().also { it.output.complete(LocalRoleResult(true, "SYNTHETIC response".toByteArray())) }
        val closeGate = CompletableDeferred<Boolean>()
        val gated = object : LocalRoleCall {
            override suspend fun await() = call.await()
            override fun cancel() = call.cancel()
            override suspend fun drain() = call.drain()
            override suspend fun close(): Boolean { call.closes.incrementAndGet(); return closeGate.await() }
        }
        val engine = object : LocalRoleEngine { override suspend fun start(request: LocalInferenceRequest) = gated; override suspend fun close() = true }
        val owner = newOwner(engine); val capture = owner.installAuthorResponseCapture(); val port = Port(author)
        val running = async { generate(owner, port) }
        eventually { call.closes.get() == 1 }; empty(capture); assertEquals(0, port.deliveries.get())
        closeGate.complete(true); running.await(); assertEquals(AuthorResponseCaptureState.RECORDED, capture.snapshot().state); owner.close()
        val closedCall = Call().also { it.output.complete(LocalRoleResult(true, "SYNTHETIC closed".toByteArray())) }
        val closedOwner = newOwner(Engine(closedCall)); val closedCapture = closedOwner.installAuthorResponseCapture()
        val closedPort = Port(author).also { it.onRespond = { closedOwner.close() } }
        try { generate(closedOwner, closedPort); fail() } catch (_: CancellationException) { }
        empty(closedCapture); assertEquals(1, closedPort.deliveries.get())
    }

    @Test fun anAcknowledgedObservationSurvivesALaterEngineCloseFailure() = runBlocking {
        val bytes = "SYNTHETIC acknowledged proposal".toByteArray()
        val call = Call().also { it.output.complete(LocalRoleResult(true, bytes)) }
        val engine = Engine(call).also { it.closedKnown = false }; val owner = newOwner(engine); val capture = owner.installAuthorResponseCapture(); val port = Port(author)
        try { generate(owner, port); fail() } catch (_: LocalInferenceUncertain) { }
        assertTrue(owner.quarantined); assertEquals(1, port.deliveries.get())
        assertEquals(AuthorResponseCaptureState.RECORDED, capture.snapshot().state)
        assertArrayEquals(bytes, capture.snapshot().responseBytes()); owner.close()
    }
}
