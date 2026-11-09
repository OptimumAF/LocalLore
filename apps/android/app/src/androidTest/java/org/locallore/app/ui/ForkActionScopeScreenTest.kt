/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.referentialEqualityPolicy
import androidx.compose.runtime.setValue
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.AnnotatedString
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/** Actual retained Material event sources; callbacks are synthetic, never native fork authority. */
class ForkActionScopeScreenTest {
    @get:Rule val compose = createComposeRule()
    private val parent = ForkScope("fork-scope", "main")
    private val input = BranchForkInput(parent, "child-a", 1, 0)
    private val context = BranchForkContext("synthetic-session", parent, 1)
    private fun click(tag: String): () -> Boolean {
        val node = compose.onNodeWithTag(tag)
        if (tag != "fork-close") node.performScrollTo()
        return checkNotNull(node.assertIsDisplayed().fetchSemanticsNode().config[SemanticsActions.OnClick].action)
    }
    @Test fun equalReplacementRetiresForgetLookupAndCheckboxWithoutBorrowingFreshConsent() {
        var state by mutableStateOf(BranchForkUiState(context, visible = true, input = input,
            lookupOnly = true, uncertain = true), referentialEqualityPolicy())
        var forgotten = 0; var lookedUp = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, state, null, true, { _, _ -> }, { _, _ -> }, {},
                    { lookedUp++ }, { check(it); forgotten++ }, {}, {}, {})
            }
        }
        compose.onNodeWithTag("fork-forget-consent").performScrollTo().performClick()
        val oldForget = click("fork-forget"); val oldLookup = click("fork-lookup")
        val oldCheckbox = click("fork-forget-consent")
        compose.runOnIdle { state = state.copy() }
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("fork-forget-consent").performScrollTo().performClick()
        compose.runOnIdle { oldForget(); oldLookup(); oldCheckbox(); assertEquals(0, forgotten); assertEquals(0, lookedUp) }
        compose.onNodeWithTag("fork-forget-consent").assertIsOn()
        compose.onNodeWithTag("fork-forget").performScrollTo().performClick()
        compose.onNodeWithTag("fork-lookup").performScrollTo().performClick()
        compose.runOnIdle { assertEquals(1, forgotten); assertEquals(1, lookedUp) }
    }
    @Test fun oldCancelAndCloseCannotActOnReplacementRequest() {
        var state by mutableStateOf(BranchForkUiState(context, visible = true, input = input))
        var cancelled = 0; var closed = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, state, null, true, { _, _ -> }, { _, _ -> }, {}, {}, {},
                    { cancelled++ }, { closed++ }, {})
            }
        }
        val oldClose = click("fork-close")
        compose.runOnIdle { state = state.copy(busy = true) }
        val oldCancel = click("fork-cancel")
        compose.runOnIdle { state = state.copy(input = input.copy(childBranch = "child-b")) }
        compose.runOnIdle { oldClose(); oldCancel(); assertEquals(0, closed); assertEquals(0, cancelled) }
        compose.onNodeWithTag("fork-cancel").performScrollTo().performClick()
        compose.runOnIdle { assertEquals(1, cancelled); state = state.copy(busy = false) }
        compose.onNodeWithTag("fork-close").performClick()
        compose.runOnIdle { assertEquals(1, closed) }
    }
    @Test fun disposedDialogCannotBorrowTheSameStateAfterRemount() {
        val state = BranchForkUiState(context, visible = true, input = input, lookupOnly = true, uncertain = true)
        var visible by mutableStateOf(true); var forgotten = 0; var closed = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(visible, state, null, true, { _, _ -> }, { _, _ -> }, {}, {},
                    { check(it); forgotten++ }, {}, { closed++ }, {})
            }
        }
        compose.onNodeWithTag("fork-forget-consent").performScrollTo().performClick()
        val oldForget = click("fork-forget"); val oldClose = click("fork-close")
        compose.runOnIdle { visible = false }
        compose.onNodeWithTag("fork-dialog").assertDoesNotExist()
        compose.runOnIdle { visible = true }
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("fork-forget-consent").performScrollTo().performClick()
        compose.runOnIdle { oldForget(); oldClose(); assertEquals(0, forgotten); assertEquals(0, closed) }
        compose.onNodeWithTag("fork-forget-consent").assertIsOn()
        compose.onNodeWithTag("fork-forget").performScrollTo().performClick()
        compose.onNodeWithTag("fork-close").performClick()
        compose.runOnIdle { assertEquals(1, forgotten); assertEquals(1, closed) }
    }
    @Test fun staleBoundaryEditingReviewAndConfirmationCannotRetargetToNewInput() {
        var state by mutableStateOf(BranchForkUiState(context, visible = true, input = input))
        val boundaries = mutableListOf<Pair<BranchForkInput?, Long>>(); val confirmed = mutableListOf<BranchForkInput>()
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, state, null, false, { i, r -> boundaries += i to r },
                    { i, consent -> check(consent); confirmed += i }, {}, {}, {}, {}, {}, {})
            }
        }
        val oldText = checkNotNull(compose.onNodeWithTag("fork-boundary").performScrollTo()
            .fetchSemanticsNode().config[SemanticsActions.SetText].action)
        val oldReview = click("fork-review-boundary")
        compose.onNodeWithTag("fork-consent").performScrollTo().performClick()
        val oldConfirm = click("fork-confirm"); val oldCheckbox = click("fork-consent")
        val replacement = input.copy(childBranch = "child-b", atRevision = 1)
        compose.runOnIdle { state = state.copy(input = replacement) }
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("fork-consent").performScrollTo().performClick()
        compose.runOnIdle { oldText(AnnotatedString("0")); oldReview(); oldConfirm(); oldCheckbox() }
        compose.onNodeWithTag("fork-consent").assertIsOn()
        compose.onNodeWithTag("fork-boundary").performScrollTo().assertTextContains("1")
        compose.runOnIdle { assertTrue(boundaries.isEmpty()); assertTrue(confirmed.isEmpty()) }
        compose.onNodeWithTag("fork-boundary").performTextReplacement("0")
        compose.onNodeWithTag("fork-review-boundary").performScrollTo().performClick()
        compose.onNodeWithTag("fork-confirm").performScrollTo().performClick()
        compose.runOnIdle { assertEquals(listOf(replacement to 0L), boundaries); assertEquals(listOf(replacement), confirmed) }
    }
    @Test fun oldForkOpenerCannotRetargetAcrossAnEqualRefreshOrScreenRemount() {
        val story = SavedStory("fork-scope", "main", "Synthetic timeline", 1)
        var state by mutableStateOf(ShellState(persistent = true, selectedStory = story, stories = listOf(story), revision = 1), referentialEqualityPolicy())
        var mounted by mutableStateOf(true); var opened = 0
        compose.setContent {
            MaterialTheme {
                if (mounted) LocalLoreScreen(state, {}, {}, {}, {}, forkAvailable = true, onFork = { opened++ })
            }
        }
        val old = click("fork-timeline")
        compose.runOnIdle { state = state.copy() }
        compose.runOnIdle { old(); assertEquals(0, opened) }
        val beforeRemount = click("fork-timeline")
        compose.runOnIdle { mounted = false }
        compose.onNodeWithTag("fork-timeline").assertDoesNotExist()
        compose.runOnIdle { mounted = true }
        compose.runOnIdle { beforeRemount(); assertEquals(0, opened) }
        compose.onNodeWithTag("fork-timeline").performScrollTo().performClick()
        compose.runOnIdle { assertEquals(1, opened) }
    }
}
