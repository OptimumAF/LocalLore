/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.ByteArrayInputStream
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.nio.file.Files
import java.nio.file.attribute.FileTime
import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.cancel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Real receipt files and original tiny bytes, without Android, JNI or an inference SDK. */
class ReceiptCandidateModelAccessTest {
    @get:Rule val temporary = TemporaryFolder()
    private val bytes = "LocalLore original model picker fixture v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
    private val identity get() = LocalModelIdentity("synthetic-receipt-access-v1", 63, sha(bytes), 1024)
    private data class Roots(val control: File, val data: File)
    private fun roots(): Roots = temporary.newFolder().canonicalFile.let {
        Roots(File(it, "control"), File(it, "data"))
    }
    private fun access(roots: Roots, guard: (Long) -> Unit = {},
        checkpoint: (ReceiptCheckpoint) -> Unit = {}) = ReceiptCandidateModelAccess(
        ReceiptModelTransaction(roots.control, roots.data, identity, { Long.MAX_VALUE }, guard, checkpoint),
    )
    private fun sha(value: ByteArray) = MessageDigest.getInstance("SHA-256").digest(value)
        .joinToString("") { "%02x".format(it) }
    private fun marker(roots: Roots) = File(roots.control, "model.accepted")
    private fun model(roots: Roots) = File(roots.data, "model.litertlm")
    private fun fixed(reason: LocalModelFailure? = null, action: () -> Unit) {
        try { action(); fail("Expected fixed access refusal") }
        catch (failure: LocalModelException) {
            if (reason != null) assertEquals(reason, failure.failure)
            var cause: Throwable? = failure
            var count = 0
            while (cause != null) {
                assertTrue(++count <= 8)
                assertEquals(LocalModelException::class.java, cause.javaClass)
                assertEquals("Local model unavailable: ${failure.failure.name}", cause.message)
                cause = cause.cause
            }
        }
    }
    private suspend fun fixedSuspend(reason: LocalModelFailure? = null, action: suspend () -> Unit) {
        try { action(); fail("Expected fixed access refusal") }
        catch (failure: LocalModelException) {
            if (reason != null) assertEquals(reason, failure.failure)
            fixed(failure.failure) { throw failure }
        }
    }

    @Test fun constructorAndPlanningDoNotInspectOrAdmitPaths() {
        var admissions = 0
        val roots = Roots(File("untrusted-relative-control"), File("untrusted-relative-data"))
        val access = access(roots, guard = { admissions++; error("No planning IO") })
        assertEquals(LocalModelFiles(roots.data, File(roots.data, "model.litertlm"), File(roots.data, "cache")),
            access.plannedFiles())
        assertEquals(0, admissions)
    }

    @Test fun absentOrLegacyDataNeverGainsRuntimeAuthorityOrGetsAdopted() = runBlocking {
        val roots = roots()
        val access = access(roots)
        assertNull(access.installed())
        fixed { access.admitRuntime() }
        assertFalse(roots.control.exists())
        assertFalse(roots.data.exists())
        roots.data.mkdir()
        model(roots).writeBytes(bytes)
        val old = File(roots.data, "legacy-cache").also { it.writeBytes(byteArrayOf(7, 3, 1)) }
        var opened = 0
        fixedSuspend(LocalModelFailure.UNSAFE_PATH) { access.import { opened++; ByteArrayInputStream(bytes) } }
        assertEquals(0, opened)
        assertArrayEquals(bytes, model(roots).readBytes())
        assertArrayEquals(byteArrayOf(7, 3, 1), old.readBytes())
        assertFalse(roots.control.exists())
    }

