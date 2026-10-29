/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.key
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTagsAsResourceId
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import org.locallore.app.StoryCreationRequest
import org.locallore.app.StoryTemplateOption
import org.locallore.app.StoryCreationUiState
import org.locallore.app.validStoryTitle
import org.locallore.app.validStoryPlayerName
import org.locallore.app.hasReviewedPlayerName
import org.locallore.app.hasReviewedCreation
import org.locallore.app.storyPresentationDraft

/** Initial starter/name/title review. No existing-story or mechanical-state editor. */
@Composable
internal fun StoryCreationDialog(
    state: StoryCreationUiState,
    onDismiss: () -> Unit,
    onTitle: (StoryCreationRequest, String) -> Unit,
    onConfirm: (StoryCreationRequest) -> Unit,
    exposeTestTags: Boolean = false,
    onTemplate: (StoryCreationRequest, StoryTemplateOption) -> Unit = { _, _ -> },
    onPlayerName: (StoryCreationRequest, String) -> Unit = { _, _ -> },
    onPlayerReview: (StoryCreationRequest) -> Unit = {},
    onTone: (StoryCreationRequest, String) -> Unit = { _, _ -> },
    onExcludedPhrases: (StoryCreationRequest, String) -> Unit = { _, _ -> },
) {
    if (!state.visible) return
    val window = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val width = with(density) { window.width.toDp() }
    val height = with(density) { window.height.toDp() }
    val request = state.review
    val editing = !state.busy && !state.creating && !state.closing
    val nameValid = request?.preview?.playerSetup == null || validStoryPlayerName(state.playerNameDraft ?: "")
    val presentationValid = request?.preview?.presentation == null || storyPresentationDraft(state.toneDraft, state.excludedPhrasesDraft) != null
    val reviewed = request != null && hasReviewedCreation(request, state.playerNameDraft, state.toneDraft, state.excludedPhrasesDraft)
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
                    Text(if (request?.preview?.presentation != null)
                        "Choose a starter, player name and narration style for this new story. Review the setup before creating the save."
                        else if (request?.preview?.playerSetup != null)
                        "Choose a built-in starter and player name, review the starting facts, then name the new save. The save title does not change its rules or world."
                        else "Choose a built-in starter, review its starting facts, then name the new save. The title does not change its rules or world.")
                    if (state.busy) {
                        CircularProgressIndicator()
                        Text(when { state.closing -> "Finishing local work…"; state.creating -> "Creating story…"; else -> "Loading starter…" })
                    }
                    state.notice?.let { notice -> Text(notice, modifier = Modifier.testTag("story-creation-notice")
                        .semantics { liveRegion = LiveRegionMode.Polite }) }
                    if (request != null) {
                        if (state.templates.size > 1) {
                            Text("Choose a starter", style = MaterialTheme.typography.titleSmall,
                                modifier = Modifier.semantics { heading() })
                            Column(Modifier.selectableGroup()) {
                                state.templates.forEach { option ->
                                    key(CreationIdentity(request), CreationIdentity(option)) {
                                        val selected = option.template == request.preview.template
                                        Row(Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                            .testTag("story-template-${option.template}")
                                            .selectable(selected = selected, enabled = editing && nameValid &&
                                                (request.preview.presentation == null || reviewed), role = Role.RadioButton,
                                                onClick = { onTemplate(request, option) }),
                                            verticalAlignment = Alignment.CenterVertically) {
                                            RadioButton(selected = selected, enabled = editing && nameValid &&
                                                (request.preview.presentation == null || reviewed), onClick = null)
                                            Text("${option.defaultTitle} · ${ruleLabel(option.profile)}")
                                        }
                                    }
                                }
                            }
                        }
                        if (request.preview.playerSetup != null) {
                            key(CreationIdentity(request.preview), request.creationId) {
                                OutlinedTextField(value = state.playerNameDraft ?: request.preview.playerSetup.playerName,
                                    onValueChange = { onPlayerName(request, it) }, enabled = editing, singleLine = true,
                                    label = { Text("Player name") }, isError = !nameValid,
                                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("story-player-name"))
                            }
                            if (request.preview.presentation != null) {
                                Text("Generated narration", style = MaterialTheme.typography.titleSmall,
                                    modifier = Modifier.semantics { heading() })
                                Column(Modifier.selectableGroup()) {
                                    listOf("plain", "warm", "brisk").forEach { tone ->
                                        key(CreationIdentity(request.preview), request.creationId, tone) {
                                            Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("story-tone-$tone")
                                                .selectable(selected = state.toneDraft == tone, enabled = editing, role = Role.RadioButton,
                                                    onClick = { onTone(request, tone) }), verticalAlignment = Alignment.CenterVertically) {
                                                RadioButton(selected = state.toneDraft == tone, enabled = editing, onClick = null)
                                                Text(toneLabel(tone))
                                            }
                                        }
                                    }
                                }
                                Text("Optional literal phrases to avoid in generated narration. Matching ignores letter case and can match inside a word. These are phrases, not topic filters or restrictions on your messages.")
                                key(CreationIdentity(request.preview), request.creationId) {
                                    OutlinedTextField(value = state.excludedPhrasesDraft.orEmpty(),
                                        onValueChange = { onExcludedPhrases(request, it) }, enabled = editing,
                                        label = { Text("Avoid phrases in generated narration") }, minLines = 2, maxLines = 4,
                                        isError = !presentationValid,
                                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("story-excluded-phrases"))
                                }
                                if (!presentationValid) Text(
                                    "Use up to 8 distinct phrases, one per line, with 1–64 characters each. Keep the combined list short and avoid outer spaces, control characters or blank lines.",
                                    color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("story-presentation-error"))
                                if (!reviewed) Text("Review setup changes before creating the story or choosing another starter.",
                                    modifier = Modifier.testTag("story-presentation-review-required"))
                            }
                            if (!nameValid) Text(
                                "Use 1–64 characters without outer spaces, line breaks or control characters. Fix and review the name before changing starter.",
                                color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("story-player-name-error"))
                            else if (!hasReviewedPlayerName(request, state.playerNameDraft)) Text(
                                "Review changes to update your starting view before creating the story.",
                                modifier = Modifier.testTag("story-player-review-required"))
                            key(CreationIdentity(request)) {
                                OutlinedButton(onClick = { onPlayerReview(request) },
                                    enabled = editing && nameValid && presentationValid && !reviewed,
                                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("story-player-review")) {
                                    Text("Review changes")
                                }
                            }
                        }
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.testTag("story-creation-preview")) {
                            Text("Starter · ${request.preview.defaultTitle}", style = MaterialTheme.typography.titleMedium)
                            Text(request.preview.description)
                            Text("Rules · ${ruleLabel(request.preview.profile)}")
                            request.preview.presentation?.let { presentation ->
                                Text("Reviewed narration tone · ${toneLabel(presentation.tone)}")
                                presentation.excludedPhrases.forEach { Text("Avoid literal phrase: $it") }
                            }
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
                            Button(onClick = { onConfirm(request) }, enabled = editing && validStoryTitle(request.title) &&
                                reviewed,
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

private fun ruleLabel(profile: String) = when (profile) {
    "fantasy_v1" -> "Fantasy"
    "narrative_v1" -> "Narrative"
    else -> "Starter-defined"
}

private fun toneLabel(tone: String) = when (tone) { "plain" -> "Plain"; "warm" -> "Warm"; "brisk" -> "Brisk"; else -> "Unknown" }
