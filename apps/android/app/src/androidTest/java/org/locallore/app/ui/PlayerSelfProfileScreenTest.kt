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
import org.locallore.app.PlayerAbility
import org.locallore.app.PlayerAttribute
import org.locallore.app.PlayerInventoryItem
import org.locallore.app.PlayerSelfProfile
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState
import org.locallore.app.TextProvider

/** Real Compose screen over inert accepted-state fixtures; no native or runtime acceptance claim. */
class PlayerSelfProfileScreenTest {
    @get:Rule val compose = createComposeRule()
    private val a = SavedStory("profile-a", "main", "SCRIPTED Orchard", 7)
    private val b = SavedStory("profile-b", "main", "SCRIPTED Pier", 7)
    private val messages = listOf(SceneMessage(1, "SCRIPTED accepted player input", true),
        SceneMessage(2, "SCRIPTED accepted narration is not a profile source.", false))
    private val profile = PlayerSelfProfile("opaque-self", "Iona 漢字", "native-location-9", true, 65535,
        listOf(PlayerAbility("ability-opaque", 4)), listOf(PlayerAttribute("Recorded resolve", -32768)),
        listOf("Recorded injury"), listOf("Recorded affiliation"), listOf("Recorded goal"))
    private class Calls { var count = 0 }
    private fun initial() = ShellState(persistent = true, selectedStory = a, stories = listOf(b, a),
        revision = 7, messages = messages, rulesProfile = "fantasy_v1", textProvider = TextProvider.SCRIPTED,
        inventory = listOf(PlayerInventoryItem("native-item", 2)), playerProfile = profile)

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
    private fun select(state: MutableState<ShellState>, next: ShellState) {
        compose.runOnIdle { state.value = next }
        compose.waitForIdle()
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun open() {
        tag("player-profile-open").assertIsEnabled().performClick()
        compose.onNodeWithTag("player-profile-dialog").assertIsDisplayed()
        compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
    }
    private fun close() {
        compose.onNodeWithTag("player-profile-close").assertIsDisplayed().assertIsEnabled().performClick()
        compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
    }
    private fun field(name: String, value: String) {
        val node = "player-profile-$name-value"
        compose.onNodeWithTag("player-profile-list").performScrollToNode(hasTestTag(node))
        compose.onNodeWithTag(node).assertTextEquals(value).assertIsDisplayed()
        compose.onNodeWithTag("player-profile-close").assertIsDisplayed().assertIsEnabled()
    }
    private fun entry(name: String, value: String) {
        compose.onNodeWithTag("player-profile-list").performScrollToNode(hasTestTag("player-profile-$name"))
        compose.onNodeWithTag("player-profile-$name").assertTextEquals(value).assertIsDisplayed()
    }
    private fun retained(name: String): () -> Boolean = checkNotNull(
        compose.onNodeWithTag(name).fetchSemanticsNode().config[SemanticsActions.OnClick].action)

    @Test fun acceptedFieldsEmptyUnavailableAndNarrativeApplicabilityStaySeparateFromDemo() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        open()
        compose.onNodeWithTag("player-profile-revision").assertTextEquals("Accepted revision · 7")
        field("observer", "opaque-self")
        field("name", "Iona 漢字")
        field("location", "native-location-9")
        field("alive", "Alive")
        field("energy", "65535")
        field("ability-0", "Rank · 4")
        compose.onNodeWithText("ability-opaque").assertIsDisplayed()
        field("attribute-0", "Value · -32768")
        compose.onNodeWithText("Recorded resolve").assertIsDisplayed()
        entry("injuries-0", "Recorded injury")
        entry("affiliations-0", "Recorded affiliation")
        entry("goals-0", "Recorded goal")
        close()

        val empty = profile.copy(alive = false, energy = 0, abilities = emptyList(), attributes = emptyList(),
            injuries = emptyList(), affiliations = emptyList(), goals = emptyList())
        select(state, original.copy(playerProfile = empty))
        open()
        field("alive", "Dead"); field("energy", "0")
        field("abilities", "No abilities recorded.")
        field("attributes", "No attributes recorded.")
        for (name in listOf("injuries", "affiliations", "goals")) field(name, "None recorded.")
        close()
        select(state, original.copy(rulesProfile = "narrative_v1", playerProfile = empty.copy(alive = true)))
        open()
        for (name in listOf("energy", "abilities", "attributes"))
            field(name, "Not applicable to this narrative rules profile.")
        field("name", profile.name)
        close()
        select(state, original.copy(playerProfile = null))
        tag("player-profile-open").assertTextEquals("Player state unavailable").assertIsNotEnabled()
        compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
        select(state, original.copy(selectedStory = null))
        compose.onNodeWithTag("player-profile-open").assertDoesNotExist()
        select(state, original.copy(persistent = false, selectedStory = null))
        tag("potion-owner").assertTextEquals("Healing potion · You")
        compose.onNodeWithTag("player-profile-open").assertDoesNotExist()
        compose.runOnIdle { assertSame(messages, state.value.messages); assertEquals(0, calls.count) }
    }

