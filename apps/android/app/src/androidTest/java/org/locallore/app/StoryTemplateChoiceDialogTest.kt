/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.StoryCreationDialog

/** Authored chooser semantics checks; compile-only until a fresh Android cohort is admitted. */
class StoryTemplateChoiceDialogTest {
    @get:Rule val compose = createComposeRule()
    private val quay = StoryCreationPreview(DEFAULT_STORY_TEMPLATE, "a".repeat(64), "Lantern Quay",
        "Original quay setting.", "fantasy_v1", listOf("You carry one potion."))
    private val harbor = StoryCreationPreview("bracken-harbor-v1", "b".repeat(64), "Bracken Harbor",
        "Original harbor setting.", "narrative_v1", listOf("You carry a folded chart."))
    private val options = listOf(quay.option(), harbor.option())
    private val original = StoryCreationRequest(quay, quay.defaultTitle, "c".repeat(32))

    @Test fun explicitChoiceShowsNarrativeFactsAndDoesNotCreateUntilNewConsent() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = original, templates = options))
        val confirmations = mutableListOf<StoryCreationRequest>()
        val choices = mutableListOf<Pair<StoryCreationRequest, StoryTemplateOption>>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, confirmations::add,
                onTemplate = { request, option ->
                    choices += request to option
                    state.value = state.value.copy(review = request.copy(preview = harbor, title = harbor.defaultTitle))
                })
        } }
        compose.onNodeWithTag("story-template-lantern-quay-v1").performScrollTo().assertIsSelected()
        compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().assertIsNotSelected().performClick()
        compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().assertIsSelected()
        compose.onNodeWithText("Rules · Narrative").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("You carry a folded chart.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("You carry one potion.").assertDoesNotExist()
        compose.runOnIdle {
            assertTrue(confirmations.isEmpty())
            assertSame(original, choices.single().first)
            assertSame(options[1], choices.single().second)
        }
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().performClick()
        compose.runOnIdle { assertSame(state.value.review, confirmations.single()) }
    }

    @Test fun retainedChooserActionKeepsItsOriginalReviewInsteadOfBorrowingTheReplacement() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = original, templates = options))
        val choices = mutableListOf<Pair<StoryCreationRequest, StoryTemplateOption>>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, {}, onTemplate = { request, option -> choices += request to option })
        } }
        val retained = checkNotNull(compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        val replacement = original.copy(title = "A newly edited title")
        compose.runOnIdle { state.value = state.value.copy(review = replacement) }
        compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().assertIsEnabled()
        compose.runOnIdle {
            retained()
            assertSame(original, choices.single().first)
            assertNotSame(replacement, choices.single().first)
            assertSame(options[1], choices.single().second)
        }
    }

    @Test fun busyCreatingAndClosingStatesDisableStarterSelection() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = original, templates = options, busy = true))
        var choices = 0
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, {}, onTemplate = { _, _ -> choices++ })
        } }
        for (next in listOf(state.value, state.value.copy(busy = false, creating = true), state.value.copy(busy = false, closing = true))) {
            compose.runOnIdle { state.value = next }
            compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        }
        compose.runOnIdle { assertEquals(0, choices) }
    }
}
