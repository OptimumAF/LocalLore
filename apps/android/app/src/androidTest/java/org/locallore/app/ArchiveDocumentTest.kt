/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.net.Uri
import android.os.Bundle
import android.system.Os
import android.system.OsConstants
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/** Real remote ContentResolver/PFD boundary; the provider owns only synthetic test-APK files. */
@RunWith(AndroidJUnit4::class)
class ArchiveDocumentTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val resolver get() = instrumentation.targetContext.contentResolver
    private val authority get() = instrumentation.context.packageName + ".archives"
    private fun uri(case: String) = Uri.parse("content://$authority/$case")
    private fun provider(method: String, arg: String? = null): Bundle =
        requireNotNull(resolver.call(authority, method, arg, null))

    @Before fun resetProvider() { provider("reset") }
    @After fun drainAndRemoveOnlySyntheticFixtures(): Unit = runBlocking {
        provider("release")
        awaitDrained()
        provider("reset")
    }

    @Test fun exactWritesUseEmptySeekableRegularRwDescriptorsAndCloseEveryOwner() = runBlocking {
        // Verify the actual opened provider descriptor, rather than metadata advertised by query().
        withContext(Dispatchers.IO) {
            requireNotNull(resolver.openFileDescriptor(uri("empty"), "rw")).use { descriptor ->
                assertEquals(0L, descriptor.statSize)
                assertTrue(OsConstants.S_ISREG(Os.fstat(descriptor.fileDescriptor).st_mode))
                assertEquals(0L, Os.lseek(descriptor.fileDescriptor, 0, OsConstants.SEEK_CUR))
            }
        }
        awaitStat("closed", 1)
        repeat(3) { index ->
            provider("new_empty")
            val bytes = "synthetic archive $index \u2603".toByteArray(Charsets.UTF_8)
            writeArchiveDocument(resolver, uri("empty"), bytes)
            awaitStat("closed", index + 2)
            assertArrayEquals(bytes, provider("bytes", "empty").getByteArray("bytes"))
        }
        assertEquals(4, provider("stats").getInt("opened"))
        assertEquals(4, provider("stats").getInt("rw"))
        assertEquals(0, provider("stats").getInt("forbidden_modes"))
    }

    @Test fun nonemptyDestinationIsPreservedAndReadOnlyDestinationFailsClosed() = runBlocking {
        val old = "SYNTHETIC_OLD_ARCHIVE_BYTES".toByteArray(Charsets.US_ASCII)
        expectFailure("Io") { writeArchiveDocument(resolver, uri("nonempty"), byteArrayOf(1, 2)) }
        awaitStat("closed", 1)
        assertArrayEquals(old, provider("bytes", "nonempty").getByteArray("bytes"))
        expectFailure("Io") { writeArchiveDocument(resolver, uri("read_only"), byteArrayOf(3)) }
        awaitStat("closed", 2)
        assertArrayEquals(byteArrayOf(), provider("bytes", "read_only").getByteArray("bytes"))
        assertEquals(0, provider("stats").getInt("forbidden_modes"))
    }

    @Test fun actualStreamAcceptsExact32MiBAndRejectsOneAdditionalByte() = runBlocking {
        val exact = readArchiveDocument(resolver, uri("exact_limit"))
        assertEquals(32 * 1024 * 1024, exact.size)
        assertTrue(exact.all { it == 0x5a.toByte() })
        exact.fill(0)
        awaitStat("closed", 1)
        // The overflow fixture is physically larger, and exposes no length through query().
        expectFailure("TooLarge") { readArchiveDocument(resolver, uri("overflow")) }
        awaitStat("closed", 2)
        assertEquals(2, provider("stats").getInt("reads"))
    }

    @Test fun unsupportedUrisAndProviderFailuresHaveFixedNotPrivateErrors() = runBlocking {
        for (destination in listOf(Uri.EMPTY, Uri.parse("file:///synthetic-private-archive"),
            Uri.parse("https://invalid.test/synthetic"))) {
            expectFailure("Io") { writeArchiveDocument(resolver, destination, byteArrayOf(1)) }
            expectFailure("Io") { readArchiveDocument(resolver, destination) }
        }
        assertEquals(0, provider("stats").getInt("started"))
        for (case in listOf("null", "failure")) {
            expectFailure("Io") { writeArchiveDocument(resolver, uri(case), byteArrayOf(1)) }
            expectFailure("Io") { readArchiveDocument(resolver, uri(case)) }
        }
        assertEquals(0, provider("stats").getInt("opened"))
        assertEquals(0, provider("stats").getInt("closed"))
    }

    @Test fun cancelledBlockedOpenKeepsMainResponsiveThenDrainsWithoutWritingAndAllowsRecovery() = runBlocking {
        val pending = launch(Dispatchers.Main) {
            writeArchiveDocument(resolver, uri("blockedopen"), byteArrayOf(7, 8))
        }
        try {
            awaitStat("blocked", 1)
            assertEquals(42, withTimeout(2_000) { async(Dispatchers.Main) { 42 }.await() })
            withContext(Dispatchers.Main) { pending.cancel() }
            delay(100)
            // This provider deliberately ignores cancellation. Cancellation is not proof of drain.
            assertFalse(pending.isCompleted)
            assertEquals(1, provider("stats").getInt("blocked"))
            provider("release")
            withTimeout(5_000) { pending.join() }
            awaitDrained()
            assertArrayEquals(byteArrayOf(), provider("bytes", "blockedopen").getByteArray("bytes"))
            assertEquals(0, provider("stats").getInt("opened_on_main"))
            writeArchiveDocument(resolver, uri("empty"), byteArrayOf(9))
            awaitDrained()
            assertArrayEquals(byteArrayOf(9), provider("bytes", "empty").getByteArray("bytes"))
        } finally {
            provider("release")
            pending.cancel()
            withTimeout(5_000) { pending.join() }
            awaitDrained()
        }
    }

    private suspend fun awaitStat(field: String, value: Int) = withTimeout(8_000) {
        while (withContext(Dispatchers.IO) { provider("stats").getInt(field) } != value) delay(10)
    }

    private suspend fun awaitDrained() = withTimeout(8_000) {
        while (true) {
            val stats = withContext(Dispatchers.IO) { provider("stats") }
            if (stats.getInt("blocked") == 0 && stats.getInt("opened") == stats.getInt("closed")) break
            delay(10)
        }
    }

    private suspend fun expectFailure(category: String, block: suspend () -> Unit) {
        try { block(); fail("Expected archive document failure") }
        catch (failure: ArchiveFailure) {
            assertEquals(category, failure.category)
            assertEquals("Archive operation failed", failure.message)
            assertNull(failure.cause)
        }
    }
}
