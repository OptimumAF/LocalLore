/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DiagnosticsUiState(
    val visible: Boolean = false,
    val preview: String = "",
    val exporting: Boolean = false,
    val notice: String? = null,
)

/** Owner-thread consent state. Exported records contain no URI, filename, story or exception. */
internal class DiagnosticsController(private val log: DiagnosticLog, private val scope: CoroutineScope) {
    private val mutable = MutableStateFlow(DiagnosticsUiState())
    val state = mutable.asStateFlow()
    private var preview: DiagnosticSnapshot? = null
    private var pending: DiagnosticSnapshot? = null
    private var ticket = 0L
    private var job: Job? = null
    private var disposed = false
    // Revoking a preview must not let an old picker result bind to a newer export.
    private var pickerOutstanding = false

    fun open() {
        if (disposed || mutable.value.exporting) return
        preview = log.snapshot()
        mutable.value = DiagnosticsUiState(visible = true, preview = preview!!.json)
    }

    fun clear() {
        if (disposed || !mutable.value.visible || mutable.value.exporting) return
        log.clear()
        preview = log.snapshot()
        mutable.value = mutable.value.copy(preview = preview!!.json, notice = "Diagnostics cleared from memory.")
    }

    fun dismiss() {
        invalidate()
        preview = null
        mutable.value = DiagnosticsUiState()
    }

    fun beginExport(): Boolean {
        if (disposed || pickerOutstanding || !mutable.value.visible || mutable.value.exporting || preview == null) return false
        ticket++
        pending = preview
        pickerOutstanding = true
        mutable.value = mutable.value.copy(exporting = true, notice = null)
        return true
    }

    fun pickerFailed() {
        pickerOutstanding = false
        if (pending == null) return
        pending = null
        log.record(DiagnosticPhase.EXPORT, DiagnosticOutcome.FAILED, 0, DiagnosticError.TRANSPORT)
        mutable.value = mutable.value.copy(exporting = false, notice = "Unable to open a document picker. Nothing was exported.")
    }

    fun completeExport(writer: (suspend (ByteArray) -> Unit)?) {
        if (!pickerOutstanding) return
        pickerOutstanding = false
        val snapshot = pending ?: return // Duplicate, late or post-process-death callback has no consent.
        pending = null
        if (disposed || !mutable.value.visible) return
        if (writer == null) {
            log.record(DiagnosticPhase.EXPORT, DiagnosticOutcome.CANCELLED, 0)
            mutable.value = mutable.value.copy(exporting = false, notice = "Export cancelled. Nothing was written by LocalLore.")
            return
        }
        val current = ticket
        job = scope.launch {
            val start = System.nanoTime()
            try {
                writer(snapshot.json.toByteArray(Charsets.UTF_8))
                if (current == ticket && !disposed) {
                    log.record(DiagnosticPhase.EXPORT, DiagnosticOutcome.COMPLETED, elapsedMillis(start))
                    mutable.value = mutable.value.copy(exporting = false, notice = "Reviewed diagnostics exported.")
                }
            } catch (cancelled: CancellationException) {
                if (current == ticket && !disposed) {
                    log.record(DiagnosticPhase.EXPORT, DiagnosticOutcome.CANCELLED, elapsedMillis(start))
                    mutable.value = mutable.value.copy(exporting = false,
                        notice = "Export cancelled. The destination may contain an incomplete file.")
                }
                throw cancelled
            } catch (_: Exception) {
                if (current == ticket && !disposed) {
                    log.record(DiagnosticPhase.EXPORT, DiagnosticOutcome.FAILED, elapsedMillis(start), DiagnosticError.TRANSPORT)
                    mutable.value = mutable.value.copy(exporting = false,
                        notice = "Export failed. The destination may contain an incomplete file.")
                }
            }
        }
    }

    fun dispose() {
        disposed = true
        dismiss()
        log.clear()
    }

    private fun invalidate() {
        ticket++
        if (pending != null || job?.isActive == true) {
            log.record(DiagnosticPhase.EXPORT, DiagnosticOutcome.CANCELLED, 0)
        }
        pending = null
        job?.cancel()
        job = null
    }
}

internal fun elapsedMillis(start: Long): Long = ((System.nanoTime() - start).coerceAtLeast(0) / 1_000_000)
    .coerceAtMost(60_000)
