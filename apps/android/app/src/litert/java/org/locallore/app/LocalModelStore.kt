/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File
import java.io.InputStream
import java.nio.channels.FileChannel
import java.nio.channels.OverlappingFileLockException
import java.nio.file.Files
import java.nio.file.FileAlreadyExistsException
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.Path
import java.nio.file.StandardOpenOption.CREATE
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.READ
import java.nio.file.StandardOpenOption.WRITE
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.coroutines.coroutineContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext

/** Built-in artifact identity. Neither picker metadata nor imported bytes supply this value. */
internal data class LocalModelIdentity(
    val id: String,
    val bytes: Long,
    val sha256: String,
    val reserveBytes: Long = 268_435_456,
) {
    init {
        require(id.matches(Regex("[a-z0-9][a-z0-9.-]{0,79}")))
        require(bytes > 0 && reserveBytes >= 0)
        require(sha256.matches(Regex("[0-9a-f]{64}")))
    }
}

internal data class LocalModelFiles(val root: File, val model: File, val cache: File)
internal enum class LocalModelFailure { BUSY, NO_SPACE, INVALID_MODEL, UNSAFE_PATH, STORAGE }

/** No source exception, path, URI, filename, or provider message crosses into UI state. */
internal class LocalModelException(val failure: LocalModelFailure) :
    Exception("Local model unavailable: ${failure.name}")

/**
 * One app-private artifact, separate from stories and benchmark caches. All file work is on IO.
 * A persistent lock inode serializes cooperating instances/processes. Only the fixed model.part
 * is recoverable staging; unknown files and all prior model/cache contents are preserved.
 * Publication uses an atomic no-clobber native rename after file force, never ATOMIC_MOVE
 * (whose destination replacement is implementation-specific). Unsupported filesystems fail closed.
 * This does not promise directory durability after sudden power loss or defend a compromised OS.
 */
