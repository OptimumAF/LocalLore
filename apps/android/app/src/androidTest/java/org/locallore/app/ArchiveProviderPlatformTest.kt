/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.net.Uri
import android.os.Bundle
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.junit.After
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.atomic.AtomicBoolean

/** Real ContentResolver calls to the separate test APK process, using only synthetic data. */
@RunWith(AndroidJUnit4::class)
class ArchiveProviderPlatformTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val resolver get() = instrumentation.targetContext.contentResolver
    private val authority get() = instrumentation.context.packageName + ".archives"

    @Before fun resetProvider() {
        provider("reset")
    }

    @After fun releaseAndResetProvider() = runBlocking {
        provider("release")
        awaitStats { it.getInt("blocked") == 0 && it.getInt("opened") == it.getInt("closed") }
        provider("reset")
        Unit
    }

    @Test fun cancelledReadOnlyOpenDrainsAndNextImportReadsExactlyTheAssetSlice() = runBlocking {
        val cancelled = cancelBlockedOpen { readArchiveDocument(resolver, uri("cancellableopen")) }
        assertEquals(0, cancelled.getInt("opened"))
        assertEquals(0, cancelled.getInt("closed"))

        val slice = withTimeout(5_000) {
            withContext(Dispatchers.Main) { readArchiveDocument(resolver, uri("slice")) }
        }
        assertArrayEquals(byteArrayOf(0, 0x41, -1, 0x42), slice)
        val closed = awaitStats { it.getInt("closed") == 1 }
        assertEquals(1, closed.getInt("opened"))
        assertEquals(2, closed.getInt("reads"))
        assertEquals(0, closed.getInt("rw"))
        assertEquals(0, closed.getInt("forbidden_modes"))
        assertEquals(0, closed.getInt("opened_on_main"))
        assertArrayEquals(
            byteArrayOf(0x71, 0x72, 0x73, 0, 0x41, -1, 0x42, 0x74, 0x75),
            provider("bytes", "slice").getByteArray("bytes"),
        )
    }

    @Test fun cancelledReadWriteOpenClosesTheLateDestinationAndNextExportWrites() = runBlocking {
        val cancelled = cancelBlockedOpen {
            writeArchiveDocument(resolver, uri("cancellablewrite"), byteArrayOf(7, 8))
        }
        assertEquals(1, cancelled.getInt("opened"))
        val closed = awaitStats { it.getInt("closed") == 1 }
        assertEquals(1, closed.getInt("rw"))
        assertArrayEquals(byteArrayOf(), provider("bytes", "cancellablewrite").getByteArray("bytes"))

        val bytes = byteArrayOf(0, -1, 9)
        withTimeout(5_000) {
            withContext(Dispatchers.Main) { writeArchiveDocument(resolver, uri("empty"), bytes) }
        }
        val finished = awaitStats { it.getInt("closed") == 2 }
        assertEquals(2, finished.getInt("opened"))
        assertEquals(2, finished.getInt("rw"))
        assertEquals(0, finished.getInt("reads"))
        assertEquals(0, finished.getInt("forbidden_modes"))
        assertEquals(0, finished.getInt("opened_on_main"))
        assertArrayEquals(bytes, provider("bytes", "empty").getByteArray("bytes"))
        assertArrayEquals(byteArrayOf(), provider("bytes", "cancellablewrite").getByteArray("bytes"))
    }

    private suspend fun cancelBlockedOpen(operation: suspend () -> Unit): Bundle = coroutineScope {
        val returned = AtomicBoolean()
        val pending = launch(Dispatchers.Main) {
            operation()
            returned.set(true)
        }
        try {
            awaitStats { it.getInt("blocked") == 1 }
            withTimeout(2_000) {
                withContext(Dispatchers.Main) {
                    assertFalse(pending.isCompleted)
                    pending.cancel()
                }
            }
            // The provider must observe the signal and finish without the test's release call.
            withTimeout(5_000) { pending.join() }
            val cancelled = provider("stats")
            assertTrue(pending.isCancelled)
            assertFalse(returned.get())
            assertEquals(0, cancelled.getInt("blocked"))
            assertEquals(1, cancelled.getInt("cancelled_opens"))
            cancelled
        } finally {
            if (!pending.isCompleted) {
                pending.cancel()
                provider("release")
                withTimeout(5_000) { pending.join() }
            }
        }
    }

    private fun uri(case: String) = Uri.parse("content://$authority/$case")

    private fun provider(method: String, arg: String? = null): Bundle =
        requireNotNull(resolver.call(authority, method, arg, null))

    private suspend fun awaitStats(condition: (Bundle) -> Boolean): Bundle = withTimeout(8_000) {
        var stats = provider("stats")
        while (!condition(stats)) {
            delay(10)
            stats = provider("stats")
        }
        stats
    }
}
