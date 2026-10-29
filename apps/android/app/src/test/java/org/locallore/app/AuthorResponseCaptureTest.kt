/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Test

class AuthorResponseCaptureTest {
    @Test fun firstFullUtf8ResponseAndEverySnapshotAreDefensiveCopies() {
        val capture = AuthorResponseCapture()
        val original = "é".repeat(4096).toByteArray(Charsets.UTF_8)
        capture.observe("author", original)
        val before = capture.snapshot()
        original.fill(0)
        before.responseBytes()!!.fill(1)
        assertEquals(AuthorResponseCaptureState.RECORDED, before.state)
        assertEquals(1, before.calls)
        assertArrayEquals("é".repeat(4096).toByteArray(), before.responseBytes())
        assertArrayEquals(before.responseBytes(), capture.snapshot().responseBytes())
        assertFalse(before.toString().contains("é"))
        assertFalse(capture.toString().contains("é"))
    }

    @Test fun emptyOverflowAndMalformedUtf8RemainInvalidWithoutTruncating() {
        for (bytes in listOf(byteArrayOf(), ByteArray(8193) { 65 }, byteArrayOf(0xc3.toByte(), 0x28))) {
            val capture = AuthorResponseCapture()
            capture.observe("author", bytes)
            val snapshot = capture.snapshot()
            assertEquals(AuthorResponseCaptureState.INVALID, snapshot.state)
            assertEquals(1, snapshot.calls)
            assertNull(snapshot.responseBytes())
        }
    }

    @Test fun nonAuthorRolesCannotAllocateOrInvalidateAnObservation() {
        val capture = AuthorResponseCapture()
        for (role in listOf("director", "narrator", "tool", "AUTHOR", "")) capture.observe(role, ByteArray(8193))
        val snapshot = capture.snapshot()
        assertEquals(AuthorResponseCaptureState.EMPTY, snapshot.state)
        assertEquals(0, snapshot.calls)
        assertNull(snapshot.responseBytes())
        capture.observe("author", "SYNTHETIC first proposal".toByteArray())
        capture.observe("director", byteArrayOf())
        assertEquals(AuthorResponseCaptureState.RECORDED, capture.snapshot().state)
        assertEquals(1, capture.snapshot().calls)
    }

    @Test fun duplicateNeverReplacesFirstBytesAndCountersSaturate() {
        val capture = AuthorResponseCapture()
        capture.observe("author", "SYNTHETIC first".toByteArray())
        val first = capture.snapshot()
        repeat(100) { capture.observe("author", "different $it".toByteArray()) }
        val duplicate = capture.snapshot()
        assertEquals(AuthorResponseCaptureState.DUPLICATE, duplicate.state)
        assertEquals(2, duplicate.calls)
        assertArrayEquals("SYNTHETIC first".toByteArray(), duplicate.responseBytes())
        assertEquals(AuthorResponseCaptureState.RECORDED, first.state)
        assertEquals(1, first.calls)
        capture.snapshot().responseBytes()!!.fill(0)
        assertArrayEquals(first.responseBytes(), capture.snapshot().responseBytes())
    }

    @Test fun aDuplicateCannotTurnAnInvalidFirstObservationIntoRecordedBytes() {
        val capture = AuthorResponseCapture()
        capture.observe("author", byteArrayOf())
        capture.observe("author", "valid later".toByteArray())
        assertEquals(AuthorResponseCaptureState.DUPLICATE, capture.snapshot().state)
        assertEquals(2, capture.snapshot().calls)
        assertNull(capture.snapshot().responseBytes())
    }

    @Test fun concurrentAuthorObservationsRetainExactlyOneBoundedFirstCopy() {
        val capture = AuthorResponseCapture()
        val start = CountDownLatch(1)
        val done = CountDownLatch(2)
        val threads = listOf("original one", "original two").map { value ->
            Thread {
                try { check(start.await(2, TimeUnit.SECONDS)); capture.observe("author", value.toByteArray()) }
                finally { done.countDown() }
            }.also { it.start() }
        }
        start.countDown()
        assertTrue(done.await(3, TimeUnit.SECONDS))
        threads.forEach { it.join(1_000); assertFalse(it.isAlive) }
        val snapshot = capture.snapshot()
        assertEquals(AuthorResponseCaptureState.DUPLICATE, snapshot.state)
        assertEquals(2, snapshot.calls)
        assertTrue(snapshot.responseBytes()!!.toString(Charsets.UTF_8) in setOf("original one", "original two"))
    }
}
