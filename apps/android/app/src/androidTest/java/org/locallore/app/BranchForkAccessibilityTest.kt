/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.BranchForkPanel

/** Real component semantics; synthetic callbacks do not create, forget, or recover a timeline. */
class BranchForkAccessibilityTest {
    @get:Rule val compose = createComposeRule()
    private val parent = ForkScope("accessible-story", "main")
    private val input = BranchForkInput(parent, "reviewed-child", 7, 3)
    private val context = BranchForkContext("accessible-session", parent, 7)
    private val createLabel = "Create exactly this new timeline, preserving the original."
    private val forgetLabel = "Forget only the recovery hint. A timeline may already exist."
    private val checkable = SemanticsMatcher.keyIsDefined(SemanticsProperties.ToggleableState)
    private val checkbox = SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Checkbox)

    private fun assertSingleLabeledCheckbox(label: String, tag: String) {
        compose.onAllNodes(hasText(label) and checkbox and checkable and hasClickAction())
            .assertCountEquals(1)
        compose.onNodeWithTag(tag).assertTextEquals(label).assert(checkbox).assert(checkable)
            .assertHasClickAction()
        // The passive visual checkbox must not become a second independently checkable action.
        compose.onAllNodes(checkable, useUnmergedTree = true).assertCountEquals(1)
    }

    @Test fun createLabelOwnsOneNamedCheckboxAndNeverDispatchesWithoutSeparateConfirmation() {
        val state = BranchForkUiState(context = context, visible = true, input = input)
        val confirmed = mutableListOf<Pair<BranchForkInput, Boolean>>()
        var forbidden = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, state, null, false,
                    { _, _ -> forbidden++ }, { value, consent -> confirmed += value to consent },
                    { forbidden++ }, { forbidden++ }, { forbidden++ }, { forbidden++ },
                    { forbidden++ }, { forbidden++ })
            }
        }
        assertSingleLabeledCheckbox(createLabel, "fork-consent")
        compose.onNodeWithTag("fork-consent").performScrollTo().assertIsDisplayed().assertIsOff()
            .assertHeightIsAtLeast(48.dp).assertWidthIsAtLeast(48.dp)
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText(createLabel).performScrollTo().performClick().assertIsOn()
        compose.runOnIdle { assertTrue(confirmed.isEmpty()); assertEquals(0, forbidden) }
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsEnabled()
        compose.onNodeWithText(createLabel).performScrollTo().performClick().assertIsOff()
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText(createLabel).performScrollTo().performClick().assertIsOn()
        compose.runOnIdle { assertTrue(confirmed.isEmpty()); assertEquals(0, forbidden) }
        compose.onNodeWithTag("fork-confirm").performScrollTo().performClick()
        compose.runOnIdle {
            assertEquals(1, confirmed.size)
            assertSame(input, confirmed.single().first)
            assertTrue(confirmed.single().second)
            assertEquals(0, forbidden)
        }
    }

    @Test fun forgetLabelOwnsOneNamedCheckboxAndRequiresItsSeparateExplicitAction() {
        val state = BranchForkUiState(context = context, visible = true, input = input,
            lookupOnly = true, uncertain = true)
        val forgotten = mutableListOf<Boolean>()
        var forbidden = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, state, null, true,
                    { _, _ -> forbidden++ }, { _, _ -> forbidden++ }, { forbidden++ },
                    { forbidden++ }, { forgotten += it }, { forbidden++ }, { forbidden++ },
                    { forbidden++ })
            }
        }
        assertSingleLabeledCheckbox(forgetLabel, "fork-forget-consent")
        compose.onNodeWithTag("fork-confirm").assertDoesNotExist()
        compose.onNodeWithTag("fork-forget-consent").performScrollTo().assertIsDisplayed().assertIsOff()
            .assertHeightIsAtLeast(48.dp).assertWidthIsAtLeast(48.dp)
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText(forgetLabel).performScrollTo().performClick().assertIsOn()
        compose.runOnIdle { assertTrue(forgotten.isEmpty()); assertEquals(0, forbidden) }
        compose.onNodeWithText(forgetLabel).performClick().assertIsOff()
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText(forgetLabel).performScrollTo().performClick().assertIsOn()
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(listOf(true), forgotten); assertEquals(0, forbidden) }
    }

    @Test fun busyConsentLabelsAreDisabledAndRealTouchesCannotAuthorizeEitherAction() {
        val state = BranchForkUiState(context = context, visible = true, input = input, busy = true)
        var dispatched = 0
        compose.setContent {
            MaterialTheme {
                BranchForkPanel(true, state, null, true,
                    { _, _ -> dispatched++ }, { _, _ -> dispatched++ }, { dispatched++ },
                    { dispatched++ }, { dispatched++ }, { dispatched++ }, { dispatched++ },
                    { dispatched++ })
            }
        }
        compose.onAllNodes(checkable, useUnmergedTree = true).assertCountEquals(2)
        for ((label, tag) in listOf(createLabel to "fork-consent", forgetLabel to "fork-forget-consent")) {
            compose.onNodeWithTag(tag).performScrollTo().assertIsDisplayed().assertTextEquals(label)
                .assert(checkbox).assertIsNotEnabled().assertIsOff()
                .performTouchInput { click() }.assertIsOff()
        }
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsNotEnabled()
        compose.runOnIdle { assertEquals(0, dispatched) }
    }

    @Test fun doubleFontCreateLabelAndSeparateActionRemainScrollableAndReachable() {
        val state = BranchForkUiState(context = context, visible = true, input = input)
        val confirmed = mutableListOf<BranchForkInput>()
        var forbidden = 0
        compose.setContent {
            val density = LocalDensity.current.density
            CompositionLocalProvider(LocalDensity provides Density(density, 2f)) {
                MaterialTheme {
                    BranchForkPanel(true, state, null, false,
                        { _, _ -> forbidden++ }, { value, consent -> assertTrue(consent); confirmed += value },
                        { forbidden++ }, { forbidden++ }, { forbidden++ }, { forbidden++ },
                        { forbidden++ }, { forbidden++ })
                }
            }
        }
        assertSingleLabeledCheckbox(createLabel, "fork-consent")
        compose.onNodeWithText(createLabel).performScrollTo().assertIsDisplayed()
            .assertHeightIsAtLeast(48.dp).assertWidthIsAtLeast(48.dp).performClick().assertIsOn()
        compose.runOnIdle { assertTrue(confirmed.isEmpty()); assertEquals(0, forbidden) }
        compose.onNodeWithTag("fork-confirm").performScrollTo().assertIsDisplayed()
            .assertIsEnabled().assertHeightIsAtLeast(48.dp).performClick()
        compose.runOnIdle { assertEquals(1, confirmed.size); assertSame(input, confirmed.single()); assertEquals(0, forbidden) }
    }

    @Test fun doubleFontForgetLabelAndSeparateActionRemainScrollableAndReachable() {
        val state = BranchForkUiState(context = context, visible = true, input = input,
            lookupOnly = true, uncertain = true)
        val forgotten = mutableListOf<Boolean>()
        var forbidden = 0
        compose.setContent {
            val density = LocalDensity.current.density
            CompositionLocalProvider(LocalDensity provides Density(density, 2f)) {
                MaterialTheme {
                    BranchForkPanel(true, state, null, true,
                        { _, _ -> forbidden++ }, { _, _ -> forbidden++ }, { forbidden++ },
                        { forbidden++ }, { forgotten += it }, { forbidden++ }, { forbidden++ },
                        { forbidden++ })
                }
            }
        }
        assertSingleLabeledCheckbox(forgetLabel, "fork-forget-consent")
        compose.onNodeWithText(forgetLabel).performScrollTo().assertIsDisplayed()
            .assertHeightIsAtLeast(48.dp).assertWidthIsAtLeast(48.dp).performClick().assertIsOn()
        compose.runOnIdle { assertTrue(forgotten.isEmpty()); assertEquals(0, forbidden) }
        compose.onNodeWithTag("fork-forget").performScrollTo().assertIsDisplayed()
            .assertIsEnabled().assertHeightIsAtLeast(48.dp).performClick()
        compose.runOnIdle { assertEquals(listOf(true), forgotten); assertEquals(0, forbidden) }
    }
}
