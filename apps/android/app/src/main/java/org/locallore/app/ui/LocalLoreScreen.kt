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
import org.locallore.app.ShellState
import org.locallore.app.SavedStory

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
    overlay: @Composable () -> Unit = {},
) {
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
                                    enabled = !state.busy,
                                    modifier = Modifier.heightIn(min = 48.dp)
                                        .testTag("reset-demo"),
                                ) { Text(if (state.persistent) "New story" else "Reset demo") }
                            }
                            Text(
                                "Local Rust engine · fake inference",
                                style = MaterialTheme.typography.labelMedium,
                                color = MutedInk,
                            )
                            Text(
                                if (state.persistent) "Local saved progress · schema ${state.schemaVersion ?: "opening"}"
                                    else "In-memory session · no saved progress",
                                style = MaterialTheme.typography.labelMedium,
                                color = MutedInk,
                            )
                            state.storageLocation?.let { location ->
                                Text(location, style = MaterialTheme.typography.labelSmall, color = MutedInk,
                                    modifier = Modifier.testTag("storage-location"))
                            }
                            if (state.uncommittedDrafts > 0) Text(
                                "${state.uncommittedDrafts} uncommitted response(s). They are retained outside accepted history.",
                                style = MaterialTheme.typography.bodySmall, color = MutedInk)
                            if (state.persistent && state.stories.isNotEmpty()) {
                                var libraryExpanded by remember { mutableStateOf(false) }
                                Box {
                                    TextButton(onClick = { libraryExpanded = true }, enabled = !state.busy,
                                        modifier = Modifier.testTag("saved-library")) {
                                        Text("Saved stories · ${state.stories.size} · ${state.selectedStory?.story.orEmpty()}")
                                    }
                                    DropdownMenu(expanded = libraryExpanded && !state.busy,
                                        onDismissRequest = { libraryExpanded = false }) {
                                        state.stories.forEach { story ->
                                            DropdownMenuItem(text = { Text("${story.title} · ${story.story} · revision ${story.revision}") },
                                                onClick = { libraryExpanded = false; onResume(story) })
                                        }
                                    }
                                }
                            }
                        }
                    }
                    item(key = "scene") {
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
                    item(key = "state") {
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
                    item(key = "actions") {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            if (state.persistent && state.recoveryRequired) OutlinedButton(
                                onClick = onRecover, enabled = !state.busy,
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
                                            if (state.preparingResponse) "Preparing local response…" else "Opening saved progress…",
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
                                enabled = !state.busy && !state.recoveryRequired,
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                    .testTag("give-potion"),
                            ) { Text("Give potion to Mira") }
                            OutlinedButton(
                                onClick = { onAction(DemoAction.TRY_ABILITY) },
                                enabled = !state.busy && !state.recoveryRequired,
                                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                    .testTag("try-ability"),
                            ) { Text("Try unlearned ability") }
                        }
                    }
                    item(key = "diagnostics") {
                        TextButton(onClick = onDiagnostics, enabled = !state.busy,
                            modifier = Modifier.heightIn(min = 48.dp).testTag("open-diagnostics")) {
                            Text("Local diagnostics")
                        }
                    }
                    item(key = "demo-controls") {
                        DemoResponses(state.mode, state.busy || state.recoveryRequired, onMode)
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
