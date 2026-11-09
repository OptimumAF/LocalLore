/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.CancellationSignal
import android.os.ParcelFileDescriptor
import android.system.Os
import android.system.OsConstants
import androidx.activity.result.contract.ActivityResultContracts
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.InputStream
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

private val importSlot = Semaphore(1)
private val importCancellationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

/** One copy of openable archive content; no request for durable document access or source editing. */
internal class ArchiveImportContract : ActivityResultContracts.GetContent() {
    override fun createIntent(context: Context, input: String): Intent {
        require(input == "*/*")
        return super.createIntent(context, input).putExtra(Intent.EXTRA_MIME_TYPES,
            arrayOf("application/json", "application/octet-stream", "text/plain"))
    }
}

/** SAF content only. No filename authority, broad storage access, or persisted URI permission. */
internal suspend fun readArchiveDocument(resolver: ContentResolver, uri: Uri): ByteArray {
    if (uri.scheme != "content") throw ArchiveFailure("Io")
    val signal = CancellationSignal()
    return readArchiveFromProvider(open = {
        val asset = resolver.openAssetFileDescriptor(uri, "r", signal)
        asset?.let {
            try {
                // The stream owns the descriptor and honors the asset's offset and length.
                it.createInputStream()
            } catch (error: Throwable) {
                runCatching { it.close() }
                throw error
            }
        }
    }, cancelOpen = signal::cancel)
}

/** Retain the slot until blocking provider work, stream ownership and cancellation have drained. */
internal suspend fun readArchiveFromProvider(open: () -> InputStream?, cancelOpen: () -> Unit): ByteArray {
    var bytes: ByteArray? = null
    try {
        withContext(Dispatchers.IO) {
            importSlot.withPermit {
                val cancellation = importCancellationScope.launch(start = CoroutineStart.LAZY) {
                    try { cancelOpen() } catch (_: Exception) { /* Keep provider details private. */ }
                }
                try {
                    suspendCancellableCoroutine<Unit> { completion ->
                        completion.invokeOnCancellation { cancellation.start() }
                        try {
                            if (!completion.isActive) return@suspendCancellableCoroutine
                            val input = open() ?: throw ArchiveFailure("Io")
                            bytes = readBoundedArchive(input) { completion.context.ensureActive() }
                            completion.resume(Unit)
                        } catch (error: Exception) {
                            if (completion.isActive) completion.resumeWithException(error)
                        }
                    }
                } finally {
                    withContext(NonCancellable) { cancellation.cancelAndJoin() }
                }
            }
        }
        return checkNotNull(bytes)
    } catch (cancelled: CancellationException) {
        bytes?.fill(0)
        throw cancelled
    }
    catch (failure: ArchiveFailure) { throw failure }
    catch (_: Exception) { throw ArchiveFailure("Io") }
}

/** rw never requests truncation. Verify the same opened descriptor before the first write. */
internal suspend fun writeArchiveDocument(resolver: ContentResolver, uri: Uri, bytes: ByteArray): Unit = withContext(Dispatchers.IO) {
    if (uri.scheme != "content" || bytes.size !in 1..MAX_ARCHIVE_BYTES) throw ArchiveFailure("Io")
    val context = currentCoroutineContext()
    try {
        val descriptor = resolver.openFileDescriptor(uri, "rw") ?: throw ArchiveFailure("Io")
        try {
            if (descriptor.statSize != 0L || !OsConstants.S_ISREG(Os.fstat(descriptor.fileDescriptor).st_mode) ||
                Os.lseek(descriptor.fileDescriptor, 0, OsConstants.SEEK_CUR) != 0L) throw ArchiveFailure("Io")
            val output = ParcelFileDescriptor.AutoCloseOutputStream(descriptor)
            writeEmptyArchive(object : ArchiveDocumentSink {
                override fun size() = output.channel.size()
                override fun position() = output.channel.position()
                override fun write(bytes: ByteArray, offset: Int, count: Int) = output.write(bytes, offset, count)
                override fun flush() = output.flush()
                override fun close() = output.close()
            }, bytes) { context.ensureActive() }
        } finally { descriptor.close() }
    } catch (cancelled: CancellationException) { throw cancelled }
    catch (failure: ArchiveFailure) { throw failure }
    catch (_: Exception) { throw ArchiveFailure("Io") }
}

/** Portable stream mechanics, separately tested without pretending Android stubs are providers. */
internal fun readBoundedArchive(input: InputStream, cap: Int = MAX_ARCHIVE_BYTES, check: () -> Unit = {}): ByteArray {
    try {
        require(cap in 1..MAX_ARCHIVE_BYTES)
        return input.use { source ->
            val output = ByteArrayOutputStream(minOf(cap, 65536))
            val buffer = ByteArray(8192)
            while (output.size() < cap) {
                check()
                val count = source.read(buffer, 0, minOf(buffer.size, cap - output.size()))
                if (count < 0) return@use output.toByteArray()
                if (count == 0) {
                    val one = source.read()
                    if (one < 0) return@use output.toByteArray()
                    output.write(one)
                } else output.write(buffer, 0, count)
            }
            check()
            if (source.read() != -1) throw ArchiveFailure("TooLarge")
            check()
            output.toByteArray()
        }
    } catch (cancelled: CancellationException) { throw cancelled }
    catch (failure: ArchiveFailure) { throw failure }
    catch (_: Exception) { throw ArchiveFailure("Io") }
}

internal interface ArchiveDocumentSink : AutoCloseable {
    fun size(): Long
    fun position(): Long
    fun write(bytes: ByteArray, offset: Int, count: Int)
    fun flush()
}

internal fun writeEmptyArchive(sink: ArchiveDocumentSink, bytes: ByteArray, check: () -> Unit = {}) {
    try {
        sink.use { output ->
            if (bytes.size !in 1..MAX_ARCHIVE_BYTES) throw ArchiveFailure("TooLarge")
            check()
            if (output.size() != 0L || output.position() != 0L) throw ArchiveFailure("Io")
            var offset = 0
            while (offset < bytes.size) {
                check()
                val count = minOf(16384, bytes.size - offset)
                output.write(bytes, offset, count)
                offset += count
            }
            check()
            output.flush()
        }
    } catch (cancelled: CancellationException) { throw cancelled }
    catch (failure: ArchiveFailure) { throw failure }
    catch (_: Exception) { throw ArchiveFailure("Io") }
}