    @Test fun retainedInspectorCallbacksRespectScopesWorkflowClosureAndAcceptedRefreshWithoutSendingDraft() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val draft = "Unsent café 漢字 🌿\nThese words cannot define player state."
        tag("play-kind-dialogue").performClick()
        tag("play-input").performTextReplacement(draft)
        tag("player-profile-open")
        val oldOpen = retained("player-profile-open")
        open()
        val oldClose = retained("player-profile-close")
        val refreshed = original.copy(selectedStory = a.copy(title = "Retitled", revision = 8), revision = 8,
            playerProfile = profile.copy(name = "Accepted refreshed name", energy = 12, goals = listOf("New goal")))
        select(state, refreshed)
        compose.onNodeWithTag("player-profile-revision").assertTextEquals("Accepted revision · 8")
        field("name", "Accepted refreshed name"); field("energy", "12"); entry("goals-0", "New goal")
        close()
        tag("play-input").assert(hasText(draft)); tag("play-kind-dialogue").assertIsSelected()

        // Cached state remains readable without provider access or an inference-time query.
        select(state, refreshed.copy(busy = true, textProvider = TextProvider.UNAVAILABLE))
        open(); field("name", "Accepted refreshed name"); close()
        select(state, refreshed)
        tag("player-inventory-open").performClick()
        val inventoryClose = retained("player-inventory-close")
        compose.runOnIdle { oldClose() }
        compose.onNodeWithTag("player-inventory-dialog").assertIsDisplayed()
        compose.runOnIdle { oldOpen() }
        compose.onNodeWithTag("player-inventory-dialog").assertDoesNotExist()
        compose.onNodeWithTag("player-profile-dialog").assertIsDisplayed()
        compose.runOnIdle { inventoryClose() }
        compose.onNodeWithTag("player-profile-dialog").assertIsDisplayed()

        for (blocked in listOf(refreshed.copy(archiveActive = true), refreshed.copy(deletionActive = true),
            refreshed.copy(forkActive = true), refreshed.copy(creationActive = true),
            refreshed.copy(recoveryRequired = true), refreshed.copy(playerProfile = null))) {
            select(state, blocked)
            compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
            tag("player-profile-open").assertIsNotEnabled()
            compose.runOnIdle { oldOpen() }
            compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
            select(state, refreshed)
            compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
            tag("play-input").assert(hasText(draft)); tag("play-kind-dialogue").assertIsSelected()
            open()
        }
        val other = original.copy(selectedStory = b, playerProfile = profile.copy(observer = "b-player", name = "B"))
        select(state, other)
        compose.runOnIdle { oldOpen() }
        compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
        tag("play-input").assert(hasText(""))
        open()
        compose.runOnIdle { oldClose() }
        field("observer", "b-player")
        val bClose = retained("player-profile-close")
        close()
        tag("player-profile-open")
        val bOpen = retained("player-profile-open")
        val fork = other.copy(selectedStory = b.copy(branch = "fork"), playerProfile = profile.copy(name = "Fork"))
        select(state, fork)
        compose.runOnIdle { bOpen(); oldOpen() }
        compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
        open()
        compose.runOnIdle { bClose(); oldClose() }
        field("name", "Fork")
        close()
        select(state, original.copy(persistent = false, selectedStory = null))
        compose.runOnIdle { oldOpen(); bOpen() }
        compose.onNodeWithTag("player-profile-dialog").assertDoesNotExist()
        tag("potion-owner").assertTextEquals("Healing potion · You")
        compose.runOnIdle { assertSame(messages, state.value.messages); assertEquals(0, calls.count) }
    }

    @Test fun doubledFontKeepsFullUnicodeCollectionsAndCloseReachableWithoutCanonicalCallbacks() {
        val longText = "Exact café 漢字 🌿\n" + "long untrimmed native text ".repeat(8)
        val abilities = (0 until 12).map { PlayerAbility("ability-${it.toString().padStart(2, '0')}-" + "x".repeat(45), it) }
        val attributes = (0 until 12).map { PlayerAttribute("$longText attribute $it", it - 6) }
        val goals = (0 until 24).map { "$longText goal $it" }
        val expanded = profile.copy(name = longText, location = "$longText location", abilities = abilities,
            attributes = attributes, injuries = listOf("$longText injury"),
            affiliations = listOf("$longText affiliation"), goals = goals)
        val original = initial().copy(playerProfile = expanded, textProvider = TextProvider.UNAVAILABLE)
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls, fontScale = 2f)
        open()
        field("observer", expanded.observer); field("name", longText); field("location", expanded.location)
        for ((index, ability) in abilities.withIndex()) {
            field("ability-$index", "Rank · ${ability.rank}")
            compose.onNodeWithText(ability.id).assertTextEquals(ability.id)
        }
        for ((index, attribute) in attributes.withIndex()) {
            field("attribute-$index", "Value · ${attribute.value}")
            compose.onNodeWithText(attribute.name).assertTextEquals(attribute.name)
        }
        entry("injuries-0", expanded.injuries.single())
        entry("affiliations-0", expanded.affiliations.single())
        for ((index, goal) in goals.withIndex()) {
            entry("goals-$index", goal)
            compose.onNodeWithTag("player-profile-close").assertIsDisplayed().assertIsEnabled()
        }
        close()
        tag("message-body-1").assertTextEquals(messages[0].text)
        tag("message-body-2").assertTextEquals(messages[1].text)
        compose.runOnIdle { assertEquals(original, state.value); assertSame(messages, state.value.messages); assertEquals(0, calls.count) }
    }
}
