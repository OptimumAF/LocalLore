/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import org.locallore.app.StoryRecordContext
import org.locallore.app.StoryRecordEventDetail
import org.locallore.app.StoryRecordProblem

/** Displays one eligible event supplied by the coordinator, without recursive source lookup. */
@Composable
internal fun StoryEventDetail(
    detail: StoryRecordEventDetail,
    context: StoryRecordContext?,
    onRetry: (() -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier.testTag("story-event-detail")) {
        Column(
            modifier = Modifier.weight(1f).fillMaxWidth()
                .verticalScroll(rememberScrollState()).testTag("story-event-content"),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "Event #${detail.reference}",
                style = MaterialTheme.typography.titleLarge,
                fontFamily = FontFamily.Serif,
                modifier = Modifier.semantics { heading() },
            )
            context?.let {
                Text(it.story.title, style = MaterialTheme.typography.titleMedium)
                Text(
                    "Frozen accepted head · ${it.revision}",
                    style = MaterialTheme.typography.labelLarge,
                )
            }
            Text("Player-visible lens · read only", style = MaterialTheme.typography.bodyMedium)
            HorizontalDivider()
            val entry = detail.entry
            when {
                detail.loading -> Row(
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.testTag("story-event-loading")
                        .semantics { liveRegion = LiveRegionMode.Polite },
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp), strokeWidth = 2.dp)
                    Text("Loading player-visible event…")
                }
                detail.problem != null || entry == null -> {
                    Text(
                        (detail.problem ?: StoryRecordProblem.EVENT_UNAVAILABLE).message,
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.testTag("story-event-problem")
                            .semantics { liveRegion = LiveRegionMode.Polite },
                    )
                    if (onRetry != null) OutlinedButton(
                        onClick = onRetry,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                            .testTag("story-event-retry"),
                    ) { Text("Try event again") }
                }
                else -> {
                    if (entry.title != "Event #${detail.reference}") Text(
                        entry.title,
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(entry.origin.label, style = MaterialTheme.typography.labelLarge)
                    entry.event?.let { event ->
                        Text("Event story time · ${event.storyTime}",
                            style = MaterialTheme.typography.bodySmall)
                        Text("Turn · ${event.turn}", style = MaterialTheme.typography.bodySmall)
                    }
                    Text(entry.text, style = MaterialTheme.typography.bodyMedium)
                    Text(
                        if (entry.sources.isEmpty()) "Source · none recorded"
                        else "Sources · ${entry.sources.joinToString(" · ")}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}
