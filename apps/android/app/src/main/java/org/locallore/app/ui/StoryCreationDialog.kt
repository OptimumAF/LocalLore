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
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.key
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTagsAsResourceId
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import org.locallore.app.StoryCreationRequest
import org.locallore.app.StoryCreationUiState
import org.locallore.app.validStoryTitle

/** A starter/title review only. No premise, seed, identity or gameplay editor is exposed. */
@Composable
internal fun StoryCreationDialog(
    state: StoryCreationUiState,
    onDismiss: () -> Unit,
    onTitle: (StoryCreationRequest, String) -> Unit,
    onConfirm: (StoryCreationRequest) -> Unit,
    exposeTestTags: Boolean = false,
) {
    if (!state.visible) return
    val window = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val width = with(density) { window.width.toDp() }
    val height = with(density) { window.height.toDp() }
    val request = state.review
    val editing = !state.busy && !state.creating && !state.closing
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.widthIn(max = minOf(560.dp, width * 0.94f)).fillMaxWidth()
            .heightIn(max = height * 0.9f).fillMaxHeight().testTag("story-creation-dialog")
            .semantics { testTagsAsResourceId = exposeTestTags },
            shape = MaterialTheme.shapes.large, color = MaterialTheme.colorScheme.surface, tonalElevation = 6.dp) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Column(Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState())
                    .testTag("story-creation-content"), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Start a story", style = MaterialTheme.typography.titleLarge,
                        modifier = Modifier.semantics { heading() })
                    Text("Choose a title for this built-in starter. The title labels a new save; it does not change its rules or world.")
                    if (state.busy) {
                        CircularProgressIndicator()
                        Text(when { state.closing -> "Finishing local work…"; state.creating -> "Creating story…"; else -> "Loading starter…" })
                    }
                    state.notice?.let { notice -> Text(notice, modifier = Modifier.testTag("story-creation-notice")
                        .semantics { liveRegion = LiveRegionMode.Polite }) }
                    if (request != null) {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.testTag("story-creation-preview")) {
                            Text("Starter · ${request.preview.defaultTitle}", style = MaterialTheme.typography.titleMedium)
                            Text(request.preview.description)
                            Text("Rules · " + when (request.preview.profile) { "fantasy_v1" -> "Fantasy"; else -> "Starter-defined" })
                            Text("Your starting view", style = MaterialTheme.typography.titleSmall)
                            request.preview.details.forEach { Text(it) }
                        }
                        // Keep typing controllers during edits, but never retarget one to another review.
                        key(CreationIdentity(request.preview), request.creationId) {
                            OutlinedTextField(value = request.title, onValueChange = { onTitle(request, it) },
                                enabled = editing, singleLine = true, label = { Text("Story title") },
                                isError = !validStoryTitle(request.title), modifier = Modifier.fillMaxWidth().testTag("story-creation-title"))
                        }
                        if (!validStoryTitle(request.title)) Text(
                            "Use 1–80 characters without outer spaces, line breaks or control characters.",
                            color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("story-creation-title-error"))
                        // Recreate only the consent button when its rendered object changes. A retained
                        // semantics callback must not route through a mutable replacement onClick.
                        key(CreationIdentity(request)) {
                            Button(onClick = { onConfirm(request) }, enabled = editing && validStoryTitle(request.title),
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("story-creation-confirm")) { Text("Create") }
                        }
                    }
                }
                OutlinedButton(onClick = onDismiss, enabled = !state.closing,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("story-creation-cancel")) {
                    Text(if (state.closing) "Finishing…" else if (request == null && !state.busy) "Close" else "Cancel")
                }
            }
        }
    }
}

private class CreationIdentity(private val value: Any) {
    override fun equals(other: Any?) = other is CreationIdentity && other.value === value
    override fun hashCode() = System.identityHashCode(value)
}
