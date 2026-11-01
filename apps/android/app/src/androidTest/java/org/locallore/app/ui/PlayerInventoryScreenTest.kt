/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.PlayerInventoryItem
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState
import org.locallore.app.TextProvider
import org.locallore.app.assertPlayerPotionQuantity

/** Real screen with inert accepted-state fixtures; no native, device or accessibility-service claim. */
class PlayerInventoryScreenTest {
    @get:Rule val compose = createComposeRule()
    private val a = SavedStory("inventory-a", "main", "SCRIPTED Orchard", 7)
    private val b = SavedStory("inventory-b", "main", "SCRIPTED Pier", 7)
    private val messages = listOf(SceneMessage(1, "SCRIPTED accepted player input", true),
        SceneMessage(2, "SCRIPTED accepted narration, never an inventory source.", false))
    private val rows = listOf(PlayerInventoryItem("opaque-a", 0), PlayerInventoryItem("opaque-z", 65535))
    private class Calls { var count = 0 }
    private fun initial() = ShellState(persistent = true, selectedStory = a, stories = listOf(b, a),
        revision = 7, messages = messages, textProvider = TextProvider.SCRIPTED, inventory = rows)

    private fun show(state: MutableState<ShellState>, calls: Calls, fontScale: Float = 1f) {
        compose.setContent {
            val density = LocalDensity.current
            CompositionLocalProvider(LocalDensity provides Density(density.density, fontScale)) {
                Box(Modifier.requiredSize(360.dp, 620.dp)) {
                    LocalLoreScreen(state.value, { calls.count++ }, { calls.count++ }, { calls.count++ },
                        { calls.count++ }, onDiagnostics = { calls.count++ }, onResume = { calls.count++ },
                        onRecover = { calls.count++ }, onText = { _, _ -> calls.count++ }, exposeTestTags = true)
                }
            }
        }
        compose.waitForIdle()
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun select(state: MutableState<ShellState>, next: ShellState) {
        compose.runOnIdle { state.value = next }
        compose.waitForIdle()
    }
    private fun open() {
        tag("player-inventory-open").assertIsEnabled().performClick()
        compose.onNodeWithTag("player-inventory-dialog").assertIsDisplayed()
    }
    private fun close() {
        compose.onNodeWithTag("player-inventory-close").assertIsDisplayed().performClick()
        compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
    }
    private fun row(id: String, quantity: Int) {
        compose.onNodeWithTag("player-inventory-list").performScrollToNode(hasTestTag("player-inventory-item-$id"))
        compose.onNodeWithText(id).assertTextEquals(id).assertIsDisplayed()
        compose.onNodeWithTag("player-inventory-quantity-$id").assertTextEquals("Quantity · $quantity")
    }
    private fun retained(name: String): () -> Boolean = checkNotNull(
        compose.onNodeWithTag(name).fetchSemanticsNode().config[SemanticsActions.OnClick].action)

    @Test fun savedRowsKnownEmptyAndUnavailableStayDistinctWhileDemoKeepsItsOriginalPotionRow() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        tag("player-inventory-open").assertTextEquals("Inventory · 2 entries")
        compose.onNodeWithTag("potion-owner").assertDoesNotExist()
        open()
        row("opaque-a", 0)
        row("opaque-z", 65535)
        compose.onNodeWithTag("player-inventory-item-potion").assertDoesNotExist()
        close()

        select(state, original.copy(inventory = emptyList()))
        tag("player-inventory-open").assertTextEquals("Inventory · Empty")
        open()
        compose.onNodeWithTag("player-inventory-empty").assertTextEquals("No items in this player inventory.")
        compose.onNodeWithTag("player-inventory-unavailable").assertDoesNotExist()
        close()
        select(state, original.copy(inventory = null))
        tag("player-inventory-open").assertTextEquals("Inventory unavailable")
        open()
        compose.onNodeWithTag("player-inventory-unavailable").assertTextEquals("Inventory is unavailable for this view.")
        compose.onNodeWithTag("player-inventory-empty").assertDoesNotExist()
        close()

        // Even misleading saved inventory metadata cannot change the nonpersistent demo row.
        select(state, original.copy(persistent = false, selectedStory = null, potionOwner = "You"))
        tag("potion-owner").assertTextEquals("Healing potion · You")
        compose.onNodeWithTag("player-inventory-open").assertDoesNotExist()
        compose.runOnIdle { assertSame(messages, state.value.messages); assertEquals(0, calls.count) }
    }

