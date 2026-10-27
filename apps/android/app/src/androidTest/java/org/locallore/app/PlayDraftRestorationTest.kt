/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.StateRestorationTester
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.AnnotatedString
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen

/** Production screen saved-instance simulation, not Activity/process-death or canon proof. UNRUN by author. */
@RunWith(AndroidJUnit4::class)
class PlayDraftRestorationTest {
    @get:Rule val compose = createComposeRule()
    private val a = SavedStory("synthetic-draft-a", "main", "Draft A", 0)
    private val child = a.copy(branch = "child", revision = 3)
    private val b = SavedStory("synthetic-draft-b", "main", "Draft B", 5)
    private lateinit var shell: MutableState<ShellState>
    private data class Sent(val input: PlayInput, val story: String?, val branch: String?)
    private val sent = mutableListOf<Sent>()

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    private fun render(): StateRestorationTester {
        shell = mutableStateOf(ShellState(
            persistent = true,
            storageLocation = "/synthetic/draft-restoration",
            stories = listOf(a, b),
            selectedStory = a,
            revision = a.revision,
            textProvider = TextProvider.SCRIPTED,
        ))
        val restoration = StateRestorationTester(compose)
        restoration.setContent {
            LocalLoreScreen(
                state = shell.value,
                onAction = {}, onMode = {}, onCancel = {}, onReset = {},
                onText = { input, expected -> sent += Sent(input, expected?.story, expected?.branch) },
            )
        }
        compose.waitForIdle()
        return restoration
    }

    private fun select(story: SavedStory?, busy: Boolean = false, recovery: Boolean = false) {
        compose.runOnIdle {
            shell.value = shell.value.copy(
                selectedStory = story, revision = story?.revision ?: shell.value.revision,
                busy = busy, recoveryRequired = recovery,
            )
        }
        compose.waitForIdle()
    }

    private fun draft(kind: PlayInputKind, text: String) {
        tag("play-kind-${kind.wire}").performClick()
        tag("play-input").performTextReplacement(text)
    }

    private fun assertDraft(kind: PlayInputKind, text: String) {
        tag("play-input").assert(hasText(text))
        tag("play-kind-${kind.wire}").assertIsSelected()
    }

    private fun noSend() { compose.runOnIdle { assertTrue(sent.isEmpty()) } }

