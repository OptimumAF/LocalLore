/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.yield
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** A blocked JVM fake native call exercises owner handoff without opening any SDK. */
@OptIn(ExperimentalCoroutinesApi::class)
class LocalInferenceReadCancellationTest {
    private class Port(
        private val blocked: String,
        private val terminal: ByteArray = """{"version":1,"status":"ok","data":{}}""".toByteArray(),
    ) : LocalInferenceNativePort {
        val calls = ConcurrentLinkedQueue<String>()
        val entered = CountDownLatch(1)
        val finished = CountDownLatch(1)
        val invalidated = CountDownLatch(1)
        val closes = AtomicInteger()
        private val release = CountDownLatch(1)

        override fun call(input: ByteArray): ByteArray {
            val operation = input.toString(Charsets.UTF_8)
            calls.add(operation)
            if (operation != blocked) return "follow-up".toByteArray()
            entered.countDown()
            try {
                check(release.await(8, TimeUnit.SECONDS)) { "Test did not release fake native call" }
                return terminal.copyOf()
            } finally {
                finished.countDown()
            }
        }

        override fun poll(): LocalInferencePending? = error("Finite commands never poll a role worker")
        override fun respond(ticket: Long, response: ByteArray): Boolean =
            error("Finite commands never deliver a role response")

        override fun close() {
            closes.incrementAndGet()
            invalidated.countDown()
        }

        fun release() = release.countDown()
    }

    private fun owner(deadlineMs: Long = 5_000) = LocalInferenceOwner(
        "{}".toByteArray(), LocalRoleWorker { error("Test must not open a role worker") },
        Dispatchers.IO, LocalInferenceLimits(cleanupMs = deadlineMs),
    )

    private suspend fun LocalInferenceOwner.call(port: Port, operation: String) =
        execute(port, operation, operation.toByteArray())

    private fun Port.assertEntered() = assertTrue("Fake native dispatch did not begin", entered.await(4, TimeUnit.SECONDS))

    private fun clean(owner: LocalInferenceOwner, port: Port) {
        port.release()
        if (port.entered.count == 0L)
            assertTrue("Fake native dispatch did not terminate", port.finished.await(4, TimeUnit.SECONDS))
        owner.close()
        assertTrue("Owner did not invalidate the fake port on close", port.invalidated.await(4, TimeUnit.SECONDS))
    }

    @Test fun canceledDispatchedReadsWaitForValidNativeCompletionAndKeepOwnerUsable() = runBlocking {
        for (operation in listOf("inspection_query", "play_presentation_v2")) {
            val owner = owner()
            val port = Port(operation)
            val outcome = CompletableDeferred<Result<ByteArray>>()
            val caller = launch { outcome.complete(runCatching { owner.call(port, operation) }) }
            try {
                yield()
                port.assertEntered()
                caller.cancel()
                yield()
                assertFalse("Cancellation must await terminal bytes", outcome.isCompleted)
                assertFalse(owner.quarantined)
                assertEquals(0, port.closes.get())

                port.release()
                withTimeout(5_000) { caller.join() }
                assertTrue(outcome.await().exceptionOrNull() is CancellationException)
                assertFalse(owner.quarantined)
                assertFalse(owner.nativeInvalidatedKnown)
                assertEquals("follow-up", owner.call(port, "workspace").toString(Charsets.UTF_8))
                assertEquals(listOf(operation, "workspace"), port.calls.toList())
                assertEquals(0, port.closes.get())
            } finally {
                clean(owner, port)
            }
        }
    }

    @Test fun callerAlreadyCanceledDoesNotDispatchOrPoisonReadOwner() = runBlocking {
        for (operation in listOf("inspection_query", "play_presentation_v2")) {
            val owner = owner()
            val port = Port(operation)
            owner.attach(port)
            val outcome = CompletableDeferred<Result<ByteArray>>()
            try {
                launch {
                    currentCoroutineContext().cancel()
                    outcome.complete(runCatching { owner.call(port, operation) })
                }.join()
                assertTrue(outcome.await().exceptionOrNull() is CancellationException)
                assertEquals(emptyList<String>(), port.calls.toList())
                assertFalse(owner.quarantined)
                assertEquals("follow-up", owner.call(port, "workspace").toString(Charsets.UTF_8))
                assertEquals(listOf("workspace"), port.calls.toList())
            } finally {
                clean(owner, port)
            }
        }
    }

