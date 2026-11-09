/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
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
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import org.locallore.app.PlayerSelfProfile

/** A cached accepted player view, without queries, inferred mechanics or game actions. */
@Composable
internal fun PlayerSelfProfileSummary(profile: PlayerSelfProfile?, enabled: Boolean, onOpen: () -> Unit) {
    TextButton(onClick = onOpen, enabled = enabled,
        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("player-profile-open")) {
        Text(if (profile == null) "Player state unavailable" else "Player state",
            style = MaterialTheme.typography.labelLarge, modifier = Modifier.testTag("player-profile-summary"))
    }
}

@Composable
private fun ProfileField(tag: String, label: String, value: String) {
    Column(Modifier.fillMaxWidth().testTag("player-profile-$tag"), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, style = MaterialTheme.typography.labelLarge, modifier = Modifier.semantics { heading() })
        Text(value, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.testTag("player-profile-$tag-value"))
    }
}

@Composable
internal fun PlayerSelfProfileDialog(profile: PlayerSelfProfile, rulesProfile: String?, acceptedRevision: Long,
    onDismiss: () -> Unit) {
    val window = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val width = with(density) { window.width.toDp() }
    val height = with(density) { window.height.toDp() }
    val narrative = rulesProfile == "narrative_v1"
    val inapplicable = "Not applicable to this narrative rules profile."
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.widthIn(max = minOf(560.dp, width * 0.94f)).fillMaxWidth()
            .heightIn(max = height * 0.9f).fillMaxHeight().testTag("player-profile-dialog"),
            shape = MaterialTheme.shapes.large, color = MaterialTheme.colorScheme.surface, tonalElevation = 6.dp) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Player state", style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.semantics { heading() })
                Text("Accepted revision · $acceptedRevision", style = MaterialTheme.typography.labelMedium,
                    modifier = Modifier.testTag("player-profile-revision"))
                LazyColumn(Modifier.weight(1f).fillMaxWidth().testTag("player-profile-list"),
                    verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    item(key = "observer") { ProfileField("observer", "Player ID", profile.observer) }
                    item(key = "name") { ProfileField("name", "Name", profile.name) }
                    item(key = "location") { ProfileField("location", "Location", profile.location) }
                    item(key = "alive") { ProfileField("alive", "Life status", if (profile.alive) "Alive" else "Dead") }
                    item(key = "energy") { ProfileField("energy", "Energy", if (narrative) inapplicable else profile.energy.toString()) }
                    item(key = "abilities-heading") {
                        ProfileField("abilities", "Abilities", when {
                            narrative -> inapplicable
                            profile.abilities.isEmpty() -> "No abilities recorded."
                            else -> "Recorded ability IDs and ranks"
                        })
                    }
                    if (!narrative) profile.abilities.forEachIndexed { index, ability ->
                        item(key = "ability-$index") { ProfileField("ability-$index", ability.id, "Rank · ${ability.rank}") }
                    }
                    item(key = "attributes-heading") {
                        ProfileField("attributes", "Attributes", when {
                            narrative -> inapplicable
                            profile.attributes.isEmpty() -> "No attributes recorded."
                            else -> "Recorded attribute names and values"
                        })
                    }
                    if (!narrative) profile.attributes.forEachIndexed { index, attribute ->
                        item(key = "attribute-$index") { ProfileField("attribute-$index", attribute.name, "Value · ${attribute.value}") }
                    }
                    for ((name, values) in listOf("injuries" to profile.injuries,
                        "affiliations" to profile.affiliations, "goals" to profile.goals)) {
                        item(key = "$name-heading") {
                            ProfileField(name, name.replaceFirstChar { it.uppercase() },
                                if (values.isEmpty()) "None recorded." else "Recorded entries")
                        }
                        values.forEachIndexed { index, value ->
                            item(key = "$name-$index") {
                                Text(value, style = MaterialTheme.typography.bodyLarge,
                                    modifier = Modifier.fillMaxWidth().testTag("player-profile-$name-$index"))
                            }
                        }
                    }
                }
                OutlinedButton(onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("player-profile-close")) { Text("Close") }
            }
        }
    }
}
