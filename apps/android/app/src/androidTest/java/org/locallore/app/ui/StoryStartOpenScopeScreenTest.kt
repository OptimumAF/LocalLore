/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.SavedStory
import org.locallore.app.ShellState

/** Actual screen opener semantics with an unguarded callback reading the latest frame. */
class StoryStartOpenScopeScreenTest {
    @get:Rule val compose = createComposeRule()
    private val opened = mutableListOf<ShellState>()

    private fun render(initial: ShellState): MutableState<ShellState> {
        val frame = mutableStateOf(initial)
        compose.setContent {
            MaterialTheme {
                LocalLoreScreen(
                    state = frame.value, onAction = {}, onMode = {}, onCancel = {},
                    onReset = { opened += frame.value },
                )
            }
        }
        return frame
    }

    private fun button(label: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag("reset-demo"))
        return compose.onNodeWithTag("reset-demo").assertIsEnabled().assertTextEquals(label)
    }

    private fun checkReplacement(frame: MutableState<ShellState>, replacement: ShellState, label: String) {
        val retained = checkNotNull(button(label).fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        compose.runOnIdle { frame.value = replacement }
        val current = button(label)
        compose.runOnIdle {
            retained()
            assertTrue(opened.isEmpty())
        }
        current.performClick()
        compose.runOnIdle {
            assertSame(replacement, opened.single())
            opened.clear()
        }
    }

    @Test fun retainedDemoResetCannotResetAnAdvancedScene() {
        val initial = ShellState(revision = 1)
        val frame = render(initial)
        checkReplacement(frame, initial.copy(revision = 2), "Reset demo")
    }

    @Test fun retainedNewStoryCannotStartForAReplacementSelectionOrEmptyLibrary() {
        val first = SavedStory("start-scope-a", "main", "Same visible title", 3)
        val other = first.copy(story = "start-scope-b", revision = 8)
        val initial = ShellState(
            persistent = true, selectedStory = first, stories = listOf(first, other), revision = first.revision,
        )
        val frame = render(initial)
        val replacement = initial.copy(selectedStory = other, revision = other.revision)
        checkReplacement(frame, replacement, "New story")
        checkReplacement(frame, replacement.copy(selectedStory = null, stories = emptyList(), revision = 0), "New story")
    }
}
