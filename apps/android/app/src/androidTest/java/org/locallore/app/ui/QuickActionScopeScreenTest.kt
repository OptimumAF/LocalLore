/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.DemoAction
import org.locallore.app.PlayInput
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState
import org.locallore.app.TextProvider

/** Real rendered button controllers with inert snapshots and callback spies; no native acceptance. */
class QuickActionScopeScreenTest {
    @get:Rule val compose = createComposeRule()
    private val a = SavedStory("scripted-a", "main", "SCRIPTED A", 7)
    private val b = SavedStory("scripted-b", "main", "SCRIPTED B", 7)
    private val messages = listOf(SceneMessage(1, "SCRIPTED original player words", true),
        SceneMessage(2, "SCRIPTED accepted history remains unchanged", false))

    private class Calls {
        val actions = mutableListOf<Pair<DemoAction, SavedStory?>>()
        val sent = mutableListOf<Pair<PlayInput, SavedStory?>>()
        var other = 0
        fun assertNoOtherWork() { assertTrue(sent.isEmpty()); assertEquals(0, other) }
    }
    private data class Clicks(val give: () -> Boolean, val ability: () -> Boolean)
    private fun initial() = ShellState(revision = 7, persistent = true, selectedStory = a,
        stories = listOf(a, b), textProvider = TextProvider.SCRIPTED, messages = messages)

    private fun show(state: MutableState<ShellState>, calls: Calls) {
        compose.setContent {
            // This plain rendered value deliberately cannot retarget a captured callback.
            val rendered = state.value
            Box(Modifier.requiredSize(360.dp, 620.dp)) {
                LocalLoreScreen(rendered, { action -> calls.actions += action to rendered.selectedStory },
                    { calls.other++ }, { calls.other++ }, { calls.other++ },
                    onDiagnostics = { calls.other++ }, onResume = { calls.other++ }, onRecover = { calls.other++ },
                    onText = { input, scope -> calls.sent += input to scope }, exposeTestTags = true)
            }
        }
        compose.waitForIdle()
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun retainEnabledClicks() = Clicks(
        checkNotNull(tag("give-potion").assertIsEnabled().fetchSemanticsNode().config[SemanticsActions.OnClick].action),
        checkNotNull(tag("try-ability").assertIsEnabled().fetchSemanticsNode().config[SemanticsActions.OnClick].action),
    )
    private fun invokeRetained(clicks: Clicks) {
        compose.runOnIdle { clicks.give(); clicks.ability() }
        compose.waitForIdle()
    }
    private fun select(state: MutableState<ShellState>, next: ShellState) {
        compose.runOnIdle { state.value = next }
        compose.waitForIdle()
    }
    private fun freshButtons() {
        tag("give-potion").assertIsEnabled().performClick()
        tag("try-ability").assertIsEnabled().performClick()
    }
    private fun assertActions(calls: Calls, scopes: List<SavedStory?>) {
        compose.runOnIdle {
            val expected = scopes.flatMap { scope -> listOf(DemoAction.GIVE_POTION to scope, DemoAction.TRY_ABILITY to scope) }
            assertEquals(expected, calls.actions)
            calls.assertNoOtherWork()
        }
    }

    @Test fun retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val oldA = retainEnabledClicks()
        select(state, original.copy(selectedStory = b))
        val words = "Unsent caf\u00e9 \u6f22\u5b57 \ud83c\udf3f\nThese are B dialogue words."
        tag("play-kind-dialogue").performClick()
        tag("play-input").performTextReplacement(words)
        invokeRetained(oldA)
        assertActions(calls, emptyList())
        tag("play-input").assert(hasText(words))
        tag("play-kind-dialogue").assertIsSelected()
        freshButtons()
        assertActions(calls, listOf(b))
        tag("play-input").assert(hasText(words))
        tag("play-kind-dialogue").assertIsSelected()
        val oldB = retainEnabledClicks()

        val fork = b.copy(branch = "fork")
        select(state, original.copy(selectedStory = fork))
        tag("play-input").assert(hasText(""))
        tag("play-kind-action").assertIsSelected()
        val forkWords = "SCRIPTED unsent fork dialogue"
        tag("play-kind-dialogue").performClick()
        tag("play-input").performTextReplacement(forkWords)
        invokeRetained(oldA)
        invokeRetained(oldB)
        assertActions(calls, listOf(b))
        freshButtons()
        assertActions(calls, listOf(b, fork))
        tag("play-input").assert(hasText(forkWords))
        tag("play-kind-dialogue").assertIsSelected()
        compose.runOnIdle {
            assertSame(messages, state.value.messages)
            assertEquals(7L, state.value.revision)
            assertEquals(fork, state.value.selectedStory)
        }
    }

    @Test fun persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val savedClicks = retainEnabledClicks()
        // All were captured while enabled. These invocations test retained controllers,
        // rather than force-clicking a disabled node fetched in a blocked state.
        val blocked = listOf(original.copy(busy = true), original.copy(archiveActive = true),
            original.copy(deletionActive = true), original.copy(forkActive = true),
            original.copy(creationActive = true), original.copy(recoveryRequired = true))
        for (next in blocked) {
            select(state, next)
            tag("give-potion").assertIsNotEnabled()
            tag("try-ability").assertIsNotEnabled()
            invokeRetained(savedClicks)
            assertActions(calls, emptyList())
            compose.runOnIdle { assertEquals(next, state.value) }
        }
        select(state, original.copy(selectedStory = null))
        tag("give-potion").assertIsNotEnabled()
        tag("try-ability").assertIsNotEnabled()
        invokeRetained(savedClicks)
        assertActions(calls, emptyList())

        val demo = original.copy(persistent = false, selectedStory = null, stories = emptyList(),
            textProvider = TextProvider.UNAVAILABLE)
        select(state, demo)
        invokeRetained(savedClicks)
        assertActions(calls, emptyList())
        freshButtons()
        assertActions(calls, listOf(null))
        val demoClicks = retainEnabledClicks()

        val refreshed = a.copy(title = "Refreshed A title", revision = 19)
        val current = original.copy(selectedStory = refreshed, revision = 19, textProvider = TextProvider.UNAVAILABLE)
        select(state, current)
        invokeRetained(demoClicks)
        assertActions(calls, listOf(null))
        freshButtons()
        assertActions(calls, listOf(null, refreshed))
        compose.runOnIdle {
            assertEquals(current, state.value)
            assertSame(messages, state.value.messages)
            calls.assertNoOtherWork()
        }
    }
}
