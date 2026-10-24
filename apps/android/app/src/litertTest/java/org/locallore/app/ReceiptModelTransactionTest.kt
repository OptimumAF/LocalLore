/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.ByteArrayInputStream
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.nio.file.Files
import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.isActive
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Assume.assumeNoException
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Real host files and original bytes. No JNI publisher, Android context or real model. */
class ReceiptModelTransactionTest {
    @get:Rule val temporary = TemporaryFolder()
    private val bytes = "LocalLore original model picker fixture v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
    private val identity get() = LocalModelIdentity("synthetic-receipt-v1", 63, sha(bytes), 1024)
    private data class Roots(val control: File, val data: File)
    private fun roots(): Roots {
        val parent = temporary.newFolder().canonicalFile
        return Roots(File(parent, "control"), File(parent, "data"))
    }
    private fun store(roots: Roots, free: Long = Long.MAX_VALUE,
        guard: (Long) -> Unit = {}, checkpoint: (ReceiptCheckpoint) -> Unit = {}) =
        ReceiptModelTransaction(roots.control, roots.data, identity, { free }, guard, checkpoint)
    private fun model(roots: Roots) = File(roots.data, "model.litertlm")
    private fun receipt(roots: Roots) = File(roots.control, "model.receipt")
    private fun marker(roots: Roots) = File(roots.control, "model.accepted")
    private fun owner(roots: Roots) = File(roots.data, "model.owner")
    private fun sha(value: ByteArray) = MessageDigest.getInstance("SHA-256").digest(value)
        .joinToString("") { "%02x".format(it) }
    private fun expectedReceipt(roots: Roots): ByteArray =
        ("locallore-model-receipt-v1\n${identity.id}\n${identity.bytes}\n${identity.sha256}\n" +
            sha(roots.data.canonicalPath.toByteArray(Charsets.UTF_8)) + "\n").toByteArray(Charsets.UTF_8)
    private fun expectedOwner(roots: Roots): ByteArray =
        ("locallore-model-owner-v1\n" + sha(roots.control.canonicalPath.toByteArray(Charsets.UTF_8)) + "\n" +
            sha(expectedReceipt(roots)) + "\n").toByteArray(Charsets.UTF_8)
    private suspend fun refused(expected: LocalModelFailure? = null, action: suspend () -> Unit) {
        try { action(); fail("Expected fixed transaction refusal") }
        catch (failure: LocalModelException) {
            if (expected != null) assertEquals(expected, failure.failure)
            assertEquals("Local model unavailable: ${failure.failure.name}", failure.message)
            // Coroutine recovery may copy the same sanitized exception, never its private cause.
            var cause: Throwable? = failure
            var count = 0
            while (cause != null) {
                assertTrue(++count <= 8)
                assertEquals(LocalModelException::class.java, cause.javaClass)
                assertEquals(failure.message, cause.message)
                cause = cause.cause
            }
        }
    }
    private suspend fun pending(roots: Roots) {
        refused {
            store(roots, checkpoint = {
                if (it == ReceiptCheckpoint.DATA_FORCED) throw IOException("private interrupted checkpoint")
            }).import { ByteArrayInputStream(bytes) }
        }
        assertFalse(marker(roots).exists())
        assertArrayEquals(bytes, model(roots).readBytes())
    }
    private fun payloadSnapshot(roots: Roots): Map<String, String> = buildMap {
        // Fixed known leaves only: no broad filesystem scan or symlink traversal.
        for ((key, file) in listOf("receipt" to receipt(roots), "owner" to owner(roots),
            "model" to model(roots), "marker" to marker(roots))) {
            if (Files.isRegularFile(file.toPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS)) put(key, sha(file.readBytes()))
        }
    }

