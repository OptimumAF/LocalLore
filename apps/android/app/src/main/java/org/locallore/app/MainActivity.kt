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
import org.locallore.app.ui.StoryRecordDialog

class MainActivity : ComponentActivity() {
    private lateinit var model: ShellViewModel
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
                return ShellViewModel(DurableGateway(NativeWorkspaceTransport(applicationContext))) as T
            }
        }
        model = ViewModelProvider(this, factory)[ShellViewModel::class.java]
        setContent {
            val state by model.state.collectAsStateWithLifecycle()
            val diagnostics by model.diagnostics.collectAsStateWithLifecycle()
            val record by model.storyRecord.collectAsStateWithLifecycle()
            val renderedRecordContext = record.context
            LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                onDiagnostics = model::openDiagnostics, onResume = model::resume, onRecover = model::recover,
                onStoryRecord = if (model.hasStoryRecords) model::openStoryRecord else null) {
                StoryRecordDialog(record, model::closeStoryRecord, model::recordSection, model::recordSearch,
                    model::nextRecordPage, model::firstRecordPage, model::retryStoryRecord,
                    onEvent = { sequence -> model.openRecordEvent(sequence, renderedRecordContext) },
                    onEventBack = model::backToStoryRecord,
                    onEventRetry = model::retryRecordEvent)
                DiagnosticsDialog(diagnostics, model::closeDiagnostics, model::clearDiagnostics) {
                    if (model.beginDiagnosticExport()) {
                        try { documentPicker.launch("locallore-diagnostics.json") }
                        catch (_: Exception) { model.diagnosticPickerFailed() }
                    }
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
