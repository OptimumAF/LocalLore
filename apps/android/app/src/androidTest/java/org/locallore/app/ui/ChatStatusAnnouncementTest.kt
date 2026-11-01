/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.PlayInput
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState
import org.locallore.app.TextProvider

/** Real composition with inert SCRIPTED snapshots; no native, speech-service or accepted-turn claim. */
class ChatStatusAnnouncementTest {
    @get:Rule val compose = createComposeRule()

    private class Calls {
        val sent = mutableListOf<Pair<PlayInput, SavedStory?>>()
        var other = 0
        fun assertQuiet() { assertTrue(sent.isEmpty()); assertEquals(0, other) }
    }

    private fun initial(): ShellState {
        val story = SavedStory("scripted-status", "main", "SCRIPTED status", 12)
        return ShellState(revision = 12, persistent = true, selectedStory = story,
            stories = listOf(story), textProvider = TextProvider.SCRIPTED,
            messages = (1..30).map {
                SceneMessage(it.toLong(), "SCRIPTED accepted row $it.\n" +
                    "The quiet harbour remains unchanged.\n".repeat(3), it % 2 == 1)
            })
    }

    private fun show(state: MutableState<ShellState>, calls: Calls) {
        compose.setContent {
            Box(Modifier.requiredSize(360.dp, 560.dp)) {
                LocalLoreScreen(state.value, { calls.other++ }, { calls.other++ },
                    { calls.other++ }, { calls.other++ }, onDiagnostics = { calls.other++ },
                    onResume = { calls.other++ }, onText = { input, scope -> calls.sent += input to scope },
                    exposeTestTags = true)
            }
        }
        compose.waitForIdle()
    }

    private fun scrollTo(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag)
    }

    private fun historyAnchor(): Float {
        compose.onNodeWithTag("message-body-10").assertIsDisplayed()
        return compose.onNodeWithTag("message-body-10").getUnclippedBoundsInRoot().top.value -
            compose.onNodeWithTag("story-list").getUnclippedBoundsInRoot().top.value
    }

    private fun assertChatAnnouncement(text: String) {
        compose.onNodeWithTag("chat-announcement", useUnmergedTree = true)
            .assertIsDisplayed().assertTextEquals(text)
            .assert(SemanticsMatcher.expectValue(SemanticsProperties.LiveRegion, LiveRegionMode.Polite))
        // Composer validation/restoration live regions are independent and remain legitimate.
        val chat = hasTestTag("chat-announcement") or hasTestTag("notice") or hasTestTag("busy-status")
        val polite = SemanticsMatcher.expectValue(SemanticsProperties.LiveRegion, LiveRegionMode.Polite)
        compose.onAllNodes(chat and polite, useUnmergedTree = true).assertCountEquals(1)
        for (tag in listOf("notice", "busy-status")) {
            compose.onAllNodesWithTag(tag, useUnmergedTree = true).fetchSemanticsNodes().forEach {
                assertFalse("Footer $tag must not duplicate the explicit chat region",
                    it.config.contains(SemanticsProperties.LiveRegion))
            }
        }
    }

    private fun changeAtAnchor(state: MutableState<ShellState>, next: ShellState, text: String, anchor: Float) {
        compose.runOnIdle { state.value = next }
        compose.waitForIdle()
        assertChatAnnouncement(text)
        assertEquals("Status changes must retain the history offset within the list", anchor, historyAnchor(), 1f)
    }

    @Test fun historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        compose.onNodeWithTag("chat-announcement").assertDoesNotExist()
        scrollTo("message-body-10").assertIsDisplayed()
        val anchor = historyAnchor()
        val preparing = original.copy(busy = true, preparingResponse = true, notice = "SCRIPTED stale accepted notice")
        changeAtAnchor(state, preparing, "Preparing local response\u2026", anchor)
        changeAtAnchor(state, preparing.copy(preparingResponse = false, checkingCancellation = true),
            "Checking cancellation\u2026", anchor)
        val accepted = original.copy(notice = "SCRIPTED response accepted locally.")
        changeAtAnchor(state, accepted, checkNotNull(accepted.notice), anchor)
        val rejected = original.copy(notice = "SCRIPTED response rejected; accepted history is unchanged.")
        changeAtAnchor(state, rejected, checkNotNull(rejected.notice), anchor)
        compose.runOnIdle { assertEquals(original.messages, state.value.messages); calls.assertQuiet() }
        // The original footer remains reachable with its exact text and tag.
        scrollTo("notice").assertTextEquals(checkNotNull(rejected.notice))
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.LiveRegion))
        compose.runOnIdle { state.value = preparing }
        compose.waitForIdle()
        scrollTo("busy-status").assertTextEquals("Preparing local response\u2026")
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.LiveRegion))
        compose.runOnIdle { calls.assertQuiet() }
    }

    @Test fun unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val draft = "Unsent caf\u00e9 \u6f22\u5b57 \ud83c\udf3f\nThese are my dialogue words."
        scrollTo("play-kind-dialogue").performClick()
        scrollTo("play-input").performTextReplacement(draft)
        scrollTo("message-body-10").assertIsDisplayed()
        val anchor = historyAnchor()
        changeAtAnchor(state, original.copy(busy = true, preparingResponse = true,
            notice = "SCRIPTED stale rejection"), "Preparing local response\u2026", anchor)
        changeAtAnchor(state, original.copy(busy = true, checkingCancellation = true),
            "Checking cancellation\u2026", anchor)
        val notice = "  SCRIPTED notice: caf\u00e9 \u6f22\u5b57 \ud83c\udf3f\n" +
            "The recorded outcome remains exactly these words. ".repeat(30) + "  "
        changeAtAnchor(state, original.copy(notice = notice), notice, anchor)
        val layouts = mutableListOf<TextLayoutResult>()
        compose.onNodeWithTag("chat-announcement").performSemanticsAction(SemanticsActions.GetTextLayoutResult) {
            assertTrue(it(layouts))
        }
        assertTrue(layouts.isNotEmpty())
        assertEquals(2, layouts.single().lineCount)
        assertTrue(layouts.single().isLineEllipsized(1))
        scrollTo("play-input").assert(hasText(draft))
        scrollTo("play-kind-dialogue").assertIsSelected()
        scrollTo("notice").assertTextEquals(notice)
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.LiveRegion))
        compose.runOnIdle { state.value = original.copy(busy = true, preparingResponse = true, notice = notice) }
        compose.waitForIdle()
        scrollTo("busy-status").assertIsDisplayed().assertTextEquals("Preparing local response\u2026")
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.LiveRegion))
        scrollTo("notice").assertIsDisplayed().assertTextEquals(notice)
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.LiveRegion))
        assertChatAnnouncement("Preparing local response\u2026")
        compose.runOnIdle { assertEquals(original.selectedStory, state.value.selectedStory); calls.assertQuiet() }
        // A status update grants no authority to carry the draft into another branch.
        val fork = checkNotNull(original.selectedStory).copy(branch = "fork")
        compose.runOnIdle { state.value = original.copy(selectedStory = fork, stories = listOf(fork), notice = "  \n\t") }
        compose.waitForIdle()
        compose.onNodeWithTag("chat-announcement").assertDoesNotExist()
        scrollTo("play-input").assert(hasText(""))
        compose.runOnIdle { assertEquals(fork, state.value.selectedStory); calls.assertQuiet() }
    }
}
