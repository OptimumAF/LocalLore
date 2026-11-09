/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import org.junit.Assert.*

/** Read-only UI projection assertions; existing native/receipt assertions remain at each call site. */
internal fun ComposeContentTestRule.assertPlayerPotionQuantity(expected: Int?, state: () -> ShellState) {
    // A lazy row can be absent merely because it is offscreen. Establish the
    // exact accepted projection first, then inspect every expected rendered row.
    val accepted = runOnIdle { state() }
    assertTrue(accepted.persistent)
    val inventory = checkNotNull(accepted.inventory).toList()
    assertEquals(expected?.let { listOf(PlayerInventoryItem("potion", it)) }.orEmpty(),
        inventory.filter { it.id == "potion" })
    // Several originalVisible helpers are deliberately called both during
    // recovery and after recovery. Keep their canonical assertion in both states.
    if (accepted.recoveryRequired || accepted.archiveActive || accepted.deletionActive ||
        accepted.forkActive || accepted.creationActive) {
        assertPausedPlayerPotionQuantity(expected, state)
        return
    }
    onNodeWithTag("story-list").performScrollToNode(hasTestTag("player-inventory-open"))
    onNodeWithTag("player-inventory-open").assertIsEnabled()
        .assertTextEquals(if (inventory.isEmpty()) "Inventory · Empty" else "Inventory · ${inventory.size} entries")
        .performClick()
    onNodeWithTag("player-inventory-dialog").assertIsDisplayed()
    onNodeWithTag("player-inventory-unavailable").assertDoesNotExist()
    if (inventory.isEmpty()) onNodeWithTag("player-inventory-empty").assertIsDisplayed()
    for (item in inventory) {
        onNodeWithTag("player-inventory-list").performScrollToNode(hasTestTag("player-inventory-item-${item.id}"))
        onNodeWithTag("player-inventory-item-${item.id}").assert(hasAnyDescendant(hasText(item.id)))
        onNodeWithTag("player-inventory-quantity-${item.id}").assertTextEquals("Quantity · ${item.quantity}")
    }
    onNodeWithTag("player-inventory-close").assertIsDisplayed().performClick()
    onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
}

/** Recovery keeps the accepted projection, while the inspector is deliberately unavailable. */
internal fun ComposeContentTestRule.assertPausedPlayerPotionQuantity(expected: Int?, state: () -> ShellState) {
    onNodeWithTag("story-list").performScrollToNode(hasTestTag("player-inventory-open"))
    onNodeWithTag("player-inventory-open").assertIsNotEnabled()
    onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
    runOnIdle {
        val inventory = checkNotNull(state().inventory)
        assertEquals(expected?.let { listOf(PlayerInventoryItem("potion", it)) }.orEmpty(),
            inventory.filter { it.id == "potion" })
    }
}
