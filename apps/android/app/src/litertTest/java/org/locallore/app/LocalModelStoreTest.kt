/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.ByteArrayInputStream
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.StandardOpenOption.CREATE
import java.nio.file.StandardOpenOption.WRITE
import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeNoException
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Original tiny byte fixtures. No real model, SDK initialization, Android provider, or network. */
class LocalModelStoreTest {
    @get:Rule val temporary = TemporaryFolder()
    private val bytes = ByteArray(131_077) { ((it * 31 + 17) % 251).toByte() }
    private val identity get() = LocalModelIdentity("synthetic-v1", bytes.size.toLong(), sha(bytes), 4096)
    private fun root() = File(temporary.newFolder(), "local-model-v1")
    private fun testStore(root: File, identity: LocalModelIdentity, availableBytes: () -> Long = { root.usableSpace }) =
        LocalModelStore(root, identity, publish = { directory ->
            // Host substitute only. Android exercises its real JNI no-replace rename separately.
            Files.createLink(File(directory, "model.litertlm").toPath(), File(directory, "model.part").toPath())
            Files.delete(File(directory, "model.part").toPath())
        }, availableBytes = availableBytes)
    private fun store(root: File, free: Long = Long.MAX_VALUE) = testStore(root, identity) { free }
    private fun sha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it) }

    private suspend fun failure(reason: LocalModelFailure, action: suspend () -> Unit) {
        try {
            action()
            fail("Expected fixed failure $reason")
        } catch (expected: LocalModelException) {
            assertEquals(reason, expected.failure)
            // Coroutine stack recovery may copy this same fixed exception, but never a provider cause.
            var current: Throwable? = expected
            val seen = java.util.Collections.newSetFromMap(java.util.IdentityHashMap<Throwable, Boolean>())
            while (current != null) {
                assertTrue(seen.add(current))
                assertTrue(seen.size <= 8)
                assertEquals(LocalModelException::class.java, current.javaClass)
                assertEquals("Local model unavailable: ${reason.name}", current.message)
                current = current.cause
            }
        }
    }

    private fun assertNoPartial(root: File) {
        assertFalse(File(root, "model.part").exists())
        assertFalse(File(root, "model.litertlm").exists())
    }

    @Test fun planningAndMissingInspectionDoNotCreateRoot() = runBlocking {
        val root = root()
        val store = store(root)
        assertEquals(LocalModelFiles(root, File(root, "model.litertlm"), File(root, "cache")), store.plannedFiles())
        assertFalse(root.exists())
        assertNull(store.installed())
        assertFalse(root.exists())
    }

    @Test fun volumeRefusalPrecedesRootCreationAndSourceOpen() = runBlocking {
        val root = root()
        var opens = 0
        val store = LocalModelStore(root, identity, storageAdmission = {
            throw LocalModelException(LocalModelFailure.STORAGE)
        })
        failure(LocalModelFailure.STORAGE) { store.import { opens++; ByteArrayInputStream(bytes) } }
        failure(LocalModelFailure.STORAGE) { store.installed() }
        assertEquals(0, opens)
        assertFalse(root.exists())
    }

    @Test fun changedVolumeAfterSourceOpenPreventsPublishAndCleanupOnReplacement() = runBlocking {
        val root = root()
        var changed = false
        var admittedBytes = -1L
        var publications = 0
        val store = LocalModelStore(root, identity, publish = { publications++ },
            availableBytes = { Long.MAX_VALUE }, storageAdmission = { missing ->
                if (changed) throw LocalModelException(LocalModelFailure.STORAGE)
                admittedBytes = maxOf(admittedBytes, missing)
            })
        failure(LocalModelFailure.STORAGE) {
            store.import { changed = true; ByteArrayInputStream(bytes) }
        }
        assertEquals(identity.bytes, admittedBytes)
        assertEquals(0, publications)
        assertFalse(File(root, "model.litertlm").exists())
        // Refusal preserves the owned partial stage: cleanup cannot operate on a changed mount.
        assertArrayEquals(bytes, File(root, "model.part").readBytes())
    }

    @Test fun importPublishesExactBytesAndRestartRehashes() = runBlocking {
        val root = root()
        val result = store(root).import { ByteArrayInputStream(bytes) }
        assertArrayEquals(bytes, result.model.readBytes())
        assertTrue(result.cache.isDirectory)
        assertFalse(File(root, "model.part").exists())
        assertEquals(result, store(root).installed())
        assertTrue(File(root, "model-import.lock").isFile)
    }

    @Test fun publicationFailureIsSanitizedAndRetainsNoPartialModel() = runBlocking {
        val root = root()
        val store = LocalModelStore(root, identity,
            publish = { throw IOException("private platform path and error") },
            availableBytes = { Long.MAX_VALUE })
        failure(LocalModelFailure.STORAGE) { store.import { ByteArrayInputStream(bytes) } }
        assertNoPartial(root)
        assertNull(store(root).installed())
    }

    @Test fun cancellationImmediatelyAfterAtomicMoveKeepsVerifiedModel() = runBlocking {
        val root = root()
        val copying = async(Dispatchers.IO) {
            val job = kotlin.coroutines.coroutineContext[kotlinx.coroutines.Job]!!
            LocalModelStore(root, identity, publish = { directory ->
                Files.move(File(directory, "model.part").toPath(), File(directory, "model.litertlm").toPath())
                job.cancel()
            }, availableBytes = { Long.MAX_VALUE }).import { ByteArrayInputStream(bytes) }
        }
        copying.join()
        assertTrue(copying.isCancelled)
        assertArrayEquals(bytes, File(root, "model.litertlm").readBytes())
        assertFalse(File(root, "model.part").exists())
        assertNotNull(store(root).installed())
    }

    @Test fun exactlyEnoughSpaceIncludesReserveWithoutOverflow() = runBlocking {
        val root = root()
        store(root, identity.bytes + identity.reserveBytes).import { ByteArrayInputStream(bytes) }
        assertArrayEquals(bytes, File(root, "model.litertlm").readBytes())
        val huge = identity.copy(bytes = Long.MAX_VALUE, reserveBytes = Long.MAX_VALUE)
        val second = root()
        failure(LocalModelFailure.NO_SPACE) {
            testStore(second, huge) { Long.MAX_VALUE }.import { error("must not open") }
        }
        assertNoPartial(second)
    }

    @Test fun lowSpaceRefusesBeforeOpeningSourceAndPreservesCache() = runBlocking {
        val root = root().also { it.mkdir() }
        val cache = File(root, "cache").also { it.mkdir() }
        val marker = File(cache, "original.bin").also { it.writeBytes(byteArrayOf(9, 8, 7)) }
        failure(LocalModelFailure.NO_SPACE) {
            store(root, identity.bytes + identity.reserveBytes - 1).import { error("must not open") }
        }
        assertArrayEquals(byteArrayOf(9, 8, 7), marker.readBytes())
        assertNoPartial(root)
    }

    @Test fun truncatedAndEmptyStreamsCannotPublish() = runBlocking {
        for (source in listOf(ByteArray(0), bytes.copyOf(bytes.size - 1))) {
            val root = root()
            failure(LocalModelFailure.INVALID_MODEL) { store(root).import { ByteArrayInputStream(source) } }
            assertNoPartial(root)
            assertNull(store(root).installed())
        }
    }

    @Test fun incorrectDigestCannotPublishAndRetryWorks() = runBlocking {
        val root = root()
        val wrong = bytes.copyOf().also { it[12] = (it[12] + 1).toByte() }
        failure(LocalModelFailure.INVALID_MODEL) { store(root).import { ByteArrayInputStream(wrong) } }
        assertNoPartial(root)
        store(root).import { ByteArrayInputStream(bytes) }
        assertArrayEquals(bytes, File(root, "model.litertlm").readBytes())
    }

    @Test fun oversizedUnboundedSourceReadsOnlyExpectedSizePlusOne() = runBlocking {
        val root = root()
        val reads = AtomicInteger()
        val closed = AtomicInteger()
        val source = object : InputStream() {
            override fun read(): Int = error("bulk read required")
            override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                assertTrue(length in 1..65_536)
                buffer.fill(0, offset, offset + length)
                reads.addAndGet(length)
                return length
            }
            override fun close() { closed.incrementAndGet() }
        }
        failure(LocalModelFailure.INVALID_MODEL) { store(root).import { source } }
        assertEquals(bytes.size + 1, reads.get())
        assertEquals(1, closed.get())
        assertNoPartial(root)
    }

    @Test fun nonProgressingStreamFailsInsteadOfSpinning() = runBlocking {
        val root = root()
        val calls = AtomicInteger()
        failure(LocalModelFailure.INVALID_MODEL) {
            store(root).import {
                object : InputStream() {
                    override fun read(): Int = 0
                    override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                        calls.incrementAndGet(); return 0
                    }
                }
            }
        }
        assertEquals(1, calls.get())
        assertNoPartial(root)
    }

    @Test fun privateOpenReadAndCloseErrorsAreSanitizedAndCleaned() = runBlocking {
        for (phase in listOf("open", "read", "close")) {
            val root = root()
            val closes = AtomicInteger()
            failure(LocalModelFailure.STORAGE) {
                store(root).import {
                    if (phase == "open") throw IOException("private content://provider/secret-open")
                    object : ByteArrayInputStream(bytes) {
                        override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                            if (phase == "read") throw IOException("private secret-read")
                            return super.read(buffer, offset, length)
                        }
                        override fun close() {
                            closes.incrementAndGet()
                            if (phase == "close") throw IOException("private secret-close")
                        }
                    }
                }
            }
            assertEquals(if (phase == "open") 0 else 1, closes.get())
            assertNoPartial(root)
        }
    }

    @Test fun validExistingArtifactNeverOpensOrReplacesFromProvider() = runBlocking {
        val root = root()
        val first = store(root).import { ByteArrayInputStream(bytes) }
        val marker = File(first.cache, "retain").also { it.writeText("cache-original") }
        val key = Files.readAttributes(first.model.toPath(), java.nio.file.attribute.BasicFileAttributes::class.java).fileKey()
        assertEquals(first, store(root, 0).import { error("must not open") })
        assertEquals(key, Files.readAttributes(first.model.toPath(), java.nio.file.attribute.BasicFileAttributes::class.java).fileKey())
        assertEquals("cache-original", marker.readText())
    }

    @Test fun existingCorruptArtifactIsPreservedOnInspectionAndImport() = runBlocking {
        for (original in listOf(bytes.copyOf(5), bytes.copyOf().also { it[0] = 0 })) {
            val root = root().also { it.mkdir() }
            val model = File(root, "model.litertlm").also { it.writeBytes(original) }
            failure(LocalModelFailure.INVALID_MODEL) { store(root).installed() }
            failure(LocalModelFailure.INVALID_MODEL) { store(root).import { error("must not open") } }
            assertArrayEquals(original, model.readBytes())
            assertFalse(File(root, "model.part").exists())
        }
    }

    @Test fun restartDetectsSameLengthTamperingRatherThanTrustingReceipt() = runBlocking {
        val root = root()
        val files = store(root).import { ByteArrayInputStream(bytes) }
        val modified = files.model.lastModified()
        val altered = bytes.copyOf().also { it[it.lastIndex] = (it.last() + 1).toByte() }
        files.model.writeBytes(altered)
        files.model.setLastModified(modified)
        failure(LocalModelFailure.INVALID_MODEL) { store(root).installed() }
        assertArrayEquals(altered, files.model.readBytes())
    }

    @Test fun staleKnownPartialRecoversButUnknownFilesRemain() = runBlocking {
        val root = root().also { it.mkdir() }
        File(root, "model.part").writeBytes(byteArrayOf(1, 2))
        val unknown = File(root, ".import-other-owner").also { it.writeText("preserve") }
        assertNull(store(root).installed())
        assertFalse(File(root, "model.part").exists())
        assertEquals("preserve", unknown.readText())
        store(root).import { ByteArrayInputStream(bytes) }
        assertEquals("preserve", unknown.readText())
    }

    @Test fun publishedArtifactWithStaleHardlinkRecoversAfterProcessDeath() = runBlocking {
        val root = root()
        val files = store(root).import { ByteArrayInputStream(bytes) }
        Files.createLink(File(root, "model.part").toPath(), files.model.toPath())
        assertEquals(files, store(root).installed())
        assertFalse(File(root, "model.part").exists())
        assertArrayEquals(bytes, files.model.readBytes())
    }

    @Test fun unknownStagingDirectoryIsNotRecursivelyDeleted() = runBlocking {
        val root = root().also { it.mkdir() }
        val stage = File(root, "model.part").also { it.mkdir() }
        val content = File(stage, "foreign").also { it.writeText("preserve") }
        failure(LocalModelFailure.UNSAFE_PATH) { store(root).import { error("must not open") } }
        assertEquals("preserve", content.readText())
    }

    @Test fun atomicPublicationCannotOverwriteDestinationAppearingDuringRead() = runBlocking {
        val root = root()
        val interloper = byteArrayOf(4, 3, 2, 1)
        failure(LocalModelFailure.STORAGE) {
            store(root).import {
                object : ByteArrayInputStream(bytes) {
                    override fun close() { File(root, "model.litertlm").writeBytes(interloper) }
                }
            }
        }
        assertArrayEquals(interloper, File(root, "model.litertlm").readBytes())
        assertFalse(File(root, "model.part").exists())
    }

    @Test fun invalidCacheCannotBeReplacedByDirectoryCreation() = runBlocking {
        val root = root().also { it.mkdir() }
        val cache = File(root, "cache").also { it.writeText("prior cache file") }
        failure(LocalModelFailure.UNSAFE_PATH) { store(root).import { error("must not open") } }
        assertEquals("prior cache file", cache.readText())
        assertNoPartial(root)
    }

    @Test fun cacheChangedDuringProviderCloseIsPreservedAndPreventsPublication() = runBlocking {
        val root = root()
        failure(LocalModelFailure.UNSAFE_PATH) {
            store(root).import {
                object : ByteArrayInputStream(bytes) {
                    override fun close() { File(root, "cache").writeText("foreign path") }
                }
            }
        }
        assertNoPartial(root)
        assertEquals("foreign path", File(root, "cache").readText())
    }

    @Test fun externalLockExcludesImportAndIsNeverUnlinked() = runBlocking {
        val root = root().also { it.mkdir() }
        val lock = File(root, "model-import.lock")
        FileChannel.open(lock.toPath(), CREATE, WRITE).use { channel ->
            channel.lock().use {
                failure(LocalModelFailure.BUSY) { store(root).import { error("must not open") } }
                failure(LocalModelFailure.BUSY) { store(root).installed() }
                assertTrue(lock.exists())
            }
        }
        store(root).import { ByteArrayInputStream(bytes) }
        assertTrue(lock.exists())
    }

    @Test fun cancellationKeepsSlotUntilBlockedReadReturnsAndCloses() = runBlocking {
        val root = root()
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val closed = AtomicInteger()
        val sourceThread = AtomicReference<String>()
        val import = async(Dispatchers.Default) {
            store(root).import {
                sourceThread.set(Thread.currentThread().name)
                object : ByteArrayInputStream(bytes) {
                    override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                        entered.countDown()
                        check(release.await(3, TimeUnit.SECONDS))
                        return super.read(buffer, offset, length)
                    }
                    override fun close() { closed.incrementAndGet() }
                }
            }
        }
        try {
            assertTrue(entered.await(3, TimeUnit.SECONDS))
            import.cancel()
            assertFalse(import.isCompleted)
            failure(LocalModelFailure.BUSY) { store(root).import { error("must not open") } }
            assertEquals(0, closed.get())
        } finally {
            release.countDown()
            import.cancelAndJoin()
        }
        assertEquals(1, closed.get())
        assertNotEquals(Thread.currentThread().name, sourceThread.get())
        assertNoPartial(root)
        store(root).import { ByteArrayInputStream(bytes) }
        assertArrayEquals(bytes, File(root, "model.litertlm").readBytes())
    }

    @Test fun cancellationDuringBlockedOpenOrCloseRetainsSlotUntilActualReturn() = runBlocking {
        for (phase in listOf("open", "close")) {
            val root = root()
            val entered = CountDownLatch(1)
            val release = CountDownLatch(1)
            val closes = AtomicInteger()
            fun block() {
                entered.countDown()
                check(release.await(3, TimeUnit.SECONDS))
            }
            val import = async(Dispatchers.Default) {
                store(root).import {
                    if (phase == "open") block()
                    object : ByteArrayInputStream(bytes) {
                        override fun close() {
                            closes.incrementAndGet()
                            if (phase == "close") block()
                        }
                    }
                }
            }
            try {
                assertTrue(entered.await(3, TimeUnit.SECONDS))
                import.cancel()
                assertFalse(import.isCompleted)
                failure(LocalModelFailure.BUSY) { store(root).installed() }
            } finally {
                release.countDown()
                import.cancelAndJoin()
            }
            assertEquals(1, closes.get())
            assertNoPartial(root)
            assertNull(store(root).installed())
        }
    }

    @Test fun normalizedTraversalRootIsRejectedWithoutCreatingDestination() = runBlocking {
        val parent = temporary.newFolder()
        val root = File(parent, "foreign/../local-model-v1")
        failure(LocalModelFailure.UNSAFE_PATH) { store(root).import { error("must not open") } }
        assertFalse(File(parent, "foreign").exists())
        assertFalse(File(parent, "local-model-v1").exists())
    }

    @Test fun symlinksAtEveryOwnedPathAreRefusedWithoutTouchingTargets() = runBlocking {
        // Host Windows policy can forbid creating links. Such a host reports this test skipped;
        // it must not be counted as symlink protection execution evidence.
        val probeTarget = temporary.newFolder()
        val probeLink = File(temporary.newFolder(), "probe")
        try {
            Files.createSymbolicLink(probeLink.toPath(), probeTarget.toPath())
        } catch (unsupported: IOException) {
            assumeNoException("Host policy cannot create symbolic links", unsupported)
        } catch (unsupported: UnsupportedOperationException) {
            assumeNoException("Host filesystem cannot create symbolic links", unsupported)
        }
        Files.delete(probeLink.toPath())
        for (name in listOf("root", "model.litertlm", "cache", "model.part", "model-import.lock")) {
            val root = root()
            val target = temporary.newFolder()
            val marker = File(target, "foreign").also { it.writeText("preserve-$name") }
            val path = if (name == "root") root else {
                root.mkdir()
                File(root, name)
            }
            Files.createSymbolicLink(path.toPath(), target.toPath())
            failure(LocalModelFailure.UNSAFE_PATH) { store(root).import { error("must not open") } }
            assertEquals("preserve-$name", marker.readText())
            assertTrue(Files.isSymbolicLink(path.toPath()))
        }
    }
}