    @Test fun exactReceiptAndMarkerLastEstablishAcceptanceAndIdempotentReopen() = runBlocking {
        val roots = roots()
        val steps = mutableListOf<ReceiptCheckpoint>()
        val transaction = store(roots, checkpoint = { step ->
            steps += step
            when (step) {
                ReceiptCheckpoint.RECEIPT_FORCED -> {
                    assertArrayEquals(expectedReceipt(roots), receipt(roots).readBytes())
                    assertTrue(receipt(roots).length() <= 512)
                    assertFalse(roots.data.exists())
                }
                ReceiptCheckpoint.DATA_FORCED -> {
                    assertArrayEquals(expectedOwner(roots), owner(roots).readBytes())
                    assertArrayEquals(bytes, model(roots).readBytes())
                }
                ReceiptCheckpoint.BEFORE_COMMIT -> {
                    assertTrue(File(roots.data, "cache").isDirectory)
                    assertFalse(marker(roots).exists())
                }
                ReceiptCheckpoint.AFTER_COMMIT -> {
                    assertTrue(marker(roots).isFile)
                    assertEquals(0, marker(roots).length())
                }
            }
        })
        assertNull(transaction.installed())
        val installed = transaction.import { ByteArrayInputStream(bytes) }
        assertEquals(ReceiptCheckpoint.values().toList(), steps)
        assertEquals(LocalModelFiles(roots.data, model(roots), File(roots.data, "cache")), installed)
        assertArrayEquals(expectedReceipt(roots), receipt(roots).readBytes())
        val before = payloadSnapshot(roots)
        val cached = File(installed.cache, "runtime.keep").apply { writeText("opaque accepted cache") }
        assertEquals(installed, store(roots).installed())
        assertEquals(installed, store(roots).import { error("Accepted copy must not reopen source") })
        refused { store(roots).discardUncommitted() }
        assertEquals(before, payloadSnapshot(roots))
        assertEquals("opaque accepted cache", cached.readText())
    }

    @Test fun completePendingCopyIsInvisibleUntilResumedWithoutOpeningSource() = runBlocking {
        val roots = roots()
        pending(roots)
        val before = payloadSnapshot(roots)
        assertNull(store(roots).installed())
        assertEquals(before, payloadSnapshot(roots))
        val result = store(roots).import { error("Complete pending copy must not reopen source") }
        assertArrayEquals(bytes, result.model.readBytes())
        assertEquals(before["model"], sha(result.model.readBytes()))
        assertEquals(before["receipt"], sha(receipt(roots).readBytes()))
        assertTrue(marker(roots).isFile)
        assertEquals(result, store(roots).installed())
    }

    @Test fun equivalentCaseAliasReopensAcceptedCopyWithoutChangingProvenance() = runBlocking {
        val roots = roots()
        val installed = store(roots).import { ByteArrayInputStream(bytes) }
        val alias = Roots(File(roots.control.parentFile, "CONTROL"), File(roots.data.parentFile, "DATA"))
        // This regression applies only where these actual existing paths share a canonical identity.
        if (alias.control.canonicalFile != roots.control.canonicalFile ||
            alias.data.canonicalFile != roots.data.canonicalFile
        ) return@runBlocking
        assertNotEquals(roots.control.path, alias.control.path)
        assertNotEquals(roots.data.path, alias.data.path)
        assertEquals(roots.control.canonicalPath, alias.control.canonicalPath)
        assertEquals(roots.data.canonicalPath, alias.data.canonicalPath)
        val before = payloadSnapshot(roots)
        assertEquals(installed, store(alias).installed())
        assertEquals(installed, store(alias).import { error("Equivalent canonical alias cannot reopen source") })
        assertEquals(before, payloadSnapshot(roots))
        assertArrayEquals(expectedReceipt(roots), receipt(roots).readBytes())
        assertArrayEquals(expectedOwner(roots), owner(roots).readBytes())
    }

    @Test fun receiptOnlyInterruptionCanContinueFreshButCannotExposeAHandle() = runBlocking {
        val roots = roots()
        refused {
            store(roots, checkpoint = {
                if (it == ReceiptCheckpoint.RECEIPT_FORCED) throw IOException("private checkpoint")
            }).import { error("Source must not open before receipt checkpoint") }
        }
        assertFalse(roots.data.exists())
        assertArrayEquals(expectedReceipt(roots), receipt(roots).readBytes())
        assertNull(store(roots).installed())
        var opened = 0
        store(roots).import { opened++; ByteArrayInputStream(bytes) }
        assertEquals(1, opened)
        assertNotNull(store(roots).installed())
    }

    @Test fun afterCommitExceptionDoesNotEraseAcceptedCopy() = runBlocking {
        val roots = roots()
        refused {
            store(roots, checkpoint = {
                if (it == ReceiptCheckpoint.AFTER_COMMIT) throw IOException("private late failure")
            }).import { ByteArrayInputStream(bytes) }
        }
        assertTrue(marker(roots).isFile)
        assertEquals(0, marker(roots).length())
        val before = payloadSnapshot(roots)
        assertNotNull(store(roots).installed())
        refused { store(roots).discardUncommitted() }
        assertEquals(before, payloadSnapshot(roots))
    }

