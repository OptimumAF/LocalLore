/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.net.Uri
import android.os.Bundle
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.IOException
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
    private val authority get() = TestDiagnosticProvider.AUTHORITY
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

    private suspend fun awaitStat(field: String, value: Int) = withTimeout(5_000) {
        while (withContext(Dispatchers.IO) { provider("stats").getInt(field) } != value) delay(10)
    }
    private suspend fun expectIllegalArgument(block: suspend () -> Unit) {
        try { block(); fail("Expected rejected destination or size") }
        catch (_: IllegalArgumentException) { }
    }
}