internal class LocalModelStore(
    root: File,
    private val identity: LocalModelIdentity,
    private val publish: (File) -> Unit = NativeModelPublication::publish,
    private val availableBytes: () -> Long = { root.usableSpace },
    private val storageAdmission: (missingModelBytes: Long) -> Unit = {},
) {
    private val base = root.absoluteFile
    private val model = File(base, "model.litertlm")
    private val cache = File(base, "cache")
    private val staging = File(base, "model.part")
    private val lock = File(base, "model-import.lock")

    /** Pure path planning only; existence/integrity is never inferred from these returned paths. */
    fun plannedFiles(): LocalModelFiles = LocalModelFiles(base, model, cache)

    /** Rechecked on IO immediately before deferred runtime construction. */
    internal fun admitRuntime() = storageAdmission(0)

    /** Rehash on every reopen. Missing means absent; corrupt/unsafe/busy is an explicit failure. */
    suspend fun installed(): LocalModelFiles? = guarded {
        if (!prepareRoot(create = false)) return@guarded null
        locked {
            recoverStaging()
            if (!exists(model.toPath())) return@locked null
            validateModel()
            prepareCache()
            plannedFiles()
        }
    }

    /** Cancellation after publication can leave a complete valid model; it never deletes it. */
    suspend fun import(open: () -> InputStream): LocalModelFiles = guarded {
        prepareRoot(create = true)
        locked {
            recoverStaging()
            if (exists(model.toPath())) {
                validateModel() // Even corrupt artifacts are preserved, never silently replaced.
                prepareCache()
                return@locked plannedFiles()
            }
            checkCache()
            storageAdmission(identity.bytes)
            val free = availableBytes()
            if (free < identity.reserveBytes || free - identity.reserveBytes < identity.bytes) {
                fail(LocalModelFailure.NO_SPACE)
            }
            coroutineContext.ensureActive()
            var ownsStage = false
            try {
                FileChannel.open(staging.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { output ->
                    ownsStage = true
                    val before = regular(staging.toPath())
                    val digest = MessageDigest.getInstance("SHA-256")
                    var count = 0L
                    open().use { input ->
                        val buffer = ByteArray(BUFFER_BYTES)
                        while (true) {
                            coroutineContext.ensureActive()
                            val remaining = identity.bytes - count
                            val limit = if (remaining >= buffer.size) buffer.size else remaining.toInt() + 1
                            val read = input.read(buffer, 0, limit)
                            coroutineContext.ensureActive()
                            if (read < 0) break
                            if (read == 0 || read.toLong() > identity.bytes - count) {
                                fail(LocalModelFailure.INVALID_MODEL)
                            }
                            count += read
                            digest.update(buffer, 0, read)
                            val bytes = java.nio.ByteBuffer.wrap(buffer, 0, read)
                            while (bytes.hasRemaining()) {
                                coroutineContext.ensureActive()
                                output.write(bytes)
                            }
                        }
                    }
                    if (count != identity.bytes || digest.hex() != identity.sha256) {
                        fail(LocalModelFailure.INVALID_MODEL)
                    }
                    output.force(true)
                    val after = regular(staging.toPath())
                    if (after.size() != count || !sameFile(before, after)) {
                        fail(LocalModelFailure.UNSAFE_PATH)
                    }
                }
                coroutineContext.ensureActive()
                checkRoot()
                checkCache()
                regular(staging.toPath())
                // Android application policy prohibits hard links. The native operation atomically
                // moves this fixed stage and refuses ANY destination, including a symlink.
                publish(base)
                ownsStage = false
                prepareCache()
                coroutineContext.ensureActive()
                plannedFiles()
            } finally {
                // Only the path this import created, while still holding the persistent lock.
                if (ownsStage) {
                    checkRoot()
                    regular(staging.toPath())
                    Files.delete(staging.toPath())
                }
            }
        }
    }

    private suspend fun validateModel() {
        storageAdmission(0)
        val before = regular(model.toPath())
        if (before.size() != identity.bytes) fail(LocalModelFailure.INVALID_MODEL)
        val digest = MessageDigest.getInstance("SHA-256")
        var count = 0L
        Files.newInputStream(model.toPath(), READ, NOFOLLOW_LINKS).use { input ->
            val buffer = ByteArray(BUFFER_BYTES)
            while (true) {
                coroutineContext.ensureActive()
                val read = input.read(buffer)
                if (read < 0) break
                if (read == 0 || read.toLong() > identity.bytes - count) {
                    fail(LocalModelFailure.INVALID_MODEL)
                }
                count += read
                digest.update(buffer, 0, read)
            }
        }
        coroutineContext.ensureActive()
        checkRoot()
        val after = regular(model.toPath())
        if (!sameFile(before, after) || before.lastModifiedTime() != after.lastModifiedTime()) {
            fail(LocalModelFailure.UNSAFE_PATH)
        }
        if (count != identity.bytes || digest.hex() != identity.sha256) {
            fail(LocalModelFailure.INVALID_MODEL)
        }
    }

    private fun prepareRoot(create: Boolean): Boolean {
        storageAdmission(0)
        if (base.canonicalFile != base || base.toPath().normalize() != base.toPath()) {
            fail(LocalModelFailure.UNSAFE_PATH)
        }
        if (!exists(base.toPath())) {
            if (!create) return false
            try {
                Files.createDirectory(base.toPath()) // Parent is the admitted app-owned anchor.
            } catch (_: FileAlreadyExistsException) {
                // A concurrent cooperating store may have created the root before taking its lock.
            }
        }
        checkRoot()
        return true
    }

    private fun checkRoot() {
        storageAdmission(0)
        if (base.canonicalFile != base || !attributes(base.toPath()).isDirectory) {
            fail(LocalModelFailure.UNSAFE_PATH)
        }
    }

    private fun checkCache() {
        checkRoot()
        if (exists(cache.toPath()) && !attributes(cache.toPath()).isDirectory) {
            fail(LocalModelFailure.UNSAFE_PATH)
        }
    }

    private fun prepareCache() {
        checkCache()
        if (!exists(cache.toPath())) Files.createDirectory(cache.toPath())
        checkCache()
    }

    private fun recoverStaging() {
        checkRoot()
        if (exists(staging.toPath())) {
            regular(staging.toPath())
            Files.delete(staging.toPath())
        }
    }

    private suspend fun <T> locked(action: suspend () -> T): T {
        // Closing another channel to this inode can release process-associated OS locks on some
        // platforms. Refuse same-process contenders before they can open a competing channel.
        if (!processSlot.compareAndSet(false, true)) fail(LocalModelFailure.BUSY)
        try {
            checkRoot()
            if (exists(lock.toPath())) regular(lock.toPath())
            FileChannel.open(lock.toPath(), CREATE, WRITE, NOFOLLOW_LINKS).use { channel ->
                val acquired = try {
                    channel.tryLock()
                } catch (_: OverlappingFileLockException) {
                    null
                } ?: fail(LocalModelFailure.BUSY)
                acquired.use {
                    checkRoot()
                    regular(lock.toPath())
                    coroutineContext.ensureActive()
                    return action()
                }
            }
        } finally {
            processSlot.set(false)
        }
    }

    private suspend fun <T> guarded(action: suspend () -> T): T = withContext(Dispatchers.IO) {
        try {
            coroutineContext.ensureActive()
            action()
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (failure: LocalModelException) {
            throw failure
        } catch (_: Exception) {
            throw LocalModelException(LocalModelFailure.STORAGE)
        }
    }

    private fun regular(path: Path): BasicFileAttributes = attributes(path).also {
        if (!it.isRegularFile) fail(LocalModelFailure.UNSAFE_PATH)
    }

    private fun attributes(path: Path): BasicFileAttributes =
        Files.readAttributes(path, BasicFileAttributes::class.java, NOFOLLOW_LINKS).also {
            if (it.isSymbolicLink) fail(LocalModelFailure.UNSAFE_PATH)
        }

    private fun exists(path: Path): Boolean = Files.exists(path, NOFOLLOW_LINKS)
    private fun sameFile(first: BasicFileAttributes, second: BasicFileAttributes): Boolean =
        first.fileKey() == second.fileKey()

    private fun MessageDigest.hex(): String = digest().joinToString("") { "%02x".format(it) }
    private fun fail(reason: LocalModelFailure): Nothing = throw LocalModelException(reason)

    private companion object {
        const val BUFFER_BYTES = 64 * 1024
        val processSlot = AtomicBoolean()
    }
}