    @Test fun fullImportAndReopenEstablishOnlyTheirOwnInstanceStamp() = runBlocking {
        val roots = roots()
        val access = access(roots)
        val closes = AtomicInteger()
        val files = access.import {
            object : ByteArrayInputStream(bytes) { override fun close() { closes.incrementAndGet(); super.close() } }
        }
        assertEquals(1, closes.get())
        assertEquals(files, access.plannedFiles())
        access.admitRuntime()
        val reopened = access(roots)
        fixed(LocalModelFailure.INVALID_MODEL) { reopened.admitRuntime() }
        assertEquals(files, reopened.installed())
        reopened.admitRuntime()
        assertEquals(files, reopened.import { error("Accepted reuse must not open source") })
        reopened.admitRuntime()
    }

    @Test fun runtimeRechecksExactRecordsAndUnknownEntriesWithoutRepair() = runBlocking {
        for (name in listOf("model.receipt", "model.accepted", "model.owner", "unknown")) {
            val roots = roots()
            val access = access(roots)
            access.import { ByteArrayInputStream(bytes) }
            val target = if (name == "model.owner") File(roots.data, name) else File(roots.control, name)
            val changed = byteArrayOf(4, 2, 9)
            target.writeBytes(changed)
            fixed(LocalModelFailure.UNSAFE_PATH) { access.admitRuntime() }
            assertArrayEquals(changed, target.readBytes())
            assertArrayEquals(bytes, model(roots).readBytes())
        }
    }

    @Test fun cacheChildWritesAreOpaqueButMissingCacheRefusesWithoutCreation() = runBlocking {
        val roots = roots()
        val access = access(roots)
        val files = access.import { ByteArrayInputStream(bytes) }
        val child = File(files.cache, "sdk-owned-tiny-fixture").also { it.writeBytes(byteArrayOf(8)) }
        Files.setLastModifiedTime(files.cache.toPath(), FileTime.fromMillis(123456))
        access.admitRuntime()
        assertArrayEquals(byteArrayOf(8), child.readBytes())
        child.delete(); files.cache.delete()
        fixed(LocalModelFailure.UNSAFE_PATH) { access.admitRuntime() }
        assertFalse(files.cache.exists())
    }

    @Test fun modelMetadataDriftRevokesStampEvenWhenBytesAreStillValid() = runBlocking {
        val roots = roots()
        val access = access(roots)
        access.import { ByteArrayInputStream(bytes) }
        val path = model(roots).toPath()
        val before = Files.getLastModifiedTime(path)
        Files.setLastModifiedTime(path, FileTime.fromMillis(before.toMillis() + 2000))
        fixed(LocalModelFailure.UNSAFE_PATH) { access.admitRuntime() }
        Files.setLastModifiedTime(path, before)
        fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
        assertNotNull(access.installed())
        access.admitRuntime()
    }

