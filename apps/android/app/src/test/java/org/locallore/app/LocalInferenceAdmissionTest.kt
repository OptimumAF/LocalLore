/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.yield
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Real blocking fake native calls exercise both directions of the generation admission fence. */
class LocalInferenceAdmissionTest {
    private class Gate(private val reply: ByteArray = "terminal".toByteArray()) {
        private val entered = CountDownLatch(1)
        private val release = CountDownLatch(1)
        private val finished = CountDownLatch(1)

        fun call(): ByteArray {
            entered.countDown()
            try {
                check(release.await(8, TimeUnit.SECONDS)) { "Test did not release the fake native command" }
                return reply.copyOf()
            } finally {
                finished.countDown()
            }
        }

        fun assertEntered() = assertTrue("Fake native command did not start", entered.await(4, TimeUnit.SECONDS))
        fun release() = release.countDown()
        fun waitIfEntered() {
            if (entered.count == 0L)
                assertTrue("Fake native command did not finish", finished.await(4, TimeUnit.SECONDS))
        }
    }

    private class Port(
        private val commands: Map<String, Gate>,
        private val closeGate: Gate? = null,
        private val terminalOnCancel: Gate? = null,
    ) : LocalInferenceNativePort {
        val calls = ConcurrentLinkedQueue<String>()
        val closes = AtomicInteger()
        val closed = CountDownLatch(1)

        override fun call(input: ByteArray): ByteArray {
            val operation = input.toString(Charsets.UTF_8)
            calls.add(operation)
            if (operation == "cancel") terminalOnCancel?.release()
            return commands[operation]?.call() ?: "$operation-terminal".toByteArray()
        }

        override fun poll(): LocalInferencePending? = null
        override fun respond(ticket: Long, response: ByteArray): Boolean =
            error("The fake native port never asks for a role response")

        override fun close() {
            closes.incrementAndGet()
            closeGate?.call()
            closed.countDown()
        }

        fun clean(owner: LocalInferenceOwner) {
            commands.values.forEach(Gate::release)
            closeGate?.release()
            owner.close()
            commands.values.forEach(Gate::waitIfEntered)
            assertTrue("Fake native close did not finish", closed.await(4, TimeUnit.SECONDS))
        }
    }

    private val generation = listOf("prepare", "authoring_generate")

    private fun owner() = LocalInferenceOwner(
        "{}".toByteArray(),
        LocalRoleWorker { error("The fake native port never requests an SDK role") },
        Dispatchers.IO,
        LocalInferenceLimits(turnMs = 5_000, cleanupMs = 5_000, pollMs = 2, authorMs = 5_000),
    )

    private suspend fun LocalInferenceOwner.call(port: Port, operation: String): String {
        val cancel = when (operation) {
            "prepare" -> "cancel".toByteArray()
            "authoring_generate" -> "authoring_cancel".toByteArray()
            else -> null
        }
        return execute(port, operation, operation.toByteArray(), cancel).toString(Charsets.UTF_8)
    }

    private suspend fun assertBothBusy(owner: LocalInferenceOwner, port: Port) {
        for (operation in generation) {
            val failure = runCatching { owner.call(port, operation) }.exceptionOrNull()
            assertTrue("$operation should be busy before dispatch, observed $failure", failure is LocalInferenceBusy)
        }
    }

    private suspend fun assertBothAvailable(owner: LocalInferenceOwner, port: Port) {
        for (operation in generation) assertEquals("$operation-terminal", owner.call(port, operation))
        assertFalse(owner.quarantined)
        assertEquals(0, port.closes.get())
    }

