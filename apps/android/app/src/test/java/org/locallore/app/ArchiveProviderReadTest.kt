/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.IOException
import java.io.InputStream
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** Exercises the provider adapter on the host; Android descriptor behavior is separate. */
class ArchiveProviderReadTest {
    @Test fun cancellationReachesBlockedOpenOffTheCallingThread() = runBlocking {
        val caller = Thread.currentThread()
        val openThread = CompletableDeferred<Thread>()
        val cancelThread = CompletableDeferred<Thread>()
        val releaseOpen = CountDownLatch(1)
        val published = AtomicInteger()
        val operation = launch {
            readArchiveFromProvider(
                open = {
                    openThread.complete(Thread.currentThread())
                    releaseOpen.awaitRelease()
                    throw IOException("private provider cancellation")
                },
                cancelOpen = {
                    cancelThread.complete(Thread.currentThread())
                    releaseOpen.countDown()
                },
            )
            published.incrementAndGet()
        }

        try {
            val opener = withTimeout(5_000) { openThread.await() }
            assertNotSame(caller, opener)
            operation.cancel()
            val canceller = withTimeout(5_000) { cancelThread.await() }
            assertNotSame(caller, canceller)
            assertNotSame(opener, canceller)
            withTimeout(5_000) { operation.join() }
            assertTrue(operation.isCancelled)
            assertEquals(0, published.get())
        } finally {
            releaseOpen.countDown()
        }
    }

    @Test fun lateStreamClosesOnceAndCancellationListenerDrainsBeforeCompletion() = runBlocking {
        val openEntered = CompletableDeferred<Unit>()
        val cancelEntered = CompletableDeferred<Unit>()
        val closed = CompletableDeferred<Unit>()
        val releaseOpen = CountDownLatch(1)
        val releaseCancel = CountDownLatch(1)
        val closes = AtomicInteger()
        val reads = AtomicInteger()
        val published = AtomicInteger()
        val stream = object : ByteArrayInputStream(byteArrayOf(11, 12)) {
            override fun read(): Int {
                reads.incrementAndGet()
                return super.read()
            }

            override fun read(bytes: ByteArray, offset: Int, count: Int): Int {
                reads.incrementAndGet()
                return super.read(bytes, offset, count)
            }

            override fun close() {
                closes.incrementAndGet()
                super.close()
                closed.complete(Unit)
            }
        }
        val operation = launch {
            readArchiveFromProvider(
                open = {
                    openEntered.complete(Unit)
                    releaseOpen.awaitRelease()
                    stream
                },
                cancelOpen = {
                    cancelEntered.complete(Unit)
                    releaseCancel.awaitRelease()
                },
            )
            published.incrementAndGet()
        }

        try {
            withTimeout(5_000) { openEntered.await() }
            operation.cancel()
            withTimeout(5_000) { cancelEntered.await() }
            assertFalse(operation.isCompleted)
            releaseOpen.countDown()
            withTimeout(5_000) { closed.await() }
            assertFalse(operation.isCompleted)
            releaseCancel.countDown()
            withTimeout(5_000) { operation.join() }
            assertEquals(1, closes.get())
            assertEquals(0, reads.get())
            assertEquals(0, published.get())
        } finally {
            releaseOpen.countDown()
            releaseCancel.countDown()
        }
    }

    @Test fun cancelledQueuedImportNeverOpensOrSignalsTheProvider() = runBlocking(Dispatchers.IO) {
        val openEntered = CompletableDeferred<Unit>()
        val releaseOpen = CountDownLatch(1)
        val queuedCalls = AtomicInteger()
        val held = launch {
            assertArrayEquals(byteArrayOf(7), readArchiveFromProvider(
                open = {
                    openEntered.complete(Unit)
                    releaseOpen.awaitRelease()
                    ByteArrayInputStream(byteArrayOf(7))
                },
                cancelOpen = {},
            ))
        }

        try {
            withTimeout(5_000) { openEntered.await() }
            // Enter the IO adapter inline so the occupied slot is the first suspension.
            val queued = launch(start = CoroutineStart.UNDISPATCHED) {
                readArchiveFromProvider(
                    open = {
                        queuedCalls.incrementAndGet()
                        ByteArrayInputStream(byteArrayOf(8))
                    },
                    cancelOpen = { queuedCalls.incrementAndGet() },
                )
            }
            queued.cancel()
            withTimeout(5_000) { queued.join() }
            assertTrue(queued.isCancelled)
            assertEquals(0, queuedCalls.get())
        } finally {
            releaseOpen.countDown()
        }
        withTimeout(5_000) { held.join() }
        assertArrayEquals(byteArrayOf(9), readArchiveFromProvider(
            open = { ByteArrayInputStream(byteArrayOf(9)) },
            cancelOpen = {},
        ))
        assertEquals(0, queuedCalls.get())
    }

    @Test fun successfulReadPreservesBytesAndUnavailableProvidersExposeFixedErrors() = runBlocking {
        val bytes = byteArrayOf(0, 1, -1)
        val closes = AtomicInteger()
        val cancels = AtomicInteger()
        val source = object : ByteArrayInputStream(bytes) {
            override fun close() {
                closes.incrementAndGet()
                super.close()
            }
        }
        assertArrayEquals(bytes, readArchiveFromProvider(
            open = { source },
            cancelOpen = { cancels.incrementAndGet() },
        ))
        assertEquals(1, closes.get())

        val unavailable: List<() -> InputStream?> = listOf(
            { null },
            { throw IOException("private content://provider/story") },
        )
        for (open in unavailable) {
            val failure = runCatching {
                readArchiveFromProvider(open) { cancels.incrementAndGet() }
            }.exceptionOrNull() as? ArchiveFailure
            assertEquals("Io", failure?.category)
            assertEquals("Archive operation failed", failure?.message)
            assertNull(failure?.cause)
        }
        assertEquals(0, cancels.get())
    }

    @Test fun cancelledBulkReadDoesNotStartTheSingleByteFallback() = runBlocking {
        val readEntered = CompletableDeferred<Unit>()
        val releaseRead = CountDownLatch(1)
        val fallbackReads = AtomicInteger()
        val closes = AtomicInteger()
        val source = object : InputStream() {
            override fun read(bytes: ByteArray, offset: Int, count: Int): Int {
                readEntered.complete(Unit)
                releaseRead.awaitRelease()
                return 0
            }

            override fun read(): Int {
                fallbackReads.incrementAndGet()
                return -1
            }

            override fun close() { closes.incrementAndGet() }
        }
        val operation = launch { readArchiveFromProvider(open = { source }, cancelOpen = {}) }
        try {
            withTimeout(5_000) { readEntered.await() }
            operation.cancel()
        } finally {
            releaseRead.countDown()
        }
        withTimeout(5_000) { operation.join() }
        assertEquals(0, fallbackReads.get())
        assertEquals(1, closes.get())
    }

    private fun CountDownLatch.awaitRelease() {
        check(await(10, TimeUnit.SECONDS)) { "Test provider did not receive its release" }
    }
}
