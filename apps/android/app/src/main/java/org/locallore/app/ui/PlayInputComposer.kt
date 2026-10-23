/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.locallore.app.MAX_PLAY_INPUT_BYTES
import org.locallore.app.PlayInput
import org.locallore.app.PlayInputKind
import org.locallore.app.TextProvider
import org.locallore.app.validPlayInput

/** Edits original intent only. Submission and all gameplay changes belong to the coordinator. */
@Composable
internal fun PlayInputComposer(
    input: PlayInput,
    provider: TextProvider,
    busy: Boolean,
    recoveryRequired: Boolean,
    onInput: (PlayInput) -> Unit,
    onSend: (PlayInput) -> Unit,
) {
    val enabled = !busy && !recoveryRequired && provider != TextProvider.UNAVAILABLE
    val valid = validPlayInput(input)
    val byteCount = input.text.toByteArray(Charsets.UTF_8).size
    val problem = when {
        input.text.isEmpty() || valid -> null
        byteCount > MAX_PLAY_INPUT_BYTES -> "Keep text within 2048 UTF-8 bytes."
        input.text.any { it.isISOControl() && it != '\n' && it != '\t' } ->
            "Text may contain new lines and tabs, but no other control characters."
        else -> "Enter an action or dialogue before sending."
    }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            "Write a turn",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.semantics { heading() },
        )
        Text(provider.label, style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.testTag("play-provider"))
        Text(
            when (provider) {
                TextProvider.UNAVAILABLE -> "Text play is unavailable in this session."
                TextProvider.SCRIPTED -> "Scripted fixture accepts the potion example and literal dialogue. " +
                    "Other actions may be rejected."
                TextProvider.LOCAL -> "A local provider is configured. This does not confirm that a model is loaded."
            },
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            PlayInputKind.entries.forEach { kind ->
                FilterChip(
                    selected = input.kind == kind,
                    onClick = { onInput(input.copy(kind = kind)) },
                    enabled = enabled,
                    label = { Text(kind.label) },
                    modifier = Modifier.weight(1f).heightIn(min = 48.dp)
                        .testTag("play-kind-${kind.wire}"),
                )
            }
        }
        Text(
            if (input.kind == PlayInputKind.DIALOGUE) {
                "Dialogue records your words as a statement, not world truth."
            } else {
                "Actions are attempts until the local engine accepts them."
            },
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        OutlinedTextField(
            value = input.text,
            onValueChange = { onInput(input.copy(text = it)) },
            enabled = enabled,
            label = { Text(if (input.kind == PlayInputKind.ACTION) "Your action" else "Your dialogue") },
            minLines = 3,
            maxLines = 6,
            isError = problem != null,
            modifier = Modifier.fillMaxWidth().testTag("play-input"),
        )
        Text(
            "$byteCount / $MAX_PLAY_INPUT_BYTES UTF-8 bytes · new lines and tabs allowed",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (problem != null) Text(
            problem,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.error,
            modifier = Modifier.testTag("play-input-problem")
                .semantics { liveRegion = LiveRegionMode.Polite },
        )
        OutlinedButton(
            onClick = { onInput(PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira.")) },
            enabled = enabled,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("play-example"),
        ) { Text("Potion example") }
        Button(
            onClick = { if (enabled && valid) onSend(input) },
            enabled = enabled && valid,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("play-send"),
        ) { Text("Send") }
    }
}
