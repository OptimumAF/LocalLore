/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

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
import org.locallore.app.ui.LocalLoreScreen

/** Real rendered navigation with inert accepted snapshots; no model, JNI, or save authority. */
class TranscriptFollowScreenTest {
    @get:Rule val compose = createComposeRule()

    private class Calls {
        val sent = mutableListOf<Pair<PlayInput, SavedStory?>>()
        var actions = 0; var modes = 0; var cancels = 0; var resets = 0; var diagnostics = 0
        fun assertQuiet() {
            assertTrue(sent.isEmpty())
            assertEquals(0, actions); assertEquals(0, modes); assertEquals(0, cancels)
            assertEquals(0, resets); assertEquals(0, diagnostics)
        }
    }

    private fun history(count: Int) = (1..count).map { index ->
        SceneMessage(index.toLong(), "SCRIPTED accepted row $index.\n" +
            "The quiet quay remains unchanged.\n".repeat(3), index % 2 == 1)
    }

    private fun initial(messages: List<SceneMessage>): ShellState {
        val story = SavedStory("scripted-transcript", "main", "SCRIPTED transcript", 9)
        return ShellState(revision = 9, potionOwner = "Mira", persistent = true,
            selectedStory = story, stories = listOf(story), textProvider = TextProvider.SCRIPTED,
            messages = messages)
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

    private fun scrollTo(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    private fun awaitVisible(name: String) {
        compose.waitUntil(5_000) {
            compose.onNodeWithTag(name).isDisplayed()
        }
        compose.onNodeWithTag(name).assertIsDisplayed()
    }

    @Test fun readingHistoryKeepsPositionUntilLatestAndPreservesTheUnsentDialogue() {
        val original = initial(history(24))
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val draft = "SCRIPTED unsent dialogue remains mine."
        scrollTo("play-kind-dialogue").performClick()
        scrollTo("play-input").performTextReplacement(draft)
        scrollTo("message-body-1").assertIsDisplayed()
        compose.waitForIdle()
        val reply = SceneMessage(100, "SCRIPTED newly accepted reply", false)
        compose.runOnIdle { state.value = original.copy(messages = original.messages + reply) }
        compose.waitForIdle()
        // No test scrolling after append: the reader's actual viewport must stay put.
        compose.onNodeWithTag("message-body-1").assertIsDisplayed()
        compose.onNodeWithTag("message-body-100").assertIsNotDisplayed()
        compose.onNodeWithTag("transcript-latest").assertIsDisplayed().performClick()
        awaitVisible("message-body-100")
        scrollTo("play-input").assert(hasText(draft))
        scrollTo("play-kind-dialogue").assertIsSelected()
        compose.runOnIdle {
            assertEquals(original.copy(messages = original.messages + reply), state.value)
            calls.assertQuiet()
        }
    }

    @Test fun seeingOnlyTheHeadOfALongTailDoesNotAuthorizeFollowingAnAppend() {
        val longReply = SceneMessage(1, (1..150).joinToString("\n") {
            "SCRIPTED long reply paragraph $it: read every line before following."
        }, false)
        val original = initial(listOf(longReply))
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        // Active saved transcript begins after brand/scene/state; land at the tall row's head.
        compose.onNodeWithTag("story-list").performScrollToIndex(3)
        compose.onNodeWithTag("message-body-1").assertIsDisplayed()
        compose.waitForIdle()
        val reply = SceneMessage(2, "SCRIPTED reply after the long unread tail", false)
        compose.runOnIdle { state.value = original.copy(messages = listOf(longReply, reply)) }
        compose.waitForIdle()
        compose.onNodeWithTag("message-body-1").assertIsDisplayed()
        compose.onNodeWithTag("message-body-2").assertIsNotDisplayed()
        compose.onNodeWithTag("transcript-latest").assertIsDisplayed()
        compose.runOnIdle { calls.assertQuiet() }
    }

    @Test fun readingTheComposerPastTheTailFollowsTheNewReplyWithoutSubmittingTheDraft() {
        val original = initial(history(18))
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val draft = "SCRIPTED action typed below the accepted transcript."
        scrollTo("play-input").performTextReplacement(draft)
        scrollTo("play-send").assertIsEnabled()
        compose.waitForIdle()
        val reply = SceneMessage(200, "SCRIPTED footer-reader append target", false)
        compose.runOnIdle { state.value = original.copy(messages = original.messages + reply) }
        // Actual production effect must navigate; the test does not scroll to the target.
        awaitVisible("message-body-200")
        compose.waitForIdle()
        compose.onNodeWithTag("transcript-latest").assertDoesNotExist()
        scrollTo("play-input").assert(hasText(draft))
        compose.runOnIdle {
            assertEquals(original.copy(messages = original.messages + reply), state.value)
            calls.assertQuiet()
        }
    }

    @Test fun retainedLatestCallbackCannotNavigateAnotherBranchWithReusedMessageIds() {
        val original = initial(history(24))
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        scrollTo("play-input").performTextReplacement("SCRIPTED main-branch draft")
        scrollTo("message-body-1").assertIsDisplayed()
        compose.waitForIdle()
        val reply = SceneMessage(300, "SCRIPTED main tail", false)
        compose.runOnIdle { state.value = original.copy(messages = original.messages + reply) }
        compose.waitForIdle()
        val retainedClick = checkNotNull(compose.onNodeWithTag("transcript-latest")
            .assertIsDisplayed().fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        val other = checkNotNull(original.selectedStory).copy(branch = "fork")
        val replacement = original.copy(selectedStory = other, stories = listOf(other),
            messages = original.messages + reply.copy(text = "SCRIPTED different branch tail, reused ID"))
        compose.runOnIdle { state.value = replacement }
        compose.waitForIdle()
        scrollTo("message-body-1").assertIsDisplayed()
        compose.runOnIdle { retainedClick() }
        compose.waitForIdle()
        compose.onNodeWithTag("message-body-1").assertIsDisplayed()
        compose.onNodeWithTag("message-body-300").assertIsNotDisplayed()
        compose.onNodeWithTag("transcript-latest").assertIsDisplayed()
        scrollTo("play-input").assert(hasText(""))
        compose.runOnIdle { assertSame(replacement, state.value); calls.assertQuiet() }
    }
}
