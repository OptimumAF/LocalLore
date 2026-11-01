/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import org.junit.Assert.*

/** Read-only UI projection assertions; existing native/receipt assertions remain at each call site. */
internal fun ComposeContentTestRule.assertPlayerPotionQuantity(expected: Int?) {
    onNodeWithTag("story-list").performScrollToNode(hasTestTag("player-inventory-open"))
    onNodeWithTag("player-inventory-open").assertIsEnabled().performClick()
    onNodeWithTag("player-inventory-dialog").assertIsDisplayed()
    onNodeWithTag("player-inventory-unavailable").assertDoesNotExist()
    if (expected == null) {
        onNodeWithTag("player-inventory-item-potion").assertDoesNotExist()
    } else {
        onNodeWithTag("player-inventory-list").performScrollToNode(hasTestTag("player-inventory-item-potion"))
        onNodeWithTag("player-inventory-item-potion").assert(hasAnyDescendant(hasText("potion")))
        onNodeWithTag("player-inventory-quantity-potion").assertTextEquals("Quantity · $expected")
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
