/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import org.locallore.app.DiagnosticsUiState

/** Presents the coordinator's frozen export preview; callbacks own consent, writing and clearing. */
@Composable
fun DiagnosticsDialog(
    state: DiagnosticsUiState,
    onDismiss: () -> Unit,
    onClear: () -> Unit,
    onExport: () -> Unit,
) {
    if (!state.visible) return
    val windowSize = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val windowWidth = with(density) { windowSize.width.toDp() }
    val windowHeight = with(density) { windowSize.height.toDp() }
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Surface(
            modifier = Modifier
                .widthIn(max = minOf(560.dp, windowWidth * 0.94f))
                .fillMaxWidth()
                .heightIn(max = windowHeight * 0.9f)
                .fillMaxHeight()
                .testTag("diagnostics-dialog"),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 6.dp,
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                // Keep every action outside this scroll area, including on small screens/large text.
                Column(
                    modifier = Modifier.weight(1f).fillMaxWidth()
                        .verticalScroll(rememberScrollState()).testTag("diagnostics-content"),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text(
                        "Local diagnostics",
                        style = MaterialTheme.typography.titleLarge,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        "Memory-only timings and error categories. No story text is recorded. " +
                            "Review the exact JSON below before exporting.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Text(
                        "Export JSON opens the system document picker. You choose the destination; " +
                            "a document provider may store your file in the cloud. Exports are plaintext. " +
                            "Cancellation or failure may leave an incomplete file. Clearing diagnostics " +
                            "does not delete copies you exported.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Text(
                        state.preview,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.testTag("diagnostics-json"),
                    )
                }
                state.notice?.let { notice ->
                    Text(
                        notice,
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                    )
                }
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Button(
                        onClick = onExport,
                        enabled = !state.exporting,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                            .testTag("diagnostics-export"),
                    ) { Text(if (state.exporting) "Exporting…" else "Export JSON") }
                    OutlinedButton(
                        onClick = onClear,
                        enabled = !state.exporting,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                            .testTag("diagnostics-clear"),
                    ) { Text("Clear diagnostics") }
                    TextButton(
                        onClick = onDismiss,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                            .testTag("diagnostics-close"),
                    ) { Text(if (state.exporting) "Cancel export / close" else "Close") }
                }
            }
        }
    }
}
