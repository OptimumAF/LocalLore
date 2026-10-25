/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File
import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Synthetic files and injected resources only: these tests never initialize an SDK/model. */
class LiteRtRoleWorkerTest {
    @get:Rule val temporary = TemporaryFolder()
    private val request = LocalInferenceRequest(1, "director", "exact original prompt", 350, 4096, 4, "{\"type\":\"object\"}")
    private class Conversation : LiteRtConversationResource {
        lateinit var callbacks: LiteRtCallbacks
        lateinit var request: LocalInferenceRequest
        val sent = CountDownLatch(1)
        var sendAction: (() -> Unit)? = null
        var cancelAction: (() -> Unit)? = null
        var closeAction: (() -> Boolean)? = null
        val cancels = AtomicInteger()
        val closes = AtomicInteger()
        override fun send(request: LocalInferenceRequest, callbacks: LiteRtCallbacks) {
            this.request = request; this.callbacks = callbacks; sent.countDown(); sendAction?.invoke()
        }
        override fun cancel() { cancels.incrementAndGet(); cancelAction?.invoke() }
        override fun close(): Boolean { closes.incrementAndGet(); return closeAction?.invoke() ?: true }
        fun text(text: String) = callbacks.message { LiteRtChunk(text = listOf(text)) }
        fun done() = callbacks.done()
    }
    private class Engine : LiteRtEngineResource {
        val conversations = CopyOnWriteArrayList<Conversation>()
        var initializeAction: (() -> Unit)? = null
        var conversationAction: (() -> Conversation)? = null
        var closeAction: (() -> Boolean)? = null
        val closes = AtomicInteger()
        var initializeThread: String? = null
        override fun initialize() { initializeThread = Thread.currentThread().name; initializeAction?.invoke() }
        override fun conversation(request: LocalInferenceRequest): LiteRtConversationResource =
            (conversationAction?.invoke() ?: Conversation()).also { conversations += it }
        override fun close(): Boolean { closes.incrementAndGet(); return closeAction?.invoke() ?: true }
    }
    private class Resources : LiteRtResources {
        val engines = CopyOnWriteArrayList<Engine>()
        var next = Engine()
        var paths: LiteRtPaths? = null
        var createAction: (() -> Unit)? = null
        override fun engine(paths: LiteRtPaths): LiteRtEngineResource {
            this.paths = paths
            createAction?.invoke()
            return next.also { engines += it; next = Engine() }
        }
    }
    private class Port(request: LocalInferenceRequest) : LocalInferenceNativePort {
        val pending = AtomicReference<LocalInferencePending?>(LocalInferencePending(7, request))
        private val terminal = CountDownLatch(1)
        val commits = AtomicInteger()
        val closes = AtomicInteger()
        val deliveries = AtomicInteger()
        @Volatile private var reply = "ready"
        override fun call(input: ByteArray): ByteArray = when (input.toString(Charsets.UTF_8)) {
            "prepare" -> { check(terminal.await(2, TimeUnit.SECONDS)); reply.toByteArray() }
            "cancel" -> { invalidate(); "cancelled".toByteArray() }
            "commit" -> { commits.incrementAndGet(); "accepted-receipt".toByteArray() }
            else -> commits.get().toString().toByteArray()
        }
        override fun poll(): LocalInferencePending? = pending.get()
        override fun respond(ticket: Long, response: ByteArray): Boolean {
            if (pending.get()?.ticket != ticket) return false
            deliveries.incrementAndGet(); pending.set(null); terminal.countDown(); return true
        }
        fun invalidate() { reply = "cancelled"; pending.set(null); terminal.countDown() }
        override fun close() { closes.incrementAndGet(); invalidate() }
    }
    private fun config(): LiteRtWorkerConfig {
        val root = temporary.newFolder()
        val model = File(root, "synthetic-only.litertlm").also { it.writeBytes(byteArrayOf(1, 2, 3, 4)) }
        val cache = File(root, "synthetic-cache").also { check(it.mkdir()) }
        val hash = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
        return LiteRtWorkerConfig(root, model, cache, 4, hash, "a".repeat(64), "b".repeat(64), "c".repeat(64))
    }

