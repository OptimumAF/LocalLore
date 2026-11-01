/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.PlayInput
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState
import org.locallore.app.TextProvider

/** Actual shell navigation with synthetic accepted rows; no native store, model, or turn writes. */
class TranscriptRolloverUiTest {
    @get:Rule val compose = createComposeRule()

    private class Calls {
        val sent = mutableListOf<Pair<PlayInput, SavedStory?>>()
        var actions = 0
        var modes = 0
        var cancels = 0
        var resets = 0
        var diagnostics = 0

        fun assertQuiet() {
            assertTrue(sent.isEmpty())
            assertEquals(0, actions)
            assertEquals(0, modes)
            assertEquals(0, cancels)
            assertEquals(0, resets)
            assertEquals(0, diagnostics)
        }
    }

    private fun window(first: Int, last: Int) = (first..last).map { id ->
        SceneMessage(id.toLong(), "SCRIPTED accepted row $id.\n" +
            "The survey quay stays unchanged.\n".repeat(3), id % 2 == 1)
    }

    private fun initial(): ShellState {
        val story = SavedStory("rollover-story", "main", "SCRIPTED rolling transcript", 20)
        return ShellState(revision = 20, potionOwner = "Mira", persistent = true,
            selectedStory = story, stories = listOf(story), textProvider = TextProvider.SCRIPTED,
            messages = window(1, 40))
    }

    private fun rolled(original: ShellState): ShellState {
        val story = checkNotNull(original.selectedStory).copy(revision = 21)
        return original.copy(revision = 21, selectedStory = story, stories = listOf(story),
            messages = window(3, 42))
    }

    private fun show(state: MutableState<ShellState>, calls: Calls) {
        compose.setContent {
            Box(Modifier.requiredSize(360.dp, 560.dp)) {
                LocalLoreScreen(state.value, { calls.actions++ }, { calls.modes++ },
                    { calls.cancels++ }, { calls.resets++ }, onDiagnostics = { calls.diagnostics++ },
                    onText = { input, story -> calls.sent += input to story }, exposeTestTags = true)
            }
        }
        compose.waitForIdle()
    }

    private fun scrollTo(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag)
    }

    private fun awaitVisible(tag: String) {
        compose.waitUntil(5_000) { compose.onNodeWithTag(tag).isDisplayed() }
        compose.onNodeWithTag(tag).assertIsDisplayed()
    }

    @Test fun readerBelowFortyRowTailSeesRolledReplyWithoutScrollingOrSendingDraft() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val draft = "SCRIPTED unsent dialogue survives the rolling window."
        scrollTo("play-kind-dialogue").performClick()
        scrollTo("play-input").performTextReplacement(draft)
        scrollTo("play-send").assertIsEnabled()
        compose.waitForIdle()
        compose.onNodeWithTag("message-body-40").assertIsNotDisplayed()
        val after = rolled(original)
        assertEquals(40, original.messages.size)
        assertEquals(40, after.messages.size)
        compose.runOnIdle { state.value = after }

        // No test scroll or Latest click after publication: production must reveal row42.
        awaitVisible("message-body-42")
        compose.runOnIdle { assertSame(after, state.value); calls.assertQuiet() }
        scrollTo("play-input").assert(hasText(draft))
        scrollTo("play-kind-dialogue").assertIsSelected()
        compose.runOnIdle { assertSame(after, state.value); calls.assertQuiet() }
    }

    @Test fun historyReaderKeepsSurvivingRowUntilLatestAndKeepsOriginalDraft() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val draft = "SCRIPTED history-reader action remains unsent."
        scrollTo("play-input").performTextReplacement(draft)
        scrollTo("message-body-10").assertIsDisplayed()
        compose.waitForIdle()
        val after = rolled(original)
        compose.runOnIdle { state.value = after }
        compose.waitForIdle()

        // The retained row has the same stable key in both forty-row windows.
        compose.onNodeWithTag("message-body-10").assertIsDisplayed()
        compose.onNodeWithTag("message-body-42").assertIsNotDisplayed()
        compose.runOnIdle { assertSame(after, state.value); calls.assertQuiet() }
        compose.onNodeWithTag("transcript-latest").assertIsDisplayed().performClick()
        awaitVisible("message-body-42")
        scrollTo("play-input").assert(hasText(draft))
        scrollTo("play-kind-action").assertIsSelected()
        compose.runOnIdle { assertSame(after, state.value); calls.assertQuiet() }
    }
}
