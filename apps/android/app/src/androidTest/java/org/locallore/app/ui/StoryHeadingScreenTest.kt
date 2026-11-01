/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.PlayInput
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState
import org.locallore.app.TextProvider

/** Real UI with inert SCRIPTED snapshots, not native authoring, accepted-turn or device evidence. */
class StoryHeadingScreenTest {
    @get:Rule val compose = createComposeRule()

    private val orchard = SavedStory("authored-orchard", "main", "Copper Orchard", 7)
    private val pier = SavedStory("authored-pier", "main", "North Pier", 12)
    private val accepted = listOf(
        SceneMessage(1, "SCRIPTED original words: Lantern Quay, Mira and Oren are valid transcript text.", true),
        SceneMessage(2, "SCRIPTED accepted narration preserves those words, not heading authority.", false),
    )

    private class Calls {
        var other = 0
        val sent = mutableListOf<Pair<PlayInput, SavedStory?>>()
        fun assertQuiet() { assertEquals(0, other); assertTrue(sent.isEmpty()) }
    }

    private fun initial() = ShellState(revision = 12, persistent = true, selectedStory = pier,
        stories = listOf(orchard, pier), textProvider = TextProvider.SCRIPTED, messages = accepted,
        storageLocation = "D:/not-a-world-location/Lantern-Quay.sqlite")

    private fun show(state: MutableState<ShellState>, calls: Calls) {
        compose.setContent {
            Box(Modifier.requiredSize(360.dp, 620.dp)) {
                LocalLoreScreen(state.value, { calls.other++ }, { calls.other++ },
                    { calls.other++ }, { calls.other++ }, onDiagnostics = { calls.other++ },
                    onResume = { calls.other++ }, onRecover = { calls.other++ },
                    onText = { input, story -> calls.sent += input to story }, exposeTestTags = true)
            }
        }
        compose.waitForIdle()
    }

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    private fun intro(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNode(hasTestTag(name) and hasAnyAncestor(hasTestTag("story-heading")),
            useUnmergedTree = true)
    }

    private fun savedIntro(title: String) {
        intro("story-heading-kind").assertTextEquals("Saved story")
        intro("story-heading-title").assertTextEquals(title)
            .assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading))
        intro("story-heading-introduction").assertTextEquals("Choose what to try or say next.")
    }

    private fun select(state: MutableState<ShellState>, next: ShellState) {
        compose.runOnIdle { state.value = next }
        compose.waitForIdle()
    }

    @Test fun selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        // The selected second entry is authoritative, even with a different first catalog title.
        savedIntro("North Pier")
        val renamedFork = pier.copy(branch = "fork", title = "\u00celes du Nord \u6f22\u5b57", revision = 13)
        select(state, original.copy(selectedStory = renamedFork, revision = 13))
        savedIntro("\u00celes du Nord \u6f22\u5b57")
        select(state, original.copy(selectedStory = orchard, revision = 7))
        savedIntro("Copper Orchard")
        // These legitimate names remain in accepted messages; only the intro is neutralized.
        tag("message-body-1").assertTextEquals(accepted[0].text)
        tag("message-body-2").assertTextEquals(accepted[1].text)
        compose.runOnIdle { assertSame(accepted, state.value.messages); calls.assertQuiet() }

        select(state, original.copy(selectedStory = null))
        tag("empty-library").assertIsDisplayed()
        compose.onNodeWithTag("story-heading", useUnmergedTree = true).assertDoesNotExist()
        compose.onNodeWithTag("story-heading-title", useUnmergedTree = true).assertDoesNotExist()
        compose.onNodeWithTag("story-heading-introduction", useUnmergedTree = true).assertDoesNotExist()

        // Misleading saved metadata in nonpersistent demo mode must not replace the demo scene.
        select(state, original.copy(persistent = false))
        intro("story-heading-kind").assertTextEquals("Demo scene")
        intro("story-heading-title").assertTextEquals("Lantern Quay")
            .assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading))
        intro("story-heading-introduction").assertTextEquals(
            "The tide laps below the quay. Mira waits beside you. Oren\u2019s borrowed brass key rests in your satchel.")
        compose.runOnIdle {
            assertSame(accepted, state.value.messages)
            assertEquals(12L, state.value.revision)
            calls.assertQuiet()
        }
    }

    @Test fun titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits() {
        val original = initial()
        val state = mutableStateOf(original)
        val calls = Calls()
        show(state, calls)
        val words = "Unsent caf\u00e9 \u6f22\u5b57 \ud83c\udf3f\nThese words stay in this scope."
        tag("play-kind-dialogue").performClick()
        tag("play-input").performTextReplacement(words)
        val renamed = pier.copy(title = "North Pier: a revised title")
        select(state, original.copy(selectedStory = renamed))
        savedIntro("North Pier: a revised title")
        tag("play-input").assert(hasText(words))
        tag("play-kind-dialogue").assertIsSelected()
        val oldEdit = checkNotNull(tag("play-input").fetchSemanticsNode().config[SemanticsActions.SetText].action)
        val oldSend = checkNotNull(tag("play-send").fetchSemanticsNode().config[SemanticsActions.OnClick].action)

        val fork = renamed.copy(branch = "fork")
        select(state, original.copy(selectedStory = fork))
        savedIntro("North Pier: a revised title")
        tag("play-input").assert(hasText(""))
        tag("play-kind-action").assertIsSelected()
        val forkWords = "SCRIPTED unsent fork-only dialogue"
        tag("play-kind-dialogue").performClick()
        tag("play-input").performTextReplacement(forkWords)
        compose.runOnIdle {
            oldEdit(AnnotatedString("STALE main edit"))
            oldSend()
        }
        tag("play-input").assert(hasText(forkWords))
        tag("play-kind-dialogue").assertIsSelected()
        val forkEdit = checkNotNull(tag("play-input").fetchSemanticsNode().config[SemanticsActions.SetText].action)
        val forkSend = checkNotNull(tag("play-send").fetchSemanticsNode().config[SemanticsActions.OnClick].action)

        select(state, original.copy(selectedStory = orchard, revision = 7))
        savedIntro("Copper Orchard")
        tag("play-input").assert(hasText(""))
        tag("play-kind-action").assertIsSelected()
        val orchardWords = "SCRIPTED fresh Orchard draft"
        tag("play-input").performTextReplacement(orchardWords)
        compose.runOnIdle {
            oldEdit(AnnotatedString("STALE main edit across story"))
            forkEdit(AnnotatedString("STALE fork edit across story"))
            oldSend()
            forkSend()
        }
        tag("play-input").assert(hasText(orchardWords))
        tag("play-kind-action").assertIsSelected()
        compose.runOnIdle {
            assertSame(accepted, state.value.messages)
            assertEquals(7L, state.value.revision)
            assertEquals(orchard, state.value.selectedStory)
            calls.assertQuiet()
        }
    }
}
