/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicLong

internal const val MAX_ARCHIVE_BYTES = 32 * 1024 * 1024

data class ArchivePreview(
    val version: Int,
    val storyId: String,
    val title: String,
    val rootBranch: String,
    val branchHeads: Map<String, Long>,
    val committedTurns: Int,
    val bytes: Long,
    val payloadSha256: String,
    val privacyWarning: String,
    val noncommittedWorkflowTransferred: Boolean,
    val retiredBranchIds: List<String> = emptyList(),
)
data class ArchivePrepared(val token: Long, val preview: ArchivePreview)
data class ArchiveImported(val story: String, val branch: String, val branches: Int, val committedTurns: Int)
enum class ArchiveKind { EXPORT, IMPORT }
data class ArchiveUiState(
    val visible: Boolean = false,
    val busy: Boolean = false,
    val awaitingPicker: Boolean = false,
    val selected: SavedStory? = null,
    val prepared: ArchivePrepared? = null,
    val kind: ArchiveKind? = null,
    val imported: ArchiveImported? = null,
    val notice: String? = null,
    val closing: Boolean = false,
)

/** Transient display identity; never a native token or canonical record. */
internal class ArchiveFrame(val state: ArchiveUiState)

internal interface ArchiveGateway {
    suspend fun prepareExport(story: SavedStory): ArchivePrepared
    suspend fun prepareImport(bytes: ByteArray): ArchivePrepared
    suspend fun exportBytes(token: Long): ByteArray
    suspend fun commitImport(token: Long): ArchiveImported
    fun cancel()
    fun close()
}
internal class ArchiveFailure(val category: String) : Exception("Archive operation failed")

