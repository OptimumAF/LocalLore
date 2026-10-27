/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.AnnotatedString
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.StoryCreationDialog

/** Real screen/dialog callbacks with synthetic state ports; not native creation or lifecycle proof. Author UNRUN. */
@RunWith(AndroidJUnit4::class)
class StoryCreationDraftFenceTest {
    @get:Rule val compose = createComposeRule()
    private val a = SavedStory("creation-draft-a", "main", "Original A", 3)
    private val b = SavedStory("creation-draft-b", "child", "Original B", 5)
    private val original = PlayInput(PlayInputKind.DIALOGUE, "SYNTHETIC unsent draft: caf\u00e9.\nKeep both fields.")
    private val example = PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira.")
    private val review = StoryCreationRequest(
        StoryCreationPreview("lantern-quay-v1", "a".repeat(64), "The Lantern Quay",
            "An original built-in starter.", "fantasy_v1", listOf("You are Rowan.")),
        "The Lantern Quay", "b".repeat(32),
    )
    private lateinit var shell: MutableState<ShellState>
    private data class Sent(val input: PlayInput, val story: String?, val branch: String?)
    private val sent = mutableListOf<Sent>()
    private var starts = 0
    private var cancelled = 0

    private data class Actions(
        val text: (AnnotatedString) -> Boolean,
        val kind: () -> Boolean,
        val example: () -> Boolean,
        val send: () -> Boolean,
    ) {
        fun invokeAll() {
            text(AnnotatedString("STALE editor action must not replace the draft"))
            kind()
            example()
            send()
        }
    }

    private fun render() {
        shell = mutableStateOf(ShellState(
            persistent = true, storageLocation = "/synthetic/creation-draft-fence",
            selectedStory = a, stories = listOf(a, b), revision = a.revision,
            textProvider = TextProvider.SCRIPTED,
        ))
        compose.setContent {
            LocalLoreScreen(
                state = shell.value,
                onAction = {}, onMode = {}, onCancel = {},
                onReset = { starts++; shell.value = shell.value.copy(creationActive = true) },
                onText = { input, expected -> sent += Sent(input, expected?.story, expected?.branch) },
                // Deliberately read the live state at invocation, not a captured render value.
                // This is the UI port contract used by Main's synchronous ViewModel gate.
                draftInteractionAllowed = { expected ->
                    val current = shell.value
                    val scope = current.selectedStory?.let { PlayDraftScope(it.story, it.branch) }
                    expected == scope && !current.busy && !current.archiveActive &&
                        !current.deletionActive && !current.forkActive && !current.creationActive &&
                        !current.recoveryRequired && current.selectedStory != null &&
                        current.textProvider != TextProvider.UNAVAILABLE
                },
                overlay = {
                    StoryCreationDialog(
                        StoryCreationUiState(visible = shell.value.creationActive, review = review),
                        onDismiss = { cancelled++; shell.value = shell.value.copy(creationActive = false) },
                        onTitle = { _, _ -> }, onConfirm = { fail("This fixture never consents to creation") },
                    )
                },
            )
        }
        compose.waitForIdle()
    }

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    private fun draft(input: PlayInput) {
        tag("play-kind-${input.kind.wire}").performClick()
        tag("play-input").performTextReplacement(input.text)
    }

    private fun retain(kind: PlayInputKind = PlayInputKind.ACTION): Actions = Actions(
        text = checkNotNull(tag("play-input").fetchSemanticsNode().config[SemanticsActions.SetText].action),
        kind = checkNotNull(tag("play-kind-${kind.wire}").fetchSemanticsNode().config[SemanticsActions.OnClick].action),
        example = checkNotNull(tag("play-example").fetchSemanticsNode().config[SemanticsActions.OnClick].action),
        send = checkNotNull(tag("play-send").assertIsEnabled().fetchSemanticsNode().config[SemanticsActions.OnClick].action),
    )

    private fun assertDraft(input: PlayInput, marker: String) {
        try {
            tag("play-input").assert(hasText(input.text))
            tag("play-kind-${input.kind.wire}").assertIsSelected()
        } catch (failure: AssertionError) {
            throw AssertionError(marker, failure)
        }
    }