    @Test fun scopeChangesFenceRetainedOpenAndCloseWhileAcceptedRefreshesKeepTheUnsentDialogue() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val draft = "Unsent caf\u00e9 \u6f22\u5b57 \ud83c\udf3f\nAn inventory view does not send these words."
        tag("play-kind-dialogue").performClick()
        tag("play-input").performTextReplacement(draft)
        tag("player-inventory-open").assertIsEnabled()
        val oldOpen = retained("player-inventory-open")
        open()
        val oldClose = retained("player-inventory-close")
        val refreshed = original.copy(selectedStory = a.copy(title = "Retitled", revision = 8), revision = 8,
            inventory = listOf(PlayerInventoryItem("new-item", 12)))
        select(state, refreshed)
        row("new-item", 12)
        compose.onNodeWithTag("player-inventory-item-opaque-a").assertDoesNotExist()
        close()
        tag("play-input").assert(hasText(draft))
        tag("play-kind-dialogue").assertIsSelected()

        // Browsing uses the coherent accepted view during generation and without text inference.
        select(state, refreshed.copy(busy = true, textProvider = TextProvider.UNAVAILABLE))
        open(); row("new-item", 12); close()
        select(state, refreshed)
        open()
        for (blocked in listOf(refreshed.copy(archiveActive = true), refreshed.copy(recoveryRequired = true))) {
            select(state, blocked)
            compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
            tag("player-inventory-open").assertIsNotEnabled()
            compose.runOnIdle { oldOpen() }
            compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
            select(state, refreshed)
            compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
            tag("play-input").assert(hasText(draft))
            tag("play-kind-dialogue").assertIsSelected()
            open()
        }

        val other = original.copy(selectedStory = b, inventory = listOf(PlayerInventoryItem("b-only", 3)))
        select(state, other)
        compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
        compose.runOnIdle { oldOpen() }
        compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
        tag("play-input").assert(hasText(""))
        open()
        compose.runOnIdle { oldClose() }
        row("b-only", 3)
        val bClose = retained("player-inventory-close")
        close()
        tag("player-inventory-open")
        val bOpenButton = retained("player-inventory-open")
        val fork = other.copy(selectedStory = b.copy(branch = "fork"), inventory = listOf(PlayerInventoryItem("fork-only", 4)))
        select(state, fork)
        compose.runOnIdle { bOpenButton(); oldOpen() }
        compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
        open()
        compose.runOnIdle { bClose(); oldClose() }
        row("fork-only", 4)
        close()
        compose.runOnIdle { assertEquals(fork, state.value); assertSame(messages, state.value.messages); assertEquals(0, calls.count) }
    }

    @Test fun doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions() {
        val longRows = (0 until 32).map { index ->
            PlayerInventoryItem("item_${index.toString().padStart(2, '0')}_" + "x".repeat(56), index * 2)
        }
        assertTrue(longRows.all { it.id.length == 64 })
        val allRows = longRows + PlayerInventoryItem("potion", 1)
        val original = initial().copy(inventory = allRows, textProvider = TextProvider.UNAVAILABLE)
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls, fontScale = 2f)
        open()
        // This potion genuinely exists but is uncomposed below the initial viewport.
        compose.onNodeWithTag("player-inventory-item-potion").assertDoesNotExist()
        for (item in allRows) {
            row(item.id, item.quantity)
            compose.onNodeWithTag("player-inventory-close").assertIsDisplayed().assertIsEnabled()
        }
        close()
        // The source-bound absence oracle must refuse even though assertDoesNotExist
        // on the initial lazy viewport alone would have falsely passed above.
        assertThrows(AssertionError::class.java) {
            compose.assertPlayerPotionQuantity(null) { state.value }
        }
        tag("message-body-1").assertTextEquals(messages[0].text)
        tag("message-body-2").assertTextEquals(messages[1].text)
        compose.runOnIdle { assertEquals(original, state.value); assertSame(messages, state.value.messages); assertEquals(0, calls.count) }
    }
}
