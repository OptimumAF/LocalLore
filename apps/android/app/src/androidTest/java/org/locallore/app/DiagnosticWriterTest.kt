/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.ContentProvider
import android.content.ContentResolver
import android.content.ContentValues
import android.database.Cursor
import android.net.Uri
import android.os.Bundle
import android.os.CancellationSignal
import android.os.Looper
import android.os.ParcelFileDescriptor
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.IOException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
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

@RunWith(AndroidJUnit4::class)
class DiagnosticWriterTest {
    private val resolver get() = InstrumentationRegistry.getInstrumentation().targetContext.contentResolver
    private val authority get() = InstrumentationRegistry.getInstrumentation().context.packageName + ".diagnostics"
    private fun uri(case: String) = Uri.parse("content://$authority/$case")
    private fun provider(method: String): Bundle = requireNotNull(resolver.call(authority, method, null, null))
    @Before fun resetProvider() { provider("reset") }
    @After fun clearSyntheticProviderFiles() { provider("reset") }

    @Test fun actualContentResolverWritesExactFrozenBytesTruncatesAndCloses() = runBlocking {
        val first = DiagnosticLog().apply {
            repeat(64) { record(DiagnosticPhase.PREPARE, DiagnosticOutcome.PREPARED, it.toLong()) }
        }.snapshot().json.toByteArray(Charsets.UTF_8)
        writeDiagnosticDocument(resolver, uri("success"), first)
        awaitStat("closed", 1)
        assertArrayEquals(first, provider("bytes").getByteArray("bytes"))
        val frozen = DiagnosticLog().snapshot().json.toByteArray(Charsets.UTF_8)
        writeDiagnosticDocument(resolver, uri("success"), frozen)
        awaitStat("closed", 2)
        assertArrayEquals(frozen, provider("bytes").getByteArray("bytes"))
        assertEquals(2, provider("stats").getInt("opened"))
        assertEquals(0, provider("stats").getInt("opened_on_main"))
    }

    @Test fun invalidSchemesAndOversizedPayloadsAreRejectedBeforeProviderAccess() = runBlocking {
        for (destination in listOf(Uri.EMPTY, Uri.parse("file:///synthetic.json"), Uri.parse("https://invalid.test"))) {
            expectIllegalArgument { writeDiagnosticDocument(resolver, destination, byteArrayOf()) }
        }
        expectIllegalArgument { writeDiagnosticDocument(resolver, uri("success"), ByteArray(16_385)) }
        assertEquals(0, provider("stats").getInt("started"))
    }

    @Test fun exactMaximumByteCountIsAccepted() = runBlocking {
        val bytes = ByteArray(16_384) { 'a'.code.toByte() }
        writeDiagnosticDocument(resolver, uri("success"), bytes)
        awaitStat("closed", 1)
        assertArrayEquals(bytes, provider("bytes").getByteArray("bytes"))
    }

    @Test fun providerErrorsAndNullDescriptorsFailWithoutLeakingOwnedResources() = runBlocking {
        for (case in listOf("failure", "null")) {
            try { writeDiagnosticDocument(resolver, uri(case), byteArrayOf(1)); fail("Expected provider failure") }
            catch (_: IOException) { }
        }
        assertEquals(0, provider("stats").getInt("opened"))
        assertEquals(0, provider("stats").getInt("closed"))
    }

    @Test fun outputFailureStillClosesTheOpenedDescriptor() = runBlocking {
        try { writeDiagnosticDocument(resolver, uri("write_failure"), byteArrayOf(1)); fail("Expected write failure") }
        catch (_: IOException) { }
        awaitStat("closed", 1)
        assertEquals(1, provider("stats").getInt("opened"))
    }

    @Test fun mainDispatcherRemainsResponsiveWhileRemoteOpenIsPendingAndCancellationReleasesIt() = runBlocking {
        val pending = launch(Dispatchers.Main) {
            writeDiagnosticDocument(resolver, uri("slow"), byteArrayOf(1))
        }
        try {
            awaitStat("started", 1)
            val mainPulse = async(Dispatchers.Main) { 42 }
            assertEquals(42, withTimeout(2_000) { mainPulse.await() })
            withContext(Dispatchers.Main) { pending.cancel() }
            withTimeout(3_000) { pending.join() }
            awaitStat("cancelled", 1)
            assertEquals(0, provider("stats").getInt("opened"))
            assertEquals(0, provider("stats").getInt("opened_on_main"))
        } finally { pending.cancelAndJoin() }
    }