    private fun noSend() = compose.runOnIdle { assertTrue("No explicit accepted Send was allowed", sent.isEmpty()) }

    private fun closeReview() {
        compose.onNodeWithTag("story-creation-cancel").assertIsEnabled().performClick()
        compose.runOnIdle { assertFalse(shell.value.creationActive) }
        compose.onNodeWithTag("story-creation-dialog").assertDoesNotExist()
    }

    @Test fun sameScopeReviewAndCancelPreserveDraftAgainstAllRetainedEditorActions() {
        render(); draft(original)
        val retained = retain()
        compose.runOnIdle { shell.value = shell.value.copy(creationActive = true) }
        compose.onNodeWithTag("story-creation-dialog").assertIsDisplayed()
        compose.runOnIdle { retained.invokeAll() }
        noSend()
        closeReview()
        assertDraft(original, "review_cancel_preserves_original_draft")
        compose.runOnIdle {
            assertEquals(a, shell.value.selectedStory)
            assertEquals(listOf(a, b), shell.value.stories)
            assertEquals(1, cancelled)
        }
        noSend()
    }

    @Test fun idleRetainedControlsReallyEditBothFieldsAndSendOnlyOnExplicitAction() {
        render(); draft(PlayInput(PlayInputKind.ACTION, "SYNTHETIC initial enabled input"))
        val retained = retain(PlayInputKind.DIALOGUE)
        val edited = PlayInput(PlayInputKind.DIALOGUE, "SYNTHETIC idle control: snow \u96ea.")
        compose.runOnIdle {
            assertTrue(retained.kind())
            assertTrue(retained.text(AnnotatedString(edited.text)))
            assertTrue(sent.isEmpty())
            assertTrue(retained.send())
        }
        assertDraft(edited, "idle_controls_are_not_vacuously_disabled")
        compose.runOnIdle { assertEquals(listOf(Sent(edited, a.story, a.branch)), sent); sent.clear() }
        compose.runOnIdle { assertTrue(retained.example()); assertTrue(sent.isEmpty()) }
        assertDraft(example, "idle_full_preset_still_replaces_input")
        tag("play-send").performClick()
        compose.runOnIdle { assertEquals(listOf(Sent(example, a.story, a.branch)), sent) }
    }

    @Test fun oldScopeActionsCannotRetargetAnotherDraftAfterTheReviewCloses() {
        render(); draft(original)
        val old = retain()
        compose.runOnIdle { shell.value = shell.value.copy(creationActive = true) }
        compose.onNodeWithTag("story-creation-dialog").assertIsDisplayed()
        closeReview()
        compose.runOnIdle { shell.value = shell.value.copy(selectedStory = b, revision = b.revision) }
        compose.waitForIdle()
        val current = PlayInput(PlayInputKind.DIALOGUE, "SYNTHETIC separate B draft")
        draft(current)
        compose.runOnIdle { old.invokeAll() }
        assertDraft(current, "closed_review_does_not_retarget_A_actions_to_B")
        noSend()
        tag("play-send").performClick()
        compose.runOnIdle { assertEquals(listOf(Sent(current, b.story, b.branch)), sent) }
    }

    @Test fun openingReviewAndInvokingOldActionsBeforeRecompositionCannotEditOrSend() {
        render()
        // Retain the real New story semantics before scrolling to the editor. No direct
        // controller invocation, fake editor, or idle/recomposition occurs between these actions.
        val start = checkNotNull(tag("reset-demo").fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        draft(original)
        val old = retain()
        compose.runOnIdle {
            assertTrue(start())
            assertEquals(1, starts)
            assertTrue(shell.value.creationActive)
            old.invokeAll()
            assertTrue("same_frame_review_blocks_retained_send", sent.isEmpty())
        }
        compose.onNodeWithTag("story-creation-dialog").assertIsDisplayed()
        closeReview()
        assertDraft(original, "same_frame_review_preserves_original_draft")
        noSend()
    }
}
