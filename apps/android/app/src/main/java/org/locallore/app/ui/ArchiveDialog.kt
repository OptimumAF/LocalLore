/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
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
import org.locallore.app.ArchiveKind
import org.locallore.app.ArchiveUiState

/** Inert preview text and explicit consent. Native capabilities remain in the controller. */
@Composable
fun ArchiveDialog(
    state: ArchiveUiState,
    onDismiss: () -> Unit,
    onCancel: () -> Unit,
    onPrepareExport: () -> Unit,
    onImportPicker: () -> Unit,
    onExportPicker: () -> Unit,
    onConfirmImport: () -> Unit,
    onOpenImported: () -> Unit,
) {
    if (!state.visible) return
    val window = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val width = with(density) { window.width.toDp() }
    val height = with(density) { window.height.toDp() }
    val ready = !state.busy && !state.awaitingPicker && !state.closing
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(
            modifier = Modifier.widthIn(max = minOf(560.dp, width * 0.94f)).fillMaxWidth()
                .heightIn(max = height * 0.9f).fillMaxHeight().testTag("archive-dialog"),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 6.dp,
        ) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Column(
                    modifier = Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState())
                        .testTag("archive-content"),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text("Playable story archive", style = MaterialTheme.typography.titleLarge,
                        fontFamily = FontFamily.Serif, modifier = Modifier.semantics { heading() })
                    state.selected?.let { Text(it.title, style = MaterialTheme.typography.titleMedium) }
                    Text(
                        "Full private story: every timeline, hidden facts, accepted messages, and model/timing/provenance references. Plaintext files expose spoilers.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Text(
                        "Model weights, separate diagnostics/raw prompt logs, caches, and uncommitted operations are excluded. " +
                            "Your chosen document provider may sync plaintext files. Checksums detect changes; they do not authenticate the author.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    HorizontalDivider()
                    if (state.busy || state.closing) Row(
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.testTag("archive-busy").semantics { liveRegion = LiveRegionMode.Polite },
                    ) {
                        CircularProgressIndicator(modifier = Modifier.size(24.dp), strokeWidth = 2.dp)
                        Text(if (state.closing) "Waiting for work and picker callbacks to finish…" else "Working locally…")
                    }
                    if (state.awaitingPicker) Text(
                        "Waiting for the system document picker. Its previous callback must finish before another picker can open.",
                        style = MaterialTheme.typography.bodyMedium, modifier = Modifier.testTag("archive-picker"),
                    )
                    state.notice?.let { Text(it, style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.testTag("archive-notice").semantics { liveRegion = LiveRegionMode.Polite }) }
                    val imported = state.imported
                    if (imported != null) {
                        Text("Import complete", style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.semantics { heading() })
                        Text("${imported.branches} timelines · ${imported.committedTurns} committed turns")
                        Text("Opening is explicit and starts a fresh session. Imported archives never resume old pending operations.",
                            style = MaterialTheme.typography.bodySmall)
                        Button(onClick = onOpenImported, enabled = ready,
                            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("archive-open-imported")) {
                            Text("Open imported story")
                        }
                    } else {
                        OutlinedButton(onClick = onPrepareExport, enabled = ready,
                            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("archive-export-prepare")) {
                            Text("Capture export preview")
                        }
                        OutlinedButton(onClick = onImportPicker, enabled = ready,
                            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("archive-import-pick")) {
                            Text("Choose archive to validate")
                        }
                        state.prepared?.preview?.let { preview ->
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.testTag("archive-preview")) {
                                HorizontalDivider()
                                Text(preview.title, style = MaterialTheme.typography.titleMedium,
                                    modifier = Modifier.semantics { heading() })
                                Text("Archive format · ${preview.version}")
                                Text("${preview.branchHeads.size} timelines · ${preview.committedTurns} committed turns · ${preview.bytes} bytes")
                                preview.branchHeads.forEach { (branch, head) -> Text(
                                    if (branch in preview.retiredBranchIds) "$branch · retained ancestry through $head (not playable)"
                                    else "$branch · accepted head $head",
                                    style = MaterialTheme.typography.bodySmall) }
                                Text(preview.privacyWarning, style = MaterialTheme.typography.bodySmall)
                                if (preview.retiredBranchIds.isNotEmpty()) Text(
                                    "Reserved deleted timeline IDs: ${preview.retiredBranchIds.joinToString()}. Import preserves these IDs and retained ancestry.",
                                    style = MaterialTheme.typography.bodySmall)
                                Text("Payload checksum · ${preview.payloadSha256}", style = MaterialTheme.typography.bodySmall)
                                if (state.kind == ArchiveKind.EXPORT) {
                                    Text("Choose a new document. LocalLore refuses nonempty or unverifiable opened destinations. " +
                                        "A stopped or failed write may leave a partial new document.", style = MaterialTheme.typography.bodySmall)
                                    Button(onClick = onExportPicker, enabled = ready,
                                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("archive-export-pick")) {
                                        Text("Export this full private archive")
                                    }
                                } else if (state.kind == ArchiveKind.IMPORT) {
                                    Text("Import adds the original story ID and all timelines. An existing ID is a conflict; nothing is overwritten or remapped.",
                                        style = MaterialTheme.typography.bodySmall)
                                    Text("Cancellation may race a completed import. Close to refresh the library if the outcome is uncertain.",
                                        style = MaterialTheme.typography.bodySmall)
                                    Button(onClick = onConfirmImport, enabled = ready,
                                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("archive-import-confirm")) {
                                        Text("Import validated archive")
                                    }
                                }
                            }
                        }
                    }
                }
                if (state.imported == null && !state.closing &&
                    (state.busy || state.awaitingPicker || state.prepared != null)) OutlinedButton(
                    onClick = onCancel, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("archive-cancel"),
                ) { Text("Cancel archive work") }
                TextButton(onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("archive-close")) {
                    Text(if (state.imported != null) "Return to library" else "Close")
                }
            }
        }
    }
}
