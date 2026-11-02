/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.getValue
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import java.lang.ref.WeakReference
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.LocalLoreTheme
import org.locallore.app.ui.DiagnosticsDialog
import org.locallore.app.ui.ArchiveDialog
import org.locallore.app.ui.StoryDeletionDialog
import org.locallore.app.ui.BranchDeletionDialog
import org.locallore.app.ui.BranchForkPanel
import org.locallore.app.ui.StoryRecordDialog
import org.locallore.app.ui.StoryCreationDialog

internal class WorkspaceConstructionUnavailable : IllegalStateException("Workspace unavailable")

open class MainActivity : ComponentActivity() {
    private var transportObservation: WeakReference<NativeWorkspaceTransport>? = null
    /** Observe this Activity's construction only; never allocate or replace an owner.
     * A recreation using an already retained ViewModel may legitimately return null.
     */
    internal val constructedWorkspaceTransport: NativeWorkspaceTransport?
        get() = transportObservation?.get()
    // Selected by application construction, never by story text or a model response.
    internal open fun createWorkspaceTransport(): NativeWorkspaceTransport =
        NativeWorkspaceTransport(applicationContext, operationObserver =
            if (BuildConfig.INPUT_PROCESS_VERIFICATION) ProcessVerificationProbe::operation else null)
    private lateinit var model: ShellViewModel
    private var pendingNavigationHint: PlayDraftScope? = null
    private var processVerificationRun: String? = null
    private val archiveImportPicker = registerForActivityResult(ArchiveImportContract()) { uri ->
        if (::model.isInitialized) {
            if (uri == null) model.completeArchiveImport(null)
            else {
                val resolver = applicationContext.contentResolver
                model.completeArchiveImport { readArchiveDocument(resolver, uri) }
            }
        }
    }
    private val archiveExportPicker = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        if (::model.isInitialized) {
            if (uri == null) model.completeArchiveExport(null)
            else {
                val resolver = applicationContext.contentResolver
                model.completeArchiveExport { bytes -> writeArchiveDocument(resolver, uri, bytes) }
            }
        }
    }
    private val documentPicker = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        if (::model.isInitialized) {
            if (uri == null) model.completeDiagnosticExport(null)
            else {
                val resolver = applicationContext.contentResolver
                model.completeDiagnosticExport { bytes -> writeDiagnosticDocument(resolver, uri, bytes) }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pendingNavigationHint = readNavigationHint(savedInstanceState)
        processVerificationRun = if (BuildConfig.INPUT_PROCESS_VERIFICATION) try {
            (savedInstanceState?.getString(ProcessVerificationProbe.RUN_STATE)
                ?: intent.getStringExtra(ProcessVerificationProbe.RUN_EXTRA))
                ?.takeIf { Regex("[0-9a-f]{16}").matches(it) }
        } catch (_: RuntimeException) { null } else null
        ProcessVerificationProbe.configure(applicationContext, processVerificationRun, taskId, savedInstanceState != null)
        enableEdgeToEdge()
        val factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                require(modelClass == ShellViewModel::class.java)
                val transport = createWorkspaceTransport()
                ProcessVerificationProbe.factoryCreated()
                transportObservation = WeakReference(transport)
                val durable = DurableGateway(transport, autoCreateIfEmpty = false,
                    initialScopeHint = pendingNavigationHint)
                return ShellViewModel(durable,
                    archiveGateway = NativeArchiveGateway(applicationContext),
                    deletionGateway = NativeArchiveGateway(applicationContext),
                    branchDeletionGateway = NativeArchiveGateway(applicationContext),
                    forkGateway = NativeForkGateway(transport::forkHandle,
                        mutationObserver = if (BuildConfig.INPUT_PROCESS_VERIFICATION) {
                            { ProcessVerificationProbe.operation("fork_mutation") }
                        } else null),
                    forkContextProvider = durable::forkContext,
                    forkRecoveryStore = AtomicForkRecoveryStore(applicationContext)) as T
            }
        }
        model = try {
            ViewModelProvider(this, factory)[ShellViewModel::class.java]
        } catch (_: WorkspaceConstructionUnavailable) {
            setContent {
                LocalLoreTheme {
                    Surface(Modifier.fillMaxSize()) {
                        Column(Modifier.padding(24.dp)) {
                            Text("Local session unavailable")
                            Text("Close the app completely before starting another local session. Saved stories remain on this device.")
                            Button(onClick = { finish() }) { Text("Close") }
                        }
                    }
                }
            }
            return
        }
        setContent {
            val shellFrame by model.frames.collectAsStateWithLifecycle()
            val state = shellFrame.state
            val diagnostics by model.diagnostics.collectAsStateWithLifecycle()
            val archiveFrame by model.archiveFrames.collectAsStateWithLifecycle()
            val deletionFrame by model.deletionFrames.collectAsStateWithLifecycle()
            val branchDeletionFrame by model.branchDeletionFrames.collectAsStateWithLifecycle()
            val creationFrame by model.creationFrames.collectAsStateWithLifecycle()
            val renderedCreation = creationFrame.state
            val recordFrame by model.storyRecordFrames.collectAsStateWithLifecycle()
            val fork by model.fork.collectAsStateWithLifecycle()
            val forkVisible by model.forkVisible.collectAsStateWithLifecycle()
            val forkProblem by model.forkProblem.collectAsStateWithLifecycle()
            val forkRecoveryPending by model.forkRecoveryPending.collectAsStateWithLifecycle()
            val renderedRecordState = recordFrame.state
            val renderedArchive = archiveFrame.state
            val renderedDeletion = deletionFrame.state
            val renderedBranchDeletion = branchDeletionFrame.state
            val renderedActionStory = state.selectedStory
            val renderedChatState = state
            LocalLoreScreen(renderedChatState, { action -> model.submit(action, renderedActionStory) }, model::setMode,
                { model.cancel(renderedChatState) }, model::startNewStory,
                onDiagnostics = model::openDiagnostics, onResume = { model.resume(it, renderedChatState) },
                onRecover = { model.recover(renderedChatState) },
                onStoryRecord = if (model.hasStoryRecords) model::openStoryRecord else null,
                onText = model::submitText,
                archiveAvailable = model.archiveController != null, onArchive = model::openArchive,
                deletionAvailable = model.deletionController != null, onDelete = model::openDeletion,
                onTimeline = { model.resumeTimeline(it, renderedChatState) },
                branchDeletionAvailable = model.branchDeletionController != null,
                onDeleteTimeline = model::openBranchDeletion,
                forkAvailable = model.forkAvailable, forkRecoveryAvailable = forkRecoveryPending || forkProblem != null,
                exposeTestTags = BuildConfig.INPUT_PROCESS_VERIFICATION,
                draftInteractionAllowed = model::canEditPlayDraft,
                onFork = { model.openFork(renderedChatState) }) {
                // Plain values bind each callback to what this composition displayed.
                val renderedFork = fork
                BranchForkPanel(forkVisible, renderedFork, forkProblem, forkRecoveryPending,
                    onBoundary = { input, revision -> model.prepareForkBoundary(input, revision, renderedFork) },
                    onConfirm = { input, consent -> model.confirmFork(input, consent, renderedFork) },
                    onRetry = { model.retryFork(it, renderedFork) }, onLookup = { model.lookupFork(renderedFork) },
                    onForget = { model.forgetFork(it, renderedFork) }, onCancel = { model.cancelFork(renderedFork) },
                    onClose = { model.closeFork(renderedFork) }, onResume = { model.resumeFork(it, renderedFork) },
                    exposeTestTags = BuildConfig.INPUT_PROCESS_VERIFICATION)
                model.branchDeletionController?.let { controller ->
                    BranchDeletionDialog(renderedBranchDeletion,
                        { controller.dismiss(renderedBranchDeletion) }, { controller.cancel(renderedBranchDeletion) },
                        { expected -> controller.confirm(expected, renderedBranchDeletion) })
                }
                model.creationController?.let { controller ->
                    StoryCreationDialog(renderedCreation, { controller.dismiss(renderedCreation) }, controller::editTitle, controller::confirm,
                        exposeTestTags = BuildConfig.INPUT_PROCESS_VERIFICATION, onTemplate = controller::chooseTemplate,
                        onPlayerName = controller::editPlayerName, onPlayerReview = controller::reviewChanges,
                        onTone = controller::editTone, onExcludedPhrases = controller::editExcludedPhrases,
                        onOriginal=controller::chooseOriginal,onOriginalEdit={s,e -> controller.editOriginal(s,e); Unit},
                        onOriginalGenerate={controller.generateOriginal(it); Unit},onOriginalReview={controller.reviewOriginal(it); Unit},
                        onOriginalCreate={s,r -> controller.confirmOriginal(s,r); Unit})
                }
                model.deletionController?.let { controller ->
                    StoryDeletionDialog(renderedDeletion,
                        { controller.dismiss(renderedDeletion) }, { controller.cancel(renderedDeletion) },
                        { expected -> controller.confirm(expected, renderedDeletion) })
                }
                StoryRecordDialog(renderedRecordState,
                    { model.closeStoryRecord(renderedRecordState) },
                    { section -> model.recordSection(section, renderedRecordState) },
                    { text -> model.recordSearch(text, renderedRecordState) },
                    { model.nextRecordPage(renderedRecordState) },
                    { model.firstRecordPage(renderedRecordState) },
                    { model.retryStoryRecord(renderedRecordState) },
                    onEvent = { sequence -> model.openRecordEvent(sequence, renderedRecordState) },
                    onScopedEvent = { reference -> model.openScopedRecordEvent(reference, renderedRecordState) },
                    onEventBack = { model.backToStoryRecord(renderedRecordState) },
                    onEventRetry = { model.retryRecordEvent(renderedRecordState) },
                    onPromiseFilter = { filter -> model.recordPromiseFilter(filter, renderedRecordState) },
                    onKnowledgeFilter = { filter -> model.recordKnowledgeFilter(filter, renderedRecordState) },
                    onFocusRelationship = { entry -> model.focusRecordRelationship(entry, renderedRecordState) },
                    onAllRelationships = { model.allRecordRelationships(renderedRecordState) })
                DiagnosticsDialog(diagnostics, model::closeDiagnostics, model::clearDiagnostics) {
                    if (model.beginDiagnosticExport()) {
                        try { documentPicker.launch("locallore-diagnostics.json") }
                        catch (_: Exception) { model.diagnosticPickerFailed() }
                    }
                }
                model.archiveController?.let { controller ->
                    ArchiveDialog(renderedArchive, { controller.dismiss(renderedArchive) },
                        { controller.cancel(renderedArchive) }, { controller.prepareExport(renderedArchive) },
                        onImportPicker = {
                            if (model.beginArchiveImportPicker(renderedArchive)) {
                                try { archiveImportPicker.launch("*/*") }
                                catch (_: Exception) { model.archiveImportPickerFailed() }
                            }
                        },
                        onExportPicker = { expected ->
                            if (model.beginArchiveExportPicker(expected, renderedArchive)) {
                                try { archiveExportPicker.launch("locallore-private-story.json") }
                                catch (_: Exception) { model.archiveExportPickerFailed() }
                            }
                        }, onConfirmImport = { expected -> controller.confirmImport(expected, renderedArchive) },
                        onOpenImported = { expected -> controller.openImported(expected, renderedArchive) })
                }
            }
        }
        ProcessVerificationProbe.created(pendingNavigationHint)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        if (::model.isInitialized) pendingNavigationHint = navigationHintToSave(pendingNavigationHint, model.state.value)
        encodeNavigationHint(pendingNavigationHint)?.let { value ->
            outState.putBundle("locallore.navigation.v1", Bundle().apply {
                putInt("version", value[0] as Int)
                putString("story", value[1] as String)
                putString("branch", value[2] as String)
            })
        }
        processVerificationRun?.let { outState.putString(ProcessVerificationProbe.RUN_STATE, it) }
        ProcessVerificationProbe.saved(pendingNavigationHint)
    }

    private fun readNavigationHint(state: Bundle?): PlayDraftScope? = try {
        state?.getBundle("locallore.navigation.v1")?.let { hint ->
            if (hint.keySet() != setOf("version", "story", "branch")) null
            else {
                @Suppress("DEPRECATION")
                decodeNavigationHint(listOf(hint.get("version"), hint.get("story"), hint.get("branch")))
            }
        }
    } catch (_: RuntimeException) { null } // Malformed UI saved state is never native storage authority.

    override fun onStop() {
        // Conservatively stop sample work when the surface leaves the foreground, including rotation.
        // Accepted state belongs to shared durable storage; configuration recreation retains the ViewModel.
        if (::model.isInitialized) {
            model.cancel()
            model.stopFork()
        }
        super.onStop()
    }
}
