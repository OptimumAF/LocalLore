/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.ContentResolver
import android.net.Uri
import android.os.CancellationSignal
import android.os.ParcelFileDescriptor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

// A noncooperative provider can delay its own export. It cannot accumulate opens
// or cancellation listeners, and its listener never runs on the UI thread.
private val exportSlot = Semaphore(1)
private val cancellationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

/** Writes only the frozen preview. No storage permission, temporary file or persistent URI grant. */
internal suspend fun writeDiagnosticDocument(resolver: ContentResolver, destination: Uri, bytes: ByteArray) {
    require(destination.scheme == "content")
    require(bytes.size <= 16_384)
    withContext(Dispatchers.IO) {
        exportSlot.withPermit {
            val signal = CancellationSignal()
            val cancellation = cancellationScope.launch(start = CoroutineStart.LAZY) {
                try { signal.cancel() } catch (_: Exception) { /* No provider exception text enters logs. */ }
            }
            try {
                suspendCancellableCoroutine<Unit> { completion ->
                    completion.invokeOnCancellation { cancellation.start() }
                    try {
                        if (!completion.isActive) return@suspendCancellableCoroutine
                        val descriptor = resolver.openFileDescriptor(destination, "wt", signal)
                            ?: throw java.io.IOException("Document provider unavailable")
                        // Resources never cross a dispatcher boundary as a returned value.
                        descriptor.use {
                            ParcelFileDescriptor.AutoCloseOutputStream(it).use { output ->
                                if (completion.isActive) {
                                    output.write(bytes)
                                    output.flush()
                                }
                            }
                        }
                        if (completion.isActive) completion.resume(Unit)
                    } catch (error: Exception) {
                        if (completion.isActive) completion.resumeWithException(error)
                    }
                }
            } finally {
                withContext(NonCancellable) {
                    if (cancellation.isActive) cancellation.join() else cancellation.cancel()
                }
            }
        }
    }
}
