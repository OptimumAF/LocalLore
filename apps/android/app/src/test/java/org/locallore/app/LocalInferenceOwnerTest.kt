/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Test

class LocalInferenceOwnerTest {
    private val request = LocalInferenceRequest(1, "director", "original prompt", 350, 4096, 4, "{\"type\":\"object\"}")
    private val limits = LocalInferenceLimits(turnMs = 1_000, cleanupMs = 300, pollMs = 2)
    private open class Port(request: LocalInferenceRequest) : LocalInferenceNativePort {
        val pending = AtomicReference<LocalInferencePending?>(LocalInferencePending(7, request))
        val nativeEntered = CountDownLatch(1)
        private val terminal = CountDownLatch(1)
        val closes = AtomicInteger()
        val commits = AtomicInteger()
        val deliveries = AtomicInteger()
        val cancels = AtomicInteger()
        val accepted = mutableListOf<ByteArray>()
        @Volatile var reply = "ready"
        @Volatile var repeatTicket = false
        @Volatile var rejectResponse = false
        @Volatile var calledThread: String? = null
        override fun call(input: ByteArray): ByteArray {
            calledThread = Thread.currentThread().name
            return when (input.toString(Charsets.UTF_8)) {
                "prepare" -> {
                    nativeEntered.countDown()
                    check(terminal.await(5, TimeUnit.SECONDS)) { "Synthetic native owner did not terminate" }
                    reply.toByteArray()
                }
                "cancel" -> { cancels.incrementAndGet(); invalidate(); "ok".toByteArray() }
                "commit" -> { commits.incrementAndGet(); "committed".toByteArray() }
                else -> "ok".toByteArray()
            }
        }
        fun invalidate() { pending.set(null); reply = "cancelled"; terminal.countDown() }
        override fun poll(): LocalInferencePending? = pending.get()
        override fun respond(ticket: Long, response: ByteArray): Boolean {
            deliveries.incrementAndGet()
            if (rejectResponse || pending.get()?.ticket != ticket) return false
            synchronized(accepted) { accepted += response.copyOf() }
            if (!repeatTicket) { pending.set(null); terminal.countDown() }
            return true
        }
        override fun close() { closes.incrementAndGet(); invalidate() }
    }
    private open class Call : LocalRoleCall {
        val entered = CompletableDeferred<Unit>()
        val output = CompletableDeferred<LocalRoleResult>()
        val closeGate = CompletableDeferred<Boolean>().also { it.complete(true) }
        val cancels = AtomicInteger()
        val drains = AtomicInteger()
        val closes = AtomicInteger()
        var drained = true
        var closeError = false
        override suspend fun await(): LocalRoleResult { entered.complete(Unit); return output.await() }
        override fun cancel() { cancels.incrementAndGet(); output.complete(LocalRoleResult(true, byteArrayOf())) }
        override suspend fun drain(): Boolean { drains.incrementAndGet(); return drained }
        override suspend fun close(): Boolean {
            closes.incrementAndGet()
            if (closeError) throw AssertionError("private role close diagnostic")
            return closeGate.await()
        }
        fun success(bytes: ByteArray = "{\"ok\":true}".toByteArray()) { output.complete(LocalRoleResult(true, bytes)) }
    }
    private open class Engine(val call: Call) : LocalRoleEngine {
        val starts = AtomicInteger()
        val closes = AtomicInteger()
        val closeGate = CompletableDeferred<Boolean>().also { it.complete(true) }
        var received: LocalInferenceRequest? = null
        override suspend fun start(request: LocalInferenceRequest): LocalRoleCall {
            received = request; starts.incrementAndGet(); return call
        }
        override suspend fun close(): Boolean { closes.incrementAndGet(); return closeGate.await() }
    }
    private fun owner(engine: LocalRoleEngine, bounds: LocalInferenceLimits = limits) =
        LocalInferenceOwner("{}".toByteArray(), LocalRoleWorker { engine }, Dispatchers.Default, bounds)
    private suspend fun prepare(owner: LocalInferenceOwner, port: Port) =
        owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray())
    private suspend fun eventually(check: () -> Boolean) = withTimeout(2_000) { while (!check()) delay(2) }
    private suspend fun refused(owner: LocalInferenceOwner, port: Port, operation: String = "commit") {
        try { owner.execute(port, operation, operation.toByteArray(), if (operation == "prepare") "cancel".toByteArray() else null); fail("uncertain owner accepted $operation") }
        catch (expected: LocalInferenceUncertain) {
            assertEquals("Local inference ownership uncertain", expected.message)
            assertNull(expected.cause)
        }
        catch (expected: LocalInferenceBusy) { assertEquals("Local inference busy", expected.message); assertNull(expected.cause) }
    }

    @Test fun immutableRequestAndCopiedTerminalResponseDeliverOnlyOnceOffCallerThread() = runBlocking {
        val call = Call(); val engine = Engine(call); val port = Port(request); val owner = owner(engine)
        val caller = Thread.currentThread().name
        val response = "{\"ok\":true}".toByteArray()
        val result = LocalRoleResult(true, response)
        response.fill(0)
        val exposed = result.response(); exposed.fill(1)
        call.output.complete(result)
        assertEquals("ready", prepare(owner, port).toString(Charsets.UTF_8))
        assertEquals(request, engine.received)
        assertEquals("{\"ok\":true}", port.accepted.single().toString(Charsets.UTF_8))
        assertEquals(1, port.deliveries.get()); assertEquals(1, call.drains.get()); assertEquals(1, call.closes.get())
        assertEquals(1, engine.closes.get()); assertNotEquals(caller, port.calledThread)
        owner.execute(port, "commit", "commit".toByteArray())
        assertEquals(1, port.commits.get()); assertFalse(owner.quarantined)
        owner.close(); eventually { owner.nativeInvalidatedKnown }
    }

    @Test fun engineCloseMustFinishBeforeReadyOrCommit() = runBlocking {
        val gate = CompletableDeferred<Boolean>()
        val call = Call().also { it.success() }
        val engine = object : Engine(call) {
            override suspend fun close(): Boolean { closes.incrementAndGet(); return gate.await() }
        }
        val port = Port(request); val owner = owner(engine)
        val result = async { prepare(owner, port) }
        eventually { engine.closes.get() == 1 }
        assertFalse(result.isCompleted)
        refused(owner, port)
        assertEquals(0, port.commits.get())
        gate.complete(true)
        assertEquals("ready", result.await().toString(Charsets.UTF_8))
        assertFalse(owner.quarantined)
        owner.close()
    }

    @Test fun roleCloseMustFinishBeforeResponseDelivery() = runBlocking {
        val gate = CompletableDeferred<Boolean>()
        val call = object : Call() {
            override suspend fun close(): Boolean { closes.incrementAndGet(); return gate.await() }
        }.also { it.success() }
        val port = Port(request); val owner = owner(Engine(call))
        val result = async { prepare(owner, port) }
        eventually { call.closes.get() == 1 }
        assertEquals(0, port.deliveries.get()); assertFalse(result.isCompleted)
        gate.complete(true)
        assertEquals("ready", result.await().toString(Charsets.UTF_8))
        owner.close()
    }

    @Test fun nativeTicketInvalidationCancelsActiveRoleAndDropsLateOutput() = runBlocking {
        val call = Call(); val engine = Engine(call); val port = Port(request); val owner = owner(engine)
        val result = async { prepare(owner, port) }
        call.entered.await(); port.invalidate()
        assertEquals("cancelled", result.await().toString(Charsets.UTF_8))
        assertEquals(1, call.cancels.get()); assertEquals(1, call.drains.get()); assertEquals(1, call.closes.get())
        assertEquals(1, engine.closes.get()); assertEquals(0, port.deliveries.get())
        assertFalse(owner.quarantined)
        owner.close()
    }

    @Test fun explicitCancelAcknowledgementWaitsForSdkCleanupBeforeRefresh() = runBlocking {
        val closeGate = CompletableDeferred<Boolean>()
        val call = Call()
        val engine = object : Engine(call) {
            override suspend fun close(): Boolean { closes.incrementAndGet(); return closeGate.await() }
        }
        val port = Port(request)
        val owner = owner(engine, LocalInferenceLimits(turnMs = 2_000, cleanupMs = 1_000, pollMs = 2))
        val operation = async { prepare(owner, port) }
        call.entered.await()
        val cancellation = async { owner.execute(port, "cancel", "cancel".toByteArray()) }
        try {
            eventually { engine.closes.get() == 1 }
            assertTrue(port.cancels.get() >= 1)
            assertFalse("Cancel ACK must not permit a refresh while SDK close is still owned", cancellation.isCompleted)
            assertFalse(owner.quarantined)
            for (operationName in listOf("open", "branches")) {
                try {
                    owner.execute(port, operationName, operationName.toByteArray())
                    fail("Refresh must remain Busy while the captured cleanup is owned")
                } catch (_: LocalInferenceBusy) { /* No early refresh permission is granted. */ }
            }
        } finally {
            closeGate.complete(true)
        }
        assertEquals("ok", cancellation.await().toString(Charsets.UTF_8))
        assertEquals("cancelled", operation.await().toString(Charsets.UTF_8))
        assertEquals("ok", owner.execute(port, "open", "open".toByteArray()).toString(Charsets.UTF_8))
        assertEquals(0, port.deliveries.get()); assertEquals(0, port.commits.get())
        assertFalse(owner.quarantined)
        owner.close()
    }

    @Test fun explicitCancelNeverAcknowledgesFailedOrUnreturnedCleanup() = runBlocking {
        for (unreturned in listOf(false, true)) {
            val gate = CompletableDeferred<Boolean>()
            val call = Call()
            val engine = object : Engine(call) {
                override suspend fun close(): Boolean {
                    closes.incrementAndGet()
                    return if (unreturned) gate.await() else false
                }
            }
            val port = Port(request)
            val owner = owner(engine, LocalInferenceLimits(turnMs = 1_000, cleanupMs = 80, pollMs = 2))
            val operation = async { runCatching { prepare(owner, port) } }
            call.entered.await()
            val cancellation = runCatching { owner.execute(port, "cancel", "cancel".toByteArray()) }
            assertTrue(cancellation.exceptionOrNull() is LocalInferenceUncertain)
            assertTrue(operation.await().exceptionOrNull() is LocalInferenceUncertain)
            assertTrue(owner.quarantined)
            assertEquals(0, port.deliveries.get()); assertEquals(0, port.commits.get())
            refused(owner, port, "open"); refused(owner, port, "branches")
            gate.complete(true) // Late physical completion cannot reopen the quarantined owner.
            refused(owner, port, "open")
            owner.close()
        }
    }

    @Test fun uiStyleCallerCancellationStillJoinsKnownCleanupBeforeRefresh() = runBlocking {
        val gate = CompletableDeferred<Boolean>()
        val call = Call()
        val engine = object : Engine(call) {
            override suspend fun close(): Boolean { closes.incrementAndGet(); return gate.await() }
        }
        val port = Port(request)
        val owner = owner(engine, LocalInferenceLimits(turnMs = 2_000, cleanupMs = 1_000, pollMs = 2))
        val operation = launch { prepare(owner, port) }
        call.entered.await()
        operation.cancel() // The UI cancels its await; this alone is not a release observation.
        val cancellation = async { owner.execute(port, "cancel", "cancel".toByteArray()) }
        try {
            eventually { engine.closes.get() == 1 && port.cancels.get() >= 1 }
            assertFalse(cancellation.isCompleted)
        } finally { gate.complete(true) }
        assertEquals("ok", cancellation.await().toString(Charsets.UTF_8))
        operation.join()
        assertFalse(owner.quarantined)
        assertEquals("ok", owner.execute(port, "branches", "branches".toByteArray()).toString(Charsets.UTF_8))
        assertEquals(0, port.deliveries.get()); assertEquals(0, port.commits.get())
        owner.close()
    }

    @Test fun cancellingWithoutAnActiveRunRetainsFiniteNativeAcknowledgement() = runBlocking {
        val port = Port(request); val owner = owner(Engine(Call()))
        assertEquals("ok", owner.execute(port, "cancel", "cancel".toByteArray()).toString(Charsets.UTF_8))
        assertFalse(owner.quarantined)
        assertEquals(1, port.cancels.get()); assertEquals(0, port.commits.get())
        owner.close()
    }

    @Test fun callerCancellationWithKnownTerminalDrainAndCloseKeepsRecoveryAvailable() = runBlocking {
        val call = Call(); val engine = Engine(call); val port = Port(request); val owner = owner(engine)
        val operation = launch { prepare(owner, port) }
        call.entered.await(); operation.cancelAndJoin()
        assertFalse(owner.quarantined)
        assertEquals(1, call.cancels.get()); assertEquals(1, call.drains.get()); assertEquals(1, call.closes.get())
        assertEquals(1, engine.closes.get()); assertEquals(0, port.deliveries.get())
        assertEquals("ok", owner.execute(port, "turn_status", "turn_status".toByteArray()).toString(Charsets.UTF_8))
        owner.close()
    }

    @Test fun inputBytesAreCapturedBeforeIndependentNativeDispatch() = runBlocking {
        val gate = CountDownLatch(1)
        val received = AtomicReference<String>()
        val port = object : LocalInferenceNativePort {
            override fun call(input: ByteArray): ByteArray {
                check(gate.await(5, TimeUnit.SECONDS)); received.set(input.toString(Charsets.UTF_8))
                return "ok".toByteArray()
            }
            override fun poll(): LocalInferencePending? = null
            override fun respond(ticket: Long, response: ByteArray) = false
            override fun close() { }
        }
        val owner = owner(Engine(Call()))
        val source = "capabilities".toByteArray()
        val result = async(start = CoroutineStart.UNDISPATCHED) { owner.execute(port, "capabilities", source) }
        source.fill(0); gate.countDown()
        assertEquals("ok", result.await().toString(Charsets.UTF_8))
        assertEquals("capabilities", received.get()); owner.close()
    }

    @Test fun changedImmutableRequestUnderSameTicketCannotReceiveOriginalOutput() = runBlocking {
        val call = Call(); val port = Port(request); val owner = owner(Engine(call))
        val result = async { prepare(owner, port) }
        call.entered.await()
        port.pending.set(LocalInferencePending(7, request.copy(schemaJson = "{\"changed\":true}")))
        assertEquals("cancelled", result.await().toString(Charsets.UTF_8))
        assertEquals(0, port.deliveries.get()); assertEquals(1, call.cancels.get())
        owner.close()
    }

    @Test fun invalidationAfterKnownRoleCloseDoesNotCancelClosedSdkObject() = runBlocking {
        val call = object : Call() {
            override fun cancel() { error("a terminal closed role must not be cancelled") }
        }.also { it.success() }
        val engine = Engine(call)
        val port = object : Port(request) {
            override fun poll(): LocalInferencePending? {
                if (call.closes.get() > 0) invalidate()
                return super.poll()
            }
        }
        val owner = owner(engine)
        assertEquals("cancelled", prepare(owner, port).toString(Charsets.UTF_8))
        assertFalse(owner.quarantined); assertEquals(0, port.deliveries.get())
        assertEquals(1, engine.closes.get()); owner.close()
    }

    @Test fun duplicateConsumedTicketCannotOpenAnotherRoleOrDeliverAgain() = runBlocking {
        val call = Call().also { it.success() }; val engine = Engine(call)
        val port = Port(request).also { it.repeatTicket = true }; val owner = owner(engine)
        try { prepare(owner, port); fail() } catch (_: LocalInferenceUncertain) { }
        assertTrue(owner.quarantined); assertEquals(1, engine.starts.get()); assertEquals(1, port.deliveries.get())
        assertEquals(1, port.closes.get()); refused(owner, port, "free_text"); refused(owner, port)
        assertEquals(0, port.commits.get())
    }

    @Test fun roleCloseErrorQuarantinesWithoutClosingUnprovenParentOrCommitting() = runBlocking {
        val call = Call().also { it.success(); it.closeError = true }; val engine = Engine(call)
        val port = Port(request); val owner = owner(engine)
        try { prepare(owner, port); fail() } catch (failure: LocalInferenceUncertain) {
            assertNull(failure.cause); assertFalse(failure.message!!.contains("private"))
        }
        assertTrue(owner.quarantined); assertTrue(owner.nativeInvalidatedKnown)
        assertEquals(0, engine.closes.get()); assertEquals(0, port.deliveries.get())
        refused(owner, port); refused(owner, port, "turn_status")
        assertEquals(0, port.commits.get())
    }

    @Test fun startErrorAfterPossibleAllocationRetainsParentAndInvalidatesSameLease() = runBlocking {
        val engine = object : Engine(Call()) {
            override suspend fun start(request: LocalInferenceRequest): LocalRoleCall {
                starts.incrementAndGet(); throw AssertionError("private possible child allocation")
            }
        }
        val port = Port(request); val owner = owner(engine)
        try { prepare(owner, port); fail() } catch (_: LocalInferenceUncertain) { }
        assertTrue(owner.quarantined); assertEquals(1, port.closes.get()); assertEquals(0, engine.closes.get())
        refused(owner, port, "prepare"); assertEquals(1, engine.starts.get())
    }

    @Test fun lateStartWithUndrainedChildNeverClosesParentEngine() = runBlocking {
        val release = CompletableDeferred<Unit>()
        val call = Call().also { it.drained = false }
        val engine = object : Engine(call) {
            override suspend fun start(request: LocalInferenceRequest): LocalRoleCall {
                starts.incrementAndGet(); release.await(); return call
            }
        }
        val port = Port(request); val owner = owner(engine)
        val result = async { try { prepare(owner, port); false } catch (_: LocalInferenceUncertain) { true } }
        eventually { engine.starts.get() == 1 }; port.invalidate()
        assertTrue(result.await()); assertTrue(owner.quarantined)
        release.complete(Unit); eventually { call.drains.get() == 1 }
        assertEquals(0, engine.closes.get()); assertEquals(0, call.closes.get())
        assertEquals(1, port.closes.get())
    }

    @Test fun noncooperativeBlockingLoaderTimeoutDoesNotMeanReleasedAndLateOwnerIsClosed() = runBlocking {
        val gate = CountDownLatch(1); val entered = CountDownLatch(1); val engine = Engine(Call())
        val owner = LocalInferenceOwner("{}".toByteArray(), LocalRoleWorker {
            entered.countDown(); check(gate.await(5, TimeUnit.SECONDS)); engine
        }, Dispatchers.Default, LocalInferenceLimits(80, 100, 2))
        val port = Port(request)
        val result = async { try { prepare(owner, port); false } catch (_: LocalInferenceUncertain) { true } }
        withTimeout(1_000) { while (entered.count != 0L) delay(2) }
        assertTrue(result.await()); assertTrue(owner.quarantined)
        assertEquals(0, engine.closes.get()); assertTrue(owner.nativeInvalidatedKnown)
        refused(owner, port)
        gate.countDown(); eventually { engine.closes.get() == 1 }
        assertTrue(owner.quarantined)
    }

    @Test fun falseEngineCloseWithholdsReadyAndForbidsNewWork() = runBlocking {
        val call = Call().also { it.success() }
        val engine = object : Engine(call) { override suspend fun close(): Boolean { closes.incrementAndGet(); return false } }
        val port = Port(request); val owner = owner(engine)
        try { prepare(owner, port); fail() } catch (_: LocalInferenceUncertain) { }
        assertTrue(owner.quarantined); assertEquals(1, port.closes.get())
        refused(owner, port); refused(owner, port, "free_text")
    }

    @Test fun cleanupStepsShareOneDeadlineRatherThanMultiplyingIt() = runBlocking {
        val call = object : Call() {
            override fun cancel() { Thread.sleep(45); super.cancel() }
            override suspend fun drain(): Boolean { drains.incrementAndGet(); delay(45); return true }
        }
        val engine = Engine(call); val port = Port(request)
        val owner = owner(engine, LocalInferenceLimits(1_000, 70, 2))
        val result = async { try { prepare(owner, port); false } catch (_: LocalInferenceUncertain) { true } }
        call.entered.await(); port.invalidate()
        assertTrue(result.await()); assertTrue(owner.quarantined)
        // Each step is under 70ms, but their sum is not. No fabricated completed cleanup.
        assertEquals(0, call.closes.get()); assertEquals(0, engine.closes.get())
        eventually { owner.nativeInvalidatedKnown }
    }

    @Test fun invalidUtf8AndOversizedOrNonterminalOutputNeverReachNativeRespond() = runBlocking {
        for (result in listOf(LocalRoleResult(true, byteArrayOf(0xc3.toByte(), 0x28)),
            LocalRoleResult(true, ByteArray(16_385) { 65 }), LocalRoleResult(false, byteArrayOf(65)))) {
            val call = Call().also { it.output.complete(result) }; val port = Port(request); val owner = owner(Engine(call))
            try { prepare(owner, port); fail() } catch (_: LocalInferenceUncertain) { }
            assertEquals(0, port.deliveries.get()); assertTrue(owner.quarantined); assertEquals(1, port.closes.get())
        }
    }

    @Test fun malformedSchemaRequestBoundsAndProfileCopiesAreCheckedWithoutModelCode() {
        request.copy(role = "narrator", maxTokens = 350).validate()
        for (bad in listOf(request.copy(version = 2), request.copy(role = "tool"), request.copy(maxTokens = 351),
            request.copy(contextTokens = 511), request.copy(threads = 5), request.copy(schemaJson = "x"),
            request.copy(schemaJson = "x".repeat(32_769)), request.copy(prompt = "\uD800"))) {
            try { bad.validate(); fail("invalid worker request") } catch (_: Exception) { }
        }
        val source = "{}".toByteArray(); val owner = LocalInferenceOwner(source, LocalRoleWorker { error("unused") })
        source.fill(0); val copy = owner.profileBytes(); copy.fill(1)
        assertEquals("{}", owner.profileBytes().toString(Charsets.UTF_8))
        for (bad in listOf(ByteArray(4097), byteArrayOf(0xc3.toByte(), 0x28))) {
            try { LocalInferenceOwner(bad, LocalRoleWorker { error("unused") }); fail() } catch (_: Exception) { }
        }
    }

    @Test fun oneOwnerCannotBeClaimedByAnotherTransportBeforeNativeAllocation() {
        val owner = owner(Engine(Call()))
        val first = Any()
        owner.claimTransport(first); owner.claimTransport(first)
        try { owner.claimTransport(Any()); fail() }
        catch (expected: IllegalArgumentException) { assertEquals("Local inference owner already attached", expected.message) }
        assertFalse(owner.quarantined)
        owner.claimTransport(first)
        assertFalse(owner.nativeInvalidatedKnown) // No native allocation/closure was invented.
    }

    @Test fun purePortBindingCannotLaterBeReclaimedByAProductionTransport() {
        val owner = owner(Engine(Call())); val port = Port(request)
        owner.attach(port)
        try { owner.claimTransport(Any()); fail() }
        catch (expected: IllegalArgumentException) { assertEquals("Local inference owner already attached", expected.message) }
        assertFalse(owner.quarantined); assertEquals(0, port.closes.get())
        owner.close()
    }

    @Test fun reservedTransportRejectsForeignPurePortBeforeDispatch() = runBlocking {
        val owner = owner(Engine(Call())); val port = Port(request); val token = Any()
        owner.claimTransport(token)
        try { owner.execute(port, "commit", "commit".toByteArray()); fail() }
        catch (expected: IllegalArgumentException) { assertEquals("Local inference owner already attached", expected.message) }
        assertEquals(0, port.commits.get()); assertFalse(owner.quarantined)
        owner.attach(port, token)
        assertEquals("ok", owner.execute(port, "turn_status", "turn_status".toByteArray()).toString(Charsets.UTF_8))
        owner.close()
    }

    @Test fun closeReturnsImmediatelyWhileBlockingNativeInvalidationRemainsUnknown() = runBlocking {
        val gate = CountDownLatch(1)
        val closeEntered = CountDownLatch(1)
        val port = object : LocalInferenceNativePort {
            override fun call(input: ByteArray) = "ok".toByteArray()
            override fun poll(): LocalInferencePending? = null
            override fun respond(ticket: Long, response: ByteArray) = false
            override fun close() { closeEntered.countDown(); check(gate.await(5, TimeUnit.SECONDS)) }
        }
        val owner = owner(Engine(Call()), LocalInferenceLimits(200, 60, 2))
        owner.attach(port)
        val before = System.nanoTime()
        try {
            owner.close()
            assertTrue((System.nanoTime() - before) / 1_000_000 < 50)
            eventually { closeEntered.count == 0L }
            eventually { owner.quarantined }
            assertFalse(owner.nativeInvalidatedKnown)
        } finally { gate.countDown() }
        eventually { owner.nativeInvalidatedKnown }
        assertTrue(owner.quarantined)
    }
}
