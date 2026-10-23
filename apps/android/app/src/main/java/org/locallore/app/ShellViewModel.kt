/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ShellViewModel(
    private val gateway: DemoGateway,
    private val diagnosticLog: DiagnosticLog = DiagnosticLog(),
) : ViewModel() {
    private val mutable = MutableStateFlow(ShellState())
    val state: StateFlow<ShellState> = mutable.asStateFlow()
    private var generation = 0L
    private var messageId = 0L
    private var pending: Job? = null
    private val diagnosticController = DiagnosticsController(diagnosticLog, viewModelScope)
    val diagnostics = diagnosticController.state
    private val recordController = StoryRecordController(StoryRecordReader(gateway::readStoryRecord), viewModelScope)
    val storyRecord = recordController.state
    val hasStoryRecords: Boolean get() = gateway.storyRecords
    private var disposed = false

    init {
        if (gateway.durable) {
            mutable.value = ShellState(busy = true, persistent = true, notice = "Opening local saved stories…")
            savedOperation("Saved story resumed. Uncommitted responses remain outside accepted history.") { gateway.initialize() }
        }
    }

    private fun publishSaved(saved: SavedSnapshot, notice: String): ShellState = mutable.value.copy(
        busy = false, preparingResponse = false, revision = saved.revision, potionOwner = saved.potionOwner,
        messages = saved.messages, persistent = true, storageLocation = saved.location,
        schemaVersion = saved.schemaVersion, stories = saved.stories, selectedStory = saved.selected,
        uncommittedDrafts = saved.uncommittedDrafts,
        rulesProfile = saved.rulesProfile,
        textProvider = saved.textProvider,
        recoveryRequired = false, notice = notice,
    )

    private fun savedOperation(notice: String, operation: suspend () -> SavedSnapshot?) {
        recordController.dismiss()
        val ticket = ++generation
        mutable.value = mutable.value.copy(busy = true, preparingResponse = false, notice = null)
        pending = viewModelScope.launch {
            try {
                val saved = operation()
                if (!disposed && ticket == generation && saved != null) mutable.value = publishSaved(saved, notice)
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (failure: Exception) {
                if (!disposed && ticket == generation) mutable.value = mutable.value.copy(
                    recoveryRequired = true, notice = recoveryNotice(failure,
                        "Saved progress could not be confirmed. Retry recovery; existing saves are retained."),
                )
            } finally {
                if (!disposed && ticket == generation) mutable.value = mutable.value.copy(busy = false)
            }
        }
    }

    fun recover() {
        if (!disposed && !mutable.value.busy && gateway.durable) savedOperation("Saved progress recovered.") {
            if (mutable.value.storageLocation == null) gateway.initialize() else gateway.recoverSaved()
        }
    }
    fun resume(story: SavedStory) {
        if (!disposed && !mutable.value.busy && gateway.durable) savedOperation("Saved story resumed.") { gateway.resumeSaved(story) }
    }

    fun openDiagnostics() { if (!disposed && !mutable.value.busy) { recordController.dismiss(); diagnosticController.open() } }
    fun openStoryRecord() {
        val current = mutable.value
        val story = current.selectedStory ?: return
        if (!disposed && gateway.storyRecords && current.persistent && !current.busy && !current.recoveryRequired) {
            diagnosticController.dismiss()
            recordController.open(StoryRecordContext(story, current.revision))
        }
    }
    fun closeStoryRecord() = recordController.dismiss()
    fun recordSection(section: StoryRecordSection) = recordController.select(section)
    fun recordSearch(text: String) = recordController.search(text)
    fun nextRecordPage() = recordController.next()
    fun firstRecordPage() = recordController.first()
    fun retryStoryRecord() = recordController.retry()
    fun openRecordEvent(sequence: Long) = recordController.openEvent(sequence)
    fun openRecordEvent(sequence: Long, expectedContext: StoryRecordContext?) {
        if (expectedContext != null && expectedContext == storyRecord.value.context)
            recordController.openEvent(sequence)
    }
    fun backToStoryRecord() = recordController.back()
    fun retryRecordEvent() = recordController.retryEvent()
    fun closeDiagnostics() = diagnosticController.dismiss()
    fun clearDiagnostics() = diagnosticController.clear()
    fun beginDiagnosticExport() = diagnosticController.beginExport()
    fun diagnosticPickerFailed() = diagnosticController.pickerFailed()
    fun completeDiagnosticExport(writer: (suspend (ByteArray) -> Unit)?) = diagnosticController.completeExport(writer)

    fun setMode(mode: DemoMode) {
        if (!mutable.value.busy && !mutable.value.recoveryRequired) mutable.value = mutable.value.copy(mode = mode, notice = null)
    }

    fun submit(action: DemoAction) = submitResponse(action.description()) { before ->
        gateway.respond(action, before.revision, before.mode)
    }

    fun submitText(input: PlayInput) {
        if (disposed || mutable.value.busy || mutable.value.recoveryRequired) return
        if (mutable.value.textProvider == TextProvider.UNAVAILABLE || !validPlayInput(input)) {
            mutable.value = mutable.value.copy(notice = "Text input is unavailable or invalid. Nothing changed.")
            return
        }
        submitResponse(input.text) { before -> gateway.respondText(input, before.revision) }
    }

    private fun submitResponse(playerText: String, prepare: suspend (ShellState) -> DemoResult) {
        if (disposed || mutable.value.busy || mutable.value.recoveryRequired) return
        recordController.dismiss()
        val before = mutable.value
        val ticket = ++generation
        mutable.value = before.copy(busy = true, preparingResponse = true, notice = null)
        pending = viewModelScope.launch {
            var committing = false
            var start = System.nanoTime()
            try {
                val prepared = prepare(before)
                // A cancelled/reset/obsolete session never attaches a late completion.
                if (ticket != generation || mutable.value.revision != before.revision) {
                    if (!disposed) diagnosticLog.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.STALE, elapsedMillis(start))
                    return@launch
                }
                diagnosticLog.record(DiagnosticPhase.PREPARE,
                    if (prepared is DemoResult.Rejected) DiagnosticOutcome.REJECTED else DiagnosticOutcome.PREPARED,
                    elapsedMillis(start), if (prepared is DemoResult.Rejected) DiagnosticError.fromNative(prepared.category) else DiagnosticError.NONE)
                start = System.nanoTime()
                committing = prepared !is DemoResult.Rejected
                val result = if (committing) gateway.commitAsync(prepared) else prepared
                if (disposed || ticket != generation) return@launch
                val saved = if (gateway.durable) gateway.snapshot() else null
                if (disposed || ticket != generation) return@launch
                mutable.value = when (result) {
                    is DemoResult.Accepted -> if (saved != null) publishSaved(saved, "Outcome accepted and saved by the local engine.") else before.copy(
                        revision = result.revision,
                        potionOwner = result.potionOwner,
                        messages = (before.messages + listOf(
                            SceneMessage(++messageId, playerText, true),
                            SceneMessage(++messageId, result.narration, false),
                        )).takeLast(40),
                        notice = "Outcome accepted by the local engine.",
                    )
                    is DemoResult.Rejected -> if (saved != null) publishSaved(saved, rejectionNotice(result.category))
                        else before.copy(notice = rejectionNotice(result.category))
                    is DemoResult.Prepared -> error("Commit returned an unfinished operation")
                }
                if (committing) diagnosticLog.record(DiagnosticPhase.COMMIT,
                    if (result is DemoResult.Accepted) DiagnosticOutcome.ACCEPTED else DiagnosticOutcome.REJECTED,
                    elapsedMillis(start), if (result is DemoResult.Rejected) DiagnosticError.fromNative(result.category) else DiagnosticError.NONE)
            } catch (cancelled: CancellationException) {
                if (!disposed) diagnosticLog.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.CANCELLED, elapsedMillis(start))
                throw cancelled
            } catch (failure: Exception) {
                if (!disposed) diagnosticLog.record(if (committing) DiagnosticPhase.COMMIT else DiagnosticPhase.PREPARE,
                    if (committing) DiagnosticOutcome.UNKNOWN else DiagnosticOutcome.FAILED,
                    elapsedMillis(start), if (failure is WorkspaceFailure) DiagnosticError.fromNative(failure.category)
                        else DiagnosticError.TRANSPORT)
                if (ticket == generation) mutable.value = if (committing || gateway.durable) before.copy(
                    recoveryRequired = true,
                    notice = if (gateway.durable) recoveryNotice(failure,
                        "Unable to confirm the outcome. Retry recovery using the original response key; saves are retained.")
                        else "Unable to confirm the outcome. Reset this in-memory demo to continue.",
                ) else before.copy(notice = "Response failed. Nothing changed; try again.")
            } finally {
                if (ticket == generation) mutable.value = mutable.value.copy(busy = false, preparingResponse = false)
            }
        }
    }

    fun cancel() {
        recordController.dismiss()
        if (!mutable.value.busy) return
        // Opening storage has no cancellable turn. Closing the ViewModel still releases its handle.
        if (gateway.durable && !mutable.value.preparingResponse) return
        val start = System.nanoTime()
        generation++
        gateway.cancel()
        pending?.cancel()
        pending = null
        if (gateway.durable) {
            savedOperation("Response stopped. Showing the accepted saved history.") { gateway.cancelSaved() }
            diagnosticLog.record(DiagnosticPhase.CANCEL, DiagnosticOutcome.COMPLETED, elapsedMillis(start))
            return
        }
        mutable.value = mutable.value.copy(busy = false, preparingResponse = false, notice = "Response cancelled. Nothing changed.")
        diagnosticLog.record(DiagnosticPhase.CANCEL, DiagnosticOutcome.COMPLETED, elapsedMillis(start))
    }

    fun reset() {
        // A retained UI callback must not reopen a native session after onCleared.
        if (disposed) return
        if (gateway.durable && mutable.value.busy) return
        val start = System.nanoTime()
        diagnosticController.dismiss()
        recordController.dismiss()
        generation++
        gateway.cancel()
        pending?.cancel()
        pending = null
        if (gateway.durable) savedOperation("New saved story created. Previous stories remain in the library.") { gateway.createSaved() }
        else { gateway.reset(); mutable.value = ShellState() }
        diagnosticLog.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, elapsedMillis(start))
    }

    override fun onCleared() {
        disposed = true
        diagnosticController.dispose()
        recordController.dispose()
        generation++
        gateway.close()
        pending?.cancel()
        pending = null
        mutable.value = mutable.value.copy(busy = false, preparingResponse = false)
        super.onCleared()
    }
}

private fun recoveryNotice(failure: Exception, fallback: String): String = when ((failure as? WorkspaceFailure)?.category) {
    "Full" -> "Local storage is full. Free space, then retry recovery. Saved progress is retained."
    "Busy" -> "The local engine is busy. Wait briefly, then retry recovery. Saved progress is retained."
    else -> fallback
}

private fun DemoAction.description(): String = when (this) {
    DemoAction.GIVE_POTION -> "Give my potion to Mira."
    DemoAction.TRY_ABILITY -> "Try the unlearned blink ability."
}

private fun rejectionNotice(category: String): String = when (category) {
    "Inventory" -> "You no longer hold the potion. Nothing changed."
    "Ability" -> "Blink is not learned. Nothing changed."
    "Agency" -> "The proposal did not match your action. Nothing changed."
    "Malformed" -> "The response was malformed. Nothing changed; try again."
    "Provider" -> "The response failed. Nothing changed; try again."
    else -> "This response was rejected. Nothing changed; try again."
}