    /** Scripted native request sequence, without a second gameplay reducer. */
    private class SequencePort(private val requests: List<LocalInferenceRequest>) : LocalInferenceNativePort {
        private val terminal = CountDownLatch(1)
        private var index = 0
        private var invalidated = false
        val deliveries = AtomicInteger()
        val commits = AtomicInteger()
        val closes = AtomicInteger()
        override fun call(input: ByteArray): ByteArray = when (input.toString(Charsets.UTF_8)) {
            "prepare" -> {
                check(terminal.await(3, TimeUnit.SECONDS))
                synchronized(this) { (if (invalidated) "cancelled" else "ready").toByteArray() }
            }
            "cancel" -> { invalidate(); "cancelled".toByteArray() }
            "commit" -> { commits.incrementAndGet(); "accepted-receipt".toByteArray() }
            else -> error("Unknown synthetic operation")
        }
        @Synchronized override fun poll(): LocalInferencePending? =
            if (invalidated || index == requests.size) null else LocalInferencePending(index + 1L, requests[index])
        @Synchronized override fun respond(ticket: Long, response: ByteArray): Boolean {
            if (invalidated || index == requests.size || ticket != index + 1L) return false
            deliveries.incrementAndGet(); index++
            if (index == requests.size) terminal.countDown()
            return true
        }
        @Synchronized private fun invalidate() { invalidated = true; terminal.countDown() }
        override fun close() { closes.incrementAndGet(); invalidate() }
    }
    private suspend fun uncertain(block: suspend () -> Unit) {
        try { block(); fail("Expected fixed ownership uncertainty") }
        catch (expected: LocalInferenceUncertain) {
            // Coroutine stack recovery may wrap this final, fixed exception with an identical copy.
            // Only a finite acyclic chain of these copies is safe; never admit an SDK/private cause.
            val seen = java.util.IdentityHashMap<Throwable, Boolean>()
            var current: Throwable? = expected
            var depth = 0
            while (current != null) {
                assertTrue("Unbounded uncertainty cause chain", depth++ < 8)
                assertNull("Cyclic uncertainty cause chain", seen.put(current, true))
                assertEquals(LocalInferenceUncertain::class.java, current.javaClass)
                assertEquals("Local inference ownership uncertain", current.message)
                current = current.cause
            }
        }
    }
    private suspend fun eventually(test: () -> Boolean) = withTimeout(2_000) { while (!test()) delay(2) }
    private fun CountDownLatch.boundedAwait() { check(await(2, TimeUnit.SECONDS)) }
    private suspend fun healthyClose(call: LocalRoleCall, engine: LocalRoleEngine) {
        assertTrue(call.drain()); assertTrue(call.close()); assertTrue(engine.close())
    }

    @Test fun structuredRoleOrderAndOriginalSchemasSurviveFreshConversationCreation() = runBlocking {
        for (roles in listOf(listOf("director", "narrator"), listOf("director", "director", "narrator"))) {
            val resources = Resources()
            val trace = LiteRtWorkerTrace()
            val engine = LiteRtRoleWorker(config(), resources, trace).open()
            for ((index, role) in roles.withIndex()) {
                val schema = """{"type":"object","properties":{"canary_$index":{"type":"string"}}}"""
                val original = request.copy(role = role, maxTokens = if (role == "narrator") 220 else 350,
                    schemaJson = schema, prompt = "original private prompt $index")
                val call = engine.start(original)
                val conversation = resources.engines.single().conversations.last()
                assertSame(original, conversation.request)
                assertEquals(schema, conversation.request.schemaJson)
                assertEquals(index + 1, trace.snapshot().creations[index].ordinal)
                assertEquals(if (role == "director") LiteRtTraceRole.DIRECTOR else LiteRtTraceRole.NARRATOR,
                    trace.snapshot().creations[index].role)
                conversation.text("{}"); conversation.done(); call.await()
                assertTrue(call.drain()); assertTrue(call.close())
            }
            assertEquals(roles.size, resources.engines.single().conversations.toSet().size)
            assertTrue(resources.engines.single().conversations.all { it.closes.get() == 1 })
            assertTrue(engine.close())
            val observed = trace.snapshot()
            assertEquals(roles.size, observed.creations.size)
            assertTrue(observed.creations.all { it.returnedMs != null && it.failedMs == null && it.failure == LiteRtTraceFailure.NONE })
            assertFalse(observed.json().contains("private prompt")); assertFalse(observed.json().contains("canary_"))
        }
    }

