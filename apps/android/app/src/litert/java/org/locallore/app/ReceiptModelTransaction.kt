/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File
import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.channels.OverlappingFileLockException
import java.nio.file.FileAlreadyExistsException
import java.nio.file.Files
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

internal enum class ReceiptCheckpoint { RECEIPT_FORCED, DATA_FORCED, BEFORE_COMMIT, AFTER_COMMIT }

/**
 * Unwired host proof: exclusive receipt, owned data and an exclusive acceptance marker.
 * Marker creation is the logical visibility point, even if its subsequent force/close fails.
 * File force is not a promise of directory durability after power loss or a hostile OS.
 */
internal class ReceiptModelTransaction(
    controlRoot: File,
    dataRoot: File,
    private val identity: LocalModelIdentity,
    private val availableBytes: () -> Long = { dataRoot.parentFile.usableSpace },
    private val storageAdmission: (Long) -> Unit = {},
    private val checkpoint: (ReceiptCheckpoint) -> Unit = {},
) {
    private val control = controlRoot
    private val data = dataRoot
    private val lock = File(control, "model-import.lock")
    private val receipt = File(control, "model.receipt")
    private val accepted = File(control, "model.accepted")
    private val owner = File(data, "model.owner")
    private val model = File(data, "model.litertlm")
    private val cache = File(data, "cache")

    suspend fun installed(): LocalModelFiles? = guarded {
        guard()
        // An incomplete transaction is not a readable model and causes no creation here.
        if (!exists(control)) return@guarded null
        controlEntries()
        if (!exists(lock) && !exists(accepted)) return@guarded null
        locked(create = false) {
            if (!exists(accepted)) null else validateAccepted()
        }
    }

    suspend fun import(open: () -> InputStream): LocalModelFiles = guarded {
        guard()
        // Refuse unreceipted data before creating even a control lock.
        if ((!exists(control) || !exists(receipt)) && exists(data)) unsafe()
        if ((exists(receipt) || exists(accepted)) && !exists(lock)) unsafe()
        if (!exists(receipt) && !exists(accepted)) guard(identity.bytes)
        if (!exists(control)) createDirectory(control)
        locked(create = true) {
            controlEntries()
            if (exists(accepted)) return@locked validateAccepted()
            if (exists(receipt)) {
                exact(receipt, receiptBytes)
            } else {
                if (exists(data)) unsafe()
                guard(identity.bytes)
                forcedNew(receipt, receiptBytes)
                checkpoint(ReceiptCheckpoint.RECEIPT_FORCED)
                coroutineContext.ensureActive()
            }
            guard()
            exact(receipt, receiptBytes)
            if (exists(data)) {
                // A preexisting directory can never acquire an owner during recovery.
                dataEntries(pending = true)
                validateModel()
            } else {
                guard(identity.bytes)
                createDirectory(data)
                forcedNew(owner, ownerBytes)
                copyModel(open)
                checkpoint(ReceiptCheckpoint.DATA_FORCED)
                coroutineContext.ensureActive()
            }
            validatePending()
            checkpoint(ReceiptCheckpoint.BEFORE_COMMIT)
            coroutineContext.ensureActive()
            // A trusted test hook may revoke admission or alter files at the boundary.
            validatePending()
            coroutineContext.ensureActive()
            if (exists(accepted)) unsafe()
            forcedNew(accepted, byteArrayOf())
            checkpoint(ReceiptCheckpoint.AFTER_COMMIT)
            coroutineContext.ensureActive()
            files()
        }
    }

    /** Explicitly discard only receipt-matched, owned, unaccepted, whitelisted files. */
    suspend fun discardUncommitted(): Unit = guarded {
        guard()
        if (!exists(control)) {
            if (exists(data)) unsafe()
            return@guarded
        }
        controlEntries()
        if (exists(accepted)) unsafe()
        if (!exists(receipt)) {
            if (exists(data)) unsafe()
            return@guarded
        }
        locked(create = false) {
            discardCheck(ownerRemoved = false) // Inspect every entry before ANY deletion.
            if (exists(data)) {
                if (exists(model)) {
                    discardCheck(ownerRemoved = false)
                    Files.delete(model.toPath())
                }
                if (exists(cache)) {
                    discardCheck(ownerRemoved = false)
                    Files.delete(cache.toPath())
                }
                discardCheck(ownerRemoved = false)
                Files.delete(owner.toPath())
                // Missing-owner recovery is never generally allowed: only this held operation
                // may remove the now-empty directory after it deleted its validated owner.
                discardCheck(ownerRemoved = true)
                Files.delete(data.toPath())
                pins.remove(data.toPath())
            }
            discardCheck(ownerRemoved = true)
            Files.delete(receipt.toPath())
        }
    }

    private fun files() = LocalModelFiles(data, model, cache)

    private suspend fun <T> guarded(action: suspend Operation.() -> T): T =
        withContext(Dispatchers.IO) {
            coroutineContext.ensureActive()
            // Never open another same-process channel that could disturb an OS lock.
            if (!processSlot.compareAndSet(false, true)) fail(LocalModelFailure.BUSY)
            try {
                Operation().action()
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (failure: LocalModelException) {
                throw failure
            } catch (_: Exception) {
                fail(LocalModelFailure.STORAGE)
            } finally {
                processSlot.set(false)
            }
        }

    private inner class Operation {
        val pins = mutableMapOf<Path, Any?>()
        private var lockPin: BasicFileAttributes? = null
        val receiptBytes: ByteArray by lazy {
            ("locallore-model-receipt-v1\n${identity.id}\n${identity.bytes}\n" +
                "${identity.sha256}\n${sha(data.path.toByteArray(Charsets.UTF_8))}\n")
                .toByteArray(Charsets.UTF_8).also { if (it.size > RECEIPT_LIMIT) unsafe() }
        }
        val ownerBytes: ByteArray by lazy {
            ("locallore-model-owner-v1\n${sha(control.path.toByteArray(Charsets.UTF_8))}\n" +
                "${sha(receiptBytes)}\n").toByteArray(Charsets.UTF_8)
        }

        fun guard(missingBytes: Long = 0) {
            storageAdmission(missingBytes)
            if (!control.isAbsolute || !data.isAbsolute || control.toPath().startsWith(data.toPath()) ||
                data.toPath().startsWith(control.toPath())) unsafe()
            checkPath(control)
            checkPath(data)
            lockPin?.let { if (!same(it, regular(lock))) unsafe() }
            val free = availableBytes()
            if (free < identity.reserveBytes || missingBytes > free - identity.reserveBytes) {
                fail(LocalModelFailure.NO_SPACE)
            }
        }

        private fun checkPath(file: File) {
            val path = file.toPath()
            if (file.canonicalFile != file || path.normalize() != path || path.parent == null) unsafe()
            var cursor: Path? = path
            if (!exists(file)) {
                if (pins.containsKey(path)) unsafe()
                cursor = path.parent
            }
            while (cursor != null) {
                val attrs = attributes(cursor)
                if (!attrs.isDirectory) unsafe()
                if (pins.containsKey(cursor) && pins[cursor] != attrs.fileKey()) unsafe()
                pins[cursor] = attrs.fileKey()
                cursor = cursor.parent
            }
        }

        suspend fun <T> locked(create: Boolean, action: suspend () -> T): T {
            guard()
            controlEntries()
            val before = if (exists(lock)) regular(lock) else null
            if (!create && before == null) unsafe()
            if (before == null && (exists(receipt) || exists(accepted))) unsafe()
            val options = if (create) arrayOf(CREATE, WRITE, NOFOLLOW_LINKS) else arrayOf(WRITE, NOFOLLOW_LINKS)
            FileChannel.open(lock.toPath(), *options).use { channel ->
                val acquired = try { channel.tryLock() } catch (_: OverlappingFileLockException) { null }
                    ?: fail(LocalModelFailure.BUSY)
                acquired.use {
                    val now = regular(lock)
                    if (before != null && !same(before, now)) unsafe()
                    lockPin = now
                    guard()
                    coroutineContext.ensureActive()
                    return action()
                }
            }
        }

        fun controlEntries() {
            guard()
            entries(control, setOf(lock.name, receipt.name, accepted.name))
            if (exists(lock)) regular(lock)
            if (exists(receipt)) regular(receipt)
            if (exists(accepted)) regular(accepted)
        }

        fun dataEntries(pending: Boolean) {
            guard()
            if (!exists(data)) unsafe()
            entries(data, setOf(owner.name, model.name, cache.name))
            exact(owner, ownerBytes)
            if (exists(model)) regular(model)
            checkCache(empty = pending)
        }

        private fun checkCache(empty: Boolean) {
            guard()
            if (!exists(cache)) return
            if (!attributes(cache.toPath()).isDirectory) unsafe()
            if (empty) entries(cache, emptySet())
        }

        private fun ensureCache(empty: Boolean) {
            checkCache(empty)
            if (!exists(cache)) createDirectory(cache)
            checkCache(empty)
        }

        suspend fun validateAccepted(): LocalModelFiles {
            controlEntries()
            if (!exists(accepted) || regular(accepted).size() != 0L) unsafe()
            exact(receipt, receiptBytes)
            dataEntries(pending = false)
            if (!exists(cache)) unsafe()
            validateModel()
            checkCache(empty = false)
            guard()
            exact(receipt, receiptBytes)
            exact(owner, ownerBytes)
            if (regular(accepted).size() != 0L) unsafe()
            return files()
        }

        suspend fun validatePending() {
            controlEntries()
            if (exists(accepted)) unsafe()
            exact(receipt, receiptBytes)
            dataEntries(pending = true)
            validateModel()
            ensureCache(empty = true)
            guard()
        }

        suspend fun copyModel(open: () -> InputStream) {
            guard(identity.bytes)
            exact(owner, ownerBytes)
            if (exists(model)) unsafe()
            try {
                FileChannel.open(model.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { output ->
                    val before = regular(model)
                    val digest = MessageDigest.getInstance("SHA-256")
                    var count = 0L
                    guard(identity.bytes)
                    coroutineContext.ensureActive()
                    open().use { input ->
                        val buffer = ByteArray(BUFFER_BYTES)
                        while (true) {
                            coroutineContext.ensureActive()
                            guard()
                            val remaining = identity.bytes - count
                            val limit = if (remaining >= buffer.size) buffer.size else remaining.toInt() + 1
                            val read = input.read(buffer, 0, limit)
                            coroutineContext.ensureActive()
                            if (read < 0) break
                            if (read == 0 || read > limit || read.toLong() > identity.bytes - count) invalid()
                            count += read
                            digest.update(buffer, 0, read)
                            val bytes = ByteBuffer.wrap(buffer, 0, read)
                            while (bytes.hasRemaining()) {
                                coroutineContext.ensureActive()
                                guard()
                                if (output.write(bytes) <= 0) fail(LocalModelFailure.STORAGE)
                            }
                        }
                    }
                    if (count != identity.bytes || digest.hex() != identity.sha256) invalid()
                    guard()
                    output.force(true)
                    val after = regular(model)
                    if (!same(before, after) || after.size() != identity.bytes) unsafe()
                }
            } catch (_: FileAlreadyExistsException) { unsafe() }
        }

        suspend fun validateModel() {
            guard()
            exact(owner, ownerBytes)
            if (!exists(model)) invalid()
            val before = regular(model)
            if (before.size() != identity.bytes) invalid()
            val digest = MessageDigest.getInstance("SHA-256")
            var count = 0L
            Files.newInputStream(model.toPath(), READ, NOFOLLOW_LINKS).use { input ->
                val buffer = ByteArray(BUFFER_BYTES)
                while (true) {
                    coroutineContext.ensureActive()
                    guard()
                    val remaining = identity.bytes - count
                    val limit = if (remaining >= buffer.size) buffer.size else remaining.toInt() + 1
                    val read = input.read(buffer, 0, limit)
                    if (read < 0) break
                    if (read == 0 || read.toLong() > identity.bytes - count) invalid()
                    count += read
                    digest.update(buffer, 0, read)
                }
            }
            coroutineContext.ensureActive()
            guard()
            val after = regular(model)
            if (!same(before, after) || before.size() != after.size() ||
                before.lastModifiedTime() != after.lastModifiedTime()) unsafe()
            if (count != identity.bytes || digest.hex() != identity.sha256) invalid()
            exact(owner, ownerBytes)
        }

        fun discardCheck(ownerRemoved: Boolean) {
            guard()
            controlEntries()
            if (exists(accepted)) unsafe()
            exact(receipt, receiptBytes)
            if (!exists(data)) return
            if (ownerRemoved) {
                entries(data, emptySet())
            } else {
                dataEntries(pending = true)
                if (exists(model) && regular(model).size() > identity.bytes) unsafe()
            }
        }

        fun createDirectory(file: File) {
            guard()
            try { Files.createDirectory(file.toPath()) } catch (_: FileAlreadyExistsException) { unsafe() }
            guard()
        }

        fun forcedNew(file: File, bytes: ByteArray) {
            guard()
            try {
                FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
                    val buffer = ByteBuffer.wrap(bytes)
                    while (buffer.hasRemaining()) {
                        guard()
                        if (channel.write(buffer) <= 0) fail(LocalModelFailure.STORAGE)
                    }
                    guard()
                    channel.force(true)
                }
            } catch (_: FileAlreadyExistsException) { unsafe() }
            guard()
        }

        fun exact(file: File, expected: ByteArray) {
            guard()
            if (!exists(file)) unsafe()
            val before = regular(file)
            if (before.size() != expected.size.toLong() || before.size() > RECEIPT_LIMIT) unsafe()
            val bytes = ByteArray(expected.size + 1)
            var count = 0
            Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS).use { input ->
                while (count < bytes.size) {
                    guard()
                    val read = input.read(bytes, count, bytes.size - count)
                    if (read < 0) break
                    if (read == 0) unsafe()
                    count += read
                }
            }
            guard()
            val after = regular(file)
            if (!same(before, after) || before.size() != after.size() ||
                before.lastModifiedTime() != after.lastModifiedTime() || count != expected.size ||
                !MessageDigest.isEqual(expected, bytes.copyOf(count))) unsafe()
        }

        private fun entries(directory: File, allowed: Set<String>) {
            guard()
            Files.newDirectoryStream(directory.toPath()).use { children ->
                for (child in children) if (child.fileName.toString() !in allowed) unsafe()
            }
        }
    }

    private fun attributes(path: Path): BasicFileAttributes =
        Files.readAttributes(path, BasicFileAttributes::class.java, NOFOLLOW_LINKS).also {
            if (it.isSymbolicLink) unsafe()
        }
    private fun regular(file: File) = attributes(file.toPath()).also { if (!it.isRegularFile) unsafe() }
    private fun exists(file: File) = Files.exists(file.toPath(), NOFOLLOW_LINKS)
    private fun same(first: BasicFileAttributes, second: BasicFileAttributes) = first.fileKey() == second.fileKey()
    private fun sha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).hexBytes()
    private fun MessageDigest.hex() = digest().hexBytes()
    private fun ByteArray.hexBytes() = joinToString("") { "%02x".format(it) }
    private fun invalid(): Nothing = fail(LocalModelFailure.INVALID_MODEL)
    private fun unsafe(): Nothing = fail(LocalModelFailure.UNSAFE_PATH)
    private fun fail(reason: LocalModelFailure): Nothing = throw LocalModelException(reason)

    private companion object {
        const val BUFFER_BYTES = 64 * 1024
        const val RECEIPT_LIMIT = 512
        val processSlot = AtomicBoolean()
    }
}
