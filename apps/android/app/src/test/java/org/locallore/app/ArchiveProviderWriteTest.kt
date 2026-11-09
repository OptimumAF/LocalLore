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
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** JVM coverage of the export adapter. Android descriptor behavior is separate. */
class ArchiveProviderWriteTest {
    @Test fun cancellationReachesBlockedExportOpenOffTheCallingThread() = runBlocking {
        val caller = Thread.currentThread()
        val opened = CompletableDeferred<Thread>()
        val signalled = CompletableDeferred<Thread>()
        val release = CountDownLatch(1)
        val returned = AtomicInteger()
        val operation = launch {
            writeArchiveToProvider(
                open = {
                    opened.complete(Thread.currentThread())
                    release.awaitRelease()
                    throw IOException("private export open cancelled")
                },
                cancelOpen = {
                    signalled.complete(Thread.currentThread())
                    release.countDown()
                },
                bytes = byteArrayOf(1),
            )
            returned.incrementAndGet()
        }
        try {
            val opener = withTimeout(5_000) { opened.await() }
            assertNotSame(caller, opener)
            operation.cancel()
            val canceller = withTimeout(5_000) { signalled.await() }
            assertNotSame(caller, canceller)
            assertNotSame(opener, canceller)
            withTimeout(5_000) { operation.join() }
            assertTrue(operation.isCancelled)
            assertEquals(0, returned.get())
        } finally {
            release.countDown()
        }
    }

    @Test fun lateExportSinkClosesWithoutIoAndCancellationListenerDrains() = runBlocking {
        val openEntered = CompletableDeferred<Unit>()
        val cancelEntered = CompletableDeferred<Unit>()
        val closed = CompletableDeferred<Unit>()
        val releaseOpen = CountDownLatch(1)
        val releaseCancel = CountDownLatch(1)
        val sink = Sink(onClose = { closed.complete(Unit) })
        val returned = AtomicInteger()
        val operation = launch {
            writeArchiveToProvider(
                open = {
                    openEntered.complete(Unit)
                    releaseOpen.awaitRelease()
                    sink
                },
                cancelOpen = {
                    cancelEntered.complete(Unit)
                    releaseCancel.awaitRelease()
                },
                bytes = byteArrayOf(2),
            )
            returned.incrementAndGet()
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
            assertEquals(listOf("close"), sink.calls)
            assertEquals(0, returned.get())
        } finally {
            releaseOpen.countDown()
            releaseCancel.countDown()
        }
    }

    @Test fun cancellingAQueuedExportNeverOpensOrSignalsItsProvider() = runBlocking(Dispatchers.IO) {
        val openEntered = CompletableDeferred<Unit>()
        val release = CountDownLatch(1)
        val queuedCalls = AtomicInteger()
        val sink = Sink()
        val held = launch {
            writeArchiveToProvider(
                open = {
                    openEntered.complete(Unit)
                    release.awaitRelease()
                    sink
                },
                cancelOpen = {},
                bytes = byteArrayOf(3),
            )
        }
        try {
            withTimeout(5_000) { openEntered.await() }
            // Enter the IO adapter inline so the occupied slot is the first suspension.
            val queued = launch(start = CoroutineStart.UNDISPATCHED) {
                writeArchiveToProvider(
                    open = {
                        queuedCalls.incrementAndGet()
                        Sink()
                    },
                    cancelOpen = { queuedCalls.incrementAndGet() },
                    bytes = byteArrayOf(4),
                )
            }
            queued.cancel()
            withTimeout(5_000) { queued.join() }
            assertTrue(queued.isCancelled)
            assertEquals(0, queuedCalls.get())
        } finally {
            release.countDown()
        }
        withTimeout(5_000) { held.join() }
        assertArrayEquals(byteArrayOf(3), sink.contents.toByteArray())
        val next = Sink()
        writeArchiveToProvider({ next }, {}, byteArrayOf(5))
        assertArrayEquals(byteArrayOf(5), next.contents.toByteArray())
        assertEquals(0, queuedCalls.get())
    }

    @Test fun writesOnlyToAnEmptySinkAndClosesExactlyOnce() = runBlocking {
        val payload = byteArrayOf(0, 1, -1)
        val empty = Sink()
        writeArchiveToProvider({ empty }, { error("Unexpected cancellation") }, payload)
        assertArrayEquals(payload, empty.contents.toByteArray())
        assertEquals(listOf("size", "position", "write", "flush", "close"), empty.calls)

        val nonempty = Sink(initialSize = 1)
        assertFixedIo { writeArchiveToProvider({ nonempty }, {}, payload) }
        assertEquals(listOf("size", "close"), nonempty.calls)
        val nonzeroPosition = Sink(initialPosition = 1)
        assertFixedIo { writeArchiveToProvider({ nonzeroPosition }, {}, payload) }
        assertEquals(listOf("size", "position", "close"), nonzeroPosition.calls)
    }

    @Test fun providerFailuresAndInvalidPayloadsExposeOnlyFixedIo() = runBlocking {
        assertFixedIo { writeArchiveToProvider({ null }, {}, byteArrayOf(1)) }
        assertFixedIo {
            writeArchiveToProvider({ throw IOException("private content://provider/story") }, {}, byteArrayOf(1))
        }
        val providerCalls = AtomicInteger()
        val open = {
            providerCalls.incrementAndGet()
            Sink()
        }
        val cancelOpen: () -> Unit = { providerCalls.incrementAndGet() }
        assertFixedIo { writeArchiveToProvider(open, cancelOpen, byteArrayOf()) }
        assertFixedIo { writeArchiveToProvider(open, cancelOpen, ByteArray(MAX_ARCHIVE_BYTES + 1)) }
        assertEquals(0, providerCalls.get())
    }

    private class Sink(
        private val initialSize: Long = 0,
        private val initialPosition: Long = 0,
        private val onClose: () -> Unit = {},
    ) : ArchiveDocumentSink {
        val calls = mutableListOf<String>()
        val contents = ByteArrayOutputStream()

        override fun size(): Long {
            calls.add("size")
            return initialSize
        }

        override fun position(): Long {
            calls.add("position")
            return initialPosition
        }

        override fun write(bytes: ByteArray, offset: Int, count: Int) {
            calls.add("write")
            contents.write(bytes, offset, count)
        }

        override fun flush() { calls.add("flush") }

        override fun close() {
            calls.add("close")
            onClose()
        }
    }

    private suspend fun assertFixedIo(block: suspend () -> Unit) {
        val failure = runCatching { block() }.exceptionOrNull() as? ArchiveFailure
        assertEquals("Io", failure?.category)
        assertEquals("Archive operation failed", failure?.message)
        assertNull(failure?.cause)
    }

    private fun CountDownLatch.awaitRelease() {
        check(await(10, TimeUnit.SECONDS)) { "Test provider did not receive its release" }
    }
}
