/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.AnnotatedString
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.StoryCreationDialog

/** Compose semantics and captured consent; native persistence and narration checks are separate. */
class StoryPresentationDialogTest {
    @get:Rule val compose = createComposeRule()
    private val preview = StoryCreationPreview(DEFAULT_STORY_TEMPLATE, "a".repeat(64), "Lantern Quay", "Original starter.",
        "fantasy_v1", listOf("Player: Rowan"), StoryPlayerSetup("a".repeat(64), "b".repeat(64), "Rowan"), StoryPresentation())
    private val request = StoryCreationRequest(preview, preview.defaultTitle, "c".repeat(32))
    private fun initial() = StoryCreationUiState(visible = true, review = request, playerNameDraft = "Rowan",
        toneDraft = "plain", excludedPhrasesDraft = "")

    @Test fun presentationEditsRequireExplicitReviewBeforeCreate() {
        val state = mutableStateOf(initial())
        val reviews = mutableListOf<StoryCreationRequest>()
        val creates = mutableListOf<StoryCreationRequest>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, creates::add,
                onTone = { _, tone -> state.value = state.value.copy(review = state.value.review!!.copy(), toneDraft = tone) },
                onExcludedPhrases = { _, text -> state.value = state.value.copy(review = state.value.review!!.copy(), excludedPhrasesDraft = text) },
                onPlayerReview = { expected ->
                    reviews += expected
                    val settings = storyPresentationDraft(state.value.toneDraft, state.value.excludedPhrasesDraft)!!
                    state.value = state.value.copy(review = expected.copy(preview = expected.preview.copy(presentation = settings,
                        playerSetup = expected.preview.playerSetup!!.copy(setupSha256 = "d".repeat(64)))))
                })
        } }
        compose.onNodeWithTag("story-tone-warm").performScrollTo().assertIsNotSelected().performClick()
        compose.onNodeWithTag("story-tone-warm").performScrollTo().assertIsSelected()
        compose.onNodeWithTag("story-excluded-phrases").performScrollTo().performTextReplacement("red fog\nstorm bell")
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("story-presentation-review-required").performScrollTo().assertIsDisplayed()
        compose.runOnIdle { assertTrue(reviews.isEmpty()); assertTrue(creates.isEmpty()) }
        compose.onNodeWithTag("story-player-review").performScrollTo().assertIsEnabled().performClick()
        compose.onNodeWithText("Reviewed narration tone · Warm").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Avoid literal phrase: red fog").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("story-player-review").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled().performClick()
        compose.runOnIdle {
            assertEquals(1, reviews.size); assertSame(state.value.review, creates.single())
            assertEquals(StoryPresentation("warm", listOf("red fog", "storm bell")), creates.single().preview.presentation)
        }
    }

    @Test fun retainedPresentationActionsCannotBorrowAReplacementReview() {
        val state = mutableStateOf(initial())
        val fields = mutableListOf<StoryCreationRequest>()
        val reviews = mutableListOf<StoryCreationRequest>()
        val creates = mutableListOf<StoryCreationRequest>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, creates::add,
                onTone = { expected, _ -> fields += expected }, onExcludedPhrases = { expected, _ -> fields += expected },
                onPlayerReview = reviews::add)
        } }
        val oldTone = checkNotNull(compose.onNodeWithTag("story-tone-warm").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        val oldPhrases = checkNotNull(compose.onNodeWithTag("story-excluded-phrases").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.SetText].action)
        val oldCreate = checkNotNull(compose.onNodeWithTag("story-creation-confirm").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        val dirty = request.copy()
        compose.runOnIdle { state.value = state.value.copy(review = dirty, toneDraft = "warm") }
        val oldReview = checkNotNull(compose.onNodeWithTag("story-player-review").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        val replacement = dirty.copy(preview = preview.copy(presentation = StoryPresentation("warm")))
        compose.runOnIdle { state.value = state.value.copy(review = replacement) }
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled()
        compose.runOnIdle {
            oldTone(); oldPhrases(AnnotatedString("Wrong")); oldReview(); oldCreate()
            assertEquals(2, fields.size)
            fields.forEach { assertSame(preview, it.preview); assertNotSame(replacement.preview, it.preview) }
            assertSame(dirty, reviews.single()); assertSame(request, creates.single())
        }
    }

    @Test fun invalidPhraseDraftsAndBusyStatesDisableReviewAndCreate() {
        val options = listOf(preview.option(), StoryTemplateOption("bracken-harbor-v1", "Bracken Harbor", "Original harbor.", "narrative_v1"))
        val state = mutableStateOf(initial().copy(templates = options, excludedPhrasesDraft = " outer"))
        var actions = 0
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, { actions++ }, onTemplate = { _, _ -> actions++ },
                onTone = { _, _ -> actions++ }, onExcludedPhrases = { _, _ -> actions++ }, onPlayerReview = { actions++ })
        } }
        for (invalid in listOf(" outer", "one\n", "echo\nECHO", "n".repeat(65))) {
            compose.runOnIdle { state.value = state.value.copy(excludedPhrasesDraft = invalid) }
            val editor = compose.onNodeWithTag("story-excluded-phrases").performScrollTo().fetchSemanticsNode()
            assertEquals(invalid, editor.config[SemanticsProperties.EditableText].text)
            compose.onNodeWithTag("story-presentation-error").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("story-player-review").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().assertIsNotEnabled()
        }
        for (next in listOf(initial().copy(toneDraft = "warm", busy = true), initial().copy(toneDraft = "warm", creating = true),
            initial().copy(toneDraft = "warm", closing = true))) {
            compose.runOnIdle { state.value = next }
            compose.onNodeWithTag("story-tone-warm").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-excluded-phrases").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-player-review").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        }
        compose.runOnIdle { state.value = StoryCreationUiState(visible = true, review = request.copy(preview = preview.copy(presentation = null)), playerNameDraft = "Rowan") }
        compose.onNodeWithTag("story-tone-warm").assertDoesNotExist()
        compose.onNodeWithTag("story-excluded-phrases").assertDoesNotExist()
        compose.onNodeWithTag("story-player-name").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled()
        compose.runOnIdle { assertEquals(0, actions) }
    }
}
