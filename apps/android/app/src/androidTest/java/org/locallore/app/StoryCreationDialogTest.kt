/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.referentialEqualityPolicy
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.AnnotatedString
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.StoryCreationDialog

/** Actual dialog semantics only; native creation/Activity/lifecycle evidence is separate. Author UNRUN. */
class StoryCreationDialogTest {
    @get:Rule val compose = createComposeRule()
    private val preview = StoryCreationPreview("lantern-quay-v1", "a".repeat(64), "The Lantern Quay",
        "An original built-in starter.", "fantasy_v1", listOf("You are Rowan.", "You carry one potion."))
    private val request = StoryCreationRequest(preview, preview.defaultTitle, "b".repeat(32))

    @Test fun humanStarterReviewAndTitleEditsNeverCreateUntilTheExplicitButton() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = request))
        val edits = mutableListOf<Pair<StoryCreationRequest, String>>()
        val confirmed = mutableListOf<StoryCreationRequest>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { expected, title ->
                edits += expected to title
                state.value = state.value.copy(review = expected.copy(title = title))
            }, confirmed::add)
        } }
        compose.onNodeWithText("Start a story").assertIsDisplayed()
        compose.onNodeWithText(preview.description).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Rules · Fantasy").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("You carry one potion.").performScrollTo().assertIsDisplayed()
        for (hidden in listOf(preview.template, preview.seedSha256, request.creationId, preview.profile)) {
            compose.onAllNodes(hasText(hidden, substring = true)).assertCountEquals(0)
        }
        compose.onNodeWithTag("story-creation-title").performScrollTo().performTextReplacement("My new title")
        compose.runOnIdle {
            assertTrue(confirmed.isEmpty())
            assertEquals("My new title", edits.last().second)
            assertSame(preview, edits.last().first.preview)
        }
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled().performClick()
        compose.runOnIdle {
            assertSame(state.value.review, confirmed.single())
            assertEquals("My new title", confirmed.single().title)
        }
    }

    @Test fun invalidLoadingAndClosingStatesCannotOfferCreationButCanCancelReadWork() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = request.copy(title = " invalid")))
        var cancelled = 0
        var created = 0
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, { cancelled++ }, { _, _ -> }, { created++ })
        } }
        compose.onNodeWithTag("story-creation-title-error").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("story-creation-cancel").assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(1, cancelled); assertEquals(0, created); state.value = StoryCreationUiState(visible = true, busy = true) }
        compose.onNodeWithText("Loading starter…").assertIsDisplayed()
        compose.onNodeWithTag("story-creation-confirm").assertDoesNotExist()
        compose.onNodeWithTag("story-creation-title").assertDoesNotExist()
        compose.onNodeWithTag("story-creation-cancel").assertIsEnabled()
        compose.runOnIdle { state.value = state.value.copy(closing = true, notice = "Finishing local work.") }
        compose.onNodeWithTag("story-creation-cancel").assertIsNotEnabled()
        compose.runOnIdle { assertEquals(0, created) }
    }

    @Test fun retainedConsentCannotBorrowAnEditedTitleAfterRecomposition() {
        assertRetainedButton(request.copy(title = "A replacement title"))
    }

    @Test fun retainedConsentCannotBorrowAnEqualButDifferentRequestObject() {
        val replacement = request.copy()
        assertEquals(request, replacement); assertNotSame(request, replacement)
        assertRetainedButton(replacement)
    }

    @Test fun retainedTitleActionCannotRetargetAReopenedReview() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = request))
        val edits = mutableListOf<Pair<StoryCreationRequest, String>>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { expected, text -> edits += expected to text }, {})
        } }
        val retained = checkNotNull(compose.onNodeWithTag("story-creation-title").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.SetText].action)
        val replacement = request.copy(preview = preview.copy(), creationId = "c".repeat(32))
        compose.runOnIdle { state.value = state.value.copy(review = replacement) }
        compose.waitForIdle()
        compose.runOnIdle {
            retained(AnnotatedString("Retained old review edit"))
            assertTrue("Retained title action borrowed the reopened review", edits.all { it.first === request })
            edits.clear()
        }
        compose.onNodeWithTag("story-creation-title").performScrollTo().performTextReplacement("New review title")
        compose.runOnIdle {
            assertSame(replacement, edits.last().first)
            assertEquals("New review title", edits.last().second)
        }
    }

    private fun assertRetainedButton(replacement: StoryCreationRequest) {
        // Equal DTOs with different references must still reach the real dialog in this oracle.
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = request), referentialEqualityPolicy())
        val confirmed = mutableListOf<StoryCreationRequest>()
        compose.setContent { MaterialTheme { StoryCreationDialog(state.value, {}, { _, _ -> }, confirmed::add) } }
        val retained = checkNotNull(compose.onNodeWithTag("story-creation-confirm").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        compose.runOnIdle { state.value = state.value.copy(review = replacement) }
        compose.waitForIdle()
        compose.runOnIdle { retained() }
        compose.runOnIdle {
            assertTrue("Retained button borrowed a different rendered request", confirmed.all { it === request })
            confirmed.clear()
        }
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().performClick()
        compose.runOnIdle { assertSame(replacement, confirmed.single()) }
    }
}
