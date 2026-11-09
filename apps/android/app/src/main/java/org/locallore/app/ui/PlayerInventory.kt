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
import androidx.compose.foundation.lazy.items
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
import org.locallore.app.PlayerInventoryItem

/** IDs and quantities only; no item-name inference, action or native query. */
@Composable
internal fun PlayerInventorySummary(inventory: List<PlayerInventoryItem>?, enabled: Boolean, onOpen: () -> Unit) {
    TextButton(onClick = onOpen, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
        .testTag("player-inventory-open")) {
        Text(
            when {
                inventory == null -> "Inventory unavailable"
                inventory.isEmpty() -> "Inventory · Empty"
                else -> "Inventory · ${inventory.size} entries"
            },
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.testTag("player-inventory-summary"),
        )
    }
}

@Composable
internal fun PlayerInventoryDialog(inventory: List<PlayerInventoryItem>?, onDismiss: () -> Unit) {
    val window = LocalWindowInfo.current.containerSize
    val density = LocalDensity.current
    val width = with(density) { window.width.toDp() }
    val height = with(density) { window.height.toDp() }
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(
            modifier = Modifier.widthIn(max = minOf(560.dp, width * 0.94f)).fillMaxWidth()
                .heightIn(max = height * 0.9f).fillMaxHeight().testTag("player-inventory-dialog"),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 6.dp,
        ) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Inventory", style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.semantics { heading() })
                LazyColumn(modifier = Modifier.weight(1f).fillMaxWidth().testTag("player-inventory-list"),
                    verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    when {
                        inventory == null -> item(key = "unavailable") {
                            Text("Inventory is unavailable for this view.",
                                modifier = Modifier.testTag("player-inventory-unavailable"))
                        }
                        inventory.isEmpty() -> item(key = "empty") {
                            Text("No items in this player inventory.",
                                modifier = Modifier.testTag("player-inventory-empty"))
                        }
                        else -> items(inventory, key = { it.id }) { item ->
                            Column(modifier = Modifier.fillMaxWidth().testTag("player-inventory-item-${item.id}"),
                                verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text(item.id, style = MaterialTheme.typography.bodyLarge)
                                Text("Quantity · ${item.quantity}", style = MaterialTheme.typography.bodyMedium,
                                    modifier = Modifier.testTag("player-inventory-quantity-${item.id}"))
                            }
                        }
                    }
                }
                OutlinedButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                    .testTag("player-inventory-close")) { Text("Close") }
            }
        }
    }
}
