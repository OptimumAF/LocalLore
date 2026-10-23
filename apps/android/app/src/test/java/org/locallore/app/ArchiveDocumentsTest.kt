/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import org.junit.Assert.*
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException

/** Portable stream tests only; actual SAF/PFD behavior requires device/provider verification. */
class ArchiveDocumentsTest {
    @Test fun readerAcceptsExactCapAndProbesOneAdditionalByteWithoutTrustingMetadata() {
        val exact = Input(byteArrayOf(1, 2, 3, 4))
        assertArrayEquals(byteArrayOf(1, 2, 3, 4), readBoundedArchive(exact, 4))
        assertTrue(exact.closed)
        val overflow = Input(byteArrayOf(1, 2, 3, 4, 5, 6))
        try { readBoundedArchive(overflow, 4); fail("Overflow accepted") }
        catch (failure: ArchiveFailure) { assertEquals("TooLarge", failure.category) }
        assertTrue(overflow.closed)
        assertEquals("Reader consumed more than its cap plus overflow probe", 1, overflow.available())
        assertEquals(32 * 1024 * 1024, MAX_ARCHIVE_BYTES)
    }

    @Test fun zeroLengthBulkReadStillMakesBoundedProgressAndClosesTheSource() {
        val input = object : Input(byteArrayOf(1, 2, 3)) {
            var first = true
            override fun read(bytes: ByteArray, offset: Int, count: Int): Int {
                if (first) { first = false; return 0 }
                return super.read(bytes, offset, count)
            }
        }
        assertArrayEquals(byteArrayOf(1, 2, 3), readBoundedArchive(input, 4))
        assertTrue(input.closed)
    }

    @Test fun unverifiableOrNonemptyOpenedTargetIsClosedWithoutWritingOrFlushing() {
        for ((size, position) in listOf(-1L to 0L, 1L to 0L, 0L to 1L)) {
            val output = Sink(size, position)
            try { writeEmptyArchive(output, byteArrayOf(1)); fail("Unsafe target accepted") }
            catch (failure: ArchiveFailure) { assertEquals("Io", failure.category) }
            assertTrue(output.closed)
            assertEquals(0, output.writes)
            assertFalse(output.flushed)
        }
    }

    @Test fun writerPreservesExactPayloadAndClosesOnlyItsOpenedSink() {
        val output = Sink()
        val bytes = ByteArray(40000) { (it % 127).toByte() }
        writeEmptyArchive(output, bytes)
        assertArrayEquals(bytes, output.output.toByteArray())
        assertEquals(3, output.writes)
        assertTrue(output.flushed)
        assertTrue(output.closed)
    }

    @Test fun cancellationAfterAPartialNewWriteClosesButNeverClaimsRollback() {
        val output = Sink()
        var checks = 0
        try {
            writeEmptyArchive(output, ByteArray(40000) { 1 }) {
                if (++checks == 3) throw CancellationException("synthetic cancellation")
            }
            fail("Cancellation ignored")
        } catch (_: CancellationException) { }
        assertEquals(16384, output.output.size())
        assertTrue(output.closed)
        assertFalse(output.flushed)
    }

    @Test fun cancelledReadsAndPrivateIoErrorsCloseResourcesAndExposeOnlyFixedFailures() {
        val cancelled = Input(ByteArray(32))
        try { readBoundedArchive(cancelled, 32) { throw CancellationException("stop") }; fail("Read was not cancelled") }
        catch (_: CancellationException) { }
        assertTrue(cancelled.closed)
        val input = object : Input(byteArrayOf(1)) {
            override fun read(bytes: ByteArray, offset: Int, count: Int): Int = throw IOException("PRIVATE content://provider/path")
        }
        try { readBoundedArchive(input); fail("Read error ignored") }
        catch (failure: ArchiveFailure) {
            assertEquals("Io", failure.category)
            assertEquals("Archive operation failed", failure.message)
            assertNull(failure.cause)
        }
        assertTrue(input.closed)
        val sink = object : Sink() {
            override fun write(bytes: ByteArray, offset: Int, count: Int) { throw IOException("PRIVATE provider filename") }
        }
        try { writeEmptyArchive(sink, byteArrayOf(1)); fail("Write error ignored") }
        catch (failure: ArchiveFailure) { assertEquals("Io", failure.category); assertNull(failure.cause) }
        assertTrue(sink.closed)
    }

    @Test fun emptyOutputPayloadCannotTouchTheTarget() {
        val output = Sink()
        try { writeEmptyArchive(output, byteArrayOf()); fail("Empty export accepted") }
        catch (failure: ArchiveFailure) { assertEquals("TooLarge", failure.category) }
        assertEquals(0, output.writes)
        assertTrue(output.closed)
    }

    private open class Input(bytes: ByteArray) : ByteArrayInputStream(bytes) {
        var closed = false
        override fun close() { closed = true; super.close() }
    }
    private open class Sink(private val initialSize: Long = 0, private val initialPosition: Long = 0) : ArchiveDocumentSink {
        val output = ByteArrayOutputStream()
        var closed = false; var flushed = false; var writes = 0
        override fun size() = initialSize
        override fun position() = initialPosition
        override fun write(bytes: ByteArray, offset: Int, count: Int) { writes++; output.write(bytes, offset, count) }
        override fun flush() { flushed = true }
        override fun close() { closed = true }
    }
}