    @Test fun repeatedWritesDoNotLeaveDescriptorsOwnedByTheWriter() = runBlocking {
        repeat(12) { index ->
            writeDiagnosticDocument(resolver, uri("success"), "{\"synthetic\":$index}".toByteArray())
        }
        awaitStat("closed", 12)
        assertEquals(12, provider("stats").getInt("opened"))
    }

    @Test @SdkSuppress(minSdkVersion = 29)
    fun synchronousLocalCancellationListenerRunsOffMainAndHoldsTheSingleExportSlot() = runBlocking {
        val opened = AtomicInteger()
        val listenerOnMain = AtomicBoolean(true)
        val openedFirst = CountDownLatch(1)
        val listenerEntered = CountDownLatch(1)
        val releaseListener = CountDownLatch(1)
        val firstDescriptor = AtomicReference<ParcelFileDescriptor?>()
        val secondDescriptor = AtomicReference<ParcelFileDescriptor?>()
        val file = File(InstrumentationRegistry.getInstrumentation().targetContext.cacheDir,
            "diagnostic-writer-synthetic-local.json")
        val local = object : ContentProvider() {
            override fun onCreate() = true
            override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor? = openFile(uri, mode, null)
            override fun openFile(uri: Uri, mode: String, signal: CancellationSignal?): ParcelFileDescriptor {
                val number = opened.incrementAndGet()
                if (number == 1) {
                    requireNotNull(signal).setOnCancelListener {
                        listenerOnMain.set(Looper.myLooper() == Looper.getMainLooper())
                        listenerEntered.countDown()
                        check(releaseListener.await(10, TimeUnit.SECONDS))
                    }
                    openedFirst.countDown()
                    val deadline = System.nanoTime() + 10_000_000_000L
                    while (!signal.isCanceled && System.nanoTime() < deadline) Thread.sleep(5)
                    check(signal.isCanceled)
                }
                return ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_CREATE or
                    ParcelFileDescriptor.MODE_READ_WRITE or ParcelFileDescriptor.MODE_TRUNCATE).also {
                    if (number == 1) firstDescriptor.set(it) else secondDescriptor.set(it)
                }
            }
            override fun getType(uri: Uri) = "application/json"
            override fun query(uri: Uri, projection: Array<out String>?, selection: String?,
                selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
            override fun insert(uri: Uri, values: ContentValues?): Uri? = null
            override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?) = 0
            override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?) = 0
        }
        val wrapped = ContentResolver.wrap(local)
        val first = launch(Dispatchers.Main) { writeDiagnosticDocument(wrapped, uri("success"), byteArrayOf(1)) }
        var second: kotlinx.coroutines.Job? = null
        try {
            assertTrue(withContext(Dispatchers.IO) { openedFirst.await(3, TimeUnit.SECONDS) })
            val cancelReturned = CompletableDeferred<Unit>()
            launch(Dispatchers.Main) { first.cancel(); cancelReturned.complete(Unit) }
            withTimeout(2_000) { cancelReturned.await() }
            assertTrue(withContext(Dispatchers.IO) { listenerEntered.await(3, TimeUnit.SECONDS) })
            assertFalse(listenerOnMain.get())
            assertEquals(42, withTimeout(2_000) { async(Dispatchers.Main) { 42 }.await() })
            withTimeout(3_000) {
                while (firstDescriptor.get()?.fileDescriptor?.valid() != false) delay(10)
            }
            val secondAttempted = CompletableDeferred<Unit>()
            val activeSecond = launch(Dispatchers.Main) {
                secondAttempted.complete(Unit)
                writeDiagnosticDocument(wrapped, uri("success"), byteArrayOf(2))
            }
            second = activeSecond
            withTimeout(2_000) { secondAttempted.await() }
            delay(100)
            assertEquals("Second export must wait for cancellation cleanup", 1, opened.get())
            assertFalse(first.isCompleted)
            releaseListener.countDown()
            withTimeout(3_000) { first.join(); activeSecond.join() }
            assertEquals(2, opened.get())
            assertFalse(requireNotNull(secondDescriptor.get()).fileDescriptor.valid())
            assertArrayEquals(byteArrayOf(2), file.readBytes())
        } finally {
            releaseListener.countDown()
            first.cancelAndJoin()
            second?.cancelAndJoin()
            firstDescriptor.get()?.close()
            secondDescriptor.get()?.close()
            file.delete()
        }
    }

    private suspend fun awaitStat(field: String, value: Int) = withTimeout(5_000) {
        while (withContext(Dispatchers.IO) { provider("stats").getInt(field) } != value) delay(10)
    }
    private suspend fun expectIllegalArgument(block: suspend () -> Unit) {
        try { block(); fail("Expected rejected destination or size") }
        catch (_: IllegalArgumentException) { }
    }
}