    @Test fun unfinishedSecondCreationKeepsRoleTimingAndNeverAuthorizesCommit() = runBlocking {
        val resources = Resources()
        val trace = LiteRtWorkerTrace()
        val first = Conversation().also { conversation -> conversation.sendAction = { conversation.text("{}"); conversation.done() } }
        val second = Conversation().also { conversation -> conversation.sendAction = { conversation.text("{}"); conversation.done() } }
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        val factories = AtomicInteger()
        resources.next.conversationAction = {
            if (factories.incrementAndGet() == 1) first else {
                entered.countDown(); release.boundedAwait(); second
            }
        }
        val config = config().copy(deadlineMs = 500)
        val owner = config.createOwner(LocalInferenceLimits(turnMs = 500, cleanupMs = 100, pollMs = 2), resources, trace)
        val port = SequencePort(listOf(request, request.copy(role = "narrator", maxTokens = 220)))
        val preparing = async { uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) } }
        try {
            eventually { entered.count == 0L }
            preparing.await()
            val observed = trace.snapshot()
            assertTrue(owner.quarantined); assertEquals(1, port.deliveries.get()); assertEquals(0, port.commits.get())
            assertEquals(listOf(LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.NARRATOR), observed.creations.map { it.role })
            assertNotNull(observed.creations[0].returnedMs)
            assertNull(observed.creations[1].returnedMs); assertNull(observed.creations[1].failedMs)
            assertTrue(observed.creations[1].enteredMs <= observed.snapshotMs)
            assertEquals(1, first.closes.get()); assertEquals(0, second.closes.get())
            assertEquals(0, observed.counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN))
        } finally { release.countDown() }
        eventually { trace.snapshot().creations[1].returnedMs != null }
        uncertain { owner.execute(port, "commit", "commit".toByteArray()) }
        assertTrue(owner.quarantined); assertEquals(1, port.deliveries.get()); assertEquals(0, port.commits.get())
    }

    @Test fun failedCreationReportsClosedCategoryAfterOriginalFenceWithoutPrivateError() = runBlocking {
        for (cancelled in listOf(false, true)) {
            val resources = Resources()
            val trace = LiteRtWorkerTrace()
            var observedBeforeFailureMark = false
            val worker = LiteRtRoleWorker(config(), resources, trace) {
                observedBeforeFailureMark = trace.snapshot().creations.single().failedMs == null
            }
            val engine = worker.open()
            resources.engines.single().conversationAction = {
                if (cancelled) throw java.util.concurrent.CancellationException("private cancellation source")
                else throw AssertionError("private native path/cause/schema")
            }
            uncertain { engine.start(request) }
            assertTrue(observedBeforeFailureMark)
            val observed = trace.snapshot()
            assertEquals(if (cancelled) LiteRtTraceFailure.CANCELLED else LiteRtTraceFailure.OTHER, observed.creations.single().failure)
            assertNotNull(observed.creations.single().failedMs); assertNull(observed.creations.single().returnedMs)
            assertFalse(observed.json().contains("private")); assertFalse(engine.close())
        }
    }

    @Test fun stageTraceDistinguishesBlockedAdmissionConstructionAndInitialization() = runBlocking {
        for ((enteredEvent, returnedEvent) in listOf(
            LiteRtWorkerEvent.ADMISSION_ENTERED to LiteRtWorkerEvent.ADMISSION_RETURNED,
            LiteRtWorkerEvent.ENGINE_CREATE_ENTERED to LiteRtWorkerEvent.ENGINE_CREATE_RETURNED,
            LiteRtWorkerEvent.INITIALIZE_ENTERED to LiteRtWorkerEvent.INITIALIZE_RETURNED,
        )) {
            val entered = CountDownLatch(1); val release = CountDownLatch(1)
            val block = { entered.countDown(); release.boundedAwait() }
            val resources = Resources()
            val original = config()
            val selected = when (enteredEvent) {
                LiteRtWorkerEvent.ADMISSION_ENTERED -> original.copy(storageAdmission = block)
                LiteRtWorkerEvent.ENGINE_CREATE_ENTERED -> original.also { resources.createAction = block }
                else -> original.also { resources.next.initializeAction = block }
            }
            val trace = LiteRtWorkerTrace()
            val worker = LiteRtRoleWorker(selected, resources, trace)
            val opening = async { worker.open() }
            try {
                eventually { entered.count == 0L }
                val observed = trace.snapshot()
                assertEquals(1, observed.counts.getValue(enteredEvent))
                assertEquals(0, observed.counts.getValue(returnedEvent))
                assertEquals(0, observed.counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN))
                assertFalse(opening.isCompleted)
            } finally { release.countDown() }
            val engine = opening.await()
            assertEquals(1, trace.snapshot().counts.getValue(returnedEvent))
            assertTrue(engine.close())
        }
    }

    @Test fun stageTraceSeparatesSendReturnTerminalAndBodyDrain() = runBlocking {
        val resources = Resources()
        val trace = LiteRtWorkerTrace()
        val engine = LiteRtRoleWorker(config(), resources, trace).open()
        val sendEntered = CountDownLatch(1); val sendRelease = CountDownLatch(1)
        val conversation = Conversation().also { it.sendAction = { sendEntered.countDown(); sendRelease.boundedAwait() } }
        resources.engines.single().conversationAction = { conversation }
        val starting = async { engine.start(request) }
        try {
            eventually { sendEntered.count == 0L }
            assertEquals(1, trace.snapshot().counts.getValue(LiteRtWorkerEvent.SEND_ENTERED))
            assertEquals(0, trace.snapshot().counts.getValue(LiteRtWorkerEvent.SEND_RETURNED))
        } finally { sendRelease.countDown() }
        val call = starting.await()
        val bodyEntered = CountDownLatch(1); val bodyRelease = CountDownLatch(1)
        val callback = async(Dispatchers.IO) { conversation.callbacks.message {
            bodyEntered.countDown(); bodyRelease.boundedAwait(); LiteRtChunk(text = listOf("{}"))
        } }
        val draining = async { call.drain() }
        try {
            eventually { bodyEntered.count == 0L }
            conversation.done()
            val snapshot = trace.snapshot()
            assertEquals(1, snapshot.counts.getValue(LiteRtWorkerEvent.DONE_RETURNED))
            assertEquals(1, snapshot.counts.getValue(LiteRtWorkerEvent.MESSAGE_ENTERED))
            assertEquals(0, snapshot.counts.getValue(LiteRtWorkerEvent.MESSAGE_RETURNED))
            assertEquals(0, snapshot.counts.getValue(LiteRtWorkerEvent.DRAIN_SETTLED))
            assertFalse(draining.isCompleted)
        } finally { bodyRelease.countDown() }
        callback.await(); assertTrue(draining.await()); call.await()
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtWorkerEvent.MESSAGE_RETURNED))
        assertTrue(call.close()); assertTrue(engine.close())
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN))
        assertEquals(1, trace.snapshot().counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN))
    }

    @Test fun stageTraceDoesNotPromoteBlockedOrFailedCloseToKnown() = runBlocking {
        val resources = Resources()
        val trace = LiteRtWorkerTrace()
        val engine = LiteRtRoleWorker(config(), resources, trace).open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        conversation.done(); call.await(); assertTrue(call.drain())
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        conversation.closeAction = { entered.countDown(); release.boundedAwait(); false }
        val closing = async { call.close() }
        try {
            eventually { entered.count == 0L }
            val observed = trace.snapshot()
            assertEquals(1, observed.counts.getValue(LiteRtWorkerEvent.CONVERSATION_CLOSE_ENTERED))
            assertEquals(0, observed.counts.getValue(LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN))
            assertFalse(engine.close())
        } finally { release.countDown() }
        assertFalse(closing.await()); assertFalse(engine.close())
        val failed = trace.snapshot()
        assertEquals(0, failed.counts.getValue(LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN))
        assertEquals(0, failed.counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED))
        assertTrue(failed.counts.getValue(LiteRtWorkerEvent.UNCERTAIN) > 0)
    }

    @Test fun stageTraceLateInitializeReturnCannotClearOwnerQuarantine() = runBlocking {
        val resources = Resources()
        val trace = LiteRtWorkerTrace()
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        resources.next.initializeAction = { entered.countDown(); release.boundedAwait() }
        val config = config().copy(deadlineMs = 100)
        val owner = config.createOwner(LocalInferenceLimits(turnMs = 100, cleanupMs = 100, pollMs = 2), resources, trace)
        val port = Port(request)
        val preparing = async { uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) } }
        try {
            eventually { entered.count == 0L }
            preparing.await()
            assertTrue(owner.quarantined)
            assertEquals(0, trace.snapshot().counts.getValue(LiteRtWorkerEvent.INITIALIZE_RETURNED))
            assertEquals(0, port.deliveries.get()); assertEquals(0, port.commits.get())
        } finally { release.countDown() }
        eventually { trace.snapshot().counts.getValue(LiteRtWorkerEvent.INITIALIZE_RETURNED) == 1 }
        uncertain { owner.execute(port, "commit", "commit".toByteArray()) }
        assertTrue(owner.quarantined); assertEquals(0, port.commits.get())
    }

    @Test fun stageTraceObservesDirectEngineCloseFailureAfterFencing() = runBlocking {
        val resources = Resources()
        val trace = LiteRtWorkerTrace()
        var fenced = false
        var priorNotifications: Int? = null
        resources.next.closeAction = { false }
        val worker = LiteRtRoleWorker(config(), resources, trace) {
            // Notification retains its original priority over observation.
            priorNotifications = trace.snapshot().counts.getValue(LiteRtWorkerEvent.UNCERTAIN)
            fenced = true
        }
        val engine = worker.open()
        assertFalse(engine.close()); assertTrue(fenced)
        assertEquals(0, priorNotifications)
        val failed = trace.snapshot()
        assertEquals(1, failed.counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED))
        assertEquals(0, failed.counts.getValue(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN))
        assertEquals(1, failed.counts.getValue(LiteRtWorkerEvent.UNCERTAIN))
        assertFalse(engine.close())
        try { worker.open(); fail() } catch (_: IllegalStateException) { }
    }

    @Test fun pairedFactoryCarriesExactTrustedProfileAndLimits() {
        val config = config().copy(narratorTokens = 300, deadlineMs = 1234, repairLimit = 0)
        val bytes = config.createOwner(LocalInferenceLimits(turnMs = 1234)).profileBytes()
        val profile = bytes.toString(Charsets.UTF_8)
        assertTrue(profile.contains("\"runtime_revision\":\"$LITERT_REVISION\""))
        assertTrue(profile.contains("\"model_sha256\":\"${config.modelSha256}\""))
        assertTrue(profile.contains("\"narrator_tokens\":300"))
        assertTrue(profile.contains("\"deadline_ms\":1234"))
        assertTrue(profile.contains("\"repair_limit\":0"))
        assertArrayEquals(bytes, config.profileBytes())
        try { config.createOwner(LocalInferenceLimits(turnMs = 1235)); fail() } catch (_: IllegalArgumentException) { }
    }

    @Test fun missingModelNeverConstructsSdkOrCreatesDirectories() = runBlocking {
        val config = config()
        check(config.model.delete()); check(config.cache.delete())
        val resources = Resources()
        uncertain { LiteRtRoleWorker(config, resources).open() }
        assertTrue(resources.engines.isEmpty())
        assertFalse(config.model.exists()); assertFalse(config.cache.exists())
    }

    @Test fun volumeRefusalBeforeAndAfterHashNeverConstructsSdk() = runBlocking {
        for (refuseAt in 1..2) {
            var observations = 0
            val config = config().copy(storageAdmission = {
                observations++
                check(observations < refuseAt)
            })
            val resources = Resources()
            uncertain { LiteRtRoleWorker(config, resources).open() }
            assertEquals(refuseAt, observations)
            assertTrue(resources.engines.isEmpty())
        }
    }

    @Test fun changedVolumeFencesInitializationConversationAndSendWithoutClosingUnknownParents() = runBlocking {
        for (refuseAt in 3..5) {
            var observations = 0
            val config = config().copy(storageAdmission = {
                observations++
                check(observations < refuseAt)
            })
            val resources = Resources()
            val worker = LiteRtRoleWorker(config, resources)
            if (refuseAt == 3) {
                uncertain { worker.open() }
                assertNull(resources.engines.single().initializeThread)
            } else {
                val engine = worker.open()
                uncertain { engine.start(request) }
                assertFalse(engine.close())
            }
            assertEquals(refuseAt, observations)
            val resource = resources.engines.single()
            assertEquals(0, resource.closes.get())
            if (refuseAt < 5) assertTrue(resource.conversations.isEmpty())
            else assertEquals(1L, resource.conversations.single().sent.count)
        }
    }

    @Test fun fullHashMismatchAndSizeMismatchNeverConstructSdk() = runBlocking {
        listOf(config().copy(modelSha256 = "0".repeat(64)), config().copy(expectedModelBytes = 5)).forEach {
            val resources = Resources()
            uncertain { LiteRtRoleWorker(it, resources).open() }
            assertTrue(resources.engines.isEmpty())
        }
    }

    @Test fun cacheOutsideConfinedRootIsRejectedBeforeSdk() = runBlocking {
        val resources = Resources()
        uncertain { LiteRtRoleWorker(config().copy(cache = temporary.newFolder()), resources).open() }
        assertTrue(resources.engines.isEmpty())
    }

    @Test fun admissionAndInitializationRunOffCallerThread() = runBlocking {
        val resources = Resources()
        val caller = Thread.currentThread().name
        val engine = LiteRtRoleWorker(config(), resources).open()
        assertNotEquals(caller, resources.engines.single().initializeThread)
        assertEquals(4096, resources.paths!!.contextTokens)
        assertTrue(engine.close())
    }

    @Test fun freshEnginesAndConversationsPreserveOriginalRequestAndSchema() = runBlocking {
        val resources = Resources()
        val worker = LiteRtRoleWorker(config(), resources)
        val engine = worker.open()
        val call = engine.start(request)
        val first = resources.engines.single().conversations.single()
        assertEquals(request, first.request)
        first.text("{\"ok\":true}"); first.done()
        assertArrayEquals("{\"ok\":true}".toByteArray(), call.await().response())
        assertTrue(call.drain()); assertTrue(call.close())
        val narrator = request.copy(role = "narrator", maxTokens = 220)
        val secondCall = engine.start(narrator)
        val second = resources.engines.single().conversations.last()
        assertNotSame(first, second); assertEquals(narrator.schemaJson, second.request.schemaJson)
        second.text("{}") ; second.done(); secondCall.await()
        healthyClose(secondCall, engine)
        val next = worker.open()
        assertEquals(2, resources.engines.size); assertTrue(next.close())
    }

    @Test fun roleAndContextMismatchPoisonOwnerWithoutParentClose() = runBlocking {
        listOf(request.copy(contextTokens = 2048), request.copy(role = "narrator", maxTokens = 221), request.copy(threads = 3)).forEach {
            val resources = Resources()
            val worker = LiteRtRoleWorker(config(), resources)
            val engine = worker.open()
            uncertain { engine.start(it) }
            assertTrue(resources.engines.single().conversations.isEmpty())
            assertFalse(engine.close()); assertEquals(0, resources.engines.single().closes.get())
            try { worker.open(); fail() } catch (_: IllegalStateException) { }
        }
    }

    @Test fun sdkVisibleNonTextRoleChannelsAndToolsFailClosed() = runBlocking {
        listOf(LiteRtChunk(modelRole = false), LiteRtChunk(nonText = true), LiteRtChunk(channels = true), LiteRtChunk(tools = true)).forEach { chunk ->
            val resources = Resources()
            val engine = LiteRtRoleWorker(config(), resources).open()
            val call = engine.start(request)
            val conversation = resources.engines.single().conversations.single()
            conversation.callbacks.message { chunk }; conversation.done()
            uncertain { call.await() }
            assertFalse(call.drain()); assertFalse(call.close()); assertFalse(engine.close())
            assertEquals(0, conversation.closes.get()); assertEquals(0, resources.engines.single().closes.get())
        }
    }

    @Test fun malformedUtf16AndOverLimitUtf8AreRejected() = runBlocking {
        listOf("\uD800", "é".repeat(8193), "a".repeat(16385)).forEach { text ->
            val resources = Resources()
            val engine = LiteRtRoleWorker(config(), resources).open()
            val call = engine.start(request)
            val conversation = resources.engines.single().conversations.single()
            conversation.text(text); conversation.done()
            uncertain { call.await() }; assertFalse(call.drain()); assertFalse(engine.close())
        }
    }

    @Test fun cumulativeUtf8LimitAndSplitThinkingMarkerAreRejected() = runBlocking {
        listOf(listOf("a".repeat(8192), "b".repeat(8193)), listOf("<thi", "nk>private")).forEach { chunks ->
            val resources = Resources()
            val engine = LiteRtRoleWorker(config(), resources).open()
            val call = engine.start(request)
            val conversation = resources.engines.single().conversations.single()
            chunks.forEach(conversation::text); conversation.done()
            uncertain { call.await() }; assertFalse(call.close()); assertFalse(engine.close())
        }
    }

    @Test fun exactUtf8BoundaryAndResponseCopiesAreAccepted() = runBlocking {
        val resources = Resources()
        val engine = LiteRtRoleWorker(config(), resources).open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        conversation.text("é".repeat(8192)); conversation.done()
        val result = call.await()
        assertEquals(16384, result.response().size)
        val copy = result.response(); copy[0] = 0
        assertNotEquals(0.toByte(), result.response()[0])
        healthyClose(call, engine)
    }

    @Test fun cancellationRemainsOwnedUntilSdkCancelReturnsAndTerminalArrives() = runBlocking {
        val resources = Resources()
        val engine = LiteRtRoleWorker(config(), resources).open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        conversation.cancelAction = { entered.countDown(); release.boundedAwait(); conversation.callbacks.error(true) }
        call.cancel(); entered.boundedAwait()
        val result = async { call.await() }
        val drain = async { call.drain() }
        try {
            delay(20); assertFalse(result.isCompleted); assertFalse(drain.isCompleted)
            assertFalse(call.close()); assertFalse(engine.close())
            assertEquals(0, conversation.closes.get()); assertEquals(0, resources.engines.single().closes.get())
        } finally { release.countDown() }
        assertTrue(withTimeout(2000) { result.await() }.response().isEmpty())
        assertTrue(drain.await()); healthyClose(call, engine)
        assertEquals(1, conversation.cancels.get())
    }

    @Test fun terminalBeforeCancelReturnStillBlocksDrain() = runBlocking {
        val resources = Resources()
        val engine = LiteRtRoleWorker(config(), resources).open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        conversation.cancelAction = { conversation.callbacks.error(true); entered.countDown(); release.boundedAwait() }
        call.cancel(); entered.boundedAwait()
        val drain = async { call.drain() }
        try { delay(20); assertFalse(drain.isCompleted); assertFalse(call.close()); assertFalse(engine.close()) }
        finally { release.countDown() }
        assertTrue(withTimeout(2000) { drain.await() }); assertTrue(call.await().response().isEmpty())
        healthyClose(call, engine)
    }

    @Test fun activeCallbackBodyMustReturnBeforeReadyOrClose() = runBlocking {
        val resources = Resources()
        val engine = LiteRtRoleWorker(config(), resources).open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        val callback = async(Dispatchers.IO) {
            conversation.callbacks.message { entered.countDown(); release.boundedAwait(); LiteRtChunk(text = listOf("{}")) }
        }
        entered.boundedAwait(); conversation.done()
        val result = async { call.await() }
        try { delay(20); assertFalse(result.isCompleted); assertFalse(call.close()); assertFalse(engine.close()) }
        finally { release.countDown() }
        callback.await(); assertEquals("{}", result.await().response().toString(Charsets.UTF_8))
        healthyClose(call, engine)
    }

    @Test fun failedStartAfterSynchronousTerminalRetainsChildAndParent() = runBlocking {
        val resources = Resources()
        val conversation = Conversation().also { call -> call.sendAction = { call.done(); throw AssertionError("private start failure") } }
        resources.next.conversationAction = { conversation }
        val worker = LiteRtRoleWorker(config(), resources)
        val engine = worker.open()
        uncertain { engine.start(request) }
        assertFalse(engine.close()); assertEquals(0, conversation.closes.get())
        assertEquals(0, resources.engines.single().closes.get())
        try { worker.open(); fail() } catch (_: IllegalStateException) { }
    }

    @Test fun initializationErrorRetainsUnknownEngineAndRejectsReuse() = runBlocking {
        val resources = Resources()
        resources.next.initializeAction = { throw AssertionError("private partially allocated loader") }
        val worker = LiteRtRoleWorker(config(), resources)
        uncertain { worker.open() }
        assertEquals(0, resources.engines.single().closes.get())
        try { worker.open(); fail() } catch (_: IllegalStateException) { }
        assertEquals(1, resources.engines.size)
    }

    @Test fun conversationCreationErrorNeverClosesPotentialParentAllocation() = runBlocking {
        val resources = Resources()
        resources.next.conversationAction = { throw AssertionError("private partial conversation") }
        val engine = LiteRtRoleWorker(config(), resources).open()
        uncertain { engine.start(request) }
        assertFalse(engine.close()); assertEquals(0, resources.engines.single().closes.get())
    }

    @Test fun callbackMappingErrorAndDuplicateTerminalStayUnknown() = runBlocking {
        for (mappingError in listOf(true, false)) {
            val resources = Resources()
            val engine = LiteRtRoleWorker(config(), resources).open()
            val call = engine.start(request)
            val conversation = resources.engines.single().conversations.single()
            if (mappingError) conversation.callbacks.message { throw AssertionError("private payload") }
            conversation.done()
            if (!mappingError) conversation.done()
            uncertain { call.await() }; assertFalse(call.drain()); assertFalse(call.close()); assertFalse(engine.close())
        }
    }

    @Test fun unsolicitedCancellationAndCancelErrorRemainUnknown() = runBlocking {
        for (requested in listOf(false, true)) {
            val resources = Resources()
            val engine = LiteRtRoleWorker(config(), resources).open()
            val call = engine.start(request)
            val conversation = resources.engines.single().conversations.single()
            if (requested) {
                conversation.cancelAction = { throw AssertionError("private cancellation failure") }
                call.cancel(); eventually { conversation.cancels.get() == 1 }
            } else conversation.callbacks.error(true)
            uncertain { call.await() }; assertFalse(call.drain()); assertFalse(call.close()); assertFalse(engine.close())
        }
    }

    @Test fun roleCloseFalseOrErrorRetainsEngineAndRejectsNewGeneration() = runBlocking {
        for (throws in listOf(false, true)) {
            val resources = Resources()
            val worker = LiteRtRoleWorker(config(), resources)
            val engine = worker.open()
            val call = engine.start(request)
            val conversation = resources.engines.single().conversations.single()
            conversation.closeAction = { if (throws) throw AssertionError("private close failure") else false }
            conversation.done(); call.await(); assertTrue(call.drain())
            assertFalse(call.close()); assertFalse(engine.close())
            assertEquals(0, resources.engines.single().closes.get())
            uncertain { engine.start(request) }
            try { worker.open(); fail() } catch (_: IllegalStateException) { }
        }
    }

    @Test fun delayedRoleCloseBlocksEngineCloseAndNextRoleUntilReturn() = runBlocking {
        val resources = Resources()
        val engine = LiteRtRoleWorker(config(), resources).open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        conversation.closeAction = { entered.countDown(); release.boundedAwait(); true }
        conversation.done(); call.await()
        val close = async { call.close() }
        try {
            eventually { entered.count == 0L }; assertFalse(engine.close()); assertFalse(close.isCompleted)
            assertEquals(0, resources.engines.single().closes.get())
        } finally { release.countDown() }
        assertTrue(close.await()); assertTrue(engine.close())
    }

    @Test fun engineCloseFalseCannotBeRetriedAsKnownOrReused() = runBlocking {
        val resources = Resources()
        resources.next.closeAction = { false }
        val worker = LiteRtRoleWorker(config(), resources)
        val engine = worker.open()
        assertFalse(engine.close()); assertFalse(engine.close())
        assertEquals(1, resources.engines.single().closes.get())
        try { worker.open(); fail() } catch (_: IllegalStateException) { }
    }

    @Test fun lateCallbackAfterKnownClosePoisonsFutureOpen() = runBlocking {
        val resources = Resources()
        val worker = LiteRtRoleWorker(config(), resources)
        val engine = worker.open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        conversation.done(); call.await(); assertTrue(call.close())
        conversation.text("late")
        assertFalse(call.drain()); assertFalse(call.close()); assertFalse(engine.close())
        try { worker.open(); fail() } catch (_: IllegalStateException) { }
    }

    @Test fun lateCallbackDuringEngineCloseInvalidatesReturnedProof() = runBlocking {
        val resources = Resources()
        val worker = LiteRtRoleWorker(config(), resources)
        val engine = worker.open()
        val call = engine.start(request)
        val conversation = resources.engines.single().conversations.single()
        conversation.done(); call.await(); assertTrue(call.close())
        resources.engines.single().closeAction = { conversation.text("late during delete"); true }
        assertFalse(engine.close()); assertFalse(engine.close()); assertFalse(call.drain())
        assertEquals(1, resources.engines.single().closes.get())
        try { worker.open(); fail() } catch (_: IllegalStateException) { }
    }

    @Test fun pairedOwnerWithholdsReadyUntilEngineCloseAndRevokesObservedLateOwner() = runBlocking {
        val resources = Resources()
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        resources.next.closeAction = { entered.countDown(); release.boundedAwait(); true }
        val config = config().copy(deadlineMs = 2000)
        val owner = config.createOwner(LocalInferenceLimits(turnMs = 2000, cleanupMs = 500, pollMs = 2), resources)
        val port = Port(request)
        val preparing = async { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
        eventually { resources.engines.firstOrNull()?.conversations?.firstOrNull()?.sent?.count == 0L }
        val conversation = resources.engines.single().conversations.single()
        conversation.text("{}"); conversation.done()
        try {
            eventually { entered.count == 0L }
            assertFalse(preparing.isCompleted)
            try { owner.execute(port, "commit", "commit".toByteArray()); fail() } catch (_: LocalInferenceBusy) { }
            assertEquals(0, port.commits.get())
        } finally { release.countDown() }
        assertEquals("ready", preparing.await().toString(Charsets.UTF_8))
        assertEquals("accepted-receipt", owner.execute(port, "commit", "commit".toByteArray()).toString(Charsets.UTF_8))
        assertEquals(1, port.commits.get())
        // SDK close had returned and Ready was visible. This newly observed violation fences the
        // same owner synchronously; its native invalidation remains independently observable.
        conversation.text("observed late after engine close")
        uncertain { owner.execute(port, "commit", "commit".toByteArray()) }
        uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
        eventually { owner.nativeInvalidatedKnown }
        assertEquals(1, port.closes.get()); assertEquals(1, port.commits.get())
        assertEquals(1, port.deliveries.get()) // Accepted history was not rolled back or duplicated.
    }

    @Test fun nativeTicketCancellationReachesActiveSdkCallAndDropsItsLateOutput() = runBlocking {
        val resources = Resources()
        val trace = LiteRtWorkerTrace()
        val config = config().copy(deadlineMs = 2000)
        val owner = config.createOwner(LocalInferenceLimits(turnMs = 2000, cleanupMs = 500, pollMs = 2), resources, trace)
        val port = Port(request)
        val preparing = async { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
        eventually { resources.engines.firstOrNull()?.conversations?.firstOrNull()?.sent?.count == 0L }
        val conversation = resources.engines.single().conversations.single()
        conversation.cancelAction = {
            conversation.text("late generated bytes")
            conversation.callbacks.error(true)
        }
        port.invalidate()
        assertEquals("cancelled", withTimeout(2000) { preparing.await() }.toString(Charsets.UTF_8))
        assertEquals(1, conversation.cancels.get()); assertEquals(1, conversation.closes.get())
        assertEquals(1, resources.engines.single().closes.get()); assertEquals(0, port.deliveries.get())
        assertEquals(0, port.commits.get()); assertFalse(owner.quarantined)
        val observed = trace.snapshot()
        for (event in listOf(LiteRtWorkerEvent.CANCEL_ENTERED, LiteRtWorkerEvent.CANCEL_RETURNED,
            LiteRtWorkerEvent.ERROR_ENTERED, LiteRtWorkerEvent.ERROR_RETURNED,
            LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN, LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)) {
            assertEquals(event.name, 1, observed.counts.getValue(event))
        }
        owner.close(); eventually { owner.nativeInvalidatedKnown }
    }

    @Test fun unknownSdkCloseInvalidatesSamePairedLeaseAndNeverReturnsReady() = runBlocking {
        val resources = Resources()
        val conversation = Conversation().also { it.closeAction = { throw AssertionError("private native delete error") } }
        resources.next.conversationAction = { conversation }
        val config = config().copy(deadlineMs = 2000)
        val owner = config.createOwner(LocalInferenceLimits(turnMs = 2000, cleanupMs = 500, pollMs = 2), resources)
        val port = Port(request)
        val preparing = async {
            uncertain { owner.execute(port, "prepare", "prepare".toByteArray(), "cancel".toByteArray()) }
        }
        eventually { resources.engines.firstOrNull()?.conversations?.firstOrNull()?.sent?.count == 0L }
        conversation.text("{}"); conversation.done(); preparing.await()
        uncertain { owner.execute(port, "commit", "commit".toByteArray()) }
        eventually { owner.nativeInvalidatedKnown }
        assertTrue(owner.quarantined); assertEquals(1, port.closes.get()); assertEquals(0, port.commits.get())
        assertEquals(0, resources.engines.single().closes.get()); assertEquals(0, port.deliveries.get())
    }

    @Test fun oldLateCallbackDuringNextInitializationCannotClearStickyUncertainty() = runBlocking {
        val resources = Resources()
        val worker = LiteRtRoleWorker(config(), resources)
        val firstEngine = worker.open()
        val firstCall = firstEngine.start(request)
        val oldConversation = resources.engines.single().conversations.single()
        oldConversation.done(); firstCall.await(); healthyClose(firstCall, firstEngine)
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        resources.next.initializeAction = { entered.countDown(); release.boundedAwait() }
        val secondOpen = async { uncertain { worker.open() } }
        try {
            eventually { entered.count == 0L }
            oldConversation.text("late from previous engine")
            assertFalse(firstEngine.close()) // Idempotent close cannot erase new observed uncertainty.
        } finally { release.countDown() }
        secondOpen.await()
        assertEquals(2, resources.engines.size)
        assertEquals(0, resources.engines.last().closes.get()) // Unreturned owner remains retained.
        try { worker.open(); fail() } catch (_: IllegalStateException) { }
    }
}
