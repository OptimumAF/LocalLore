/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.AnnotatedString
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.StoryCreationDialog

/** Compose consent semantics; native names and durability are separate checks. */
class StoryPlayerSetupDialogTest {
    @get:Rule val compose = createComposeRule()
    private val preview = StoryCreationPreview(DEFAULT_STORY_TEMPLATE, "a".repeat(64), "Lantern Quay",
        "Original starter.", "fantasy_v1", listOf("Player: Rowan"), StoryPlayerSetup("a".repeat(64), "b".repeat(64), "Rowan"))
    private val request = StoryCreationRequest(preview, preview.defaultTitle, "c".repeat(32))
    private fun reviewed(name: String) = preview.copy(details = listOf("Player: $name"),
        playerSetup = preview.playerSetup!!.copy(playerName = name, setupSha256 = "d".repeat(64)))

    @Test fun editingNameRequiresExplicitReviewBeforeCreate() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = request, playerNameDraft = "Rowan"))
        val reviews = mutableListOf<StoryCreationRequest>()
        val confirmed = mutableListOf<StoryCreationRequest>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, confirmed::add,
                onPlayerName = { _, text -> state.value = state.value.copy(review = state.value.review!!.copy(),
                    playerNameDraft = text, playerNameEdited = true) },
                onPlayerReview = { expected ->
                    reviews += expected
                    state.value = state.value.copy(review = expected.copy(preview = reviewed(state.value.playerNameDraft!!)))
                })
        } }
        compose.onNodeWithTag("story-player-name").performScrollTo().performTextReplacement("Marin")
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText("Player: Rowan").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("story-player-review-required").performScrollTo().assertIsDisplayed()
        compose.runOnIdle { assertTrue(reviews.isEmpty()); assertTrue(confirmed.isEmpty()) }
        compose.onNodeWithTag("story-player-review").performScrollTo().assertIsEnabled().performClick()
        compose.onNodeWithText("Player: Marin").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Player: Rowan").assertDoesNotExist()
        compose.onNodeWithTag("story-player-review").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled().performClick()
        compose.runOnIdle {
            assertEquals(1, reviews.size)
            assertSame(state.value.review, confirmed.single())
            assertEquals("Marin", confirmed.single().preview.playerSetup!!.playerName)
            assertEquals(request.creationId, confirmed.single().creationId)
        }
    }

    @Test fun retainedNameReviewAndConfirmActionsKeepTheirOriginalRequest() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = request, playerNameDraft = "Rowan"))
        val names = mutableListOf<StoryCreationRequest>()
        val reviews = mutableListOf<StoryCreationRequest>()
        val confirmed = mutableListOf<StoryCreationRequest>()
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, confirmed::add,
                onPlayerName = { expected, _ -> names += expected }, onPlayerReview = reviews::add)
        } }
        val oldName = checkNotNull(compose.onNodeWithTag("story-player-name").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.SetText].action)
        val oldConfirm = checkNotNull(compose.onNodeWithTag("story-creation-confirm").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        val dirty = request.copy()
        compose.runOnIdle { state.value = state.value.copy(review = dirty, playerNameDraft = "Marin", playerNameEdited = true) }
        val oldReview = checkNotNull(compose.onNodeWithTag("story-player-review").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        val replacement = dirty.copy(preview = reviewed("Marin"))
        compose.runOnIdle { state.value = state.value.copy(review = replacement) }
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled()
        compose.runOnIdle {
            oldName(AnnotatedString("Wrong name")); oldReview(); oldConfirm()
            // Typing may target the latest draft of the SAME preview, never a replacement preview.
            assertSame(preview, names.single().preview)
            assertNotSame(replacement.preview, names.single().preview)
            assertSame(dirty, reviews.single())
            assertSame(request, confirmed.single())
        }
    }

    @Test fun invalidNamesAndBusyStatesCannotReviewOrCreate() {
        val state = mutableStateOf(StoryCreationUiState(visible = true, review = request, playerNameDraft = " outer"))
        var actions = 0
        compose.setContent { MaterialTheme {
            StoryCreationDialog(state.value, {}, { _, _ -> }, { actions++ },
                onPlayerName = { _, _ -> actions++ }, onPlayerReview = { actions++ })
        } }
        for (name in listOf(" outer", "", "n".repeat(65))) {
            compose.runOnIdle { state.value = state.value.copy(playerNameDraft = name) }
            compose.onNodeWithTag("story-player-name-error").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("story-player-review").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        }
        for (busy in listOf(
            state.value.copy(playerNameDraft = "Marin", busy = true),
            state.value.copy(playerNameDraft = "Marin", creating = true),
            state.value.copy(playerNameDraft = "Marin", closing = true))) {
            compose.runOnIdle { state.value = busy }
            compose.onNodeWithTag("story-player-name").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-player-review").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        }
        compose.runOnIdle { state.value = StoryCreationUiState(visible = true, review = request.copy(preview = preview.copy(playerSetup = null))) }
        compose.onNodeWithTag("story-player-name").assertDoesNotExist()
        compose.onNodeWithTag("story-player-review").assertDoesNotExist()
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled()
        compose.runOnIdle { assertEquals(0, actions) }
    }
}