/** One owner-thread operation and one outstanding picker. No story text or URI is logged. */
internal class ArchiveController(
    private val gateway: ArchiveGateway,
    private val scope: CoroutineScope,
    private val onClosed: (ArchiveImported?) -> Unit,
) {
    private val mutable = MutableStateFlow(ArchiveUiState())
    private val publishedFrames = MutableStateFlow(ArchiveFrame(mutable.value))
    val state = mutable.asStateFlow()
    val frames = publishedFrames.asStateFlow()
    private var generation = 0L
    private var picker: Picker? = null
    private var active: Job? = null
    private var disposed = false
    private var draining = false
    private var closeResult: ArchiveImported? = null
    private data class Picker(val ticket: Long, val kind: ArchiveKind, val generation: Long,
        val prepared: ArchivePrepared?, var valid: Boolean = true)
    private companion object { val pickerTickets = AtomicLong() }

    private fun publish(value: ArchiveUiState) {
        mutable.value = value
        // Value-equal reopen must still deliver the latest exact callback owner.
        publishedFrames.value = ArchiveFrame(mutable.value)
    }
    private fun renderedCurrent(rendered: ArchiveUiState) =
        !disposed && rendered.visible && mutable.value === rendered

    fun dismiss(rendered: ArchiveUiState) { if (renderedCurrent(rendered)) dismiss() }
    fun cancel(rendered: ArchiveUiState) { if (renderedCurrent(rendered)) cancel() }
    fun prepareExport(rendered: ArchiveUiState) { if (renderedCurrent(rendered)) prepareExport() }
    fun beginImportPicker(rendered: ArchiveUiState): Long? =
        if (renderedCurrent(rendered)) beginImportPicker() else null
    fun beginExportPicker(expected: ArchivePrepared, rendered: ArchiveUiState): Long? =
        if (renderedCurrent(rendered)) beginExportPicker(expected) else null
    fun confirmImport(expected: ArchivePrepared, rendered: ArchiveUiState) {
        if (renderedCurrent(rendered)) confirmImport(expected)
    }
    fun openImported(expected: ArchiveImported, rendered: ArchiveUiState) {
        if (renderedCurrent(rendered)) openImported(expected)
    }

    fun open(story: SavedStory) {
        if (disposed || mutable.value.visible || draining || picker != null || active != null) return
        generation++
        closeResult = null
        publish(ArchiveUiState(visible = true, selected = story))
    }
    private fun available() = !disposed && mutable.value.visible && !mutable.value.busy &&
        !mutable.value.closing && !draining && picker == null && mutable.value.imported == null

    fun prepareExport() {
        if (!available()) return
        val story = mutable.value.selected ?: return
        publish(mutable.value.copy(kind = ArchiveKind.EXPORT, prepared = null))
        work({ archiveNotice(it) }) { ticket ->
            val prepared = freeze(gateway.prepareExport(story))
            if (current(ticket)) publish(mutable.value.copy(prepared = prepared,
                notice = "Review this exact captured archive before choosing a new destination."))
        }
    }
    fun beginImportPicker(): Long? {
        if (!available()) return null
        val ticket = newPicker(ArchiveKind.IMPORT, null) ?: return null
        gateway.cancel()
        publish(mutable.value.copy(kind = ArchiveKind.IMPORT, prepared = null,
            awaitingPicker = true, notice = null))
        return ticket
    }
    fun beginExportPicker(expected: ArchivePrepared): Long? {
        if (!available() || mutable.value.kind != ArchiveKind.EXPORT) return null
        val prepared = mutable.value.prepared ?: return null
        if (prepared !== expected) return null
        val ticket = newPicker(ArchiveKind.EXPORT, prepared) ?: return null
        publish(mutable.value.copy(awaitingPicker = true, notice = null))
        return ticket
    }
    private fun newPicker(kind: ArchiveKind, prepared: ArchivePrepared?): Long? {
        val ticket: Long
        while (true) {
            val previous = pickerTickets.get()
            if (previous == Long.MAX_VALUE) return null
            if (pickerTickets.compareAndSet(previous, previous + 1)) { ticket = previous + 1; break }
        }
        picker = Picker(ticket, kind, generation, prepared)
        return ticket
    }
    private fun takePicker(ticket: Long, kind: ArchiveKind): Picker? {
        val pending = picker ?: return null
        if (pending.ticket != ticket || pending.kind != kind) return null
        picker = null
        if (!disposed) publish(mutable.value.copy(awaitingPicker = false))
        if (disposed || !pending.valid || pending.generation != generation || mutable.value.closing) {
            finishClosing()
            return null
        }
        return pending
    }
    fun completeImport(ticket: Long, reader: (suspend () -> ByteArray)?) {
        if (takePicker(ticket, ArchiveKind.IMPORT) == null) return
        if (reader == null) {
            publish(mutable.value.copy(notice = "Import cancelled. No archive was imported."))
            return
        }
        work({ archiveNotice(it) }) { serial ->
            val bytes = reader()
            try {
                if (!current(serial)) return@work
                if (bytes.size > MAX_ARCHIVE_BYTES) throw ArchiveFailure("TooLarge")
                val prepared = freeze(gateway.prepareImport(bytes))
                if (current(serial)) publish(mutable.value.copy(prepared = prepared,
                    notice = "Archive validated locally. Review it, then explicitly confirm import."))
            } finally { bytes.fill(0) }
        }
    }
    fun completeExport(ticket: Long, writer: (suspend (ByteArray) -> Unit)?) {
        val pending = takePicker(ticket, ArchiveKind.EXPORT) ?: return
        if (writer == null) {
            publish(mutable.value.copy(notice = "Export cancelled. No document was written by LocalLore."))
            return
        }
        val prepared = pending.prepared ?: return
        // The native token is single use. A failed/partial write requires a new captured preview.
        publish(mutable.value.copy(prepared = null))
        work({ "Export failed or stopped. The new destination may contain a partial plaintext archive. Capture a new preview to retry." }) { serial ->
            val bytes = gateway.exportBytes(prepared.token)
            try {
                if (!current(serial)) return@work
                if (bytes.size > MAX_ARCHIVE_BYTES || bytes.size.toLong() != prepared.preview.bytes)
                    throw ArchiveFailure("Integrity")
                writer(bytes)
                if (current(serial)) publish(mutable.value.copy(
                    notice = "The captured archive was written. Your document provider may sync this plaintext copy."))
            } finally { bytes.fill(0) }
        }
    }
    fun confirmImport(expected: ArchivePrepared) {
        if (!available() || mutable.value.kind != ArchiveKind.IMPORT) return
        val prepared = mutable.value.prepared ?: return
        if (prepared !== expected) return
        publish(mutable.value.copy(prepared = null))
        work({ importCommitNotice(it) }) { ticket ->
            val imported = gateway.commitImport(prepared.token)
            if (current(ticket)) publish(mutable.value.copy(imported = imported,
                notice = "Archive imported. Choose whether to open its root timeline or return to the library."))
        }
    }
    fun pickerFailed(ticket: Long) {
        val pending = picker ?: return
        if (pending.ticket != ticket) return
        picker = null
        if (disposed) return
        publish(mutable.value.copy(awaitingPicker = false))
        if (pending.valid && pending.generation == generation && !mutable.value.closing)
            publish(mutable.value.copy(notice = "Unable to open the document picker. No document was read or written."))
        finishClosing()
    }
    fun cancel() {
        if (disposed || !mutable.value.visible || mutable.value.closing || mutable.value.imported != null) return
        stop(false, null)
    }
    fun dismiss() {
        if (disposed || !mutable.value.visible || mutable.value.closing) return
        stop(true, null)
    }
    fun openImported(expected: ArchiveImported) {
        val imported = mutable.value.imported ?: return
        if (imported !== expected) return
        if (disposed || mutable.value.busy || mutable.value.closing || picker != null) return
        stop(true, imported)
    }
    private fun stop(close: Boolean, result: ArchiveImported?) {
        val serial = ++generation
        picker?.valid = false // Keep the ticket tombstone until its original callback arrives.
        gateway.cancel()
        val previous = active
        previous?.cancel()
        draining = true
        closeResult = result
        publish(mutable.value.copy(busy = previous != null, prepared = null,
            kind = null, closing = close,
            notice = if (close) "Finishing local work and waiting for any outstanding document picker…"
            else "Stopped. An export may be partial, and an import may already have completed. Close to refresh the library."))
        scope.launch {
            previous?.join()
            if (!disposed && generation == serial) {
                active = null
                draining = false
                publish(mutable.value.copy(busy = false))
                finishClosing()
            }
        }
    }
    private fun finishClosing() {
        if (disposed || !mutable.value.closing || draining || active != null || picker != null) return
        val result = closeResult
        closeResult = null
        publish(ArchiveUiState())
        onClosed(result)
    }
    fun dispose() {
        if (disposed) return
        disposed = true
        generation++
        picker?.valid = false
        gateway.cancel()
        active?.cancel()
        gateway.close()
        publish(ArchiveUiState())
    }
    private fun current(ticket: Long) = !disposed && generation == ticket && mutable.value.visible && !mutable.value.closing
    private fun work(failureNotice: (Exception) -> String, block: suspend (Long) -> Unit) {
        val ticket = ++generation
        publish(mutable.value.copy(busy = true, notice = null))
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try { block(ticket) }
            catch (failure: CancellationException) {
                if (current(ticket)) publish(mutable.value.copy(notice = failureNotice(failure)))
                throw failure
            } catch (failure: Exception) {
                if (current(ticket)) publish(mutable.value.copy(notice = failureNotice(failure)))
            } finally {
                if (active === currentCoroutineContext()[Job]) active = null
                if (current(ticket)) publish(mutable.value.copy(busy = false))
            }
        }
        active = job
        job.start()
    }
    private fun freeze(prepared: ArchivePrepared) = prepared.copy(preview = prepared.preview.copy(
        branchHeads = java.util.Collections.unmodifiableMap(LinkedHashMap(prepared.preview.branchHeads)),
        retiredBranchIds = java.util.Collections.unmodifiableList(ArrayList(prepared.preview.retiredBranchIds))))
}