    @Test fun runtimeMetadataIsNotARepeatedModelHashAndFullRecheckStillDetectsCorruption() = runBlocking {
        val roots = roots()
        val access = access(roots)
        access.import { ByteArrayInputStream(bytes) }
        val path = model(roots).toPath()
        val modified = Files.getLastModifiedTime(path)
        val corrupted = bytes.copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() }
        // Same inode/size/time deliberately defeats metadata. No byte-integrity claim is made here.
        model(roots).writeBytes(corrupted)
        Files.setLastModifiedTime(path, modified)
        access.admitRuntime()
        fixedSuspend(LocalModelFailure.INVALID_MODEL) { access.installed() }
        fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
        assertArrayEquals(corrupted, model(roots).readBytes())
    }

    @Test fun currentVolumeAdmissionAndFailedReverificationClearStamp() = runBlocking {
        val roots = roots()
        var refused = false
        var checks = 0
        val access = access(roots, guard = { checks++; if (refused) throw LocalModelException(LocalModelFailure.NO_SPACE) })
        access.import { ByteArrayInputStream(bytes) }
        val before = checks
        access.admitRuntime()
        assertTrue(checks > before)
        refused = true
        fixedSuspend(LocalModelFailure.NO_SPACE) { access.installed() }
        refused = false
        fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
        assertNotNull(access.installed())
        access.admitRuntime()
        refused = true
        fixed(LocalModelFailure.NO_SPACE) { access.admitRuntime() }
        refused = false
        fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
    }

    @Test fun runtimeStorageFailureIsRedactedAndNeverCachesAuthority() = runBlocking {
        val roots = roots()
        var refused = false
        val access = access(roots, guard = { if (refused) throw IOException("private path must not escape") })
        access.import { ByteArrayInputStream(bytes) }
        refused = true
        fixed(LocalModelFailure.STORAGE) { access.admitRuntime() }
        refused = false
        fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
    }

    @Test fun cancellationOnBothSidesOfAcceptanceRequiresFullRecheck() = runBlocking {
        for (boundary in listOf(ReceiptCheckpoint.BEFORE_COMMIT, ReceiptCheckpoint.AFTER_COMMIT)) {
            val roots = roots()
            lateinit var cancel: () -> Unit
            val access = access(roots, checkpoint = { if (it == boundary) cancel() })
            val closes = AtomicInteger()
            val job = async(Dispatchers.IO) {
                val context = currentCoroutineContext()
                cancel = { context.cancel() }
                access.import {
                    object : ByteArrayInputStream(bytes) { override fun close() { closes.incrementAndGet(); super.close() } }
                }
            }
            try { job.await(); fail("Expected cancellation") } catch (_: CancellationException) { }
            assertEquals(1, closes.get())
            assertEquals(boundary == ReceiptCheckpoint.AFTER_COMMIT, marker(roots).exists())
            fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
            if (boundary == ReceiptCheckpoint.AFTER_COMMIT) {
                assertNotNull(access.installed())
                access.admitRuntime()
            } else {
                assertNull(access.installed())
                assertArrayEquals(bytes, model(roots).readBytes())
            }
        }
    }

    @Test fun failedSourceCloseAndLateAcceptedFailureDoNotPublishStamp() = runBlocking {
        val roots = roots()
        val access = access(roots)
        val closes = AtomicInteger()
        fixedSuspend(LocalModelFailure.STORAGE) {
            access.import { object : ByteArrayInputStream(bytes) {
                override fun close() { closes.incrementAndGet(); throw IOException("private close failure") }
            } }
        }
        assertEquals(1, closes.get())
        fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
        assertFalse(marker(roots).exists())
        val recovered = access(roots, checkpoint = {
            if (it == ReceiptCheckpoint.AFTER_COMMIT) throw IOException("private late failure")
        })
        fixedSuspend(LocalModelFailure.STORAGE) { recovered.import { error("Resume cannot open source") } }
        assertTrue(marker(roots).exists())
        fixed(LocalModelFailure.INVALID_MODEL) { recovered.admitRuntime() }
        assertNotNull(recovered.installed())
        recovered.admitRuntime()
    }

    @Test fun blockedReadCancellationRetainsRuntimeAndReopenExclusionUntilCloseReturns() = runBlocking {
        val roots = roots()
        val access = access(roots)
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val closes = AtomicInteger()
        val job = async(Dispatchers.IO) {
            access.import {
                object : InputStream() {
                    override fun read(): Int = error("Bounded array read required")
                    override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                        entered.countDown()
                        check(release.await(5, TimeUnit.SECONDS))
                        return -1
                    }
                    override fun close() { closes.incrementAndGet() }
                }
            }
        }
        try {
            assertTrue(entered.await(5, TimeUnit.SECONDS))
            job.cancel()
            fixed(LocalModelFailure.BUSY) { access.admitRuntime() }
            fixedSuspend(LocalModelFailure.BUSY) { access.installed() }
            assertFalse(job.isCompleted)
            assertEquals(0, closes.get())
        } finally { release.countDown(); withTimeout(5000) { job.join() } }
        assertEquals(1, closes.get())
        assertNull(access.installed())
        fixed(LocalModelFailure.INVALID_MODEL) { access.admitRuntime() }
    }
}
