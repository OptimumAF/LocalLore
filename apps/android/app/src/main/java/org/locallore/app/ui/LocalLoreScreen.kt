/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import org.locallore.app.DemoAction
import org.locallore.app.DemoMode
import org.locallore.app.PlayInput
import org.locallore.app.PlayInputKind
import org.locallore.app.ShellState
import org.locallore.app.SavedStory
import org.locallore.app.SavedTimeline
import org.locallore.app.TextProvider

private val Paper = Color(0xFFF8F5EC)
private val Ink = Color(0xFF202D2A)
private val Teal = Color(0xFF18584E)
private val MutedInk = Color(0xFF4D5C56)

/** A state-only sample surface. The coordinator owns every response and state change. */
@Composable
fun LocalLoreScreen(
    state: ShellState,
    onAction: (DemoAction) -> Unit,
    onMode: (DemoMode) -> Unit,
    onCancel: () -> Unit,
    onReset: () -> Unit,
    onDiagnostics: () -> Unit = {},
    onResume: (SavedStory) -> Unit = {},
    onRecover: () -> Unit = {},
    onStoryRecord: (() -> Unit)? = null,
    onText: ((PlayInput) -> Unit)? = null,
    archiveAvailable: Boolean = false,
    onArchive: () -> Unit = {},
    deletionAvailable: Boolean = false,
    onDelete: () -> Unit = {},
    onTimeline: ((SavedTimeline) -> Unit)? = null,
    branchDeletionAvailable: Boolean = false,
    onDeleteTimeline: () -> Unit = {},
    forkAvailable: Boolean = false,
    forkRecoveryAvailable: Boolean = false,
    onFork: () -> Unit = {},
    overlay: @Composable () -> Unit = {},
) {
    // Keep unsent text in this composition, including when its lazy item scrolls off screen.
    // A new accepted head retains it; a different story/branch or disposal forgets it.
    var playInput by remember(state.selectedStory?.story, state.selectedStory?.branch) {
        mutableStateOf(PlayInput(PlayInputKind.ACTION, ""))
    }
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = Teal,
            onPrimary = Color.White,
            surface = Paper,
            background = Paper,
            onSurface = Ink,
            onBackground = Ink,
            onSurfaceVariant = MutedInk,
            outline = MutedInk,
        ),
    ) {
        overlay()
        Scaffold(containerColor = Paper) { safePadding ->
            Box(
                modifier = Modifier.fillMaxSize().padding(safePadding),
                contentAlignment = Alignment.TopCenter,
            ) {
                // A single scroll surface keeps actions reachable in landscape and at large fonts.
                LazyColumn(
                    modifier = Modifier.widthIn(max = 760.dp).fillMaxSize()
                        .testTag("story-list"),
                    contentPadding = PaddingValues(horizontal = 24.dp, vertical = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(20.dp),
                ) {
                    item(key = "brand") {
                        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text(
                                    text = "LocalLore",
                                    style = MaterialTheme.typography.headlineLarge,
                                    fontFamily = FontFamily.Serif,
                                    modifier = Modifier.weight(1f).semantics { heading() },
                                )
                                TextButton(
                                    onClick = onReset,
                                    enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && (!state.persistent || !state.recoveryRequired),
                                    modifier = Modifier.heightIn(min = 48.dp)
                                        .testTag("reset-demo"),
                                ) { Text(if (state.persistent) "New story" else "Reset demo") }
                            }
                            Text(
                                when (state.textProvider) {
                                    TextProvider.LOCAL -> "Local Rust engine · local inference configured"
                                    TextProvider.SCRIPTED -> "Local Rust engine · fake inference"
                                    TextProvider.UNAVAILABLE -> "Local Rust engine · text inference unavailable"
                                },
                                style = MaterialTheme.typography.labelMedium,
                                color = MutedInk,
                                modifier = Modifier.testTag("inference-provider"),
                            )
                            Text(
                                if (state.persistent) "Local saved progress · database schema ${state.databaseSchemaVersion ?: "opening"}"
                                    else "In-memory session · no saved progress",
                                style = MaterialTheme.typography.labelMedium,
                                color = MutedInk,
                            )
                            state.storageLocation?.let { location ->
                                Text(location, style = MaterialTheme.typography.labelSmall, color = MutedInk,
                                    modifier = Modifier.testTag("storage-location"))
                            }
                            state.selectedStory?.let { story ->
                                Text("Rules · ${state.rulesProfile ?: "unknown"} · ${story.story} / ${story.branch} · head ${state.revision}",
                                    style = MaterialTheme.typography.labelSmall, color = MutedInk,
                                    modifier = Modifier.testTag("workspace-detail"))
                            }
                            if (state.uncommittedDrafts > 0) Text(
                                "${state.uncommittedDrafts} uncommitted response(s). They are retained outside accepted history.",
                                style = MaterialTheme.typography.bodySmall, color = MutedInk)
                            if (state.persistent && state.stories.isNotEmpty()) {
                                var libraryExpanded by remember { mutableStateOf(false) }
                                Box {
                                    TextButton(onClick = { libraryExpanded = true }, enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired,
                                        modifier = Modifier.testTag("saved-library")) {
                                        Text("Saved stories · ${state.stories.size} · ${state.selectedStory?.story.orEmpty()}")
                                    }
                                    DropdownMenu(expanded = libraryExpanded && !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired,
                                        onDismissRequest = { libraryExpanded = false }) {
                                        state.stories.forEach { story ->
                                            DropdownMenuItem(text = { Text("${story.title} · ${story.story} · revision ${story.revision}") },
                                                onClick = { libraryExpanded = false; onResume(story) })
                                        }
                                    }
                                }
                            }
                            if (onTimeline != null && state.persistent && state.selectedStory != null && state.timelines.isNotEmpty()) {
                                var timelinesExpanded by remember(state.selectedStory.story) { mutableStateOf(false) }
                                val canSelect = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired
                                val selected = state.timelines.firstOrNull { it.branch == state.selectedStory.branch }
                                selected?.let { timeline ->
                                    Text("Timeline · ${timeline.branch} · " +
                                        (timeline.parentBranch?.let { "from $it at ${timeline.forkRevision}" } ?: "original") +
                                        " · revision ${timeline.revision} · ${timeline.uncommittedDrafts} uncommitted",
                                        style = MaterialTheme.typography.bodySmall)
                                }
                                Box {
                                    TextButton(onClick = { timelinesExpanded = true }, enabled = canSelect,
                                        modifier = Modifier.heightIn(min = 48.dp).testTag("timeline-library")) {
                                        Text("Choose timeline · ${state.timelines.size}")
                                    }
                                    DropdownMenu(expanded = timelinesExpanded && canSelect,
                                        onDismissRequest = { timelinesExpanded = false }) {
                                        state.timelines.forEach { timeline ->
                                            DropdownMenuItem(text = { Text("${timeline.branch} · " +
                                                (timeline.parentBranch?.let { "from $it at ${timeline.forkRevision}" } ?: "original") +
                                                " · revision ${timeline.revision} · ${timeline.uncommittedDrafts} uncommitted") },
                                                onClick = { timelinesExpanded = false; onTimeline(timeline) },
                                                modifier = Modifier.heightIn(min = 48.dp).testTag("timeline-${timeline.branch}"))
                                        }
                                    }
                                }
                            }
                            if (forkAvailable && state.persistent && (state.selectedStory != null || forkRecoveryAvailable)) {
                                OutlinedButton(onClick = onFork,
                                    enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired,
                                    modifier = Modifier.heightIn(min = 48.dp).testTag("fork-timeline")) {
                                    Text(if (forkRecoveryAvailable) "Recover timeline request…" else "New timeline…")
                                }
                            }
                            if (state.forkActive) Text("Timeline review is open or finishing. Other actions are paused.",
                                style = MaterialTheme.typography.bodySmall, modifier = Modifier.testTag("fork-active"))
                            if (archiveAvailable && state.persistent) {
                                OutlinedButton(onClick = onArchive,
                                    enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired && state.selectedStory != null,
                                    modifier = Modifier.testTag("story-archive")) { Text("Story archive") }
                            }
                            if (deletionAvailable && state.persistent && state.selectedStory != null) {
                                OutlinedButton(onClick = onDelete,
                                    enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired,
                                    modifier = Modifier.heightIn(min = 48.dp).testTag("delete-story")) { Text("Delete story...") }
                            }
                            if (branchDeletionAvailable && state.persistent && state.selectedStory != null) {
                                val root = state.stories.firstOrNull { it.story == state.selectedStory.story }
                                OutlinedButton(onClick = onDeleteTimeline,
                                    enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired &&
                                        root != null && state.selectedStory.branch != root.branch,
                                    modifier = Modifier.heightIn(min = 48.dp).testTag("delete-timeline")) { Text("Delete timeline...") }
                            }
                        }
                    }
                    if (state.persistent && state.selectedStory == null) item(key = "empty-library") {
                        Text("No saved stories. Choose New story to begin.", modifier = Modifier.testTag("empty-library"))
                    }
                    if (!state.persistent || state.selectedStory != null) item(key = "scene") {
                        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            HorizontalDivider(color = MutedInk.copy(alpha = 0.3f))
                            Text(
                                "Lantern Quay",
                                style = MaterialTheme.typography.headlineMedium,
                                fontFamily = FontFamily.Serif,
                                modifier = Modifier.semantics { heading() },
                            )
                            Text(
                                "The tide laps below the quay. Mira waits beside you. " +
                                    "Oren’s borrowed brass key rests in your satchel.",
                                style = MaterialTheme.typography.bodyLarge,
                                fontFamily = FontFamily.Serif,
                            )
                        }
                    }
                    if (!state.persistent || state.selectedStory != null) item(key = "state") {
                        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(
                                "Healing potion · ${state.potionOwner}",
                                style = MaterialTheme.typography.labelLarge,
                                modifier = Modifier.testTag("potion-owner"),
                            )
                            Text(
                                "Accepted revision · ${state.revision}",
                                style = MaterialTheme.typography.labelMedium,
                                color = MutedInk,
                                modifier = Modifier.testTag("revision"),
                            )
                        }
                    }
                    items(state.messages, key = { "message-${it.id}" }) { message ->
                        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(
                                if (message.isPlayer) "You" else "Narrator",
                                style = MaterialTheme.typography.labelMedium,
                                color = MutedInk,
                            )
                            Text(
                                message.text,
                                style = MaterialTheme.typography.bodyLarge,
                                fontFamily = if (message.isPlayer) {
                                    FontFamily.SansSerif
                                } else {
                                    FontFamily.Serif
                                },
                            )
                        }
                    }
                    item(key = "notice") {
                        AnimatedVisibility(visible = state.notice != null) {
                            Text(
                                state.notice.orEmpty(),
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.testTag("notice").semantics {
                                    liveRegion = LiveRegionMode.Polite
                                },
                            )
                        }
                    }
                    if (onText != null) item(key = "play-composer") {
                        PlayInputComposer(
                            input = playInput,
                            provider = state.textProvider,
                            busy = state.busy || state.archiveActive || state.deletionActive || state.forkActive ||
                                (state.persistent && state.selectedStory == null),
                            recoveryRequired = state.recoveryRequired,
                            onInput = { playInput = it },
                            onSend = onText,
                        )
                    }
                    item(key = "actions") {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            if (state.persistent && state.recoveryRequired) OutlinedButton(
                                onClick = onRecover, enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive,
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("recover-save"),
                            ) { Text("Recover saved progress") }
                            AnimatedVisibility(visible = state.busy) {
                                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Row(
                                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                    ) {
                                        CircularProgressIndicator(
                                            modifier = Modifier.widthIn(max = 24.dp)
                                                .heightIn(max = 24.dp),
                                            strokeWidth = 2.dp,
                                        )
                                        Text(
                                            when {
                                                state.preparingResponse -> "Preparing local response…"
                                                state.checkingCancellation -> "Checking cancellation…"
                                                else -> "Opening saved progress…"
                                            },
                                            style = MaterialTheme.typography.bodyMedium,
                                            modifier = Modifier.testTag("busy-status").semantics {
                                                liveRegion = LiveRegionMode.Polite
                                            },
                                        )
                                    }
                                    if (state.preparingResponse) OutlinedButton(
                                        onClick = onCancel,
                                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                            .testTag("cancel-turn"),
                                    ) { Text("Cancel response") }
                                }
                            }
                            Button(
                                onClick = { onAction(DemoAction.GIVE_POTION) },
                                enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired && (!state.persistent || state.selectedStory != null),
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                    .testTag("give-potion"),
                            ) { Text("Give potion to Mira") }
                            OutlinedButton(
                                onClick = { onAction(DemoAction.TRY_ABILITY) },
                                enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired && (!state.persistent || state.selectedStory != null),
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                    .testTag("try-ability"),
                            ) { Text("Try unlearned ability") }
                        }
                    }
                    if (onStoryRecord != null) item(key = "story-record") {
                        OutlinedButton(
                            onClick = onStoryRecord,
                            enabled = state.persistent && state.selectedStory != null &&
                                !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive && !state.recoveryRequired,
                            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                .testTag("story-record-open"),
                        ) { Text("Story record") }
                    }
                    item(key = "diagnostics") {
                        TextButton(onClick = onDiagnostics, enabled = !state.busy && !state.archiveActive && !state.deletionActive && !state.forkActive,
                            modifier = Modifier.heightIn(min = 48.dp).testTag("open-diagnostics")) {
                            Text("Local diagnostics")
                        }
                    }
                    item(key = "demo-controls") {
                        DemoResponses(state.mode, state.busy || state.archiveActive || state.deletionActive || state.forkActive || state.recoveryRequired || (state.persistent && state.selectedStory == null), onMode)
                    }
                }
            }
        }
    }
}

@Composable
private fun DemoResponses(mode: DemoMode, busy: Boolean, onMode: (DemoMode) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        HorizontalDivider(color = MutedInk.copy(alpha = 0.3f))
        Box {
            TextButton(
                onClick = { expanded = true },
                enabled = !busy,
                modifier = Modifier.heightIn(min = 48.dp).testTag("mode-menu"),
            ) { Text("Demo responses · ${mode.label()}") }
            DropdownMenu(expanded = expanded && !busy, onDismissRequest = { expanded = false }) {
                DemoMode.entries.forEach { option ->
                    DropdownMenuItem(
                        text = { Text(option.label()) },
                        onClick = {
                            expanded = false
                            onMode(option)
                        },
                        modifier = Modifier.heightIn(min = 48.dp).testTag("mode-${option.name}"),
                    )
                }
            }
        }
    }
}

private fun DemoMode.label(): String = when (this) {
    DemoMode.ACCEPTED -> "Normal"
    DemoMode.MALFORMED -> "Malformed"
    DemoMode.REJECTED -> "Rejected"
    DemoMode.DELAYED -> "Delayed"
    DemoMode.FAILED -> "Failure"
}