private fun archiveNotice(failure: Exception): String = when ((failure as? ArchiveFailure)?.category) {
    "Conflict" -> "A story with this ID already exists. It cannot be overwritten or remapped."
    "Unsupported" -> "This archive version or feature is unsupported. Nothing was imported."
    "TooLarge" -> "The archive exceeds supported size or history limits. The file limit is 32 MiB. Nothing was imported."
    "Malformed", "Integrity" -> "The archive is invalid or failed its integrity checks. Nothing was imported."
    "Stale" -> "The selected story changed. Close this view and refresh the library."
    "Busy" -> "Local storage is busy. Try again after the current work finishes."
    "Full" -> "Local storage is full. Close to refresh the library. Free storage and validate the archive again before retrying."
    "Cancelled" -> "Archive work stopped. No import was confirmed. Close to refresh the library."
    else -> "Archive work failed. Close to refresh the library before retrying."
}
private fun importCommitNotice(failure: Exception): String = when ((failure as? ArchiveFailure)?.category) {
    "Conflict" -> "A story with this ID already exists. Nothing was overwritten."
    "Unsupported", "Malformed", "Integrity", "TooLarge", "Full" -> archiveNotice(failure)
    else -> "The import outcome is uncertain. It may already have completed. Close to refresh the library; do not assume cancellation rolled it back."
}