    @Test fun overlappingOpenAndCommitBlockBothGenerationsUntilTheLastReplySettles() = runBlocking {
        val owner = owner()
        val openGate = Gate()
        val commitGate = Gate()
        val port = Port(mapOf("open" to openGate, "commit" to commitGate))
        val opening = async { runCatching { owner.call(port, "open") } }
        val committing = async { runCatching { owner.call(port, "commit") } }
        try {
            yield()
            openGate.assertEntered()
            commitGate.assertEntered()
            assertBothBusy(owner, port)
            assertEquals(2, port.calls.size)
            assertEquals(setOf("open", "commit"), port.calls.toSet())

            openGate.release()
            assertEquals("terminal", withTimeout(5_000) { opening.await().getOrThrow() })
            assertBothBusy(owner, port)
            assertEquals(2, port.calls.size)

            commitGate.release()
            assertEquals("terminal", withTimeout(5_000) { committing.await().getOrThrow() })
            assertBothAvailable(owner, port)
            assertEquals(generation, port.calls.toList().drop(2))
        } finally {
            port.clean(owner)
        }
    }

    @Test fun canceledInspectionStillBlocksGenerationUntilNativeTerminalBytesAreObserved() = runBlocking {
        val owner = owner()
        val readGate = Gate()
        val port = Port(mapOf("inspection_query" to readGate))
        val outcome = CompletableDeferred<Result<String>>()
        val reader = launch { outcome.complete(runCatching { owner.call(port, "inspection_query") }) }
        try {
            yield()
            readGate.assertEntered()
            reader.cancel()
            yield()
            assertFalse(outcome.isCompleted)
            assertFalse(owner.quarantined)
            assertBothBusy(owner, port)
            assertEquals(listOf("inspection_query"), port.calls.toList())

            readGate.release()
            withTimeout(5_000) { reader.join() }
            assertTrue(outcome.await().exceptionOrNull() is CancellationException)
            assertBothAvailable(owner, port)
            assertEquals(listOf("inspection_query") + generation, port.calls.toList())
        } finally {
            port.clean(owner)
        }
    }

    @Test fun allowedStatusCanOverlapGenerationAndCancelStillReachesTheActiveRun() = runBlocking {
        val owner = owner()
        val statusGate = Gate()
        val runGate = Gate()
        val port = Port(mapOf("turn_status" to statusGate, "prepare" to runGate), terminalOnCancel = runGate)
        val status = async { runCatching { owner.call(port, "turn_status") } }
        try {
            yield()
            statusGate.assertEntered()
            val preparing = async { runCatching { owner.call(port, "prepare") } }
            yield()
            runGate.assertEntered()
            assertEquals("authoring_status-terminal", owner.call(port, "authoring_status"))
            assertEquals("cancel-terminal", owner.call(port, "cancel"))
            assertEquals("terminal", withTimeout(5_000) { preparing.await().getOrThrow() })
            assertFalse(status.isCompleted)
            assertEquals(listOf("turn_status", "prepare", "authoring_status", "cancel"), port.calls.toList())
            assertFalse(owner.quarantined)

            statusGate.release()
            assertEquals("terminal", withTimeout(5_000) { status.await().getOrThrow() })
        } finally {
            port.clean(owner)
        }
    }

    @Test fun malformedFiniteReplyStillRefusesGenerationWhileInvalidationIsPending() = runBlocking {
        val owner = owner()
        val commitGate = Gate(byteArrayOf(0xc3.toByte(), 0x28))
        val closeGate = Gate()
        val port = Port(mapOf("commit" to commitGate), closeGate = closeGate)
        val committing = async { runCatching { owner.call(port, "commit") } }
        try {
            yield()
            commitGate.assertEntered()
            assertBothBusy(owner, port)

            commitGate.release()
            // The committing coroutine must resume to classify the terminal bytes.
            withTimeout(5_000) { while (port.closes.get() == 0) yield() }
            closeGate.assertEntered()
            assertTrue(owner.quarantined)
            assertFalse(owner.nativeInvalidatedKnown)
            for (operation in generation) {
                val failure = runCatching { owner.call(port, operation) }.exceptionOrNull()
                assertTrue(failure is LocalInferenceUncertain)
            }
            assertEquals(listOf("commit"), port.calls.toList())

            closeGate.release()
            assertTrue(withTimeout(5_000) { committing.await().exceptionOrNull() } is LocalInferenceUncertain)
            assertTrue(owner.nativeInvalidatedKnown)
            assertEquals(1, port.closes.get())
        } finally {
            port.clean(owner)
        }
    }
}