    @Test fun exactKindAndTextRestoreAcrossSameScopeHeadsAndOnlyExplicitSendDispatches() {
        val restoration = render()
        val input = PlayInput(PlayInputKind.DIALOGUE,
            "SYNTHETIC draft: café 🧭\nNo accepted event.\tOriginal spacing.")
        draft(input.kind, input.text)
        noSend()
        restoration.emulateSavedInstanceStateRestore()
        assertDraft(input.kind, input.text)
        noSend()
        select(a.copy(title = "New title", revision = 9))
        assertDraft(input.kind, input.text)
        restoration.emulateSavedInstanceStateRestore()
        assertDraft(input.kind, input.text)
        compose.onNodeWithTag("play-draft-not-restored").assertDoesNotExist()
        noSend()
        tag("play-send").assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(listOf(Sent(input, a.story, a.branch)), sent) }
    }

    @Test fun unresolvedAsyncAndRecoveryHideSavedPayloadUntilOnlyItsExactScopeReturns() {
        val restoration = render()
        for ((index, flags) in listOf(true to false, false to true).withIndex()) {
            val words = "SYNTHETIC hidden pending draft $index"
            draft(PlayInputKind.DIALOGUE, words)
            select(null, busy = flags.first, recovery = flags.second)
            restoration.emulateSavedInstanceStateRestore()
            assertDraft(PlayInputKind.ACTION, "")
            tag("play-send").assertIsNotEnabled()
            compose.onNodeWithTag("play-draft-not-restored").assertDoesNotExist()
            noSend()
            select(a.copy(revision = index.toLong() + 1))
            assertDraft(PlayInputKind.DIALOGUE, words)
            noSend()
        }
        select(null, busy = true)
        restoration.emulateSavedInstanceStateRestore()
        select(b)
        assertDraft(PlayInputKind.ACTION, "")
        select(a)
        assertDraft(PlayInputKind.ACTION, "")
        noSend()
    }

    @Test fun settledBranchAndStorySwitchesDiscardTheSingleDraftWithoutPerStoryResurrection() {
        render()
        draft(PlayInputKind.DIALOGUE, "SYNTHETIC A draft")
        select(child)
        assertDraft(PlayInputKind.ACTION, "")
        draft(PlayInputKind.DIALOGUE, "SYNTHETIC child draft")
        select(b)
        assertDraft(PlayInputKind.ACTION, "")
        draft(PlayInputKind.DIALOGUE, "SYNTHETIC B draft")
        select(a)
        assertDraft(PlayInputKind.ACTION, "")
        noSend()
    }

    @Test fun retainedEditAndSendActionsCannotChangeOrSubmitTheNewScopeDraft() {
        render()
        draft(PlayInputKind.DIALOGUE, "SYNTHETIC old A text")
        val retainedEdit = checkNotNull(tag("play-input").fetchSemanticsNode().config[SemanticsActions.SetText].action)
        val retainedSend = checkNotNull(tag("play-send").fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        select(b)
        val words = "SYNTHETIC fresh B text"
        draft(PlayInputKind.DIALOGUE, words)
        compose.runOnIdle {
            retainedEdit(AnnotatedString("STALE A callback must not become B text"))
            retainedSend()
        }
        assertDraft(PlayInputKind.DIALOGUE, words)
        noSend()
        tag("play-send").performClick()
        compose.runOnIdle {
            assertEquals(listOf(Sent(PlayInput(PlayInputKind.DIALOGUE, words), b.story, b.branch)), sent)
        }
    }

    @Test fun saveBoundUsesUtf8BytesAndDoesNotRelaxTheSmallerSendBound() {
        val restoration = render()
        val exact = "é".repeat(4096)
        assertEquals(8192, exact.toByteArray(Charsets.UTF_8).size)
        draft(PlayInputKind.DIALOGUE, exact)
        tag("play-send").assertIsNotEnabled()
        restoration.emulateSavedInstanceStateRestore()
        assertDraft(PlayInputKind.DIALOGUE, exact)
        compose.onNodeWithTag("play-draft-not-restored").assertDoesNotExist()
        tag("play-send").assertIsNotEnabled()
        noSend()
        val sendBoundary = "é".repeat(1024)
        assertEquals(2048, sendBoundary.toByteArray(Charsets.UTF_8).size)
        tag("play-input").performTextReplacement(sendBoundary)
        tag("play-send").assertIsEnabled()
        tag("play-input").performTextReplacement(sendBoundary + "x")
        tag("play-send").assertIsNotEnabled()
        noSend()
    }

    @Test fun unsafeSavedPayloadIsOmittedWholeWithPersistentReentryNoticeAndOriginalKind() {
        val restoration = render()
        val unsafe = listOf("é".repeat(4096) + "x", "\uD800unpaired high", "unpaired low\uDC00")
        assertEquals(8193, unsafe.first().toByteArray(Charsets.UTF_8).size)
        for ((index, words) in unsafe.withIndex()) {
            draft(PlayInputKind.DIALOGUE, words)
            // Saving must omit unsafe text, not alter/truncate the live edit.
            assertDraft(PlayInputKind.DIALOGUE, words)
            tag("play-send").assertIsNotEnabled()
            if (index == unsafe.lastIndex) select(null, recovery = true)
            restoration.emulateSavedInstanceStateRestore()
            if (index == unsafe.lastIndex) {
                assertDraft(PlayInputKind.ACTION, "")
                compose.onNodeWithTag("play-draft-not-restored").assertDoesNotExist()
                select(a)
            }
            assertDraft(PlayInputKind.DIALOGUE, "")
            tag("play-draft-not-restored").assertIsDisplayed()
            tag("play-send").assertIsNotEnabled()
            restoration.emulateSavedInstanceStateRestore()
            assertDraft(PlayInputKind.DIALOGUE, "")
            tag("play-draft-not-restored").assertIsDisplayed()
            noSend()
            tag("play-input").performTextReplacement("SYNTHETIC explicit re-entry")
            compose.onNodeWithTag("play-draft-not-restored").assertDoesNotExist()
            tag("play-send").assertIsEnabled()
            noSend()
        }
    }
}
