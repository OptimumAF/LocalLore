/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsNotSelected
import androidx.compose.ui.test.assertIsOff
import androidx.compose.ui.test.assertIsOn
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.click
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasAnyDescendant
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.OriginalStoryDialog

/** Compose semantics and typed edit dispatch over a synthetic, unsaved author draft. */
class OriginalStoryChoiceAccessibilityTest {
    @get:Rule val compose = createComposeRule()

    private val edits = mutableListOf<OriginalStoryEdit>()

    private fun showDraft(busy: Boolean = false) {
        val draft = mutableStateOf(OriginalStoryUiState(
            input = OriginalInput(
                premise = "An apprentice visits a garden.",
                playerName = "Iris",
            ),
            proposal = OriginalProposal(
                locations = listOf(
                    OriginalLocation("Garden", "A walled garden."),
                    OriginalLocation("Tower", "A watchtower."),
                ),
                playerLocation = 0,
                characters = listOf(OriginalCharacter("Sel", "A gardener.", 0, listOf(0))),
                routes = listOf(OriginalRoute(0, 1)),
                facts = emptyList(),
                beliefs = emptyList(),
                possessions = emptyList(),
            ),
            provider = "scripted",
            busy = busy,
        ))
        compose.setContent {
            MaterialTheme {
                OriginalStoryDialog(
                    state = draft.value,
                    onDismiss = {},
                    onEdit = { expected, edit ->
                        assertSame(draft.value, expected)
                        edits += edit
                        draft.value = applyOriginalEdit(expected, edit)
                    },
                    onGenerate = {},
                    onReview = {},
                    onCreate = { _, _ -> },
                    exposeTestTags = false,
                )
            }
        }
    }

    private fun choice(label: String, role: Role) =
        compose.onNode(hasText(label) and SemanticsMatcher.expectValue(SemanticsProperties.Role, role))

    private fun actionRow(label: String, role: Role) =
        hasAnyDescendant(hasText(label)) and
            SemanticsMatcher.expectValue(SemanticsProperties.Role, role) and hasClickAction()

    private fun verifyOneAction(label: String, role: Role, grouped: Boolean = false) {
        val row = actionRow(label, role)
        compose.onAllNodes(row, useUnmergedTree = true).assertCountEquals(1)
        compose.onAllNodes(hasAnyAncestor(row) and hasClickAction(), useUnmergedTree = true)
            .assertCountEquals(0)
        if (grouped) {
            val group = SemanticsMatcher.keyIsDefined(SemanticsProperties.SelectableGroup)
            compose.onNode(row and hasAnyAncestor(group), useUnmergedTree = true).assertExists()
        }
    }

    private fun touchLabel(label: String, role: Role) {
        val labelInRow = hasText(label) and hasAnyAncestor(actionRow(label, role))
        compose.onNode(labelInRow, useUnmergedTree = true)
            .performScrollTo()
            .performTouchInput { click() }
    }

    @Test fun exclusiveRulesExposeSelectionAndRespondToLabelTouch() {
        showDraft()
        verifyOneAction("Fantasy", Role.RadioButton, grouped = true)
        choice("Narrative", Role.RadioButton).performScrollTo().assertIsSelected()
        choice("Fantasy", Role.RadioButton).performScrollTo()
            .assertIsNotSelected().assertHeightIsAtLeast(48.dp)

        touchLabel("Fantasy", Role.RadioButton)

        choice("Fantasy", Role.RadioButton).assertIsSelected()
        choice("Narrative", Role.RadioButton).assertIsNotSelected()
        compose.runOnIdle { assertEquals(listOf(OriginalStoryEdit.Select(OriginalSelection.PROFILE, 0)), edits) }
    }

    @Test fun knowledgeAndDirectedRoutesExposeIndependentCheckedStates() {
        showDraft()
        verifyOneAction("Sel", Role.Checkbox)
        choice("Iris", Role.Checkbox).performScrollTo().assertIsOn()
        choice("Sel", Role.Checkbox).performScrollTo().assertIsOff().assertHeightIsAtLeast(48.dp)
        touchLabel("Sel", Role.Checkbox)
        choice("Sel", Role.Checkbox).assertIsOn()
        choice("Iris", Role.Checkbox).assertIsOn()

        verifyOneAction("Tower → Garden", Role.Checkbox)
        choice("Garden → Tower", Role.Checkbox).performScrollTo().assertIsOn()
        choice("Tower → Garden", Role.Checkbox).performScrollTo().assertIsOff()
        touchLabel("Tower → Garden", Role.Checkbox)
        choice("Tower → Garden", Role.Checkbox).assertIsOn()
        choice("Garden → Tower", Role.Checkbox).assertIsOn()
        compose.runOnIdle {
            assertEquals(listOf(
                OriginalStoryEdit.ToggleKnown(OriginalKnown.CHARACTER, row = 0, actor = 1),
                OriginalStoryEdit.ToggleRoute(from = 1, to = 0),
            ), edits)
        }
    }

    @Test fun busyDraftDisablesSelectionAndLabelTouchesDoNotEdit() {
        showDraft(busy = true)
        choice("Fantasy", Role.RadioButton).performScrollTo().assertIsNotEnabled()
        touchLabel("Fantasy", Role.RadioButton)
        choice("Sel", Role.Checkbox).performScrollTo().assertIsNotEnabled()
        touchLabel("Sel", Role.Checkbox)
        choice("Tower → Garden", Role.Checkbox).performScrollTo().assertIsNotEnabled()
        touchLabel("Tower → Garden", Role.Checkbox)
        compose.runOnIdle { assertEquals(emptyList<OriginalStoryEdit>(), edits) }
    }
}