    @Test fun actualChildCancellationBeforeAndAfterMarkerPreservesTheAcceptanceBoundary() = runBlocking {
        for (boundary in listOf(ReceiptCheckpoint.BEFORE_COMMIT, ReceiptCheckpoint.AFTER_COMMIT)) {
            val roots = roots()
            val closed = AtomicInteger()
            val reached = AtomicInteger()
            lateinit var operation: kotlinx.coroutines.Deferred<LocalModelFiles>
            operation = async(Dispatchers.IO, start = CoroutineStart.LAZY) {
                store(roots, checkpoint = {
                    if (it == boundary) {
                        reached.incrementAndGet()
                        operation.cancel()
                    }
                }).import {
                    object : ByteArrayInputStream(bytes) {
                        override fun close() { closed.incrementAndGet(); super.close() }
                    }
                }
            }
            operation.start()
            withTimeout(10_000) { operation.join() }
            assertTrue("Cancellation must stay confined to the owned child", currentCoroutineContext().isActive)
            assertTrue(operation.isCancelled)
            assertEquals(1, reached.get())
            assertEquals(1, closed.get())
            assertArrayEquals(bytes, model(roots).readBytes())
            assertArrayEquals(expectedReceipt(roots), receipt(roots).readBytes())
            assertArrayEquals(expectedOwner(roots), owner(roots).readBytes())
            val before = payloadSnapshot(roots)
            if (boundary == ReceiptCheckpoint.BEFORE_COMMIT) {
                assertFalse(marker(roots).exists())
                assertNull(store(roots).installed())
                assertEquals(before, payloadSnapshot(roots))
                store(roots).discardUncommitted()
                assertFalse(roots.data.exists())
                assertFalse(receipt(roots).exists())
            } else {
                assertTrue(marker(roots).isFile)
                assertEquals(0, marker(roots).length())
                assertNotNull(store(roots).installed())
                refused { store(roots).discardUncommitted() }
                assertEquals(before, payloadSnapshot(roots))
            }
        }
    }

    @Test fun invalidPartialCopiesArePreservedUntilExplicitDiscardThenRetry() = runBlocking {
        for (source in listOf(bytes.copyOf(17), bytes.copyOf().also { it[2] = (it[2] + 1).toByte() })) {
            val roots = roots()
            refused { store(roots).import { ByteArrayInputStream(source) } }
            assertFalse(marker(roots).exists())
            assertArrayEquals(source, model(roots).readBytes())
            assertArrayEquals(expectedReceipt(roots), receipt(roots).readBytes())
            refused { store(roots).import { error("Partial copy may not silently restart") } }
            store(roots).discardUncommitted()
            assertFalse(roots.data.exists())
            assertFalse(receipt(roots).exists())
            assertTrue(File(roots.control, "model-import.lock").isFile)
            assertArrayEquals(bytes, store(roots).import { ByteArrayInputStream(bytes) }.model.readBytes())
        }
    }

