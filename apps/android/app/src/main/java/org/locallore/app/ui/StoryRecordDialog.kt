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
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
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
import org.locallore.app.StoryRecordEntry
import org.locallore.app.StoryRecordSection
import org.locallore.app.StoryRecordState

/** Renders only the coordinator's player-eligible records; it cannot change story state. */
@Composable
fun StoryRecordDialog(
    state: StoryRecordState,
    onDismiss: () -> Unit,
    onSection: (StoryRecordSection) -> Unit,
    onSearch: (String) -> Unit,
    onNext: () -> Unit,
    onFirst: () -> Unit,
    onRetry: () -> Unit,
    onEvent: (Long) -> Unit = {},
    onEventBack: () -> Unit = {},
    onEventRetry: (() -> Unit)? = null,
) {
    if (!state.visible) return
    // A new story/head or applied query must never inherit another context's edited search.
    var searchDraft by remember(state.context, state.search) { mutableStateOf(state.search) }
    val recordScrollState = rememberScrollState()
    val windowSize = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val windowWidth = with(density) { windowSize.width.toDp() }
    val windowHeight = with(density) { windowSize.height.toDp() }
    val canQuery = state.context != null && !state.loading

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Surface(
            modifier = Modifier.widthIn(max = minOf(560.dp, windowWidth * 0.94f))
                .fillMaxWidth().heightIn(max = windowHeight * 0.9f).fillMaxHeight()
                .testTag("story-record-dialog"),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 6.dp,
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                val eventDetail = state.eventDetail
                if (eventDetail != null) {
                    StoryEventDetail(
                        detail = eventDetail,
                        context = state.context,
                        onRetry = onEventRetry,
                        modifier = Modifier.weight(1f).fillMaxWidth(),
                    )
                    OutlinedButton(
                        onClick = onEventBack,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                            .testTag("story-event-back"),
                    ) { Text("Back to records") }
                } else Column(
                    modifier = Modifier.weight(1f).fillMaxWidth()
                        .verticalScroll(recordScrollState).testTag("story-record-content"),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text(
                        "Story record",
                        style = MaterialTheme.typography.titleLarge,
                        fontFamily = FontFamily.Serif,
                        modifier = Modifier.semantics { heading() },
                    )
                    state.context?.let { context ->
                        Text(context.story.title, style = MaterialTheme.typography.titleMedium)
                        Text(
                            "Accepted revision · ${context.revision}",
                            style = MaterialTheme.typography.labelLarge,
                        )
                    }
                    Text(
                        "Player-visible lens · read only",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Text(
                        "Statements and beliefs keep their own labels. " +
                            "They do not establish world facts.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    StoryRecordSection.entries.chunked(2).forEach { sections ->
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            sections.forEach { section ->
                                FilterChip(
                                    selected = state.section == section,
                                    onClick = { onSection(section) },
                                    enabled = state.context != null,
                                    label = { Text(section.label) },
                                    modifier = Modifier.weight(1f).heightIn(min = 48.dp)
                                        .testTag("story-record-section-${section.wire}"),
                                )
                            }
                        }
                    }
                    OutlinedTextField(
                        value = searchDraft,
                        onValueChange = { searchDraft = it },
                        enabled = canQuery,
                        label = { Text("Search visible records") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth().testTag("story-record-search"),
                    )
                    Button(
                        onClick = { onSearch(searchDraft) },
                        enabled = canQuery,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                            .testTag("story-record-search-submit"),
                    ) { Text("Search") }
                    HorizontalDivider()
                    when {
                        state.loading -> {
                            Row(
                                horizontalArrangement = Arrangement.spacedBy(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.testTag("story-record-loading")
                                    .semantics { liveRegion = LiveRegionMode.Polite },
                            ) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(24.dp),
                                    strokeWidth = 2.dp,
                                )
                                Text("Loading player-visible records…")
                            }
                        }
                        state.problem != null -> {
                            Text(
                                state.problem.message,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.testTag("story-record-problem")
                                    .semantics { liveRegion = LiveRegionMode.Polite },
                            )
                            OutlinedButton(
                                onClick = onRetry,
                                enabled = canQuery,
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                    .testTag("story-record-retry"),
                            ) { Text("Try again") }
                        }
                        state.context != null -> {
                            Text(
                                "Matched visible records · ${state.total}",
                                style = MaterialTheme.typography.labelLarge,
                            )
                            Text(
                                "This page · ${state.entries.size} records",
                                style = MaterialTheme.typography.bodySmall,
                            )
                            state.storyTime?.let { time ->
                                Text("Story time · $time", style = MaterialTheme.typography.bodySmall)
                            }
                            if (state.entries.isEmpty()) {
                                Text(
                                    "No player-visible records match this view.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    modifier = Modifier.testTag("story-record-empty")
                                        .semantics { liveRegion = LiveRegionMode.Polite },
                                )
                            }
                            state.entries.forEachIndexed { index, entry ->
                                StoryRecordRow(entry, index, onEvent)
                            }
                        }
                        else -> Text("No saved story is selected.")
                    }
                    if (!state.loading && state.problem == null && state.limitations.isNotEmpty()) {
                        Text(
                            "Limits of this view",
                            style = MaterialTheme.typography.titleSmall,
                            modifier = Modifier.semantics { heading() },
                        )
                        state.limitations.forEach { limitation ->
                            Text(limitation, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(
                            onClick = onFirst,
                            enabled = canQuery && state.cursor != null,
                            modifier = Modifier.weight(1f).heightIn(min = 48.dp)
                                .testTag("story-record-first"),
                        ) { Text("First page") }
                        OutlinedButton(
                            onClick = onNext,
                            enabled = canQuery && state.problem == null && state.nextCursor != null,
                            modifier = Modifier.weight(1f).heightIn(min = 48.dp)
                                .testTag("story-record-next"),
                        ) { Text("Next page") }
                    }
                }
                // Dismissal remains reachable even when enlarged text fills a small window.
                TextButton(
                    onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                        .testTag("story-record-close"),
                ) { Text("Close") }
            }
        }
    }
}

@Composable
private fun StoryRecordRow(entry: StoryRecordEntry, index: Int, onEvent: (Long) -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth().testTag("story-record-entry-$index"),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        HorizontalDivider()
        Text(
            entry.title,
            style = MaterialTheme.typography.titleSmall,
            modifier = Modifier.semantics { heading() },
        )
        Text(entry.origin.label, style = MaterialTheme.typography.labelLarge)
        Text(entry.text, style = MaterialTheme.typography.bodyMedium)
        Text(
            if (entry.sources.isEmpty()) "Source · none recorded"
            else "Sources · ${entry.sources.joinToString(" · ")}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        // Only typed, eligible event references supplied by the coordinator become navigation.
        entry.eventSources.forEachIndexed { sourceIndex, reference ->
            OutlinedButton(
                onClick = { onEvent(reference) },
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                    .testTag("story-record-source-$index-$sourceIndex"),
            ) { Text("Open event #$reference") }
        }
    }
}
