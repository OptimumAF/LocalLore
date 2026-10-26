/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

class ShellViewModel internal constructor(
    private val gateway: DemoGateway,
    private val diagnosticLog: DiagnosticLog = DiagnosticLog(),
    archiveGateway: ArchiveGateway? = null,
    deletionGateway: StoryDeletionGateway? = null,
    branchDeletionGateway: BranchDeletionGateway? = null,
    forkGateway: BranchForkGateway? = null,
    private val forkContextProvider: ((SavedStory, Long, Long) -> BranchForkContext?)? = null,
    private val forkRecoveryStore: ForkRecoveryPersistence? = null,
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

    private var forkEpoch = 0L
    private var forkRecoveryIdentity: BranchForkRecovery? = null
    private val mutableForkVisible = MutableStateFlow(false)
    internal val forkVisible = mutableForkVisible.asStateFlow()
    private val mutableForkProblem = MutableStateFlow<String?>(null)
    internal val forkProblem = mutableForkProblem.asStateFlow()
    private val mutableForkRecoveryPending = MutableStateFlow(false)
    internal val forkRecoveryPending = mutableForkRecoveryPending.asStateFlow()
    internal val forkController = forkGateway?.let {
        check(forkContextProvider != null && forkRecoveryStore != null)
        BranchForkController(viewModelScope, it, ::saveForkRecovery)
    }
    internal val fork = forkController?.state ?: MutableStateFlow(BranchForkUiState()).asStateFlow()
    internal val forkAvailable: Boolean get() = forkController != null
    private fun forkBlocksActions() = mutableForkVisible.value || fork.value.busy
    private fun saveForkRecovery(value: BranchForkRecovery?) {
        checkNotNull(forkRecoveryStore).save(value)
        forkRecoveryIdentity = value
        mutableForkRecoveryPending.value = value != null
        mutableForkProblem.value = null
    }
    private fun invalidateForkContext() {
        forkEpoch++
        mutableForkVisible.value = false
        forkController?.contextChanged(null)
        mutable.value = mutable.value.copy(forkActive = fork.value.busy)
    }
    private fun synchronizeForkContext(next: ShellState = mutable.value): BranchForkContext? {
        val selected = next.selectedStory
        val context = if (!disposed && next.persistent && !next.busy && !next.archiveActive && !next.deletionActive &&
            !next.recoveryRequired && !storyRecord.value.visible && !diagnostics.value.visible && selected != null)
            try { forkContextProvider?.invoke(selected, next.revision, forkEpoch) } catch (_: Exception) { null }
        else null
        forkController?.contextChanged(context)
        return context
    }
    internal fun openFork() {
        val before = mutable.value
        val controller = forkController ?: return
        if (disposed || forkBlocksActions() || before.busy || before.archiveActive || before.deletionActive ||
            before.recoveryRequired || !before.persistent) return
        diagnosticController.dismiss(); recordController.dismiss()
        val context = synchronizeForkContext()
        val saved = forkRecoveryIdentity
        if (saved != null) controller.restore(saved)
        else if (mutableForkProblem.value == null) {
            if (context == null) {
                mutable.value = mutable.value.copy(notice = "A coherent saved timeline is required before preparing a fork.")
                return
            }
            controller.prepare(context.head)
        }
        mutableForkVisible.value = true
        mutable.value = mutable.value.copy(forkActive = true)
    }
    internal fun prepareForkBoundary(rendered: BranchForkInput?, atRevision: Long) {
        if (disposed || !mutableForkVisible.value || fork.value.busy || forkRecoveryIdentity != null || mutableForkProblem.value != null ||
            fork.value.input !== rendered) return
        val context = synchronizeForkContext() ?: return
        if (fork.value.input !== rendered || context.head != mutable.value.revision) return
        if (rendered != null && (fork.value.uncertain || fork.value.outcome != null || fork.value.lookupOnly ||
                rendered.parent != context.parent || rendered.expectedParentRevision != context.head)) return
        // Editing an unsubmitted boundary keeps its fixed child ID; never reroll a retry.
        if (rendered == null) forkController?.prepare(atRevision)
        else forkController?.prepare(atRevision, rendered.childBranch)
    }
    internal fun confirmFork(rendered: BranchForkInput, consent: Boolean) {
        if (disposed || !mutableForkVisible.value || mutableForkProblem.value != null) return
        synchronizeForkContext()
        forkController?.confirm(rendered, consent)
    }
    internal fun retryFork(consent: Boolean) {
        if (disposed || !mutableForkVisible.value || mutable.value.busy) return
        synchronizeForkContext()
        forkController?.retryExact(consent)
    }
    internal fun lookupFork() {
        if (disposed || !mutableForkVisible.value || mutable.value.busy || mutable.value.archiveActive || mutable.value.deletionActive) return
        synchronizeForkContext()
        forkController?.lookup()
    }
    internal fun forgetFork(consent: Boolean) {
        if (disposed || !mutableForkVisible.value || mutable.value.busy) return
        forkController?.forgetRecovery(consent)
    }
    internal fun cancelFork() { if (!disposed && mutableForkVisible.value) forkController?.cancel() }
    internal fun closeFork() {
        if (disposed || !mutableForkVisible.value) return
        if (fork.value.busy) { forkController?.cancel(); return }
        forkController?.dismiss()
        mutableForkVisible.value = false
        mutable.value = mutable.value.copy(forkActive = false)
        if (forkRecoveryIdentity != null && !mutable.value.busy)
            savedOperation("Timeline request closed. The original selection is retained; recovery remains explicit.") { gateway.snapshot() }
        else synchronizeForkContext()
    }
    internal fun resumeFork(rendered: BranchForkOutcome) {
        val before = mutable.value
        val current = fork.value
        if (disposed || !mutableForkVisible.value || current.busy || before.busy || current.outcome !== rendered) return
        val input = current.input ?: return
        if (!matchesForkOutcome(rendered, input)) return
        forkController?.dismiss()
        mutableForkVisible.value = false
        mutable.value = before.copy(forkActive = false)
        savedOperation("New timeline resumed. Original history and downstream choices remain unchanged.") {
            // A lookup can observe a story restored by another owner after this UI's catalog.
            // Refresh only on this explicit resume action; never create/select on lookup alone.
            val saved = gateway.snapshot() ?: throw WorkspaceFailure("NotFound")
            val root = saved.stories.singleOrNull { it.story == rendered.scope.story }
                ?: throw WorkspaceFailure("NotFound")
            gateway.resumeSaved(SavedStory(rendered.scope.story, rendered.scope.branch, root.title, rendered.headRevision))
        }
    }
    internal fun stopFork() { if (!disposed) invalidateForkContext() }

    fun openBranchDeletion() {
        val controller = branchDeletionController ?: return
        val before = mutable.value
        if (disposed || forkBlocksActions() || before.busy || before.archiveActive || before.deletionActive || before.recoveryRequired || !before.persistent) return
        val selected = before.selectedStory ?: return
        val root = before.stories.firstOrNull { it.story == selected.story } ?: return
        if (selected.branch == root.branch) return
        diagnosticController.dismiss()
        recordController.dismiss()
        invalidateForkContext()
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
        if (disposed || forkBlocksActions() || before.busy || before.archiveActive || before.deletionActive || before.recoveryRequired || !before.persistent) return
        val selected = before.selectedStory ?: return
        val root = before.stories.firstOrNull { it.story == selected.story } ?: return
        diagnosticController.dismiss()
        recordController.dismiss()
        invalidateForkContext()
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
        if (disposed || forkBlocksActions() || before.archiveActive || before.deletionActive || before.busy || before.recoveryRequired || !before.persistent) return
        val story = before.selectedStory ?: return
        diagnosticController.dismiss()
        recordController.dismiss()
        invalidateForkContext()
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
        forkController?.let { controller ->
            try {
                val saved = checkNotNull(forkRecoveryStore).load()
                if (saved != null) {
                    check(saved.version == 1 && validForkInput(saved.input))
                    forkRecoveryIdentity = saved
                    mutableForkRecoveryPending.value = true
                    controller.restore(saved)
                    controller.dismiss() // Explicit opening/lookup only; never register on startup.
                }
            } catch (_: Exception) {
                mutableForkProblem.value = "The saved fork recovery hint is unavailable. Review and explicitly forget it before creating another timeline."
            }
            viewModelScope.launch(start = CoroutineStart.UNDISPATCHED) {
                controller.state.collect { current ->
                    if (!disposed) {
                        val active = mutableForkVisible.value || current.busy
                        if (mutable.value.forkActive != active) mutable.value = mutable.value.copy(forkActive = active)
                    }
                }
            }
        }
        if (gateway.durable) {
            mutable.value = ShellState(busy = true, persistent = true, notice = "Opening local saved stories…")
            savedOperation("Saved story resumed. Uncommitted responses remain outside accepted history.") { gateway.initialize() }
        }
    }

    private fun publishSaved(saved: SavedSnapshot, notice: String): ShellState {
        val next = mutable.value.copy(
            busy = false, preparingResponse = false, revision = saved.revision, potionOwner = saved.potionOwner,
            messages = saved.messages, persistent = true, storageLocation = saved.location,
            schemaVersion = saved.schemaVersion, stories = saved.stories, selectedStory = saved.selected,
            uncommittedDrafts = saved.uncommittedDrafts,
            rulesProfile = saved.rulesProfile,
            databaseSchemaVersion = saved.databaseSchemaVersion,
            timelines = saved.timelines,
            textProvider = saved.textProvider,
            recoveryRequired = false, checkingCancellation = false,
            notice = if (saved.selectionRestoreUnavailable)
                "Previously selected timeline is unavailable. Review the library before sending." else notice,
        )
        synchronizeForkContext(next)
        return next
    }

    private fun savedOperation(notice: String, checkingCancellation: Boolean = false, operation: suspend () -> SavedSnapshot?) {
        invalidateForkContext()
        recordController.dismiss()
        val ticket = ++generation
        mutable.value = mutable.value.copy(busy = true, preparingResponse = false,
            checkingCancellation = checkingCancellation, notice = null)
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
                if (!disposed && ticket == generation) mutable.value = mutable.value.copy(busy = false, checkingCancellation = false)
            }
        }
    }

    fun recover() {
        if (!disposed && !forkBlocksActions() && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive && gateway.durable) savedOperation("Saved progress recovered.") {
            if (mutable.value.storageLocation == null) gateway.initialize() else gateway.recoverSaved()
        }
    }
    fun resume(story: SavedStory) {
        if (!disposed && !forkBlocksActions() && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive && !mutable.value.recoveryRequired && gateway.durable) savedOperation("Saved story resumed.") { gateway.resumeSaved(story) }
    }
    fun resumeTimeline(timeline: SavedTimeline) {
        val before = mutable.value
        if (disposed || forkBlocksActions() || before.busy || before.archiveActive || before.deletionActive || before.recoveryRequired ||
            !before.persistent || !gateway.durable || before.selectedStory?.story != timeline.story ||
            before.timelines.none { it === timeline }) return
        val root = before.stories.firstOrNull { it.story == timeline.story } ?: return
        diagnosticController.dismiss()
        recordController.dismiss()
        savedOperation("Saved timeline resumed.") {
            gateway.resumeSaved(SavedStory(timeline.story, timeline.branch, root.title, timeline.revision))
        }
    }

    fun openDiagnostics() { if (!disposed && !forkBlocksActions() && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive) {
        invalidateForkContext(); recordController.dismiss(); diagnosticController.open()
    } }
    fun openStoryRecord() {
        val current = mutable.value
        val story = current.selectedStory ?: return
        if (!disposed && !forkBlocksActions() && gateway.storyRecords && current.persistent && !current.busy && !current.archiveActive && !current.deletionActive && !current.recoveryRequired) {
            invalidateForkContext()
            diagnosticController.dismiss()
            recordController.open(StoryRecordContext(story, current.revision))
        }
    }
    fun closeStoryRecord() { recordController.dismiss(); synchronizeForkContext() }
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
    fun closeDiagnostics() { diagnosticController.dismiss(); synchronizeForkContext() }
    fun clearDiagnostics() = diagnosticController.clear()
    fun beginDiagnosticExport() = diagnosticController.beginExport()
    fun diagnosticPickerFailed() = diagnosticController.pickerFailed()
    fun completeDiagnosticExport(writer: (suspend (ByteArray) -> Unit)?) = diagnosticController.completeExport(writer)

    fun setMode(mode: DemoMode) {
        if (!disposed && !forkBlocksActions() && !mutable.value.busy && !mutable.value.archiveActive && !mutable.value.deletionActive && !mutable.value.recoveryRequired) mutable.value = mutable.value.copy(mode = mode, notice = null)
    }

    fun submit(action: DemoAction) = submitResponse(action.description()) { before ->
        gateway.respond(action, before.revision, before.mode)
    }

    /** A retained UI callback cannot retarget its text after selecting another timeline. */
    fun submitText(input: PlayInput, expectedStory: SavedStory?) {
        val selected = mutable.value.selectedStory
        if (expectedStory?.story != selected?.story || expectedStory?.branch != selected?.branch) return
        submitText(input)
    }

    fun submitText(input: PlayInput) {
        if (disposed || forkBlocksActions() || mutable.value.busy || mutable.value.archiveActive || mutable.value.deletionActive || mutable.value.recoveryRequired ||
            (gateway.durable && mutable.value.selectedStory == null)) return
        if (mutable.value.textProvider == TextProvider.UNAVAILABLE || !validPlayInput(input)) {
            mutable.value = mutable.value.copy(notice = "Text input is unavailable or invalid. Nothing changed.")
            return
        }
        submitResponse(input.text) { before -> gateway.respondText(input, before.revision) }
    }

    private fun submitResponse(playerText: String, prepare: suspend (ShellState) -> DemoResult) {
        if (disposed || forkBlocksActions() || mutable.value.busy || mutable.value.archiveActive || mutable.value.deletionActive || mutable.value.recoveryRequired ||
            (gateway.durable && mutable.value.selectedStory == null)) return
        invalidateForkContext()
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
        if (forkBlocksActions()) { cancelFork(); return }
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
            savedOperation("Cancellation checked. Showing the accepted saved history.", checkingCancellation = true) {
                try {
                    gateway.cancelSaved().also {
                        if (!disposed) diagnosticLog.record(DiagnosticPhase.CANCEL,
                            DiagnosticOutcome.COMPLETED, elapsedMillis(start))
                    }
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (failure: Exception) {
                    if (!disposed) diagnosticLog.record(DiagnosticPhase.CANCEL,
                        DiagnosticOutcome.UNKNOWN, elapsedMillis(start),
                        if (failure is WorkspaceFailure) DiagnosticError.fromNative(failure.category)
                        else DiagnosticError.TRANSPORT)
                    throw failure
                }
            }
            return
        }
        mutable.value = mutable.value.copy(busy = false, preparingResponse = false, notice = "Response cancelled. Nothing changed.")
        diagnosticLog.record(DiagnosticPhase.CANCEL, DiagnosticOutcome.COMPLETED, elapsedMillis(start))
    }

    fun reset() {
        // A retained UI callback must not reopen a native session after onCleared.
        if (disposed || forkBlocksActions() || mutable.value.archiveActive || mutable.value.deletionActive) return
        if (gateway.durable && (mutable.value.busy || mutable.value.recoveryRequired)) return
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
        forkController?.dispose() // Cancel/retire before the single workspace transport closes.
        mutableForkVisible.value = false
        archiveController?.dispose()
        deletionController?.dispose()
        branchDeletionController?.dispose()
        archiveImportPicker = null
        archiveExportPicker = null
        diagnosticController.dispose()
        recordController.dispose()
        generation++
        gateway.close()
        pending?.cancel()
        pending = null
        mutable.value = mutable.value.copy(busy = false, preparingResponse = false, forkActive = false, checkingCancellation = false)
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