    @Test fun blockedReadCancellationKeepsSlotUntilActualReturnAndClose() = runBlocking {
        val roots = roots()
        val blocked = CountDownLatch(1)
        val release = CountDownLatch(1)
        val closed = AtomicInteger()
        val source = object : InputStream() {
            var first = true
            override fun read(): Int = error("Bulk read required")
            override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                if (first) {
                    first = false
                    bytes.copyInto(buffer, offset, 0, 17)
                    return 17
                }
                blocked.countDown()
                check(release.await(10, TimeUnit.SECONDS))
                return -1
            }
            override fun close() { closed.incrementAndGet() }
        }
        val operation = async(Dispatchers.IO) { store(roots).import { source } }
        try {
            assertTrue(blocked.await(5, TimeUnit.SECONDS))
            operation.cancel()
            assertFalse(operation.isCompleted)
            assertEquals(0, closed.get())
            refused(LocalModelFailure.BUSY) { store(roots).installed() }
            refused(LocalModelFailure.BUSY) { store(roots).import { error("Busy source opened") } }
            refused(LocalModelFailure.BUSY) { store(roots).discardUncommitted() }
            assertArrayEquals(bytes.copyOf(17), model(roots).readBytes())
            assertFalse(marker(roots).exists())
        } finally {
            release.countDown()
            withTimeout(10_000) { operation.join() }
        }
        assertEquals(1, closed.get())
        assertNull(store(roots).installed())
        store(roots).discardUncommitted()
        assertNotNull(store(roots).import { ByteArrayInputStream(bytes) })
    }

    @Test fun markerAndReceiptCorruptionCannotExposeOrDiscardAcceptedBytes() = runBlocking {
        for (mutation in listOf<(Roots) -> Unit>(
            { marker(it).writeBytes(byteArrayOf(1)) },
            { Files.delete(receipt(it).toPath()) },
            { receipt(it).writeText("x".repeat(513)) },
            { receipt(it).writeText(String(expectedReceipt(it), Charsets.UTF_8).replace(identity.id, "other-model")) },
            { model(it).writeBytes(bytes.copyOf().also { value -> value[5] = (value[5] + 1).toByte() }) },
        )) {
            val roots = roots()
            store(roots).import { ByteArrayInputStream(bytes) }
            mutation(roots)
            val before = payloadSnapshot(roots)
            refused { store(roots).installed() }
            refused { store(roots).import { error("Malformed acceptance cannot select source") } }
            refused { store(roots).discardUncommitted() }
            assertEquals(before, payloadSnapshot(roots))
        }
    }

    @Test fun oversizedAndNonprogressingStreamsCloseOnceAndNeverAccept() = runBlocking {
        for (zeroProgress in listOf(false, true)) {
            val roots = roots()
            val readBytes = AtomicInteger()
            val calls = AtomicInteger()
            val closed = AtomicInteger()
            val source = object : InputStream() {
                override fun read(): Int = error("Bulk read required")
                override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                    check(calls.incrementAndGet() <= 2)
                    if (zeroProgress) return 0
                    buffer.fill(0, offset, offset + length)
                    readBytes.addAndGet(length)
                    return length
                }
                override fun close() { closed.incrementAndGet() }
            }
            refused(LocalModelFailure.INVALID_MODEL) { store(roots).import { source } }
            assertEquals(1, calls.get())
            assertEquals(if (zeroProgress) 0 else bytes.size + 1, readBytes.get())
            assertEquals(1, closed.get())
            assertFalse(marker(roots).exists())
            assertNull(store(roots).installed())
        }
    }

    @Test fun receiptIsBoundToExactIdentityAndDataRootNotReusableAtAnotherRoot() = runBlocking {
        val first = roots()
        pending(first)
        val second = roots()
        second.control.mkdir()
        File(second.control, "model-import.lock").writeBytes(byteArrayOf())
        receipt(second).writeBytes(receipt(first).readBytes())
        refused { store(second).import { error("Wrong provenance cannot open source") } }
        refused { store(second).discardUncommitted() }
        assertFalse(second.data.exists())
        assertArrayEquals(expectedReceipt(first), receipt(second).readBytes())
        assertFalse(marker(first).exists())
        assertArrayEquals(bytes, model(first).readBytes())
    }

    @Test fun anotherControlRootCannotAdoptOrDiscardForeignPendingDataWithMatchingReceipt() = runBlocking {
        val first = roots()
        pending(first)
        val secondControl = File(first.control.parentFile, "second-control").apply { mkdir() }
        val foreign = Roots(secondControl, first.data)
        File(secondControl, "model-import.lock").writeBytes(byteArrayOf())
        // Both path-bound receipts are byte-identical; only the data owner distinguishes them.
        assertArrayEquals(expectedReceipt(first), expectedReceipt(foreign))
        receipt(foreign).writeBytes(expectedReceipt(foreign))
        assertFalse(expectedOwner(first).contentEquals(expectedOwner(foreign)))
        val before = payloadSnapshot(first)
        refused { store(foreign).import { error("Foreign pending data cannot reopen source") } }
        refused { store(foreign).discardUncommitted() }
        assertEquals(before, payloadSnapshot(first))
        assertArrayEquals(expectedOwner(first), owner(first).readBytes())
        assertArrayEquals(expectedReceipt(foreign), receipt(foreign).readBytes())
        assertNotNull(store(first).import { error("Original owner must resume its complete copy") })
    }

    @Test fun missingMalformedOrForeignDataOwnerNeverPermitsAdoptionOrDiscard() = runBlocking {
        for (mutation in listOf<(Roots) -> Unit>(
            { Files.delete(owner(it).toPath()) },
            { owner(it).writeText("malformed owner") },
            { owner(it).writeText("x".repeat(513)) },
        )) {
            val roots = roots()
            pending(roots)
            mutation(roots)
            val before = payloadSnapshot(roots)
            refused { store(roots).import { error("Invalid owner must not open source") } }
            refused { store(roots).discardUncommitted() }
            assertEquals(before, payloadSnapshot(roots))
            assertTrue(roots.data.isDirectory)
        }
    }

    @Test fun oversizedPendingModelCannotBeResumedOrSilentlyReplaced() = runBlocking {
        val roots = roots()
        pending(roots)
        model(roots).appendBytes(byteArrayOf(1))
        val before = payloadSnapshot(roots)
        assertNull(store(roots).installed())
        refused(LocalModelFailure.INVALID_MODEL) {
            store(roots).import { error("Oversized pending model may not reopen source") }
        }
        refused { store(roots).discardUncommitted() }
        assertEquals(before, payloadSnapshot(roots))
        assertFalse(marker(roots).exists())
    }

    @Test fun ownerOnlyPendingDirectoryCanBeExplicitlyDiscardedButOwnerlessCannot() = runBlocking {
        for (withOwner in listOf(true, false)) {
            val roots = roots()
            roots.control.mkdir()
            File(roots.control, "model-import.lock").writeBytes(byteArrayOf())
            receipt(roots).writeBytes(expectedReceipt(roots))
            roots.data.mkdir()
            if (withOwner) owner(roots).writeBytes(expectedOwner(roots))
            assertNull(store(roots).installed())
            if (withOwner) {
                store(roots).discardUncommitted()
                assertFalse(roots.data.exists())
                assertFalse(receipt(roots).exists())
            } else {
                refused { store(roots).discardUncommitted() }
                assertTrue(roots.data.isDirectory)
                assertArrayEquals(expectedReceipt(roots), receipt(roots).readBytes())
            }
        }
    }

    @Test fun acceptedCopyCannotReconstructItsMissingPersistentLock() = runBlocking {
        val roots = roots()
        store(roots).import { ByteArrayInputStream(bytes) }
        val lock = File(roots.control, "model-import.lock")
        Files.delete(lock.toPath())
        val before = payloadSnapshot(roots)
        refused(LocalModelFailure.UNSAFE_PATH) { store(roots).installed() }
        refused(LocalModelFailure.UNSAFE_PATH) { store(roots).import { error("Missing lock may not reopen source") } }
        refused(LocalModelFailure.UNSAFE_PATH) { store(roots).discardUncommitted() }
        assertEquals(before, payloadSnapshot(roots))
        assertFalse(lock.exists())
    }

    @Test fun acceptedMissingCacheIsRefusedWithoutReconstruction() = runBlocking {
        val roots = roots()
        val installed = store(roots).import { ByteArrayInputStream(bytes) }
        Files.delete(installed.cache.toPath())
        val before = payloadSnapshot(roots)
        refused { store(roots).installed() }
        refused { store(roots).import { error("Missing accepted cache cannot reopen source") } }
        refused { store(roots).discardUncommitted() }
        assertEquals(before, payloadSnapshot(roots))
        assertFalse(installed.cache.exists())
    }

    @Test fun unknownControlDataOrCacheChildPreventsEveryDiscardDeletion() = runBlocking {
        for (location in listOf("control", "data", "cache")) {
            val roots = roots()
            pending(roots)
            val directory = when (location) {
                "control" -> roots.control
                "data" -> roots.data
                else -> File(roots.data, "cache").apply { if (!exists()) mkdir() }
            }
            val unknown = File(directory, "unknown.keep").apply { writeText("original unknown") }
            val before = payloadSnapshot(roots)
            refused { store(roots).discardUncommitted() }
            assertEquals(before, payloadSnapshot(roots))
            assertEquals("original unknown", unknown.readText())
            assertTrue(roots.data.isDirectory)
        }
    }

    @Test fun preexistingUnownedDataRootAndOverlappingRootsRefuseWithoutAdoption() = runBlocking {
        val roots = roots()
        roots.data.mkdir()
        val unknown = File(roots.data, "model.litertlm").apply { writeBytes(bytes) }
        refused { store(roots).import { error("Unowned root cannot open source") } }
        assertArrayEquals(bytes, unknown.readBytes())
        assertFalse(receipt(roots).exists())
        val parent = temporary.newFolder().canonicalFile
        for (pair in listOf(Roots(parent, parent), Roots(parent, File(parent, "nested")),
            Roots(File(parent, "nested"), parent))) {
            refused { store(pair).import { error("Overlapping roots cannot open source") } }
        }
        val absentParent = File(temporary.root.canonicalFile, "absent-parent")
        refused { store(Roots(File(absentParent, "control"), File(absentParent, "data"))).import { error("Missing parent") } }
        assertFalse(absentParent.exists())
        val existing = temporary.newFolder().canonicalFile
        File(existing, "alias").mkdir()
        refused {
            store(Roots(File(existing, "alias/../control"), File(existing, "data"))).import {
                error("Noncanonical roots cannot open source")
            }
        }
        assertFalse(File(existing, "control").exists())
    }

    @Test fun capacityBoundaryAndStorageGuardRefuseBeforeSourceAndBeforeCommit() = runBlocking {
        val roots = roots()
        refused(LocalModelFailure.NO_SPACE) {
            store(roots, identity.bytes + identity.reserveBytes - 1).import { error("Low space opened source") }
        }
        assertFalse(roots.data.exists())
        assertFalse(receipt(roots).exists())
        assertFalse(marker(roots).exists())
        store(roots, identity.bytes + identity.reserveBytes).import { ByteArrayInputStream(bytes) }
        val huge = roots()
        refused(LocalModelFailure.NO_SPACE) {
            ReceiptModelTransaction(huge.control, huge.data,
                identity.copy(bytes = Long.MAX_VALUE, reserveBytes = Long.MAX_VALUE), { Long.MAX_VALUE })
                .import { error("Overflow cannot open source") }
        }
        assertFalse(huge.data.exists())
        assertFalse(receipt(huge).exists())
        val pending = roots()
        var changed = false
        refused {
            store(pending, guard = { if (changed) throw LocalModelException(LocalModelFailure.STORAGE) }, checkpoint = {
                if (it == ReceiptCheckpoint.BEFORE_COMMIT) changed = true
            }).import { ByteArrayInputStream(bytes) }
        }
        assertFalse(marker(pending).exists())
        assertArrayEquals(bytes, model(pending).readBytes())
        val before = payloadSnapshot(pending)
        refused {
            store(pending, guard = { throw LocalModelException(LocalModelFailure.STORAGE) }).discardUncommitted()
        }
        assertEquals(before, payloadSnapshot(pending))
    }

    @Test fun guardLossDuringDiscardStopsRemainingDeletesWithoutClaimingRollback() = runBlocking {
        val roots = roots()
        pending(roots)
        val originalReceipt = receipt(roots).readBytes()
        var rejectedAfterDelete = false
        refused(LocalModelFailure.STORAGE) {
            store(roots, guard = {
                if (!model(roots).exists()) {
                    rejectedAfterDelete = true
                    throw LocalModelException(LocalModelFailure.STORAGE)
                }
            }).discardUncommitted()
        }
        assertTrue(rejectedAfterDelete)
        // The permitted first deletion need not roll back; control ownership must remain.
        assertArrayEquals(originalReceipt, receipt(roots).readBytes())
        assertTrue(roots.data.isDirectory)
        assertFalse(marker(roots).exists())
    }

    @Test fun symlinkMarkerOrRootNeverDeletesOrAcceptsItsTarget() = runBlocking {
        val roots = roots()
        pending(roots)
        val sentinel = File(temporary.newFolder(), "sentinel").apply { writeText("protected target") }
        try { Files.createSymbolicLink(marker(roots).toPath(), sentinel.toPath()) }
        catch (unsupported: IOException) { assumeNoException("Host cannot create symbolic links", unsupported) }
        catch (unsupported: UnsupportedOperationException) { assumeNoException(unsupported) }
        refused { store(roots).installed() }
        refused { store(roots).discardUncommitted() }
        assertEquals("protected target", sentinel.readText())
        assertArrayEquals(bytes, model(roots).readBytes())
        val aliases = roots()
        Files.createSymbolicLink(aliases.data.toPath(), roots.data.toPath())
        refused { store(aliases).import { error("Linked root opened source") } }
        assertEquals("protected target", sentinel.readText())
        assertArrayEquals(bytes, model(roots).readBytes())
    }
}
