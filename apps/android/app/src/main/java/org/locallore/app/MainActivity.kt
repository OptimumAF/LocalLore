/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.getValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.DiagnosticsDialog
import org.locallore.app.ui.ArchiveDialog
import org.locallore.app.ui.StoryDeletionDialog
import org.locallore.app.ui.BranchDeletionDialog

class MainActivity : ComponentActivity() {
    private lateinit var model: ShellViewModel
    private val archiveImportPicker = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
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
        enableEdgeToEdge()
        val factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                require(modelClass == ShellViewModel::class.java)
                return ShellViewModel(DurableGateway(NativeWorkspaceTransport(applicationContext), autoCreateIfEmpty = false),
                    archiveGateway = NativeArchiveGateway(applicationContext),
                    deletionGateway = NativeArchiveGateway(applicationContext),
                    branchDeletionGateway = NativeArchiveGateway(applicationContext)) as T
            }
        }
        model = ViewModelProvider(this, factory)[ShellViewModel::class.java]
        setContent {
            val state by model.state.collectAsStateWithLifecycle()
            val diagnostics by model.diagnostics.collectAsStateWithLifecycle()
            val archive by model.archive.collectAsStateWithLifecycle()
            val deletion by model.deletion.collectAsStateWithLifecycle()
            val branchDeletion by model.branchDeletion.collectAsStateWithLifecycle()
            LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                onDiagnostics = model::openDiagnostics, onResume = model::resume, onRecover = model::recover,
                archiveAvailable = model.archiveController != null, onArchive = model::openArchive,
                deletionAvailable = model.deletionController != null, onDelete = model::openDeletion,
                onTimeline = model::resumeTimeline,
                branchDeletionAvailable = model.branchDeletionController != null,
                onDeleteTimeline = model::openBranchDeletion) {
                model.branchDeletionController?.let { controller ->
                    BranchDeletionDialog(branchDeletion, controller::dismiss, controller::cancel, controller::confirm)
                }
                model.deletionController?.let { controller ->
                    StoryDeletionDialog(deletion, controller::dismiss, controller::cancel, controller::confirm)
                }
                DiagnosticsDialog(diagnostics, model::closeDiagnostics, model::clearDiagnostics) {
                    if (model.beginDiagnosticExport()) {
                        try { documentPicker.launch("locallore-diagnostics.json") }
                        catch (_: Exception) { model.diagnosticPickerFailed() }
                    }
                }
                model.archiveController?.let { controller ->
                    ArchiveDialog(archive, controller::dismiss, controller::cancel, controller::prepareExport,
                        onImportPicker = {
                            if (model.beginArchiveImportPicker()) {
                                try { archiveImportPicker.launch(arrayOf("application/json", "application/octet-stream", "text/plain")) }
                                catch (_: Exception) { model.archiveImportPickerFailed() }
                            }
                        },
                        onExportPicker = {
                            if (model.beginArchiveExportPicker()) {
                                try { archiveExportPicker.launch("locallore-private-story.json") }
                                catch (_: Exception) { model.archiveExportPickerFailed() }
                            }
                        }, onConfirmImport = controller::confirmImport, onOpenImported = controller::openImported)
                }
            }
        }
    }

    override fun onStop() {
        // Conservatively stop sample work when the surface leaves the foreground, including rotation.
        // Accepted state belongs to shared durable storage; configuration recreation retains the ViewModel.
        if (::model.isInitialized) model.cancel()
        super.onStop()
    }
}
