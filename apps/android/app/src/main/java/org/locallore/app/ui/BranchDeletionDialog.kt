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
import androidx.compose.material3.ButtonDefaults
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
import org.locallore.app.BranchDeletionPrepared
import org.locallore.app.BranchDeletionUiState

/** All retention decisions and counts come from the captured native preview. */
@Composable
fun BranchDeletionDialog(
    state: BranchDeletionUiState,
    onDismiss: () -> Unit,
    onCancel: () -> Unit,
    onConfirm: (BranchDeletionPrepared) -> Unit,
) {
    if (!state.visible) return
    val window = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val width = with(density) { window.width.toDp() }
    val height = with(density) { window.height.toDp() }
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(
            modifier = Modifier.widthIn(max = minOf(560.dp, width * 0.94f)).fillMaxWidth()
                .heightIn(max = height * 0.9f).fillMaxHeight().testTag("branch-delete-dialog"),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 6.dp,
        ) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Column(
                    modifier = Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).testTag("branch-delete-content"),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text("Delete timeline", style = MaterialTheme.typography.titleLarge, fontFamily = FontFamily.Serif,
                        modifier = Modifier.semantics { heading() })
                    Text("This removes the selected playable timeline and unreachable history. " +
                        "Remaining timelines keep the original ancestry they need.", style = MaterialTheme.typography.bodyMedium)
                    state.selected?.let { Text("Selected timeline · ${it.branch} · accepted head ${it.revision}",
                        style = MaterialTheme.typography.bodySmall) }
                    if (state.busy) Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        CircularProgressIndicator(modifier = Modifier.size(24.dp), strokeWidth = 2.dp)
                        Text(if (state.closing) "Waiting for local work to finish…" else "Working locally…")
                    }
                    state.notice?.let { Text(it, style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.testTag("branch-delete-notice").semantics { liveRegion = LiveRegionMode.Polite }) }
                    state.prepared?.let { prepared ->
                        val preview = prepared.preview
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.testTag("branch-delete-preview")) {
                            HorizontalDivider()
                            Text(preview.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
                            Text("Story · ${preview.storyId}", style = MaterialTheme.typography.bodySmall)
                            Text("Timeline · ${preview.branchId} · accepted head ${preview.expectedRevision}", style = MaterialTheme.typography.bodySmall)
                            Text("Original timeline · ${preview.rootBranch}", style = MaterialTheme.typography.bodySmall)
                            Text("Preview version · ${preview.version}", style = MaterialTheme.typography.bodySmall)
                            Text("Remaining child timelines", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
                            if (preview.retainedDescendants.isEmpty()) Text("No remaining child timelines.", style = MaterialTheme.typography.bodySmall)
                            preview.retainedDescendants.forEach { (branch, head) -> Text("$branch · accepted head $head", style = MaterialTheme.typography.bodySmall) }
                            Text("Required original ancestry retained", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
                            if (preview.retainedHeads.isEmpty()) Text("No ancestry records need to remain for this deletion.", style = MaterialTheme.typography.bodySmall)
                            preview.retainedHeads.forEach { (branch, head) -> Text("$branch · retained through head $head", style = MaterialTheme.typography.bodySmall) }
                            Text("Timeline records removed", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
                            if (preview.removedBranches.isEmpty()) Text("The selected timeline remains only as required ancestry.", style = MaterialTheme.typography.bodySmall)
                            preview.removedBranches.forEach { branch -> Text(branch, style = MaterialTheme.typography.bodySmall) }
                            Text("Committed turns removed · ${preview.removedCommittedTurns}")
                            Text("Noncommitted turns removed · ${preview.removedNoncommittedTurns}")
                            Text("Native rows removed", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
                            preview.removedRows.forEach { (name, count) -> Text("$name · $count", style = MaterialTheme.typography.bodySmall) }
                            Text(preview.privacyWarning, style = MaterialTheme.typography.bodySmall)
                            Button(onClick = { onConfirm(prepared) }, enabled = !state.busy && !state.closing && state.deleted == null,
                                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error,
                                    contentColor = MaterialTheme.colorScheme.onError),
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("branch-delete-confirm")) {
                                Text("Delete this timeline")
                            }
                        }
                    }
                    state.deleted?.let { deleted ->
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.testTag("branch-delete-completed")) {
                            Text("Timeline removed from play", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
                            Text(deleted.retainedThroughRevision?.let { "Original ancestry retained through head $it." }
                                ?: "The selected timeline no longer needs ancestry records.")
                            Text("Timeline records collected · ${deleted.collectedBranches}")
                            Text("Turns removed · ${deleted.deletedTurns}")
                            Text("Close to refresh the retained saved history.", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
                if (state.deleted == null && !state.closing) OutlinedButton(onClick = onCancel,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("branch-delete-cancel")) { Text("Cancel deletion") }
                TextButton(onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("branch-delete-close")) {
                    Text(if (state.closing) "Waiting to close…" else "Close")
                }
            }
        }
    }
}
