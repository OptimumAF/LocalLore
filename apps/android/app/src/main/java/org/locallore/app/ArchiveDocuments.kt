/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.ParcelFileDescriptor
import android.system.Os
import android.system.OsConstants
import androidx.activity.result.contract.ActivityResultContracts
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.InputStream

/** One copy of openable archive content; no request for durable document access or source editing. */
internal class ArchiveImportContract : ActivityResultContracts.GetContent() {
    override fun createIntent(context: Context, input: String): Intent {
        require(input == "*/*")
        return super.createIntent(context, input).putExtra(Intent.EXTRA_MIME_TYPES,
            arrayOf("application/json", "application/octet-stream", "text/plain"))
    }
}

/** SAF content only. No filename authority, broad storage access, or persisted URI permission. */
internal suspend fun readArchiveDocument(resolver: ContentResolver, uri: Uri): ByteArray = withContext(Dispatchers.IO) {
    if (uri.scheme != "content") throw ArchiveFailure("Io")
    val context = currentCoroutineContext()
    try {
        val input = resolver.openInputStream(uri) ?: throw ArchiveFailure("Io")
        readBoundedArchive(input) { context.ensureActive() }
    } catch (cancelled: CancellationException) { throw cancelled }
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
