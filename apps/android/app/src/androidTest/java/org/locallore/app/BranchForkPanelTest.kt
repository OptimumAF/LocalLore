/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.BranchForkPanel

/** State-only component tests: actual app/VM/JNI journeys are distinct, separately gated checks. */
class BranchForkPanelTest {
    @get:Rule val compose = createComposeRule()
    private val parent = ForkScope("synthetic", "main")
    private val context = BranchForkContext("session", parent, 4, epoch = 1)
    private val input = BranchForkInput(parent, "fixed-child", 4, 2)

    @Test fun hiddenThenExplicitConsentForwardsOnlyTheRenderedFixedIdentity() {
        var visible by mutableStateOf(false)
        var confirmed: BranchForkInput? = null
        var count = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(visible, BranchForkUiState(context = context, input = input, visible = true), null, false,
                    { _, _ -> }, { value, consent -> assertTrue(consent); confirmed = value; count++ }, {}, {}, {}, {}, {}, {})
            }
        }
        compose.onNodeWithTag("fork-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(0, count); visible = true }
        compose.onNodeWithTag("fork-parent").performScrollTo().assertTextEquals("Requested parent: synthetic / main")
        compose.onNodeWithTag("fork-child").performScrollTo().assertTextEquals("Fixed child ID: fixed-child")
        compose.onNodeWithText("Author corrections are unavailable. This does not grant abilities, knowledge or edit existing facts.")
            .performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsNotEnabled().performClick()
        compose.runOnIdle { assertEquals(0, count) }
        compose.onNodeWithTag("fork-consent").performScrollTo().performClick()
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(1, count); assertSame(input, confirmed) }
    }
    @Test fun restoredLookupOnlyCannotCreateAndForgettingRequiresSeparateConsent() {
        var lookups = 0; var forgotten = 0; var forbidden = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, BranchForkUiState(context = context.copy(parent = ForkScope("other", "root")),
                    input = input, visible = true, lookupOnly = true, uncertain = true), null, true,
                    { _, _ -> forbidden++ }, { _, _ -> forbidden++ }, { forbidden++ }, { lookups++ },
                    { consent -> assertTrue(consent); forgotten++ }, {}, {}, { forbidden++ })
            }
        }
        compose.onNodeWithTag("fork-parent").performScrollTo().assertTextEquals("Requested parent: synthetic / main")
        compose.onNodeWithText("Current selection: other / root · head 4").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("fork-lookup-only").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("fork-confirm").assertDoesNotExist()
        compose.onNodeWithTag("fork-retry").assertDoesNotExist()
        compose.onNodeWithTag("fork-boundary").assertDoesNotExist()
        compose.onNodeWithTag("fork-lookup").performScrollTo().performClick()
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsNotEnabled().performClick()
        compose.runOnIdle { assertEquals(1, lookups); assertEquals(0, forgotten); assertEquals(0, forbidden) }
        compose.onNodeWithTag("fork-forget-consent").performScrollTo().performClick()
        compose.onNodeWithTag("fork-forget").performScrollTo().performClick()
        compose.runOnIdle { assertEquals(1, forgotten); assertEquals(0, forbidden) }
    }
    @Test fun pendingAllowsCancelAndConfirmedOutcomeRequiresExplicitResume() {
        val outcome = BranchForkOutcome(1, ForkScope(parent.story, input.childBranch), parent, 2, 3, false)
        var state by mutableStateOf(BranchForkUiState(context = context, input = input, visible = true, busy = true))
        var cancelled = 0; var closed = 0; var resumed: BranchForkOutcome? = null
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, state, null, true, { _, _ -> }, { _, _ -> }, {}, {}, {},
                    { cancelled++ }, { closed++ }, { resumed = it })
            }
        }
        compose.onNodeWithTag("fork-pending").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("fork-close").assertIsNotEnabled().performClick()
        compose.onNodeWithTag("fork-lookup").performScrollTo().assertIsNotEnabled().performClick()
        compose.onNodeWithTag("fork-cancel").performScrollTo().performClick()
        compose.runOnIdle {
            assertEquals(1, cancelled); assertEquals(0, closed); assertNull(resumed)
            state = state.copy(busy = false, outcome = outcome)
        }
        compose.onNodeWithTag("fork-outcome").performScrollTo().assertTextEquals("Existing fork found: synthetic / fixed-child · fork 2 · current head 3")
        compose.onNodeWithTag("fork-resume").performScrollTo().assertIsEnabled().performClick()
        compose.runOnIdle { assertSame(outcome, resumed) }
    }
}