    @Test fun canceledReadUsesOriginalDeadlineWhenNativeCompletionRemainsUnknown() = runTest {
        val operation = "inspection_query"
        val owner = owner(deadlineMs = 200)
        val port = Port(operation)
        val outcome = CompletableDeferred<Result<ByteArray>>()
        val caller = launch { outcome.complete(runCatching { owner.call(port, operation) }) }
        try {
            runCurrent()
            port.assertEntered()
            advanceTimeBy(150)
            caller.cancel()
            runCurrent()
            assertFalse(outcome.isCompleted)
            assertFalse(owner.quarantined)

            advanceTimeBy(51)
            runCurrent()
            assertTrue("Cancellation must not restart the 200 ms command deadline", owner.quarantined)
            assertTrue(port.invalidated.await(4, TimeUnit.SECONDS))
            caller.join()
            assertTrue(outcome.await().isFailure)
            assertTrue(owner.nativeInvalidatedKnown)
            assertEquals(1, port.closes.get())
            assertEquals(1L, port.finished.count)
            assertTrue(runCatching { owner.call(port, "workspace") }.exceptionOrNull() is LocalInferenceUncertain)
            assertEquals(listOf(operation), port.calls.toList())
        } finally {
            clean(owner, port)
        }
    }

    @Test fun canceledReadWithInvalidTerminalBytesQuarantinesAndInvalidates() = runBlocking {
        val operation = "play_presentation_v2"
        val owner = owner()
        val port = Port(operation, byteArrayOf(0xc3.toByte(), 0x28))
        val outcome = CompletableDeferred<Result<ByteArray>>()
        val caller = launch { outcome.complete(runCatching { owner.call(port, operation) }) }
        try {
            yield()
            port.assertEntered()
            caller.cancel()
            yield()
            assertFalse(outcome.isCompleted)
            assertFalse(owner.quarantined)

            port.release()
            withTimeout(5_000) { caller.join() }
            assertTrue(outcome.await().isFailure)
            assertTrue(owner.quarantined)
            assertTrue(owner.nativeInvalidatedKnown)
            assertEquals(1, port.closes.get())
            assertTrue(runCatching { owner.call(port, "workspace") }.exceptionOrNull() is LocalInferenceUncertain)
            assertEquals(listOf(operation), port.calls.toList())
        } finally {
            clean(owner, port)
        }
    }

    @Test fun canceledDispatchedMutationStillQuarantinesWithoutAssumingRelease() = runBlocking {
        val operation = "commit"
        val owner = owner()
        val port = Port(operation)
        val outcome = CompletableDeferred<Result<ByteArray>>()
        val caller = launch { outcome.complete(runCatching { owner.call(port, operation) }) }
        try {
            yield()
            port.assertEntered()
            caller.cancel()
            withTimeout(5_000) { caller.join() }
            assertTrue(outcome.await().exceptionOrNull() is LocalInferenceUncertain)
            assertTrue(owner.quarantined)
            assertTrue(owner.nativeInvalidatedKnown)
            assertEquals(1, port.closes.get())
            assertEquals(1L, port.finished.count)
            assertTrue(runCatching { owner.call(port, "workspace") }.exceptionOrNull() is LocalInferenceUncertain)
            assertEquals(listOf(operation), port.calls.toList())
        } finally {
            clean(owner, port)
        }
    }

    @Test fun successfulReadBytesCannotPublishAfterOwnerCloses() = runBlocking {
        val operation = "inspection_query"
        val owner = owner()
        val port = Port(operation)
        val outcome = CompletableDeferred<Result<ByteArray>>()
        val caller = launch { outcome.complete(runCatching { owner.call(port, operation) }) }
        try {
            yield()
            port.assertEntered()
            owner.close()
            assertTrue(port.invalidated.await(4, TimeUnit.SECONDS))
            port.release()
            withTimeout(5_000) { caller.join() }
            assertTrue(outcome.await().isFailure)
            assertEquals(listOf(operation), port.calls.toList())
            assertEquals(1, port.closes.get())
        } finally {
            clean(owner, port)
        }
    }
}
