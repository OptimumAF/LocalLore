/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.system.Os
import android.system.OsConstants
import android.util.AtomicFile
import java.io.File
import java.io.FileInputStream
import java.io.FileNotFoundException

/** Only a fixed fork input hint. It is never a canonical story, session, or executable operation. */
internal interface ForkRecoveryPersistence {
    fun load(): BranchForkRecovery?
    /** Completes synchronously or throws BEFORE the controller can register native work. */
    fun save(value: BranchForkRecovery?)
}
internal class ForkRecoveryFailure : Exception("Timeline recovery hint unavailable")

/** Fixed app noBackup path, bounded reads, one process-wide writer gate and compare-before-write.
 * This does not coordinate arbitrary external processes or guarantee storage hardware behavior.
 */
internal class AtomicForkRecoveryStore(context: Context) : ForkRecoveryPersistence {
    private val directory = File(context.applicationContext.noBackupFilesDir, "fork-recovery-v1")
    private val file = File(directory, "pending.json")
    private val atomic = AtomicFile(file)
    private var loaded = false
    private var expected: DiskState? = null
    private class Raw(val length: Long, val prefix: ByteArray) {
        fun same(other: Raw?) = other != null && length == other.length && prefix.contentEquals(other.prefix)
    }
    private class DiskState(val values: List<Raw?>) {
        fun same(other: DiskState) = values.zip(other.values).all { (a, b) ->
            if (a == null) b == null else a.same(b)
        }
        fun absent() = values.all { it == null }
    }
    private fun observe(): DiskState = DiskState(listOf(file, File(file.path + ".new"), File(file.path + ".bak")).map { raw(it) })
    private fun raw(source: File): Raw? {
        val input = try { FileInputStream(source) } catch (_: FileNotFoundException) {
            if (!source.exists()) return null
            throw ForkRecoveryFailure()
        }
        return input.use {
            val length = it.channel.size()
            val prefix = ByteArray(LIMIT + 1)
            var used = 0
            while (used < prefix.size) {
                val count = it.read(prefix, used, prefix.size - used)
                if (count < 0) break
                if (count == 0) throw ForkRecoveryFailure()
                used += count
            }
            Raw(length, prefix.copyOf(used))
        }
    }
    private fun canonicalBytes(): ByteArray? {
        val input = try { atomic.openRead() } catch (_: FileNotFoundException) {
            if (observe().absent()) return null
            throw ForkRecoveryFailure()
        }
        return input.use {
            val length = it.channel.size()
            if (length !in 1..LIMIT.toLong()) throw ForkRecoveryFailure()
            val bytes = ByteArray(length.toInt())
            var used = 0
            while (used < bytes.size) {
                val count = it.read(bytes, used, bytes.size - used)
                if (count <= 0) throw ForkRecoveryFailure()
                used += count
            }
            if (it.read() != -1) throw ForkRecoveryFailure()
            bytes
        }
    }
    override fun load(): BranchForkRecovery? = synchronized(gate) {
        loaded = false
        try {
            var readFailure: Exception? = null
            val bytes = try { canonicalBytes() } catch (failure: Exception) { readFailure = failure; null }
            // Also bind rejected/orphan AtomicFile artifacts so an explicit clear is possible.
            expected = observe()
            loaded = true
            if (readFailure != null) throw ForkRecoveryFailure()
            bytes?.let { ForkNativeWire.recovery(it) }
        } catch (_: Exception) { throw ForkRecoveryFailure() }
    }
    override fun save(value: BranchForkRecovery?) = synchronized(gate) {
        if (!loaded || expected?.same(observe()) != true) throw ForkRecoveryFailure()
        try {
            if (value == null) {
                atomic.delete()
                if (!observe().absent()) throw ForkRecoveryFailure()
                if (directory.exists()) syncDirectory(directory)
            } else {
                // Even this store's previous failed acknowledgment cannot silently change identity.
                val old = canonicalBytes()?.let { ForkNativeWire.recovery(it) }
                if (old != null && old != value) throw ForkRecoveryFailure()
                val bytes = ForkNativeWire.recovery(value)
                if (bytes.size > LIMIT) throw ForkRecoveryFailure()
                check(directory.isDirectory || directory.mkdirs())
                syncDirectory(checkNotNull(directory.parentFile))
                val stream = atomic.startWrite()
                try {
                    stream.write(bytes)
                    stream.flush()
                    stream.fd.sync() // Surface a sync failure before native admission.
                    atomic.finishWrite(stream)
                } catch (failure: Exception) {
                    atomic.failWrite(stream)
                    throw failure
                }
                syncDirectory(directory)
                if (canonicalBytes()?.contentEquals(bytes) != true) throw ForkRecoveryFailure()
            }
            expected = observe()
        } catch (_: Exception) {
            // A write may have completed before an I/O error: no rollback/absence promise.
            // Rebinding permits only explicit same-identity retry or consented clear.
            try { expected = observe() } catch (_: Exception) { loaded = false }
            throw ForkRecoveryFailure()
        }
    }
    private fun syncDirectory(source: File) {
        val descriptor = Os.open(source.absolutePath, OsConstants.O_RDONLY or OsConstants.O_DIRECTORY or OsConstants.O_CLOEXEC, 0)
        try { Os.fsync(descriptor) } finally { Os.close(descriptor) }
    }
    private companion object {
        const val LIMIT = 4096
        val gate = Any()
    }
}
