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

class ShellViewModel internal constructor(
    private val gateway: DemoGateway,
    private val diagnosticLog: DiagnosticLog = DiagnosticLog(),
    archiveGateway: ArchiveGateway? = null,
    deletionGateway: StoryDeletionGateway? = null,
    branchDeletionGateway: BranchDeletionGateway? = null,
) : ViewModel() {
    private val mutable = MutableStateFlow(ShellState())
    val state: StateFlow<ShellState> = mutable.asStateFlow()
    private var generation = 0L
    private var messageId = 0L
    private var pending: Job? = null
    private val diagnosticController = DiagnosticsController(diagnosticLog, viewModelScope)
    val diagnostics = diagnosticController.state
    private var disposed = false
    internal val archiveController = archiveGateway?.let { ArchiveController(it, viewModelScope, ::archiveClosed) }
    val archive = archiveController?.state ?: MutableStateFlow(ArchiveUiState()).asStateFlow()
    private var archiveImportPicker: Long? = null
    private var archiveExportPicker: Long? = null
    internal val deletionController = deletionGateway?.let { StoryDeletionController(viewModelScope, it, ::deletionClosed) }
    internal val deletion = deletionController?.state ?: MutableStateFlow(StoryDeletionUiState()).asStateFlow()
    internal val branchDeletionController = branchDeletionGateway?.let {
        BranchDeletionController(viewModelScope, it, ::branchDeletionClosed)
    }
    internal val branchDeletion = branchDeletionController?.state ?: MutableStateFlow(BranchDeletionUiState()).asStateFlow()

    fun openBranchDeletion() {
        val controller = branchDeletionController ?: return
        val before = mutable.value
        if (disposed || before.busy || before.archiveActive || before.deletionActive || before.recoveryRequired || !before.persistent) return
        val selected = before.selectedStory ?: return
        val root = before.stories.firstOrNull { it.story == selected.story } ?: return
        if (selected.branch == root.branch) return
        diagnosticController.dismiss()
        mutable.value = before.copy(deletionActive = true)
        controller.open(selected.copy(title = root.title, revision = before.revision), root.branch)
    }
    private fun branchDeletionClosed(deleted: BranchDeleted?, uncertain: Boolean) {
        if (disposed) return
        mutable.value = mutable.value.copy(deletionActive = false)
        val notice = when {
            uncertain -> "Deletion could not be confirmed and may already have completed. Saved timelines refreshed from local storage."
            deleted != null -> "Timeline removed. Showing the retained saved history."
            else -> "Saved timelines refreshed from local storage."
        }
        savedOperation(notice) { gateway.reconcileSaved() }
    }

    fun openDeletion() {
        val controller = deletionController ?: return
        val before = mutable.value
        if (disposed || before.busy || before.archiveActive || before.deletionActive || before.recoveryRequired || !before.persistent) return
        val selected = before.selectedStory ?: return
        val root = before.stories.firstOrNull { it.story == selected.story } ?: return
        diagnosticController.dismiss()
        mutable.value = before.copy(deletionActive = true)
        controller.open(root)
    }
    private fun deletionClosed(deleted: StoryDeleted?) {
        if (disposed) return
        mutable.value = mutable.value.copy(deletionActive = false)
        savedOperation(if (deleted == null) "Saved-story library refreshed." else "Story and all its timelines deleted.") {
            gateway.reconcileSaved()
        }
    }

    fun openArchive() {
        val controller = archiveController ?: return
        val before = mutable.value
        if (disposed || before.archiveActive || before.deletionActive || before.busy || before.recoveryRequired || !before.persistent) return
        val story = before.selectedStory ?: return
        diagnosticController.dismiss()
        mutable.value = before.copy(archiveActive = true)
        controller.open(story)
    }
    private fun archiveClosed(imported: ArchiveImported?) {
        if (disposed) return
        mutable.value = mutable.value.copy(archiveActive = false)
        savedOperation(if (imported == null) "Saved-story library refreshed." else "Imported story opened from accepted history.") {
            val saved = gateway.snapshot() ?: return@savedOperation null
            if (imported == null) saved else {
                val selected = saved.stories.firstOrNull { it.story == imported.story && it.branch == imported.branch }
                    ?: error("Imported story unavailable")
                gateway.resumeSaved(selected)
            }
        }
    }
    internal fun beginArchiveImportPicker(): Boolean {
        val ticket = archiveController?.beginImportPicker() ?: return false
        archiveImportPicker = ticket
        return true
    }
    internal fun completeArchiveImport(reader: (suspend () -> ByteArray)?) {
        val ticket = archiveImportPicker ?: return
        archiveImportPicker = null
        archiveController?.completeImport(ticket, reader)
    }
    internal fun archiveImportPickerFailed() {
        val ticket = archiveImportPicker ?: return
        archiveImportPicker = null
        archiveController?.pickerFailed(ticket)
    }
    internal fun beginArchiveExportPicker(): Boolean {
        val ticket = archiveController?.beginExportPicker() ?: return false
        archiveExportPicker = ticket
        return true
    }
    internal fun completeArchiveExport(writer: (suspend (ByteArray) -> Unit)?) {
        val ticket = archiveExportPicker ?: return
        archiveExportPicker = null
        archiveController?.completeExport(ticket, writer)
    }
    internal fun archiveExportPickerFailed() {
        val ticket = archiveExportPicker ?: return
        archiveExportPicker = null
        archiveController?.pickerFailed(ticket)
    }

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
        databaseSchemaVersion = saved.databaseSchemaVersion,
        timelines = saved.timelines,
        recoveryRequired = false, notice = notice,
    )

    private fun savedOperation(notice: String, operation: suspend () -> SavedSnapshot?) {
        val ticket = ++generation
        mutable.value = mutable.value.copy(busy = true, preparingResponse = false, notice = null)
        pending = viewModelScope.launch {
            try {
                val saved = operation()
                if (!disposed && ticket == generation && saved != null) mutable.value = publishSaved(saved, notice)
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) {
                if (!disposed && ticket == generation) mutable.value = mutable.value.copy(
                    recoveryRequired = true, notice = "Saved progress could not be confirmed. Retry recovery; existing saves are retained.",
                )
            } finally {
                if (!disposed && ticket == generation) mutable.value = mutable.value.copy(busy = false)
            }
        }
    }

    fun recover() {
        if (!disposed && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive && gateway.durable) savedOperation("Saved progress recovered.") {
            if (mutable.value.storageLocation == null) gateway.initialize() else gateway.recoverSaved()
        }
    }
    fun resume(story: SavedStory) {
        if (!disposed && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive && gateway.durable) savedOperation("Saved story resumed.") { gateway.resumeSaved(story) }
    }
    fun resumeTimeline(timeline: SavedTimeline) {
        val before = mutable.value
        if (disposed || before.busy || before.archiveActive || before.deletionActive || before.recoveryRequired ||
            !before.persistent || !gateway.durable || before.selectedStory?.story != timeline.story ||
            before.timelines.none { it === timeline }) return
        val root = before.stories.firstOrNull { it.story == timeline.story } ?: return
        diagnosticController.dismiss()
        savedOperation("Saved timeline resumed.") {
            gateway.resumeSaved(SavedStory(timeline.story, timeline.branch, root.title, timeline.revision))
        }
    }

    fun openDiagnostics() { if (!disposed && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive) diagnosticController.open() }
    fun closeDiagnostics() = diagnosticController.dismiss()
    fun clearDiagnostics() = diagnosticController.clear()
    fun beginDiagnosticExport() = diagnosticController.beginExport()
    fun diagnosticPickerFailed() = diagnosticController.pickerFailed()
    fun completeDiagnosticExport(writer: (suspend (ByteArray) -> Unit)?) = diagnosticController.completeExport(writer)

    fun setMode(mode: DemoMode) {
        if (!disposed && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive && !mutable.value.recoveryRequired) mutable.value = mutable.value.copy(mode = mode, notice = null)
    }

    fun submit(action: DemoAction) {
        if (disposed || mutable.value.busy || mutable.value.archiveActive || mutable.value.deletionActive || mutable.value.recoveryRequired ||
            (gateway.durable && mutable.value.selectedStory == null)) return
        val before = mutable.value
        val ticket = ++generation
        mutable.value = before.copy(busy = true, preparingResponse = true, notice = null)
        pending = viewModelScope.launch {
            var committing = false
            var start = System.nanoTime()
            try {
                val prepared = gateway.respond(action, before.revision, before.mode)
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
                            SceneMessage(++messageId, action.description(), true),
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
            } catch (_: Exception) {
                if (!disposed) diagnosticLog.record(if (committing) DiagnosticPhase.COMMIT else DiagnosticPhase.PREPARE,
                    if (committing) DiagnosticOutcome.UNKNOWN else DiagnosticOutcome.FAILED,
                    elapsedMillis(start), DiagnosticError.TRANSPORT)
                if (ticket == generation) mutable.value = if (committing || gateway.durable) before.copy(
                    recoveryRequired = true,
                    notice = if (gateway.durable) "Unable to confirm the outcome. Retry recovery using the original response key; saves are retained."
                        else "Unable to confirm the outcome. Reset this in-memory demo to continue.",
                ) else before.copy(notice = "Response failed. Nothing changed; try again.")
            } finally {
                if (ticket == generation) mutable.value = mutable.value.copy(busy = false, preparingResponse = false)
            }
        }
    }

    fun cancel() {
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
        if (disposed || mutable.value.archiveActive || mutable.value.deletionActive) return
        if (gateway.durable && mutable.value.busy) return
        val start = System.nanoTime()
        diagnosticController.dismiss()
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
        archiveController?.dispose()
        deletionController?.dispose()
        branchDeletionController?.dispose()
        archiveImportPicker = null
        archiveExportPicker = null
        diagnosticController.dispose()
        generation++
        gateway.close()
        pending?.cancel()
        pending = null
        mutable.value = mutable.value.copy(busy = false, preparingResponse = false)
        super.onCleared()
    }
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
